#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xlsx_io 自研读写器测试（含手构 raw xlsx 验证日期序列/共享字符串/合并单元格）。"""

import sys
import unittest
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import xlsx_io  # noqa: E402
from patrol_lib import WORK_DIR  # noqa: E402

TMP = WORK_DIR / "test_tmp"
TMP.mkdir(parents=True, exist_ok=True)


def _make_raw(path, sheet_xml, styles_xml=None, shared_xml=None, merged=False):
    """手构最小 xlsx，用于覆盖自研写入器不产生的特性（日期样式/共享字符串）。"""
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
          '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>')
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<sheets><sheet name="数据" sheetId="1" r:id="rId1"/></sheets></workbook>')
    wbrels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
              '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
              '</Relationships>')
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", ct)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", wb)
        zf.writestr("xl/_rels/workbook.xml.rels", wbrels)
        if shared_xml:
            zf.writestr("xl/sharedStrings.xml", shared_xml)
        if styles_xml:
            zf.writestr("xl/styles.xml", styles_xml)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)


SHEET_HEAD = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              '<sheetData>')
SHEET_TAIL = '</sheetData></worksheet>'


class TestWriteReadRoundTrip(unittest.TestCase):
    def test_round_trip(self):
        path = TMP / "rt.xlsx"
        rows = [["名称", "数量", "比率", "备注"],
                ["区域A", 12, 3.25, None],
                ["区域B", 0, 100.0, "正常"]]
        xlsx_io.write_rows(path, "汇总", rows)
        back, warnings = xlsx_io.read_rows(path)
        self.assertEqual(warnings, [])
        # 空串/None 单元格读回统一为 None（OOXML 无空格概念）
        expected = [["名称", "数量", "比率", "备注"],
                    ["区域A", 12, 3.25, None],
                    ["区域B", 0, 100.0, "正常"]]
        self.assertEqual(back, expected)
        self.assertIsInstance(back[1][1], int)
        self.assertIsInstance(back[2][2], float)

    def test_suffix_auto_append(self):
        path = TMP / "nosuffix"
        out = xlsx_io.write_rows(path, "汇总", [["a", 1]])
        self.assertTrue(out.endswith(".xlsx"))
        self.assertTrue(Path(out).exists())
        self.assertEqual(xlsx_io.sheet_names(out), ["汇总"])


class TestRawFeatures(unittest.TestCase):
    def test_shared_string_and_number(self):
        path = TMP / "shared.xlsx"
        shared = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="2" uniqueCount="2">'
                  '<si><t>人巡</t></si><si><r><t>机器</t></r><r><t>巡查</t></r></si></sst>')
        sheet = (SHEET_HEAD
                 + '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="C1"><v>42</v></c></row>'
                 + SHEET_TAIL)
        _make_raw(path, sheet, shared_xml=shared)
        rows, warnings = xlsx_io.read_rows(path)
        self.assertEqual(warnings, [])
        self.assertEqual(rows[0][0], "人巡")
        self.assertEqual(rows[0][1], "机器巡查")
        self.assertEqual(rows[0][2], 42)

    def test_date_serial(self):
        path = TMP / "date.xlsx"
        styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                  '<numFmts count="1"><numFmt numFmtId="164" formatCode="yyyy-mm-dd"/></numFmts>'
                  '<fonts count="1"><font/></fonts><fills count="1"><fill/></fills><borders count="1"><border/></borders>'
                  '<cellStyleXfs count="1"><xf numFmtId="0"/></cellStyleXfs>'
                  '<cellXfs count="2"><xf numFmtId="0"/><xf numFmtId="164" applyNumberFormat="1"/></cellXfs>'
                  '</styleSheet>')
        sheet = (SHEET_HEAD
                 + '<row r="1"><c r="A1" s="1"><v>45000</v></c><c r="B1"><v>45000</v></c></row>'
                 + SHEET_TAIL)
        _make_raw(path, sheet, styles_xml=styles)
        rows, warnings = xlsx_io.read_rows(path)
        self.assertEqual(warnings, [])
        self.assertEqual(rows[0][0], "2023-03-15")  # 序列 45000 = 2023-03-15
        self.assertEqual(rows[0][1], 45000)          # 无日期样式保持数值

    def test_merged_fill(self):
        path = TMP / "merged.xlsx"
        sheet = (SHEET_HEAD
                 + '<row r="1"><c r="A1"><v>10</v></c></row>'
                 + '<row r="2"><c r="A2"><v>7</v></c><c r="B2"><v>1</v></c></row>'
                 + '<row r="3"><c r="A3"/><c r="B3"><v>2</v></c></row>'
                 + SHEET_TAIL)
        # 在 sheetData 之后补 mergeCells：把 A2:A3 合并
        sheet = sheet.replace("</worksheet>",
                              '<mergeCells count="1"><mergeCell ref="A2:A3"/></mergeCells></worksheet>')
        _make_raw(path, sheet)
        rows, warnings = xlsx_io.read_rows(path)
        self.assertEqual(warnings, [])
        self.assertEqual(rows[1][0], 7)
        self.assertEqual(rows[2][0], 7)  # 空从格被主格填充
        self.assertEqual(rows[2][1], 2)  # 显式值不覆盖

    def test_sheet_names_and_pick(self):
        path = TMP / "rt.xlsx"
        xlsx_io.write_rows(path, "汇总", [["a"]])
        self.assertEqual(xlsx_io.sheet_names(path), ["汇总"])
        rows, _ = xlsx_io.read_rows(path, sheet="汇总")
        self.assertEqual(rows, [["a"]])
        with self.assertRaises(xlsx_io.XlsxError):
            xlsx_io.read_rows(path, sheet="不存在")

    def test_not_xlsx_raises(self):
        path = TMP / "bad.xlsx"
        path.write_text("not a zip", encoding="utf-8")
        with self.assertRaises(xlsx_io.XlsxError):
            xlsx_io.read_rows(path)

    def test_dtd_entity_refused(self):
        # 恶意构造：sheet XML 内嵌 DTD 实体扩展（billion laughs）→ 必须拒绝
        path = TMP / "evil.xlsx"
        lol = "".join('<!ENTITY e%d "&e%d&e%d&e%d&e%d">' % ((i,) + (i - 1,) * 4) for i in range(1, 6))
        sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<!DOCTYPE worksheet [<!ENTITY e0 "lol">' + lol + ']>'
                 '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                 '<sheetData><row r="1"><c r="A1"><v>&e5;</v></c></row></sheetData></worksheet>')
        _make_raw(path, sheet)
        with self.assertRaises(xlsx_io.XlsxError) as cm:
            xlsx_io.read_rows(path)
        self.assertIn("DTD", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
