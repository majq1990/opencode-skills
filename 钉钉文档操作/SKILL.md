---
name: dingtalk-docs
description: Deprecated DingTalk document sync skill kept only for legacy REST API reference. Use only when reviewing old dingtalk-docs implementations or migrating them to dws CLI and DingTalk MCP tools.
---

# 钉钉文档同步 Skill — ⚠️ 已废弃

> **状态**：废弃（deprecated）
> **替代方案**：`dws` CLI + `dingtalk` MCP + `dingtalk-spreadsheet` MCP
> **废弃原因**：当前工作流已全面切换到 dws CLI 和 MCP 工具，不再使用 REST API 直调方式操作钉钉文档。

## 当前推荐方案

所有钉钉文档操作请使用以下工具：

| 操作 | 工具 |
|---|---|
| 读取文档内容 | `mcp__dingtalk__get_document_content` |
| 创建文档 | `mcp__dingtalk__create_document` |
| 更新文档 | `mcp__dingtalk__update_document`（append/overwrite 模式） |
| 复制文档（团队空间） | `mcp__dingtalk__copy_document` |
| 表格数据读写 | `mcp__dingtalk-spreadsheet__get_range` / `update_range` / `append_rows` |
| 表格结构操作 | `mcp__dingtalk-spreadsheet__add_dimension` / `create_sheet` 等 |
| 搜索文档 | `mcp__dingtalk__search_documents` |
| 列出节点 | `mcp__dingtalk__list_nodes` |

## 原方案参考（已废弃）

以下 REST API 方案仅供参考，不再维护：

- 原功能：获取知识库列表、节点遍历、增量同步、RAG 切分
- 原实现：JavaScript 调用 `api.dingtalk.com/v1.0/wiki/...` REST API
- 原认证：AppKey + AppSecret → access_token → API 调用

详见 git history 或备份文件。
