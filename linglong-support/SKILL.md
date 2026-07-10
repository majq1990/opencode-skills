---
name: 灵珑支持
description: |
  灵珑（LingLong）低代码平台一站式支持 skill，数字政通灵珑平台全部能力汇总（2026-07-10 由
  linglong-guide + linglong-cert-exam + egova-config-linglong-js 三个 skill 合并而成）。四大能力：
  ①配置场景库：112 份实战配置文档（动作交互/列表Hook/表单流程/SQL视图/工作台看板/地图/移动端/打印/性能/全局变量/Token/API管理等）；
  ②JS 脚本规范：表单/列表/页面交互/树组件脚本模板 + API 版本差异与代码审查清单；
  ③认证考核：灵珑资深专家认证 5 道考题原题 + 点击级配置手册（领导看板/PC工作台/移动流程/复杂视图公式打印/数据模型高级检索）；
  ④知识库检索：钉钉「灵珑」知识库 901 篇文档 nodeId 索引，按需 MCP 拉取原文；
  ⑤需求交付：给一个真实需求（文字描述/Redmine 案件号/设计文档链接），自动读取 Redmine 案件（含附件/journals）
  和钉钉设计文档，按标准工作流产出完整可实施的灵珑实施方案报告（数据设计 SQL/页面组件/脚本公式/流程/验收清单）。
  触发词：灵珑 / linglong / 低代码配置 / 列表hook / 数据视图 / ddcat / 表单设计 / 打印模板 / 工作台看板 /
  灵珑需求 / 灵珑方案 / 灵珑实施方案 / 灵珑报告 / redmine案件灵珑 / 设计文档出方案 /
  领导看板 / 流程表单 / 移动流程 / JS脚本 / SQL模板 / 会话变量 / 静态变量 / 全局变量 / ECharts图表 / 树部件 /
  卡片列表 / 高级搜索 / 高级检索 / 动作面板 / 灵珑认证 / 灵珑考核 / 灵珑考试 / 灵珑资深专家 / 灵珑脚本 /
  DATA_EXECUTOR / DATA_SOURCE_EXECUTE / 文号规则 / 打印预览 / API后置脚本 / 批量打印 / 明细表格 / iframe /
  地图轨迹 / 移动端看板 / 导航菜单 / Token配置 / 公式清单 / WithRecursive / 子表插入。
---

# 灵珑支持（LingLong Support）

灵珑是北京数字政通（EGOVA）的低代码应用搭建平台（可视化配置 + JS 脚本 + 后端公式）。
本 skill 是灵珑全部本地知识的总入口，按下面四条支线路由。

## 路由：先判断用户要做什么

| 用户意图 | 支线 | 入口 |
|---|---|---|
| 配置某个功能/场景（列表、表单、看板、地图、打印…） | ① 配置场景库 | `references/guide/`（先读 `guide/_索引.md` 找文档） |
| 写/调/优化 JS 脚本 | ② 脚本规范 | `references/scripting/` |
| 灵珑资深专家认证考试（做题/备考） | ③ 认证考核 | `references/exam/` + `references/playbooks/` |
| 以上没覆盖、要查官方知识库 | ④ 知识库检索 | `references/知识库索引.md` → MCP 拉原文 |
| **真实业务需求 → 完整实施方案报告**（给需求描述 / Redmine 案件 / 设计文档） | ⑤ 需求交付 | `references/需求交付-工作流.md` |

多条支线可叠加：例如考试中写脚本卡住 → playbook + scripting 一起用；需求交付会调用 ①②④ 全部资源。

## ⑤ 需求交付（references/需求交付-工作流.md）

真实需求的标准交付流：**需求采集 →拆解 → 历史避坑 → 方案生成 → 报告输出**。
- Redmine 案件：`mcp__redmine__redmine_request`（/issues/{id}.json?include=attachments,journals,relations）+ `redmine_download` 下附件
- 设计文档：钉钉 `get_document_content`（勿用 wiki read_document）；docx/pdf 附件用对应解析 skill
- 报告按模板成文（数据设计含完整 SQL / 页面组件清单 / 完整脚本公式 / 流程 / 验收清单 / 风险），存 `D:\opencode\file\yyyy-mm-dd\`
- 硬规则：缺关键输入先出「待确认清单」不编造表结构；每段 SQL/脚本完整可复制无"此处略"；禁引未定稿标准

## ① 配置场景库（references/guide/，112 份文档）

- **必读入口**：`references/guide/_索引.md` —— 112 份文档按 10 大类的完整分类索引
  （动作交互与脚本 / 列表部件 / 卡片与树 / 表单与流程 / 数据模型与SQL / 工作台与看板 / 地图 / 移动端 / 页面高级交互 / 平台高级配置），每份有内容概要和适用场景。
- 用法：按索引定位 1-3 份文档 → 读取 → 提取配置步骤/脚本模板/注意事项。
- 图片型文档（明细表格/数据视图）的原图在 `guide/_images/`。

## ② JS 脚本规范（references/scripting/，6 份文档）

| 文档 | 场景 |
|---|---|
| `components-api-reference.md` | 全局 API 速查：组件查找/消息/对话框/表单操作/看板赋值/路由参数 |
| `form-scripts-guide.md` | 表单脚本：API调用、组件操作、提交、AES加密、弹窗、麒舰刷新菜单 |
| `list-scripts-guide.md` | 列表脚本：Hook 查询与分页规范、刷新、字段样式、行高亮 |
| `page-interaction-guide.md` | 页面跳转/传参/生命周期/移动端特殊交互（附件/拨号/WebView） |
| `tree-component-guide.md` | 树组件 6 种联动场景 + 常用方法 |
| `best-practices.md` | 命名/结构/错误处理/防抖节流/移动端适配/调试 |

**核心约束（写任何灵珑脚本前先过一遍）**：
1. 函数第一行 `const self = this;`，后续用 self（function 回调里 this 会变）
2. 隐藏组件用 `$$m()` / `$$model()` 获取，`$$()` 找不到
3. 事件监听用 `$$addEventListener`，不用 `window.addEventListener`（防内存泄漏）
4. 删除确认用 `$$confirm`，不用 `modal.confirm`
5. Promise 必须有 `.catch()`；耗时操作有 loading 管理
6. 消息提示：PC 用 `$message`，移动端用 `$ztToast`；1.6.0 前后对话框 API 有差异

**⚠️ API 版本差异（重要）**：新版规范中 `api.DATA_SOURCE_EXECUTE` 已标废弃，推荐
`api.DATA_EXECUTOR()`；但存量环境（含大量官方文档和本 skill 的考试手册）仍用
`DATA_SOURCE_EXECUTE` 且可用。**以目标环境实测为准**：新环境优先 DATA_EXECUTOR，
旧环境照手册写法不必强改。

## ③ 认证考核（references/exam/ + references/playbooks/）

「大区灵珑资深专家认证」：每年 4/9 月，必考 2 题（各 40 分）+ 抽考 1 题（20 分），总分 100。

| 题号 | 题目 | 分值 | 手册 |
|---|---|---|---|
| 一（必考） | 领导看板（差错案件统计 ddcat+看板+跳转） | 40 | `playbooks/题目一-领导看板-配置手册.md` |
| 二（必考） | PC工作台（建筑垃圾联单：查询+概览+ECharts+列表） | 40 | `playbooks/题目二-PC工作台-配置手册.md` |
| 三（抽考） | 移动流程（违建问题处置→核查→核实→办结） | 20 | `playbooks/题目三-移动流程-配置手册.md` |
| 四（抽考） | 复杂视图公式打印（法规管理：联合树+公式+审核+打印） | 20 | `playbooks/题目四-复杂视图公式打印-配置手册.md` |
| 五（抽考） | 数据模型高级检索（API后置脚本+exists检索） | 20 | `playbooks/题目五-数据模型高级检索-配置手册.md` |

手册均为点击级操作（哪个菜单→点什么→属性怎么填→✅本步验证→⚠️注意事项），
SQL/JS/groovy/公式可直接复制（替换占位 ID），结尾有评分点 checklist 和排错速查。
原题（含完整表结构和评分标准）在 `references/exam/`。
**使用流程**：确定题号 → 读对应手册按步骤做 → 卡住查手册排错附录 → 交卷前走 checklist。

## ④ 知识库检索（references/知识库索引.md）

钉钉「灵珑」知识库全目录树（79 文件夹 / 901 文档，nodeId 级）。本地文档没覆盖时：
1. 在索引里按目录/文档名找到 nodeId；
2. 用 `mcp__dingtalk__get_document_content` 传 nodeId 拉取 markdown 原文；
3. **勿用** `mcp__dingtalk-wiki__read_document`（对该库 403，缺 Storage.File.Read 权限）。

关键 nodeId：知识库根 `m9bN7RYPWdlgzjZLfbYgGo51WZd1wyK0`（workspace `Ao01nSxlxbbr3x8J`）、
考题文件夹 `ydxXB52LJq7l145giMPjgqQ3WqjMp697`、考核说明 `amweZ92PV6vZaGX4TKoaoj2AVxEKBD6p`。

## 关键 API 速查（高频）

| API | 用途 |
|-----|------|
| `api.DATA_SOURCE_EXECUTE(id, type, query, form, json)` | 调用数据源（ddcat/API）；type="ddcat" 时 res.result 是数组，"api" 时是 JSON 字符串需 parse |
| `api.DATA_EXECUTOR().executeDataModelForList(id, param)` | 列表 Hook 使用数据模型（新版推荐入口） |
| `api.DATA_EXECUTOR().executeApiModelForList(id, "BUNCHES", param, {lostAbility})` | 列表 Hook 使用 API 模型（BUNCHES=灵珑API） |
| `api.EXEC_FORMULA(formula)` | 执行后端公式（UUID()/NOW()/INSERT()/UPDATE()/APP_CONST() 等） |
| `api.CONST["bd_var:xxx"]` / `this.$$getConstValue("bd_var:xxx")` | 读取全局静态变量 |
| `this.$$("id")` / `this.$$element("id")` / `this.$$m("id")` | 向下查找 / 向上查找 / 取隐藏组件模型 |
| `${com.egova.lowcode.data.util.AppConstUtils::getValue("bd_var:xxx")}` | SQL 模板/后置脚本取全局变量 |
| `${com.egova.lowcode.foundation.util.UserSessionUtils::getSessionVariable("id", true)}` | SQL 模板取会话变量（登录人） |
| `FLOW_START(流程表单页面id, 文号)` | 表单执行后公式：提交自动启动流程 |

## 目录结构

```
linglong-support/
├── SKILL.md                  # 本文件（总路由）
└── references/
    ├── guide/                # ① 112 份配置场景文档（_索引.md 为分类目录，_images/ 为图片）
    ├── scripting/            # ② 6 份 JS 脚本规范（_原SKILL说明.md 为原始工作流）
    ├── exam/                 # ③ 5 道认证考题原题
    ├── playbooks/            # ③ 5 份点击级配置手册
    ├── 知识库索引.md          # ④ 钉钉知识库 901 篇 nodeId 索引
    └── 需求交付-工作流.md     # ⑤ 需求→实施方案报告的标准流程与报告模板
```

## 来源与维护

- 2026-07-08：linglong-guide（桌面 .skill 包，112 文档）+ linglong-cert-exam（考题手册+索引）落地
- 2026-07-10：合并 egova-agent-skills 仓库的 egova-config-linglong-js（JS 脚本规范），三合一为本 skill
- 旧的 linglong-guide / linglong-cert-exam 两个独立 skill 已移除（git 历史可找回）
