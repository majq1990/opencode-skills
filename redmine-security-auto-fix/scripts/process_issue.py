#!/usr/bin/env python3
"""Process one Redmine security issue through parsing and internal enrichment."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import sys
from pathlib import Path

from build_security_corpus import download_attachment
from classify_vulns import classify_vulnerability
from fetch_vuln_docs import fetch_issue
from generate_dingtalk_doc import generate_doc_markdown
from recommendation_engine import enrich_all
from report_parser import parse_report

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


def merge_vulnerabilities(items: list[dict]) -> list[dict]:
    """Merge exact/near-exact names while preserving all report suggestions."""
    merged: dict[str, dict] = {}
    for item in items:
        key = " ".join((item.get("name") or "").lower().split())
        if not key:
            continue
        if key not in merged:
            merged[key] = dict(item)
            merged[key]["source_files"] = [item.get("source_file")]
            continue
        current = merged[key]
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
        for field in ("description", "harm", "cve", "cwe"):
            if not current.get(field) and item.get(field):
                current[field] = item[field]
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
        "--similar-assist", default=r"D:\git\redmine-similar-assist"
    )
    parser.add_argument(
        "--dingtalk-parent-node",
        default=DEFAULT_PARENT_NODE_ID,
        help="钉钉修复文档目标目录节点",
    )
    args = parser.parse_args()

    sys.path.insert(0, args.similar_assist)
    from src.config import cfg

    config = cfg()
    if not args.api_key:
        args.api_key = config["redmine"]["api_key"]

    output_dir = Path(
        args.output_dir or rf"D:\opencode\_archive\{args.issue_id}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    issue = fetch_issue(args.redmine_url, args.api_key, args.issue_id)
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
