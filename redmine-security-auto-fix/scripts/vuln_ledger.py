#!/usr/bin/env python3
"""安全漏洞台账（钉钉多维表「安全漏洞台账」）只读查询。

台账是公司级持续更新的权威漏洞清单，**检索优先级第一**：处理案件时先查
台账——CVE 已登记且带处理方案的，直接沿用，不再走互联网搜索；台账查不到
的才依次走内部检索和搜索兜底。

依赖 `dws` CLI（钉钉工作台命令行，认证由其 profile 管理），本模块只做只读
调用：base/field/record query。

用法：
  python scripts\\vuln_ledger.py lookup "CVE-2024-38819,CVE-2021-44228"
  python scripts\\vuln_ledger.py lookup <enriched.json>     # 从结果 JSON 取全部 CVE
  python scripts\\vuln_ledger.py recent --days 7            # 最近 N 天新录入（日常查看）
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

_DWS = shutil.which("dws") or "dws"

DEFAULT_BASE_ID = "qnYMoO1rWxDl1N54sz3zaKemW47Z3je9"  # 安全漏洞台账
# CVE 跟踪表（用户指定为日常 CVE 获取与方案查询的第一来源）
DEFAULT_TABLE_ID = "S2LBsat"

# 字段名 → 列 ID（2026-09-30 实测；运行时仍会先拉一次 field get 校准）
FIELD_IDS = {
    "CVE编号": "sRKdhAT",
    "漏洞名称": "NIDPdMM",
    "CVSS": "XRthl81",
    "危险程度": "olQTi1r",
    "披露日期": "d2Jq3zA",
    "信息来源": "1iQXQdS",
    "影响组件": "VadxQje",
    "漏洞描述": "PAt1bo0",
    "是否涉及": "8SLXQm9",
    "分类": "VaD5ZQS",
    "状态": "BG2HzNm",
    "标签": "cKUY2PI",
    "修复文档链接": "Ypqicnc",
    "Redmine案件号": "4gLnEHB",
    "详情链接": "sm0lBBl",
    "CNVD编号": "VX5heJp",
    "录入日期": "9V0Xwza",
}


class LedgerError(RuntimeError):
    pass


def _dws(args: list[str], timeout_s: int = 120) -> dict:
    proc = subprocess.run(
        [_DWS, *args, "--format", "json", "--timeout", str(timeout_s)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout_s + 30,
    )
    out = proc.stdout.strip()
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        raise LedgerError(f"dws 输出不是 JSON: {out[:200]}") from exc
    if isinstance(data, dict) and data.get("error"):
        err = data["error"]
        raise LedgerError(f"dws 错误: {err.get('message', err)}")
    if proc.returncode != 0:
        raise LedgerError(f"dws 退出码 {proc.returncode}: {proc.stderr[:200]}")
    return data


def resolve_field_ids(base_id: str, table_id: str) -> dict[str, str]:
    """拉一次字段列表校准 名称→列ID 映射；失败则退回内置映射。"""
    try:
        data = _dws(["aitable", "field", "get", "--base-id", base_id, "--table-id", table_id])
        fields = (data.get("data") or {}).get("fields") or []
        live = {f.get("fieldName"): f.get("fieldId") for f in fields if f.get("fieldName") and f.get("fieldId")}
        if live:
            merged = dict(FIELD_IDS)
            merged.update(live)
            return merged
    except (LedgerError, OSError, subprocess.SubprocessError):
        pass
    return dict(FIELD_IDS)


def query_records(base_id: str, table_id: str, filters: dict | None = None,
                  limit: int = 200) -> list[dict]:
    """读记录（自动翻页），返回 [{recordId, cells}]。cells 的键是列 ID。"""
    args = ["aitable", "record", "query", "--base-id", base_id, "--table-id", table_id,
            "--limit", str(min(limit, 100))]
    if filters:
        args += ["--filters", json.dumps(filters, ensure_ascii=False)]
    records: list[dict] = []
    cursor = None
    for _ in range(10):  # 硬上限防失控
        cmd = args + (["--cursor", cursor] if cursor else [])
        data = _dws(cmd)
        payload = data.get("data") or {}
        records.extend(payload.get("records") or [])
        cursor = payload.get("nextCursor")
        if not cursor:
            break
    return records


def _cell_name(cell) -> str:
    """单选/成员等单元格是 {id, name} 结构，取 name；普通值原样返回。"""
    if isinstance(cell, dict):
        return str(cell.get("name") or cell.get("text") or "")
    if isinstance(cell, list):
        names = [n for c in cell if (n := _cell_name(c))]
        return "、".join(names)
    return "" if cell is None else str(cell)


def lookup_cves(cves: list[str], base_id: str = DEFAULT_BASE_ID,
                table_id: str = DEFAULT_TABLE_ID) -> dict[str, dict]:
    """按 CVE 编号批量查台账，返回 {cve: 台账记录(字段名化)}；未登记的 CVE 不在结果里。"""
    cves = sorted({c.strip().upper() for c in cves if c and c.strip()})
    if not cves:
        return {}
    fmap = resolve_field_ids(base_id, table_id)
    cve_field = fmap.get("CVE编号")
    if not cve_field:
        raise LedgerError("台账缺少「CVE编号」列")
    found: dict[str, dict] = {}
    # 过滤条件一次最多塞 20 个，分批查
    for start in range(0, len(cves), 20):
        batch = cves[start : start + 20]
        filters = {
            "operator": "or",
            "operands": [
                {"operator": "eq", "operands": [cve_field, cve]} for cve in batch
            ],
        }
        for record in query_records(base_id, table_id, filters):
            cells = record.get("cells") or {}
            row = {}
            for name, col in fmap.items():
                if col in cells:
                    row[name] = _cell_name(cells[col])
            cve_value = str(row.get("CVE编号") or "").strip().upper()
            if cve_value:
                found[cve_value] = row
    return found


def attach_to_vulns(vulns: list[dict], base_id: str = DEFAULT_BASE_ID,
                    table_id: str = DEFAULT_TABLE_ID) -> dict[str, dict]:
    """给结果 JSON 的漏洞数组挂台账命中：v['ledger'] = {...}。

    台账已登记处理方案（有修复文档链接或状态非待定）的，直接改写
    web_search 决定：不再需要互联网搜索。
    """
    cves = sorted({str(v.get("cve") or "").strip().upper() for v in vulns if v.get("cve")})
    if not cves:
        return {}
    hits = lookup_cves(cves, base_id, table_id)
    suppressed = 0
    for v in vulns:
        cve = str(v.get("cve") or "").strip().upper()
        hit = hits.get(cve)
        if not hit:
            continue
        v["ledger"] = hit
        # 该表实际状态记在「标签」列（处理中/已解决…），「状态」列多为空
        status = hit.get("标签") or hit.get("状态")
        hit["状态"] = status or hit.get("状态") or ""
        has_solution = bool(hit.get("修复文档链接")) or status not in (None, "", "待定")
        ws = v.get("web_search")
        if has_solution and isinstance(ws, dict) and ws.get("required"):
            ws["required"] = False
            ws["reason"] = (
                f"台账已登记（状态：{hit.get('状态') or '未知'}），沿用台账方案，不做互联网搜索。"
            )
            suppressed += 1
        if has_solution:
            v.setdefault("recommendations", []).insert(0, {
                "source": "ledger",
                "suggestion": (
                    f"台账已登记：状态「{hit.get('状态') or '未知'}」"
                    + (f"，CVSS {hit['CVSS']}" if hit.get("CVSS") else "")
                    + (f"，修复文档：{hit['修复文档链接']}" if hit.get("修复文档链接") else "")
                ),
                "reference": {"cve": cve, "ledger": hit},
            })
    return {"matched": len(hits), "suppressed_web_search": suppressed,
            "hits": hits}


def recent(days: int = 7, base_id: str = DEFAULT_BASE_ID,
           table_id: str = DEFAULT_TABLE_ID) -> list[dict]:
    """最近 N 天新录入的台账记录（按「录入日期」过滤），供日常 CVE 查看。"""
    fmap = resolve_field_ids(base_id, table_id)
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    filters = {
        "operator": "and",
        "operands": [
            {"operator": "not_before", "operands": [fmap["录入日期"], since]},
        ],
    }
    rows = []
    for record in query_records(base_id, table_id, filters, limit=100):
        cells = record.get("cells") or {}
        row = {name: _cell_name(cells.get(col)) for name, col in fmap.items() if col in cells}
        if row.get("CVE编号") or row.get("漏洞名称"):
            rows.append(row)
    return rows


def _extract_cves_from_enriched(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return sorted({
        str(v.get("cve") or "").strip().upper()
        for v in data.get("vulns") or [] if v.get("cve")
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_lookup = sub.add_parser("lookup", help="按 CVE 批量查台账")
    p_lookup.add_argument("target", help="逗号分隔的 CVE 列表，或 enriched JSON 路径")
    p_lookup.add_argument("--base-id", default=DEFAULT_BASE_ID)
    p_lookup.add_argument("--table-id", default=DEFAULT_TABLE_ID)

    p_recent = sub.add_parser("recent", help="最近 N 天新录入的台账记录")
    p_recent.add_argument("--days", type=int, default=7)
    p_recent.add_argument("--base-id", default=DEFAULT_BASE_ID)
    p_recent.add_argument("--table-id", default=DEFAULT_TABLE_ID)

    args = parser.parse_args()
    try:
        if args.cmd == "lookup":
            target = args.target.strip()
            if target.endswith(".json") and Path(target).exists():
                cves = _extract_cves_from_enriched(Path(target))
            else:
                cves = re.split(r"[,，;；\s]+", target)
            hits = lookup_cves(cves, args.base_id, args.table_id)
            print(json.dumps(hits, ensure_ascii=False, indent=1))
            print(f"查询 {len(set(cves))} 个 CVE，台账命中 {len(hits)} 个", file=sys.stderr)
            return 0
        rows = recent(args.days, args.base_id, args.table_id)
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"最近 {args.days} 天新录入 {len(rows)} 条", file=sys.stderr)
        return 0
    except LedgerError as exc:
        print(f"台账查询失败: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
