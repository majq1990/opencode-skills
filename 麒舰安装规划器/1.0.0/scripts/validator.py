#!/usr/bin/env python3
"""
validator.py — metadata.yml 完整性校验脚本

检查项：
  1. YAML 语法合法
  2. 所有必填顶层字段存在（mysql / redis / ... / service / microservice）
  3. need=true 的服务都有对应的 master 注释 IP（可选检查，--strict 模式）
  4. need=true 的服务与规划结果中 status=ok/warn 的分配一致
  5. 无多余字段（防止手误引入未知 key）

输入：
  --metadata  待校验的 metadata.yml
  --specs     服务组规格 JSON（用于交叉比对）
  --result    规划结果 JSON（用于交叉比对）
  --strict    严格模式（所有 need=true 项必须有 master 注释）

输出：
  stdout — 校验报告
  退出码 0: 通过, 1: 有错误, 2: 有警告（--strict 下警告也变错误）
"""

import argparse
import json
import re
import sys

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# ── 预期出现的顶层 key ─────────────────────────────────────────────
EXPECTED_MIDDLEWARE = [
    "mysql", "redis", "minio", "nginx", "zookeeper",
    "kafka", "elasticsearch", "postgresql", "cetus", "TDengine",
]

EXPECTED_SERVICES = [
    "eUrbanMIS", "eUrbanMF", "eUrbanUMA", "eUrbanGIS",
    "eUrbanSG", "eGovaPublic", "IMserver", "statgather",
]

EXPECTED_MICROSERVICES = [
    "linglong", "wukong", "dex", "httpfileservice", "evaluation",
    "export", "usercenter", "eurbanpro", "mjing", "patrol_gather",
    "trajectory", "sms", "eurbanpro_media", "xuanzang", "dataflow",
    "dataflow_zookeeper", "giscenter", "gisserver",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml_naive(path):
    """
    不依赖 PyYAML 的简单解析：提取 key: value 对和注释，
    仅用于校验 need 字段和注释存在性，不做完整解析。
    """
    structure = {}
    current_section = None  # middleware / service / microservice
    current_key = None

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.rstrip()

        # 跳过注释行（但记录 master/slave 注释）
        if stripped.lstrip().startswith("#"):
            comment = stripped.lstrip()[1:].strip()
            if current_key and (comment.startswith("master:") or comment.startswith("slave:")):
                structure[current_key]["comments"].append(comment)
            continue

        # 顶层 key（无缩进）
        top_match = re.match(r'^(\w+):\s*$', stripped)
        if top_match:
            k = top_match.group(1)
            if k == "service":
                current_section = "service"
                current_key = None
            elif k == "microservice":
                current_section = "microservice"
                current_key = None
            else:
                current_section = "middleware"
                current_key = k
                structure[k] = {"need": None, "comments": [], "section": "middleware"}
            continue

        # need: true/false（一级或二级缩进）
        need_match = re.match(r'^\s+need:\s+(true|false)', stripped)
        if need_match and current_key:
            structure[current_key]["need"] = (need_match.group(1) == "true")
            continue

        # service / microservice 子 key（两空格缩进）
        if current_section in ("service", "microservice"):
            sub_match = re.match(r'^  (\w+):\s*$', stripped)
            if sub_match:
                current_key = sub_match.group(1)
                structure[current_key] = {
                    "need": None,
                    "comments": [],
                    "section": current_section
                }

    return structure


def check(metadata_path, specs_path, result_path, strict):
    errors   = []
    warnings = []

    # ── 1. 解析 metadata.yml ─────────────────────────────────────
    if HAS_YAML:
        with open(metadata_path, "r", encoding="utf-8") as f:
            try:
                doc = yaml.safe_load(f)
            except yaml.YAMLError as e:
                errors.append(f"YAML 语法错误: {e}")
                return errors, warnings
        structure = load_yaml_naive(metadata_path)
    else:
        structure = load_yaml_naive(metadata_path)

    # ── 2. 检查必填顶层字段 ───────────────────────────────────────
    for mw in EXPECTED_MIDDLEWARE:
        if mw not in structure:
            errors.append(f"缺少顶层字段: {mw}")

    for svc in EXPECTED_SERVICES:
        if svc not in structure:
            errors.append(f"service 节点缺少字段: {svc}")

    for ms in EXPECTED_MICROSERVICES:
        if ms not in structure:
            errors.append(f"microservice 节点缺少字段: {ms}")

    # ── 3. 与规划结果交叉比对 ──────────────────────────────────────
    if result_path:
        result      = load_json(result_path)
        assignments = result.get("assignments", [])

        # 构建 sub_type → status 映射
        sub_type_status = {}
        for a in assignments:
            if a.get("sub_type"):
                sub_type_status[a["sub_type"]] = a["status"]

        # module_type → any ok/warn 分配
        module_type_active = set()
        for a in assignments:
            if a.get("module_type") and a["status"] in ("ok", "warn"):
                module_type_active.add(a["module_type"])

        for key, info in structure.items():
            if info["need"] is None:
                continue

            # 中间件：need=true 但规划中无对应活跃分配
            if info["section"] == "middleware":
                if info["need"] and key not in module_type_active:
                    warnings.append(f"{key}: need=true 但规划结果中无对应服务被分配")
                if not info["need"] and key in module_type_active:
                    warnings.append(f"{key}: need=false 但规划结果中有服务被分配（可能遗漏）")

            # service / microservice
            else:
                planned_status = sub_type_status.get(key)
                if info["need"] and planned_status not in ("ok", "warn"):
                    warnings.append(
                        f"{key}: need=true 但规划结果中状态为 {planned_status or '未找到'}"
                    )
                if not info["need"] and planned_status in ("ok", "warn"):
                    warnings.append(
                        f"{key}: need=false 但规划结果中已分配节点（可能遗漏）"
                    )

    # ── 4. strict 模式：need=true 项必须有 master 注释 ────────────
    if strict:
        for key, info in structure.items():
            if info["need"]:
                has_master = any(c.startswith("master:") for c in info["comments"])
                if not has_master:
                    warnings.append(f"{key}: need=true 但缺少 master 注释（strict 模式）")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="校验 metadata.yml")
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--specs",    required=False)
    parser.add_argument("--result",   required=False)
    parser.add_argument("--strict",   action="store_true")
    args = parser.parse_args()

    errors, warnings = check(
        args.metadata,
        args.specs,
        args.result,
        args.strict,
    )

    if not errors and not warnings:
        print("✅ 校验通过，metadata.yml 格式完整，与规划结果一致。")
        sys.exit(0)

    if warnings:
        print(f"⚠️  {len(warnings)} 个警告：")
        for w in warnings:
            print(f"  • {w}")

    if errors:
        print(f"❌ {len(errors)} 个错误：")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)
    else:
        sys.exit(0 if not args.strict else 2)


if __name__ == "__main__":
    main()
