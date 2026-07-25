#!/usr/bin/env python3
"""把 parse_probe.py 的结构化输出推到钉钉 AI 表格.

输入: parse_probe.py 的 JSON (stdin 或 --input)
动作:
  1. 矩阵表: 对每个识别到的软件 record_id, 把 OS×CPU 列(field_id) 更新为版本字符串
  2. 问题表: 跑 risk_rules.evaluate(), 把命中的 findings + probe gap 插入新记录,
     批次 key = yyyymmdd-<os_key>
  3. dry-run: 只 print 待写内容, 不调 dws

调 dws CLI: `dws aitable record update/create --base-id ... --table-id ... --records '...'`
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
import risk_rules  # noqa: E402

META_PATH = SCRIPT_DIR.parent / "config" / "aitable_meta.json"


def load_meta() -> dict:
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def dws_call(args: list[str], dry_run: bool = False) -> dict | None:
    if dry_run:
        print(f"[DRY-RUN] dws {' '.join(args)}", file=sys.stderr)
        return None
    cmd = ["dws"] + args + ["--format", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        print(f"[ERR] dws failed: {r.stderr}", file=sys.stderr)
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        print(f"[ERR] dws output not JSON: {r.stdout[:400]}", file=sys.stderr)
        return None


def update_matrix(parsed: dict, dry_run: bool = False) -> dict:
    """更新矩阵表 OS×CPU 列. 返回 {software: status} 摘要."""
    meta = load_meta()
    base_id = meta["baseId"]
    matrix = meta["tables"]["matrix"]
    table_id = matrix["tableId"]
    os_field = parsed.get("os_field")
    if not os_field:
        print(f"[WARN] OS key '{parsed.get('os_key')}' 未映射到任何 matrix 列, 跳过矩阵更新",
              file=sys.stderr)
        return {}

    sw_to_rec = meta["software_to_record"]
    sw_ver = parsed["software_versions"]

    records = []
    summary = {}
    for sw, ver in sw_ver.items():
        rec = sw_to_rec.get(sw)
        if not rec:
            summary[sw] = "skip(no recordId)"
            continue
        records.append({"recordId": rec, "cells": {os_field: ver[:500]}})
        summary[sw] = "queued"

    if not records:
        return summary

    if dry_run:
        print(f"[DRY-RUN] 矩阵表 {table_id} 拟更新 {len(records)} 条:", file=sys.stderr)
        for r in records:
            print(f"  - {r['recordId']}: {list(r['cells'].values())[0]}", file=sys.stderr)
        return summary

    # 单批 ≤30 安全 (本场景 ≤30 软件)
    chunk = 30
    for i in range(0, len(records), chunk):
        sub = records[i:i + chunk]
        result = dws_call([
            "aitable", "record", "update",
            "--base-id", base_id, "--table-id", table_id,
            "--records", json.dumps(sub, ensure_ascii=False),
        ])
        if result and result.get("status") == "success":
            for r in sub:
                # 反查 sw
                for sw, rec in sw_to_rec.items():
                    if rec == r["recordId"]:
                        summary[sw] = "updated"
                        break
        else:
            for r in sub:
                for sw, rec in sw_to_rec.items():
                    if rec == r["recordId"]:
                        summary[sw] = "failed"
                        break
    return summary


def insert_findings(parsed: dict, batch_key: str, dry_run: bool = False) -> dict:
    """跑 risk_rules + probe_gaps, 插入问题表. 返回统计."""
    meta = load_meta()
    base_id = meta["baseId"]
    findings_tab = meta["tables"]["findings"]
    table_id = findings_tab["tableId"]
    F = findings_tab["fields"]

    sw_ver = parsed["software_versions"]
    records = []
    by_level = {"高": 0, "中": 0, "低": 0, "信息": 0}

    for sw, ver in sw_ver.items():
        for f in risk_rules.evaluate(sw, ver):
            records.append({"cells": {
                F["扫描批次"]: batch_key,
                F["软件名称"]: sw,
                F["实测版本"]: ver,
                F["风险等级"]: f["level"],
                F["风险描述"]: f["desc"],
                F["建议动作"]: f["action"],
                F["关联CVE"]: f["cve"],
                F["状态"]: "待处理",
            }})
            by_level[f["level"]] = by_level.get(f["level"], 0) + 1

    # 探测脚本缺陷条目
    for gap in risk_rules.detect_probe_gaps(parsed["merged"]):
        records.append({"cells": {
            F["扫描批次"]: batch_key,
            F["软件名称"]: gap["software"],
            F["实测版本"]: parsed["merged"].get("NACOS_JAR", ""),
            F["风险等级"]: gap["level"],
            F["风险描述"]: gap["desc"],
            F["建议动作"]: gap["action"],
            F["关联CVE"]: gap["cve"],
            F["状态"]: "待处理",
        }})
        by_level[gap["level"]] = by_level.get(gap["level"], 0) + 1

    if not records:
        return {"inserted": 0, **by_level}

    if dry_run:
        print(f"[DRY-RUN] 问题表 {table_id} 拟插入 {len(records)} 条 (批次 {batch_key}):",
              file=sys.stderr)
        for r in records[:5]:
            print(f"  - {r['cells'][F['软件名称']]} / {r['cells'][F['风险等级']]} / "
                  f"{r['cells'][F['风险描述']][:60]}...", file=sys.stderr)
        if len(records) > 5:
            print(f"  ... +{len(records)-5} more", file=sys.stderr)
        return {"inserted": len(records), **by_level, "dry_run": True}

    chunk = 30
    inserted = 0
    for i in range(0, len(records), chunk):
        sub = records[i:i + chunk]
        result = dws_call([
            "aitable", "record", "create",
            "--base-id", base_id, "--table-id", table_id,
            "--records", json.dumps(sub, ensure_ascii=False),
        ])
        if result and result.get("status") == "success":
            inserted += len(sub)

    return {"inserted": inserted, **by_level}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = argparse.ArgumentParser()
    p.add_argument("--input", help="parse_probe.py 输出的 JSON 文件; 不传则从 stdin 读")
    p.add_argument("--batch", help="批次 key, 默认 yyyymmdd-<os_key>")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-matrix", action="store_true", help="只跑 findings 不更新矩阵")
    p.add_argument("--skip-findings", action="store_true", help="只更新矩阵不插 findings")
    args = p.parse_args()

    raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    parsed = json.loads(raw)

    today = dt.datetime.now().strftime("%Y%m%d")
    os_key = parsed.get("os_key", "unknown")
    batch = args.batch or f"{today}-{os_key}"

    out = {"batch": batch, "os_key": os_key, "os_field": parsed.get("os_field")}

    if not args.skip_matrix:
        out["matrix"] = update_matrix(parsed, dry_run=args.dry_run)
    if not args.skip_findings:
        out["findings"] = insert_findings(parsed, batch, dry_run=args.dry_run)

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
