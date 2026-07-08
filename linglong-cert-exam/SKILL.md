---
name: 灵珑认证考核助手
description: |
  灵珑资深专家认证考核（大区灵珑资深专家认证）逐题配置助手。覆盖全部 5 道考题：
  必考一「领导看板」（40分，差错案件统计 ddcat + 看板筛选/指标/横向柱状图 + 跳转列表）、
  必考二「PC工作台」（40分，建筑垃圾联单监管：查询区 + 概览指标 + ECharts柱线趋势 + 列表导出跳转）、
  抽考三「移动流程」（20分，违建问题处置→核查→核实→办结全流程 + 5tab移动端）、
  抽考四「复杂视图公式打印」（20分，法规管理：联合树区域权限 + 文号规则公式 + 审核日志 + 打印预览）、
  抽考五「数据模型高级检索」（20分，巡检任务：API后置脚本扩展子表标签 + exists高级检索）。
  每题提供原题存档 + 配置手册（SOP步骤、SQL模板、JS脚本、公式写法、评分点对照checklist、常见坑）。
  触发词：灵珑认证 / 灵珑考核 / 灵珑资深专家 / 灵珑考试 / 领导看板考题 / PC工作台考题 /
  移动流程考题 / 复杂视图公式打印 / 数据模型高级检索 / linglong-cert / 灵珑必考 / 灵珑抽考。
---

# 灵珑资深专家认证考核助手

## 考核背景

「大区灵珑资深专家认证」由数字政通技术支持部组织，每年 4 月、9 月两次集中认证，目标是支撑
**年中灵珑自主交付率 50%、年终 70%**。报名门槛：持灵珑高级认证满 1 年 + 近 1 年主导 3 个以上
高复杂度配置案例。各大区每年至少 2 人通过。

考核模式：**必考 2 题（各 40 分）+ 随机抽考 1 题（20 分）**，总分 100。

| 题号 | 类型 | 题目 | 分值 | 核心考点 |
|------|------|------|------|----------|
| 一 | 必考 | 领导看板 | 40 | 2 个 ddcat SQL（统计+TOP5）、看板筛选/指标/横向柱状图、指标点击跳转列表带参 |
| 二 | 必考 | PC 工作台 | 40 | 查询区组合筛选、4 指标概览、ECharts 柱线混合趋势图（天/周/月切换）、列表导出+跳转 |
| 三 | 抽考 | 移动流程 | 20 | 流程模板（批转/退回）、流水号表单、启动流程公式、移动端 5 tab、办理页面 |
| 四 | 抽考 | 复杂视图公式打印 | 20 | 联合树+区域权限隔离、文号规则/UUID()等公式自动填入、审核写日志、打印预览 |
| 五 | 抽考 | 数据模型高级检索 | 20 | 主子表禁止联查→API 后置脚本扩展字段、全局变量存库名、exists 高级检索 |

## 使用方式

1. **确定题目**：用户说明在做哪道题（或描述题目特征，按上表匹配）。
2. **读对应配置手册**：`references/playbooks/题目N-xxx-配置手册.md`，按 SOP 步骤指导配置，
   SQL/JS/公式模板可直接复制后替换环境相关 id。
3. **需要原题细节时**：读 `references/exam/题目N-xxx-原题.md`（含完整表结构、字段要求、评分标准）。
4. **交卷前**：走配置手册末尾的「评分点对照 checklist」逐项自查。
5. **手册没覆盖的配置细节**：
   - 优先查本机 `linglong-guide` skill（`~/.claude/skills/linglong-guide/references/`，112 份实战文档）；
   - 再查 `references/知识库索引.md`，拿 nodeId 用 `mcp__dingtalk__get_document_content` 现场拉取钉钉知识库原文
     （注意：`mcp__dingtalk-wiki__read_document` 对该库权限不足，勿用）。

## 文件地图

```
linglong-cert-exam/
├── SKILL.md                      # 本文件
└── references/
    ├── 知识库索引.md              # 钉钉「灵珑」知识库全目录树 + nodeId（按需 MCP 拉原文）
    ├── exam/                     # 5 道考题原题存档（含表结构、评分标准）
    │   ├── 题目一-领导看板-原题.md
    │   ├── 题目二-PC工作台-原题.md
    │   ├── 题目三-移动流程-原题.md
    │   ├── 题目四-复杂视图公式打印-原题.md
    │   └── 题目五-数据模型高级检索-原题.md
    └── playbooks/                # 逐题配置手册（SOP + 模板 + checklist）
        ├── 题目一-领导看板-配置手册.md
        ├── 题目二-PC工作台-配置手册.md
        ├── 题目三-移动流程-配置手册.md
        ├── 题目四-复杂视图公式打印-配置手册.md
        └── 题目五-数据模型高级检索-配置手册.md
```

## 相关资源

- 配套 skill：`linglong-guide`（灵珑平台 112 份配置参考文档，本 skill 的知识底座）
- 考核说明文档：nodeId `amweZ92PV6vZaGX4TKoaoj2AVxEKBD6p`（灵珑资深专家认证考核说明）
- 考题文件夹：nodeId `ydxXB52LJq7l145giMPjgqQ3WqjMp697`（知识库「考题」目录，5 篇 adoc）
- 灵珑知识库根：nodeId `m9bN7RYPWdlgzjZLfbYgGo51WZd1wyK0`（workspace `Ao01nSxlxbbr3x8J`）
- 技能清单：nodeId `jb9Y4gmKWr7l1v5Mij052xKyVGXn6lpz`（灵珑配置专家技能清单）

## 关键 API 速查（考试高频）

| API | 用途 |
|-----|------|
| `api.DATA_SOURCE_EXECUTE(id, type, query, form, json)` | 调用数据源（ddcat/API） |
| `api.DATA_EXECUTOR().executeDataModelForList(id, param)` | 列表 Hook 使用数据模型 |
| `api.DATA_EXECUTOR().executeApiModelForList(id, type, param)` | 列表 Hook 使用 API 模型 |
| `api.EXEC_FORMULA(formula)` | 执行后端公式（UUID()、APP_CONST() 等） |
| `api.CONST["bd_var:xxx"]` / `this.$$getConstValue("bd_var:xxx")` | 读取全局静态变量 |
| `this.$$("component_id")` / `this.$$m("model_id")` | 查找页面组件 / 数据模型 |
| `${com.egova.lowcode.data.util.AppConstUtils::getValue("bd_var:xxx")}` | SQL 模板中取全局变量 |
| `${com.egova.lowcode.foundation.util.UserSessionUtils::getSessionVariable("id", true)}` | SQL 模板中取会话变量（登录人） |
