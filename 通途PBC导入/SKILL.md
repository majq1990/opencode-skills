---
name: tongtu-pbc
description: 通途平台工程PBC表数据导入工具。⚠️ REST API 直调方案已废弃，当前统一走 ztoa MCP 调用。支持从Excel批量导入PBC职级数据。触发词：PBC导入 / 工程PBC / 批量导入PBC / 更新PBC职级。
status: updated
---

# 通途PBC导入助手 (TongTu PBC Importer)

> **当前方案**：统一使用 `ztoa` MCP（`mcp__ztoa__*` 工具）操作通途数据。
> **废弃方案**：REST API 直调（`ztoa.egova.com.cn/api/v2/open/worksheet/...`）已废弃，不再维护。

## 工作表信息

| 项目 | 值 |
|---|---|
| 工作表名称 | 工程PBC表 |
| 工作表ID | `gcpbcb`（别名）/ 完整 ID `64194b73a35db665c3115933` |

## 字段映射

| 字段名称 | 字段ID | 类型 | 说明 |
|---|---|---|---|
| 工号 | `64194b73a35db665c3115934` | 文本(type 2) | 必填，员工工号 |
| 更新日期 | `64194bcd210ef681d9895b28` | 日期(type 15) | 格式: YYYY-MM-DD |
| PBC归属年份 | `64194ce0210ef681d9895b95` | 数值(type 6) | 必填，年份如2025 |
| 人员 | `64194bcd210ef681d9895b29` | 成员(type 26) | 使用工号关联 |
| PBC职级 | `64194bcd210ef681d9895b2a` | 单选(type 11) | 必填，A/B+/B/C/D |

## PBC职级选项

| 职级 | Key |
|---|---|
| A | `b3557f4b-7e65-41f8-9f35-bbaee288bfa1` |
| B+ | `b07e676e-055f-4351-9378-2011dbae109d` |
| B | `46a5faae-f519-4f6b-8ea0-c798a133e370` |
| C | `26a2a9da-eb64-4912-be65-d561ff0385b6` |
| D | `3e3047e7-1a07-44dd-90ea-b4ba7e75203f` |

## MCP 调用方式

### 查询现有数据

```
mcp__ztoa__query_records(
  worksheet_id="gcpbcb",
  filters=[{
    controlId: "64194ce0210ef681d9895b95",
    dataType: 6,
    spliceType: 1,
    filterType: 2,
    value: "2025"
  }]
)
```

### 批量新建

```
mcp__ztoa__admin_create_records_batch(
  worksheet_id="gcpbcb",
  rows=[[
    {"controlId": "64194b73a35db665c3115934", "value": "283"},
    {"controlId": "64194bcd210ef681d9895b28", "value": "2026-03-24"},
    {"controlId": "64194ce0210ef681d9895b95", "value": 2025},
    {"controlId": "64194bcd210ef681d9895b29", "value": "283"},
    {"controlId": "64194bcd210ef681d9895b2a", "value": "B"}
  ], ...]
)
```

### 编辑单条

> ⚠️ 必须先 query 拿现有字段值，把所有字段一起传。单字段更新会报「数据不能为空 10001」。

```
mcp__ztoa__edit_record(
  worksheet_id="gcpbcb",
  row_id="<rowId>",
  controls=[...完整字段列表...]
)
```

## 导入流程

1. 读取 Excel（列名：工号、更新日期、PBC归属年份(年)、人员、PBC职级）
2. 数据清洗（空值处理、日期格式化）
3. 查询现有数据（按年份去重）
4. 批量删除旧数据（可选）
5. 批量导入新数据（`admin_create_records_batch`，≤50条/批）
6. 验证结果（`get_records_total` 确认数量）

## 注意事项

1. **工号必填**：Excel中工号字段不能为空，空工号的记录跳过
2. **人员关联**：人员字段使用工号关联，系统自动匹配
3. **年份去重**：导入前建议先清理同年度现有数据
4. **API限流**：批量导入时段间隔 ≥50ms
5. **单选字段**：PBC职级是 type=11 单选，传字符串值（不是 list）
