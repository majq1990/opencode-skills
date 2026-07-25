#!/usr/bin/env python3
"""Render software CVE markdown from scan.json + plan.json + software_template.md.

scan.json   — output of fetch_software_advisory.py
plan.json   — 研判结论（文档标题/版本/检测命令/缓解措施/离线包），由 LLM 或人写
template.md — references/software_template.md

输出：archive_dir/sw-<software>-<ts>_doc.md（LF 换行）

Python 3.6+ compatible.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import archive_dir, references_dir  # noqa: E402

TEMPLATE_PATH = references_dir() / "software_template.md"
CST = timezone(timedelta(hours=8))
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def _table(headers: List[str], rows: List[List[str]]) -> str:
    if not rows:
        return ""
    line1 = "| " + " | ".join(headers) + " |"
    line2 = "|" + "|".join(["------"] * len(headers)) + "|"
    body = "\n".join("| " + " | ".join(str(c) for c in r) + " |" for r in rows)
    return "\n".join([line1, line2, body])


def render_cve_table(scan_cves: List[dict], plan_overrides: Dict[str, dict]) -> str:
    """plan_overrides: {cve_id: {title, brief}} — 覆盖 NVD 默认描述"""
    rows = []
    for entry in scan_cves:
        cve_id = entry["cve_id"]
        nvd = next((v for v in entry["vendor_lookups"] if v["source"] == "nvd" and v.get("status") == "ok"), {})
        ghsa = next((v for v in entry["vendor_lookups"] if v["source"] == "ghsa" and v.get("status") == "ok"), {})
        ov = plan_overrides.get(cve_id, {})
        title = ov.get("title") or (ghsa.get("summary") or _short(nvd.get("description"), 40) or "")
        cvss = ov.get("cvss") or nvd.get("cvss") or ghsa.get("cvss") or "-"
        severity = ov.get("severity") or nvd.get("severity") or ghsa.get("severity") or "-"
        brief = ov.get("brief") or _short(nvd.get("description"), 80) or ""
        rows.append([cve_id, title, str(cvss), severity, brief])
    return _table(["CVE 编号", "漏洞名称", "CVSS", "严重等级", "简述"], rows)


def render_reference_links(scan_cves: List[dict], extras: List[str]) -> str:
    seen = set()
    lines = []
    for c in scan_cves:
        for v in c.get("vendor_lookups") or []:
            if v.get("status") != "ok":
                continue
            for r in v.get("references") or []:
                u = r.get("url") if isinstance(r, dict) else r
                if u and u not in seen:
                    seen.add(u)
                    lines.append(f"- {u}")
            url = v.get("html_url") or v.get("advisory_url")
            if url and url not in seen:
                seen.add(url)
                lines.append(f"- {url}")
    for u in extras or []:
        if u not in seen:
            seen.add(u)
            lines.append(f"- {u}")
    return "\n".join(lines)


def render_offline_patch_table(rows: List[dict]) -> str:
    if not rows:
        return "_本次涉及软件可直接通过包管理器升级，无需额外离线包。_"
    return _table(
        ["补丁包类型", "下载来源", "说明"],
        [[r.get("type", "-"), r.get("url", "-"), r.get("note", "")] for r in rows],
    )


def _short(s, n: int) -> str:
    if not s:
        return ""
    s = str(s).replace("\n", " ").strip()
    return s if len(s) <= n else s[:n] + "..."


def build(scan: dict, plan: dict, template: str) -> str:
    sw_key = scan["software"]
    plan_overrides = {item["cve_id"]: item for item in plan.get("cve_overrides", [])}

    mapping = {
        "DOC_TITLE": plan["doc_title"],
        "SOFTWARE_DISPLAY_NAME": plan["software_display_name"],
        "SOFTWARE_KEY": sw_key,
        "AFFECTED_VERSIONS": plan["affected_versions"],
        "FIXED_VERSIONS": plan["fixed_versions"],
        "CVE_TABLE": render_cve_table(scan["cves"], plan_overrides),
        "VULN_SUMMARY": plan["vuln_summary"].rstrip(),
        "REFERENCE_LINKS": render_reference_links(scan["cves"], plan.get("extra_references", [])),
        "VERSION_CHECK_CMD": plan["version_check_cmd"].rstrip(),
        "VERSION_CHECK_RULE": plan.get("version_check_rule", "").rstrip(),
        "CONFIG_CHECK_BODY": plan.get("config_check_body", "_无特定配置触发条件_").rstrip(),
        "ONLINE_UPGRADE_CMD": plan["online_upgrade_cmd"].rstrip(),
        "VERIFY_CMD": plan["verify_cmd"].rstrip(),
        "VERIFY_RULE": plan.get("verify_rule", "").rstrip(),
        "MITIGATION_BODY": plan.get("mitigation_body", "_无可用临时缓解，请直接升级_").rstrip(),
        "OFFLINE_PATCH_TABLE": render_offline_patch_table(plan.get("offline_patch_rows", [])),
        "OFFLINE_UPGRADE_STEPS": plan.get("offline_upgrade_steps", "_略，参考 2.2 在线升级命令并替换为本地包路径_").rstrip(),
    }

    out = template
    for k, v in mapping.items():
        out = out.replace("{{" + k + "}}", str(v))

    leftover = PLACEHOLDER_RE.findall(out)
    if leftover:
        raise SystemExit(f"[build-software] unfilled placeholders: {sorted(set(leftover))}")

    out = out.replace("\r\n", "\n").replace("\r", "\n")
    if not out.endswith("\n"):
        out += "\n"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scan", help="path to software scan.json")
    ap.add_argument("plan", help="path to plan.json (research outcome)")
    ap.add_argument("--template", default=str(TEMPLATE_PATH))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    scan = json.loads(Path(args.scan).read_text(encoding="utf-8"))
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    template = Path(args.template).read_text(encoding="utf-8").replace("\r\n", "\n")

    md = build(scan, plan, template)

    sw = scan["software"]
    ts = datetime.now(CST).strftime("%Y%m%d%H%M%S")
    out = Path(args.out) if args.out else archive_dir() / f"sw-{sw}-{ts}_doc.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fp:
        fp.write(md)
    print(str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
