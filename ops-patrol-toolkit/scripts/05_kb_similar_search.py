#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05 历史相似案例检索：接入公司 redmine-assist MCP 公网端点。

检索范围：约 17 万条历史 Redmine 运维工单 + 4500 篇钉钉知识库文档，返回综合答案与案件/文档链接。
与 02 号 MySQL I/O 分诊形成闭环：02 产出 triage.json -> 本工具 from-triage 自动拼检索词查历史同类案例。

MCP 接入方式（Streamable HTTP，响应为 SSE 形态，纯标准库客户端，不引入 mcp sdk）：
  1. POST initialize（头 Accept: application/json, text/event-stream）-> 200，响应头取 mcp-session-id
  2. POST notifications/initialized（带 session 头）-> 202
  3. POST tools/call（带 session 头）-> SSE data 行里取 JSON-RPC result
工具：
  - zhengtong_query  入参 {"query": "..."}（服务端检索约 15 秒）
  - precheck         入参 {"description": "..."}（服务端检索约 45 秒）
  返回综合答案，输出结构为 {"result": string}
鉴权：HTTP 头 Authorization: Bearer <token>；token 只经环境变量 DEMO_EGOVA_MCP_TOKEN 注入，绝不落盘。
客户端超时默认 120s（服务端要跑检索，下限 90s）。

用法:
  python scripts/05_kb_similar_search.py query --text "症状描述" [--tool zhengtong_query|precheck] [--out work/kb/result.md]
  python scripts/05_kb_similar_search.py from-triage --triage work/io_triage/triage.json [--out work/kb/result.md]

token 获取：浏览器打开 https://demo.egova.com.cn/oauth/dingtalk/login 钉钉扫码换取 Session Token，
写入环境变量 DEMO_EGOVA_MCP_TOKEN 后重试。
"""

import argparse
import http.client
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import patrol_lib  # noqa: E402  # stdout/stderr reconfigure utf-8 + gap 信封设施
from patrol_lib import emit, load_config, read_json, stop, write_text  # noqa: E402

__version__ = "1.0.0"

MCP_PROTOCOL_VERSION = "2024-11-05"
CLIENT_INFO = {"name": "ops-patrol-toolkit-kb-search", "version": __version__}
TOKEN_HELP_URL = "https://demo.egova.com.cn/oauth/dingtalk/login"
KNOWN_TOOLS = ("zhengtong_query", "precheck")
TOOL_PARAM = {"zhengtong_query": "query", "precheck": "description"}
DEFAULT_TIMEOUT_S = 120
MIN_TIMEOUT_S = 90      # 服务端检索要跑 15-45s，真实端点的超时上限不应低于 90s
SQL_SNIPPET_MAX = 120   # 拼检索词时 top_sql 摘要截断长度
DEFAULT_OUT = "work/kb/result.md"

# 关键数字（带常见单位）提取，用于把 evidence 收敛成检索词里的数字证据
_NUM_TOKEN = re.compile(
    r"\d+(?:\.\d+)?\s*(?:%|MB/s|KB/s|GB/s|MB|GB|KB|TB|ms|iops|IOPS|次|行|条|个|倍)"
)
_WS = re.compile(r"\s+")


class McpClientError(Exception):
    """MCP 调用失败（网络/HTTP/超时/JSON-RPC error/答案为空），由上层转成 gap 停止。"""


# ---------------------------------------------------------------------------
# 文本辅助
# ---------------------------------------------------------------------------

def _flatten(text):
    """压平空白（换行/连续空格 -> 单空格），用于把多行内容放进单行检索词/表头。"""
    return _WS.sub(" ", str(text)).strip()


def _truncate(text, limit):
    s = _flatten(text)
    return s if len(s) <= limit else s[:limit] + "..."


def tool_arguments(tool, text):
    """按工具名把检索词放进约定入参键：zhengtong_query->query，precheck->description。"""
    key = TOOL_PARAM.get(tool)
    if key is None:
        stop("未知检索工具 %s，可选: %s" % (tool, "|".join(KNOWN_TOOLS)))
    return {key: text}


def _evidence_text(ev):
    """把 evidence 条目（字符串或字典）压成一段文本。"""
    if isinstance(ev, str):
        return ev
    if isinstance(ev, dict):
        for key in ("text", "detail", "desc", "description", "message", "reason"):
            value = ev.get(key)
            if isinstance(value, (str, int, float)) and str(value).strip():
                return str(value)
        metric = ev.get("metric") or ev.get("key") or ev.get("name")
        if metric:
            unit = ev.get("unit") or ""
            return "%s=%s%s" % (metric, ev.get("value", ev.get("val", "")), unit)
        return json.dumps(ev, ensure_ascii=False)
    return str(ev)


def _sql_text(row):
    """把 top_sql 条目（字符串或字典）压成 SQL 文本。"""
    if isinstance(row, str):
        return row
    if isinstance(row, dict):
        for key in ("sql", "digest_text", "digest", "sql_text", "query", "text", "sample"):
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return json.dumps(row, ensure_ascii=False)
    return str(row)


def _key_numbers(text, limit=4):
    """提取 evidence 文本里的关键数字（带常见单位），保持出现顺序去重。"""
    out = []
    for m in _NUM_TOKEN.finditer(str(text)):
        token = _flatten(m.group(0))
        if token and token not in out:
            out.append(token)
        if len(out) >= limit:
            break
    return out


def build_query_from_triage(triage):
    """从 02 号分诊 triage.json 拼检索词。

    规则：主因（candidates[0].name）+ 前 2 条 evidence 的关键数字（无数字则截断原文）
    + top_sql 第一条 SQL 摘要（截断），拼成一句具体的症状描述。
    """
    candidates = triage.get("candidates") or []
    if not candidates or not isinstance(candidates[0], dict):
        stop("triage.json 缺少可用的 candidates（首条根因缺失），请先跑 02 号分诊产出完整 triage.json")
    top = candidates[0]
    name = str(top.get("name") or top.get("cause") or top.get("root_cause") or "").strip()
    if not name:
        stop("triage.json 首条候选根因缺少 name 字段，无法确定主因")

    evidence_parts = []
    for ev in (top.get("evidence") or [])[:2]:
        text = _evidence_text(ev)
        numbers = _key_numbers(text)
        evidence_parts.append("、".join(numbers) if numbers else _truncate(text, 40))

    sql = ""
    top_sql = triage.get("top_sql") or []
    if top_sql:
        sql = _truncate(_sql_text(top_sql[0]), SQL_SNIPPET_MAX)

    parts = ["MySQL只读副本高I/O分诊：主因是「%s」" % name]
    if any(evidence_parts):
        parts.append("关键证据数字：%s" % "；".join(p for p in evidence_parts if p))
    if sql:
        parts.append("最重慢查询摘要：%s" % sql)
    parts.append("请检索历史相似运维工单与知识库文档，给出同类案例的根因确认与处理方案")
    return "；".join(parts) + "。"


# ---------------------------------------------------------------------------
# SSE / JSON-RPC 解析
# ---------------------------------------------------------------------------

def parse_sse(text):
    """把 SSE 文本解析为 [(event, data), ...]。

    遵循 SSE 规范：空行分隔事件；同一事件内多行 data 以 \\n 连接；
    event 字段缺省记为 message；冒号开头的注释行忽略；id/retry 等字段忽略。
    """
    events = []
    event = None
    data_lines = []
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        if not line.strip():
            if data_lines:
                events.append((event or "message", "\n".join(data_lines)))
            event, data_lines = None, []
            continue
        if line.startswith(":"):
            continue
        field, _, value = line.partition(":")
        if value.startswith(" "):
            value = value[1:]
        if field == "event":
            event = value
        elif field == "data":
            data_lines.append(value)
    if data_lines:
        events.append((event or "message", "\n".join(data_lines)))
    return events


def sse_json_payloads(sse_text):
    """从 SSE 文本提取全部 JSON 载荷。整体解析失败时退化为逐行解析（容忍一行一个 JSON）。"""
    payloads = []
    for _event, data in parse_sse(sse_text):
        try:
            payloads.append(json.loads(data))
            continue
        except json.JSONDecodeError:
            pass
        for ln in data.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                payloads.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    return payloads


def response_payloads(body):
    """MCP 响应体解析：SSE 形态优先（端点实测形态），纯 JSON 体兜底。"""
    body = (body or "").strip()
    if not body:
        return []
    if body.startswith("{") or body.startswith("["):
        try:
            return [json.loads(body)]
        except json.JSONDecodeError:
            pass
    return sse_json_payloads(body)


def extract_answer(result):
    """从 tools/call 的 result 提取答案文本。

    工具输出结构为 {"result": string}；同时兼容 structuredContent 与 content[].text 常见形态。
    """
    if isinstance(result, str):
        return result.strip()
    if not isinstance(result, dict):
        return str(result).strip() if result is not None else ""
    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        for key in ("result", "answer", "text"):
            value = structured.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    content = result.get("content")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        joined = "\n".join(p.strip() for p in parts if p and p.strip())
        if joined.strip():
            return joined.strip()
    for key in ("result", "answer", "text", "output"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


# ---------------------------------------------------------------------------
# MCP 客户端（三步调用，同一 mcp-session-id 贯穿）
# ---------------------------------------------------------------------------

def _post(url, token, session_id, payload, timeout_s):
    """POST 一条 JSON-RPC 消息，返回 (status, headers, body_text)；失败抛 McpClientError。"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer %s" % token,
        # 公司 WAF 拦截 Python-urllib 特征（WinError 10054），必须带浏览器 UA
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }
    if session_id:
        headers["mcp-session-id"] = session_id
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout_s)
    except socket.timeout:
        raise McpClientError(
            "请求超时（客户端等待上限 %ss）：MCP 服务端检索未在时限内返回，"
            "可调大 config/patrol/kb_search.json 的 timeout_s 后重试" % timeout_s
        )
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read(500).decode("utf-8", "replace").strip()
        except Exception:
            pass
        if e.code in (401, 403):
            raise McpClientError(
                "MCP 端点返回 HTTP %s：token 无效或已过期，请到 %s 重新扫码获取（%s）"
                % (e.code, TOKEN_HELP_URL, detail or e.reason)
            )
        raise McpClientError("MCP 端点返回 HTTP %s：%s" % (e.code, detail or e.reason))
    except (urllib.error.URLError, http.client.HTTPException, OSError) as e:
        raise McpClientError("网络错误，无法访问 MCP 端点 %s：%s" % (url, e))
    body = resp.read().decode("utf-8", "replace")
    return resp.status, resp.headers, body


def mcp_call_tool(mcp_url, token, tool_name, arguments, timeout_s=DEFAULT_TIMEOUT_S):
    """三步调用 MCP 工具（initialize -> notifications/initialized -> tools/call）。

    返回 (session_id, answer_text)。任一步失败抛 McpClientError，由上层转 gap 停止。
    """
    # 第 1 步：initialize，从响应头取 mcp-session-id
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": CLIENT_INFO,
        },
    }
    _status, headers, body = _post(mcp_url, token, None, init_payload, timeout_s)
    session_id = headers.get("mcp-session-id")
    if not session_id:
        raise McpClientError("MCP initialize 响应缺少 mcp-session-id 头，无法建立会话")
    for obj in response_payloads(body):
        if isinstance(obj, dict) and obj.get("error"):
            err = obj["error"]
            raise McpClientError(
                "MCP initialize 返回 JSON-RPC error：code=%s message=%s"
                % (err.get("code"), err.get("message"))
            )

    # 第 2 步：notifications/initialized（无 id 通知，服务端通常回 202）
    _post(
        mcp_url, token, session_id,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        timeout_s,
    )

    # 第 3 步：tools/call，从 SSE data 行取 JSON-RPC result
    call_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    _status, _headers, body = _post(mcp_url, token, session_id, call_payload, timeout_s)
    found_result = False
    answer = ""
    for obj in response_payloads(body):
        if not isinstance(obj, dict):
            continue
        if obj.get("error"):
            err = obj["error"]
            raise McpClientError(
                "MCP tools/call 返回 JSON-RPC error：code=%s message=%s"
                % (err.get("code"), err.get("message"))
            )
        if "result" not in obj:
            continue  # progress 等通知消息跳过
        if obj.get("id") not in (None, 2):
            continue
        found_result = True
        answer = extract_answer(obj["result"])
        if answer.strip():
            break
    if not found_result:
        raise McpClientError("MCP tools/call 响应（SSE）中未找到 JSON-RPC result")
    if not answer.strip():
        raise McpClientError("MCP 工具 %s 返回的答案为空，无法生成检索报告" % tool_name)
    return session_id, answer


# ---------------------------------------------------------------------------
# 运行入口
# ---------------------------------------------------------------------------

def resolve_out(out):
    """输出路径：相对路径一律相对 skill 根目录解析（与工具集输出契约一致）。"""
    p = Path(out)
    if not p.is_absolute():
        p = patrol_lib.ROOT / p
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def render_markdown(answer, tool, query, mcp_url):
    lines = [
        "# 历史相似案例检索结果",
        "",
        "**【待复核】** 本报告由 ops-patrol-toolkit 05 号子工具自动生成，未经人工复核不得外发。",
        "",
        "- 生成时间：%s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "- 检索工具：%s" % tool,
        "- 检索词：%s" % _flatten(query),
        "- 数据来源：redmine-assist MCP（历史 Redmine 运维工单 + 钉钉知识库文档）",
        "- 端点：%s" % mcp_url,
        "",
        "## 检索结论",
        "",
        answer.strip(),
        "",
        "---",
        "说明：以上结论由历史工单与知识库自动检索拼装，处理方案需人工确认并在测试环境验证后方可使用。",
    ]
    return "\n".join(lines) + "\n"


def run_query(text, tool, out, mcp_url, token, timeout_s):
    """按症状描述检索并落盘 markdown，打印成功信封。"""
    t0 = time.time()
    try:
        _session_id, answer = mcp_call_tool(
            mcp_url, token, tool, tool_arguments(tool, text), timeout_s
        )
    except McpClientError as e:
        stop(str(e))
    elapsed_s = round(time.time() - t0, 2)
    out_path = resolve_out(out)
    write_text(out_path, render_markdown(answer, tool, text, mcp_url))
    emit({
        "tool": tool,
        "elapsed_s": elapsed_s,
        "answer_len": len(answer),
        "output": str(out_path),
        "query": _flatten(text),
    })
    return out_path


def run_from_triage(triage_path, tool, out, mcp_url, token, timeout_s):
    """读 02 号分诊 triage.json，自动拼检索词后检索并落盘 markdown。"""
    triage = read_json(triage_path)  # 缺文件/坏 JSON 由 patrol_lib 统一 gap
    if not isinstance(triage, dict):
        stop("triage.json 结构不符合约定（应为对象，含 candidates/sql_evidence/top_sql/io），无法拼检索词")
    query = build_query_from_triage(triage)
    t0 = time.time()
    try:
        _session_id, answer = mcp_call_tool(
            mcp_url, token, tool, tool_arguments(tool, query), timeout_s
        )
    except McpClientError as e:
        stop(str(e))
    elapsed_s = round(time.time() - t0, 2)
    out_path = resolve_out(out)
    write_text(out_path, render_markdown(answer, tool, query, mcp_url))
    emit({
        "tool": tool,
        "elapsed_s": elapsed_s,
        "answer_len": len(answer),
        "output": str(out_path),
        "query": query,
    })
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="05_kb_similar_search.py",
        description="历史相似案例检索：接入 redmine-assist MCP，查历史 Redmine 运维工单与钉钉知识库文档",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_query = sub.add_parser("query", help="按症状描述检索历史相似案例")
    p_query.add_argument("--text", required=True, help="症状描述/检索词")
    p_query.add_argument("--tool", default=None, help="zhengtong_query（默认）或 precheck")
    p_query.add_argument("--out", default=None, help="输出 markdown 路径，默认 %s" % DEFAULT_OUT)

    p_triage = sub.add_parser("from-triage", help="读 02 号分诊 triage.json 自动拼检索词检索")
    p_triage.add_argument("--triage", required=True, help="02 号工具产出的 triage.json 路径")
    p_triage.add_argument("--tool", default=None, help="zhengtong_query（默认）或 precheck")
    p_triage.add_argument("--out", default=None, help="输出 markdown 路径，默认 %s" % DEFAULT_OUT)

    args = ap.parse_args(argv)

    cfg = load_config("kb_search")
    mcp_url = str(cfg.get("mcp_url") or "").strip()
    if not mcp_url:
        stop("配置 kb_search.json 缺少 mcp_url，请补齐后再用")

    tool = (getattr(args, "tool", None) or cfg.get("default_tool") or "zhengtong_query")
    if tool not in KNOWN_TOOLS:
        stop("未知检索工具 %s，可选: %s" % (tool, "|".join(KNOWN_TOOLS)))

    token_env_ref = str(cfg.get("token_env_ref") or "DEMO_EGOVA_MCP_TOKEN")
    token = os.environ.get(token_env_ref, "").strip()
    if not token:
        stop(
            "环境变量 %s 未设置，无法访问 MCP 端点。获取方式：浏览器打开 %s 钉钉扫码换取 Session Token，"
            "然后设置环境变量 %s 后重试（token 绝不写入任何文件）"
            % (token_env_ref, TOKEN_HELP_URL, token_env_ref)
        )

    try:
        timeout_s = int(cfg.get("timeout_s") or DEFAULT_TIMEOUT_S)
    except (TypeError, ValueError):
        timeout_s = DEFAULT_TIMEOUT_S
    if timeout_s < MIN_TIMEOUT_S:
        # 服务端检索要跑 15-45s，超时上限过低会必然失败，托底到 90s
        timeout_s = MIN_TIMEOUT_S

    out = getattr(args, "out", None) or DEFAULT_OUT

    if args.cmd == "query":
        text = (args.text or "").strip()
        if not text:
            stop("--text 检索词为空，请提供具体的症状描述（谁在什么场景看到什么异常）")
        run_query(text, tool, out, mcp_url, token, timeout_s)
    else:
        run_from_triage(args.triage, tool, out, mcp_url, token, timeout_s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
