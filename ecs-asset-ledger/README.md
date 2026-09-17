# ECS 资产台账

阿里云后付费资源日扫描 + 钉钉群推送。每个工作日早上自动扫 ECS 实例释放状态、EIP 未绑定、独立云盘、RDS/Redis/SLB/NAT/OSS Bucket 等后付费资源，推送钉钉群（关键词 egova）。

## 快速上手

### 1. 部署到 demo.egova.com.cn

```bash
# 本地 PowerShell
ssh root@demo.egova.com.cn "mkdir -p /egova/ecs-asset-ledger/{logs,scripts/lib}"

scp -r D:/opencode/config/skills/ecs-asset-ledger/scripts/* \
  root@demo.egova.com.cn:/egova/ecs-asset-ledger/scripts/

scp D:/opencode/config/skills/ecs-asset-ledger/config.example.json \
  root@demo.egova.com.cn:/egova/ecs-asset-ledger/config.json
```

### 2. 编辑 config.json

填入：
- `WEBHOOK_URL`：钉钉群机器人 webhook（关键词必须填 `egova`）
- `REGIONS`：要扫描的 region 列表

### 3. 配置 cron

```cron
0 9 * * 1-5 bash /egova/ecs-asset-ledger/scripts/main.sh >> /egova/ecs-asset-ledger/logs/cron.log 2>&1
```

### 4. 手动跑一次验证

```bash
ssh root@demo.egova.com.cn
bash /egova/ecs-asset-ledger/scripts/main.sh
```

应能在钉钉群收到一条「egova 阿里云后付费资源日报」。

## 触发词

- ECS 台账 / 资产台账 / 服务器释放核对
- 释放告警 / 在用服务器清单 / 后付费资源
- ECS 资产 / 到店核对释放
- /ecs-asset-ledger