"""Step 5：把 projects_with_userids.json 批量插到 dws AI 表格。

每条 record:
  cells = {
    项目: ..., 大区: ..., 区域: ..., 项目经理: [{userId:..}],
    反馈状态: "未反馈"
  }
分批 20 条/批（Windows 命令行 ~32K 限制）。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts import _config as cfg
from scripts._common import call_dws, dws_ok, work_path

BATCH = 20


def main(plan: dict) -> dict:
    meta = json.loads(work_path(plan, "table_meta.json").read_text(encoding="utf-8"))
    base_id, table_id = meta["baseId"], meta["tableId"]
    name_to_id = meta["fields"]
    f_proj = name_to_id["项目"]
    f_daqu = name_to_id["大区"]
    f_qu = name_to_id["区域"]
    f_pm = name_to_id["项目经理"]
    f_fb_status = name_to_id["反馈状态"]
    f_note = name_to_id.get("反馈备注")
    initial_fb = (plan.get("feedback_status_options") or ["未反馈"])[0]

    projects = json.loads(work_path(plan, "projects_with_userids.json").read_text(encoding="utf-8"))
    records = []
    for p in projects:
        cells = {
            f_proj: p["项目"],
            f_qu: p["区域"],
            f_fb_status: initial_fb,
        }
        if p["大区"] in cfg.VALID_DAQU_SET:
            cells[f_daqu] = p["大区"]
        if p["dingtalk_userids"]:
            cells[f_pm] = [{"userId": u} for u in p["dingtalk_userids"]]
        elif f_note and p.get("pm_match_note"):
            cells[f_note] = p["pm_match_note"]
        records.append({"cells": cells})

    print(f"[step5] pushing {len(records)} records in batches of {BATCH}...")
    success = fail = 0
    for i in range(0, len(records), BATCH):
        b = records[i: i + BATCH]
        payload = json.dumps(b, ensure_ascii=False)
        d, out, err = call_dws(["aitable", "record", "create", "--base-id", base_id, "--table-id", table_id, "-y", "--records", payload], timeout=120)
        if dws_ok(d):
            n = len((d.get("data") or {}).get("newRecordIds") or [])
            success += n
            print(f"  batch {i // BATCH + 1}: +{n}")
        else:
            fail += len(b)
            err_msg = (d or {}).get("error") or out[:200]
            print(f"  batch {i // BATCH + 1}: FAIL {err_msg}")
            (work_path(plan, f"push_err_batch_{i // BATCH + 1:02d}.json")).write_text(payload, encoding="utf-8")
        time.sleep(0.2)
    print(f"[done] success={success}  fail={fail}")
    return {"success": success, "fail": fail}


if __name__ == "__main__":
    from scripts._common import load_plan
    main(load_plan(sys.argv[1]))
