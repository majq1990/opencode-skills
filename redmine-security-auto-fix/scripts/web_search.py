#!/usr/bin/env python3
"""anysearch 互联网搜索兜底（本 skill 默认搜索源）。

查询词一律来自 recommendation_engine._build_web_query 的产物（已过红线：
只含通用漏洞名/CVE/组件，禁止客户名称、内网地址、案件正文）。

用法：
  python scripts\\web_search.py search "CVE-2024-38819 修复 官方建议" [--max-results 3]
  python scripts\\web_search.py draft <enriched.json> [--out <draft.json>] [--per-vuln 1] [--limit 20]

draft 子命令：对结果 JSON 里所有 `web_search.required` 的漏洞逐条搜索，
生成待审核的 web_results 草稿——人工/Agent 审核修订后，再用
apply_web_results.py 合并回结果 JSON。草稿内容是原始搜索摘要，未审核不得合并。

Key 优先级：环境变量 ANYSEARCH_API_KEY → skill 根目录 .env → 匿名访问。
匿名有速率限制，初始化时推荐配置 key（https://anysearch.com/console/api-keys）。
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import socket
import ssl
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests

SCRIPTS = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

_REVALIDATE_HOST = "api.anysearch.com"


def _validate_endpoint(endpoint: str) -> None:
    """出站前固定校验：仅允许 https + 官方域名，解析 IP 必须为公网。"""
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or parsed.hostname != _REVALIDATE_HOST:
        raise ValueError(f"endpoint 只允许 https://{_REVALIDATE_HOST}，当前: {endpoint}")
    for info in socket.getaddrinfo(parsed.hostname, 443, proto=socket.IPPROTO_TCP):
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise ValueError(f"{_REVALIDATE_HOST} 解析到非公网地址 {ip}，拒绝请求")


def load_api_key() -> str | None:
    """环境变量优先，其次 skill 根目录 .env（ANYSEARCH_API_KEY=...），都没有则匿名。"""
    key = os.environ.get("ANYSEARCH_API_KEY")
    if key:
        return key.strip()
    env_file = SKILL_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("ANYSEARCH_API_KEY="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return value
    return None


def call_anysearch(query: str, max_results: int = 3, attempts: int = 3) -> str:
    """调用 anysearch MCP 端点做一次搜索，返回结果文本。网络抖动退避重试。"""
    _validate_endpoint("https://api.anysearch.com/mcp")
    headers = {"Content-Type": "application/json"}
    api_key = load_api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search",
            "arguments": {"query": query, "max_results": max_results},
        },
    }
    last_error: Exception | None = None
    resp = None
    for attempt in range(attempts):
        if attempt:
            time.sleep(5 * attempt)
        try:
            resp = requests.post(
                "https://api.anysearch.com/mcp", json=payload,
                headers=headers, timeout=90, allow_redirects=False,
            )
            resp.raise_for_status()
            break
        except requests.exceptions.HTTPError as exc:
            detail = ""
            try:
                detail = resp.json().get("error", {}).get("message", "")
            except Exception:
                detail = resp.text[:300]
            raise RuntimeError(f"anysearch HTTP 错误: {exc} {detail}") from exc
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
                ssl.SSLError, OSError) as exc:
            last_error = exc
            print(f"[web_search] 第 {attempt + 1}/{attempts} 次失败: "
                  f"{type(exc).__name__}: {str(exc)[:120]}", file=sys.stderr, flush=True)
    else:
        raise RuntimeError(f"anysearch 连续 {attempts} 次不可达: {last_error}")

    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"anysearch API 错误: {data['error'].get('message', data['error'])}")
    for item in data.get("result", {}).get("content", []):
        if item.get("type") == "text":
            return item.get("text", "")
    raise RuntimeError("anysearch 返回为空")


def parse_results(text: str) -> list[dict]:
    """解析 anysearch 结果文本：`### N. 标题` + `- **URL**: ...` + 摘要行。"""
    results: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        heading = re.match(r"^###\s+\d+\.\s+(.+)$", line.strip())
        if heading:
            if current:
                results.append(current)
            current = {"title": heading.group(1).strip(), "url": "", "snippet": ""}
            continue
        if current is None:
            continue
        url = re.match(r"^-\s*\*\*URL\*\*[:：]\s*(\S+)", line.strip())
        if url:
            current["url"] = url.group(1)
            continue
        bullet = re.match(r"^-\s+(.+)$", line.strip())
        if bullet and not line.strip().startswith("- **URL**"):
            snippet = bullet.group(1).strip()
            if snippet and len(current["snippet"]) < 600:
                current["snippet"] += (" " if current["snippet"] else "") + snippet
    if current:
        results.append(current)
    return [r for r in results if r["url"].startswith(("http://", "https://"))]


def build_draft(enriched_path: Path, out_path: Path, per_vuln: int, limit: int) -> int:
    """对 enriched JSON 里待搜索漏洞生成 web_results 草稿，返回草稿条数。"""
    sys.path.insert(0, str(SCRIPTS))
    from recommendation_engine import _build_web_query  # 红线：查询词必须过引擎

    data = json.loads(enriched_path.read_text(encoding="utf-8"))
    pending = [
        v for v in data.get("vulns") or []
        if (v.get("web_search") or {}).get("required")
    ]
    if limit > 0:
        pending = pending[:limit]
    rows = []
    for vuln in pending:
        query = (vuln.get("web_search") or {}).get("query") or _build_web_query(vuln)
        if not query:
            continue
        print(f"[draft] #{vuln.get('id')} {query}", file=sys.stderr, flush=True)
        try:
            found = parse_results(call_anysearch(query, max_results=max(3, per_vuln)))
        except RuntimeError as exc:
            print(f"[draft] 搜索失败，跳过: {exc}", file=sys.stderr, flush=True)
            continue
        for hit in found[:per_vuln]:
            publisher = urlparse(hit["url"]).netloc
            rows.append({
                "id": vuln["id"],
                "vuln_id": vuln["id"],
                "name": vuln.get("name") or "",
                "query": query,
                "title": hit["title"],
                "url": hit["url"],
                "publisher": publisher,
                "suggestion": f"{hit['title']}。{hit['snippet']}"[:1200],
                "accessed_at": date.today().isoformat(),
                "_review_status": "draft-unreviewed",
            })
    out_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return len(rows)


import re  # noqa: E402  （parse_results 使用；置于底部避免打断参数说明）


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search", help="单次搜索并打印结果")
    p_search.add_argument("query")
    p_search.add_argument("--max-results", type=int, default=3)

    p_draft = sub.add_parser("draft", help="批量生成待审核 web_results 草稿")
    p_draft.add_argument("enriched_json")
    p_draft.add_argument("--out", default=None)
    p_draft.add_argument("--per-vuln", type=int, default=1)
    p_draft.add_argument("--limit", type=int, default=0, help="最多处理几条，0=全部")

    args = parser.parse_args()
    if args.cmd == "search":
        print(call_anysearch(args.query, max_results=args.max_results))
        return 0
    enriched = Path(args.enriched_json)
    out = Path(args.out) if args.out else enriched.with_name(
        enriched.stem.replace("_enriched", "") + "_web_results_draft.json"
    )
    count = build_draft(enriched, out, args.per_vuln, args.limit)
    print(f"草稿已写出: {out}（{count} 条，_review_status=draft-unreviewed）")
    print("未经人工/Agent 审核修订，不得用 apply_web_results.py 合并。")
    return 0 if count else 1


if __name__ == "__main__":
    sys.exit(main())
