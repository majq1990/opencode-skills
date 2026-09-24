#!/usr/bin/env python3
"""Enrich parsed vulnerabilities under the required source-priority policy."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sec_kb_bridge import SecKbBridge
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


# 建议优先级（与 SKILL.md「建议优先级」一节一致）：安全池两类都高于全库两类
_SOURCE_ORDER = {
    "sec_pool_history": 0,
    "sec_pool_kb": 1,
    "redmine_history": 2,
    "knowledge_base": 3,
}


def _ordered_suggestions(internal: dict[str, Any]) -> list[dict[str, Any]]:
    """按来源优先级排出可复用建议，过滤掉没有实际内容的候选。"""
    if "ordered" in internal:
        return list(internal["ordered"] or [])
    return [
        item for item in internal["history"] + internal["knowledge"]
        if item.get("suggestion")
    ]


def merge_internal(
    sec_result: dict[str, Any] | None,
    full_result: dict[str, Any] | None,
) -> dict[str, Any]:
    """合并安全池与全库两条链路的检索结果。

    顺序即优先级：安全池案件 → 安全池文档 → 全库案件 → 全库文档。
    外部 CVE 情报单独走 `external_intel`，不混入修复建议（情报只补充漏洞事实）。
    """
    sec_result = sec_result or {}
    full_result = full_result or {}
    history = list(sec_result.get("history") or []) + list(full_result.get("history") or [])
    knowledge = list(sec_result.get("knowledge") or []) + list(full_result.get("knowledge") or [])
    ordered = sorted(
        history + knowledge,
        key=lambda item: _SOURCE_ORDER.get(item.get("type"), 99),
    )
    return {
        "history": history,
        "knowledge": knowledge,
        "ordered": ordered,
        "external_intel": list(sec_result.get("external_intel") or []),
        "sec_pool_error": sec_result.get("_error"),
        "sec_pool_engine": sec_result.get("engine"),
    }


def enrich_vulnerability(
    vuln: dict[str, Any],
    bridge: SimilarAssistBridge,
    internal: dict[str, Any] | None = None,
    sec_bridge: SecKbBridge | None = None,
) -> dict[str, Any]:
    result = dict(vuln)
    code_related = is_code_vulnerability(vuln)
    if internal is None:
        query = build_query(vuln)
        if sec_bridge is not None:
            with ThreadPoolExecutor(max_workers=2) as pool:
                sec_future = pool.submit(sec_bridge.search_security_pool, query)
                full_future = pool.submit(bridge.search_internal, query)
                internal = merge_internal(sec_future.result(), full_future.result())
        else:
            internal = bridge.search_internal(query)

    suggestions = []
    if vuln.get("fix_suggestion"):
        suggestions.append(
            {
                "source": "report",
                "suggestion": vuln["fix_suggestion"],
            }
        )
    for item in _ordered_suggestions(internal):
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
    result["external_intel"] = internal.get("external_intel") or []

    internal_has_solution = any(
        item.get("suggestion") for item in _ordered_suggestions(internal)
    )
    # 代码类：仅当内部（安全池+全库）无可执行方案时，才允许互联网作为兜底；
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
    vulns: list[dict[str, Any]],
    repo_path: str = r"D:\git\redmine-similar-assist",
    with_sec_pool: bool = True,
) -> list[dict[str, Any]]:
    bridge = SimilarAssistBridge(repo_path)
    sec_bridge = SecKbBridge() if with_sec_pool else None
    items = [{"id": index, "query": build_query(vuln)} for index, vuln in enumerate(vulns)]

    with ThreadPoolExecutor(max_workers=2) as pool:
        full_future = pool.submit(bridge.search_internal_batch, items)
        sec_future = (
            pool.submit(sec_bridge.search_batch, items) if sec_bridge else None
        )
        full_batch = full_future.result()
        sec_batch = sec_future.result() if sec_future else {}

    return [
        enrich_vulnerability(
            vuln,
            bridge,
            internal=merge_internal(sec_batch.get(index), full_batch.get(index)),
            sec_bridge=sec_bridge,
        )
        for index, vuln in enumerate(vulns)
    ]
