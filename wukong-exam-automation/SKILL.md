---
name: wukong-exam-automation
version: 1.0.0
description: 悟空 3.0 认证考核全流程自动化。用于用户给出考核人员名单、考核开始/结束时间、笔试 Moodle overview 地址、原始阅卷模板或评分表时，编排考前 ECS 采购（买一周）、悟空服务器初始化、license 授权（用本机数据库 key 申请）、考生账号录入、群通知/公告，考后自动改密、查询无操作账号、拉取笔试成绩、复制原始阅卷清单并输出阅卷分配表；支持群内延期申请的定时跟踪与自动开通。触发词：悟空考核自动化、悟空认证自动化、悟空实操环境、悟空阅卷分配、考后改密、笔试成绩回填、license申请、群公告、延期申请、wukong-exam-automation。
author: majianquan
category: support-dept
visibility: support-dept
---

# 悟空认证考核自动化

## 输入契约

必须先收集并确认这些输入：

- 人员名单：钉钉表格链接或本地 Excel/CSV，至少包含姓名、工号、岗位/区域、是否参考；若缺账号列，按姓名/工号规则生成。
- 考核时间段：开始时间、结束时间；默认在开始当天采购 ECS，购买 1 周；默认考核结束后 30 分钟进入考后流程。
- 笔试地址：Moodle `mod/quiz/report.php?id=...&mode=overview` 或 `mod/quiz/view.php?id=...`，用于考后拉取 `评分/100.00`。
- 原始阅卷模板：钉钉表格/文档链接，优先直接复制原表，保留阅卷细表、截图列、格式和公式。
- 输出位置：钉钉知识库/文件夹；未给出时用原模板所在空间或本次任务约定输出目录。

缺任一关键输入时只补问缺口；不要先采购、改密或创建新阅卷表。

## 默认编排

1. 考前准备：读取人员名单，校验字段、人数、账号规则和参考状态。
2. 环境采购：按 `references/environment.md` 采购 cn-wulanchabu 悟空 ECS，付费周期 1 周（余额不足先按量付费再转包年包月）。
3. 初始化：SSH 免密（镜像不做密钥对注入，走云助手补钥，脚本 `scripts/ecs_api.py`）、清脏数据（先备份）、安装 mydumper。
4. License 授权：**先取本机数据库 key `select substring(uuid(),25)` 让用户申请**（不是 info API 显示的 licenseKey！），拿到后写入 `wukong.com_license` + `data_exchange.com_license` 两个库，重启 dex/wukong/videocenter，验证授权。完整机制与排障见 `references/license.md`。
5. 账号录入：按人员名单生成/执行悟空账号 SQL（`scripts/自动生成悟空用户导入语句.py`），记录账号、默认密码和访问地址；抽查登录（SM2 流程见 `references/license.md`）。
6. 群通知：在考核群发布公告。**群公告无 OpenAPI**，给用户全文让其客户端手动发；同时可用群消息兜底（见 `references/environment.md` 群通知节）。公告要素：访问地址（必须带 `/index.html`，`/wukong/` 是 403）、账号规则+举例、默认密码、考题文档、延期政策。
7. 考中监控：保存实例、IP、license、账号导入、服务健康检查结果；异常先止损，不做考后动作。
8. 延期跟踪（如用户要求）：定时拉取群内 @我 的消息，延期申请自动开通（账号到期改到延期者的结束时间、备注标注）并群内确认；账号问题诊断修复；其他按公告回复或记录。定点轮（如结束前 N 分钟）要输出延期名单。
9. 考后 30 分钟（延期者按其结束时间）：重置改过密码的考生账号、查询无页面无项目账号，输出无需评分名单。
10. 笔试成绩：按 `references/moodle-written-scores.md` 登录 Moodle，下载 overview CSV/JSON，按姓名回填笔试分数。
11. 阅卷表：按 `references/grading-workbook.md` 复制原始阅卷模板，清理旧阅卷记录，分配考官，联动实操分数和综合分。
12. 校验交付：验证截图列、公式错误、人员匹配、未作答名单、笔试未匹配名单，输出最终表链接和摘要。

## 操作边界

- 采购 ECS、修改释放时间、释放实例、批量改密、批量写钉钉表格、群内发言/撤回都属于有影响操作；执行前必须展示目标、范围和预计影响。
- 不要编造阿里云安全组、交换机、镜像、license key、Moodle quiz id、钉钉 nodeId 或人员字段；查不到就停下来列候选或要求补充。
- license 申请标识必须是**当次采购的机器上现取**的 `substring(uuid(),25)`；复用上次的值会得到绑错 key 的 license。
- 阅卷表必须以原始模板复制为基础。不要手搓阅卷细表结构，除非用户明确要求重建。
- 考后改密只改考生账号，不改 `admin`；已批准延期的账号（备注含"延至23:00"或到期时间在当晚）要排除，按其个人时间线单独处理。
- 笔试成绩按姓名精确匹配；同名或重复 attempt 要列出，不静默覆盖。
- 最终表中的 `实操分数` 应按 `实操阅卷人` 联动到对应考官 sheet 的总得分；`笔试分数` 来自 Moodle；`综合分` 使用容错公式。
- 群内自动回复只覆盖公告已声明的事实（时间/地址/账号规则/延期政策）；不确定的不回复，记录交用户。

## 资源路由

- 环境采购、初始化、改密、无操作账号查询、群通知：读 `references/environment.md`。
- **license 申请标识、校验机制、排障、SM2 登录验证：读 `references/license.md`**。
- 人员名单字段、账号生成、账号 SQL：读 `references/accounts.md`。
- 云助手补 SSH 公钥/远程执行（绕开 CLI 编码 bug）：`scripts/ecs_api.py`。
- 账号导入 SQL 生成器：`scripts/自动生成悟空用户导入语句.py`。
- 考后改密/无操作查询脚本：`scripts/wukong_postexam_task.ps1`。
- Moodle 笔试成绩拉取和匹配：读 `references/moodle-written-scores.md`。
- 阅卷分配表复制、清理、公式和校验：读 `references/grading-workbook.md`。
- 若要接入定时器、Webhook、钉钉 AI 表格或外部调度，读 `references/scheduling.md`。

## 交付摘要

完成后返回：

- 悟空环境：实例 ID、地域、到期/释放时间、公网 IP、访问地址（带 `/index.html`）。
- 账号结果：导入人数、跳过人数、失败账号、默认密码说明。
- License：申请的数据库 key、有效期、写入的两个库、登录抽查结果。
- 群通知：公告/消息发布情况（群公告需用户手动发时要说明）。
- 延期跟踪：批准的延期者名单及其结束时间。
- 考后结果：改密人数、无页面无项目名单。
- 笔试结果：Moodle 记录数、匹配人数、未匹配名单。
- 阅卷表：最终钉钉链接、考官分组、公式错误数、截图列校验。

仅在用户要求时展示敏感密码；默认只说明"已按约定默认密码配置"。
