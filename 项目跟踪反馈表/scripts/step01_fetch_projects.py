"""Step 1：从 ztoa「交付项目」表拉行，过滤项目状态=='打开' + 至少 1 名在职 PM。

输出 work_dir/projects.json，结构：
[
  {
    "ztoa_row_id": "...", "项目": "...", "大区": "...", "区域": "...",
    "pm_names": ["..."], "pm_account_ids": ["..."]
  }, ...
]
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts import _config as cfg
from scripts._common import (
    cell_to_text, make_ztoa_client, parse_user_cell, run_async, work_path,
)


async def _fetch_all_rows():
    c = make_ztoa_client()
    try:
        rows, page = [], 1
        while True:
            r = await c.query_records(cfg.WS_DELIVERY, page_size=200, page_index=page)
            chunk = (r.get("data") or {}).get("rows") or []
            if not chunk:
                break
            rows.extend(chunk)
            if len(chunk) < 200:
                break
            page += 1
            if page > 30:
                break
        return rows
    finally:
        await c.aclose()


def main(plan: dict) -> Path:
    print("[step1] fetching ztoa delivery projects...")
    rows = run_async(_fetch_all_rows())
    print(f"  total rows fetched: {len(rows)}")

    out = []
    skipped_status = skipped_no_pm = 0
    for r in rows:
        if cell_to_text(r, cfg.F_PROJ_STATUS) != cfg.PROJ_STATUS_OPEN_VALUE:
            skipped_status += 1
            continue
        pms = parse_user_cell(r.get(cfg.F_PROJ_PM))
        active = [p for p in pms if p.get("status") in (1, "1") and p.get("accountId")]
        if not active:
            skipped_no_pm += 1
            continue
        out.append({
            "ztoa_row_id": r.get("rowid") or r.get("rowId"),
            "项目": cell_to_text(r, cfg.F_PROJ_NAME),
            "大区": cell_to_text(r, cfg.F_PROJ_DAQU_SEL) or cell_to_text(r, cfg.F_PROJ_DAQU_TXT),
            "区域": cell_to_text(r, cfg.F_PROJ_QUYU) or cell_to_text(r, cfg.F_PROJ_QUYU_TXT),
            "pm_names": [(p.get("fullname") or "").strip() for p in active if (p.get("fullname") or "").strip()],
            "pm_account_ids": [p.get("accountId") for p in active],
        })
    print(f"  filtered: status_skip={skipped_status}  no_pm_skip={skipped_no_pm}")
    print(f"  open + active PM: {len(out)}")

    p = work_path(plan, "projects.json")
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {p}")
    return p


if __name__ == "__main__":
    from scripts._common import load_plan
    plan = load_plan(sys.argv[1])
    main(plan)
