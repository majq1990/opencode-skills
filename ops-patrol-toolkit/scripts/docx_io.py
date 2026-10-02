#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小 OOXML (.docx) 读写器 —— 纯标准库实现。

能力：
  - read_paragraphs / read_tables：读取段落（含样式）与表格文本
  - make_document：从结构化 blocks 生成 docx（标题/段落/占位段/表格，A4 版面）
  - fill_template：复制模板并做「跨 run 文本替换」与「指定单元格覆写」，段落与表格结构不动

显式边界：
  - 只处理 word/document.xml；页眉页脚、批注、脚注不读取不替换
  - 替换命中的段落会把多个 run 合并为一个（保留首个 run 的字体属性），版面结构不受影响
  - 复杂模板（smartArt、文本框内文字、嵌套表格）不支持替换
所有函数不打印。
"""

import re
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

_COMMON_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "v": "urn:schemas-microsoft-com:vml",
    "w10": "urn:schemas-microsoft-com:office:word",
    "o": "urn:schemas-microsoft-com:office:office",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "wne": "http://schemas.microsoft.com/office/word/2006/wordml",
}


class DocxError(Exception):
    """docx 结构性错误。"""


def _open_doc_xml(path):
    try:
        zf = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, FileNotFoundError) as e:
        raise DocxError("无法打开 docx %s: %s" % (path, e))
    try:
        raw = zf.read("word/document.xml")
        names = zf.namelist()
    finally:
        zf.close()
    return raw, names


def _para_style(p):
    ps = p.find(W + "pPr/" + W + "pStyle")
    return ps.get(W + "val") if ps is not None else None


def _para_text(p):
    return "".join(t.text or "" for t in p.iter(W + "t"))


def read_paragraphs(path):
    """正文顶层段落（不含表格内段落）：[{"style": val或None, "text": str}]"""
    raw, _ = _open_doc_xml(path)
    root = ET.fromstring(raw)
    body = root.find(W + "body")
    if body is None:
        raise DocxError("document.xml 缺少 body")
    out = []
    for child in body:
        if child.tag == W + "p":
            out.append({"style": _para_style(child), "text": _para_text(child)})
    return out


def read_tables(path):
    """全部表格（含嵌套表格的外层按最外层计）：[[[cell,...],...],...]

    每格取单元格内所有段落文本以换行拼接。
    """
    raw, _ = _open_doc_xml(path)
    root = ET.fromstring(raw)
    tables = []
    for tbl in root.iter(W + "tbl"):
        grid = []
        for tr in tbl.findall(W + "tr"):
            row = []
            for tc in tr.findall(W + "tc"):
                texts = [_para_text(p) for p in tc.findall(W + "p")]
                row.append("\n".join(t for t in texts if t))
            grid.append(row)
        tables.append(grid)
    return tables


def extract(path):
    return {"paragraphs": read_paragraphs(path), "tables": read_tables(path)}


# ---------------------------------------------------------------- 生成

_CT_DOCX = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

_ROOT_RELS_DOCX = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

_DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

_STYLES_DOCX = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:eastAsia="宋体" w:hAnsi="Calibri"/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="312" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:styleId="Normal" w:default="1"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:outlineLvl w:val="0"/><w:spacing w:before="320" w:after="160"/></w:pPr><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:outlineLvl w:val="1"/><w:spacing w:before="260" w:after="130"/></w:pPr><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:outlineLvl w:val="2"/><w:spacing w:before="200" w:after="100"/></w:pPr><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading4"><w:name w:val="heading 4"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:outlineLvl w:val="3"/><w:spacing w:before="160" w:after="80"/></w:pPr><w:rPr><w:b/><w:sz w:val="22"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Placeholder"><w:name w:val="Placeholder"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:color w:val="C00000"/></w:rPr></w:style>
<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/><w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4" w:color="000000"/><w:left w:val="single" w:sz="4" w:color="000000"/><w:bottom w:val="single" w:sz="4" w:color="000000"/><w:right w:val="single" w:sz="4" w:color="000000"/><w:insideH w:val="single" w:sz="4" w:color="000000"/><w:insideV w:val="single" w:sz="4" w:color="000000"/></w:tblBorders></w:tblPr></w:style>
</w:styles>"""


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _run(text, bold=False):
    rpr = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return "<w:r>%s<w:t xml:space=\"preserve\">%s</w:t></w:r>" % (rpr, _esc(text))


def _para_xml(text, style=None, bold=False):
    ppr = '<w:pPr><w:pStyle w:val="%s"/></w:pPr>' % style if style else ""
    if not text:
        return "<w:p>%s</w:p>" % ppr
    return "<w:p>%s%s</w:p>" % (ppr, _run(text, bold))


def _tbl_xml(rows, header=True):
    ncols = max(len(r) for r in rows) if rows else 1
    grid = "".join('<w:gridCol w:w="%d"/>' % (8296 // ncols) for _ in range(ncols))
    trs = []
    for i, row in enumerate(rows):
        cells = []
        for c in list(row) + [""] * (ncols - len(row)):
            bold = header and i == 0
            cells.append('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/></w:tcPr>%s</w:tc>'
                         % (8296 // ncols, _para_xml(str(c), bold=bold)))
        trs.append("<w:tr>%s</w:tr>" % "".join(cells))
    return ('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/></w:tblPr>'
            '<w:tblGrid>%s</w:tblGrid>%s</w:tbl>' % (grid, "".join(trs)))


def make_document(out_path, blocks):
    """从 blocks 生成 docx。

    block 类型：
      {"type":"h","level":1-4,"text":...}        标题
      {"type":"p","text":...}                    普通段落
      {"type":"ph","text":...}                   占位/待补充段（红色加粗）
      {"type":"table","rows":[[...]],"header":true}  表格
    """
    parts = []
    for b in blocks:
        t = b.get("type")
        if t == "h":
            parts.append(_para_xml(b.get("text", ""), "Heading%d" % min(max(int(b.get("level", 1)), 1), 4)))
        elif t == "p":
            parts.append(_para_xml(b.get("text", "")))
        elif t == "ph":
            parts.append(_para_xml(b.get("text", ""), "Placeholder", bold=True))
        elif t == "table":
            parts.append(_tbl_xml(b.get("rows") or [], header=bool(b.get("header", True))))
        else:
            raise ValueError("未知 block 类型: %r" % t)

    body = "".join(parts) + (
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1800" w:bottom="1440" w:left="1800" '
        'w:header="851" w:footer="992" w:gutter="0"/></w:sectPr>')
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body>%s</w:body></w:document>' % body)

    out_path = str(out_path)
    if out_path.lower().endswith(".docx"):
        out_path = out_path[:-5]
    out_path += ".docx"
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CT_DOCX)
        zf.writestr("_rels/.rels", _ROOT_RELS_DOCX)
        zf.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        zf.writestr("word/styles.xml", _STYLES_DOCX)
        zf.writestr("word/document.xml", document)
    return out_path


# ---------------------------------------------------------------- 模板回填

def _register_namespaces(raw):
    head = raw[:2048]
    for prefix, uri in re.findall(r'xmlns:([\w.-]+)="([^"]+)"', head.decode("utf-8", "replace")):
        ET.register_namespace(prefix, uri)
    for prefix, uri in _COMMON_NS.items():
        ET.register_namespace(prefix, uri)


def _set_para_text(p, text):
    """把段落文本整体置为 text：保留首个 run 的 rPr，删除其余 run。"""
    runs = [c for c in list(p) if c.tag == W + "r"]
    if runs:
        first = runs[0]
        for t in first.findall(W + "t"):
            first.remove(t)
        for br in first.findall(W + "br"):
            first.remove(br)
        t = ET.SubElement(first, W + "t")
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t.text = text
        for r in runs[1:]:
            p.remove(r)
    else:
        r = ET.SubElement(p, W + "r")
        t = ET.SubElement(r, W + "t")
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t.text = text


def fill_template(template_path, out_path, replacements=None, cells=None):
    """复制模板并回填，模板原件不动。

    replacements: {旧文本: 新文本}，按段落全文匹配（跨 run 生效）。
    cells: [{"table": 表序号0起, "row": 行号0起, "col": 列号0起, "text": 新文本}]
    返回 (写入路径, 命中的替换键列表, 未命中的替换键列表)。
    """
    raw, names = _open_doc_xml(template_path)
    _register_namespaces(raw)
    root = ET.fromstring(raw)
    body = root.find(W + "body")
    if body is None:
        raise DocxError("document.xml 缺少 body")

    hits, misses = [], []
    if replacements:
        for p in body.iter(W + "p"):
            text = _para_text(p)
            if not text:
                continue
            new = text
            changed = False
            for k, v in replacements.items():
                if k in new:
                    new = new.replace(k, v)
                    changed = True
                    hits.append(k)
            if changed:
                _set_para_text(p, new)
        misses = [k for k in replacements if k not in set(hits)]

    for spec in (cells or []):
        tables = body.findall(W + "tbl")
        ti = int(spec.get("table", 0))
        if ti >= len(tables):
            raise DocxError("模板中不存在第 %d 个表格（共 %d 个）" % (ti + 1, len(tables)))
        rows = tables[ti].findall(W + "tr")
        ri = int(spec.get("row", 0))
        if ri >= len(rows):
            raise DocxError("表 %d 不存在第 %d 行（共 %d 行）" % (ti + 1, ri + 1, len(rows)))
        tcs = rows[ri].findall(W + "tc")
        ci = int(spec.get("col", 0))
        if ci >= len(tcs):
            raise DocxError("表 %d 行 %d 不存在第 %d 列" % (ti + 1, ri + 1, ci + 1))
        paras = tcs[ci].findall(W + "p")
        target = paras[0] if paras else ET.SubElement(tcs[ci], W + "p")
        _set_para_text(target, str(spec.get("text", "")))
        hits.append("cell(%d,%d,%d)" % (ti, ri, ci))

    out_path = str(out_path)
    if out_path.lower().endswith(".docx"):
        out_path = out_path[:-5]
    out_path += ".docx"
    new_doc = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    with zipfile.ZipFile(template_path) as zin, \
            zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "word/document.xml":
                zout.writestr(item, new_doc)
            else:
                zout.writestr(item, zin.read(item.filename))
    return out_path, hits, misses
