# -*- coding: utf-8 -*-
"""verify_migration.compare_inventories 纯函数单测（无 DB 依赖）。"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from verify_migration import EXIT_MISMATCH, EXIT_OK, compare_inventories  # noqa: E402


def _inv(schema, tables, rows=None, views=None, procs=None, funcs=None):
    return {
        "dialect": "mysql", "schema": schema,
        "counts": {"tables": len(tables), "views": len(views or []),
                   "procedures": len(procs or []), "functions": len(funcs or []),
                   "indexes": 0},
        "tables": tables, "views": views or [],
        "procedures": procs or [], "functions": funcs or [],
        "row_counts": rows or {},
    }


def test_consistent_inventories_pass():
    base = _inv("cgdb", ["T1", "T2"], rows={"T1": 100, "T2": 5})
    targ = _inv("DLMIS", ["T1", "T2"], rows={"T1": 100, "T2": 5})
    report = compare_inventories(base, targ)
    assert report["consistent"] is True


def test_missing_table_detected():
    base = _inv("cgdb", ["T1", "T2", "T3"])
    targ = _inv("DLMIS", ["T1", "T2"])
    report = compare_inventories(base, targ)
    assert report["consistent"] is False
    assert report["missing_tables"] == ["T3"]
    assert report["extra_tables"] == []


def test_row_mismatch_respects_tolerance():
    base = _inv("cgdb", ["T1"], rows={"T1": 1000})
    targ = _inv("DLMIS", ["T1"], rows={"T1": 980})
    strict = compare_inventories(base, targ, row_tolerance_pct=0.0)
    loose = compare_inventories(base, targ, row_tolerance_pct=5.0)
    assert strict["consistent"] is False and len(strict["row_mismatches"]) == 1
    assert loose["consistent"] is True


def test_row_error_negative_marks_not_mismatch():
    base = _inv("cgdb", ["T1"], rows={"T1": -1})   # 采集失败记 -1
    targ = _inv("DLMIS", ["T1"], rows={"T1": 10})
    report = compare_inventories(base, targ)
    assert report["row_mismatches"] == []
    assert len(report["row_errors"]) == 1
    assert report["consistent"] is True  # 统计异常不算数据不一致，单列提示


def test_missing_view_procedure_function():
    base = _inv("cgdb", ["T1"], views=["V1"], procs=["P1"], funcs=["F1"])
    targ = _inv("DLMIS", ["T1"], views=["V1"], procs=[], funcs=["F1"])
    report = compare_inventories(base, targ)
    assert report["consistent"] is False
    assert report["missing_procedures"] == ["P1"]
    assert report["missing_views"] == []
    assert report["missing_functions"] == []


def test_cli_compare_exit_codes(tmp_path):
    """compare 子命令退出码：一致→0，缺表→2（tmp_path 走 basetemp，避开系统 Temp ACL）。"""
    root = Path(__file__).resolve().parent.parent / "scripts" / "verify_migration.py"
    b, t = tmp_path / "b.json", tmp_path / "t.json"
    b.write_text(json.dumps(_inv("cgdb", ["T1", "T2"])), encoding="utf-8")
    t.write_text(json.dumps(_inv("DLMIS", ["T1", "T2"])), encoding="utf-8")
    r_ok = subprocess.run([sys.executable, str(root), "compare",
                           "--baseline", str(b), "--target", str(t)],
                          capture_output=True, text=True)
    # 缺表 = 不一致；多表（liquibase 自动建表类）只提示不判定
    t.write_text(json.dumps(_inv("DLMIS", ["T1"])), encoding="utf-8")
    r_bad = subprocess.run([sys.executable, str(root), "compare",
                            "--baseline", str(b), "--target", str(t)],
                           capture_output=True, text=True)
    assert r_ok.returncode == EXIT_OK, r_ok.stdout + r_ok.stderr
    assert r_bad.returncode == EXIT_MISMATCH, r_bad.stdout + r_bad.stderr
