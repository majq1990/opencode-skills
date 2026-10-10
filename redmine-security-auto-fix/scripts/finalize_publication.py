#!/usr/bin/env python3
"""Record a verified DingTalk document into the result JSON.

发布即交付：文档发布成功、回读校验通过后，把真实链接写回结果 JSON 即完成。
不发任何群机器人通知（通知模块已按需求移除）；需要同步给谁，把文档链接
发给谁即可。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

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
    args = parser.parse_args()

    path = Path(args.result_json)
    result = json.loads(path.read_text(encoding="utf-8"))
    result["dingtalk_document"] = {
        "published": True,
        "node_id": args.node_id,
        "doc_url": args.doc_url,
        "parent_node_id": PARENT_NODE_ID,
        "parent_url": PARENT_URL,
    }
    result["notification"] = {
        "sent": False,
        "skipped": "群机器人通知模块已移除（2026-09-30），发布即交付",
    }
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"已记录发布: {args.doc_url}")


if __name__ == "__main__":
    main()
