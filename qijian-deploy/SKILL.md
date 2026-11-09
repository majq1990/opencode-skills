---
name: qijian-deploy
version: 1.2.0
description: 麒舰（eurbanpro）微服务栈一键自动化部署技能。从阿里云 ECS 抢占式采购（cn-beijing-h / ecs.e-c1m4.2xlarge）到 oneinstall_v2 install.sh 菜单 0/1/2/3 全流程自动化，支持银河麒麟 V10 SP2/SP3/V11、openEuler 22.03/24.03、UOS 20-1060a/1060e/1070a、CentOS 7.9 等多种 OS（x86 与 aarch64），根据用户指定的操作系统自动选择镜像 ID 与 dl_v2.sh 菜单路径；节点分布支持 2/3/5 节点预设加动态规划。用户说"部署一套麒舰"、"采购麒舰部署机"、"跑一遍 oneinstall_v2"、"麒舰考核环境准备"、"部署麒舰 kylin V10 SP3"、"用欧拉 22.03 跑麒舰"、"/qijian-deploy" 等任一表述时必须激活本技能。部署异常自动推送钉钉 #oneinstall 告警，成功后在对话回显摘要。
---

# 麒舰微服务栈一键部署 Skill

> **版本**：v1.2.0（2026-11-06：全自动模式 + 乌兰察布 C 区 + 菜单/坑位修正）
> **最近一次成功部署**：2026-11-06（乌兰察布 C 区，麒麟 V10 SP3 x86，3 节点 8U32G；入口 `/eurbanpro/index.html` HTTP 200）
> **注意**：本 skill 用于麒舰考核/测试环境快速搭建。生产环境部署走独立流程。

## 目的

从零采购阿里云 ECS 开始，自动完成麒舰（eurbanpro）微服务栈分布式部署。全程在本地 Windows 环境执行（aliyun-cli 本地调用，SSH 直连 ECS 节点），不经过跳板机。

## 工具依赖检查

| 工具 | 用途 | 检查命令 | 安装方式 |
|---|---|---|---|
| aliyun-cli | 阿里云 API 调用 | `aliyun configure list` | `winget install Alibaba.Chinese.A AlibabaCloudCLI` |
| jq | JSON 解析 | `jq --version` | `winget install jqlang.jq` |
| yq | install.sh 菜单/配置读写（**主控机必需，缺了菜单都起不来**） | `yq --version` | GitHub `mikefarah/yq` releases 下 `yq_linux_amd64` 放 `src/bin/yq`（官方查找路径）或系统 PATH；yum/apt 无此包 |
| sshpass | 密码方式 SSH 免密分发（Git Bash 下不可用，用 python paramiko 替代） | `sshpass -V` | MSYS2: `pacman -S sshpass`；或 paramiko |
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
| 阿里云区域 / 可用区 | cn-beijing / cn-beijing-h（乌兰察布备选：cn-wulanchabu / cn-wulanchabu-c，VPC vpc-0jl32yi9rx5ovum932wnz，vsw-0jlfj7todyuefm058cws1）|
| VPC / 交换机 | vpc-2ze5yg4iioqg6p8be1abs / vsw-2ze6dmyu5gjp9p9oes7qa |
| 实例规格 | ecs.e-c1m4.2xlarge (8U32G) |
| 付费模式 | SpotAsPriceGo 抢占式 |
| 节点数量 | 默认 3（可变） |
| 系统盘 | 80G cloud_essd（**采购规范 2026-11-06：不挂数据盘，容量需求直接扩系统盘**）|
| 安全组 | sg-2ze1pookadxppb0kx9q2（同 VPC，ALL -1/-1 src=10.0.0.0/8）|
| root 密码 | Egova@123 |
| SSH 密钥 | 本地 `~/.ssh/id_rsa`（阶段 2 分发到 ECS 节点）|
| oneinstall_v2 源 | 本地 `D:\git\oneinstall_v2` |
| 麒舰版本 | release720 |
| 项目代号 | faq |
| 包下载账号 | majianquan / Egova@123 |
| License 服务 | 乌兰察布统一 `172.21.133.146:11113`（填 `egova_license_url`，无 http:// 前缀）|

> ⚠️ **root 密码 Egova@123 是出厂默认，生产环境完毕必须立即改密。**

## SSH 密钥说明

- 本机密钥：`~/.ssh/id_rsa`（RSA）或 `~/.ssh/mjqegova-ed25519`（ed25519，较新部署用）
- 阶段 2 通过 sshpass 将本地公钥分发到 ECS 节点
- qijian 集群内节点间 SSH 走内网，同 VPC SG 内互通无需额外配置

## 全自动模式（推荐，2026-11-06 实战固化）

`scripts/auto_deploy.sh` 覆盖「采购 → 公共访问 → 拉包 → 渲染配置 → install.sh 0→1→2→3 → 验收」全流程，无人值守，失败自动推钉钉：

```bash
cd ~/.agents/skills/qijian-deploy/scripts
bash auto_deploy.sh                        # 默认：乌兰察布 C 区 / 系统盘 200G / 3 节点 / faq
bash auto_deploy.sh --region cn-beijing --zone cn-beijing-h   # 换北京
bash auto_deploy.sh --disk 100 --nodes 3                       # 改系统盘大小
```

内置能力（今天踩过的坑全部自动处理）：
- 采购只传 `--SystemDisk`（**规范：不挂数据盘**，容量靠系统盘扩容）
- 公钥分发 + node1→其余节点内网免密自检
- 服务器端 `setup_node1.sh`：解压 oneinstall → GitHub 拉 yq 双落位（src/bin + PATH）→ `mkdir /etc/systemd/system.conf.d` → 后台 dl_v2（正确菜单序列 `3/1/1/2/2/空/账号/密码/项目/0`；**第 4 位 base_select 必须是 2**，第 3 位是架构 1=x86）
- 等待拉包完成（≥27 包断言）
- `render.sh`（服务器端 yq）：hosts.yml 三私网 IP、`eurbanpro_multi_server.yml` 按 3-node-standard 预填 master、`all.yml` 写 `outlet_nginx_ip=P1` 与 **固定 license `172.21.133.146:11113`**、metadata service 段 null→`{}`（outlet_nginx NoneType 坑）
- install.sh 四步后台化（输入文件 + rc 轮询 + 超时），step3 序列含灵珑 y
- 验收：`/eurbanpro/index.html` HTTP 码 + 三节点端口 checklist（curl telnet 探测）
- 产物：`D:\opencode\file\<当天>\auto-deploy.log`、`instances.txt`、`SUMMARY.md`

#### 应用部署（install 3）的全自动通道（2026-11-08 实战定型）

**install 3 的依赖配置交互是工具设计内的人工决策环节**（55 个微服务 × 各自依赖清单），静态输入序列写不全（实测 4 轮失败）。定型方案 = 三阶段压缩：

1. **CLI 预装支持软件**：工具箱自带跳菜单入口 `echo y | ./i_software.sh <type> <host_name>`（在 `shell/tools/` 下；host 传 hosts.yml 主机名 node1/2/3；唯一交互=show_params 的 `y`）。按渲染分配装：mysql@P1、redis@P1+@P3、nacos@P1、TDengine@P1、TDengine3@P2、zookeeper@P3、kafka@P3、postgresql@P1。**外层 RC 不可信**（工具箱不传 ansible 失败码），判定看 `f4_<type>_<host>.log` 的 `failed=1` 与 metadata 实例。
2. **yq 预填依赖**：装完后动态读 metadata 实例 key（`yq '.mysql | keys | .[0]'` 等），给每个微服务 `.microservice.<app>.<app>_N.depends[i].depend_key` 预填——把逐项人工选实例压成脚本写入。type→实例映射：mysql→mysql_1、redis→node1 实例、usercenter_redis→node3 redis 实例、其余同名单实例；microservice 类型依赖指 `<sub_type>_1`。
3. **y 冗余触发**：依赖预填后所有决策点 y 可答，`printf '3\n2\n1\n'` + 40 个 `y\n`（2 秒间隔）触发部署。

**包缺口侦破法**（dl_v2 清单之外的包）：oneops 源站 nginx 开目录浏览，`curl --header "$AUTH" http://oneops.egova.com.cn:8093/one/v2/` 逐层 `grep href`。已知特殊位置：
- lua-resty-egova.tar.gz → `/one/v2/tools-script/oneinstall_v2/src/bin/tools/`（nacos playbook 硬依赖，缺失时 nacos failed=1）
- env-common-bin-x86 → `/one/v2/` 根目录（无 kylinV10_x86 前缀）
- **zookeeper/kafka 主 tgz 在全部 ini 与源站目录均不存在**（2026-11-08 实测）——周五部署的来源待查，遇到缺失先找项目经理确认内网源位置

依赖：`aliyun-cli`、`python` + `paramiko`（Windows 无 sshpass）、本地 `~/.ssh/id_rsa`、`D:\git\oneinstall_v2`。

> 已知边界：`install.sh step2（加服务器）`自动喂 `2\nq`（hosts 已预填 + 免密已配时等价跳过）；若上游改版导致交互变化，看 `/egova/install_step<N>.log` 修正输入序列。

---

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
2. 在 node1 跑 `bash dl_v2.sh`（官方下载脚本，断点续传），喂 10 行输入（2026-11-08 源码级确认的菜单顺序）：
   ```
   3                  # ① OS 家族：3=银河麒麟
   1                  # ② 版本（1=V14 智信云标准）
   1                  # ③ CPU 架构：1=x86 / 2=arm  ⚠️ 麒舰 x86 选 1
   2                  # ④ base_select —— ⚠️ 必须选 2！
   2                  # ⑤ script_select：INSTALL_FILE_ARRAY[1]=ms-eurbanpro（麒舰微服务清单）
                      # 空行 = web_ver 默认 release720
   majianquan         # ⑥ account
   Egova@123          # ⑦ password
   faq                # ⑧ project
   0                  # ⑨ web_app_select（全选）
   ```

> ⚠️ **参数位血泪教训（2026-11-08 两次踩坑）**：
> ① 菜单顺序是 OS→版本→**架构**→base→script（源码 display_os_version→CPU 架构→display_base_type），
> 架构位和 base 位极易搞混：架构 1=x86/2=arm，填 2 会整晚下载 arm 包。
> ② base_select 选 1 只拉 base.ini（不含 env 组），导致 `env-tools-script`（lua-resty-egova，
> nacos 硬依赖）、`env-security-toolbox`、**`env-common-bin`（zookeeper_3.9.3.tgz 与
> kafka_2.12-3.6.0.tgz 的家，532MB）** 三包缺失——部署时 zookeeper/kafka/nacos 全部 failed=1。
> 这些包聚合在 env-common-bin 里，按 zookeeper 文件名在源站搜不到。选 2 拉 base+env-base 全量 6 包。
> 重跑 dl_v2.sh 已有包 wget -c 秒过，补选代价小。

成功判据：`/root`（或下载目录）下 ≥35 个 tar.gz，且**必须含**：
`oneinstall_v2-env-common-bin.tar.gz`、`oneinstall_v2-env-tools-script.tar.gz`、`oneinstall_v2-env-security-toolbox.tar.gz` 三个 env 组包；总大小 > 20G。

### 阶段 4：资源包完整性断言（关键 gate）

在 node1 上执行 SQL 文件结构性断言（LOCK/UNLOCK 配对、`-- Dump completed` 尾部检查）。

> ⚠️ cgdb.sql 坏包历史：上游 mysqldump 导出不完整时 LOCK/UNLOCK 数量不等。**不要尝试重下载**，直接推钉钉让麒舰侧重导源包。

#### 坏包重下规则（2026-11-08 实战）

- **env-common-bin-x86 的正确 URL 无 `kylinV10_x86/` 前缀**：`/one/v2/oneinstall_v2-env-common-bin-x86.tar.gz`（根目录，其余 env-repo/env-bin 等在 `kylinV10_x86/` 下）。按错误前缀下到的是 404 页面。
- **677M 大包需要 15-20 分钟**（源站到乌兰察布实测 7-10 MB/s）——`timeout 600` 必败（下到 329M 被 kill → unexpected end of file）。
- **wget 坏包修复公式：先删文件再 `wget -c`**。`rm -f dest && wget -c -t 20 -T 30 URL -O dest`：删除保证从零（不接坏前端），`-c` 保证会话内断连续传（不重头）；`-T 30` 断连自动重连，`-t 20` 重试上限。裸 `-c` 续传坏前端 = 把坏尾巴永远带着；无 `-c` 重试 = 每次断连从头。
- **gzip -t 校验是唯一可信断言**，文件大小接近不代表完整。

> ⚠️ **sshd 挂死**：对同一实例大量 paramiko 并发连接后，sshd 停止响应 banner（间歇 "Error reading SSH protocol banner" / WinError 10054）。重试无法恢复时，用 `aliyun ecs RebootInstance` 重置（实例 /root 数据保留）。

### 阶段 5：渲染配置 + 推送到 node1

根据 3 台实际私网 IP 渲染 `hosts.yml` 与 `eurbanpro_multi_server.yml`：
- `ip_web_uma.need_flag: 0`（UMA tomcat 包不在麒舰栈）
- TDengine v2 与 TDengine3 永不共置（6030 端口冲突）
- mysql 主库所在节点不跑 nacos / eurbanpro 等高负载微服务

> ⚠️ `hosts.yml` 字段名用 `ansible_ssh_host`（不是 `ansible_host`）；node1 自身公钥需加入自身 `authorized_keys`。

### 阶段 6：执行 install.sh 菜单 0→1→2→3

- `0` 建本地 repo → **必须再输入 yum 源端口**（如 `0\n7777\n`）：端口缺输入时菜单死循环追问（实测刷屏 26 万次直到 timeout）；端口被占用时菜单提示"已在使用，请更换其他端口"，换一个空闲端口重试
- `1` 装 ansible + ntp + jdk → tail /var/log/ansible.log 直到 PLAY RECAP 出现 failed=0
- `2` 加服务器 → **子菜单是 `0`(添加并执行免密)/`a`(rds)/`1`(删除)**：输入必须是 `2\n0\n`；喂 `q` 会"输入错误"后**核心转储**。完成后独立验证免密（`ssh root@P2 hostname`），不依赖 install rc
- `3` 部署应用 → 周五实测序列 `3\n2\n1\ny\ny\ny\n` → 并行 tail -f /var/log/ansible.log
- **判定纪律**：install.sh 菜单 read EOF 会死循环（rc=124 timeout 属预期），步骤成败看产物日志与独立验证，不看 rc

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
10. **dl_v2 菜单漂移（2026-11-06 实测）**：服务类型 **1=V14 智信云标准、2=麒舰平台微服务**（选 1 下错成 V14 包集 15G）；架构 **1=x86 / 2=arm**；麒舰不弹版本菜单直接默认 release720。以 os_image_map.yml（已修正）为准
11. **麒麟 V10 SP3 镜像缺 `/etc/systemd/system.conf.d`**（部分节点有部分没有）：common 角色「systemd 句柄 drop-in」task 直接 failed=1，连锁 **redis 安装失败、部署退出码 1**。部署前在三台 `mkdir -p /etc/systemd/system.conf.d`
12. **metadata.yml service 段 null → outlet_nginx 失败**：未部署的 service 型应用（eUrbanMIS/eUrbanMF/eUrbanSG/eGovaPublic/IMserver/statgather）写成 null，outlet_nginx 角色 `| default({})` 挡不住 None → `NoneType has no len()`，出口 nginx 路由不生成。修复：python3 把 service 段 null → `{}` 后重跑（续装）
13. **麒舰默认必须部署 m2（运管服）**：不是可选项（2026-11-06 用户确认）
14. **license 统一地址（乌兰察布）**：`egova_license_url: "172.21.133.146:11113"`（host:port 无 http:// 前缀），所有乌兰察布环境通用
15. **dl_v2 下载包自动解压**：env-repo / env-bin / web 包后续命令自动解压落位 `src/{bin,repo,web}`，无需手工 tar；step 0 成功判据 = `/egova/opt/repo/<os>` 建好 + `/etc/yum.repos.d/egova-oneinstall-local.repo` 存在

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

- `scripts/auto_deploy.sh`：**全自动主脚本**（采购→部署→验收，无人值守）
- `scripts/rrun.py`：paramiko 远程执行/传文件（Windows 无 sshpass 的替代，auto_deploy.sh 依赖）
- `scripts/push_dingtalk.sh`：钉钉推送
- `config/os_image_map.yml`：OS → 镜像 → dl_v2 菜单映射（2026-11-06 已修正 arch/服务类型）
- `config/node_roles.yml`：节点分布预设（auto_deploy.sh 的 svc_map 与之对应）


---

<!-- feedback-channel v1 -->
## 反馈渠道

本技能已纳入企业反馈监控。使用中如遇「连续多轮仍未解决同一类问题」、「工具执行报错」，或你想主动反馈：

- 在装有 feedback-monitor 插件的 agent（opencode / Claude Code / 腾讯 WorkBuddy）中，会自动采集并（脱敏后）上报到企业反馈平台；
- 也可随时在 **skills-manager 应用 →「反馈 / 建议」** 手动提交，会自动记录关联技能与提交人。
