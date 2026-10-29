#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""08 Prometheus 告警拉取与离线分诊测试。

全离线：本地 http.server（绑定 127.0.0.1:0）假 /api/v1/alerts，返回 canned
{"status":"success","data":{"alerts":[...]}}（critical 实例告警 / warning 磁盘告警 /
info 无实例告警），另一路由返回 status:"error"；绝不访问真实端点。
fixture 配置 monitors_local.json 双开 allow_local_targets/allow_private_targets 且
enabled=true、url 尾部带斜杠（验证归一不出双斜杠），{PORT} 由测试运行时替换。

覆盖：alerts 端到端（url 尾斜杠归一、Bearer 头、severity 归一、id 构造、缺实例补
unknown、落盘结构与 token 不落盘）；status error -> gap；alerts 非列表 gap；
token 缺失 gap 且断言未发任何请求；enabled=false gap；0 条告警 ok:true；
triage 离线端到端（fixture alerts.json + 通用剧本库：剧本命中/排序/报告产出）；
缺 findings 键 gap；空 findings ok；归一/URL/剧本匹配/兜底工具单测。

临时产物只写 work/test_tmp/prometheus/（避免与其他并行 agent 撞名）。
unittest 风格，pytest 兼容。
"""

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

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "patrol" / "prometheus"
COMMON = ROOT / "references" / "playbooks" / "common_playbooks.json"
TMP = ROOT / "work" / "test_tmp" / "prometheus"

sys.path.insert(0, str(SCRIPTS))

import patrol_lib  # noqa: E402

# 脚本名以数字开头不能用常规 import 语法，用 importlib 按路径加载
_spec = importlib.util.spec_from_file_location(
    "prometheus_triage_08", SCRIPTS / "08_prometheus_triage.py"
)
mod = importlib.util.module_from_spec(_spec)
sys.modules["prometheus_triage_08"] = mod
_spec.loader.exec_module(mod)

FAKE_TOKEN = "fake-token"
TOKEN_ENV_REF = "PROMETHEUS_API_TOKEN"
ALERTS_PATH = "/api/v1/alerts"


class FakePrometheus:
    """本地假 Prometheus HTTP 服务（ThreadingHTTPServer，端口系统分配）。

    - 仅 GET /api/v1/alerts 有效，其余 404
    - status_error=True 时返回 {"status":"error",...}
    - alerts_not_list=True 时 data.alerts 给非数组（模拟结构异常）
    - empty=True 时返回空告警数组
    - 记录每次请求的 path 与 Authorization 头（供断言）
    """

    def __init__(self, alerts=None, status_error=False, alerts_not_list=False, empty=False):
        if alerts is None:
            alerts = json.loads((FIXTURES / "api_alerts.json").read_text(encoding="utf-8")
                                )["data"]["alerts"]
        self.alerts = alerts
        self.status_error = status_error
        self.alerts_not_list = alerts_not_list
        self.empty = empty
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _json(self, obj, status=200):
                body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                outer.requests.append({
                    "path": self.path,
                    "authorization": self.headers.get("Authorization", ""),
                })
                if self.path != ALERTS_PATH:
                    self._json({"status": "error", "error": "unknown path"}, 404)
                    return
                if outer.status_error:
                    self._json({"status": "error", "errorType": "server-error",
                                "error": "query timed out"})
                    return
                if outer.alerts_not_list:
                    self._json({"status": "success", "data": {"alerts": {"unexpected": True}}})
                    return
                rows = [] if outer.empty else outer.alerts
                self._json({"status": "success", "data": {"alerts": rows}})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.url = "http://127.0.0.1:%d" % self.port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def _config_for(fake, **overrides):
    """fixture 配置模板替换 {PORT} 后落盘到 TMP，返回配置文件路径。"""
    cfg = json.loads((FIXTURES / "monitors_local.json").read_text(encoding="utf-8"))
    cfg["prometheus"]["url"] = cfg["prometheus"]["url"].replace("{PORT}", str(fake.port))
    cfg["prometheus"].update(overrides)
    p = TMP / ("monitors_%d.json" % time.time_ns())
    p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _last_json(buf):
    return json.loads(buf.getvalue().strip().splitlines()[-1])


def _run(argv):
    """运行 CLI 子命令，返回 (rc, 信封)。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.main(list(argv))
    return rc, _last_json(buf)


def _expect_gap(argv):
    """期待 gap 退出（SystemExit 2），返回失败信封。"""
    buf = io.StringIO()
    code = None
    with contextlib.redirect_stdout(buf):
        try:
            mod.main(list(argv))
        except SystemExit as e:
            code = e.code
    payload = _last_json(buf)
    assert payload.get("ok") is False, payload
    assert payload.get("gap"), payload
    assert code == patrol_lib.EXIT_GAP, "期望退出码 %s，实际 %s" % (patrol_lib.EXIT_GAP, code)
    return payload


def _no_token_env():
    """清掉 token 环境变量的上下文（clear=True 全量还原，避免进程环境污染）。"""
    env = {k: v for k, v in os.environ.items() if k != TOKEN_ENV_REF}
    return mock.patch.dict(os.environ, env, clear=True)


class TestAlerts(unittest.TestCase):
    """alerts 阶段：假服务端到端 + 各 gap 路径。"""

    def setUp(self):
        TMP.mkdir(parents=True, exist_ok=True)

    def test_alerts_end_to_end(self):
        """端到端：url 尾斜杠归一（无双斜杠）、Bearer 头、severity/id/host 归一、落盘结构。"""
        fake = FakePrometheus()
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("alerts_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            rc, env = _run(["alerts", "--config", str(cfg), "--group", "prometheus",
                            "--out", str(out)])

        # 信封
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 3)
        self.assertEqual(env["by_severity"], {"critical": 1, "warning": 1, "info": 1})
        self.assertEqual(env["endpoint"], "127.0.0.1:%d%s" % (fake.port, ALERTS_PATH))
        self.assertTrue(Path(env["output"]).is_file())

        # 请求形态：url 尾斜杠归一后恰为 /api/v1/alerts，token 走 Bearer 头
        self.assertEqual(len(fake.requests), 1)
        req = fake.requests[0]
        self.assertEqual(req["path"], ALERTS_PATH)
        self.assertNotIn("//", req["path"])
        self.assertEqual(req["authorization"], "Bearer %s" % FAKE_TOKEN)

        # 落盘结构：token 绝不出现，endpoint 不含 scheme
        out_path = Path(env["output"])
        raw = out_path.read_text(encoding="utf-8")
        self.assertNotIn(FAKE_TOKEN, raw)
        doc = json.loads(raw)
        self.assertIn("version", doc)
        self.assertRegex(doc["fetched_at"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        self.assertEqual(doc["source"], "prometheus")
        self.assertEqual(doc["endpoint"], "127.0.0.1:%d%s" % (fake.port, ALERTS_PATH))
        findings = doc["findings"]
        self.assertEqual(len(findings), 3)

        # critical 实例告警：id=alertname@instance，severity 归一，labels 原样保留
        f0 = findings[0]
        self.assertEqual(f0["source"], "prometheus")
        self.assertEqual(f0["id"], "InstanceDown@10.10.0.11:9100")
        self.assertEqual(f0["title"], "Instance down: node unreachable")  # annotations.summary
        self.assertEqual(f0["host"], "10.10.0.11:9100")
        self.assertEqual(f0["severity_label"], "critical")
        self.assertEqual(f0["state"], "active")
        self.assertEqual(f0["active_at"], "2026-10-08T09:30:00Z")
        self.assertEqual(f0["value"], "1")
        self.assertIn("has been down", f0["description"])
        self.assertEqual(f0["labels"]["job"], "node")
        self.assertEqual(f0["labels"]["severity"], "critical")

        # warning 磁盘告警
        f1 = findings[1]
        self.assertEqual(f1["id"], "NodeDiskUsageHigh@10.10.0.12:9100")
        self.assertEqual(f1["severity_label"], "warning")
        self.assertEqual(f1["value"], "86.4")

        # info 无实例告警：instance 缺省补 unknown，title 回落 alertname，severity=none -> info
        f2 = findings[2]
        self.assertEqual(f2["id"], "Watchdog@unknown")
        self.assertEqual(f2["host"], "unknown")
        self.assertEqual(f2["title"], "Watchdog")
        self.assertEqual(f2["severity_label"], "info")

    def test_alerts_status_error_gap(self):
        """响应 status:"error" -> gap 带 error 详情，只发一条请求。"""
        fake = FakePrometheus(status_error=True)
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("err_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            payload = _expect_gap(["alerts", "--config", str(cfg), "--out", str(out)])
        self.assertIn("非 success", payload["gap"])
        self.assertIn("query timed out", payload["gap"])
        self.assertEqual(len(fake.requests), 1)

    def test_alerts_bad_shape_gap(self):
        """data.alerts 不是数组 -> gap，不猜测。"""
        fake = FakePrometheus(alerts_not_list=True)
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("shape_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            payload = _expect_gap(["alerts", "--config", str(cfg), "--out", str(out)])
        self.assertIn("data.alerts", payload["gap"])
        self.assertEqual(len(fake.requests), 1)

    def test_alerts_token_missing_gap_no_request(self):
        """token_env_ref 声明了变量但环境变量未设 -> gap 含变量名，且未发任何出站请求。"""
        fake = FakePrometheus()
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("notok_%d.json" % time.time_ns())
        with _no_token_env():
            payload = _expect_gap(["alerts", "--config", str(cfg), "--out", str(out)])
        self.assertIn(TOKEN_ENV_REF, payload["gap"])
        self.assertIn("token_env_ref", payload["gap"])
        self.assertEqual(fake.requests, [])

    def test_alerts_disabled_gap(self):
        """enabled=false -> gap 明示置 true 的动作指引，不发请求。"""
        fake = FakePrometheus()
        self.addCleanup(fake.stop)
        cfg = _config_for(fake, enabled=False)
        out = TMP / ("disabled_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            payload = _expect_gap(["alerts", "--config", str(cfg), "--out", str(out)])
        self.assertIn("端点未启用", payload["gap"])
        self.assertIn("prometheus.enabled=false", payload["gap"])
        self.assertEqual(fake.requests, [])

    def test_alerts_empty_ok_no_active(self):
        """0 条活动告警：ok:true 且注明无活动告警，alerts.json findings 为空数组。"""
        fake = FakePrometheus(empty=True)
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("empty_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            rc, env = _run(["alerts", "--config", str(cfg), "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 0)
        self.assertEqual(env["by_severity"], {})
        self.assertIn("无活动告警", env.get("note", ""))
        doc = json.loads(Path(env["output"]).read_text(encoding="utf-8"))
        self.assertEqual(doc["findings"], [])


class TestTriage(unittest.TestCase):
    """triage 阶段：纯离线（不启动任何服务）。"""

    def setUp(self):
        TMP.mkdir(parents=True, exist_ok=True)

    def test_triage_end_to_end_fixture(self):
        """fixture alerts.json + 通用剧本库 -> 报告 critical->warning->info 分块、命中/兜底齐全。"""
        out = TMP / ("guide_%d.md" % time.time_ns())
        rc, env = _run(["triage", "--alerts", str(FIXTURES / "alerts.json"),
                        "--common", str(COMMON), "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 3)
        self.assertEqual(env["matched"], 2)    # InstanceDown -> service_down；磁盘 -> disk_usage_high
        self.assertEqual(env["unmatched"], 1)  # Watchdog（无关键词命中）
        self.assertEqual(env["by_severity"], {"critical": 1, "warning": 1, "info": 1})

        report = Path(env["report"])
        self.assertTrue(report.is_file())
        text = report.read_text(encoding="utf-8")
        # 头部三要素
        self.assertIn("**【待复核】**", text)
        self.assertRegex(text, r"生成时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
        self.assertIn("prometheus.example.internal:9090/api/v1/alerts", text)
        self.assertIn("告警总数：3（剧本命中 2 / 通用兜底 1）", text)
        # critical -> warning -> info 排序分块
        i1 = text.index("## 1. [critical]")
        i2 = text.index("## 2. [warning]")
        i3 = text.index("## 3. [info]")
        self.assertLess(i1, i2)
        self.assertLess(i2, i3)
        # 命中剧本块的要素：ID/实例/严重度/触发时间/当前值/描述/处置步骤
        self.assertIn("告警 ID：InstanceDown@10.10.0.11:9100", text)
        self.assertIn("实例：10.10.0.11:9100", text)
        self.assertIn("触发时间：2026-10-08T09:30:00Z", text)
        self.assertIn("当前值：86.4", text)
        self.assertIn("描述：Disk usage on /data is above 85 percent.", text)
        self.assertIn("处置剧本：服务/主机失联", text)
        self.assertIn("处置剧本：磁盘空间", text)
        self.assertIn("   1. ", text)  # 编号步骤
        # 兜底块：通用 3 步 + runbook_url 列出 + 05 号子工具示例命令
        self.assertIn("通用兜底", text)
        self.assertIn("http://prometheus.example.internal/runbooks/watchdog", text)
        self.assertIn("05_kb_similar_search.py query --text", text)

    def test_triage_missing_findings_key_gap(self):
        """alerts 文件缺 findings 键 -> gap 指明结构问题与补救动作。"""
        bad = TMP / ("bad_%d.json" % time.time_ns())
        bad.write_text(json.dumps({"version": "1.0", "source": "prometheus"}),
                       encoding="utf-8")
        out = TMP / ("bad_guide_%d.md" % time.time_ns())
        payload = _expect_gap(["triage", "--alerts", str(bad), "--out", str(out)])
        self.assertIn("findings", payload["gap"])

    def test_triage_empty_findings_ok(self):
        """findings 为空数组 -> ok:true，报告仍生成（0 告警）。"""
        src = TMP / ("empty_%d.json" % time.time_ns())
        src.write_text(json.dumps({
            "version": "1.0", "fetched_at": "2026-10-08 10:00:00",
            "source": "prometheus", "endpoint": "prometheus.example.internal:9090/api/v1/alerts",
            "findings": [],
        }, ensure_ascii=False), encoding="utf-8")
        out = TMP / ("empty_guide_%d.md" % time.time_ns())
        rc, env = _run(["triage", "--alerts", str(src), "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 0)
        self.assertEqual(env["matched"], 0)
        self.assertEqual(env["unmatched"], 0)
        text = Path(env["report"]).read_text(encoding="utf-8")
        self.assertIn("**【待复核】**", text)
        self.assertIn("告警总数：0", text)


class TestHelpers(unittest.TestCase):
    """归一化/URL/剧本匹配/兜底工具单测（纯函数，无 IO）。"""

    def test_norm_severity_label(self):
        self.assertEqual(mod.norm_severity_label("critical"), "critical")
        self.assertEqual(mod.norm_severity_label("Firing"), "critical")
        self.assertEqual(mod.norm_severity_label("warning"), "warning")
        self.assertEqual(mod.norm_severity_label("warn"), "warning")
        self.assertEqual(mod.norm_severity_label("none"), "info")
        self.assertEqual(mod.norm_severity_label(""), "info")
        self.assertEqual(mod.norm_severity_label(None), "info")

    def test_build_alerts_url_trailing_slash(self):
        self.assertEqual(mod.build_alerts_url("http://prom.example.internal:9090"),
                         "http://prom.example.internal:9090/api/v1/alerts")
        self.assertEqual(mod.build_alerts_url("http://prom.example.internal:9090/"),
                         "http://prom.example.internal:9090/api/v1/alerts")
        self.assertEqual(mod.build_alerts_url("http://prom.example.internal:9090//"),
                         "http://prom.example.internal:9090/api/v1/alerts")
        self.assertNotIn("//api", mod.build_alerts_url("http://prom.example.internal:9090/"))

    def test_endpoint_of(self):
        self.assertEqual(
            mod.endpoint_of("http://prom.example.internal:9090/api/v1/alerts"),
            "prom.example.internal:9090/api/v1/alerts")
        self.assertEqual(mod.endpoint_of("http://prom.internal/api/v1/alerts"),
                         "prom.internal/api/v1/alerts")

    def test_count_by_severity_order(self):
        counts = mod.count_by_severity([
            {"severity_label": "info"},
            {"severity_label": "critical"},
            {"severity_label": "critical"},
            {"severity_label": "warning"},
            {"severity_label": "page"},  # 未知标签追加在最后
        ])
        self.assertEqual(list(counts.keys()), ["critical", "warning", "info", "page"])
        self.assertEqual(counts["critical"], 2)

    def test_playbook_match_and_fallback(self):
        """剧本按库内顺序首命中（三字段拼接 hay）；兜底 3 步含 runbook 与 05 命令。"""
        pbs = json.loads(COMMON.read_text(encoding="utf-8"))["playbooks"]
        # 命中来自 labels.alertname（title 平淡）
        pb = mod.match_playbook({"title": "告警", "labels": {"alertname": "HighCpuLoad"},
                                 "description": ""}, pbs)
        self.assertIsNotNone(pb)
        self.assertEqual(pb["id"], "cpu_high")
        # 命中来自 description（title/alertname 都不带关键词；注意避开含 "io" 的词，
        # 如 replication，否则库序靠前的 disk_io_high 会先命中）
        pb2 = mod.match_playbook({"title": "x", "labels": {},
                                  "description": "mysql replica lag detected on db-01"}, pbs)
        self.assertEqual(pb2["id"], "mysql_slow")
        # 完全无关
        self.assertIsNone(mod.match_playbook(
            {"title": "完全无关的自研告警xyz", "labels": {}, "description": ""}, pbs))

        # 兜底 3 步：无 runbook_url 时提示查规则 annotations.runbook_url
        steps = mod.fallback_steps({"title": "自定义业务接口探活连续失败", "host": "biz-gw-01",
                                    "annotations": {}, "labels": {}})
        self.assertEqual(len(steps), 3)
        self.assertIn("annotations.runbook_url", steps[1])
        self.assertIn("05_kb_similar_search.py", steps[2])
        self.assertIn("自定义业务接口探活连续失败", steps[2])
        # annotations.runbook_url 有值时直接列出
        steps2 = mod.fallback_steps({"title": "Watchdog", "host": "unknown",
                                     "annotations": {"runbook_url": "http://runbook.example.internal/w"},
                                     "labels": {}})
        self.assertIn("http://runbook.example.internal/w", steps2[1])


if __name__ == "__main__":
    unittest.main()
