# -*- coding: utf-8 -*-
"""check_props_coverage 单测：构造两份 properties，核对 MISSING/EXTRA/DIFF 与值打印开关。

回归护栏同 query_xc 口径：无写模式 open、无凭据字面量、无 --out。
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_props_coverage import (  # noqa: E402
    compare_props, main, parse_properties, render,
)

SRC = Path(__file__).resolve().parent.parent / "scripts" / "check_props_coverage.py"


def test_parse_properties_handles_comments_separators_and_blanks():
    text = (
        "# 注释\n"
        "! 另一条注释\n"
        "\n"
        "a=1\n"
        "b : 2\n"
        "c   3\n"
        "d=\n"
        "e=x=y\n"
    )
    assert parse_properties(text) == {"a": "1", "b": "2", "c": "3", "d": "", "e": "x=y"}


def test_parse_properties_joins_continuation_lines():
    assert parse_properties("k=a\\\n    b\n") == {"k": "ab"}


def test_parse_properties_keeps_first_occurrence():
    assert parse_properties("k=1\nk=2\n") == {"k": "1"}


def test_compare_props_classifies_three_buckets():
    res = compare_props({"a": "1", "b": "2", "c": "3"}, {"a": "1", "b": "9", "d": "4"})
    assert res["missing"] == ["c"]
    assert res["extra"] == ["d"]
    assert res["diff"] == ["b"]
    assert res["base_count"] == 3 and res["target_count"] == 3


def test_compare_props_identical_is_empty():
    res = compare_props({"a": "1"}, {"a": "1"})
    assert res["missing"] == [] and res["extra"] == [] and res["diff"] == []


def test_render_hides_values_by_default():
    res = compare_props({"secret.key": "s3cr3t-value"}, {})
    out = render("base.properties", "target.properties", res,
                 {"secret.key": "s3cr3t-value"}, {}, show_values=False)
    assert "secret.key" in out
    assert "s3cr3t-value" not in out
    assert "--show-values" in out


def test_render_shows_values_on_opt_in():
    res = compare_props({"a": "1"}, {})
    out = render("b.properties", "t.properties", res, {"a": "1"}, {}, show_values=True)
    assert "a = 1" in out


def test_render_clean_case():
    res = compare_props({"a": "1"}, {"a": "1"})
    assert "MISSING 0" in render("b", "t", res, {"a": "1"}, {"a": "1"}, False)


def test_main_strict_exit_code_and_json(tmp_path, capsys):
    base = tmp_path / "MYSQLV14.properties"
    target = tmp_path / "DM.properties"
    base.write_text("jdbc.url=jdbc:mysql://10.0.0.1:3306/cgdb\n"
                    "hibernate.dialect=org.hibernate.dialect.MySQLDialect\n"
                    "extra.only.base=1\n", encoding="utf-8")
    target.write_text("jdbc.url=jdbc:dm://10.0.0.9:5236\n"
                      "hibernate.dialect=org.hibernate.dialect.DmDialect\n",
                      encoding="utf-8")
    assert main(["--base", str(base), "--target", str(target), "--json"]) == 0
    payload = capsys.readouterr().out
    assert '"missing"' in payload
    assert main(["--base", str(base), "--target", str(target), "--strict"]) == 2
    capsys.readouterr()


def test_main_rejects_missing_file(tmp_path):
    good = tmp_path / "a.properties"
    good.write_text("a=1\n", encoding="utf-8")
    with pytest.raises(SystemExit) as ei:
        main(["--base", str(good), "--target", str(tmp_path / "nope.properties")])
    assert "不存在" in str(ei.value)


def test_no_write_mode_open_in_source():
    hits = [
        (i, l) for i, l in enumerate(SRC.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"\bopen\s*\([^)]*,\s*[\"'](?:w|a|x|\+)[\"']", l)
    ]
    assert hits == [], f"发现写模式 open：{hits}"


def test_no_credential_literal_in_source():
    src = SRC.read_text(encoding="utf-8")
    assert not re.search(r"(?i)(token|password|passwd|secret)\s*=\s*[\"'][^\"']{12,}[\"']", src)
    assert '"--out"' not in src
    assert "makedirs" not in src
