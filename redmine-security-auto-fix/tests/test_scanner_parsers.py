import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from report_parser import (
    _parse_appscan_pdf,
    _parse_fortify_cwe_top25_pdf,
    _parse_fortify_dev_workbook_pdf,
    _parse_osv_table_txt,
    _parse_trivy_table_txt,
    _parse_zap_html,
    _parse_zap_pdf,
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
