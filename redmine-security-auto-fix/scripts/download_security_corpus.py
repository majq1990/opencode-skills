#!/usr/bin/env python3
"""Concurrently download one year of security attachments with resume support."""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from build_security_corpus import (
    download_attachment,
    hydrate_content_urls,
    load_download_credentials,
)
from similar_assist_bridge import SimilarAssistBridge


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--tracker-id", type=int, default=26)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output-dir", default=r"D:\opencode\_archive\security-corpus")
    parser.add_argument(
        "--similar-assist", default=r"D:\git\redmine-similar-assist"
    )
    parser.add_argument("--download-config", required=True)
    args = parser.parse_args()

    bridge = SimilarAssistBridge(args.similar_assist)
    issues = bridge.list_recent_security_issues(args.days, args.tracker_id)
    attachments = bridge.list_attachments(row["id"] for row in issues)
    base_url, api_key = load_download_credentials(args.download_config)
    attachments = hydrate_content_urls(base_url, api_key, attachments)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    def fetch(attachment: dict) -> dict:
        record = dict(attachment)
        if record.get("_metadata_error") or (
            record.get("_url_error") and not record.get("content_url")
        ):
            record["status"] = "metadata_error"
            return record
        try:
            path = download_attachment(base_url, api_key, record, output_dir)
            record["local_path"] = str(path)
            record["status"] = "downloaded"
        except Exception as exc:
            record["status"] = "download_error"
            record["download_error"] = str(exc)
        return record

    results = []
    completed = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(fetch, row): row for row in attachments}
        for future in as_completed(futures):
            results.append(future.result())
            completed += 1
            if completed % 20 == 0 or completed == len(attachments):
                print(f"download progress: {completed}/{len(attachments)}", flush=True)

    manifest = {
        "lookback_days": args.days,
        "tracker_id": args.tracker_id,
        "issue_count": len(issues),
        "attachment_count": len(attachments),
        "downloaded": sum(1 for row in results if row["status"] == "downloaded"),
        "failed": sum(1 for row in results if row["status"] != "downloaded"),
        "attachments": sorted(
            results, key=lambda row: (int(row.get("issue_id") or 0), int(row.get("id") or 0))
        ),
    }
    manifest_path = output_dir / "download-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {key: value for key, value in manifest.items() if key != "attachments"},
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
