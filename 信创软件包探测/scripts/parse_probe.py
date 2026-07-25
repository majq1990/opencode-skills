#!/usr/bin/env python3
"""解析 probe_versions.sh 多节点输出 → 结构化 dict

输入 (stdin 或文件): 多节点 KEY=VALUE 块, 节点头 `########## NODE <ip> ##########`
输出 (stdout JSON): {
  "os_field": "lZl6Era",  # 匹配 aitable_meta.os_to_field 的 fieldId; 未匹配则 None
  "os_key": "kylin-V10-x86_64",
  "nodes": {
    "<ip>": {...node1 解析后的 KEY=VALUE...},
    ...
  },
  "merged": {KEY: value, ...},  # 跨节点合并: 取首个非空值, 软件名 → 版本
  "software_versions": {  # 软件名 (matrix 表行) → 版本字符串
    "Tomcat": "9.0.105 (apache-tomcat-9.0.105-GIS)",
    "MySQL Server": "8.0.34-1.el8",
    ...
  }
}
"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

META_PATH = Path(__file__).parent.parent / "config" / "aitable_meta.json"


def load_meta() -> dict:
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def split_nodes(raw: str) -> dict[str, dict[str, str]]:
    """raw → {ip: {KEY: VALUE}}"""
    blocks = re.split(r"^#+\s*NODE\s+(\S+)\s*#+\s*$", raw, flags=re.MULTILINE)
    # blocks: ['前置噪音', ip1, 内容1, ip2, 内容2, ...]
    out = {}
    if len(blocks) < 3:
        return out
    for i in range(1, len(blocks), 2):
        ip = blocks[i].strip()
        body = blocks[i + 1] if i + 1 < len(blocks) else ""
        kvs = {}
        for line in body.splitlines():
            line = line.rstrip()
            if "=" not in line or line.startswith("#") or line.startswith("Authorized"):
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip()
            # 跳过 bash 报错行
            if k.startswith("bash:") or "command not found" in v:
                continue
            if k and v:
                kvs[k] = v
        out[ip] = kvs
    return out


def detect_os_key(merged: dict[str, str]) -> tuple[str, str | None]:
    """根据 merged 中 OS_ID/OS_VER/ARCH 推 OS key + matrix fieldId."""
    meta = load_meta()
    os_id = merged.get("OS_ID", "").strip()
    os_ver = merged.get("OS_VER", "").strip()
    arch = merged.get("ARCH", "").strip() or "x86_64"

    # 多种 OS_ID 标准化
    norm = os_id.lower()
    candidates = []
    if norm.startswith("kylin"):
        candidates.append(f"kylin-{os_ver}-{arch}")
    elif norm.startswith("openeuler"):
        candidates.append(f"openEuler-{os_ver}-{arch}")
    elif norm.startswith("anolis"):
        # anolis 7.x / 8.x: 取主版本号
        major = os_ver.split(".")[0] if os_ver else ""
        candidates.append(f"anolis-{major}-{arch}")
        candidates.append(f"anolis-{os_ver}-{arch}")
    elif norm.startswith("centos"):
        major = os_ver.split(".")[0] if os_ver else ""
        candidates.append(f"centos-{major}-{arch}")
    elif norm.startswith("ubuntu"):
        candidates.append(f"ubuntu-{os_ver}-{arch}")
    elif norm.startswith("uos") or "uniontech" in norm:
        # UOS 区分 1060a/1060e 等需用户提示, 这里取通用 20-1060a 占位
        candidates.append(f"uos-{os_ver}-1060a-{arch}")
        candidates.append(f"uos-{os_ver}-{arch}")

    o2f = meta["os_to_field"]
    for k in candidates:
        if k in o2f:
            return k, o2f[k]
    return f"{os_id}-{os_ver}-{arch}", None


def merge_nodes(nodes: dict[str, dict]) -> dict:
    """跨节点合并: 同 KEY 取首个非空 (节点 IP 字典序保证稳定)."""
    merged: dict[str, str] = {}
    for ip in sorted(nodes.keys()):
        for k, v in nodes[ip].items():
            if k not in merged or not merged[k]:
                merged[k] = v
    return merged


def map_to_software_versions(merged: dict[str, str]) -> dict[str, str]:
    """probe KEY → matrix 软件名 → version. 后到的不覆盖已有值(probe_key_to_software 顺序优先级)."""
    meta = load_meta()
    k2s: dict[str, str] = meta["probe_key_to_software"]
    sw_ver: dict[str, str] = {}
    for probe_key, sw_name in k2s.items():
        if probe_key.startswith("_"):
            continue
        v = merged.get(probe_key)
        if v and sw_name not in sw_ver:
            sw_ver[sw_name] = v
    return sw_ver


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raw = sys.stdin.read() if len(sys.argv) < 2 else Path(sys.argv[1]).read_text(encoding="utf-8")
    nodes = split_nodes(raw)
    merged = merge_nodes(nodes)
    os_key, os_field = detect_os_key(merged)
    sw_ver = map_to_software_versions(merged)
    out = {
        "os_key": os_key,
        "os_field": os_field,
        "nodes": nodes,
        "merged": merged,
        "software_versions": sw_ver,
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
