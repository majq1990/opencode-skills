#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""06_risk_register.py — 风险登记册（台账 + 分级 + 责任人/时限 + 升级清单）。

数据来源两条腿：
  1) **审查发现自动入册**：读 audit_result.json，把每条问题按规则映射成风险条目。
  2) **人工登记**：--risks <人工风险.json>，与自动条目合并去重（按归一化标题互含判定）。

分级：score = probability × impact，落到 risk_matrix.json 的 thresholds。
升级：命中 escalation.conditions 任一条（blocks_acceptance / affects_data /
affects_schedule / customer_related），无论分数一律升级并给出上报对象。

产物（写入 --outdir）：
  risk_register.csv / risk_escalation.md / risk_summary.md

用法:
  python 06_risk_register.py --audit <audit_result.json> --outdir <目录> \
      [--risks <人工风险.json>] [--owner-map <责任人映射.json>] [--matrix <矩阵.json>]
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daa_common import (  # noqa: E402
    F_AUDIT, F_RISK, GapError, emit, envelope, exit_gap, load_json, norm_key,
    safe_path, setup_io, skill_root, today_str, write_csv, write_text,
)

REG_HEADERS = ["风险编号", "来源", "风险描述", "触发条件/问题依据", "交付物编号",
               "概率(1-5)", "影响(1-5)", "风险值", "风险等级", "处置要求",
               "责任部门", "责任人", "应对措施", "截止日", "状态", "是否升级",
               "上报对象", "关联文件"]

DEFAULT_AUTO_RULES = {
    "completeness":      {"probability": 4, "impact": 5,
                          "measure": "按 missing_list.csv 逐项补交，补交后复审"},
    "format_mismatch":   {"probability": 3, "impact": 3,
                          "measure": "按验收标准要求的格式重新导出并替换"},
    "empty_file":        {"probability": 3, "impact": 4,
                          "measure": "补充实质内容后重新提交，禁止提交空壳占位"},
    "sensitive":         {"probability": 2, "impact": 5,
                          "measure": "按脱敏规则处理敏感信息后重新提交，涉密件走线下渠道"},
    "forbidden_ext":     {"probability": 3, "impact": 2,
                          "measure": "清理临时/日志文件，重新打包交付"},
    "naming":            {"probability": 3, "impact": 2,
                          "measure": "按命名规范重命名后更新材料目录"},
    "duplicate_version": {"probability": 2, "impact": 2,
                          "measure": "确认最新版后删除或归档旧版本，保留唯一有效件"},
    "cross_reference":   {"probability": 2, "impact": 3,
                          "measure": "核对被引用文档编号，修正引用或补齐被引材料"},
    "oversize":          {"probability": 2, "impact": 2,
                          "measure": "拆分或压缩后重新提交"},
    "sla_overdue":       {"probability": 3, "impact": 3,
                          "measure": "明确补交时间并同步项目经理，纳入周报跟踪"},
}

LEVEL_ORDER_CN = ["极高", "高", "中", "低", "极低"]

_LEADING_ID = re.compile(r"([A-Za-z]{1,4}[-_]?\d+(?:[-–]\d+)*)")


def _leading_id(path):
    """从文件名/路径提取前导交付物编号，如 13-用户测试报审/B-30-1xxx.docx → B-30-1。"""
    base = re.split(r"[\\/]", str(path or ""))[-1]
    m = _LEADING_ID.search(base)
    return m.group(1) if m else ""


def classify(score, matrix):
    for th in matrix.get("thresholds") or []:
        if score >= int(th.get("min", 0)):
            return th.get("level"), th.get("color"), th.get("action")
    return "极低", "green", "仅登记，无需专项动作"


def level_action(level, matrix):
    for th in matrix.get("thresholds") or []:
        if th.get("level") == level:
            return th.get("action") or ""
    return ""


def escalation_hits(tags, matrix):
    conds = {c.get("id"): c for c in
             ((matrix.get("escalation") or {}).get("conditions") or [])}
    return [conds[t] for t in (tags or []) if t in conds]


def risks_from_audit(audit, matrix, auto_rules):
    """把审查问题转成风险条目。"""
    out = []
    for iss in audit.get("all_issues") or []:
        rule = iss.get("rule")
        cfg = auto_rules.get(rule)
        if not cfg:
            continue
        # 严重级越高，概率/影响同步上调，不让 Critical 问题算出「低风险」
        prob, imp = cfg.get("probability"), cfg.get("impact")
        bump = {"Critical": 1, "High": 0}.get(iss.get("level"), 0)
        prob = min(5, prob + bump)
        if iss.get("blocks_acceptance"):
            imp = 5
        prob, imp = max(1, min(5, prob)), max(1, min(5, imp))
        tags = []
        if iss.get("blocks_acceptance") or iss.get("level") == "Critical":
            tags.append("blocks_acceptance")
        if rule == "sensitive":
            tags.append("affects_data")
        item_id = iss.get("item_id") or iss.get("item_key") \
            or _leading_id(iss.get("path") or iss.get("file") or "")
        out.append({
            "来源": "审查发现",
            "风险描述": "%s：%s" % (rule, iss.get("message") or ""),
            "触发条件/问题依据": "%s / 严重级 %s" % (item_id or "全目录", iss.get("level")),
            "交付物编号": item_id,
            "概率(1-5)": prob,
            "影响(1-5)": imp,
            "应对措施": iss.get("advice") or cfg.get("measure") or "",
            "责任部门": iss.get("owner_dept") or "",
            "责任人": iss.get("owner") or "",
            "截止日": iss.get("deadline") or "",
            "关联文件": iss.get("path") or iss.get("file") or "",
            "_tags": tags,
        })
    return out


def load_manual(path):
    data = load_json(path)
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("risks") or data.get("items") or []
    else:
        raise GapError("人工风险文件格式无法识别：应为数组或 {risks: []}")
    out = []
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            raise GapError("人工风险第 %d 条不是对象" % (i + 1))
        out.append({
            "来源": "人工登记",
            "风险描述": it.get("title") or it.get("desc") or "",
            "触发条件/问题依据": it.get("trigger") or it.get("basis") or "",
            "交付物编号": it.get("item_id") or "",
            "概率(1-5)": int(it.get("probability") or 3),
            "影响(1-5)": int(it.get("impact") or 3),
            "应对措施": it.get("measure") or it.get("response") or "",
            "责任部门": it.get("owner_dept") or it.get("department") or "",
            "责任人": it.get("owner") or "",
            "截止日": it.get("due") or it.get("deadline") or "",
            "状态": it.get("status") or "开放",
            "关联文件": it.get("file") or "",
            "_tags": it.get("escalate") or [],
        })
    return out


def merge(auto, manual):
    """按归一化标题去重：人工条目补齐自动条目缺失字段，不重复计条。
    归一后互为包含（人工标题常是自动描述的截断）也视为同一条。"""
    out = []
    for r in auto + manual:
        k = norm_key(r.get("风险描述") or "")
        hit = None
        for i, old in enumerate(out):
            ok = norm_key(old.get("风险描述") or "")
            if not ok or not k:
                continue
            if ok[:60] == k[:60] or (len(k) >= 12 and k in ok) \
                    or (len(ok) >= 12 and ok in k):
                hit = i
                break
        if hit is not None:
            old = out[hit]
            for f, v in r.items():
                if v and not old.get(f):
                    old[f] = v
            if r.get("来源") == "人工登记":
                old["来源"] = "审查发现+人工登记"
            continue
        out.append(dict(r))
    return out


_DEPT_HINTS = [
    ("sensitive", "技术支持"), ("forbidden_ext", "实施"),
    ("naming", "项目管理"), ("completeness", "项目管理"),
    ("duplicate_version", "项目管理"), ("cross_reference", "项目管理"),
    ("sla_overdue", "项目管理"), ("format_mismatch", "实施"),
    ("empty_file", "研发"), ("oversize", "实施"),
]


def _guess_dept(r):
    for key, dept in _DEPT_HINTS:
        if key in (r.get("风险描述") or ""):
            return dept
    return ""


def enrich(rows, matrix, owner_map):
    owner_map = owner_map or {}
    depts = matrix.get("default_owner_departments") or []
    for i, r in enumerate(rows, 1):
        prob = max(1, min(5, int(r.get("概率(1-5)") or 3)))
        imp = max(1, min(5, int(r.get("影响(1-5)") or 3)))
        r["概率(1-5)"], r["影响(1-5)"] = prob, imp
        score = prob * imp
        level, _color, _action = classify(score, matrix)
        hits = escalation_hits(r.get("_tags"), matrix)
        r["风险值"] = score
        r["风险等级"] = level
        r["处置要求"] = level_action(level, matrix)
        r["风险编号"] = "R-%s-%03d" % (today_str().replace("-", ""), i)
        if not r.get("责任部门"):
            r["责任部门"] = _guess_dept(r) or (depts[0] if depts else "待指派")
        key = norm_key(r.get("交付物编号") or "")
        m = owner_map.get(key)
        if m is None and key:
            # 前缀匹配：B-30 可映射 B-30-1（编号最长者优先）
            cands = [k for k in owner_map if k and key.startswith(norm_key(k))]
            if cands:
                m = owner_map[max(cands, key=len)]
        if m is not None:
            if isinstance(m, dict):
                r["责任人"] = r.get("责任人") or m.get("owner", "")
                r["责任部门"] = m.get("dept") or r["责任部门"]
            else:
                r["责任人"] = r.get("责任人") or str(m)
        r.setdefault("状态", "开放")
        if hits:
            r["是否升级"] = "是"
            r["上报对象"] = " + ".join(dict.fromkeys(
                h.get("escalate_to", "") for h in hits))
        elif level in ("极高", "高"):
            r["是否升级"] = "是"
            r["上报对象"] = "项目经理"
        else:
            r["是否升级"] = "否"
            r["上报对象"] = ""
        if not r.get("责任人"):
            r["责任人"] = "待指派"
        if not r.get("截止日"):
            r["截止日"] = {"极高": "+1工作日", "高": "+3工作日", "中": "+7工作日",
                           "低": "里程碑前", "极低": "—"}[level]
    for r in rows:
        r.pop("_tags", None)
    return rows


def main():
    setup_io()
    ap = argparse.ArgumentParser(description="风险登记册（分级/责任人/时限/升级清单）")
    ap.add_argument("--audit", default=None, help="audit_result.json；不传则仅登记人工风险")
    ap.add_argument("--risks", default=None, help="人工风险 JSON")
    ap.add_argument("--owner-map", default=None, help="交付物编号 → 责任人/部门 映射 JSON")
    ap.add_argument("--matrix", default=None, help="风险矩阵 JSON，默认取 skill 内置")
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    outdir = safe_path(a.outdir)

    try:
        matrix = load_json(a.matrix, required=False) if a.matrix else None
        if matrix is None:
            matrix = load_json(os.path.join(skill_root(), "config", "risk_matrix.json"))
        if not matrix.get("thresholds"):
            raise GapError("风险矩阵缺少 thresholds，无法分级")
        auto_rules = dict(DEFAULT_AUTO_RULES)
        auto_rules.update(matrix.get("auto_rules") or {})
        owner_map = load_json(a.owner_map, required=False, default=None) or {}
        audit = load_json(a.audit, required=False) if a.audit else None
        if a.audit and not audit:
            raise GapError("审查结果为空：%s" % a.audit)
        if not audit and not a.risks:
            raise GapError("未提供 --audit 也未提供 --risks，无输入可登记")
        manual = load_manual(a.risks) if a.risks else []
    except GapError as e:
        return exit_gap("risk_register", str(e))

    auto = risks_from_audit(audit, matrix, auto_rules) if audit else []
    rows = enrich(merge(auto, manual), matrix, owner_map)
    if not rows:
        return exit_gap("risk_register", "合并去重后无风险条目，拒绝生成空台账")

    rows.sort(key=lambda r: (-LEVEL_ORDER_CN.index(r["风险等级"]), -int(r["风险值"])))

    write_csv(outdir, F_RISK, rows, REG_HEADERS)

    stats = {}
    for r in rows:
        stats[r["风险等级"]] = stats.get(r["风险等级"], 0) + 1
    escalated = [r for r in rows if r["是否升级"] == "是"]

    lines = ["# 风险升级清单", "",
             "生成时间：%s ｜ 共 %d 条风险，其中需升级 %d 条"
             % (today_str(), len(rows), len(escalated)), ""]
    if not escalated:
        lines.append("本期无升级项。")
    else:
        lines += ["## 需升级条目", ""]
        for r in escalated:
            lines.append("### %s [%s] 风险值 %s" % (r["风险编号"], r["风险等级"], r["风险值"]))
            lines.append("- **风险**：%s" % r["风险描述"])
            lines.append("- **依据**：%s" % r["触发条件/问题依据"])
            lines.append("- **上报对象**：%s" % r["上报对象"])
            lines.append("- **责任**：%s / %s" % (r["责任部门"], r["责任人"]))
            lines.append("- **时限**：%s" % (r["截止日"] or "待定"))
            lines.append("- **处置要求**：%s" % r["处置要求"])
            if r["应对措施"]:
                lines.append("- **应对措施**：%s" % r["应对措施"])
            lines.append("")
    write_text(outdir, "risk_escalation.md", "\n".join(lines) + "\n")

    s = ["# 风险登记册汇总", "", "生成时间：%s" % today_str(), "",
         "## 分级统计", "", "| 风险等级 | 条数 | 处置要求 |", "| --- | --- | --- |"]
    for lv in LEVEL_ORDER_CN:
        if stats.get(lv):
            s.append("| %s | %d | %s |" % (lv, stats[lv], level_action(lv, matrix)))
    s += ["", "合计 %d 条；需升级 %d 条；待指派责任人 %d 条。"
          % (len(rows), len(escalated), sum(1 for r in rows if r["责任人"] == "待指派")),
          "", "## Top 10 风险", "", "| 编号 | 等级 | 风险值 | 风险 | 责任 |",
          "| --- | --- | --- | --- | --- |"]
    for r in rows[:10]:
        s.append("| %s | %s | %s | %s | %s/%s |"
                 % (r["风险编号"], r["风险等级"], r["风险值"],
                    r["风险描述"][:60], r["责任部门"], r["责任人"]))
    write_text(outdir, "risk_summary.md", "\n".join(s) + "\n")

    emit(envelope("risk_register", True, outdir=outdir,
                  total=len(rows), from_audit=len(auto), from_manual=len(manual),
                  escalated=len(escalated), levels=stats,
                  unassigned_owner=sum(1 for r in rows if r["责任人"] == "待指派"),
                  files=[F_RISK, "risk_escalation.md", "risk_summary.md"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
