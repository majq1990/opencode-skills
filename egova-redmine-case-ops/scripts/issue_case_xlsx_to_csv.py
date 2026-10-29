#!/usr/bin/env python3
"""把督办遗留任务 xlsx 转成 batch_update.py 的 CSV 输入格式。

典型输入：领导/PM 给的一份督办任务 Excel 表格
输出：UTF-8 with BOM 的 CSV，可直接喂给：
  python3 issue_case_batch_update.py --input <output.csv> --update-only --dry-run

智能识别"混合列"：xlsx 的"调整完成日期"列里既可能是 YYYY-MM-DD 日期，
也可能是"取消督办"字符串——脚本自动判断生成正确的 CSV。

备注（opinion）组装规则：**表格备注 + 实际进行的操作**
  - 延期：`<表格备注>，督办延期至<YYYY-MM-DD>`
  - 取消：`<表格备注>，取消督办`
  - 表格备注为空时只写操作部分；加 `--raw-opinion` 可退回「只用表格备注原文」。
  例：备注「改造范围较多，预留研发和测试时间不够」+ 延期到 2026-10-15
      → 「改造范围较多，预留研发和测试时间不够，督办延期至2026-10-15」

依赖：openpyxl（用 uv run --with openpyxl 跑，或先 pip install openpyxl）

示例：
  # 默认列名（本团队督办任务表的标准格式）
  python3 issue_case_xlsx_to_csv.py \\
    --input "督办遗留任务.xlsx" \\
    --output duban.csv

  # 自定义列名映射（其它来源的 xlsx）
  python3 issue_case_xlsx_to_csv.py \\
    --input other.xlsx --output duban.csv \\
    --column-case-id "案卷号" \\
    --column-opinion "调整原因" \\
    --column-new-duban "新督办日期"
"""

import argparse
import csv
import sys
from pathlib import Path

try:
    import openpyxl
except ModuleNotFoundError:
    print(
        "❌ 缺依赖 openpyxl。请用以下任一方式安装：",
        file=sys.stderr,
    )
    print(
        "   uv run --with openpyxl python3 issue_case_xlsx_to_csv.py ...",
        file=sys.stderr,
    )
    print(
        "   pip install openpyxl",
        file=sys.stderr,
    )
    sys.exit(1)


# 督办任务表的标准列名
DEFAULT_COL_CASE_ID = "#"
DEFAULT_COL_OPINION = "备注"
DEFAULT_COL_NEW_DUBAN = "调整完成日期"
DEFAULT_COL_OLD_DUBAN_DONE = "督办完成日期"
DEFAULT_COL_CF334 = "督办排期日期"
DEFAULT_COL_DUE_DATE = "计划完成日期"
DEFAULT_CANCEL_VALUE = "取消督办"
DEFAULT_DELAY_VALUE = "督办延期"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="把督办 xlsx 转成 batch_update.py 的 CSV 输入",
    )
    parser.add_argument("--input", required=True, help="xlsx 文件路径")
    parser.add_argument("--output", required=True, help="输出 CSV 路径")
    parser.add_argument("--column-case-id", default=DEFAULT_COL_CASE_ID,
                        help=f"案卷 ID 列名（默认 '{DEFAULT_COL_CASE_ID}'）")
    parser.add_argument("--column-opinion", default=DEFAULT_COL_OPINION,
                        help=f"批转意见列名（默认 '{DEFAULT_COL_OPINION}'）")
    parser.add_argument("--column-new-duban", default=DEFAULT_COL_NEW_DUBAN,
                        help=f"新督办日期列名（默认 '{DEFAULT_COL_NEW_DUBAN}'）")
    parser.add_argument("--column-old-duban-done", default=DEFAULT_COL_OLD_DUBAN_DONE,
                        help=f"原督办完成日期列名（默认 '{DEFAULT_COL_OLD_DUBAN_DONE}'，可选）")
    parser.add_argument("--column-cf334", default=DEFAULT_COL_CF334,
                        help=f"督办排期日期列名（默认 '{DEFAULT_COL_CF334}'，可选）")
    parser.add_argument("--column-due-date", default=DEFAULT_COL_DUE_DATE,
                        help=f"计划完成日期列名（默认 '{DEFAULT_COL_DUE_DATE}'，可选）")
    parser.add_argument("--cancel-value", default=DEFAULT_CANCEL_VALUE,
                        help=f"取消标记值（默认 '{DEFAULT_CANCEL_VALUE}'）")
    parser.add_argument("--delay-value", default=DEFAULT_DELAY_VALUE,
                        help=f"延期标记值（默认 '{DEFAULT_DELAY_VALUE}'）")
    parser.add_argument("--raw-opinion", action="store_true",
                        help="opinion 只用表格备注原文，不追加实际操作（默认会拼成「备注，督办延期至X」/「备注，取消督办」）")
    parser.add_argument("--minimal", action="store_true",
                        help="只输出督办两个字段（cf335/cf346），不带表格里的督办排期日期/计划完成日期，改动面最小")
    return parser.parse_args()


def _cell_to_str(c) -> str:
    """把 xlsx 单元格值转字符串：None/空→''，数字直接 str()，其他 str().strip()。"""
    if c is None:
        return ""
    if isinstance(c, str):
        return c.strip()
    return str(c).strip()


def load_xlsx_rows(xlsx_path: Path) -> tuple[list[str], list[tuple]]:
    """读 xlsx 第一张 sheet，返回 (列头, 数据行)。"""
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise SystemExit(f"xlsx 完全空：{xlsx_path}")
    header = [_cell_to_str(c) for c in rows[0]]
    data = list(rows[1:])
    # 过滤完全空行
    data = [r for r in data if any(_cell_to_str(c) for c in r)]
    return header, data


def normalize_date(val) -> str:
    """从 datetime/字符串提取 YYYY-MM-DD 部分。空值返回空串。"""
    if val is None:
        return ""
    s = str(val).strip()
    if not s:
        return ""
    # openpyxl 读日期单元格可能是 datetime 对象，自动转 str
    return s[:10]


def main() -> None:
    args = parse_args()
    src = Path(args.input)
    if not src.exists():
        raise SystemExit(f"xlsx 文件不存在：{src}")
    out_path = Path(args.output)

    header, data = load_xlsx_rows(src)
    col_idx = {name: i for i, name in enumerate(header)}

    # 校验必需列存在
    required = {
        args.column_case_id: "案卷 ID",
        args.column_opinion: "批转意见",
        args.column_new_duban: "新督办日期",
    }
    missing = [f"'{k}'（{v}）" for k, v in required.items() if k not in col_idx]
    if missing:
        raise SystemExit(
            f"xlsx 缺少必需列：{'; '.join(missing)}\n"
            f"  实际列头：{header}\n"
            f"  用 --column-* 参数指定列名映射"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cancel_count = 0
    delay_count = 0
    with out_path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.writer(fp)
        header_cols = ["case_id", "opinion", "custom_field_335", "custom_field_346"]
        if not args.minimal:
            header_cols += ["custom_field_334", "due_date"]
        header_cols.append("_note")  # 内部列：脚本读完会忽略，便于人工 review
        writer.writerow(header_cols)
        for row in data:
            case_id = _cell_to_str(row[col_idx[args.column_case_id]])
            opinion = _cell_to_str(row[col_idx[args.column_opinion]])
            new_duban_raw = _cell_to_str(row[col_idx[args.column_new_duban]])

            if new_duban_raw == args.cancel_value:
                cf335 = "#clear"
                cf346 = args.cancel_value
                flag = "CANCEL"
                action = args.cancel_value
                cancel_count += 1
            else:
                cf335 = normalize_date(new_duban_raw)
                cf346 = args.delay_value
                flag = f"延期→{cf335}"
                action = f"督办延期至{cf335}" if cf335 else args.delay_value
                delay_count += 1

            # 备注规则：表格备注 + 实际进行的操作（如「…，督办延期至2026-10-15」）
            if not args.raw_opinion:
                opinion = f"{opinion}，{action}" if opinion else action

            # 可选列：缺则留空；--minimal 时一律不输出，保证只动督办字段
            row_out = [case_id, opinion, cf335, cf346]
            if not args.minimal:
                cf334 = ""
                if args.column_cf334 in col_idx:
                    cf334 = normalize_date(row[col_idx[args.column_cf334]])
                due = ""
                if args.column_due_date in col_idx:
                    due = normalize_date(row[col_idx[args.column_due_date]])
                row_out += [cf334, due]
            row_out.append(flag)

            writer.writerow(row_out)

    print(f"✅ 输出 {out_path}：延期 {delay_count} 条 + 取消 {cancel_count} 条 = {delay_count + cancel_count} 条")
    print("   备注规则：表格备注 + 实际操作（--raw-opinion 可关闭）")
    print("   字段范围：" + ("仅督办完成日期 + 督办状态变更（--minimal）"
                         if args.minimal else "督办两个字段 + 督办排期日期 + 计划完成日期"))


if __name__ == "__main__":
    main()
