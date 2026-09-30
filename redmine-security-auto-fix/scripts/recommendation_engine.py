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


# 互联网查询词的名称上限。这个长度不是安全边界——真正拦案情描述的是下面的
# _PROSE_MARK；上限只是兜底防呆，所以按"漏洞类型名写得再长也就到这个程度"
# 来定：扫全语料 1214 个名称，截到 40 字只剩 140 个被切，压到 24 字会切掉
# 571 个（"HTTPS会话中的敏感cookie没有设置安全属性"这类长类型名被腰斩），
# 而两种上限下泄漏都是 0。
_WEB_NAME_MAX = 40
# 出现这些词就说明截出来的仍是案情/影响描述，里面必然带客户名和内网信息
_PROSE_MARK = re.compile(
    r"获取|突破|反弹|横向|内网|主机|权限|政务|省政府|市人民政府|办公室|"
    r"互联网系统|攻击者|攻击成功|失陷|沦陷|植入|webshell|shell权限"
)


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

    # 报告没写等级时 level 是默认 medium；同一编号的情报带了 NVD 真实
    # severity 就拿它回填，否则整张漏扫表会一片 medium，分级失去意义
    if not vuln.get("level_explicit"):
        cve = str(vuln.get("cve") or "").strip().upper()
        for intel in result["external_intel"]:
            if not cve or str(intel.get("cve_id") or "").upper() != cve:
                continue
            severity = str(intel.get("severity") or "").strip().lower()
            if severity in ("critical", "high", "medium", "low", "info"):
                result["level"] = severity
                result["level_source"] = "external_intel"
            break

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
    elif not _build_web_query(vuln):
        result["web_search"] = {
            "required": False,
            "query": "",
            "reason": "报告只给了案情描述、没有可用的漏洞类型名称，需人工确认后再检索。",
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
    """互联网查询词。

    红线：查询词不得带客户名称、内网地址、案件正文。编号是最精确的查询词，
    有 CVE 就只发编号；没有编号时名称只取第一句并截断，取出来仍像案情
    描述的（"获取××主机管理员权限"这类）整条弃用，转人工确认。
    """
    name = re.sub(r"^\s*\d+(?:\s*\.\s*\d+)+\s*|\d{1,2}\s*[、.．,，]\s*", "", str(vuln.get("name") or ""))
    name = re.sub(r"[【\[][^】\]]*[】\]]", "", name)
    # 等级/状态括号对检索没有增量，去掉后查询词更干净
    name = re.sub(
        r"[（(]\s*(?:严重|高危|高|中危|中|低危|低|信息)"
        r"(?:\s*[/\-—,，、]\s*(?:严重|高危|高|中危|中|低危|低|信息|待修复|已修复|已关闭|待整改|已整改))?"
        r"\s*(?:风险|漏洞|等级|问题|级别|状态)?\s*[)）]",
        "",
        name,
    )
    name = name.strip(" ：:，,、")
    # 标题行尾部的页码残留
    name = re.sub(r"\s+\d{1,3}\s*$", "", name)
    cve = str(vuln.get("cve") or "").strip().upper()
    if cve:
        return f"{cve} 安全 漏洞 修复 加固 官方建议"
    head = re.split(r"[。；;！!？?\n]", name)[0]
    head = re.split(r"[，,]", head)[0][:_WEB_NAME_MAX].strip()
    if not head or _PROSE_MARK.search(head):
        return ""
    return f"{head} 安全 漏洞 修复 加固 官方建议"


def enrich_all(
    vulns: list[dict[str, Any]],
    repo_path: str = r"D:\git\redmine-similar-assist",
    with_sec_pool: bool = True,
) -> list[dict[str, Any]]:
    bridge = SimilarAssistBridge(repo_path)
    sec_bridge = SecKbBridge() if with_sec_pool else None
    # 漏扫清单里同名漏洞占绝大多数（"SSH 服务支持弱加密算法"能重复几百次），
    # 按「漏洞名+CVE」去重后只检索唯一条，结果共享给同键的所有漏洞——
    # 1132 条的案件收敛到 ~260 条唯一键。检索命中由名称/CVE 决定，描述的
    # 差异不影响命中，不值得为它翻倍检索量
    items: list[dict[str, Any]] = []
    key_first_index: dict[tuple, int] = {}
    key_of_index: dict[int, tuple] = {}
    for index, vuln in enumerate(vulns):
        key = (
            str(vuln.get("name") or "").strip(),
            str(vuln.get("cve") or "").strip().upper(),
        )
        if key in key_first_index:
            key_of_index[index] = key
            continue
        key_first_index[key] = index
        key_of_index[index] = key
        items.append({"id": index, "query": build_query(vuln)})

    with ThreadPoolExecutor(max_workers=2) as pool:
        full_future = pool.submit(bridge.search_internal_batch, items)
        sec_future = (
            pool.submit(sec_bridge.search_batch, items) if sec_bridge else None
        )
        full_batch = full_future.result()
        sec_batch = sec_future.result() if sec_future else {}

    def _internal_for(index: int) -> dict[str, Any]:
        representative = key_first_index[key_of_index[index]]
        return merge_internal(sec_batch.get(representative), full_batch.get(representative))

    return [
        enrich_vulnerability(
            vuln,
            bridge,
            internal=_internal_for(index),
            sec_bridge=sec_bridge,
        )
        for index, vuln in enumerate(vulns)
    ]
