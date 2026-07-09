#!/usr/bin/env python3
"""Classify vulnerability remediation ownership by technical layer."""

from __future__ import annotations

import argparse
import json
import re
from typing import Any

OPS_PATTERNS = (
    (r"nginx|反向代理|网关|waf", "nginx", "服务器或网关配置"),
    (r"https|ssl|tls|hsts|加密连接", "tls", "传输层配置"),
    (r"响应头|cors|content-security-policy|x-frame|referrer-policy", "nginx", "HTTP安全头配置"),
    (r"tomcat|server\.xml|中间件版本|详细.{0,4}(?:报错|错误)信息|错误页面", "middleware", "中间件错误输出配置"),
)

DEV_PATTERNS = (
    (r"sql\s*注入|xss|跨站脚本|命令注入|代码执行|rce", "application_code", "应用代码漏洞"),
    (r"路径穿越|目录穿越|目录遍历|任意文件读取|文件读取", "application_code", "应用文件访问逻辑"),
    (r"越权|idor|未授权访问|权限绕过|鉴权", "application_code", "应用鉴权逻辑"),
    (r"敏感信息(?:泄漏|泄露)|密码回显|未脱敏", "application_code", "接口数据输出逻辑"),
    (r"业务逻辑|逻辑漏洞|空密码", "application_code", "应用业务逻辑"),
    (r"restful|csrf|删除接口", "application_code", "接口语义与安全校验"),
    (r"cookie|httponly|spring|application\.properties|web\.xml", "java_app", "Java应用配置"),
    (r"jquery|requirejs|javascript库|js库|前端框架", "frontend", "前端依赖或代码"),
)


def classify_vulnerability(vuln: dict[str, Any] | str) -> dict[str, str]:
    if isinstance(vuln, str):
        text = vuln
    else:
        text = " ".join(
            str(vuln.get(key) or "")
            for key in ("name", "description", "harm", "fix_suggestion")
        )
    text = text.lower()

    # Application-specific findings take precedence over generic words such as
    # "server" or "configuration" in report descriptions.
    for pattern, layer, reason in DEV_PATTERNS:
        if re.search(pattern, text, re.I):
            return {
                "owner": "dev",
                "owner_name": "研发中心",
                "layer": layer,
                "reason": reason,
            }
    for pattern, layer, reason in OPS_PATTERNS:
        if re.search(pattern, text, re.I):
            return {
                "owner": "ops",
                "owner_name": "工程中心",
                "layer": layer,
                "reason": reason,
            }
    return {
        "owner": "dev",
        "owner_name": "研发中心",
        "layer": "application_review",
        "reason": "未命中服务器配置规则，默认由研发确认应用实现",
    }


def classify_vulns(vulns: list[dict[str, Any]]) -> dict[str, list[dict]]:
    result = {"ops_fixes": [], "dev_fixes": []}
    for vuln in vulns:
        responsibility = classify_vulnerability(vuln)
        item = {**vuln, "responsibility": responsibility}
        result[
            "ops_fixes" if responsibility["owner"] == "ops" else "dev_fixes"
        ].append(item)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("vuln_json")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()
    with open(args.vuln_json, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    classified = classify_vulns(data.get("vulns", []))
    classified["issue_id"] = data.get("issue_id", "unknown")
    classified["stats"] = {
        "ops_fixes": len(classified["ops_fixes"]),
        "dev_fixes": len(classified["dev_fixes"]),
    }
    content = json.dumps(classified, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(content)
    else:
        print(content)


if __name__ == "__main__":
    main()
