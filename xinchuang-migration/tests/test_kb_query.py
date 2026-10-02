# -*- coding: utf-8 -*-
"""kb_query 纯函数单测（SSE 解析 / 会话头提取 / token 缺失报错），不打网络。"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from kb_query import extract_session_id, load_token, parse_sse, result_text  # noqa: E402


def _sse(payload: dict, ping_first: bool = True) -> str:
    body = ""
    if ping_first:
        body += ": ping - 2026-10-02T12:00:00\r\n\r\n"
    body += "event: message\r\n"
    body += "data: " + json.dumps(payload, ensure_ascii=False) + "\r\n\r\n"
    return body


def test_parse_sse_skips_ping_and_finds_id():
    rpc = _sse({"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "OK"}]}})
    obj = parse_sse(rpc, 3)
    assert obj is not None and result_text(obj) == "OK"


def test_parse_sse_no_match_returns_none():
    rpc = _sse({"jsonrpc": "2.0", "id": 99, "result": {}})
    assert parse_sse(rpc, 3) is None


def test_extract_session_id_case_insensitive():
    headers = b"HTTP/2 200\r\ncontent-type: text/event-stream\r\nMcp-Session-Id: abc123\r\n\r\n"
    assert extract_session_id(headers) == "abc123"
    assert extract_session_id(b"HTTP/2 200\r\n\r\n") == ""


def test_load_token_missing_exits_with_hint(tmp_path, monkeypatch):
    monkeypatch.delenv("REDMINE_ASSIST_TOKEN", raising=False)
    missing = tmp_path / "no-such-config.json"
    with pytest.raises(SystemExit) as ei:
        load_token(str(missing))
    assert "REDMINE_ASSIST_TOKEN" in str(ei.value)


def test_load_token_from_config(tmp_path, monkeypatch):
    monkeypatch.delenv("REDMINE_ASSIST_TOKEN", raising=False)
    cfg = tmp_path / "mcp.json"
    cfg.write_text(json.dumps({"endpoint": "https://demo.egova.com.cn/redmine-assist/mcp",
                               "auth": {"token": "t-abc"}}), encoding="utf-8")
    token, endpoint = load_token(str(cfg))
    assert token == "t-abc"
    assert endpoint.endswith("/redmine-assist/mcp")
