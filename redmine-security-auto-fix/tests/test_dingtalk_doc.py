import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from generate_dingtalk_doc import (  # noqa: E402
    _mask_internal_addresses,
    _redact_sensitive_text,
    _sanitize_description,
    generate_doc_markdown,
)
from process_issue import _diagnose_no_report  # noqa: E402


class NoReportNoticeTests(unittest.TestCase):
    def test_no_report_renders_reason_and_sanitized_description(self):
        """0 漏洞时必须说明原因，并只给去链接去凭据的描述摘录。"""
        description = (
            '<p>SonarQube 控制台：<a href="http://10.255.30.6:9000/dashboard?id=x">'
            "链接</a>，账号/密码：admin/egovasonar，存在 3 个高危问题</p>"
        )
        no_report = _diagnose_no_report(
            attachments=[],
            parse_results=[],
            issue={"description": description},
        )
        self.assertEqual(no_report["reason"], "本案没有可下载的附件，漏洞明细只写在案件描述里")

        md = generate_doc_markdown(
            {"issue_id": "533943", "vulns": [], "no_report": no_report},
            "https://faq.egova.com.cn:7787/issues/533943",
        )

        self.assertIn("未解析到漏洞清单", md)
        self.assertIn("本案没有可下载的附件", md)
        self.assertIn("存在 3 个高危问题", md)
        # 内网地址和凭据不能出现在对外方案里
        self.assertNotIn("10.255.30.6", md)
        self.assertNotIn("egovasonar", md)
        self.assertNotIn("href=", md)
        # 空表之外仍要有可执行的下一步
        self.assertIn("处理建议", md)

    def test_normal_doc_has_no_notice(self):
        """有漏洞时不能出现说明块，避免把正常方案说得像没查到。"""
        md = generate_doc_markdown(
            {
                "issue_id": "525440",
                "vulns": [
                    {
                        "name": "SQL注入",
                        "level": "high",
                        "description": "参数未过滤",
                        "harm": "数据泄露",
                        "fix_suggestion": "参数化查询",
                        "source_file": "report.docx",
                    }
                ],
            },
            "https://faq.egova.com.cn:7787/issues/525440",
        )
        self.assertNotIn("未解析到漏洞清单", md)
        self.assertIn("SQL注入", md)
        self.assertIn("共识别 **1 类", md)

    def test_reason_varies_by_failure_mode(self):
        """附件缺失/格式不符/解析失败要分开说，排查动作不一样。"""
        no_attachments = _diagnose_no_report([], [], {"description": ""})
        unsupported = _diagnose_no_report(
            [{"filename": "shot.png"}], [], {"description": ""}
        )
        failed = _diagnose_no_report(
            [{"filename": "a.pdf"}], [{"file": "a.pdf", "error": "boom"}], {"description": ""}
        )
        parsed_empty = _diagnose_no_report(
            [{"filename": "a.pdf"}], [{"file": "a.pdf", "total": 0}], {"description": ""}
        )
        self.assertIn("没有可下载的附件", no_attachments["reason"])
        self.assertIn("都不是支持解析的报告格式", unsupported["reason"])
        self.assertIn("全部解析失败", failed["reason"])
        self.assertIn("未识别出漏洞条目", parsed_empty["reason"])

    def test_sanitize_description_strips_urls_and_credentials(self):
        text = (
            "登录页 https://demo.test/login?token=abc123 存在弱口令，"
            "账号：admin 密码：P@ssw0rd，另见 http://10.0.0.1:8080/console"
        )
        cleaned = _sanitize_description(text)
        self.assertNotIn("abc123", cleaned)
        self.assertNotIn("P@ssw0rd", cleaned)
        self.assertNotIn("10.0.0.1", cleaned)
        self.assertNotIn("demo.test/login", cleaned)
        self.assertIn("弱口令", cleaned)
        self.assertIn("[REDACTED]", cleaned)

    def test_redact_stops_at_fullwidth_comma(self):
        """"密码：abc，存在严重问题"里的正文不能被凭据规则吞掉。"""
        cleaned = _redact_sensitive_text("密码：abc，存在严重问题")
        self.assertIn("[REDACTED]", cleaned)
        self.assertIn("存在严重问题", cleaned)

    def test_redact_handles_fullwidth_colon_and_account_labels(self):
        """中文报告的"密码：xxx""账户=xxx"以前漏红，发布即泄密。"""
        self.assertIn("[REDACTED]", _redact_sensitive_text("密码：admin123"))
        self.assertIn("[REDACTED]", _redact_sensitive_text("用户名=zhangsan"))
        self.assertIn("[REDACTED]", _redact_sensitive_text("账户：root/123456"))
        # 不带分隔符的正常语句不能被误伤
        self.assertEqual(
            _redact_sensitive_text("默认口令使用随机数生成"),
            "默认口令使用随机数生成",
        )
        self.assertEqual(
            _redact_sensitive_text("password 字段需哈希存储"),
            "password 字段需哈希存储",
        )


class InternalAddressMaskTests(unittest.TestCase):
    """安全池先例原文里的内网地址不能跟着进对外方案（529626 实测泄露 135 处）。"""

    def test_mask_private_and_loopback_with_port(self):
        self.assertEqual(
            _mask_internal_addresses("测试版本 1.7.3.93 http://10.255.18.31:8080/bigdata-api/tree"),
            "测试版本 1.7.3.93 http://[内网地址已省略]/bigdata-api/tree",
        )
        for raw in ("192.168.1.1", "172.16.0.9:8080", "127.0.0.1:9000", "169.254.1.1"):
            self.assertNotIn(raw, _mask_internal_addresses(f"见 {raw} 已屏蔽"))

    def test_mask_keeps_public_addresses_and_domains(self):
        text = "参考 https://faq.egova.com.cn:7787/issues/520604 与 223.5.5.5"
        self.assertEqual(_mask_internal_addresses(text), text)

    def test_recommendation_text_is_masked_in_doc(self):
        md = generate_doc_markdown(
            {
                "issue_id": "529626",
                "vulns": [
                    {
                        "name": "越权（待确认）GET /drone-api//unity/gis/wayline/theme/getlist",
                        "level": "medium",
                        "description": "越权",
                        "recommendations": [
                            {
                                "source": "sec_pool_history",
                                "suggestion": (
                                    "[测试验证] 结果说明: 测试版本：1.7.3.93 "
                                    "http://10.255.18.31:8080/bigdata-api/free/transformer/tree 已屏蔽此接口"
                                ),
                            }
                        ],
                    }
                ],
            },
            "https://faq.egova.com.cn:7787/issues/529626",
        )
        self.assertNotIn("10.255.18.31", md)
        self.assertIn("[内网地址已省略]", md)
        self.assertIn("已屏蔽此接口", md)

    def test_urls_and_name_are_masked_in_doc(self):
        md = generate_doc_markdown(
            {
                "issue_id": "900001",
                "vulns": [
                    {
                        "name": "未授权访问 http://10.250.4.84:38080/agent-uc/free/ms/oauth/get-token",
                        "level": "high",
                        "description": "未授权访问",
                        "urls": ["http://10.11.1.1:32001/console"],
                    }
                ],
            },
            "https://faq.egova.com.cn:7787/issues/900001",
        )
        self.assertNotIn("10.250.4.84", md)
        self.assertNotIn("10.11.1.1", md)


if __name__ == "__main__":
    unittest.main()
