#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""01 三源巡查汇总：人巡/机巡/部件 源表 → 统一 9 列明细表（巡查日报标准输入）。

移植自王宝鑫「巡查三源汇总」skill（patrol_parser.py / summary_model.py /
gen_summary_table.py 的解析与领域逻辑），xlsx 读写全部改走自研 xlsx_io
（纯标准库，禁 openpyxl）。

保留的领域规则：
  - 三源均为「日期分块堆叠」反范式表：块标题行 + 字段头行 + 数据行 + 小计行 + 空行
  - 日期只写在块首行，后续同日期行向下继承（合并单元格由 xlsx_io 预先填充）
  - 日期序列号原样保留；源表为日期格式单元格时（xlsx_io 已转为可读串）反推序列号
  - 小计/合计/总计行与空行排除；一条明细一行，不跨源合并去重
  - 字段头不依赖块标题，靠 config.column_signatures 签名定位
    （机巡部分日期块没有标题行，只有重复字段头）
  - 人巡的 巡查视频数量/问题上报总量 属日期级字段，随日期块向下继承，汇入备注列

映射确认机制（移植自「先丢一条样例行让用户确认」）：
  - 不带 --yes：只解析，输出字段映射 + 样例行（written:false），不写任何产物
  - 带 --yes：确认映射并写 xlsx（--csv 同时写 csv，utf-8-sig）
  - --stdout-only：强制只输出预览，即使带了 --yes 也不写

stdout 最后一行 JSON 信封：成功 {"ok":true,...}；失败 {"ok":false,"gap":"..."}
退出码 2（源文件缺失 / 0 条解析 / 映射无法确认）。
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import patrol_lib  # noqa: E402
import xlsx_io  # noqa: E402
from patrol_lib import emit, read_json, stop  # noqa: E402

#: Excel 序列号纪元（1900 日期系统）
EXCEL_EPOCH = date(1899, 12, 30)

#: 小计/合计类行，不计入明细
SUBTOTAL_KEYWORDS = ("合计", "总计", "小计")

#: 分块标题识别（域结构常量，移植自源实现）
RE_BLOCK_TITLE = re.compile(r"^(摄像头人工巡查|摄像头智能巡查|部件使用统计情况)")
#: 部件块标题里的中文日期：部件使用统计情况（2025.1.10）
RE_PART_DATE = re.compile(r"[（(]\s*(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})\s*[)）]")
#: 可读日期串（xlsx_io 已把日期格式单元格转为 "YYYY-MM-DD[ HH:MM:SS]"）
RE_DATE_TEXT = re.compile(
    r"^(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?$")

#: 各来源解析列宽 + 源字段 → 9 列口径映射（供 mapping 信封展示确认）
KIND_SPECS = {
    "人巡": {
        "width": 6,
        "cols": {"date": 0, "video": 1, "total": 2, "ptype": 3, "count": 4, "rate": 5},
        "field_map": {
            "巡查视频时间": "日期序列号+日期(可读)",
            "问题上报类型": "问题/单位",
            "类型数量": "数量",
            "立案率": "比率",
            "问题上报总量": "备注(上报总量)",
            "巡查视频数量": "备注(巡查视频)",
        },
    },
    "机巡": {
        "width": 5,
        "cols": {"date": 0, "ptype": 1, "video": 2, "meet": 3, "rate": 4},
        "field_map": {
            "视频巡查时间": "日期序列号+日期(可读)",
            "问题上报类型": "问题/单位",
            "视频巡查数量": "数量",
            "满足立案标准数量": "达标/立案数",
            "该类的识别准确率": "比率",
        },
    },
    "部件": {
        "width": 2,
        "field_map": {
            "(块标题日期)": "日期(可读)",
            "部门名称": "问题/单位",
            "单位名称": "问题/单位",
            "访问量": "数量",
        },
    },
}

#: 统一 9 列（config.output_columns 缺省时的口径）
DEFAULT_OUTPUT_COLUMNS = ["序号", "数据来源", "日期序列号", "日期(可读)", "问题/单位",
                          "数量", "达标/立案数", "比率", "备注"]

OUT_SHEET = "数据汇总"


# ---------------------------------------------------------------------------
# 单元格工具（移植自 patrol_parser）
# ---------------------------------------------------------------------------

def to_number(value):
    """尽量把单元格值转成数字；失败返回 None。"""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", "")
    if s.endswith("%"):
        try:
            return float(s[:-1]) / 100.0
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def to_int(value):
    n = to_number(value)
    return None if n is None else int(round(n))


def is_subtotal(values):
    """判断一行是否为小计/合计行。"""
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if s in SUBTOTAL_KEYWORDS:
            return True
        if s.startswith("总计") and len(s) <= 6:
            return True
    return False


def is_blank_row(values):
    """整行为空。"""
    return all(v is None or str(v).strip() == "" for v in values)


def serial_to_readable(serial):
    """Excel 序列号 → YYYY-MM-DD；非法返回 None。"""
    if isinstance(serial, bool) or not isinstance(serial, (int, float)) or serial <= 0:
        return None
    try:
        return (EXCEL_EPOCH + timedelta(days=float(serial))).strftime("%Y-%m-%d")
    except (OverflowError, ValueError):
        return None


def parse_chinese_date(text):
    """从「部件使用统计情况（2025.1.10）」里抽出 YYYY-MM-DD。"""
    m = RE_PART_DATE.search(text or "")
    if not m:
        return None
    y, mo, d = (int(g) for g in m.groups())
    return "%04d-%02d-%02d" % (y, mo, d)


def normalize_date_cell(value):
    """日期格 → (序列号, 可读日期)；两者都可能为 None。

    - 数字（Excel 序列号）：原样保留为序列号，可读日期由纪元换算
    - 日期串（xlsx_io 已把日期格式单元格读成 "YYYY-MM-DD"）：反推序列号，两列都不缺
    - 其余（空/普通文本）：(None, None)，调用方保持当前日期块不变
    """
    if value is None or isinstance(value, bool):
        return None, None
    if isinstance(value, (int, float)):
        if value > 0:
            return value, serial_to_readable(value)
        return None, None
    s = str(value).strip()
    m = RE_DATE_TEXT.match(s)
    if not m:
        return None, None
    y, mo, d = (int(g) for g in m.groups()[:3])
    if not 1900 <= y <= 9999:
        return None, None
    try:
        dt = date(y, mo, d)
    except ValueError:
        return None, None
    return (dt - EXCEL_EPOCH).days, dt.strftime("%Y-%m-%d")


def match_signature(row, signatures):
    """返回命中的签名候选；无命中返回 None。

    命中条件：候选里的全部字段名同时出现在本行单元格中；候选按配置顺序尝试。
    """
    cells = {str(v).strip() for v in row if v is not None and str(v).strip() != ""}
    for sig in signatures:
        if sig and all(s in cells for s in sig):
            return sig
    return None


# ---------------------------------------------------------------------------
# 解析器（移植自 patrol_parser.parse_renxun / parse_jixun / parse_bujian）
# ---------------------------------------------------------------------------

def parse_date_kind(rows, kind, signatures, warnings, label):
    """人巡/机巡：日期在 c0 的日期分块堆叠表。

    状态机：字段头签名复位 seen_header；块标题重置 seen_header（其后到下一字段头
    之间的残行一律丢弃）；小计/空行排除；日期写在块首行、后续行向下继承。
    """
    spec = KIND_SPECS[kind]
    width, cols = spec["width"], spec["cols"]
    records = []
    seen_header = False
    header_row = None
    matched_sig = None
    cur = {"serial": None, "readable": None, "video": None, "total": None}
    for i, raw in enumerate(rows, 1):
        vals = list(raw[:width]) + [None] * (width - len(raw))
        if is_blank_row(vals):
            continue
        sig = match_signature(vals, signatures)
        if sig:
            seen_header = True
            if header_row is None:
                header_row, matched_sig = i, sig
            continue
        s0 = "" if vals[0] is None else str(vals[0]).strip()
        if RE_BLOCK_TITLE.match(s0):
            seen_header = False
            continue
        if not seen_header:
            continue
        if is_subtotal(vals):
            continue
        # 日期列有值 → 新日期块，重置日期级字段（人巡的数量/总量随块首行更新）
        if vals[0] is not None and s0 != "":
            serial, readable = normalize_date_cell(vals[0])
            if serial is not None or readable is not None:
                cur = {"serial": serial, "readable": readable, "video": None, "total": None}
                if kind == "人巡":
                    cur["video"] = to_int(vals[cols["video"]])
                    cur["total"] = to_int(vals[cols["total"]])
        ptype = "" if vals[cols["ptype"]] is None else str(vals[cols["ptype"]]).strip()
        if not ptype:
            warnings.append("[%s] 第%d行非空但缺少问题类型，已跳过" % (label, i))
            continue
        rec = {"serial": cur["serial"], "readable": cur["readable"], "ptype": ptype}
        if kind == "人巡":
            rec.update(count=to_int(vals[cols["count"]]),
                       rate=to_number(vals[cols["rate"]]),
                       video=cur["video"], total=cur["total"])
        else:
            rec.update(video=to_int(vals[cols["video"]]),
                       meet=to_int(vals[cols["meet"]]),
                       rate=to_number(vals[cols["rate"]]))
        records.append(rec)
    return records, header_row, matched_sig


def parse_bujian(rows, signatures, warnings, label):
    """部件：日期来自块标题「部件使用统计情况（YYYY.M.D）」，字段头为 部门/单位名称+访问量。"""
    records = []
    cur_date = None
    header_row = None
    matched_sig = None
    for i, raw in enumerate(rows, 1):
        vals = list(raw[:2]) + [None] * (2 - len(raw))
        if is_blank_row(vals):
            continue
        s0 = "" if vals[0] is None else str(vals[0]).strip()
        if s0.startswith("部件使用统计情况"):
            cur_date = parse_chinese_date(s0)
            if cur_date is None:
                warnings.append("[%s] 第%d行块标题「%s」未解析出日期，该块已跳过" % (label, i, s0))
            continue
        sig = match_signature(vals, signatures)
        if sig:
            if header_row is None:
                header_row, matched_sig = i, sig
            continue
        if is_subtotal(vals):
            continue
        if not cur_date:
            continue
        if not s0:
            continue
        records.append({"readable": cur_date, "dept": s0, "visits": to_int(vals[1])})
    return records, header_row, matched_sig


# ---------------------------------------------------------------------------
# 汇总模型（移植自 summary_model.build_summary_rows）
# ---------------------------------------------------------------------------

def build_record_dicts(records_by_kind):
    """三类记录 → 统一 9 列记录字典列表。一条明细一行，不跨源合并去重。"""
    out = []
    seq = 0
    for r in records_by_kind.get("人巡", []):
        seq += 1
        remark = "上报总量%s" % r["total"] if r["total"] is not None else ""
        if r["video"] is not None:
            remark = (remark + "；" if remark else "") + "巡查视频%s" % r["video"]
        out.append({"序号": seq, "数据来源": "人巡",
                    "日期序列号": r["serial"] if r["serial"] is not None else "",
                    "日期(可读)": r["readable"] or "",
                    "问题/单位": r["ptype"],
                    "数量": r["count"] if r["count"] is not None else "",
                    "达标/立案数": "",
                    "比率": r["rate"] if r["rate"] is not None else "",
                    "备注": remark})
    for r in records_by_kind.get("机巡", []):
        seq += 1
        out.append({"序号": seq, "数据来源": "机巡",
                    "日期序列号": r["serial"] if r["serial"] is not None else "",
                    "日期(可读)": r["readable"] or "",
                    "问题/单位": r["ptype"],
                    "数量": r["video"] if r["video"] is not None else "",
                    "达标/立案数": r["meet"] if r["meet"] is not None else "",
                    "比率": r["rate"] if r["rate"] is not None else "",
                    "备注": ""})
    for r in records_by_kind.get("部件", []):
        seq += 1
        out.append({"序号": seq, "数据来源": "部件",
                    "日期序列号": "",
                    "日期(可读)": r["readable"] or "",
                    "问题/单位": r["dept"],
                    "数量": r["visits"] if r["visits"] is not None else "",
                    "达标/立案数": "",
                    "比率": "",
                    "备注": ""})
    return out


def project(records, columns):
    """按配置的输出列顺序投影（列名不在记录里的补空串）。"""
    return [[rec.get(c, "") for c in columns] for rec in records]


# ---------------------------------------------------------------------------
# 源表读取
# ---------------------------------------------------------------------------

def read_csv_rows(path):
    """读 csv 源（utf-8-sig），返回字符串行列表。"""
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return [list(r) for r in csv.reader(f)]


def read_source_rows(path, sheet_name, label, warnings):
    """读源表；xlsx 走 xlsx_io（sheet 为空时取第一个非空 Sheet），csv 走内置读取。

    xlsx_io 的告警（公式无缓存值/错误单元格等）带前缀收进 warnings。
    """
    if path.suffix.lower() == ".csv":
        return read_csv_rows(str(path)), "(csv)"
    if sheet_name:
        rows, w = xlsx_io.read_rows(str(path), sheet=sheet_name)
        warnings.extend("[%s] %s" % (label, x) for x in w)
        return rows, sheet_name
    names = xlsx_io.sheet_names(str(path))
    rows, chosen = [], None
    for name in names:
        r, w = xlsx_io.read_rows(str(path), sheet=name)
        warnings.extend("[%s] %s" % (label, x) for x in w)
        if any(not is_blank_row(rw) for rw in r):
            return r, name
        rows = r
    if len(names) > 1:
        warnings.append("[%s] 所有 Sheet 均为空，按第一个 Sheet「%s」处理" % (label, names[0]))
    return rows, names[0]


def resolve_source_path(raw, base_dir):
    """配置里的源路径：绝对路径直用，相对路径相对配置文件所在目录。"""
    p = Path(str(raw)).expanduser()
    if not p.is_absolute():
        p = base_dir / p
    return p


def write_csv_file(path, columns, body):
    p = Path(str(path)).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(columns)
        w.writerows(body)
    return p


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="人巡/机巡/部件 三源巡查 Excel/CSV → 统一 9 列明细表")
    ap.add_argument("--config", required=True, help="sources.json 配置路径")
    ap.add_argument("--out", default=None, help="输出 xlsx 路径（--yes 时必填）")
    ap.add_argument("--csv", dest="csv_out", default=None, help="同时输出 csv 路径（utf-8-sig）")
    ap.add_argument("--yes", action="store_true", help="确认字段映射并写产物")
    ap.add_argument("--stdout-only", action="store_true", help="只输出预览，不写产物")
    args = ap.parse_args(argv)

    cfg = read_json(args.config)
    base_dir = Path(args.config).resolve().parent

    sources = cfg.get("sources")
    if not isinstance(sources, list) or not sources:
        stop("配置缺少 sources 列表或为空: %s" % args.config)
    signatures = cfg.get("column_signatures") or {}
    columns = cfg.get("output_columns") or DEFAULT_OUTPUT_COLUMNS

    warnings = []
    per_source = {}
    mapping = {}
    records_by_kind = {"人巡": [], "机巡": [], "部件": []}
    first_by_label = {}

    for src in sources:
        kind = src.get("kind")
        if kind not in KIND_SPECS:
            stop("不支持的来源类型「%s」（应为 人巡/机巡/部件 之一）" % kind)
        label = src.get("label") or kind
        raw_path = src.get("path")
        if not raw_path:
            stop("来源[%s]缺少 path 配置" % kind)
        path = resolve_source_path(raw_path, base_dir)
        if not path.is_file():
            stop("源文件不存在: %s（来源[%s]）——请核对配置的 path" % (path, kind))
        sigs = signatures.get(kind)
        if not sigs:
            stop("配置缺少来源[%s]的表头签名 column_signatures.%s" % (kind, kind))
        try:
            rows, used_sheet = read_source_rows(path, src.get("sheet"), label, warnings)
        except xlsx_io.XlsxError as exc:
            stop("源文件无法读取 [%s] %s: %s" % (kind, path, exc))
        if kind == "部件":
            records, header_row, matched = parse_bujian(rows, sigs, warnings, label)
        else:
            records, header_row, matched = parse_date_kind(rows, kind, sigs, warnings, label)
        if header_row is None:
            warnings.append("[%s] 未命中任何表头签名（候选: %s）" % (label, sigs))
        records_by_kind[kind].extend(records)
        per_source[label] = len(records)
        mapping[label] = {
            "kind": kind,
            "file": str(path),
            "sheet": used_sheet,
            "header_row": header_row,
            "signature": matched,
            "field_map": KIND_SPECS[kind]["field_map"],
            "rows": len(records),
        }
        if records and label not in first_by_label:
            first_by_label[label] = records[0]

    for lb, rec in first_by_label.items():
        mapping[lb]["sample"] = build_record_dicts({mapping[lb]["kind"]: [rec]})[0]

    detail = build_record_dicts(records_by_kind)
    total = len(detail)
    write_mode = bool(args.yes) and not args.stdout_only

    if total == 0:
        stop("解析结果为 0 条：请核对源表结构（字段头签名不匹配或表内无明细行）",
             per_source=per_source, warnings=warnings)
    if write_mode:
        unconfirmed = [lb for lb, m in mapping.items() if m["header_row"] is None]
        if unconfirmed:
            stop("映射无法确认：%s 未命中任何表头签名，请核对 column_signatures 与源表字段头"
                 % "、".join(unconfirmed))
        if not args.out:
            stop("带 --yes 写产物需要 --out 路径")

    payload = {
        "ok": True,
        "written": False,
        "rows": total,
        "per_source": per_source,
        "mapping": mapping,
        "sample_row": detail[0] if detail else None,
        "warnings": warnings,
        "output_columns": columns,
    }

    if write_mode:
        out_path = Path(str(args.out)).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        body = project(detail, columns)
        xlsx_io.write_rows(str(out_path), OUT_SHEET, [columns] + body,
                           header_bold=True,
                           col_widths={1: 8, 2: 10, 3: 12, 4: 14, 5: 26,
                                       6: 10, 7: 14, 8: 10, 9: 30})
        payload["written"] = True
        payload["output"] = str(out_path.resolve())
        print("已写出: %s（%d 行明细）" % (out_path, total))
        if args.csv_out:
            csv_path = write_csv_file(args.csv_out, columns, body)
            payload["csv_output"] = str(csv_path.resolve())
            print("已写出: %s（csv）" % csv_path)
    else:
        print("[预览] 未带 --yes，不写产物；请核对字段映射与样例行后，再带 --yes 执行")

    emit(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
