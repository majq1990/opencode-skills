import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from recommendation_engine import _build_web_query, enrich_vulnerability


class _StubBridge:
    def search_internal(self, query):
        return {"ordered": [], "external_intel": []}


class WebQueryRedlineTests(unittest.TestCase):
    """红线：互联网查询词不得带客户名称、内网地址、案件正文。"""

    def test_cve_only_query_drops_the_report_name(self):
        query = _build_web_query(
            {
                "name": "Apache HTTP Server 安全漏洞(CVE-2024-38473)",
                "cve": "CVE-2024-38473",
            }
        )
        self.assertEqual(query, "CVE-2024-38473 安全 漏洞 修复 加固 官方建议")

    def test_case_narrative_is_not_sent_to_the_internet(self):
        # 案件470125的原始条目名：整句都是案情，含客户单位和内网描述
        name = (
            "利用Log4j2远程代码执行漏洞获取本溪市人民政府办公室互联网系统主机管理员权限，"
            "通过内网横向攻击突破隔离进入辽宁省级政府内网网络。"
        )
        self.assertEqual(_build_web_query({"name": name}), "")

    def test_province_level_narrative_is_dropped(self):
        self.assertEqual(_build_web_query({"name": "突破进入辽宁省政务网络"}), "")

    def test_short_type_name_survives(self):
        self.assertEqual(
            _build_web_query({"name": "利用log4j2漏洞"}),
            "利用log4j2漏洞 安全 漏洞 修复 加固 官方建议",
        )

    def test_section_prefix_is_stripped_before_query(self):
        self.assertEqual(
            _build_web_query({"name": "2.1.1【已关闭-已修复】（中危）pprof服务器信息泄露 1"}),
            "pprof服务器信息泄露 安全 漏洞 修复 加固 官方建议",
        )

    def test_long_name_is_truncated(self):
        # 上限按"写得再长的漏洞类型名"定，不是案情描述的拦截线——
        # 拦案情的是 _PROSE_MARK，这里只保证超长名称不会整条外发
        query = _build_web_query({"name": "跨站脚本攻击漏洞" * 6})
        self.assertLessEqual(len(query.split(" 安全")[0]), 40)

    def test_long_type_name_survives_whole(self):
        # 漏扫/代码审计的长类型名要整条进查询词，被腰斩就检索不到
        for name in (
            "HTTPS会话中的敏感cookie没有设置安全属性",
            "客户端潜在的跨站脚本攻击（存储型）",
            "使用不够随机的伪随机数生成器生成安全敏感值",
        ):
            self.assertEqual(
                _build_web_query({"name": name}),
                f"{name} 安全 漏洞 修复 加固 官方建议",
            )

    def test_narrative_name_never_survives_the_cap(self):
        # 把上限放大也换不来泄漏：这些超长名称仍必须被 _PROSE_MARK 拦掉
        for name in (
            "利用Log4j2远程代码执行漏洞获取某单位互联网系统主机管理员权限并进一步横向移动",
            "攻击者通过上传 webshell 获取服务器权限后植入后门长期控制",
            "突破网络隔离进入省级政务内网后对核心业务系统进行批量数据窃取",
        ):
            self.assertEqual(_build_web_query({"name": name}), "")

    def test_unusable_name_marks_web_search_as_not_required(self):
        result = enrich_vulnerability(
            {
                "name": "利用Log4j2远程代码执行漏洞获取某单位互联网系统主机管理员权限，"
                "通过内网横向攻击突破隔离进入省级政府内网网络。",
                "level": "high",
                "fix_suggestion": "",
            },
            _StubBridge(),
            internal={"ordered": [], "external_intel": []},
        )
        self.assertFalse(result["web_search"]["required"])
        self.assertEqual(result["web_search"]["query"], "")
        self.assertIn("人工确认", result["web_search"]["reason"])


if __name__ == "__main__":
    unittest.main()
