#!/usr/bin/env python3
"""Process one Redmine security issue through parsing and internal enrichment."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import sys
from pathlib import Path

from build_security_corpus import download_attachment
from classify_vulns import classify_vulnerability
from fetch_vuln_docs import RedmineAccessError, fetch_issue
from generate_dingtalk_doc import generate_doc_markdown
from recommendation_engine import enrich_all
from report_parser import parse_report
from asset_triage_link import attach as attach_asset_triage
from asset_triage_link import render_section as render_asset_triage_section

DEFAULT_PARENT_NODE_ID = "dQPGYqjpJYg0vw9osZbj1mpgWakx1Z5N"

SUPPORTED = {
    ".docx",
    ".doc",
    ".xlsx",
    ".xls",
    ".csv",
    ".tsv",
    ".pdf",
    ".json",
    ".html",
    ".htm",
    ".txt",
    ".md",
    ".log",
    ".out",
    ".properties",
    ".zip",
    ".rar",
}


_LEVEL_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

# 同一漏洞在报告里常同时出现在段落标题和汇总表格中，名称会带上章节号、
# 等级/状态标记和页码残留，精确匹配合并不掉。只剥这些标记——括号里的
# 模块名等信息要留，否则"越权访问（订单）"会被误合成"越权访问（用户）"。
# 等级词必须是括号内的主体，"（中山路接口）"这类地名才不会被打成等级标记。
_LEVEL_WORDS = r"严重|高危|高|中危|中|低危|低|信息|待修复|已修复|已关闭|待整改|已整改|提示"
_LEVEL_MARK = re.compile(
    rf"[（(\[【]\s*(?:{_LEVEL_WORDS})"
    rf"(?:\s*[/\-—,，、]\s*(?:{_LEVEL_WORDS}))?"
    rf"\s*(?:风险|漏洞|等级|问题|级别|状态)?\s*[)）\]】]"
)
# 标题行前缀："2.1.3" 或 "1、"；普通数字开头的名称（3DES）不能动，
# 所以点号链至少要两级，或必须紧跟中文编号符号
_LEAD_NUM = re.compile(r"^\s*(?:\d+(?:\s*\.\s*\d+)+\s*[、.．,，]?|\d{1,2}\s*[、.．,，])\s*")
_TAIL_NUM = re.compile(r"\s+\d{1,3}\s*$")
_PUNCT = re.compile(r"[\s，,。;；:：/／\-_]+")


def _clean_name(name: str) -> str:
    """标题行名称清洗：去掉章节号、等级/状态标记和页码残留，模块名保留。"""
    text = _LEVEL_MARK.sub("", name or "")
    text = _LEAD_NUM.sub("", text)
    text = _TAIL_NUM.sub("", text)
    return re.sub(r"\s{2,}", " ", text).strip(" ：:，,、")


def _dedupe_key(name: str) -> str:
    return _PUNCT.sub("", _clean_name(name).lower())


def _to_int_like(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _diagnose_no_report(
    attachments: list[dict], parse_results: list[dict], issue: dict
) -> dict:
    """0 漏洞时说明"查过了什么、为什么是 0"。

    一类案件根本没传报告附件，漏洞明细只写在案件描述里；另一类附件
    不是报告（截图、扫描器导出）。这两种都不能交一份只有"共识别 0 类"
    的空表——读者分不清是没查到还是本案没问题。
    """
    parseable = [
        result
        for result in parse_results
        if not result.get("error") and result.get("total")
    ]
    if not attachments:
        reason = "本案没有可下载的附件，漏洞明细只写在案件描述里"
    elif not parse_results:
        reason = f"本案 {len(attachments)} 个附件都不是支持解析的报告格式"
    elif not parseable and all(result.get("error") for result in parse_results):
        reason = f"{len(parse_results)} 个附件全部解析失败"
    else:
        reason = "附件已下载并解析，但未识别出漏洞条目"
    return {
        "reason": reason,
        "attachment_count": len(attachments),
        "parse_results": parse_results,
        "description": issue.get("description") or "",
    }


def merge_vulnerabilities(items: list[dict]) -> list[dict]:
    """Merge exact/near-exact names while preserving all report suggestions."""
    merged: dict[str, dict] = {}
    for item in items:
        row = dict(item)
        # 名称先清洗再合并：否则段落标题的章节号/状态标记会让同一条漏洞
        # 在文档里以两种写法各出现一次
        row["name"] = _clean_name(row.get("name") or "") or (row.get("name") or "")
        key = _dedupe_key(row["name"])
        if not key:
            continue
        if key not in merged:
            merged[key] = row
            merged[key]["source_files"] = [item.get("source_file")]
            merged[key]["occurrences"] = 1
            continue
        current = merged[key]
        # occurrences 只记录"原始报告里有几条"，不改变 instances 语义
        # （instances 取较大例数，避免首测/复测重复计数）；总览用它如实展示
        current["occurrences"] = current.get("occurrences", 1) + 1
        if item.get("source_file") not in current["source_files"]:
            current["source_files"].append(item.get("source_file"))
        if item.get("fix_suggestion"):
            suggestions = {
                text.strip()
                for text in (current.get("fix_suggestion") or "").split("\n---\n")
                if text.strip()
            }
            suggestions.add(item["fix_suggestion"].strip())
            current["fix_suggestion"] = "\n---\n".join(sorted(suggestions))
        for field in ("description", "harm", "cve", "cwe", "urls"):
            if not current.get(field) and item.get(field):
                current[field] = item[field]
        # 同一缺陷类型在多个附件里重复出现时取较大例数：相加会把
        # 首测/复测同一批实例算两遍
        if _to_int_like(item.get("instances")) > _to_int_like(current.get("instances")):
            current["instances"] = item["instances"]
        # 表格行常缺等级，段落行才带等级；出现分歧时取更高的一档，
        # 低报风险比重复一条更糟
        if _LEVEL_RANK.get(item.get("level"), 2) > _LEVEL_RANK.get(
            current.get("level"), 2
        ):
            current["level"] = item["level"]
            current["level_explicit"] = True
        current["urls"] = sorted(
            set(current.get("urls") or []) | set(item.get("urls") or [])
        )
    result = list(merged.values())
    for index, item in enumerate(result, 1):
        item["id"] = index
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("issue_id", type=int)
    parser.add_argument("--redmine-url", default="https://faq.egova.com.cn:7787")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--similar-assist", default=r"D:\git\redmine-assist"
    )
    parser.add_argument(
        "--dingtalk-parent-node",
        default=DEFAULT_PARENT_NODE_ID,
        help="钉钉修复文档目标目录节点",
    )
    parser.add_argument(
        "--with-asset-triage",
        action="store_true",
        help="启用三源研判对照（v2.0，默认关闭；需 --triage-cases 提供 cases JSON）",
    )
    parser.add_argument(
        "--triage-cases",
        default=None,
        help="triage_cases.py 产出的 cases_<date>.json 路径",
    )
    args = parser.parse_args()

    # 检索仓路径写死过旧目录名，PATH 上又有无关的 src/config.py，
    # import 会静默串到别的项目然后报看不懂的 ImportError；先自己校验
    assist_root = Path(args.similar_assist)
    if not (assist_root / "src" / "config.py").is_file():
        print(
            f"[error] 检索仓不可用：{assist_root} 下缺少 src/config.py。"
            "请用 --similar-assist 指向 redmine-assist 仓的根目录",
            file=sys.stderr,
        )
        return 2
    sys.path.insert(0, args.similar_assist)
    from src.config import cfg

    config = cfg()
    if not args.api_key:
        args.api_key = config["redmine"]["api_key"]

    output_dir = Path(
        args.output_dir or rf"D:\opencode\_archive\{args.issue_id}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        issue = fetch_issue(args.redmine_url, args.api_key, args.issue_id)
    except RedmineAccessError as exc:
        # key 失效/案件不存在时必须中断：否则会交一份"没有附件"的假方案
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    attachments = issue.get("attachments") or []

    parsed_items = []
    parse_results = []
    for attachment in attachments:
        path = download_attachment(
            args.redmine_url,
            args.api_key,
            {**attachment, "issue_id": args.issue_id},
            output_dir,
        )
        if not path or Path(path).suffix.lower() not in SUPPORTED:
            continue
        try:
            parsed = parse_report(path)
            parsed_items.extend(parsed["vulns"])
            parse_results.append(
                {
                    "file": str(path),
                    "format": parsed["format"],
                    "total": parsed["total"],
                }
            )
        except Exception as exc:
            parse_results.append({"file": str(path), "error": str(exc)})

    vulns = merge_vulnerabilities(parsed_items)
    enriched = enrich_all(vulns, args.similar_assist)
    for row in enriched:
        row["responsibility"] = classify_vulnerability(row)

    # 台账第一优先：安全漏洞台账已登记的 CVE 直接沿用其方案/状态，
    # 并压掉互联网搜索；台账不可达时降级继续（不阻塞主流程）
    ledger_summary = None
    try:
        from vuln_ledger import attach_to_vulns
        ledger_summary = attach_to_vulns(enriched)
        if ledger_summary:
            print(f"台账命中 {ledger_summary['matched']} 个 CVE，"
                  f"据此免搜 {ledger_summary['suppressed_web_search']} 条")
    except Exception as exc:
        print(f"[ledger] 台账查询不可用，跳过（{type(exc).__name__}: {exc}）",
              file=sys.stderr)

    # v2.0 可选后处理：三源研判对照（默认关闭，关闭时与 v1.1.0 行为一致）
    triage_summary = None
    triage_section = ""
    if args.with_asset_triage:
        if not args.triage_cases:
            parser.error("--with-asset-triage 需要 --triage-cases 指向 cases_<date>.json")
        with open(args.triage_cases, encoding="utf-8") as handle:
            cases_doc = json.load(handle)
        triage_summary = attach_asset_triage(enriched, cases_doc)
        triage_section = render_asset_triage_section(enriched, cases_doc.get("meta") or {})

    result = {
        "issue_id": args.issue_id,
        "source": "current_issue_attachments",
        "parse_results": parse_results,
        "total": len(enriched),
        "stats": dict(Counter(row.get("level", "medium") for row in enriched)),
        "responsibility_stats": dict(
            Counter(row["responsibility"]["owner"] for row in enriched)
        ),
        "vulns": enriched,
        "web_search_required": [
            {
                "id": row["id"],
                "name": row["name"],
                "query": row["web_search"]["query"],
            }
            for row in enriched
            if row.get("web_search", {}).get("required")
        ],
    }
    if triage_summary is not None:
        result["asset_triage"] = triage_summary
    if not enriched:
        result["no_report"] = _diagnose_no_report(attachments, parse_results, issue)
    result_path = output_dir / f"{args.issue_id}_enriched.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    doc_path = output_dir / f"{args.issue_id}_fix_plan.md"
    doc_path.write_text(
        generate_doc_markdown(
            result, f"{args.redmine_url.rstrip('/')}/issues/{args.issue_id}"
        ),
        encoding="utf-8",
    )
    if triage_section:
        with open(doc_path, "a", encoding="utf-8") as handle:
            handle.write("\n" + triage_section)

    title = f"{issue.get('subject') or f'案件{args.issue_id}'} 安全漏洞修复方案"
    result["dingtalk_document"] = {
        "published": False,
        "status": "pending_mcp_publish",
        "parent_node_id": args.dingtalk_parent_node,
        "title": title,
        "markdown_path": str(doc_path),
    }
    result["notification"] = {
        "sent": False,
        "reason": "waiting for verified DingTalk document publication",
    }
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Result: {result_path}")
    print(f"Document: {doc_path}")
    print(f"DingTalk publish request: {result['dingtalk_document']}")
    print("Notification suppressed until finalize_publication.py")
    print(
        f"Pending web searches: {len(result['web_search_required'])} "
        "(non-code always + code vulns with no internal solution)"
    )


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
