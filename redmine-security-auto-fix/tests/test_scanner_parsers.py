import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from report_parser import (
    _parse_api_security_scan_html,
    _parse_appscan_pdf,
    _parse_fortify_cwe_top25_pdf,
    _parse_fortify_dev_workbook_pdf,
    _parse_jianshi_html,
    _parse_osv_table_txt,
    _parse_trivy_table_txt,
    _parse_zap_html,
    _parse_zap_pdf,
    parse_report,
)


class FortifyCweTop25Tests(unittest.TestCase):
    TEXT = """Fortify Audit Workbench
CWE Top 25 2023
demo-project
Table of Contents
Issue Details
[1] CWE ID 079
CWE-79 is used to identify an "Improper Neutralization of Input During Web Page
Generation ('Cross- site Scripting')" weakness.
These weaknesses occur because "The software does not neutralize user input."
Cross-Site Scripting: DOM
Remediation Effort(Hrs): 0.1 Critical
Package: public.static.ZLMRTCClient
Location Analysis Info Analyzer
src/views/device/index.ts:33
Cross-Site Scripting: Poor Validation
Remediation Effort(Hrs): 0.2 Low
Package: src.views.platform
[2] CWE ID 089
CWE-89 is used to identify an "Improper Neutralization of Special Elements used in
an SQL Command ('SQL Injection')" weakness.
These weaknesses occur because "The software builds SQL with external input."
No Issues
[3] CWE ID 787
CWE-787 is used to identify a "Write to an Out-of-bounds Index" weakness.
These weaknesses occur because "Writing past the end of a buffer."
Package: src.views.chart
Remediation Effort(Hrs): 0.3 High
"""

    def test_parses_only_sections_with_issues(self):
        rows = _parse_fortify_cwe_top25_pdf(self.TEXT)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["漏洞名称"], "CWE-79 Cross-site Scripting")
        self.assertEqual(rows[0]["风险等级"], "严重")
        self.assertEqual(rows[0]["实例数"], 2)
        self.assertEqual(rows[0]["CWE"], "CWE-79")

    def test_level_takes_the_strongest_instance(self):
        rows = _parse_fortify_cwe_top25_pdf(self.TEXT)
        # 实例里同时有 Critical 和 Low，取 Critical
        self.assertEqual(rows[0]["风险等级"], "严重")
        self.assertEqual(rows[1]["风险等级"], "高危")

    def test_rejects_non_fortify_text(self):
        self.assertEqual(_parse_fortify_cwe_top25_pdf("普通报告 漏洞名称：SQL注入"), [])


class FortifyDevWorkbookTests(unittest.TestCase):
    TEXT = """Fortify Audit Workbench
Developer Workbook
demo-project
Results Outline
Dynamic Code Evaluation: Code Injection (1 issue)
Abstract
在运行时中解析用户控制的指令，会让攻击者有机会执行恶意代码。
Explanation
当程序员错误地认为由用户直接提供的指令仅会执行无害操作时，就会出现注入漏洞。
Recommendation
尽可能避免动态代码解析，绝不直接执行未验证的用户输入。
Issue Summary
Dynamic Code Evaluation: Code Injection Critical
Package: .src.lib.longmai
packages/zartd-law/src/lib/longmai/mToken.js, line 1029
Insecure Transport (64 issues)
Abstract
数据通过不加密的信道传输。
Explanation
HTTPS 应该用于所有主机名与资源。
Recommendation
启用 TLS 并校验证书。
Issue Summary
Insecure Transport Critical
Package: src/main.ts, line 20
"""

    def test_parses_categories_from_results_outline(self):
        rows = _parse_fortify_dev_workbook_pdf(self.TEXT)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["漏洞名称"], "Dynamic Code Evaluation: Code Injection")
        self.assertEqual(rows[0]["实例数"], 1)
        self.assertEqual(rows[0]["风险等级"], "严重")
        self.assertIn("避免动态代码解析", rows[0]["加固建议"])
        self.assertEqual(rows[1]["漏洞名称"], "Insecure Transport")
        self.assertEqual(rows[1]["实例数"], 64)

    def test_rejects_text_without_outline(self):
        self.assertEqual(_parse_fortify_dev_workbook_pdf("Fortify Audit Workbench\n无大纲正文"), [])


class AppScanTests(unittest.TestCase):
    TEXT = """Web 应用程序报告该报告由 HCL AppScan Standard 创建 10.0.0
目录介绍介绍常规信息摘要摘要问题类型按问题类型分类的问题按问题类型分类的问题SQL 注入1
摘要问题类型问题类型 9问题类型问题类型问题的数量 问题的数量高SQL 注入1
低“Content-Security-Policy”头缺失或不安全 5 低“X-Content-Type-Options”头缺失或不安全 5
低发现数据库错误模式1 低检测到隐藏目录2 低在参数值中找到了内部 IP 公开模式8
参发现内部 IP 泄露模式16 参应用程序错误2
有漏洞的有漏洞的 URL 29URL问题的数量 问题的数量
"""

    def test_parses_compressed_summary_rows(self):
        rows = _parse_appscan_pdf(self.TEXT)
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0]["漏洞名称"], "SQL 注入")
        self.assertEqual(rows[0]["风险等级"], "高危")
        self.assertEqual(rows[0]["实例数"], 1)
        # 名称里带"中"字的条目不能被级别字切断
        self.assertEqual(rows[5]["漏洞名称"], "在参数值中找到了内部 IP 公开模式")
        self.assertEqual(rows[5]["实例数"], 8)
        # 参考级映射为信息
        self.assertEqual(rows[6]["风险等级"], "信息")
        self.assertEqual(rows[7]["漏洞名称"], "应用程序错误")

    def test_rejects_text_without_appscan_marker(self):
        self.assertEqual(_parse_appscan_pdf("摘要问题类型 高SQL注入1 低XSS2"), [])


class ZapPdfTests(unittest.TestCase):
    TEXT = """ ZAP by Checkmarx Scanning
Report
http://10.11.1.1:32001
ZAP 2.16.1
1
2
SQL 2
Content Security Policy (CSP) Header Not Set 1
SQL
SQL
URL http://10.11.1.1:32001/api/getrec?id=1
GET
f926b10f' AND '1'='1' --
The page results were successfully manipulated.
URL http://10.11.1.1:32001/api/getrec?id=2
GET
The page results were successfully manipulated.
CWE Id 89
WASC Id 19
 Id 40018
Content Security Policy (CSP) Header Not Set
CSP provides a set of standard HTTP headers.
URL http://10.11.1.1:32001/index.html
GET
1
Ensure that your web server is configured.
CWE Id 693
WASC Id 15
 Id 10038
"""

    def test_parses_alert_blocks(self):
        rows = _parse_zap_pdf(self.TEXT)
        self.assertEqual(len(rows), 2)
        # 首块跳过报告头和汇总表后取到第一个告警
        self.assertEqual(rows[0]["漏洞名称"], "SQL")
        self.assertEqual(rows[0]["CWE"], "CWE-89")
        self.assertEqual(rows[0]["实例数"], 2)
        self.assertEqual(rows[1]["漏洞名称"], "Content Security Policy (CSP) Header Not Set")
        self.assertEqual(rows[1]["CWE"], "CWE-693")

    def test_dedupes_same_alert(self):
        rows = _parse_zap_pdf(self.TEXT)
        names = [r["漏洞名称"] for r in rows]
        self.assertEqual(len(names), len(set(names)))

    def test_rejects_text_without_cwe_blocks(self):
        self.assertEqual(_parse_zap_pdf("ZAP by Checkmarx\n没有详情块的报告"), [])


class ZapHtmlTests(unittest.TestCase):
    HTML = """<html><body>ZAP by Checkmarx Scanning Report
<section id="alert-type-counts"><h3>Alert Counts by Alert Type</h3><table>
<tr><th scope="row"><a href="#alert-type-0">易受攻击的 JS 库</a></th>
<td class="risk-level">高</td><td><span>2</span></td></tr>
<tr><th scope="row"><a href="#alert-type-1">Content Security Policy (CSP) Header Not Set</a></th>
<td class="risk-level">中</td><td><span>1</span></td></tr>
</table></section>
<section id="alert-type-0">
<h4>易受攻击的 JS 库</h4>
<table class="alerts-table">
<tr><th scope="row">CWE ID</th><td>1395</td></tr>
<tr><th scope="row">Alert description</th><td><p>The identified library appears to be vulnerable.</p></td></tr>
<tr><th scope="row">Other info</th><td>The identified library lodash, version 4.17.10 is vulnerable.</td></tr>
<tr><th scope="row">Solution</th><td><p>Upgrade to the latest version of the affected library.</p></td></tr>
</table></section>
<section id="alert-type-1">
<h4>Content Security Policy (CSP) Header Not Set</h4>
<table class="alerts-table">
<tr><th scope="row">Alert description</th><td>CSP is an added layer of security.</td></tr>
<tr><th scope="row">Solution</th><td>Ensure that your web server sets the header.</td></tr>
</table></section>
</body></html>"""

    def test_parses_summary_and_details(self):
        rows = _parse_zap_html(self.HTML)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["漏洞名称"], "易受攻击的 JS 库")
        self.assertEqual(rows[0]["风险等级"], "高危")
        self.assertEqual(rows[0]["实例数"], 2)
        self.assertIn("Upgrade to the latest version", rows[0]["加固建议"])
        self.assertEqual(rows[1]["加固建议"], "Ensure that your web server sets the header.")

    def test_rejects_non_zap_html(self):
        self.assertEqual(_parse_zap_html("<html><body>普通页面</body></html>"), [])


class TrivyTableTests(unittest.TestCase):
    TEXT = """Report Summary

┌──────────────────────┬──────┬─────────────────┐
│ Target               │ Type │ Vulnerabilities │
├──────────────────────┼──────┼─────────────────┤
│ modules/base/pom.xml │ pom  │        2        │
└──────────────────────┴──────┴─────────────────┘

modules/base/pom.xml (pom)
==========================
Total: 2 (UNKNOWN: 0, LOW: 0, MEDIUM: 2, HIGH: 0, CRITICAL: 0)

┌──────────────┬────────────────┬──────────┬──────────┬──────┬───────┬──────────────────────────────┐
│   Library    │ Vulnerability  │ Severity │  Status  │ Ins  │ Fixed │            Title             │
├──────────────┼────────────────┼──────────┼──────────┼──────┼───────┼──────────────────────────────┤
│ commons-lang │ CVE-2025-48924 │ MEDIUM   │ affected │ 2.6  │  2.9  │ commons-lang: Uncontrolled   │
│              │                │          │          │      │       │ recursion                    │
│              ├────────────────┼──────────┼──────────┼──────┼───────┼──────────────────────────────┤
│              │ CVE-2024-38819 │ MEDIUM   │ affected │      │ 6.1.14│ spring-webmvc: Path traversal│
│              │                │          │          │      │       │ vulnerability                │
└──────────────┴────────────────┴──────────┴──────────┴──────┴───────┴──────────────────────────────┘
"""

    def test_parses_entries_and_continuation_rows(self):
        rows = _parse_trivy_table_txt(self.TEXT)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["漏洞名称"], "CVE-2025-48924 commons-lang")
        self.assertEqual(rows[0]["风险等级"], "中危")
        self.assertEqual(rows[0]["CVE"], "CVE-2025-48924")
        # 续行的 Title 碎片要拼回完整描述，修复版本要带上
        self.assertIn("recursion", rows[0]["漏洞描述"])
        self.assertIn("2.9", rows[0]["漏洞描述"])
        self.assertIn("升级", rows[0]["加固建议"])
        self.assertEqual(rows[1]["CVE"], "CVE-2024-38819")


class OsvTableTests(unittest.TestCase):
    TEXT = """NAME                    INSTALLED     FIXED IN       TYPE          VULNERABILITY     SEVERITY
bcpkix-jdk15on          1.70          1.79           java-archive  CVE-2025-8916     Medium
bcprov-jdk15on          1.70                         java-archive  CVE-2023-33201    Medium
org.bouncycastle:bcprov 1.70                         java-archive  GHSA-xxxx-yyyy    Low
"""

    def test_parses_rows_with_and_without_fixed_version(self):
        rows = _parse_osv_table_txt(self.TEXT)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["漏洞名称"], "CVE-2025-8916 bcpkix-jdk15on")
        self.assertEqual(rows[0]["CVE"], "CVE-2025-8916")
        self.assertEqual(rows[0]["风险等级"], "中危")
        self.assertIn("1.79", rows[0]["加固建议"])
        # FIXED IN 为空的行：修复建议不写具体版本
        self.assertEqual(rows[1]["加固建议"], "升级 bcprov-jdk15on 至已修复版本。")
        # GHSA 编号不进 CVE 字段
        self.assertEqual(rows[2]["CVE"], "")
        self.assertEqual(rows[2]["风险等级"], "低危")

    def test_rejects_text_without_table_header(self):
        self.assertEqual(_parse_osv_table_txt("随机文本\nCVE-2024-1234 something"), [])


if __name__ == "__main__":
    unittest.main()


class JianshiHtmlTests(unittest.TestCase):
    """坚石诚信 HTML 报告；重点是别把 JS 渲染页/索引页的标题收成漏洞。"""

    REPORT = """越权
漏洞描述
未校验资源归属即可读取他人数据。
解决办法
接口层校验 owner。
敏感信息泄露
漏洞描述
响应里带回内部 IP。
解决办法
脱敏后返回。
"""

    def test_parses_blocks_with_description_and_fix(self):
        rows = _parse_jianshi_html(self.REPORT)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["漏洞名称"], "越权")
        self.assertIn("资源归属", rows[0]["漏洞描述"])
        self.assertIn("owner", rows[0]["加固建议"])

    def test_rejects_js_rendered_report_shell(self):
        """数据全在 script 里、正文只剩标题的扫描页，不能出一条漏洞。"""
        shell = (
            "Codex Security 批量扫描报告\n"
            "生成时间：2026-09-03 16:08 ｜ 共 7 个仓库 ｜ 共 21 个安全问题\n"
            "21 全部发现\n2 高严重度\n9 中严重度\n10 低严重度\n7 扫描仓库\n"
        )
        self.assertEqual(_parse_jianshi_html(shell), [])

    def test_rejects_report_index_page(self):
        """索引页只有标题和指向别处报告的链接。"""
        index = (
            "安全测试报告汇总\n"
            "以下为五份完整中文报告。原始 Markdown 报告保持不变。\n"
            "egova-urbanpro-core — 中文安全测试报告\n"
            "egova-urbanpro-mobile-framework-h5 — 中文安全测试报告\n"
            "说明：egova-urbanpro-sms-service 下的两个扫描目录为空。\n"
        )
        self.assertEqual(_parse_jianshi_html(index), [])


def _api_card(issue_id, badge, title, method, path, status, note="", analysis=""):
    return f"""<div class="card {badge.lower()}" id="{issue_id}">
<span class="badge badge-{badge.lower()}">{badge}</span>
<strong>{title}</strong>
<p style="margin-top: 10px;"><code>{method}</code> <span title="http://10.250.4.84:38080{path}">{path}</span></p>
<p style="color: #888; margin-top: 5px;">{note}</p>
<p style="margin-top: 6px;"><strong>越权状态:</strong> {status}</p>
<p style="color: #4ecdc4; margin-top: 8px; font-style: italic;">{analysis}</p>
</div>"""


class ApiSecurityScanHtmlTests(unittest.TestCase):
    """星揆 API 安全扫描报告；只收回放结论不是"通过"的接口。"""

    REPORT = (
        '<h2 id="auth-issues" class="section-toggle">鉴权问题 (未授权访问)</h2>'
        + _api_card(
            "auth-issue-1",
            "HIGH",
            "未授权访问",
            "POST",
            "/usercenter-api/oauth/get-token",
            "",
            "无需认证即可访问接口",
            "🤖 未携带任何凭证即可换取访问令牌。",
        )
        + '<h2 id="privilege-issues" class="section-toggle">越权问题 (权限控制)</h2>'
        + _api_card(
            "privilege-issue-1",
            "MEDIUM",
            "越权测试回放",
            "POST",
            "/unity/gis/user/updatemenus",
            "通过",
            "已完成高低权限回放",
            "🤖 操作的是当前登录用户自身菜单配置，属正常业务逻辑。",
        )
        + _api_card(
            "privilege-issue-2",
            "MEDIUM",
            "越权测试回放",
            "GET",
            "/unity/encryption/getencryptkey",
            "不通过",
            "已完成高低权限回放",
            "🤖 返回 256 字符加密密钥，低权限用户不应取得。",
        )
        + _api_card(
            "privilege-issue-3",
            "MEDIUM",
            "越权测试回放",
            "GET",
            "/unity/gis/wayline/theme/getlist",
            "待确认",
            "已完成高低权限回放",
            "🤖 高低权限响应完全一致，无法判断是否为公开配置。",
        )
    )

    def test_only_failing_and_unconfirmed_cards_are_kept(self):
        rows = _parse_api_security_scan_html(self.REPORT)
        names = [row["漏洞名称"] for row in rows]
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            names[0], "未授权访问 POST /usercenter-api/oauth/get-token"
        )
        self.assertIn("不通过", names[1])
        self.assertIn("待确认", names[2])
        self.assertEqual(rows[0]["风险等级"], "high")
        self.assertEqual(rows[1]["风险等级"], "medium")

    def test_endpoint_comes_from_visible_text_not_title(self):
        """title 里带着内网 IP 和端口，不能进对外交付物。"""
        rows = _parse_api_security_scan_html(self.REPORT)
        blob = repr(rows)
        self.assertNotIn("10.250.4.84", blob)
        self.assertNotIn("38080", blob)
        self.assertIn("/unity/encryption/getencryptkey", blob)

    def test_description_carries_verdict_and_analysis(self):
        rows = _parse_api_security_scan_html(self.REPORT)
        self.assertIn("不通过", rows[1]["漏洞描述"])
        self.assertIn("加密密钥", rows[1]["漏洞描述"])

    def test_rejects_other_html_reports(self):
        self.assertEqual(_parse_api_security_scan_html("<html><body>无卡片</body></html>"), [])
        zap = '<div class="alert"><h3>VULN-0001：越权</h3></div>'
        self.assertEqual(_parse_api_security_scan_html(zap), [])


class DependencyCheckCsvTests(unittest.TestCase):
    """OWASP dependency-check CSV：一行一个「组件 × CVE」，以前几乎全被丢弃。"""

    CSV = (
        '"Project","ScanDate","DependencyName","Description","License","CVE","CWE",'
        '"Vulnerability","Source","CVSSv2_Severity","CVSSv3_BaseSeverity","Name",'
        '"ShortDescription"\n'
        '"demo","Wed, 2 Sep 2026 21:37:06 +0800",app.jar: commons-compress-1.25.0.jar,'
        '"compression API",https://www.apache.org/licenses/LICENSE-2.0.txt,'
        '"CVE-2024-25710","CWE-835 Loop with Unreachable Exit Condition (\'Infinite Loop\')",'
        '"Loop with Unreachable Exit Condition (\'Infinite Loop\') vulnerability in Apache '
        'Commons Compress.This issue affects Apache Commons Compress: from 1.3 through 1.25.0.",'
        '"NVD","","MEDIUM","",""\n'
        '"demo","Wed, 2 Sep 2026 21:37:06 +0800",app.jar: liquibase-core-4.4.3.jar,'
        '"DB migration",https://www.apache.org/licenses/LICENSE-2.0.txt,'
        '"CVE-2022-0839","CWE-611 Improper Restriction of XML External Entity Reference",'
        '"Improper Restriction of XML External Entity Reference in GitHub repository '
        'liquibase/liquibase prior to 4.8.0.","NVD","","CRITICAL","",""\n'
    )

    def _parse(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dependency-check-report.csv"
            path.write_text(text, encoding="utf-8")
            return parse_report(path)

    def test_every_component_cve_row_becomes_a_vuln(self):
        result = self._parse(self.CSV)
        vulns = result["vulns"]
        self.assertEqual(result["total"], 2)
        self.assertEqual([v["cve"] for v in vulns], ["CVE-2024-25710", "CVE-2022-0839"])
        self.assertEqual([v["level"] for v in vulns], ["medium", "critical"])
        self.assertTrue(all(v["level_explicit"] for v in vulns))

    def test_name_keeps_component_and_short_title(self):
        result = self._parse(self.CSV)
        names = [v["name"] for v in result["vulns"]]
        self.assertIn("commons-compress-1.25.0.jar", names[0])
        self.assertNotIn("This issue affects", names[0])
        self.assertIn("liquibase-core-4.4.3.jar", names[1])
        self.assertEqual(result["vulns"][0]["cwe"], "CWE-835")

    def test_plain_csv_is_untouched(self):
        """不带 dependency-check 特征列的普通漏扫表仍走原 ALIASES 映射。"""
        plain = (
            "漏洞名称,风险等级,漏洞描述\n"
            "越权,高,未校验资源归属\n"
            "SQL注入,中,参数未转义\n"
        )
        result = self._parse(plain)
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["vulns"][0]["name"], "越权")
        self.assertEqual(result["vulns"][1]["level"], "medium")

    LONG_ROW = (
        '"demo","Wed, 2 Sep 2026 21:37:06 +0800",app.jar: shardingsphere-proxy-5.3.2.jar,'
        '"proxy",https://www.apache.org/licenses/LICENSE-2.0.txt,'
        '"CVE-2025-12345","CWE-89 Improper Neutralization of Special Elements",'
        '"Apache ShardingSphere-Proxy prior to 5.3.0 when using MySQL as database backend '
        "did not cleanup the database session completely after client authentication "
        'failed, which allowed an attacker to execute normal commands with the '
        'authenticated user, and then access the database.This issue affects Apache '
        'ShardingSphere-Proxy: from 5.0.0 through 5.3.2. This vulnerability is fixed in '
        '5.4.0.",'
        '"NVD","","HIGH","",""\n'
    )
    DISPUTED_ROW = (
        '"demo","Wed, 2 Sep 2026 21:37:06 +0800",app.jar: commons-jxpath-1.3.jar,'
        '"xpath",https://www.apache.org/licenses/LICENSE-2.0.txt,'
        '"CVE-2022-40352","CWE-611",'
        '"** DISPUTED ** This record was originally reported by the oss-fuzz project who '
        'failed to consider the security context in which JXPath is intended to be used '
        'and failed to contact the JXPath maintainers prior to requesting the CVE '
        'allocation.","NVD","","MEDIUM","",""\n'
    )

    def _row(self, data_row: str) -> str:
        return self.CSV.splitlines()[0] + "\n" + data_row

    def test_long_nvd_description_becomes_a_short_name(self):
        """整段 NVD 描述不能直接当名称：表格和章节标题会被撑坏。"""
        result = self._parse(self._row(self.LONG_ROW))
        vuln = result["vulns"][0]
        self.assertLessEqual(len(vuln["name"]), 110)
        self.assertNotIn("This issue affects", vuln["name"])
        self.assertNotIn("authenticated user", vuln["name"])
        # 全量描述一个字不丢
        self.assertIn("This issue affects Apache ShardingSphere-Proxy", vuln["description"])
        self.assertIn("fixed in 5.4.0", vuln["description"])

    def test_name_carries_cve_and_component(self):
        """不带 CVE 号就没法对账、查不了台账；标题截断后也靠它区分类别。"""
        result = self._parse(self._row(self.LONG_ROW))
        name = result["vulns"][0]["name"]
        self.assertIn("CVE-2025-12345", name)
        self.assertIn("shardingsphere-proxy-5.3.2.jar", name)

    def test_nvd_noise_prefix_is_dropped(self):
        result = self._parse(self._row(self.DISPUTED_ROW))
        name = result["vulns"][0]["name"]
        self.assertFalse(name.startswith("**"))
        self.assertNotIn("DISPUTED", name)
        self.assertIn("commons-jxpath-1.3.jar", name)

    def test_rows_sharing_a_prefix_stay_separate_classes(self):
        """同前缀不同 CVE 不能被截断合并成一类。"""
        result = self._parse(self._row(self.LONG_ROW.replace("CVE-2025-12345", "CVE-2025-12346")))
        self.assertEqual(result["total"], 1)
        single = self._parse(self._row(self.LONG_ROW))["vulns"][0]["name"]
        other = result["vulns"][0]["name"]
        self.assertNotEqual(single, other)
        self.assertIn("CVE-2025-12346", other)


class MdPentestReportTests(unittest.TestCase):
    MD = """# 渗透测试报告 — 测试平台（example.cn）

## 1. 执行摘要

本次测试发现一个认证缺陷。

## 4.2 完整漏洞清单

| 编号 | 漏洞名称 | 严重度 | CVSS | 验证 | 发现 Agent |
|------|---------|--------|------|------|-----------|
| AUTH-001 | SSO 任意用户会话伪造（根因） | 🔴 Critical | 9.8 | ✅ VERIFIED | auth |
| BL-02 | OAuth 授权码经开放重定向外泄 | 🟠 High | 7.1 | ✅ VERIFIED | bl |
| INFO-01 | 版本信息泄露 | 🟡 Low | 3.1 | ✅ | info |

## 5. 漏洞详情

### AUTH-001 · SSO 任意用户会话伪造（根因） 🔴

**描述**：SSO 子系统把加密用户名视为身份凭证，攻击者可用公开公钥离线伪造任意用户会话。

**修复建议**：authorize 必须校验调用方签名；公钥不可作为单独认证因子；改用服务端签发一次性票据。

### BL-02 · OAuth 授权码经开放重定向外泄 🟠

**描述**：授权码经开放重定向泄露给第三方站点。

**修复建议**：redirect_uri 严格白名单校验。
"""

    def test_parses_summary_table_with_details(self):
        rows = _parse_md_pentest_report(self.MD)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["漏洞名称"], "SSO 任意用户会话伪造（根因）")
        self.assertEqual(rows[0]["风险等级"], "严重")
        self.assertTrue(rows[0]["漏洞描述"].startswith("CVSS 9.8"))
        self.assertIn("一次性票据", rows[0]["加固建议"])
        self.assertEqual(rows[1]["风险等级"], "高危")
        self.assertEqual(rows[2]["风险等级"], "低危")

    def test_rejects_design_doc_markdown(self):
        self.assertEqual(
            _parse_md_pentest_report("# 登录超时设计\n\n## 方案\n\n用户 30 分钟无操作自动登出。"),
            [],
        )


from report_parser import _parse_md_pentest_report  # noqa: E402  (放底部避免打乱既有导入)
