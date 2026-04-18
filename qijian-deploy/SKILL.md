---
name: qijian-deploy
description: 麒舰（eurbanpro）微服务栈一键自动化部署技能。从阿里云 ECS 抢占式采购（cn-beijing-h / ecs.e-c1m4.2xlarge）到 oneinstall_v2 install.sh 菜单 0/1/2/3 全流程自动化，支持银河麒麟 V10 SP2/SP3/V11、openEuler 22.03/24.03、UOS 20-1060a/1060e/1070a、CentOS 7.9 等多种 OS（x86 与 aarch64），根据用户指定的操作系统自动选择镜像 ID 与 dl_v2.sh 菜单路径；节点分布支持 2/3/5 节点预设加动态规划。用户说"部署一套麒舰"、"采购麒舰部署机"、"跑一遍 oneinstall_v2"、"麒舰考核环境准备"、"部署麒舰 kylin V10 SP3"、"用欧拉 22.03 跑麒舰"、"/qijian-deploy" 等任一表述时必须激活本技能。部署异常自动推送钉钉 #oneinstall 告警，成功后在对话回显摘要。
---

# 麒舰微服务栈一键部署 Skill

## 目的

从零采购阿里云 ECS 开始，自动完成麒舰（eurbanpro）微服务栈分布式部署。全程在本地 Windows 环境执行（aliyun-cli 本地调用，SSH 直连 ECS 节点），不经过跳板机。触发后 Claude 按本文档逐阶段执行，部署异常时推钉钉，完成后在当前对话回显摘要。

## 工具依赖检查与安装引导

**阶段 0 前置检查时，必须先检查以下工具是否可用。任一缺失时，按对应安装命令引导用户安装，安装完成后再继续流程。**

| 工具 | 用途 | 检查命令 | 安装方式 |
|---|---|---|---|
| aliyun-cli | 阿里云 API 调用 | `aliyun configure list` | `winget install Alibaba.Chinese.AlibabaCloudCLI` 或从 [GitHub Releases](https://github.com/aliyun/aliyun-cli/releases) 下载 |
| jq | JSON 解析 aliyun-cli 输出 | `jq --version` | `winget install jqlang.jq` |
| sshpass | 密码方式 SSH 免密分发 | `sshpass -V` | Git Bash: 从 MSYS2 安装 `pacman -S sshpass`；或下载 [sshpass-win32](https://github.com/xhcoding/sshpass-win32/releases) 放入 PATH |
| ssh / scp | 远程连接与文件传输 | `ssh -V` | Windows 11 自带 OpenSSH |
| tar | 打包 oneinstall_v2 源码 | `tar --version` | Windows 11 / Git Bash 自带 |
| curl | 钉钉推送 | `curl --version` | Windows 11 / Git Bash 自带 |

**自动安装流程**（Claude 在前置检查中执行）：

```
1. 检测 jq → 缺失则运行 `winget install jqlang.jq --accept-package-agreements --accept-source-agreements`
2. 检测 sshpass → 缺失则：
   a. 尝试下载 sshpass-win32 到 C:\Users\majq1\bin\sshpass.exe
   b. 若 ~/bin 不在 PATH 中，提示用户加入 PATH 或重启终端
3. 检测 aliyun-cli → 缺失则运行 `winget install Alibaba.Chinese.AlibabaCloudCLI`
   → 未配置则引导 `aliyun configure --mode AK` 交互式配置
```

**备选方案**：若 sshpass 实在无法安装，阶段 2 可改用以下替代：
- 方案 A：ECS 创建时指定 KeyPairName（需提前在阿里云创建密钥对并下载私钥）
- 方案 B：手动对 3 台执行 `ssh-copy-id root@<IP>`（Claude 提示用户输入密码）

## 使用说明

### 1. 前置检查（触发后 Claude 先跑，任一失败立即停下来告诉用户）

| 检查项 | 命令 / 路径 | 失败应对 |
|---|---|---|
| 工具依赖齐全 | 见"工具依赖检查与安装引导" | 按安装指引逐个安装 |
| 本地 aliyun-cli 已配置 | `aliyun configure list` | 引导 `aliyun configure --mode AK`，需用户提供 AccessKey |
| 本地有 oneinstall_v2 源码 | `ls D:\git\oneinstall_v2\install.sh` | 引导用户 `git pull` 或指到正确路径 |
| 本地 SSH 可达公网 | `ssh -o ConnectTimeout=5 root@<任一已知IP> true`（仅断点续跑时） | 检查网络 / 防火墙 |
| 节点配额未爆 | `aliyun ecs DescribeAccountAttributes --RegionId cn-beijing` | 配额不足时提醒用户去控制台申请 |

### 2. 触发方式

- 显式 slash：`/qijian-deploy`
- 自然语言（见"触发"章节）：用户提到"部署麒舰 / 跑 oneinstall_v2 / 麒舰考核准备"等

### 3. 输入约定（可在触发语里给出，缺省走默认）

| 参数 | 默认 | 覆盖示例 | 约束 |
|---|---|---|---|
| OS 版本 | `kylin_v10_sp3_x86`（映射见 `config/os_image_map.yml`） | "部署麒舰 用 openEuler 22.03 x86" | 未 `verified: true` 的 OS 先人工核对 dl_v2 菜单 |
| 节点数 | 3 台 | "2 节点精简部署"、"来 5 台演练生产拓扑" | 见 `config/node_roles.yml` preset 或 `dynamic_planning_rules` |
| region | `cn-beijing` | "用乌兰察布 h 区" | 该 region 下必须有对应 OS 镜像，否则回退并确认 |
| 实例规格 | `ecs.e-c1m4.2xlarge` (8U32G) | "用 16U64G 跑性能验证" | 规格变化需重校 preset 命中 |
| 付费模式 | 抢占式（SpotAsPriceGo） | "改按量付费" | 抢占式默认次日 23:59 自动释放 |
| 麒舰版本 | `release720` | "装 release730" | 改 `dl_v2_input_template.web_ver` |
| 项目代号 | `faq` | "项目用 demo" | 改 `dl_v2_input_template.project` |

### 4. 运行过程中 Claude 对话的节奏

- 每阶段**开始**时：说清楚本阶段目标 + 预计耗时（见下表）
- 每阶段**完成**时：一句话汇报关键结果（InstanceId / 下载包数量 / PLAY RECAP）
- 遇到 fatal：贴完整 task name + stdout + stderr，推钉钉，暂停等决策
- 切勿静默工作 5 分钟以上，长任务用 `tail -f` 的周期性心跳行代替

| 阶段 | 典型耗时 | 是否可并行 |
|---|---|---|
| 0 参数解析 + 工具检查 | 几秒~几分钟（含安装） | — |
| 1 ECS 采购 | 2-3 分钟 | 3 台并发创建 |
| 2 SSH 免密 | 1 分钟 | 3 台并发 |
| 3 下载资源包 | 15-25 分钟 | 单 node1 串行（20G+ tar.gz） |
| 4 SQL 断言 | 30 秒 | 可并发遍历 |
| 5 渲染 + scp 配置 | 1 分钟 | — |
| 6 install.sh 0→1→2→3 | 30-45 分钟 | 菜单串行，ansible 对节点并发 |
| **合计** | **约 50-75 分钟** | — |

### 5. 输出预期

- **成功**：在当前对话按"完成后对话回显模板"输出摘要（3 个公网 IP、访问入口 `http://<n1>:8080`、root 密码、自动释放时间）；**不推钉钉**
- **失败**：按"钉钉推送规范"推送 #oneinstall 告警（含阶段 + 失败 block）+ 终止流程，等待用户决定重试或修复

### 6. 异常处理与断点续跑

- 每阶段有独立的成功判据与失败处置（见各阶段小节）
- fatal 命中后必须**立即暂停**，不要自作主张重试：ansible task 之间有顺序依赖，带错推进只会雪崩
- **断点续跑**：用户要求"从阶段 X 继续"时，跳过已完成阶段，但阶段 0 的参数解析 + 前置检查**每次都要重跑**（机器 IP 可能已变）
- **抢占式回收**：若 ECS 被阿里云回收（`Status=Stopped` 且 `StoppedMode=StoppedByCloud`），不要试图再启动；直接推钉钉让用户决定是否重新采购

### 7. 部署完成后的善后提醒

对话回显摘要之后，Claude 要主动提醒：
1. **改密**：`Egova@123` 是出厂默认，生产环境立即改
2. **自动释放时间**：抢占式次日 23:59 被阿里云回收，长期使用请转按量付费
3. **浏览器验收**：访问 `http://<n1>:8080` 走一遍登录 + 关键菜单，端口就绪不代表应用可用
4. **留痕**：把 3 个 InstanceId / 公网 IP / 本次 OS / preset 写入 `project_ecs_oneinstall_deploy.md` memory，方便追溯

## 安全与凭据提示

- **`Egova@123`** 是麒舰部署栈的默认初始密码（root 密码、包下载账号密码），并非生产密码。部署完成后应提醒用户改密，长期环境务必替换。
- **钉钉 webhook access_token** 明文写在本 SKILL.md，是"#oneinstall 告警机器人"的常驻值，泄露后别人可以向该群推任意文本（但受关键词 `oneinstall` 过滤保护）。推送时已支持 `DINGTALK_WEBHOOK_TOKEN` 环境变量覆盖，CI/共享环境下建议用环境变量注入。
- **阿里云 AK**：本 skill 使用本地 `~/.aliyun/config.json` 中配置的 aliyun-cli profile，不在 skill 文件中明文写 AK。
- **SSH 密钥**：阶段 2 通过 sshpass + ssh-copy-id 将本地公钥（`~/.ssh/id_rsa.pub`）分发到 ECS 节点，后续所有 SSH 操作走免密。若本地无密钥对，阶段 2 前自动 `ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa`。

## 触发

用户说以下任一条时激活：
- `/qijian-deploy`
- "部署一套麒舰"、"采购麒舰部署机"、"跑一遍 oneinstall_v2"
- "麒舰考核环境准备"
- 指明 OS 时的简写，如 "部署一套麒舰 kylin V10 SP3"、"用欧拉 22.03 跑麒舰"

## OS → 镜像 → 下载包 联动

**重要**：镜像和下载包是联动的。OS 选定后，镜像 ID 与 `dl_v2.sh` 的前 3 行输入（OS 菜单路径）都随之确定。所有映射固化在 `config/os_image_map.yml`。

**阶段 0（流程入口）必须执行**：
1. 从用户输入里解析 OS 名称（如 "kylin V10 SP3 x86"），在 `os_image_map.yml` 的 `aliases` 里匹配到 OS key；用户没指定则用 `default_os: kylin_v10_sp3_x86`
2. 根据 region（默认 `cn-beijing`）从 OS 的 `images` 取 ImageId；该 region 下无镜像则回退到另一个 region 或向用户确认
3. 取出 OS 的 `dl_v2_menu`（3 个整数）+ `dl_v2_input_template`（通用部分），**在阶段 3 拼成完整 10 行输入** `<dl_v2_menu 3行> + <base_select/script_select/空行/账号/密码/项目/web_app_select>`
4. 若 OS 条目 `verified: false`，**必须先 ssh node1 手工跑一次 `dl_v2.sh` 核对菜单路径**（`dl_v2_menu` 里 2/1 对应 x86/arm 是基于 kylin V10 SP3 x86 实测的推断，其他 OS 未验证），确认后把结果回写到 `os_image_map.yml` 并把 `verified` 改为 `true`。**不要跳过此步直接自动化**，错一行菜单会导致下错包，后续阶段 4 才爆掉，浪费 40+ 分钟

## 关键常量

| 项目 | 值 |
|---|---|
| 执行环境 | 本地 Windows 11（Git Bash），aliyun-cli + SSH 直连 ECS |
| 阿里云区域 / 可用区 | cn-beijing / cn-beijing-h |
| VPC / 交换机 | vpc-2ze5yg4iioqg6p8be1abs / vsw-2ze6dmyu5gjp9p9oes7qa |
| 实例规格 | ecs.e-c1m4.2xlarge (8U32G) |
| 付费模式 | SpotAsPriceGo 抢占式 |
| 自定义镜像 | 由 `config/os_image_map.yml` 按用户指定的 OS + region 动态选择 |
| 节点数量 | 默认 3（可变，见"节点分布预设"章节） |
| 系统盘 | 80G cloud_essd |
| 安全组 | sg-2ze1pookadxppb0kx9q2（同 VPC） |
| root 密码 | Egova@123 |
| SSH 密钥 | 本地 `~/.ssh/id_rsa`（阶段 2 分发到 ECS 节点） |
| oneinstall_v2 源 | 本地 `D:\git\oneinstall_v2`（scp 到 node1 后使用） |
| 麒舰版本 | release720 |
| 项目代号 | faq |
| 包下载账号 | majianquan / Egova@123 |
| 钉钉 webhook | https://oapi.dingtalk.com/robot/send?access_token=6529f41717e2d0582db6d251c94a6bca7a1196eb8a029a0e9998975c57c245fc |
| 推送标签 | 所有推送 content 首行必须含 `#oneinstall` |

## 节点分布预设

**节点分布不是硬编码的**：每次部署实际采购的节点数 / 规格 / 业务目标可能不同。所有可选分布见 `config/node_roles.yml`，入口字段 `presets`，默认 `default_preset: 3-node-standard`。

**阶段 5 渲染 hosts.yml 前必须执行的决策流程**：

1. 读 `config/node_roles.yml` 取 `default_preset`
2. 拿阶段 1 采购结果的 `node_count` 与 `spec` 和各 preset 的 `node_count` / `spec` 做精确匹配
3. 命中 preset → 直接使用；未命中 → 按 `dynamic_planning_rules` 即席规划，**并在对话里把推导过程告知用户、等待确认后再渲染**
4. 无论哪种路径，最后都必须叠加 `overrides`（例如 `ip_web_uma.need_flag: 0`）

**固定约束（跨所有 preset 与动态规划）**：
- TDengine v2 与 TDengine3 永不共置（6030 端口冲突）
- mysql 主库所在节点不跑 nacos / eurbanpro 等高负载微服务
- UMA tomcat 包不在麒舰栈，`ip_web_uma.need_flag` 恒为 0

## 全流程（6 阶段）

### 阶段 1：采购 3 台 ECS

本地用 aliyun-cli 发起 `RunInstances`（Amount=3），必须指定 VSwitchId。成功后记录 3 个 InstanceId + 公网 IP + 私网 IP。

```bash
aliyun ecs RunInstances \
  --RegionId cn-beijing \
  --ZoneId cn-beijing-h \
  --ImageId <从 os_image_map.yml 选定> \
  --InstanceType ecs.e-c1m4.2xlarge \
  --VSwitchId vsw-2ze6dmyu5gjp9p9oes7qa \
  --SecurityGroupId sg-2ze1pookadxppb0kx9q2 \
  --SystemDisk.Category cloud_essd \
  --SystemDisk.Size 80 \
  --InternetMaxBandwidthOut 100 \
  --InternetChargeType PayByTraffic \
  --InstanceChargeType PostPaid \
  --SpotStrategy SpotAsPriceGo \
  --SpotDuration 0 \
  --Password "Egova@123" \
  --Amount 3 \
  --HostName qijian-node \
  --InstanceName qijian-deploy
```

创建后轮询 `DescribeInstanceAttribute` 直到 Status=Running，获取公网 IP（必要时调 `AllocatePublicIpAddress`）。

成功判据：3 个实例 Status=Running 且都拿到公网 IP。

失败处置：推钉钉 `[阶段1 采购失败]`，终止流程。

### 阶段 2：密钥分发 + 基础连通

**前提**：本地 `~/.ssh/id_rsa.pub` 存在，不存在则先 `ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa`。

本地用 sshpass 对 3 台 ECS 公网 IP 执行密钥分发：

```bash
sshpass -p "Egova@123" ssh-copy-id -o StrictHostKeyChecking=no root@<公网IP>
```

分发后验证免密 + OS 信息：

```bash
ssh root@<公网IP> 'uname -a; cat /etc/os-release | head -3'
```

**sshpass 不可用时的替代方案**：
1. 提示用户手动执行 `ssh-copy-id root@<IP1> && ssh-copy-id root@<IP2> && ssh-copy-id root@<IP3>`，输入密码 `Egova@123`
2. 或在 ECS 创建时通过 `--KeyPairName` 指定已有密钥对（需提前在阿里云控制台创建）

成功判据：3 台免密 SSH 均返回预期 OS 信息。

### 阶段 3：下发 oneinstall_v2 + 下载资源包

3.1. 本地 `D:\git\oneinstall_v2` 打 tar → scp 到 node1 → 解压到 `/egova/onekey_install/oneinstall_v2`

```bash
cd /d/git && tar czf /tmp/oneinstall_v2.tar.gz oneinstall_v2/
scp /tmp/oneinstall_v2.tar.gz root@<node1公网IP>:/tmp/
ssh root@<node1公网IP> 'mkdir -p /egova/onekey_install && cd /egova/onekey_install && tar xzf /tmp/oneinstall_v2.tar.gz'
```

3.2. 在 node1 跑 `bash /egova/onekey_install/oneinstall_v2/dl_v2.sh`，喂**按 OS 动态拼接**的 10 行输入：

```
<dl_v2_menu[0]>    # 阶段 0 选定 OS 的 dl_v2_menu 第 1 项（OS 家族）
<dl_v2_menu[1]>    # OS 子版本
<dl_v2_menu[2]>    # 架构（x86=2 / arm=1，基于实测）
<base_select>      # 模板固定 2（含 env/repo）
<script_select>    # 模板固定 1（麒舰微服务 v14-standard）
                   # 空行 = web_ver=release720
<account>          # majianquan
<password>         # Egova@123
<project>          # faq
<web_app_select>   # 模板固定 0（全选，应对 [dataflow-毕升采集] 子菜单）
```

**示例**（kylin V10 SP3 x86 → `dl_v2_menu: [3, 1, 2]`）：最终 10 行为 `3 / 1 / 2 / 2 / 1 / <空> / majianquan / Egova@123 / faq / 0`（即本次 2026-04-16 实测序列）。

若 OS 的 `verified: false`，先 ssh node1 手工跑一次 dl_v2.sh 核对菜单路径，把正确 dl_v2_menu 回写到 `os_image_map.yml` 后再进入自动化。

成功判据：`/egova/one/` 下至少 32 个 tar.gz，总大小 > 20G，每个 md5 与 ini 里声明一致。

失败处置：推钉钉 `[阶段3 下载失败]` + 具体缺包，终止流程。

### 阶段 4：资源包完整性断言（关键 gate）

**在 node1 上执行**。对每个解压后的 .sql 文件必须通过以下断言，任一失败立即推钉钉 + 终止：

```bash
ssh root@<node1公网IP> 'for f in $(find /opt/egova/db -name "*.sql"); do
  tail -5 "$f" | grep -q "^-- Dump completed" || { echo "BAD_TAIL: $f"; exit 1; }
  L=$(grep -cE "^LOCK TABLES" "$f")
  U=$(grep -cE "^UNLOCK TABLES" "$f")
  [ "$L" = "$U" ] || { echo "LOCK_UNBALANCED: $f L=$L U=$U"; exit 1; }
done && echo "SQL_ASSERT_OK"'
```

**失败场景示例**（2026-04-16 实测 cgdb.sql）：上游 mysqldump 导出 cgdb720 未跑完，LOCK 1161 / UNLOCK 1160，末尾 ALTER TABLE DISABLE KEYS 后 EOF。此时**不要尝试重下载**，直接推钉钉让麒舰侧重导源包。

### 阶段 5：渲染配置 + 推送到 node1

本地根据 3 台实际私网 IP 渲染 `hosts.yml` 与 `eurbanpro_multi_server.yml`（模板：`D:\git\oneinstall_v2\ansible\inventory\test-config\`），关键字段：
- `ip_web_uma.need_flag: 0`
- `ip_db_tdengine.hosts.master: node2`，`ip_db_tdengine_3.hosts.master: node3`（避免端口碰撞）
- TDengine3 与 PG 共置 node3 时注意 6030/5432 端口不冲突

scp 2 个 yml 到 `node1:/egova/onekey_install/oneinstall_v2/ansible/inventory/test-config/`：

```bash
scp D:/git/oneinstall_v2/ansible/inventory/test-config/hosts.yml root@<node1公网IP>:/egova/onekey_install/oneinstall_v2/ansible/inventory/test-config/
scp D:/git/oneinstall_v2/ansible/inventory/test-config/eurbanpro_multi_server.yml root@<node1公网IP>:/egova/onekey_install/oneinstall_v2/ansible/inventory/test-config/
```

### 阶段 6：执行 install.sh 菜单 0→1→2→3 + 日志跟踪

通过 SSH 在 node1 上执行 `bash /egova/onekey_install/oneinstall_v2/install.sh`，按顺序喂菜单：
- `0` 建本地 repo → 等待 `OK` 提示
- `1` 装 ansible + ntp + jdk → tail /var/log/ansible.log 直到 PLAY RECAP 出现 failed=0
- `2` 加服务器 → 验证 3 台免密 + 时钟同步
- `3` 部署应用 → 并行 `ssh root@<每台公网IP> tail -f /var/log/ansible.log`

**fatal 检测**：grep `^fatal:.*FAILED!` 且**不是** `...ignoring`（probe-then-install 模式正常）。一旦命中真 fatal：
1. 抓取该 task 的 task name + stdout + stderr
2. 推钉钉 `[阶段6 部署失败]` 含完整 fatal block
3. 暂停流程，等用户决定重试/修复

**成功判据**：最后一次 PLAY RECAP 所有 node 均 failed=0；各节点预期端口就绪（见下方 checklist）。

#### 各节点预期端口 checklist

| 节点 | 端口 |
|---|---|
| node1 | 22, 2181(kafka-zk), 8080/7777(nginx), 8848/9848/9849/7848(nacos), 9093(kafka), 30001/34761(minio) |
| node2 | 22, 3306/33060(mysql), 6380(redis), 6030/6035/6040/6041(TDengine) |
| node3 | 22, 5432(postgres), 6030(TDengine3), 其他 GIS 应用端口 |

## 钉钉推送规范

推送通过本地 curl 直接调用钉钉 webhook，内容首行必须含 `#oneinstall`：

```bash
curl -s -X POST "https://oapi.dingtalk.com/robot/send?access_token=${DINGTALK_WEBHOOK_TOKEN:-6529f41717e2d0582db6d251c94a6bca7a1196eb8a029a0e9998975c57c245fc}" \
  -H "Content-Type: application/json" \
  -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"#oneinstall ${TITLE}\n${CONTENT}\"}}"
```

触发点：

| 触发 | 标题 | 推送时机 |
|---|---|---|
| 阶段 1 失败 | 【麒舰部署 · 采购失败】 | 采购后 60s 仍无 Running 实例 |
| 阶段 2 失败 | 【麒舰部署 · 密钥分发失败】 | 任一台 ssh 免密失败 |
| 阶段 3 失败 | 【麒舰部署 · 资源下载失败】 | tar.gz 数量/大小/md5 不达标 |
| 阶段 4 失败 | 【麒舰部署 · SQL 包损坏】 | SQL 结构性断言失败（含文件名 + 计数） |
| 阶段 6 失败 | 【麒舰部署 · ansible 失败】 | ansible fatal（非 ignoring） |
| **成功** | （不推钉钉）| 在对话里回显摘要即可 |

## 已知 pitfall 档案

- **cgdb.sql 类坏包**：2026-04-16 实测 eUrbanUMA 初始化被 ERROR 1100 拦，源包本身不完整。**务必执行阶段 4 的 SQL 断言**，不要盲目信任下载成功即可用
- **dl_v2.sh display_web_app_select 菜单**：`oneinstall_v2-files-ms-eurbanpro.ini` 的 `[dataflow-毕升采集]` 键含 `-` 触发子菜单，要额外追加 `0`
- **Kylin V10 识别**：ansible 识别为 `Kylin Linux Advanced Server`，多个 role 只认 `kylin_x86`；需要在 `group_vars/all.yml` 补映射或给 role when 加别名
- **UMA tomcat 包**：麒舰栈不含，用 `ip_web_uma.need_flag=0` 跳过
- **db_init.sh 单连接 source+insert**：即使 SQL 完整，任一未配对 LOCK 都会再触发 1100，阶段 4 断言是必经 gate
- **Windows SSH 路径注意**：scp 本地路径使用 `/d/git/...` 格式（Git Bash）或 `D:/git/...` 格式，不要用反斜杠

## 完成后对话回显模板

```
麒舰部署完成 ✓
采购：i-xxx / i-yyy / i-zzz（北京h区抢占式）
公网 IP：<n1>/<n2>/<n3>  私网 IP：<p1>/<p2>/<p3>
下载：32 包总计 <N>G，SQL 断言全通过
部署：ansible failed=0，端口 checklist 全部就绪
访问入口：http://<n1>:8080
控制台账号：<...>
自动释放：<次日 23:59>
```

## 脚本清单

- `config/os_image_map.yml`：OS → 镜像 → dl_v2 菜单映射
- `config/node_roles.yml`：节点分布预设（供阶段 5 渲染引用）
