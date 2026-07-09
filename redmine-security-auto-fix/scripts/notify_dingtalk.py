#!/usr/bin/env python3
"""
钉钉机器人通知脚本
推送安全漏洞修复通知到钉钉机器人
"""

import argparse
import hashlib
import hmac
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from collections import Counter
from datetime import datetime


def sign_timestamp(secret, timestamp):
    """计算钉钉机器人加签"""
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()
    return urllib.parse.quote_plus(base64.b64encode(hmac_code).decode("utf-8"))


def build_markdown_message(
    vuln_data, doc_url, issue_url, keyword=None, parent_url=None
):
    """构建钉钉Markdown消息"""
    issue_id = vuln_data.get("issue_id", "unknown")
    stats = vuln_data.get("stats") or Counter(
        vuln.get("level", "medium") for vuln in vuln_data.get("vulns", [])
    )
    total = vuln_data.get("total", 0)
    keyword_line = f"**通知关键词**：{keyword}\n" if keyword else ""
    doc_line = f"\n**修复文档**：[查看文档]({doc_url})\n" if doc_url else ""
    parent_line = (
        f"\n**存放目录**：[项目案例]({parent_url})\n" if parent_url else ""
    )
    
    message = {
        "msgtype": "markdown",
        "markdown": {
            "title": "安全漏洞修复通知",
            "text": f"""## 安全漏洞修复通知

{keyword_line}
**案件ID**：{issue_id}
**案件链接**：[点击查看]({issue_url})

**漏洞统计**：共{total}个漏洞
- 严重：{stats.get('critical', 0)}个
- 高危：{stats.get('high', 0)}个
- 中危：{stats.get('medium', 0)}个
- 低危：{stats.get('low', 0)}个
{parent_line}
{doc_line}

请及时处理！"""
        }
    }
    
    return message


def send_dingtalk_message(webhook_url, secret, message):
    """发送钉钉消息"""
    timestamp = str(round(time.time() * 1000))
    
    if secret:
        sign = sign_timestamp(secret, timestamp)
        url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
    else:
        url = webhook_url
    
    data = json.dumps(message).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result
    except Exception as e:
        print(f"Error sending message: {e}", file=sys.stderr)
        return {"errcode": -1, "errmsg": str(e)}


def main():
    parser = argparse.ArgumentParser(description="推送钉钉机器人通知")
    parser.add_argument("vuln_json", help="漏洞解析结果JSON文件")
    parser.add_argument("--webhook", required=True, help="钉钉机器人Webhook地址")
    parser.add_argument("--secret", default=None, help="钉钉机器人加签密钥")
    parser.add_argument("--doc-url", default=None, help="真实的钉钉修复文档链接")
    parser.add_argument("--issue-url", default=None, help="Redmine案件链接")
    parser.add_argument("--keyword", default=None, help="机器人安全关键词")
    
    args = parser.parse_args()
    
    with open(args.vuln_json, "r", encoding="utf-8") as f:
        vuln_data = json.load(f)
    
    issue_id = vuln_data.get("issue_id", "unknown")
    if not args.issue_url:
        args.issue_url = f"https://faq.egova.com.cn:7787/issues/{issue_id}"
    
    message = build_markdown_message(
        vuln_data, args.doc_url, args.issue_url, args.keyword
    )
    
    result = send_dingtalk_message(args.webhook, args.secret, message)
    
    if result.get("errcode") == 0:
        print("Message sent successfully")
    else:
        print(f"Failed to send message: {result}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
