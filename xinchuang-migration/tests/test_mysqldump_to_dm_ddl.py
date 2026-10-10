# -*- coding: utf-8 -*-
"""mysqldump_to_dm_ddl 纯文本转换单测：类型映射 / 列转换 / 建表拆分 / 约束后置。

全部走纯函数与 stdin-stdout，不打网络、不连库、不执行 SQL。
"""
import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from mysqldump_to_dm_ddl import (  # noqa: E402
    convert_column,
    convert_constraint,
    convert_create,
    map_type,
    split_statements,
)

import mysqldump_to_dm_ddl as mod  # noqa: E402


# ---------------------------------------------------------------------------
# 类型映射（口径 = runbook 第一节，2026-10-10 四库 5589 表实证）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("raw,expect", [
    # 字符类：按字符单位声明，规避 DM LENGTH_IN_CHAR=0 的字节截断
    ("varchar(64)", "VARCHAR(64 CHAR)"),
    ("varchar(5000)", "CLOB"),                 # 超 4000 字符降级
    ("char(4)", "CHAR(4 CHAR)"),               # 保留 CHAR 语义，不退化成 VARCHAR
    ("nvarchar(100)", "VARCHAR(100 CHAR)"),
    # 大对象
    ("text", "CLOB"),
    ("longtext", "CLOB"),
    ("mediumtext", "CLOB"),
    ("json", "CLOB"),
    ("blob", "BLOB"),
    ("longblob", "BLOB"),
    ("varbinary(64)", "BLOB"),
    ("geometry", "BLOB"),
    ("multipolygon", "BLOB"),
    # 数值 / 时间
    ("tinyint(1)", "INT"),
    ("int(11)", "INT"),
    ("bigint(20) unsigned", "BIGINT"),
    ("bit(1)", "INT"),
    ("float", "DOUBLE"),
    ("double(10,4)", "DOUBLE"),
    ("decimal(18,2)", "DECIMAL(18,2)"),
    ("decimal(10)", "DECIMAL(10,0)"),
    ("date", "DATE"),
    ("datetime", "TIMESTAMP"),
    ("timestamp", "TIMESTAMP"),
    ("time", "VARCHAR(32 CHAR)"),
    ("year", "INT"),
    ("enum('a','b')", "VARCHAR(500 CHAR)"),
    ("set('x','y')", "VARCHAR(500 CHAR)"),
])
def test_map_type_known(raw, expect):
    dm, known = map_type(raw)
    assert dm == expect
    assert known is True


def test_map_type_unknown_flags_for_manual_review():
    """认不出的类型必须报 known=False，不能静默把 MySQL 类型写进 DDL。"""
    dm, known = map_type("geometrycollection(3)")
    assert known is True  # 在 GEOM_TYPES 里
    dm, known = map_type("serialsafe(8)")
    assert known is False
    assert dm == "SERIALSAFE(8)"


# ---------------------------------------------------------------------------
# 列定义转换
# ---------------------------------------------------------------------------
def test_convert_column_backticks_and_identity():
    out, note = convert_column("`id` bigint(20) unsigned NOT NULL AUTO_INCREMENT")
    assert out == '"id" BIGINT NOT NULL IDENTITY(1,1)'
    assert note is None


def test_convert_column_drops_mysql_only_clauses():
    out, _ = convert_column(
        "`name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL"
    )
    assert out == '"name" VARCHAR(100 CHAR) NOT NULL'


def test_convert_column_strips_on_update_current_timestamp():
    """ON UPDATE 必须整段剥掉（含小数位），DM 不支持，改触发器。"""
    out, _ = convert_column("`t` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP(3)")
    assert "ON UPDATE" not in out
    assert "IDENTITY" not in out
    assert out.endswith("DEFAULT CURRENT_TIMESTAMP")


def test_convert_column_zero_date_becomes_null():
    out, _ = convert_column("`d` date NOT NULL DEFAULT '0000-00-00'")
    assert "DEFAULT NULL" in out
    assert "0000-00-00" not in out


def test_convert_column_numeric_default_unquoted():
    """mysqldump 给数值列也写引号，DM 侧数值列去掉引号更稳。"""
    out, _ = convert_column("`c` int(11) NOT NULL DEFAULT '0'")
    assert "DEFAULT 0" in out
    assert "'0'" not in out


def test_convert_column_keeps_quoted_default_for_text():
    out, _ = convert_column("`s` varchar(20) NOT NULL DEFAULT 'N/A'")
    assert "DEFAULT 'N/A'" in out


def test_convert_column_chinese_identifier_kept():
    out, _ = convert_column("`标识码` varchar(32) DEFAULT NULL")
    assert out.startswith('"标识码" VARCHAR(32 CHAR)')


def test_convert_column_unknown_type_warns():
    out, note = convert_column("`x` weirdtype(4)")
    assert "WEIRDTYPE(4)" in out
    assert note and "未识别类型" in note


def test_convert_column_generated_column_warns():
    out, note = convert_column("`g` int GENERATED ALWAYS AS (`a` + `b`) STORED")
    assert note and "生成列" in note
    # 至少别把 MySQL 反引号标识符带进输出
    assert "`" not in out


# ---------------------------------------------------------------------------
# 建表语句：MySQL 专属子句清除 + 约束后置
# ---------------------------------------------------------------------------
DUMP = """
CREATE TABLE `t_user` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `标识码` varchar(32) DEFAULT NULL,
  `desc` text,
  `money` decimal(18,2) DEFAULT '0.00',
  `ct` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `flag` tinyint(1) DEFAULT '0',
  `blob_col` blob,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`标识码`),
  KEY `idx_ct` (`ct`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='用户表';
"""


def test_convert_create_moves_constraints_to_second_block():
    create, cons, notes = convert_create(DUMP)
    # 建表段只剩列定义
    assert "PRIMARY KEY" not in create
    assert "UNIQUE KEY" not in create
    assert "KEY `idx_ct`" not in create
    assert len(cons) == 3
    # MySQL 专属子句全部清掉
    for junk in ("ENGINE=", "AUTO_INCREMENT=", "CHARSET", "COLLATE", "`"):
        assert junk not in create
    # 表注释保留
    assert "COMMENT '用户表'" in create
    # 类型口径
    assert '"id" BIGINT NOT NULL IDENTITY(1,1)' in create
    assert '"标识码" VARCHAR(32 CHAR) DEFAULT NULL' in create
    assert '"desc" CLOB' in create
    assert '"money" DECIMAL(18,2) DEFAULT 0.00' in create
    assert '"blob_col" BLOB' in create


def test_convert_constraint_forms_and_prefix():
    """约束名/索引名一律加 prefix，否则同 schema 灰度验证会撞名。"""
    sql, note = convert_constraint("PRIMARY KEY (`id`)", '"t_user"', "T_")
    assert sql == 'ALTER TABLE "t_user" ADD CONSTRAINT "PK_t_user" PRIMARY KEY ("id");'
    assert note is None

    sql, _ = convert_constraint("UNIQUE KEY `uk_code` (`标识码`)", '"t_user"', "T_")
    assert sql == 'ALTER TABLE "t_user" ADD CONSTRAINT "T_uk_code" UNIQUE ("标识码");'

    sql, _ = convert_constraint("KEY `idx_ct` (`ct`)", '"t_user"', "T_")
    assert sql == 'CREATE INDEX "T_idx_ct" ON "t_user" ("ct");'

    # 无名前缀时索引名也不该丢
    sql, _ = convert_constraint("KEY `idx_ct` (`ct`)", '"t_user"')
    assert sql == 'CREATE INDEX "idx_ct" ON "t_user" ("ct");'


def test_convert_constraint_fulltext_and_spatial_need_manual():
    sql, note = convert_constraint("FULLTEXT KEY `ft` (`desc`)", '"t_user"')
    assert sql is None
    assert "全文" in note


def test_convert_constraint_prefix_length_stripped_with_note():
    sql, note = convert_constraint("KEY `idx_huge` (`huge`(10))", '"t_user"')
    assert sql == 'CREATE INDEX "idx_huge" ON "t_user" ("huge");'
    assert note and "前缀长度" in note


def test_convert_create_partition_table_warns():
    stmt = ("CREATE TABLE `t_p` (`id` int NOT NULL, PRIMARY KEY (`id`)) "
            "/*!50100 PARTITION BY RANGE (id) */")
    _, _, notes = convert_create(stmt)
    assert any("分区表" in n for n in notes)


def test_convert_create_table_like_is_named_not_silently_skipped():
    """cgdb 真实 dump 有 2 张 CREATE TABLE ... LIKE 表，必须点名而不是静默跳过。"""
    create, cons, notes = convert_create(
        "create table tc_x_bak_latest like tc_x;")
    assert create is None
    assert cons == []
    assert len(notes) == 1
    assert "tc_x_bak_latest" in notes[0]
    assert "LIKE" in notes[0]


# ---------------------------------------------------------------------------
# 语句切分与主流程
# ---------------------------------------------------------------------------
def test_split_statements_tolerates_semicolons_in_literals():
    stmts = split_statements("INSERT INTO t VALUES ('a;b'); CREATE TABLE x (a int);")
    assert len(stmts) == 2
    assert stmts[0].endswith(";")


def test_split_statements_tolerates_backticks_and_parens():
    stmts = split_statements("CREATE TABLE `a;b` (`c` decimal(10,2)) ;")
    assert len(stmts) == 1


def test_main_reads_stdin_writes_stdout(monkeypatch):
    """stdin/stdout 双端：-o 之类 CLI 写路径一律不留，落盘由调用方重定向。"""
    out = io.StringIO()
    monkeypatch.setattr(mod.sys, "argv", ["mysqldump_to_dm_ddl.py", "-"])
    monkeypatch.setattr(mod.sys, "stdin", io.StringIO(DUMP))
    monkeypatch.setattr(mod.sys, "stdout", out)
    assert mod.main() == 0
    text = out.getvalue()
    assert "第一段" in text and "第二段" in text
    assert '"id" BIGINT NOT NULL IDENTITY(1,1)' in text
    assert 'ALTER TABLE "t_user" ADD CONSTRAINT "PK_t_user"' in text


def test_main_skips_non_create_statements(monkeypatch):
    out = io.StringIO()
    err = io.StringIO()
    monkeypatch.setattr(mod.sys, "argv", ["mysqldump_to_dm_ddl.py", "-"])
    monkeypatch.setattr(mod.sys, "stdin", io.StringIO(
        "SET NAMES utf8mb4;\nINSERT INTO t VALUES (1);\n" + DUMP))
    monkeypatch.setattr(mod.sys, "stdout", out)
    monkeypatch.setattr(mod.sys, "stderr", err)
    assert mod.main() == 0
    assert out.getvalue().count("CREATE TABLE") == 1


def test_main_warns_on_table_like(monkeypatch):
    """跳过的语句必须把表名喊到 stderr，不能只计入汇总数字。"""
    out, err = io.StringIO(), io.StringIO()
    monkeypatch.setattr(mod.sys, "argv", ["mysqldump_to_dm_ddl.py", "-"])
    monkeypatch.setattr(mod.sys, "stdin", io.StringIO(
        "create table tc_x_bak_latest like tc_x;\n" + DUMP))
    monkeypatch.setattr(mod.sys, "stdout", out)
    monkeypatch.setattr(mod.sys, "stderr", err)
    assert mod.main() == 0
    text = err.getvalue()
    assert "tc_x_bak_latest" in text
    assert "跳过 1 条" in text
