#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb_query.py — 信创知识库公网 MCP 直调（precheck / zhengtong_query）。

通道：https://demo.egova.com.cn/redmine-assist/mcp（JSON-RPC 2.0 streamable-http，SSE 响应）
鉴权：Bearer 会话 token，来自配置文件 auth.token 或环境变量 REDMINE_ASSIST_TOKEN。
     token 由 /oauth/dingtalk/login 钉钉扫码获得；401 = 过期，重新扫码更新配置文件，不得绕过鉴权。
兜底：MCP 不可用时按 SKILL.md"兜底策略优先级"降级（query_xc.py REST / similar_assist_bridge SSH）。

用法：
  python kb_query.py "<问题>"                          # zhengtong_query（默认）
  python kb_query.py "<业务描述>" --tool precheck      # 对接前置避坑
  python kb_query.py "<问题>" --config <path> --timeout 90
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_CONFIG = r"D:\opencode\config\redmine-assist-mcp.json"
DEFAULT_ENDPOINT = "https://demo.egova.com.cn/redmine-assist/mcp"
ALLOWED_HOST_SUFFIX = ".egova.com.cn"
TOOLS = ("zhengtong_query", "precheck")


def load_token(config_path: str | None) -> tuple[str, str]:
    """返回 (token, endpoint)。token 优先级：环境变量 > 配置文件。"""
    path = Path(config_path or os.environ.get("REDMINE_ASSIST_CONFIG") or DEFAULT_CONFIG)
    token = os.environ.get("REDMINE_ASSIST_TOKEN", "")
    endpoint = DEFAULT_ENDPOINT
    if path.exists():
        try:
            cfg = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"[kb] 配置文件解析失败 {path}: {exc}", file=sys.stderr)
            cfg = {}
        token = token or ((cfg.get("auth") or {}).get("token") or "")
        endpoint = cfg.get("endpoint") or endpoint
    if not token:
        raise SystemExit(
            "[kb] 未找到 token：请配置环境变量 REDMINE_ASSIST_TOKEN，"
            f"或在 {path} 的 auth.token 写入（/oauth/dingtalk/login 扫码获取）"
        )
    return token, endpoint


def validate_endpoint(url: str) -> str:
    """endpoint 边界校验：仅 https、仅公司域名、解析结果不得落入私网/环回/链路本地段。"""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise SystemExit(f"[kb] endpoint 必须是 https，拒绝：{url}")
    host = (parsed.hostname or "").lower()
    if not host.endswith(ALLOWED_HOST_SUFFIX):
        raise SystemExit(
            f"[kb] endpoint 主机不在允许范围（*{ALLOWED_HOST_SUFFIX}），拒绝：{host}"
        )
    try:
        infos = socket.getaddrinfo(host, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise SystemExit(f"[kb] 域名解析失败 {host}: {exc}")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_reserved or ip.is_multicast or ip.is_unspecified
        ):
            raise SystemExit(f"[kb] {host} 解析到受限地址 {ip}，拒绝请求")
    return url


def extract_session_id(raw_headers: bytes) -> str:
    """从响应头里取 Mcp-Session-Id（大小写不敏感）。"""
    for line in raw_headers.decode("utf-8", errors="replace").splitlines():
        if line.lower().startswith("mcp-session-id:"):
            return line.split(":", 1)[1].strip()
    return ""


def parse_sse(raw: str, expect_id) -> dict | None:
    """从 SSE 文本里取 id 匹配的 JSON-RPC 响应；跳过 ': ping' 注释与通知帧。"""
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload:
            continue
        try:
            obj = json.loads(payload)
        except ValueError:
            continue
        if str(obj.get("id", "")) == str(expect_id):
            return obj
    return None


def result_text(rpc: dict) -> str:
    if "error" in rpc:
        return f"[RPC错误] {json.dumps(rpc['error'], ensure_ascii=False)}"
    parts = [
        c.get("text", "")
        for c in (rpc.get("result") or {}).get("content", [])
        if isinstance(c, dict)
    ]
    return "\n".join(p for p in parts if p)


def call_tool(tool: str, text: str, token: str, endpoint: str, timeout: int) -> str:
    endpoint = validate_endpoint(endpoint)

    def post(payload: dict, session: str = "") -> tuple[bytes, bytes, int]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {token}",
        }
        if session:
            headers["Mcp-Session-Id"] = session
        req = urllib.request.Request(
            endpoint, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.headers.as_bytes(), resp.read(), resp.status
        except urllib.error.HTTPError as exc:
            return b"", (exc.read() or b""), exc.code

    # 1) initialize
    init_payload = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "xinchuang-migration-kb", "version": "2.0.0"},
        },
    }
    raw_h, raw_b, status = post(init_payload)
    if status == 401:
        raise SystemExit(
            "[kb] 401 token 无效或过期：到 https://demo.egova.com.cn/oauth/dingtalk/login "
            "钉钉扫码拿新 Session Token，更新 redmine-assist-mcp.json 的 auth.token（不要绕过鉴权）"
        )
    if status != 200:
        raise SystemExit(
            f"[kb] initialize 失败 HTTP {status}：{raw_b[:200]!r}。"
            "若非 401，可按 SKILL.md 降级用 query_xc.py REST 或 similar_assist_bridge.py SSH 通道"
        )
    init = parse_sse(raw_b.decode("utf-8", errors="replace"), 1)
    if init is None:
        raise SystemExit("[kb] initialize 响应里没有匹配的 data 帧，服务端协议可能变更")
    session = extract_session_id(raw_h)

    # 2) notifications/initialized
    post({"jsonrpc": "2.0", "method": "notifications/initialized"}, session)

    # 3) tools/call
    arg_key = "description" if tool == "precheck" else "query"
    call_payload = {
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": tool, "arguments": {arg_key: text}},
    }
    raw_h2, raw_b2, status = post(call_payload, session)
    if status != 200:
        raise SystemExit(f"[kb] tools/call 失败 HTTP {status}：{raw_b2[:200]!r}")
    rpc = parse_sse(raw_b2.decode("utf-8", errors="replace"), 2)
    if rpc is None:
        raise SystemExit("[kb] tools/call 响应里没有匹配的 data 帧")
    return result_text(rpc)


def bridge_hint() -> str:
    """SSH 兜底通道位置提示（不在此实现，避免复制凭证逻辑）。"""
    return ("[kb] 备用通道：D:/opencode/config/skills/redmine-security-auto-fix/scripts/"
            "similar_assist_bridge.py（SSH→demo 容器内 sqlite-vec KNN）")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="信创知识库公网 MCP 直调")
    parser.add_argument("query", help="问题（zhengtong_query）或业务描述（precheck）")
    parser.add_argument("--tool", default="zhengtong_query", choices=TOOLS)
    parser.add_argument("--config", default=None, help="redmine-assist-mcp.json 路径")
    parser.add_argument("--timeout", type=int, default=90, help="单请求超时秒数")
    args = parser.parse_args(argv)

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    token, endpoint = load_token(args.config)
    try:
        print(call_tool(args.tool, args.query, token, endpoint, args.timeout))
        return 0
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        print(bridge_hint(), file=sys.stderr)
        return 1
    except (urllib.error.URLError, OSError) as exc:
        print(f"[kb] 网络异常: {exc}", file=sys.stderr)
        print(bridge_hint(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
