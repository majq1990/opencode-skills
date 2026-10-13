# -*- coding: utf-8 -*-
"""lbpatch.py.txt 两条规则的用例。

覆盖点：
- empty-prefix-dot 只在属性声明值为空串或以点结尾时才删那个字面点；
  属性值是别的内容时不许动（否则会把 EGOVAPUBLIC.so_x.nextval 改成
  EGOVAPUBLICso_x.nextval）。
- 属性值合法地可以是空串，空串是假值，属性解析不能用 `or` 串。
- sqlserver-identity-insert 只删所属 changeSet 在目标库确会执行的语句；
  dbms 限定在别处的原样不动。
- 达梦被 fork 按 OracleDatabase 适配，shortName 是 oracle 不是 dm，
  dbms="oracle" 的 changeset 在达梦路径下同样生效。
- 补丁从后往前应用，多个命中不会互相破坏偏移。
"""
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_ROOT / "scripts" / "dm" / "lbpatch.py.txt"


def _load(path, name):
    # .py.txt 不是 Python 认的后缀，spec_from_file_location 会返回 None，
    # 必须显式给 SourceFileLoader。
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


lbpatch = _load(SCRIPT, "lbpatch_under_test")


def _src(text, name="changelog.xml", kind="disk", container="."):
    return lbpatch.Source(name, kind, container, name, text)


CHANGELOG = """<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog>
  <property name="schema.dlsys_" value=""/>
  <property name="schema.other_" value="EGOVAPUBLIC."/>
  <property name="schema.plain_" value="EGOVAPUBLIC"/>
  <changeSet id="a1" author="egova">
    <sql>select ${schema.dlsys_}.so_t.nextval from dual</sql>
  </changeSet>
  <changeSet id="a2" author="egova">
    <sql>select ${schema.other_}.so_t.nextval from dual</sql>
  </changeSet>
  <changeSet id="a2b" author="egova">
    <sql>select ${schema.plain_}.so_t.nextval from dual</sql>
  </changeSet>
  <changeSet id="a3" author="egova" dbms="mysql">
    <sql>select ${schema.dlsys_}.so_t.nextval from dual</sql>
  </changeSet>
  <changeSet id="a4" author="egova" dbms="oracle">
    <sql>SET IDENTITY_INSERT tc_pub_city_module_config ON;</sql>
    <sql>INSERT INTO tc_pub_city_module_config (id) VALUES (1);</sql>
    <sql>SET IDENTITY_INSERT tc_pub_city_module_config OFF;</sql>
  </changeSet>
  <changeSet id="a5" author="egova" dbms="sqlserver">
    <sql>SET IDENTITY_INSERT tc_pub_city_module_config ON;</sql>
  </changeSet>
</databaseChangeLog>
"""


def _prepare():
    files = {"changelog.xml": _src(CHANGELOG)}
    lbpatch.parse_sources(files)
    props = lbpatch.collect_props(files)
    order = ["changelog.xml"]
    return files, props, order


def test_empty_prefix_dot_hits_only_dot_ending_properties():
    """属性值为空串或以点结尾时那个字面点才冗余；值是 EGOVAPUBLIC（不带点）
    时删了就把 EGOVAPUBLIC.so_t.nextval 变成 EGOVAPUBLICso_t.nextval。"""
    files, props, order = _prepare()
    hits = lbpatch.scan_rule_empty_prefix_dot(files, order, props, "oracle")
    got = sorted(h["name"] for h in hits)
    assert got == ["schema.dlsys_", "schema.other_"]
    for h in hits:
        assert h["after"] == "${%s}" % h["name"]


def test_empty_prefix_dot_empty_string_value_is_not_swallowed():
    """属性值合法地可以是空串；空串是假值，属性解析不能用 `or` 串，
    否则这条规则会把空前缀属性全漏掉。"""
    files, props, order = _prepare()
    assert lbpatch.resolve_prop(props, "schema.dlsys_", "oracle") == ""
    assert lbpatch.resolve_prop(props, "schema.plain_", "oracle") == "EGOVAPUBLIC"


def test_empty_prefix_dot_respects_dbms():
    files, props, order = _prepare()
    hits = lbpatch.scan_rule_empty_prefix_dot(files, order, props, "oracle")
    # a3 限定 dbms="mysql"，目标库是 oracle，不该命中
    assert all(h["line"] != CHANGELOG[:CHANGELOG.index('id="a3"')].count("\n") + 2
               for h in hits)


def test_identity_insert_rule_hits_only_executed_changesets():
    files, props, order = _prepare()
    hits = lbpatch.scan_rule_sqlserver_identity_insert(files, order, props,
                                                       "oracle")
    # a4(dbms=oracle) 的 ON/OFF 两条命中；a5(dbms=sqlserver) 不命中
    assert len(hits) == 2
    assert all("ON" in h["before"] or "OFF" in h["before"] for h in hits)


def test_identity_insert_not_hit_when_shortname_is_dm_literal():
    """如果误把 shortName 当成 dm，dbms="oracle" 的 changeset 会被判成不适用，
    这条规则就漏修——这正是必须用 getShortName() 而不是字面量 dm 的原因。"""
    files, props, order = _prepare()
    hits = lbpatch.scan_rule_sqlserver_identity_insert(files, order, props, "dm")
    assert hits == []


def test_dbms_applies_treats_oracle_as_matching_dm():
    assert lbpatch.dbms_applies(None, "oracle") is True
    assert lbpatch.dbms_applies("", "oracle") is True
    assert lbpatch.dbms_applies("oracle", "oracle") is True
    assert lbpatch.dbms_applies("mysql, oracle", "oracle") is True
    assert lbpatch.dbms_applies("mysql", "oracle") is False


def test_apply_hits_rewrites_disk_file_and_backs_up(tmp_path):
    webapp = tmp_path / "webapp"
    liquibase = webapp / "liquibase"
    liquibase.mkdir(parents=True)
    target = liquibase / "changelog.xml"
    target.write_text(CHANGELOG, encoding="utf-8")

    files = {"changelog.xml": lbpatch.Source(
        "changelog.xml", "disk", str(liquibase), "changelog.xml",
        target.read_text(encoding="utf-8"))}
    props = lbpatch.collect_props(files)
    hits = (lbpatch.scan_rule_empty_prefix_dot(files, ["changelog.xml"],
                                               props, "oracle")
            + lbpatch.scan_rule_sqlserver_identity_insert(
                files, ["changelog.xml"], props, "oracle"))

    backup = tmp_path / "backup"
    changed = lbpatch.apply_hits(files, hits, str(backup))

    assert changed == ["changelog.xml"]
    out = target.read_text(encoding="utf-8")
    # a1 的属性值是空串、a2 的值以点结尾 -> 两处字面点都删掉
    assert out.count("${schema.dlsys_}so_t.nextval") == 1
    assert out.count("${schema.other_}so_t.nextval") == 1
    # a3 限定 dbms="mysql"，目标库是 oracle 不许动；a2b 的属性值不带点，
    # 删了会把 EGOVAPUBLIC.so_t 粘成 EGOVAPUBLICso_t，也不许动
    assert out.count("${schema.dlsys_}.so_t.nextval") == 1
    assert out.count("${schema.plain_}.so_t.nextval") == 1
    # SET IDENTITY_INSERT 在 a4（dbms=oracle，达梦真会执行）整条消失，INSERT
    # 本体保留；a5 限定 dbms=sqlserver 不匹配，原样留下
    assert out.count("IDENTITY_INSERT") == 1
    assert "INSERT INTO tc_pub_city_module_config (id) VALUES (1);" in out
    # 备份存在且是改前内容
    orig = (backup / "changelog.xml.orig").read_text(encoding="utf-8")
    assert "IDENTITY_INSERT" in orig


def test_scan_after_fix_is_clean(tmp_path):
    """复扫必须 0 命中，否则说明补丁没打全或规则不自洽。"""
    webapp = tmp_path / "webapp"
    liquibase = webapp / "liquibase"
    liquibase.mkdir(parents=True)
    target = liquibase / "changelog.xml"
    target.write_text(CHANGELOG, encoding="utf-8")

    files = {"changelog.xml": lbpatch.Source(
        "changelog.xml", "disk", str(liquibase), "changelog.xml",
        target.read_text(encoding="utf-8"))}
    props = lbpatch.collect_props(files)
    order = ["changelog.xml"]
    hits = (lbpatch.scan_rule_empty_prefix_dot(files, order, props, "oracle")
            + lbpatch.scan_rule_sqlserver_identity_insert(files, order,
                                                          props, "oracle"))
    lbpatch.apply_hits(files, hits, str(tmp_path / "backup"))

    again = (lbpatch.scan_rule_empty_prefix_dot(files, order, props, "oracle")
             + lbpatch.scan_rule_sqlserver_identity_insert(files, order,
                                                           props, "oracle"))
    assert again == []


def test_unknown_rule_name_is_rejected(tmp_path):
    """--rules 传错名字必须报错退出，不能静默按默认跑。"""
    rc = lbpatch.main(["--scan", "--webapp", str(tmp_path), "--no-db",
                       "--rules", "no-such-rule"])
    assert rc == 2


def test_empty_webapp_is_rejected(tmp_path):
    rc = lbpatch.main(["--scan", "--webapp", str(tmp_path), "--no-db"])
    assert rc == 2
