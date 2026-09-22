# -*- coding: utf-8 -*-
"""CVE 情报 × 扫描结果 × 资产台账 三源融合研判分级。v2.0 自 security-case-handling 移植。

用法：
  python scripts/triage_cases.py --cve <cve_items.json> \
      --scan <scan.json> --asset <asset.json> \
      --date 2026-09-22 [--time 09:00] [--out <cases.json>]

缺省输入路径在 work/security_case/cache/{cve,scan,asset}/ 下按日期查找。
风险分 = round(cvss × 资产关键度权重 × 暴露面系数 × EXP系数, 2)
分级阈值与 SLA 全部来自 config/security_case/triage_rules.json，改 JSON 不碰代码。
融合后 0 案件 → 返回 {"ok":false,"gap":...} 并停止（exit 2）。

CVE 情报输入 schema（与 collect_cve_intel.py 文档对齐）：
  {"meta": {...}, "items": [{"cve_id","title","cvss_score","has_public_exploit",
    "in_kev","published","source_url"}]}
"""
import copy
import os
import sys
from datetime import datetime, timedelta

from security_case_lib import (
    emit, load_config, parse_args, read_json, skill_path, stop, to_float, work_path, write_json,
)

LEVEL_ORDER = ["Critical", "High", "Medium", "Low"]


def level_of(score, thresholds):
    if score >= thresholds.get("Critical", 12.0):
        return "Critical"
    if score >= thresholds.get("High", 8.0):
        return "High"
    if score >= thresholds.get("Medium", 4.0):
        return "Medium"
    return "Low"


def dedup(findings, key_fields):
    """按 dedup.key 去重，保留 last_seen / first_seen 最新的一条。"""
    kept, removed = {}, []
    for f in findings:
        k = tuple(str(f.get(x, "")) for x in key_fields)
        cur = kept.get(k)
        if cur is None:
            kept[k] = f
            continue
        if (f.get("last_seen") or "") >= (cur.get("last_seen") or ""):
            removed.append({"kept": cur.get("finding_id"), "dropped": f.get("finding_id"),
                            "reason": "同资产同CVE同端口重复，保留 last_seen 较新者"})
            kept[k] = f
        else:
            removed.append({"kept": cur.get("finding_id"), "dropped": f.get("finding_id"),
                            "reason": "同资产同CVE同端口重复，保留 last_seen 较新者"})
    return list(kept.values()), removed


def main(argv):
    args = parse_args(argv, {"date": "", "time": "09:00", "out": ""})
    date = args.get("date")
    if not date:
        stop("缺少 --date（研判基准日期，用于计算 SLA 到期时间）")

    rules, err = load_config("triage_rules.json")
    if err:
        stop("分级规则缺失: config/security_case/triage_rules.json -> %s" % err)

    weights = rules["weights"]
    w_crit = weights["asset_criticality"]
    w_expo = weights["exposure"]
    w_exp = weights["exploit_factor"]
    thresholds = rules["level_thresholds"]
    sla = rules["sla_hours"]
    dedup_cfg = rules["dedup"]
    owner_policy = rules["owner_missing_policy"]

    loaded, warnings = {}, []
    for name, key in (("cve", "cve"), ("scan", "scan"), ("asset", "asset")):
        src = args.get(key) or work_path("cache", name, "%s_%s.json" % (name, date))
        path = src if os.path.isabs(src) else skill_path(src)
        data, e = read_json(path)
        if e:
            stop("数据源缺失: %s -> %s" % (key, e), hint="请先执行对应的 collect_*.py 步骤")
        loaded[key] = data
        for w in (loaded[key].get("warnings") or []):
            warnings.append("[%s] %s" % (key, w))

    cve_idx = {c["cve_id"]: c for c in loaded["cve"].get("items", [])}
    asset_idx = {a["asset_ip"]: a for a in loaded["asset"].get("items", [])}

    findings, removed = dedup(loaded["scan"].get("items", []), dedup_cfg.get("key", ["asset_ip", "cve_id", "port"]))
    for r in removed:
        warnings.append("[scan] %s -> %s（%s）" % (r["dropped"], r["kept"], r["reason"]))

    unmapped_assets, unmapped_cve, cases = [], [], []
    for f in findings:
        cve = cve_idx.get(f["cve_id"])
        asset = asset_idx.get(f["asset_ip"])
        if asset is None:
            unmapped_assets.append({
                "finding_id": f.get("finding_id") or "",
                "asset_ip": f["asset_ip"], "hostname": f.get("hostname") or "",
                "port": f.get("port"), "cve_id": f["cve_id"],
                "scanner_severity": f.get("scanner_severity") or "",
                "issue": "扫描资产不在本次授权台账内，无法定责，需人工确认归属后再入案件池",
            })
            continue
        if cve is None:
            unmapped_cve.append({"finding_id": f.get("finding_id") or "", "cve_id": f["cve_id"],
                                 "asset_ip": f["asset_ip"],
                                 "issue": "扫描命中 CVE 不在本次情报窗口内，需人工补充情报后再分级"})
            continue

        cvss = to_float(cve.get("cvss_score"))
        if cvss is None:
            unmapped_cve.append({"finding_id": f.get("finding_id") or "", "cve_id": f["cve_id"],
                                 "asset_ip": f["asset_ip"],
                                 "issue": "CVE 情报缺有效 cvss_score（原始值 %r），转人工补充后再分级"
                                          % (cve.get("cvss_score"),)})
            continue

        aw = w_crit.get(asset["criticality"], 0.6)
        ef = w_expo.get(asset["exposure"], 1.0)
        xf = w_exp.get("public_exploit", 1.15) if cve["has_public_exploit"] else w_exp.get("none", 1.0)
        score = round(cvss * aw * ef * xf, 2)
        level = level_of(score, thresholds)
        sla_h = sla.get(level, 72)
        base = datetime.strptime("%s %s" % (date, args.get("time", "09:00")), "%Y-%m-%d %H:%M")
        due_at = (base + timedelta(hours=sla_h)).strftime("%Y-%m-%d %H:%M")

        owner = asset.get("owner") or ""
        owner_source = "asset_owner"
        if not owner:
            owner = owner_policy.get("default_owner", "安全运维值班（待指派）")
            owner_source = "fallback"
        # collect_scanner_results 归一后字段为 owner_from_scan；直喂原始扫描数据时兼容 owner 键
        owner_from_scan = f.get("owner_from_scan") or f.get("owner") or ""
        if owner_from_scan and owner_from_scan != owner:
            warnings.append("[scan] %s 扫描器自带 owner=%s 与台账 %s 不一致，忽略扫描器值（定责以台账为准）"
                            % (f.get("finding_id") or "", owner_from_scan, owner or "空"))

        cases.append({
            "case_id": "",
            "cve_id": cve["cve_id"],
            "title": cve["title"],
            "cvss_score": cvss,
            "has_public_exploit": cve["has_public_exploit"],
            "in_kev": cve["in_kev"],
            "published": cve["published"],
            "asset_ip": asset["asset_ip"],
            "hostname": asset["hostname"],
            "business": asset["business"],
            "service": asset["service"],
            "criticality": asset["criticality"],
            "exposure": asset["exposure"],
            "asset_weight": aw,
            "exposure_factor": ef,
            "exploit_factor": xf,
            "risk_score": score,
            "level": level,
            "sla_hours": sla_h,
            "due_at": due_at,
            "owner": owner,
            "owner_source": owner_source,
            "department": asset.get("department", ""),
            "port": f.get("port"),
            "scanner_severity": f.get("scanner_severity") or "",
            "last_seen": f.get("last_seen") or "",
            "evidence_ref": f.get("evidence_ref") or "",
            "status": "open",
            "cve_source_url": cve.get("source_url", ""),
        })

    if not cases:
        stop("三源融合后有效案件为 0，停止出报告（请检查数据源范围与去重结果）",
             hint="如属正常无风险场景，需在报告中显式写明【无有效案件】并经人工确认后再归档")

    cases.sort(key=lambda c: (-c["risk_score"], c["cve_id"]))
    for i, c in enumerate(cases, 1):
        c["case_id"] = "SC-%s-%03d" % (date, i)

    used_cve = {c["cve_id"] for c in cases}
    orphan_cve = {u["cve_id"] for u in unmapped_assets}
    unused_cve = [{"cve_id": c["cve_id"], "title": c["title"], "cvss_score": c["cvss_score"],
                   "note": ("扫描命中台账外资产，待归属确认后再定责（见未定责清单）"
                            if c["cve_id"] in orphan_cve else
                            "情报窗口内未命中本次台账资产（暂不影响我方资产）")}
                  for c in loaded["cve"].get("items", []) if c["cve_id"] not in used_cve]

    levels = {lv: 0 for lv in LEVEL_ORDER}
    for c in cases:
        levels[c["level"]] = levels.get(c["level"], 0) + 1

    out = args.get("out") or work_path("output", "cases_%s.json" % date)
    payload = {
        "meta": {
            "date": date,
            "base_time": "%s %s" % (date, args.get("time", "09:00")),
            "formula": rules["formula"],
            "rules_version": rules["version"],
            "source_files": {k: (v.get("meta", {}) or {}).get("source", "") for k, v in loaded.items()},
            "dedup_key": dedup_cfg.get("key"),
            "dedup_window_days": dedup_cfg.get("window_days"),
        },
        "stats": {
            "cve_raw": loaded["cve"].get("meta", {}).get("record_count_raw"),
            "cve_clean": len(loaded["cve"].get("items", [])),
            "scan_raw": loaded["scan"].get("meta", {}).get("record_count_raw"),
            "scan_clean": len(loaded["scan"].get("items", [])),
            "asset_raw": loaded["asset"].get("meta", {}).get("record_count_raw"),
            "asset_clean": len(loaded["asset"].get("items", [])),
            "case_count": len(cases),
            "dedup_removed": len(removed),
            "unmapped_assets": len(unmapped_assets),
            "unmapped_cve": len(unmapped_cve),
            "unaffected_cve": len(unused_cve),
            "levels": levels,
        },
        "cases": cases,
        "unmapped_assets": unmapped_assets,
        "unmapped_cve": unmapped_cve,
        "unaffected_cve": unused_cve,
        "warnings": warnings,
    }
    write_json(out, payload)
    emit({"ok": True, "step": "triage_cases", "written": out.replace("\\", "/"),
          "count": len(cases), "levels": levels, "dedup_removed": len(removed),
          "unmapped_assets": len(unmapped_assets), "unaffected_cve": len(unused_cve),
          "warnings": warnings, "cases": copy.deepcopy(cases)})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
