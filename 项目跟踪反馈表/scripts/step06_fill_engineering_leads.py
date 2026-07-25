"""Step 6：按 (大区, 区域) 联合键，把大区工程总 + 省份工程总回填到已写入的 records。

不依赖 step5 返回的 newRecordIds，重新 query 全表 → 按 (项目, 大区, 区域) 索引匹配。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts._common import call_dws, cell_to_text, dws_ok, work_path

BATCH = 20


def fetch_all_records(base_id: str, table_id: str) -> list[dict]:
    all_recs, cursor = [], ""
    while True:
        args = ["aitable", "record", "query", "--base-id", base_id, "--table-id", table_id, "--limit", "100", "-y"]
        if cursor:
            args += ["--cursor", cursor]
        d, out, err = call_dws(args, timeout=60)
        if not dws_ok(d):
            print(f"  query fail: {out[:200]}")
            break
        recs = (d.get("data") or {}).get("records") or []
        all_recs.extend(recs)
        cursor = (d.get("data") or {}).get("nextCursor") or ""
        if not cursor:
            break
    return all_recs


def main(plan: dict) -> dict:
    if not plan.get("include_engineering_leads", True):
        print("[step6] include_engineering_leads=False，跳过")
        return {"updated": 0}

    meta = json.loads(work_path(plan, "table_meta.json").read_text(encoding="utf-8"))
    base_id, table_id = meta["baseId"], meta["tableId"]
    name_to_id = meta["fields"]
    f_proj = name_to_id["项目"]
    f_daqu = name_to_id["大区"]
    f_qu = name_to_id["区域"]
    f_d_eng = name_to_id["大区工程总"]
    f_p_eng = name_to_id["省份工程总"]

    mapping = json.loads(work_path(plan, "langya_mapping.json").read_text(encoding="utf-8"))

    print(f"[step6] fetching all records from table...")
    records = fetch_all_records(base_id, table_id)
    print(f"  records: {len(records)}")

    updates = []
    miss = 0
    for r in records:
        cells = r.get("cells") or {}
        proj = cell_to_text(cells, f_proj)
        daqu = cell_to_text(cells, f_daqu)
        qu = cell_to_text(cells, f_qu)
        if not proj:
            continue
        m = mapping.get(f"{daqu}|{qu}")
        if not m:
            miss += 1
            continue
        c = {}
        if m.get("大区工程总_userids"):
            c[f_d_eng] = [{"userId": u} for u in m["大区工程总_userids"]]
        if m.get("省份工程总_userids"):
            c[f_p_eng] = [{"userId": u} for u in m["省份工程总_userids"]]
        if c:
            updates.append({"recordId": r.get("recordId"), "cells": c})
    print(f"  to update: {len(updates)}  not in langya: {miss}")

    success = fail = 0
    for i in range(0, len(updates), BATCH):
        b = updates[i: i + BATCH]
        d, out, err = call_dws(["aitable", "record", "update", "--base-id", base_id, "--table-id", table_id, "-y", "--records", json.dumps(b, ensure_ascii=False)], timeout=120)
        if dws_ok(d):
            success += len(b)
            print(f"  batch {i // BATCH + 1}: +{len(b)}")
        else:
            fail += len(b)
            print(f"  batch {i // BATCH + 1}: FAIL {(d or {}).get('error') or out[:200]}")
        time.sleep(0.2)
    print(f"[done] updated={success}  fail={fail}")
    return {"updated": success, "fail": fail, "miss_in_langya": miss}


if __name__ == "__main__":
    from scripts._common import load_plan
    main(load_plan(sys.argv[1]))
