#!/usr/bin/env python3
"""Enrich parsed vulnerabilities under the required source-priority policy."""

from __future__ import annotations

import re
from typing import Any

from similar_assist_bridge import SimilarAssistBridge

CODE_PATTERNS = (
    r"sql\s*注入",
    r"xss|跨站脚本",
    r"命令注入",
    r"代码执行|rce",
    r"反序列化",
    r"文件上传",
    r"路径穿越|目录穿越|目录遍历|任意文件读取|文件读取",
    r"ssrf",
    r"csrf",
    r"越权|idor|权限绕过|未授权访问|鉴权",
    r"业务逻辑|逻辑漏洞",
    r"硬编码",
    r"敏感信息(?:泄漏|泄露)|密码回显|未脱敏",
    r"详细.{0,4}(?:报错|错误)信息|异常信息.{0,4}(?:泄漏|泄露)",
    r"不安全的\s*restful\s*api",
)


def is_code_vulnerability(vuln: dict[str, Any]) -> bool:
    text = " ".join(
        str(vuln.get(key) or "")
        for key in ("name", "description", "harm", "cwe")
    ).lower()
    return any(re.search(pattern, text, re.I) for pattern in CODE_PATTERNS)


def build_query(vuln: dict[str, Any]) -> str:
    parts = [
        vuln.get("name") or "",
        vuln.get("cve") or "",
        vuln.get("cwe") or "",
        (vuln.get("description") or "")[:600],
        (vuln.get("harm") or "")[:300],
    ]
    return "\n".join(str(part) for part in parts if part)


def enrich_vulnerability(
    vuln: dict[str, Any], bridge: SimilarAssistBridge
) -> dict[str, Any]:
    result = dict(vuln)
    code_related = is_code_vulnerability(vuln)
    internal = bridge.search_internal(build_query(vuln))

    suggestions = []
    if vuln.get("fix_suggestion"):
        suggestions.append(
            {
                "source": "report",
                "suggestion": vuln["fix_suggestion"],
            }
        )
    for item in internal["history"] + internal["knowledge"]:
        if item.get("suggestion"):
            suggestions.append(
                {
                    "source": item["type"],
                    "suggestion": item["suggestion"],
                    "reference": item,
                }
            )

    result["fix_type"] = "code" if code_related else "non_code"
    result["internal_matches"] = internal
    result["recommendations"] = suggestions

    internal_has_solution = any(
        item.get("suggestion")
        for item in internal["history"] + internal["knowledge"]
    )
    # 代码类：仅当内部（历史+知识库）无可执行方案时，才允许互联网作为兜底；
    #        内部有方案则禁止互联网补充（保留原安全红线）。
    # 非代码类：始终并行搜互联网（保持现状）。
    if code_related and internal_has_solution:
        result["web_search"] = {
            "required": False,
            "query": "",
            "reason": "代码类漏洞已命中内部修复方案，不做互联网补充。",
        }
    else:
        result["web_search"] = {
            "required": True,
            "query": _build_web_query(vuln),
            "reason": (
                "内部知识已命中，互联网结果作为补充参考。"
                if internal_has_solution
                else (
                    "代码类漏洞内部无可执行方案，互联网结果作为兜底优先建议。"
                    if code_related
                    else "知识库未命中，优先使用互联网搜索结果提供修复建议。"
                )
            ),
            "kb_has_solution": internal_has_solution,
        }
    return result


def _build_web_query(vuln: dict[str, Any]) -> str:
    name = vuln.get("name") or ""
    cve = vuln.get("cve") or ""
    if cve:
        return f"{cve} {name} 安全 修复 加固 官方建议"
    return f"{name} 安全 漏洞 修复 加固 官方建议"


def enrich_all(
    vulns: list[dict[str, Any]], repo_path: str = r"D:\git\redmine-similar-assist"
) -> list[dict[str, Any]]:
    bridge = SimilarAssistBridge(repo_path)
    return [enrich_vulnerability(vuln, bridge) for vuln in vulns]
