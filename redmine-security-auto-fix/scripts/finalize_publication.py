#!/usr/bin/env python3
"""Record a verified DingTalk document and send the completion notification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from notify_dingtalk import build_markdown_message, send_dingtalk_message

PARENT_NODE_ID = "dQPGYqjpJYg0vw9osZbj1mpgWakx1Z5N"
PARENT_URL = (
    "https://alidocs.dingtalk.com/i/nodes/"
    "dQPGYqjpJYg0vw9osZbj1mpgWakx1Z5N"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_json")
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--doc-url", required=True)
    parser.add_argument("--similar-assist", default=r"D:\git\redmine-similar-assist")
    parser.add_argument("--redmine-url", default="https://faq.egova.com.cn:7787")
    args = parser.parse_args()

    path = Path(args.result_json)
    result = json.loads(path.read_text(encoding="utf-8"))
    issue_id = result["issue_id"]
    result["dingtalk_document"] = {
        "published": True,
        "node_id": args.node_id,
        "doc_url": args.doc_url,
        "parent_node_id": PARENT_NODE_ID,
        "parent_url": PARENT_URL,
    }

    sys.path.insert(0, args.similar_assist)
    from src.config import cfg

    notify_config = (cfg().get("notify") or {})
    webhook = notify_config.get("dingtalk_webhook")
    if not webhook:
        raise RuntimeError("notify.dingtalk_webhook is not configured")

    issue_url = f"{args.redmine_url.rstrip('/')}/issues/{issue_id}"
    response = send_dingtalk_message(
        webhook,
        notify_config.get("dingtalk_secret"),
        build_markdown_message(
            result,
            args.doc_url,
            issue_url,
            notify_config.get("dingtalk_keyword"),
            PARENT_URL,
        ),
    )
    if response.get("errcode") != 0:
        raise RuntimeError(f"DingTalk notification failed: {response}")

    result["notification"] = {
        "sent": True,
        "errcode": response.get("errcode"),
        "errmsg": response.get("errmsg", ""),
    }
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result["notification"], ensure_ascii=False))


if __name__ == "__main__":
    main()
