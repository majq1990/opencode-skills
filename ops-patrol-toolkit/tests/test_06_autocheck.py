#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""06_autocheck_triage 测试。

覆盖：预警表达式安全求值（gt/lt 数字、eq 字符串、and/or 组合、千分位、abs、
CURTIME30、解析失败按告警保守处理）；指标键解析（4 段无 wiki / 5 段有 wiki /
表达式空不告警）；单位格式化（B 系列/UNIXTIME/FLOAT/NO_FORMAT/默认+单位）；
WIKI 链接构造；fixture 端到端（2 主机多 topic，告警项/剧本匹配/报告产出）；
--metrics/--playbooks 精确层优先命中；缺文件/JSON 损坏/结构不识别 gap 退出码 2。

unittest 风格，pytest 兼容；全离线；临时产物只写 work/test_tmp/autocheck/。
"""

import contextlib
import importlib
import io
import json
import shutil
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "patrol" / "autocheck"
TMP = ROOT / "work" / "test_tmp" / "autocheck"

sys.path.insert(0, str(SCRIPTS))

import patrol_lib  # noqa: E402

# 脚本名以数字开头不能用常规 import 语法，走 importlib
triage06 = importlib.import_module("06_autocheck_triage")  # noqa: E402

FIXTURE_REPORT = FIXTURES / "report_fixture.json"

# 真实 auto-check 指标键样例（取自 D:/git/auto-check 角色脚本，脱敏沿用）
K_CPU = "01:cpu_used%:%:DATA_gt_60:#4864"
K_IDLE = "01:cpu_idle::lt_95:9744"
K_LOAD = "02:cpu_loadavg1::DATA_gt_10:#4864"
K_FSTAB = "07:fstab::WRAPDATA_eq__quot_ERROR_quot_:#9776"
K_CLOCK = "05:clock_diff:s:abs_lbc_DATA_rbc_gt_10:#9775"
K_MAXMEM = "04:maxmemory:B:DATA_lt_3221225472_and_DATA_ne_0:#5027"
K_OR = "01:z::DATA_lt_1_or_DATA_gt_10"
K_AND = "01:y::DATA_gt_10_and_DATA_lt_20"
K_STATUS = "03:check_status_code::WRAPDATA_ne__quot_TCP_quot__and_DATA_ne_200:#9786"
K_NE0 = "01:count::DATA_eq_0:#17730"
K_STATE400 = "02:状态::WRAPDATA_lt__quot_400_quot_:#18679"
K_THREADVAR = "03:总线程数::WRAPDATA_gt__quot_${THREAD_TOTAL_MAX}_quot_"
K_NEXTFIRE = "08:next_fire_time::WRAPDATA_lt_CURTIME30:#10003"
K_PAREN = "01:x::_lbc_DATA_gt_5"
K_USED_MEM = "01:used_memory:B:DATA_gt_3221225472:#5027"


def _last_json(text):
    return json.loads(text.strip().splitlines()[-1])


def _call(argv):
    """运行 CLI，返回 (rc, stdout_text)。gap 路径的 SystemExit 由用例自行断言。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = triage06.main(list(argv))
    return rc, buf.getvalue()


class TestExprEval(unittest.TestCase):
    """预警表达式求值：check_by_key 安全复刻参考实现（无表达式 False，异常 True）。"""

    def test_numeric_gt_lt(self):
        self.assertTrue(triage06.check_by_key("95.3", K_CPU))
        self.assertFalse(triage06.check_by_key("30", K_CPU))
        self.assertTrue(triage06.check_by_key("32.5", K_IDLE))   # 32.5 < 95 → 告警
        self.assertFalse(triage06.check_by_key("96.0", K_IDLE))
        self.assertFalse(triage06.check_by_key("2.5", K_LOAD))

    def test_string_eq_and_quoted_numeric_threshold(self):
        self.assertFalse(triage06.check_by_key("OK", K_FSTAB))
        self.assertTrue(triage06.check_by_key("ERROR", K_FSTAB))
        # 数值型数据时带引号纯数字阈值去引号做数值比较（参考实现 re.sub 行为）
        self.assertTrue(triage06.check_by_key("398", K_STATE400))
        self.assertFalse(triage06.check_by_key("500", K_STATE400))

    def test_and_or_combination(self):
        self.assertTrue(triage06.check_by_key("15", K_AND))
        self.assertFalse(triage06.check_by_key("25", K_AND))
        self.assertFalse(triage06.check_by_key("5", K_AND))
        self.assertTrue(triage06.check_by_key("50", K_OR))
        self.assertFalse(triage06.check_by_key("5", K_OR))
        self.assertTrue(triage06.check_by_key("0", K_OR))

    def test_thousand_separator_value(self):
        self.assertTrue(triage06.check_by_key("1,234.5", "01:n::DATA_gt_1000"))
        self.assertFalse(triage06.check_by_key("999", "01:n::DATA_gt_1000"))
        self.assertTrue(triage06.check_by_key("12,345", "01:n::DATA_gt_10000"))

    def test_abs_and_curtime30(self):
        self.assertFalse(triage06.check_by_key("0.35", K_CLOCK))
        self.assertTrue(triage06.check_by_key("15.2", K_CLOCK))
        self.assertFalse(triage06.check_by_key("-3", K_CLOCK))  # abs(-3)=3，不大于 10
        self.assertTrue(triage06.check_by_key("2020-01-01 00:00:00", K_NEXTFIRE))
        self.assertFalse(triage06.check_by_key("2999-01-01 00:00:00", K_NEXTFIRE))
        # 非时间字符串按字符串比较（"N" > "2"），与参考实现 eval 行为一致
        self.assertFalse(triage06.check_by_key("NO_A_TIME", K_NEXTFIRE))

    def test_parse_failure_alerts(self):
        # 真实键：解码残留裸标识符（HTTP/TCP），参考实现 eval 异常→True，本实现同样告警
        self.assertTrue(triage06.check_by_key("HTTP", K_STATUS))
        self.assertTrue(triage06.check_by_key("TCP", K_STATUS))
        # DATA_eq_0 解码为 "5 ==0"（合法），与参考实现一致：0 告警、5 不告警
        self.assertTrue(triage06.check_by_key("0", K_NE0))
        self.assertFalse(triage06.check_by_key("5", K_NE0))
        self.assertTrue(triage06.check_by_key("10", K_PAREN))    # 缺右括号
        self.assertTrue(triage06.check_by_key("120", K_THREADVAR))  # 数值比字符串 → 类型错
        # 阈值含未展开变量同样保守告警
        self.assertTrue(triage06.check_by_key("NO", "01:s::WRAPDATA_ne__quot_YES_quot_"))
        self.assertFalse(triage06.check_by_key("YES", "01:s::WRAPDATA_ne__quot_YES_quot_"))

    def test_no_expr_never_alerts(self):
        self.assertFalse(triage06.check_by_key("999999", "01:cpu_processors"))
        self.assertFalse(triage06.check_by_key("8.0.32", "03:version::"))
        self.assertEqual(triage06.decode_expr("999", "01:cpu_processors"), "")

    def test_safe_eval_forbidden_ops(self):
        """求值器白名单外一律拒绝：不允许调用/属性/下标等逃逸面。"""
        for bad in ("__import__('os')", "1 if True else 2", "[1][0]", "abs(1) or eval('1')"):
            with self.assertRaises(triage06.ExprError):
                triage06.safe_eval(bad)
        self.assertEqual(triage06.safe_eval("abs(-5) > 3"), True)
        self.assertEqual(triage06.safe_eval('"a" != "b" and 1 < 2'), True)


class TestKeyParse(unittest.TestCase):
    def test_key_parse_4_and_5_parts(self):
        info = triage06.parse_metric_key(K_LOAD)
        self.assertEqual(info["seq"], "02")
        self.assertEqual(info["name"], "cpu_loadavg1")
        self.assertEqual(info["unit"], "")
        self.assertEqual(info["expr"], "DATA_gt_10")
        self.assertEqual(info["wiki"], "4864")

        info4 = triage06.parse_metric_key("01:count::DATA_eq_0")
        self.assertEqual(info4["wiki"], "")
        self.assertEqual(info4["unit"], "")

        info_digit = triage06.parse_metric_key(K_IDLE)  # 锚点无 # 前缀的纯数字形式
        self.assertEqual(info_digit["wiki"], "9744")

        self.assertEqual(triage06.parse_metric_key("00:access_to_internet")["name"],
                         "access_to_internet")  # 2 段也认（无单位/表达式）
        self.assertIsNone(triage06.parse_metric_key("plain_key"))  # 无冒号不是指标键

    def test_wiki_url(self):
        self.assertEqual(triage06.wiki_url(K_CPU),
                         "http://faq.egova.com.cn:7777/projects/redmine/wiki/4864")
        self.assertEqual(triage06.wiki_url(K_IDLE),
                         "http://faq.egova.com.cn:7777/projects/redmine/wiki/9744")
        self.assertEqual(triage06.wiki_url("01:count::DATA_eq_0"), "")
        self.assertEqual(triage06.wiki_url("07:slave_delay::DATA_gt_10000:#9845:"),
                         "http://faq.egova.com.cn:7777/projects/redmine/wiki/9845")

    def test_topic_display(self):
        self.assertEqual(triage06.topic_display("01:cpu"), "cpu")
        self.assertEqual(triage06.topic_display("03:disk"), "disk")
        self.assertEqual(triage06.topic_display("plain"), "plain")


class TestFormat(unittest.TestCase):
    def test_format_size_b_series(self):
        f = triage06.format_size
        self.assertEqual(f(3221225472.0, "B"), "3.00GB")
        self.assertEqual(f(500.0, "KB"), "500.00KB")
        self.assertEqual(f(2048.0, "MB"), "2.00GB")
        self.assertEqual(f(1024.0, "B"), "1024.00B")  # 边界：>1024 才进位
        self.assertEqual(f(16333088.0, "KB"), "15.58GB")

    def test_format_by_key_units(self):
        self.assertEqual(triage06.format_by_key("OK", K_FSTAB), "OK")  # NO_FORMAT
        self.assertEqual(triage06.format_by_key("95.3", K_CPU), "95.3%")
        self.assertEqual(triage06.format_by_key("95.3", "01:x:FLOAT:DATA_gt_10"), "95.30")
        self.assertEqual(triage06.format_by_key("4294967296", K_USED_MEM), "4.00GB")
        self.assertEqual(triage06.format_by_key("35000", "01:n"), "35,000")
        # 参考实现怪癖：带小数走 '{:,}'.format(str) 必抛 → 原样返回
        self.assertEqual(triage06.format_by_key("32.5", "01:n"), "32.5")
        expected = datetime.fromtimestamp(0).strftime("%Y-%m-%d %H:%M:%S")
        self.assertEqual(triage06.format_by_key("0", "01:t:UNIXTIME"), expected)
        self.assertEqual(triage06.format_by_key("bad", "01:t:UNIXTIME"), "bad")

    def test_human_threshold(self):
        self.assertEqual(triage06.human_threshold(K_IDLE), "值 < 95")
        self.assertEqual(triage06.human_threshold("01:x:%:DATA_gt_60"), "值 > 60%")
        self.assertEqual(triage06.human_threshold(K_USED_MEM), "值 > 3.00GB")
        self.assertEqual(triage06.human_threshold(K_FSTAB), '值 == "ERROR"')
        self.assertIn("当前时间-30分钟", triage06.human_threshold(K_NEXTFIRE))
        self.assertEqual(triage06.human_threshold("01:cpu_processors"), "")


class TestPlaybookMatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TMP.mkdir(parents=True, exist_ok=True)
        cls.pb_file = TMP / "pb_custom.json"
        cls.pb_file.write_text(json.dumps({
            "version": "t1",
            "playbooks": [{
                "metric_names": ["cpu_used%"],
                "title": "CPU 专项处置",
                "severity_hint": "critical",
                "steps": ["专用步骤：按 CPU 专项手册处理"]
            }]
        }, ensure_ascii=False), encoding="utf-8")
        cls.metric_file = TMP / "metrics_custom.json"
        cls.metric_file.write_text(json.dumps({
            "version": "t1",
            "metrics": {
                "swap_used%": {"title": "Swap 专项目录", "severity_hint": "medium",
                                "steps": ["Swap 专项步骤一"]}
            }
        }, ensure_ascii=False), encoding="utf-8")
        cls.custom = triage06.load_playbook_layer(cls.pb_file, "pb", [])
        cls.metrics = triage06.load_playbook_layer(cls.metric_file, "metrics", [])

    def test_custom_playbooks_exact_wins(self):
        entry, source = triage06.match_playbook(K_CPU, self.custom, self.metrics, [])
        self.assertEqual(source, "playbooks(精确)")
        self.assertEqual(entry["severity_hint"], "critical")
        self.assertIn("专用步骤", entry["steps"][0])
        # 未配置精确名的指标不受影响，继续走 common
        entry2, source2 = triage06.match_playbook(
            "01:memory_used%:%:DATA_gt_98:#4891", self.custom, self.metrics,
            triage06.load_common_playbooks(
                str(ROOT / "references" / "playbooks" / "common_playbooks.json"), []))
        self.assertTrue(source2.startswith("common("))
        self.assertEqual(entry2["title"], "内存使用率过高/OOM 风险")

    def test_metrics_layer_and_priority_over_common(self):
        entry, source = triage06.match_playbook(
            "04:swap_used%:%:DATA_gt_90:#4891", self.custom, self.metrics, [])
        self.assertEqual(source, "metrics(精确)")
        self.assertEqual(entry["severity_hint"], "medium")
        self.assertIn("Swap 专项步骤一", entry["steps"][0])

    def test_fallback_steps_content(self):
        common = triage06.load_common_playbooks(
            str(ROOT / "references" / "playbooks" / "common_playbooks.json"), [])
        entry, source = triage06.match_playbook("02:TIME_WAIT::DATA_gt_5000:#9779",
                                                None, None, common)
        self.assertEqual(source, "fallback")
        joined = " ".join(entry["steps"])
        self.assertIn("05_kb_similar_search", joined)
        self.assertIn("确认现象与影响范围", joined)
        # common 关键词命中示例：inode → disk_usage_high
        entry2, source2 = triage06.match_playbook(
            "05:inode_available::DATA_lt_100000:#4908", None, None, common)
        self.assertTrue(source2.startswith("common(inode"))
        self.assertEqual(entry2["title"], "磁盘空间/ inode 不足")


class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TMP.mkdir(parents=True, exist_ok=True)

    def test_fixture_e2e_report_and_envelope(self):
        out = TMP / "e2e.md"
        rc, text = _call(["triage", "--report", str(FIXTURE_REPORT), "--out", str(out)])
        self.assertEqual(rc, 0)
        env = _last_json(text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["files"], 1)
        self.assertEqual(env["hosts"], 2)
        self.assertEqual(env["topics"], 7)
        self.assertEqual(env["alert_items"], 10)
        self.assertEqual(env["by_severity"], {"high": 8, "warn": 2})
        self.assertEqual(env["warnings"], [])

        rep = out.read_text(encoding="utf-8")
        self.assertIn("【待复核】", rep)
        self.assertIn("os_node_demo1", rep)
        self.assertIn("mysql_node_demo1", rep)
        self.assertIn("cpu_used%", rep)
        self.assertIn("95.3%", rep)
        self.assertIn("值 > 60%", rep)
        self.assertIn("3.00GB", rep)                     # B 系列阈值人读
        self.assertIn("值 > 3.00GB", rep)
        self.assertIn("CPU 使用率/负载过高", rep)          # common 剧本命中
        self.assertIn("MySQL 连接数接近/达到上限", rep)
        self.assertIn("wiki/4864", rep)
        self.assertIn("/egova/data", rep)                # 多行 topic 的行标识
        self.assertIn("05_kb_similar_search", rep)       # 兜底步骤示例命令
        self.assertNotIn("无告警项", rep)

    def test_layer_flags_change_output(self):
        out = TMP / "e2e_layers.md"
        argv = ["triage", "--report", str(FIXTURE_REPORT),
                "--playbooks", str(TMP / "pb_custom.json"),
                "--metrics", str(TMP / "metrics_custom.json"),
                "--out", str(out)]
        rc, text = _call(argv)
        self.assertEqual(rc, 0)
        env = _last_json(text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["by_severity"]["critical"], 1)  # cpu_used% 被专属剧本改为 critical
        self.assertEqual(env["by_severity"]["medium"], 1)    # swap_used% 被指标目录改为 medium
        self.assertEqual(env["by_severity"]["high"], 6)      # 其余 8 个 high 中 2 个被改层
        self.assertEqual(env["by_severity"]["warn"], 2)
        rep = out.read_text(encoding="utf-8")
        self.assertIn("CPU 专项处置", rep)
        self.assertIn("专用步骤", rep)
        self.assertIn("Swap 专项目录", rep)

    def test_dir_collection_with_bad_file_warning(self):
        d = TMP / "dirscan"
        d.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(FIXTURE_REPORT, d / "ok_report.json")
        (d / "bad_structure.json").write_text(json.dumps({"foo": 1}), encoding="utf-8")
        (d / "not_json.txt").write_text("ignored", encoding="utf-8")  # 非 json 不收
        out = TMP / "e2e_dir.md"
        rc, text = _call(["triage", "--dir", str(d), "--out", str(out)])
        self.assertEqual(rc, 0)
        env = _last_json(text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["files"], 2)
        self.assertEqual(env["hosts"], 2)
        self.assertTrue(any("bad_structure.json" in w for w in env["warnings"]))
        self.assertEqual(env["alert_items"], 10)

    def test_no_alert_report(self):
        d = TMP / "noalert"
        d.mkdir(parents=True, exist_ok=True)
        quiet = {"os_demo2": {"version": "1", "report_time": "2026-10-07 03:00:00",
                              "data": {"basic": {"01:hostname": "demo-2"},
                                       "topics": {"01:cpu": [
                                           {"01:cpu_used%:%:DATA_gt_60:#4864": "20.0"}]}}}}
        (d / "quiet.json").write_text(json.dumps(quiet, ensure_ascii=False), encoding="utf-8")
        out = TMP / "e2e_quiet.md"
        rc, text = _call(["triage", "--dir", str(d), "--out", str(out)])
        self.assertEqual(rc, 0)
        env = _last_json(text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["alert_items"], 0)
        self.assertEqual(env["by_severity"], {})
        rep = out.read_text(encoding="utf-8")
        self.assertIn("无告警项", rep)

    def test_missing_report_gap_exit_2(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                triage06.main(["triage", "--report", str(TMP / "no_such_report.json"),
                               "--out", str(TMP / "gap1.md")])
        self.assertEqual(cm.exception.code, 2)
        env = _last_json(buf.getvalue())
        self.assertFalse(env["ok"])
        self.assertIn("no_such_report.json", env["gap"])

    def test_corrupt_json_gap_exit_2(self):
        p = TMP / "corrupt.json"
        p.write_text('{"os_x": {"version": "1", "data": ', encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                triage06.main(["triage", "--report", str(p), "--out", str(TMP / "gap2.md")])
        self.assertEqual(cm.exception.code, 2)
        env = _last_json(buf.getvalue())
        self.assertFalse(env["ok"])
        self.assertTrue(env["gap"])

    def test_unrecognized_structure_gap_exit_2(self):
        p = TMP / "alien.json"
        p.write_text(json.dumps({"hello": "world"}), encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                triage06.main(["triage", "--report", str(p), "--out", str(TMP / "gap3.md")])
        self.assertEqual(cm.exception.code, 2)
        env = _last_json(buf.getvalue())
        self.assertFalse(env["ok"])
        self.assertIn("auto-check", env["gap"])

    def test_no_input_gap(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                triage06.main(["triage"])
        self.assertEqual(cm.exception.code, 2)
        env = _last_json(buf.getvalue())
        self.assertFalse(env["ok"])
        self.assertIn("--report", env["gap"])


class TestScanDetails(unittest.TestCase):
    def test_nested_dict_and_row_label(self):
        with open(FIXTURE_REPORT, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        warnings = []
        blocks = triage06.parse_report_blocks(data, "report_fixture.json", warnings)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(warnings, [])
        block = blocks[0]
        common = triage06.load_common_playbooks(
            str(ROOT / "references" / "playbooks" / "common_playbooks.json"), [])
        alerts, topics = triage06.scan_block(block, None, None, common)
        self.assertEqual(topics, 4)
        names = [a["name"] for a in alerts]
        self.assertIn("TIME_WAIT", names)          # 嵌套 dict 下钻命中
        self.assertIn("cpu_used%", names)
        self.assertIn("inode_available", names)
        self.assertNotIn("tcpconnection", names)   # 父键无表达式不告警
        disk = [a for a in alerts if a["name"] == "inode_available"][0]
        self.assertEqual(disk["row_label"], "/egova/data")
        self.assertEqual(disk["playbook_title"], "磁盘空间/ inode 不足")
        cpu = [a for a in alerts if a["name"] == "cpu_used%"][0]
        self.assertEqual(cpu["severity"], "high")
        self.assertEqual(cpu["wiki"],
                         "http://faq.egova.com.cn:7777/projects/redmine/wiki/4864")
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
