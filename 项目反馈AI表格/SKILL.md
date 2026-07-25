---
name: project-feedback-aitable
description: 从 ztoa 工程实施项目数据创建钉钉 AI 项目反馈表。用户给项目名称清单、项目编号清单或表格文件，再给反馈内容时使用；自动通过 ztoa MCP 获取项目大区、项目区域、项目名称、项目经理、项目销售经理、省份总、大区总、片区总，调用钉钉 AI 表格能力在指定知识库建立反馈表，写入反馈处理情况、截图证明、处理人、处理时间和可见人员字段。触发词：项目反馈表 / AI反馈表格 / 项目问题跟踪 / 按项目反馈 / ztoa项目清单 / project-feedback-aitable。
---

# 项目反馈 AI 表格

## 固定目标

把一批项目转成钉钉 AI 表格反馈台账。默认知识库/文件夹节点：

`https://alidocs.dingtalk.com/i/nodes/lyQod3RxJK3moqXKip330KX5Jkb4Mw9r`

输入可以是：
- 项目名称列表
- 项目编号列表
- Excel/CSV/表格文件，其中包含项目名称或项目编号列

用户还必须给一段「反馈内容」。没有反馈内容时先追问一句。

## 工作流

1. 解析输入清单，归一化为 `项目名称[]` 或 `项目编号[]`。
2. 调 `mcp__ztoa__`，先 `whoami`，再 `get_worksheet_schema` 确认字段，最后 `query_records` 查项目。
3. 对每个项目补齐：项目大区、项目区域、项目名称、项目编号、项目经理、项目销售经理、省份总、大区总、片区总。
4. 将 ztoa 成员姓名/accountId 映射到钉钉 AI 表格 `user` 字段可写的 `userId`。优先复用项目字段里已有 userId；缺失时用 `dws contact user search` 按姓名查。
5. 生成 `D:\opencode\_archive\<topic>_project_feedback\projects_enriched.json`，先给用户预览项目数、未匹配项目、未匹配人员。
6. 用户确认后运行 `scripts/create_aitable.py` 创建 AI 表格并批量写入记录。
7. 创建后用钉钉 MCP `move_document` 将 baseId 对应节点移动到固定知识库节点下。
8. 权限限制：自动写入「可见人员」字段；如果当前 `dws`/MCP 没有行级权限 API，必须明确提示“行级可见规则待在钉钉前端或后续权限 API 配置”，不要声称已完成限制。

## 输出字段

基础字段：
- 项目编号
- 项目名称
- 项目大区
- 项目区域
- 项目经理
- 项目销售经理
- 省份总
- 大区总
- 片区总

反馈字段：
- 反馈内容
- 反馈处理情况：单选，默认选项 `无需处理`、`已经处理`；用户给其他选项时追加
- 反馈处理截图证明：附件
- 反馈处理人：成员
- 反馈处理时间：日期时间
- 可见人员：成员多选，写入项目经理、省份总、大区总、片区总，必要时追加项目销售经理

## ztoa 查询规则

优先读取 [references/ztoa-fields.md](references/ztoa-fields.md)。

必须使用 `mcp__ztoa__`：
- `get_worksheet_schema`：确认 `交付项目` 与 `大区省份表-琅琊榜特殊使用` 字段是否仍存在。
- `query_records`：查询项目和区域责任人。

项目匹配：
- 项目名称：对「项目名称」做 Like；多个候选时优先项目状态为 `打开` 的记录。
- 项目编号：优先精确匹配 schema 中名字含 `项目编号` / `项目编码` / `编号` 的字段；找不到时匹配 `autoid` 或关联项目信息中的编号字段，并把不确定项列入预览。

区域责任人匹配：
- 用项目 `大区 + 区域` 去「大区省份表-琅琊榜特殊使用」匹配。
- 只使用 `是否可用 == 是` 的记录。
- `大区总` = `大区责任人`
- `省份总` = `省份责任人`
- `片区总` = `片区工程责任人`

## AI 表格创建

准备一个 plan：

```json
{
  "topic": "某次专项反馈",
  "base_name": "某次专项反馈-项目反馈表",
  "feedback_content": "请各项目确认处理情况并上传截图。",
  "status_options": ["无需处理", "已经处理"],
  "knowledge_node_id": "lyQod3RxJK3moqXKip330KX5Jkb4Mw9r"
}
```

运行：

```powershell
cd D:\opencode\config\skills\project-feedback-aitable
python .\scripts\create_aitable.py D:\opencode\_archive\<topic>_project_feedback\plan.json D:\opencode\_archive\<topic>_project_feedback\projects_enriched.json
```

脚本产出 `table_meta.json`，其中包含 `baseId`、`tableId`、字段 ID 和访问链接。

## 注意

- 单次 `record create` 最多 30 条，脚本默认 20 条一批。
- `dws aitable record create` 的 key 必须是 fieldId，不能用字段名。
- 附件字段只建字段，不预填截图；后续填表人上传。
- 行级可见控制必须验证后再向用户报告完成。当前自动部分是写入「可见人员」字段和权限配置计划。
