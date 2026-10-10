import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from report_parser import (
    _parse_cn_audit_detail_pdf,
    _parse_cn_source_scan_pdf,
    _parse_qijian_strix_html,
    _parse_seczone_iast_pdf,
    normalize_rows,
    parse_report,
)


class ReportParserTests(unittest.TestCase):
    def test_csv_aliases_are_normalized(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.csv"
            path.write_text(
                "漏洞名称,风险等级,漏洞描述,整改建议,漏洞地址\n"
                "CORS配置不当,中危,来源校验不足,配置域名白名单,https://example.test/a\n",
                encoding="utf-8",
            )
            result = parse_report(path)
        self.assertEqual(result["total"], 1)
        vuln = result["vulns"][0]
        self.assertEqual(vuln["name"], "CORS配置不当")
        self.assertEqual(vuln["level"], "medium")
        self.assertEqual(vuln["fix_suggestion"], "配置域名白名单")
        self.assertEqual(vuln["urls"], ["https://example.test/a"])

    def test_json_items_are_normalized(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(
                '{"items":[{"title":"弱口令","severity":"high","remediation":"修改密码策略"}]}',
                encoding="utf-8",
            )
            result = parse_report(path)
        self.assertEqual(result["vulns"][0]["level"], "high")
        self.assertEqual(result["vulns"][0]["fix_suggestion"], "修改密码策略")

    def test_docx_heading_styles_do_not_split_body_text(self):
        from docx import Document

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.docx"
            document = Document()
            document.add_heading("【高危】SQL注入", level=2)
            document.add_paragraph("漏洞描述：")
            document.add_paragraph("攻击者利用注入漏洞读取数据库信息。")
            document.add_paragraph("测试过程：")
            document.add_paragraph("该接口存在SQL注入漏洞。")
            document.add_paragraph("加固建议：")
            document.add_paragraph("使用参数化查询。")
            document.add_heading("【中危】详细的报错信息*2", level=2)
            document.add_paragraph("漏洞危害：")
            document.add_paragraph("错误信息可能泄露数据库连接信息。")
            document.save(path)

            result = parse_report(path)

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["vulns"][0]["name"], "SQL注入")
        self.assertIn("该接口存在SQL注入漏洞", result["vulns"][0]["description"])
        self.assertEqual(result["vulns"][0]["fix_suggestion"], "使用参数化查询。")
        self.assertEqual(result["vulns"][1]["name"], "详细的报错信息*2")

    def test_docx_numbered_items_with_suggestion_labels(self):
        """编号条目式漏洞清单：条目名不含"漏洞/注入"等关键词，靠后面的"建议："反推。"""
        from docx import Document

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.docx"
            document = Document()
            document.add_paragraph("1、硬编码明文默认口令")
            document.add_paragraph("建议：默认口令使用随机数生成，不要使用硬编码固定口令")
            document.add_paragraph("2、微服务接口签名弱哈希加密")
            document.add_paragraph("建议：使用强加密方式对签名进行加密")
            document.save(path)

            result = parse_report(path)

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["vulns"][0]["name"], "硬编码明文默认口令")
        self.assertEqual(
            result["vulns"][0]["fix_suggestion"], "默认口令使用随机数生成，不要使用硬编码固定口令"
        )
        self.assertEqual(result["vulns"][1]["name"], "微服务接口签名弱哈希加密")

    def test_docx_inline_section_content_is_kept(self):
        """"漏洞描述：xxx"与标签同行时，内容要落到规范字段而不是英文键。"""
        from docx import Document

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.docx"
            document = Document()
            document.add_heading("【高危】越权访问", level=2)
            document.add_paragraph("漏洞描述：未校验归属即可查看他人订单。")
            document.add_paragraph("加固建议：服务端校验资源归属。")
            document.save(path)

            result = parse_report(path)

        self.assertEqual(result["total"], 1)
        self.assertIn("未校验归属", result["vulns"][0]["description"])
        self.assertEqual(result["vulns"][0]["fix_suggestion"], "服务端校验资源归属。")

    def test_cn_source_scan_pdf_groups_by_defect_type(self):
        """国产静态源代码扫描报告按缺陷类型出条，例数合计要与报告统计一致。"""
        text = (
            "源代码扫描分析报告\n"
            "中正检测\n"
            "漏洞名称 风险类别 不可用 已确认 高优先 待评审 总计\n"
            "反射型跨站脚本攻击 高 0 40 0 0 40\n"
            "弱哈希 中 0 1 0 0 1\n"
            "已确认\n"
            "漏洞名称 风险类别 漏洞数量\n"
            "反射型跨站脚本攻击 高 40\n"
            "弱哈希 中 1\n"
            "反射型跨站脚本攻击   ( 40例) \n"
            "Path1:\n"
            "入口点 \\app\\web\\A.java\n"
            "出口点 \\app\\web\\A.java\n"
            "审计备注\n"
            "弱哈希   ( 1例) \n"
            "Path1:\n"
            "入口点 \\app\\util\\MD5Utils.java\n"
            "审计备注\n"
        )
        rows = _parse_cn_source_scan_pdf(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["漏洞名称"], "反射型跨站脚本攻击")
        self.assertEqual(rows[0]["风险等级"], "高")
        self.assertIn("共 40 例", rows[0]["漏洞描述"])
        self.assertIn("A.java", rows[0]["漏洞描述"])
        self.assertEqual(rows[1]["风险等级"], "中")
        self.assertIn("MD5Utils.java", rows[1]["漏洞描述"])
        # 没有"（N例）"结构的普通文本不能误入这条路
        self.assertEqual(_parse_cn_source_scan_pdf("一份普通的安全通报正文"), [])

    def test_seczone_iast_pdf_groups_by_weakness_type(self):
        """安全岛 IAST 报告按弱点类型出条，实例数取状态标记数，等级原样透传。"""
        text = (
            "一体化平台 /让企业交付更安全的软件\n"
            "22 / 60\n"
            "安全弱点分布\n"
            "安全弱点详情:\n"
            "SQL注入\n"
            "严重性： 高\n"
            "风险： 用户输入未校验时会破坏sql语句结构。\n"
            "解决方法： 使用ORM框架与参数化查询。\n"
            "安全弱点：\n"
            "DEFEB035099. /api/a 页面存在SQL注入\n"
            "状态： 新发现\n"
            "安全弱点：\n"
            "DEFEB035100. /api/b 页面存在SQL注入\n"
            "状态： 新发现\n"
            "一体化平台 /让企业交付更安全的软件\n"
            "43 / 60\n"
            "缺少CSP响应头\n"
            "严重性： 建议\n"
            "风险： 未配置CSP时攻击者可注入脚本。\n"
            "解决方法： 设置Content-Security-Policy响应头，参考 vulHunter.seczone.cn。\n"
            "安全弱点：\n"
            "DEFEB035095. 有40个页面缺少CSP响应头\n"
            "状态： 新发现\n"
        )
        rows = _parse_seczone_iast_pdf(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["漏洞名称"], "SQL注入")
        self.assertEqual(rows[0]["风险等级"], "高")
        self.assertEqual(rows[0]["实例数"], 2)
        self.assertIn("/api/a", rows[0]["漏洞描述"])
        self.assertEqual(rows[0]["加固建议"], "使用ORM框架与参数化查询。")
        self.assertEqual(rows[1]["漏洞名称"], "缺少CSP响应头")
        self.assertEqual(rows[1]["风险等级"], "建议")
        self.assertEqual(rows[1]["实例数"], 1)
        # 没有 seczone 结构的普通文本不能误入这条路
        self.assertEqual(_parse_seczone_iast_pdf("一份普通的安全通报正文"), [])

    def test_seczone_iast_pdf_levels_normalize(self):
        """"建议"级要落到 info，不能掉默认 medium，否则中危以上过滤会误纳。"""
        text = (
            "安全弱点分布\n"
            "缺少CSP响应头\n"
            "严重性： 建议\n"
            "风险： 未配置CSP。\n"
            "解决方法： 配置响应头。\n"
            "安全弱点：\n"
            "DEFEB035095. 有40个页面缺少CSP响应头\n"
            "状态： 新发现\n"
            "vulHunter.seczone.cn\n"
        )
        vulns = normalize_rows(_parse_seczone_iast_pdf(text), "seczone.pdf")
        self.assertEqual(vulns[0]["level"], "info")
        self.assertTrue(vulns[0]["level_explicit"])

    def test_qijian_strix_html_groups_by_vuln_heading(self):
        """麒舰 strix HTML 报告按 VULN 标题出条，端点并进描述，方案取修复方案节。"""
        html = (
            "<html><body><h2>三、漏洞详情</h2>"
            "<h3>VULN-0002：存储型SpEL注入（通过规则引擎实现RCE）</h3>"
            "<p>不受限制的StandardEvaluationContext评估可写入的规则表达式</p>"
            "<p>严重</p><p>CVSS评分：</p><p>9.9</p>"
            "<p>端点：</p><p>POST /ms/rule/save-or-update</p>"
            "<p>CWE：</p><p>CWE-94</p>"
            "<h4>漏洞描述</h4><p>规则引擎执行存储的规则表达式。</p>"
            "<h4>影响分析</h4><p>可远程执行任意命令。</p>"
            "<h4>修复建议</h4>"
            "<h4>修复方案</h4><p>改用SimpleEvaluationContext只读绑定。</p>"
            "<h3>VULN-0004：存储型SQL注入（通过SQL类型规则）</h3>"
            "<p>高危</p><p>CVSS评分：</p><p>8.6</p>"
            "<h4>漏洞描述</h4><p>规则体作为原始SQL执行。</p>"
            "<h4>修复方案</h4><p>改用参数化查询。</p>"
            "</body></html>"
        )
        rows = _parse_qijian_strix_html(html)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["漏洞名称"], "存储型SpEL注入（通过规则引擎实现RCE）")
        self.assertEqual(rows[0]["风险等级"], "严重")
        self.assertEqual(rows[0]["实例数"], 1)
        self.assertIn("端点：POST /ms/rule/save-or-update", rows[0]["漏洞描述"])
        self.assertIn("可远程执行任意命令", rows[0]["漏洞描述"])
        self.assertEqual(rows[0]["加固建议"], "改用SimpleEvaluationContext只读绑定。")
        self.assertEqual(rows[0]["CWE"], "CWE-94")
        self.assertEqual(rows[1]["漏洞名称"], "存储型SQL注入（通过SQL类型规则）")
        self.assertEqual(rows[1]["风险等级"], "高危")
        self.assertEqual(rows[1]["加固建议"], "改用参数化查询。")
        # 没有 VULN 编号标题的普通页面不能误入这条路
        self.assertEqual(_parse_qijian_strix_html("<html><p>普通通报</p></html>"), [])

    def test_qijian_strix_html_levels_normalize(self):
        html = (
            "<h3>VULN-0001：越权访问</h3><p>低危</p>"
            "<h4>漏洞描述</h4><p>未做权限校验。</p>"
            "<h4>修复方案</h4><p>加权限注解。</p>"
        )
        vulns = normalize_rows(_parse_qijian_strix_html(html), "report.html")
        self.assertEqual(vulns[0]["level"], "low")
        self.assertTrue(vulns[0]["level_explicit"])

    def test_cn_audit_detail_pdf_uses_numbered_heading_as_name(self):
        text = (
            "省级城市运行管理服务平台代码审计\n"
            "脆弱性汇总表\n"
            "序号 系统名称 漏洞名称 脆弱性描述 漏洞等级\n"
            "1. \n省级城市运\n行管理服务\n平台 \nSQL 注入 \nMyBatis 中${}是字符串直接拼接 中 \n"
            "\n"
            "1、SQL 注入  \n"
            "漏洞描述： \n"
            "不受信赖的数据由 queryForList 返回，攻击者可发送恶意 SQL 查询。 \n"
            "漏洞类型：安全功能 \n"
            "漏洞等级：中 \n"
            "漏洞链接： \n"
            "/src/main/A.java \n"
            "整改建议： \n"
            "使用 PreparedStatement 的 setString 设置参数变量。 \n"
            "2、弱加密哈希算法  \n"
            "漏洞描述： \n"
            "MD5、SHA-1 已被证实不安全。 \n"
            "漏洞等级：中 \n"
            "整改建议： \n"
            "调整使用 SM3、SHA256 等算法。 \n"
        )
        rows = _parse_cn_audit_detail_pdf(text)
        self.assertEqual(
            [row["漏洞名称"] for row in rows], ["SQL 注入", "弱加密哈希算法"]
        )
        self.assertEqual(rows[0]["风险等级"], "中")
        self.assertIn("PreparedStatement", rows[0]["加固建议"])
        self.assertIn("queryForList", rows[0]["漏洞描述"])

    def test_cn_audit_detail_pdf_rejects_numbered_text_without_labels(self):
        self.assertEqual(_parse_cn_audit_detail_pdf("漏洞描述 四个字出现在正文里"), [])
        # 编号条目后面没有任何详情小标签时，整份都不出条目
        self.assertEqual(
            _parse_cn_audit_detail_pdf("1、第一项\n2、第二项\n普通说明文字，没有小标签"),
            [],
        )

    def test_weak_point_name_column_is_aliased(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scan.csv"
            path.write_text(
                "扫描目标,分类,弱点名称,风险等级,涉事地址\n"
                "http://10.0.0.1,WEB,存在漏洞的JavaScript库,中危,http://10.0.0.1/a\n",
                encoding="utf-8",
            )
            result = parse_report(path)
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["vulns"][0]["name"], "存在漏洞的JavaScript库")
        self.assertEqual(result["vulns"][0]["level"], "medium")

    def test_risk_name_column_is_aliased(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "baseline.csv"
            path.write_text(
                "主机名,IP,风险名,风险类型,风险详情\n"
                "db-1,172.26.169.174,弱口令-Linux系统登录弱口令,弱口令,检查项目 系统登录弱口令\n",
                encoding="utf-8",
            )
            result = parse_report(path)
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["vulns"][0]["name"], "弱口令-Linux系统登录弱口令")

    def test_instance_count_column_is_carried(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scan.csv"
            path.write_text(
                "缺陷类型,实例数\nSQL 注入,37\n弱哈希,1\n",
                encoding="utf-8",
            )
            result = parse_report(path)
        self.assertEqual([row["instances"] for row in result["vulns"]], [37, 1])


if __name__ == "__main__":
    unittest.main()
