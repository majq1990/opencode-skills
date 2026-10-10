import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from fetch_vuln_docs import RedmineAccessError, fetch_issue, _validate_redmine_url


def _http_error(code):
    return urllib.error.HTTPError(
        "https://faq.egova.com.cn:7787/issues/1.json", code, "boom", {}, None
    )


class FetchIssueAccessTests(unittest.TestCase):
    """认证/权限/案件不存在必须中断，不能退化成"没有附件"的假方案。"""

    @patch("fetch_vuln_docs.urllib.request.urlopen")
    def test_unauthorized_raises_instead_of_empty_issue(self, urlopen):
        urlopen.side_effect = _http_error(401)
        with self.assertRaises(RedmineAccessError) as ctx:
            fetch_issue("https://faq.egova.com.cn:7787", "bad-key", 1)
        self.assertIn("API Key", str(ctx.exception))

    @patch("fetch_vuln_docs.urllib.request.urlopen")
    def test_forbidden_raises(self, urlopen):
        urlopen.side_effect = _http_error(403)
        with self.assertRaises(RedmineAccessError):
            fetch_issue("https://faq.egova.com.cn:7787", "key", 1)

    @patch("fetch_vuln_docs.urllib.request.urlopen")
    def test_missing_issue_raises(self, urlopen):
        urlopen.side_effect = _http_error(404)
        with self.assertRaises(RedmineAccessError) as ctx:
            fetch_issue("https://faq.egova.com.cn:7787", "key", 999999)
        self.assertIn("找不到案件", str(ctx.exception))

    @patch("fetch_vuln_docs.urllib.request.urlopen")
    def test_server_error_still_degrades_to_empty(self, urlopen):
        urlopen.side_effect = _http_error(500)
        self.assertEqual(fetch_issue("https://faq.egova.com.cn:7787", "key", 1), {})


class RedmineUrlGuardTests(unittest.TestCase):
    def test_rejects_non_http_scheme(self):
        with self.assertRaises(RedmineAccessError):
            _validate_redmine_url("ftp://faq.egova.com.cn:7787")

    def test_rejects_credentials_in_url(self):
        with self.assertRaises(RedmineAccessError):
            _validate_redmine_url("https://user:pass@faq.egova.com.cn:7787")

    def test_rejects_loopback_and_metadata_addresses(self):
        for host in ("http://127.0.0.1:7787", "http://169.254.169.254"):
            with self.assertRaises(RedmineAccessError):
                _validate_redmine_url(host)

    def test_allows_public_redmine_host(self):
        url = "https://faq.egova.com.cn:7787"
        self.assertEqual(_validate_redmine_url(url), url)
