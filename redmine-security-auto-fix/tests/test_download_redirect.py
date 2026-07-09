import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_security_corpus import download_attachment


class DownloadRedirectTests(unittest.TestCase):
    @patch("build_security_corpus.shutil.which", return_value=None)
    @patch("requests.get")
    def test_downloads_from_cross_host_redirect(self, get, _which):
        redirect = Mock()
        redirect.is_redirect = True
        redirect.is_permanent_redirect = False
        redirect.headers = {"Location": "https://oss.example/report.pdf"}
        payload = Mock()
        payload.content = b"report"
        payload.raise_for_status = Mock()
        get.side_effect = [redirect, payload]

        with tempfile.TemporaryDirectory() as directory:
            path = download_attachment(
                "https://redmine.example",
                "secret",
                {
                    "id": 1,
                    "issue_id": 2,
                    "filename": "report.pdf",
                    "filesize": 6,
                    "content_url": "https://redmine.example/attachments/download/1/report.pdf",
                },
                Path(directory),
            )
            self.assertEqual(path.read_bytes(), b"report")

        first_headers = get.call_args_list[0].kwargs["headers"]
        self.assertEqual(first_headers["X-Redmine-API-Key"], "secret")
        self.assertNotIn("headers", get.call_args_list[1].kwargs)


if __name__ == "__main__":
    unittest.main()
