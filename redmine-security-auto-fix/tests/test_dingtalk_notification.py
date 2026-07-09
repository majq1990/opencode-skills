import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from notify_dingtalk import build_markdown_message


class DingTalkNotificationTests(unittest.TestCase):
    def test_builds_stats_and_omits_fake_document_link(self):
        message = build_markdown_message(
            {
                "issue_id": 504039,
                "total": 2,
                "vulns": [{"level": "critical"}, {"level": "high"}],
            },
            None,
            "https://faq.example/issues/504039",
            "安全通知",
            "https://alidocs.example/folder",
        )

        text = message["markdown"]["text"]
        self.assertIn("严重：1个", text)
        self.assertIn("高危：1个", text)
        self.assertIn("安全通知", text)
        self.assertIn("项目案例", text)
        self.assertNotIn("查看文档", text)


if __name__ == "__main__":
    unittest.main()
