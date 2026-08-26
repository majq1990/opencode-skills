#!/usr/bin/env python3
"""Bridge to redmine-similar-assist without copying its credentials."""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

# 远端批量检索：完整知识库在 demo.egova.com.cn 容器内（本地 vectors.db 只是过时副本）。
# 查询打包经 ssh+docker exec 送入容器执行 embed+KNN+LLM gate，一次索引加载处理全部查询。
RESULT_MARKER = "===RESULT_JSON==="

REMOTE_DEFAULTS = {
    "enabled": True,
    "ssh_host": "demo.egova.com.cn",
    "container": "redmine-assist",
}

_REMOTE_RUNNER = r'''
# 容器内执行：sqlite-vec SQL KNN（绕开 faiss 全量加载）+ LLM gate
import json
import sys

sys.path.insert(0, "/app")

import numpy as np
import sqlite3
import sqlite_vec

DB_PATH = "/app/data/vectors.db"


def open_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


CONN = open_db()


def knn_candidates(table: str, meta_sql: str, query_vec, top: int) -> list[dict]:
    """sqlite-vec 暴力 MATCH 召回；取回候选向量精确算余弦并剔除零向量。"""
    blob = struct_pack(query_vec)
    over = max(top * 3, 12)
    rows = CONN.execute(
        f"SELECT rowid, distance FROM {table} "
        f"WHERE embedding MATCH ? AND k = ? ORDER BY distance",
        (blob, over),
    ).fetchall()
    qn = np.asarray(query_vec, dtype="float32")
    qn = qn / (np.linalg.norm(qn) or 1.0)
    out: list[dict] = []
    seen = set()
    for rowid, _dist in rows:
        if len(out) >= top:
            break
        if rowid in seen:
            continue
        seen.add(rowid)
        buf = CONN.execute(
            f"SELECT embedding FROM {table} WHERE rowid=?", (rowid,)
        ).fetchone()[0]
        v = np.frombuffer(buf, dtype="float32")
        norm = float(np.linalg.norm(v))
        if norm < 1e-6:
            continue
        cos = float(np.dot(qn, v / norm))
        meta = CONN.execute(meta_sql, (rowid,)).fetchone()
        if not meta:
            continue
        item = dict(zip(meta.keys(), meta))
        item["cosine"] = cos
        out.append(item)
    return out


def struct_pack(vec):
    import struct

    return struct.pack(f"{len(vec)}f", *vec)


def search_one(query: str, top: int, min_relevance: float) -> dict:
    from src.embedder import Embedder
    from src.llm_judge import judge, judge_docs

    embedding = Embedder().embed([query])[0]

    issue_candidates = knn_candidates(
        "vec_issues",
        "SELECT issue_id, subject, status, closed_on, resolution "
        "FROM issues_meta WHERE issue_id=?",
        embedding,
        top,
    )
    verdicts = judge(
        query,
        [
            {
                "issue_id": r["issue_id"],
                "subject": r.get("subject") or "",
                "resolution": r.get("resolution") or "",
            }
            for r in issue_candidates
        ],
    )
    by_id = {r["issue_id"]: r for r in issue_candidates}
    history = []
    for v in verdicts:
        if not v.get("related"):
            continue
        row = by_id.get(int(v.get("issue_id", 0)))
        if not row:
            continue
        score = float(v.get("score", row.get("cosine", 0)))
        if score < min_relevance:
            continue
        history.append(
            {
                "type": "redmine_history",
                "issue_id": row["issue_id"],
                "title": row.get("subject") or "",
                "score": score,
                "suggestion": v.get("solution") or "",
            }
        )

    doc_candidates = knn_candidates(
        "vec_docs",
        "SELECT node_id, title, url, summary FROM docs_meta WHERE node_id=?",
        [float(x) for x in embedding],
        top,
    )
    doc_verdicts = judge_docs(
        query,
        [
            {
                "node_id": r["node_id"],
                "title": r.get("title") or "",
                "summary": r.get("summary") or "",
            }
            for r in doc_candidates
        ],
    )
    docs_by_id = {str(r["node_id"]): r for r in doc_candidates}
    knowledge = []
    for v in doc_verdicts:
        if not v.get("related"):
            continue
        row = docs_by_id.get(str(v.get("node_id") or ""))
        if not row:
            continue
        score = float(v.get("score", row.get("cosine", 0)))
        if score < min_relevance:
            continue
        knowledge.append(
            {
                "type": "knowledge_base",
                "node_id": row["node_id"],
                "title": row.get("title") or "",
                "url": row.get("url") or "",
                "score": score,
                "suggestion": v.get("solution") or "",
            }
        )

    history.sort(key=lambda r: r["score"], reverse=True)
    knowledge.sort(key=lambda r: r["score"], reverse=True)
    return {"history": history, "knowledge": knowledge}


def main():
    request = json.load(open(sys.argv[1], encoding="utf-8"))
    results = []
    for item in request.get("queries", []):
        try:
            payload = search_one(
                item["query"], int(request.get("top", 5)),
                float(request.get("min_relevance", 0.75)),
            )
            payload["id"] = item.get("id")
            payload["error"] = None
        except Exception as exc:
            payload = {
                "id": item.get("id"), "history": [], "knowledge": [],
                "error": str(exc),
            }
        results.append(payload)
    sys.stdout.write("\n===RESULT_JSON===\n")
    json.dump({"results": results}, sys.stdout, ensure_ascii=False)


main()
'''

# 宿主机与容器的 bind mount 对应路径（RUNBOOK：/opt/redmine-assist/data ↔ /app/data）
REMOTE_HOST_DATA_DIR = "/opt/redmine-assist/data"
REMOTE_CTR_DATA_DIR = "/app/data"


def _load_similar_assist(repo_path: str):
    root = Path(repo_path).resolve()
    if not (root / "src" / "db_client.py").exists():
        raise FileNotFoundError(f"redmine-similar-assist not found: {root}")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from src.db_client import RedmineDB
    from src.embedder import Embedder
    from src.llm_judge import judge, judge_docs
    from src.vector_store import get_doc_store, get_vector_store

    return RedmineDB, Embedder, judge, judge_docs, get_vector_store, get_doc_store


class SimilarAssistBridge:
    def __init__(self, repo_path: str = r"D:\git\redmine-similar-assist") -> None:
        self.repo_path = str(Path(repo_path).resolve())
        (
            self.RedmineDB,
            self.Embedder,
            self.judge,
            self.judge_docs,
            self.get_vector_store,
            self.get_doc_store,
        ) = _load_similar_assist(repo_path)

    def list_recent_security_issues(
        self, days: int = 365, tracker_id: int = 26
    ) -> list[dict]:
        """Return security issues created during the requested lookback window."""
        since = dt.datetime.now() - dt.timedelta(days=days)
        db = self.RedmineDB()
        try:
            with db._conn() as (_, cur):
                cur.execute(
                    """SELECT id, project_id, tracker_id, status_id, subject,
                              description, created_on, updated_on, closed_on
                         FROM issues
                        WHERE tracker_id = %s
                          AND created_on >= %s
                     ORDER BY created_on DESC, id DESC""",
                    (tracker_id, since),
                )
                return list(cur.fetchall())
        except Exception as db_error:
            from src.redmine_client import RedmineClient

            client = RedmineClient()
            offset = 0
            rows = []
            while True:
                data = client._get(
                    "/issues.json",
                    {
                        "tracker_id": tracker_id,
                        "status_id": "*",
                        "created_on": f">={since:%Y-%m-%d}",
                        "sort": "created_on:desc,id:desc",
                        "limit": 100,
                        "offset": offset,
                    },
                )
                batch = data.get("issues") or []
                rows.extend(batch)
                offset += len(batch)
                if not batch or offset >= int(data.get("total_count") or 0):
                    break
            for row in rows:
                row["_source"] = "redmine_rest"
                row["_db_fallback_reason"] = str(db_error)
            return rows

    def list_attachments(self, issue_ids: Iterable[int]) -> list[dict]:
        ids = [int(x) for x in issue_ids]
        if not ids:
            return []
        db = self.RedmineDB()
        placeholders = ",".join("%s" for _ in ids)
        try:
            with db._conn() as (_, cur):
                cur.execute(
                    f"""SELECT id, container_id AS issue_id, filename, disk_filename,
                               disk_directory, content_type, filesize, created_on
                          FROM attachments
                         WHERE container_type = 'Issue'
                           AND container_id IN ({placeholders})
                      ORDER BY container_id, id""",
                    tuple(ids),
                )
                return list(cur.fetchall())
        except Exception:
            from src.redmine_client import RedmineClient

            attachments = []

            def fetch_one(issue_id: int) -> tuple[int, list[dict]]:
                client = RedmineClient()
                issue = client.get_issue(issue_id, include="attachments")
                return issue_id, issue.get("attachments") or []

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(fetch_one, issue_id): issue_id for issue_id in ids}
                for future in as_completed(futures):
                    issue_id = futures[future]
                    try:
                        _, issue_attachments = future.result()
                    except Exception as exc:
                        attachments.append(
                            {
                                "issue_id": issue_id,
                                "_source": "redmine_rest",
                                "_metadata_error": str(exc),
                            }
                        )
                        continue
                    for attachment in issue_attachments:
                        item = dict(attachment)
                        item["issue_id"] = issue_id
                        item["_source"] = "redmine_rest"
                        attachments.append(item)
            return attachments

    def _load_remote_config(self) -> dict:
        """读取 redmine-similar-assist config.yaml 的可选 bridge_remote 段，缺省启用远端。"""
        merged = dict(REMOTE_DEFAULTS)
        try:
            import yaml

            cfg_path = Path(self.repo_path) / "config.yaml"
            data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            section = data.get("bridge_remote") or {}
            if isinstance(section, dict):
                merged.update(section)
        except Exception:
            pass
        return merged

    def search_internal_batch(
        self,
        items: list[dict],
        top: int = 5,
        min_relevance: float = 0.75,
    ) -> dict:
        """批量内部检索。items: [{"id": key, "query": str}]。

        优先走远端（demo.egova.com.cn 容器内全量库：~19 万案件 + ~4900 篇知识库）；
        远端失败时回退本地库并在 stderr 明确告警（本地库不完整）。
        返回 {id: {"history": [...], "knowledge": [...]}}。
        """
        remote_cfg = self._load_remote_config()
        if remote_cfg.get("enabled"):
            try:
                return self._search_remote_batch(items, top, min_relevance, remote_cfg)
            except Exception as exc:
                print(
                    f"[bridge] 远端检索失败({exc})，回退本地库——注意本地库可能不完整",
                    file=sys.stderr,
                )
        out: dict = {}
        for item in items:
            result = self.search_internal(item["query"], top=top, min_relevance=min_relevance)
            out[item["id"]] = {"history": result["history"], "knowledge": result["knowledge"]}
        return out

    def _search_remote_batch(
        self,
        items: list[dict],
        top: int,
        min_relevance: float,
        remote_cfg: dict,
    ) -> dict:
        host = str(remote_cfg["ssh_host"])
        container = str(remote_cfg["container"])

        def ssh_run(command: str, input_bytes: bytes | None = None,
                    timeout_s: int = 120) -> subprocess.CompletedProcess:
            return subprocess.run(
                ["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes", host, command],
                input=input_bytes, capture_output=True, timeout=timeout_s,
            )

        # 1) 上传 runner 与请求（Windows OpenSSH 对 docker exec -i 的 stdin 转发不可靠，
        #    统一走宿主机 bind mount 文件，容器内重定向读取）
        stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S%f")
        host_runner = f"{REMOTE_HOST_DATA_DIR}/.rsa_runner_{stamp}.py"
        host_request = f"{REMOTE_HOST_DATA_DIR}/.rsa_request_{stamp}.json"
        ctr_runner = f"{REMOTE_CTR_DATA_DIR}/.rsa_runner_{stamp}.py"
        ctr_request = f"{REMOTE_CTR_DATA_DIR}/.rsa_request_{stamp}.json"

        payload = json.dumps(
            {
                "queries": [
                    {"id": item["id"], "query": item["query"]} for item in items
                ],
                "top": top,
                "min_relevance": min_relevance,
            },
            ensure_ascii=False,
        ).encode("utf-8")

        up1 = ssh_run(f"cat > {host_runner}", _REMOTE_RUNNER.encode("utf-8"))
        if up1.returncode != 0:
            raise RuntimeError(f"upload runner failed: {up1.stderr.decode('utf-8', 'replace')[:300]}")
        up2 = ssh_run(f"cat > {host_request}", payload)
        if up2.returncode != 0:
            raise RuntimeError(f"upload request failed: {up2.stderr.decode('utf-8', 'replace')[:300]}")

        try:
            proc = ssh_run(
                f"docker exec {container} python {ctr_runner} {ctr_request}",
                timeout_s=2400,
            )
        finally:
            ssh_run(f"rm -f {host_runner} {host_request}", timeout_s=30)

        stdout = proc.stdout.decode("utf-8", errors="replace")
        idx = stdout.rfind(RESULT_MARKER)
        if proc.returncode != 0 or idx < 0:
            raise RuntimeError(
                f"rc={proc.returncode} stderr={proc.stderr.decode('utf-8', 'replace')[:400]}"
            )
        data = json.loads(stdout[idx + len(RESULT_MARKER):].strip())
        out: dict = {}
        for row in data.get("results", []):
            out[row.get("id")] = {
                "history": row.get("history") or [],
                "knowledge": row.get("knowledge") or [],
                "_error": row.get("error"),
            }
        return out

    def search_internal(
        self, query: str, top: int = 5, min_relevance: float = 0.75
    ) -> dict:
        """Search historical issues and DingTalk knowledge documents."""
        embedding = self.Embedder().embed([query])[0]

        issue_candidates = self.get_vector_store().knn(embedding, top=top)
        issue_verdicts = self.judge(
            query,
            [
                {
                    "issue_id": row["issue_id"],
                    "subject": row.get("subject") or "",
                    "resolution": row.get("resolution") or "",
                }
                for row in issue_candidates
            ],
        )
        issues_by_id = {row["issue_id"]: row for row in issue_candidates}
        history = []
        for verdict in issue_verdicts:
            if not verdict.get("related"):
                continue
            source = issues_by_id.get(int(verdict.get("issue_id", 0)))
            if not source:
                continue
            score = float(verdict.get("score", source.get("cosine", 0)))
            if score < min_relevance:
                continue
            history.append(
                {
                    "type": "redmine_history",
                    "issue_id": source["issue_id"],
                    "title": source.get("subject") or "",
                    "score": score,
                    "suggestion": verdict.get("solution") or "",
                }
            )

        doc_candidates = self.get_doc_store().knn(embedding, top=top)
        doc_verdicts = self.judge_docs(
            query,
            [
                {
                    "node_id": row["node_id"],
                    "title": row.get("title") or "",
                    "summary": row.get("summary") or "",
                }
                for row in doc_candidates
            ],
        )
        docs_by_id = {row["node_id"]: row for row in doc_candidates}
        knowledge = []
        for verdict in doc_verdicts:
            if not verdict.get("related"):
                continue
            source = docs_by_id.get(str(verdict.get("node_id") or ""))
            if not source:
                continue
            score = float(verdict.get("score", source.get("cosine", 0)))
            if score < min_relevance:
                continue
            knowledge.append(
                {
                    "type": "knowledge_base",
                    "node_id": source["node_id"],
                    "title": source.get("title") or "",
                    "url": source.get("url") or "",
                    "score": score,
                    "suggestion": verdict.get("solution") or "",
                }
            )

        history.sort(key=lambda row: row["score"], reverse=True)
        knowledge.sort(key=lambda row: row["score"], reverse=True)
        return {"history": history, "knowledge": knowledge}
