#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""04_monthly_report 测试。

覆盖：check-servers 用内置 http.server（127.0.0.1 随机端口）验证 200/404/
拒绝连接三类观测与 expect_status 判定、结果 JSON 落盘、网络异常不算脚本失败
（全失败仍 ok:true 且 failed==total）、targets 为空/缺 url 的 gap；fill 用
入库合成模板 + fixture stats 验证全命中、未命中报 unresolved_placeholders
（【待复核】口径）、模板原件不被改写、--config 兜底模板/输出/默认替换值
（stats 显式值优先）、模板缺失/ stats 结构非法/单元格越界的 gap（退出码 2）。

unittest 风格，pytest 兼容；全部离线（HTTP 用本地 http.server，不访问外网）；
测试临时产物只写 work/test_tmp/monthly/。fixture 数据全部虚构，不含真实
区域/客户/项目名/IP。
"""

import contextlib
import importlib
import io
import json
import socket
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "patrol" / "monthly"
ASSETS = ROOT / "assets"
TMP = ROOT / "work" / "test_tmp" / "monthly"

sys.path.insert(0, str(SCRIPTS))

import docx_io  # noqa: E402

# 脚本名以数字开头不能用常规 import 语法，走 importlib
tool04 = importlib.import_module("04_monthly_report")  # noqa: E402

TEMPLATE = ASSETS / "monthly-report-template.docx"

# 与入库模板 assets/monthly-report-template.docx 的生成口径一致（校验用）
TPL_PLACEHOLDERS = [
    "{{project_name}}", "{{month}}", "{{author}}", "{{report_date}}",
    "{{summary}}", "{{target_total}}", "{{target_ok}}", "{{target_failed}}",
    "{{availability}}", "{{tickets_total}}", "{{tickets_closed}}",
    "{{incidents_total}}", "{{issues}}",
]


# ---------------------------------------------------------------------------
# CLI 调用辅助
# ---------------------------------------------------------------------------

def _last_json(text):
    return json.loads(text.strip().splitlines()[-1])


def _call(argv):
    """运行 CLI，返回 (rc, stdout_text)。stop() 的 SystemExit 捕获为 rc=2。"""
    buf = io.StringIO()
    rc = None
    try:
        with contextlib.redirect_stdout(buf):
            rc = tool04.main(list(argv))
    except SystemExit as e:
        rc = e.code
    return rc, buf.getvalue()


def _write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return path


# ---------------------------------------------------------------------------
# 本地 HTTP 服务（离线巡检目标）
# ---------------------------------------------------------------------------

class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/ok":
            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            body = b"no"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, *args):  # 静默访问日志
        pass


def _free_port():
    """借一个空闲 TCP 端口后立即释放，用于构造"拒绝连接"目标。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Test04CheckServers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TMP.mkdir(parents=True, exist_ok=True)
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.port = cls.httpd.server_address[1]
        cls.base = "http://127.0.0.1:%d" % cls.port
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.closed_port = _free_port()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    # -- 200/404 与 expect_status 判定 ------------------------------------

    def test_01_check_200_and_404_envelope_and_file(self):
        """200 判正常、404 判异常（error 说明状态码不符）；信封与落盘 JSON 一致。"""
        cfg = _write_json(TMP / "servers_ok404.json", {
            "version": "1.0",
            "note": "运行期合成配置，目标为本测试的本地 http.server。",
            "timeout_s": 3,
            "targets": [
                {"name": "本地健康检查", "url": self.base + "/ok", "expect_status": 200},
                {"name": "本地缺失页", "url": self.base + "/missing", "expect_status": 200},
            ],
        })
        out = TMP / "servers_ok404_result.json"
        rc, out_text = _call(["check-servers", "--config", str(cfg), "--out", str(out)])
        self.assertEqual(rc, 0)
        env = _last_json(out_text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 2)
        self.assertEqual(env["failed"], 1)
        r_ok, r_404 = env["results"]
        self.assertTrue(r_ok["ok"])
        self.assertEqual(r_ok["status"], 200)
        self.assertIsNone(r_ok["error"])
        self.assertFalse(r_404["ok"])
        self.assertEqual(r_404["status"], 404)
        self.assertIn("200", r_404["error"])  # 与期望 200 不符
        self.assertTrue(all(isinstance(r["elapsed_ms"], int) for r in env["results"]))
        # 落盘文件可读回且 results 口径一致
        self.assertTrue(out.exists())
        saved = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(saved["results"], env["results"])
        self.assertEqual(saved["total"], 2)
        self.assertEqual(saved["failed"], 1)

    def test_02_expect_status_404_is_ok(self):
        """expect_status: 404 时访问 /missing（实际 404）判正常。"""
        cfg = _write_json(TMP / "servers_expect404.json", {
            "targets": [{"name": "预期404", "url": self.base + "/missing",
                         "expect_status": 404}],
        })
        rc, out_text = _call(["check-servers", "--config", str(cfg),
                              "--out", str(TMP / "servers_expect404_result.json")])
        self.assertEqual(rc, 0)
        env = _last_json(out_text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["failed"], 0)
        self.assertTrue(env["results"][0]["ok"])
        self.assertEqual(env["results"][0]["status"], 404)

    # -- 拒绝连接：单目标失败进 results，不算脚本失败 ----------------------

    def test_03_refused_connection_and_all_failed(self):
        """拒绝连接 -> status 0 + error；全部目标失败时信封仍 ok:true 且 failed==total。"""
        cfg = _write_json(TMP / "servers_refused.json", {
            "targets": [
                {"name": "无监听端口A", "url": "http://127.0.0.1:%d/" % self.closed_port,
                 "expect_status": 200},
                {"name": "无监听端口B", "url": "http://127.0.0.1:%d/health" % self.closed_port,
                 "expect_status": 200},
            ],
        })
        rc, out_text = _call(["check-servers", "--config", str(cfg),
                              "--out", str(TMP / "servers_refused_result.json"),
                              "--timeout", "2"])
        self.assertEqual(rc, 0)  # 网络异常不是脚本失败
        env = _last_json(out_text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total"], 2)
        self.assertEqual(env["failed"], 2)  # 全部失败仍 ok:true
        for r in env["results"]:
            self.assertFalse(r["ok"])
            self.assertEqual(r["status"], 0)
            self.assertTrue(r["error"])

    # -- 配置缺失/为空 -> gap（退出码 2） ---------------------------------

    def test_04_empty_targets_gap(self):
        """targets 为空数组 -> gap 信封，退出码 2。"""
        cfg = _write_json(TMP / "servers_empty.json", {"targets": []})
        rc, out_text = _call(["check-servers", "--config", str(cfg)])
        self.assertEqual(rc, 2)
        env = _last_json(out_text)
        self.assertFalse(env["ok"])
        self.assertIn("targets", env["gap"])

    def test_05_target_missing_url_gap(self):
        """targets 某条缺 url -> gap 信封，退出码 2（第几条可定位）。"""
        cfg = _write_json(TMP / "servers_nourl.json", {
            "targets": [{"name": "无url条目"}],
        })
        rc, out_text = _call(["check-servers", "--config", str(cfg)])
        self.assertEqual(rc, 2)
        env = _last_json(out_text)
        self.assertFalse(env["ok"])
        self.assertIn("url", env["gap"])
        self.assertIn("1", env["gap"])


class Test04Fill(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TMP.mkdir(parents=True, exist_ok=True)
        # 入库模板存在且占位符齐全（模板与 fixtures/stats_fixture.json 配套）
        assert TEMPLATE.is_file(), "缺少入库模板 assets/monthly-report-template.docx"
        paras = docx_io.read_paragraphs(str(TEMPLATE))
        tables = docx_io.read_tables(str(TEMPLATE))
        tpl_text = "\n".join(p["text"] for p in paras)
        tpl_text += "\n" + "\n".join(
            c for grid in tables for row in grid for c in row)
        for ph in TPL_PLACEHOLDERS:
            assert ph in tpl_text, "模板缺占位符 %s" % ph
        assert len(tables) == 1, "模板应有且仅有 1 张统计表格"
        assert tables[0][1][1] == "{{availability}}"

    # -- 全命中回填 ---------------------------------------------------------

    def test_06_fill_full_hits(self):
        """fixture stats 全命中：misses 为空、信封无 unresolved_placeholders、
        段落与单元格回填正确（含 cells 覆写可用率）。"""
        out = TMP / "月报_full.docx"
        rc, out_text = _call(["fill", "--template", str(TEMPLATE),
                              "--stats", str(FIXTURES / "stats_fixture.json"),
                              "--out", str(out)])
        self.assertEqual(rc, 0)
        env = _last_json(out_text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["misses"], [])
        self.assertNotIn("unresolved_placeholders", env)
        self.assertNotIn("review_required", env)
        self.assertNotIn("leftover_placeholders", env)  # 输出无任何残留 {{...}}
        self.assertEqual(env["replacements_hit"], 12)
        self.assertEqual(env["cells_written"], 1)
        self.assertEqual(env["month"], "2026-09")
        self.assertTrue(Path(env["output"]).exists())
        paras = docx_io.read_paragraphs(str(out))
        self.assertEqual(paras[0]["text"], "示例园区月度运维报告")
        self.assertTrue(any("报告月份：2026-09" in p["text"] for p in paras))
        self.assertTrue(any("正常 1 个，异常 2 个" in p["text"] for p in paras))
        tables = docx_io.read_tables(str(out))
        self.assertEqual(tables[0][1], ["系统可用率", "99.95%"])  # cells 覆写
        self.assertEqual(tables[0][2], ["受理工单总数", "42"])    # replacements 命中表格内段落

    # -- 未命中占位 -> unresolved_placeholders +【待复核】 ------------------

    def test_07_fill_misses_reported(self):
        """占位符未命中：信封带 unresolved_placeholders/review_required，正文提示待复核。"""
        out = TMP / "月报_partial.docx"
        rc, out_text = _call(["fill", "--template", str(TEMPLATE),
                              "--stats", str(FIXTURES / "stats_fixture_partial.json"),
                              "--out", str(out)])
        self.assertEqual(rc, 0)
        env = _last_json(out_text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["unresolved_placeholders"], ["{{no_such_placeholder}}"])
        self.assertTrue(env["review_required"])
        self.assertIn("{{month}}", env["leftover_placeholders"])  # 输出残留模板占位符
        self.assertIn("{{no_such_placeholder}}", out_text)
        self.assertIn("【待复核】", out_text)

    # -- 模板原件不动 --------------------------------------------------------

    def test_08_template_untouched_after_fill(self):
        """回填后再次读模板：占位符原样保留，模板未被改写。"""
        out = TMP / "月报_t0.docx"
        rc, _ = _call(["fill", "--template", str(TEMPLATE),
                       "--stats", str(FIXTURES / "stats_fixture.json"),
                       "--out", str(out)])
        self.assertEqual(rc, 0)
        tpl_text = "\n".join(p["text"] for p in docx_io.read_paragraphs(str(TEMPLATE)))
        self.assertIn("{{project_name}}", tpl_text)
        self.assertIn("{{summary}}", tpl_text)
        tables = docx_io.read_tables(str(TEMPLATE))
        self.assertEqual(tables[0][1][1], "{{availability}}")

    # -- --config 兜底（模板/输出/默认替换值） ------------------------------

    def test_09_config_defaults_and_stats_priority(self):
        """--config 提供 template/out_dir/out_name/defaults：免 --template/--out 可跑；
        defaults.replacements 对 stats 未提供的键生效，stats 显式值优先于 defaults 同名键。"""
        out_dir = TMP / "cfg_out"
        cfg = _write_json(TMP / "monthly_runtime.json", {
            "template": str(TEMPLATE),
            "out_dir": str(out_dir),
            "out_name": "r09.docx",
            "defaults": {"replacements": {
                "{{author}}": "配置默认编制人",                    # 被 stats 显式值覆盖
                "{{issues}}": "配置默认问题段（stats 未提供，应生效）",  # defaults 兜底生效
            }},
        })
        stats = _write_json(TMP / "stats_runtime.json", {
            "month": "2026-09",
            "project": "示例园区（合成样例）",
            "replacements": {"{{author}}": "stats显式编制人", "{{project_name}}": "示例园区"},
            "cells": [],
        })
        out = out_dir / "r09.docx"
        rc, out_text = _call(["fill", "--config", str(cfg), "--stats", str(stats)])
        self.assertEqual(rc, 0)
        env = _last_json(out_text)
        self.assertTrue(env["ok"])
        self.assertTrue(out.exists())
        joined = "\n".join(p["text"] for p in docx_io.read_paragraphs(str(out)))
        self.assertIn("stats显式编制人", joined)  # stats 显式值优先
        self.assertNotIn("配置默认编制人", joined)
        self.assertIn("配置默认问题段（stats 未提供，应生效）", joined)  # defaults 兜底生效
        self.assertIn("示例园区月度运维报告", joined)
        # stats 只给了 2 个键 + defaults 1 个键，模板其余占位符在输出中残留
        # -> 属"未回填占位"，按【待复核】口径暴露（区别于 misses：stats 键未命中模板）
        self.assertTrue(env["review_required"])
        self.assertEqual(env["misses"], [])
        self.assertIn("{{summary}}", env["leftover_placeholders"])
        self.assertIn("{{month}}", env["leftover_placeholders"])

    # -- 失败路径（gap，退出码 2） -------------------------------------------

    def test_10_missing_template_gap(self):
        """模板不存在 -> gap 信封，退出码 2。"""
        rc, out_text = _call(["fill", "--template", str(TMP / "no_such_template.docx"),
                              "--stats", str(FIXTURES / "stats_fixture.json"),
                              "--out", str(TMP / "月报_should_not_exist.docx")])
        self.assertEqual(rc, 2)
        env = _last_json(out_text)
        self.assertFalse(env["ok"])
        self.assertIn("模板文件不存在", env["gap"])

    def test_11_invalid_stats_gap(self):
        """stats.json 缺 replacements 键 / replacements 非对象 -> gap，退出码 2。"""
        bad1 = _write_json(TMP / "stats_no_reps.json", {"month": "2026-09"})
        rc, out_text = _call(["fill", "--template", str(TEMPLATE),
                              "--stats", str(bad1), "--out", str(TMP / "月报_bad1.docx")])
        self.assertEqual(rc, 2)
        env = _last_json(out_text)
        self.assertFalse(env["ok"])
        self.assertIn("replacements", env["gap"])

        bad2 = _write_json(TMP / "stats_reps_list.json", {"replacements": [["k", "v"]]})
        rc, out_text = _call(["fill", "--template", str(TEMPLATE),
                              "--stats", str(bad2), "--out", str(TMP / "月报_bad2.docx")])
        self.assertEqual(rc, 2)
        env = _last_json(out_text)
        self.assertFalse(env["ok"])
        self.assertIn("replacements", env["gap"])

    def test_12_cell_out_of_range_gap(self):
        """cells 表序号越界 -> DocxError 转 gap 信封，退出码 2。"""
        bad = _write_json(TMP / "stats_cell_overflow.json", {
            "replacements": {"{{project_name}}": "X"},
            "cells": [{"table": 5, "row": 0, "col": 0, "text": "y"}],
        })
        out = TMP / "月报_bad3.docx"
        rc, out_text = _call(["fill", "--template", str(TEMPLATE),
                              "--stats", str(bad), "--out", str(out)])
        self.assertEqual(rc, 2)
        env = _last_json(out_text)
        self.assertFalse(env["ok"])
        self.assertIn("表格", env["gap"])
        self.assertFalse(out.exists())  # gap 路径不产生半成品


if __name__ == "__main__":
    unittest.main()
