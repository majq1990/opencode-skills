---
name: unread-message-summary
description: >
  钉钉未读消息总结。自动获取当前用户所有有未读消息的会话，逐一读取未读内容，
  并用 AI 汇总每个会话的核心信息，让你快速掌握重要动态。
  每当用户说"帮我看看未读消息"、"总结一下未读的消息"、"我有哪些未读消息"、
  "帮我整理未读消息"、"未读消息摘要"、"消息总结"时都应触发本技能。
  支持按会话维度逐条汇总，输出结构化的未读消息摘要报告。
metadata:
  label: 未读消息总结
---

# 未读消息总结

自动拉取所有有未读消息的会话，读取每个会话的未读内容，用 AI 汇总关键信息，
帮你快速了解错过了什么。

## MCP 服务配置

本技能依赖以下 MCP 服务，运行时**必须**先读取 `mcp-config.json` 获取服务 URL：

| 环境变量名 | MCP 服务 | mcpId |
|------------|----------|-------|
| `$UNREAD_MSG_URL` | 未读消息总结（获取未读会话列表） | 9932 |

**约束：调用方 agent 必须在执行任何 MCP 调用前，先读取 mcp-config.json 文件**

```python
import json
with open("mcp-config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
UNREAD_MSG_URL = config["UNREAD_MSG_URL"]["url"]
```

---

## 工作流程

### 整体流程

```
① 读取 mcp-config.json 获取 MCP URL
② 调用 MCP 获取有未读消息的会话列表（含 conversationId、未读条数、最后消息时间）
③ 遍历每个会话，调用 dws 命令读取该会话的未读消息内容
④ AI 汇总每个会话的核心信息
⑤ 输出结构化未读消息摘要报告
```

---

### 步骤一：读取配置

```python
import json
with open("mcp-config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
UNREAD_MSG_URL = config["UNREAD_MSG_URL"]["url"]
```

---

### 步骤二：获取未读会话列表

调用 MCP 工具 `get_unread_conversation_list`，获取所有有未读消息的会话信息：

```bash
python3 scripts/call_mcp.py call "$UNREAD_MSG_URL" get_unread_conversation_list \
  --params '{}'
```

**返回数据结构**（`result.conversations.items` 数组，每条会话包含）：
- `openConversationId`：会话唯一 ID（用于后续 dws 查询）
- `title`：会话标题（群名）；**单聊时不返回此字段**
- `singleChat`：是否为单聊（`true` = 单聊，`false` = 群聊）
- `unreadPoint`：未读消息条数
- `lastMsgCreateAt`：最后一条未读消息的创建时间戳（毫秒）
- `notificationOff`：免打扰标识（`1` = 已开启免打扰）

> 若返回列表为空，直接告知用户"当前没有未读消息 🎉"，流程结束。

---

### 步骤三：逐会话读取未读消息内容

对每个会话，将 `lastMsgCreateAt`（毫秒时间戳）转换为 `YYYY-MM-DD HH:MM:SS` 格式，
调用 dws 命令拉取该时间点**之前**的消息，条数限制为该会话的 `unreadPoint` 值：

```bash
dws chat message list \
  --group <openConversationId> \
  --time "<lastMsgCreateAt 转换后的时间，格式 YYYY-MM-DD HH:MM:SS>" \
  --forward false \
  --limit <unreadPoint> \
  --format json
```

**参数说明**：
- `--time`：取 `lastMsgCreateAt` 转换后的时间字符串
- `--forward false`：拉取指定时间**之前**的消息（未读消息在这条时间之前）
- `--limit`：直接使用 MCP 返回的 `unreadPoint` 值，精确控制拉取条数，避免拉取多余历史

**时间转换示例（Python）**：
```python
import datetime

def ms_to_timestr(ms_timestamp):
    """毫秒时间戳转 YYYY-MM-DD HH:MM:SS"""
    dt = datetime.datetime.fromtimestamp(ms_timestamp / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")
```

---

### 步骤四：AI 汇总每个会话

对每个会话的消息内容，提取并总结：
1. **核心议题**：主要在讨论什么
2. **重要信息**：需要关注的决策、通知、任务
3. **@我的内容**：是否有人 @ 了当前用户，具体说了什么
4. **待办事项**：是否有需要我回复或处理的事项

---

### 步骤五：输出摘要报告

**输出格式示例**：

```
📬 未读消息摘要（共 N 个会话，M 条未读）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 【项目Alpha群】  未读 12 条
核心议题：讨论本周上线计划，确认发布时间为周五 18:00
重要信息：技术负责人要求所有人在今晚 22:00 前完成代码提交
@我：张三 @ 你，询问接口文档是否已更新
待办：回复接口文档更新进度 ⚠️

📌 【李四（同事）】  未读 3 条
核心议题：询问明天会议室预订情况
待办：确认是否需要帮忙预订 ⚠️

📌 【运营通知群】  未读 5 条
核心议题：系统维护通知，今晚 23:00-次日 1:00 暂停服务
重要信息：维护期间请勿提交工单

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 有 2 个会话需要你回复，请及时处理。
```

---

**处理建议（优先级判断）**：

在输出格式示例之后，紧接着输出一段 AI 自动判断的处理建议，规则如下：

**优先级判断规则**（基于 MCP 返回字段，按会话逐条评估）：

| 优先级 | 触发条件 | 标记 |
|--------|----------|------|
| 🔴 高优先 | `singleChat=true`（单聊），说明是点对点沟通，通常需要回复 | `[高优先]` |
| 🔴 高优先 | 消息内容中有 @ 当前用户 | `[高优先]` |
| 🟡 中优先 | `singleChat=false`（群聊）且 `notificationOff≠1` 且 `unreadPoint≥10` | `[中优先]` |
| 🟢 低优先 | `notificationOff=1`（已开启免打扰）的群聊 | `[低优先]` |
| 🟢 低优先 | 群聊且 `unreadPoint<10` 且无 @ 当前用户 | `[低优先]` |

**处理建议输出示例**：

```
📋 处理建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 高优先（建议立即处理）
  · 【李四（同事）】— 单聊，对方在等你回复
  · 【项目Alpha群】— 有人 @ 了你，需要响应

🟡 中优先（建议今日内处理）
  · 【前端技术群】— 群聊，未读 15 条，有重要讨论

🟢 低优先（可择机查看）
  · 【运营通知群】— 免打扰群，通知类消息为主
  · 【全员公告群】— 未读 3 条，无需回复

💡 建议优先处理高优先会话，低优先会话可在空闲时批量查阅。
```

---

## 异常处理

| 情况 | 处理方式 |
|------|----------|
| MCP 返回空列表 | 告知"当前没有未读消息 🎉" |
| 某会话 dws 命令失败 | 跳过该会话，标注"消息读取失败，请手动查看"，继续处理其他会话 |
| 时间戳转换异常 | 使用当前时间往前推 24 小时作为兜底时间参数 |
| URL 未配置 | 提示"mcp-config.json 中 UNREAD_MSG_URL 未注入，请联系管理员配置" |
| dws 命令不存在 | 提示"dws 命令未安装，请先安装钉钉工作台命令行工具" |
| 会话消息为空 | 标注"该会话无可读消息内容"，跳过汇总 |

---

## 注意事项

1. **隐私保护**：消息内容仅用于本次摘要生成，不做任何持久化存储
2. **会话数量限制**：若未读会话超过 20 个，优先处理 `unreadPoint` 最多的前 20 个，并告知用户
3. **dws 命令依赖**：需确保本地已安装并登录 dws（钉钉工作台命令行工具）
