#!/usr/bin/env python3
"""Bridge to redmine-similar-assist without copying its credentials."""

from __future__ import annotations

import datetime as dt
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable


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
