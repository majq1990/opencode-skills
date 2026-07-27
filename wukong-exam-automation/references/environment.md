# 悟空考核环境生命周期

## 关键常量

| 项目 | 默认值 |
|---|---|
| 地域 | `cn-wlcb`（华北6 乌兰察布） |
| 镜像 | `m-0jlafwqq03tbtoerkiep`（悟空实操环境-2025年5月15日） |
| 规格 | `ecs.g6.2xlarge`（8U32G） |
| 付费 | 包年包月 1 周，`PrePaid Period=1 PeriodUnit=Week` |
| 带宽 | 按流量，峰值 100Mbps |
| 系统盘 | 默认 100G `cloud_essd`，人数较多时扩容 |
| 数据库 root 密码 | 使用现有环境约定，不在最终答复明文展示 |
| mydumper rpm | `https://demo.egova.com.cn/MediaRoot/rpm/openeuler/22.03-lts-sp4/x86_64/mydumper-0.16.1-3.el8.x86_64.rpm` |

安全组和交换机必须实时查询：

```powershell
aliyun ecs DescribeSecurityGroups --RegionId cn-wlcb --output json
aliyun ecs DescribeVSwitches --RegionId cn-wlcb --output json
```

## 考前流程

1. 检查 `aliyun configure list`、SSH、配额。
2. 展示采购摘要：地域、镜像、规格、系统盘、带宽、购买 1 周、实例数、命名规则。
3. 调用 `RunInstances`，必须显式传 `--RegionId cn-wlcb`。
4. 轮询实例到 `Running`，记录实例 ID 和公网 IP。
5. SSH 验证：`ssh root@<ip> 'uname -a'`。
6. 清理非 admin 的页面、项目、用户脏数据。
7. 生成数据库标识，让用户申请 license；拿到 license 后写入 `wukong.com_license` 和 `data_exchange.com_license`。
8. 重启 `dex`、`wukong`、`wuneng`，按顺序启动视频服务，最后重启 `videocenter`。
9. 轮询 `http://127.0.0.1:8080/wukong-api/free/license/info` 验证授权。
10. 安装或校验 mydumper。

## 考后流程

考核结束后 30 分钟执行：

1. 重置所有非 admin 考生密码为约定默认密码。
2. 查询无页面且无项目账号，作为无需实操评分名单。
3. 保存查询结果，给阅卷表的 `未作答（0分）` sheet 和总表实操分数使用。

## 已知坑

- cn-wlcb 与 cn-beijing 的安全组、交换机不通用；不要复用北京 `sg-2ze*`。
- aliyun-cli 某些 ECS API 必须显式传 `--RegionId`，尤其 `StartInstance`、`AllocatePublicIpAddress`、`ModifyInstanceAutoReleaseTime`。
- 镜像禁用密码登录，优先 SSH 免密；免密失败先查密钥，不要硬试密码。
- license 未写入前不要重启业务。
- 视频中心脚本有顺序要求，按 server、mediaserverinfo、mediaserver、videocenter 的顺序处理。
