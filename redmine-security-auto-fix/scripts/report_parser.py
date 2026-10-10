#!/usr/bin/env python3
"""Normalize heterogeneous vulnerability reports into one JSON schema."""

from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

LEVELS = {
    "严重": "critical",
    "致命": "critical",
    "超危": "critical",
    "critical": "critical",
    "高危": "high",
    "高风险": "high",
    "high": "high",
    "中危": "medium",
    "中风险": "medium",
    "medium": "medium",
    "低危": "low",
    "低风险": "low",
    "low": "low",
    "建议": "info",
    "信息": "info",
    "提示": "info",
    "info": "info",
}

ALIASES = {
    "name": (
        "漏洞名称",
        "漏洞名",
        "弱点名称",
        "风险名称",
        "风险名",
        "问题名称",
        "组件名称",
        "缺陷类型",
        "漏洞类型",
        "标题",
        "name",
        "title",
        "category",
    ),
    "level": (
        "风险等级",
        "风险级别",
        "组件等级",
        "漏洞等级",
        "危险等级",
        "级别",
        "severity",
        "risk",
        "level",
    ),
    "description": (
        "漏洞描述",
        "问题描述",
        "风险描述",
        "漏洞简述",
        "描述",
        "组件来源",
        "问题所在文件",
        "description",
        "detail",
    ),
    "harm": ("漏洞危害", "风险影响", "影响", "危害", "impact", "harm"),
    "fix_suggestion": (
        "加固建议",
        "修复建议",
        "整改建议",
        "解决方案",
        "修复方案",
        "recommendation",
        "remediation",
        "solution",
    ),
    "url": ("漏洞地址", "涉及url", "url", "uri", "位置", "路径"),
    "cve": ("cve", "cve编号"),
    "cwe": ("cwe", "cwe编号"),
    "instances": ("实例数", "数量", "例数", "出现次数", "count", "instances"),
}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _find_key(row: dict, aliases: tuple[str, ...]) -> str:
    lowered = {_clean(k).lower(): v for k, v in row.items()}
    for alias in aliases:
        if alias.lower() in lowered:
            return _clean(lowered[alias.lower()])
    return ""


def _to_int(value: str) -> int:
    """实例数列取数：空值/非数字都退回 0，由调用方决定是否按 1 计。"""
    found = re.search(r"\d+", _clean(value).replace(",", ""))
    return int(found.group(0)) if found else 0


def _normalize_level(value: str) -> str:
    text = _clean(value).lower()
    for key, level in LEVELS.items():
        if key.lower() in text:
            return level
    # Single-character Chinese severity (e.g. "高", "中", "低")
    single = {
        "严重": "critical",
        "高": "high",
        "中": "medium",
        "低": "low",
        "信息": "info",
    }
    for char, level in single.items():
        if char in text:
            return level
    return "medium"


def normalize_rows(rows: list[dict], source_file: str) -> list[dict]:
    vulns = []
    for row in rows:
        name = _find_key(row, ALIASES["name"])
        if not name:
            name = _find_key(row, ("描述",))
        if not name:
            rule = _find_key(row, ("扫描规则",))
            finding = _find_key(row, ("扫描结果",))
            if rule or finding:
                name = f"代码扫描发现：{finding or rule[:80]}"
        if not name:
            continue
        urls = _find_key(row, ALIASES["url"])
        level_raw = _find_key(row, ALIASES["level"])
        cve = _find_key(row, ALIASES["cve"])
        instances = _find_key(row, ALIASES["instances"])
        if not cve:
            # 漏扫表常把 CVE 编号写在漏洞名称里而没有独立列；
            # 抽出来才能进查询词、才能按编号向 NVD 精确补情报
            found = re.search(r"CVE-\d{4}-\d{4,7}", name, re.I)
            if found:
                cve = found.group(0).upper()
        vulns.append(
            {
                "name": name,
                "level": _normalize_level(level_raw),
                # 报告没写等级时 level 会落到默认 medium；留这个标记，
                # 后续才能判断能不能用 CVE 情报回填真实等级
                "level_explicit": bool(level_raw.strip()),
                "description": _find_key(row, ALIASES["description"]),
                "harm": _find_key(row, ALIASES["harm"]),
                "fix_suggestion": _find_key(row, ALIASES["fix_suggestion"]),
                "urls": re.findall(r"https?://[^\s,;]+", urls),
                "cve": cve,
                "cwe": _find_key(row, ALIASES["cwe"]),
                # 汇总表按缺陷类型出条，一"类"背后是几十个实例；
                # 没有这一列文档会把 247 个实例印成 28 个
                "instances": _to_int(instances),
                "source_file": source_file,
            }
        )
    return vulns


def _parse_delimited(path: Path) -> list[dict]:
    for encoding in ("utf-8-sig", "gb18030", "utf-8"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                sample = handle.read(4096)
                handle.seek(0)
                dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
                return list(csv.DictReader(handle, dialect=dialect))
        except (UnicodeDecodeError, csv.Error):
            continue
    raise ValueError(f"Unable to decode delimited report: {path}")


_NVD_NOISE_PREFIX = re.compile(
    r"^\s*(?:\*\*\s*(?:DISPUTED|REJECT|WITHDRAWN)\s*\*\*|Note:)\s*", re.IGNORECASE
)
# NVD 的 Vulnerability 列是整段描述，多数没有 ".This issue" 或句号可截：
# 505980 实测名称中位数 127 字、最长 476 字，总览表格和章节标题直接不能看
_NVD_TITLE_LIMIT = 60
_DEPENDENCY_NAME_LIMIT = 110


def _shorten_nvd_title(text: str, limit: int = _NVD_TITLE_LIMIT) -> str:
    """NVD 描述当漏洞名用：去噪声前缀、截到句界、再压到 limit 字以内。"""
    title = _NVD_NOISE_PREFIX.sub("", str(text or "")).strip()
    title = re.split(r"\.This issue\b|\.\s", title)[0].strip(" .") or title
    if len(title) <= limit:
        return title
    clipped = title[:limit].rsplit(" ", 1)[0].rstrip(" ,;:，。；：")
    return f"{(clipped or title[:limit]).rstrip()}…"


def _dependency_check_name(title: str, cve: str, component: str) -> str:
    """dependency-check 条目名称：短标题 + CVE + 组件，整体有上限。

    CVE 必须进名称：这批条目不带 CVE 号就没法对账、也没法查安全漏洞台账；
    标题截断后也靠它保证不同 CVE 不会被合并成一类。
    """
    suffix = "、".join(part for part in (cve, component) if part)
    if not suffix:
        return title
    room = _DEPENDENCY_NAME_LIMIT - len(suffix) - 2
    if len(title) > max(room, 20):
        title = _shorten_nvd_title(title, max(room, 20))
    return f"{title}（{suffix}）"


def _normalize_dependency_check_rows(rows: list[dict]) -> list[dict]:
    """OWASP dependency-check CSV：一行一个「组件 × CVE」。

    列名是 DependencyName / CVE / Vulnerability / CVSSv3_BaseSeverity 这套，
    ALIASES 一个都命中不了（只有 NVD 元数据的 Name 列偶尔有值，且多为空），
    不认这个格式就会出现 49 行只解析出 1 条的漏抽。
    """
    if not rows or not {"DependencyName", "CVE", "Vulnerability"} <= set(rows[0].keys()):
        return []
    normalized = []
    for row in rows:
        cve = _clean(row.get("CVE"))
        vuln = _clean(row.get("Vulnerability"))
        if not cve and not vuln:
            continue
        # NVD 描述形如「<标题> vulnerability in <产品>.This issue affects ...」，
        # 标题截到 ".This issue" 或首个句号，全量描述放漏洞描述列
        title = _shorten_nvd_title(vuln)
        dependency = _clean(row.get("DependencyName"))
        component = dependency.split(":")[-1].strip() if dependency else ""
        severity = _clean(row.get("CVSSv3_BaseSeverity")) or _clean(
            row.get("CVSSv2_Severity")
        )
        cwe = re.search(r"CWE-\d+", _clean(row.get("CWE")))
        normalized.append(
            {
                "漏洞名称": _dependency_check_name(title, cve, component),
                "漏洞等级": severity,
                "漏洞描述": vuln,
                "加固建议": _clean(row.get("ShortDescription")),
                "CVE": cve,
                "CWE": cwe.group(0) if cwe else "",
            }
        )
    return normalized


def _parse_excel(path: Path) -> list[dict]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("Excel parsing requires pandas and openpyxl/xlrd") from exc
    sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=str)
    rows = []
    for sheet_name, frame in sheets.items():
        frame = frame.fillna("")
        if frame.empty or len(frame.columns) == 0:
            continue
        header_index = 0
        best_score = -1
        aliases = {
            alias.lower()
            for values in ALIASES.values()
            for alias in values
        } | {"扫描规则", "扫描结果", "整改建议", "组件名称", "风险名称"}
        for index in range(min(20, len(frame))):
            values = [_clean(value).lower() for value in frame.iloc[index].tolist()]
            score = sum(1 for value in values if value in aliases)
            if score > best_score:
                header_index = index
                best_score = score
        headers = [
            _clean(value) or f"column_{column}"
            for column, value in enumerate(frame.iloc[header_index].tolist())
        ]
        data = frame.iloc[header_index + 1 :].copy()
        data.columns = headers
        for row in data.to_dict(orient="records"):
            row["_sheet"] = sheet_name
            rows.append(row)
    return rows


def _merge_heading_with_tables(heading_rows: list[dict], table_rows: list[dict]) -> list[dict]:
    if not heading_rows or not table_rows:
        return heading_rows or table_rows

    def bigrams(text: str) -> set[str]:
        chars = re.sub(r"[\d.\-a-z_/\\]+", "", text or "", flags=re.I)
        return {chars[i:i+2] for i in range(len(chars) - 1)}

    def keywords(text: str) -> set[str]:
        return set(re.findall(r"[\u4e00-\u9fff]{2,}", text or ""))

    # Build a score matrix between every heading and every table, then assign
    # greedily by descending score so a strong match is never stolen by an
    # earlier heading that only weakly overlaps the same table.
    scores: list[tuple[float, int, int]] = []
    heading_bigrams = [(bigrams(h.get("漏洞名称") or ""), keywords(h.get("漏洞名称") or "")) for h in heading_rows]
    table_bigrams = [(bigrams(t.get("漏洞名称") or ""), keywords(t.get("漏洞名称") or "")) for t in table_rows]
    for hi, (hb, hk) in enumerate(heading_bigrams):
        hname = heading_rows[hi].get("漏洞名称") or ""
        for ti, (tb, tk) in enumerate(table_bigrams):
            tname = table_rows[ti].get("漏洞名称") or ""
            score = len(hb & tb) * 1.5 + len(hk & tk) * 2.0
            if hname in tname or tname in hname:
                score += 10
            scores.append((score, hi, ti))

    heading_to_table: dict[int, int] = {}
    used_tables: set[int] = set()
    for score, hi, ti in sorted(scores, key=lambda x: x[0], reverse=True):
        if score < 2 or hi in heading_to_table or ti in used_tables:
            continue
        heading_to_table[hi] = ti
        used_tables.add(ti)

    result: list[dict] = []
    for hi, heading in enumerate(heading_rows):
        ti = heading_to_table.get(hi)
        if ti is None:
            result.append(heading)
            continue
        table_row = table_rows[ti]
        merged = dict(heading)
        for field in ("漏洞描述", "漏洞危害", "加固建议", "漏洞地址", "风险等级"):
            if not merged.get(field) and table_row.get(field):
                merged[field] = table_row[field]
        result.append(merged)
    return result


# 目录行：正文标题在 Word 里带"制表符+页码"后缀，正文里同样的标题没有
_DOCX_TOC_LINE = re.compile(r"\t+\d+\s*$")
# 纯章节标题：渗透报告的目录和正文里大量"二、漏洞类型测试结果"这类标题，
# 含"漏洞"二字，会被段落解析的关键词规则误收成漏洞条目
_DOCX_SECTION_TITLE = re.compile(
    r"(测试结果|状况说明|问题归纳|风险总结|安全现状|测试目的|测试依据|测试工具|"
    r"测试范围|设计原则|附录)$"
)


def _parse_docx(path: Path) -> list[dict]:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("DOCX parsing requires python-docx") from exc

    doc = Document(path)
    rows = []
    for table in doc.tables:
        if not table.rows:
            continue
        vertical = {}
        vertical_keys = {
            "风险名称": "漏洞名称",
            "漏洞名称": "漏洞名称",
            "问题名称": "漏洞名称",
            "检测项": "漏洞名称",
            "检测目": "漏洞名称",
            "检测内容": "漏洞名称",
            "风险级别": "风险等级",
            "风险等级": "风险等级",
            "漏洞等级": "风险等级",
            "风险描述": "漏洞描述",
            "漏洞描述": "漏洞描述",
            "漏洞危害": "漏洞危害",
            "风险影响": "漏洞危害",
            "风险分析": "漏洞危害",
            "结果描述": "漏洞危害",
            "加固建议": "加固建议",
            "修复建议": "加固建议",
            "整改建议": "加固建议",
            "解决方案": "加固建议",
            "漏洞链接": "漏洞地址",
            "涉及URL": "漏洞地址",
        }
        for table_row in table.rows:
            values = [_clean(cell.text) for cell in table_row.cells]
            if len(values) >= 2:
                label = values[0]
                matched = next(
                    (v for k, v in vertical_keys.items() if k in label),
                    None,
                )
                if matched:
                    vertical[matched] = values[1]
        if vertical.get("漏洞名称"):
            rows.append(vertical)
            continue
        headers = [_clean(cell.text) for cell in table.rows[0].cells]
        if not any(headers):
            continue
        for table_row in table.rows[1:]:
            values = [_clean(cell.text) for cell in table_row.cells]
            rows.append(dict(zip(headers, values)))

    paragraph_records = [
        (paragraph.text.strip(), paragraph.style.name or "")
        for paragraph in doc.paragraphs
        if paragraph.text.strip()
    ]
    heading = re.compile(
        r"(?:【(?P<level>严重|高危|中危|低危|信息)】|\[(?P<level_en>critical|high|medium|low|info)\])?\s*"
        r"(?P<name>[^\n：:]{3,100})(?:\*(?P<count>\d+))?$",
        re.I,
    )
    explicit_heading = re.compile(
        r"^(?:【(?P<level>严重|高危|中危|低危|信息)】|\[(?P<level_en>critical|high|medium|low|info)\])\s*"
        r"(?P<name>.+)$",
        re.I,
    )
    section_re = re.compile(
        r"^(漏洞描述|问题描述|漏洞危害|影响|漏洞简述|测试过程|加固建议|修复建议|整改建议|解决方案|建议)[：:]?\s*(.*)$",
        re.I,
    )
    # 段落式漏洞清单："1、硬编码明文默认口令" + "建议：..."。这类条目名往往不含
    # "漏洞/注入"等关键词，靠编号后的建议标签反推它是漏洞条目，否则整段被丢弃。
    # level/level_en 是与 heading 同名占位组，让下面的 group() 调用无需分支。
    numbered_item = re.compile(
        r"^\d{1,2}\s*[、.．]\s*(?P<level>)(?P<level_en>)(?P<name>[^\n：:]{3,80})$"
    )
    suggestion_label = re.compile(
        r"^(?:加固建议|修复建议|整改建议|处置建议|解决方案|修复方案|整改措施|建议)[：:]?\s*(.*)$"
    )
    numbered_heading_idx = set()
    for idx, (line, _style) in enumerate(paragraph_records):
        if not numbered_item.match(line):
            continue
        for follow, _s in paragraph_records[idx + 1: idx + 8]:
            if numbered_item.match(follow):
                break
            if suggestion_label.match(follow):
                numbered_heading_idx.add(idx)
                break
    # 段落小节标签 → 规范字段名。内联内容（"漏洞描述：xxx"）与续行都要落到同一个
    # 中文键上，否则 normalize_rows 的 _find_key 取不到。
    section_keys = {
        "description": "漏洞描述",
        "harm": "漏洞危害",
        "fix_suggestion": "加固建议",
    }
    has_styled_headings = any(
        style.lower().startswith("heading") and explicit_heading.match(line)
        for line, style in paragraph_records
    )
    current = None
    current_section = None
    for idx, (line, style) in enumerate(paragraph_records):
        # 目录行（带页码后缀）和纯章节标题既不当条目名，也不当小节正文：
        # 渗透报告目录里"二、漏洞类型测试结果"含"漏洞"二字，会被关键词规则
        # 误收成漏洞；章节标题混进建议正文也是灌水
        if _DOCX_TOC_LINE.search(line) or _DOCX_SECTION_TITLE.search(_clean(line)):
            continue
        section = section_re.match(line)
        if section and current:
            label, content = section.groups()
            current_section = (
                "fix_suggestion"
                if any(x in label for x in ("建议", "方案"))
                else "harm"
                if any(x in label for x in ("危害", "影响"))
                else "description"
            )
            if content:
                current[section_keys[current_section]] = content
            continue
        # 编号条目优先：heading 也会整行匹配上，但会把"1、"前缀留在名称里
        match = numbered_item.match(line) if idx in numbered_heading_idx else None
        if match is None:
            match = (
                explicit_heading.match(line)
                if has_styled_headings
                else heading.match(line)
            )
        is_heading = bool(
            match
            and (
                has_styled_headings
                and style.lower().startswith("heading")
                or not has_styled_headings
                and (
                    match.group("level")
                    or match.group("level_en")
                    or idx in numbered_heading_idx
                    or any(
                        word in line
                        for word in ("漏洞", "注入", "跨站", "越权", "泄露")
                    )
                )
            )
        )
        if is_heading:
            if current:
                rows.append(current)
            current = {
                "漏洞名称": match.group("name"),
                "风险等级": match.group("level") or match.group("level_en") or "",
                "漏洞描述": "",
                "漏洞危害": "",
                "加固建议": "",
                "source": "paragraph",
            }
            current_section = None
        elif current and current_section:
            key = section_keys[current_section]
            current[key] = _clean(f"{current.get(key, '')} {line}")
    if current:
        rows.append(current)

    if rows:
        table_rows = [r for r in rows if r.get("漏洞名称") and (r.get("source") != "paragraph")]
        para_rows = [r for r in rows if r.get("source") == "paragraph"]
        rows = _merge_heading_with_tables(para_rows, table_rows)
    return rows


_PENTEST_LABEL = re.compile(
    r"^(漏洞危害|危害|详细信息|漏洞详情|漏洞描述|漏洞URL|漏洞地址|涉及URL|"
    r"测试过程|加固建议|修复建议|整改建议|处置建议)[：:]?\s*(.*)$"
)
# 证据附录：HTTP 原始包头和"数据包如下"这类引导语，进描述只是灌水
_PENTEST_HTTP_NOISE = re.compile(
    r"^(?:[A-Za-z][A-Za-z0-9-]*:\s|"
    r"(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|TRACE|CONNECT)\s+\S+\s+HTTP)"
)
_PENTEST_PACKET_LEAD = ("数据包如下", "请求如下", "响应如下", "数据包")


def _pentest_narrative(paragraphs: list[str], name: str) -> dict:
    """在叙述段落里按条目名找回 危害/详情/过程/建议/URL 各节。

    条目名在正文里可能比测试项表里的短（表里"垂直越权访问"、正文"垂直越
    权"），互相包含即算命中；目录行和章节标题不是条目名。
    """
    start = None
    for index, text in enumerate(paragraphs):
        if _DOCX_TOC_LINE.search(text):
            continue
        cleaned = _clean(text)
        if _DOCX_SECTION_TITLE.search(cleaned):
            continue
        if (name in cleaned or cleaned in name) and len(cleaned) <= len(name) + 6:
            start = index
            break
    sections = {"description": "", "harm": "", "fix": "", "url": ""}
    if start is None:
        return sections
    current = None
    for text in paragraphs[start + 1 :]:
        cleaned = _clean(text)
        if not cleaned or cleaned.startswith("图"):
            continue
        if (
            _DOCX_SECTION_TITLE.search(cleaned)
            or re.match(r"^\d+\.\d", cleaned)
            or re.match(r"^[一二三四五]、", cleaned)
        ):
            break
        if _PENTEST_HTTP_NOISE.match(cleaned) or cleaned in _PENTEST_PACKET_LEAD:
            continue
        label = _PENTEST_LABEL.match(cleaned)
        if label:
            head, content = label.groups()
            # "测试过程如下："这类引导语不是内容
            if content.strip("：: ") in ("如下", ""):
                content = ""
            current = (
                "fix"
                if any(word in head for word in ("建议", "措施"))
                else "harm"
                if "危害" in head or head == "影响"
                else "url"
                if "URL" in head or "地址" in head
                else "description"
            )
            if content:
                sections[current] = _clean(f"{sections[current]} {content}")
            continue
        if current == "url":
            found = re.search(r"https?://[^\s，。;；]*", cleaned)
            if found:
                sections["url"] = found.group(0).rstrip("等")
            continue
        if current:
            sections[current] = _clean(f"{sections[current]} {cleaned}")
    return {key: value[:1500] for key, value in sections.items()}


def _parse_pentest_result_docx(path: Path) -> list[dict]:
    """渗透测试结果报告：测试项矩阵里非"通过"的那几行才是漏洞。

    这类报告（实测 535109）正文全是叙述段落，通用段落解析会把目录和章节
    标题当漏洞收进来；漏洞清单其实在一张「测试分类/测试项/测试结果」大表
    里——125 行只有一行不是"通过"，另有「系统名称/严重漏洞/高危漏洞/…」
    统计表给等级，叙述段按条目名找回危害/过程/URL/建议。
    """
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("DOCX parsing requires python-docx") from exc

    doc = Document(path)
    failing: list[str] = []
    level_counts: dict[str, int] = {}
    for table in doc.tables:
        if not table.rows:
            continue
        headers = [_clean(cell.text) for cell in table.rows[0].cells]
        if any("测试项" in h for h in headers) and any("测试结果" in h for h in headers):
            item_at = next(i for i, h in enumerate(headers) if "测试项" in h)
            result_at = next(i for i, h in enumerate(headers) if "测试结果" in h)
            for table_row in table.rows[1:]:
                values = [_clean(cell.text) for cell in table_row.cells]
                if len(values) <= max(item_at, result_at):
                    continue
                if values[result_at] and values[result_at] != "通过":
                    failing.append(values[item_at])
        elif any("严重漏洞" in h for h in headers) and any("高危漏洞" in h for h in headers):
            level_at = {
                index: level
                for index, header in enumerate(headers)
                for level in ("严重", "高危", "中危", "低危")
                if level in header
            }
            for table_row in table.rows[1:]:
                values = [_clean(cell.text) for cell in table_row.cells]
                for index, level in level_at.items():
                    if index < len(values) and values[index].isdigit():
                        level_counts[level] = level_counts.get(level, 0) + int(
                            values[index]
                        )
    if not failing:
        return []
    level = ""
    nonzero = [(lv, count) for lv, count in level_counts.items() if count]
    # 只有一档非零且例数对得上才回填等级；对不上就留空，交给 CVE 情报补
    if len(nonzero) == 1 and nonzero[0][1] == len(failing):
        level = nonzero[0][0]
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    rows = []
    for name in failing:
        detail = _pentest_narrative(paragraphs, name)
        rows.append(
            {
                "漏洞名称": name,
                "风险等级": level,
                "漏洞描述": detail["description"],
                "漏洞危害": detail["harm"],
                "加固建议": detail["fix"],
                "漏洞地址": detail["url"],
                "source": "pentest_result_docx",
            }
        )
    return rows


def _parse_pdf(path: Path) -> list[dict]:
    rows = []
    text_parts = []
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        text_parts = [(page.extract_text() or "") for page in reader.pages]
    except ImportError:
        pass
    except Exception:
        text_parts = []

    if not any(part.strip() for part in text_parts):
        try:
            import pdfplumber
        except ImportError as exc:
            raise RuntimeError("PDF parsing requires pypdf or pdfplumber") from exc
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
                for table in page.extract_tables() or []:
                    if len(table) < 2:
                        continue
                    headers = [_clean(cell) for cell in table[0]]
                    rows.extend(dict(zip(headers, row)) for row in table[1:])
    text = "\n".join(text_parts)
    specialized = _parse_seczone_iast_pdf(text)
    if specialized:
        return specialized
    specialized = _parse_cn_audit_report_pdf(text)
    if specialized:
        return specialized
    specialized = _parse_cn_audit_detail_pdf(text)
    if specialized:
        return specialized
    specialized = _parse_cn_source_scan_pdf(text)
    if specialized:
        return specialized
    specialized = _parse_fortify_cwe_top25_pdf(text)
    if specialized:
        return specialized
    specialized = _parse_fortify_dev_workbook_pdf(text)
    if specialized:
        return specialized
    specialized = _parse_appscan_pdf(text)
    if specialized:
        return specialized
    specialized = _parse_zap_pdf(text)
    if specialized:
        return specialized
    specialized = _parse_fortify_pdf(text)
    if specialized:
        return specialized
    cve_bulletin = _parse_cve_bulletin(text)
    if cve_bulletin:
        return cve_bulletin
    if rows:
        normalized = normalize_rows(rows, path.name)
        if normalized:
            return rows
    return _parse_labeled_text(text)


def _parse_seczone_iast_pdf(text: str) -> list[dict]:
    """安全岛（seczone / vulHunter）IAST 交互式应用安全测试报告。

    结构：`安全弱点分布` 段按弱点类型逐块给
    `<弱点名> / 严重性：X / 风险：… / 解决方法：…`，块内挂若干
    `安全弱点：…` 实例条目（位置 + `状态：新发现` + 数据流跟踪）。
    一个类型出一条（带实例数与代表位置），不展开代码片段——
    SQL注入一个类型的解决方案跨 17 页代码，展开没有增量价值。
    """
    if "安全弱点分布" not in text and "安全弱点详情" not in text:
        return []
    if "seczone" not in text and "vulHunter" not in text:
        return []

    heads = list(
        re.finditer(
            r"(?P<name>[^\n：:]{2,60})\n严重性[：:]\s*(?P<sev>[^\n：:]{1,10})",
            text,
        )
    )
    if not heads:
        return []

    rows = []
    seen = set()
    for index, match in enumerate(heads):
        name = _clean(match.group("name"))
        # 页眉页脚、"安全弱点详情:"这类标签不是弱点名
        if (
            not name
            or name in seen
            or name.startswith("安全弱点")
            or re.fullmatch(r"[\d\s/]+", name)
            or "让企业交付更安全" in name
        ):
            continue
        seen.add(name)
        end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
        block = text[match.start() : end]

        risk_match = re.search(
            r"风险[：:]\s*(.*?)(?=\n解决方法[：:]|\n安全弱点[：:]|\Z)", block, re.S
        )
        fix_match = re.search(
            r"解决方法[：:]\s*(.*?)(?=\n安全弱点[：:]|\Z)", block, re.S
        )
        locations: list[str] = []
        for location in re.findall(r"安全弱点[：:]\s*\n?\s*([^\n]{2,200})", block):
            location = _clean(location)
            if location and location not in locations:
                locations.append(location)
        status_hits = re.findall(r"状态[：:]\s*(\S+)", block)
        statuses = sorted({_clean(s) for s in status_hits})
        instances = len(status_hits) or len(locations) or 1

        parts = []
        if risk_match:
            parts.append(_clean(risk_match.group(1))[:600])
        if statuses:
            parts.append("状态：" + "、".join(statuses))
        if locations:
            shown = locations[:4]
            tail = f"等共 {len(locations)} 处" if len(locations) > len(shown) else ""
            parts.append("涉及位置：" + "；".join(shown) + tail)
        rows.append(
            {
                "漏洞名称": name,
                "风险等级": match.group("sev"),
                "漏洞描述": _clean("；".join(parts))[:1500],
                "加固建议": _clean(fix_match.group(1))[:3000] if fix_match else "",
                "实例数": instances,
                "source": "seczone_iast",
            }
        )
    return rows


def _parse_cn_audit_report_pdf(text: str) -> list[dict]:
    """国产代码审计缺陷报告（深圳网安等检测机构出具）。

    结构：`2. 发现缺陷类型汇总` 一张表（序号 缺陷类型 严重/高/中/合计），
    然后 `3. 缺陷列表` 逐条列 `3.N. 等级：文件:行号 + 缺陷详情 + 缺陷类型`。
    逐条展开会有上千行代码片段，对出修复方案没有增量价值，按缺陷类型汇总出条。
    """
    if "缺陷列表" not in text or "缺陷类型" not in text:
        return []

    rows = []
    seen = set()
    for m in re.finditer(
        r"^(?P<idx>\d{1,3})\s+(?P<name>\S.*?[^\s\d])\s+"
        r"(?P<critical>\d+)\s+(?P<high>\d+)\s+(?P<medium>\d+)\s+(?P<total>\d+)\s*$",
        text,
        re.M,
    ):
        name = _clean(m.group("name"))
        if not name or name in seen:
            continue
        seen.add(name)
        critical, high, medium, total = (
            int(m.group(k)) for k in ("critical", "high", "medium", "total")
        )
        if total <= 0:
            continue
        # 等级看落在哪一列：汇总表同一类型只可能出现在一档
        level = (
            "critical" if critical else
            "high" if high else
            "medium" if medium else
            "low"
        )
        rows.append(
            {
                "漏洞名称": name,
                "风险等级": level,
                "漏洞描述": _clean(
                    f"共 {total} 例（严重 {critical}／高 {high}／中 {medium}）"
                )[:1500],
                "加固建议": "",
                "实例数": total,
                "source": "cn_audit_report",
            }
        )
    return rows


def _parse_cn_audit_detail_pdf(text: str) -> list[dict]:
    """国产代码审计报告详情段：`1、SQL 注入` + 漏洞描述/漏洞类型/漏洞等级/整改建议。

    这类报告不设"漏洞名称"标签，编号标题本身就是漏洞名；条目之间靠编号标题
    分隔。汇总表里也有"1."但编号单独成行、名称在下一行，匹配不上，不会重复收。
    """
    if "漏洞描述" not in text:
        return []
    if not re.search(r"(?:整改建议|加固建议|修复建议)", text):
        return []

    heads = list(
        re.finditer(r"^\s*\d{1,2}\s*[、.．]\s*([^\n：:]{2,60}?)\s*$", text, re.M)
    )
    if len(heads) < 2:
        return []

    rows = []
    seen = set()
    for index, match in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
        block = text[match.end() : end]
        name = _clean(match.group(1))
        if not name or name in seen:
            continue
        seen.add(name)
        row = {"漏洞名称": name}
        for field, labels in {
            "风险等级": ("漏洞等级", "风险等级", "危险等级"),
            "漏洞描述": ("漏洞描述", "问题描述"),
            "加固建议": ("整改建议", "加固建议", "修复建议", "解决方案"),
        }.items():
            pattern = "|".join(re.escape(label) for label in labels)
            found = re.search(
                rf"(?:{pattern})[：:]\s*(.*?)(?=\n\s*(?:漏洞描述|问题描述|漏洞类型|漏洞等级|风险等级|"
                rf"加固建议|修复建议|整改建议|解决方案|漏洞链接)[：:]|\Z)",
                block,
                re.S,
            )
            row[field] = _clean(found.group(1))[:1500] if found else ""
        # 汇总表/说明文字里的编号行取不到任何详情标签，不当成漏洞条目
        if not (row["漏洞描述"] or row["加固建议"] or row["风险等级"]):
            continue
        rows.append(row)
    return rows


def _parse_cn_source_scan_pdf(text: str) -> list[dict]:
    """国产静态源代码扫描报告（中正检测等平台导出）。

    结构：开头是缺陷类型统计表（`漏洞名称 风险类别 数量`），正文按
    `<缺陷类型>   ( N例)` 标题分块，块内是 `Path1/入口点/出口点 + 代码 + 审计备注`。
    一条缺陷类型出一行（含例数、等级、涉及文件），不展开每条 Path——
    展开会把 195 页代码全塞进结果，对出修复方案没有增量价值。
    """
    if not any(k in text for k in ("源代码扫描", "静态检测", "中正检测", "zhongzheng")):
        return []

    # 统计表给等级；已确认表是整齐的 `名称 等级 数量` 三列，优先取它
    severity: dict[str, tuple[str, int]] = {}
    for m in re.finditer(
        r"^(?P<name>[^\n：:]{2,60}?)\s+(?P<level>高|中|低)\s+(?P<count>\d+)\s*$",
        text,
        re.M,
    ):
        name = _clean(m.group("name"))
        if name and name not in severity:
            severity[name] = (m.group("level"), int(m.group("count")))

    heads = list(
        re.finditer(
            r"^(?P<name>[^\n：:]{2,60}?)\s*[（(]\s*(?P<count>\d+)\s*例\s*[)）]\s*$",
            text,
            re.M,
        )
    )
    if not heads:
        return []

    rows = []
    seen = set()
    for index, match in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
        block = text[match.end() : end]
        name = _clean(match.group("name"))
        if not name or name in seen:
            continue
        seen.add(name)
        level, stat_count = severity.get(name, ("", 0))
        count = int(match.group("count")) or stat_count

        files: list[str] = []
        for fm in re.finditer(r"(?:入口点|出口点)\s+(\S+)", block):
            path = _clean(fm.group(1))
            # 有的块"入口点"后面直接跟"审计备注"，没有路径；按路径形态过滤
            if not path or not re.search(r"[\\/]|\.\w{1,5}$", path):
                continue
            if path not in files:
                files.append(path)
        paths = len(re.findall(r"Path\d+\s*:", block))

        parts = []
        if count:
            parts.append(f"共 {count} 例")
        if paths and paths != count:
            parts.append(f"{paths} 条路径")
        if files:
            parts.append(f"涉及 {len(files)} 个代码位置：" + "、".join(files[:12]))
        rows.append(
            {
                "漏洞名称": name,
                "风险等级": level,
                "漏洞描述": _clean("；".join(parts))[:1500],
                "加固建议": "",
                "实例数": count,
                "source": "cn_source_scan",
            }
        )
    # 至少一个类型名要能在统计表里对上，否则视为正文里偶然出现的"（N例）"
    if not any(name in severity for name in seen):
        return []
    return rows


def _parse_fortify_pdf(text: str) -> list[dict]:
    matches = list(
        re.finditer(
            r"Category:\s*(?P<name>.+?)\s*\((?P<count>\d+)\s+Issues?\)",
            text,
            re.I,
        )
    )
    rows = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end() : end]
        level_match = re.search(
            r"Fortify Priority:\s*(Critical|High|Medium|Low)", block, re.I
        )
        recommendation = ""
        recommendation_match = re.search(
            r"(?:Recommendations?|Recommendation Summary)\s*[:\n]\s*(.*?)(?=\n(?:[A-Z][A-Za-z ]{2,}:|Category:)|\Z)",
            block,
            re.S,
        )
        if recommendation_match:
            recommendation = _clean(recommendation_match.group(1))[:3000]
        rows.append(
            {
                "漏洞名称": _clean(match.group("name")),
                "风险等级": level_match.group(1) if level_match else "",
                "漏洞描述": _clean(block[:1500]),
                "加固建议": recommendation,
            }
        )
    return rows


_FORTIFY_LEVEL_CN = {
    "critical": "严重",
    "high": "高危",
    "medium": "中危",
    "low": "低危",
}


def _parse_fortify_cwe_top25_pdf(text: str) -> list[dict]:
    """Fortify Audit Workbench「CWE Top 25 / SANS Top 25」导出。

    三种变体：
    - 英文实例式：`[N] CWE ID xxx` 分节，官方弱点全名 + 每实例 `Package:` 块
    - 英文分类表式：节内是 Fortify Category 汇总表（名称 例数 已审 工时 +
      `Critical N M` 行），没有 Package 实例
    - 中文 SANS 式：`<分组> - CWE ID xxx` 分节，中文描述 + `分类 等级` 行 +
      Package 实例
    节的开头在目录里也会出现一次（空节），靠"能否取到弱点名"跳过。
    """
    if "Fortify Audit Workbench" not in text or not re.search(r"CWE Top 25|SANS Top 25", text):
        return []
    heads = list(
        re.finditer(
            r"^(?:\[(?:\d{1,2})\]\s*CWE ID\s*(?P<id>\d{2,4})"
            r"|(?:Risky Resource Management|Insecure Interaction|Porous Defenses)"
            r"\s*-\s*CWE ID\s*(?P<id2>\d{2,4}))\s*$",
            text,
            re.M,
        )
    )
    if len(heads) < 3:
        return []
    rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    rows = []
    seen: set[str] = set()

    def _add(name: str, cwe_id: int, level: str, desc: str, instances: int) -> None:
        if not name or name in seen or not instances:
            return
        seen.add(name)
        rows.append(
            {
                "漏洞名称": name,
                "风险等级": _FORTIFY_LEVEL_CN.get(level, ""),
                "漏洞描述": desc[:1500],
                "CWE": f"CWE-{cwe_id}",
                "实例数": instances,
            }
        )

    for index, match in enumerate(heads):
        cwe_id = int(match.group("id") or match.group("id2"))
        end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
        block = text[match.end() : end]
        # 弱点名：英文官方全名 / 中文官方全名 / SANS 中文首句（也用来跳过目录空节）
        desc = ""
        short = ""
        full = re.search(r'CWE-\d+ is used to identify an? "(.+?)" weakness', block, re.S)
        cn_full = re.search(r'CWE-\d+\s*用于识别[“"](.+?)[”"]缺陷', block, re.S)
        cn = re.search(r"^\s*([^。\n]{4,60}?)。\s*CWE-\d+\s*声明", block, re.M)
        if full:
            occur = re.search(r'These weaknesses occur because "(.+?)"', block, re.S)
            desc = _clean(occur.group(1)) if occur else _clean(full.group(1))
            full_name = re.sub(r"(\w)-\s+(\w)", r"\1-\2", _clean(full.group(1)))
            short_m = re.search(r"\('([^']{3,80})'\)", full_name)
            short = short_m.group(1).rstrip("）) ") if short_m else full_name
        elif cn_full:
            occur = re.search(r'出现这些缺陷是因为[“"](.+?)[”"]', block, re.S)
            desc = _clean(occur.group(1)) if occur else _clean(cn_full.group(1))
            full_name = re.sub(r"(\w)-\s+(\w)", r"\1-\2", _clean(cn_full.group(1)))
            short_m = re.search(r"\('([^']{3,80})'\)", full_name)
            short = short_m.group(1).rstrip("）) ") if short_m else full_name
        elif cn:
            short = _clean(cn.group(1))
            paren = re.search(r"（([^（）]{2,40})）", short)
            if paren:
                short = paren.group(1).strip("“”\" ")
            desc = _clean(cn.group(1))
        else:
            continue  # 目录里的空节

        if cn:
            # SANS 中文式：`分类 等级` 行后跟 Package 实例，按分类出条
            parts = re.split(
                r"\n(?=[^\n]{2,80}\s+(?:Critical|High|Medium|Low)\s*\n\s*Package:)", block
            )
            for part in parts[1:]:
                pm = re.match(r"\s*([^\n]{2,80}?)\s+(Critical|High|Medium|Low)\s*\n\s*Package:", part)
                if not pm:
                    continue
                packages = len(re.findall(r"^\s*Package:", part, re.M))
                _add(f"CWE-{cwe_id} {_clean(pm.group(1))}", cwe_id, pm.group(2).lower(), desc, packages)
            continue

        # 英文分类表式：`分类 例数 已审 工时` 行，等级在下一行 `Critical N M`。
        # 分类名里允许冒号（"Cross-Site Scripting: DOM"）
        table = re.finditer(
            r"^\s*(?P<cat>[A-Z][^\n]{2,70}?)\s+(?P<n>\d{1,4})\s+(?P<aud>\d{1,4})\s+(?P<eff>[\d.]+)\s*$\n?"
            r"(?:\s*(?P<pri>Critical|High|Medium|Low)\s+\d{1,4}\s+\d{1,4}\s*$)?",
            block,
            re.M,
        )
        table_rows = 0
        for tm in table:
            _add(f"CWE-{cwe_id} {_clean(tm.group('cat'))}", cwe_id, (tm.group("pri") or "").lower(), desc, int(tm.group("n")))
            table_rows += 1
        if table_rows:
            continue

        # 英文实例式：Remediation Effort 行带等级，Package 计实例，按节出一行
        packages = len(re.findall(r"^\s*Package:", block, re.M))
        if packages:
            levels = re.findall(
                r"Remediation Effort(?:\s*\(Hrs\))?\s*:\s*[\d.]+\s*(Critical|High|Medium|Low)",
                block,
                re.I,
            )
            rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            best_level = max((lev.lower() for lev in levels), key=lambda x: rank.get(x, 0), default="")
            _add(f"CWE-{cwe_id} {short}", cwe_id, best_level, desc, packages)
    return rows


def _parse_fortify_dev_workbook_pdf(text: str) -> list[dict]:
    """Fortify Audit Workbench「Developer Workbook」导出。

    Results Outline 按 `<分类名> (N issues)` 分块，块内是 Abstract /
    Explanation / Recommendation 三段加 `Package:` 实例清单，等级词紧跟在
    Package 行前一行（`<分类名> Critical`）。
    """
    if "Fortify Audit Workbench" not in text or "Developer Workbook" not in text:
        return []
    heads = list(
        re.finditer(r"^\s*(?P<name>\S[^\n]{2,90}?)\s*\(\s*(?P<count>\d{1,5})\s+issues?\s*\)\s*$", text, re.M)
    )
    # 单分类的报告（只有一条 "(N issues)"）也是合法的
    if not heads:
        return []
    rows = []
    seen: set[str] = set()
    for index, match in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
        block = text[match.end() : end]
        if "Explanation" not in block and "Recommendation" not in block:
            continue
        name = _clean(match.group("name"))
        if name in seen:
            continue
        seen.add(name)
        # 分类名可能因换行折断，等级改从 "Critical/High/... \n Package:" 边界取
        levels = re.findall(
            r"\b(Critical|High|Medium|Low)\s*\n\s*Package:", block, re.I
        )
        rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        level = max((lev.lower() for lev in levels), key=lambda x: rank.get(x, 0), default="")

        def _section(label: str, stop_labels: tuple[str, ...]) -> str:
            found = re.search(rf"\n\s*{label}\s*\n(.*?)(?=\n\s*(?:{'|'.join(stop_labels)})\s*\n|\Z)", block, re.S)
            return _clean(found.group(1)) if found else ""

        explanation = _section("Explanation", ("Recommendation", "Issue Summary", "Engine Breakdown"))
        recommendation = _section("Recommendation", ("Issue Summary", "Engine Breakdown"))
        # 标题里的例数与 Package 实例数可能不一致（部分实例被折叠），取大者
        packages = len(re.findall(r"^\s*Package:", block, re.M))
        instances = max(int(match.group("count")), packages)
        rows.append(
            {
                "漏洞名称": name,
                "风险等级": _FORTIFY_LEVEL_CN.get(level, ""),
                "漏洞描述": explanation[:1500],
                "加固建议": recommendation[:3000],
                "实例数": instances,
            }
        )
    return rows


_APPSCAN_LEVEL_CN = {"高": "高危", "中": "中危", "低": "低危", "参": "信息"}


def _parse_appscan_pdf(text: str) -> list[dict]:
    """HCL AppScan Standard 中文报告。

    摘要表被压成一行文字："…问题的数量 高SQL 注入1 低“…”5 …"。
    名称里可能带"中"字（"在参数值中找到了…"），不能直接按级别字切，
    只在「数字后跟级别字」的边界拆条。
    """
    if "AppScan" not in text:
        return []
    # "摘要问题类型"先出现在目录里（后面紧跟"有漏洞的 URL"），真表在正文的
    # 第二次出现处，所以要取最后一次
    start = text.rfind("摘要问题类型")
    if start < 0:
        return []
    stop = text.find("有漏洞的", start)
    segment = text[start : stop if stop > start else start + 8000]
    pos = segment.rfind("问题的数量")
    if pos >= 0:
        segment = segment[pos:]
    segment = re.sub(r"^\s*问题的数量\s*", "", segment)
    tokens = re.split(r"(?<=[0-9])\s*(?=[高中低参][^0-9])", segment)
    rows = []
    for token in tokens:
        m = re.match(r"\s*([高中低参])\s*(.+?)\s*(\d{1,4})\s*$", token.strip(), re.S)
        if not m:
            continue
        name = _clean(m.group(2))
        if len(name) < 3 or len(name) > 80:
            continue
        rows.append(
            {
                "漏洞名称": name,
                "风险等级": _APPSCAN_LEVEL_CN.get(m.group(1), ""),
                "实例数": int(m.group(3)),
            }
        )
    return rows if len(rows) >= 2 else []


def _parse_zap_pdf(text: str) -> list[dict]:
    """OWASP ZAP 2.16 PDF 报告。

    每个告警的详情以 `CWE Id N / WASC Id N / Id N` 收尾，据此切块；
    块首行是告警名，实例数取块内 `URL ` 出现次数。中文描述用的字体
    pypdf 抽不出来（只剩 ASCII），所以描述和建议都可能残缺——名称、
    实例数和 CWE 是可靠部分。
    """
    if "ZAP by Checkmarx" not in text:
        return []
    ends = list(re.finditer(r"CWE Id (\d{1,4})\s*\nWASC Id \d+\s*\n\s*Id \d+", text))
    if len(ends) < 2:
        return []
    # 每个告警段：从上一条收尾行到本条 CWE Id 行；首段额外带报告头和汇总表，
    # 首个告警的名字在汇总表最后一个"名称+例数"行之后
    starts = [0] + [m.end() for m in ends[:-1]]
    blocks = zip(starts, ends)
    rows = []
    seen: set[str] = set()
    for index, (start, end) in enumerate(blocks):
        block = text[start : end.start()]
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if index == 0:
            # 跳过报告头+汇总表：最后一个"以数字结尾的短行"之后才是详情标题
            last_pair = 0
            for pos, line in enumerate(lines[:40]):
                if re.search(r"\S.{0,90}\s\d{1,4}$", line) and len(line) < 100:
                    last_pair = pos
            lines = lines[last_pair + 1 :] or lines
        name = _clean(lines[0])
        count = 0
        # 首段的名字行带汇总例数："SQL 2"；后续块的名字行没有例数
        tail = re.search(r"\s(\d{1,4})$", name)
        if tail:
            count = int(tail.group(1))
            name = name[: tail.start()].strip()
        # 名字在行首被折断的（如" - Unix"）取不回全名，宁缺勿滥
        if len(name) < 3 or len(name) > 90 or name.lower().startswith(("http", "-", "zap by checkmarx")):
            continue
        if name in seen:
            continue
        seen.add(name)
        instances = len(re.findall(r"^\s*URL\s+\S", block, re.M))
        # 汇总例数是权威数（详情可能只列 1 个示例）；详情更多时取大者
        if count:
            instances = max(count, instances)
        if not instances:
            continue
        cwe = f"CWE-{end.group(1)}"
        rows.append(
            {
                "漏洞名称": name,
                "风险等级": "",
                "漏洞描述": _clean(" ".join(lines[1:9]))[:1500],
                "CWE": cwe,
                "实例数": instances,
            }
        )
    return rows


def _parse_trivy_table_txt(text: str) -> list[dict]:
    """Trivy `--format table` 文本报告（sani*.txt 之类）。

    Report Summary 后按 `<目标> (<类型>)` 分节，每节一个
    Library│Vulnerability│Severity│…│Title 的框线表；单元格换行会把
    Title/Fixed 拆成多行（Library 列为空的行是上一条的续行）。
    """
    if "│" not in text or "Severity" not in text:
        return []
    sections = list(
        re.finditer(
            r"^\s*(?P<target>\S[^\n]{2,120}?)\s*\(\s*(?P<type>[a-z]+)\s*\)\s*\n=+\s*\n"
            r"Total:\s*(?P<total>\d+)",
            text,
            re.M,
        )
    )
    if not sections:
        return []

    def _cells(line: str) -> list[str]:
        parts = re.findall(r"│([^│]*)", line)
        return [_clean(part) for part in parts]

    rows = []
    for index, match in enumerate(sections):
        end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
        block = text[match.end() : end]
        target = _clean(match.group("target"))
        current: dict | None = None
        last_library = ""
        fixed_idx: int | None = None
        for line in block.splitlines():
            if "│" not in line:
                continue
            cells = _cells(line)
            if len(cells) < 3:
                continue
            if cells[0] == "Library":
                # 表头行：记住 Fixed Version 列的下标，数据行按它取修复版本
                fixed_idx = next(
                    (k for k, c in enumerate(cells) if c.startswith("Fixed")),
                    None,
                )
                continue
            cve_m = re.search(r"CVE-\d{4}-\d{4,7}", cells[1])
            if not cve_m:
                # 续行：补 Fixed Version / Title 的换行碎片
                if current is not None:
                    for cell in cells:
                        if re.fullmatch(r"\d+(?:\.\d+)+", cell):
                            current["_fixed"].append(cell)
                        elif cell and not re.fullmatch(r"[\s│]*", cell):
                            if cell.startswith("http"):
                                current["_desc"] += f" {cell}"
                            else:
                                current["_title"].append(cell)
                continue
            # 新条目：Library 列因竖向合并可能为空，从上一条继承或从
            # Title 的 "group:artifact: 说明" 前缀里取
            cve = cve_m.group(0).upper()
            title = cells[-1]
            library = cells[0] or last_library
            if not cells[0] and ":" in title and " " not in title.split(":", 1)[0]:
                library = title.split(":", 1)[0]
            last_library = library
            artifact = library.split(":")[-1] or library
            severity = cells[2].lower() if len(cells) > 2 else ""
            current = {
                "漏洞名称": f"{cve} {artifact}"[:120],
                "风险等级": {"critical": "严重", "high": "高危", "medium": "中危", "low": "低危"}.get(
                    severity, ""
                ),
                "CVE": cve,
                "实例数": 1,
                "_library": library,
                "_title": [title] if title else [],
                "_fixed": (
                    [cells[fixed_idx]]
                    if fixed_idx is not None and fixed_idx < len(cells) - 1
                    and re.fullmatch(r"[\d.]+", cells[fixed_idx])
                    else []
                ),
                "_desc": f"{library}（{target}）" if target else library,
            }
            rows.append(current)
    result = []
    for row in rows:
        title = _clean(" ".join(row.pop("_title")))
        fixed = "/".join(dict.fromkeys(row.pop("_fixed")))
        library = row.pop("_library")
        desc = row.pop("_desc")
        if fixed:
            desc += f"，修复版本 {fixed}"
        if title:
            desc += f"。{title}"[:900]
        row["漏洞描述"] = desc[:1500]
        row["加固建议"] = f"将 {library} 升级到已修复版本 {fixed}。" if fixed else f"升级 {library} 至已修复版本。"
        result.append(row)
    return result


_MD_SEVERITY_CN = {
    "critical": "严重", "high": "高危", "medium": "中危",
    "low": "低危", "info": "信息",
}


def _parse_md_pentest_report(text: str) -> list[dict]:
    """Markdown 渗透/安全测试报告（Agent 产出的结构化 md）。

    两种数据源，优先用汇总表（编号/漏洞名称/严重度/CVSS），详情节
    （`### ID · 名称` + `**描述**`/`**修复建议**`）按编号回填描述与建议；
    没有汇总表时退回逐详情节解析。设计文档/普通 md 不含这些结构，不会误收。
    """
    if not re.search(r"渗透测试|漏洞清单|漏洞详情", text) or "**描述**" not in text:
        return []
    details: dict[str, dict] = {}
    for match in re.finditer(r"^###\s+([A-Za-z][A-Za-z0-9_-]{1,15})\s*·\s*([^\n]{3,90})", text, re.M):
        vid = match.group(1).strip()
        name = _clean(match.group(2).rstrip(" 🔴🟠🟡🔵🟣⚪"))
        end = text.find("\n### ", match.end())
        if end < 0:
            end = len(text)
        block = text[match.end():end]
        desc = re.search(r"\*\*描述\*\*[：:]\s*(.+?)(?=\n\*\*|\n```)", block, re.S)
        fix = re.search(r"\*\*(?:修复建议|整改建议|加固建议)\*\*[：:]\s*(.+?)(?=\n\*\*|\n### |\n## |\Z)", block, re.S)
        level = re.search(
            r"(?:风险等级|严重度|危害)\*\*[：:]?\s*[^\n]*?(Critical|High|Medium|Low|严重|高危|中危|低危)",
            block, re.I,
        )
        details[vid] = {
            "漏洞名称": _clean(re.sub(r"^[（(【\[]?[A-Za-z0-9-]+[）)】\]]?\s*", "", name) or name),
            "漏洞描述": _clean(desc.group(1))[:1500] if desc else "",
            "加固建议": _clean(fix.group(1))[:3000] if fix else "",
            "风险等级": _MD_SEVERITY_CN.get((level.group(1) if level else "").lower(), ""),
        }

    rows = []
    table = re.search(
        r"\|\s*编号\s*\|\s*漏洞名称\s*\|\s*严重度\s*\|\s*CVSS\s*\|[^\n]*\n(?:\|.*\n)+", text
    )
    if table:
        for line in table.group(0).splitlines()[1:]:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 4 or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{1,15}", cells[0]):
                continue
            vid, name = cells[0], _clean(cells[1])
            sev = re.search(r"(Critical|High|Medium|Low|Info)", cells[2], re.I)
            detail = details.get(vid, {})
            row = {
                "漏洞名称": name or detail.get("漏洞名称") or vid,
                "风险等级": _MD_SEVERITY_CN.get((sev.group(1) if sev else "").lower(), "")
                or detail.get("风险等级", ""),
                "漏洞描述": detail.get("漏洞描述", ""),
                "加固建议": detail.get("加固建议", ""),
            }
            cvss = re.search(r"\d+(?:\.\d+)?", cells[3])
            if cvss:
                row["漏洞描述"] = (f"CVSS {cvss.group(0)}。" + row["漏洞描述"])[:1500]
            if row["漏洞名称"] and (row["漏洞描述"] or row["加固建议"] or row["风险等级"]):
                rows.append(row)
        if rows:
            return rows

    # 无汇总表：退回逐详情节（至少 2 节带描述/建议才算漏洞条目）
    for vid, detail in details.items():
        if detail["漏洞描述"] or detail["加固建议"]:
            rows.append(detail)
    return rows if len(rows) >= 2 else []


def _parse_osv_table_txt(text: str) -> list[dict]:
    """osv-scanner 表格文本报告（NAME/INSTALLED/FIXED IN/TYPE/VULNERABILITY/…）。

    列按 2+ 空格切分；FIXED IN 整列为空时行里会少一列，所以不能按固定
    下标取——以漏洞编号（唯一匹配 `前缀-编号` 模式的列）为锚往左右定位。
    """
    if "VULNERABILITY" not in text or "INSTALLED" not in text:
        return []
    lines = text.splitlines()
    header_idx = next(
        (i for i, ln in enumerate(lines) if re.search(r"\bNAME\b", ln) and "VULNERABILITY" in ln),
        None,
    )
    if header_idx is None:
        return []
    rows = []
    for line in lines[header_idx + 1 :]:
        if not line.strip() or set(line.strip()) <= {"-", " "}:
            continue
        loose = [c for c in re.split(r"\s{2,}", line.strip()) if c]
        if len(loose) < 4:
            continue
        vi = next(
            (k for k, c in enumerate(loose[1:], 1) if re.fullmatch(r"[A-Z][A-Z0-9]*-[A-Za-z0-9._-]+", c)),
            None,
        )
        if vi is None or vi < 2:
            continue
        vuln = loose[vi]
        name_col = loose[0]
        # vi-1 是 TYPE 列（java-archive 之类）；vi-2 往前是版本号。有修复版本
        # 的行是 [名, 已装, 修复, TYPE, 编号]，没有的是 [名, 已装, TYPE, 编号]
        # ——靠 vi-3 是否也是版本号区分。
        fixed = ""
        installed = ""
        if re.fullmatch(r"\d+(?:\.\d+)*", loose[vi - 2]):
            if vi >= 3 and re.fullmatch(r"\d+(?:\.\d+)*", loose[vi - 3]):
                installed = loose[vi - 3]
                fixed = loose[vi - 2]
            else:
                installed = loose[vi - 2]
        severity = str(loose[vi + 1] if vi + 1 < len(loose) else "").lower()
        artifact = name_col.split(":")[-1] or name_col
        rows.append(
            {
                "漏洞名称": f"{vuln} {artifact}"[:120],
                "风险等级": {"critical": "严重", "high": "高危", "medium": "中危", "low": "低危"}.get(
                    severity, ""
                ),
                "CVE": vuln if vuln.startswith("CVE-") else "",
                "漏洞描述": f"{name_col}（已装版本 {installed or '未知'}）",
                "加固建议": f"将 {name_col} 升级到已修复版本 {fixed}。" if fixed else f"升级 {name_col} 至已修复版本。",
                "实例数": 1,
            }
        )
    return rows


def _parse_cve_bulletin(text: str) -> list[dict]:
    cves = sorted(set(re.findall(r"CVE-\d{4}-\d{4,7}", text, re.I)))
    if not cves:
        return []
    title_lines = [
        _clean(line)
        for line in text.splitlines()[:20]
        if _clean(line) and not re.fullmatch(r"[\d年月日、,，()（）\s-]+", _clean(line))
    ]
    name = " ".join(title_lines[:4])
    if len(name) > 180:
        name = f"{'、'.join(cves)} 安全漏洞"
    suggestion = ""
    match = re.search(
        r"(?:处置建议|修复建议|解决方案)\s*(.*?)(?=\n第[五六七八九十]章|\n参考资料|\Z)",
        text,
        re.S,
    )
    if match:
        suggestion = _clean(match.group(1))[:5000]
    level_match = re.search(r"风险等级\s*([^\n]+)", text)
    return [
        {
            "漏洞名称": name,
            "风险等级": level_match.group(1) if level_match else "",
            "漏洞描述": _clean(text[:2000]),
            "加固建议": suggestion,
            "CVE编号": "、".join(cves),
        }
    ]


def _parse_legacy_doc(path: Path) -> list[dict]:
    """Convert binary .doc with an available local converter."""
    with tempfile.TemporaryDirectory() as directory:
        target_dir = Path(directory)
        libreoffice = shutil.which("soffice") or shutil.which("libreoffice")
        if libreoffice:
            subprocess.run(
                [
                    libreoffice,
                    "--headless",
                    "--convert-to",
                    "docx",
                    "--outdir",
                    str(target_dir),
                    str(path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            converted = target_dir / f"{path.stem}.docx"
            return _parse_pentest_result_docx(converted) or _parse_docx(converted)
        antiword = shutil.which("antiword")
        if antiword:
            result = subprocess.run(
                [antiword, str(path)],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            return _parse_labeled_text(result.stdout)
    raise RuntimeError(
        "Legacy DOC parsing requires LibreOffice (soffice) or antiword"
    )


def _safe_extract_zip(path: Path, target: Path) -> list[Path]:
    files = []
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            member_path = (target / member.filename).resolve()
            if target.resolve() not in member_path.parents and member_path != target.resolve():
                continue
            if member.is_dir():
                continue
            member_path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, member_path.open("wb") as destination:
                shutil.copyfileobj(source, destination)
            files.append(member_path)
    return files


def _safe_extract_rar(path: Path, target: Path) -> list[Path]:
    try:
        import rarfile
    except ImportError as exc:
        raise RuntimeError("RAR parsing requires rarfile and an unrar backend") from exc
    files = []
    with rarfile.RarFile(path) as archive:
        for member in archive.infolist():
            member_path = (target / member.filename).resolve()
            if target.resolve() not in member_path.parents and member_path != target.resolve():
                continue
            if member.isdir():
                continue
            member_path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, member_path.open("wb") as destination:
                shutil.copyfileobj(source, destination)
            files.append(member_path)
    return files


def _parse_jianshi_html(text: str) -> list[dict]:
    """Parse 坚石诚信 (Jet Sreality) HTML scan report text.

    Pattern: vulnerability name followed by a numeric count, then
    "漏洞描述" / "解决办法" sections.
    """
    known_vulns = {
        "CORS", "SameSite", "Cookie", "HttpOnly", "Secure", "跨域",
        "XSS", "SQL注入", "CSRF", "信息泄露", "ClickJacking", "点击劫持",
        "弱口令", "明文传输", "不安全的HTTP方法", "目录遍历", "路径穿越",
        "文件包含", "命令执行", "未授权", "越权", "敏感信息泄露",
        "安全配置错误", "不安全设计", "注入", "过时的组件", "自带缺陷",
        "SRI", "子资源完整性", "域名访问限制", "用户认证信息",
        "密码表单自动完成", "电子邮箱", "应用错误信息", "HTML信息泄露",
    }
    lines = text.split("\n")
    rows = []

    def _is_next_vuln_name(candidate: str) -> bool:
        """已经收到过正文段后，再出现关键词行就认为是下一条漏洞名。"""
        return len(candidate) <= 60 and any(kw in candidate for kw in known_vulns)

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Skip empty lines, numbers, and section headers
        if not line or re.match(r"^\d+$", line) or line in ("漏洞描述", "解决办法", "漏洞名称", "风险等级", "漏洞链接"):
            i += 1
            continue
        # Check if this looks like a vulnerability name (contains known keywords or is a reasonable length)
        has_kw = any(kw in line for kw in known_vulns)
        if not has_kw and (len(line) < 4 or len(line) > 60):
            i += 1
            continue
        # Skip common non-vuln lines
        if line in ("漏洞（种", "实例（个", "插件ID", "风险等级图标", "比较危险"):
            i += 1
            continue
        # This might be a vulnerability name. Look ahead for 漏洞描述/解决办法
        desc = ""
        fix = ""
        level = ""
        found_section = False
        j = i + 1
        while j < min(i + 100, len(lines)):
            lj = lines[j].strip()
            if lj in ("漏洞描述", "解决办法"):
                found_section = True
                field = "漏洞描述" if lj == "漏洞描述" else "解决办法"
                k = j + 1
                parts = []
                while k < min(j + 30, len(lines)):
                    lk = lines[k].strip()
                    if lk in ("解决办法", "漏洞描述", "漏洞名称", "风险等级", "漏洞链接"):
                        break
                    if re.match(r"^\d+$", lk) and len(lk) < 5:
                        break
                    # 正文里出现下一条漏洞名就到此为止，否则两条漏洞会被并成一条
                    if parts and _is_next_vuln_name(lk):
                        break
                    if lk:
                        parts.append(lk)
                    k += 1
                if field == "漏洞描述":
                    desc = " ".join(parts)
                else:
                    fix = " ".join(parts)
                j = k
                continue
            if lj == "漏洞名称" or lj == "风险等级" or lj == "漏洞链接":
                j += 1
                continue
            # 收过正文段之后又遇到关键词行：那是下一条漏洞，前瞻就此打住
            if found_section and _is_next_vuln_name(lj):
                break
            j += 1
        # 只有后面真的跟着"漏洞描述/解决办法"段的才算漏洞条目。JS 渲染的
        # 扫描报告（数据全在 script 里）和报告索引页只有标题和链接，
        # 不收就会把"XX批量扫描报告"这种页面标题当成一条漏洞交出去
        if line and found_section:
            rows.append({"漏洞名称": line, "漏洞描述": desc, "加固建议": fix, "风险等级": "medium"})
            i = j
        else:
            i += 1
    return rows


_ZAP_RISK_CN = {"高": "高危", "中": "中危", "低": "低危", "信息提示": "信息"}


def _parse_zap_html(html: str) -> list[dict]:
    """OWASP ZAP 2.17 HTML 报告。

    `id="alert-type-counts"` 汇总表一行一条（名称/风险/例数），每个
    `id="alert-type-N"` 详情段里有 CWE 编号、Alert description、Solution
    和告警标签里的 CVE 列表。
    """
    if 'id="alert-type-counts"' not in html or "ZAP by Checkmarx" not in html:
        return []
    summary = re.search(r'id="alert-type-counts"(.*?)</section>', html, re.S)
    if not summary:
        return []
    rows = []
    for match in re.finditer(
        r'<a href="#alert-type-(\d+)">([^<]+)</a>\s*</th>\s*'
        r'<td class="risk-level">([^<]*)</td>\s*<td>\s*<span>(\d+)</span>',
        summary.group(1),
    ):
        rows.append(
            {
                "_anchor": match.group(1),
                "漏洞名称": _clean(match.group(2)),
                "风险等级": _ZAP_RISK_CN.get(_clean(match.group(3)), ""),
                "实例数": int(match.group(4)),
            }
        )
    if not rows:
        return []
    # 详情段补描述/方案/CVE；段落缺失不影响该行落表
    anchors = list(re.finditer(r'id="alert-type-(\d+)"\s*>', html))
    details: dict[str, str] = {}
    for index, match in enumerate(anchors):
        end = anchors[index + 1].start() if index + 1 < len(anchors) else len(html)
        details.setdefault(match.group(1), html[match.end() : end])
    for row in rows:
        block = details.get(row.pop("_anchor"), "")
        text = re.sub(r"<[^>]+>", "\n", block)
        text = re.sub(r"\n{2,}", "\n", text)

        def _after(label: str, stops: tuple[str, ...]) -> str:
            found = re.search(
                rf"^\s*{label}\s*$(.*?)(?=^\s*(?:{'|'.join(stops)})\s*$|\Z)",
                text,
                re.M | re.S,
            )
            return _clean(found.group(1)) if found else ""

        desc = _after("Alert description", ("Other info", "Evidence", "Solution"))
        solution = _after("Solution", ("Alert tags", "Other info", "Evidence", "Reference"))
        cves = sorted(set(re.findall(r"CVE-\d{4}-\d{4,7}", block, re.I)))
        row["漏洞描述"] = desc[:1500]
        if solution:
            row["加固建议"] = solution[:3000]
        if cves:
            row["CVE"] = cves[0]
            row["漏洞描述"] = (row["漏洞描述"] + " 关联CVE：" + ", ".join(cves[1:8])).strip()[:1500]
    return rows


def _parse_api_security_scan_html(html: str) -> list[dict]:
    """星揆 API 安全扫描报告（纵向/水平越权高低权限回放）。

    结构：`测试接口清单` 一段接口矩阵，`鉴权问题 (未授权访问)` 与
    `越权问题 (权限控制)` 两段 issue 卡片。每张卡片带 badge 等级、
    `<strong>` 标题、`<code>METHOD</code> + 路径、以及 `越权状态: 通过/
    不通过/待确认`。和渗透测试结果报告同一条规矩：结论不是"通过"的才出条。

    端点只取 `<span>` 的可见文本（路径），不取 title 属性里的完整地址——
    那里面带着内网 IP 和端口，不能进对外交付物。
    """
    if 'id="auth-issues"' not in html and 'id="privilege-issues"' not in html:
        return []
    cards = re.split(
        r'<div class="card[^"]*"\s+id="(?:auth|privilege)-issue-\d+"\s*>', html
    )[1:]
    rows = []
    for card in cards:
        badge = re.search(r'badge badge-(\w+)">([^<]*)<', card)
        kind = re.search(r"<strong>([^<]*)</strong>", card)
        endpoint = re.search(
            r"<code>\s*([A-Z]+)\s*</code>\s*<span[^>]*>\s*([^<]*?)\s*</span>", card
        )
        status = re.search(r"(?:越权状态|鉴权状态):</strong>\s*([^<]*)<", card)
        verdict = _clean(status.group(1)) if status else ""
        if verdict == "通过":
            continue
        method = endpoint.group(1) if endpoint else ""
        path = _clean(endpoint.group(2)) if endpoint else ""
        if not path:
            continue
        analysis = ""
        for para in re.findall(
            r'<p style="color: #4ecdc4[^"]*"[^>]*>(.*?)</p>', card, re.S
        ):
            analysis = _clean(re.sub(r"<[^>]+>", "", para))
            break
        title = _clean(kind.group(1)) if kind else ""
        is_auth = "未授权" in title or "无需认证" in card[:600]
        prefix = "未授权访问" if is_auth else "越权"
        name = f"{prefix} {method} {path}".strip()
        if verdict:
            name = f"{prefix}（{verdict}）{method} {path}".strip()
        row = {
            "漏洞名称": name,
            "风险等级": _normalize_level(badge.group(2)) if badge else "",
            "漏洞描述": (f"{title}。" if title else "")
            + (f"回放结论：{verdict}。" if verdict else "")
            + analysis,
        }
        rows.append(row)
    return rows


def _parse_qijian_strix_html(html: str) -> list[dict]:
    """麒舰 strix 源码扫描产出的中文 HTML 渗透测试报告。

    `<h3>VULN-000X：<漏洞名></h3>` 一个漏洞一块，块首是「严重性/CVSS评分/
    发现时间/端点/CWE」属性行，后面跟「漏洞描述/影响分析/技术分析/修复建议/
    修复方案」小节；其中"修复建议"小节常为空，方案正文在"修复方案"里。
    """
    if not re.search(r"<h[1-6][^>]*>\s*VULN-\d+\s*[：:]", html):
        return []
    starts = [
        (m.start(), m.end(), _clean(m.group(2)))
        for m in re.finditer(
            r"<(h[1-6])[^>]*>\s*(VULN-\d+\s*[：:][^<]*?)\s*</\1>", html
        )
    ]
    if not starts:
        return []
    rows = []
    for index, (_, content_start, heading) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(html)
        block = html[content_start:end]
        text = re.sub(r"<[^>]+>", "\n", block)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n", text)

        def _after(label: str, stops: tuple[str, ...]) -> str:
            found = re.search(
                rf"^\s*{label}\s*$(.*?)(?=^\s*(?:{'|'.join(stops)})\s*$|\Z)",
                text,
                re.M | re.S,
            )
            return _clean(found.group(1)) if found else ""

        # 严重性是块首独立一行，只在属性区找，避免描述里的"严重影响"误判
        head_area = text.split("漏洞描述")[0]
        severity = re.search(r"^\s*(严重|高危|中危|低危|提示)\s*$", head_area, re.M)
        description = " ".join(
            part
            for part in (
                _after("漏洞描述", ("影响分析", "技术分析", "修复建议", "修复方案")),
                _after("影响分析", ("技术分析", "修复建议", "修复方案")),
                _after("技术分析", ("修复建议", "修复方案")),
            )
            if part
        )
        fix = " ".join(
            part
            for part in (
                _after("修复建议", ("修复方案",)),
                _after("修复方案", ()),
            )
            if part
        )
        endpoint = re.search(r"^\s*端点[：:]\s*(.+?)\s*$", text, re.M)
        cwe = re.search(r"\b(CWE-\d+)\b", head_area)
        # 端点是"POST /path"这类非 URL 路径，进不了 urls（只收 http(s)），
        # 并进描述开头，修复方案要拿它定位改动点
        location = f"端点：{_clean(endpoint.group(1))}。" if endpoint else ""
        row = {
            "漏洞名称": re.sub(r"^VULN-\d+\s*[：:]\s*", "", heading),
            "风险等级": severity.group(1) if severity else "",
            "漏洞描述": (location + description)[:1500],
            "实例数": 1,
            "source": "qijian_strix_html",
        }
        if fix:
            row["加固建议"] = fix[:3000]
        if cwe:
            row["CWE"] = cwe.group(1)
        rows.append(row)
    return rows


_QJ_ROLLUP_FINDING_H3 = (
    "关键发现",
    "主要发现",
    "发现汇总",
    "发现概览",
    "汇总发现",
    "已确认的发现",
)
# 等级标记两种摆放：后缀"名称（高危，CVSS 8.8）"/"名称（高危，High）"，
# 前缀"高危（High）——名称"/"高风险 — 名称"；英文档位与 CVSS/CWE 都放过
_QJ_ROLLUP_SEV_SUFFIX = re.compile(
    r"^(?P<name>.*?)（(?P<sev>严重|高危|高风险|中危|中风险|低危|低风险|信息级|提示级)"
    r"(?:[，,][^）]*)?）\s*[。.]?\s*$"
)
_QJ_ROLLUP_SEV_PREFIX = re.compile(
    r"^(?P<sev>严重|高危|高风险|中危|中风险|低危|低风险)\s*(?:（[^）]*）)?"
    r"\s*[—\-–:：]+\s*(?P<name>.+?)\s*[。.]?\s*$"
)
# 等级不写在名称里而是跟在后面："名称</strong>（高危，High，7.6）——描述"
_QJ_ROLLUP_BODY_LEVEL = re.compile(
    r"^（(?P<sev>严重|高危|高风险|中危|中风险|低危|低风险|信息级|提示级)"
    r"(?:[，,][^）]*)?）\s*(?:[—\-–:：]+\s*)?"
)
# 并列发现的连接词：前文以它们收尾时，后面的 strong 仍是条目名而非强调
_QJ_ROLLUP_NAME_CONNECTORS = ("以及", "及", "和", "与", "、", "，", ",", "；", ";")


def _qijian_li_item(li: str) -> list[tuple[str, str, str]]:
    """把一个 `<li>` 解析成若干 (名称, 等级, 描述)，不是发现条目返回空表。

    条目名以 `<strong>` 起头，但正文里的强调加粗（"但<strong>不会</strong>
    阻止…"）不是条目：只有段首、连接词之后、自带等级、或以逗号句号收尾
    且够长的 strong 才算条目名。一个 li 里偶发两个发现并列（"名称A（中危）
    以及名称B（低危）"），逐个 strong 拆开各出一条，正文取最后一个条目名
    之后的文本。方法论条目没有 strong，两种路径都收不进来。
    """
    names: list[tuple[str, int]] = []
    for strong in re.finditer(r"<strong>(.*?)</strong>", li, re.S):
        text = _clean(re.sub(r"<[^>]+>", " ", strong.group(1)))
        if not text:
            continue
        before = _clean(re.sub(r"<[^>]+>", " ", li[: strong.start()]))
        after = _clean(re.sub(r"<[^>]+>", " ", li[strong.end() :]))
        leveled = bool(
            _QJ_ROLLUP_SEV_SUFFIX.match(text) or _QJ_ROLLUP_SEV_PREFIX.match(text)
        )
        is_name = (
            not before
            or before.endswith(_QJ_ROLLUP_NAME_CONNECTORS)
            or leveled
            or (len(text) >= 4 and after[:1] in "，,。")
        )
        if is_name:
            names.append((text, strong.end()))
    if not names:
        return []
    body = re.sub(r"<[^>]+>", " ", li[names[-1][1] :])
    body = _clean(re.sub(r"^[—\-–:：，,。.\s]+", "", re.sub(r"\s+", " ", body)))
    items: list[tuple[str, str, str]] = []
    for strong_text, _ in names:
        matched = _QJ_ROLLUP_SEV_SUFFIX.match(strong_text) or _QJ_ROLLUP_SEV_PREFIX.match(
            strong_text
        )
        if matched:
            name = _clean(matched.group("name")).strip("—\\-–:：").rstrip("。")
            severity = matched.group("sev")
        else:
            name = strong_text.strip("—\\-–:：").rstrip("。")
            severity = ""
        if not name:
            continue
        if not severity:
            body_level = _QJ_ROLLUP_BODY_LEVEL.match(body)
            if body_level:
                severity = body_level.group("sev")
                body = body[body_level.end() :]
        items.append((name, severity, body))
    return items


def _qijian_rollup_items(section: str) -> list[tuple[str, str, str]]:
    """从一个项目段落里挑发现条目，返回 (名称, 等级, 描述) 列表。

    执行摘要里的发现列表带等级标记，优先取"第一个含等级条目的列表"且只收
    带等级的条目（同列表后半段常接着方法论条目，不能一起收）；技术分析里
    还有一份不带等级或换个写法的详情列表，一概不看，避免同一发现出两条。
    整段都没有等级标记时，退回第一个"关键发现/主要发现"等小节。
    """
    for block in re.findall(r"<[uo]l>(.*?)</[uo]l>", section, re.S):
        items = []
        for li in re.findall(r"<li>(.*?)</li>", block, re.S):
            items.extend(_qijian_li_item(li))
        # 判定"这是发现列表"看有没有带等级的条目；收的时候整表全收——
        # 同列表里没写等级的也是真发现（如"46 个经核实的依赖 CVE"），
        # 而方法论条目没有 strong，本来就被 _qijian_li_item 滤掉
        if any(item[1] for item in items):
            return items

    h3s = [
        (m.start(), m.end(), _clean(re.sub(r"<[^>]+>", " ", m.group(1))))
        for m in re.finditer(r"<h3[^>]*>(.*?)</h3>", section, re.S)
    ]
    for index, (_, content_start, title) in enumerate(h3s):
        if not any(keyword in title for keyword in _QJ_ROLLUP_FINDING_H3):
            continue
        end = h3s[index + 1][0] if index + 1 < len(h3s) else len(section)
        items = []
        for li in re.findall(r"<li>(.*?)</li>", section[content_start:end], re.S):
            items.extend(_qijian_li_item(li))
        if items:
            return items
    return []


def _parse_qijian_rollup_html(html: str) -> list[dict]:
    """麒舰 strix 多项目汇总渗透报告：一个 `<h2>XX · 安全渗透测试报告</h2>`
    一个项目，没有 VULN 编号标题，发现藏在各项目段落的列表里。"""
    h2s = [
        (m.start(), _clean(re.sub(r"<[^>]+>", " ", m.group(1))))
        for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", html, re.S)
    ]
    projects = [item for item in h2s if "安全渗透测试报告" in item[1]]
    if len(projects) < 2:
        return []
    rows = []
    seen: set[tuple[str, str]] = set()
    for index, (start, heading) in enumerate(projects):
        end = projects[index + 1][0] if index + 1 < len(projects) else len(html)
        section = html[start:end]
        project = re.sub(r"\s*·\s*安全渗透测试报告.*$", "", heading).strip()
        prefix = f"【{project}】" if project else ""
        for name, severity, description in _qijian_rollup_items(section):
            # 每个项目只取一个列表，同项目重复的概率很低；去重键带上项目前缀，
            # 两个项目真有同名发现时不能把后一个项目的条目吞掉
            key = (prefix + name, severity)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "漏洞名称": prefix + name,
                    "风险等级": severity,
                    "漏洞描述": description[:1500],
                    "实例数": 1,
                    "source": "qijian_rollup_html",
                }
            )
    return rows


def _parse_labeled_text(text: str) -> list[dict]:
    blocks = re.split(r"\n(?=(?:【?(?:严重|高危|中危|低危|信息)】?)?\s*\d*[.、]?\s*[^。\n]{2,60})", text)
    # 条目小标签：出现任一即认为这个块是漏洞详情而不是汇总表/说明文字
    _LABELS = re.compile(
        r"(?:漏洞描述|问题描述|漏洞危害|漏洞等级|风险等级|加固建议|修复建议|整改建议|解决方案)[：:]"
    )
    rows = []
    for block in blocks:
        name = re.search(r"(?:漏洞名称|问题名称|标题)[：:]\s*([^\n]+)", block)
        if not name:
            name = re.search(r"【(严重|高危|中危|低危|信息)】\s*([^\n]+)", block)
        if not name:
            # 国产审计报告常用"1、SQL 注入"作条目名，后面跟 漏洞描述/等级/整改建议。
            # 汇总表里也有"1. xxx"，但那些行没有这些小标签，靠标签区分，
            # 否则汇总表会被当成漏洞条目再收一遍。
            if _LABELS.search(block):
                name = re.search(
                    r"^\s*\d{1,2}\s*[、.．]\s*([^\n：:]{2,60})\s*$", block, re.M
                )
        if not name:
            continue
        title = name.group(2) if name.lastindex and name.lastindex >= 2 else name.group(1)
        row = {"漏洞名称": title}
        for field, labels in {
            "风险等级": ("风险等级", "漏洞等级"),
            "漏洞描述": ("漏洞描述", "问题描述"),
            "漏洞危害": ("漏洞危害", "影响"),
            "加固建议": ("加固建议", "修复建议", "整改建议", "解决方案"),
        }.items():
            pattern = "|".join(re.escape(label) for label in labels)
            match = re.search(
                rf"(?:{pattern})[：:]\s*(.*?)(?=\n(?:漏洞描述|问题描述|漏洞危害|影响|加固建议|修复建议|整改建议|解决方案)[：:]|\Z)",
                block,
                re.S,
            )
            row[field] = _clean(match.group(1)) if match else ""
        rows.append(row)
    return rows


def parse_report(path: str | Path) -> dict:
    report = Path(path)
    suffix = report.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        rows = _parse_excel(report)
    elif suffix in (".csv", ".tsv"):
        rows = _parse_delimited(report)
        dependency_rows = _normalize_dependency_check_rows(rows)
        if dependency_rows:
            rows = dependency_rows
    elif suffix == ".docx":
        rows = _parse_pentest_result_docx(report) or _parse_docx(report)
    elif suffix == ".doc":
        rows = _parse_legacy_doc(report)
    elif suffix == ".pdf":
        rows = _parse_pdf(report)
    elif suffix == ".json":
        data = json.loads(report.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            rows = data.get("vulns") or data.get("items") or data.get("results") or [data]
        else:
            rows = data
    elif suffix in (".html", ".htm"):
        try:
            from bs4 import BeautifulSoup
        except ImportError as exc:
            raise RuntimeError("HTML parsing requires beautifulsoup4") from exc
        raw = report.read_text(encoding="utf-8", errors="ignore")
        zap_rows = _parse_zap_html(raw)
        api_rows = _parse_api_security_scan_html(raw)
        qijian_rows = _parse_qijian_strix_html(raw)
        rollup_rows = _parse_qijian_rollup_html(raw)
        if zap_rows:
            rows = zap_rows
        elif api_rows:
            rows = api_rows
        elif qijian_rows:
            rows = qijian_rows
        elif rollup_rows:
            rows = rollup_rows
        else:
            text = BeautifulSoup(raw, "html.parser").get_text("\n")
            rows = _parse_jianshi_html(text) or _parse_labeled_text(text)
    elif suffix in (".txt", ".md", ".log", ".out", ".properties"):
        content = report.read_text(encoding="utf-8", errors="ignore")
        rows = (
            _parse_md_pentest_report(content)
            or _parse_trivy_table_txt(content)
            or _parse_osv_table_txt(content)
            or _parse_labeled_text(content)
        )
    elif suffix in (".zip", ".rar"):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            extracted = (
                _safe_extract_zip(report, target)
                if suffix == ".zip"
                else _safe_extract_rar(report, target)
            )
            vulns = []
            parse_errors = []
            for extracted_file in extracted:
                try:
                    parsed = parse_report(extracted_file)
                    for vuln in parsed["vulns"]:
                        vuln["source_file"] = (
                            f"{report.name}!{extracted_file.relative_to(target)}"
                        )
                    vulns.extend(parsed["vulns"])
                except Exception as exc:
                    parse_errors.append(
                        {
                            "file": str(extracted_file.relative_to(target)),
                            "error": str(exc),
                        }
                    )
            for index, vuln in enumerate(vulns, 1):
                vuln["id"] = index
            return {
                "source_file": str(report),
                "format": suffix.lstrip("."),
                "total": len(vulns),
                "vulns": vulns,
                "archive_parse_errors": parse_errors,
            }
    else:
        raise ValueError(f"Unsupported report format: {suffix or '(none)'}")

    vulns = normalize_rows(rows, report.name)
    for index, vuln in enumerate(vulns, 1):
        vuln["id"] = index
    return {
        "source_file": str(report),
        "format": suffix.lstrip("."),
        "total": len(vulns),
        "vulns": vulns,
    }
