---
name: tongtu-assistant
description: 通途平台数据操作助手。⚠️ REST API 直调方案已废弃，当前统一走 ztoa MCP 调用。提供数据查询、写入、更新、能力。触发词：通途 / ztoa / 查工作表 / 写数据 / 人员职级 / 认证情况 / 故障统计。
status: updated
---

# 通途助手 (TongTu Assistant)

> **当前方案**：统一使用 `ztoa` MCP（`mcp__ztoa__*` 工具）操作通途数据。
> **废弃方案**：REST API 直调（`ztoa.egova.com.cn/api/v2/open/worksheet/...`）已废弃，不再维护。

## 核心能力

| 能力 | 工具 |
|---|---|
| 查询工作表数据 | `mcp__ztoa__query_records` |
| 读取工作表结构 | `mcp__ztoa__get_worksheet_schema` |
| 新建记录 | `mcp__ztoa__create_record` |
| 编辑记录 | `mcp__ztoa__edit_record` |
| 批量编辑（多行同字段同值） | `mcp__ztoa__admin_edit_records_batch` |
| 删除记录 | `mcp__ztoa__delete_record` |
| 获取单行详情 | `mcp__ztoa__get_record` |
| 统计行数 | `mcp__ztoa__get_records_total` |
| 查关联记录 | `mcp__ztoa__admin_get_record_relations` |
| 查当前用户身份 | `mcp__ztoa__whoami` |

> ⚠️ `edit_record` 必须传完整字段值（先 query 再 edit），单字段更新会报「数据不能为空 10001」。
> 详见 memory `feedback_ztoa_editrow_full_controls.md`。

## 常用数据源

| 数据类型 | 工作表 ID | 别名 | 用途 |
|---|---|---|---|
| 人员职级表 | `63eb293d6028cc4370630dcf` | `ryzjb` | 查询人员职级 |
| 人员认证总表 | `63e0b25fcc4ec422a4d43e6e` | `ryrzqkb_yc` | 查询认证情况 |
| 工程能力认证 | `6315b359a67a71d4d9b690d6` | - | 工程认证数据 |
| 交付项目信息 | `629da7f86f0dcb3b9b7cd603` | `jfxx` | 项目基本信息（项目状态=打开过滤） |
| 故障统计 | `gztj`（别名） | `gztj` | 故障处理情况 |
| 大区省份表-琅琊榜 | `63e59ab31c09549442d4717f` | - | 大区/省份工程总映射 |
| 软件漏洞表 | `oz3kcid3c79qy2lqspsn3` | - | vuln-response 写入 |
| 第三方依赖包漏洞 | `xi7jwt0lfqjgjoe1mffx4` | - | vuln-bridge 写入 |

> **注意**：以上 ID 为当前已知值，新增工作表时先用 `list_app` + `get_worksheet_schema` 获取。

## 筛选条件参数

### filterType 值

| 值 | 操作 | 说明 |
|---|---|---|
| 1 | Like（包含） | 文本模糊匹配，"标题包含 XX"时用 |
| 2 | Eq（精确等于） | 精确匹配 |
| 7 | IsNull（字段为空） | 不要传 value |
| 8 | HasValue（字段不为空） | 不要传 value |

> ⚠️ 不要把 filterType=7（IsNull）拿来搜索关键词——会变成"字段为空 AND value=关键词"导致 0 行。

### 常见 dataType

| 值 | 类型 |
|---|---|
| 2 | 文本 |
| 6 | 数值 |
| 10 | 多选（MCP 传 list，自动转 JSON 字符串） |
| 11 | 单选（传字符串，不是 list） |
| 26 | 成员（user） |
| 29 | 表关联 |
| 34 | 子表 |

> ⚠️ type=10 多选可直接传 list；type=11 单选传 list 会报错。

## view_mode 选择

调用 `query_records` 前先调 `whoami` 确认可用 view_mode：
- `mine`：只看当前用户相关的记录（成员字段含当前用户）
- `all`：全表（仅技术支持部 + 管理员可用）

## 操作日志

> **历史**（已停用）：旧方案曾记录到 `D:\opencode\file\tongtu_operations.log`
>
> **当前**：不单独记录文件日志。MCP 调用日志可通过会话历史追溯。

## 注意事项

1. **ztoa OpenAPI 已关闭 user/department 接口**（404/405），拿不到工号/手机号 → 必须走 `dws contact user search` + `dws contact user get`
2. **单选字段值用中文 value 比对**（如 `项目状态=='打开'`），不是 key
3. **批量写入上限**：`admin_create_records_batch` 单次建议 ≤50 条
