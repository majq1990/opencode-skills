#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bridge to the server-side sec_kb security pool (demo.egova.com.cn).

与 `similar_assist_bridge.py` 的分工：

  - similar_assist_bridge：全库检索（19.9 万工单 + 7,700 篇文档），sqlite-vec KNN
    + LLM gate，覆盖面广但不区分安全与非安全。
  - 本文件：只检索**安全池**——tracker_id=26 的安全案件 + 语义审计回填的漏召案件
    （当前 9,000+ 条）+ 297 篇已打安全标记的文档 + NVD/GHSA 外部情报，
    走服务器上的安全专用小索引，秒级返回。

两条链路互补：全库回答"历史上有没有人处理过类似问题"，安全池回答
"安全问题我们内部是怎么处置的、有没有现成修复操作、外部有没有对应 CVE"。

只读，不写任何服务器数据；失败时返回 `_error`，由调用方回落到
similar_assist_bridge，不阻塞主流程。
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

# 宿主机与容器的 bind mount 对应路径（/opt/redmine-assist/data ↔ /app/data）
REMOTE_HOST_DATA_DIR = "/opt/redmine-assist/data"
REMOTE_CTR_DATA_DIR = "/app/data"

REMOTE_DEFAULTS = {
    "enabled": True,
    "ssh_host": "demo.egova.com.cn",
    "container": "redmine-assist",
}

RESULT_MARKER = "===SEC_KB_RESULT==="

# 容器内执行：调 sec_kb.query 的 structured 输出，本 runner 不做任何检索口径判断
# （阈值、★安全文档优先、按 node_id 去重全部由 sec_kb 侧实现，避免两处漂移）。
_REMOTE_RUNNER = r'''
# -*- coding: utf-8 -*-
import json
import sys

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/scripts")

MARKER = "===SEC_KB_RESULT==="

from sec_kb.query import sec_query

request = json.load(open(sys.argv[1], encoding="utf-8"))
top_cases = int(request.get("top_cases", 8))
top_docs = int(request.get("top_docs", 5))
results = []

for item in request.get("queries", []):
    entry = {"id": item.get("id"), "history": [], "knowledge": [],
             "external_intel": [], "error": None, "engine": None}
    try:
        res = sec_query(
            item["query"],
            top_cases=top_cases,
            top_docs=top_docs,
            use_llm=False,          # 桥接只做召回，综合研判交给 skill 自己的 LLM 步骤
            pool=request.get("pool", "sec"),
            fast=bool(request.get("fast", True)),
            structured=True,
        )
        entry["engine"] = (res.get("stats") or {}).get("engine")
        for c in res.get("cases") or []:
            resolution = (c.get("resolution") or "").strip()
            # 没有实际处理内容的候选不算有效修复建议（与 similar_assist_bridge 同规则）
            if len(resolution) < 8:
                continue
            entry["history"].append({
                "type": "sec_pool_history",
                "issue_id": c.get("issue_id"),
                "title": c.get("subject") or "",
                "score": round(float(c.get("cosine") or 0.0), 4),
                "suggestion": resolution[:2000],
                "tracker_id": c.get("tracker_id"),
                "status": c.get("status") or "",
                "vuln_kind": c.get("vuln_kind") or "",
                "product_line": c.get("product_line") or "",
                "severity_hint": c.get("severity_hint") or "",
                "has_fix_record": bool(c.get("has_fix_record")),
                "match_reason": c.get("match_reason") or "",
                "updated_on": c.get("updated_on") or "",
            })
        for d in res.get("docs") or []:
            text = (d.get("text") or "").strip()
            if len(text) < 8:
                continue
            entry["knowledge"].append({
                "type": "sec_pool_kb",
                "node_id": d.get("node_id"),
                "title": d.get("title") or d.get("heading") or "",
                "url": d.get("url") or "",
                "score": round(float(d.get("cosine") or 0.0), 4),
                "suggestion": text[:2000],
                "is_sec_doc": bool(d.get("is_sec_doc")),
            })
        for i in res.get("intel") or []:
            entry["external_intel"].append({
                "type": "external_intel",
                "cve_id": i.get("cve_id") or "",
                "title": i.get("title") or "",
                "source": i.get("source") or "",
                "severity": i.get("severity") or "",
                "cvss": i.get("cvss"),
                "published": i.get("published") or "",
                "url": i.get("url") or "",
                # 命中的公司关注面组件（sec_kb.watchlist 从案件语料派生）。
                # 空列表表示这条是提问者显式点名 CVE 编号带出来的，不代表与公司环境相关。
                "matched": list(i.get("matched") or []),
            })
        entry["history"].sort(key=lambda r: r["score"], reverse=True)
        entry["knowledge"].sort(key=lambda r: r["score"], reverse=True)
    except Exception as exc:
        entry["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
    results.append(entry)

sys.stdout.write("\n" + MARKER + "\n")
json.dump({"results": results}, sys.stdout, ensure_ascii=False)
'''


def _remote_cfg(remote_cfg: dict | None) -> dict:
    merged = dict(REMOTE_DEFAULTS)
    if remote_cfg:
        merged.update({k: v for k, v in remote_cfg.items() if v is not None})
    return merged


class SecKbBridge:
    """Read-only bridge to the sec_kb security pool on the demo server."""

    def __init__(
        self,
        ssh_host: str = "demo.egova.com.cn",
        container: str = "redmine-assist",
        enabled: bool = True,
    ) -> None:
        self.ssh_host = ssh_host
        self.container = container
        self.enabled = enabled

    # ------------------------------------------------------------------ 传输层

    def _ssh_run(self, command: str, input_bytes: bytes | None = None,
                 timeout_s: int = 300) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
             self.ssh_host, command],
            input=input_bytes, capture_output=True, timeout=timeout_s,
        )

    def _run_remote(self, items: list[dict], top_cases: int, top_docs: int,
                    pool: str, fast: bool) -> dict:
        host = self.ssh_host
        stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S%f")
        host_runner = f"{REMOTE_HOST_DATA_DIR}/.sec_kb_runner_{stamp}.py"
        host_request = f"{REMOTE_HOST_DATA_DIR}/.sec_kb_request_{stamp}.json"
        ctr_runner = f"{REMOTE_CTR_DATA_DIR}/.sec_kb_runner_{stamp}.py"
        ctr_request = f"{REMOTE_CTR_DATA_DIR}/.sec_kb_request_{stamp}.json"

        payload = json.dumps(
            {
                "queries": [{"id": it["id"], "query": it["query"]} for it in items],
                "top_cases": top_cases,
                "top_docs": top_docs,
                "pool": pool,
                "fast": fast,
            },
            ensure_ascii=False,
        ).encode("utf-8")

        up1 = self._ssh_run(f"cat > {host_runner}", _REMOTE_RUNNER.encode("utf-8"))
        if up1.returncode != 0:
            raise RuntimeError(
                f"upload runner failed: {up1.stderr.decode('utf-8', 'replace')[:300]}"
            )
        up2 = self._ssh_run(f"cat > {host_request}", payload)
        if up2.returncode != 0:
            self._ssh_run(f"rm -f {host_runner}", timeout_s=30)
            raise RuntimeError(
                f"upload request failed: {up2.stderr.decode('utf-8', 'replace')[:300]}"
            )

        try:
            # 快路径秒级；pool=all/fast=False 回落全库 faiss，冷启动可达 12 分钟
            proc = self._ssh_run(
                f"docker exec -e PYTHONIOENCODING=utf-8 -e PYTHONPATH=/app:/app/scripts "
                f"-w /app {self.container} python -u {ctr_runner} {ctr_request}",
                timeout_s=2400,
            )
        finally:
            self._ssh_run(f"rm -f {host_runner} {host_request}", timeout_s=30)

        stdout = proc.stdout.decode("utf-8", errors="replace")
        idx = stdout.rfind(RESULT_MARKER)
        if proc.returncode != 0 or idx < 0:
            raise RuntimeError(
                f"rc={proc.returncode} stderr={proc.stderr.decode('utf-8', 'replace')[:400]}"
            )
        return json.loads(stdout[idx + len(RESULT_MARKER):].strip())

    # ------------------------------------------------------------------ 检索层

    def search_security_pool(
        self,
        query: str,
        top_cases: int = 8,
        top_docs: int = 5,
        pool: str = "sec",
        fast: bool = True,
    ) -> dict:
        """检索安全池，返回与 similar_assist_bridge 同构的 history/knowledge，
        外加 external_intel（NVD/GHSA 情报，全库链路没有这一路）。"""
        if not self.enabled:
            return {"history": [], "knowledge": [], "external_intel": [],
                    "engine": None, "_error": "disabled"}
        try:
            data = self._run_remote(
                [{"id": 0, "query": query}], top_cases, top_docs, pool, fast
            )
        except Exception as exc:
            return {"history": [], "knowledge": [], "external_intel": [],
                    "engine": None, "_error": f"{type(exc).__name__}: {exc}"}
        row = (data.get("results") or [{}])[0]
        return {
            "history": row.get("history") or [],
            "knowledge": row.get("knowledge") or [],
            "external_intel": row.get("external_intel") or [],
            "engine": row.get("engine"),
            "_error": row.get("error"),
        }

    def search_batch(
        self,
        queries: Iterable[dict],
        top_cases: int = 8,
        top_docs: int = 5,
        pool: str = "sec",
        fast: bool = True,
    ) -> dict:
        """批量检索。queries: [{"id": ..., "query": ...}]，按 id 返回。"""
        items = [{"id": q.get("id"), "query": q["query"]} for q in queries]
        if not self.enabled or not items:
            return {}
        try:
            data = self._run_remote(items, top_cases, top_docs, pool, fast)
        except Exception as exc:
            return {it["id"]: {"history": [], "knowledge": [],
                               "external_intel": [], "engine": None,
                               "_error": f"{type(exc).__name__}: {exc}"}
                    for it in items}
        out: dict = {}
        for row in data.get("results") or []:
            out[row.get("id")] = {
                "history": row.get("history") or [],
                "knowledge": row.get("knowledge") or [],
                "external_intel": row.get("external_intel") or [],
                "engine": row.get("engine"),
                "_error": row.get("error"),
            }
        return out


def main() -> int:
    """命令行自测：python sec_kb_bridge.py "查询词" [--pool all] [--no-fast]"""
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--pool", choices=["sec", "all"], default="sec")
    ap.add_argument("--no-fast", action="store_true")
    ap.add_argument("--top-cases", type=int, default=8)
    ap.add_argument("--top-docs", type=int, default=5)
    args = ap.parse_args()

    bridge = SecKbBridge()
    res = bridge.search_security_pool(
        args.query, top_cases=args.top_cases, top_docs=args.top_docs,
        pool=args.pool, fast=not args.no_fast,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))
    if res.get("_error"):
        print(f"[warn] {res['_error']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
