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
            return _parse_docx(converted)
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
        j = i + 1
        while j < min(i + 100, len(lines)):
            lj = lines[j].strip()
            if lj == "漏洞描述":
                k = j + 1
                desc_parts = []
                while k < min(j + 30, len(lines)):
                    lk = lines[k].strip()
                    if lk in ("解决办法", "漏洞描述", "漏洞名称", "风险等级", "漏洞链接") or (re.match(r"^\d+$", lk) and len(lk) < 5):
                        break
                    if lk:
                        desc_parts.append(lk)
                    k += 1
                desc = " ".join(desc_parts)
                j = k
                continue
            if lj == "解决办法":
                k = j + 1
                fix_parts = []
                while k < min(j + 30, len(lines)):
                    lk = lines[k].strip()
                    if lk in ("解决办法", "漏洞描述", "漏洞名称", "风险等级", "漏洞链接") or (re.match(r"^\d+$", lk) and len(lk) < 5):
                        break
                    if lk:
                        fix_parts.append(lk)
                    k += 1
                fix = " ".join(fix_parts)
                j = k
                continue
            j += 1
        if line:
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
    elif suffix == ".docx":
        rows = _parse_docx(report)
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
        if zap_rows:
            rows = zap_rows
        else:
            text = BeautifulSoup(raw, "html.parser").get_text("\n")
            rows = _parse_jianshi_html(text) or _parse_labeled_text(text)
    elif suffix in (".txt", ".md", ".log", ".out", ".properties"):
        content = report.read_text(encoding="utf-8", errors="ignore")
        rows = (
            _parse_trivy_table_txt(content)
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
