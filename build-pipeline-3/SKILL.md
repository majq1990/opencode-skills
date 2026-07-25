---
name: build-pipeline
version: 1.0.1
description: 跨 OS 自动打包 RPM/DEB。用户说"打包 X"、"build X"、"给 X 出包"、"做 X 的 rpm"、"pack X for Y"等需要把某个软件打成 .rpm/.deb 跨多个 Linux 发行版分发时使用。覆盖 6 大 OS 家族（CentOS、openEuler、Anolis、Ubuntu、Kylin、UOS）共 31 个 OS 版本。流程：本地 controller 起阿里云抢占式 ECS（用专用打包镜像 build-host-v1）→ 跑 build pipeline → 自动上传 182.92.5.151 → 释放 ECS。
author: majianquan
category: support-dept
visibility: support-dept
---

# build-pipeline — 跨 OS 自动打包

按需起一台阿里云抢占式 ECS（用今天做的自定义镜像 `build-host-v1`），跑完打包自动释放，产物自动上传到 `182.92.5.151:/egova/MediaRoot/rpm/<os>/<ver>/<arch>/`。

## 前置依赖（首次使用必读）

> 部门内共用一套阿里云资源（账号、VPC、vSwitch、SG、KeyPair、自定义镜像、上传 repo），`controller/config.py` 里所有 ID 都是部门共享值，**不要改**。每个同事只需要在自己电脑上做下面 3 件事即可。

### 1. 本地工具

| 工具 | 安装 | 验证 |
|---|---|---|
| **aliyun-cli** | `winget install Alibaba.AliyunCLI` 或从 https://github.com/aliyun/aliyun-cli/releases 下二进制 | `aliyun version` |
| **OpenSSH 客户端** | Windows 11 自带 | `ssh -V` |
| **Python 3.9+** | 自带或 winget | `python --version` |

### 2. 阿里云 RAM 子账号认证（aliyun-cli profile）

controller 通过 `subprocess.run(["aliyun", "ecs", ...])` 调阿里云 OpenAPI，**不读环境变量、不读 SDK config**，完全依赖本机 `aliyun-cli` 自己的 default profile：

```bash
aliyun configure --profile default
# 依次填：AccessKeyId / AccessKeySecret / Region(cn-wulanchabu) / Output(json)
```

AK/SK 用部门给你的 RAM 子账号；最小权限 ECS `RunInstances` / `DescribeInstances` / `DeleteInstance`，简单点直接挂 `AliyunECSFullAccess`。

### 3. KeyPair 私钥落地

部门共用 KeyPair 名 `mjqegova-ed25519`（已挂在 ECS 控制台）。私钥文件向作者要一份，放到：

```
~/.ssh/mjqegova-ed25519        # 私钥本体
chmod 600 ~/.ssh/mjqegova-ed25519
```

私钥路径已经写死在 `controller/config.py` 的 `SSH_KEY_PATH`，**保持默认即可**。

### 4. 钉钉机器人（无需配置）

build.sh 里硬编码的是部门 egova 群机器人 webhook（关键字 `egova`），打包完成会自动推送进群，开箱即用。

---

## 触发

用户说出以下意图时调用：
- "打包 openresty / nginx / redis / xxx"
- "build XX for centos/ubuntu/openeuler"
- "给麒麟 V10 出 redis 的包"
- "pack <软件> [<版本>] [--os <家族>] [--osver <版本>]"

## 用法

```bash
# 默认：最新版 × 全部 OS × 全部版本
pack openresty

# 指定版本
pack openresty 1.29.2.3

# 指定 OS 家族（多个用逗号）
pack redis --os openeuler,uos,kylin

# 指定 OS 版本
pack redis --os centos --osver 7
pack openresty --os ubuntu --osver 22.04,24.04

# 调试用：跑完不释放 ECS
pack openresty --keep
```

## 默认值规则

| 参数缺省 | 行为 |
|---|---|
| version | 调每个 recipe 的 latest 解析（openresty: 抓 download.html；redis: GitHub releases）|
| --os | 全部 6 家：centos / openeuler / anolis / ubuntu / kylin / uos |
| --osver | 该家族下所有版本（共 31 个 -pkg 镜像）|

## 输出

1. **本地 `./output/`**：scp 拉回的 .rpm / .deb，按 `<distro_tag>/<package>` 组织
2. **182.92.5.151**：scp 上传到 `/egova/MediaRoot/rpm/<os>/<ver>/<arch>/`
3. **下载 URL**：`http://182.92.5.151:38081/MediaRoot/rpm/<os>/<ver>/<arch>/<package>`（nginx root 是 `/egova`）
4. **打包完成自动给出完整下载 URL 清单**：build.sh 和 controller 都会在最后输出"下载 URL 清单"，每行一个 URL，方便复制分发
5. **自动写入钉钉表格**：打包完成后自动将记录写入钉钉在线表格，包含以下字段：
   - 软件名称
   - 版本
   - 操作系统
   - 系统版本
   - 下载路径
   - 安装依赖清单

   钉钉表格地址：https://alidocs.dingtalk.com/i/nodes/2Amq4vjg89gq7LzDsPB9boynV3kdP0wQ

## 关键资源

- **ECS 自定义镜像**（双架构）：
  - x86_64：`m-0jl856ue5sjer9s2rpaw` (build-host-v1, cn-wulanchabu) - 含 31 个 -pkg 镜像
  - aarch64：`m-0jl4qlwteu7cv53a014v` (build-host-arm64-v3, cn-wulanchabu) - 含 21 个 -pkg 镜像（信创全套：openeuler 7 + anolis 7×全部 + kylin 4 + uos 3）+ recipe wget→curl 修复 + dnf sqlite backend fix
- **实例规格**：
  - x86：`ecs.e-c1m4.xlarge` (4C16G), 抢占式, ¥0.05-0.15/小时
  - arm：`ecs.c8y.xlarge` (4C8G), 抢占式, ¥0.05-0.22/小时
- **VPC/SG/Key**：沿用 8.145 模板
- **Build pipeline**：`/opt/build-pipeline/scripts/build.sh`
- **Bootstrap 脚本**：`/opt/build-bootstrap/bootstrap.sh`
- **Recipes**：`/opt/build-pipeline/recipes/<sw>/<ver>/{recipe.sh,targets.list,meta.yaml}`

## 钉钉推送（自动）

build.sh 跑完会自动 POST 钉钉机器人（关键字 `egova`），webhook：
`https://oapi.dingtalk.com/robot/send?access_token=abba9910309cc78b4dcfe5dea9c4ab90a601a0dfefb7c9087662a306c57be4ae`

推送内容含：软件名+版本+arch、OK/FAIL 数量、完整下载 URL 清单。

## 钉钉表格记录（自动）

打包完成后，controller 会自动将打包记录写入钉钉在线表格，便于追踪和管理。

### 表格字段

| 字段 | 说明 |
|---|---|
| 软件名称 | 打包的软件名（如 openresty、redis） |
| 版本 | 软件版本号 |
| 操作系统 | OS 家族（centos、ubuntu、openeuler、anolis、kylin、uos） |
| 系统版本 | OS 版本号（如 7、22.04、24.03-lts） |
| 下载路径 | 完整的 HTTP 下载 URL |
| 安装依赖清单 | 运行时依赖（从 meta.yaml 的 runtime_depends 读取） |

### 表格地址

https://alidocs.dingtalk.com/i/nodes/2Amq4vjg89gq7LzDsPB9boynV3kdP0wQ

### 实现细节

- 数据收集：`controller/dingtalk.py` 的 `collect_build_records()` 函数
- 依赖信息：从 `recipes/<software>/<version>/meta.yaml` 的 `runtime_depends` 字段读取
- 写入方式：通过 `dws` CLI 调用钉钉表格 API
- 写入时机：在打包完成、产物上传成功后自动执行

## 添加新软件

在 `recipes/<software>/<version>/` 下放 3 个文件：

| 文件 | 内容 |
|---|---|
| `recipe.sh` | `build` 阶段（装依赖+编译+make install 到 staging）+ `package` 阶段（fpm 打 rpm/deb） |
| `targets.list` | 每行一个 `-pkg` 镜像名，# 注释，空行跳过 |
| `meta.yaml` | name/version/description/license/maintainer 等元信息 |

## 添加同事 SSH 公钥（新成员加入）

部门新人要能 ssh 进 build host 调试（`pack --keep` 场景），把 ta 的公钥追加到自定义镜像的 `/root/.ssh/authorized_keys` 里：

```bash
# 默认 x86 + arm 两套都注入
python inject_pubkey.py ~/.ssh/liaokun.pub ~/.ssh/yaofeng.pub

# 只处理某一架构
python inject_pubkey.py ~/.ssh/foo.pub --arch x86_64

# 只造新镜像不替换 config.py（演练）
python inject_pubkey.py ~/.ssh/foo.pub --dry-run
```

**流程（每个 arch 独立）**：起源镜像 ECS → ssh append 去重 → `CreateImage` 拍照 → 用新 ImageId 起验证 ECS → 跑 `recipes/hello-noop/0.1.0` 单 target 烟雾测试（< 30s）→ 通过则 in-place 改 `controller/config.py`（先备份 `.bak.<ts>`）→ 终止两台实例。

**安全约束（不要绕开）**：
- 任一步骤失败立即 abort，旧 IMAGE_ID 保留不动
- **新镜像 commit 后不会自动删旧镜像**：脚本只改 `config.py` 指向新 ImageId，旧 ImageId 保留。等部门同事日常打包验证一两次确认没问题后，单独跑：
  ```bash
  python inject_pubkey.py --delete-old m-0jl856ue5sjer9s2rpaw
  ```
  脚本会拒绝删 config.py 当前在用的 ID，并要求二次手输 ImageId 确认。

**钉钉通知**：成功后通过 dws 调钉钉机器人推送（关键字 `egova`），操作者身份从 `dws contact user get-self` 拿，包含：操作者真名、新增公钥文件名、各 arch 新旧 ImageId、删旧镜像的回滚提示命令。

**hello-noop recipe（验证专用）**：在 `recipes/hello-noop/0.1.0/`，零网络依赖、零编译，只 fpm 一个 1 行 shell 脚本，仅供 inject_pubkey 验证用，**不要拿来上传 repo**。

## 已知 issue

- **Anolis 8.6/8.8 -pkg rpm bdb_ro 损坏**：commit 后 BerkeleyDB env 状态丢失，dnf 写操作 EPERM。已用 anolis 23.x 替代。x86 + arm 都复现。
- **CentOS 6/7**：OpenSSL 1.0.2 太老，需要 recipe 嵌入 OpenSSL 1.1.1w 静态编译。
- **Kylin/UOS 商业 OS**：repo 需要 license，第三方包不全；编译期依赖如缺需要源码自带或第三方源。
- **arm UOS v20-1050/1060** redis 编译 set-e 早退（依赖装好后 11s/130s FAIL）：根因待查，v20-1070 OK 可作 UOS 系代表。
- **docker.xuanyuan.me 偶发 429 限流**：anolis 7.9 arm pull 时遇到。重试或换 daocloud 镜像。
- **fpm `--architecture` 必须用 `$(uname -m)` 动态值**：写死 x86_64 在 arm 镜像里输出错文件名。recipe.sh 已修。
- **OSS ossfs `mv`/`ls` 偶发 EPERM**：cp 部分成功 + delete 失败 → 残留 .x86_64.rpm 旧文件。HTTP 200 是真理，下载验证为准。

## 架构 routing

controller 启 ECS 时，根据 `--arch` 参数（默认 x86_64）选 ImageId + InstanceType：
| arch | ImageId | InstanceType |
|---|---|---|
| x86_64 | m-0jl856ue5sjer9s2rpaw | ecs.e-c1m4.xlarge |
| aarch64 | m-0jlhzb9zkuvwjvelwl3c | ecs.c8y.xlarge |

OS 镜像支持双架构（docker pull 自动选 manifest），arm 镜像里 -pkg 目前仅 openeuler:24.03-lts、kylin:v10-sp2、uos:v20-1070。要扩展 arm 覆盖只需起 arm 实例 + 跑 bootstrap.sh 改造对应 OS + commit 新镜像。

## 后续规划

- arm 镜像扩展：让 arm build-host 也覆盖 31 OS 全集（当前仅 3 个）
- 包仓库地址变更：替换 scripts/build.sh 里 UPLOAD_HOST


---

<!-- feedback-channel v1 -->
## 反馈渠道

本技能已纳入企业反馈监控。使用中如遇「连续多轮仍未解决同一类问题」、「工具执行报错」，或你想主动反馈：

- 在装有 feedback-monitor 插件的 agent（opencode / Claude Code / 腾讯 WorkBuddy）中，会自动采集并（脱敏后）上报到企业反馈平台；
- 也可随时在 **skills-manager 应用 →「反馈 / 建议」** 手动提交，会自动记录关联技能与提交人。
