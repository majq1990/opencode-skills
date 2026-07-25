---
name: qijian-deploy
version: 1.1.0
description: 麒舰（eurbanpro）微服务栈一键自动化部署技能。从阿里云 ECS 抢占式采购（cn-beijing-h / ecs.e-c1m4.2xlarge）到 oneinstall_v2 install.sh 菜单 0/1/2/3 全流程自动化，支持银河麒麟 V10 SP2/SP3/V11、openEuler 22.03/24.03、UOS 20-1060a/1060e/1070a、CentOS 7.9 等多种 OS（x86 与 aarch64），根据用户指定的操作系统自动选择镜像 ID 与 dl_v2.sh 菜单路径；节点分布支持 2/3/5 节点预设加动态规划。用户说"部署一套麒舰"、"采购麒舰部署机"、"跑一遍 oneinstall_v2"、"麒舰考核环境准备"、"部署麒舰 kylin V10 SP3"、"用欧拉 22.03 跑麒舰"、"/qijian-deploy" 等任一表述时必须激活本技能。部署异常自动推送钉钉 #oneinstall 告警，成功后在对话回显摘要。
---

# 麒舰微服务栈一键部署 Skill

> **版本**：v1.1.0
> **最近一次成功部署**：2026-04-18（openEuler 22.03 SP3 x86，3 节点）
> **注意**：本 skill 用于麒舰考核/测试环境快速搭建。生产环境部署走独立流程。

## 目的

从零采购阿里云 ECS 开始，自动完成麒舰（eurbanpro）微服务栈分布式部署。全程在本地 Windows 环境执行（aliyun-cli 本地调用，SSH 直连 ECS 节点），不经过跳板机。

## 工具依赖检查

| 工具 | 用途 | 检查命令 | 安装方式 |
|---|---|---|---|
| aliyun-cli | 阿里云 API 调用 | `aliyun configure list` | `winget install Alibaba.Chinese.A AlibabaCloudCLI` |
| jq | JSON 解析 | `jq --version` | `winget install jqlang.jq` |
| sshpass | 密码方式 SSH 免密分发 | `sshpass -V` | MSYS2: `pacman -S sshpass` |
| ssh / scp | 远程连接与文件传输 | `ssh -V` | Windows 11 自带 |
| tar | 打包 oneinstall_v2 源码 | `tar --version` | 自带 |
| curl | 钉钉推送 | `curl --version` | 自带 |

## 触发方式

- 显式 slash：`/qijian-deploy`
- 自然语言："部署一套麒舰"、"采购麒舰部署机"、"跑一遍 oneinstall_v2"、"麒舰考核环境准备"等

## 输入约定

| 参数 | 默认 | 覆盖示例 |
|---|---|---|
| OS 版本 | `kylin_v10_sp3_x86` | "部署麒舰 用 openEuler 22.03 x86" |
| 节点数 | 3 台 | "2 节点精简部署" |
| region | `cn-beijing` | "用乌兰察布 h 区" |
| 实例规格 | `ecs.e-c1m4.2xlarge` (8U32G) | "用 16U64G" |
| 付费模式 | 抢占式（SpotAsPriceGo） | "改按量付费" |
| 麒舰版本 | `release720` | "装 release730" |
| 项目代号 | `faq` | "项目用 demo" |

## OS → 镜像 → 下载包 联动

所有映射固化在 `config/os_image_map.yml`。

**阶段 0 必须执行**：
1. 从用户输入解析 OS 名称，在 `os_image_map.yml` 的 `aliases` 里匹配到 OS key
2. 根据 region 从 OS 的 `images` 取 ImageId
3. 取出 OS 的 `dl_v2_menu`（3 个整数）+ `dl_v2_input_template`（通用部分），在阶段 3 拼成完整 10 行输入
4. 若 OS 条目 `verified: false`，**必须先 ssh node1 手工跑一次 `dl_v2.sh` 核对菜单路径**，确认后回写 `os_image_map.yml` 并把 `verified` 改为 `true`

> ⚠️ 错一行菜单会导致下错包，后续阶段 4 才爆掉，浪费 40+ 分钟。

## 关键常量

| 项目 | 值 |
|---|---|
| 执行环境 | 本地 Windows 11（Git Bash），aliyun-cli + SSH 直连 ECS |
| 阿里云区域 / 可用区 | cn-beijing / cn-beijing-h |
| VPC / 交换机 | vpc-2ze5yg4iioqg6p8be1abs / vsw-2ze6dmyu5gjp9p9oes7qa |
| 实例规格 | ecs.e-c1m4.2xlarge (8U32G) |
| 付费模式 | SpotAsPriceGo 抢占式 |
| 节点数量 | 默认 3（可变） |
| 系统盘 | 80G cloud_essd |
| 安全组 | sg-2ze1pookadxppb0kx9q2（同 VPC，ALL -1/-1 src=10.0.0.0/8） |
| root 密码 | Egova@123 |
| SSH 密钥 | 本地 `~/.ssh/id_rsa`（阶段 2 分发到 ECS 节点） |
| oneinstall_v2 源 | 本地 `D:\git\oneinstall_v2` |
| 麒舰版本 | release720 |
| 项目代号 | faq |
| 包下载账号 | majianquan / Egova@123 |

> ⚠️ **root 密码 Egova@123 是出厂默认，生产环境完毕必须立即改密。**

## SSH 密钥说明

- 本机密钥：`~/.ssh/id_rsa`（RSA）或 `~/.ssh/mjqegova-ed25519`（ed25519，较新部署用）
- 阶段 2 通过 sshpass 将本地公钥分发到 ECS 节点
- qijian 集群内节点间 SSH 走内网，同 VPC SG 内互通无需额外配置

## 全流程

### 阶段 1：采购 ECS

```bash
aliyun ecs RunInstances \
  --RegionId cn-beijing --ZoneId cn-beijing-h \
  --ImageId <从 os_image_map.yml 选定> \
  --InstanceType ecs.e-c1m4.2xlarge \
  --VSwitchId vsw-2ze6dmyu5gjp9p9oes7qa \
  --SecurityGroupId sg-2ze1pookadxppb0kx9q2 \
  --SystemDisk.Category cloud_essd --SystemDisk.Size 80 \
  --InternetMaxBandwidthOut 100 --InternetChargeType PayByTraffic \
  --InstanceChargeType PostPaid --SpotStrategy SpotAsPriceGo --SpotDuration 0 \
  --Password "Egova@123" --Amount 3 \
  --HostName qijian-node --InstanceName qijian-deploy
```

> ⚠️ aliyun-cli `RunInstances` 必须加 `--RegionId`（否则静默失败）；spot 实例公网 IP 必须主动调 `AllocatePublicIpAddress` 获取。
> 详见 memory `feedback_aliyun_cli_quirks.md`。

轮询 `DescribeInstanceAttribute` 直到 Status=Running，获取公网 IP。

### 阶段 2：密钥分发 + 基础连通

```bash
sshpass -p "Egova@123" ssh-copy-id -o StrictHostKeyChecking=no root@<公网IP>
```

验证：`ssh root@<公网IP> 'uname -a; cat /etc/os-release | head -3'`

sshpass 不可用时替代方案：
- 方案 A：ECS 创建时指定 `--KeyPairName`（需提前在阿里云创建密钥对）
- 方案 B：手动 `ssh-copy-id root@<IP>`（Claude 提示用户输入密码）

### 阶段 3：下发 oneinstall_v2 + 下载资源包

1. 本地 `D:\git\oneinstall_v2` 打 tar → scp 到 node1 → 解压到 `/egova/onekey_install/oneinstall_v2`
2. 在 node1 跑 `bash /egova/onekey_install/oneinstall_v2/dl_v2.sh`，喂按 OS 动态拼接的 10 行输入：
   ```
   <dl_v2_menu[0]>   # OS 家族
   <dl_v2_menu[1]>   # OS 子版本
   <dl_v2_menu[2]>   # 架构（x86=2 / arm=1）
   2                  # base_select（含 env/repo）
   1                  # script_select（麒舰微服务 v14-standard）
                      # 空行 = web_ver=release720
   majianquan         # account
   Egova@123          # password
   faq                # project
   0                  # web_app_select（全选）
   ```

成功判据：`/egova/one/` 下至少 32 个 tar.gz，总大小 > 20G。

### 阶段 4：资源包完整性断言（关键 gate）

在 node1 上执行 SQL 文件结构性断言（LOCK/UNLOCK 配对、`-- Dump completed` 尾部检查）。

> ⚠️ cgdb.sql 坏包历史：上游 mysqldump 导出不完整时 LOCK/UNLOCK 数量不等。**不要尝试重下载**，直接推钉钉让麒舰侧重导源包。

### 阶段 5：渲染配置 + 推送到 node1

根据 3 台实际私网 IP 渲染 `hosts.yml` 与 `eurbanpro_multi_server.yml`：
- `ip_web_uma.need_flag: 0`（UMA tomcat 包不在麒舰栈）
- TDengine v2 与 TDengine3 永不共置（6030 端口冲突）
- mysql 主库所在节点不跑 nacos / eurbanpro 等高负载微服务

> ⚠️ `hosts.yml` 字段名用 `ansible_ssh_host`（不是 `ansible_host`）；node1 自身公钥需加入自身 `authorized_keys`。

### 阶段 6：执行 install.sh 菜单 0→1→2→3

- `0` 建本地 repo → 等待 `OK` 提示
- `1` 装 ansible + ntp + jdk → tail /var/log/ansible.log 直到 PLAY RECAP 出现 failed=0
- `2` 加服务器 → 验证 3 台免密 + 时钟同步
- `3` 部署应用 → 并行 tail -f /var/log/ansible.log

**fatal 检测**：grep `^fatal:.*FAILED!` 且**不是** `...ignoring`。

#### 各节点预期端口 checklist

| 节点 | 端口 |
|---|---|
| node1 | 22, 2181(kafka-zk), 8080/7777(nginx), 8848/9848/9849/7848(nacos), 9093(kafka), 30001/34761(minio) |
| node2 | 22, 3306/33060(mysql), 6380(redis), 6030/6035/6040/6041(TDengine) |
| node3 | 22, 5432(postgres), 6030(TDengine3), 其他 GIS 应用端口 |

## 节点分布预设

见 `config/node_roles.yml`，默认 `default_preset: 3-node-standard`。

固定约束（跨所有 preset）：
- TDengine v2 与 TDengine3 永不共置（6030 端口冲突）
- mysql 主库所在节点不跑 nacos / eurbanpro 等高负载微服务
- UMA tomcat 包不在麒舰栈，`ip_web_uma.need_flag` 恒为 0

## 钉钉推送规范

```bash
curl -s -X POST "https://oapi.dingtalk.com/robot/send?access_token=${DINGTALK_WEBHOOK_TOKEN:-6529f41717e2d0582db6d251c94a6bca7a1196eb8a029a0e9998975c57c245fc}" \
  -H "Content-Type: application/json" \
  -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"#oneinstall ${TITLE}\n${CONTENT}\"}}"
```

| 触发 | 标题 |
|---|---|
| 阶段 1 失败 | 【麒舰部署 · 采购失败】 |
| 阶段 2 失败 | 【麒舰部署 · 密钥分发失败】 |
| 阶段 3 失败 | 【麒舰部署 · 资源下载失败】 |
| 阶段 4 失败 | 【麒舰部署 · SQL 包损坏】 |
| 阶段 6 失败 | 【麒舰部署 · ansible 失败】 |
| **成功** | （不推钉钉，对话回显摘要） |

## 已知 pitfall 档案

1. **cgdb.sql 坏包**：务必执行阶段 4 SQL 断言
2. **dl_v2.sh display_web_app_select 子菜单**：`[dataflow-毕升采集]` 键含 `-` 触发子菜单，需额外追加 `0`
3. **Kylin V10 ansible 识别**：ansible 识别为 `Kylin Linux Advanced Server`，需在 `group_vars/all.yml` 补映射
4. **YAML null 值**：`eurbanpro_multi_server.yml` 中 `master:` / `slave:` 无值时必须显式写 `master: ""`
5. **install.sh stdin 被消费**：菜单 loop + yq 等子进程会消费 stdin，不可靠。可改为直接调底层脚本 `i_multi_software.sh` 绕过交互菜单
6. **openresty 端口自阻塞**：step 0 先启动 openresty 再问端口，已占用则死循环。手动完成 step 0
7. **Windows SSH 路径**：scp 本地路径用 `/d/git/...`（Git Bash）或 `D:/git/...`，不要用反斜杠
8. **aliyun-cli 必须加 --RegionId**：否则静默失败
9. **spot 实例公网 IP**：必须主动调 `AllocatePublicIpAddress`，不会自动分配

## 完成后对话回显模板

```
麒舰部署完成 ✓
采购：i-xxx / i-yyy / i-zzz（北京h区抢占式）
公网 IP：<n1>/<n2>/<n3>  私网 IP：<p1>/<p2>/<p3>
下载：32 包总计 <N>G，SQL 断言全通过
部署：ansible failed=0，端口 checklist 全部就绪
访问入口：http://<n1>:8080
自动释放：<次日 23:59>
```

## 善后提醒

1. **改密**：`Egova@123` 是出厂默认，生产环境立即改
2. **自动释放时间**：抢占式次日 23:59 被阿里云回收，长期使用请转按量付费
3. **浏览器验收**：访问 `http://<n1>:8080` 走一遍登录 + 关键菜单
4. **留痕**：把 3 个 InstanceId / 公网 IP / 本次 OS / preset 写入 memory

## 脚本清单

- `config/os_image_map.yml`：OS → 镜像 → dl_v2 菜单映射
- `config/node_roles.yml`：节点分布预设（供阶段 5 渲染引用）
