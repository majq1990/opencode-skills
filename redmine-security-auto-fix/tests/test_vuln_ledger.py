import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import vuln_ledger


class FakeDws(unittest.TestCase):
    """替换 _dws，喂固定响应，验证过滤条件构造与结果字段化。"""

    def setUp(self):
        self.calls = []
        self.responses = {
            "field": {
                "data": {"fields": [
                    {"fieldId": "sRKdhAT", "fieldName": "CVE编号", "type": "text"},
                    {"fieldId": "NIDPdMM", "fieldName": "漏洞名称", "type": "text"},
                    {"fieldId": "olQTi1r", "fieldName": "危险程度", "type": "singleSelect"},
                    {"fieldId": "cKUY2PI", "fieldName": "标签", "type": "singleSelect"},
                    {"fieldId": "Ypqicnc", "fieldName": "修复文档链接", "type": "url"},
                ]},
                "status": "success",
            },
            "record": {
                "data": {"records": [{
                    "recordId": "rec1",
                    "cells": {
                        "sRKdhAT": "CVE-2024-38819",
                        "NIDPdMM": "Spring 路径遍历漏洞",
                        "olQTi1r": {"id": "opt1", "name": "高危"},
                        "cKUY2PI": {"id": "opt2", "name": "处理中"},
                        "Ypqicnc": "https://example.com/fix",
                    },
                }], "status": "success"},
            },
        }
        original = vuln_ledger._dws

        def fake_dws(args, timeout_s=120):
            self.calls.append(args)
            key = "record" if "record" in args else "field"
            return self.responses[key]

        vuln_ledger._dws = fake_dws
        self.addCleanup(setattr, vuln_ledger, "_dws", original)

    def test_lookup_builds_or_filter_and_names_cells(self):
        hits = vuln_ledger.lookup_cves(["CVE-2024-38819", "CVE-0000-0000"])
        self.assertIn("CVE-2024-38819", hits)
        hit = hits["CVE-2024-38819"]
        self.assertEqual(hit["漏洞名称"], "Spring 路径遍历漏洞")
        self.assertEqual(hit["危险程度"], "高危")
        self.assertEqual(hit["标签"], "处理中")
        # 过滤条件：or + eq 每个 CVE 一支
        record_calls = [c for c in self.calls if "record" in c]
        self.assertEqual(len(record_calls), 1)
        filters = json.loads(record_calls[0][record_calls[0].index("--filters") + 1])
        self.assertEqual(filters["operator"], "or")
        self.assertEqual(len(filters["operands"]), 2)

    def test_attach_suppresses_web_search_when_solution_exists(self):
        vulns = [{
            "id": 1, "cve": "CVE-2024-38819", "name": "spring 路径遍历",
            "web_search": {"required": True, "query": "x", "kb_has_solution": True},
            "recommendations": [],
        }]
        summary = vuln_ledger.attach_to_vulns(vulns)
        self.assertEqual(summary["matched"], 1)
        self.assertEqual(summary["suppressed_web_search"], 1)
        self.assertFalse(vulns[0]["web_search"]["required"])
        self.assertIn("台账已登记", vulns[0]["web_search"]["reason"])
        self.assertEqual(vulns[0]["recommendations"][0]["source"], "ledger")
        self.assertEqual(vulns[0]["ledger"]["修复文档链接"], "https://example.com/fix")

    def test_attach_keeps_search_when_ledger_pending(self):
        # 台账登记了但无方案（无修复文档、标签=待定）：不压掉互联网搜索
        self.responses["record"]["data"]["records"][0]["cells"].pop("Ypqicnc")
        self.responses["record"]["data"]["records"][0]["cells"]["cKUY2PI"] = {
            "id": "opt9", "name": "待定",
        }
        vulns = [{
            "id": 1, "cve": "CVE-2024-38819", "name": "spring 路径遍历",
            "web_search": {"required": True, "query": "x", "kb_has_solution": True},
            "recommendations": [],
        }]
        summary = vuln_ledger.attach_to_vulns(vulns)
        self.assertEqual(summary["matched"], 1)
        self.assertEqual(summary["suppressed_web_search"], 0)
        self.assertTrue(vulns[0]["web_search"]["required"])


if __name__ == "__main__":
    unittest.main()
