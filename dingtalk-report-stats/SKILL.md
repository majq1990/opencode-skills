---
name: dingtalk-report-stats
version: 1.0.0
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
| 项目路径 | `/opt/dingtalk-report-v3/` |
| 容器名 | `dingtalk-report-v3`（docker-compose v1 语法） |
| 数据库 | 阿里云 RDS MySQL，库 `ops_log`，用户 `ops_log` |
| 对外域名 | `https://demo.egova.com.cn`（nginx 443 → 127.0.0.1:81；8080 已转发到 443） |
| 根部门 | 工程技术中心 `MAIN_DEPARTMENT_ID=668486038` |

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

## 调度任务（13 个，`src/scheduler/scheduler.py`）

| job id | 触发 | 说明 |
|--------|------|------|
| `weekly_missing_push` | `mon-fri 11:00`，guard `should_push_summary()` 只在本周首个工作日真实推送 | 推送上周工程技术中心漏报清单到机器人（CSV+Excel 下载链接） |
| 其余 | 日报采集、统计、周报采集、统计、员工月度、白名单同步、人员同步等 | 参考 `scheduler.py` JOBS 常量 |

## 推送格式（`push_weekly_missing_report`）

- 消息体：markdown。必须包含关键词 `漏报`。
- 段落：标题 → 漏报范围 → 漏报人数（总）→ **一级部门分布表**（L1 部门名 | 人数 | 人次 | 合计）→ CSV / Excel 下载链接。
- 文件：`static/exports/missing_{weekstart}_{weekend}_{stamp}.{csv,xlsx}`，列 = `一级部门, 部门路径, 部门, 姓名, 漏报天数, 漏报日期`。CSV 使用 `utf-8-sig`。
- L1 归属：从员工部门沿 `parent_id` 向上走，直到 `parent_id == MAIN_DEPARTMENT_ID`，该节点即一级部门。
- `PushHistory.push_type = 'weekly_missing_summary'`（枚举值需要 DB 中存在，DB 改动：`ALTER TABLE push_history MODIFY push_type ENUM(..., 'weekly_missing_summary') NOT NULL;`）。

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
| 模型 | `src/models/`（`DailyReport`, `WeeklyReport`, `DailyReportStatistics`, `WeeklyReportStatistics`, `EmployeeDailyStats`, `DailyReportWhitelist`, `LeaveApproval`, `Department`, `Employee`, `Holiday`, `PushHistory`） |

## 常见坑

1. **改 enum 必须带 NOT NULL** 否则列会被改为可空：`ALTER TABLE push_history MODIFY push_type ENUM(...) NOT NULL;`
2. **`daily_reports` 无 unique 约束**，重复采集会产生重复行 → upsert key 必须严格 `(user_id, report_date, template_name)`。
3. **机器人 webhook 不支持附件**，大列表必须走「短 markdown + 静态 URL 下载」方式。
4. **PUBLIC_BASE_URL 改动后必须 `up -d`** 才能生效，`restart` 无效。
5. 钉钉请假条的 `exempt_daily_report` 由 LeaveApproval 流程审批元数据解析，改采集逻辑要小心不要误丢弃请假条。

## 参考

- 项目路径：`/opt/dingtalk-report-v3/`
- 机器人 webhook access_token：`41718fda5989ce91b8b9ea6fd340dc8fd674a7b9384781e66b3b72bea1078cf1`
- 下载基址：`https://demo.egova.com.cn/static/exports/`
