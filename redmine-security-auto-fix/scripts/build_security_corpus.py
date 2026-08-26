#!/usr/bin/env python3
"""Download and inventory one year of security-case report attachments."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import urllib.request
import urllib.parse
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from pathlib import Path

from report_parser import parse_report
from similar_assist_bridge import SimilarAssistBridge


def load_download_credentials(config_path: str | None) -> tuple[str, str]:
    if config_path:
        import yaml

        config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        redmine = config["redmine"]
        return redmine["base_url"], redmine["api_key"]

    from src.config import cfg

    redmine = cfg()["redmine"]
    return redmine["base_url"], redmine["api_key"]


def download_attachment(
    base_url: str, api_key: str, attachment: dict, target_dir: Path
) -> Path:
    filename = attachment.get("filename") or f"attachment-{attachment['id']}"
    issue_dir = target_dir / str(attachment["issue_id"])
    issue_dir.mkdir(parents=True, exist_ok=True)
    target = issue_dir / f"{attachment['id']}_{filename}"
    if target.exists() and target.stat().st_size == int(attachment.get("filesize") or 0):
        return target
    url = attachment.get("content_url") or (
        f"{base_url.rstrip('/')}/attachments/download/{attachment['id']}/"
        f"{urllib.parse.quote(filename)}"
    )
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if curl:
        result = subprocess.run(
            [
                curl,
                "-k",
                "-L",
                "--fail",
                "--silent",
                "--show-error",
                "--retry",
                "2",
                "-H",
                f"X-Redmine-API-Key: {api_key}",
                "-o",
                str(target),
                url,
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode != 0:
            target.unlink(missing_ok=True)
            raise RuntimeError(
                f"curl download failed ({result.returncode}): {result.stderr.strip()}"
            )
        expected_size = int(attachment.get("filesize") or 0)
        actual_size = target.stat().st_size
        content_type = str(attachment.get("content_type") or "")
        tolerance = (
            max(1024, int(expected_size * 0.01))
            if content_type.startswith("text/")
            else 0
        )
        if expected_size and abs(actual_size - expected_size) > tolerance:
            target.unlink(missing_ok=True)
            raise RuntimeError(
                f"Attachment size mismatch: expected={expected_size}, "
                f"actual={actual_size}"
            )
        return target

    import requests

    first = requests.get(
        url,
        headers={"X-Redmine-API-Key": api_key},
        verify=False,
        allow_redirects=False,
        timeout=90,
    )
    if first.is_redirect or first.is_permanent_redirect:
        location = first.headers.get("Location")
        if not location:
            raise RuntimeError(f"Attachment redirect has no Location header: {url}")
        download_url = urllib.parse.urljoin(url, location)
        response = requests.get(download_url, verify=False, timeout=90)
    else:
        response = first
    response.raise_for_status()
    target.write_bytes(response.content)
    expected_size = int(attachment.get("filesize") or 0)
    actual_size = target.stat().st_size
    content_type = str(attachment.get("content_type") or "")
    tolerance = (
        max(1024, int(expected_size * 0.01))
        if content_type.startswith("text/")
        else 0
    )
    if expected_size and abs(actual_size - expected_size) > tolerance:
        target.unlink(missing_ok=True)
        raise RuntimeError(
            f"Attachment size mismatch: expected={expected_size}, "
            f"actual={actual_size}"
        )
    return target


def hydrate_content_urls(
    base_url: str, api_key: str, attachments: list[dict]
) -> list[dict]:
    by_issue: dict[int, list[dict]] = {}
    for attachment in attachments:
        if attachment.get("id") and attachment.get("issue_id"):
            by_issue.setdefault(int(attachment["issue_id"]), []).append(attachment)

    def fetch_issue(issue_id: int) -> tuple[int, list[dict]]:
        url = f"{base_url.rstrip('/')}/issues/{issue_id}.json?include=attachments"
        request = urllib.request.Request(url)
        request.add_header("X-Redmine-API-Key", api_key)
        with urllib.request.urlopen(request, timeout=60) as response:
            issue = json.loads(response.read().decode("utf-8"))["issue"]
        return issue_id, issue.get("attachments") or []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(fetch_issue, issue_id): issue_id for issue_id in by_issue
        }
        for future in as_completed(futures):
            issue_id = futures[future]
            try:
                _, remote_attachments = future.result()
            except Exception as exc:
                for attachment in by_issue[issue_id]:
                    attachment["_url_error"] = str(exc)
                continue
            remote_by_id = {int(row["id"]): row for row in remote_attachments}
            for attachment in by_issue[issue_id]:
                remote = remote_by_id.get(int(attachment["id"]))
                if remote:
                    attachment["content_url"] = remote.get("content_url")
    return attachments


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--tracker-id", type=int, default=26)
    parser.add_argument("--output-dir", default=r"D:\opencode\_archive\security-corpus")
    parser.add_argument(
        "--similar-assist", default=r"D:\git\redmine-similar-assist"
    )
    parser.add_argument(
        "--download-config",
        default=None,
        help="YAML containing redmine.base_url/api_key for attachment access",
    )
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()

    bridge = SimilarAssistBridge(args.similar_assist)
    issues = bridge.list_recent_security_issues(args.days, args.tracker_id)
    attachments = bridge.list_attachments(row["id"] for row in issues)

    redmine_base_url, redmine_api_key = load_download_credentials(
        args.download_config
    )
    if not args.inventory_only:
        attachments = hydrate_content_urls(
            redmine_base_url, redmine_api_key, attachments
        )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    format_counts = Counter()
    parse_failures = []

    for attachment in attachments:
        if attachment.get("_metadata_error"):
            records.append(attachment)
            continue
        suffix = Path(attachment.get("filename") or "").suffix.lower() or "(none)"
        format_counts[suffix] += 1
        record = dict(attachment)
        record["content_type"] = record.get("content_type") or mimetypes.guess_type(
            record.get("filename") or ""
        )[0]
        if not args.inventory_only:
            try:
                local_path = download_attachment(
                    redmine_base_url, redmine_api_key, attachment, output_dir
                )
                record["local_path"] = str(local_path)
                try:
                    parsed = parse_report(local_path)
                    record["parsed_vulnerabilities"] = parsed["total"]
                except Exception as exc:
                    record["parse_error"] = str(exc)
                    parse_failures.append(record)
            except Exception as exc:
                record["download_error"] = str(exc)
        records.append(record)

    inventory = {
        "lookback_days": args.days,
        "tracker_id": args.tracker_id,
        "issue_count": len(issues),
        "attachment_count": len(attachments),
        "formats": dict(format_counts),
        "download_failure_count": sum(
            1 for record in records if record.get("download_error")
        ),
        "parse_failure_count": len(parse_failures),
        "attachments": records,
    }
    inventory_path = output_dir / "inventory.json"
    inventory_path.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps({k: v for k, v in inventory.items() if k != "attachments"}, ensure_ascii=False, indent=2))
    print(f"Inventory: {inventory_path}")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()