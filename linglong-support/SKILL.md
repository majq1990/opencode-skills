---
name: 灵珑支持
description: |
  灵珑（LingLong）低代码平台一站式支持 skill，数字政通灵珑平台全部能力汇总（2026-07-10 由
  linglong-guide + linglong-cert-exam + egova-config-linglong-js 三个 skill 合并而成）。四大能力：
  ①配置场景库：112 份实战配置文档（动作交互/列表Hook/表单流程/SQL视图/工作台看板/地图/移动端/打印/性能/全局变量/Token/API管理等）；
  ②JS 脚本规范：表单/列表/页面交互/树组件脚本模板 + API 版本差异与代码审查清单；
  ③配置方法论 + 手册生成：5 类配置方法论（领导看板/PC工作台/移动流程/复杂视图公式打印/数据模型高级检索）作为可复用资产，
  面对具体考题或配置场景，按方法论生成点击级配置手册成果物（输出到 file 目录）；含灵珑资深专家认证备考；samples/ 存 5 份生成范例；
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
本 skill 是灵珑全部本地知识的总入口，按下面五条支线路由。

**核心理念**：skill 内置的是**知识与生成能力**（配置文档 + 脚本规范 + 5 类配置方法论 + 生成工作流），
不是固定答案。**手册 / 方案 / 报告都是"成果物"——按输入现生成、输出到 `D:\opencode\file\yyyy-mm-dd\`**，
不焊死进 skill。`samples/` 里的 5 份考题手册只是"生成出来长什么样"的对照范例，不是标准答案库。

## 路由：先判断用户要做什么

| 用户意图 | 支线 | 入口 |
|---|---|---|
| 配置某个功能/场景（列表、表单、看板、地图、打印…） | ① 配置场景库 | `references/guide/`（先读 `guide/_索引.md` 找文档） |
| 写/调/优化 JS 脚本 | ② 脚本规范 | `references/scripting/` |
| **给一道考题/一个配置场景 → 生成配置手册成果物**（含认证备考） | ③ 配置方法论 + 手册生成 | `references/methodology/` + `references/手册生成-工作流.md` |
| 以上没覆盖、要查官方知识库 | ④ 知识库检索 | `references/知识库索引.md` → MCP 拉原文 |
| **真实业务需求 → 完整实施方案报告**（给需求描述 / Redmine 案件 / 设计文档） | ⑤ 需求交付 | `references/需求交付-工作流.md` |

多条支线可叠加：例如生成手册时写脚本卡住 → methodology + scripting 一起用；③⑤ 都会调用 ①②④ 全部资源。
③ 和 ⑤ 同一条逻辑——**给输入、按方法论生成成果物**，区别只是考题场景 vs 真实需求场景。

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

## ③ 配置方法论 + 手册生成（references/手册生成-工作流.md）

**一份工作流文档搞定**：内含五类配置方法论要点 + 可复用骨架（附录 A1~A5），以及"场景 → 手册成果物"的标准流程。

五类：**领导看板 / PC工作台 / 移动流程 / 复杂视图公式打印 / 数据模型高级检索**。每类给了：施工顺序、
SQL 模式模板、跟具体表无关的 JS/groovy/公式骨架（照抄换占位 ID）、通用坑清单。

**使用流程**：给一道**具体考题**或**配置场景** → ① 场景识别选类别 → ② 采集输入(题目原文/表结构/评分标准) →
③ 套用生成(骨架照抄换占位 ID，SQL 按模式填本题表字段) → ④ 成型点击级手册(操作步骤+完整代码+评分/验收 checklist+坑) →
⑤ **输出独立 md 成果物到 `D:\opencode\file\yyyy-mm-dd\`，不写回 skill**。

- **认证考核背景**：「大区灵珑资深专家认证」每年 4/9 月，必考 2 题（各 40 分：领导看板/PC工作台）+ 抽考 1 题（20 分：移动流程/复杂视图公式打印/数据模型高级检索 三选一），总分 100。
- **成熟范例**：`D:\opencode\file\2026-07-10\灵珑配置手册\`（2026 版 5 道考题生成的手册，各 760~914 行 + 配套原题）——展示"生成出来长什么样"，可作结构模板；**新题不要直接抄它们的 SQL/表名**。
- ⚠️ 考题每年更换、表结构会变——**手册是每次现生成的独立成果物文件，不是 skill 里的固定文档**。

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
└── references/               # skill 只存「能力资产」，成果物不进 skill
    ├── guide/                # ① 112 份配置场景文档（_索引.md 为分类目录，_images/ 为图片）
    ├── scripting/            # ② 6 份 JS 脚本规范（_原SKILL说明.md 为原始工作流）
    ├── 手册生成-工作流.md     # ③ 五类方法论要点+骨架(附录A1~A5) + 场景→手册成果物流程
    ├── 知识库索引.md          # ④ 钉钉知识库 901 篇 nodeId 索引
    └── 需求交付-工作流.md     # ⑤ 需求 → 实施方案报告的标准流程与报告模板
```

> **成果物（手册/方案/报告）不进 skill**，输出到 `D:\opencode\file\yyyy-mm-dd\`。
> skill 只存"生成能力"（配置文档 / 脚本规范 / 方法论工作流）；方法论有改进（新坑/新写法）才更新工作流的附录。
> 2026 版 5 道考题的成熟手册范例：`D:\opencode\file\2026-07-10\灵珑配置手册\`。

## 来源与维护

- 2026-07-08：linglong-guide（桌面 .skill 包，112 文档）+ linglong-cert-exam（考题手册+索引）落地
- 2026-07-10：合并 egova-agent-skills 仓库的 egova-config-linglong-js（JS 脚本规范），三合一为本 skill
- 旧的 linglong-guide / linglong-cert-exam 两个独立 skill 已移除（git 历史可找回）
