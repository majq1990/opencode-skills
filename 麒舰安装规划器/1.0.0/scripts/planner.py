#!/usr/bin/env python3
"""
planner.py — 部署规划核心脚本

输入：
  --servers      服务器列表 JSON
  --specs        服务组规格 JSON（来自规格接口或 fallback）
  --constraints  约束条件 JSON（pins / reserves / disables）
  --scale        用户规模（100/500/1000/2000/3000）
  --mode         产品模式（qijian/uma/lifeline/mingjing）
  --arch         架构类型（x86_64/aarch64）
  --output       输出结果 JSON 路径

输出：
  /tmp/dp_result.json — 规划结果，结构见 references/script_contracts.md
  stdout — 人类可读的摘要
  stderr — WARN / ERROR 前缀的问题信息
  退出码 — 0: 成功（可含警告）, 1: 致命错误
"""

import argparse
import json
import math
import sys
from copy import deepcopy

# ── 产品模式 → 服务组启禁规则 ─────────────────────────────────────
MODE_RULES = {
    "qijian": {
        "enable":  ["ip_web_eurbanpro", "ip_web_usercenter", "ip_web_linglong", "ip_web_dex"],
        "disable": ["ip_web_uma", "ip_web_mis", "ip_web_mf"],
    },
    "uma": {
        "enable":  ["ip_web_uma"],
        "disable": ["ip_web_mis", "ip_web_mf"],
    },
    "lifeline": {
        "enable":  ["ip_web_linglong"],
        "disable": ["ip_web_uma", "ip_web_mis", "ip_web_mf"],
    },
    "mingjing": {
        "enable":  ["ip_web_mis"],
        "disable": ["ip_web_uma", "ip_web_mf"],
    },
}

# 分类优先级（数字越小越优先）
CATEGORY_PRIORITY = {
    "db":      1,
    "cache":   2,
    "infra":   3,
    "gis":     4,
    "storage": 5,
    "app":     6,
    "biz":     7,
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def warn(msg):
    print(f"WARN {msg}", file=sys.stderr)


def error(msg):
    print(f"ERROR {msg}", file=sys.stderr)


# ── 预处理：服务组过滤与资源缩放 ──────────────────────────────────
def preprocess_groups(groups, mode, arch, disables):
    """
    返回处理后的服务组列表，每项含 enabled 字段。
    """
    mode_rule = MODE_RULES.get(mode, {"enable": [], "disable": []})
    arm = (arch == "aarch64")

    result = []
    for g in groups:
        g = deepcopy(g)

        # 1. 用户显式禁用
        if g["key"] in disables:
            g["enabled"] = False
            g["disable_reason"] = "user_disabled"
            result.append(g)
            continue

        # 2. 产品模式禁用
        if g["key"] in mode_rule["disable"]:
            g["enabled"] = False
            g["disable_reason"] = "mode_disabled"
            result.append(g)
            continue

        # 3. need=false 且 optional=true → 默认禁用（用户可覆盖）
        if not g.get("need", True) and g.get("optional", False):
            g["enabled"] = False
            g["disable_reason"] = "optional_default_off"
            result.append(g)
            continue

        g["enabled"] = True

        # 4. ARM CPU 上浮
        if arm:
            g["req_cpu"] = math.ceil(g["req_cpu"] * 1.2)
            g["arm_adjusted"] = True

        result.append(g)

    # 5. 按分类优先级排序（disabled 项排到最后）
    result.sort(key=lambda x: (
        0 if x["enabled"] else 1,
        CATEGORY_PRIORITY.get(x.get("category", "app"), 99)
    ))

    return result


# ── 服务器初始化 ───────────────────────────────────────────────────
def init_servers(servers):
    result = []
    for s in servers:
        s = deepcopy(s)
        s["mem_used"]  = 0
        s["cpu_used"]  = 0
        s["disk_used"] = 0
        result.append(s)
    return result


# ── 评分函数 ───────────────────────────────────────────────────────
def score(server):
    """综合余量得分：内存权重 0.5，CPU 权重 0.3，磁盘权重 0.2"""
    mem_ratio  = (server["mem"]  - server["mem_used"])  / max(server["mem"],  1)
    cpu_ratio  = (server["cpu"]  - server["cpu_used"])  / max(server["cpu"],  1)
    disk_ratio = (server["disk"] - server["disk_used"]) / max(server["disk"], 1)
    return mem_ratio * 0.5 + cpu_ratio * 0.3 + disk_ratio * 0.2


# ── 核心分配逻辑 ───────────────────────────────────────────────────
def find_best_server(servers, group, pins, reserves):
    """
    返回最合适的服务器，或 None（无可用节点时）。
    优先级：pin 约束 > reserve 约束 > 资源余量评分。
    """
    req_mem  = group["req_mem"]
    req_cpu  = group["req_cpu"]
    req_disk = group["req_disk"]

    # 1. 检查 pin 约束
    pinned_ip = pins.get(group["key"])
    if pinned_ip:
        pinned = next((s for s in servers if s["ip"] == pinned_ip), None)
        if pinned is None:
            error(f"pin 约束引用的 IP {pinned_ip} 不在服务器列表中，服务: {group['key']}")
            return None
        # pin 约束下仍记录超配警告
        if (pinned["mem"]  - pinned["mem_used"])  < req_mem:
            warn(f"{group['name']} 被 pin 到 {pinned_ip}，但该节点内存不足")
        if (pinned["cpu"]  - pinned["cpu_used"])  < req_cpu:
            warn(f"{group['name']} 被 pin 到 {pinned_ip}，但该节点 CPU 不足")
        return pinned

    # 2. 应用 reserve 约束过滤可用服务器
    category = group.get("category", "app")
    available = []
    for s in servers:
        reserved_cats = reserves.get(s["ip"])
        if reserved_cats and category not in reserved_cats:
            continue  # 该服务器被 reserve 给其他分类，跳过
        available.append(s)

    if not available:
        warn(f"{group['name']} 无可用服务器（所有节点被 reserve 约束排除）")
        return None

    # 3. 找满足资源要求的候选节点
    candidates = [
        s for s in available
        if (s["mem"]  - s["mem_used"])  >= req_mem
        and (s["cpu"]  - s["cpu_used"])  >= req_cpu
        and (s["disk"] - s["disk_used"]) >= req_disk
    ]

    if candidates:
        return max(candidates, key=score)

    # 4. 无满足节点 → 超配，选余量最大的
    warn(f"{group['name']} 资源不足，将超配分配")
    return max(available, key=score)


# ── 主规划函数 ─────────────────────────────────────────────────────
def plan(servers, groups, constraints, mode, arch):
    pins     = {p["group_key"]: p["ip"] for p in constraints.get("pins", [])}
    reserves = {r["ip"]: r["only_categories"] for r in constraints.get("reserves", [])}
    disables = set(constraints.get("disables", []))

    servers = init_servers(servers)
    groups  = preprocess_groups(groups, mode, arch, disables)

    assignments = []

    for group in groups:
        if not group["enabled"]:
            assignments.append({
                "key":            group["key"],
                "name":           group["name"],
                "category":       group.get("category", ""),
                "status":         "disabled",
                "disable_reason": group.get("disable_reason", ""),
                "assigned_ip":    None,
                "assigned_name":  None,
                "slave_ip":       None,
                "slave_name":     None,
                "req_mem":        group.get("req_mem", 0),
                "req_cpu":        group.get("req_cpu", 0),
                "req_disk":       group.get("req_disk", 0),
                "sub_type":       group.get("sub_type", ""),
                "module_type":    group.get("module_type", ""),
                "arm_adjusted":   group.get("arm_adjusted", False),
            })
            continue

        best = find_best_server(servers, group, pins, reserves)

        if best is None:
            status = "unassigned"
            assigned_ip   = None
            assigned_name = None
        else:
            best["mem_used"]  += group["req_mem"]
            best["cpu_used"]  += group["req_cpu"]
            best["disk_used"] += group["req_disk"]

            over_mem  = (best["mem"]  - best["mem_used"])  < 0
            over_cpu  = (best["cpu"]  - best["cpu_used"])  < 0
            status = "warn" if (over_mem or over_cpu) else "ok"

            assigned_ip   = best["ip"]
            assigned_name = best["name"]

        assignments.append({
            "key":           group["key"],
            "name":          group["name"],
            "category":      group.get("category", ""),
            "status":        status,
            "assigned_ip":   assigned_ip,
            "assigned_name": assigned_name,
            "slave_ip":      None,
            "slave_name":    None,
            "req_mem":       group["req_mem"],
            "req_cpu":       group["req_cpu"],
            "req_disk":      group["req_disk"],
            "sub_type":      group.get("sub_type", ""),
            "module_type":   group.get("module_type", ""),
            "arm_adjusted":  group.get("arm_adjusted", False),
        })

    # 服务器使用情况汇总
    server_summary = []
    for s in servers:
        mem_pct  = round(s["mem_used"]  / max(s["mem"],  1) * 100)
        cpu_pct  = round(s["cpu_used"]  / max(s["cpu"],  1) * 100)
        disk_pct = round(s["disk_used"] / max(s["disk"], 1) * 100)
        status = "ok"
        if mem_pct >= 100 or cpu_pct >= 100:
            status = "overloaded"
        elif mem_pct >= 90 or cpu_pct >= 90:
            status = "tight"
        server_summary.append({
            "ip":        s["ip"],
            "name":      s["name"],
            "mem_total": s["mem"],
            "mem_used":  s["mem_used"],
            "mem_pct":   mem_pct,
            "cpu_total": s["cpu"],
            "cpu_used":  s["cpu_used"],
            "cpu_pct":   cpu_pct,
            "disk_total": s["disk"],
            "disk_used":  s["disk_used"],
            "disk_pct":   disk_pct,
            "status":    status,
        })

    return {
        "assignments":     assignments,
        "server_summary":  server_summary,
        "params": {
            "scale": None,   # 由调用方填入
            "mode":  mode,
            "arch":  arch,
        },
    }


# ── 统计摘要（stdout）─────────────────────────────────────────────
def print_summary(result):
    a = result["assignments"]
    ok       = sum(1 for x in a if x["status"] == "ok")
    warn_cnt = sum(1 for x in a if x["status"] == "warn")
    unassign = sum(1 for x in a if x["status"] == "unassigned")
    disabled = sum(1 for x in a if x["status"] == "disabled")
    total    = len(a)

    print(f"规划完成：共 {total} 个服务组")
    print(f"  ✅ 正常分配  {ok}")
    print(f"  ⚠️ 超配警告  {warn_cnt}")
    print(f"  ❌ 未分配    {unassign}")
    print(f"  — 已禁用    {disabled}")

    if warn_cnt or unassign:
        print("\n问题服务：")
        for x in a:
            if x["status"] == "warn":
                print(f"  ⚠️ {x['name']} → {x['assigned_ip']} （超配）")
            elif x["status"] == "unassigned":
                print(f"  ❌ {x['name']} → 无可用节点")


# ── 入口 ───────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="eUrbanPro 部署规划脚本")
    parser.add_argument("--servers",     required=True)
    parser.add_argument("--specs",       required=True)
    parser.add_argument("--constraints", required=True)
    parser.add_argument("--scale",       required=True, type=int)
    parser.add_argument("--mode",        required=True,
                        choices=["qijian", "uma", "lifeline", "mingjing"])
    parser.add_argument("--arch",        required=True,
                        choices=["x86_64", "aarch64"])
    parser.add_argument("--output",      required=True)
    args = parser.parse_args()

    if args.scale > 5000:
        error("用户规模超过 5000，请联系技术支持部和质管部制定专属方案。")
        sys.exit(1)

    servers     = load_json(args.servers)
    specs       = load_json(args.specs)
    constraints = load_json(args.constraints)

    if not servers:
        error("服务器列表为空，无法规划。")
        sys.exit(1)

    groups = specs.get("groups", [])
    if not groups:
        error("服务组规格为空，请检查规格接口或 fallback 数据。")
        sys.exit(1)

    result = plan(servers, groups, constraints, args.mode, args.arch)
    result["params"]["scale"] = args.scale

    save_json(result, args.output)
    print_summary(result)

    # 有未分配服务时以非零退出码提示，但不终止（Claude 会解读）
    unassigned = [x for x in result["assignments"] if x["status"] == "unassigned"]
    if unassigned:
        sys.exit(2)


if __name__ == "__main__":
    main()
