# -*- coding: utf-8 -*-
"""次日滚动跟踪：读取案件状态 → 分类（超期 / 进行中 / 待验证）→ 生成次日提醒。

v2.0 自 security-case-handling 移植。

用法：
  python scripts/track_case_state.py --date 2026-09-23 \
      --state work/security_case/output/case_state_2026-09-22.json \
      [--progress work/security_case/progress/progress_2026-09-22.json]

progress 文件格式（人工回填，登记口头/钉钉回报的处置进展）：
  {"SC-2026-09-22-002": {"status": "fixed", "by": "王磊", "note": "已升级 Log4j 到 2.17.2 并复测"}}

输出：
  work/security_case/output/nextday_reminder_<date>.md —— 超期/进行中/待验证三类清单，
  供次日 09:00 复核后决定是否升级上报；状态文件原地更新 track_log。
"""
import json
import os
import sys
from datetime import datetime

from security_case_lib import (
    emit, parse_args, read_json, skill_path, stop, work_path, write_json, write_text,
)

LEVEL_ORDER = ["Critical", "High", "Medium", "Low"]
LEVEL_CN = {"Critical": "[紧急]", "High": "[高]", "Medium": "[中]", "Low": "[低]"}


def main(argv):
    args = parse_args(argv, {"date": "", "state": "", "progress": "", "outdir": ""})
    date = args.get("date")
    if not date:
        stop("缺少 --date（跟踪基准日，一般为研判日次日）")
    state_path = args.get("state") or work_path("output", "case_state_%s.json" % date)
    state, err = read_json(state_path)
    if err:
        stop("未找到案件状态文件: %s" % state_path, hint="请先执行 gen_security_report.py 生成状态文件")
    try:
        base = datetime.strptime("%s 09:00" % date, "%Y-%m-%d %H:%M")
    except Exception as e:
        stop("--date 格式应为 YYYY-MM-DD: %s" % e)

    progress = {}
    src = args.get("progress")
    if src:
        p = src if os.path.isabs(src) else skill_path(src)
        doc, e = read_json(p)
        if e:
            stop("读取进展回填文件失败: %s" % e)
        progress = doc if isinstance(doc, dict) else {}

    overdue, running, pending_verify, closed = [], [], [], []
    for c in state.get("cases", []):
        cid = c["case_id"]
        upd = progress.get(cid) or {}
        if upd.get("status"):
            c["status"] = upd["status"]
            c.setdefault("track_history", []).append({
                "date": date, "action": "status->%s" % upd["status"],
                "by": upd.get("by", "unknown"), "note": upd.get("note", "")})
        due = datetime.strptime(c.get("due_at"), "%Y-%m-%d %H:%M")
        if c["status"] in ("fixed", "verified"):
            (pending_verify if c["status"] == "fixed" else closed).append(c)
            continue
        if c["status"] == "closed":
            closed.append(c)
            continue
        if base > due:
            c["overdue_hours"] = round((base - due).total_seconds() / 3600.0, 1)
            overdue.append(c)
        else:
            running.append(c)

    def table(rows, show_overdue=False):
        if not rows:
            return "无。"
        head = ["| 案件号 | 级别 | CVE | 资产 | 责任人 | 截止 | %s |" % ("超期时长" if show_overdue else "状态"),
                "| --- | --- | --- | --- | --- | --- | --- |"]
        for c in sorted(rows, key=lambda x: (LEVEL_ORDER.index(x["level"]), -(x.get("overdue_hours") or 0))):
            tail = ("%s 小时" % c["overdue_hours"]) if show_overdue else c["status"]
            head.append("| %s | %s | %s | %s(%s) | %s | %s | %s |" % (
                c["case_id"], LEVEL_CN.get(c["level"], c["level"]), c["cve_id"], c["hostname"],
                c["asset_ip"], c["owner"], c["due_at"], tail))
        return "\n".join(head)

    md = "\n".join([
        "# 安全案件次日跟踪提醒（%s）" % date,
        "",
        "> 来源状态文件：%s" % state_path.replace("\\", "/"),
        "> 跟踪口径：基准日 %s 09:00 比对案件 SLA 截止时间；三类清单需人工复核后决定是否升级上报" % date,
        "",
        "## 一、超期未闭环（%d 项）" % len(overdue),
        "",
        table(overdue, show_overdue=True),
        "",
        "处置建议：由我本人核对是否已私下处理；确未处理的在 %s 12:00 前同步责任人及直属主管。" % date,
        "",
        "## 二、进行中（%d 项）" % len(running),
        "",
        table(running),
        "",
        "## 三、待验证（%d 项，责任人已回报修复）" % len(pending_verify),
        "",
        table(pending_verify),
        "",
        "处置建议：安排一次针对性复扫（只扫单资产单端口），复扫无命中后再置 verified；未通过回到进行中。",
        "",
        "## 四、已闭环（%d 项）" % len(closed),
        "",
        table(closed),
        "",
        "---",
        "",
        "生成脚本：`scripts/track_case_state.py`（只读状态文件 + 只写本地 work/）",
        "人工复核人：（待签字）｜复核时间：（待填写）",
    ])

    outdir = args.get("outdir")
    if outdir:
        outdir = outdir if os.path.isabs(outdir) else skill_path(outdir)
    else:
        outdir = work_path("output")
    os.makedirs(outdir, exist_ok=True)
    out_path = os.path.join(outdir, "nextday_reminder_%s.md" % date)
    write_text(out_path, md)
    state.setdefault("track_log", []).append({
        "date": date, "overdue": len(overdue), "in_progress": len(running),
        "pending_verify": len(pending_verify), "closed": len(closed),
        "reminder_file": out_path.replace("\\", "/")})
    write_json(state_path, state)

    emit({"ok": True, "step": "track_case_state", "written": out_path.replace("\\", "/"),
          "overdue": len(overdue), "in_progress": len(running),
          "pending_verify": len(pending_verify), "closed": len(closed),
          "overdue_ids": [c["case_id"] for c in overdue],
          "pending_verify_ids": [c["case_id"] for c in pending_verify]})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
