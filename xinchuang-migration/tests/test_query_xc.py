# -*- coding: utf-8 -*-
"""query_xc 纯函数单测（endpoint 边界 / token 来源 / 无写路径无凭据字面量的回归护栏），不打网络。"""
import re
import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from query_xc import TOKEN_ENV, load_token, validate_endpoint  # noqa: E402

SRC = Path(__file__).resolve().parent.parent / "scripts" / "query_xc.py"


def _fake_gai(ip: str):
    def _gai(host, port, proto=None):
        return [(socket.AF_INET, socket.SOCK_STREAM, proto, "", (ip, port or 443))]
    return _gai


def test_validate_endpoint_rejects_plain_http():
    with pytest.raises(SystemExit) as ei:
        validate_endpoint("http://demo.egova.com.cn/redmine-assist/query")
    assert "https" in str(ei.value)


def test_validate_endpoint_rejects_foreign_host():
    with pytest.raises(SystemExit) as ei:
        validate_endpoint("https://evil.example.com/redmine-assist/query")
    assert "egova.com.cn" in str(ei.value)


def test_validate_endpoint_rejects_suffix_lookalike():
    # "notegova.com.cn" 不以 ".egova.com.cn" 结尾，必须拒
    with pytest.raises(SystemExit):
        validate_endpoint("https://notegova.com.cn/redmine-assist/query")


def test_validate_endpoint_rejects_private_ip(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _fake_gai("10.0.0.8"))
    with pytest.raises(SystemExit) as ei:
        validate_endpoint("https://demo.egova.com.cn/redmine-assist/query")
    assert "受限地址" in str(ei.value)


def test_validate_endpoint_rejects_loopback(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _fake_gai("127.0.0.1"))
    with pytest.raises(SystemExit):
        validate_endpoint("https://demo.egova.com.cn/redmine-assist/query")


def test_validate_endpoint_accepts_public_ip(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _fake_gai("47.93.233.85"))
    url = "https://demo.egova.com.cn/redmine-assist/query"
    assert validate_endpoint(url) == url


def test_load_token_from_env(monkeypatch):
    monkeypatch.setenv(TOKEN_ENV, "t-from-env")
    assert load_token() == "t-from-env"


def test_load_token_missing_exits_with_hint(monkeypatch):
    monkeypatch.delenv(TOKEN_ENV, raising=False)
    with pytest.raises(SystemExit) as ei:
        load_token()
    assert TOKEN_ENV in str(ei.value)


def test_no_write_mode_open_in_source():
    """回归护栏：脚本不得留下任何 CLI 可控的写文件路径（Mimosa 路径穿越口径）。"""
    hits = [
        (i, l) for i, l in enumerate(SRC.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"\bopen\s*\([^)]*,\s*[\"'](?:w|a|x|\+)[\"']", l)
    ]
    assert hits == [], f"发现写模式 open：{hits}"


def test_no_credential_literal_in_source():
    """回归护栏：源码不得出现 token/密码字面量。"""
    src = SRC.read_text(encoding="utf-8")
    assert "DEFAULT_TOKEN" not in src
    assert not re.search(r"(?i)(token|password|passwd|secret)\s*=\s*[\"'][^\"']{12,}[\"']", src)


def test_no_cli_token_or_out_options():
    """--token / --out 已移除：token 只走环境变量，落盘只走 stdout 重定向。"""
    src = SRC.read_text(encoding="utf-8")
    assert '"--token"' not in src
    assert '"--out"' not in src
    assert "makedirs" not in src
