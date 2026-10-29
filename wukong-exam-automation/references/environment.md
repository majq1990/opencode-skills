# 悟空考核环境生命周期

> 2026-10-28 实测修订：原文档里的 `cn-wlcb` 不被 aliyun CLI 识别，正确 RegionId 是 **`cn-wulanchabu`**；新增代理、SSH 注入、CLI 编码、余额、license 等坑的处置。

## 关键常量

| 项目 | 默认值 |
|---|---|
| 地域 | `cn-wulanchabu`（华北6 乌兰察布） |
| 镜像 | `m-0jlafwqq03tbtoerkiep`（悟空实操环境-2025年5月15日） |
| 规格 | `ecs.g6.2xlarge`（8U32G） |
| 付费 | 包年包月 1 周，`PrePaid Period=1 PeriodUnit=Week`（账户余额不足时先按量付费跑起来，再 `ModifyInstanceChargeType --InstanceIds '["i-xxx"]' --InstanceChargeType PrePaid --Period 1 --PeriodUnit Week --AutoPay true` 转换） |
| 带宽 | 按流量，峰值 100Mbps |
| 系统盘 | 默认 100G `cloud_essd` |
| 数据库 root 密码 | 使用现有环境约定（`/egova/apps/basic/wukong/wukong.env` 的 `DATASOURCE_PASSWORD`），不在最终答复明文展示 |
| mydumper rpm | `https://demo.egova.com.cn/MediaRoot/rpm/openeuler/22.03-lts-sp4/x86_64/mydumper-0.16.1-3.el8.x86_64.rpm` |
| license 申请标识 | **本机 `select substring(uuid(),25)`**，不是 info API 的 licenseKey！详见 [license.md](license.md) |

安全组和交换机必须实时查询，且**每条 aliyun 命令都要显式带 `--RegionId cn-wulanchabu`**：

```powershell
# 注意：本机代理会掐断到乌兰察布的连接，aliyun 命令必须先清代理变量
$env:HTTP_PROXY=''; $env:HTTPS_PROXY=''; $env:http_proxy=''; $env:https_proxy=''; $env:all_proxy=''
aliyun ecs DescribeSecurityGroups --RegionId cn-wulanchabu
aliyun ecs DescribeVSwitches --RegionId cn-wulanchabu
```

安全组选择：优先名字带"入职考核"的（如 `sg-0jl2a7gkrr0w698fk9ne` 乌兰察布互联网特殊安祖_只给入职考核）或已确认开放 8080/22 的（如 `sg-0jliso7y75ht42qso0da` 开放8080-22）；不猜，让用户指定。

## 考前流程

1. 检查 `aliyun configure list`、SSH、配额；确认代理已清。
2. 展示采购摘要：地域、镜像、规格、系统盘、带宽、购买时长、实例数、命名规则。
3. 调用 `RunInstances`（必须显式 `--RegionId cn-wulanchabu`）。实例名建议 `wukong3-exam-<yyyymmdd>`。
4. 轮询实例到 `Running`，记录实例 ID 和公网 IP；如用按量付费，设 `ModifyInstanceAutoReleaseTime`（格式 `2026-10-29T04:00:00Z`，**必须带秒**）。
5. **SSH 免密（镜像不做密钥对注入！）**：镜像把二十多位同事的公钥烤死在 `/root/.ssh/authorized_keys`，阿里云密钥对绑定形同虚设。处置：
   - 先试本地已有密钥（`ssh -i ~/.ssh/id_rsa -o BatchMode=yes -o GSSAPIAuthentication=no root@<ip>`；本机 id_rsa 曾匹配 `zjb-restore-key`，但换机后以实测为准）；
   - 不通就走**云助手**补钥（旧版 aliyun CLI 的 `CreateCommand --CommandContent` 有编码 bug，中文/长内容必乱码，用 `scripts/ecs_api.py` 自己签名调 API）：把本机公钥 append 进 `/root/.ssh/authorized_keys`，`chmod 700 ~/.ssh; chmod 600 authorized_keys; restorecon -rv /root/.ssh`；
   - IP 是回收复用的话，先 `ssh-keygen -R <ip>` 清 known_hosts 旧记录。
6. 清理非 admin 的页面、项目、用户脏数据（**先 mysqldump 备份再删**）：
   ```sql
   START TRANSACTION;
   DELETE c FROM wukong_page_card c JOIN wukong_page p ON c.pageId=p.id WHERE p.creator<>'admin';
   DELETE l FROM wukong_page_layer l JOIN wukong_page p ON l.pageId=p.id WHERE p.creator<>'admin';
   DELETE s FROM wukong_page_sublayer s JOIN wukong_page_layer l ON s.layerId=l.id JOIN wukong_page p ON l.pageId=p.id WHERE p.creator<>'admin';
   DELETE FROM wukong_page WHERE creator<>'admin';
   DELETE FROM wukong_project WHERE creator<>'admin';
   DELETE FROM wukong_page_group WHERE creator<>'admin';
   DELETE m FROM com_role_member m JOIN com_user u ON m.memberId=u.id WHERE u.username<>'admin';
   DELETE FROM com_user WHERE username<>'admin';
   COMMIT;
   ```
   admin 建的页面/项目/分组是基础模板，保留。清理后应为：1 用户、302 页面、7 项目、19 分组。
7. 申请并写入 license（**先取本机 DB key**，见 [license.md](license.md)）：`UPDATE wukong.com_license` + `UPDATE data_exchange.com_license`（两库同一套内容）。
8. 重启 `dex`、`wukong`，最后 `videocenter`（`wuneng` 一般已在跑）。
9. 验证授权：`curl http://127.0.0.1:8080/wukong-api/free/license/info` 的 licenseKey 应等于本机 DB key、有效期覆盖考核日；日志无"证书校验失败"。
10. 安装或校验 mydumper。
11. 外网入口验证：`curl http://<ip>:8080/wukong/index.html` 应 200（**注意必须带 `/index.html`**，`/wukong/` 是 403）。

## 账号录入

用 `scripts/自动生成悟空用户导入语句.py` 生成 SQL 再执行（该脚本 2026-10-28 修过列错位 bug，见文件头注释）。导入后抽查登录（SM2 流程见 [license.md](license.md) 末节）。

## 考后流程

考核结束后 30 分钟执行（有人延期到晚上的，按他的结束时间+30分钟，用备注"延至23:00"区分）：

1. 重置改过密码的考生账号为约定默认密码（`passwordExpireTime=NULL` 保护）。
2. 查询无页面且无项目账号，作为无需实操评分名单。
3. 保存查询结果，给阅卷表的 `未作答（0分）` sheet 和总表实操分数使用。
4. Moodle 笔试成绩拉取回填（见 `references/moodle-written-scores.md`）。
5. 阅卷表分配（见 `references/grading-workbook.md`）。

## 群通知（2026-10-28 实测）

- **群公告无法通过 API 发布**：钉钉未开放群公告 OpenAPI（devdoc 搜"群公告/群通知"无创建接口，dws chat 无相关 shortcut）。只能给用户公告全文，让他在客户端「群设置 → 群公告」手动发。
- 退而求其次用 `dws chat +send-to-group --group <群名> --text <内容> --yes` 发群消息（支持 @所有人 文本）；发错了用 `dws chat +messages-recall --conversation-id <cid> --msg-id <mid> --yes` 撤回。
- 公告要素：访问地址（带 /index.html）、账号规则（拼音+工号，举例）、默认密码、考题文档位置、延期政策（群内 @谁申请、延到几点）、无需提交文档/直接关闭页面。

## 已知坑（2026-10-28 累积）

- RegionId 是 `cn-wulanchabu`；`cn-wlcb` 报 `InvalidOperation.NotSupportedEndpoint`。
- 本机代理（127.0.0.1:18083）掐断阿里云连接，aliyun CLI 必须清代理变量后用；`ecs.cn-wulanchabu.aliyuncs.com` 显式 endpoint 也一样。
- 镜像禁密码登录且不做密钥对注入，SSH 免密靠云助手补 authorized_keys。
- 旧版 aliyun CLI 3.3.4 的 `CreateCommand --CommandContent` 在 Windows 上确定性乱码（Git Bash/PowerShell 均复现），改用 `scripts/ecs_api.py`。
- `ModifyInstanceAutoReleaseTime` 的时间格式必须带秒（`...T04:00:00Z`）。
- 包年包月可能因余额不足被拒（`InvalidAccountStatus.NotEnoughBalance`）：先按量付费保障开考，再转包年包月。
- 镜像数据里 com_role_member 有大量历史孤儿（指向已删用户 ID），不影响使用，可不清。
- wukong 启动时 DataTemplateUploadRunner 报 IndexOutOfBounds 是镜像固有现象，任务会继续，不影响服务。
- 数据库 key（license 用）在 wukong/data_exchange 两库一致，申请一套即可；换机必须重取。
