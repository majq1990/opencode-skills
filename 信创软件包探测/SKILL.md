---
name: xinchuang-pkg-probe
description: |
  信创节点第三方软件版本探测 + 钉钉 AI 表格回填 + CVE 风险标记。
  与 egova-security-scanner 配套：扫描机 → 目标节点 → 抓 30 项第三方软件实际版本 →
  按 (软件 × OS × CPU) 落矩阵表 → 按 yyyymmdd-OS_VER 批次落问题记录表。
  必由 egova-security-scan 扫描完成后自动链调，也可独立按参数调起。
trigger_keywords:
  - 信创版本探测
  - 包探测
  - 拉包打包矩阵
  - xinchuang-pkg-probe
  - probe versions
  - 软件版本回填
  - 版本矩阵
when_to_use: |
  必须满足: (1) 目标节点为用户自有/已授权资产; (2) 用户能提供扫描机 + 目标节点 IP 列表;
  (3) ssh 密钥链已就绪(本机→扫描机 = mjqegova-ed25519, 扫描机→节点 = qijian_key 或自定义)。
  典型调用场景:
    a) egova-security-scan 扫完后自动链调
    b) qijian-deploy 部署完后手动触发批回填
    c) 已有环境定期版本巡检
when_not_to_use: |
  不要触发: (a) 节点未授权; (b) 仅是基础设施问题/网络问题无关版本探测;
  (c) 跨网/跨账号无 ssh 跳板; (d) 矩阵表与本 skill 配套的 baseId 不可用。
---

# xinchuang-pkg-probe

为信创一键部署(oneinstall_v2)产出的节点跑第三方软件版本探测,落地到固定的钉钉 AI 表格,
让"哪些软件、哪个 OS、哪个版本"成为可被 CVE 匹配的结构化数据。

## 仓库与位置

- skill 根目录: `~/.claude/skills/xinchuang-pkg-probe/`
- 配套数据项目(开发源): `D:\git\xinchuang-pkg-matrix\`
- 钉钉 AI 表格 baseId: `G1DKw2zgV2RXpGMNTPNyZ0XYVB5r9YAn` (`信创第三方软件拉包打包矩阵`)
  - 矩阵表 tableId `doEGaSZ` — 软件 × OS×CPU 列 ,30 行
  - 问题表 tableId `vQAo1g0` — 按批次 `yyyymmdd-OS_VER` 写风险
- 配置: `config/aitable_meta.json`(baseId/tableIds/fieldIds/recordIds 静态映射)

## 调起方式

### 1. egova-security-scan 链式自动触发(主路径)

`egova-security-scan` 的 SKILL.md 已加死规则: 报告生成后必调本 skill 续跑版本探测。
触发链:
```
用户: "扫一下 qijian 三节点漏洞"
  → egova-security-scan 跑 nmap/nuclei/ZAP/hydra 出 report.html
  → 自动调 /xinchuang-pkg-probe 传 scanner+nodes 续跑版本探测
  → 矩阵表对应 OS 列回填, 问题表 yyyymmdd-OS 批次落风险
```

### 2. egova-security-scanner CLI 双保险触发

`egova-scan run <target> --with-probe --probe-scanner <ip> --probe-nodes <ip1,ip2,...>`
Python 流水线在 report 后调用本 skill 的 `scripts/run.sh`, 不依赖 LLM 编排。

### 3. 手动直调

```
/xinchuang-pkg-probe --scanner 101.200.233.112 --nodes 101.200.85.159,101.200.180.202,101.200.151.219
```

或自然语言: "对刚部署的三个 qijian 节点跑版本探测,扫描机 101.200.233.112"

## 输入参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--scanner` | 是 | 扫描机公网 IP, 本机用 `mjqegova-ed25519` 连 |
| `--nodes` | 是 | 目标节点 IP 逗号分隔, 扫描机用 `qijian_key` 连 |
| `--scanner-key` | 否 | 本机→扫描机密钥路径, 默认 `~/.ssh/mjqegova-ed25519` |
| `--node-key` | 否 | 扫描机→节点密钥名(扫描机上路径), 默认 `~/.ssh/qijian_key` |
| `--batch` | 否 | 批次 key, 默认 `$(date +%Y%m%d)-${OS_VER}`(运行时拼) |
| `--dry-run` | 否 | 只跑探测不写表 |

## 核心流程

```
1. 本机 ssh→扫描机, 推 probe_versions.sh 到 /tmp/
2. 扫描机 ssh→各节点, bash -s < probe_versions.sh 抓全量
3. 本机解析输出 (KEY=VALUE) → JSON
4. 自动识别 OS_ID + OS_VER + ARCH → 映射到矩阵表对应 fieldId
   (kylin V10 x86_64 → lZl6Era, openEuler22 x86_64 → K3ReqNl, ...)
5. 调 dws aitable record update 批量回填矩阵列
6. 跑 risk_rules.py 对每个软件版本做风险评估
   (MySQL <8.0.42 → 高; Python 3.7.x EOL → 高; Kafka 3.6.0 → 中 CVE-2024-31141; ...)
7. 调 dws aitable record create 批量插问题表, 批次 key `yyyymmdd-OS_VER`
8. 输出汇总: 矩阵更新数 + 问题数(高/中/低/信息) + AI 表格直达链接
```

## 探测能力(probe_versions.sh v3 覆盖)

JDK 8/11 / Docker + compose / MySQL server+client / Redis / PostgreSQL+PostGIS /
TDengine 2 + 3 / OpenResty(nginx) / **Tomcat (递归找 catalina.jar, 多实例)** /
Kafka / ZooKeeper / **Nacos (MANIFEST + runtime API 双取版本)** / MinIO / Cetus /
Elasticsearch / OnlyOffice / nmap / sysbench / Python2/3 /
关键 rpm/deb: percona-xtrabackup-80, mydumper, apr/apr-util, postgresql13,
logrotate, ntp, chrony, lvm2

## 风险规则(scripts/risk_rules.py 内置, 可扩展)

| 检测条件 | 等级 | 说明 |
|---|---|---|
| MySQL < 8.0.42 | 高 | InnoDB/Server 多 CVE |
| Python 3.7.x | 高 | EOL 2023-06-27 |
| TDengine 2.x | 高 | EOL/受限支持 |
| MinIO < 1 年(release date) | 高 | 安全发布积累 |
| ntp 4.2.8p14 与 chrony 共存 | 高 | 冗余 + ntpd 风险面大 |
| Kafka 3.6.0 | 中 | CVE-2024-31141 |
| mydumper 0.12.x | 中 | 老,0.16+ 修复 |
| PG 13 | 中 | EOL 2025-11 |
| Spring-Boot 内嵌 2.7.x (Nacos) | 信息 | 框架老化 |
| 探测脚本无法抓到已部署组件 | 信息 | probe 脚本待完善 |

## OS×CPU 列映射(config/aitable_meta.json)

| OS_ID-OS_VER-ARCH | matrix fieldId | 备注 |
|---|---|---|
| centos-7-x86_64 | 3nJnNcf | centos7_x86 |
| kylin-V10-x86_64 | lZl6Era | kylinV10_x86 |
| kylin-V10-aarch64 | Om40rJ0 | kylinV10_arm |
| openEuler-22.03-x86_64 | K3ReqNl | openEuler22_x86 |
| openEuler-22.03-aarch64 | MSYzkip | openEuler22_arm |
| anolis-7.x-x86_64 | GEdaeTV | anolis7_x86 |
| anolis-8.x-x86_64 | UXVj2yT | anolis8_x86 |
| anolis-8.x-aarch64 | 1noGkqq | anolis8_arm |
| ubuntu-20.04-x86_64 | xTOUWVk | ubuntu20_x86 |
| uos-20-1060a-x86_64 | ZnV48Dl | uos20a_x86 |
| uos-20-1060a-aarch64 | 2Y1yHj3 | uos20a_arm |
| uos-20-1060e-x86_64 | ii0DlBx | uos20e_x86 |
| uos-20-1060e-aarch64 | AWonIAW | uos20e_arm |

未识别 OS 会写入"备注:OS_ID-OS_VER-ARCH 未映射"的 finding, 不阻塞流程。

## 触发示例

✅ "egova-scan 扫完了, 顺便对 3 节点跑一次版本探测" → 直调本 skill
✅ "qijian-deploy 部署完毕, 帮我探测一下版本到矩阵表" → 直调本 skill
✅ egova-security-scan 自动报告生成后 → 自动链调本 skill (主路径)
❌ "查一下 MySQL 8.0.34 有什么 CVE" → 不触发本 skill, 走 vuln-response/手工查
