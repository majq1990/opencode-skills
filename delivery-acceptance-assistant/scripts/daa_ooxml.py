# -*- coding: utf-8 -*-
"""OOXML 文本提取与模板替换（纯标准库）。

设计约束（来自实测教训，不可放宽）：
  - 提取用精确标签匹配，<w:t[^>]*> 会误吞 <w:tab>/<w:tabs>；
  - 替换两级：段落级跨 run（Word/PPT 拆词）→ 整 part 字符串（含数字实体变体）；
  - 只改文字内容，不增删 run、不改属性样式，版面完全保持。
"""
import os
import re
import json
import fnmatch
import zipfile

from daa_io import GapError, safe_path, ensure_parent

_NUM_ENTITY = re.compile(r"&#(\d+);|&#x([0-9A-Fa-f]+);")

DOCX_PARTS = ["word/document.xml", "word/header*.xml", "word/footer*.xml",
              "word/footnotes.xml", "word/endnotes.xml"]
XLSX_PARTS = ["xl/sharedStrings.xml", "xl/worksheets/sheet*.xml"]
PPTX_PARTS = ["ppt/slides/slide*.xml", "ppt/notesSlides/notesSlide*.xml"]


def _unescape(s):
    s = (s.replace("&lt;", "<").replace("&gt;", ">")
          .replace("&quot;", '"').replace("&apos;", "'"))
    if "&#" in s:
        def _num(m):
            dec, hx = m.group(1), m.group(2)
            cp = int(dec) if dec else int(hx, 16)   # 十进制走 base10，十六进制走 base16
            return chr(cp) if 0 < cp < 0x110000 else m.group(0)
        s = _NUM_ENTITY.sub(_num, s)
    return s.replace("&amp;", "&")


def extract_ooxml_text(path, parts, tag):
    """从 .docx/.xlsx/.pptx 的指定 part 提取正文文本。

    tag 必须精确匹配：<w:t[^>]*> 会误吞 <w:tab>/<w:tabs>，导致取到 XML 噪声。
    """
    lines = []
    try:
        z = zipfile.ZipFile(safe_path(path))
    except Exception:
        return ""
    names = z.namelist()
    pat = re.compile(r"<%s(?:\s[^>]*)?>(.*?)</%s>" % (re.escape(tag), re.escape(tag)), re.S)
    for part in parts:
        targets = [n for n in names if fnmatch.fnmatch(n, part)] if "*" in part else \
                  ([part] if part in names else [])
        for n in targets:
            try:
                xml = z.read(n).decode("utf-8", "ignore")
            except Exception:
                continue
            body = (xml.replace("</w:tc>", " | ").replace("</w:tr>", "\n")
                       .replace("</w:p>", "\n").replace("</a:p>", "\n"))
            for seg in body.split("\n"):
                t = "".join(pat.findall(seg))
                t = _unescape(re.sub(r"\s+", " ", t).strip())
                if t:
                    lines.append(t)
    z.close()
    return "\n".join(lines)


def extract_doc_legacy(path):
    """旧版 .doc（OLE2 二进制）：按 utf-16le 粗提取可打印字符。"""
    try:
        raw = open(safe_path(path), "rb").read()
    except Exception:
        return ""
    txt = raw.decode("utf-16-le", "ignore")
    keep = []
    for c in txt:
        o = ord(c)
        if c in "\r\n":
            keep.append("\n")
        elif 0x20 <= o <= 0x7E or 0x4E00 <= o <= 0x9FFF or o in (
                0x3001, 0x3002, 0xFF08, 0xFF09, 0xFF1A, 0xFF0C, 0xFF1B, 0x300A, 0x300B):
            keep.append(c)
        else:
            keep.append(" ")
    return re.sub(r"[ \t]{2,}", " ", "".join(keep))


def get_text(path, ext=None, text_exts=None):
    """统一取文本入口。ext 缺省取扩展名；text_exts 为 None 则全部文本文件都读。"""
    ext = (ext or os.path.splitext(path)[1]).lower()
    if ext == ".docx":
        return extract_ooxml_text(path, DOCX_PARTS, "w:t")
    if ext == ".xlsx":
        return extract_ooxml_text(path, XLSX_PARTS, "t")
    if ext == ".pptx":
        return extract_ooxml_text(path, PPTX_PARTS, "a:t")
    if ext == ".doc":
        return extract_doc_legacy(path)
    if text_exts is not None and ext not in text_exts:
        return None
    try:
        with open(safe_path(path), encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def ooxml_layout(path):
    """统计 OOXML 版面元素：图片 / 表格 / 域。生成前后比对，任一减少即判失败。"""
    counts = {"media": 0, "tables": 0, "fields": 0}
    try:
        z = zipfile.ZipFile(safe_path(path))
    except Exception:
        return counts
    for n in z.namelist():
        if "/media/" in n:
            counts["media"] += 1
    if "word/document.xml" in z.namelist():
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
        counts["tables"] += len(re.findall(r"<w:tbl>", xml))
        counts["fields"] += len(re.findall(r"<w:fldChar", xml))
    for n in z.namelist():
        if n.startswith("ppt/slides/slide") and n.endswith(".xml"):
            xml = z.read(n).decode("utf-8", "ignore")
            counts["tables"] += len(re.findall(r"<a:tbl>", xml))
    z.close()
    return counts


def _esc_num(s):
    return "".join(c if ord(c) < 128 else "&#%d;" % ord(c) for c in s)


def _variants(text):
    """同一段文字在 OOXML 里的可能写法：字面量 / 全数字实体。"""
    v = [(text, text)]
    e = _esc_num(text)
    if e != text:
        v.append((e, e))
    return v


def _pairs_with_key(replaced):
    """展开 {原文: 新文} 为 (原文键, 查找串, 替换串) 列表。

    查找串与替换串必须同一种编码风格——实体对实体、字面量对字面量。
    """
    out = []
    for old, new in replaced.items():
        for o, _unused in _variants(old):
            out.append((old, o, new if o == old else _esc_num(new)))
    return out


def _replace_pairs(replaced):
    return [(o, n) for _, o, n in _pairs_with_key(replaced)]


_PARA_RE_CACHE = {}


def _paragraph_re(tag):
    if tag not in _PARA_RE_CACHE:
        _PARA_RE_CACHE[tag] = re.compile(
            r"<%s(?:\s[^>]*)?>.*?</%s>" % (re.escape(tag), re.escape(tag)), re.S)
    return _PARA_RE_CACHE[tag]


def _replace_in_paragraphs(xml, para_tag, text_tag, pairs):
    """段落级替换：处理「一个词被 Word/PPT 拆进多个 run」的情形。

    把段落内所有文本元素拼起来匹配；命中后把新文本整体写进第一个被占用的
    文本元素，其余被占用的文本元素清空。不增删 run、不改属性样式。
    坐标系注意：spans 是「拼接文本」坐标，cursor/s/t 是「XML block」坐标。
    """
    t_re = re.compile(r"(<%s(?:\s[^>]*)?>)(.*?)(</%s>)"
                      % (re.escape(text_tag), re.escape(text_tag)), re.S)
    changed = 0
    matched = set()
    for pm in list(_paragraph_re(para_tag).finditer(xml)):
        block = pm.group(0)
        elems = list(t_re.finditer(block))
        if len(elems) < 2:
            continue
        spans, acc = [], 0
        for e in elems:
            n = len(e.group(2))
            spans.append((acc, acc + n))
            acc += n
        joined = "".join(e.group(2) for e in elems)
        target = None
        for old, new in pairs:
            if old in joined:
                target = (old, new)
                break
        if not target:
            continue
        old, new = target
        pos = joined.find(old)
        end = pos + len(old)

        out, cursor, placed = [], 0, False
        for e, (js, je) in zip(elems, spans):
            s, t = e.start(2), e.end(2)
            out.append(block[cursor:s])
            lo, hi = max(js, pos), min(je, end)
            if lo < hi and not placed:
                out.append(e.group(2)[:lo - js] + new + e.group(2)[hi - js:])
                placed = True
            elif lo < hi:
                out.append("")
            else:
                out.append(e.group(2))
            cursor = t
        out.append(block[cursor:])
        if not placed:
            continue
        xml = xml.replace(block, "".join(out), 1)
        matched.add(old)
        changed += 1
    return xml, changed, matched


def rewrite_zip(src, dst, replacements, parts_filter=None):
    """复制 zip 并做文本替换，保持其余字节原样。返回 {原文键: 命中次数}。"""
    if not replacements:
        raise GapError("replacements 为空，拒绝生成空文档")
    replaced = {k: str(v) for k, v in replacements.items() if k and k != str(v)}
    if not replaced:
        raise GapError("replacements 全部为恒等替换（原文==新文），无意义")
    hit = {k: 0 for k in replaced}
    src, dst = safe_path(src), safe_path(dst)
    if not os.path.isfile(src):
        raise GapError("模板文件不存在：%s" % src)
    if os.path.abspath(src) == os.path.abspath(dst):
        raise GapError("输出路径与模板相同，会覆盖模板，已拒绝")
    zin = zipfile.ZipFile(src, "r")
    ensure_parent(dst)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.endswith(".xml") and (
                    parts_filter is None or parts_filter(item.filename)):
                try:
                    xml = data.decode("utf-8")
                except UnicodeDecodeError:
                    zout.writestr(item, data)
                    continue
                # 段落容器标签与文本标签必须分开：word=w:p/w:t，ppt=a:p/a:t，
                # xlsx=si（共享字符串项）/t。混用会导致跨 run 替换整层失效。
                if item.filename.startswith("word/"):
                    para_tag, ttag = "w:p", "w:t"
                elif item.filename.startswith("ppt/"):
                    para_tag, ttag = "a:p", "a:t"
                else:
                    para_tag, ttag = "si", "t"
                xml, npara, pkeys = _replace_in_paragraphs(
                    xml, para_tag, ttag, _replace_pairs(replaced))
                for old in pkeys:
                    hit[old] += 1
                for old, o, n in _pairs_with_key(replaced):
                    if o in xml:
                        hit[old] += xml.count(o)
                        xml = xml.replace(o, n)
                data = xml.encode("utf-8")
            zout.writestr(item, data)
    zin.close()
    return hit


def parts_filter_for(ext):
    ext = (ext or "").lower()
    if ext == ".docx":
        return lambda n: n.startswith("word/") and n.endswith(".xml")
    if ext == ".xlsx":
        return lambda n: n.startswith("xl/") and n.endswith(".xml")
    if ext == ".pptx":
        return lambda n: n.startswith("ppt/slides/slide") and n.endswith(".xml")
    return lambda n: n.endswith(".xml")
