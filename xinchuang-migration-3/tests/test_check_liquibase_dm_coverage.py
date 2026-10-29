# -*- coding: utf-8 -*-
"""check_liquibase_dm_coverage 单测：构造 changelog fixture，核对四类判定与门禁退出码。

同时带 Mimosa 口径的回归护栏：不连库、不执行 SQL、不留 CLI 可控写路径、无凭据字面量、
不用会做实体扩展的 XML 解析入口。
"""
import json
import re
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_liquibase_dm_coverage import (  # noqa: E402
    audit_changelog, audit_dir, audit_jar, dbms_matches, main, render,
)

SRC = Path(__file__).resolve().parent.parent / "scripts" / "check_liquibase_dm_coverage.py"

NS = 'xmlns="http://www.liquibase.org/xml/ns/dbchangelog"'


def _wrap(body: str) -> str:
    return "<databaseChangeLog " + NS + ">\n" + body + "\n</databaseChangeLog>\n"


def test_dbms_matches_semantics():
    assert dbms_matches("") is True
    assert dbms_matches("dm") is True
    assert dbms_matches("mysql, dm") is True
    assert dbms_matches("mysql, oracle") is False
    assert dbms_matches("!dm") is False
    assert dbms_matches("!mysql, dm") is True
    assert dbms_matches("DM") is True


def test_ok_when_dm_branch_present():
    rep = audit_changelog(_wrap(
        '<changeSet id="a" author="u">'
        '<sql dbms="mysql">select 1</sql>'
        '<sql dbms="dm">select 1</sql>'
        "</changeSet>"))
    assert rep["counts"]["OK"] == 1
    assert rep["counts"]["NOOP"] == 0


def test_noop_when_all_sql_excluded_by_dbms():
    rep = audit_changelog(_wrap(
        '<changeSet id="b" author="u">'
        '<sql dbms="mysql">select 1</sql>'
        '<sql dbms="oracle">select 2</sql>'
        "</changeSet>"))
    assert rep["counts"]["NOOP"] == 1
    cs = rep["changesets"][0]
    assert cs["id"] == "b"
    assert "mysql" in cs["reason"] and "oracle" in cs["reason"]


def test_skip_when_changeset_level_dbms_excludes_dm():
    rep = audit_changelog(_wrap(
        '<changeSet id="c" author="u" dbms="oracle">'
        "<sql>select 1</sql>"
        "</changeSet>"))
    assert rep["counts"]["SKIP"] == 1
    assert "changeSet 级" in rep["changesets"][0]["reason"]


def test_skip_when_precondition_dbms_excludes_dm():
    rep = audit_changelog(_wrap(
        '<changeSet id="d" author="u">'
        "<preConditions><dbms type=\"mysql\"/></preConditions>"
        "<sql>select 1</sql>"
        "</changeSet>"))
    assert rep["counts"]["SKIP"] == 1
    assert "preConditions" in rep["changesets"][0]["reason"]


def test_meta_when_no_sql_child():
    rep = audit_changelog(_wrap(
        '<changeSet id="e" author="u">'
        '<createTable tableName="t"><column name="a" type="int"/></createTable>'
        "</changeSet>"))
    assert rep["counts"]["META"] == 1
    assert rep["counts"]["NOOP"] == 0


def test_sqlfile_tag_is_treated_as_sql():
    rep = audit_changelog(_wrap(
        '<changeSet id="f" author="u">'
        '<sqlFile dbms="mysql" path="x.sql"/>'
        "</changeSet>"))
    assert rep["counts"]["NOOP"] == 1


def test_includes_are_reported_not_followed():
    rep = audit_changelog(_wrap('<include file="other.xml" relativeToChangelogFile="true"/>'))
    assert rep["includes"] == ["other.xml"]
    assert rep["total"] == 0


def test_non_changelog_root_is_flagged():
    rep = audit_changelog("<other/>", source="x.xml")
    assert rep["error"]
    assert rep["total"] == 0


def test_broken_xml_is_flagged_not_raised():
    rep = audit_changelog("<databaseChangeLog><changeSet>", source="bad.xml")
    assert "XML 解析失败" in rep["error"]


def test_xml_declaration_and_encoding_are_tolerated():
    """带 XML 声明的正常 changelog 必须照常解析，不能因为硬化解析器误杀。"""
    rep = audit_changelog(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + _wrap('<changeSet id="k" author="u">'
                '<sql dbms="mysql">x</sql>'
                '<sql dbms="dm">y</sql>'
                "</changeSet>"))
    assert rep["error"] == ""
    assert rep["counts"]["OK"] == 1


def test_entity_declaration_is_refused():
    """回归护栏：DTD/ENTITY 一律拒绝——防 billion laughs 实体扩展与外部实体。"""
    payload = (
        '<?xml version="1.0"?>\n'
        "<!DOCTYPE databaseChangeLog [\n"
        '  <!ENTITY lol "lol">\n'
        '  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">\n'
        "]>\n"
        + _wrap('<changeSet id="l" author="u">'
                '<sql dbms="mysql">&lol2;</sql></changeSet>'))
    rep = audit_changelog(payload, source="evil.xml")
    assert rep["error"] and "实体" in rep["error"]
    assert rep["total"] == 0


def test_external_entity_is_refused():
    """外部实体（读本地文件/SSRF 的载体）必须在解析器层被拒。"""
    payload = (
        '<?xml version="1.0"?>\n'
        '<!DOCTYPE databaseChangeLog [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>\n'
        + _wrap('<changeSet id="m" author="u"><sql>&xxe;</sql></changeSet>'))
    rep = audit_changelog(payload, source="xxe.xml")
    assert rep["error"] and "实体" in rep["error"]
    assert rep["total"] == 0


def test_audit_dir_finds_changelogs_and_skips_others(tmp_path):
    (tmp_path / "a.xml").write_text(
        _wrap('<changeSet id="a" author="u"><sql dbms="mysql">x</sql></changeSet>'),
        encoding="utf-8")
    (tmp_path / "b.xml").write_text("<beans/>", encoding="utf-8")
    reports = audit_dir(tmp_path)
    assert len(reports) == 1
    assert reports[0]["counts"]["NOOP"] == 1


def test_audit_jar_reads_entry_without_extracting(tmp_path):
    jar = tmp_path / "egova-gis-1.0.1.jar"
    with zipfile.ZipFile(str(jar), "w") as zf:
        zf.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n")
        zf.writestr("gis-db-changelog.xml",
                    _wrap('<changeSet id="a" author="u"><sql dbms="mysql">x</sql></changeSet>'))
        zf.writestr("other.xml", "<beans/>")
    reports = audit_jar(jar)
    assert len(reports) == 1
    assert reports[0]["counts"]["NOOP"] == 1
    explicit = audit_jar(jar, "other.xml")
    assert explicit[0]["error"] or explicit[0]["total"] == 0


def test_render_lists_bad_changesets_and_totals():
    rep = audit_changelog(_wrap(
        '<changeSet id="g" author="u"><sql dbms="mysql">x</sql></changeSet>'
        '<changeSet id="h" author="u" dbms="oracle"><sql>y</sql></changeSet>'))
    out = render([rep])
    assert "NOOP" in out and "SKIP" in out
    assert "id=g" in out and "id=h" in out
    assert "空执行" in out and "不执行" in out


def test_render_clean_case():
    rep = audit_changelog(_wrap('<changeSet id="i" author="u"><sql dbms="dm">x</sql></changeSet>'))
    assert "✅" in render([rep])


def test_main_json_and_strict_exit_code(tmp_path, capsys):
    f = tmp_path / "cl.xml"
    f.write_text(_wrap('<changeSet id="j" author="u"><sql dbms="mysql">x</sql></changeSet>'),
                 encoding="utf-8")
    assert main(["--changelog", str(f), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["counts"]["NOOP"] == 1
    assert main(["--changelog", str(f), "--strict"]) == 2
    capsys.readouterr()


def test_main_requires_an_input():
    with pytest.raises(SystemExit) as ei:
        main([])
    assert "必须给" in str(ei.value)


def test_no_write_mode_open_in_source():
    """回归护栏：只读脚本，不留任何 CLI 可控写路径。"""
    hits = [
        (i, l) for i, l in enumerate(SRC.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"\bopen\s*\([^)]*,\s*[\"'](?:w|a|x|\+)[\"']", l)
    ]
    assert hits == [], f"发现写模式 open：{hits}"


def test_no_sql_execution_or_connection_in_source():
    """回归护栏：不连库、不执行 SQL、不走网络、不吃 stdin 交互。"""
    src = SRC.read_text(encoding="utf-8")
    for banned in ("execute(", "executemany(", "cursor", "dmPython", "jdbc:dm",
                   "socket", "urllib", "requests", "paramiko", "getpass", "input("):
        assert banned not in src, f"源码出现禁用符号：{banned}"


def test_no_entity_expanding_xml_parser_in_source():
    """回归护栏：不得回到 ElementTree.fromstring / minidom 这类会做实体扩展的入口。"""
    src = SRC.read_text(encoding="utf-8")
    for banned in ("xml.etree.ElementTree", "ET.fromstring", "minidom", "xml.sax",
                   "lxml", "defusedxml", "etree.parse"):
        assert banned not in src, f"源码出现不安全的 XML 解析入口：{banned}"
    assert "EntityDeclHandler" in src, "必须显式安装实体声明拒绝回调"


def test_no_credential_literal_in_source():
    src = SRC.read_text(encoding="utf-8")
    assert not re.search(r"(?i)(token|password|passwd|secret)\s*=\s*[\"'][^\"']{12,}[\"']", src)
    assert '"--out"' not in src
    assert '"--token"' not in src
    assert "makedirs" not in src
