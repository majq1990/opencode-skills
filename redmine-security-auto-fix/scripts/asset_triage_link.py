# -*- coding: utf-8 -*-
"""v2.0 可选后处理：把三源研判案件关联回 process_issue 的 enriched 漏洞列表。

process_issue.py --with-asset-triage --triage-cases <cases_*.json> 时启用，
默认关闭（关闭时 v1.1.0 行为完全不变）。本模块为纯函数、无 IO，便于单测。

attach(vulns, cases_doc) 规则：
  - 对每条漏洞取其 cve 字段（字符串或列表均可，strip+upper 归一，空值跳过）；
  - 在 cases_doc["cases"] 里按 cve_id 精确匹配，同 CVE 多资产可命中多案件；
  - 命中：vuln["asset_triage"] = [{"case_id","level","risk_score","owner",
    "owner_source","due_at","sla_hours","asset_ip","hostname"}]；
  - 未命中不报错，只计数。

返回汇总 dict（rules_version / matched / unmatched / case_links）。
render_section(vulns, meta) 生成追加到 fix_plan.md 末尾的 markdown 小节；
没有任何命中时返回空串（不污染原文档结构）。
"""
from __future__ import annotations

CASE_LINK_FIELDS = (
    "case_id", "level", "risk_score", "owner", "owner_source",
    "due_at", "sla_hours", "asset_ip", "hostname",
)


def _cve_ids_of(vuln: dict) -> list[str]:
    raw = vuln.get("cve")
    if not raw:
        return []
    if isinstance(raw, str):
        candidates = [part.strip() for part in raw.replace(",", " ").split()]
    elif isinstance(raw, (list, tuple)):
        candidates = [str(part).strip() for part in raw]
    else:
        return []
    return [c.upper() for c in candidates if c]


def attach(vulns: list[dict], cases_doc: dict) -> dict:
    cases_by_cve: dict[str, list[dict]] = {}
    for case in cases_doc.get("cases") or []:
        cve_id = str(case.get("cve_id") or "").strip().upper()
        if cve_id:
            cases_by_cve.setdefault(cve_id, []).append(case)

    matched = unmatched = links = 0
    for vuln in vulns:
        hits: list[dict] = []
        for cve_id in _cve_ids_of(vuln):
            for case in cases_by_cve.get(cve_id, []):
                hits.append({field: case.get(field) for field in CASE_LINK_FIELDS})
        if hits:
            vuln["asset_triage"] = hits
            matched += 1
            links += len(hits)
        else:
            unmatched += 1
    return {
        "rules_version": (cases_doc.get("meta") or {}).get("rules_version", ""),
        "triage_date": (cases_doc.get("meta") or {}).get("date", ""),
        "matched_vulns": matched,
        "unmatched_vulns": unmatched,
        "case_links": links,
    }


def render_section(vulns: list[dict], meta: dict) -> str:
    lines = [
        "",
        "---",
        "",
        "## 资产对照与责任人（三源研判，规则版本 %s，研判日 %s）" % (
            meta.get("rules_version", "-"), meta.get("date", "-")),
        "",
        "> 来源：`triage_cases.py` 产出（CVE 情报 × 扫描结果 × 资产台账）。"
        "台账 owner 为定责依据；无命中漏洞不列示。",
        "",
        "| 漏洞 | CVE | 案件号 | 级别 | 风险分 | 责任人 | 资产 | SLA 截止 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    rows = 0
    for vuln in vulns:
        cve_list = "、".join(_cve_ids_of(vuln)) or "-"
        for hit in vuln.get("asset_triage") or []:
            lines.append("| %s | %s | %s | %s | %s | %s | %s(%s) | %s |" % (
                vuln.get("name") or "-",
                cve_list,
                hit.get("case_id") or "-",
                hit.get("level") or "-",
                hit.get("risk_score") if hit.get("risk_score") is not None else "-",
                "%s（%s）" % (hit.get("owner") or "-", hit.get("owner_source") or "-"),
                hit.get("hostname") or "-",
                hit.get("asset_ip") or "-",
                hit.get("due_at") or "-",
            ))
            rows += 1
    if not rows:
        return ""
    lines.append("")
    return "\n".join(lines)
