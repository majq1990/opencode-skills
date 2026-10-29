#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09 SkyWalking 告警拉取与离线分诊测试。

全离线：本地 http.server（绑定 127.0.0.1:0）假 /graphql，POST 返回 canned
{"data":{"alarms":[3 条不同形态：key+message+startTime / id+name / 缺字段]}}；
errors 模式返回 {"errors":[{"message":"duration format error"}]}；
missing_alarms 模式返回 {"data":{}}；绝不访问真实端点。
fixture 配置 monitors_local.json 双开 allow_local_targets/allow_private_targets
且 enabled=true，{PORT} 由测试运行时替换。

覆盖：alarms 端到端（POST payload 含 query+variables、Bearer 头、duration 覆盖、
三种形态归一化、落盘结构、token 不落盘）；配置 duration 与自定义 alarm_query 生效；
errors -> gap；data.alarms 缺失 -> gap；token 缺失 -> gap 且断言未发任何请求；
enabled=false -> gap；0 条告警 ok:true；triage 离线端到端（fixture alarms.json +
通用剧本库，jvm/cpu 命中、业务告警兜底）；缺 findings 键 gap；findings 非数组 gap；
空 findings ok；剧本匹配（标题+服务名）/兜底与时间工具单测。

临时产物只写 work/test_tmp/skywalking/（避免与其他并行 agent 撞名）。
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
FIXTURES = ROOT / "tests" / "fixtures" / "patrol" / "skywalking"
COMMON = ROOT / "references" / "playbooks" / "common_playbooks.json"
TMP = ROOT / "work" / "test_tmp" / "skywalking"

sys.path.insert(0, str(SCRIPTS))

import patrol_lib  # noqa: E402

# 脚本名以数字开头不能用常规 import 语法，用 importlib 按路径加载
_spec = importlib.util.spec_from_file_location(
    "skywalking_triage_09", SCRIPTS / "09_skywalking_triage.py"
)
mod = importlib.util.module_from_spec(_spec)
sys.modules["skywalking_triage_09"] = mod
_spec.loader.exec_module(mod)

FAKE_TOKEN = "fake-token"
TOKEN_ENV_REF = "SKYWALKING_API_TOKEN"


class FakeSkyWalking:
    """本地假 SkyWalking OAP GraphQL 服务（ThreadingHTTPServer，端口系统分配）。

    - 仅 /graphql 有效，其余 404 + errors 响应
    - mode="ok" 返回 {"data":{"alarms":[...]}}；"errors" 返回 {"errors":[...]}；
      "missing_alarms" 返回 {"data":{}}（缺 alarms 字段）
    - 记录每次请求的 path/headers/body 供断言（含 Authorization 头）
    """

    def __init__(self, alarms=None, mode="ok"):
        if alarms is None:
            alarms = json.loads((FIXTURES / "api_alarms.json").read_text(encoding="utf-8"))
        self.alarms = alarms
        self.mode = mode
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
                    "authorization": self.headers.get("Authorization", ""),
                    "content_type": self.headers.get("Content-Type", ""),
                    "body": body,
                })
                if self.path != "/graphql":
                    self._json({"errors": [{"message": "unknown path: %s" % self.path}]}, 404)
                    return
                if outer.mode == "errors":
                    self._json({"errors": [{"message": "duration format error"}]})
                elif outer.mode == "missing_alarms":
                    self._json({"data": {}})
                else:
                    self._json({"data": {"alarms": outer.alarms}})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.url = "http://127.0.0.1:%d/graphql" % self.port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def _config_for(fake, **overrides):
    """fixture 配置模板替换 {PORT} 后落盘到 TMP，返回配置文件路径。"""
    cfg = json.loads((FIXTURES / "monitors_local.json").read_text(encoding="utf-8"))
    cfg["skywalking"]["url"] = cfg["skywalking"]["url"].replace("{PORT}", str(fake.port))
    cfg["skywalking"].update(overrides)
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


class TestAlarms(unittest.TestCase):
    """alarms 阶段：假服务端到端 + 各 gap 路径。"""

    def setUp(self):
        TMP.mkdir(parents=True, exist_ok=True)

    def test_alarms_end_to_end(self):
        """端到端：GraphQL payload 含 query+variables、Bearer 头、duration 覆盖、
        三种形态归一化、落盘结构、token 不落盘。"""
        fake = FakeSkyWalking()
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("alarms_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            rc, env = _run(["alarms", "--config", str(cfg), "--group", "skywalking",
                            "--duration", "minutes:30", "--out", str(out)])

        # 信封
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 3)
        self.assertEqual(env["endpoint"], "127.0.0.1:%d/graphql" % fake.port)
        self.assertEqual(env["duration"], "minutes:30")
        self.assertTrue(Path(env["output"]).is_file())

        # 请求形态：单条 GraphQL POST，Bearer 头，payload 含 query 与 variables
        self.assertEqual(len(fake.requests), 1)
        r = fake.requests[0]
        self.assertEqual(r["path"], "/graphql")
        self.assertEqual(r["authorization"], "Bearer %s" % FAKE_TOKEN)
        self.assertTrue(r["content_type"].startswith("application/json"), r["content_type"])
        body = r["body"]
        self.assertEqual(body["query"], mod.DEFAULT_QUERY)
        self.assertEqual(body["variables"], {"duration": "minutes:30"})

        # 落盘结构：token 绝不出现，endpoint 不含 scheme
        out_path = Path(env["output"])
        raw = out_path.read_text(encoding="utf-8")
        self.assertNotIn(FAKE_TOKEN, raw)
        doc = json.loads(raw)
        self.assertIn("version", doc)
        self.assertRegex(doc["fetched_at"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        self.assertEqual(doc["source"], "skywalking")
        self.assertEqual(doc["endpoint"], "127.0.0.1:%d/graphql" % fake.port)
        self.assertEqual(doc["duration"], "minutes:30")
        findings = doc["findings"]
        self.assertEqual(len(findings), 3)

        # 形态一：key+message+startTime 齐全（key 优先做 id，message 做标题，scope 无字段补 unknown）
        f0 = findings[0]
        self.assertEqual(f0["source"], "skywalking")
        self.assertEqual(f0["id"], "3001")
        self.assertIn("cpu utilization", f0["title"])
        self.assertEqual(f0["scope"], "unknown")
        self.assertRegex(f0["started_at"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        self.assertEqual(f0["started_at"], mod.epoch_to_str(1790000000))
        self.assertIn("cpu utilization", f0["message"])
        self.assertIsInstance(f0["raw"], dict)
        self.assertEqual(f0["raw"].get("key"), "3001")

        # 形态二：id+name（无 message -> name 做标题与服务名，无 startTime -> 开始时间留空）
        f1 = findings[1]
        self.assertEqual(f1["id"], "5002")
        self.assertEqual(f1["title"], "网关服务 gateway-core")
        self.assertEqual(f1["scope"], "网关服务 gateway-core")
        self.assertEqual(f1["started_at"], "")

        # 形态三：缺字段（id 回落序号，scope 字段补服务名，startTime 可转换）
        f2 = findings[2]
        self.assertEqual(f2["id"], "3")
        self.assertEqual(f2["title"], "3")
        self.assertEqual(f2["scope"], "Endpoint")
        self.assertEqual(f2["started_at"], mod.epoch_to_str(1790003000))

    def test_alarms_config_duration_and_query(self):
        """不带 --duration 用配置 duration；配置 alarm_query 覆盖默认查询。"""
        fake = FakeSkyWalking()
        self.addCleanup(fake.stop)
        custom_query = ("query ($duration: Duration!) { alarms: queryAlarms(duration: $duration) "
                        "{ key id message } }")
        cfg = _config_for(fake, alarm_query=custom_query)
        out = TMP / ("cfgq_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            rc, env = _run(["alarms", "--config", str(cfg), "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        body = fake.requests[0]["body"]
        self.assertEqual(body["query"], custom_query)  # 配置 alarm_query 生效
        self.assertEqual(body["variables"], {"duration": "minutes:60"})  # 配置 duration 生效
        self.assertEqual(env["duration"], "minutes:60")

    def test_alarms_errors_gap(self):
        """响应含非空 errors -> gap 带 message，只发一条请求。"""
        fake = FakeSkyWalking(mode="errors")
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("err_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            payload = _expect_gap(["alarms", "--config", str(cfg), "--out", str(out)])
        self.assertIn("errors", payload["gap"])
        self.assertIn("duration format error", payload["gap"])
        self.assertEqual(len(fake.requests), 1)

    def test_alarms_missing_alarms_gap(self):
        """data.alarms 缺失 -> gap 提示 alarm_query 可调整，不猜测。"""
        fake = FakeSkyWalking(mode="missing_alarms")
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("noalarms_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            payload = _expect_gap(["alarms", "--config", str(cfg), "--out", str(out)])
        self.assertIn("data.alarms", payload["gap"])
        self.assertIn("alarm_query", payload["gap"])
        self.assertEqual(len(fake.requests), 1)

    def test_alarms_token_missing_gap_no_request(self):
        """token_env_ref 声明了变量但环境变量未设 -> gap 含变量名，且未发任何出站请求。"""
        fake = FakeSkyWalking()
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("notok_%d.json" % time.time_ns())
        with _no_token_env():
            payload = _expect_gap(["alarms", "--config", str(cfg), "--out", str(out)])
        self.assertIn(TOKEN_ENV_REF, payload["gap"])
        self.assertIn("token_env_ref", payload["gap"])
        self.assertEqual(fake.requests, [])

    def test_alarms_disabled_gap(self):
        """enabled=false -> gap 明示置 true 的动作指引，不发请求。"""
        fake = FakeSkyWalking()
        self.addCleanup(fake.stop)
        cfg = _config_for(fake, enabled=False)
        out = TMP / ("disabled_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            payload = _expect_gap(["alarms", "--config", str(cfg), "--out", str(out)])
        self.assertIn("端点未启用", payload["gap"])
        self.assertIn("skywalking.enabled=false", payload["gap"])
        self.assertEqual(fake.requests, [])

    def test_alarms_empty_ok_no_active(self):
        """0 条告警：ok:true 且注明无活动告警，alarms.json findings 为空数组。"""
        fake = FakeSkyWalking(alarms=[])
        self.addCleanup(fake.stop)
        cfg = _config_for(fake)
        out = TMP / ("empty_%d.json" % time.time_ns())
        with mock.patch.dict(os.environ, {TOKEN_ENV_REF: FAKE_TOKEN}):
            rc, env = _run(["alarms", "--config", str(cfg), "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 0)
        self.assertIn("无活动告警", env.get("note", ""))
        doc = json.loads(Path(env["output"]).read_text(encoding="utf-8"))
        self.assertEqual(doc["findings"], [])


class TestTriage(unittest.TestCase):
    """triage 阶段：纯离线（不启动任何服务）。"""

    def setUp(self):
        TMP.mkdir(parents=True, exist_ok=True)

    def test_triage_end_to_end_fixture(self):
        """fixture alarms.json + 通用剧本库 -> 报告按拉取顺序分块、命中/兜底齐全。"""
        out = TMP / ("guide_%d.md" % time.time_ns())
        rc, env = _run(["triage", "--alarms", str(FIXTURES / "alarms.json"),
                        "--common", str(COMMON), "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 3)
        self.assertEqual(env["matched"], 2)    # jvm -> tomcat_threadpool；cpu -> cpu_high
        self.assertEqual(env["unmatched"], 1)  # 业务任务排队告警（无关键词命中）

        report = Path(env["report"])
        self.assertTrue(report.is_file())
        text = report.read_text(encoding="utf-8")
        # 头部要素：【待复核】+ 生成时间 + endpoint + duration
        self.assertIn("**【待复核】**", text)
        self.assertRegex(text, r"生成时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
        self.assertIn("skywalking-oap.example.internal:12800/graphql", text)
        self.assertIn("告警时间窗：minutes:60", text)
        self.assertIn("告警总数：3（剧本命中 2 / 通用兜底 1）", text)
        # 分块按拉取顺序：jvm -> cpu -> 业务兜底
        i1 = text.index("## 1. jvm old gen usage")
        i2 = text.index("## 2. service cpu utilization")
        i3 = text.index("## 3. 订单导出任务排队时长超过 300 秒")
        self.assertLess(i1, i2)
        self.assertLess(i2, i3)
        # 命中剧本块的要素：告警 ID/服务/开始时间/告警消息/剧本/编号步骤
        self.assertIn("服务/范围：order-service", text)
        self.assertIn("开始时间：2026-10-08 09:30:00", text)
        self.assertIn("告警消息：jvm old gen usage", text)
        self.assertIn("处置剧本：Tomcat 线程池/JVM 异常（tomcat_threadpool）", text)
        self.assertIn("处置剧本：CPU 使用率/负载过高（cpu_high）", text)
        self.assertIn("   1. ", text)  # 编号步骤
        # 兜底块：通用 3 步 + 05 号子工具示例命令
        self.assertIn("通用兜底", text)
        self.assertIn("SkyWalking UI", text)
        self.assertIn("alarm-settings.yml", text)
        self.assertIn("webhooks", text)
        self.assertIn("05_kb_similar_search.py query --text", text)

    def test_triage_missing_findings_key_gap(self):
        """alarms 文件缺 findings 键 -> gap 指明结构问题与补救动作。"""
        bad = TMP / ("bad_%d.json" % time.time_ns())
        bad.write_text(json.dumps({"version": "1.0", "source": "skywalking"}),
                       encoding="utf-8")
        out = TMP / ("bad_guide_%d.md" % time.time_ns())
        payload = _expect_gap(["triage", "--alarms", str(bad), "--out", str(out)])
        self.assertIn("findings", payload["gap"])

    def test_triage_findings_not_list_gap(self):
        """findings 键不是数组 -> gap，不猜测。"""
        bad = TMP / ("notlist_%d.json" % time.time_ns())
        bad.write_text(json.dumps({"version": "1.0", "source": "skywalking",
                                   "findings": {"oops": True}}), encoding="utf-8")
        out = TMP / ("notlist_guide_%d.md" % time.time_ns())
        payload = _expect_gap(["triage", "--alarms", str(bad), "--out", str(out)])
        self.assertIn("不是数组", payload["gap"])

    def test_triage_empty_findings_ok(self):
        """findings 为空数组 -> ok:true，报告仍生成（0 告警）。"""
        src = TMP / ("empty_%d.json" % time.time_ns())
        src.write_text(json.dumps({
            "version": "1.0", "fetched_at": "2026-10-08 10:00:00",
            "source": "skywalking", "endpoint": "skywalking-oap.example.internal:12800/graphql",
            "duration": "minutes:60", "findings": [],
        }, ensure_ascii=False), encoding="utf-8")
        out = TMP / ("empty_guide_%d.md" % time.time_ns())
        rc, env = _run(["triage", "--alarms", str(src), "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 0)
        self.assertEqual(env["matched"], 0)
        self.assertEqual(env["unmatched"], 0)
        text = Path(env["report"]).read_text(encoding="utf-8")
        self.assertIn("**【待复核】**", text)
        self.assertIn("告警总数：0", text)

    def test_playbook_match_and_fallback(self):
        """剧本按库内顺序首命中（标题+服务名合并匹配）；兜底 3 步含 05 命令。"""
        pbs = json.loads(COMMON.read_text(encoding="utf-8"))["playbooks"]
        # 标题命中
        pb = mod.match_playbook(
            {"title": "jvm old gen usage of order-service is over 90%", "scope": "order-service"}, pbs)
        self.assertIsNotNone(pb)
        self.assertEqual(pb["id"], "tomcat_threadpool")
        # 服务名命中（标题无关键词）
        pb2 = mod.match_playbook({"title": "监控指标异常", "scope": "mysql-readonly-01"}, pbs)
        self.assertEqual(pb2["id"], "mysql_slow")
        # 标题与服务名均未命中
        self.assertIsNone(mod.match_playbook({"title": "完全无关的自研告警xyz", "scope": "svc-x"}, pbs))

        steps = mod.fallback_steps({"title": "订单导出任务排队时长超过 300 秒", "scope": "dispatcher-01"})
        self.assertEqual(len(steps), 3)
        self.assertIn("05_kb_similar_search.py", steps[2])
        self.assertIn("订单导出任务排队时长超过 300 秒", steps[2])
        self.assertIn("dispatcher-01", steps[0])

    def test_time_helpers(self):
        """epoch 转换、标题截断、endpoint 提取（不含 scheme 与凭证）。"""
        self.assertEqual(mod.epoch_to_str(0), "")
        self.assertEqual(mod.epoch_to_str("abc"), "")
        self.assertEqual(mod.epoch_to_str(1790000000), time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(1790000000)))
        # 标题截断 120
        self.assertEqual(mod.truncate_title("x" * 100), "x" * 100)
        long_title = mod.truncate_title("y" * 200)
        self.assertEqual(long_title, "y" * 120 + "...")
        self.assertEqual(len(long_title), 123)
        self.assertEqual(mod.truncate_title("  a \n b  "), "a b")
        # endpoint 提取
        self.assertEqual(
            mod.endpoint_of("http://skywalking-oap.example.internal:12800/graphql"),
            "skywalking-oap.example.internal:12800/graphql")
        self.assertEqual(mod.endpoint_of("http://oap.internal/graphql"),
                         "oap.internal/graphql")
        # duration 解析：CLI 覆盖 > 配置 > 默认
        self.assertEqual(mod.resolve_duration("minutes:30", {"duration": "minutes:60"}), "minutes:30")
        self.assertEqual(mod.resolve_duration(None, {"duration": "minutes:60"}), "minutes:60")
        self.assertEqual(mod.resolve_duration(None, {}), "minutes:60")
        self.assertEqual(mod.resolve_duration("  ", {"duration": ""}), "minutes:60")


if __name__ == "__main__":
    unittest.main()
