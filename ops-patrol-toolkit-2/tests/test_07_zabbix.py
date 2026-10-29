#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""07 Zabbix 告警拉取与离线分诊测试。

全离线：本地 http.server（绑定 127.0.0.1:0）假 /api_jsonrpc.php，按 payload.method
分发 problem.get/trigger.get 的 canned result；auth 不对返回 JSON-RPC error；
绝不访问真实端点。fixture 配置 monitors_local.json 双开 allow_local_targets/
allow_private_targets 且 enabled=true，{PORT} 由测试运行时替换。

覆盖：problems 端到端（problem.get -> trigger.get 调用顺序、host 回填、severity_label、
落盘结构、token 不落盘）；CLI --severities 覆盖配置；JSON-RPC error -> gap；
token 缺失 -> gap 且断言未发任何请求；enabled=false -> gap；0 条告警 ok:true；
triage 离线端到端（fixture problems.json + 通用剧本库）；缺 findings 键 gap；
空 findings ok；剧本匹配/兜底与时间工具单测。

临时产物只写 work/test_tmp/zabbix/（避免与其他并行 agent 撞名）。
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
FIXTURES = ROOT / "tests" / "fixtures" / "patrol" / "zabbix"
COMMON = ROOT / "references" / "playbooks" / "common_playbooks.json"
TMP = ROOT / "work" / "test_tmp" / "zabbix"

sys.path.insert(0, str(SCRIPTS))

import patrol_lib  # noqa: E402

# 脚本名以数字开头不能用常规 import 语法，用 importlib 按路径加载
_spec = importlib.util.spec_from_file_location(
    "zabbix_triage_07", SCRIPTS / "07_zabbix_triage.py"
)
mod = importlib.util.module_from_spec(_spec)
sys.modules["zabbix_triage_07"] = mod
_spec.loader.exec_module(mod)

FAKE_TOKEN = "fake-token"
TOKEN_ENV_REF = "ZABBIX_API_TOKEN"


class FakeZabbix:
    """本地假 Zabbix JSON-RPC 服务（ThreadingHTTPServer，端口系统分配）。

    - 仅 /api_jsonrpc.php 有效，其余 404 + JSON-RPC error
    - auth != FAKE_TOKEN 一律返回 JSON-RPC error（Not authorized）
    - problem.get 按 params.severity 过滤 canned 数据（severities 过滤由服务端模拟）
    - trigger.get 按 params.triggerids 过滤 canned 触发器
    - problems 传非 list 可模拟响应结构异常
    """

    def __init__(self, problems=None, triggers=None, empty=False):
        if problems is None:
            problems = json.loads((FIXTURES / "api_problems.json").read_text(encoding="utf-8"))
        if triggers is None:
            triggers = json.loads((FIXTURES / "api_triggers.json").read_text(encoding="utf-8"))
        self.problems = problems
        self.triggers = triggers
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

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(n) if n else b""
                try:
                    body = json.loads(raw.decode("utf-8")) if raw else {}
                except json.JSONDecodeError:
                    body = {}
                outer.requests.append({
                    "path": self.path,
                    "content_type": self.headers.get("Content-Type", ""),
                    "body": body,
                })
                if self.path != "/api_jsonrpc.php":
                    self._json({"jsonrpc": "2.0", "id": body.get("id"),
                                "error": {"code": -32601, "message": "unknown path"}}, 404)
                    return
                if body.get("auth") != FAKE_TOKEN:
                    self._json({"jsonrpc": "2.0", "id": body.get("id"),
                                "error": {"code": -32602, "message": "Not authorized"}})
                    return
                method = body.get("method")
                params = body.get("params") or {}
                if method == "problem.get":
                    rows = [] if outer.empty else outer.problems
                    sev = params.get("severity")
                    if isinstance(rows, list) and sev:
                        wanted = {int(x) for x in sev}
                        rows = [p for p in rows
                                if int(p.get("severity") or 0) in wanted]
                    self._json({"jsonrpc": "2.0", "id": body.get("id"), "result": rows})
                elif method == "trigger.get":
                    ids = {str(x) for x in (params.get("triggerids") or [])}
                    rows = [t for t in outer.triggers
                            if str(t.get("triggerid")) in ids]
                    self._json({"jsonrpc": "2.0", "id": body.get("id"), "result": rows})
                else:
                    self._json({"jsonrpc": "2.0", "id": body.get("id"),
                                "error": {"code": -32601,
                                          "message": "method not found: %s" % method}})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.url = "http://127.0.0.1:%d/api_jsonrpc.php" % self.port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def _config_for(fake, **overrides):
    """fixture 配置模板替换 {PORT} 后落盘到 TMP，返回配置文件路径。"""
    cfg = json.loads((FIXTURES / "monitors_local.json").read_text(encoding="utf-8"))
    cfg["zabbix"]["url"] = cfg["zabbix"]["url"].replace("{PORT}", str(fake.port))
    cfg["zabbix"].update(overrides)
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


class TestProblems(unittest.TestCase):
    """problems 阶段：假服务端到端 + 各 gap 路径。"""

    def setUp(self):
        TMP.mkdir(parents=True, exist_ok=True)

    def test_problems_end_to_end(self):
        """端到端：problem.get -> trigger.get 顺序、host 回填、severity_label、落盘结构。"""
        fake = FakeZabbix()
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("problems_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            rc, env = _run(["problems", "--config", str(cfg), "--group", "zabbix",
                            "--limit", "50", "--out", str(out)])

        # 信封
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 4)
        self.assertEqual(env["by_severity"], {"灾难": 2, "严重": 1, "一般严重": 1})
        self.assertEqual(env["endpoint"], "127.0.0.1:%d/api_jsonrpc.php" % fake.port)
        self.assertTrue(Path(env["output"]).is_file())

        # 调用顺序与请求形态：先 problem.get（id=1）后 trigger.get（id=2）
        self.assertEqual([r["body"].get("method") for r in fake.requests],
                         ["problem.get", "trigger.get"])
        for r in fake.requests:
            self.assertEqual(r["path"], "/api_jsonrpc.php")
            self.assertTrue(r["content_type"].startswith("application/json-rpc"),
                            r["content_type"])
        p_req = fake.requests[0]["body"]
        self.assertEqual(p_req["id"], 1)
        self.assertEqual(p_req["auth"], FAKE_TOKEN)
        self.assertEqual(p_req["params"]["recent"], True)
        self.assertEqual(p_req["params"]["sortfield"], "eventid")
        self.assertEqual(p_req["params"]["sortorder"], "DESC")
        self.assertEqual(p_req["params"]["limit"], 50)
        self.assertEqual(p_req["params"]["severity"], [3, 4, 5])  # 来自 fixture 配置
        t_req = fake.requests[1]["body"]
        self.assertEqual(t_req["id"], 2)
        self.assertEqual(t_req["params"]["triggerids"],
                         ["10501", "10502", "10503", "10504"])
        self.assertEqual(t_req["params"]["output"],
                         ["triggerid", "description", "priority"])
        self.assertEqual(t_req["params"]["selectHosts"], ["host", "name"])

        # 落盘结构：token 绝不出现，endpoint 不含 scheme
        out_path = Path(env["output"])
        raw = out_path.read_text(encoding="utf-8")
        self.assertNotIn(FAKE_TOKEN, raw)
        doc = json.loads(raw)
        self.assertIn("version", doc)
        self.assertRegex(doc["fetched_at"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        self.assertEqual(doc["source"], "zabbix")
        self.assertEqual(doc["endpoint"], "127.0.0.1:%d/api_jsonrpc.php" % fake.port)
        findings = doc["findings"]
        self.assertEqual(len(findings), 4)
        f0 = findings[0]
        self.assertEqual(f0["source"], "zabbix")
        self.assertEqual(f0["id"], "3001")
        self.assertIn("cpu", f0["title"].lower())
        self.assertEqual(f0["host"], "应用服务器 01")  # selectHosts 的 name 回填
        self.assertEqual(f0["severity"], 5)
        self.assertEqual(f0["severity_label"], "灾难")
        self.assertRegex(f0["fired_at"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        self.assertGreaterEqual(f0["age_s"], 0)
        self.assertEqual(f0["tags"], [{"tag": "scope", "value": "performance"}])
        # 第二条 host 同样回填
        self.assertEqual(findings[1]["host"], "数据库服务器 01")
        self.assertEqual(findings[1]["severity_label"], "严重")

    def test_problems_cli_severities_override(self):
        """CLI --severities 覆盖配置：problem.get 带指定级别，fake 服务端过滤后仅返回该级。"""
        fake = FakeZabbix()
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("sev_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            rc, env = _run(["problems", "--config", str(cfg), "--severities", "5",
                            "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 2)  # 3001/3004 均为 severity 5
        self.assertEqual(env["by_severity"], {"灾难": 2})
        self.assertEqual(fake.requests[0]["body"]["params"]["severity"], [5])

    def test_problems_jsonrpc_error_gap(self):
        """响应含 JSON-RPC error（auth 不对）-> gap 带 code/message，只发一条请求。"""
        fake = FakeZabbix()
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("err_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: "wrong-token"}):
            payload = _expect_gap(["problems", "--config", str(cfg), "--out", str(out)])
        self.assertIn("JSON-RPC error", payload["gap"])
        self.assertIn("Not authorized", payload["gap"])
        self.assertEqual(len(fake.requests), 1)  # problem.get 失败即停，无第二步

    def test_problems_token_missing_gap_no_request(self):
        """token_env_ref 声明了变量但环境变量未设 -> gap 含变量名，且未发任何出站请求。"""
        fake = FakeZabbix()
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("notok_%d.json" % time.time_ns())
        with _no_token_env():
            payload = _expect_gap(["problems", "--config", str(cfg), "--out", str(out)])
        self.assertIn(TOKEN_ENV_REF, payload["gap"])
        self.assertIn("token_env_ref", payload["gap"])
        self.assertEqual(fake.requests, [])

    def test_problems_disabled_gap(self):
        """enabled=false -> gap 明示置 true 的动作指引，不发请求。"""
        fake = FakeZabbix()
        self.addCleanup(fake.stop)
        cfg = _config_for(fake, enabled=False)
        out = TMP / ("disabled_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            payload = _expect_gap(["problems", "--config", str(cfg), "--out", str(out)])
        self.assertIn("端点未启用", payload["gap"])
        self.assertIn("zabbix.enabled=false", payload["gap"])
        self.assertEqual(fake.requests, [])

    def test_problems_empty_ok_no_active(self):
        """0 条活动告警：ok:true 且注明无活动告警，problems.json findings 为空数组。"""
        fake = FakeZabbix(empty=True)
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("empty_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            rc, env = _run(["problems", "--config", str(cfg), "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 0)
        self.assertEqual(env["by_severity"], {})
        self.assertIn("无活动告警", env.get("note", ""))
        doc = json.loads(Path(env["output"]).read_text(encoding="utf-8"))
        self.assertEqual(doc["findings"], [])

    def test_problems_bad_result_shape_gap(self):
        """problem.get 的 result 不是数组 -> gap，不猜测。"""
        fake = FakeZabbix(problems={"unexpected": True})
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("shape_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            payload = _expect_gap(["problems", "--config", str(cfg), "--out", str(out)])
        self.assertIn("不是数组", payload["gap"])
        self.assertEqual(len(fake.requests), 1)


class TestTriage(unittest.TestCase):
    """triage 阶段：纯离线（不启动任何服务）。"""

    def setUp(self):
        TMP.mkdir(parents=True, exist_ok=True)

    def test_triage_end_to_end_fixture(self):
        """fixture problems.json + 通用剧本库 -> 报告按严重度降序分块、命中/兜底齐全。"""
        out = TMP / ("guide_%d.md" % time.time_ns())
        rc, env = _run(["triage", "--problems", str(FIXTURES / "problems.json"),
                        "--common", str(COMMON), "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 3)
        self.assertEqual(env["matched"], 2)    # cpu_high + disk_usage_high
        self.assertEqual(env["unmatched"], 1)  # 自定义业务接口探活（无关键词命中）
        self.assertEqual(env["by_severity"], {"灾难": 1, "严重": 1, "一般严重": 1})

        report = Path(env["report"])
        self.assertTrue(report.is_file())
        text = report.read_text(encoding="utf-8")
        # 头部三要素
        self.assertIn("**【待复核】**", text)
        self.assertRegex(text, r"生成时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
        self.assertIn("zabbix.example.internal/zabbix/api_jsonrpc.php", text)
        # 严重度降序分块：灾难 -> 严重 -> 一般严重
        i1 = text.index("## 1. [灾难]")
        i2 = text.index("## 2. [严重]")
        i3 = text.index("## 3. [一般严重]")
        self.assertLess(i1, i2)
        self.assertLess(i2, i3)
        # 命中剧本块的要素：标题/主机/触发时间/持续时长/处置步骤
        self.assertIn("Free disk space is less than 5% on volume /data", text)
        self.assertIn("数据库服务器 01", text)
        self.assertIn("触发时间：2026-10-08 09:10:00", text)
        self.assertIn("持续时长：50 分钟", text)
        self.assertIn("处置剧本：磁盘空间", text)
        self.assertIn("处置剧本：CPU 使用率/负载过高", text)
        self.assertIn("   1. ", text)  # 编号步骤
        # 兜底块：通用 3 步 + 05 号子工具示例命令
        self.assertIn("自定义业务接口探活连续失败", text)
        self.assertIn("通用兜底", text)
        self.assertIn("05_kb_similar_search.py query --text", text)

    def test_triage_missing_findings_key_gap(self):
        """problems 文件缺 findings 键 -> gap 指明结构问题与补救动作。"""
        bad = TMP / ("bad_%d.json" % time.time_ns())
        bad.write_text(json.dumps({"version": "1.0", "source": "zabbix"}),
                       encoding="utf-8")
        out = TMP / ("bad_guide_%d.md" % time.time_ns())
        payload = _expect_gap(["triage", "--problems", str(bad), "--out", str(out)])
        self.assertIn("findings", payload["gap"])

    def test_triage_empty_findings_ok(self):
        """findings 为空数组 -> ok:true，报告仍生成（0 告警）。"""
        src = TMP / ("empty_%d.json" % time.time_ns())
        src.write_text(json.dumps({
            "version": "1.0", "fetched_at": "2026-10-08 10:00:00",
            "source": "zabbix", "endpoint": "zabbix.example.internal/api_jsonrpc.php",
            "findings": [],
        }, ensure_ascii=False), encoding="utf-8")
        out = TMP / ("empty_guide_%d.md" % time.time_ns())
        rc, env = _run(["triage", "--problems", str(src), "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 0)
        self.assertEqual(env["matched"], 0)
        self.assertEqual(env["unmatched"], 0)
        text = Path(env["report"]).read_text(encoding="utf-8")
        self.assertIn("**【待复核】**", text)
        self.assertIn("告警总数：0", text)

    def test_playbook_match_and_fallback(self):
        """剧本按库内顺序首命中（utilization 含 io 但 cpu 库序靠前）；兜底 3 步含 05 命令。"""
        pbs = json.loads(COMMON.read_text(encoding="utf-8"))["playbooks"]
        pb = mod.match_playbook("High CPU utilization (over 90% for 5m)", pbs)
        self.assertIsNotNone(pb)
        self.assertEqual(pb["id"], "cpu_high")
        pb2 = mod.match_playbook("MySQL: Threads_connected is over 90%", pbs)
        self.assertEqual(pb2["id"], "mysql_slow")
        self.assertIsNone(mod.match_playbook("完全无关的自研告警xyz", pbs))

        steps = mod.fallback_steps({"title": "自定义业务接口探活连续失败", "host": "biz-gw-01"})
        self.assertEqual(len(steps), 3)
        self.assertIn("05_kb_similar_search.py", steps[2])
        self.assertIn("自定义业务接口探活连续失败", steps[2])

    def test_time_helpers(self):
        """epoch 转换、时长人性化、endpoint 提取（不含 scheme 与凭证）。"""
        self.assertEqual(mod.epoch_to_str(0), "")
        self.assertEqual(mod.epoch_to_str("abc"), "")
        self.assertEqual(mod.epoch_to_str(1790000000), time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(1790000000)))
        self.assertEqual(mod.humanize_duration(59), "59 秒")
        self.assertEqual(mod.humanize_duration(60), "1 分钟")
        self.assertEqual(mod.humanize_duration(3600), "1 小时 0 分钟")
        self.assertEqual(mod.humanize_duration(90000), "1 天 1 小时")
        self.assertEqual(mod.humanize_duration("x"), "未知")
        self.assertEqual(
            mod.endpoint_of("http://zabbix.example.internal:8080/zabbix/api_jsonrpc.php"),
            "zabbix.example.internal:8080/zabbix/api_jsonrpc.php")
        self.assertEqual(mod.endpoint_of("http://zb.internal/api_jsonrpc.php"),
                         "zb.internal/api_jsonrpc.php")


if __name__ == "__main__":
    unittest.main()
