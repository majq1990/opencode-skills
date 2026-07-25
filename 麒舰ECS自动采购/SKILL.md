---
name: ecs-auto-procurement
description: 麒舰考核 ECS 自动采购，通过钉钉 AI 表格触发 Webhook 自动采购阿里云实例并推送待办通知。
version: 1.0.1
---

# 麒舰考核 ECS 自动采购 Skill

## 概述

自动化采购阿里云 ECS 实例用于麒舰考核实操练习。通过钉钉 AI 表格收集考核信息，Webhook 触发自动采购，完成后推送钉钉待办通知。

## 架构

```
用户填写钉钉AI表格 → 自动化规则（到达时间触发）→ Webhook → 服务器 Flask 服务 → 采购脚本 → 写回表格 → 推送待办
```

## 服务器信息

| 项目 | 值 |
|------|-----|
| 服务器 | demo.egova.com.cn（CentOS 7，root 免密） |
| 部署路径 | /egova/ecs-auto-procurement/ |
| Webhook 端口 | 8899（仅本地，外部不可直达） |
| Webhook 服务 | ecs-webhook (systemd) |
| Webhook Token | ecs-procurement-2026 |
| 公开 Webhook URL | https://demo.egova.com.cn/webhooks/ecs-procurement |
| nginx 边缘 token 预检 | X-Webhook-Token 头缺失/错误 → 401 |
| nginx location 文件 | /etc/nginx/conf.d/ecs-webhook.location |

## 脚本清单

| 脚本 | 功能 |
|------|------|
| 01-provision-ecs.sh | 阿里云 ECS 采购（aliyun-cli） |
| 02-poll-and-sync.sh | AI表格轮询 + 写回结果 |
| 03-notify-todo.sh | 钉钉待办通知推送 |
| main.sh | 主调度入口 |
| webhook_server.py | Flask Webhook 接收服务 |
| config.json | 配置文件（AccessKey、ECS参数、表格ID） |

## 麒舰考核 ECS 参数

| 参数 | 值 |
|------|-----|
| 区域 | cn-beijing (华北2北京) |
| 可用区 | cn-beijing-h |
| 实例规格 | ecs.e-c1m4.2xlarge (8U32G) |
| 付费模式 | 抢占式实例 (SpotAsPriceGo) |
| 数量 | 2台 |
| 系统盘 | 80G cloud_essd |
| 网络 | 分配公网IP，按流量计费 100Mbps |
| 安全组 | sg-2ze1pookadxppb0kx9q2, sg-2zegckithes232ebtmzq |
| 密码 | Egova@123 |
| 实例名称 | qijian_年月日_三位顺序号（每天从001递增） |
| 释放时间 | 实际采购日（脚本执行当天）+1天 23:59（北京时间，不基于计划开始时间） |

## AI 表格配置

| 项目 | 值 |
|------|-----|
| Base ID | Gl6Pm2Db8D3moL97iGK7pjedJxLq0Ee4 |
| Table ID | zWJ8RQh |
| 表名 | 考核信息收集表 |

### 字段映射

| 字段名 | Field ID | 类型 |
|--------|----------|------|
| 标题 | 6v0t5v6 | text |
| 人员 | 4Qd3hNV | user |
| 所在部门 | UkbXluS | department |
| 本次考核内容 | U8asEVV | singleSelect（麒舰/性能安全） |
| 计划开始实操练习时间 | YEt9c1v | date |
| ECS实例ID1 | IVMqkfB | text |
| ECS实例ID2 | SK4QF3I | text |
| ECS实例名称1 | ue8uXBM | text |
| ECS实例名称2 | fJdMn5o | text |
| 公网IP1 | trHIjwJ | text |
| 公网IP2 | mxgbFFv | text |
| 采购状态 | gnFTXtU | singleSelect（待采购/采购中/已完成） |
| 采购时间 | KmXzh0u | text |
| 释放时间 | TLMeAra | text |
| 待办任务ID | HW58TJp | text |

## 钉钉AI表格自动化规则配置

1. 打开表格 → 顶部「自动化」→ 「从空白创建」
2. **触发条件**：到达记录中的时间时 → 选择「计划开始实操练习时间」
3. **执行动作**：发送HTTP请求
   - 请求方法：POST
   - 请求URL：https://demo.egova.com.cn/webhooks/ecs-procurement
   - 请求头：X-Webhook-Token: ecs-procurement-2026
   - 请求体（JSON）：
   ```json
   {"recordId": "{{记录ID}}", "plannedStart": "{{计划开始实操练习时间}}"}
   ```
   > **注意**：plannedStart 仅用于日志记录，释放时间基于脚本执行当天（实际采购日）+1天
4. 保存并发布

## 常用运维命令

```bash
# 查看服务状态
systemctl status ecs-webhook

# 重启服务
systemctl restart ecs-webhook

# 查看日志
tail -f /egova/ecs-auto-procurement/logs/$(date +%Y-%m-%d).log

# 手动执行采购
bash /egova/ecs-auto-procurement/01-provision-ecs.sh 2026-04-10 2

# 手动执行完整流程
bash /egova/ecs-auto-procurement/main.sh

# 手动触发单条记录
bash /egova/ecs-auto-procurement/02-poll-and-sync.sh <recordId>

# 手动补发待办通知
bash /egova/ecs-auto-procurement/03-notify-todo.sh <recordId> <startDate> <ip1> <ip2>

# 查询实例IP
aliyun ecs DescribeInstances --RegionId cn-beijing --InstanceIds '["i-xxx","i-yyy"]'

# 手动分配公网IP（如果实例没有公网IP）
aliyun ecs AllocatePublicIpAddress --InstanceId i-xxx

# 设置自动释放时间
aliyun ecs ModifyInstanceAutoReleaseTime --RegionId cn-beijing --InstanceId i-xxx --AutoReleaseTime "2026-04-10T15:59:00Z"
```

## 依赖

| 组件 | 版本 | 说明 |
|------|------|------|
| aliyun-cli | 3.3.4 | 阿里云命令行工具 |
| dws CLI | v1.0.7 | 钉钉工作台CLI |
| Python3 | 3.6.8 | Webhook服务（CentOS 7 默认，避开 3.7+ 特性） |
| Flask | - | Web框架 |
| jq | - | JSON处理 |

## 认证配置

- aliyun-cli: ~/.aliyun/config.json（AK模式）
- dws: OAuth设备流认证（~/.dws/）

## 注意事项

1. 实例创建后可能没有公网IP，需要手动调用 AllocatePublicIpAddress
2. 释放时间对用户显示北京时间（+08:00）；调用 `ModifyInstanceAutoReleaseTime` 必须传 UTC `Z` 格式，例如北京时间 23:59 对应 `15:59:00Z`
3. 实例名称格式：qijian_YYYYMMDD_NNN，每天从001递增
4. 待办通知不支持 --description 参数，信息需放在 --title 中
5. Webhook 服务使用 Flask 开发服务器，生产环境建议用 gunicorn
6. **Python 3.6.8 兼容**：`subprocess.run` 不能用 `capture_output` / `text=True`，用 `stdout=PIPE, stderr=PIPE, universal_newlines=True`
7. **jq 语法**：`.cells["key"]` 正确，`.cells.["key"]` 错误（多余点号会导致待办推送静默失败）
8. **nginx 边缘 token 预检**：错误/缺失 `X-Webhook-Token` 直接 401，不打到后端
9. **释放时间基于实际采购日**：脚本执行当天 +1 天，不基于计划开始时间（故障延迟采购时以实际执行日为准）
10. **修改释放时间**：`aliyun ecs ModifyInstanceAutoReleaseTime --RegionId cn-beijing --InstanceId i-xxx --AutoReleaseTime "2026-06-02T15:59:00Z"`
