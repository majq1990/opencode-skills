import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from process_issue import _clean_name, merge_vulnerabilities


def _vuln(name, **extra):
    row = {
        "name": name,
        "level": "medium",
        "description": "",
        "harm": "",
        "fix_suggestion": "",
        "urls": [],
        "cve": "",
        "cwe": "",
        "source_file": "a.docx",
    }
    row.update(extra)
    return row


class MergeDedupeTests(unittest.TestCase):
    def test_same_finding_from_heading_and_table_is_merged(self):
        merged = merge_vulnerabilities(
            [
                _vuln("3.2 SQL注入漏洞", level="high", fix_suggestion="用参数化查询"),
                _vuln("SQL注入漏洞", level="medium", source_file="b.xlsx"),
            ]
        )
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["level"], "high")
        self.assertIn("参数化查询", merged[0]["fix_suggestion"])

    def test_level_marker_only_variants_are_merged(self):
        merged = merge_vulnerabilities(
            [
                _vuln("越权访问（高危）", level="high"),
                _vuln("越权访问【已修复】", level="high"),
                _vuln("越权访问", level="medium"),
            ]
        )
        self.assertEqual(len(merged), 1)

    def test_distinct_modules_stay_separate(self):
        merged = merge_vulnerabilities(
            [
                _vuln("越权访问（订单模块）", level="high"),
                _vuln("越权访问（用户模块）", level="medium"),
            ]
        )
        self.assertEqual([row["name"] for row in merged], ["越权访问（订单模块）", "越权访问（用户模块）"])

    def test_place_name_inside_brackets_is_not_a_level_mark(self):
        merged = merge_vulnerabilities(
            [
                _vuln("越权访问（中山路接口）"),
                _vuln("越权访问（人民路接口）"),
            ]
        )
        self.assertEqual(len(merged), 2)

    def test_name_starting_with_digit_is_preserved(self):
        self.assertEqual(_clean_name("3DES弱加密"), "3DES弱加密")

    def test_section_prefix_and_status_mark_are_stripped_from_name(self):
        self.assertEqual(
            _clean_name("2.1.1【已关闭-已修复】（中危）pprof服务器信息泄露 1"),
            "pprof服务器信息泄露",
        )
        self.assertEqual(_clean_name("1、硬编码明文默认口令"), "硬编码明文默认口令")

    def test_trailing_page_number_is_ignored(self):
        merged = merge_vulnerabilities(
            [
                _vuln("目录穿越漏洞 12", fix_suggestion="白名单校验"),
                _vuln("目录穿越漏洞"),
            ]
        )
        self.assertEqual(len(merged), 1)
        self.assertIn("白名单校验", merged[0]["fix_suggestion"])

    def test_missing_level_is_backfilled_from_higher_row(self):
        merged = merge_vulnerabilities(
            [
                _vuln("弱口令", level="medium"),
                _vuln("弱口令", level="critical"),
            ]
        )
        self.assertEqual(merged[0]["level"], "critical")
        self.assertTrue(merged[0]["level_explicit"])

    def test_different_findings_are_never_merged(self):
        merged = merge_vulnerabilities(
            [
                _vuln("存储型XSS"),
                _vuln("反射型XSS"),
            ]
        )
        self.assertEqual(len(merged), 2)


if __name__ == "__main__":
    unittest.main()
