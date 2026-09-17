# 部署指南（demo.egova.com.cn）

## 部署路径

```
/egova/ecs-asset-ledger/
├── config.json
├── logs/
│   ├── skill.log            # 脚本统一日志
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

## 部署命令

```bash
ssh root@demo.egova.com.cn

# 建目录
mkdir -p /egova/ecs-asset-ledger/{logs,scripts/lib}

# 上传本地 skill 的 scripts/
# （本地 PowerShell）
scp -r D:/opencode/config/skills/ecs-asset-ledger/scripts/* \
  root@demo.egova.com.cn:/egova/ecs-asset-ledger/scripts/

# 上传 config.json（手动编辑后上传）
scp D:/opencode/config/skills/ecs-asset-ledger/config.example.json \
  root@demo.egova.com.cn:/egova/ecs-asset-ledger/config.json

# 编辑 config.json
ssh root@demo.egova.com.cn
vi /egova/ecs-asset-ledger/config.json
```

## cron 配置

```cron
# 工作日（周一至周五）早上 09:00 跑扫描 + 推送
0 9 * * 1-5 bash /egova/ecs-asset-ledger/scripts/main.sh >> /egova/ecs-asset-ledger/logs/cron.log 2>&1
```

> `* * 1-5` 表示周一到周五；周末不推。

## 钉钉群机器人

1. 在指定群（运维/资产群）加自定义机器人
2. 安全设置：勾「自定义关键词」→ 填 `egova`
3. 拿到 webhook URL（`https://oapi.dingtalk.com/robot/send?access_token=...`）
4. 写入 `config.json` 的 `WEBHOOK_URL`
5. 推送测试：

```bash
curl -X POST "https://oapi.dingtalk.com/robot/send?access_token=xxx" \
  -H "Content-Type: application/json" \
  -d '{"msgtype":"markdown","markdown":{"title":"egova 测试","text":"egova 这是一条测试推送"}}'
```

## 依赖检查

```bash
# aliyun-cli
aliyun configure list
aliyun ecs DescribeRegions --output cols=RegionId rows=Regions.Region[] | head

# 各产品 API 可用性
aliyun vpc DescribeRegions --output cols=RegionId rows=Regions.Region[] | head
aliyun rds DescribeRegions --output cols=RegionId rows=Regions.RDSRegion[]
aliyun r-kvstore DescribeRegions --output cols=RegionId rows=RegionIds.KVStoreRegion[]
aliyun slb DescribeRegions --output cols=RegionId rows=Regions.Region[]
# OSS 用 ossutil64
which ossutil64 || echo "ossutil64 未装，将用 aliyun oss 降级"
```

## 日志轮转

```bash
cat > /etc/logrotate.d/ecs-asset-ledger << 'EOF'
/egova/ecs-asset-ledger/logs/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

## 故障排查

| 现象 | 排查 |
|---|---|
| cron 没跑 | `systemctl status crond` / `ls /var/spool/cron/root` |
| aliyun 报 InvalidInstanceId.NotFound | 缺 `--RegionId`，参考 `memory-feedback-aliyun-cli-quirks.md` |
| 推送无消息 | 群机器人 webhook 是否被禁用 / 关键词 `egova` 是否出现在消息里 |
| OSS 扫不到 | 装 `ossutil64`（`pip install oss2` 或下载二进制） |
| EIP 扫不到 | 检查 RAM 子账号是否有 `vpc:DescribeEipAddresses` 权限 |
| 02b 卡住 | 单个 region API 超时 → 加 `set -o pipefail` + 超时阈值；逐 region 重试 |

## 升级

```bash
scp D:/opencode/config/skills/ecs-asset-ledger/scripts/0?-*.sh \
  root@demo.egova.com.cn:/egova/ecs-asset-ledger/scripts/

scp D:/opencode/config/skills/ecs-asset-ledger/scripts/main.sh \
  root@demo.egova.com.cn:/egova/ecs-asset-ledger/scripts/

scp D:/opencode/config/skills/ecs-asset-ledger/scripts/lib/common.sh \
  root@demo.egova.com.cn:/egova/ecs-asset-ledger/scripts/lib/common.sh
```