"""一条命令跑完 6 步：python -m scripts.main path/to/plan.json [--from-step N] [--to-step N]

Steps:
  1 fetch_projects        ztoa 拉打开+在职 PM 项目
  2 resolve_pms           PM 姓名→钉钉 userId（部门去歧）
  3 fetch_langya          琅琊榜映射（include_engineering_leads=true 才跑）
  4 create_table          建 base + table + 字段 + 单选 options
  5 push_records          批量插记录
  6 fill_eng_leads        回填大区工程总+省份工程总（include_engineering_leads=true 才跑）

支持中断恢复：每步把中间结果落 work_dir/，重跑跳过已完成。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts import (
    step01_fetch_projects, step02_resolve_pms, step03_fetch_langya,
    step04_create_table, step05_push_records, step06_fill_engineering_leads,
)
from scripts._common import load_plan

STEPS = [
    ("fetch_projects", step01_fetch_projects.main),
    ("resolve_pms", step02_resolve_pms.main),
    ("fetch_langya", step03_fetch_langya.main),
    ("create_table", step04_create_table.main),
    ("push_records", step05_push_records.main),
    ("fill_eng_leads", step06_fill_engineering_leads.main),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan", help="path to plan.json")
    ap.add_argument("--from-step", type=int, default=1)
    ap.add_argument("--to-step", type=int, default=len(STEPS))
    args = ap.parse_args()

    plan = load_plan(args.plan)
    print(f"=== plan: {plan['topic']} ===")
    print(f"=== work_dir: {plan['work_dir']} ===\n")

    for i, (name, fn) in enumerate(STEPS, 1):
        if i < args.from_step or i > args.to_step:
            print(f"[skip] step {i} ({name})")
            continue
        print(f"\n>>> Step {i}/{len(STEPS)}: {name}")
        fn(plan)


if __name__ == "__main__":
    main()
