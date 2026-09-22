# -*- coding: utf-8 -*-
"""漏洞扫描结果采集（nessus/openvas/xray 兼容 → 归一化）。v2.0 自 security-case-handling 移植。

用法：
  python scripts/collect_scanner_results.py --file tests/fixtures/security_case/sample_scan.json --date 2026-09-22
  python scripts/collect_scanner_results.py --fetch --date 2026-09-22   # 需 SCANNER_TOKEN_REF 且内网放行

只读拉取已有扫描结果，不触发新的扫描任务；扫描器严重度仅作参考字段，最终分级以 triage_rules.json 计算为准。
"""
import copy
import os
import sys

from security_case_lib import (
    emit, load_config, norm_date, norm_enum, parse_args, read_json,
    skill_path, stop, work_path, write_json,
)

LEVEL_ALIASES = {
    "critical": "critical", "严重": "critical", "crit": "critical",
    "high": "high", "高危": "high", "hi": "high",
    "medium": "medium", "中危": "medium", "med": "medium",
    "low": "low", "低危": "low",
    "info": "info", "informational": "info", "提示": "info",
}
LEVEL_CN = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low", "info": "Info"}


def normalize(items):
    clean, warnings = [], []
    for idx, row in enumerate(items):
        seq = "row#%d" % (idx + 1)
        fid = (row.get("finding_id") or "").strip() or seq
        ip = (row.get("asset_ip") or "").strip()
        cve_id = (row.get("cve_id") or "").strip()
        if not ip or not cve_id:
            warnings.append("%s(%s) 缺 asset_ip 或 cve_id，已丢弃" % (seq, fid))
            continue
        raw_sev = row.get("scanner_severity")
        sev = norm_enum(raw_sev, set(LEVEL_ALIASES.keys()), LEVEL_ALIASES)
        sev_warn = None
        # 只有"真正的脏值"才告警：纯大小写差异（critical/CRITICAL）不算问题，中文/别名写法才算
        if sev is None:
            sev, sev_warn = "unknown", "%s(%s) 扫描器严重度 %r 无法识别，记为 unknown（不影响自算分级）" % (seq, fid, raw_sev)
        elif str(raw_sev).strip().lower() != sev:
            sev_warn = "%s(%s) 扫描器严重度别名 %r 已归一为 %s" % (seq, fid, raw_sev, LEVEL_CN[sev])
        port = row.get("port")
        try:
            port = int(port)
        except Exception:
            port = 0
            warnings.append("%s(%s) port 非法，记为 0" % (seq, fid))
        item = {
            "finding_id": fid,
            "asset_ip": ip,
            "hostname": (row.get("hostname") or "").strip(),
            "port": port,
            "protocol": (row.get("protocol") or "tcp").strip(),
            "service": (row.get("service") or "").strip(),
            "cve_id": cve_id,
            "scanner_severity": LEVEL_CN.get(sev, "unknown"),
            "scanner_severity_raw": raw_sev,
            "first_seen": norm_date(row.get("first_seen")),
            "last_seen": norm_date(row.get("last_seen")),
            "evidence_ref": (row.get("evidence_ref") or "").strip(),
            "owner_from_scan": (row.get("owner") or "").strip(),  # 仅记录，不作为定责依据
        }
        clean.append(item)
        if sev_warn:
            warnings.append(sev_warn)
    return clean, warnings


def dup_groups(items, key_fields):
    seen, dup = {}, 0
    for it in items:
        k = tuple(str(it.get(f, "")) for f in key_fields)
        if k in seen:
            dup += 1
        seen[k] = 1
    return dup


def main(argv):
    args = parse_args(argv, {"date": "", "file": "", "out": ""})
    date = args.get("date") or ""
    cfg, err = load_config("scanner.json")
    if err:
        stop("配置文件缺失: config/security_case/scanner.json -> %s" % err)
    rules, err = load_config("triage_rules.json")
    if err:
        stop("配置文件缺失: config/security_case/triage_rules.json -> %s" % err)

    if "fetch" in args:
        token_ref = cfg.get("token_env_ref")
        if not os.environ.get(token_ref or "", ""):
            stop("缺少扫描器凭证：请先在环境变量 %s 中设置 Token（禁止把 Token 写进配置文件或提示词）" % token_ref,
                 hint="离线验证请改用 --file <样例扫描结果 JSON>")
        base_ref = cfg.get("base_url_env_ref")
        if not os.environ.get(base_ref or "", ""):
            stop("缺少扫描器地址：请先在环境变量 %s 中设置只读 API 地址" % base_ref)
        stop("扫描器线上拉取需内网出站权限，本机策略未放行；如需线上运行请先申请放行后重试")

    src = args.get("file") or cfg.get("sample_file")
    if not src:
        stop("未指定数据源：缺少 --file，且配置中无 sample_file")
    path = src if os.path.isabs(src) else skill_path(src)
    data, err = read_json(path)
    if err:
        stop("读取扫描结果失败: %s" % err, source=src)
    raw_items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(raw_items, list):
        stop("扫描结果结构异常：缺少 items 数组", source=src)
    raw_count = len(raw_items)

    items, warnings = normalize(raw_items)
    key_fields = rules.get("dedup", {}).get("key", ["asset_ip", "cve_id", "port"])
    dup = dup_groups(items, key_fields)
    if dup:
        warnings.append("检测到重复定位键 %d 条（%s），融合阶段按去重窗口 %s 天去重" % (
            dup, "+".join(key_fields), rules.get("dedup", {}).get("window_days", 7)))

    out = args.get("out") or work_path("cache", "scan", ("scan_%s.json" % date if date else "scan_latest.json"))
    payload = {
        "meta": {
            "source_name": cfg.get("source_name"),
            "scanner": cfg.get("scanner"),
            "source": path.replace("\\", "/"),
            "mode": "offline-sample" if args.get("file") else "live-fetch",
            "collected_date": date,
            "record_count_raw": raw_count,
            "record_count_clean": len(items),
            "duplicate_key_groups": dup,
            "permission": cfg.get("permission"),
            "note": "扫描器严重度为参考字段，最终分级以 config/security_case/triage_rules.json 计算为准",
        },
        "items": items,
        "warnings": warnings,
    }
    write_json(out, payload)
    emit({"ok": True, "step": "collect_scanner_results", "written": out.replace("\\", "/"),
          "raw": raw_count, "clean": len(items), "duplicate_key_groups": dup,
          "warnings": warnings, "items": copy.deepcopy(items)})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
