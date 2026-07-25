#!/usr/bin/env python3
"""Render OS CVE markdown from scan.json + plan.json + template.

scan.json   — output of fetch_vendor_advisory.py (vendor 公告原始数据)
plan.json   — 研判结论（漏洞名/概述/检测工具/各 OS 修复段/缓解措施/离线包），由 LLM 或人写
template.md — references/os_cve_template.md

输出：_archive/<CVE>_doc_<ts>.md（LF 换行）

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

TEMPLATE_PATH = references_dir() / "os_cve_template.md"
CST = timezone(timedelta(hours=8))

PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def _table(headers: List[str], rows: List[List[str]]) -> str:
    line1 = "| " + " | ".join(headers) + " |"
    line2 = "|" + "|".join(["------"] * len(headers)) + "|"
    body = "\n".join("| " + " | ".join(str(c) for c in r) + " |" for r in rows)
    return "\n".join([line1, line2, body])


def render_affected_table(rows: List[dict]) -> str:
    return _table(
        ["操作系统", "受影响版本", "默认内核版本"],
        [[r["os"], r["versions"], r["default_kernel"]] for r in rows],
    )


def render_offline_patch_table(rows: List[dict]) -> str:
    return _table(
        ["操作系统", "补丁包类型", "下载来源", "说明"],
        [[r["os"], r["type"], r["url"], r.get("note", "")] for r in rows],
    )


def render_os_fix_sections(os_fixes: List[dict]) -> str:
    parts = []
    for i, f in enumerate(os_fixes, start=1):
        block = [f"### 2.2.{i} {f['name']}", ""]
        block.append("**确认说明：**")
        block.extend(f"- {line}" for line in f.get("confirm_lines", []))
        block.append("")
        block.append("**在线修复命令：**")
        block.append("")
        block.append("```bash")
        block.append(f["fix_cmd"].rstrip())
        block.append("```")
        block.append("")
        block.append(f"**官方公告：** {f['advisory_url']}")
        block.append("")
        block.append("---")
        block.append("")
        parts.append("\n".join(block))
    return "\n".join(parts).rstrip() + "\n"


def render_reference_links(links: List[str]) -> str:
    return "\n".join(f"- {url}" for url in links)


def render_not_affected_list(items: List[str]) -> str:
    return "\n".join(f"- {it}" for it in items)


def render_detect_tool_features(features: List[str]) -> str:
    return "\n".join(f"- {f}" for f in features)


def build(scan: dict, plan: dict, template: str) -> str:
    cve_id = scan["cve_id"]
    detect = plan["detect_tool"]
    mit = plan["mitigation"]

    mapping: Dict[str, Any] = {
        "VULN_TITLE": plan["vuln_title"],
        "CVE_ID": cve_id,
        "VULN_SUMMARY": plan["vuln_summary"].rstrip(),
        "REFERENCE_LINKS": render_reference_links(plan.get("reference_links", [])),
        "AFFECTED_RANGE_INTRO": plan.get("affected_range_intro", "").rstrip(),
        "AFFECTED_TABLE": render_affected_table(plan["affected_table_rows"]),
        "NOT_AFFECTED_LIST": render_not_affected_list(plan.get("not_affected_list", [])),
        "KERNEL_VERSION_RULE": plan["kernel_version_rule"].rstrip(),
        "KERNEL_CONFIG_CHECK_CMD": plan["kernel_config_check_cmd"].rstrip(),
        "KERNEL_CONFIG_RULE": plan["kernel_config_rule"].rstrip(),
        "MODULE_CHECK_CMD": plan["module_check_cmd"].rstrip(),
        "MODULE_CHECK_RULE": plan["module_check_rule"].rstrip(),
        "DETECT_TOOL_REPO": detect["repo"],
        "DETECT_TOOL_LICENSE": detect.get("license", "MIT 协议"),
        "DETECT_TOOL_STARS": detect.get("stars", "?"),
        "DETECT_TOOL_FORKS": detect.get("forks", "?"),
        "DETECT_TOOL_UPDATED": detect.get("updated", "?"),
        "DETECT_TOOL_FEATURES": render_detect_tool_features(detect.get("features", [])),
        "DETECT_TOOL_GITHUB": detect["github"],
        "DETECT_TOOL_RAW": detect["raw"],
        "DETECT_TOOL_JSDELIVR": detect["jsdelivr"],
        "DETECT_TOOL_GHPROXY": detect["ghproxy"],
        "DETECT_TOOL_USAGE": detect["usage"].rstrip(),
        "OS_FIX_SECTIONS": render_os_fix_sections(plan["os_fixes"]).rstrip(),
        "MITIGATION_MODULE_NAME": mit["module_name"],
        "MITIGATION_MODULE_GREP": mit.get("module_grep", mit["module_name"]),
        "MITIGATION_INITCALL": mit["initcall"],
        "MITIGATION_SECCOMP": mit["seccomp"].rstrip(),
        "OFFLINE_PATCH_TABLE": render_offline_patch_table(plan["offline_patch_table_rows"]),
    }

    out = template
    for key, val in mapping.items():
        out = out.replace("{{" + key + "}}", str(val))

    leftover = PLACEHOLDER_RE.findall(out)
    if leftover:
        raise SystemExit(f"[build] unfilled placeholders: {sorted(set(leftover))}")

    out = out.replace("\r\n", "\n").replace("\r", "\n")
    if not out.endswith("\n"):
        out += "\n"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scan", help="path to scan.json (output of fetch_vendor_advisory.py)")
    ap.add_argument("plan", help="path to plan.json (research outcome)")
    ap.add_argument("--template", default=str(TEMPLATE_PATH))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    scan = json.loads(Path(args.scan).read_text(encoding="utf-8"))
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    template = Path(args.template).read_text(encoding="utf-8").replace("\r\n", "\n")

    md = build(scan, plan, template)

    cve = scan["cve_id"]
    ts = datetime.now(CST).strftime("%Y%m%d%H%M%S")
    out = Path(args.out) if args.out else archive_dir() / f"{cve}_doc_{ts}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fp:
        fp.write(md)
    print(str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
