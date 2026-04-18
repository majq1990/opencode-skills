---
name: aliyun-ecs
version: 1.0.0
description: 阿里云 ECS 服务器采购与管理工作流。基于 aliyun-cli 实现完整的 ECS 实例生命周期管理，包括：创建实例、启动实例、状态轮询、公网 IP 分配、实例查询等。支持参数化配置、按量付费、完整采购流程自动化。当用户提及阿里云服务器采购、ECS实例创建、云服务器购买、实例启动、阿里云资源管理等需求时自动触发。
author: majianquan
category: cloud-infra
visibility: cloud-infra
---

# 阿里云 ECS 服务器采购 Skill

**官方仓库**: https://github.com/aliyun/aliyun-cli
**Stars**: 936 | **License**: Apache-2.0 | **语言**: Go

## 概述

基于 `aliyun-cli` 构建的阿里云 ECS 服务器采购与管理工作流。提供从实例创建、启动到状态确认的完整自动化流程，专为 AI Agent 和运维自动化设计。

**核心特性**：
- **完整采购流程**：创建实例 → 等待就绪 → 启动实例 → 轮询运行状态 → 返回公网 IP
- **参数化配置**：地域、规格、镜像、网络等全部可配置
- **按量付费**：默认 PostPaid 模式，支持灵活计费
- **状态轮询**：内置 `--waiter` 机制，自动等待实例就绪
- **安全规则**：危险操作确认、禁止编造 ID、严格参数校验

---

## 前置条件

### 1. 安装 aliyun-cli

**Windows (PowerShell)**：
```powershell
# 下载并解压 Windows 版本
$downloadUrl = "https://aliyuncli.alicdn.com/aliyun-cli-windows-latest-amd64.zip"
$tempDir = "$env:TEMP\aliyun-cli"
New-Item -ItemType Directory -Force -Path $tempDir
Invoke-WebRequest -Uri $downloadUrl -OutFile "$tempDir\aliyun-cli.zip"
Expand-Archive -Path "$tempDir\aliyun-cli.zip" -DestinationPath $tempDir -Force
# 添加到 PATH（或移动到系统目录）
Move-Item -Path "$tempDir\aliyun.exe" -Destination "C:\Windows\System32\aliyun.exe" -Force
```

**macOS / Linux**：
```bash
# 使用 brew（推荐）
brew install aliyun-cli

# 或使用一键安装脚本
/bin/bash -c "$(curl -fsSL https://aliyuncli.alicdn.com/install.sh)"
```

### 2. 配置认证凭证

```bash
aliyun configure --mode AK
```

需要配置以下信息：
- **AccessKey ID**：阿里云 AccessKey ID
- **AccessKey Secret**：阿里云 AccessKey Secret
- **Default Region Id**：默认地域（如 cn-hangzhou）
- **Output Format**：json
- **Language**：zh

**环境变量方式（CI/CD）**：
```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-access-key-id>
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-access-key-secret>
export ALIBABA_CLOUD_REGION_ID=cn-hangzhou
```

### 3. 验证配置

```bash
aliyun ecs DescribeRegions --output cols=RegionId,LocalName rows=Regions.Region[]
```

---

## 安全规则

### 严格禁止（NEVER DO）

1. **禁止使用 aliyun-cli 以外的方式调用阿里云 API**
   - 禁止 `curl`、HTTP API 直接调用、SDK 直接调用
   - 所有操作必须通过 `aliyun ecs` CLI

2. **禁止编造标识符**
   - 不允许猜测或虚构 InstanceId、ImageId、SecurityGroupId、VSwitchId 等
   - 所有 ID 必须从 `aliyun` 命令返回或用户明确提供中提取

3. **禁止跳过参数校验**
   - 创建实例前必须先确认必需参数已提供
   - 禁止使用 `--force` 参数绕过校验（除非用户明确要求）

4. **禁止忽略实例状态**
   - 创建实例后必须等待状态变为 `Stopped` 才能启动
   - 启动实例后必须等待状态变为 `Running` 才算完成

### 严格要求（MUST DO）

1. **所有命令必须加 `--output json`**
   - AI Agent 默认需要结构化输出
   - 示例：`aliyun ecs DescribeInstances --RegionId cn-hangzhou --output json`

2. **危险操作必须向用户确认**
   - 展示操作摘要（操作类型 + 目标对象 + 影响范围）
   - 用户明确回复确认（如 "确认"/"好的"）
   - 确认后才执行

3. **使用 --waiter 等待状态转换**
   - 创建实例后：等待状态变为 `Stopped`
   - 启动实例后：等待状态变为 `Running`

4. **错误处理**
   - 捕获并解析返回的 JSON 错误信息
   - 提供清晰的错误原因和解决建议

---

## 危险操作清单

以下操作需要用户确认后才可执行：

| 命令 | 说明 |
|------|------|
| `aliyun ecs CreateInstance` | 创建新的 ECS 实例（产生费用） |
| `aliyun ecs DeleteInstance` | 删除 ECS 实例（数据丢失） |
| `aliyun ecs StopInstance` | 停止运行中的实例（服务中断） |
| `aliyun ecs RebootInstance` | 重启实例（服务中断） |
| `aliyun ecs ReleaseInstance` | 释放按量付费实例（数据丢失） |

**确认流程**：
```
Step 1 → 展示操作摘要（操作类型 + 目标对象 + 影响范围 + 费用影响）
Step 2 → 用户明确回复确认（如 "确认" / "好的"）
Step 3 → 执行命令
```

---

## 核心 API 命令速查

### 查询类（只读，无需确认）

```bash
# 查询可用地域列表
aliyun ecs DescribeRegions --output cols=RegionId,LocalName rows=Regions.Region[]

# 查询可用区列表
aliyun ecs DescribeZones --RegionId cn-hangzhou --output cols=ZoneId,LocalName rows=Zones.Zone[]

# 查询实例规格列表
aliyun ecs DescribeInstanceTypes --RegionId cn-hangzhou --MaxResults 20

# 查询可用资源（库存检查）
aliyun ecs DescribeAvailableResource --RegionId cn-hangzhou --ZoneId cn-hangzhou-h \
  --DestinationResource InstanceType --InstanceType ecs.g6.large

# 查询镜像列表
aliyun ecs DescribeImages --RegionId cn-hangzhou --ImageOwnerAlias system --MaxResults 10 \
  --output cols=ImageId,OSName,Size rows=Images.Image[]

# 查询安全组列表
aliyun ecs DescribeSecurityGroups --RegionId cn-hangzhou --VpcId <vpc-id> \
  --output cols=SecurityGroupId,SecurityGroupName rows=SecurityGroups.SecurityGroup[]

# 查询交换机列表
aliyun ecs DescribeVSwitches --RegionId cn-hangzhou --VpcId <vpc-id> \
  --output cols=VSwitchId,VSwitchName,CidrBlock rows=VSwitches.VSwitch[]

# 查询实例列表
aliyun ecs DescribeInstances --RegionId cn-hangzhou --MaxResults 10 \
  --output cols=InstanceId,InstanceName,Status,InstanceType rows=Instances.Instance[]

# 查询指定实例详情
aliyun ecs DescribeInstances --RegionId cn-hangzhou --InstanceIds '["i-xxxxxxxxxxxxx"]'

# 查询实例状态
aliyun ecs DescribeInstanceStatus --RegionId cn-hangzhou --MaxResults 10

# 查询实例公网 IP
aliyun ecs DescribeInstances --RegionId cn-hangzhou --InstanceIds '["i-xxxxxxxxxxxxx"]' \
  --output cols=InstanceId,PublicIp rows=Instances.Instance[]
```

### 创建类（危险操作，需确认）

```bash
# 创建 ECS 实例（基础版）
aliyun ecs CreateInstance \
  --RegionId cn-hangzhou \
  --InstanceType ecs.g6.large \
  --ImageId ubuntu_22_04_x64_20G_alibase_20240528.vhd \
  --SecurityGroupId sg-xxxxxxxxxxxxx \
  --VSwitchId vsw-xxxxxxxxxxxxx \
  --InstanceChargeType PostPaid \
  --InternetMaxBandwidthOut 5 \
  --InstanceName "my-ecs-instance" \
  --SystemDiskCategory cloud_essd \
  --SystemDiskSize 40

# 创建 ECS 实例（完整版，含密码、数据盘、标签等）
aliyun ecs CreateInstance \
  --RegionId cn-hangzhou \
  --ZoneId cn-hangzhou-h \
  --InstanceType ecs.g6.large \
  --ImageId ubuntu_22_04_x64_20G_alibase_20240528.vhd \
  --SecurityGroupId sg-xxxxxxxxxxxxx \
  --VSwitchId vsw-xxxxxxxxxxxxx \
  --InstanceChargeType PostPaid \
  --InternetChargeType PayByTraffic \
  --InternetMaxBandwidthOut 5 \
  --InstanceName "production-server-01" \
  --Password "YourStrongP@ssw0rd!" \
  --SystemDiskCategory cloud_essd \
  --SystemDiskSize 40 \
  --SystemDiskPerformanceLevel PL1 \
  --DataDisk.1.Category cloud_essd \
  --DataDisk.1.Size 100 \
  --DataDisk.1.DiskName "data-disk-1" \
  --Tag.1.Key "Environment" \
  --Tag.1.Value "Production" \
  --Tag.2.Key "Project" \
  --Tag.2.Value "MyProject"
```

### 启动/停止类（危险操作，需确认）

```bash
# 启动实例
aliyun ecs StartInstance --InstanceId i-xxxxxxxxxxxxx

# 停止实例
aliyun ecs StopInstance --InstanceId i-xxxxxxxxxxxxx --ForceStop false

# 重启实例
aliyun ecs RebootInstance --InstanceId i-xxxxxxxxxxxxx --ForceStop false
```

### 网络类

```bash
# 分配公网 IP（创建实例时带宽为 0 时需要）
aliyun ecs AllocatePublicIpAddress --InstanceId i-xxxxxxxxxxxxx

# 修改实例带宽
aliyun ecs ModifyInstanceNetworkSpec \
  --InstanceId i-xxxxxxxxxxxxx \
  --InternetMaxBandwidthOut 10
```

### 删除类（⚠️ 极度危险，需确认）

```bash
# 删除实例（默认保留云盘）
aliyun ecs DeleteInstance --InstanceId i-xxxxxxxxxxxxx --Force true

# 删除实例（同时释放云盘）
aliyun ecs DeleteInstance --InstanceId i-xxxxxxxxxxxxx --Force true --TerminateSubscription true
```

---

## 完整采购工作流

### 工作流 1：标准采购流程（创建 + 启动 + 等待运行）

```bash
# ===== Step 1: 确认配置参数 =====
# 必需参数清单：
# - RegionId: 地域 ID（如 cn-hangzhou）
# - InstanceType: 实例规格（如 ecs.g6.large）
# - ImageId: 镜像 ID
# - SecurityGroupId: 安全组 ID
# - VSwitchId: 交换机 ID（VPC 网络必需）

# ===== Step 2: 检查资源库存（可选但推荐）=====
aliyun ecs DescribeAvailableResource \
  --RegionId cn-hangzhou \
  --ZoneId cn-hangzhou-h \
  --DestinationResource InstanceType \
  --InstanceType ecs.g6.large

# ===== Step 3: 创建实例 =====
aliyun ecs CreateInstance \
  --RegionId cn-hangzhou \
  --InstanceType ecs.g6.large \
  --ImageId ubuntu_22_04_x64_20G_alibase_20240528.vhd \
  --SecurityGroupId sg-xxxxxxxxxxxxx \
  --VSwitchId vsw-xxxxxxxxxxxxx \
  --InstanceChargeType PostPaid \
  --InternetMaxBandwidthOut 5 \
  --InstanceName "my-new-server" \
  --SystemDiskCategory cloud_essd \
  --SystemDiskSize 40
# 返回：InstanceId = "i-xxxxxxxxxxxxx"

# ===== Step 4: 等待实例创建完成（状态变为 Stopped）=====
aliyun ecs DescribeInstanceStatus \
  --RegionId cn-hangzhou \
  --InstanceIds '["i-xxxxxxxxxxxxx"]' \
  --waiter expr='InstanceStatuses.InstanceStatus[0].Status' to=Stopped timeout=300 interval=10

# ===== Step 5: 启动实例 =====
aliyun ecs StartInstance --InstanceId i-xxxxxxxxxxxxx

# ===== Step 6: 等待实例运行（状态变为 Running）=====
aliyun ecs DescribeInstances \
  --RegionId cn-hangzhou \
  --InstanceIds '["i-xxxxxxxxxxxxx"]' \
  --waiter expr='Instances.Instance[0].Status' to=Running timeout=300 interval=10

# ===== Step 7: 获取实例信息（含公网 IP）=====
aliyun ecs DescribeInstances \
  --RegionId cn-hangzhou \
  --InstanceIds '["i-xxxxxxxxxxxxx"]' \
  --output cols=InstanceId,InstanceName,Status,InstanceType,PublicIpAddress,PrivateIpAddress \
  rows=Instances.Instance[]
```

### 工作流 2：查询可用资源后采购

```bash
# ===== Step 1: 查询可用地域 =====
aliyun ecs DescribeRegions --output cols=RegionId,LocalName rows=Regions.Region[]

# ===== Step 2: 查询可用区 =====
aliyun ecs DescribeZones --RegionId cn-hangzhou --output cols=ZoneId,LocalName rows=Zones.Zone[]

# ===== Step 3: 查询可用实例规格 =====
aliyun ecs DescribeInstanceTypes --RegionId cn-hangzhou --MaxResults 20 \
  --output cols=InstanceTypeId,CpuCoreCount,MemorySize,InstanceTypeFamily rows=InstanceTypes.InstanceType[]

# ===== Step 4: 查询可用镜像 =====
aliyun ecs DescribeImages --RegionId cn-hangzhou --ImageOwnerAlias system --MaxResults 10 \
  --output cols=ImageId,OSName,Size rows=Images.Image[]

# ===== Step 5: 查询可用安全组 =====
aliyun ecs DescribeSecurityGroups --RegionId cn-hangzhou --VpcId vpc-xxxxxxxxxxxxx \
  --output cols=SecurityGroupId,SecurityGroupName rows=SecurityGroups.SecurityGroup[]

# ===== Step 6: 创建并启动（同工作流 1）=====
# ... 执行工作流 1 的 Step 3-7
```

### 工作流 3：批量查询实例状态

```bash
# 查询所有运行中的实例
aliyun ecs DescribeInstances --RegionId cn-hangzhou --Status Running --MaxResults 50 \
  --output cols=InstanceId,InstanceName,InstanceType,Status,CreationTime \
  rows=Instances.Instance[]

# 查询指定安全组内的实例
aliyun ecs DescribeInstances --RegionId cn-hangzhou --SecurityGroupId sg-xxxxxxxxxxxxx \
  --output cols=InstanceId,InstanceName,Status rows=Instances.Instance[]

# 按标签查询实例
aliyun ecs DescribeInstances --RegionId cn-hangzhou \
  --Tag.1.Key "Environment" --Tag.1.Value "Production" \
  --output cols=InstanceId,InstanceName,Status rows=Instances.Instance[]
```

---

## 参数详解

### CreateInstance 核心参数

| 参数 | 类型 | 必填 | 说明 | 示例值 |
|------|------|:---:|------|--------|
| `RegionId` | string | ✅ | 地域 ID | `cn-hangzhou` |
| `InstanceType` | string | ✅ | 实例规格 | `ecs.g6.large` |
| `ImageId` | string | 条件 | 镜像 ID（不指定 ImageFamily 时必填） | `ubuntu_22_04_x64_20G_alibase_20240528.vhd` |
| `SecurityGroupId` | string | 条件 | 安全组 ID（VPC 网络推荐指定） | `sg-xxxxxxxxxxxxx` |
| `VSwitchId` | string | 条件 | 交换机 ID（VPC 网络必需） | `vsw-xxxxxxxxxxxxx` |
| `InstanceChargeType` | string | ❌ | 付费方式：PostPaid/PrePaid | `PostPaid` |
| `InternetMaxBandwidthOut` | integer | ❌ | 公网出带宽（Mbit/s），0 表示不分配公网 IP | `5` |
| `InstanceName` | string | ❌ | 实例名称（2-128 字符） | `my-server` |
| `Password` | string | ❌ | 实例密码（8-30 字符，含大小写+数字+特殊字符） | `YourP@ssw0rd!` |
| `SystemDisk.Category` | string | ❌ | 系统盘类型 | `cloud_essd` |
| `SystemDisk.Size` | integer | ❌ | 系统盘大小（GiB） | `40` |
| `ZoneId` | string | ❌ | 可用区 ID | `cn-hangzhou-h` |
| `InternetChargeType` | string | ❌ | 网络计费类型：PayByTraffic/PayByBandwidth | `PayByTraffic` |
| `KeyPairName` | string | ❌ | SSH 密钥对名称（Linux 推荐） | `my-keypair` |
| `UserData` | string | ❌ | 实例自定义数据（Base64 编码） | `IyEvYmluL2Jhc2g=` |

### 系统盘类型（SystemDisk.Category）

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| `cloud_essd` | ESSD 云盘 | 高性能业务（推荐） |
| `cloud_essd_entry` | ESSD Entry 云盘 | 轻量级业务（仅 ecs.u1/ecs.e 规格） |
| `cloud_auto` | ESSD AutoPL 云盘 | 自动弹性扩容 |
| `cloud_ssd` | SSD 云盘 | 中等性能需求 |
| `cloud_efficiency` | 高效云盘 | 一般性能需求 |
| `cloud` | 普通云盘 | 已停售规格 |

### 常见实例规格

| 规格 | vCPU | 内存 | 适用场景 |
|------|:----:|:----:|----------|
| `ecs.e-c1m2.large` | 2 | 2 GiB | 轻量级 Web 服务 |
| `ecs.e-c1m4.large` | 2 | 4 GiB | 小型应用服务 |
| `ecs.g6.large` | 2 | 8 GiB | 通用计算（推荐） |
| `ecs.g6.xlarge` | 4 | 16 GiB | 中型应用服务 |
| `ecs.g6.2xlarge` | 8 | 32 GiB | 大型应用服务 |
| `ecs.c6.xlarge` | 4 | 8 GiB | 计算密集型 |
| `ecs.r6.xlarge` | 4 | 32 GiB | 内存密集型 |

### 常见公共镜像

| 操作系统 | ImageId 示例 | 说明 |
|----------|-------------|------|
| Ubuntu 22.04 | `ubuntu_22_04_x64_20G_alibase_20240528.vhd` | 推荐 |
| Ubuntu 20.04 | `ubuntu_20_04_x64_20G_alibase_20240528.vhd` | 稳定版本 |
| CentOS 7.9 | `centos_7_9_x64_20G_alibase_20240528.vhd` | 经典版本 |
| Debian 12 | `debian_12_x64_20G_alibase_20240528.vhd` | 轻量稳定 |
| Windows Server 2022 | `win2022_64_dtc_20220916_en-us_40G_alibase_20240528.vhd` | Windows 服务器 |

> **注意**：ImageId 会随时间更新，建议通过 `aliyun ecs DescribeImages` 查询最新可用镜像。

---

## --waiter 参数详解

`--waiter` 用于轮询等待实例状态转换，是采购流程中的关键机制。

### 语法

```bash
--waiter expr='<jmespath表达式>' to=<目标状态> timeout=<超时秒数> interval=<轮询间隔秒数>
```

### 常用场景

```bash
# 等待实例创建完成（Pending → Stopped）
aliyun ecs DescribeInstanceStatus \
  --RegionId cn-hangzhou \
  --InstanceIds '["i-xxxxxxxxxxxxx"]' \
  --waiter expr='InstanceStatuses.InstanceStatus[0].Status' to=Stopped timeout=300 interval=10

# 等待实例启动完成（Starting → Running）
aliyun ecs DescribeInstances \
  --RegionId cn-hangzhou \
  --InstanceIds '["i-xxxxxxxxxxxxx"]' \
  --waiter expr='Instances.Instance[0].Status' to=Running timeout=300 interval=10

# 等待实例停止完成（Stopping → Stopped）
aliyun ecs DescribeInstances \
  --RegionId cn-hangzhou \
  --InstanceIds '["i-xxxxxxxxxxxxx"]' \
  --waiter expr='Instances.Instance[0].Status' to=Stopped timeout=300 interval=10
```

### 状态转换图

```
创建请求 → Pending（创建中） → Stopped（已停止，创建完成）
                                                      ↓
                                              StartInstance
                                                      ↓
                                             Starting（启动中） → Running（运行中）✅

运行中 → Stopping（停止中） → Stopped（已停止）
                              ↓
                      DeleteInstance / ReleaseInstance
```

---

## 常见错误处理

| 错误代码 | 说明 | 处理方式 |
|---------|------|----------|
| `InvalidInstanceType.ValueNotSupported` | 实例规格不存在或无权限 | 使用 `DescribeInstanceTypes` 查询可用规格 |
| `InvalidImageId.NotFound` | 镜像不存在 | 使用 `DescribeImages` 查询可用镜像 |
| `InvalidSecurityGroupId.NotFound` | 安全组不存在 | 使用 `DescribeSecurityGroups` 查询可用安全组 |
| `InvalidVSwitchId.NotFound` | 交换机不存在 | 使用 `DescribeVSwitches` 查询可用交换机 |
| `OperationDenied` | 操作被拒绝（可能库存不足） | 检查可用区库存，尝试其他可用区 |
| `Zone.NotOnSale` | 可用区暂停售卖 | 尝试其他可用区 |
| `QuotaExceed.AfterpayInstance` | 按量付费实例数量超限 | 前往 ECS 控制台申请提升配额 |
| `IncorrectInstanceStatus` | 实例状态不支持当前操作 | 等待实例状态转换完成后再操作 |
| `InsufficientBalance` | 账户余额不足 | 充值后再操作 |
| `Account.Arrearage` | 账户欠费 | 结清欠款后再操作 |

### 错误排查命令

```bash
# 查看实例详细状态
aliyun ecs DescribeInstances --RegionId cn-hangzhou --InstanceIds '["i-xxxxxxxxxxxxx"]'

# 查看实例操作锁
aliyun ecs DescribeInstances --RegionId cn-hangzhou --InstanceIds '["i-xxxxxxxxxxxxx"]' \
  --output cols=InstanceId,Status,OperationLocks rows=Instances.Instance[]
```

---

## 环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `ALIBABA_CLOUD_ACCESS_KEY_ID` | AccessKey ID | `LTAI5t...` |
| `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | AccessKey Secret | `abc123...` |
| `ALIBABA_CLOUD_REGION_ID` | 默认地域 | `cn-hangzhou` |
| `ALIBABA_CLOUD_PROFILE` | 指定配置 profile | `production` |
| `ALIBABA_CLOUD_IGNORE_PROFILE` | 忽略配置文件 | `TRUE` |
| `DEBUG=sdk` | 开启 HTTP 请求调试 | `sdk` |

---

## 参考文档

- **官方仓库**: https://github.com/aliyun/aliyun-cli
- **CLI 使用文档**: https://help.aliyun.com/zh/cli/
- **ECS CreateInstance API**: https://help.aliyun.com/zh/ecs/developer-reference/api-ecs-2014-05-26-createinstance
- **ECS RunInstances API**: https://help.aliyun.com/zh/ecs/developer-reference/api-ecs-2014-05-26-runinstances
- **ECS StartInstance API**: https://help.aliyun.com/zh/ecs/developer-reference/api-ecs-2014-05-26-startinstance
- **ECS DescribeInstances API**: https://help.aliyun.com/zh/ecs/developer-reference/api-ecs-2014-05-26-describeinstances
- **实例规格族**: https://help.aliyun.com/zh/ecs/user-guide/overview-of-instance-families
- **公共镜像列表**: https://help.aliyun.com/zh/ecs/user-guide/public-images
