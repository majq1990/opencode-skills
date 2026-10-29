#!/usr/bin/env python3
"""督办调整入口：把「随口一说」的督办需求，翻译成一次最小改动的批量提交。

只管三件事：督办完成日期、督办状态变更、备注。其它字段一律不碰。

输入格式（每条案件一组，字段用逗号 / 中文逗号 / 竖线 / Tab 分隔，顺序固定）：

    案件号, 新的督办完成日期, 新的督办状态, 备注(可选)

- 案件号：必填，支持纯数字或案件 URL
- 新的督办完成日期：YYYY-MM-DD；也接受 2026/10/15、2026.10.15、
  2026-10-15 00:00:00（带时间会自动截成日期）
- 新的督办状态：督办延期 / 取消督办 / 无，留空按 --default-state 处理
- 备注：可选，只填备注不填日期也行

备注（opinion）自动按规则拼：**原备注 + 操作说明**

| 输入 | 最终备注 |
|---|---|
| 备注「改造范围较多」+ 延期到 2026-10-15 | 改造范围较多，督办延期至2026-10-15 |
| 备注为空 + 延期到 2026-10-15 | 督办延期至2026-10-15 |
| 备注「超期自动督办任务」+ 取消 | 超期自动督办任务，取消督办 |

用示例
------

    # 命令行直接给（每条一个 --case）
    python3 duban_adjust.py \
      --case "526984, 2026-10-15, 督办延期, 改造范围较多" \
      --case "526273, , 取消督办, 超期自动督办任务" \
      --dry-run

    # 或写成文本文件，一行一条
    python3 duban_adjust.py --input cases.txt --dry-run

    # 确认无误后执行（提交前还会再问一次）
    python3 duban_adjust.py --input cases.txt --yes

    # 只想生成 CSV，不提交（拿去改或存档）
    python3 duban_adjust.py --input cases.txt --print-only

遇到 422「XX 不是合法日期」时加 --fix-dirty-dates 重跑，见 SKILL.md。
"""

import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ENGINE = SCRIPT_DIR / "issue_case_batch_update.py"

CF_DUBAN_DONE = "custom_field_335"    # 督办完成日期
CF_DUBAN_STATE = "custom_field_346"   # 督办状态变更
CLEAR_MARK = "#clear"

STATE_DELAY = "督办延期"
STATE_CANCEL = "取消督办"
STATE_NONE = "无"
VALID_STATES = (STATE_DELAY, STATE_CANCEL, STATE_NONE)

# 状态同义词 → 标准值
STATE_ALIASES = {
    "延期": STATE_DELAY, "督办延期": STATE_DELAY, "推迟": STATE_DELAY,
    "取消": STATE_CANCEL, "取消督办": STATE_CANCEL,
    "无": STATE_NONE, "不延期": STATE_NONE, "": "",
}

DATE_RE = re.compile(r"(\d{4})\s*[-/.年]\s*(\d{1,2})\s*[-/.月]\s*(\d{1,2})")


def normalize_date(raw: str) -> str | None:
    """把各种写法的日期归一成 YYYY-MM-DD；带时间的一并截掉。"""
    raw = (raw or "").strip()
    if not raw:
        return None
    m = DATE_RE.search(raw)
    if not m:
        return None
    y, mo, d = m.groups()
    return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"


def normalize_state(raw: str, default: str) -> str:
    key = (raw or "").strip().replace(" ", "")
    if key in STATE_ALIASES:
        return STATE_ALIASES[key] or default
    # 没识别出来就原样带上，交给 Redmine 校验
    return key or default


def parse_line(line: str, lineno: int) -> dict:
    parts = [p.strip() for p in re.split(r"[,，|\t]", line.strip())]
    while len(parts) < 4:
        parts.append("")
    case_id, date_raw, state_raw, note = parts[0], parts[1], parts[2], parts[3]
    # parts[3] 之后还有内容 → 说明备注里带了英文逗号，拼回去
    rest = parts[4:]
    if rest:
        note = "，".join([note] + rest)

    if not case_id:
        raise ValueError(f"第 {lineno} 行缺少案件号")
    if not note and state_raw and not date_raw:
        # `123, , 督办延期` 这种把状态写在第 3 列的情况已覆盖；空备注保持空
        pass
    return {"case_id": case_id, "date_raw": date_raw, "state_raw": state_raw, "note": note}


def collect_rows(args) -> list[dict]:
    rows: list[dict] = []
    if args.input:
        text = Path(args.input).read_text(encoding="utf-8-sig")
        for i, line in enumerate(text.splitlines(), 1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            rows.append(parse_line(s, i))
    for raw in args.case or []:
        rows.append(parse_line(raw, 0))
    if not rows:
        raise SystemExit("❌ 没有读到任何案件。用 --case 或 --input 给一条试试。")
    return rows


def build_record(row: dict, default_state: str) -> dict:
    case_id = row["case_id"].strip()
    m = re.search(r"/issues/(\d+)", case_id)
    if m:
        case_id = m.group(1)
    if not case_id.isdigit():
        raise SystemExit(f"❌ 案件号不合法：{row['case_id']}")

    date = normalize_date(row["date_raw"])
    state = normalize_state(row["state_raw"], default_state)
    note = row["note"].strip()

    if state not in VALID_STATES:
        raise SystemExit(
            f"❌ 案件 {case_id} 的督办状态「{state}」不认识。"
            f"可用：{' / '.join(VALID_STATES)}"
        )
    if row["date_raw"] and not date:
        raise SystemExit(f"❌ 案件 {case_id} 的日期「{row['date_raw']}」不是合法日期（需要 YYYY-MM-DD）")
    if state == STATE_DELAY and not date:
        raise SystemExit(f"❌ 案件 {case_id} 是「督办延期」但没给新的督办完成日期")

    # 备注 = 原备注 + 操作说明
    if state == STATE_DELAY:
        op = f"督办延期至{date}"
    elif state == STATE_CANCEL:
        op = "取消督办"
    else:
        op = ""
    opinion = f"{note}，{op}" if note and op else (note or op)
    if not opinion:
        opinion = f"督办状态调整为{state}"

    rec = {"case_id": case_id, "opinion": opinion, CF_DUBAN_STATE: state}
    if state == STATE_DELAY:
        rec[CF_DUBAN_DONE] = date
    elif state == STATE_CANCEL:
        rec[CF_DUBAN_DONE] = CLEAR_MARK      # 取消督办要清空完成日期
    elif date:
        rec[CF_DUBAN_DONE] = date
    return rec


def main() -> None:
    parser = argparse.ArgumentParser(
        description="督办调整：案件号 + 新督办完成日期 + 新督办状态 + 备注(可选)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--case", action="append", metavar="'案件号,日期,状态,备注'",
                        help="一条案件，可重复多次")
    parser.add_argument("--input", help="文本文件，一行一条（# 开头为注释）")
    parser.add_argument("--default-state", default=STATE_DELAY,
                        help=f"没写状态时默认用哪个（默认 {STATE_DELAY}）")
    parser.add_argument("--csv-out", help="生成的 CSV 路径（默认写到 /tmp）")
    parser.add_argument("--print-only", action="store_true", help="只生成 CSV 并打印，不提交")
    parser.add_argument("--dry-run", action="store_true", help="联网预览 from→to，不提交")
    parser.add_argument("--yes", action="store_true", help="跳过提交前的人工确认")
    parser.add_argument("--fix-dirty-dates", action="store_true",
                        help="顺带修复 date 字段的脏值（带时间的），解决 422")
    args = parser.parse_args()

    rows = collect_rows(args)
    records = [build_record(r, args.default_state) for r in rows]

    out = Path(args.csv_out) if args.csv_out else Path(f"/tmp/duban-{time.strftime('%Y%m%d-%H%M%S')}.csv")
    cols = ["case_id", "opinion", CF_DUBAN_DONE, CF_DUBAN_STATE]
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in records:
            w.writerow(r)

    print(f"📋 共 {len(records)} 条，已生成：{out}\n")
    for r in records:
        date = r.get(CF_DUBAN_DONE, "-")
        date = "（清空）" if date == CLEAR_MARK else date
        print(f"  #{r['case_id']}  {r[CF_DUBAN_STATE]:<6} 督办完成日期={date}")
        print(f"      备注：{r['opinion']}")

    if args.print_only:
        print("\nℹ️  --print-only：未提交。")
        return

    cmd = [sys.executable, str(ENGINE), "--input", str(out), "--update-only"]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.yes:
        cmd.append("--yes")
    if args.fix_dirty_dates:
        cmd.append("--fix-dirty-dates")

    print(f"\n▶️  调用批量引擎（只改督办相关字段）：\n   {' '.join(cmd)}\n")
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        print("\n⚠️  有案件没成功。若报「XX 不是合法日期 / 不是合法字符串」，"
              "加 --fix-dirty-dates 重跑即可；详见 SKILL.md「422 怎么处理」。")
    raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
