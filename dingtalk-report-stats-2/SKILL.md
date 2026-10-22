---
name: dingtalk-report-stats
version: 1.1.0
description: 钉钉日报统计平台（dingtalk-report-v3）运维与开发工作流。覆盖日报采集、周报统计、漏报推送（企业技术中心）、白名单管理、员工月度统计、部门层级汇总等。当用户提及日报统计、钉钉日报、漏报推送、工程技术中心日报、日报白名单、周报统计、新人免填、company month 26-25 等需求时自动触发。
author: majianquan
category: internal-ops
visibility: internal-ops
---

# 钉钉日报统计平台 Skill (dingtalk-report-v3)

FastAPI + SQLAlchemy + APScheduler 架构，部署于 `demo.egova.com.cn`，负责从钉钉拉取日/周报、按部门层级 × 模板 × 时间维度汇总、定时推送漏报清单到钉钉群机器人。

## 基础设施

| 项 | 值 |
|----|----|
| 服务器 | `demo.egova.com.cn`（SSH 免密，用户 root） |
| 项目路径 | `/opt/dingtalk-report-v3/`（**已 git init**，分支 `master`，git 1.8.3.1，**无 remote**） |
| 本地工作仓 | `D:\git\dingtalk-report-v3`（**2026-10-21 恢复**，此前丢失）<br>origin → GitHub、prod → 服务器、backup → 本地裸仓、gitlab → 公司 GitLab |
| 本地裸仓备份 | `D:\git\dingtalk-report-v3.git`（**2026-10-21 重建**） |
| GitHub 备份 | `majq1990/dingtalk-report-v3`（private，2026-06-28 建） |
| 公司 GitLab | `devops/jszc/dingtalk-report-v3`（private，**2026-10-22 push-to-create 建仓**）<br>Web: http://gitlab.egova.com.cn:8000/devops/jszc/dingtalk-report-v3<br>SSH: `ssh://git@gitlab.egova.com.cn:222/devops/jszc/dingtalk-report-v3.git`（~/.ssh/config 已配 Port 222 + ed25519 密钥） |
| 容器名 | `dingtalk-report-v3`（docker-compose v1 语法） |
| 数据库 | 阿里云 RDS MySQL，库 `ops_log`，用户 `ops_log` |
| 对外域名 | `https://demo.egova.com.cn`（nginx 443 → 127.0.0.1:81；8080 已转发到 443） |
| 根部门 | 工程技术中心 `MAIN_DEPARTMENT_ID=668486038` |

> ⚠️ **GitLab pre-receive hook 强制公司邮箱**：提交作者/提交者必须
> `<拼音全拼>@egova.com.cn`（如 `majianquan@egova.com.cn`），gmail 等私人邮箱会被拒。
> 2026-10-22 已用 `git filter-branch --env-filter` 把全部 8 个提交重写为公司邮箱
> （commit hash 因此全部变更，旧 hash c621d8e → 新 588d761，内容不变），
> 并已同步到 GitHub（force push）/服务器/裸仓/GitLab 五处。

## 关键配置（`.env`）

```
DATABASE_URL=mysql+pymysql://ops_log:ops_log-Eg0va@rm-2zeve65004dooj2s890210.mysql.rds.aliyuncs.com:3306/ops_log?charset=utf8mb4
DINGTALK_CORP_ID=ding950f23e6cefc750c35c2f4657eb6378f
DINGTALK_APP_KEY=dingckyxwwtify3ypyft
DINGTALK_APP_SECRET=5W5998unCM98fYhVfO2fyUHA-EINyP3VASsQwJ99gvJ0_Qza9bHgboKd2P4w_aTs
DINGTALK_AGENT_ID=4447219578
MAIN_DEPARTMENT_ID=668486038
LEAVE_PROCESS_CODE=PROC-272B603A-817B-4319-9A97-8055A667E1AA
MISSING_REPORT_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=41718fda5989ce91b8b9ea6fd340dc8fd674a7b9384781e66b3b72bea1078cf1
MISSING_REPORT_KEYWORD=漏报
PUBLIC_BASE_URL=https://demo.egova.com.cn
SCHEDULER_ENABLED=true
TIMEZONE=Asia/Shanghai
```

## 业务规则（务必遵守）

1. **日报截止时间**：`report_date = d` 的截止时间 = 下一个工作日 `09:00`（准时）/ `10:00`（迟交）。
2. **report_date 推导**（采集入库时必须用 `_derive_report_date(submit_time)`）：
   - 提交时间 ≤ 当日 10:00 → cursor = 当日
   - 否则 cursor = 次日；cursor 非工作日则前移；最终 `report_date = get_prev_workday(cursor)`
3. **upsert key** = `(user_id, report_date, template_name)`，禁止使用 `_target_hint` 当 report_date。
4. **新人免填**：`hired_date` 所在自然周全部免填，从次周周一起才需要写日报。由 `utils/date_util.is_hire_exempt(hired_date, target)` 统一判定。必须在三处应用：`stats_missing_page`、`_calc_daily_one` 的 exempt 集合、`push_weekly_missing_report`。
5. **company month**：上月 26 日 ~ 本月 25 日，`get_company_month_range(d)`。
6. **免填来源**：请假条（`LeaveApproval.exempt_daily_report = True`）∪ 白名单 ∪ 新人免填。
7. **部门层级**：统计服务为每个部门生成 `{自身} ∪ {所有后代}` 的汇总行，模板维度在 `DailyReportTemplate`（None 表示全部模板合计）。
8. **周报应交人按职位界定**（2026-06-28 起）：`job_template_mapping(job_title, template_id)` 把**职位**映射到周报模板，`job_title` 匹配的是 `employees.position`（不是工号）。`_calc_weekly_one` 用它界定每模板应交人：有映射 → 只有该职位的在职员工算应交；无映射 → 沿用「部门子树全员在职」。已配置：`工程周会周报(id=4)→工程技术中心大区总经理 + 工程技术中心副总经理`（共 7 人）、`工程技术中心周报(id=7)→15 类工程岗职位`（共 284 人）。**当前 active 周报模板仅 id=4、id=7**；`研发中心重点专项工作周报(id=18)` 已停用（工程不需提交，原先无映射→按部门全员算出 应交370/漏交370 纯噪音，已停用并清空其统计行）。
9. **`employees.position` 存的是钉钉职位 `title`**（采集 `position=info.get("title")`，2026-06-28 修复，此前误取不存在的 `position` 键恒为空）。`job_title` 仍是工号（export 依赖）。新增/改职位规则后需重跑 employee_sync 或定向回填 position。
10. **周报归属周推导**：采集用 `_derive_week_start(submit_time)`——某周「首个工作日」结束前提交算**上一周**的报（典型周一上午补交），否则算本周。采集窗口 = 本周一 ~ 下周首个工作日 23:59，覆盖「下周才提交」常态。周报截止 = 下一工作周**首个工作日 23:59**，两档（≤截止=已交，其余=漏交，看板把 late 并入漏交）。
   - `weekly_report_collect` 周一 22:00 采集（喂周一 22:00 的 `weekly_summary_push`），另有 `weekly_report_recollect` 周二 02:00 **补采+补算上周**，捞回周一 22:00–23:59（截止前）的迟到提交。upsert 幂等、不动推送。（2026-07 加）
11. **周报整周请假免交**（2026-07 起）：某周「所有工作日」都落在已批准免填请假（`LeaveApproval.exempt_daily_report=True` 且 `result='agree'`）区间内的人，本周免交，从应交里扣除。判定统一走 `statistics_service.week_leave_exempt_ids(db, week_start, week_end, candidate_ids=None)`。已在 `_calc_weekly_one`（聚合 `exempt_employees/required/missing`）与反查页 `stats_weekly_detail_page`（`required`/`missing` 模式排除、新增 `exempt` 模式看免交名单）两处应用。改了免交规则后需 `calc_weekly` 重算相关周。

## 调度任务（18 个，`src/scheduler/scheduler.py`）

| job id | 触发 | 说明 |
|--------|------|------|
| `weekly_missing_push` | `mon-fri 11:00`，guard `should_push_summary()` 只在本周首个工作日真实推送 | 推送上周工程技术中心漏报清单到**省份技术总群**（CSV+Excel 下载链接）。2026-10-21 恢复，2026-05-27 重构时被误删导致停推 21 周 |
| `monthly_missing_push` / `_second` | 每天 11:00，内部判「25 号后首/第二个工作日」 | 推送月度漏报清单到**两个群**：「工程日报统计群」+「省份技术总群」 |
| 其余 | 日报采集、统计、周报采集、统计、员工月度、白名单同步、人员同步等 | 参考 `scheduler.py` JOBS 常量 |

## 漏报清单推送（2026-10-21 恢复并改造）

| 项 | 值 |
|----|----|
| 周度 | `PushService.push_weekly_missing_report(week_start, week_end)`，push_type=`weekly_missing_summary`，webhook=`MISSING_REPORT_WEBHOOK` → 省份技术总群 |
| 月度 | `PushService.push_monthly_missing_summary(start, end)`，push_type=`monthly_missing_summary`，webhook=`MONTHLY_MISSING_REPORT_WEBHOOK` → 工程日报统计群 **+** `MISSING_REPORT_WEBHOOK` → 省份技术总群 |
| 共用逻辑 | `_build_missing_content()` 拼 markdown；`_send_missing_robot(history, content, title, targets)` 多群发送，targets=[(群名, webhook), ...]，每群一条 `PushDetail`（`user_id="robot"`, `user_name=群名`），任一群失败 → `status=partial` |
| 周度窗口 | 上一个自然周周一~周日：`last_monday = today - (today.weekday()+7)`，`last_sunday = last_monday + 6` |
| 数据源 | `v_emp_day_status`（`status='missing'`）+ `v_emp_l1_dept`，**与工程技术中心月度面板同源**，自带新人免填/请假/白名单/待填不计漏报规则 |
| 导出 | `ExportService.export_weekly_missing()` → `static/exports/missing_{start}_{end}_{stamp}.{xlsx,csv}`，列 = 一级部门/部门路径/部门/工号/姓名/漏报天数/漏报日期，CSV 用 `utf-8-sig` |
| SSRF 防护 | `_validate_robot_webhook()`：https + 主机白名单 `oapi.dingtalk.com` + 路径 `/robot/send` + DNS 解析后 IP 须为公网；请求 `follow_redirects=False` |
| 机器人安全关键词 | `漏报`（markdown 正文必含，否则被钉钉拦截） |

**重要**：周度数字会比 2026-05-25 之前小——旧实现缺新人免填/请假/白名单/待填规则
（同窗口旧算法 133 人/460 人次，现役口径 56 人/80 人次）。这是口径修正，周度与月度面板现在对得上账。

**周度明细名单口径**（与历史 4-15/5-25 推送的逐行格式一致）：
标题 → 漏报范围（含工作日数）→ 漏报人数 → 一级部门分布表（人数 | 人次 | 合计）→ Excel/CSV 下载链接。

## 漏报推送历史

- 2026-05-27 12:36 重构把 `push_weekly_missing_report`/`push_monthly_missing_report`/`_push_missing_report`
  三件套整体删除，当晚只补回月度版 `push_monthly_missing_summary`，**周度版从未恢复**，
  导致省份技术总群自 2026-05-25 11:00 起停推 21 周。2026-10-21 已重建。
- 旧实现原文可从 Codex 归档找回：
  `C:\Users\majq1\.codex\archived_sessions\rollout-2026-05-16T21-23-14-019e30f4-8fe8-70f2-b6b4-f31c7686b727.jsonl`
  第 112/113 行 = 两个包装函数，第 124/125 行 = `_push_missing_report` 前 ~80 行。
- `push_history` 表中 `push_type='weekly_missing_summary'` 的历史 11 条（2026-04-15 ~ 2026-05-25）仍完整保留。

## 常见运维操作

### 重新加载 .env（改了配置后）
```bash
ssh root@demo.egova.com.cn 'cd /opt/dingtalk-report-v3 && docker-compose up -d app'
```
> `docker-compose restart` **不会**重新加载 `env_file`，必须 `up -d` 重建容器。

### 手动触发推送/采集/统计
通过 `/admin/*` 管理页面（见 `src/api/routes.py`）或进入容器 python shell：
```bash
docker exec -it dingtalk-report-v3 python -c "
from src.db import SessionLocal
from src.services.push_service import PushService
from src.services.data_collection_service import DataCollectionService
from src.services.statistics_service import StatisticsService
from datetime import date
with SessionLocal() as db:
    # 重采某日
    DataCollectionService(db).collect_daily_reports(date(2026,4,14))
    # 重算某日统计
    StatisticsService(db).calc_daily(date(2026,4,14))
    # 重算当月员工月度
    StatisticsService(db).calc_employee_monthly(date.today())
    # 手动推送漏报
    # PushService(db).push_weekly_missing_report(...)
"
```

### 白名单变更自动重算
`/admin/whitelist/add|toggle|delete` 已接入 `_recalc_current_year_async()`，后台 daemon 线程调用 `StatisticsService.recalc_current_year_daily()`，无需手动触发。

### 查看日志
```bash
ssh root@demo.egova.com.cn 'docker logs --tail 200 dingtalk-report-v3'
```

## 关键代码位置

| 职责 | 文件 |
|------|------|
| 日报采集 + report_date 推导 | `src/services/data_collection_service.py`（`_derive_report_date`, `_upsert_daily_report`） |
| 统计汇总（部门×模板×日/周） | `src/services/statistics_service.py` |
| 漏报推送（CSV/Excel + markdown） | `src/services/push_service.py` 的 `push_weekly_missing_report` |
| 日期/工作日/新人免填工具 | `src/utils/date_util.py` |
| 调度任务 | `src/scheduler/scheduler.py` JOBS |
| 管理页面 / 白名单 CRUD / 漏报看板 | `src/api/routes.py`（`stats_missing_page`, `/admin/whitelist/*`） |
| 周报看板 + 反查 | `src/api/routes.py`：`stats_weekly_page` 汇总；**活反查** `stats_weekly_detail_page` = `/stats/weekly/detail?dept_id&week_start&template_id&mode=`（`total/required/on_time/late/missing/exempt` 六模式，看板 5 列全部下钻）；旧 `stats_weekly_missing_page`(`/weekly/missing`) 已无链接保留。模板 `stats_weekly.html`、`stats_weekly_detail.html` |
| 模板管理 + 职位映射配置 | `src/api/routes.py` `admin_templates_page`（传 `tpl_names`）；模板 `admin_templates.html` 可配 `job_template_mapping` 职位→周报映射 |
| 模型 | `src/models/`（`DailyReport`, `WeeklyReport`, `DailyReportStatistics`, `WeeklyReportStatistics`, `EmployeeDailyStats`, `DailyReportWhitelist`, `LeaveApproval`, `Department`, `Employee`, `Holiday`, `PushHistory`） |

## 离职 / 调离人员判定（2026-10-22 修复，务必理解后再改）

`sync_employees()` 每日 02:30 跑，把「不在钉钉部门成员列表里」的在职员工当**离场候选**，
走三分支判定（`_sweep_dimissions`）：**离职(resigned) / 调离中心(transferred) / 保持在职**。

**钉钉接口信号（实测）**：

| 来源 | 信号 | 含义 |
|------|------|------|
| `listdimission` `status=2` | 已离职 | HR 确认离职（唯一可靠离职信号） |
| `listdimission` `status=3` | 在职 | HR 侧仍在职 |
| `listdimission` `last_work_day` | 最后工作日(ms) | **仅 HR 登记了才返回** |
| `user/get` errcode `50002` | 不在授权范围 | 人已**调离**工程技术中心（人可能仍在职，只是不在本中心） |

**判定优先级**（`_sweep_dimissions`）：

1. `last_work_day` → 权威，直接用，`exit_type=resigned`
2. `status=2` 但无 `last_work_day` → 用 `employees.last_seen_date` 兜底，`exit_type=resigned`
3. `status=3`/无记录，但 `probe_user_scope()==out_of_scope`（errcode 50002）
   → 人已调离中心，用 `last_seen_date` 兜底设 `left_date`，`exit_type=transferred`
4. 其余（仍 in_scope / unknown）→ **保持在职**，仅告警

两种离场都设 `left_date` + `is_active=False`（统计视图 `v_emp_day_status` 靠 `left_date`
截断历史窗口，人离开工程技术中心就不该再计入其日报统计）；区别只在 `exit_type`：
`resigned` 是真离职，`transferred` 是调离（人仍在职，将来若调回中心可据此恢复）。

> ⚠️ **「不在花名册」≠「离职」**。实测丑永辉调岗到工程技术中心之外（钉钉联系可搜到、
> 人仍在职），`user/get` 返回 50002 → 判 `transferred`；胡思杰实为在岗（四川区域），
> 只有一条脏的陕西区域 `employee_departments` 关联，已由 `_prune_emp_dept_links` 按钉钉
> 权威 `dept_id_list` 清理。**绝不能仅凭"连续不在花名册"判定离场**——那会误伤在岗同事
> （曾用"连续 7 天不在花名册即判离"规则，实测误伤已移除）。`absent_days` 现仅用于监控告警。

**修复前的 bug**：原代码 `if not rec.get("last_work_day"): continue`，导致 HR 侧
未登记最后工作日的离职者被永远跳过（王祥印连续 15 天 unmatched），在平台里一直是
「在职」并持续产生漏报（9-08~10-20 共 27 个漏报日）。

**新字段**：
- 迁移 `c3f8a91d4e20`：`employees.last_seen_date`（最后出现在成员列表日期）、`employees.absent_days`（连续缺席天数，仅告警）
- 迁移 `d5e7b2c91a04`：`employees.exit_type`（`resigned` / `transferred`，带索引；历史 111 条离职回填为 `resigned`）

**关联清理**：`_prune_emp_dept_links(uid, dept_id_list)` 在每次 `sync_employees` 按钉钉
权威 `dept_id_list` 删除该员工已不属于的 `employee_departments` 关联（调岗/调离后残留的
旧部门），空 `dept_id_list` 不清理（防接口抖动误删）。

**回填脚本**：`scripts/backfill_employee_left_date.py`（花名册 + 钉钉状态 + 授权范围三重校验，
处理 `status=2` 离职与 50002 调离两类）。容器里用 `docker exec -i dingtalk-report-v3 python - < 脚本`
运行（`scripts/` 未挂载进容器，不要直接 `docker exec python scripts/...`）。

**审计「还有没有漏认的」**（全量在职约 370 人，跑一次即可）：
- 漏认离职：`listdimission` 里 `status=2` 但平台 `is_active=1` 的人（实测 0）
- 漏认调离：`probe_user_scope()` 返回 `out_of_scope` 但平台 `is_active=1` 的人（实测仅丑永辉，已处理）

**排查**：日志搜 `dimission sweep unmatched uids`（带姓名+absent 天数）。同一批人持续出现 =
钉钉 HR 侧状态没更新，需 HR 补登记或确认调岗。

## 常见坑

1. **改 enum 必须带 NOT NULL** 否则列会被改为可空：`ALTER TABLE push_history MODIFY push_type ENUM(...) NOT NULL;`
2. **`daily_reports` 无 unique 约束**，重复采集会产生重复行 → upsert key 必须严格 `(user_id, report_date, template_name)`。
3. **机器人 webhook 不支持附件**，大列表必须走「短 markdown + 静态 URL 下载」方式。
4. **PUBLIC_BASE_URL 改动后必须 `up -d`** 才能生效，`restart` 无效。
5. 钉钉请假条的 `exempt_daily_report` 由 LeaveApproval 流程审批元数据解析，改采集逻辑要小心不要误丢弃请假条。
6. **scp 部署会覆盖服务器工作区的未提交改动**。2026-10-22 就把马健权自己的 MJQ
   anomaly 特例（`if is_anomaly and uid == MJQ_USER_ID: status = "late"`）覆盖掉了，
   从 `.backup/` 恢复后才提交入库。**部署前先 `git diff` 看有没有别人的未提交改动。**
7. **不要用 `employees.updated_at` 近似"最后出现日期"**。SQLAlchemy 在字段值未变时
   不发 UPDATE，在职员工的 `updated_at` 可能停在几个月前（李逢华/吴昊等高管停在 6-28），
   拿它回填会把在职员工误判为长期缺席。正确做法是用真实花名册反查。
8. **本地 Windows 检出默认转 CRLF**。服务器多数文件是 LF（`scheduler.py` 是 CRLF），
   scp 前先 `git config core.autocrlf false` 并统一行尾，否则 git diff 全是噪声。
9. **容器内 `scripts/` 不是宿主机挂载的**，宿主机 `scripts/*.py` 要用
   `docker exec -i dingtalk-report-v3 python - < 文件` 执行。

## 版本控制（2026-06-28 建立，2026-10-21 重整）

之前服务器目录是裸目录、无版本控制，本地只有零散补丁。现已建仓：

- 服务器 `/opt/dingtalk-report-v3/` 已 `git init`（`master`，git 1.8.3.1），首提交 = 生产快照。
  **服务器上没有任何 remote**，也未配置 GitHub 凭据。
- 本地工作仓 `D:\git\dingtalk-report-v3`（**2026-10-21 恢复，此前已丢失**）：
  `git clone root@demo.egova.com.cn:/opt/dingtalk-report-v3`。
- 本地裸仓备份 `D:\git\dingtalk-report-v3.git`（**2026-10-21 重建**），作为 `backup` remote。
- GitHub 备份 `majq1990/dingtalk-report-v3`（private，2026-06-28 建，**GitLab 上没有本项目**）。
- `.gitignore` 排除：`.env`（密钥）、`logs/*`、`static/exports/*`、`__pycache__`。

**当前 remote 配置**（本地工作仓）：

```
origin  → https://github.com/majq1990/dingtalk-report-v3.git   （GitHub 备份）
prod    → root@demo.egova.com.cn:/opt/dingtalk-report-v3        （生产）
backup  → D:/git/dingtalk-report-v3.git                          （本地裸仓）
gitlab  → ssh://git@gitlab.egova.com.cn:222/devops/jszc/dingtalk-report-v3.git （公司 GitLab，走 ~/.ssh/config）
```

**改完代码四步走**（服务器侧改 → 本地 pull → 推各远端）：

```bash
# 1. 服务器侧改完并 commit（工作区即生产目录；作者邮箱必须是 majianquan@egova.com.cn）
ssh root@demo.egova.com.cn 'cd /opt/dingtalk-report-v3 && git add -A && git commit -m "..."'

# 2. 本地拉取
cd D:\git\dingtalk-report-v3 && git fetch prod master && git reset --hard FETCH_HEAD

# 3. 推四个远端（GitHub 需临时注入 token，推完移除）
git push origin master && git push backup master && git push gitlab master
```

> GitLab 建仓不需要 API token：对 `devops/jszc/<新项目名>.git` 直接 push 即可
> （push-to-create）。但注意 hook 会校验提交人邮箱。

⚠️ **服务器是 non-bare 仓且工作区即生产目录**，`git push` 不会自动更新工作区文件。
⚠️ 推 GitHub 需临时注入 token（`gh auth token`），**推完必须把 token 从 remote URL 移除**。
⚠️ 本地 Windows 检出默认转 CRLF，先 `git config core.autocrlf false`。

## 参考

- 项目路径：`/opt/dingtalk-report-v3/`
- 机器人 webhook access_token：`41718fda5989ce91b8b9ea6fd340dc8fd674a7b9384781e66b3b72bea1078cf1`
- 下载基址：`https://demo.egova.com.cn/static/exports/`
