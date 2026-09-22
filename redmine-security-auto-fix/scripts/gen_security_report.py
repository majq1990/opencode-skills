# -*- coding: utf-8 -*-
"""生成处置报告 + 待办清单 + 案件状态文件。v2.0 自 security-case-handling 移植。

用法：
  python scripts/gen_security_report.py --cases <cases.json> --date 2026-09-22 \
      [--project "项目名"]

产物（默认落在 work/security_case/output/）：
  security_report_<date>.md  （默认落盘标记为【待复核】）
  todo_<date>.md
  case_state_<date>.json     （案件状态持久化，供次日跟踪 track_case_state.py）

只写本地目录；报告头部默认为【待复核】，未经人工签字不得推送。
推送通道沿用本 skill 既有 notify_dingtalk.py / finalize_publication.py 链路，
推送目标先测试群后真实群（config/security_case/notify.json）。
"""
import copy
import os
import sys
from datetime import datetime, timedelta

from security_case_lib import (
    emit, load_config, parse_args, read_json, skill_path, stop, work_path, write_json, write_text,
)

LEVEL_ORDER = ["Critical", "High", "Medium", "Low"]
LEVEL_CN = {"Critical": "紧急", "High": "高", "Medium": "中", "Low": "低"}
ACTION_CN = {
    "Critical": "4 小时内处置或下线/改策略规避，处理完 30 分钟内回报",
    "High": "24 小时内完成升级/补丁或启用临时规避策略",
    "Medium": "72 小时内排期修复，纳入本周变更窗口",
    "Low": "14 天内排期修复，随版本升级处理",
}
PROGRESS_DIR_LINE = "work/security_case/progress/progress_{date}.json"


def render(template, mapping):
    for k, v in mapping.items():
        template = template.replace("{{%s}}" % k, v)
    return template


def build(cases_doc, project, rules):
    date = cases_doc["meta"]["date"]
    cases = cases_doc["cases"]
    stats = cases_doc["stats"]
    warnings = cases_doc.get("warnings") or []
    next_date = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    lv = stats["levels"]
    level_line = " / ".join("%s %s" % (k, lv.get(k, 0)) for k in LEVEL_ORDER if lv.get(k))
    overview_lines = [
        "| 指标 | 值 | 说明 |",
        "| --- | --- | --- |",
        "| CVE 情报（原始 / 有效） | %s / %s | NVD/厂商公告接口或离线样例快照 |" % (stats["cve_raw"], stats["cve_clean"]),
        "| 扫描结果（原始 / 归一后） | %s / %s | 扫描器夜跑任务结果 |" % (stats["scan_raw"], stats["scan_clean"]),
        "| 资产台账（原始 / 有效） | %s / %s | CMDB 快照，同 IP 保留较新记录 |" % (stats.get("asset_raw", "-"), stats["asset_clean"]),
        "| 去重剔除 | %s | 定位键：%s，窗口 %s 天 |" % (stats["dedup_removed"], "+".join(cases_doc["meta"]["dedup_key"]), cases_doc["meta"]["dedup_window_days"]),
        "| 有效案件数 | **%s** | 三源融合后进入处置池 |" % stats["case_count"],
        "| 分级分布 | %s | 按本报告口径自算，非扫描器严重度 |" % level_line,
        "| 未定责扫描项 | %s | 资产不在授权台账，转人工确认 |" % stats["unmapped_assets"],
        "| 情报未进案件池 | %s | 未命中台账资产或命中台账外资产 |" % stats.get("unaffected_cve", 0),
    ]
    overview_table = "\n".join(overview_lines)

    w = rules["weights"]
    rule_lines = [
        "```",
        rules["formula"],
        "```",
        "",
        "| 维度 | 取值 | 系数 |",
        "| --- | --- | --- |",
    ]
    for k, v in w["asset_criticality"].items():
        rule_lines.append("| 资产关键度 | %s | %s |" % (k, v))
    for k, v in w["exposure"].items():
        rule_lines.append("| 暴露面 | %s | %s |" % (k, v))
    for k, v in w["exploit_factor"].items():
        rule_lines.append("| EXP/KEV | %s | %s |" % (k, v))
    rule_lines += [
        "",
        "| 级别 | 风险分区间 | SLA | 处置要求 |",
        "| --- | --- | --- | --- |",
    ]
    th = rules["level_thresholds"]
    sla = rules["sla_hours"]
    rule_lines.append("| Critical | >= %s | %s 小时 | %s |" % (th["Critical"], sla["Critical"], ACTION_CN["Critical"]))
    rule_lines.append("| High | >= %s | %s 小时 | %s |" % (th["High"], sla["High"], ACTION_CN["High"]))
    rule_lines.append("| Medium | >= %s | %s 小时 | %s |" % (th["Medium"], sla["Medium"], ACTION_CN["Medium"]))
    rule_lines.append("| Low | < %s | %s 小时（14 天） | %s |" % (th["Medium"], sla["Low"], ACTION_CN["Low"]))
    rule_block = "\n".join(rule_lines)

    # 关键案件详情
    key_cases = [c for c in cases if c["level"] in ("Critical", "High")]
    blocks = []
    for c in key_cases:
        calc = "%s × %s(%s) × %s(%s) × %s(%s) = **%.2f**（%s）" % (
            c["cvss_score"], c["asset_weight"], c["criticality"], c["exposure_factor"], c["exposure"],
            c["exploit_factor"], "公开EXP" if c["has_public_exploit"] else "无EXP", c["risk_score"], c["level"])
        blocks.append("\n".join([
            "### %s ｜ %s ｜ [%s]" % (c["case_id"], c["title"], c["level"]),
            "",
            "- CVE 编号：%s（CVSS %s%s）｜发布：%s｜情报来源：%s" % (
                c["cve_id"], c["cvss_score"], "，CISA KEV 在野利用" if c["in_kev"] else "",
                c["published"] or "未知", c["cve_source_url"] or "NVD"),
            "- 资产：%s（%s）｜业务：%s｜服务：%s｜端口：%s" % (
                c["hostname"], c["asset_ip"], c["business"], c["service"], c["port"]),
            "- 暴露面：%s｜扫描器严重度（参考）：%s｜最近检出：%s" % (
                c["exposure"], c["scanner_severity"], c["last_seen"]),
            "- 责任人：%s（%s）%s" % (
                c["owner"], c["department"], "｜⚠ 台账缺责任人，按兜底规则指派，需补台账" if c["owner_source"] == "fallback" else ""),
            "- 风险计算：%s" % calc,
            "- 时限要求：%s（截止 %s）" % (ACTION_CN[c["level"]], c["due_at"]),
            "- 证据编号：%s（具体报文/路径不进报告，避免二次泄露）" % (c["evidence_ref"] or "-"),
        ]))
    if not blocks:
        blocks.append("本期无 Critical / High 级别案件。")
    critical_blocks = "\n\n".join(blocks)

    full = ["| 案件号 | CVE | CVSS | 资产 | 业务 | 关键度 | 暴露面 | EXP | 风险分 | 级别 | 截止 | 责任人 | 状态 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for c in cases:
        full.append("| %s | %s | %s | %s(%s) | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            c["case_id"], c["cve_id"], c["cvss_score"], c["hostname"], c["asset_ip"], c["business"],
            c["criticality"], c["exposure"], "有" if c["has_public_exploit"] else "无",
            "%.2f" % c["risk_score"], "[%s]" % c["level"], c["due_at"],
            c["owner"] + ("(兜底)" if c["owner_source"] == "fallback" else ""), c["status"]))
    full_table = "\n".join(full)

    unmapped = cases_doc.get("unmapped_assets") or []
    if unmapped:
        ub = ["| 扫描项 | IP | 主机 | CVE | 扫描器严重度 | 处置建议 |", "| --- | --- | --- | --- | --- | --- |"]
        for u in unmapped:
            ub.append("| %s | %s | %s | %s | %s | 资产不在本次授权台账，先确认归属再定责，不得直接推送给无关团队 |" % (
                u["finding_id"], u["asset_ip"], u["hostname"], u["cve_id"], u["scanner_severity"]))
        unmapped_blocks = "\n".join(ub)
    else:
        unmapped_blocks = "无。"

    unaffected = cases_doc.get("unaffected_cve") or []
    if unaffected:
        ut = ["| CVE | 标题 | CVSS | 备注 |", "| --- | --- | --- | --- |"]
        for u in unaffected:
            ut.append("| %s | %s | %s | %s |" % (u["cve_id"], u["title"], u["cvss_score"], u["note"]))
        unaffected_table = "\n".join(ut)
    else:
        unaffected_table = "无。"

    if warnings:
        warnings_block = "\n".join("%d. %s" % (i + 1, w) for i, w in enumerate(warnings))
    else:
        warnings_block = "无数据质量告警。"

    steps = []
    for lv_name in LEVEL_ORDER:
        group = [c for c in cases if c["level"] == lv_name]
        if not group:
            continue
        steps.append("- [%s] %s 项，要求：%s。（%s）" % (
            lv_name, len(group), ACTION_CN[lv_name], "，".join(c["case_id"] for c in group)))
    progress_file = PROGRESS_DIR_LINE.format(date=date)
    steps.append("- 责任人回填：处置完成后更新 `%s`（status=fixed），次日自动转【待验证】并安排单资产复扫" % progress_file)
    steps.append("- 次日跟踪：`python scripts/track_case_state.py --date %s --state work/security_case/output/case_state_%s.json --progress %s`" % (
        next_date, date, progress_file))
    next_steps = "\n".join(steps)

    unmapped_ips = "、".join(u["asset_ip"] for u in (cases_doc.get("unmapped_assets") or [])) or "无"
    fallback_hosts = "、".join(sorted({c["hostname"] for c in cases if c["owner_source"] == "fallback"})) or "无"
    task_block = "\n".join([
        "- **任务理解**：把 %s 的 CVE 情报、扫描器夜跑结果、资产台账三源融合，算出每条漏洞落在本方资产上的处置优先级，" % date,
        "  产出可推送的处置报告与分责任人待办，并在次日跟踪闭环。",
        "- **使用工具/Skill**：redmine-security-auto-fix v2.0（本报告由 `scripts/gen_security_report.py` 生成，规则版本 %s，阈值批准口径 %s）" % (
            cases_doc["meta"]["rules_version"], rules.get("approved_by", "-")),
        "- **执行摘要**：CVE 情报 %s 原始 → %s 有效；扫描结果 %s 原始 → %s 归一后；资产台账 %s 原始 → %s 有效；" % (
            stats["cve_raw"], stats["cve_clean"], stats["scan_raw"], stats["scan_clean"],
            stats.get("asset_raw", "-"), stats["asset_clean"]),
        "  去重剔除 %s 条；三源融合后有效案件 **%s** 条（%s）；台账外未定责 %s 条。" % (
            stats["dedup_removed"], stats["case_count"], level_line, stats["unmapped_assets"]),
        "- **未确定项**：① 台账外 IP（%s）归属待线下核查，暂不推送；② %s 台账责任人缺失已按兜底策略指派，需补台账；" % (
            unmapped_ips, fallback_hosts),
        "  ③ 分级阈值是否调整属人工决策（本次不改规则，见复核记录）；④ 情报未进案件池 %s 条，逐条列于第六节。" % stats.get("unaffected_cve", 0),
    ])

    # 待办分组
    groups = {}
    for c in cases:
        groups.setdefault(c["owner"] or "待指派", []).append(c)
    todo_blocks = []
    for owner in sorted(groups.keys(), key=lambda o: min(
            LEVEL_ORDER.index(x["level"]) for x in groups[o])):
        todo_blocks.append("### 责任人：%s" % owner)
        todo_blocks.append("")
        todo_blocks.append("| 案件号 | 级别 | CVE | 资产 | 业务 | 截止 | 处置要求 |")
        todo_blocks.append("| --- | --- | --- | --- | --- | --- | --- |")
        for c in sorted(groups[owner], key=lambda x: LEVEL_ORDER.index(x["level"])):
            todo_blocks.append("| %s | [%s] | %s | %s(%s) | %s | %s | %s |" % (
                c["case_id"], c["level"], c["cve_id"], c["hostname"], c["asset_ip"], c["business"],
                c["due_at"], ACTION_CN[c["level"]]))
        todo_blocks.append("")

    return {
        "date": date,
        "next_date": next_date,
        "task_block": task_block,
        "overview_table": overview_table,
        "rule_block": rule_block,
        "critical_blocks": critical_blocks,
        "full_table": full_table,
        "unmapped_blocks": unmapped_blocks,
        "unaffected_table": unaffected_table,
        "warnings_block": warnings_block,
        "next_steps": next_steps,
        "todo_blocks": "\n".join(todo_blocks),
        "case_count": len(cases),
    }


def main(argv):
    args = parse_args(argv, {"date": "", "project": "我负责的项目", "outdir": ""})
    date = args.get("date")
    cases_path = args.get("cases") or work_path("output", "cases_%s.json" % date if date else "cases.json")
    if not date:
        stop("缺少 --date")
    path = cases_path if os.path.isabs(cases_path) else skill_path(cases_path)
    doc, err = read_json(path)
    if err:
        stop("读取融合结果失败: %s" % err)
    rules, err = load_config("triage_rules.json")
    if err:
        stop("分级规则缺失: config/security_case/triage_rules.json -> %s" % err)

    project = args.get("project") or "我负责的项目"
    b = build(doc, project, rules)
    outdir = args.get("outdir")
    if outdir:
        outdir = outdir if os.path.isabs(outdir) else skill_path(outdir)
    else:
        outdir = work_path("output")
    os.makedirs(outdir, exist_ok=True)

    report_tpl = open(skill_path("assets", "security_case_report_template.md"), "r", encoding="utf-8").read()
    todo_tpl = open(skill_path("assets", "security_case_todo_template.md"), "r", encoding="utf-8").read()

    common = {
        "project": project,
        "date": date,
        "case_count": str(b["case_count"]),
        "status": "待复核（本报告未经人工签字，禁止推送）",
        "source_line": "；".join("%s=%s" % (k, (v or "").split("/")[-1]) for k, v in (doc["meta"]["source_files"] or {}).items()),
        "formula": doc["meta"]["formula"],
        "rules_version": doc["meta"]["rules_version"],
        "approved_by": rules.get("approved_by", "-"),
        "reviewer": "（待人工签字）",
        "review_time": "（待填写）",
    }
    report_md = render(report_tpl, dict(common, **{
        "task_block": b["task_block"],
        "overview_table": b["overview_table"],
        "rule_block": b["rule_block"],
        "critical_blocks": b["critical_blocks"],
        "full_table": b["full_table"],
        "unmapped_blocks": b["unmapped_blocks"],
        "unaffected_table": b["unaffected_table"],
        "warnings_block": b["warnings_block"],
        "next_steps": b["next_steps"],
    }))
    sla_lines = ["| 级别 | SLA | 要求 |", "| --- | --- | --- |"]
    for lv_name in LEVEL_ORDER:
        sla_lines.append("| %s | %s 小时 | %s |" % (lv_name, rules["sla_hours"][lv_name], ACTION_CN[lv_name]))
    todo_md = render(todo_tpl, dict(common, **{
        "todo_blocks": b["todo_blocks"],
        "unmapped_blocks": b["unmapped_blocks"],
        "sla_block": "\n".join(sla_lines),
        "next_date": b["next_date"],
    }))

    report_path = os.path.join(outdir, "security_report_%s.md" % date)
    todo_path = os.path.join(outdir, "todo_%s.md" % date)
    state_path = os.path.join(outdir, "case_state_%s.json" % date)
    write_text(report_path, report_md)
    write_text(todo_path, todo_md)

    state = {
        "date": date,
        "project": project,
        "rules_version": doc["meta"]["rules_version"],
        "status": "pending_review",
        "cases": [{
            "case_id": c["case_id"], "cve_id": c["cve_id"], "asset_ip": c["asset_ip"],
            "hostname": c["hostname"], "business": c["business"], "owner": c["owner"],
            "owner_source": c["owner_source"], "level": c["level"], "risk_score": c["risk_score"],
            "due_at": c["due_at"], "sla_hours": c["sla_hours"], "status": "open",
            "track_history": [{"date": date, "action": "created", "by": "triage_cases"}],
        } for c in doc["cases"]],
        "review_log": [],
    }
    write_json(state_path, state)

    emit({"ok": True, "step": "gen_security_report",
          "written": [report_path.replace("\\", "/"), todo_path.replace("\\", "/"), state_path.replace("\\", "/")],
          "case_count": b["case_count"], "levels": doc["stats"]["levels"],
          "status": "pending_review", "note": "报告默认【待复核】，推送须经人工复核并先走测试目标"})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
