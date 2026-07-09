import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from report_parser import parse_report


class ArchiveParserTests(unittest.TestCase):
    def test_zip_recursively_parses_supported_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "inside.csv"
            csv_path.write_text(
                "漏洞名称,风险等级,修复建议\nCORS配置不当,中危,限制来源\n",
                encoding="utf-8",
            )
            archive_path = root / "reports.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.write(csv_path, "nested/inside.csv")
            result = parse_report(archive_path)
        self.assertEqual(result["total"], 1)
        self.assertIn("reports.zip!nested", result["vulns"][0]["source_file"])


if __name__ == "__main__":
    unittest.main()
