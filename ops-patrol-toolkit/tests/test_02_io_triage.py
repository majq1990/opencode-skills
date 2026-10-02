#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""02_mysql_io_triage 测试。

覆盖：iostat 多轮取最后一轮 + 吞吐单位自动识别（-m/-k）；digest CSV 与 JSON 双格式；
DDL 解析（大字段/无主键/索引少）；fixture 驱动的端到端 run（report.md/triage.json 产出
且 top 根因符合预期）；阈值配置外置加载；缺 iostat 时 gap 信封退出码 2。

unittest 风格，pytest 兼容；临时产物只写 work/test_tmp/io_triage/（避免与其他并行 agent 撞名）。
"""

import contextlib
import importlib
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "patrol" / "io_triage"
TMP = ROOT / "work" / "test_tmp" / "io_triage"

sys.path.insert(0, str(SCRIPTS))

import patrol_lib  # noqa: E402

# 脚本名以数字开头不能用常规 import 语法，走 importlib
triage02 = importlib.import_module("02_mysql_io_triage")  # noqa: E402


def _last_json(text):
    return json.loads(text.strip().splitlines()[-1])


def _call(argv):
    """运行 CLI 子命令，返回 (rc, stdout_text)。失败路径的 SystemExit 向上抛由用例断言。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = triage02.main(list(argv))
    return rc, buf.getvalue()


class TestIostatParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = triage02.read_text(str(FIXTURES / "iostat_sample.txt"))

    def test_multi_round_takes_last_and_unit(self):
        """多轮采样只取最后一轮；-m 单位自动识别；dm-* 不参与主压力设备竞争。"""
        p = triage02.parse_iostat(self.text)
        self.assertEqual(p["samples"], 3)
        self.assertEqual(p["unit"], "MB/s")
        agg = triage02.aggregate_devices(p["devices"])
        # 最后一轮：r/s = 7905.00 + 0.40；若误把三轮相加会得到 19405.6 之类
        self.assertAlmostEqual(agg["r_s"], 7905.4, places=2)
        self.assertAlmostEqual(agg["w_s"], 205.1, places=2)
        self.assertAlmostEqual(agg["r_mbs"], 120.5, places=2)
        # dm-0 与底层盘重复，不得成为主压力设备（聚合排除虚拟设备前缀）
        self.assertEqual(agg["hot_dev"], "vda")
        self.assertAlmostEqual(agg["hot_util"], 97.2, places=2)
        # 平均单次读 = 120.5MB/s * 1024 / 7905.4 ≈ 15.61 KB，小块随机读特征
        self.assertAlmostEqual(agg["avg_read_kb"], 15.61, places=1)
        self.assertLess(agg["avg_read_kb"], 16.0)
        # CPU 同样取最后一轮
        self.assertAlmostEqual(p["cpu"]["iowait"], 24.87, places=2)

    def test_kb_unit_auto_convert(self):
        """-k（rkB/s）单位自动识别并归一换算成 MB/s。"""
        text = (
            "avg-cpu:  %user   %nice %system %iowait  %steal   %idle\n"
            "           5.00    0.00    2.00   10.00    0.00   83.00\n"
            "\n"
            "Device:         rrqm/s   wrqm/s     r/s     w/s    rkB/s    wkB/s"
            " avgrq-sz avgqu-sz   await r_await w_await  svctm  %util\n"
            "vda                0.00    2.00   300.00    50.00  2048.00   256.00"
            "     8.00     0.50    1.00    0.80    2.00   0.50  12.00\n"
        )
        p = triage02.parse_iostat(text)
        self.assertEqual(p["unit"], "kB/s")
        agg = triage02.aggregate_devices(p["devices"])
        self.assertAlmostEqual(agg["r_mbs"], 2048.0 / 1024.0, places=6)
        self.assertAlmostEqual(agg["w_mbs"], 256.0 / 1024.0, places=6)
        # 平均单次读 = 2.0MB/s * 1024 / 300 = 2048/300 KB
        self.assertAlmostEqual(agg["avg_read_kb"], 2048.0 / 300.0, places=2)


class TestDigestParse(unittest.TestCase):
    def test_csv_and_json_dual_format(self):
        """CSV（带 BOM）与 JSON 数组两种格式解析结果一致，TOP 排序按扫描压力。"""
        csv_rows = triage02.parse_digest(triage02.read_text(str(FIXTURES / "digest_sample.csv")))
        json_rows = triage02.parse_digest(triage02.read_text(str(FIXTURES / "digest_sample.json")))
        self.assertEqual(len(csv_rows), 5)
        self.assertEqual(len(json_rows), 5)
        # BOM 兼容：CSV 首列 digest_text 能映射成 sql，而不是带 BOM 的原列名
        self.assertIn("sql", csv_rows[0])
        for rows in (csv_rows, json_rows):
            top = triage02.rank_digest(rows, 10)
            self.assertEqual(top[0]["rank"], 1)
            self.assertIn("biz_event_log", top[0]["sql"])
            self.assertAlmostEqual(top[0]["rows_examined"], 4820000000.0, places=0)
            self.assertGreater(top[0]["scan_ratio"], 100)
            self.assertGreaterEqual(top[0]["rows_examined"], top[1]["rows_examined"])
        self.assertEqual(csv_rows[0]["sql"], json_rows[0]["sql"])


class TestDdlParse(unittest.TestCase):
    def test_ddl_lob_no_pk_few_index(self):
        """大字段/大 varchar/主键有无/索引数量解析。"""
        t = triage02.parse_ddl(triage02.read_text(str(FIXTURES / "schema_sample.sql")))
        self.assertEqual(set(t), {"biz_event_log", "sys_account", "biz_event_attach"})

        log = t["biz_event_log"]
        self.assertEqual(log["lob_fields"], ["detail", "ext_data"])
        self.assertEqual(log["big_varchar"], ["remark"])
        self.assertTrue(log["has_pk"])
        self.assertEqual(len(log["indexes"]), 2)
        self.assertEqual(log["engine"], "InnoDB")
        self.assertEqual(log["row_format"], "DYNAMIC")

        attach = t["biz_event_attach"]
        self.assertFalse(attach["has_pk"])  # 无主键
        self.assertEqual(attach["lob_fields"], ["payload"])
        self.assertLessEqual(
            len(attach["indexes"]),
            triage02.load_thresholds()["ddl_bump"]["index_few_max"])  # 索引偏少

        self.assertTrue(t["sys_account"]["has_pk"])
        self.assertEqual(t["sys_account"]["lob_fields"], [])


class TestThresholds(unittest.TestCase):
    def test_thresholds_externalized_and_loaded(self):
        """阈值配置可加载、含治理元数据；判定结果必须随配置变化（证明代码真读配置）。"""
        th = triage02.load_thresholds(refresh=True)
        for section in ("version", "updated", "note", "triggers", "scoring", "digest_bump",
                        "ddl_bump", "digest_rank_weights", "digest_norm", "confidence",
                        "judges", "aggregate"):
            self.assertIn(section, th)
        self.assertEqual(th["triggers"]["random_read"]["read_iops_gte"], 500)
        self.assertEqual(th["triggers"]["random_read"]["avg_read_kb_lt"], 32)
        self.assertEqual(th["triggers"]["device_saturation"]["util_gte"], 85)
        self.assertEqual(th["triggers"]["mismatch_low_io"]["iowait_gte"], 15)
        self.assertEqual(th["judges"]["await_obvious_gte"], 10)
        self.assertEqual(th["digest_rank_weights"]["tmp_disk_tables"], 5000.0)

        text = triage02.read_text(str(FIXTURES / "iostat_sample.txt"))
        p = triage02.parse_iostat(text)
        agg = triage02.aggregate_devices(p["devices"])
        base, _, _ = triage02.triage(agg, p["cpu"], [], {}, {})
        self.assertTrue(any(c["key"] == "random_read_amplification" for c in base))

        # 把触发阈值改到不可能达到的量级 → 该候选不再触发（缓存即时生效）
        triage02.load_thresholds()["triggers"]["random_read"]["read_iops_gte"] = 99999999
        try:
            off, _, _ = triage02.triage(agg, p["cpu"], [], {}, {})
            self.assertFalse(any(c["key"] == "random_read_amplification" for c in off))
        finally:
            triage02.load_thresholds(refresh=True)  # 从磁盘重读，还原缓存，避免污染其他用例


class TestRunEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TMP.mkdir(parents=True, exist_ok=True)

    def _run_full(self, name):
        out = TMP / name
        argv = ["run",
                "--iostat", str(FIXTURES / "iostat_sample.txt"),
                "--digest", str(FIXTURES / "digest_sample.csv"),
                "--ddl", str(FIXTURES / "schema_sample.sql"),
                "--meta", str(FIXTURES / "meta_sample.json"),
                "--out", str(out)]
        rc, text = _call(argv)
        return out, rc, _last_json(text), text

    def test_run_full_produces_report_and_top_cause(self):
        """端到端：报告/结构化产物落盘，主因为随机小块读（证据链 + 置信度）+【待复核】标记。"""
        out, rc, env, _ = self._run_full("e2e_full")
        self.assertEqual(rc, 0)
        self.assertTrue(env["ok"])
        rp, jp = Path(env["report"]), Path(env["triage"])
        self.assertTrue(rp.is_file())
        self.assertTrue(jp.is_file())
        # top 根因符合预期：随机小块读主导 · 二级索引回表/点查放大，置信度高
        self.assertEqual(env["top_cause"]["key"], "random_read_amplification")
        self.assertEqual(env["top_cause"]["confidence"], "高")
        self.assertEqual(env["unit"], "MB/s")
        self.assertEqual(env["samples"], 3)

        data = json.loads(jp.read_text(encoding="utf-8"))
        self.assertEqual(data["candidates"][0]["key"], "random_read_amplification")
        self.assertEqual(len(data["candidates"]), 3)  # 随机读 / 写压力 / 设备饱和
        self.assertEqual(len(data["candidates"][0]["evidence"]), 6)
        self.assertEqual(data["thresholds_version"], triage02.load_thresholds()["version"])

        rep = rp.read_text(encoding="utf-8")
        self.assertIn("【待复核】", rep)
        self.assertIn("未经 DBA 人工复核不得外发", rep)
        for sec in ("场景与目标", "数据来源与口径", "物理 I/O 画像", "SQL 归因",
                    "表结构佐证", "根因判定", "风险边界", "待确认项"):
            self.assertIn(sec, rep)
        self.assertIn("MYS-RO-REDACTED", rep)

    def test_run_degraded_without_digest_and_ddl(self):
        """digest/ddl 缺失自动降级：报告对应章节标注跳过，iostat 部分照常出结论。"""
        out = TMP / "e2e_degraded"
        argv = ["run",
                "--iostat", str(FIXTURES / "iostat_sample.txt"),
                "--meta", str(FIXTURES / "meta_sample.json"),
                "--out", str(out)]
        rc, text = _call(argv)
        self.assertEqual(rc, 0)
        env = _last_json(text)
        self.assertTrue(env["ok"])
        rep = Path(env["report"]).read_text(encoding="utf-8")
        self.assertIn("未提供 digest 材料，本节跳过", rep)
        self.assertIn("未提供 DDL 材料，本节跳过", rep)
        data = json.loads(Path(env["triage"]).read_text(encoding="utf-8"))
        self.assertEqual(data["top_sql"], [])
        self.assertTrue(data["candidates"])  # iostat 单独也足够触发根因候选
        self.assertEqual(env["top_cause"]["key"], "random_read_amplification")

    def test_missing_iostat_gap_exit_code_2(self):
        """缺 iostat 材料：gap 信封 + 退出码 2，不猜测不伪装成功。"""
        argv = ["run",
                "--iostat", str(FIXTURES / "no_such_iostat.txt"),
                "--out", str(TMP / "gap_run")]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                triage02.main(argv)
        self.assertEqual(cm.exception.code, 2)
        env = _last_json(buf.getvalue())
        self.assertFalse(env["ok"])
        self.assertTrue(env["gap"])  # gap 必须是可行动的缺失说明
        self.assertIn("no_such_iostat.txt", env["gap"])


class TestSubcommandEnvelope(unittest.TestCase):
    """三个分析子命令的 stdout 最后一行也必须是 ok:true 的 JSON 信封。"""

    def test_parse_iostat_envelope(self):
        rc, text = _call(["parse-iostat", "--iostat", str(FIXTURES / "iostat_sample.txt")])
        self.assertEqual(rc, 0)
        env = _last_json(text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["samples"], 3)
        self.assertEqual(env["unit"], "MB/s")
        self.assertEqual(env["aggregate"]["hot_dev"], "vda")

    def test_analyze_digest_envelope_top(self):
        rc, text = _call(["analyze-digest", "--digest", str(FIXTURES / "digest_sample.json"),
                          "--top", "3"])
        self.assertEqual(rc, 0)
        env = _last_json(text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["count"], 3)
        self.assertIn("biz_event_log", env["top"][0]["sql"])

    def test_analyze_ddl_envelope(self):
        rc, text = _call(["analyze-ddl", "--ddl", str(FIXTURES / "schema_sample.sql")])
        self.assertEqual(rc, 0)
        env = _last_json(text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["count"], 3)


if __name__ == "__main__":
    unittest.main()
