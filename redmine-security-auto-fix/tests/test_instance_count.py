import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from generate_dingtalk_doc import _instance_count, generate_doc_markdown
from report_parser import _parse_cn_source_scan_pdf


class InstanceCountTests(unittest.TestCase):
    def test_instances_field_wins(self):
        self.assertEqual(_instance_count({"instances": 37, "name": "路径遍历"}), 37)

    def test_description_count_is_used_when_field_missing(self):
        vuln = {"name": "路径遍历", "description": "共 37 例；涉及 5 个代码位置"}
        self.assertEqual(_instance_count(vuln), 37)

    def test_star_notation_in_name_is_used(self):
        self.assertEqual(_instance_count({"name": "SQL注入*12"}), 12)

    def test_defaults_to_one(self):
        self.assertEqual(_instance_count({"name": "弱口令"}), 1)

    def test_source_scan_rows_carry_instance_count(self):
        text = (
            "中正检测 源代码扫描报告\n"
            "缺陷类型统计\n"
            "路径遍历 高 37\n"
            "反射型跨站脚本攻击 高 12\n"
            "\n"
            "路径遍历   ( 37例)\n"
            "入口点 src/main/java/A.java\n"
            "出口点 src/main/java/B.java\n"
            "\n"
            "反射型跨站脚本攻击   ( 12例)\n"
            "入口点 src/main/java/C.java\n"
        )
        rows = _parse_cn_source_scan_pdf(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["实例数"], 37)
        self.assertEqual(rows[1]["实例数"], 12)

    def test_overview_reports_instance_total_not_type_count(self):
        vulns = [
            {"name": "路径遍历", "level": "high", "instances": 37},
            {"name": "弱口令", "level": "medium", "instances": 1},
        ]
        md = generate_doc_markdown(
            {"issue_id": 1, "vulns": vulns, "stats": {"high": 1, "medium": 1}},
            "https://example.invalid/issues/1",
        )
        self.assertIn("共识别 **2 类、38 个漏洞实例**", md)
        self.assertIn("| 37 |", md)


if __name__ == "__main__":
    unittest.main()
