#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_manual_standardize · 维护手册规范化（ops-patrol-toolkit 子工具 03）

双模式 + 生成后自动回检闭环（判定逻辑移植自内部评审入选样例工程"规范项目维护手册"，
已脱敏），并按本仓库契约改造：
  - docx 读写一律走共享库 docx_io（read_paragraphs/read_tables/make_document），
    本脚本不自带任何 OOXML 代码
  - 匹配阈值/占位文案外置到 config/patrol/manual_rules.json，代码不写死
  - stdout 最后一行固定为 JSON 信封：成功 {"ok": true, ...}；失败 {"ok": false, "gap": "..."}
    并以退出码 2 结束
  - 差异清单头部带【待复核】标记，未经人工复核不得外发；控制台不使用 emoji

子命令:
  extract   读取资料 docx 的段落/表格 -> extracted.json（供 AI/人工快速浏览资料结构）
  generate  project_info.json + 资料 docx -> 11 个标准章节的手册初稿（缺失要素写【待补充】
            占位段），生成后自动回跑 check，信封带 self_check（P0 应为 0）
  check     以 references/standard-structure.json 为基线做章节完整性/要素/术语检测，
            输出四级差异清单 markdown：P0 章节缺失 / P1 疑似改名·要素缺失·样式 / P2 术语不统一

章节两级判定（移植自源 compare_manuals.py，踩坑注释近保真保留）:
  1. 标题模糊匹配: 主名精确 > 别名/高相似(>=alias_sim_min，全角半角+编号归一化) > 关键词命中
  2. 内容证据兜底: 标题未命中的章节扫描全文找关键词证据，有证据降级 P1"疑似改名待人工审核"，
     标题与内容均无证据才判 P0 缺失

移植偏差（相对源 extract_docx.py / generate_draft.py / compare_manuals.py，均已注释标明）:
  1. docx_io 公共 API 不提供"表格在正文流中的位置"，段落块与表格分离处理：
     章节匹配只在段落块上进行；table_cols_all 要素检查与术语/内容证据对全部表格做全文扫描；
     文本类要素检查在章节段落范围之外追加全文表格文本作为补充证据源。
     代价是表格证据无法归属到具体章节——不会漏报 P0，只可能少报 P1 要素缺失。
  2. 源版三个脚本合一为 extract/generate/check 三个子命令；extract 输出改为
     段落/表格分列的 JSON（并在 note 中注明上述位置限制）。
  3. 标题层级由段落样式 ID（Heading N / 标题 N）推断；docx_io 不读 styles.xml，
     中文 Word 里 styleId 为纯数字（如"1"）的标题样式识别不到，按正文段落处理（已知边界）。

安全约束:
  - 手册含账号密码等敏感信息：展示摘要不得复述明文密码，分发范围由责任人确认
  - 真实项目名/人名/IP/电话禁止进入本仓库（fixtures 全虚构）
"""

import argparse
import datetime
import difflib
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import docx_io  # noqa: E402  共享 docx 读写库（本工具禁止自带 OOXML 代码）
import patrol_lib  # noqa: E402  公共库：信封(emit/stop)/路径(skill_path/work_path)/退出码

__version__ = "1.0.0"

DEFAULT_STRUCTURE = patrol_lib.skill_path("references", "standard-structure.json")
DEFAULT_TERMS = patrol_lib.skill_path("references", "terminology.json")

# generate 表格的标准列序（也是 harvest 行映射的目标列）
SERVER_KEYS = ("设备名称", "IP地址", "操作系统", "配置", "用户/密码", "用途", "部署服务")
CONTACT_KEYS = ("姓名", "单位", "职位", "电话", "负责事项")

_RULES_CACHE = None


def load_rules(refresh=False):
    """加载外置规则 config/patrol/manual_rules.json（进程内缓存一份）。

    约定：匹配阈值/占位文案一律不写死在代码里，改数值只改配置；
    配置缺失或 JSON 损坏由 patrol_lib 直接 gap 停机（退出码 2），不做静默兜底。
    """
    global _RULES_CACHE
    if _RULES_CACHE is None or refresh:
        _RULES_CACHE = patrol_lib.load_config("manual_rules")
    return _RULES_CACHE


# ---------------------------------------------------------------- 文本规范化


_FW = "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ：．（）－"
_HW = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:.()-"
_TRANS = str.maketrans(_FW, _HW)

_NUM_PREFIX = re.compile(
    r"^\s*(?:[(（][一二三四五六七八九十\d]+[)）]|[一二三四五六七八九十\d]+[、.．])")


def normalize(text):
    """规范化用于章节匹配: 全角转半角、去编号前缀、去空白、转小写（移植自源码）。"""
    t = (text or "").translate(_TRANS)
    t = _NUM_PREFIX.sub("", t)
    t = re.sub(r"\s+", "", t)
    return t.lower()


def sim(a, b):
    """标题相似度: 全等 1.0 > 包含 0.95 > difflib.SequenceMatcher（移植自源码）。"""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.95
    return difflib.SequenceMatcher(None, a, b).ratio()


# ---------------------------------------------------------------- docx 读取


class DocxReadError(Exception):
    """docx 读取失败（文件缺失/损坏/非 docx）。由调用方决定 stop 还是降级。"""


def _heading_level(style):
    """由段落样式 ID 推断标题层级，非标题返回 None。

    docx_io 只暴露 styleId（不读 styles.xml 样式名），因此覆盖两类常见写法：
    英文 Heading1 / heading 1 与中文 标题1 / 标题 1；styleId 为纯数字的中文 Word
    文档（styleId="1" 对应"标题 1"）识别不到，按正文段落处理（已知边界，见模块头）。
    """
    if not style:
        return None
    s = str(style).strip()
    low = s.lower()
    if low.startswith("heading"):
        tail = low[7:].strip()
        if tail.isdigit() and 1 <= int(tail) <= 6:
            return int(tail)
        return 1  # 裸 heading 样式按一级标题处理
    if s.startswith("标题"):
        tail = s[2:].strip()
        if tail.isdigit() and 1 <= int(tail) <= 6:
            return int(tail)
        return 1
    return None


def read_doc(path):
    """读取 docx -> (段落块列表, 表格列表)。

    段落块: {"type": "heading"|"para", "level": int|None, "style": styleId,
             "text": str, "index": int}

    移植偏差说明（重要，保留踩坑注释精神）：
      docx_io 公共 API 只提供 read_paragraphs（正文顶层段落）与 read_tables（全部表格），
      不提供表格在正文流中的相对位置。因此段落块与表格分离返回：
        - 章节匹配/章节范围/术语位置等依赖块序的逻辑只作用于段落块；
        - 表格内容统一做全文扫描补偿（要素检查 table_cols_all、术语扫描、内容证据），
          代价是表格证据无法归属到具体章节（不会漏报 P0，只可能少报 P1 要素缺失）。
    """
    if not os.path.isfile(str(path)):
        raise DocxReadError("文件不存在: %s" % path)
    try:
        paras = docx_io.read_paragraphs(str(path))
        tables = docx_io.read_tables(str(path))
    except docx_io.DocxError as e:
        raise DocxReadError(str(e))
    blocks = []
    for p in paras:
        text = (p.get("text") or "").strip()
        if not text:
            continue
        style = p.get("style")
        level = _heading_level(style)
        blocks.append({"type": "heading" if level else "para", "level": level,
                       "style": style, "text": text, "index": len(blocks)})
    tables = [t for t in tables
              if t and any(any(str(c).strip() for c in row) for row in t)]
    return blocks, tables


# ---------------------------------------------------------------- 章节匹配


def match_sections(blocks, sections, start=0, end=None, rules=None):
    """把结构定义中的必备章节贪婪唯一匹配到文档段落块（移植自源 compare_manuals.py）。

    匹配优先级: 主名精确 > 别名/高相似(>=alias_sim_min) > 关键词命中(keyword_score)；
    返回 [{score, section, block, kind}]，kind 为 'heading' 或 'para'。
    偏差说明：本函数只接收段落块（heading/para），表格由调用方全文扫描补偿；
    源版里表格块可能落进段落匹配分支（表格首行拼串误当段落）的隐患随之消除。
    """
    m_rules = (rules or load_rules())["match"]
    alias_min = m_rules["alias_sim_min"]
    kw_score = m_rules["keyword_score"]
    para_min = m_rules["para_sim_min"]
    short_len = m_rules["short_name_min_len"]

    end = len(blocks) if end is None else end
    cands = []
    for si, sec in enumerate(sections):
        names = [normalize(n) for n in [sec["name"]] + sec.get("aliases", [])]
        kws = [normalize(k) for k in sec.get("keywords", []) if k]
        for bi in range(start, end):
            b = blocks[bi]
            nb = normalize(b.get("text", "")[:60])
            if not nb:
                continue
            score = max(sim(n, nb) for n in names if n)
            kw_hit = any(k and k in nb for k in kws)
            if b["type"] == "heading":
                if kw_hit:
                    # 关键词命中: 稳定给 keyword_score，低于别名精确命中，但可兜住
                    # "差好几个字"的改名章节（如"云平台资源情况"命中"服务器配置信息"）
                    cands.append({"score": max(score, kw_score) + 0.01, "si": si, "bi": bi})
                elif score >= alias_min:
                    # 主名精确命中 > 别名命中；标题 > 段落
                    bonus = 0.01 + (0.005 if normalize(sec["name"]) == nb else 0)
                    cands.append({"score": score + bonus, "si": si, "bi": bi})
            else:
                # 目录行过滤: 末尾带页码的段落（如"6.1 系统备份策略11"）不参与段落匹配，
                # 避免目录条目抢走正文标题的匹配（源样例踩坑保留）
                if m_rules.get("toc_page_suffix", True) and re.search(r"\d{1,3}$", normalize(b.get("text", ""))):
                    continue
                # 段落匹配要求更高置信度; 短名（< short_name_min_len 字符，如 FAQ）必须完全
                # 一致，防止 URL/正文中出现 "faq" 之类子串导致误匹配
                best_name, best_score = max(((n, sim(n, nb)) for n in names if n),
                                            key=lambda x: x[1])
                if best_score >= para_min and (len(best_name) >= short_len or best_score == 1.0):
                    cands.append({"score": best_score, "si": si, "bi": bi})
    # 得分降序；同分时优先靠前的块（避免被后文的小节抢走匹配）
    cands.sort(key=lambda c: (-c["score"], c["bi"]))
    used_s, used_b, result = set(), set(), []
    for c in cands:
        si, bi = c["si"], c["bi"]
        if si in used_s or bi in used_b:
            continue
        used_s.add(si)
        used_b.add(bi)
        sec, blk = sections[si], blocks[bi]
        kind = "heading" if blk["type"] == "heading" else "para"
        result.append({"score": round(c["score"], 2), "section": sec,
                       "block": blk, "kind": kind})
    result.sort(key=lambda r: r["block"]["index"])
    return result


def section_range(matches, match, total):
    """计算某个已匹配章节的内容范围 [start, end)（移植自源码）。"""
    idx = match["block"]["index"]
    start = idx + 1
    end = total
    for m in matches:
        if m is match:
            continue
        if idx < m["block"]["index"] < end:
            end = m["block"]["index"]
    return start, end


# ---------------------------------------------------------------- 内容要素检查


def _tables_text(tables):
    """全部表格单元格拼接文本（小写），用于无法定位章节的表格内容补偿。"""
    return "\n".join(str(c) for t in tables for row in t for c in row).lower()


def check_elements(blocks, start, end, elements, tables):
    """按定义检查章节内容要素，返回 [(element, ok, detail)]（移植自源码）。

    偏差补偿：表格无法定位到章节范围，因此
      - table_cols_all 直接做全文表格扫描；
      - text_any/text_all/regex 在章节段落范围之外，追加全文表格文本作为补充证据源。
    """
    scope = blocks[start:end]
    joined = "\n".join(b.get("text", "") for b in scope if b["type"] != "table")
    joined_l = joined.lower()
    tables_l = _tables_text(tables)
    results = []
    for el in elements or []:
        chk = el.get("check", {})
        ctype = chk.get("type")
        ok, detail = False, ""
        if ctype == "text_any":
            vals = [v.lower() for v in chk.get("values", [])]
            hit = [v for v in vals if v in joined_l]
            if not hit:
                hit = [v for v in vals if v in tables_l]
            if hit:
                ok, detail = True, "命中: %s" % ", ".join(hit)
            else:
                ok, detail = False, "未找到关键词: %s" % chk.get("values")
        elif ctype == "text_all":
            vals = [v.lower() for v in chk.get("values", [])]
            miss = [v for v in vals if v not in joined_l and v not in tables_l]
            ok, detail = not miss, ("全部命中" if not miss else "缺少: %s" % ", ".join(miss))
        elif ctype == "table_cols_all":
            vals = [normalize(v) for v in chk.get("values", [])]
            for t in tables:
                for row in t:
                    norm_row = [normalize(c) for c in row]
                    if all(any(v in c for c in norm_row) for v in vals):
                        ok = True
                        break
                if ok:
                    break
            detail = "需要含列: %s 的表格（全文表格扫描）" % "/".join(chk.get("values", []))
        elif ctype == "regex":
            pat = chk.get("pattern", "")
            ok = bool(re.search(pat, joined, re.I))
            if not ok and tables_l:
                ok = bool(re.search(pat, tables_l, re.I))
            detail = "正则: %s" % pat
        else:
            ok, detail = True, "仅要求章节存在"
        results.append((el, ok, detail))
    return results


# ---------------------------------------------------------------- 内容证据兜底


def find_content_evidence(blocks, tables, sec, limit=5):
    """标题未匹配时，按关键词扫描全文寻找该章节的内容证据（移植自源码）。

    返回 [{'location': 最近标题, 'text': 命中片段, 'hit': 关键词}]；无证据返回 []。
    偏差说明：表格内容的证据位置无法归属章节，统一标注为"表格N"。
    """
    kws = [k for k in sec.get("keywords", []) if k]
    if not kws:
        return []
    evidence, current_loc = [], "（文档开头）"
    for b in blocks:
        if b["type"] == "heading":
            current_loc = b["text"]
            continue
        nl = normalize(b["text"])
        if not nl:
            continue
        hit = next((k for k in kws if normalize(k) in nl), None)
        if hit:
            evidence.append({"location": current_loc, "text": b["text"].strip()[:60], "hit": hit})
            if len(evidence) >= limit:
                return evidence
    for ti, t in enumerate(tables, 1):
        for row in t:
            for cell in row:
                nl = normalize(cell)
                if not nl:
                    continue
                hit = next((k for k in kws if normalize(k) in nl), None)
                if hit:
                    evidence.append({"location": "表格%d" % ti,
                                     "text": str(cell).strip()[:60], "hit": hit})
                    if len(evidence) >= limit:
                        return evidence
    return evidence


# ---------------------------------------------------------------- 术语检查

_CMD_MARKERS = ("service ", "systemctl ", "yum ", "apt-get", "nohup", "java -jar",
                "tail -f", "grant ", "redis-cli", "regsvr32", "ntpdate", "mysqldump",
                "startup.sh", "kill ")


def _is_command_or_url(line):
    """命令行、URL 中的小写写法属于正常用法，术语扫描自动忽略（移植自源码）。"""
    s = str(line).strip()
    if "http://" in s or "https://" in s:
        return True
    if s.startswith(("/", "$", "#!", "C:\\", "D:\\", "E:\\")):
        return True
    return any(m in s.lower() for m in _CMD_MARKERS)


def _variant_count(line, variant):
    if re.search(r"[A-Za-z]", variant):
        # 词边界: 前后不能是字母或数字（避免匹配 tomcat80、mysql57、mysqld 等名称）
        pattern = r"(?<![A-Za-z0-9])" + re.escape(variant) + r"(?![A-Za-z0-9])"
        return len(re.findall(pattern, str(line)))
    return str(line).count(variant)


def check_terminology(blocks, tables, terms):
    """扫描术语变体。返回 {variant: {'count': n, 'locations': [位置...], 'standard': 写法}}。

    移植自源码；偏差：表格单元单独扫描，位置标注"表格N"（docx_io 无法定位表格所属章节）。
    """
    findings = {}

    def scan_line(line, loc):
        if not line or _is_command_or_url(line):
            return
        for term in terms:
            for variant in term.get("variants", []):
                n = _variant_count(line, variant)
                if n:
                    rec = findings.setdefault(variant, {"count": 0, "locations": [],
                                                        "standard": term["standard"]})
                    rec["count"] += n
                    if loc not in rec["locations"]:
                        rec["locations"].append(loc)

    current_loc = "（文档开头）"
    for b in blocks:
        if b["type"] == "heading":
            current_loc = b["text"]
            continue
        scan_line(b["text"], current_loc)
    for ti, t in enumerate(tables, 1):
        for row in t:
            for cell in row:
                scan_line(cell, "表格%d" % ti)
    return findings


# ---------------------------------------------------------------- 审计与报告


def audit_manual(manual_path, structure, terms, rules=None):
    """对单本手册做完整审计，返回报告 dict（移植自源 compare_manuals.audit_one）。"""
    rules = rules or load_rules()
    sections = structure.get("required_sections") or []
    if not sections:
        patrol_lib.stop("章节基线缺少 required_sections 定义，请检查基线 JSON"
                        "（references/standard-structure.json 或 --baseline 指向的文件）")
    try:
        blocks, tables = read_doc(manual_path)
    except DocxReadError as e:
        patrol_lib.stop("无法读取手册 docx: %s（旧版 .doc 请先在 Word 中另存为 .docx）" % e)

    matches = match_sections(blocks, sections, rules=rules)
    report = {"target": str(manual_path), "matched": [], "missing": [],
              "renamed": [], "style_issues": [], "element_missing": [],
              "term_findings": {}, "extra_headings": [],
              "total_sections": len(sections)}

    used_block_idx = {m["block"]["index"] for m in matches}
    for sec in sections:
        m = next((x for x in matches if x["section"]["id"] == sec["id"]), None)
        if m is None:
            # 两级判定的第二级: 标题没匹配上，先找内容证据，有证据降级为 P1 疑似改名待人工审核；
            # AI 只提供证据，由人工决定"更名对齐标准 / 保留现名补要素 / 确认缺失转 P0"
            ev = find_content_evidence(blocks, tables, sec, rules["check"]["evidence_limit"])
            if ev:
                report["renamed"].append({"section": sec, "evidence": ev})
            else:
                report["missing"].append(sec)
            continue
        report["matched"].append({"section": sec, "match": m})

        # 样式 / 层级检查
        if sec.get("require_heading_style", True):
            if m["kind"] != "heading":
                report["style_issues"].append(
                    {"section": sec,
                     "issue": "章节“%s”以正文形式存在，未使用标题样式（影响自动目录生成）"
                              % m["block"]["text"][:40]})
            elif sec.get("expected_level") and m["block"].get("level", 0) > sec["expected_level"]:
                report["style_issues"].append(
                    {"section": sec,
                     "issue": "章节标题层级为 H%d，标准中应为 H%d"
                              % (m["block"]["level"], sec["expected_level"])})

        # 内容范围与要素
        start, end = section_range(matches, m, len(blocks))
        for el, ok, detail in check_elements(blocks, start, end, sec.get("elements", []), tables):
            if not ok:
                report["element_missing"].append({"section": sec, "element": el, "detail": detail})

        # 子章节（如"应用软件系统"下的"数据库服务"/"web应用服务器"）
        for child in sec.get("children", []):
            sub_matches = match_sections(blocks, [child], start, end, rules=rules)
            if not sub_matches:
                report["missing"].append(dict(child, _parent=sec["name"]))
                continue
            sm = sub_matches[0]
            all_sub = match_sections(blocks, sec.get("children", []), start, end, rules=rules)
            later = [x["block"]["index"] for x in all_sub if x["block"]["index"] > sm["block"]["index"]]
            s2 = sm["block"]["index"] + 1
            e2 = min([x for x in later if x > s2] or [end])
            e2 = min(e2, end)
            for el, ok, detail in check_elements(blocks, s2, e2, child.get("elements", []), tables):
                if not ok:
                    report["element_missing"].append({"section": child, "element": el, "detail": detail})

    # 目标独有的一级标题（提示，不算问题）
    for b in blocks:
        if b["type"] == "heading" and b.get("level") == 1 and b["index"] not in used_block_idx:
            report["extra_headings"].append(b["text"])

    report["term_findings"] = check_terminology(blocks, tables, terms)
    return report


def summarize(report):
    """把报告 dict 折算成 p0/p1/p2 计数（信封口径）。

    P0 = 章节缺失；P1 = 疑似改名 + 内容要素缺失 + 命名/样式问题；P2 = 术语不统一组数。
    """
    return {
        "p0": len(report["missing"]),
        "p1": len(report["renamed"]) + len(report["element_missing"]) + len(report["style_issues"]),
        "p2": len(report["term_findings"]),
        "matched": len(report["matched"]),
        "total_sections": report["total_sections"],
    }


def render_report(r, baseline_name):
    """渲染四级差异清单 markdown（移植自源 compare_manuals.render_report）。

    与源版的差异：标题带【待复核】标记；去掉 emoji，结论用纯文字表述。
    """
    counts = summarize(r)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    L = []
    A = L.append
    A("# 《%s》差异清单 【待复核】" % os.path.basename(r["target"]))
    A("")
    A("- **审计基线**: %s（必备章节 + 别名 + 内容要素定义）" % baseline_name)
    A("- **审计工具**: ops-patrol-toolkit 03_manual_standardize v%s（规范检测模式）" % __version__)
    A("- **生成时间**: %s" % now)
    A("- **复核要求**: 本清单由工具自动生成；P1\"疑似改名\"章节须人工确认后才能定性，未经复核不得外发。")
    A("")
    n_missing = len(r["missing"])
    n_renamed = len(r["renamed"])
    n_style = len(r["style_issues"])
    n_elem = len(r["element_missing"])
    n_term = len(r["term_findings"])
    A("## 一、总体概览")
    A("")
    A("| 检查项 | 结果 |")
    A("| --- | --- |")
    A("| 章节完整度 | %d / %d（P0 缺失 %d 个，疑似改名待人工审核 %d 个） |"
      % (len(r["matched"]), r["total_sections"], n_missing, n_renamed))
    A("| 命名/样式问题 | %d 处 |" % n_style)
    A("| 内容要素缺失 | %d 项 |" % n_elem)
    A("| 术语不统一 | %d 组 |" % n_term)
    A("")
    if counts["p0"] == 0 and counts["p1"] == 0 and counts["p2"] == 0:
        A("> 结论: 与标准基线结构一致，未发现问题。")
    else:
        A("> 结论: P0 缺失章节 %d 个、疑似改名待人工审核 %d 个、命名/样式问题 %d 处、"
          "内容要素缺失 %d 项、术语不统一 %d 组，建议按下列清单修订。"
          % (n_missing, n_renamed, n_style, n_elem, n_term))
    A("")

    if r["renamed"]:
        A("## 二、疑似改名待人工审核（P1 —— 标题未按标准名/别名/关键词命中，但找到内容证据）")
        A("")
        A("> 以下章节很可能以其他名称存在。**请人工确认后决定: 更名对齐标准 / 保留现名并补充"
          "标准要素 / 确认缺失转 P0。**")
        A("")
        A("| 标准章节 | 内容证据（位置 → 命中关键词） | 建议动作 |")
        A("| --- | --- | --- |")
        for item in r["renamed"]:
            sec = item["section"]
            ev = "；".join("%s →「%s」(%s)" % (e["location"], e["text"], e["hit"])
                           for e in item["evidence"][:3])
            A("| %s | %s | 人工审核: 确认是否为同一章节 |" % (sec["name"], ev))
        A("")

    if r["missing"]:
        A("## 三、缺失章节（P0 —— 标题与内容均无证据，必须补充）")
        A("")
        A("| 序号 | 标准章节 | 上级章节 | 章节说明 | 应包含的内容 |")
        A("| --- | --- | --- | --- | --- |")
        for i, sec in enumerate(r["missing"], 1):
            els = "；".join(e["desc"] for e in sec.get("elements", [])) or "（仅要求章节存在）"
            A("| %d | %s | %s | %s | %s |" % (
                i, sec["name"], sec.get("_parent", "—"),
                sec.get("description", ""), els))
        A("")

    if r["style_issues"]:
        A("## 四、命名与样式问题（P1）")
        A("")
        for s in r["style_issues"]:
            A("- **%s**: %s" % (s["section"]["name"], s["issue"]))
        A("")

    if r["element_missing"]:
        A("## 五、内容要素缺失（P1 —— 章节存在但内容不全）")
        A("")
        A("| 所属章节 | 缺失要素 | 检查说明 |")
        A("| --- | --- | --- |")
        for e in r["element_missing"]:
            A("| %s | %s | %s |" % (e["section"]["name"], e["element"]["desc"], e["detail"]))
        A("")

    if r["term_findings"]:
        A("## 六、术语不统一（P2 —— 建议统一写法）")
        A("")
        A("| 标准写法 | 文档中的写法 | 出现次数 | 主要位置 |")
        A("| --- | --- | --- | --- |")
        for variant, rec in sorted(r["term_findings"].items(), key=lambda kv: -kv[1]["count"]):
            locs = "、".join(rec["locations"][:3])
            if len(rec["locations"]) > 3:
                locs += " 等"
            A("| %s | %s | %d | %s |" % (rec["standard"], variant, rec["count"], locs))
        A("")
        A("> 注: 命令行、URL 中的小写写法属于正常用法，已自动忽略；上表仅统计正文与表格中的不一致写法。")
        A("")

    if r["extra_headings"]:
        A("## 七、目标文档独有章节（提示，供确认是否有价值）")
        A("")
        for h in r["extra_headings"]:
            A("- %s" % h)
        A("")

    A("---")
    A("")
    A("*修订建议: 优先处理 P0 缺失章节；\"疑似改名待人工审核\"章节请逐条人工确认后决定更名或补内容；"
      "其次 P1 样式与内容要素，最后统一 P2 术语；修订完成后在《文件变更记录》表中登记版本号与变更类型。*")
    A("*安全提示: 本报告可能包含手册中的账号密码等敏感信息，请注意保存与分发范围。*")
    return "\n".join(L)


# ---------------------------------------------------------------- 资料自动抽取


def _norm_cell(v):
    return re.sub(r"\s+", "", str(v or "")).lower()


def harvest(docx_path):
    """从资料 docx 中抽取服务器表、联系人表、访问地址（移植自源 generate_draft.harvest）。

    返回 {'servers': [(header, row), ...], 'contacts': [(header, row), ...], 'urls': [...]}。
    """
    blocks, tables = read_doc(docx_path)
    found = {"servers": [], "contacts": [], "urls": set()}
    for t in tables:
        if len(t) <= 1:
            continue
        header = [_norm_cell(c) for c in t[0]]

        def col(*keys):
            for i, h in enumerate(header):
                if any(k in h for k in keys):
                    return i
            return None

        ci_name, ci_ip = col("设备名称", "服务器名称", "主机名"), col("ip")
        ci_contact, ci_tel = col("姓名", "联系人"), col("电话", "手机", "联系方式")
        if ci_name is not None and ci_ip is not None:
            for row in t[1:]:
                if len(row) > max(ci_name, ci_ip) and str(row[ci_ip]).strip():
                    found["servers"].append((t[0], row))
        elif ci_contact is not None and ci_tel is not None:
            for row in t[1:]:
                if len(row) > max(ci_contact, ci_tel) and str(row[ci_contact]).strip():
                    found["contacts"].append((t[0], row))
    for b in blocks:
        if b["type"] == "para":
            found["urls"].update(re.findall(r"https?://[^\s，,；;）)]+", b["text"]))
    found["urls"] = sorted(found["urls"])
    return found


def row_to_server(row, header):
    """按原表头语义映射一行服务器数据到标准列（移植自源码）。"""

    def val(*keys):
        for i, h in enumerate(header):
            if any(k in _norm_cell(h) for k in keys) and i < len(row):
                return str(row[i]).strip()
        return ""

    return [val("设备名称", "服务器名称", "主机名"), val("ip"),
            val("操作系统"), val("配置"), val("用户", "密码", "账号"),
            val("用途"), val("部署", "服务")]


def row_to_contact(row, header):
    """按原表头语义映射一行联系人数据到标准列（移植自源码）。"""

    def val(*keys):
        for i, h in enumerate(header):
            if any(k in _norm_cell(h) for k in keys) and i < len(row):
                return str(row[i]).strip()
        return ""

    return [val("姓名", "联系人"), val("单位", "公司"), val("职位", "职务"),
            val("电话", "手机", "联系方式"), val("负责", "职责", "事项")]


def merge_harvest(info, sources):
    """用自动抽取结果填补 info 中缺失的服务器/联系人/访问地址（移植自源码）。

    --info 显式给出的内容优先于自动抽取结果。
    返回抽取统计 dict；资料全部无法解析时按 SKILL 停止条件 4 直接 gap 停机。
    """
    servers, contacts, urls = [], [], []
    failures = []
    for src in sources:
        try:
            h = harvest(src)
        except DocxReadError as e:
            failures.append("%s: %s" % (src, e))
            print("警告: 解析 %s 失败: %s" % (src, e))
            continue
        for header, row in h["servers"]:
            servers.append(row_to_server(row, header))
        for header, row in h["contacts"]:
            contacts.append(row_to_contact(row, header))
        for u in h["urls"]:
            urls.append({"名称": "", "地址": u})
    if sources and len(failures) == len(sources):
        patrol_lib.stop("资料全部无法解析（%d 个）：%s；请确认为有效 .docx 文件"
                        "（旧版 .doc 先另存为 .docx），或改用 --info 手工填写"
                        % (len(sources), "; ".join(failures)))
    if servers and not info.get("servers"):
        # 去重（按设备名称+IP）
        seen, uniq = set(), []
        for s in servers:
            key = (s[0], s[1])
            if key not in seen:
                seen.add(key)
                uniq.append(dict(zip(SERVER_KEYS, s)))
        info["servers"] = uniq
    if contacts and not info.get("contacts"):
        seen, uniq = set(), []
        for c in contacts:
            key = (c[0], c[3])
            if key not in seen:
                seen.add(key)
                uniq.append(dict(zip(CONTACT_KEYS, c)))
        info["contacts"] = uniq
    if urls and not info.get("access_urls"):
        info["access_urls"] = urls
    return {"sources": len(sources), "parse_failed": len(failures),
            "harvested_servers": len(servers), "harvested_contacts": len(contacts),
            "harvested_urls": len(urls)}


# ---------------------------------------------------------------- 手册初稿生成


def build_blocks(info, rules):
    """把项目信息组装成 docx_io 块序列：11 个标准一级章节 + 缺失要素【待补充】占位段。

    移植自源 generate_draft.build_body；偏差：
      - 输出改为 docx_io 的 block 结构（h/p/ph/table），OOXML 由共享库负责；
      - 封面文字用普通段落（docx_io 无 Title 块，也避免封面被检测逻辑当作章节标题）；
      - 封面下追加【待复核】占位段，明确"未经运维负责人审核不得外发"。
    """
    ph = rules["generate"]["placeholder"]
    marker = rules["generate"]["review_marker"]
    B = []

    def h(level, text):
        B.append({"type": "h", "level": level, "text": text})

    def p(text):
        B.append({"type": "p", "text": text})

    def ph_para(text):
        B.append({"type": "ph", "text": text})

    def tbl(rows):
        # 数据行空单元格统一占位，避免产出空表（源版 table() 同款行为）
        body = [[str(c).strip() or ph for c in row] for row in rows[1:]]
        B.append({"type": "table", "rows": [list(rows[0])] + body, "header": True})

    name = info.get("project_name") or ph

    # 封面
    p("项目维护手册")
    p(str(name))
    p("版本：%s" % info.get("version", "V1.0"))
    p("日期：%s" % info.get("date", ""))
    p("编制：ops-patrol-toolkit 03_manual_standardize（初稿，待运维人员审核）")
    ph_para("%s 本手册为自动生成初稿，文中所有%s处须经运维负责人核实补齐后方可外发。"
            % (marker, ph))

    # 1 文件变更记录
    h(1, "文件变更记录")
    tbl([["版本号", "日期", "变更类型（A*M*D）", "修改人", "摘要", "审核人", "备注"],
         [info.get("version", "V1.0"), info.get("date", ""), "A",
          info.get("author", "AI 初稿生成"), "依据项目立项、建设等阶段资料生成初稿", "", "待审核"]])

    # 2 项目承建内容
    h(1, "项目承建内容")
    h(2, "软件维保概况")
    scope = info.get("project_scope") or {}
    p("项目背景：%s" % (scope.get("背景") or ph))
    p("维保范围：%s" % (scope.get("维保范围") or ph))
    subs = scope.get("子系统清单") or []
    if subs:
        rows = [["序号", "子系统名称", "功能简介"]]
        rows += [[str(i + 1), s.get("名称", ph), s.get("功能简介", ph)]
                 for i, s in enumerate(subs)]
        tbl(rows)
    else:
        ph_para("子系统清单：%s" % ph)
    h(2, "基础地图数据")
    p(str(scope.get("基础地图数据") or ph))

    # 3 服务器配置信息
    h(1, "服务器配置信息")
    servers = info.get("servers") or []
    if servers:
        rows = [["序号"] + list(SERVER_KEYS)]
        rows += [[str(i)] + [str(s.get(k, "")) for k in SERVER_KEYS]
                 for i, s in enumerate(servers, 1)]
        tbl(rows)
    else:
        ph_para("服务器清单：%s（建议从云资源申请表/服务器台账中获取）" % ph)

    # 4 服务器部署信息
    h(1, "服务器部署信息")
    p("通用账号：%s" % (info.get("common_account") or ph))
    svcs = info.get("services") or []
    if svcs:
        h(2, "服务启动命令")
        tbl([["服务器", "服务名称", "启动命令", "说明"]]
            + [[s.get(k, "") for k in ("服务器", "服务名称", "启动命令", "说明")] for s in svcs])
    else:
        ph_para("%s服务启动命令（建议从部署文档/云资源清单中获取）" % ph)
    urls = info.get("access_urls") or []
    if urls:
        h(2, "应用访问地址")
        tbl([["系统/模块", "访问地址"]]
            + [[u.get("名称", ""), u.get("地址", "")] for u in urls])
    else:
        ph_para("%s应用访问地址（建议从立项方案/部署文档中获取）" % ph)

    # 5 应用软件系统
    h(1, "应用软件系统")
    h(2, "数据库服务")
    dbs = info.get("databases") or []
    if dbs:
        tbl([["服务器", "数据库名", "部署软件", "账号/密码", "字符集", "备注"]]
            + [[d.get(k, "") for k in ("服务器", "数据库名", "部署软件", "账号/密码", "字符集", "备注")]
               for d in dbs])
    else:
        ph_para("%s（建议从部署文档/服务器部署信息中获取）" % ph)
    h(2, "web应用服务器")
    webs = info.get("web_apps") or []
    if webs:
        tbl([["服务器", "发布程序", "部署路径", "访问地址", "账号/密码"]]
            + [[w.get(k, "") for k in ("服务器", "发布程序", "部署路径", "访问地址", "账号/密码")]
               for w in webs])
    else:
        ph_para("%s（建议从部署文档中获取各服务器发布程序与路径）" % ph)

    # 6 备份计划
    h(1, "备份计划")
    backup = info.get("backup") or {}
    h(2, "本地备份")
    p(str(backup.get("本地备份") or ph))
    h(2, "异地备份")
    p(str(backup.get("异地备份") or ph))

    # 7 互联网专线
    h(1, "互联网专线")
    line = info.get("internet_line") or []
    if line:
        tbl([["用途", "带宽", "IP", "网关", "备注"]]
            + [[x.get(k, "") for k in ("用途", "带宽", "IP", "网关", "备注")] for x in line])
    else:
        ph_para("无" if info.get("internet_line") == "无"
                else "%s（无专线也需明确写\"无\"）" % ph)

    # 8 端口映射
    h(1, "端口映射")
    ports = info.get("port_mappings") or []
    if ports:
        tbl([["公网地址", "公网端口", "内网地址", "内网端口", "协议", "用途"]]
            + [[pm.get(k, "") for k in ("公网地址", "公网端口", "内网地址", "内网端口", "协议", "用途")]
               for pm in ports])
    else:
        ph_para("无" if info.get("port_mappings") == "无"
                else "%s（无映射也需明确写\"无\"）" % ph)

    # 9 硬件部分
    h(1, "硬件部分")
    hw = info.get("hardware") or []
    if hw:
        tbl([["序号", "设备名称", "型号", "数量", "用途"]]
            + [[str(i + 1), x.get("设备名称", ""), x.get("型号", ""),
                str(x.get("数量", "")), x.get("用途", "")] for i, x in enumerate(hw)])
    else:
        ph_para("无自购硬件" if info.get("hardware") == "无"
                else "%s（无自购硬件也需保留本章节并注明\"无\"）" % ph)

    # 10 联系人信息表
    h(1, "联系人信息表")
    contacts = info.get("contacts") or []
    if contacts:
        tbl([["姓名", "单位", "职位", "电话", "负责事项"]]
            + [[c.get(k, "") for k in CONTACT_KEYS] for c in contacts])
    else:
        ph_para("%s（建议从项目组架构/交接资料中获取甲方、乙方、第三方厂商联系人）" % ph)

    # 11 项目常见问题及解决方法
    h(1, "项目常见问题及解决方法")
    h(2, "常用工具软件存放地址")
    if info.get("tools_location"):
        p(str(info["tools_location"]))
    else:
        ph_para("常用工具软件存放地址：%s（如工具服务器共享目录）" % ph)
    h(2, "常见问题")
    faq = info.get("faq") or []
    if faq:
        tbl([["序号", "问题现象", "解决办法"]]
            + [[str(i + 1), f.get("现象", ""), f.get("解决办法", "")] for i, f in enumerate(faq)])
    else:
        ph_para("%s（建议从故障报告、巡检记录、运维周报中整理）" % ph)

    return B


def _run_self_check(manual_path, rules, report_path):
    """对生成结果自动回跑 check（闭环），差异清单与初稿一起落盘，返回计数。"""
    structure = patrol_lib.read_json(DEFAULT_STRUCTURE)
    terms = (patrol_lib.read_json(DEFAULT_TERMS)).get("terms") or []
    report = audit_manual(manual_path, structure, terms, rules)
    counts = summarize(report)
    patrol_lib.write_text(report_path, render_report(report, "references/standard-structure.json（内置默认）"))
    return counts


# ---------------------------------------------------------------- 子命令


def cmd_extract(a):
    """extract: 读取资料 docx 的段落/表格 -> extracted.json。"""
    try:
        blocks, tables = read_doc(a.docx)
    except DocxReadError as e:
        patrol_lib.stop("无法读取 docx: %s（旧版 .doc 请先在 Word 中另存为 .docx）" % e)
    paras_out = [{"index": b["index"], "type": b["type"], "level": b.get("level"),
                  "style": b.get("style"), "text": b["text"]} for b in blocks]
    counts = {"headings": sum(1 for b in blocks if b["type"] == "heading"),
              "paragraphs": sum(1 for b in blocks if b["type"] == "para"),
              "tables": len(tables)}
    data = {
        "file": str(a.docx),
        "extractor": "ops-patrol-toolkit 03_manual_standardize v%s + docx_io" % __version__,
        "note": "段落与表格分别输出：docx_io 公共 API 不提供表格在正文流中的相对位置；"
                "heading.level 由段落样式（Heading N/标题 N）推断，中文数字样式 ID 识别不到",
        "counts": counts,
        "paragraphs": paras_out,
        "tables": tables,
    }
    out = patrol_lib.write_json(a.out, data)
    print("OK: 提取 %d 个标题、%d 个段落、%d 张表格 -> %s"
          % (counts["headings"], counts["paragraphs"], counts["tables"], out))
    patrol_lib.emit({"cmd": "extract", "docx": str(a.docx), "out": str(out), **counts})
    return 0


def cmd_generate(a):
    """generate: 零散立项资料 -> 11 章节手册初稿，生成后自动回跑 check（闭环）。"""
    rules = load_rules()
    if not a.info:
        patrol_lib.stop("缺少必填参数: --info（项目信息 JSON；键结构参照"
                        " tests/fixtures/patrol/manual/project_info.json 或源 draft-info.template.json 适配）")
    info = patrol_lib.read_json(a.info)
    if not isinstance(info, dict):
        patrol_lib.stop("project_info JSON 顶层应为对象: %s" % a.info)
    if not str(info.get("project_name") or "").strip():
        patrol_lib.stop("project_info 缺少必备键 project_name（项目名称），无法生成手册封面")

    sources = list(a.sources or [])
    harvest_stats = (merge_harvest(info, sources) if sources
                     else {"sources": 0, "parse_failed": 0, "harvested_servers": 0,
                           "harvested_contacts": 0, "harvested_urls": 0})

    # 自检: 抽取计数>0 但值全空 = 映射失败（源样例人工复核记录 2026-09-12 第 3 条，
    # 立即提示而非静默产出空表，踩坑精神保留）
    for key, label in (("servers", "服务器表"), ("contacts", "联系人表")):
        rows = info.get(key) or []
        if rows and not any(any(str(v).strip() for v in row.values()) for row in rows):
            print("警告: 自动抽取的%s共 %d 行但值全为空，大概率是资料表头与预期列名"
                  "（设备名称/IP地址、姓名/电话）差异过大，请检查后重跑或改用 --info 手工填写。"
                  % (label, len(rows)))

    blocks = build_blocks(info, rules)
    out_parent = Path(a.out).parent
    if str(out_parent) not in ("", "."):
        out_parent.mkdir(parents=True, exist_ok=True)
    out_path = docx_io.make_document(a.out, blocks)
    n_ph = sum(1 for b in blocks if b["type"] == "ph")
    filled = sum(1 for k in ("servers", "contacts", "services", "databases",
                             "web_apps", "port_mappings", "faq") if info.get(k))

    # 生成后自动回跑 check（闭环）：P0 应为 0；差异清单与初稿一起交付
    stem = Path(out_path).stem
    report_path = Path(out_path).parent / ("手册差异清单-%s.md" % stem)
    counts = _run_self_check(out_path, rules, report_path)

    print("OK: 初稿已生成 -> %s" % out_path)
    print("    已填充信息块: %d/7（servers/contacts/services/databases/web_apps/port_mappings/faq）" % filled)
    print("    占位段%s: %d 处（请运维人员结合实际资料补齐）" % (rules["generate"]["placeholder"], n_ph))
    print("    自动回检: P0=%d, P1=%d, P2=%d（差异清单: %s）"
          % (counts["p0"], counts["p1"], counts["p2"], report_path))
    if counts["p0"] != 0:
        print("    警告: 自动回检发现 P0 缺失章节，生成结果异常，请人工排查本工具或章节基线。")
    patrol_lib.emit({
        "cmd": "generate",
        "out": out_path,
        "sections": counts["total_sections"],
        "matched": counts["matched"],
        "placeholders": n_ph,
        "filled_blocks": "%d/7" % filled,
        "sources": harvest_stats,
        "self_check": {"p0": counts["p0"], "p1": counts["p1"], "p2": counts["p2"],
                       "matched": counts["matched"], "report": str(report_path)},
    })
    return 0


def cmd_check(a):
    """check: 章节完整性/要素/术语检测 -> 四级差异清单 markdown。"""
    rules = load_rules()
    baseline = a.baseline or str(DEFAULT_STRUCTURE)
    structure = patrol_lib.read_json(baseline)
    terms = (patrol_lib.read_json(a.terms or str(DEFAULT_TERMS))).get("terms") or []
    report = audit_manual(a.manual, structure, terms, rules)
    counts = summarize(report)
    if a.out:
        out_path = str(a.out)
    else:
        out_path = str(patrol_lib.work_path("manual", "手册差异清单-%s.md" % Path(a.manual).stem))
    patrol_lib.write_text(out_path, render_report(report, os.path.basename(baseline)))
    print("检测完成: %s" % a.manual)
    print("    章节完整度 %d/%d；P0 缺失 %d，P1 %d（疑似改名/要素缺失/样式），P2 术语 %d 组"
          % (counts["matched"], counts["total_sections"], counts["p0"], counts["p1"], counts["p2"]))
    print("    差异清单 -> %s（头部带【待复核】，未经人工确认不得外发）" % out_path)
    patrol_lib.emit({
        "cmd": "check",
        "manual": str(a.manual),
        "report": out_path,
        "baseline": os.path.basename(baseline),
        "total_sections": counts["total_sections"],
        "matched": counts["matched"],
        "p0": counts["p0"],
        "p1": counts["p1"],
        "p2": counts["p2"],
        "renamed": len(report["renamed"]),
        "element_missing": len(report["element_missing"]),
        "style_issues": len(report["style_issues"]),
        "extra_headings": len(report["extra_headings"]),
    })
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="03_manual_standardize",
        description="维护手册规范化：extract/generate/check 双模式 + 生成后自动回检闭环")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("extract", help="读取资料 docx 的段落/表格 -> extracted.json")
    p1.add_argument("--docx", required=True, help="输入资料 .docx")
    p1.add_argument("--out", required=True, help="输出 JSON 路径")
    p1.set_defaults(func=cmd_extract)

    p2 = sub.add_parser("generate", help="零散立项资料 -> 标准章节手册初稿（生成后自动回检）")
    p2.add_argument("--info", default=None,
                    help="项目信息 JSON（键结构参照 draft-info.template.json 适配版，必填）")
    p2.add_argument("--sources", action="append", default=None,
                    help="项目原始资料 .docx（可多次指定；自动抽取服务器表/联系人表/访问地址）")
    p2.add_argument("--out", required=True, help="输出初稿 docx 路径")
    p2.set_defaults(func=cmd_generate)

    p3 = sub.add_parser("check", help="章节完整性/要素/术语检测 -> 四级差异清单 markdown")
    p3.add_argument("--manual", required=True, help="待检测手册 .docx")
    p3.add_argument("--baseline", default=None,
                    help="章节结构基线 JSON（缺省 references/standard-structure.json）")
    p3.add_argument("--terms", default=None,
                    help="术语基线 JSON（缺省 references/terminology.json）")
    p3.add_argument("--out", default=None,
                    help="差异清单输出路径（缺省 work/manual/手册差异清单-<文件名>.md）")
    p3.set_defaults(func=cmd_check)

    a = ap.parse_args(argv)
    return a.func(a) or 0


if __name__ == "__main__":
    sys.exit(main())
