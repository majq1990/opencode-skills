import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from recommendation_engine import enrich_vulnerability, is_code_vulnerability


class FakeBridge:
    def __init__(self, history=None, knowledge=None):
        self.result = {
            "history": history or [],
            "knowledge": knowledge or [],
        }

    def search_internal(self, query, top=5):
        return self.result


class RecommendationPolicyTests(unittest.TestCase):
    def test_code_vulnerability_requests_web_search_as_fallback_when_no_internal(self):
        # 新策略：代码类内部无可执行方案时，兜底触发互联网检索
        vuln = {"name": "SQL注入漏洞", "description": "参数未过滤"}
        result = enrich_vulnerability(vuln, FakeBridge())
        self.assertTrue(is_code_vulnerability(vuln))
        self.assertEqual(result["fix_type"], "code")
        self.assertTrue(result["web_search"]["required"])
        self.assertFalse(result["web_search"]["kb_has_solution"])
        self.assertEqual(result["recommendations"], [])

    def test_code_vulnerability_with_internal_solution_skips_web_search(self):
        # 红线保留：代码类内部已有方案时，禁止互联网补充
        vuln = {"name": "SQL注入漏洞", "fix_suggestion": "对参数做过滤"}
        bridge = FakeBridge(
            history=[
                {
                    "type": "redmine_history",
                    "issue_id": 9,
                    "title": "历史案件",
                    "score": 0.9,
                    "suggestion": "改用参数化查询/预编译语句",
                }
            ]
        )
        result = enrich_vulnerability(vuln, bridge)
        self.assertEqual(result["fix_type"], "code")
        self.assertFalse(result["web_search"]["required"])

    def test_directory_traversal_and_sensitive_output_are_code_vulnerabilities(self):
        for name in (
            "文件读取*2",
            "未授权访问漏洞",
            "敏感信息泄漏漏洞",
            "详细的报错信息",
        ):
            with self.subTest(name=name):
                self.assertTrue(is_code_vulnerability({"name": name}))

    def test_non_code_without_internal_solution_requests_web_search(self):
        vuln = {"name": "Strict-Transport-Security响应头缺失"}
        result = enrich_vulnerability(vuln, FakeBridge())
        self.assertEqual(result["fix_type"], "non_code")
        self.assertTrue(result["web_search"]["required"])
        self.assertIn("官方", result["web_search"]["query"])

    def test_non_code_with_internal_solution_still_searches_in_parallel(self):
        # 非代码类始终并行搜互联网（即便内部已命中，互联网结果作补充）
        vuln = {"name": "CORS配置不当", "fix_suggestion": "限制允许来源"}
        bridge = FakeBridge(
            history=[
                {
                    "type": "redmine_history",
                    "issue_id": 123,
                    "title": "历史案件",
                    "score": 0.9,
                    "suggestion": "在 Nginx 中配置域名白名单",
                }
            ]
        )
        result = enrich_vulnerability(vuln, bridge)
        self.assertEqual(result["fix_type"], "non_code")
        self.assertTrue(result["web_search"]["required"])
        self.assertTrue(result["web_search"]["kb_has_solution"])
        self.assertEqual(
            [row["source"] for row in result["recommendations"]],
            ["report", "redmine_history"],
        )


if __name__ == "__main__":
    unittest.main()
