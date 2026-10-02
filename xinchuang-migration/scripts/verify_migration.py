#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_migration.py — 信创迁移前后数据一致性校验。

两个子命令：
  collect  采集数据库对象清单（表/视图/存储过程/函数/索引）→ JSON 基线
  compare  对比基线与目标 JSON，输出差异报告；判不一致时退出码 2，不自动修复

SQL 安全：所有 SQL 均为调用点字面量 + %s 参数绑定，无任何拼接或动态构造。
         行数抽查 SQL（SELECT COUNT(*) FROM "表名"）为人工交互执行，模板见
         references/migration_steps.md 第 4.0/4.4 节，其结果可手工并入基线 JSON
         的 row_counts 字段供 compare 比对。

连接参数中的密码一律走环境变量（XC_DB_PASSWORD）或交互输入，不接受命令行明文。

依赖（按 dialect 惰性导入，缺失时给出 gap 提示而不是崩溃）：
  mysql → pymysql   （pip install pymysql）
  dm    → dmPython  （达梦驱动；libdmdpi.so 报错见 SKILL.md 报错速查表 ldconfig 条目）
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_MISMATCH = 2


# ---------------------------------------------------------------- collect

def _connect(dialect: str, host: str, port: int, user: str, password: str, schema: str):
    if dialect == "mysql":
        try:
            import pymysql
        except ImportError:
            raise SystemExit("gap: 缺少 pymysql（pip install pymysql）")
        return pymysql.connect(
            host=host, port=port, user=user, password=password,
            database=schema, charset="utf8mb4",
        )
    try:
        import dmPython
    except ImportError:
        raise SystemExit(
            "gap: 缺少 dmPython。安装：pip install dmPython；"
            "若报 libdmdpi.so 找不到，见 SKILL.md 报错速查表 ldconfig 条目"
        )
    return dmPython.connect(user=user, password=password, host=host, port=port)


def collect_inventory(dialect: str, conn, schema: str) -> dict:
    """采集对象清单。SQL 全部为调用点字面量 + 参数绑定，无拼接。"""
    cur = conn.cursor()
    if dialect == "mysql":
        cur.execute("SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema=%s AND table_type='BASE TABLE'", (schema,))
        tables = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema=%s AND table_type='VIEW'", (schema,))
        views = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT routine_name FROM information_schema.routines "
                    "WHERE routine_schema=%s AND routine_type='PROCEDURE'", (schema,))
        procs = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT routine_name FROM information_schema.routines "
                    "WHERE routine_schema=%s AND routine_type='FUNCTION'", (schema,))
        funcs = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT DISTINCT index_name FROM information_schema.statistics "
                    "WHERE table_schema=%s", (schema,))
        index_n = len({r[0] for r in cur.fetchall()})
    else:  # dm：user_* 视图即当前用户，固定 SQL 无参数
        cur.execute("SELECT table_name FROM user_tables ORDER BY table_name")
        tables = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT view_name FROM user_views ORDER BY view_name")
        views = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT object_name FROM user_objects "
                    "WHERE object_type='PROCEDURE' ORDER BY object_name")
        procs = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT object_name FROM user_objects "
                    "WHERE object_type='FUNCTION' ORDER BY object_name")
        funcs = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT DISTINCT index_name FROM user_indexes")
        index_n = len({r[0] for r in cur.fetchall()})
    cur.close()

    return {
        "dialect": dialect,
        "schema": schema,
        "counts": {
            "tables": len(tables), "views": len(views),
            "procedures": len(procs), "functions": len(funcs),
            "indexes": index_n,
        },
        "tables": sorted(tables),
        "views": sorted(views),
        "procedures": sorted(procs),
        "functions": sorted(funcs),
        "row_counts": {},  # 行数抽查为人工交互执行，结果可手工并入此字段
    }


# ---------------------------------------------------------------- compare

def compare_inventories(baseline: dict, target: dict,
                        row_tolerance_pct: float = 0.0) -> dict:
    """纯函数：对比两份清单，返回差异报告 dict（无 DB 依赖，供单测）。"""
    report: dict = {
        "baseline_schema": baseline.get("schema"),
        "target_schema": target.get("schema"),
        "missing_tables": [], "extra_tables": [],
        "missing_views": [], "missing_procedures": [], "missing_functions": [],
        "row_mismatches": [], "row_errors": [],
        "counts_baseline": baseline.get("counts", {}),
        "counts_target": target.get("counts", {}),
    }
    base_tables = set(baseline.get("tables") or [])
    targ_tables = set(target.get("tables") or [])
    report["missing_tables"] = sorted(base_tables - targ_tables)
    # extra_tables 仅提示不判定：目标库多出的表多为 liquibase 自动建表/系统表，属迁移预期
    report["extra_tables"] = sorted(targ_tables - base_tables)

    base_rows = baseline.get("row_counts") or {}
    targ_rows = target.get("row_counts") or {}
    for t in sorted(base_tables & targ_tables):
        b, a = base_rows.get(t), targ_rows.get(t)
        if b is None or a is None:
            continue
        if b < 0 or a < 0:
            report["row_errors"].append({"table": t, "baseline": b, "target": a})
            continue
        if b == a:
            continue
        tol = abs(b) * row_tolerance_pct / 100.0
        if abs(b - a) > tol:
            report["row_mismatches"].append(
                {"table": t, "baseline": b, "target": a, "diff": a - b}
            )

    for key, out in (("views", "missing_views"), ("procedures", "missing_procedures"),
                     ("functions", "missing_functions")):
        report[out] = sorted(set(baseline.get(key) or []) - set(target.get(key) or []))

    report["consistent"] = not any(
        report[k] for k in
        ("missing_tables", "row_mismatches", "missing_views",
         "missing_procedures", "missing_functions")
    )
    return report


def render_report(report: dict) -> str:
    lines = [
        f"基线 {report['baseline_schema']} vs 目标 {report['target_schema']}",
        f"对象计数  基线={report['counts_baseline']}  目标={report['counts_target']}",
    ]
    if report["missing_tables"]:
        lines.append(f"缺失表（{len(report['missing_tables'])}）: "
                     + ", ".join(report["missing_tables"][:30]))
    if report["extra_tables"]:
        lines.append(f"多出表（{len(report['extra_tables'])}）: "
                     + ", ".join(report["extra_tables"][:30]))
    for key, label in (("missing_views", "缺失视图"),
                       ("missing_procedures", "缺失存储过程"),
                       ("missing_functions", "缺失函数")):
        if report[key]:
            lines.append(f"{label}（{len(report[key])}）: " + ", ".join(report[key][:30]))
    for m in report["row_mismatches"][:50]:
        lines.append(f"行数不一致 {m['table']}: 基线={m['baseline']} 目标={m['target']} "
                     f"差={m['diff']}")
    if len(report["row_mismatches"]) > 50:
        lines.append(f"...另有 {len(report['row_mismatches']) - 50} 张表行数不一致")
    for e in report["row_errors"][:10]:
        lines.append(f"行数统计异常 {e['table']}: 基线={e['baseline']} 目标={e['target']}")
    lines.append("结论: " + ("一致 ✅" if report["consistent"]
                          else "不一致 ❌ —— 按停止条件输出差异清单并停止，不自动修复"))
    return "\n".join(lines)


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="信创迁移前后数据一致性校验")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_c = sub.add_parser("collect", help="采集数据库对象清单基线")
    p_c.add_argument("--dialect", required=True, choices=("mysql", "dm"))
    p_c.add_argument("--host", required=True)
    p_c.add_argument("--port", type=int, required=True)
    p_c.add_argument("--user", required=True)
    p_c.add_argument("--schema", required=True)
    p_c.add_argument("--out", required=True, help="基线 JSON 输出路径")
    p_c.add_argument("--password-env", default="XC_DB_PASSWORD",
                     help="密码所在环境变量名（默认 XC_DB_PASSWORD），未设置则交互输入")

    p_d = sub.add_parser("compare", help="对比基线与目标")
    p_d.add_argument("--baseline", required=True)
    p_d.add_argument("--target", required=True)
    p_d.add_argument("--row-tolerance-pct", type=float, default=0.0,
                     help="行数允许差异百分比（默认 0 = 逐行精确）")

    args = parser.parse_args(argv)

    if args.cmd == "collect":
        password = os.environ.get(args.password_env, "")
        if not password:
            password = getpass.getpass(f"数据库密码（{args.user}@{args.host}:{args.port}）: ")
        conn = _connect(args.dialect, args.host, args.port, args.user, password, args.schema)
        try:
            inv = collect_inventory(args.dialect, conn, args.schema)
        finally:
            conn.close()
        Path(args.out).write_text(
            json.dumps(inv, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"基线已写出: {args.out} | 对象计数 {inv['counts']} | "
              f"行数抽查 SQL 按 migration_steps.md 4.0 节人工执行后并入 row_counts")
        return EXIT_OK

    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    target = json.loads(Path(args.target).read_text(encoding="utf-8"))
    report = compare_inventories(baseline, target, args.row_tolerance_pct)
    print(render_report(report))
    return EXIT_OK if report["consistent"] else EXIT_MISMATCH


if __name__ == "__main__":
    sys.exit(main())
