#!/usr/bin/env python3
"""Merge reviewed web-search recommendations into an enriched issue JSON.

当 KB 无命中时，互联网结果提升为优先建议（排在 report 之后、空 KB 之前）；
当 KB 有命中时，互联网结果追加为补充参考。
代码类漏洞只在内部无方案（kb_has_solution=false）时才写入互联网兜底建议；
内部已有方案的代码类漏洞仍拒绝写入。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


def _insert_internet_suggestion(vuln: dict, result: dict) -> None:
    url = result.get("url") or ""
    if urlparse(url).scheme not in ("http", "https"):
        raise ValueError(f"Invalid source URL for vulnerability {vuln['id']}")
    suggestion = (result.get("suggestion") or "").strip()
    if not suggestion:
        raise ValueError(f"Empty web suggestion for vulnerability {vuln['id']}")

    entry = {
        "source": "internet",
        "suggestion": suggestion,
        "reference": {
            "title": result.get("title") or "",
            "url": url,
            "publisher": result.get("publisher") or "",
            "accessed_at": result.get("accessed_at") or "",
        },
    }

    kb_has_solution = vuln.get("web_search", {}).get("kb_has_solution", True)

    if kb_has_solution:
        vuln.setdefault("recommendations", []).append(entry)
    else:
        existing = vuln.get("recommendations", [])
        insert_at = 0
        for idx, rec in enumerate(existing):
            if rec.get("source") != "report":
                insert_at = idx
                break
        else:
            insert_at = len(existing)
        existing.insert(insert_at, entry)
        entry["priority"] = "kb_empty_primary"

    vuln["web_search"] = {
        "required": False,
        "reason": (
            "内部无匹配后，互联网搜索结果已作为优先建议注入。"
            if not kb_has_solution
            else "内部知识已命中，互联网结果作为补充参考追加。"
        ),
        "kb_has_solution": kb_has_solution,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("enriched_json")
    parser.add_argument("web_results_json")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    enriched_path = Path(args.enriched_json)
    data = json.loads(enriched_path.read_text(encoding="utf-8"))
    web_results = json.loads(Path(args.web_results_json).read_text(encoding="utf-8"))
    by_id = {int(row.get("vuln_id", row["id"])): row for row in web_results}

    for vuln in data.get("vulns", []):
        result = by_id.get(int(vuln["id"]))
        if not result:
            continue
        if vuln.get("fix_type") == "code":
            kb_has_solution = vuln.get("web_search", {}).get(
                "kb_has_solution", True
            )
            # 代码类只在内部无方案（兜底）时才允许写入互联网建议；
            # 内部已有方案的代码类仍拒绝，保留原安全红线。
            if kb_has_solution:
                raise ValueError(
                    "Internet result supplied for code vulnerability with "
                    f"internal solution: {vuln['name']}"
                )
        _insert_internet_suggestion(vuln, result)

    data["web_search_required"] = [
        {
            "id": row["id"],
            "name": row["name"],
            "query": row["web_search"].get("query", ""),
        }
        for row in data.get("vulns", [])
        if row.get("web_search", {}).get("required")
    ]
    output = Path(args.output) if args.output else enriched_path
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Updated: {output}")


if __name__ == "__main__":
    main()