"""钉钉表格写入模块 — 将打包记录写入钉钉在线表格."""
from __future__ import annotations

import json
import yaml
from pathlib import Path
from typing import Any

DINGTALK_SPREADSHEET_NODE_ID = "2Amq4vjg89gq7LzDsPB9boynV3kdP0wQ"
DINGTALK_SPREADSHEET_SHEET_ID = "kgqie6hm"


def _load_meta(recipe_dir: str) -> dict[str, Any]:
    """加载 recipe 的 meta.yaml 文件."""
    meta_path = Path(recipe_dir) / "meta.yaml"
    if not meta_path.exists():
        return {}
    with open(meta_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_runtime_depends(meta: dict[str, Any], os_family: str) -> str:
    """从 meta.yaml 获取运行时依赖."""
    runtime = meta.get("runtime_depends", {})
    if os_family in ("centos", "openeuler", "anolis", "kylin", "uos"):
        depends = runtime.get("rpm", [])
    elif os_family == "ubuntu":
        depends = runtime.get("deb", [])
    else:
        depends = []
    return ", ".join(depends) if depends else "无"


def collect_build_records(
    software: str,
    version: str,
    output_dir: str,
    recipe_dir: str,
) -> list[dict[str, str]]:
    """收集打包记录.

    Returns:
        记录列表，每条记录包含: 软件名称, 版本, 操作系统, 系统版本, 下载路径, 安装依赖清单
    """
    import platform
    arch = platform.machine() or "x86_64"
    if arch == "AMD64":
        arch = "x86_64"

    meta = _load_meta(recipe_dir)
    records = []

    output_path = Path(output_dir)
    if not output_path.exists():
        return records

    for distro_tag in sorted(output_path.iterdir()):
        if not distro_tag.is_dir():
            continue

        os_family, os_version = _parse_distro_tag(distro_tag.name)
        if not os_family:
            continue

        depends = _get_runtime_depends(meta, os_family)

        for pkg_file in sorted(distro_tag.iterdir()):
            if not pkg_file.is_file():
                continue
            if not (pkg_file.name.endswith(".rpm") or pkg_file.name.endswith(".deb")):
                continue

            download_url = f"http://182.92.5.151:38081/MediaRoot/rpm/{os_family}/{os_version}/{arch}/{pkg_file.name}"
            records.append({
                "软件名称": software,
                "版本": version,
                "操作系统": os_family,
                "系统版本": os_version,
                "下载路径": download_url,
                "安装依赖清单": depends,
            })

    return records


def _parse_distro_tag(tag: str) -> tuple[str, str]:
    """解析 distro_tag 为 (os_family, os_version).

    Examples:
        centos-7 → (centos, 7)
        openeuler-openeuler-24.03-lts → (openeuler, 24.03-lts)
        openanolis-anolisos-8.6 → (anolis, 8.6)
        ubuntu-22.04 → (ubuntu, 22.04)
        macrosan-kylin-v10-sp2 → (kylin, v10-sp2)
        macrosan-uos-v20-1070 → (uos, v20-1070)
    """
    static_map = {
        "centos-6": ("centos", "6"),
        "centos-7": ("centos", "7"),
        "centos-stream9": ("centos", "stream9"),
        "centos-stream10": ("centos", "stream10"),
        "macrosan-uos-v20-1050": ("uos", "v20-1050"),
        "macrosan-uos-v20-1060": ("uos", "v20-1060"),
        "macrosan-uos-v20-1070": ("uos", "v20-1070"),
        "macrosan-kylin-v10-sp1": ("kylin", "v10-sp1"),
        "macrosan-kylin-v10-sp2": ("kylin", "v10-sp2"),
        "macrosan-kylin-v10-sp3": ("kylin", "v10-sp3"),
        "macrosan-kylin-v10-sp3-2403": ("kylin", "v10-sp3-2403"),
    }

    if tag in static_map:
        return static_map[tag]

    if tag.startswith("openeuler-openeuler-"):
        return ("openeuler", tag[len("openeuler-openeuler-"):])
    if tag.startswith("openanolis-anolisos-"):
        return ("anolis", tag[len("openanolis-anolisos-"):])
    if tag.startswith("ubuntu-"):
        return ("ubuntu", tag[len("ubuntu-"):])

    return ("", "")


def format_records_for_dingtalk(records: list[dict[str, str]]) -> list[list[str]]:
    """将记录格式化为钉钉表格所需的二维数组格式."""
    result = []
    for r in records:
        result.append([
            r["软件名称"],
            r["版本"],
            r["操作系统"],
            r["系统版本"],
            r["下载路径"],
            r["安装依赖清单"],
        ])
    return result


def get_next_row(spreadsheet_get_range_func, node_id: str, sheet_id: str) -> int:
    """获取表格下一空行的行号.

    Args:
        spreadsheet_get_range_func: 钉钉表格获取范围的函数
        node_id: 表格节点 ID
        sheet_id: 工作表 ID

    Returns:
        下一空行的行号 (1-based)
    """
    result = spreadsheet_get_range_func(
        node_id=node_id,
        sheet_id=sheet_id,
        range="A:A",
    )
    values = result.get("values", [])
    last_row = 0
    for i, row in enumerate(values):
        if row and row[0]:
            last_row = i + 1
    return last_row + 1
