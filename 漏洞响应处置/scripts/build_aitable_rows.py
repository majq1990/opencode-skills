#!/usr/bin/env python3
"""Generate aitable record-create payload from plan.json.

plan.json 必须含 `aitable_rows: list[dict]`，每行字段：
  - os: 显示名（必须在白名单内）
  - version: 形如 "V10 SP3" / "22.04 LTS"
  - cvss: number 或 None
  - source: 信息来源描述（厂商 + SA 编号）
  - affected: "是" / "否"
  - default_kernel: 形如 "5.10.x"
  - vuln_name: 漏洞名称
  - fix_cmd / verify_cmd / advisory_url —— 自动拼成「处置建议」三段式

输出：_archive/<CVE>_rows_<ts>.json，结构为 {"records":[{"fields":{...}}]}，
直接可被 `dws aitable record create --records '<json>'` 消费。

Python 3.6+ compatible.
"""
import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import archive_dir  # noqa: E402

CST = timezone(timedelta(hours=8))

BASE_ID = "qnYMoO1rWxDl1N54sz3zaKemW47Z3je9"
TABLE_ID = "f3dzlj97k3121hq4adg10"

FIELD_ID = {
    "os":             "eyyot4lp34qhb0no8pfft",
    "version":        "k7k539eh44ge7cx4a00kg",
    "cvss":           "4c0tcmju3g99f13eaviy5",
    "source":         "92sy0dfe1sui2jb8chr94",
    "affected":       "kgdi0bpx8hz6zc0lz5792",
    "default_kernel": "mszmmh1eeh3e0j13znjx1",
    "cve_id":         "rqhppwz3wc6ei91funonu",
    "vuln_name":      "w4yy82i3eupd9bq2j0bwk",
    "advice":         "oxlb9cvxvwku691qho1e1",
}

OS_OPTIONS = {"统信UOS", "openEuler", "Ubuntu", "CentOS", "银河麒麟", "OpenAnolis"}
AFFECTED_OPTIONS = {"是", "否"}


def _three_segments(fix_cmd: str, verify_cmd: str, advisory_url: str) -> str:
    return f"[修复] {fix_cmd.strip()} | [验证] {verify_cmd.strip()} | [公告] {advisory_url.strip()}"


def build_records(cve_id: str, vuln_name: str, rows: List[dict]) -> List[dict]:
    out: List[dict] = []
    for i, r in enumerate(rows):
        if r["os"] not in OS_OPTIONS:
            raise SystemExit(f"[rows] row {i} os '{r['os']}' not in {OS_OPTIONS}")
        if r["affected"] not in AFFECTED_OPTIONS:
            raise SystemExit(f"[rows] row {i} affected '{r['affected']}' must be 是/否")
        fields = {
            FIELD_ID["os"]:             r["os"],
            FIELD_ID["version"]:        str(r["version"]),
            FIELD_ID["source"]:         r["source"],
            FIELD_ID["affected"]:       r["affected"],
            FIELD_ID["default_kernel"]: str(r.get("default_kernel", "")),
            FIELD_ID["cve_id"]:         cve_id,
            FIELD_ID["vuln_name"]:      r.get("vuln_name") or vuln_name,
            FIELD_ID["advice"]:         _three_segments(r["fix_cmd"], r["verify_cmd"], r["advisory_url"]),
        }
        if r.get("cvss") is not None:
            fields[FIELD_ID["cvss"]] = float(r["cvss"])
        out.append({"cells": fields})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan", help="path to plan.json")
    ap.add_argument("--cve", default=None, help="override CVE id (default = plan.cve_id)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    cve_id = (args.cve or plan.get("cve_id") or "").upper()
    if not cve_id:
        raise SystemExit("[rows] missing cve_id (plan.cve_id or --cve)")

    vuln_name = plan.get("vuln_codename") or plan.get("vuln_name") or ""
    rows = plan.get("aitable_rows")
    if not rows:
        raise SystemExit("[rows] plan.aitable_rows is required and non-empty")

    records = build_records(cve_id, vuln_name, rows)
    payload = {
        "_meta": {
            "baseId": BASE_ID,
            "tableId": TABLE_ID,
            "cve_id": cve_id,
            "row_count": len(records),
            "generated_at": datetime.now(CST).isoformat(timespec="seconds"),
        },
        "records": records,
    }
    ts = datetime.now(CST).strftime("%Y%m%d%H%M%S")
    out = Path(args.out) if args.out else archive_dir() / f"{cve_id}_rows_{ts}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
