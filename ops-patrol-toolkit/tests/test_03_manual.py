#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""03_manual_standardize 测试。

覆盖：extract 读取段落与表格；generate 产出 11 个标准章节 + 【待补充】占位段 +
自动回检 self_check P0=0（含 --sources 服务器/联系人表自动抽取落地）；check 对缺章节
手册报 P0；别名匹配命中（"变更记录" -> 文件变更记录）；疑似改名（内容证据兜底）P1；
术语变体 P2（命令行/词边界不误报）；缺 --info 文件 gap 退出码 2。

fixture 全部为虚构数据（IP 用 RFC5737 测试网段，电话用占位段），不含真实项目信息。
unittest 风格，pytest 兼容；临时产物只写 work/test_tmp/manual/（避免与其他并行 agent 撞名）。
"""

import contextlib
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "patrol" / "manual"
TMP = ROOT / "work" / "test_tmp" / "manual"

sys.path.insert(0, str(SCRIPTS))

import docx_io  # noqa: E402

# 模块名以数字开头，不能常规 import，用 importlib 按路径加载
_spec = importlib.util.spec_from_file_location(
    "manual_standardize_03", SCRIPTS / "03_manual_standardize.py")
mod = importlib.util.module_from_spec(_spec)
sys.modules["manual_standardize_03"] = mod
_spec.loader.exec_module(mod)

SRC_DOCX = FIXTURES / "资料样例.docx"
BAD_DOCX = FIXTURES / "不合规手册样例.docx"
INFO_JSON = FIXTURES / "project_info.json"


def _last_json(text):
    return json.loads(text.strip().splitlines()[-1])


def _call(argv):
    """运行 CLI 子命令，返回 (rc, stdout_text)。失败路径的 SystemExit 向上抛由用例断言。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.main(list(argv))
    return rc, buf.getvalue()


def _load_structure():
    return json.loads((ROOT / "references" / "standard-structure.json").read_text(encoding="utf-8"))


def _load_terms():
    return json.loads((ROOT / "references" / "terminology.json").read_text(encoding="utf-8"))["terms"]


class Test03Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TMP.mkdir(parents=True, exist_ok=True)
        for f in (SRC_DOCX, BAD_DOCX, INFO_JSON):
            if not f.is_file():
                raise AssertionError("缺少合成 fixture: %s" % f)


class TestExtract(Test03Base):
    def test_extract_reads_paragraphs_and_tables(self):
        """extract 读取段落（含标题层级/样式）与表格，落盘 JSON 且信封计数一致。"""
        out = TMP / "extracted.json"
        rc, text = _call(["extract", "--docx", str(SRC_DOCX), "--out", str(out)])
        self.assertEqual(rc, 0)
        env = _last_json(text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["tables"], 2)
        self.assertEqual(env["headings"], 1)
        data = json.loads(out.read_text(encoding="utf-8"))
        # 服务器表整表可读，IP 列在位
        self.assertEqual(data["tables"][0][0],
                         ["设备名称", "IP地址", "操作系统", "配置", "用途", "部署服务"])
        self.assertEqual(data["tables"][0][1][1], "192.0.2.10")
        # 联系人表在位
        self.assertEqual(data["tables"][1][0], ["姓名", "单位", "职位", "电话", "负责事项"])
        # 段落：标题带 level，正文含访问地址 URL
        paras = data["paragraphs"]
        self.assertTrue(any(p["type"] == "heading" and p["level"] == 1 for p in paras))
        self.assertTrue(any("http://192.0.2.10:8080/app" in p["text"] for p in paras))
        self.assertTrue(all("style" in p for p in paras))

    def test_extract_missing_docx_gap_exit_2(self):
        """docx 缺失：gap 信封 + 退出码 2，不猜测不伪装成功。"""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                mod.main(["extract", "--docx", str(TMP / "no_such.docx"),
                          "--out", str(TMP / "no_such.json")])
        self.assertEqual(cm.exception.code, 2)
        env = _last_json(buf.getvalue())
        self.assertFalse(env["ok"])
        self.assertIn("no_such.docx", env["gap"])


class TestGenerate(Test03Base):
    def test_generate_11_sections_placeholders_and_self_check_p0_zero(self):
        """generate 产出 11 个标准章节 + 【待补充】占位段 + 【待复核】标记，
        --sources 抽取的服务器/联系人/URL 落进手册，自动回检 self_check P0=0。"""
        out = TMP / "draft.docx"
        rc, text = _call(["generate", "--info", str(INFO_JSON),
                          "--sources", str(SRC_DOCX), "--out", str(out)])
        self.assertEqual(rc, 0)
        env = _last_json(text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["sections"], 11)
        self.assertEqual(env["self_check"]["p0"], 0)
        self.assertGreaterEqual(env["placeholders"], 3)  # 硬件/工具地址/常见问题 + 待复核标记段

        paras = docx_io.read_paragraphs(str(out))
        head1 = [p["text"] for p in paras if (p["style"] or "").startswith("Heading1")]
        for sec in _load_structure()["required_sections"]:
            self.assertIn(sec["name"], head1)  # 11 个标准章节标题逐一在位
        self.assertTrue(any(p["style"] == "Placeholder" and "待补充" in p["text"] for p in paras))
        self.assertTrue(any("【待复核】" in p["text"] for p in paras))

        tables = docx_io.read_tables(str(out))
        flat = "\n".join("|".join(r) for t in tables for r in t)
        self.assertIn("192.0.2.10", flat)                    # --sources 自动抽取的服务器行
        self.assertIn("13800000001", flat)                   # 自动抽取的联系人行
        self.assertIn("http://192.0.2.10:8080/app", flat)    # 自动抽取的访问地址
        para_flat = "\n".join(p["text"] for p in paras)
        self.assertIn("01:00", para_flat)                    # --info 的备份时间进入手册段落
        self.assertTrue(Path(env["self_check"]["report"]).is_file())  # 回检差异清单随初稿落盘

    def test_generate_missing_info_gap_exit_2(self):
        """缺 --info 参数或 --info 文件不存在：gap 信封 + 退出码 2。"""
        # 情形一：未提供 --info 参数
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                mod.main(["generate", "--sources", str(SRC_DOCX),
                          "--out", str(TMP / "noinfo.docx")])
        self.assertEqual(cm.exception.code, 2)
        env = _last_json(buf.getvalue())
        self.assertFalse(env["ok"])
        self.assertIn("--info", env["gap"])

        # 情形二：--info 指向不存在的文件
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                mod.main(["generate", "--info", str(TMP / "no_such_info.json"),
                          "--out", str(TMP / "noinfo2.docx")])
        self.assertEqual(cm.exception.code, 2)
        env = _last_json(buf.getvalue())
        self.assertFalse(env["ok"])
        self.assertIn("no_such_info.json", env["gap"])


class TestCheck(Test03Base):
    def test_check_reports_p0_for_missing_sections(self):
        """check 对缺 5 个章节的烂手册报 P0=5；差异清单带【待复核】与四级结构。"""
        out_md = TMP / "bad_diff.md"
        rc, text = _call(["check", "--manual", str(BAD_DOCX), "--out", str(out_md)])
        self.assertEqual(rc, 0)
        env = _last_json(text)
        self.assertTrue(env["ok"])
        self.assertEqual(env["total_sections"], 11)
        self.assertEqual(env["p0"], 5)   # 服务器部署信息/应用软件系统/互联网专线/端口映射/硬件部分
        self.assertEqual(env["p1"], 1)   # 备份计划疑似改名（内容证据兜底）
        self.assertEqual(env["p2"], 2)   # tomcat / mysql 两组术语变体
        rep = out_md.read_text(encoding="utf-8")
        self.assertIn("【待复核】", rep)
        self.assertIn("缺失章节（P0", rep)
        self.assertIn("疑似改名待人工审核（P1", rep)
        self.assertIn("术语不统一（P2", rep)
        self.assertIn("服务器部署信息", rep)   # P0 清单里出现缺失章节
        self.assertIn("数据保护安排", rep)     # 疑似改名证据里出现实际标题
        self.assertIn("章节完整度 | 5 / 11", rep)

    def test_alias_match_and_renamed_evidence(self):
        """别名命中不判缺失（"变更记录"->文件变更记录）；
        改名章节走内容证据兜底降级 P1"疑似改名"而非 P0；子章节不因父章节缺失被重复计数。"""
        report = mod.audit_manual(str(BAD_DOCX), _load_structure(), _load_terms())
        matched_ids = [x["section"]["id"] for x in report["matched"]]
        self.assertIn("change-log", matched_ids)  # 别名"变更记录"命中

        missing_names = [s["name"] for s in report["missing"]]
        for name in ("服务器部署信息", "应用软件系统", "互联网专线", "端口映射", "硬件部分"):
            self.assertIn(name, missing_names)
        self.assertNotIn("备份计划", missing_names)      # 有内容证据，降级 P1
        self.assertEqual(missing_names.count("应用软件系统"), 1)  # 父章节缺失时子章节不重复计数

        renamed = {item["section"]["id"]: item["evidence"] for item in report["renamed"]}
        self.assertIn("backup-plan", renamed)
        ev = renamed["backup-plan"][0]
        self.assertEqual(ev["hit"], "备份")
        self.assertIn("本地备份", ev["text"])           # 证据带命中片段与位置
        self.assertTrue(ev["location"])

        # 完整手册要素核验：烂手册中存在的章节要素不误报
        self.assertEqual(report["element_missing"], [])
        self.assertEqual(report["style_issues"], [])
        self.assertIn("某园区监控系统运维文档", report["extra_headings"])

    def test_terminology_variants_p2_and_command_skip(self):
        """术语变体计入 P2；命令行忽略、词边界不误报（mysqld 不算 mysql 变体）。"""
        tiny = TMP / "tiny.docx"
        docx_io.make_document(tiny, [
            {"type": "h", "level": 1, "text": "附录说明"},
            {"type": "p", "text": "系统使用 tomcat 与 nginx 提供服务。"},
            {"type": "p", "text": "systemctl start mysqld"},
            {"type": "p", "text": "访问入口 https://192.0.2.10/app 需要账号"},
        ])
        report = mod.audit_manual(str(tiny), _load_structure(), _load_terms())
        tf = report["term_findings"]
        self.assertEqual(tf["tomcat"]["standard"], "Tomcat")
        self.assertEqual(tf["nginx"]["standard"], "Nginx")
        self.assertNotIn("mysql", tf)      # mysqld 词边界拦截 + 命令行忽略双保险
        self.assertNotIn("mysqld", tf)
        # 表格单元里的变体同样计入，位置标注"表格N"
        tbl_doc = TMP / "tbl.docx"
        docx_io.make_document(tbl_doc, [
            {"type": "h", "level": 1, "text": "资产"},
            {"type": "table", "rows": [["组件", "版本"], ["tomcat", "8.5"]], "header": True},
        ])
        report2 = mod.audit_manual(str(tbl_doc), _load_structure(), _load_terms())
        self.assertIn("tomcat", report2["term_findings"])
        self.assertTrue(any(loc.startswith("表格") for loc in
                            report2["term_findings"]["tomcat"]["locations"]))

    def test_check_missing_manual_gap_exit_2(self):
        """待检手册文件缺失：gap 信封 + 退出码 2。"""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                mod.main(["check", "--manual", str(TMP / "no_such_manual.docx")])
        self.assertEqual(cm.exception.code, 2)
        env = _last_json(buf.getvalue())
        self.assertFalse(env["ok"])
        self.assertIn("no_such_manual.docx", env["gap"])


if __name__ == "__main__":
    unittest.main()
