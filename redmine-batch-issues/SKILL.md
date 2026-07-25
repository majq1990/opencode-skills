---
name: redmine-batch-issues
description: 从 Excel 功能清单批量创建 Redmine Issue。触发词：批量提案、Redmine批量、功能清单导入、项目建设内容匹配分析、批量创建issue、批量提交案件。当用户提供 Excel 文件并希望将未完成项提交到 Redmine 时使用。
author: majianquan
version: 1.0.0
license: MIT
compatibility: opencode
metadata:
  category: project-management
  platform: redmine
  features: excel-import,batch-issue-creation,redmine
---

# Redmine 批量提案助手

从项目建设内容匹配分析 Excel 中，筛选未完成项，批量创建 Redmine Issue。

基于 [runekaagaard/mcp-redmine](https://github.com/runekaagaard/mcp-redmine) MCP Server，每个用户使用自己的 Redmine API Key。

## 适用场景

- 用户提供一份项目功能清单 Excel（如"E3级-天津河西区运管服和市容环境综合整治平台对接 项目建设内容匹配分析.xlsx"）
- 需要将"是否完成"不为"是"的条目，逐条提交为 Redmine Issue
- 支持预览、确认、批量创建、结果汇总

---

## 1. 前置检查（首次使用引导）

每次执行前，必须按顺序完成以下检查：

### 1.0 本机快速通道（已配置则跳过 1.2~1.3）

先读 `~/.workbuddy/mcp.json`，若已含 `redmine` 条目且 env 内 `REDMINE_URL` / `REDMINE_API_KEY` 齐全，**跳过 API Key 与安装引导**，直接执行 1.4 连通性验证即可。

### 1.1 检查 MCP redmine 是否可用

调用 MCP redmine 的 `redmine_request` 工具（path: `/projects.json`, method: GET），若能返回项目列表则连通正常。

**如果 MCP 未配置或连接失败**，引导用户按以下步骤操作：

### 1.2 获取 Redmine API Key

1. 打开浏览器，访问 `https://faq.egova.com.cn:7787/`
2. 登录你的 Redmine 账号
3. 点击右上角 **"我的账户"**
4. 页面右侧找到 **"API访问键"**
5. 点击 **"显示"** 获取你的 Key（如果没有则点"重置"生成一个）
6. 复制 API Key

### 1.3 配置 MCP

在 `~/.workbuddy/mcp.json` 中添加 redmine 配置：

```json
{
  "mcpServers": {
    "redmine": {
      "command": "node",
      "args": ["<mcp-server-redmine 路径>"],
      "env": {
        "REDMINE_URL": "https://faq.egova.com.cn:7787",
        "REDMINE_API_KEY": "<你的API Key>"
      },
      "type": "stdio",
      "description": "Redmine 项目管理系统 - 用于需求、问题和项目管理"
    }
  }
}
```

> 如果使用 uvx 方式，可参考：
> ```json
> {
>   "command": "<uvx.exe的完整路径>",
>   "args": ["--index-url", "https://mirrors.aliyun.com/pypi/simple/", "--from", "mcp-redmine", "mcp-redmine"],
>   "env": {
>     "REDMINE_URL": "https://faq.egova.com.cn:7787",
>     "REDMINE_API_KEY": "<你的API Key>",
>     "REDMINE_DANGEROUSLY_ACCEPT_INVALID_CERTS": "1"
>   }
> }
> ```

### 1.4 验证连通性

配置完成后，重启 WorkBuddy，然后调用 MCP redmine 工具验证连通性。若返回项目列表，即可继续。

---

## 2. MCP 工具说明（runekaagaard/mcp-redmine）

本 Skill 使用以下 MCP 工具：

### redmine_request（核心工具）

执行 Redmine REST API 调用。

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| path | string | 是 | API 路径，如 `/issues.json`、`/projects.json` |
| method | string | 否 | HTTP 方法，默认 GET。创建用 POST |
| data | object | 否 | 请求体（POST/PUT 时使用） |
| params | object | 否 | 查询参数 |

#### 常用调用示例

**获取项目列表：**
```
redmine_request(path="/projects.json", method="GET")
```

**创建 Issue：**
```
redmine_request(
  path="/issues.json",
  method="POST",
  data={
    "issue": {
      "project_id": 123,
      "subject": "[悟空大屏] 智能采集专题场景",
      "description": "功能描述内容..."
    }
  }
)
```

**搜索 Issue：**
```
redmine_request(path="/issues.json", method="GET", params={"project_id": 123, "limit": 25})
```

### redmine_paths_list

列出所有可用的 Redmine API 路径。无需参数。

### redmine_paths_info

获取特定 API 路径的详细规格说明。

---

## 3. Excel 格式规范

### 支持的标准列结构

| 列 | 表头 | 说明 | 是否必需 |
|----|------|------|----------|
| A | 合同交付系统 | 所属系统/模块分类 | 是 |
| B | 合同交付模块名称 | 具体模块名称 | 是 |
| C | 投标文件功能描述 | 功能的详细描述 | 否 |
| D | 交付的标准模块名称 | 对应的标准产品模块 | 否 |
| E | 是否标品 | 标品/定制开发 | 否 |
| F | 定开分析 | 定制开发分析说明 | 否 |
| G | 是否完成 | **关键列**：值为"是"则跳过，否则创建 Issue | 是 |

### 筛选规则

- **创建 Issue 条件**：`是否完成` 列的值**不是** `"是"`（包括"否"、空值、其他任何值）
- **跳过条件**：`是否完成` 列的值**精确等于** `"是"`

### 容错处理

- 表头行自动识别（第一行）
- 支持列顺序不固定（按表头名称匹配）
- 空行自动跳过
- 支持多 Sheet（默认取第一个 Sheet，用户可指定）

---

## 4. 批量创建流程

**严格按以下步骤执行，不得跳过任何步骤：**

### Step 1: 读取 Excel

```python
import openpyxl

wb = openpyxl.load_workbook(excel_path)
ws = wb.active  # 或用户指定的 sheet
headers = [cell.value for cell in ws[1]]

records = []
for row in ws.iter_rows(min_row=2, values_only=True):
    record = dict(zip(headers, row))
    if not any(row):
        continue
    records.append(record)
```

### Step 2: 筛选未完成项

```python
to_create = []
for record in records:
    completion = str(record.get('是否完成', '')).strip()
    if completion != '是':
        to_create.append(record)
```

### Step 3: 确定目标项目

- 用户提供项目名称或项目编号
- 调用 `redmine_request(path="/projects.json")` 获取项目列表，按名称/编号匹配
- 展示匹配结果，请用户确认目标 `project_id`
- 如果用户直接提供了 project_id，跳过查询直接使用

### Step 4: 预览待创建 Issue 列表

以表格形式展示待创建的 Issue：

```
| # | Subject | 系统 | 模块 | 是否标品 | 当前状态 |
|---|---------|------|------|----------|----------|
| 1 | [悟空大屏] 智能采集专题场景 | 悟空大屏 | 智能采集专题场景 | 定制开发 | 否 |
| 2 | ... | ... | ... | ... | ... |
```

**必须展示以下信息并等待用户确认：**
- 总共读取 X 条记录
- 已完成（跳过）X 条
- 待创建 X 条
- 目标项目：XXX（project_id: XX）

### Step 5: 用户确认后批量创建

逐条调用 MCP `redmine_request` 工具创建 Issue：

```
redmine_request(
  path="/issues.json",
  method="POST",
  data={
    "issue": {
      "project_id": <用户选定的项目ID>,
      "subject": "[{合同交付系统}] {合同交付模块名称}",
      "description": "## 投标文件功能描述\n\n{投标文件功能描述}\n\n## 交付信息\n\n- **交付的标准模块**：{交付的标准模块名称}\n- **是否标品**：{是否标品}\n- **定开分析**：{定开分析}\n\n---\n*由 Redmine 批量提案助手自动创建*"
    }
  }
)
```

**创建规则：**
- 每条创建后记录结果（成功/失败+原因）
- 如果连续失败 3 次，暂停并询问用户

### Step 6: 结果汇总

创建完成后，输出汇总报告：

```
## 批量创建结果

- 总记录数：20
- 跳过（已完成）：5
- 成功创建：13
- 创建失败：2

### 失败详情
| # | Subject | 错误原因 |
|---|---------|----------|
| 8 | [XX系统] XX模块 | 项目无权限 |

### 已创建 Issue 列表
| # | Issue ID | Subject | 链接 |
|---|----------|---------|------|
| 1 | #1234 | [悟空大屏] 智能采集专题场景 | https://faq.egova.com.cn:7787/issues/1234 |
```

---

## 5. Issue 字段映射规则

| Redmine 字段 | 映射来源 | 格式 |
|-------------|----------|------|
| `subject` | 合同交付系统 + 合同交付模块名称 | `[{系统}] {模块名称}` |
| `description` | 投标文件功能描述 + 交付信息 | Markdown 格式 |
| `project_id` | 用户指定 | 整数 |
| `tracker_id` | 默认不指定（使用项目默认 tracker） | 可选，用户可指定 |

### Subject 生成规则

- 如果"合同交付系统"和"合同交付模块名称"都有值：`[{合同交付系统}] {合同交付模块名称}`
- 如果只有"合同交付模块名称"：直接使用模块名称
- 如果只有"合同交付系统"：使用系统名称
- subject 最长 255 字符，超出则截断

### Description 模板

```markdown
## 投标文件功能描述

{投标文件功能描述的完整内容}

## 交付信息

| 项目 | 内容 |
|------|------|
| 交付的标准模块 | {交付的标准模块名称} |
| 是否标品 | {是否标品} |
| 定开分析 | {定开分析} |

---
*由 Redmine 批量提案助手自动创建*
```

---

## 6. 安全约束

1. **创建前必须预览确认**：绝不跳过预览直接创建
2. **单次上限 50 条**：超过 50 条时分批，每批确认
3. **dry-run 模式**：用户说"预览"或"测试"时只展示不创建
4. **失败熔断**：连续 3 次失败则暂停，等待用户指示
5. **不修改已有 Issue**：本 skill 只创建新 Issue，不更新/删除已有 Issue
6. **不重复创建**：如果用户再次执行同一份 Excel，提醒可能重复
7. **改 MCP 配置前必须备份**：若需变更 `~/.workbuddy/mcp.json`（例如新增 / 修改 redmine env），必须先复制为 `<file>.backup.<yyyyMMdd-HHmmss>` 再写

---

## 7. 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `KeyError: 'REDMINE_URL'` | `.mcp.json` 中未配置环境变量 | 检查 env 中 REDMINE_URL 和 REDMINE_API_KEY |
| MCP 工具不可用 | uv/uvx 未安装或路径错误 | 运行 `pip install uv`，确认 uvx.exe 路径 |
| SSL 证书错误 | 自签名证书 | 设置 `REDMINE_DANGEROUSLY_ACCEPT_INVALID_CERTS=1` |
| 创建 Issue 返回 403 | API Key 无创建权限 | 联系 Redmine 管理员开通权限 |
| Excel 读取失败 | 文件格式不对或表头不匹配 | 确认 Excel 包含标准列（见格式规范） |
| 找不到目标项目 | project_id 错误 | 调用 `redmine_request(path="/projects.json")` 查看可用项目 |
| PyPI 下载超时 | 网络问题 | 使用阿里云镜像：`--index-url https://mirrors.aliyun.com/pypi/simple/` |
