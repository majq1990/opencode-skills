#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""docx_io 自研读写器测试：生成/读取/模板回填。"""

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import docx_io  # noqa: E402
from patrol_lib import WORK_DIR  # noqa: E402

TMP = WORK_DIR / "test_tmp"
TMP.mkdir(parents=True, exist_ok=True)

BLOCKS = [
    {"type": "h", "level": 1, "text": "项目维护手册"},
    {"type": "h", "level": 2, "text": "一、系统概述"},
    {"type": "p", "text": "本系统为测试项目。"},
    {"type": "ph", "text": "【待补充】服务器清单"},
    {"type": "table", "rows": [["名称", "IP"], ["app-01", "192.0.2.10"]], "header": True},
]


class TestMakeAndRead(unittest.TestCase):
    def test_round_trip(self):
        path = TMP / "made.docx"
        out = docx_io.make_document(path, BLOCKS)
        self.assertTrue(Path(out).exists())
        paras = docx_io.read_paragraphs(out)
        self.assertEqual(paras[0]["style"], "Heading1")
        self.assertEqual(paras[0]["text"], "项目维护手册")
        self.assertEqual(paras[3]["style"], "Placeholder")
        self.assertIn("待补充", paras[3]["text"])
        tables = docx_io.read_tables(out)
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0][0], ["名称", "IP"])
        self.assertEqual(tables[0][1], ["app-01", "192.0.2.10"])

    def test_suffix_auto(self):
        out = docx_io.make_document(TMP / "nosuffix2", [{"type": "p", "text": "x"}])
        self.assertTrue(out.endswith(".docx"))


class TestFillTemplate(unittest.TestCase):
    def setUp(self):
        self.tpl = docx_io.make_document(
            TMP / "tpl.docx",
            [{"type": "p", "text": "{{project_name}} 月度运维报告"},
             {"type": "p", "text": "统计月份：{{month}}，故障总数：{{incidents}}"},
             {"type": "table", "rows": [["指标", "数值"], ["可用率", ""], ["工单量", ""]], "header": True}])

    def test_replacements_and_cells(self):
        out, hits, misses = docx_io.fill_template(
            self.tpl, TMP / "filled.docx",
            replacements={"{{project_name}}": "智慧园区", "{{month}}": "2026-09", "{{incidents}}": "3"},
            cells=[{"table": 0, "row": 1, "col": 1, "text": "99.98%"},
                   {"table": 0, "row": 2, "col": 1, "text": "42"}])
        self.assertEqual(misses, [])
        self.assertIn("{{project_name}}", hits)
        paras = docx_io.read_paragraphs(out)
        self.assertIn("智慧园区 月度运维报告", paras[0]["text"])
        self.assertIn("2026-09", paras[1]["text"])
        tables = docx_io.read_tables(out)
        self.assertEqual(tables[0][1], ["可用率", "99.98%"])
        self.assertEqual(tables[0][2], ["工单量", "42"])

    def test_partial_hit_reports_misses(self):
        out, hits, misses = docx_io.fill_template(
            self.tpl, TMP / "partial.docx", replacements={"{{project_name}}": "X", "{{nope}}": "Y"})
        self.assertIn("{{nope}}", misses)
        self.assertIn("{{project_name}}", hits)

    def test_template_untouched(self):
        docx_io.fill_template(self.tpl, TMP / "filled2.docx", replacements={"{{project_name}}": "Z"})
        paras = docx_io.read_paragraphs(str(self.tpl))
        self.assertIn("{{project_name}}", paras[0]["text"])  # 原模板未被改写

    def test_cell_out_of_range(self):
        with self.assertRaises(docx_io.DocxError):
            docx_io.fill_template(self.tpl, TMP / "err.docx",
                                  cells=[{"table": 5, "row": 0, "col": 0, "text": "x"}])

    def test_cross_run_replace_keeps_structure(self):
        # 用两个 run 拼出的关键词（模拟 Word 分段存储），替换后段落结构不变、表格数不变
        tpl2 = docx_io.make_document(TMP / "tpl2.docx", [{"type": "p", "text": "告警总数 ABC 个"}])
        out, hits, misses = docx_io.fill_template(tpl2, TMP / "cross.docx", replacements={"ABC": "12"})
        self.assertEqual(misses, [])
        paras = docx_io.read_paragraphs(out)
        self.assertIn("告警总数 12 个", paras[0]["text"])
        self.assertEqual(len(docx_io.read_tables(out)), 0)


if __name__ == "__main__":
    unittest.main()
