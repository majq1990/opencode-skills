#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""01_patrol_merge 测试。

覆盖：三源合并行数与 9 列口径；日期向下继承（含源表日期格式单元格被 xlsx_io
转成可读串后反推序列号）；小计/合计行排除；字段头签名定位（含机巡无块标题的
重复字段头、部件「单位名称」备选签名）与字段映射信封；无 --yes 不写产物；
--yes 写出 xlsx 可被 xlsx_io.read_rows 读回且行数正确；--csv 产出（utf-8-sig）；
csv 源表支持；缺源文件 gap（退出码 2）；0 条解析 gap；--stdout-only 覆盖 --yes；
异常残行告警且不中断；入库 fixture 端到端。

unittest 风格，pytest 兼容；临时产物只写 work/test_tmp/patrol_merge/。
fixture 数据全部虚构，不含真实区域/客户/项目名。
"""

import contextlib
import csv as csv_mod
import importlib
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "patrol" / "patrol_merge"
TMP = ROOT / "work" / "test_tmp" / "patrol_merge"

sys.path.insert(0, str(SCRIPTS))

import xlsx_io  # noqa: E402

# 脚本名以数字开头不能用常规 import 语法，走 importlib
tool01 = importlib.import_module("01_patrol_merge")  # noqa: E402

SIGNATURES = {
    "人巡": [["巡查视频时间", "巡查视频数量", "问题上报总量", "问题上报类型", "类型数量", "立案率"]],
    "机巡": [["视频巡查时间", "问题上报类型", "视频巡查数量", "满足立案标准数量", "该类的识别准确率"]],
    "部件": [["部门名称", "访问量"], ["单位名称", "访问量"]],
}
OUTPUT_COLUMNS = list(tool01.DEFAULT_OUTPUT_COLUMNS)

# ---------------------------------------------------------------------------
# 合成 fixture（真实形态：日期分块堆叠 + 小计行 + 块标题/字段头在表头 +
# 机巡第二块无块标题仅重复字段头 + 部件第二块改用「单位名称」签名 +
# 人巡第二块日期为字符串，模拟源表日期格式单元格被 xlsx_io 转成可读串）
# ---------------------------------------------------------------------------

RENXUN_ROWS = [
    ["摄像头人工巡查"],
    ["巡查视频时间", "巡查视频数量", "问题上报总量", "问题上报类型", "类型数量", "立案率"],
    [45673, 120, 15, "占道经营", 6, 0.85],
    [None, None, None, "流动摊贩", 5, None],
    [None, None, None, "合计", 11, None],
    [],
    ["摄像头人工巡查"],
    ["巡查视频时间", "巡查视频数量", "问题上报总量", "问题上报类型", "类型数量", "立案率"],
    ["2025-01-17", 130, 18, "店外经营", 7, 0.9],
    [None, None, None, "违规广告", 4, None],
]

JIXUN_ROWS = [
    ["摄像头智能巡查"],
    ["视频巡查时间", "问题上报类型", "视频巡查数量", "满足立案标准数量", "该类的识别准确率"],
    [45673, "跨门经营", 50, 42, 0.84],
    [None, "乱张贴", 30, 25, 0.83],
    [None, "合计", 80, 67, None],
    ["视频巡查时间", "问题上报类型", "视频巡查数量", "满足立案标准数量", "该类的识别准确率"],
    [45674, "违规广告", 40, 36, 0.9],
    [None, "总计", 120, 103, None],
]

BUJIAN_ROWS = [
    ["部件使用统计情况（2025.1.10）"],
    ["部门名称", "访问量"],
    ["采集一组", 320],
    ["采集二组", 280],
    ["合计", 600],
    [],
    ["部件使用统计情况（2025.1.11）"],
    ["单位名称", "访问量"],
    ["采集一组", 310],
    ["采集三组", 150],
]

BUJIAN_CSV_ROWS = [
    ["部件使用统计情况（2025.1.12）", ""],
    ["部门名称", "访问量", ""],
    ["采集一组", "90", ""],
    ["采集二组", "60", ""],
    ["合计", "150", ""],
]

FIXTURE_SOURCES = [
    {"kind": "人巡", "path": "renxun_fixture.xlsx", "sheet": None},
    {"kind": "机巡", "path": "jixun_fixture.xlsx", "sheet": None},
    {"kind": "部件", "path": "bujian_fixture.xlsx", "sheet": None},
]


def build_fixtures(dest):
    """把三个 xlsx 源表 + 一个 csv 源样例写到 dest，返回路径字典。

    入库 fixture（tests/fixtures/patrol/patrol_merge/）与本测试运行期副本
    （work/test_tmp/patrol_merge/）由同一函数生成，保证口径一致。
    """
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    out = {
        "renxun": xlsx_io.write_rows(str(dest / "renxun_fixture.xlsx"), "人巡", RENXUN_ROWS),
        "jixun": xlsx_io.write_rows(str(dest / "jixun_fixture.xlsx"), "机巡", JIXUN_ROWS),
        "bujian": xlsx_io.write_rows(str(dest / "bujian_fixture.xlsx"), "部件", BUJIAN_ROWS),
    }
    csv_path = dest / "bujian_csv.csv"
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        csv_mod.writer(f).writerows(BUJIAN_CSV_ROWS)
    out["bujian_csv"] = str(csv_path)
    return out


def write_fixture_config(path, sources=None, note="合成样例，数据全部虚构。"):
    cfg = {
        "version": "1.0",
        "updated": "2026-10-02",
        "note": note,
        "sources": sources if sources is not None else FIXTURE_SOURCES,
        "column_signatures": SIGNATURES,
        "output_columns": OUTPUT_COLUMNS,
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return path


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
            rc = tool01.main(list(argv))
    except SystemExit as e:
        rc = e.code
    return rc, buf.getvalue()


class Test01PatrolMerge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = build_fixtures(TMP)
        cls.cfg = write_fixture_config(
            TMP / "sources_runtime.json",
            note="运行期生成，相对路径相对本配置文件所在目录解析。")

    # -- 三源合并行数与 9 列口径 ------------------------------------------

    def test_01_preview_no_write(self):
        """无 --yes：只输出映射 + 样例行，written:false，不写任何产物。"""
        out_path = TMP / "preview_should_not_exist.xlsx"
        rc, out = _call(["--config", str(self.cfg), "--out", str(out_path)])
        self.assertEqual(rc, 0)
        env = _last_json(out)
        self.assertTrue(env["ok"])
        self.assertFalse(env["written"])
        self.assertEqual(env["rows"], 11)
        self.assertEqual(env["per_source"], {"人巡": 4, "机巡": 3, "部件": 4})
        self.assertEqual(env["output_columns"], OUTPUT_COLUMNS)
        self.assertEqual(env["sample_row"]["数据来源"], "人巡")
        self.assertEqual(env["sample_row"]["问题/单位"], "占道经营")
        self.assertEqual(env["sample_row"]["日期序列号"], 45673)
        self.assertEqual(env["sample_row"]["日期(可读)"], "2025-01-16")
        self.assertEqual(env["sample_row"]["数量"], 6)
        self.assertEqual(env["sample_row"]["备注"], "上报总量15；巡查视频120")
        self.assertFalse(out_path.exists())

    def test_02_yes_writes_xlsx_readback(self):
        """--yes 写出 xlsx：可被 xlsx_io.read_rows 读回，行数与 9 列口径正确。"""
        out_path = TMP / "summary.xlsx"
        rc, out = _call(["--config", str(self.cfg), "--yes", "--out", str(out_path)])
        self.assertEqual(rc, 0)
        env = _last_json(out)
        self.assertTrue(env["written"])
        self.assertTrue(Path(env["output"]).is_absolute())
        self.assertTrue(out_path.exists())
        self.assertEqual(xlsx_io.sheet_names(str(out_path)), ["数据汇总"])
        back, warnings = xlsx_io.read_rows(str(out_path))
        self.assertEqual(warnings, [])
        self.assertEqual(back[0], OUTPUT_COLUMNS)
        self.assertEqual(len(back), 12)  # 1 表头 + 11 明细
        self.assertEqual(back[1], [1, "人巡", 45673, "2025-01-16", "占道经营", 6, None,
                                   0.85, "上报总量15；巡查视频120"])
        self.assertEqual(back[2], [2, "人巡", 45673, "2025-01-16", "流动摊贩", 5, None,
                                   None, "上报总量15；巡查视频120"])
        self.assertEqual(back[5], [5, "机巡", 45673, "2025-01-16", "跨门经营", 50, 42,
                                   0.84, None])
        self.assertEqual(back[8], [8, "部件", None, "2025-01-10", "采集一组", 320,
                                   None, None, None])

    # -- 日期向下继承 ------------------------------------------------------

    def test_03_date_inheritance_and_serial_preserve(self):
        """日期写在块首行、后续行向下继承；序列号原样保留；字符串日期反推序列号。"""
        rows, _ = xlsx_io.read_rows(self.paths["renxun"])
        recs, header_row, sig = tool01.parse_date_kind(
            rows, "人巡", SIGNATURES["人巡"], [], "人巡")
        self.assertEqual(header_row, 2)
        self.assertEqual(sig, SIGNATURES["人巡"][0])
        self.assertEqual(len(recs), 4)
        self.assertEqual(recs[0]["serial"], 45673)  # 原样保留的序列号
        self.assertEqual(recs[1]["serial"], 45673)  # 块内第二行向下继承
        self.assertEqual(recs[1]["video"], 120)     # 日期级字段（巡查视频数量）同样继承
        self.assertEqual(recs[1]["total"], 15)      # 日期级字段（问题上报总量）同样继承
        self.assertEqual(recs[2]["serial"], 45674)  # 字符串日期（源表日期格式）反推序列号
        self.assertEqual(recs[2]["readable"], "2025-01-17")
        self.assertEqual(recs[3]["serial"], 45674)  # 第二块内继承
        # 机巡跨块继承（第二块无块标题、仅重复字段头，日期仍正确继承）
        jrows, _ = xlsx_io.read_rows(self.paths["jixun"])
        jrecs, _, _ = tool01.parse_date_kind(jrows, "机巡", SIGNATURES["机巡"], [], "机巡")
        self.assertEqual([r["serial"] for r in jrecs], [45673, 45673, 45674])

    # -- 小计行排除 --------------------------------------------------------

    def test_04_subtotal_rows_excluded(self):
        """合计/总计/小计行不计入明细，且不影响日期继承。"""
        cases = [("人巡", "renxun", 4), ("机巡", "jixun", 3), ("部件", "bujian", 4)]
        for kind, key, expected in cases:
            rows, _ = xlsx_io.read_rows(self.paths[key])
            raw_text = " ".join(str(c) for row in rows for c in row if c is not None)
            self.assertIn("合计", raw_text, "fixture 应确实包含合计行（%s）" % kind)
            if kind == "人巡":
                recs, _, _ = tool01.parse_date_kind(rows, kind, SIGNATURES[kind], [], kind)
            elif kind == "机巡":
                recs, _, _ = tool01.parse_date_kind(rows, kind, SIGNATURES[kind], [], kind)
            else:
                recs, _, _ = tool01.parse_bujian(rows, SIGNATURES[kind], [], kind)
            self.assertEqual(len(recs), expected)
            for r in recs:
                name = r.get("ptype") or r.get("dept")
                self.assertNotIn(name, {"合计", "总计", "小计"})

    # -- 签名定位与字段映射 ------------------------------------------------

    def test_05_signature_location_and_mapping(self):
        """签名定位：机巡无块标题块靠重复字段头解析；部件备选签名生效；映射信封完整。"""
        rc, out = _call(["--config", str(self.cfg)])
        self.assertEqual(rc, 0)
        env = _last_json(out)
        mapping = env["mapping"]
        self.assertEqual(mapping["人巡"]["header_row"], 2)
        self.assertEqual(mapping["机巡"]["header_row"], 2)
        self.assertEqual(mapping["部件"]["header_row"], 2)
        self.assertEqual(mapping["部件"]["signature"], ["部门名称", "访问量"])
        self.assertEqual(mapping["机巡"]["field_map"]["满足立案标准数量"], "达标/立案数")
        self.assertEqual(mapping["人巡"]["field_map"]["类型数量"], "数量")
        # 机巡第二块（无块标题、重复字段头）解析出数据
        self.assertIn("违规广告", self._jixun_ptypes())
        # 部件第二块用「单位名称」备选签名：数据解析成功且字段头未被当成明细
        brecs = self._bujian_records()
        depts = [r["dept"] for r in brecs]
        self.assertIn("采集三组", depts)
        self.assertNotIn("单位名称", depts)
        self.assertNotIn("部门名称", depts)
        self.assertEqual(brecs[2]["readable"], "2025-01-11")  # 第二块日期来自块标题

    def _jixun_ptypes(self):
        rows, _ = xlsx_io.read_rows(self.paths["jixun"])
        recs, _, _ = tool01.parse_date_kind(rows, "机巡", SIGNATURES["机巡"], [], "机巡")
        return [r["ptype"] for r in recs]

    def _bujian_records(self):
        rows, _ = xlsx_io.read_rows(self.paths["bujian"])
        recs, _, _ = tool01.parse_bujian(rows, SIGNATURES["部件"], [], "部件")
        return recs

    # -- --csv 产出 --------------------------------------------------------

    def test_06_csv_output_utf8_sig(self):
        """--csv 产出 utf-8-sig csv，行数与表头正确。"""
        csv_path = TMP / "summary.csv"
        rc, out = _call(["--config", str(self.cfg), "--yes",
                         "--out", str(TMP / "s6.xlsx"), "--csv", str(csv_path)])
        self.assertEqual(rc, 0)
        env = _last_json(out)
        self.assertEqual(env["csv_output"], str(csv_path.resolve()))
        self.assertTrue(csv_path.exists())
        raw = csv_path.read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"), "csv 应为 utf-8-sig（带 BOM）")
        rows = list(csv_mod.reader(io.StringIO(raw.decode("utf-8-sig"))))
        self.assertEqual(rows[0], OUTPUT_COLUMNS)
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[1][4], "占道经营")

    # -- 失败路径（gap，退出码 2） ------------------------------------------

    def test_07_missing_source_gap(self):
        """缺源文件 → ok:false gap 信封，退出码 2。"""
        cfg = write_fixture_config(
            TMP / "sources_missing.json",
            sources=[{"kind": "人巡", "path": "no_such_file.xlsx", "sheet": None}])
        rc, out = _call(["--config", str(cfg)])
        self.assertEqual(rc, 2)
        env = _last_json(out)
        self.assertFalse(env["ok"])
        self.assertIn("源文件不存在", env["gap"])
        self.assertIn("no_such_file.xlsx", env["gap"])

    def test_08_zero_rows_gap(self):
        """解析结果为 0 条（只有块标题与字段头）→ gap，退出码 2。"""
        p = TMP / "only_header.xlsx"
        xlsx_io.write_rows(str(p), "人巡",
                           [["摄像头人工巡查"], SIGNATURES["人巡"][0]])
        cfg = write_fixture_config(
            TMP / "sources_zero.json",
            sources=[{"kind": "人巡", "path": "only_header.xlsx", "sheet": None}])
        rc, out = _call(["--config", str(cfg)])
        self.assertEqual(rc, 2)
        env = _last_json(out)
        self.assertFalse(env["ok"])
        self.assertIn("0 条", env["gap"])

    # -- csv 源表 ----------------------------------------------------------

    def test_09_csv_source_support(self):
        """csv 源样例可解析（块标题中文日期 + 访问量数字串）。"""
        cfg = write_fixture_config(
            TMP / "sources_csv.json",
            sources=[{"kind": "部件", "path": str(FIXTURES / "bujian_csv.csv"),
                      "sheet": None}])
        rc, out = _call(["--config", str(cfg)])
        self.assertEqual(rc, 0)
        env = _last_json(out)
        self.assertTrue(env["ok"])
        self.assertEqual(env["rows"], 2)
        self.assertEqual(env["per_source"], {"部件": 2})
        self.assertEqual(env["sample_row"]["问题/单位"], "采集一组")
        self.assertEqual(env["sample_row"]["日期(可读)"], "2025-01-12")
        self.assertEqual(env["sample_row"]["数量"], 90)

    # -- 入库 fixture 端到端 ------------------------------------------------

    def test_10_committed_fixture_e2e(self):
        """对入库 sources_fixture.json 跑 --yes 全流程（与冒烟命令同路径）。"""
        out_path = TMP / "e2e_fixture.xlsx"
        rc, out = _call(["--config", str(FIXTURES / "sources_fixture.json"),
                         "--yes", "--out", str(out_path)])
        self.assertEqual(rc, 0)
        env = _last_json(out)
        self.assertTrue(env["ok"])
        self.assertTrue(env["written"])
        self.assertEqual(env["rows"], 11)
        self.assertTrue(out_path.exists())

    def test_11_stdout_only_overrides_yes(self):
        """--stdout-only 与 --yes 同给：只预览不写产物。"""
        p = TMP / "should_not_exist_s11.xlsx"
        rc, out = _call(["--config", str(self.cfg), "--yes", "--stdout-only",
                         "--out", str(p)])
        self.assertEqual(rc, 0)
        env = _last_json(out)
        self.assertFalse(env["written"])
        self.assertFalse(p.exists())

    # -- 异常残行告警 --------------------------------------------------------

    def test_12_anomaly_row_warning_and_continue(self):
        """字段头之后出现非空但缺少问题类型的残行：告警、跳过、不中断后续解析。"""
        rows = [
            ["摄像头人工巡查"],
            SIGNATURES["人巡"][0],
            [45673, 10, 2, "占道经营", 1, 0.5],
            [None, None, None, None, 3, None],  # 非空残行（仅数量列有值）
            [None, None, None, "流动摊贩", 2, None],
        ]
        p = TMP / "anomaly.xlsx"
        xlsx_io.write_rows(str(p), "人巡", rows)
        back, _ = xlsx_io.read_rows(str(p))
        warnings = []
        recs, _, _ = tool01.parse_date_kind(back, "人巡", SIGNATURES["人巡"],
                                            warnings, "人巡")
        self.assertEqual(len(recs), 2)
        self.assertTrue(any("缺少问题类型" in w for w in warnings))
        self.assertEqual(recs[1]["ptype"], "流动摊贩")  # 异常行不中断后续解析
        self.assertEqual(recs[1]["serial"], 45673)      # 日期继承不受残行影响


if __name__ == "__main__":
    unittest.main()
