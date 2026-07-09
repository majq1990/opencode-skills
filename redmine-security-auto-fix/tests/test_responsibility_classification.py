import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from classify_vulns import classify_vulnerability


class ResponsibilityClassificationTests(unittest.TestCase):
    def test_application_vulnerabilities_belong_to_development(self):
        for name in ("SQL注入", "跨站脚本XSS", "未授权访问", "目录穿越"):
            with self.subTest(name=name):
                self.assertEqual(
                    classify_vulnerability({"name": name})["owner"], "dev"
                )

    def test_middleware_error_output_belongs_to_engineering(self):
        result = classify_vulnerability(
            {"name": "详细的报错信息", "description": "泄露Tomcat中间件版本"}
        )
        self.assertEqual(result["owner"], "ops")
        self.assertEqual(result["layer"], "middleware")


if __name__ == "__main__":
    unittest.main()
