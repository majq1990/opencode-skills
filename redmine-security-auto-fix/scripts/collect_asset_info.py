# -*- coding: utf-8 -*-
"""资产台账采集（CMDB → 归一化）。v2.0 自 security-case-handling 移植。

用法：
  python scripts/collect_asset_info.py --file tests/fixtures/security_case/sample_asset.json --date 2026-09-22
  python scripts/collect_asset_info.py --fetch --date 2026-09-22   # 需 CMDB_TOKEN_REF 且内网放行

责任人一律以台账 owner 字段为准；台账为空时不猜不填，按 owner_missing_policy 兜底并在报告中标注。
"""
import copy
import os
import sys

from security_case_lib import (
    emit, load_config, norm_date, norm_enum, parse_args, read_json,
    skill_path, stop, work_path, write_json,
)

CRIT_ALIASES = {"core": "core", "high": "high", "medium": "medium", "low": "low",
                "核心": "core", "高": "high", "中": "medium", "低": "low"}
EXPO_ALIASES = {"public": "public", "internal": "internal", "isolated": "isolated",
                "公网": "public", "内网": "internal", "隔离": "isolated"}


def normalize(items, rules):
    """返回 (clean, warnings, dedup_removed)；同 IP 保留 updated_at 最新的一条。"""
    clean_map, warnings, dedup_removed = {}, [], 0
    w_crit = set(rules["weights"]["asset_criticality"].keys())
    w_expo = set(rules["weights"]["exposure"].keys())
    for idx, row in enumerate(items):
        seq = "row#%d" % (idx + 1)
        ip = (row.get("asset_ip") or "").strip()
        if not ip:
            warnings.append("%s 缺 asset_ip，已丢弃" % seq)
            continue
        crit_raw, expo_raw = row.get("criticality"), row.get("exposure")
        crit = norm_enum(crit_raw, w_crit, CRIT_ALIASES)
        expo = norm_enum(expo_raw, w_expo, EXPO_ALIASES)
        if crit is None:
            crit = "medium"
            warnings.append("%s(%s) criticality 脏值 %r，回退 medium" % (seq, ip, crit_raw))
        elif str(crit_raw).strip() != crit:
            warnings.append("%s(%s) criticality %r 已归一为 %s" % (seq, ip, crit_raw, crit))
        if expo is None:
            expo = "internal"
            warnings.append("%s(%s) exposure 脏值 %r，回退 internal" % (seq, ip, expo_raw))
        elif str(expo_raw).strip() != expo:
            warnings.append("%s(%s) exposure %r 已归一为 %s" % (seq, ip, expo_raw, expo))
        item = {
            "asset_ip": ip,
            "hostname": (row.get("hostname") or "").strip(),
            "business": (row.get("business") or "").strip(),
            "os": (row.get("os") or "").strip(),
            "service": (row.get("service") or "").strip(),
            "criticality": crit,
            "exposure": expo,
            "owner": (row.get("owner") or "").strip(),
            "department": (row.get("department") or "").strip(),
            "updated_at": norm_date(row.get("updated_at")),
        }
        if ip in clean_map:
            old = clean_map[ip]
            dedup_removed += 1
            if (item["updated_at"] or "") >= (old["updated_at"] or ""):
                warnings.append("同 IP %s 台账重复行，保留较新记录 %s(%s)，丢弃 %s(%s)" % (
                    ip, item["hostname"], item["updated_at"], old["hostname"], old["updated_at"]))
                clean_map[ip] = item
            else:
                warnings.append("同 IP %s 台账重复行，保留较新记录 %s(%s)，丢弃 %s(%s)" % (
                    ip, old["hostname"], old["updated_at"], item["hostname"], item["updated_at"]))
            continue
        clean_map[ip] = item
    clean = sorted(clean_map.values(), key=lambda x: x["asset_ip"])
    return clean, warnings, dedup_removed


def main(argv):
    args = parse_args(argv, {"date": "", "file": "", "out": ""})
    date = args.get("date") or ""
    cfg, err = load_config("asset.json")
    if err:
        stop("配置文件缺失: config/security_case/asset.json -> %s" % err)
    rules, err = load_config("triage_rules.json")
    if err:
        stop("配置文件缺失: config/security_case/triage_rules.json -> %s" % err)

    if "fetch" in args:
        token_ref = cfg.get("token_env_ref")
        if not os.environ.get(token_ref or "", ""):
            stop("缺少 CMDB 凭证：请先在环境变量 %s 中设置 Token（禁止把 Token 写进配置文件或提示词）" % token_ref,
                 hint="离线验证请改用 --file <样例台账 JSON>")
        stop("CMDB 线上拉取需内网出站权限，本机策略未放行；如需线上运行请先申请放行后重试")

    src = args.get("file") or cfg.get("sample_file")
    if not src:
        stop("未指定数据源：缺少 --file，且配置中无 sample_file")
    path = src if os.path.isabs(src) else skill_path(src)
    data, err = read_json(path)
    if err:
        stop("读取资产台账失败: %s" % err, source=src)
    raw_items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(raw_items, list):
        stop("资产台账结构异常：缺少 items 数组", source=src)
    raw_count = len(raw_items)

    items, warnings, dedup_removed = normalize(raw_items, rules)
    no_owner = [i["asset_ip"] for i in items if not i["owner"]]
    if no_owner:
        warnings.append("台账缺责任人资产 %d 台（%s），按 owner_missing_policy 兜底指派并转人工补台账" % (
            len(no_owner), ",".join(no_owner)))

    out = args.get("out") or work_path("cache", "asset", ("asset_%s.json" % date if date else "asset_latest.json"))
    payload = {
        "meta": {
            "source_name": cfg.get("source_name"),
            "source": path.replace("\\", "/"),
            "snapshot_date": cfg.get("snapshot_date"),
            "mode": "offline-sample" if args.get("file") else "live-fetch",
            "collected_date": date,
            "record_count_raw": raw_count,
            "record_count_clean": len(items),
            "dedup_removed": dedup_removed,
            "permission": cfg.get("permission"),
            "owner_authority": cfg.get("owner_authority"),
        },
        "items": items,
        "warnings": warnings,
    }
    write_json(out, payload)
    emit({"ok": True, "step": "collect_asset_info", "written": out.replace("\\", "/"),
          "raw": raw_count, "clean": len(items), "dedup_removed": dedup_removed,
          "no_owner_assets": no_owner, "warnings": warnings, "items": copy.deepcopy(items)})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
