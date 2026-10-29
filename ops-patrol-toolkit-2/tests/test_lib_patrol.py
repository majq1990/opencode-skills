#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patrol_lib 公共库测试。"""

import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import patrol_lib  # noqa: E402


class TestParseArgs(unittest.TestCase):
    def test_key_value_and_flag(self):
        a = patrol_lib.parse_args(["--out", "x.xlsx", "--yes", "--dry-run"])
        self.assertEqual(a["out"], "x.xlsx")
        self.assertTrue(a["yes"])
        self.assertTrue(a["dry_run"])

    def test_eq_form_and_kebab(self):
        a = patrol_lib.parse_args(["--max-rows=5"])
        self.assertEqual(a["max_rows"], "5")

    def test_positional(self):
        a = patrol_lib.parse_args(["a.txt", "--stdin"])
        self.assertEqual(a["_pos"], ["a.txt"])
        self.assertTrue(a["stdin"])

    def test_defaults_preserved(self):
        a = patrol_lib.parse_args([], defaults={"top": 10})
        self.assertEqual(a["top"], 10)


class TestEnvelope(unittest.TestCase):
    def test_emit_ok_true(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            patrol_lib.emit({"rows": 3})
        payload = json.loads(buf.getvalue().strip().splitlines()[-1])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["rows"], 3)

    def test_stop_exit_2(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                patrol_lib.stop("缺配置")
        self.assertEqual(cm.exception.code, 2)
        payload = json.loads(buf.getvalue().strip().splitlines()[-1])
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["gap"], "缺配置")

    def test_require_missing(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                patrol_lib.require({"out": ""}, "out", "file")


class TestJsonIo(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(os.path.join(patrol_lib.WORK_DIR, "test_tmp"))
        self.tmp.mkdir(parents=True, exist_ok=True)

    def test_read_write_json(self):
        p = self.tmp / "a.json"
        patrol_lib.write_json(p, {"a": "中文", "n": 1})
        self.assertEqual(patrol_lib.read_json(p)["a"], "中文")

    def test_read_json_missing_stops(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                patrol_lib.read_json(self.tmp / "no_such.json")

    def test_to_float(self):
        self.assertEqual(patrol_lib.to_float("1.5"), 1.5)
        self.assertEqual(patrol_lib.to_float(None), 0.0)
        self.assertEqual(patrol_lib.to_float("abc", 9.0), 9.0)

    def test_as_bool(self):
        self.assertTrue(patrol_lib.as_bool("yes"))
        self.assertTrue(patrol_lib.as_bool(True))
        self.assertFalse(patrol_lib.as_bool("no"))
        self.assertFalse(patrol_lib.as_bool(None))


class TestKeywordHit(unittest.TestCase):
    """处置剧本关键词边界感知命中（06-09 共用）。"""

    def test_ascii_left_boundary_blocks_midword(self):
        self.assertFalse(patrol_lib.keyword_hit("io", "mysql replication delay"))  # 词中 io 不命中
        self.assertFalse(patrol_lib.keyword_hit("port", "export-worker timeout"))  # 词中 port 不命中
        self.assertFalse(patrol_lib.keyword_hit("port", "EXPORT blocked"))  # 全大写词中同样拦截
        self.assertTrue(patrol_lib.keyword_hit("io", "disk io high"))
        self.assertTrue(patrol_lib.keyword_hit("port", "port 8080 exposed"))

    def test_camelcase_hump_allowed(self):
        self.assertTrue(patrol_lib.keyword_hit("cpu", "HighCpuLoad"))  # Cpu 驼峰词首命中
        self.assertTrue(patrol_lib.keyword_hit("load", "HighCpuLoad"))  # Load 驼峰词首命中
        self.assertTrue(patrol_lib.keyword_hit("memory", "HighMemoryUsage"))

    def test_ascii_right_extension_allowed(self):
        self.assertTrue(patrol_lib.keyword_hit("connection", "too many connections"))
        self.assertTrue(patrol_lib.keyword_hit("mem", "memory usage 95%"))
        self.assertTrue(patrol_lib.keyword_hit("cpu", "cpu usage high"))

    def test_left_boundary_allows_start_and_punct(self):
        self.assertTrue(patrol_lib.keyword_hit("io", "io等待过高"))
        self.assertTrue(patrol_lib.keyword_hit("io", "mysql_io_test"))  # 下划线视为分隔
        self.assertTrue(patrol_lib.keyword_hit("tomcat", "tomcat-thread-pool: 98%"))
        self.assertTrue(patrol_lib.keyword_hit("down", "service is DOWN"))

    def test_chinese_contains(self):
        self.assertTrue(patrol_lib.keyword_hit("磁盘", "磁盘空间不足"))
        self.assertTrue(patrol_lib.keyword_hit("慢查询", "存在慢查询堆积"))
        self.assertFalse(patrol_lib.keyword_hit("磁盘", "memory high"))

    def test_empty_and_case(self):
        self.assertFalse(patrol_lib.keyword_hit("", "anything"))
        self.assertFalse(patrol_lib.keyword_hit(None, "anything"))
        self.assertTrue(patrol_lib.keyword_hit("CPU", "cpu load 99%"))


if __name__ == "__main__":
    unittest.main()
