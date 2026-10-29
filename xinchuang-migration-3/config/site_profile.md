# 多现场参数差异表（site_profile）

> v2.0 新增。同一套六阶段流程在不同现场执行时，下列参数存在档位差异。
> **纪律**：本文档所有 IP/密码均为占位符；现场真实值只写进现场交付物，禁止回写本 skill（SKILL.md 停止条件 3）。

## 占位符约定

| 占位符 | 含义 | 使用位置 |
|---|---|---|
| `{{ONEOPS_IP}}` | oneops.egova.com.cn 解析地址（政务网写 /etc/hosts 用） | SKILL.md 阶段一、migration_steps.md |
| `{{DM_PWD_EXAMPLE}}` | 示例密码占位（SYSDBA/应用用户） | SKILL.md、migration_steps.md |

## 已知现场档位（来自 quiz266 提交物沉淀，2026-10-02）

| 参数项 | 现场A（辽宁，2025-12 档） | 现场B（辽宁，2025-11 档） | 说明 |
|---|---|---|---|
| DM8 ISO 版本 | 20251202 版 | 20251114 版 | 达梦安装镜像月份档 |
| AAS 版本 | SP11-20251205 | SP10-20251128 | 金蝶 Apusic 安装包档 |
| 达梦表空间 | 12288M | 10240M | dminit/建表空间 SIZE |
| ES 版本 | 7.17.8 | 7.17.5 | 基础设施小版本 |
| 备份保留份数 | 15 份 / 03:00 调度 | 12 份 / 02:00 调度 | backup_*.sh 的 KEEP_COUNT 与 crontab |
| dinstall 组 gid | 2002 | 2001 | dmdba 用户组 |
| oneops IP | `{{ONEOPS_IP}}` | `{{ONEOPS_IP}}` | 各现场不同 |
| 示例密码 | `{{DM_PWD_EXAMPLE}}` | `{{DM_PWD_EXAMPLE}}` | 各现场不同 |

> 两档均出自辽宁区域现场实测；新现场按此表格式追加"现场C"列，并在 P3 演练后补充演练机档位。

## 新现场初始化清单（执行迁移前逐项确认）

1. DM8 ISO 版本与 OS/CPU 架构匹配（x86_64/aarch64）
2. 金蝶 AAS 安装包 + **license.xml 就绪**（skill 不生成不修改 license）
3. 表空间规划（默认参照 ≥10240M 档，按数据量上浮）
4. ES/Kafka/Redis/Nacos 等基础设施版本与产品基准库匹配
5. `scripts/backup_*.sh` 的 KEEP_COUNT 与 crontab 按现场要求调整
6. dmdba 组 gid 与现场既有用户不冲突
7. oneops 可达性：`ping oneops.egova.com.cn`，不通则写 /etc/hosts（用 `{{ONEOPS_IP}}` 对应现场真实值）
