---
name: notebooklm
version: 1.3.0
description: NotebookLM 自动日报/周报系统运维 skill。从 NotebookLM 抓 note → AI 整理日报/周报 → 钉钉推草稿（支持编辑/确认/否决）→ 确认后通过 dws 提交到钉钉文档；周报推送 24h 未提交自动补推一次。部署在 majq1990.asia，cron 日报 18:20 / 周报 11:00 / 补推检查 11:30。触发词：notebooklm / 日报 / 周报 / 周报补推 / NotebookLM 抓取失败 / notebooklm 部署。
---

# NotebookLM 自动日报/周报系统

> **版本**：v1.3.0
> **部署位置**：`majq1990.asia:/opt/notebooklm-daily-report/`
> **触发词**：日报 / 周报 / notebooklm / NotebookLM

## 系统架构

```
NotebookLM Google 账号
    ↓ playwright 自动化抓取（keepalive + fetch + write）
/opt/notebooklm-daily-report/（Docker 容器）
    ↓ Python cron 18:20（日报）/ 11:00（周报）
AI 整理 → 钉钉推草稿（支持编辑/确认/否决）
    ↓ 用户确认
dws 写钉钉文档
```

## 部署信息

| 项 | 值 |
|---|---|
| 项目路径 | `/opt/notebooklm-daily-report/` |
| 管理方式 | `docker-compose`（容器名 `notebooklm-daily-report`） |
| cron 日报 | 每日 18:20（Asia/Shanghai） |
| cron 周报 | 每周工作日 11:00 |
| cron 补推 | 每日 11:30 检查，周报 24h 未提交自动补推（src/repush_checker.py） |
| 关键脚本 | `src/notebooklm_fetch.py` / `src/notebooklm_write.py` |
| 备份后缀 | `.bak-YYYYMMDD` |

## 关键配置

```bash
# 查看 SSH 到 majq1990.asia
ssh root@majq1990.asia

# 项目目录
cd /opt/notebooklm-daily-report

# 查看 cron
crontab -l  # 或 /etc/cron.d/ 下对应文件

# 查看日志
docker compose logs --tail 100 keepalive
cat keepalive.log
```

## bind mount 生效方式

`docker-compose.yml` 用 `volumes: - ./src:/app/src` bind mount：
- **改 `src/` 后下次 `docker compose run --rm <svc>` 立即生效，不用 rebuild 镜像**
- **改完顺手清 `__pycache__/`**：`rm -rf /opt/notebooklm-daily-report/src/__pycache__/`
- 语法校验：`python3 -c "import ast; ast.parse(open(fp).read())"`

## 三级确认流程

1. AI 从 NotebookLM 抓内容 → 整理日报/周报 → 推钉钉草稿
2. 用户在钉钉中**编辑/确认/否决**
3. 确认 → dws 写入钉钉文档；否决 → 重新生成

## 自动补推机制（2026-09-14 上线）

周报草稿推送 **24h 仍未提交/否决** → `src/repush_checker.py` 自动补推一次（推送标题带「（补推）」，同天旧链接作废）：

- 判定条件：`status=pending` + 未过期 + 距创建 ≥24h + `repush_count<1`（历史旧记录无 created 字段时用 `expire - 72h` 反推）
- 点「❌ 否决」后**不会**再补推；日报不参与补推
- 调度：cron `30 11 * * *`（日志 `data/repush.log`）
- 手动补推：`docker compose run --rm weekly-worker python -m src.repush_checker --force W2026-XX-XX`
- 有效期文案已改为动态「链接有效至 MM-DD HH:MM」（原固定「链接 1 小时内有效」为旧文案 bug，已修）
- 状态字段：`save_draft` 新增 `created`、`repush_count`；`state.all_records()` / `state.set_status()` 为运维接口

## 已知踩坑 + 修复

### 2026-09-14：日报整理 prompt 缺聚合规则

- **现象**：日报多条同项目记录（如银川×2）拆开罗列，用户反馈"效果不好"
- **根因**：日报 `SUMMARIZE_PROMPT` 无聚合要求（周报 prompt 早有"同一项目必须合并 1 条"）
- **修复**：prompt 加「按项目聚合（含正反例）+ 书面化表达（口语→正式汇报语，保持原意）+ 案件号/工单号必留 + 不扩写不拔高」；备份 `ai_client.py.bak-prompt-20260914`
- **重推模式**：gen（fetch+summarize，报告 JSON 存 `/app/data/`，勿用容器 /tmp——`--rm` 退出即销毁）→ push（读 JSON → superseded 旧 token → save_draft → push_draft）
- ✅ **用户验收通过（2026-09-14）**：新版日报（银川合并/书面化/案件号保留）确认 OK，prompt v3 定稿

### 2026-05-21：goto timeout 60s 间歇失败

- **现象**：playwright `Page.goto: Timeout 60000ms exceeded`（notebooklm.google.com domcontentloaded）
- **根因**：chromium 冷启动 + Google 全套 JS 资源加载，偶发卡在 60s 临界值附近
- **修复**：`notebooklm_fetch.py:87` `timeout=60000 → 120000`
- **其他 goto 不动**：登录态同源跳转（30s 稳定）

### 2026-05-19：prepend 3s 等待不够

- **现象**：`Locator.wait_for: Timeout 10000ms exceeded` 目标 `button.add-note-button`
- **根因**：`_note_exists()` 假阴性（3s 页面未渲染完 → 返回 False → 进 create 分支）
- **修复**：把 `page.wait_for_timeout(3000)` 替换为 `wait_for_selector(state="attached", timeout=45000)`（fetch 和 write 两处）

## 故障排查

| 症状 | 排查 |
|---|---|
| 日报/周报未触发 | `crontab -l` → `docker compose logs <svc>` |
| 日报抓取 0 字符（found 0/2 elements） | note 页面时序问题（9 月多次出现）：18:20 首抓失败常见，19:10 retry 兜底；手动重试 `docker compose run --rm worker`（成功后 19:10 自动跳过） |
| playwright Timeout | 先看 keepalive.log 历史，判断是否时段性抖动 → 调 timeout |
| bind mount 未生效 | 清 `__pycache__/`，语法校验后再跑 |
| 页面元素找不到 | NotebookLM UI 改版 → 更新选择器 + 备份旧版 `.bak` |
| _note_exists 假阴性 | 等待时间不够 → 增大 wait_for_selector timeout |

## 常用运维命令

```bash
# 手动跑一次 keepalive
docker compose run --rm keepalive

# 手动跑一次 fetch
docker compose run --rm fetch_today

# 手动跑一次 write
docker compose run --rm write_today

# 重启容器（不重建）
docker compose up -d

# 看 keepalive 日志
tail -f keepalive.log

# 预览哪些周报会被自动补推（不推送）
docker compose run --rm weekly-worker python -m src.repush_checker --dry-run

# 手动补推指定周报
docker compose run --rm weekly-worker python -m src.repush_checker --force W2026-09-07
```
