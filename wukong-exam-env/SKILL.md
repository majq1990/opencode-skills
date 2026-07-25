---
name: wukong-exam-env
description: 悟空实操考核环境一键准备。自动完成阿里云 ECS 采购（cn-wlcb 乌兰察布 / 镜像 m-0jlafwqq03tbtoerkiep「悟空实操环境-2025年5月15日」）→ SSH 免密 → 授权初始化（清脏数据/刷 license/重启服务/启动视频中心）→ 安装 mydumper 备份工具。全程仅 2 步需人工：首次配置 aliyun AK、网页获取 license 后粘贴。触发词：悟空实操环境 / 悟空考核环境 / 准备悟空实操 / wukong-exam-env / 悟空环境一键搭建。
metadata:
  version: 1.0.0
  author: majianquan
  category: cloud-infra
---

# 悟空实操考核环境一键准备 Skill

## 目的

从零采购阿里云 ECS 开始，自动完成悟空 3.0 实操考核环境的全部初始化，对应钉钉文档《悟空 3.0 认证支持》（nodeId: 93NwLYZXWygl1kevsQDq4wK4JkyEqBQm）中「准备实操环境 → 授权初始化 → 备份数据」三个章节的手工步骤。

全程在本地 Windows 执行（aliyun-cli + SSH 直连），**仅 2 步必须人工**：
1. 首次使用需配置阿里云 AK（`aliyun configure --mode AK`，一次性）
2. 获取 license 需人工登录 http://faq.egova.com.cn:7788/#/login ，拿到后粘贴给 Codex

## 关键常量

| 项目 | 值 |
|---|---|
| 地域 | cn-wlcb（华北6 乌兰察布） |
| 镜像 | m-0jlafwqq03tbtoerkiep（悟空实操环境-2025年5月15日） |
| 实例规格 | 8U32G（默认 ecs.g6.2xlarge；≤100 考生够用，>200 人建议 2 台分流） |
| 付费类型 | 包年包月 1 周（PrePaid Period=1 PeriodUnit=Week；可改按量/抢占式） |
| 带宽 | 按使用流量，峰值 100Mbps |
| 系统盘 | 默认 100G cloud_essd（>30 考生建议 200G，约每人 500M） |
| 数据库 root 密码 | eGovaZT@2023 |
| 悟空默认登录密码 | admin / eGova@2025WK |
| mydumper rpm | https://demo.egova.com.cn/MediaRoot/rpm/openeuler/22.03-lts-sp4/x86_64/mydumper-0.16.1-3.el8.x86_64.rpm |

**禁止编造标识符**：安全组/交换机 ID 必须通过 `aliyun ecs DescribeSecurityGroups` / `DescribeVSwitches` 在 cn-wlcb 下实时查询，查不到时列出候选让用户选择，不得猜测。

## 阶段 0：前置检查

| 检查项 | 命令 | 失败应对 |
|---|---|---|
| aliyun-cli 已装 | `aliyun configure list` | `winget install Alibaba.Chinese.AlibabaCloudCLI` |
| AK 已配置 | 同上 | **人工步骤 1**：引导 `aliyun configure --mode AK` |
| ssh 可用 | `ssh -V` | Windows 11 自带 OpenSSH |
| sshpass（可选） | `sshpass -V` | 镜像已内置常用秘钥，通常不需要；免密失败再装 |
| 配额充足 | `aliyun ecs DescribeAccountAttributes --RegionId cn-wlcb` | 提醒去控制台申请 |

## 阶段 1：采购 ECS（危险操作，先向用户展示摘要再执行）

```bash
# 1) 查询 cn-wlcb 下可用安全组与交换机（禁止编造 ID）
aliyun ecs DescribeSecurityGroups --RegionId cn-wlcb --output json
aliyun ecs DescribeVSwitches --RegionId cn-wlcb --output json

# 2) 创建实例（包年包月 1 周）
aliyun ecs RunInstances \
  --RegionId cn-wlcb \
  --ImageId m-0jlafwqq03tbtoerkiep \
  --InstanceType ecs.g6.2xlarge \
  --VSwitchId <查询得到> \
  --SecurityGroupId <查询得到> \
  --SystemDisk.Category cloud_essd \
  --SystemDisk.Size 100 \
  --InternetMaxBandwidthOut 100 \
  --InternetChargeType PayByTraffic \
  --InstanceChargeType PrePaid \
  --Period 1 --PeriodUnit Week \
  --Amount 1 \
  --InstanceName wukong-exam-env

# 3) 轮询 Running 并取公网 IP
aliyun ecs DescribeInstances --RegionId cn-wlcb --InstanceIds '["<id>"]' \
  --waiter expr='Instances.Instance[0].Status' to=Running timeout=300 interval=10
```

成功判据：Status=Running 且拿到公网 IP。

## 阶段 2：SSH 免密

镜像已禁用密码登录且内置常用公钥，先试免密：
```bash
ssh -o ConnectTimeout=10 root@<公网IP> 'uname -a'
```
失败则提示用户核对本地私钥是否在镜像内置清单，或走自定义秘钥重新分发。

## 阶段 3：授权初始化

3.1 清脏数据 + 取数据库标识（全自动）：
```bash
ssh root@<公网IP> 'mysql_pass="eGovaZT@2023"
mysql -uroot -p"${mysql_pass}" -A << "EOF"
delete from wukong.wukong_page where creator not in ("admin");
delete from wukong.wukong_project where creator not in ("admin");
delete from wukong.com_user where username not in ("admin");
EOF
mysql -uroot -p"${mysql_pass}" -A -e "SELECT SUBSTR(UUID(), 25) FROM DUAL;"'
```

3.2 **人工步骤 2（唯一阻塞点）**：把上一步输出的数据库标识发给用户，请其登录
http://faq.egova.com.cn:7788/#/login 申请 license（参考：http://faq.egova.com.cn:7777/projects/redmine/wiki/悟空license授权说明），
拿到 license 字符串后粘贴回来。**拿到前不要继续。**

3.3 刷 license + 重启服务（全自动）：
```bash
ssh root@<公网IP> 'mysql_pass="eGovaZT@2023"; license="<用户粘贴的license>"
mysql -uroot -p"${mysql_pass}" -A -e "update wukong.com_license set content='"'"'${license}'"'"';"
mysql -uroot -p"${mysql_pass}" -A -e "update data_exchange.com_license set content='"'"'${license}'"'"';"
systemctl restart dex wukong wuneng
cd /egova/apps/ai/video/server && bash startZtserver.sh
cd /egova/apps/ai/video/mediaserverinfo && bash serverinfo-start.sh
cd /egova/apps/ai/video/mediaserver && bash start-ZT-mediaserver.sh
systemctl restart videocenter'
```

3.4 验证（服务重启约需 5 分钟，用 waiter 轮询而非干等）：
```bash
ssh root@<公网IP> 'for i in $(seq 1 30); do
  out=$(curl -s http://127.0.0.1:8080/wukong-api/free/license/info) && [ -n "$out" ] && echo "$out" && break
  sleep 20
done'
echo "http://<公网IP>:8080/wukong/index.html"
```
成功判据：license/info 返回 validFromDate/validToDate 且未过期。

## 阶段 4：安装 mydumper（备份依赖）

```bash
ssh root@<公网IP> 'rpm -q mydumper || rpm -ivh https://demo.egova.com.cn/MediaRoot/rpm/openeuler/22.03-lts-sp4/x86_64/mydumper-0.16.1-3.el8.x86_64.rpm
mydumper --version'
```
成功判据：mydumper --version 正常输出版本号。

## 完成后回显模板

```
悟空实操环境就绪 ✓
实例：<InstanceId>（cn-wlcb 包年包月 1 周，到期 <日期>）
公网 IP：<ip>
悟空：http://<ip>:8080/wukong/index.html      admin / eGova@2025WK
管理后台：http://<ip>:8080/wukong-admin/#/login
星桥：http://<ip>:8080/dex/index.html         admin / 123456
视频中心：http://<ip>:8080/videocenter/index.html   admin / eGova@Spzxai1
授权有效期：<validFromDate> ~ <validToDate>
mydumper：<version>（备份/还原命令见钉钉文档「备份数据」章节）
```

## 善后提醒（回显后必须主动告知）

1. **GIS 验证**：实操用公司 GIS 服务 http://47.94.232.253:8082/eUrbanGIS 不稳定，考前务必验证，不可用找 GIS 研发
2. **磁盘**：>30 考生建议扩容；阿里云扩容后需 parted + resize2fs 调整分区
3. **人数**：>200 考生建议再采购一台分流（重复本 skill 即可）
4. **新增考生账号**：用改造后的「自动生成悟空用户导入语句.py」，从钉钉导出的名单 Excel/CSV 读姓名+工号生成批量插入 SQL
5. **到期释放**：包年包月到期前如需保留数据，先执行 mydumper 备份再释放实例

## 已知 pitfall

- cn-wlcb 的安全组/交换机与 cn-beijing 不通用，文档旧安全组 sg-2ze* 均为北京资源，**必须实时查询 cn-wlcb 下的**
- 镜像禁用密码登录，不要尝试 sshpass + 密码，密钥不通就先排查密钥
- license 未生效就重启业务会导致授权接口查不到，先刷 license 再重启
- 视频中心 3 个启动脚本有先后关系，按阶段 3.3 顺序执行，systemctl restart videocenter 收尾
