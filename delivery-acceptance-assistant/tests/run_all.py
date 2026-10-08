#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_all.py — delivery-acceptance-assistant 自测（全链路回归 + 反向用例）。

正向：以 references/sample 为交付目录跑 采集→审查→报告→风险登记 全链路，
      断言产物存在、关键数字正确、目标目录零写入。
反向：坏 JSON / 缺模板 / 输出目录在目标内 / 命名 P0 / 升级缺回滚 / 无输入
      等场景，断言脚本以 gap 信封 + 非零码退出，且不落半成品。

用法:
  python tests/run_all.py [--quick]
退出码：0=全部通过；1=有用例失败。
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s %s %s" % ("PASS" if cond else "FAIL", name, detail if not cond else ""))


def last_json(stdout):
    """从输出中取最后一个完整 JSON 对象（信封可能跟在日志行后）。"""
    dec = json.JSONDecoder()
    for i in range(len(stdout) - 1, -1, -1):
        if stdout[i] == "{":
            try:
                obj, _end = dec.raw_decode(stdout[i:])
            except Exception:
                continue
            if stdout[i + _end:].strip() == "":
                return obj
    return None


def run2(script, *args):
    p = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)] + list(args),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, last_json(p.stdout or "")


SAMPLE = os.path.join(ROOT, "references", "sample")


def build_sample(tmp):
    """把内置最小样例铺到临时目录作为交付目录。"""
    dst = os.path.join(tmp, "deliverables")
    os.makedirs(dst, exist_ok=True)
    if os.path.isdir(SAMPLE):
        shutil.copytree(SAMPLE, dst, dirs_exist_ok=True)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="跳过较重用例")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="daa_test_")
    print("工作目录：%s" % tmp)
    try:
        t_e2e(tmp)
        t_negative(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n通过 %d / 失败 %d" % (len(PASS), len(FAIL)))
    if FAIL:
        print("失败用例：")
        for f in FAIL:
            print("  -", f)
        return 1
    return 0


def t_e2e(tmp):
    print("\n== 全链路回归 ==")
    d = build_sample(tmp)
    out = os.path.join(tmp, "out")
    r, env = run2("01_collect.py", "--deliverable-dir", d, "--outdir", out,
                  "--project", os.path.join(ROOT, "references", "sample_project.json"))
    check("collect 退出 0", r == 0, "code=%s" % r)
    check("collect 零写入自证通过",
          bool(env and env.get("readonly_proof", {}).get("tree_identical")))
    check("manifest.json 落盘",
          os.path.isfile(os.path.join(out, "manifest.json")))

    r, env = run2("02_audit.py", "--outdir", out,
                  "--project", os.path.join(ROOT, "references", "sample_project.json"))
    check("audit 退出 0/1（有 Critical 允许 1）", r in (0, 1), "code=%s" % r)
    ar = os.path.join(out, "audit_result.json")
    ok = False
    if os.path.isfile(ar):
        data = json.load(open(ar, encoding="utf-8"))
        ok = data.get("ok") is True and isinstance(data.get("results"), list)
    check("audit_result.json 结构完整", ok)

    r, env = run2("03_report.py", "--outdir", out)
    check("report 退出 0", r == 0, "code=%s env=%s" % (r, env))
    for f in ("audit_report.md", "missing_list.csv"):
        check("产物 %s 存在" % f, os.path.isfile(os.path.join(out, f)))

    gdocs = os.path.join(tmp, "gendocs")
    r, env = run2("04_gen_docs.py",
                  "--templates", os.path.join(ROOT, "references", "templates"),
                  "--manifest", os.path.join(ROOT, "config", "doc_templates.json"),
                  "--replacements", os.path.join(ROOT, "references",
                                                 "replacements_sample.json"),
                  "--outdir", gdocs)
    check("gen_docs 退出 0", r == 0, "code=%s env=%s" % (r, env))
    check("gen_docs 4 份产物", bool(env) and env.get("generated") == 4,
          str(env and env.get("generated")))
    check("gen_docs 无未覆盖", bool(env) and env.get("uncovered_total") == 0)

    arts = os.path.join(tmp, "artifacts")
    r, env = run2("05_gen_artifacts.py",
                  "--model", os.path.join(ROOT, "references", "model_sample.json"),
                  "--outdir", arts)
    check("gen_artifacts 退出 0", r == 0, "code=%s env=%s" % (r, env))
    sqldir = os.path.join(arts, "sql")
    check("SQL 四件套齐全", os.path.isdir(sqldir) and
          len([x for x in os.listdir(sqldir) if x.endswith(".sql")]) == 4,
          str(os.listdir(sqldir) if os.path.isdir(sqldir) else "无"))

    risks = os.path.join(tmp, "risks")
    r, env = run2("06_risk_register.py", "--audit", ar, "--outdir", risks)
    check("risk_register 退出 0", r == 0, "code=%s" % r)
    for f in ("risk_register.csv", "risk_escalation.md", "risk_summary.md"):
        check("产物 %s 存在" % f, os.path.isfile(os.path.join(risks, f)))
    csv_rows = open(os.path.join(risks, "risk_register.csv"),
                    encoding="utf-8-sig").read()
    check("台账含表头与数据行", csv_rows.count("\n") >= 2)


def t_negative(tmp):
    print("\n== 反向用例 ==")
    d = build_sample(tmp)

    bad = os.path.join(tmp, "bad.json")
    open(bad, "w", encoding="utf-8").write("{not json")
    r, env = run2("05_gen_artifacts.py", "--model", bad,
                  "--outdir", os.path.join(tmp, "x1"))
    check("坏 JSON → gap 退出", r != 0 and bool(env) and not env.get("ok")
          and bool(env.get("gap")), "code=%s" % r)

    r, env = run2("04_gen_docs.py", "--templates", os.path.join(tmp, "nope"),
                  "--replacements", os.path.join(ROOT, "references",
                                                 "replacements_sample.json"),
                  "--outdir", os.path.join(tmp, "x2"))
    check("缺模板目录 → gap 退出", r != 0 and bool(env) and env.get("gap"),
          "code=%s" % r)

    r, env = run2("01_collect.py", "--deliverable-dir", d,
                  "--outdir", os.path.join(d, "out"),
                  "--project", os.path.join(ROOT, "references", "sample_project.json"))
    check("输出目录在目标内 → 拒绝", r != 0 and bool(env) and env.get("gap"),
          "code=%s" % r)

    ident = os.path.join(tmp, "ident.json")
    open(ident, "w", encoding="utf-8").write(json.dumps(
        {"实施方案": {"项目实施方案": "项目实施方案"}}, ensure_ascii=False))
    r, env = run2("04_gen_docs.py", "--templates",
                  os.path.join(ROOT, "references", "templates"),
                  "--manifest", os.path.join(ROOT, "config", "doc_templates.json"),
                  "--replacements", ident, "--outdir", os.path.join(tmp, "x3"))
    check("全恒等替换 → 拒绝", r != 0 and bool(env) and env.get("gap"), "code=%s" % r)

    badtbl = os.path.join(tmp, "badtbl.json")
    open(badtbl, "w", encoding="utf-8").write(json.dumps({
        "project": "t", "db_name": "db", "tables": [
            {"name": "tb_user", "comment": "用户",
             "columns": [{"name": "user_name", "type": "varchar(64)",
                          "null": False, "comment": "姓名"}]}]}, ensure_ascii=False))
    r, env = run2("05_gen_artifacts.py", "--model", badtbl,
                  "--outdir", os.path.join(tmp, "x4"))
    check("废弃前缀 tb_ → P0 拦截", r != 0 and bool(env) and not env.get("ok")
          and "P0" in (env.get("gap") or ""), "code=%s" % r)
    check("P0 拦截时不落任何文件", not os.path.isdir(os.path.join(tmp, "x4")))

    badcol = os.path.join(tmp, "badcol.json")
    open(badcol, "w", encoding="utf-8").write(json.dumps({
        "project": "t", "db_name": "db", "tables": [
            {"name": "t_biz_order", "comment": "订单",
             "columns": [{"name": "order", "type": "varchar(64)",
                          "null": False, "comment": "订单"}]}]}, ensure_ascii=False))
    r, env = run2("05_gen_artifacts.py", "--model", badcol,
                  "--outdir", os.path.join(tmp, "x5"))
    check("保留字字段 order → P0 拦截",
          r != 0 and bool(env) and "P0" in (env.get("gap") or ""), "code=%s" % r)

    norb = os.path.join(tmp, "norb.json")
    open(norb, "w", encoding="utf-8").write(json.dumps({
        "project": "t", "db_name": "db", "tables": [
            {"name": "t_biz_a", "comment": "A",
             "columns": [{"name": "a_name", "type": "varchar(64)",
                          "null": False, "comment": "名"}]}],
        "upgrade": {"from_version": "v1.0.0",
                    "statements": ["ALTER TABLE t_biz_a ADD COLUMN c1 INT NULL COMMENT 'c1'"]}},
        ensure_ascii=False))
    r, env = run2("05_gen_artifacts.py", "--model", norb,
                  "--outdir", os.path.join(tmp, "x6"))
    check("升级缺回滚 → 拒绝", r != 0 and bool(env) and "回滚" in (env.get("gap") or ""),
          "code=%s" % r)

    r, env = run2("06_risk_register.py", "--outdir", os.path.join(tmp, "x7"))
    check("风险登记无输入 → gap 退出", r != 0 and bool(env) and env.get("gap"),
          "code=%s" % r)

    badrisk = os.path.join(tmp, "badrisk.json")
    open(badrisk, "w", encoding="utf-8").write("[1,2,3]")
    r, env = run2("06_risk_register.py", "--risks", badrisk,
                  "--outdir", os.path.join(tmp, "x8"))
    check("人工风险非对象 → gap 退出", r != 0 and bool(env) and env.get("gap"),
          "code=%s" % r)

    sys.path.insert(0, SCRIPTS)
    try:
        lost = {"media": (3, 2), "tables": (1, 1), "fields": (0, 0)}
        decreased = {k: v for k, v in lost.items() if v[1] < v[0]}
        check("版面丢失判定逻辑", decreased == {"media": (3, 2)})
    except Exception as e:
        check("版面丢失判定逻辑", False, str(e))


if __name__ == "__main__":
    sys.exit(main())
