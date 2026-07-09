#!/usr/bin/env python3
"""Validate that downloaded reports yield concrete vulnerability records."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from report_parser import parse_report

REPORT_EXTENSIONS = {
    ".docx",
    ".doc",
    ".pdf",
    ".xls",
    ".xlsx",
    ".csv",
    ".tsv",
    ".html",
    ".htm",
    ".json",
    ".txt",
    ".md",
    ".log",
    ".out",
    ".properties",
    ".zip",
    ".rar",
}

GENERIC_NAMES = {
    "漏洞名称",
    "问题名称",
    "风险名称",
    "标题",
    "name",
    "title",
    "漏洞详情",
    "漏洞列表",
}


def is_concrete_vulnerability(row: dict) -> bool:
    name = re.sub(r"\s+", " ", str(row.get("name") or "")).strip()
    if len(name) < 3 or name.lower() in GENERIC_NAMES:
        return False
    if re.fullmatch(r"[\d\W_]+", name):
        return False
    useful = " ".join(
        str(row.get(key) or "")
        for key in ("name", "description", "harm", "fix_suggestion", "cve", "cwe")
    )
    security_markers = (
        "漏洞",
        "注入",
        "跨站",
        "越权",
        "泄露",
        "弱口令",
        "未授权",
        "缺失",
        "不安全",
        "风险",
        "cve-",
        "cwe-",
        "xss",
        "csrf",
        "ssrf",
        "sql",
        "rce",
        "cors",
        "cookie",
        "密码",
        "硬编码",
        "敏感信息",
        "ip地址",
        "https",
        "tls",
    )
    return any(marker in useful.lower() for marker in security_markers)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus-dir", default=r"D:\opencode\_archive\security-corpus"
    )
    parser.add_argument("--sample-per-format", type=int, default=10)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=45)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    root = Path(args.corpus_dir)
    files = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.name not in ("inventory.json", "download-manifest.json")
        and path.suffix.lower() in REPORT_EXTENSIONS
    ]
    results = []
    examples = defaultdict(list)
    format_stats = defaultdict(Counter)

    worker = Path(__file__).with_name("parse_report_worker.py")

    def validate_one(path: Path) -> tuple[dict, list[dict]]:
        suffix = path.suffix.lower()
        record = {"file": str(path), "format": suffix.lstrip(".")}
        try:
            process = subprocess.run(
                [sys.executable, str(worker), str(path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=args.timeout_seconds,
            )
            if process.returncode != 0:
                raise RuntimeError(process.stderr.strip() or "parser worker failed")
            parsed = json.loads(process.stdout)
            concrete = [
                row for row in parsed.get("vulns", []) if is_concrete_vulnerability(row)
            ]
            record["parsed_count"] = parsed.get("total", 0)
            record["concrete_count"] = len(concrete)
            record["status"] = "valid" if concrete else "empty_or_nonconcrete"
            sample = concrete[:5]
        except subprocess.TimeoutExpired:
            record["status"] = "timeout"
            record["error"] = f"parser exceeded {args.timeout_seconds}s"
            sample = []
        except Exception as exc:
            record["status"] = "parse_error"
            record["error"] = str(exc)
            sample = []
        return record, sample

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(validate_one, path): path for path in files}
        for index, future in enumerate(as_completed(futures), 1):
            path = futures[future]
            record, sample = future.result()
            results.append(record)
            suffix = path.suffix.lower()
            format_stats[suffix][record["status"]] += 1
            if sample and len(examples[suffix]) < args.sample_per_format:
                examples[suffix].append(
                    {
                        "file": path.name,
                        "issue_id": path.parent.name,
                        "vulnerabilities": [
                            {
                                "name": row.get("name"),
                                "level": row.get("level"),
                                "fix_suggestion": (row.get("fix_suggestion") or "")[:300],
                            }
                            for row in sample
                        ],
                    }
                )
            if index % 20 == 0 or index == len(files):
                print(f"parse progress: {index}/{len(files)}", flush=True)

    report = {
        "corpus_dir": str(root),
        "files_checked": len(files),
        "valid_files": sum(1 for row in results if row["status"] == "valid"),
        "empty_or_nonconcrete_files": sum(
            1 for row in results if row["status"] == "empty_or_nonconcrete"
        ),
        "parse_error_files": sum(
            1 for row in results if row["status"] == "parse_error"
        ),
        "timeout_files": sum(1 for row in results if row["status"] == "timeout"),
        "concrete_vulnerability_count": sum(
            int(row.get("concrete_count") or 0) for row in results
        ),
        "format_stats": {
            key.lstrip("."): dict(value) for key, value in sorted(format_stats.items())
        },
        "examples": dict(examples),
        "files": results,
    }
    output = Path(args.output) if args.output else root / "extraction-validation.json"
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key not in ("files", "examples")},
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"Validation: {output}")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
