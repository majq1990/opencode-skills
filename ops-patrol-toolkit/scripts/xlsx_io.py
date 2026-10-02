#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小 OOXML (.xlsx) 读写器 —— 纯标准库实现。

读取能力：
  - sharedStrings / inlineStr / 布尔 / 数值 / 日期格式序列号（自动转 "YYYY-MM-DD[ HH:MM:SS]"）
  - 合并单元格：主格值自动填充到区域内空从格（unmerge 语义），显式值不覆盖
写入能力：
  - 生成单工作表 xlsx（inline 字符串 + 数值），可选表头加粗浅底色、列宽

显式边界（不静默吞掉，以 warning 形式随返回值带出）：
  - 公式单元格只取缓存值，无缓存值记 None 并写 warning
  - 错误单元格（#DIV/0! 等）记 None 并写 warning
  - 图表/批注/透视表等非数据内容忽略
  - 不支持老版二进制 .xls
所有函数不打印，warning 一律通过返回值传递。
"""

import re
import zipfile
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL_DOC = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

_COL_RE = re.compile(r"^([A-Z]+)(\d+)$")

# 内置日期/时间格式号（Excel 规范）；自定义格式按格式码内容判定
_BUILTIN_DATE_IDS = {14, 15, 16, 17, 18, 19, 20, 21, 22, 27, 30, 36, 45, 46, 47, 55, 56}


class XlsxError(Exception):
    """xlsx 结构性错误（文件损坏/不是 xlsx/找不到工作表）。"""


def _col_to_idx(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n  # 1-based


def _cell_rc(ref):
    m = _COL_RE.match(ref or "")
    if not m:
        return None, None
    return int(m.group(2)), _col_to_idx(m.group(1))  # row, col（均 1-based）


def _serial_to_datetime(num):
    days = int(num)
    frac = num - days
    if days < 60:
        base = datetime(1900, 1, 1) + timedelta(days=days - 1)
    else:
        base = datetime(1899, 12, 30) + timedelta(days=days)  # 跳过 Excel 假闰日 1900-02-29
    if frac:
        base = base + timedelta(seconds=round(frac * 86400))
    return base


def _parse_shared(zf, warnings):
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except ET.ParseError as e:
        warnings.append("sharedStrings.xml 解析失败: %s" % e)
        return []
    return ["".join(t.text or "" for t in si.iter(NS_MAIN + "t"))
            for si in root.findall(NS_MAIN + "si")]


def _parse_date_styles(zf, warnings):
    """style 索引 -> 是否日期格式。"""
    date_ids = set(_BUILTIN_DATE_IDS)
    custom_date = set()
    if "xl/styles.xml" not in zf.namelist():
        return {}
    try:
        root = ET.fromstring(zf.read("xl/styles.xml"))
    except ET.ParseError as e:
        warnings.append("styles.xml 解析失败: %s" % e)
        return {}
    for nf in root.iter(NS_MAIN + "numFmt"):
        code = nf.get("formatCode") or ""
        stripped = re.sub(r"\[[^\]]*\]|\"[^\"]*\"|\\.", "", code)
        if re.search(r"[yYdDhHsS]", stripped):
            custom_date.add(nf.get("numFmtId"))
    cell_xfs = root.find(NS_MAIN + "cellXfs")
    if cell_xfs is None:
        return {}
    out = {}
    for idx, xf in enumerate(cell_xfs.findall(NS_MAIN + "xf")):
        fid = xf.get("numFmtId")
        if fid is None:
            continue
        if int(fid) in date_ids or fid in custom_date:
            out[idx] = True
    return out


def sheet_names(path):
    """返回工作表名列表（按工作簿顺序）。"""
    with zipfile.ZipFile(path) as zf:
        try:
            wb = ET.fromstring(zf.read("xl/workbook.xml"))
        except (KeyError, ET.ParseError) as e:
            raise XlsxError("不是有效的 xlsx（workbook.xml 缺失或损坏）: %s" % e)
    return [sh.get("name") or "Sheet%d" % (i + 1)
            for i, sh in enumerate(wb.iter(NS_MAIN + "sheet"))]


def _sheet_part(zf, sheet):
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    sheets = list(wb.iter(NS_MAIN + "sheet"))
    if not sheets:
        raise XlsxError("workbook.xml 中没有工作表")
    idx = None
    if sheet is not None:
        for i, sh in enumerate(sheets):
            if sh.get("name") == sheet:
                idx = i
                break
        if idx is None:
            raise XlsxError("找不到工作表: %s（现有: %s）"
                            % (sheet, ",".join(sh.get("name") or "" for sh in sheets)))
    else:
        idx = 0
    rid = sheets[idx].get(NS_REL_DOC + "id")
    part = "xl/worksheets/sheet%d.xml" % (idx + 1)  # 回退猜测
    if rid:
        try:
            rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
            for r in rels:
                if r.get("Id") == rid:
                    target = r.get("Target") or ""
                    if target.startswith("/"):
                        part = target[1:]
                    elif not target.startswith("xl/"):
                        part = "xl/" + target
                    else:
                        part = target
                    break
        except KeyError:
            pass
    return part


def read_rows(path, sheet=None, fill_merged=True, max_rows=None):
    """读一个工作表，返回 (rows, warnings)。

    rows: list[list]，每格为 str/int/float/None；末尾整行为空时裁掉。
    fill_merged: 合并单元格主格值填充到区域内空从格。
    """
    warnings = []
    try:
        zf = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, FileNotFoundError) as e:
        raise XlsxError("无法打开 xlsx %s: %s" % (path, e))
    with zf:
        shared = _parse_shared(zf, warnings)
        date_styles = _parse_date_styles(zf, warnings)
        part = _sheet_part(zf, sheet)
        try:
            root = ET.fromstring(zf.read(part))
        except (KeyError, ET.ParseError) as e:
            raise XlsxError("工作表数据损坏 %s: %s" % (part, e))

        grid = {}
        max_col = 0
        max_row = 0
        for row in root.iter(NS_MAIN + "row"):
            rn = int(row.get("r") or (max_row + 1))
            max_row = max(max_row, rn)
            for c in row.findall(NS_MAIN + "c"):
                ref = c.get("r") or ""
                _, cn = _cell_rc(ref)
                if cn is None:
                    cn = max_col + 1
                max_col = max(max_col, cn)
                val, warn = _cell_value(c, shared, date_styles)
                if warn:
                    warnings.append("%s!%s %s" % (sheet or part, ref or rn, warn))
                grid[(rn, cn)] = val
                if max_rows and rn > max_rows:
                    break

        if fill_merged:
            _apply_merges(root, grid)

        rows = []
        for rn in range(1, max_row + 1):
            row_vals = [grid.get((rn, cn)) for cn in range(1, max_col + 1)]
            rows.append(row_vals)
        while rows and all(v is None or v == "" for v in rows[-1]):
            rows.pop()
    return rows, warnings


def _apply_merges(root, grid):
    mc = root.find(NS_MAIN + "mergeCells")
    if mc is None:
        return
    for m in mc.findall(NS_MAIN + "mergeCell"):
        ref = m.get("ref") or ""
        if ":" not in ref:
            continue
        a, b = ref.split(":", 1)
        r1, c1 = _cell_rc(a)
        r2, c2 = _cell_rc(b)
        if r1 is None or r2 is None:
            continue
        master = grid.get((r1, c1))
        for rr in range(r1, r2 + 1):
            for cc in range(c1, c2 + 1):
                if (rr, cc) != (r1, c1):
                    cur = grid.get((rr, cc))
                    if cur is None or cur == "":
                        grid[(rr, cc)] = master


def _cell_value(c, shared, date_styles):
    """返回 (value, warning或None)。"""
    t = c.get("t")
    if t == "inlineStr":
        is_el = c.find(NS_MAIN + "is")
        if is_el is None:
            return None, None
        return "".join(x.text or "" for x in is_el.iter(NS_MAIN + "t")), None
    v = c.find(NS_MAIN + "v")
    if v is None or v.text is None:
        return None, None
    raw = v.text
    if t == "s":
        try:
            return shared[int(raw)], None
        except (IndexError, ValueError):
            return None, "共享字符串索引越界"
    if t == "b":
        return ("FALSE" if raw in ("0", "") else "TRUE"), None
    if t == "str":
        return raw, None
    if t == "e":
        return None, "错误单元格(%s)" % raw
    try:
        num = float(raw)
    except ValueError:
        return raw, None
    style_idx = c.get("s")
    if style_idx and date_styles.get(int(style_idx)):
        dt = _serial_to_datetime(num)
        if dt.hour or dt.minute or dt.second:
            return dt.strftime("%Y-%m-%d %H:%M:%S"), None
        return dt.strftime("%Y-%m-%d"), None
    if "." not in raw and "e" not in raw.lower() and abs(num) < 1e15:
        return int(num), None
    return num, None


# ---------------------------------------------------------------- 写入

_CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

_ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

_WB_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFDCE6F1"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>
</styleSheet>"""


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _col_name(idx):
    out = ""
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        out = chr(65 + rem) + out
    return out


def write_rows(path, sheet_name, rows, header_bold=True, col_widths=None):
    """写一个单工作表 xlsx。rows 为 list[list]；datetime 自动转 "YYYY-MM-DD HH:MM:SS" 字符串。

    col_widths: {列号(1-based): 字符宽}，可选。
    """
    from datetime import datetime as _dt

    def cell_xml(v, ref, style=None):
        s_attr = ' s="%d"' % style if style else ""
        if v is None or v == "":
            return ""
        if isinstance(v, bool):
            return '<c r="%s" t="inlineStr"%s><is><t>%s</t></is></c>' % (ref, s_attr, _esc("TRUE" if v else "FALSE"))
        if isinstance(v, float):
            return '<c r="%s"%s><v>%s</v></c>' % (ref, s_attr, repr(v))
        if isinstance(v, int):
            return '<c r="%s"%s><v>%d</v></c>' % (ref, s_attr, v)
        if isinstance(v, _dt):
            v = v.strftime("%Y-%m-%d %H:%M:%S")
        return '<c r="%s" t="inlineStr"%s><is><t xml:space="preserve">%s</t></is></c>' % (ref, s_attr, _esc(v))

    max_col = 0
    body = []
    for rn, row in enumerate(rows, 1):
        cells = []
        for cn, v in enumerate(row, 1):
            max_col = max(max_col, cn)
            style = 1 if (header_bold and rn == 1) else None
            xml = cell_xml(v, "%s%d" % (_col_name(cn), rn), style)
            if xml:
                cells.append(xml)
        if cells:
            body.append('<row r="%d">%s</row>' % (rn, "".join(cells)))

    cols = ""
    if col_widths:
        parts = ['<col min="%d" max="%d" width="%s" customWidth="1"/>' % (cn, cn, w)
                 for cn, w in sorted(col_widths.items())]
        cols = "<cols>%s</cols>" % "".join(parts)

    dim = "A1:%s%d" % (_col_name(max(max_col, 1)), max(len(rows), 1))
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             '<dimension ref="%s"/>%s<sheetData>%s</sheetData></worksheet>' % (dim, cols, "".join(body)))

    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<sheets><sheet name="%s" sheetId="1" r:id="rId1"/></sheets></workbook>' % _esc(sheet_name))

    import os
    path = str(path)
    if os.path.splitext(path)[1].lower() != ".xlsx":
        path += ".xlsx"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CT)
        zf.writestr("_rels/.rels", _ROOT_RELS)
        zf.writestr("xl/workbook.xml", wb)
        zf.writestr("xl/_rels/workbook.xml.rels", _WB_RELS)
        zf.writestr("xl/styles.xml", _STYLES)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)
    return path
