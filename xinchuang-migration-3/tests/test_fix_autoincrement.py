# -*- coding: utf-8 -*-
"""fix_autoincrement.py.txt 的用例。

覆盖点（都是实测踩过的坑，不是假想分支）：
- 标识符白名单 fullmatch 才算过，带引号/分号/空格的直接拒绝。
- 序列名超长时按「截短 + sha256 后缀」收敛，且不同表列不碰撞。
- 类型串重建：长度/精度为 0 表示不适用，不能输出 VARCHAR(0)。
- IDENTITY 列识别：DDL 里该列定义行出现 IDENTITY 才算，别的列有不算。
- PL 块三道闸：占位符未填满拒绝、生成结果不合语法拒绝
  （这是防止把注入面留进脚本的唯一结构性保证）。
- 多库跑不给 --dm-pw-map 必须报错，不能拿一个口令文件连所有用户。
"""
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_ROOT / "scripts" / "dm" / "fix_autoincrement.py.txt"


def _load(path, name):
    # .py.txt 不是 Python 认的后缀，spec_from_file_location 会返回 None，
    # 必须显式给 SourceFileLoader。
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


fx = _load(SCRIPT, "fix_ai_under_test")


# ---------------------------------------------------------------- 标识符白名单

def test_ident_accepts_plain_names():
    assert fx.ident("pub_encrypt_interface", "表名") == "pub_encrypt_interface"
    assert fx.ident("id", "列名") == "id"
    assert fx.ident("SEQ_A$B", "序列名") == "SEQ_A$B"


@pytest.mark.parametrize("bad", [
    'pub_t"; DROP TABLE x;--',
    "pub t",
    "",
    "pub-t",
    "pub.t",
    "pub\tt",
    "x" * 61,
    None,
])
def test_ident_rejects_everything_not_whitelisted(bad):
    with pytest.raises(ValueError):
        fx.ident(bad, "标识符")


# ---------------------------------------------------------------- 序列名

def test_seq_name_short_is_readable():
    assert fx.seq_name("pub_base_message", "id") == "SEQ_PUB_BASE_MESSAGE_ID"


def test_seq_name_long_is_truncated_and_deterministic():
    long_table = "t" * 60
    a = fx.seq_name(long_table, "id")
    b = fx.seq_name(long_table, "id")
    assert a == b
    assert len(a) <= 57
    assert a.startswith("SEQ_")


def test_seq_name_collision_resistant():
    """两个不同的超长表名不能收敛到同一个序列名，否则共用一个序列会串号。"""
    a = fx.seq_name("t" * 60, "id")
    b = fx.seq_name("u" * 60, "id")
    assert a != b


def test_seq_name_sanitises_separators():
    assert fx.seq_name("pub.msg", "my id") == "SEQ_PUB_MSG_MY_ID"


# ---------------------------------------------------------------- 类型串

def test_type_str_varchar_with_length():
    assert fx.type_str("VARCHAR", 200, 0, 0) == "VARCHAR(200)"
    assert fx.type_str("varchar2", 64, 0, 0) == "VARCHAR2(64)"


def test_type_str_varchar_without_length_is_not_zero():
    """长度 0 表示不适用，绝不能输出 VARCHAR(0)。"""
    assert fx.type_str("VARCHAR", 0, 0, 0) == "VARCHAR"
    assert fx.type_str("VARCHAR", None, 0, 0) == "VARCHAR"


def test_type_str_number_precision_scale():
    assert fx.type_str("NUMBER", 0, 10, 2) == "NUMBER(10,2)"
    assert fx.type_str("NUMBER", 0, 10, 0) == "NUMBER(10)"
    assert fx.type_str("NUMBER", 0, 0, 0) == "NUMBER"


def test_type_str_plain_types_pass_through():
    assert fx.type_str("INT", 0, 0, 0) == "INT"
    assert fx.type_str("BIGINT", 0, 0, 0) == "BIGINT"
    assert fx.type_str("TIMESTAMP", 0, 6, 0) == "TIMESTAMP"


# ---------------------------------------------------------------- IDENTITY

DDL_WITH_IDENTITY = """CREATE TABLE "EGOVAPUBLIC"."PUB_X"
(
    "ID" INT IDENTITY(1, 1) NOT NULL,
    "NAME" VARCHAR(200),
    PRIMARY KEY("ID")
)"""

DDL_PLAIN = """CREATE TABLE "EGOVAPUBLIC"."PUB_Y"
(
    "ID" INT DEFAULT 1 NOT NULL,
    "NAME" VARCHAR(200)
)"""


def test_is_identity_detects_the_column():
    assert fx.is_identity(DDL_WITH_IDENTITY, "id") is True
    assert fx.is_identity(DDL_WITH_IDENTITY, "ID") is True


def test_is_identity_ignores_other_columns():
    assert fx.is_identity(DDL_WITH_IDENTITY, "name") is False


def test_is_identity_false_when_only_default():
    assert fx.is_identity(DDL_PLAIN, "id") is False


# ---------------------------------------------------------------- PL 块闸门

def _plan_row(**kw):
    row = {"db": "public", "dm_user": "EGOVAPUBLIC",
           "table": "pub_encrypt_interface", "col": "id", "type": "INT",
           "nullable": "N", "ai_next": 46, "ai_floor": 46,
           "seq": "SEQ_PUB_ENCRYPT_INTERFACE_ID"}
    row.update(kw)
    return row


def test_ddl_for_emits_not_null_when_column_not_nullable():
    out = fx.ddl_for(_plan_row())
    assert "NOCACHE" in out
    assert '("id" INT DEFAULT SEQ_PUB_ENCRYPT_INTERFACE_ID.NEXTVAL NOT NULL)'
    assert out.endswith("END;\n/")


def test_ddl_for_omits_not_null_when_nullable():
    out = fx.ddl_for(_plan_row(nullable="Y"))
    assert "NEXTVAL)" in out
    assert "NEXTVAL NOT NULL)" not in out


def test_ddl_for_seed_is_computed_in_db_not_python():
    """种子必须写成 GREATEST(max+1, 源库值, 1) 让库自己实测，
    不能在 Python 里算死——MySQL 的 auto_increment 不是可靠的"下一个值"。"""
    out = fx.ddl_for(_plan_row(ai_floor=46))
    assert "GREATEST(v_max + 1, 46, 1)" in out
    assert 'SELECT NVL(MAX("id"), 0) INTO v_max '
    assert 'FROM "pub_encrypt_interface";' in out


def test_ddl_for_rejects_bad_identifier():
    with pytest.raises(ValueError):
        fx.ddl_for(_plan_row(table='pub_x"; DROP TABLE t;--'))


def test_ddl_for_rejects_bad_type_string():
    with pytest.raises(ValueError):
        fx.ddl_for(_plan_row(type="INT; DROP TABLE t"))


def test_sub_rejects_unfilled_placeholder():
    """漏填一个占位符就必须拒绝，不能把带 @ 的残句写进脚本。"""
    with pytest.raises(ValueError):
        fx._sub(fx.PL_TMPL, SEQ="S", COL="c", TAB="t", TYPE="INT",
                NOTNULL="")


def test_sub_rejects_output_off_grammar():
    """占位符填的内容不合规时，整句语法校验必须挡下，不许写进脚本。"""
    with pytest.raises(ValueError):
        fx._sub(fx.PL_TMPL, SEQ="S; DROP TABLE t", COL="c", TAB="t",
                TYPE="INT", NOTNULL="", AI="1")


# ---------------------------------------------------------------- 口令文件

class _Args:
    dm_pw_file = None
    dm_pw_map = {}


def test_pw_file_for_uses_map_first():
    args = _Args()
    args.dm_pw_map = {"CGDB": "/root/.a", "MMS": "/root/.b"}
    args.dm_pw_file = "/root/.single"
    assert fx.pw_file_for(args, "CGDB") == "/root/.a"
    assert fx.pw_file_for(args, "MMS") == "/root/.b"


def test_pw_file_for_falls_back_to_single_file():
    args = _Args()
    args.dm_pw_file = "/root/.single"
    assert fx.pw_file_for(args, "ANYUSER") == "/root/.single"


def test_pw_file_for_errors_when_no_file_for_user():
    args = _Args()
    with pytest.raises(SystemExit):
        fx.pw_file_for(args, "CGDBSTAT")


def test_main_requires_mysql_pw_and_dm_pw():
    with pytest.raises(SystemExit):
        fx.main(["--scan"])
