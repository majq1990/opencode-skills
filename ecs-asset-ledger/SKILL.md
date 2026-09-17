---
name: ecs-asset-ledger
version: 2.0.0
description: 阿里云后付费资源日扫描 + 钉钉群推送。每个工作日早上扫 ECS 实例释放状态、EIP 未绑定、独立云盘未挂载、RDS/Redis/SLB/NAT 网关/OSS Bucket 等后付费资源，把异常和清单推到指定钉钉群，关键词 egova。避免考核/测试机释放失败、未绑定 EIP、独立云盘等被遗忘的资源持续扣费。触发词：ECS台账 / 资产台账 / 服务器释放核对 / 释放告警 / 后付费资源 / ECS资产 / 到店核对释放 / egova ECS日报。
---

# 阿里云后付费资源日报

## 目的

解决**所有**阿里云后付费资源被遗忘导致持续扣费的问题，覆盖：

1. **ECS 实例**：AutoReleaseTime 已过期 / 即将到期 / 野实例（PostPaid 无 AutoReleaseTime 且运行超 3 天）
2. **EIP**：未绑定实例（Available 状态）的弹性公网 IP（按小时计费，最易遗忘）
3. **独立云盘**：未挂载实例（Available 状态）的云盘（按容量×小时计费）
4. **RDS 实例**：按小时计费
5. **Redis 实例**：按小时计费
6. **SLB 负载均衡**：按小时计费
7. **NAT 网关**：按小时计费
8. **OSS Bucket**：按存储量计费（即使无数据也可能因生命周期规则、版本控制扣费）

每个工作日早上 09:00 由 demo.egova.com.cn cron 自动扫描，推送到指定钉钉群（关键词 `egova`），@ 资产管理员。

## 架构

```
demo.egova.com.cn cron 工作日 09:00
├── 01-scan-release.sh      # 扫 ECS 实例：AutoReleaseTime / 野实例
├── 02-scan-active.sh       # 扫 ECS 实例：Running 清单 + 按用途分类
├── 02b-scan-billable.sh    # 扫 EIP / 独立云盘 / RDS / Redis / SLB / NAT / OSS
└── 03-dingtalk-push.sh     # 聚合推送（关键词 egova）
```

## 部署路径

```
/egova/ecs-asset-ledger/
├── config.json
├── logs/
│   ├── skill.log            # 所有脚本统一日志
│   ├── release-anomalies.json
│   ├── active-summary.json
│   ├── other-billable.json
│   └── cron.log             # cron 输出
└── scripts/
    ├── lib/common.sh
    ├── 01-scan-release.sh
    ├── 02-scan-active.sh
    ├── 02b-scan-billable.sh
    ├── 03-dingtalk-push.sh
    └── main.sh
```

## cron 配置

```cron
# 工作日（周一至周五）早上 09:00 跑扫描 + 推送
0 9 * * 1-5 bash /egova/ecs-asset-ledger/scripts/main.sh >> /egova/ecs-asset-ledger/logs/cron.log 2>&1
```

## 钉钉群机器人配置

- **Webhook**：`https://oapi.dingtalk.com/robot/send?access_token=...`（写入 `config.json` 的 `WEBHOOK_URL`）
- **关键词**：`egova`（推送内容必须含此关键词）
- **@ 资产管理员**：`AT_USERIDS` 数组填钉钉 userId

## 推送格式示例

```markdown
# egova 阿里云后付费资源日报 · 2026-08-18 (Monday)

## ⚠️ ECS 释放异常 (2 条)

| 状态 | 实例ID | 实例名 | 区域 | 付费 | 公网IP | AutoReleaseTime |
|---|---|---|---|---|---|---|
| ⚠️ 已过期未释放 | i-xxx | qijian_20260817_001 | cn-beijing | PostPaid | 1.2.3.4 | 2026-08-18T15:59:00Z |
| ⚠️ 野实例(无AutoRelease且运行5天) | i-yyy | faq-test | cn-hangzhou | PostPaid | - | - |

## 📊 ECS 在用实例（合计 12 台）

**按用途分类**：

| 用途 | 数量 |
|---|---|
| 麒舰考核 | 6 |
| 麒舰部署 | 3 |
| 悟空考核 | 2 |
| 星桥考核 | 1 |

**按区域**：

| 区域 | 数量 |
|---|---|
| cn-beijing | 8 |
| cn-wulanchabu | 4 |

## 💰 其他后付费资源

**EIP**：总 8 个，未绑定 1 个（⚠️ 持续扣费）

| EIP | 区域 | 状态 | 带宽 |
|---|---|---|---|
| eip-xxx | cn-beijing | Available | 5M |

**独立云盘**：总 3 个，未挂载 0 个

**RDS**：2 个实例

| 实例ID | 区域 | 引擎 | 类型 | 计费 |
|---|---|---|---|---|
| rm-xxx | cn-beijing | MySQL | Primary | Postpaid |

**Redis**：5 个实例

**SLB**：2 个实例

**NAT 网关**：1 个

**OSS Bucket**：4 个

@马健权
```

## 依赖

| 工具 | 用途 |
|---|---|
| aliyun-cli | 阿里云 API 调用（ecs / vpc / rds / r-kvstore / slb / oss） |
| ossutil64 | OSS Bucket 列表（可选；aliyun oss 也支持） |
| jq | JSON 解析 |
| curl | 钉钉群机器人推送 |

## 安全规则

1. **禁止编造资源 ID**：所有 ID 来自 aliyun 命令返回
2. **不推送公网 IP 之外的敏感信息**：实例密码/密钥绝不进钉钉
3. **危险操作必确认**：发现「野实例」或「未绑定 EIP」只告警，不自动删；删除需人工走 aliyun-cli 二次确认

## 已知 pitfall

- **aliyun-cli 必须显式传 `--RegionId`**：参考 `memory-feedback-aliyun-cli-quirks.md`
- **OSS Bucket 列表**：必须装 ossutil64，否则会全 region 扫一遍（慢）
- **EIP 未绑定状态**：可能是临时（实例刚释放但 EIP 还在保留期），不要立刻删，先确认

## 关联文档

- `references/deployment.md` - 部署细节
- `阿里云ECS管理/SKILL.md` - ECS 采购动作
- `ecs-auto-procurement-2/SKILL.md` - 麒舰/星桥考核采购