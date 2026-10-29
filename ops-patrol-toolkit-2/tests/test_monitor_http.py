#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""monitor_http 共享安全闸/HTTP 客户端测试（全部离线，本地 http.server 模拟）。"""

import http.server
import json
import sys
import threading
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import monitor_http  # noqa: E402
from patrol_lib import WORK_DIR  # noqa: E402

TMP = WORK_DIR / "test_tmp" / "monitor_http"
TMP.mkdir(parents=True, exist_ok=True)


class _EchoHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/json":
            body = json.dumps({"ok": True, "echo_ua": self.headers.get("User-Agent", "")}).encode("utf-8")
            self.send_response(200)
        elif self.path == "/notjson":
            body = b"<html>hello</html>"
            self.send_response(200)
        else:
            body = b"not found"
            self.send_response(404)
        self.send_header("Content-Type", "application/json" if "json" in self.path else "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        payload = json.loads(self.rfile.read(n) or b"{}")
        body = json.dumps({"received": payload}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class TestGuardUrl(unittest.TestCase):
    def test_scheme_whitelist(self):
        with self.assertRaises(monitor_http.MonitorHttpError) as cm:
            monitor_http.guard_url("ftp://example.com/x")
        self.assertEqual(cm.exception.kind, "scheme")
        with self.assertRaises(monitor_http.MonitorHttpError) as cm:
            monitor_http.guard_url("file:///etc/passwd")
        self.assertEqual(cm.exception.kind, "scheme")

    def test_userinfo_rejected(self):
        with self.assertRaises(monitor_http.MonitorHttpError) as cm:
            monitor_http.guard_url("http://user:pass@example.com/api")
        self.assertEqual(cm.exception.kind, "userinfo")

    def test_public_host_allowed_by_default(self):
        # example.com 为 IANA 保留域、公网可解析；本用例仅验证默认放行公网主机
        scheme, host, port = monitor_http.guard_url("https://example.com/api/v1")
        self.assertEqual((scheme, host), ("https", "example.com"))

    def test_loopback_blocked_by_default(self):
        for u in ("http://127.0.0.1:9090/api", "http://localhost:3000/x"):
            with self.assertRaises(monitor_http.MonitorHttpError) as cm:
                monitor_http.guard_url(u)
            self.assertEqual(cm.exception.kind, "blocked_local")

    def test_loopback_allowed_with_flag(self):
        scheme, host, port = monitor_http.guard_url("http://127.0.0.1:9090/api", allow_local=True)
        self.assertEqual(host, "127.0.0.1")

    def test_metadata_always_blocked(self):
        for allow in (False, True):
            with self.assertRaises(monitor_http.MonitorHttpError) as cm:
                monitor_http.guard_url("http://169.254.169.254/latest/meta-data", allow_local=True)
            self.assertEqual(cm.exception.kind, "blocked_local")

    def test_private_blocked_by_default_allowed_with_flag(self):
        with self.assertRaises(monitor_http.MonitorHttpError) as cm:
            monitor_http.guard_url("http://10.20.30.40:10050/zabbix")
        self.assertEqual(cm.exception.kind, "blocked_private")
        scheme, host, port = monitor_http.guard_url("http://10.20.30.40:10050/zabbix", allow_private=True)
        self.assertEqual(host, "10.20.30.40")
        # 192.168 段同理
        monitor_http.guard_url("http://192.168.1.5/api", allow_private=True)

    def test_unresolvable_host(self):
        with self.assertRaises(monitor_http.MonitorHttpError) as cm:
            monitor_http.guard_url("http://no-such-host.invalid/api")
        self.assertEqual(cm.exception.kind, "url")


class TestRequestJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _EchoHandler)
        cls.port = cls.httpd.server_address[1]
        cls.base = "http://127.0.0.1:%d" % cls.port
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_get_json_with_ua(self):
        status, obj = monitor_http.http_get_json(
            self.base + "/json", allow_local=True)
        self.assertEqual(status, 200)
        self.assertTrue(obj["ok"])
        self.assertIn("Mozilla", obj["echo_ua"])  # WAF 兼容 UA 已内置

    def test_guard_blocks_local_without_flag(self):
        with self.assertRaises(monitor_http.MonitorHttpError) as cm:
            monitor_http.http_get_json(self.base + "/json")
        self.assertEqual(cm.exception.kind, "blocked_local")

    def test_post_json_roundtrip(self):
        status, obj = monitor_http.http_post_json(
            self.base + "/graphql", {"query": "alarms"}, allow_local=True)
        self.assertEqual(status, 200)
        self.assertEqual(obj["received"], {"query": "alarms"})

    def test_http_error_kind(self):
        with self.assertRaises(monitor_http.MonitorHttpError) as cm:
            monitor_http.http_get_json(self.base + "/missing", allow_local=True)
        self.assertEqual(cm.exception.kind, "http")
        self.assertIn("404", cm.exception.message)

    def test_not_json_kind(self):
        with self.assertRaises(monitor_http.MonitorHttpError) as cm:
            monitor_http.http_get_json(self.base + "/notjson", allow_local=True)
        self.assertEqual(cm.exception.kind, "not_json")

    def test_token_header(self):
        # token 传入不报错即可（模拟服务不校验头），重点是不抛 guard 异常
        status, _ = monitor_http.http_get_json(
            self.base + "/json", allow_local=True, token="dummy")
        self.assertEqual(status, 200)


class TestLoadMonitorConfig(unittest.TestCase):
    def test_load_group_and_token_env(self):
        import os
        p = TMP / "mon.json"
        p.write_text(json.dumps({"zabbix": {"url": "http://10.0.0.1/api", "token_env_ref": "T_REF_X"}}),
                     encoding="utf-8")
        os.environ["T_REF_X"] = "tok123"
        g = monitor_http.load_monitor_config(str(p), "zabbix")
        self.assertEqual(g["_token"], "tok123")
        self.assertEqual(g["url"], "http://10.0.0.1/api")

    def test_missing_group_raises(self):
        p = TMP / "mon2.json"
        p.write_text("{}", encoding="utf-8")
        with self.assertRaises(KeyError):
            monitor_http.load_monitor_config(str(p), "nope")


if __name__ == "__main__":
    unittest.main()
