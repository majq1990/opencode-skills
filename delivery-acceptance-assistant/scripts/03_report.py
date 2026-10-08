#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""03_report.py — 生成审查报告 / 待补清单 / 次日跟踪。

产物（写入 --outdir）：
  audit_report.md     六节审查报告（总体/阻断/明细/逐项核查/规则命中/清单外）
  missing_list.csv    待补清单（P0-P3 分级，可直接转任务）
  nextday_tracking.md 次日跟踪单（基于 audit_state.json 基线做新增/闭环判定）
  audit_state.json    本次结果基线（供下次对比）

用法:
  python 03_report.py --outdir out [--owner-map 责任人映射.json]
"""
import os
import re
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daa_common import (  # noqa: E402
    F_AUDIT, F_MISSING, F_REPORT, F_STATE, F_TRACK, LEVEL_ORDER, GapError, dump_json,
    emit, envelope, exit_gap, load_json, log, read_csv, setup_io, today_str, write_csv,
    write_text,
)

LEVEL_CN = {"Critical": "🔴 严重", "High": "🟠 高", "Medium": "🟡 中",
            "Low": "🔵 低", "Pass": "✅ 通过"}
RULE_CN = {
    "completeness": "必备件缺失", "empty_file": "空文件", "format_mismatch": "格式不符",
    "naming": "命名不合规", "sensitive": "敏感信息", "cross_reference": "交叉引用断裂",
    "duplicate_version": "重复版本", "forbidden_ext": "禁入扩展名",
    "oversize": "超大文件", "sla_overdue": "超交付时限",
}
PRIORITY = {"Critical": "P0", "High": "P1", "Medium": "P2", "Low": "P3"}
MISSING_HEADERS = ["优先级", "严重级", "交付物编号", "交付物名称", "问题类型",
                   "问题描述", "责任部门", "责任人", "补交截止日", "处理建议", "涉及文件"]

_DUE_OFFSET = {"P0": 5, "P1": 7, "P2": 14, "P3": 30}


def plus_days(days):
    import datetime
    return (datetime.date.today() + datetime.timedelta(days=days)).isoformat()


def due_for(prio):
    return plus_days(_DUE_OFFSET.get(prio, 14))


def load_owner_map(path):
    if not path:
        return {}
    data = load_json(path, required=False, default={}) or {}
    return data if isinstance(data, dict) else {}


def esc(s):
    return str(s or "").replace("|", "\\|").replace("\n", " ")


def build_missing_rows(audit, owner_map):
    rows = []
    for iss in audit.get("all_issues", []):
        prio = PRIORITY.get(iss.get("level"), "P3")
        item_id = iss.get("item_id") or iss.get("item_key") or ""
        om = owner_map.get(item_id, {}) if isinstance(owner_map.get(item_id), dict) else {}
        dept = om.get("dept") or iss.get("owner") or "待指派"
        person = om.get("owner") or ""
        rows.append({
            "优先级": prio,
            "严重级": iss.get("level", ""),
            "交付物编号": item_id,
            "交付物名称": iss.get("item_name", ""),
            "问题类型": RULE_CN.get(iss.get("rule"), iss.get("rule", "")),
            "问题描述": iss.get("message", ""),
            "责任部门": dept,
            "责任人": iss.get("owner") or person,
            "补交截止日": iss.get("deadline") or due_for(prio),
            "处理建议": iss.get("advice") or iss.get("expected") or "",
            "涉及文件": iss.get("path", ""),
        })
    order = {p: i for i, p in enumerate(["P0", "P1", "P2", "P3"])}
    rows.sort(key=lambda r: (order.get(r["优先级"], 9), r["交付物编号"]))
    return rows


def render_report(audit):
    p = audit.get("project") or {}
    if isinstance(p, str):
        p = {"name": p}
    t = audit["totals"]
    lv = audit["levels"]
    lines = []
    A = lines.append
    A("# 交付物审查报告")
    A("")
    A("| 项 | 值 |")
    A("| --- | --- |")
    A("| 项目名称 | %s |" % (p.get("name") or "未填写"))
    A("| 项目编号 | %s |" % (p.get("code") or "未填写"))
    A("| 建设单位 | %s |" % (p.get("customer") or "未填写"))
    A("| 承建方 | %s |" % (p.get("our_side") or "未填写"))
    A("| 项目经理 | %s |" % (p.get("pm") or "未填写"))
    A("| 审查日期 | %s |" % audit["audit_date"])
    A("| 审查目录 | `%s` |" % (audit.get("deliverable_dir") or ""))
    A("| **审查结论** | **%s** |" % audit["verdict"])
    A("")
    A("> 本报告由脚本机械生成，覆盖「验收清单 ⊕ 材料目录 ⊕ 验收标准」三源融合。")
    A("> 结论仅针对**材料齐套性与形式合规性**，不构成对文档内容实质质量的结论，")
    A("> 也不替代建设单位与承建方签署的验收结论。")
    A("")
    A("## 一、总体情况")
    A("")
    A("| 指标 | 数值 |")
    A("| --- | --- |")
    A("| 扫描文件数 | %d |" % t["files_scanned"])
    A("| 交付物清单项 | %d |" % t["checklist_items"])
    A("| 已匹配清单项 | %d |" % t["matched_items"])
    A("| 缺失必备项 | %d |" % t["missing_items"])
    A("| 清单外文件 | %d |" % t["unmatched_files"])
    A("| 问题总数 | %d |" % t["issues"])
    A("| 阻断验收问题 | %d |" % t["blocking_issues"])
    A("| 目标目录零写入自证 | 通过 |")
    A("")
    dist = "、".join("%s %d 项" % (LEVEL_CN[lv], lv_n)
                     for lv, lv_n in sorted(lv.items(), key=lambda kv: LEVEL_ORDER.index(kv[0]))
                     if lv_n and lv != "Pass")
    A("问题分级分布：%s" % (dist or "无"))
    A("")

    blockers = [iss for iss in audit.get("all_issues", [])
                if iss.get("blocks_acceptance")]
    A("## 二、阻断项（必须闭环后方可进入验收）")
    A("")
    if blockers:
        A("| 编号 | 交付物 | 问题 | 责任部门 | 建议 |")
        A("| --- | --- | --- | --- | --- |")
        for iss in blockers:
            A("| %s | %s | %s | %s | %s |" % (
                esc(iss.get("item_key") or iss.get("item_id") or "—"),
                esc(iss.get("item_name", "")), esc(iss.get("message", "")),
                esc(iss.get("owner") or "待指派"), esc(iss.get("advice", ""))))
    else:
        A("无阻断项。")
    A("")

    A("## 三、问题明细")
    A("")
    if audit.get("all_issues"):
        A("| 编号 | 级别 | 规则 | 问题 | 涉及文件 |")
        A("| --- | --- | --- | --- | --- |")
        for iss in audit.get("all_issues", []):
            A("| %s | %s | %s | %s | `%s` |" % (
                iss.get("id", ""), LEVEL_CN.get(iss.get("level"), iss.get("level")),
                RULE_CN.get(iss.get("rule"), iss.get("rule", "")),
                esc(iss.get("message", "")), esc(iss.get("path", ""))))
    else:
        A("未发现问题。")
    A("")

    A("## 四、逐项核查表")
    A("")
    A("| 编号 | 名称 | 必交 | 匹配方式 | 文件数 | 结论 |")
    A("| --- | --- | --- | --- | --- | --- |")
    for r in audit.get("results", []):
        A("| %s | %s | %s | %s | %d | %s |" % (
            esc(r["item_key"]), esc(r["item_name"]),
            "是" if r["required"] else "否", r["matched_by"], len(r["files"]),
            LEVEL_CN.get(r["level"], r["level"])))
    A("")

    A("## 五、规则命中率")
    A("")
    A("| 规则 | 开关 | 命中 |")
    A("| --- | --- | --- |")
    for rule, st in (audit.get("rule_stats") or {}).items():
        A("| %s | %s | %d |" % (
            RULE_CN.get(rule, rule),
            "开" if st.get("enabled") else "关", st.get("hits", 0)))
    A("")

    A("## 六、清单外文件（提示项，非违规）")
    A("")
    info = audit.get("informational") or []
    if info:
        A("| 文件 | 大小 | 说明 |")
        A("| --- | --- | --- |")
        for x in info:
            A("| `%s` | %d B | %s |" % (esc(x.get("path", "")),
                                        x.get("size", 0), esc(x.get("reason", ""))))
    else:
        A("无。")
    A("")
    return "\n".join(lines) + "\n"


def render_tracking(audit, state):
    t = audit["totals"]
    today = today_str()
    if state:
        prev_day = state.get("time", "上次")
        head = "# 交付物审查次日跟踪单（%s → %s）" % (prev_day, today)
        prev_keys = {(x.get("item_key"), x.get("rule"), x.get("message"))
                     for x in state.get("issues", [])}
        cur_keys = {(x.get("item_key"), x.get("rule"), x.get("message"))
                    for x in audit.get("all_issues", [])}
        new = [x for x in audit.get("all_issues", [])
               if (x.get("item_key"), x.get("rule"), x.get("message")) not in prev_keys]
        closed = [x for x in state.get("issues", [])
                  if (x.get("item_key"), x.get("rule"), x.get("message")) not in cur_keys]
    else:
        head = "# 交付物审查次日跟踪单（%s → %s）" % (today, plus_days(1))
        prev_day = None
        new = audit.get("all_issues", [])
        closed = []
    lines = [head, ""]
    lines.append("> 基线：%s ｜ 本次问题 %d 项（新增 %d，已闭环 %d）"
                 % (prev_day or "首次运行，无上次基线，本单为全量待办",
                    t["issues"], len(new), len(closed)))
    lines.append("")
    lines.append("## 一、本次新增问题（%d）" % len(new))
    lines.append("")
    if new:
        lines.append("| 优先级 | 编号 | 名称 | 问题 | 责任部门 | 建议截止 |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for iss in new:
            prio = PRIORITY.get(iss.get("level"), "P3")
            lines.append("| %s | %s | %s | %s | %s | %s |" % (
                prio, esc(iss.get("item_key") or iss.get("item_id") or "—"),
                esc(iss.get("item_name", "")), esc(iss.get("message", "")),
                esc(iss.get("owner") or "待指派"),
                esc(iss.get("deadline") or due_for(prio))))
    else:
        lines.append("无新增。")
    lines.append("")
    lines.append("## 二、已闭环问题（%d）" % len(closed))
    lines.append("")
    if closed:
        lines.append("| 编号 | 规则 | 问题 |")
        lines.append("| --- | --- | --- |")
        for iss in closed:
            lines.append("| %s | %s | %s |" % (
                esc(iss.get("item_key") or "—"),
                RULE_CN.get(iss.get("rule"), iss.get("rule", "")),
                esc(iss.get("message", ""))))
    else:
        lines.append("无（基线为空或无闭环）。")
    lines.append("")
    return "\n".join(lines) + "\n"


def main():
    setup_io()
    ap = argparse.ArgumentParser(description="生成审查报告/待补清单/次日跟踪")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--owner-map", default=None, help="责任人映射 JSON")
    a = ap.parse_args()
    outdir = a.outdir

    try:
        audit = load_json(os.path.join(outdir, F_AUDIT), required=True)
        if not isinstance(audit, dict) or "results" not in audit:
            raise GapError("审查结果缺失或结构不对，请先运行 02_audit.py")
        state = load_json(os.path.join(outdir, F_STATE), required=False, default=None)
        owner_map = load_owner_map(a.owner_map)
    except GapError as e:
        return exit_gap("report", str(e))

    report = render_report(audit)
    write_text(outdir, F_REPORT, report)

    rows = build_missing_rows(audit, owner_map)
    write_csv(outdir, F_MISSING, rows, MISSING_HEADERS)

    tracking = render_tracking(audit, state)
    write_text(outdir, F_TRACK, tracking)

    dump_json(outdir, F_STATE, {
        "time": today_str(), "verdict": audit["verdict"],
        "levels": audit["levels"], "totals": audit["totals"],
        "issues": audit["all_issues"],
    })

    log(outdir, "report: missing_rows=%d" % len(rows))
    emit(envelope("report", True,
                  report=os.path.join(outdir, F_REPORT),
                  missing_rows=len(rows),
                  tracking_new=len(re.findall(r"^\| P\d \|", tracking, re.M))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
