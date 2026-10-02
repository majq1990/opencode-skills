#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""05 历史相似案例检索测试（全离线：本地假 MCP 服务，端口由系统分配，绝不访问真实端点）。"""

import contextlib
import importlib.util
import io
import json
import os
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "patrol" / "kb_search"
TMP = ROOT / "work" / "test_tmp" / "kb_search"

sys.path.insert(0, str(SCRIPTS))

import patrol_lib  # noqa: E402

# 模块名以数字开头，不能常规 import，用 importlib 按路径加载
_spec = importlib.util.spec_from_file_location(
    "kb_search_05", SCRIPTS / "05_kb_similar_search.py"
)
mod = importlib.util.module_from_spec(_spec)
sys.modules["kb_search_05"] = mod
_spec.loader.exec_module(mod)


def sse_text(payloads, event="message"):
    """把 JSON 对象列表构造成 SSE 文本（每对象一个 event）。"""
    chunks = []
    for p in payloads:
        chunks.append("event: %s\ndata: %s\n\n" % (event, json.dumps(p, ensure_ascii=False)))
    return "".join(chunks)


FAKE_ANSWER = (
    "历史相似案例：案件 #10233（2025-03，某市平台只读副本 I/O 打满，定位为慢查询回表放大），"
    "处理方案：为 t_order_detail.detail_blob 拆表并增加覆盖索引；"
    "参考文档：钉钉知识库《只读副本高 I/O 排查手册》。"
)


def default_tools_call_sse():
    """默认 tools/call 响应：先一条 progress 通知 event，再一条把 JSON 拆成两个 data 行的最终响应。"""
    obj = {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "content": [{"type": "text", "text": FAKE_ANSWER}],
            "structuredContent": {"result": FAKE_ANSWER},
        },
    }
    data = json.dumps(obj, ensure_ascii=False)
    # 在 JSON 允许空白的位置（顶层 "result": 之后）拆成两个 data 行，客户端按 SSE 规范用 \n 连接还原
    cut = data.index('"result"') + len('"result":')
    progress = sse_text([{
        "jsonrpc": "2.0",
        "method": "notifications/progress",
        "params": {"progressToken": 2, "progress": 1},
    }])
    multi = "event: message\ndata: %s\ndata: %s\n\n" % (data[:cut], data[cut:])
    return progress + multi


class FakeMcp:
    """本地假 redmine-assist MCP 服务（绑定 127.0.0.1:0，端口由系统分配，避免并行冲突）。"""

    def __init__(self, tools_call_sse=None, delay=0.0, require_session=True,
                 session_id="sess-fake-123"):
        self.requests = []
        self.tools_call_sse = tools_call_sse
        self.delay = delay
        self.require_session = require_session
        self.session_id = session_id
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _sse(self, status, text, extra=None):
                payload = text.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "text/event-stream")
                for k, v in (extra or {}).items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b""
                try:
                    body = json.loads(raw.decode("utf-8")) if raw else {}
                except json.JSONDecodeError:
                    body = {}
                outer.requests.append({
                    "path": self.path,
                    "headers": {k.lower(): v for k, v in self.headers.items()},
                    "body": body,
                })
                if outer.delay:
                    time.sleep(outer.delay)
                method = body.get("method") if isinstance(body, dict) else None
                if method == "initialize":
                    result = {
                        "jsonrpc": "2.0",
                        "id": body.get("id", 1),
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "serverInfo": {"name": "fake-redmine-assist", "version": "0.0.1"},
                        },
                    }
                    self._sse(200, sse_text([result]), {"mcp-session-id": outer.session_id})
                elif method == "notifications/initialized":
                    self.send_response(202)
                    self.send_header("Content-Type", "text/plain")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                elif method == "tools/call":
                    if outer.require_session and not self.headers.get("mcp-session-id"):
                        self.send_response(400)
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return
                    self._sse(200, outer.tools_call_sse or default_tools_call_sse())
                else:
                    self.send_response(404)
                    self.send_header("Content-Length", "0")
                    self.end_headers()

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = "http://127.0.0.1:%d/redmine-assist/mcp" % self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def _last_envelope(buf):
    lines = [ln for ln in buf.getvalue().strip().splitlines() if ln.strip()]
    return json.loads(lines[-1])


def _run_capture(fn, *args):
    """运行目标函数并捕获 stdout，返回信封（stdout 最后一行 JSON）。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args)
    return _last_envelope(buf)


class TestSseParsing(unittest.TestCase):
    """SSE 解析：多 event / 多 data 行 / 注释与未知字段。"""

    def test_multi_events_and_multi_data_lines(self):
        sse = (
            ": keep-alive\n"
            "retry: 3000\n"
            "event: message\n"
            'data: {"a": 1}\n'
            "\n"
            "event: progress\n"
            "data: line-one\n"
            "data: line-two\n"
            "\n"
            "event: message\n"
            'data: {"jsonrpc": "2.0", "id": 2,\n'
            'data: "result": {"ok": true}}\n'
            "\n"
            "data: 42\n"
            "\n"
        )
        events = mod.parse_sse(sse)
        self.assertEqual(events[0], ("message", '{"a": 1}'))
        self.assertEqual(events[1], ("progress", "line-one\nline-two"))
        self.assertEqual(events[2][0], "message")
        # 多 data 行按 SSE 规范以 \n 连接后仍是合法 JSON
        self.assertEqual(json.loads(events[2][1]),
                         {"jsonrpc": "2.0", "id": 2, "result": {"ok": True}})
        self.assertEqual(events[3], ("message", "42"))

        payloads = mod.sse_json_payloads(sse)
        self.assertEqual(payloads[0], {"a": 1})
        self.assertEqual(payloads[1], {"jsonrpc": "2.0", "id": 2, "result": {"ok": True}})
        self.assertIn(42, payloads)

    def test_response_payloads_plain_json_fallback(self):
        self.assertEqual(
            mod.response_payloads('{"jsonrpc": "2.0", "id": 2, "result": {}}'),
            [{"jsonrpc": "2.0", "id": 2, "result": {}}],
        )
        self.assertEqual(mod.response_payloads("  "), [])
        # SSE 形态优先
        self.assertEqual(mod.response_payloads("event: message\ndata: {\"a\": 2}\n\n"),
                         [{"a": 2}])


class TestEndToEnd(unittest.TestCase):
    """本地假 MCP 端到端：三轮请求顺序、session 头传递、answer 落盘。"""

    def setUp(self):
        TMP.mkdir(parents=True, exist_ok=True)

    def test_query_end_to_end_fake_mcp(self):
        fake = FakeMcp()
        self.addCleanup(fake.stop)
        out = TMP / ("query_%d.md" % time.time_ns())
        text = "只读副本 util 99%，慢查询暴增，怀疑回表放大"
        envelope = _run_capture(
            mod.run_query, text, "zhengtong_query", str(out), fake.url, "fake-token", 30
        )

        # 信封
        self.assertTrue(envelope["ok"])
        self.assertEqual(envelope["tool"], "zhengtong_query")
        self.assertGreaterEqual(envelope["elapsed_s"], 0)
        self.assertEqual(envelope["answer_len"], len(FAKE_ANSWER))
        self.assertEqual(envelope["query"], text)
        out_path = Path(envelope["output"])
        self.assertTrue(out_path.is_file())

        # 三轮请求顺序：initialize -> notifications/initialized -> tools/call
        self.assertEqual(
            [r["body"].get("method") for r in fake.requests],
            ["initialize", "notifications/initialized", "tools/call"],
        )
        # session 头：第一轮不带，后两轮带同一个 mcp-session-id
        self.assertNotIn("mcp-session-id", fake.requests[0]["headers"])
        self.assertEqual(fake.requests[1]["headers"].get("mcp-session-id"), "sess-fake-123")
        self.assertEqual(fake.requests[2]["headers"].get("mcp-session-id"), "sess-fake-123")
        for r in fake.requests:
            self.assertEqual(r["headers"].get("authorization"), "Bearer fake-token")
            self.assertEqual(r["headers"].get("accept"), "application/json, text/event-stream")
        init = fake.requests[0]["body"]
        self.assertEqual(init["jsonrpc"], "2.0")
        self.assertIn("protocolVersion", init["params"])
        self.assertIn("clientInfo", init["params"])
        # tools/call 入参
        call = fake.requests[2]["body"]
        self.assertEqual(call["params"]["name"], "zhengtong_query")
        self.assertEqual(call["params"]["arguments"], {"query": text})

        # answer 落盘为 markdown（头部含待复核/生成时间/工具名/检索词）
        md = out_path.read_text(encoding="utf-8")
        self.assertIn("**【待复核】**", md)
        self.assertIn("生成时间", md)
        self.assertIn("检索工具：zhengtong_query", md)
        self.assertIn("检索词：%s" % text, md)
        self.assertIn("## 检索结论", md)
        self.assertIn(FAKE_ANSWER, md)

    def test_precheck_uses_description_param(self):
        fake = FakeMcp()
        self.addCleanup(fake.stop)
        out = TMP / ("precheck_%d.md" % time.time_ns())
        _run_capture(
            mod.run_query, "预检：新上线采集服务", "precheck", str(out), fake.url, "fake-token", 30
        )
        call = fake.requests[2]["body"]
        self.assertEqual(call["params"]["name"], "precheck")
        self.assertEqual(call["params"]["arguments"], {"description": "预检：新上线采集服务"})


class TestFromTriage(unittest.TestCase):
    """from-triage：检索词拼接 + 端到端 + 结构缺失 gap。"""

    def setUp(self):
        TMP.mkdir(parents=True, exist_ok=True)
        self.triage = json.loads((FIXTURES / "triage.json").read_text(encoding="utf-8"))

    def test_build_query_from_triage(self):
        q = mod.build_query_from_triage(self.triage)
        self.assertIn("慢查询回表放大导致读 I/O 放大", q)   # 主因 name
        self.assertIn("99.2%", q)                            # evidence[0] 关键数字
        self.assertIn("45.1ms", q)
        self.assertIn("1280000", q)                          # evidence[1] 关键数字
        self.assertIn("8.4", q)
        sql = self.triage["top_sql"][0]["sql"]
        self.assertIn(mod._truncate(sql, mod.SQL_SNIPPET_MAX), q)  # SQL 摘要（截断）
        self.assertIn("...", q)                              # 长 SQL 确认被截断
        self.assertTrue(q.endswith("。"))

    def test_from_triage_end_to_end(self):
        fake = FakeMcp()
        self.addCleanup(fake.stop)
        out = TMP / ("triage_%d.md" % time.time_ns())
        envelope = _run_capture(
            mod.run_from_triage, str(FIXTURES / "triage.json"),
            "zhengtong_query", str(out), fake.url, "fake-token", 30,
        )
        expected_query = mod.build_query_from_triage(self.triage)
        self.assertTrue(envelope["ok"])
        self.assertEqual(envelope["query"], expected_query)  # 信封多带 query 字段
        self.assertEqual(
            fake.requests[2]["body"]["params"]["arguments"], {"query": expected_query}
        )
        md = Path(envelope["output"]).read_text(encoding="utf-8")
        self.assertIn("检索词：%s" % expected_query, md)
        self.assertIn(FAKE_ANSWER, md)

    def test_from_triage_missing_candidates_gap(self):
        fake = FakeMcp()
        self.addCleanup(fake.stop)
        bad = TMP / ("bad_%d.json" % time.time_ns())
        bad.write_text(json.dumps({"io": {"util_pct": 99.0}}, ensure_ascii=False), encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                mod.run_from_triage(
                    str(bad), "zhengtong_query", str(TMP / "x.md"), fake.url, "fake-token", 30
                )
        self.assertEqual(cm.exception.code, 2)
        payload = _last_envelope(buf)
        self.assertFalse(payload["ok"])
        self.assertIn("candidates", payload["gap"])
        self.assertEqual(fake.requests, [])  # 拼不出检索词就不该发起网络调用


class TestGapStop(unittest.TestCase):
    """各类失败路径必须 gap 停止（退出码 2）。"""

    def setUp(self):
        TMP.mkdir(parents=True, exist_ok=True)

    def _expect_gap(self, fn, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                fn(*args)
        self.assertEqual(cm.exception.code, 2)
        return _last_envelope(buf)

    def test_token_missing_gap_contains_howto(self):
        env = dict(os.environ)
        env.pop("DEMO_EGOVA_MCP_TOKEN", None)
        with mock.patch.dict(os.environ, env, clear=True):
            payload = self._expect_gap(mod.main, ["query", "--text", "磁盘 IO 高"])
        self.assertFalse(payload["ok"])
        self.assertIn("DEMO_EGOVA_MCP_TOKEN", payload["gap"])
        self.assertIn("https://demo.egova.com.cn/oauth/dingtalk/login", payload["gap"])

    def test_jsonrpc_error_gap(self):
        err_sse = sse_text([{
            "jsonrpc": "2.0",
            "id": 2,
            "error": {"code": -32000, "message": "检索服务内部错误"},
        }])
        fake = FakeMcp(tools_call_sse=err_sse)
        self.addCleanup(fake.stop)
        payload = self._expect_gap(
            mod.run_query, "症状", "zhengtong_query",
            str(TMP / ("err_%d.md" % time.time_ns())), fake.url, "fake-token", 30,
        )
        self.assertFalse(payload["ok"])
        self.assertIn("JSON-RPC error", payload["gap"])
        self.assertIn("检索服务内部错误", payload["gap"])

    def test_empty_answer_gap(self):
        empty_sse = sse_text([{
            "jsonrpc": "2.0",
            "id": 2,
            "result": {"content": [{"type": "text", "text": "   "}]},
        }])
        fake = FakeMcp(tools_call_sse=empty_sse)
        self.addCleanup(fake.stop)
        payload = self._expect_gap(
            mod.run_query, "症状", "zhengtong_query",
            str(TMP / ("empty_%d.md" % time.time_ns())), fake.url, "fake-token", 30,
        )
        self.assertFalse(payload["ok"])
        self.assertIn("答案为空", payload["gap"])

    def test_timeout_gap(self):
        fake = FakeMcp(delay=1.5)
        self.addCleanup(fake.stop)
        t0 = time.time()
        payload = self._expect_gap(
            mod.run_query, "症状", "zhengtong_query",
            str(TMP / ("timeout_%d.md" % time.time_ns())), fake.url, "fake-token", 0.3,
        )
        self.assertFalse(payload["ok"])
        self.assertIn("超时", payload["gap"])
        self.assertLess(time.time() - t0, 5)  # 不能傻等到服务端返回


if __name__ == "__main__":
    unittest.main()
