# build-pipeline-controller

按需起一台阿里云 ECS（用打包专用自定义镜像 `build-host-v1`）跑打包，跑完释放。

## 用法

```bash
pack openresty                                    # 最新版 × 全部 OS × 全部版本
pack openresty 1.29.2.3                           # 指定版本
pack openresty --os ubuntu                        # 仅 ubuntu 全版本
pack openresty 1.29.2.3 --os centos --osver 7     # 一对一精确
pack nginx --os centos,openeuler --osver 7,24.03-lts
pack openresty --keep                             # 跑完不释放（调试用）
pack openresty --no-spot                          # 用按量付费而非抢占式
```

## 架构

```
本地 controller (Python)
   ├─ ① 解析参数 + 决议 targets
   ├─ ② RunInstances（基于 build-host-v1 自定义镜像，抢占式）
   ├─ ③ 等 SSH 就绪（轮询 22 端口）
   ├─ ④ 同步 recipe + 执行 /opt/build-pipeline/scripts/build.sh
   ├─ ⑤ scp 拉 /opt/build-pipeline/repo/ 到本地
   └─ ⑥ 释放 ECS（除非 --keep）
```

## 关键参数（基于 8.145 模板）

| 项 | 值 | 备注 |
|---|---|---|
| Region | cn-wulanchabu | 8.145 所在 region |
| Zone | cn-wulanchabu-c |  |
| InstanceType | ecs.e-c1m4.xlarge | 4 vCPU / 16 GB |
| ImageId | `m-...`（自定义镜像 build-host-v1） | 待生成 |
| Charge | PostPaid + SpotAsPriceGo | 抢占式，省 70%+ |
| Disk | cloud_essd 50 GB |  |
| KeyPair | mjqegova-ed25519 | 本地 ~/.ssh/mjqegova-ed25519 |
| VPC/VSwitch/SG | 沿用 8.145 配置 |  |

## 文件结构

```
build-pipeline-controller/
├── pack.py                CLI 入口
├── controller/
│   ├── __init__.py
│   ├── ecs.py             ECS 生命周期管理
│   ├── ssh.py             SSH 客户端（paramiko）
│   ├── targets.py         targets 决议（OS family/version → -pkg image）
│   ├── recipe.py          recipe 同步（如果本地有更新）
│   └── config.py          常量配置
├── recipes/               与服务器 /opt/build-pipeline/recipes 同步源
└── output/                打包产物落地
```

## 已知 issue

- Anolis 8.8-pkg：rpm DB bdb_ro 模式问题，已通过重建镜像 + chmod rpm DB 修复
- CentOS 6/7 需要源码嵌入 OpenSSL 1.1.1w（recipe.sh 已处理）
- Ubuntu 18.04 archive 已迁，需走 mirrors.aliyun.com（bootstrap 已处理）
- Kylin / UOS 商业 OS 的 repo 需要 license，build 阶段如缺包要自带源码或第三方源
