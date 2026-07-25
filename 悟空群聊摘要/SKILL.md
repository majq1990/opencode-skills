---
name: wukong-doc-group-chat-summary
description: >
  将钉钉群聊消息提取、分析并生成结构化钉钉云文档摘要，涵盖议题、决策、行动项与风险。
  Use when user mentions "总结群聊", "群消息摘要", "整理群讨论",
  or asks to "帮我总结一下群里的聊天", "把群消息整理成文档", "群里最近讨论了啥".
  Distinct from wukong-doc-meeting-minutes (会议纪要基于会议录音而非群聊消息)
  and wukong-approval-reminder (审批催办而非消息总结).
  Do NOT use for 会议录音总结, 单聊消息整理, 群管理操作(建群/拉人/踢人).
metadata:
  label: 群聊内容摘要
---

# 钉钉群聊摘要技能

从指定群聊中拉取消息，AI 分析提取议题、决策、行动项与风险，生成结构化钉钉云文档摘要。

## 禁止事项

- 禁止通过 curl、HTTP API 等非 `dws` 方式操作钉钉产品
- 禁止凭空构造 openconversation_id、userId、nodeId 等标识符，所有 ID 必须从实际命令返回值中提取
- 禁止 `dws` 命令不加 `--format json` 参数
- 禁止 markdown 内容以 `#` 一级标题开头——`dws doc create --name` 已设置文档标题
- 禁止使用字面量 `\n` 作为换行——必须使用真实换行符
- 禁止在写入文档的 markdown 中使用 ASCII Art 架构图——钉钉文档等宽字体不保证对齐，改用表格或列表
- 禁止单次 `dws doc update` 的 `--markdown` 超过 1500 字符——必须分块追加
- 禁止 `dws chat search` / `dws doc search` 传入整句——关键词须短小精准（2-4 字）
- 禁止跳过翻页——`dws chat message list` 返回 hasMore=true 时必须用边界 createTime 继续拉取

## 强制要求

- 每条 `dws` 命令均须携带 `--format json` 参数
- 拉取消息前必须与用户确认：目标群聊 + 时间范围（默认过去 24 小时，UTC+8）
- 群消息拉取必须完整翻页，不可只拉第一页就开始分析
- 文档必须包含：TL;DR、核心议题、关键决策、行动项、风险与问题
- 行动项必须标注负责人（未明确标"待分配"）和截止时间（未明确标"待确认"）
- `dws doc create` 返回的 `docUrl` 必须以可点击链接形式输出给用户
- 遇到 403 权限错误时，告知用户无权限并建议联系群主或管理员

## 能力清单

| 动作 | 安全等级 | 说明 |
|------|---------|------|
| 搜索群聊 | 只读 | `dws chat search` 按群名搜索 |
| 拉取群消息 | 只读 | `dws chat message list` 按时间范围拉取，需完整翻页 |
| 查看群成员 | 只读 | `dws chat group members` 获取参与人列表 |
| 查询用户信息 | 只读 | `dws contact user get` / `get-self` 补全发言人姓名 |
| 创建摘要文档 | 写入 | `dws doc create` 创建钉钉云文档 |
| 写入摘要内容 | 写入 | `dws doc update --mode append` 分块追加内容 |

## 涉及工具

| 工具 | 用途 | 关键参数 | 参考文件 |
|------|------|---------|---------|
| `dws chat search` | 按群名搜索群聊，提取 openconversation_id | `--query` [必填] | [chat.md](../../skills/dingtalk-workspace/references/products/chat.md) |
| `dws chat message list` | 拉取群聊消息 | `--group` [必填], `--time` [必填], `--limit`, `--forward` | ↑ |
| `dws chat group members` | 查看群成员列表 | `--id` [必填] | ↑ |
| `dws contact user get-self` | 获取当前用户信息 | 无必填参数 | [contact.md](../../skills/dingtalk-workspace/references/products/contact.md) |
| `dws contact user get` | 批量获取用户详情，补全发言人姓名 | `--ids` [必填] | ↑ |
| `dws doc create` | 创建摘要文档 | `--name` [必填], `--folder` | [doc.md](../../skills/dingtalk-workspace/references/products/doc.md) |
| `dws doc update` | 分块追加摘要内容 | `--node` [必填], `--markdown` [必填], `--mode append` | ↑ |

## 总体工作流

用户请求 → A 确认范围+拉取消息 → B 结构化分析 → C 生成文档 → 返回链接

### Module A — 消息获取

**目标**: 定位目标群聊，拉取指定时间范围内的完整消息

1. **A1 确认范围**: 与用户确认群名、时间范围（默认过去 24 小时 UTC+8）、关注主题（可选）
2. **A2 搜索群聊**: `dws chat search --query "{群名关键词}" --format json` → 提取 `openConversationId`；多条结果列出让用户选择
3. **A3 拉取消息**: `dws chat message list --group <oid> --time "{起始时间}" --format json`，hasMore=true 时用边界 createTime 作为下次 `--time` 翻页，直到拉完所有消息
4. **A4 补全人员**（可选）: 收集消息中 userId 集合，`dws contact user get --ids <ids> --format json` 批量补全姓名

**关键陷阱**: `--time` 格式必须是 `yyyy-MM-dd HH:mm:ss`；`--forward` 默认 true 拉之后的消息，设为 false 拉之前的

### Module B — 结构化分析

**目标**: 从原始消息中提取议题、决策、行动项、风险

1. **B1 去噪分段**: 过滤系统消息/纯表情/闲聊，按时间间隔（>30min）和话题切换分段
2. **B2 议题识别**: 从讨论段中提取 3-7 个核心议题，按消息数+参与人数排序
3. **B3 决策提取**: 识别信号词（决定/确认/同意/拍板），提取决策人、时间、原文引用
4. **B4 行动项提取**: 识别分配信号（@XX 负责/我来做/周五前），标注负责人+截止时间
5. **B5 风险提取**: 识别阻塞信号（卡住了/风险在于/谁能帮忙），标注严重程度
6. **B6 重要链接**: 提取钉钉文档/GitHub/外部链接，可选用 `dws doc info` 补全文档标题

📖 去噪规则、信号词、分段策略详见 [references/workflow-detail.md](./references/workflow-detail.md)

### Module C — 文档生成

**目标**: 创建钉钉云文档，分块写入结构化摘要

1. **C1 创建文档**: `dws doc create --name "群聊摘要：{群名}（{时间范围}）" --format json` → 提取 `nodeId` 和 `docUrl`
2. **C2 分块写入**: 按 TL;DR → 核心议题 → 关键决策 → 行动项 → 风险与问题 → 待跟进 的顺序，每块 ≤1500 字符，`dws doc update --node <nodeId> --markdown "<内容>" --mode append --format json`
3. **C3 返回链接**: 将 `docUrl` 以可点击链接输出给用户

📖 文档结构模板见 [references/doc-template.md](./references/doc-template.md)

**关键陷阱**: markdown 禁止以 `#` 开头；换行必须用真实换行符；每次 update 都用 `--mode append`，禁止意外 overwrite

## 上下文传递表

| 阶段 | 从返回中提取 | 用于 |
|------|-------------|------|
| A2: `dws chat search` | `openConversationId` | A3 的 `--group`、群成员查询的 `--id` |
| A3: `dws chat message list` | 消息列表 + 边界 `createTime` | B 模块分析输入；hasMore 时作为下次 `--time` |
| A3: `dws chat message list` | 消息中 `userId` 集合 | A4 `dws contact user get --ids` |
| A4: `dws contact user get` | userId → 姓名映射 | B 模块中标注发言人真实姓名 |
| C1: `dws doc create` | `nodeId` / `docUrl` | C2 `dws doc update --node`；C3 输出给用户 |

## 意图映射

| 用户说 | 线索 | 映射功能 |
|--------|------|---------|
| "帮我总结一下XX群的聊天记录" | 群名 + 总结 | A→B→C 完整流程 |
| "把项目群最近一周的讨论整理成文档" | 群名 + 时间范围 + 文档 | A→B→C 完整流程 |
| "总结今天群里的重要决策和待办" | 今天 + 决策/待办 | A→B→C，B 聚焦决策+行动项 |
| "帮我追踪XX群里关于YY的讨论" | 群名 + 关键词 | A→B→C，B 按关键词过滤 |
| "查一下群里昨天发了什么" | 群消息 + 简单查看 | A→B（仅消息分段摘要） |
| "帮我看一下群里有什么重要消息" | 群消息 + 重要 | A→B→C 完整流程 |

## 易混淆场景

| 用户说 | 线索 | 应路由到 |
|--------|------|---------|
| "帮我总结一下今天的会议" | 会议录音/纪要，非群聊消息 | wukong-doc-meeting-minutes |
| "帮我发个群消息" / "通知一下群里" | 发送消息，非总结消息 | 通用 chat 技能 |
| "帮我建个群" / "把XX拉进群" | 群管理操作（建群/加人） | 通用 chat 技能 |
| "帮我看看审批进度" | 审批场景，非消息总结 | wukong-approval-progress |
| "把私聊记录整理一下" | 单聊消息，非群聊 | 不适用本技能 |

## 使用示例

### 示例 1: 标准群聊总结
**用户说**: "帮我总结一下'Q1项目冲刺'群最近3天的讨论"
**执行步骤**:
1. A2: `dws chat search --query "Q1项目" --format json` → 提取 oid
2. A3: `dws chat message list --group <oid> --time "2026-03-23 00:00:00" --format json`，翻页至完整
3. A4: `dws contact user get --ids <userId1,userId2,...> --format json` 补全姓名
4. B1-B6: 去噪分段、提取议题/决策/行动项/风险/链接
5. C1: `dws doc create --name "群聊摘要：Q1项目冲刺（3月23-26日）" --format json`
6. C2: 分块 `dws doc update --node <nodeId> --mode append --format json`
**期望输出**: "已生成群聊摘要：[群聊摘要：Q1项目冲刺（3月23-26日）](docUrl)，共识别决策3项、行动项7项、高风险2项。"

### 示例 2: 最简触发
**用户说**: "总结下群聊"
**执行步骤**:
1. 追问：哪个群？时间范围？（默认过去 24 小时）
2. 确认后执行 A→B→C 完整流程
**期望输出**: 确认信息后执行

## 错误处理

| 错误 | 原因 | AI 应该怎么做 |
|------|------|--------------|
| `chat search` 无结果 | 群名关键词不匹配 | 缩短关键词至 2-4 字重试；仍无结果请用户提供精确群名 |
| `chat message list` 返回 403 | 无权限访问该群消息 | 告知用户无权限，建议确认是否为群成员或联系群主授权 |
| 消息量过大（>1000 条） | 时间范围过长或群活跃 | 建议用户缩小时间范围，或指定关注主题聚焦分析 |
| `doc create` 失败 | 权限不足或配额限制 | 检查错误信息，建议用户确认文档空间权限 |
| 摘要内容单块超限 | 议题多、消息复杂 | 增加分块次数，确保每块 ≤1500 字符 |
| 无关键决策/行动项 | 群聊内容为闲聊 | 告知用户该时段无实质讨论，建议调整时间范围 |

## 详细参考（按需读取）

- [references/doc-template.md](./references/doc-template.md) — 摘要文档结构模板（Module C 写入前必须读取）
- [references/workflow-detail.md](./references/workflow-detail.md) — 详细工作流步骤、去噪规则、识别信号词（Module A/B 执行前必须读取）
