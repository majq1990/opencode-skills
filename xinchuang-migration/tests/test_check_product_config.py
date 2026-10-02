# -*- coding: utf-8 -*-
"""check_product_config 单测：临时目录构造 fixture 配置树，核对 PASS/FAIL/SKIP。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_product_config import (  # noqa: E402
    check_products, load_profile, render,
)

SKILL_ROOT = Path(__file__).resolve().parent.parent


def _profile():
    return load_profile(str(SKILL_ROOT / "config" / "product-config-map.json"))


def _make_migrated(root: Path):
    """构造"已迁移完成"的 MIS 配置（达梦 URL + DmDriver + DmDialect）。"""
    d = root / "web" / "eUrbanMIS" / "WEB-INF" / "classes"
    d.mkdir(parents=True)
    (d / "jdbc.properties").write_text(
        "jdbc.url=jdbc:dm://10.0.0.9:5236?schema=DLMIS\n"
        "jdbc.username=DLMIS\n"
        "jdbc.driverClassName=dm.jdbc.driver.DmDriver\n"
        "hibernate.dialect=org.hibernate.dialect.DmDialect\n",
        encoding="utf-8",
    )


def test_pass_when_dm_config_in_place(tmp_path):
    _make_migrated(tmp_path)
    results = check_products(_profile(), tmp_path)
    mis = next(r for r in results if r["product"] == "MIS/UMA/MF")
    assert mis["status"] == "PASS"
    assert mis["files"], "应解析到 jdbc.properties"


def test_fail_when_mysql_url_remains(tmp_path):
    _make_migrated(tmp_path)
    f = tmp_path / "web" / "eUrbanMIS" / "WEB-INF" / "classes" / "jdbc.properties"
    f.write_text(f.read_text(encoding="utf-8") + "old.url=jdbc:mysql://10.0.0.1:3306/cgdb\n",
                 encoding="utf-8")
    results = check_products(_profile(), tmp_path)
    mis = next(r for r in results if r["product"] == "MIS/UMA/MF")
    assert mis["status"] == "FAIL"
    bad = [x for x in mis["results"] if not x["ok"]]
    assert any("MySQL" in x["desc"] for x in bad)


def test_skip_when_no_file(tmp_path):
    results = check_products(_profile(), tmp_path)
    xingqiao = next(r for r in results if r["product"] == "星桥")
    assert xingqiao["status"] == "SKIP"
    assert "dex" in xingqiao["note"]


def test_render_contains_summary(tmp_path):
    _make_migrated(tmp_path)
    out = render(check_products(_profile(), tmp_path))
    assert "汇总" in out and "PASS" in out
