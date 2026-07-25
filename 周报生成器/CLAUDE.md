# Report Automation Skill

自动从 NotebookLM 读取工作日志，生成结构化日报和周报，并自动提交到钉钉。

---

## 文件存储规范（全局要求）

**所有生成的文件必须按日期存储到 `D:\opencode\file\{日期}` 目录**

### 目录结构

```
D:\opencode\file\
├── 20260404\           # 日期目录（YYYYMMDD格式）
│   ├── 日报_260403.md  # 当天生成的日报
│   └── 周报_260404.md  # 当天生成的周报
├── 20260405\           # 下一天的目录
│   └── 日报_260404.md
└── ...
```

### 规则

1. **目录命名**：使用 `YYYYMMDD` 格式（如 `20260404`）
2. **自动创建**：脚本会自动创建日期目录（如果不存在）
3. **文件命名**：
   - 日报：`日报_{日期}.md`（如 `日报_260403.md`）
   - 周报：`周报_{日期}.md`（如 `周报_260404.md`）

### 代码实现

```python
import os
from datetime import datetime

BASE_DIR = r"D:\opencode\file"

def get_file_dir() -> str:
    """获取文件保存目录（按日期）"""
    today = datetime.now().strftime("%Y%m%d")
    file_dir = os.path.join(BASE_DIR, today)
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    return file_dir
```

---

## 功能特性

- **日报自动生成**：每天10点自动读取前一天的 NotebookLM 日志，生成工程技术中心日报
- **周报自动生成**：每周日20点自动读取本周所有日志，生成工程技术中心周报
- **智能内容分类**：自动按工作类别归类（住建部项目、AI技术、团队管理、质量运维等）
- **自动推送通知**：通过 Webhook 机器人推送完成通知到钉钉群
- **指定接收人**：自动发送给吴江寿、赵明明、王洪深、凌灿、吴昊

---

## 任务时间表

| 任务 | 执行时间 | 执行脚本 | 功能 |
|------|----------|----------|------|
| 日报 | 每天 10:00 | `daily-report-auto.py` | 读取前一天日志，生成日报 |
| 周报 | 每周日 20:00 | `weekly-report-auto.py` | 读取本周日志，生成周报 |

---

## 快速开始

### 1. 手动生成日报

```bash
# 生成昨天日报
python D:\opencode\daily-report-auto.py
```

### 2. 手动生成周报

```bash
# 生成本周周报
python D:\opencode\weekly-report-auto.py
```

### 3. 设置自动定时任务（以管理员身份运行）

```powershell
D:\opencode\setup-report-tasks.ps1
```

---

## 配置说明

### 固定配置（在脚本中修改）

```python
# NotebookLM 配置
NOTEBOOK_ID = "5019bce9-3d40-43e3-9abe-a2538bb0d285"

# 模板 ID
DAILY_TEMPLATE_ID = "194ee9d353b28b20dd6343a461394d83"   # 工程技术中心日报
WEEKLY_TEMPLATE_ID = "18e88a8d4b5b557015800b74ca7bbbfa"  # 工程技术中心周报

# Webhook 机器人
WEBHOOK_TOKEN = "261f9a593279dd8964da0588f94199be7d32b9399a748cade442e1bb40171419"
WEBHOOK_KEYWORD = "AI"

# 接收人 userId
RECEIVERS = [
    "1668256621598900",   # 吴江寿
    "061543134735636725", # 赵明明
    "022265434729319890", # 王洪深
    "1865386565677939",   # 凌灿
    "0243204459694358"    # 吴昊
]
```

---

## 日报模板

提交到钉钉的日报包含以下字段：

| 字段 | 内容来源 |
|------|----------|
| 今日工作总结 | 从日志提取的工作内容（按关键词分类） |
| 待协调的事项 | 包含"沟通"、"协调"、"待"、"需"等关键词的条目 |
| 未完成工作 | 固定为"无" |
| 明日工作计划 | 包含"计划"、"明天"、"后续"等关键词的条目 |

### 日报逻辑

- 每天10点执行
- 查找前一天的日志（如4月4日10点找4月3日的日志260403）
- 如果未找到日志，不提交，仅发送 Webhook 通知

---

## 周报模板

提交到钉钉的周报包含以下字段：

| 字段 | 说明 |
|------|------|
| 大区、区域、填报日期 | 西北大区 / 工程技术中心 / 日期范围 |
| 本周完成工作 | 按工作类别分类，包含三段论 |
| 本周工作总结 | 收获与待解决问题 |
| 下周工作计划 | 下周主要工作 |
| 需协调与帮助 | 需要支持的事项 |

### 周报逻辑

- 每周日20点执行
- 查找本周（周一至周日）的所有日志
- 按类别归类工作内容
- 三段论格式：做了什么工作、取得什么结果、需要协调的事项

---

## 日志命名规范

NotebookLM 中的日志必须按以下格式命名：

```
260403  →  2026年4月3日
260404  →  2026年4月4日
260330  →  2026年3月30日
```

格式：**年份后两位 + 月份(2位) + 日期(2位)**

---

## 文件清单

| 文件 | 说明 |
|------|------|
| `weekly-report-auto.py` | 周报生成主脚本（Python） |
| `weekly-report-run.ps1` | 周报启动脚本（PowerShell） |
| `daily-report-auto.py` | 日报生成主脚本（Python） |
| `daily-report-run.ps1` | 日报启动脚本（PowerShell） |
| `setup-report-tasks.ps1` | Windows 任务计划设置脚本 |
| `CLAUDE.md` | 本文档 |
| `skill.json` | Skill 配置文件 |

---

## 安装部署

### 前置要求

1. Python 3.x 已安装
2. `notebooklm-py` 已安装：`pip install notebooklm-py`
3. `dws` 钉钉 skill 已配置并认证
4. NotebookLM 已登录认证：`notebooklm login`

### 步骤

1. **确保所有脚本在 `D:\opencode\` 目录**

2. **以管理员身份运行 PowerShell，执行设置脚本：**

```powershell
D:\opencode\setup-report-tasks.ps1
```

3. **验证任务是否创建成功：**

```powershell
Get-ScheduledTask -TaskName "*Report*"
```

预期输出：
```
TaskName           State   NextRunTime
--------           -----   -----------
DailyReport-Auto   Ready   2026/04/05 10:00:00
WeeklyReport-Auto  Ready   2026/04/06 20:00:00
```

---

## 任务管理

### 查看任务状态

```powershell
# 查看所有报告任务
Get-ScheduledTask -TaskName "*Report*"

# 查看上次运行时间
(Get-ScheduledTask -TaskName "WeeklyReport-Auto").LastRunTime
(Get-ScheduledTask -TaskName "DailyReport-Auto").LastRunTime

# 查看下次运行时间
(Get-ScheduledTask -TaskName "WeeklyReport-Auto").NextRunTime
(Get-ScheduledTask -TaskName "DailyReport-Auto").NextRunTime
```

### 禁用任务

```powershell
# 禁用日报
Disable-ScheduledTask -TaskName "DailyReport-Auto"

# 禁用周报
Disable-ScheduledTask -TaskName "WeeklyReport-Auto"
```

### 启用任务

```powershell
# 启用日报
Enable-ScheduledTask -TaskName "DailyReport-Auto"

# 启用周报
Enable-ScheduledTask -TaskName "WeeklyReport-Auto"
```

### 删除任务

```powershell
Unregister-ScheduledTask -TaskName "DailyReport-Auto"
Unregister-ScheduledTask -TaskName "WeeklyReport-Auto"
```

---

## Webhook 通知

任务完成后，会通过 Webhook 机器人推送通知到钉钉群。

### 通知内容示例

**日报通知：**
```
AI日报生成完成

日期: 260404
数据来源: NotebookLM 日报
接收人: 吴江寿、赵明明、王洪深、凌灿、吴昊
状态: ✅ 已提交并存档
reportId: xxx

今日工作摘要:
- 完成系统更新和验证
- 研究AI中转方案
- 人员沟通协调
```

**周报通知：**
```
AI周报生成完成

周期间: 260330 - 260405
数据来源: 5 条日志
接收人: 吴江寿、赵明明、王洪深、凌灿、吴昊
状态: ✅ 已提交并存档
reportId: xxx
```

---

## 故障排查

### 1. 任务未执行

**检查步骤：**

```powershell
# 1. 检查任务是否存在
Get-ScheduledTask -TaskName "DailyReport-Auto"

# 2. 检查任务状态
(Get-ScheduledTask -TaskName "DailyReport-Auto").State

# 3. 查看任务历史记录
# 打开"任务计划程序" → "任务计划程序库" → 找到任务 → "历史记录"选项卡
```

**常见原因：**
- 用户未登录（任务设置为"只在用户登录时运行"）
- 计算机处于睡眠状态
- 脚本执行权限不足

### 2. 脚本执行失败

**手动测试：**

```powershell
# 测试日报
D:\opencode\daily-report-run.ps1

# 测试周报
D:\opencode\weekly-report-run.ps1
```

**查看错误输出：**

脚本执行日志保存在 Windows 事件查看器中，或修改脚本添加日志记录。

### 3. NotebookLM 认证失败

```bash
# 重新登录
notebooklm login

# 验证登录状态
notebooklm status
```

### 4. dws 认证失败

```bash
# 检查 dws 状态
dws status

# 重新认证（如果需要）
# 按照 dws skill 文档重新配置
```

### 5. Webhook 发送失败

**检查事项：**
- Token 是否有效
- 机器人是否在群聊中
- 消息内容是否包含关键词 "AI"
- 网络连接是否正常

**测试 Webhook：**

```bash
dws chat message send-by-webhook --token "261f9a593279dd8964da0588f94199be7d32b9399a748cade442e1bb40171419" --title "测试" --text "AI测试消息"
```

### 6. 未找到日志

**检查：**

```bash
# 查看 NotebookLM 中的 sources
notebooklm source list --notebook 5019bce9-3d40-43e3-9abe-a2538bb0d285
```

**确保：**
- 日志标题格式正确（260403）
- 日志在正确的 notebook 中
- 日志状态为 "ready"

---

## 高级配置

### 修改执行时间

编辑 `setup-report-tasks.ps1`：

```powershell
# 日报时间（默认每天10:00）
$dailyTrigger = New-ScheduledTaskTrigger -Daily -At "10:00"

# 周报时间（默认每周日20:00）
$weeklyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "20:00"
```

重新运行设置脚本。

### 修改接收人

编辑 `daily-report-auto.py` 和 `weekly-report-auto.py`：

```python
RECEIVER_USER_IDS = [
    "1668256621598900",   # 用户1
    "061543134735636725", # 用户2
    # 添加或删除 userId
]
```

### 添加更多通知渠道

可以在脚本中添加企业微信、飞书等其他通知方式。

---

## 更新日志

### v1.0.0 (2026-04-04)

- ✅ 日报自动生成功能
- ✅ 周报自动生成功能
- ✅ Windows 任务计划集成
- ✅ Webhook 通知推送
- ✅ 指定接收人功能
- ✅ 智能内容分类

---

## 作者

- **作者**: majq1
- **创建日期**: 2026-04-04

---

## 依赖

- [notebooklm-py](https://github.com/teng-lin/notebooklm-py) - NotebookLM 自动化
- [dws](https://github.com) - 钉钉产品能力 Skill
