#!/usr/bin/env python3
"""信创节点第三方软件版本风险评估规则

每条规则: predicate(version_str) → (level, description, suggested_action, cve_hint)
level ∈ {"高","中","低","信息"}

返回所有命中规则;同一软件可命中多条。
"""
from __future__ import annotations
import re
from typing import Callable, Iterable

# (software_key, predicate, level, description, action, cve_hint)
RULES: list[tuple[str, Callable[[str], bool], str, str, str, str]] = [
    # MySQL Server/Client
    ("MySQL Server", lambda v: bool(re.search(r"8\.0\.(?:[0-9]|[1-3][0-9]|4[01])(?:\D|$)", v)),
     "高", "MySQL 8.0.x 早于 8.0.42, 期间 InnoDB/Server 累积多个 CVE 修复",
     "升级到 ≥8.0.42 (8.0 LTS 末) 或迁 8.4 LTS", ""),
    ("MySQL Client", lambda v: bool(re.search(r"8\.0\.(?:[0-9]|[1-3][0-9]|4[01])(?:\D|$)", v)),
     "高", "MySQL Client 8.0.x 早于 8.0.42, 与 Server 同步老化", "随 server 一起升级", ""),
    # Python 3.7 EOL
    ("Python3 pip/wheel", lambda v: "3.7" in v,
     "高", "Python 3.7 EOL 2023-06-27, 无新增安全补丁", "梳理依赖, 升级到 3.10+ 或剥离用法", ""),
    # TDengine 2 EOL
    ("TDengine 2", lambda v: v.strip().startswith("2.") or "2.6.0" in v,
     "高", "TDengine 2.x 线已 EOL/受限支持; 历史 CVE 不再回补",
     "业务侧明确 TD2→TD3 数据迁移时间表, 逐步下线 2.x", ""),
    # MinIO 旧版本
    ("MinIO", lambda v: bool(re.search(r"RELEASE\.(202[0-4])-", v)),
     "高", "MinIO release 超 1 年未升级, 期间累积多次安全发布 (含 IAM/Bucket 越权)",
     "升级到最新 stable RELEASE, 回归测试", ""),
    # NTP 老版本
    ("NTP客户端", lambda v: "ntp-4.2.8p1" in v or ("ntp" in v.lower() and "chrony" in v.lower()),
     "高", "ntpd 4.x 历史 CVE 高发 (DoS/信息泄露/配置注入); 与 chrony 并存冗余",
     "统一时间同步到 chrony, 卸载/禁用 ntpd; 或升到最新 4.2.8p18+", ""),
    # Kafka 3.6.0
    ("Kafka", lambda v: "3.6.0" in v,
     "中", "Kafka 3.6.0 后多次 CVE 披露 (CVE-2024-31141 等)",
     "升级到 3.7.x 或 3.6.x 最新补丁版本", "CVE-2024-31141"),
    # mydumper 旧版
    ("mydumper", lambda v: bool(re.search(r"0\.1[0-4]\.", v)),
     "中", "mydumper 0.10-0.14 较老, 0.16+ 有性能/稳定性/数据一致性修复",
     "升级到最新 stable (≥0.16), 实测全量+增量备份回归", ""),
    # PG 13 EOL 2025-11
    ("PostgreSQL 13", lambda v: "13" in v,
     "中", "PostgreSQL 13 EOL 2025-11-13", "规划升级到 PG 15/16 LTS", ""),
    ("PostgreSQL+PostGIS", lambda v: "_13" in v or "postgis35_13" in v,
     "中", "PostgreSQL 13 (Docker 化) EOL 2025-11-13", "规划升 PG 15/16 + PostGIS 兼容评估", ""),
    # XtraBackup vs Server 版本
    ("Percona XtraBackup", lambda v: "8.0.35" in v,
     "中", "XtraBackup 8.0.35 与 MySQL Server 跨小版本时需校验 (Server 若 < 8.0.35 可能失败)",
     "对齐到 server 同版本, 或现场实测 backup→restore", ""),
    # Spring-Boot 内嵌 (Nacos)
    ("Nacos", lambda v: "2.7." in v.lower() or "spring-boot 2.7" in v.lower(),
     "信息", "Nacos 内嵌 Spring-Boot 2.7.x, 该框架社区 EOL 2023-11 (商业版仍维护)",
     "关注 Nacos 上游 Spring-Boot 升级动态, 必要时主动追新 Nacos 版本", ""),
    # OpenIM 2.x EOL
    ("OpenIM Server", lambda v: v.strip().startswith("2.") or "open_im_" in v.lower() or "legacy" in v.lower(),
     "高", "OpenIM 2.x 分支自 2023 起停止维护(3.x 大重写, 命名 open_im_* → openim-*); 2.x 历史安全公告未回补",
     "评估迁移到 OpenIM 3.x; 短期至少 ingress 白名单限制 IM 端口暴露面", ""),
    # MongoDB EOL versions (锚定开头, 防"7.0.5" 误匹配中间的 0.5)
    ("MongoDB", lambda v: bool(re.match(r"^\s*(?:[0-3]\.\d|4\.[0-3](?:\D|$))", v.lstrip())),
     "高", "MongoDB <4.4 已 EOL(4.0 EOL 2022-04); 不再接收安全补丁",
     "升级到 MongoDB 6.0/7.0 LTS; OpenIM 2.x 升级时同步迁移", ""),
    # etcd 老镜像
    ("etcd", lambda v: "2018" in v or "2019" in v or "2020" in v or "latest" in v.lower(),
     "高", "etcd 镜像过老(build 时间 >2 年) 或使用 latest tag(反模式); 历史 CVE(认证/DoS/泄露) 累积",
     "固定到 quay.io/coreos/etcd:v3.5.x 当前 stable; 重新拉镜像并重启容器", ""),
]


def evaluate(software: str, version: str) -> list[dict]:
    """返回所有命中规则的 finding 字典列表."""
    if not version or version in {"未安装", "未探到", "未安装(麒舰栈)", "未安装(麒舰栈无)"}:
        return []
    out = []
    for sw, pred, level, desc, action, cve in RULES:
        if sw != software:
            continue
        try:
            if pred(version):
                out.append({"level": level, "desc": desc, "action": action, "cve": cve})
        except Exception:
            pass
    return out


# 探测脚本本身的缺陷探针 — 输入 parsed dict 找未抓到但应该有的项
def detect_probe_gaps(parsed: dict, deployed_hints: set[str] | None = None) -> list[dict]:
    """根据 parsed 结果检测 probe 脚本是否漏抓.

    deployed_hints: 调用方可传"已知部署的软件名集合"(从 docker images/进程等推断),
    若该软件名在 parsed 里值为空且 hints 标记应部署, 输出 gap finding.
    """
    gaps = []
    # Tomcat: 若 docker_images 含 tomcat 或 /egova/tomcat 存在但 TOMCAT_1 空
    if not parsed.get("TOMCAT_1") and parsed.get("TOMCAT") == "未安装":
        # 双重确认空, 不视为 gap (确实没部署)
        pass
    # Nacos: 若 NACOS_JAR 有但 NACOS_VERSION 空
    if parsed.get("NACOS_JAR") and not parsed.get("NACOS_VERSION"):
        gaps.append({
            "software": "Nacos",
            "level": "信息",
            "desc": f"probe 找到 jar ({parsed['NACOS_JAR']}) 但版本提取失败",
            "action": "检查 MANIFEST.MF 是否含 Implementation-Version; 或调 runtime API",
            "cve": "",
        })
    return gaps


if __name__ == "__main__":
    # 简单自测
    samples = [
        ("MySQL Server", "8.0.34-1.el8"),
        ("MySQL Server", "8.0.42-1.el8"),
        ("Python3 pip/wheel", "Python 3.7.9"),
        ("Kafka", "kafka_2.12-3.6.0"),
        ("Nacos", "2.5.1 (Spring-Boot 2.7.18 内嵌)"),
    ]
    for sw, v in samples:
        rs = evaluate(sw, v)
        print(f"{sw} / {v} → {len(rs)} 命中: {[r['level'] for r in rs]}")
