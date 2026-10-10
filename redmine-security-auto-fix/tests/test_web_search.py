import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import web_search


class ParseResultsTests(unittest.TestCase):
    TEXT = """## Search Results (2 results, 1228ms)

### 1. Spring Framework CVE-2024-38819 published
- **URL**: https://spring.io/blog/2024/10/17/spring-fix
- The Spring Framework has released version 6.1.14 that contains a fix.
- Versions 6.1.13 and older are affected. date: Oct 17, 2024

### 2. 路径遍历漏洞分析
- **URL**: https://www.secrss.com/articles/71343
- 奇安信CERT监测到官方修复 Spring Framework 路径遍历漏洞。
"""

    def test_parses_titles_urls_and_snippets(self):
        rows = web_search.parse_results(self.TEXT)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["title"], "Spring Framework CVE-2024-38819 published")
        self.assertEqual(rows[0]["url"], "https://spring.io/blog/2024/10/17/spring-fix")
        self.assertIn("6.1.14", rows[0]["snippet"])
        self.assertIn("date: Oct 17, 2024", rows[0]["snippet"])
        self.assertTrue(rows[1]["snippet"].startswith("奇安信CERT"))

    def test_drops_entries_without_url(self):
        text = "## Search Results (1 results, 1ms)\n\n### 1. 无链接条目\n- 只有摘要没有链接\n"
        self.assertEqual(web_search.parse_results(text), [])


class LoadApiKeyTests(unittest.TestCase):
    def test_env_var_wins(self):
        import os
        os.environ["ANYSEARCH_API_KEY"] = "env-key"
        try:
            self.assertEqual(web_search.load_api_key(), "env-key")
        finally:
            del os.environ["ANYSEARCH_API_KEY"]

    def test_missing_key_returns_none(self):
        import os
        saved = os.environ.pop("ANYSEARCH_API_KEY", None)
        try:
            # skill 根目录当前没有 .env（有也会被下面的 monkeypatch 隔离）
            original = web_search.SKILL_ROOT
            web_search.SKILL_ROOT = Path(__file__).parent / "_no_such_dir_"
            try:
                self.assertIsNone(web_search.load_api_key())
            finally:
                web_search.SKILL_ROOT = original
        finally:
            if saved:
                os.environ["ANYSEARCH_API_KEY"] = saved


if __name__ == "__main__":
    unittest.main()
