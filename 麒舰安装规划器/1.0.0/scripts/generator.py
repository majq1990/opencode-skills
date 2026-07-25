#!/usr/bin/env python3
"""
generator.py — 从规划结果生成 metadata.yml

输入：
  --result   规划结果 JSON（/tmp/dp_result.json）
  --specs    服务组规格 JSON（/tmp/dp_specs.json）
  --output   输出路径（/tmp/metadata.yml）
  --fix      尝试自动修正已知问题（可选标志）

输出：
  metadata.yml — 符合 eUrbanPro 一键部署项目格式的配置文件
  退出码 0: 成功, 1: 致命错误
"""

import argparse
import json
import sys
from datetime import datetime

# ── 字段映射：module_type / sub_type → metadata.yml 结构 ──────────

# 顶层中间件 key
MIDDLEWARE_TYPES = {
    "mysql", "redis", "minio", "nginx", "zookeeper",
    "kafka", "elasticsearch", "postgresql", "cetus", "TDengine",
}

# service 节点下的 sub_type
SERVICE_SUB_TYPES = {
    "eUrbanMIS", "eUrbanMF", "eUrbanUMA", "eUrbanGIS",
    "eUrbanSG", "eGovaPublic", "IMserver", "statgather",
}

# microservice 节点下的所有 sub_type（完整列表，确保未规划的也出现在 yml 中）
ALL_MICROSERVICES = [
    "linglong", "wukong", "dex", "httpfileservice", "evaluation",
    "export", "usercenter", "eurbanpro", "mjing", "patrol_gather",
    "trajectory", "sms", "eurbanpro_media", "xuanzang", "dataflow",
    "dataflow_zookeeper", "giscenter", "gisserver",
]

# 所有中间件（确保未规划的也以 need: false 出现）
ALL_MIDDLEWARE = [
    "mysql", "redis", "minio", "nginx", "zookeeper",
    "kafka", "elasticsearch", "postgresql", "cetus", "TDengine",
]

# 所有 service
ALL_SERVICES = [
    "eUrbanMIS", "eUrbanMF", "eUrbanUMA", "eUrbanGIS",
    "eUrbanSG", "eGovaPublic", "IMserver", "statgather",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_comment(label, ip, name):
    """生成节点注释行"""
    if not ip:
        return ""
    display = f"{ip} ({name})" if name else ip
    return f"  # {label}: {display}"


def generate_yaml(result, specs):
    assignments = result["assignments"]
    params      = result["params"]

    # 建立 sub_type → assignment 的映射（只取 enabled 且已分配的）
    sub_type_map = {}
    for a in assignments:
        if a["status"] in ("ok", "warn") and a.get("sub_type"):
            sub_type_map[a["sub_type"]] = a

    # 建立 module_type → assignment 列表（一个 module_type 可能有多个服务组，如 mysql）
    module_map = {}
    for a in assignments:
        if a["status"] in ("ok", "warn") and a.get("module_type"):
            mt = a["module_type"]
            module_map.setdefault(mt, [])
            module_map[mt].append(a)

    ts    = datetime.now().strftime("%Y-%m-%d %H:%M")
    scale = params.get("scale", "")
    mode  = params.get("mode", "")
    arch  = params.get("arch", "")

    lines = [
        f"# 由 eUrbanPro 部署规划工具生成",
        f"# 生成时间: {ts}",
        f"# 用户规模: {scale} | 产品模式: {mode} | 架构: {arch}",
        "",
        "# ── 中间件 ──────────────────────────────────────────",
        "",
    ]

    # 中间件节点
    for mw in ALL_MIDDLEWARE:
        enabled_assignments = module_map.get(mw, [])
        need = len(enabled_assignments) > 0
        lines.append(f"{mw}:")
        lines.append(f"  need: {'true' if need else 'false'}")
        if need:
            for a in enabled_assignments:
                master_comment = format_comment("master", a["assigned_ip"], a["assigned_name"])
                if master_comment:
                    lines.append(master_comment)
                slave_comment = format_comment("slave", a.get("slave_ip"), a.get("slave_name"))
                if slave_comment:
                    lines.append(slave_comment)
        lines.append("")

    # service 节点
    lines += [
        "# ── 应用服务 ─────────────────────────────────────────",
        "",
        "service:",
        "",
    ]
    for svc in ALL_SERVICES:
        a = sub_type_map.get(svc)
        need = a is not None
        lines.append(f"  {svc}:")
        lines.append(f"    need: {'true' if need else 'false'}")
        if need:
            master_comment = format_comment("master", a["assigned_ip"], a["assigned_name"])
            if master_comment:
                lines.append("  " + master_comment.lstrip())
            slave_comment = format_comment("slave", a.get("slave_ip"), a.get("slave_name"))
            if slave_comment:
                lines.append("  " + slave_comment.lstrip())
        lines.append("")

    # microservice 节点
    lines += [
        "# ── 微服务 ───────────────────────────────────────────",
        "",
        "microservice:",
        "",
    ]
    for ms in ALL_MICROSERVICES:
        a = sub_type_map.get(ms)
        need = a is not None
        lines.append(f"  {ms}:")
        lines.append(f"    need: {'true' if need else 'false'}")
        if need:
            master_comment = format_comment("master", a["assigned_ip"], a["assigned_name"])
            if master_comment:
                lines.append("  " + master_comment.lstrip())
            slave_comment = format_comment("slave", a.get("slave_ip"), a.get("slave_name"))
            if slave_comment:
                lines.append("  " + slave_comment.lstrip())
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="生成 metadata.yml")
    parser.add_argument("--result",  required=True)
    parser.add_argument("--specs",   required=True)
    parser.add_argument("--output",  required=True)
    parser.add_argument("--fix",     action="store_true", help="自动修正已知问题")
    args = parser.parse_args()

    result = load_json(args.result)
    specs  = load_json(args.specs)

    yaml_content = generate_yaml(result, specs)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print(f"✅ metadata.yml 已生成：{args.output}")


if __name__ == "__main__":
    main()
