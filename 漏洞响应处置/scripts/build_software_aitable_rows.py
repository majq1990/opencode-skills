#!/usr/bin/env python3
"""Generate aitable record-create payload for software vulnerabilities.

录入范式：软件 × 多 CVE 合并 = 一行。
只填 4 字段：软件、序号、漏洞项、说明&解决方案。其他 6 字段全留空（用户决策）。

序号、说明&解决方案 用 sentinel 占位，由 publish.py 在写入时回填：
  - __AUTO_INCREMENT__   → publish.py query 表当前 max(序号)+1
  - __DOC_URL__          → publish.py 用刚 publish 出来的 nodeId 拼成 alidocs URL

输出：archive_dir/sw-<software>-<ts>_rows.json

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
TABLE_ID = "oz3kcid3c79qy2lqspsn3"

FIELD_ID = {
    "software":       "7ajxu4kgmvjirkvoamcv3",
    "sequence":       "7k08ogebp2icgn93thnv4",
    "vuln_items":     "6hcpem5c9dgsvsmyxv7tq",
    "advice_url":     "o9qusfb8e9qow49igstwg",
    # 留空字段 fieldId 也记录，便于审计
    "involved_product": "n3djf91ig7kmb0kdr22x8",
    "field9":           "1z0wikuz84x1gsm5lx2od",
    "feedback_date":    "mg7pem3ji0yfumkbxrw2y",
    "field8":           "y0wszd9ndgz5i56nx4xxp",
    "attachment":       "ktfe3cqp3oc01nm95j8dg",
    "task_id":          "r9jnby1krjxr9qgyihb1b",
}

SENTINEL_AUTO_INC = "__AUTO_INCREMENT__"
SENTINEL_DOC_URL = "__DOC_URL__"


def render_vuln_items(plan_overrides_list: List[dict], scan_cves: List[dict]) -> str:
    """每行格式：<标题>(<CVE-ID>)，多个 CVE 用 \n 分隔。"""
    overrides_map = {o["cve_id"]: o for o in plan_overrides_list}
    lines = []
    for entry in scan_cves:
        cve_id = entry["cve_id"]
        ov = overrides_map.get(cve_id, {})
        title = ov.get("title")
        if not title:
            ghsa = next((v for v in entry["vendor_lookups"]
                         if v["source"] == "ghsa" and v.get("status") == "ok"), {})
            nvd = next((v for v in entry["vendor_lookups"]
                        if v["source"] == "nvd" and v.get("status") == "ok"), {})
            title = ghsa.get("summary") or _short(nvd.get("description"), 40) or "未命名"
        lines.append(f"{title}({cve_id})")
    return "\n".join(lines)


def _short(s, n: int) -> str:
    if not s:
        return ""
    s = str(s).replace("\n", " ").strip()
    return s if len(s) <= n else s[:n] + "..."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scan", help="path to software scan.json")
    ap.add_argument("plan", help="path to plan.json")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    scan = json.loads(Path(args.scan).read_text(encoding="utf-8"))
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))

    sw_key = scan["software"]
    if not sw_key:
        raise SystemExit("[rows-software] scan.software is required")

    cve_overrides = plan.get("cve_overrides", [])
    vuln_items = render_vuln_items(cve_overrides, scan["cves"])

    record = {
        "cells": {
            FIELD_ID["software"]:   sw_key,
            FIELD_ID["sequence"]:   SENTINEL_AUTO_INC,
            FIELD_ID["vuln_items"]: vuln_items,
            FIELD_ID["advice_url"]: SENTINEL_DOC_URL,
        }
    }

    payload = {
        "_meta": {
            "mode": "software",
            "baseId": BASE_ID,
            "tableId": TABLE_ID,
            "software": sw_key,
            "row_count": 1,
            "auto_increment_field": FIELD_ID["sequence"],
            "doc_url_field": FIELD_ID["advice_url"],
            "generated_at": datetime.now(CST).isoformat(timespec="seconds"),
        },
        "records": [record],
    }

    ts = datetime.now(CST).strftime("%Y%m%d%H%M%S")
    out = Path(args.out) if args.out else archive_dir() / f"sw-{sw_key}-{ts}_rows.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
