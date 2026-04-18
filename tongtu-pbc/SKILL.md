---
name: tongtu-pbc
description: 通途平台工程PBC表数据导入工具，支持从Excel批量导入PBC职级数据，自动记录所有操作日志
license: MIT
compatibility: opencode
metadata:
  category: support-dept
  platform: tongtu
  features: excel-import, pbc-data, batch-import, operation-logging
---
# 通途PBC导入助手 (TongTu PBC Importer)

通途平台工程PBC表数据导入工具，支持从Excel批量导入PBC职级数据，自动记录所有操作日志。

## 概述

本Skill封装了工程PBC表数据导入的完整流程，包括：
- Excel数据读取与验证
- 现有数据清理（按年份删除）
- 批量数据导入
- 导入结果验证
- **操作日志自动记录**

## 操作日志

所有写操作自动记录到日志文件：

**日志位置**: `D:\opencode\file\tongtu_pbc_operations.log`

**日志格式**:
```
[2026-03-24 10:30:00] [IMPORT] 文件:2025年PBC.xlsx 年份:2025 成功:315 失败:0
[2026-03-24 10:35:00] [ADD] 工号:283 年份:2025 职级:B 结果:成功
[2026-03-24 10:35:01] [DELETE] 年份:2025 删除数量:300 结果:成功
[2026-03-24 10:40:00] [UPDATE] 工号:283 rowId:xxx 字段:PBC职级 值:A 结果:成功
```

## 工作表信息

| 项目 | 值 |
|------|-----|
| 工作表名称 | 工程PBC表 |
| 工作表ID | `gcpbcb` |
| 完整ID | `64194b73a35db665c3115933` |

## 字段映射

| 字段名称 | 字段ID | 类型 | 说明 |
|----------|--------|------|------|
| 工号 | `64194b73a35db665c3115934` | 文本(type 2) | 必填，员工工号 |
| 更新日期 | `64194bcd210ef681d9895b28` | 日期(type 15) | 格式: YYYY-MM-DD |
| PBC归属年份 | `64194ce0210ef681d9895b95` | 数值(type 6) | 必填，年份如2025 |
| 人员 | `64194bcd210ef681d9895b29` | 成员(type 26) | 使用工号关联 |
| PBC职级 | `64194bcd210ef681d9895b2a` | 单选(type 11) | 必填，A/B+/B/C/D |

## PBC职级选项

| 职级 | Key |
|------|-----|
| A | `b3557f4b-7e65-41f8-9f35-bbaee288bfa1` |
| B+ | `b07e676e-055f-4351-9378-2011dbae109d` |
| B | `46a5faae-f519-4f6b-8ea0-c798a133e370` |
| C | `26a2a9da-eb64-4912-be65-d561ff0385b6` |
| D | `3e3047e7-1a07-44dd-90ea-b4ba7e75203f` |

## 导入流程

```
1. 读取Excel文件
   ├── 验证列名：工号、更新日期、PBC归属年份(年)、人员、PBC职级
   └── 数据清洗：处理空值、日期格式化

2. 清理现有数据（可选）
   ├── 查询指定年份的现有数据
   └── 批量删除

3. 批量导入
   ├── 构建controls数组
   ├── 人员字段使用工号关联
   └── 调用addRow API

4. 验证结果
   └── 查询确认导入数量
```

## API调用示例

### 查询工作表数据

```python
import requests
import json

base_url = "https://ztoa.egova.com.cn"
app_key = "YOUR_APP_KEY"
sign = "YOUR_SIGN"

response = requests.post(
    f"{base_url}/api/v2/open/worksheet/getFilterRows",
    json={
        "appKey": app_key,
        "sign": sign,
        "worksheetId": "gcpbcb",
        "pageSize": 1000,
        "pageIndex": 1
    },
    headers={"Content-Type": "application/json"},
    timeout=60
)
```

### 添加单条数据

```python
controls = [
    {"controlId": "64194b73a35db665c3115934", "value": "283"},        # 工号
    {"controlId": "64194bcd210ef681d9895b28", "value": "2026-03-24"}, # 更新日期
    {"controlId": "64194ce0210ef681d9895b95", "value": 2025},         # PBC归属年份
    {"controlId": "64194bcd210ef681d9895b29", "value": "283"},        # 人员(工号)
    {"controlId": "64194bcd210ef681d9895b2a", "value": "B"}           # PBC职级
]

response = requests.post(
    f"{base_url}/api/v2/open/worksheet/addRow",
    json={
        "appKey": app_key,
        "sign": sign,
        "worksheetId": "gcpbcb",
        "controls": controls
    },
    headers={"Content-Type": "application/json"},
    timeout=30
)
```

### 删除单条数据

```python
response = requests.post(
    f"{base_url}/api/v2/open/worksheet/deleteRow",
    json={
        "appKey": app_key,
        "sign": sign,
        "worksheetId": "gcpbcb",
        "rowId": "row-id-here"
    },
    headers={"Content-Type": "application/json"},
    timeout=30
)
```

## 使用场景

### 场景1: 导入年度PBC数据

```
用户: 将Excel文件 D:\pbc\2025年PBC.xlsx 导入工程PBC表
助手: 
1. 读取Excel数据
2. 删除2025年现有数据
3. 导入新数据
4. 返回导入结果
```

### 场景2: 更新特定人员PBC

```
用户: 更新工号283的2025年PBC职级为A
助手:
1. 查询工号283的2025年记录
2. 获取rowId
3. 调用updateRow更新职级字段
```

### 场景3: 查询PBC数据

```
用户: 查询2025年PBC职级为A的人员
助手:
1. 构建筛选条件
2. 调用getFilterRows
3. 返回结果列表
```

## 注意事项

1. **工号必填**: Excel中工号字段不能为空，空工号的记录会被跳过
2. **人员关联**: 人员字段使用工号关联，系统会自动匹配通途系统中该工号对应的人员
3. **年份去重**: 导入前建议先清理同年度的现有数据，避免重复
4. **API限流**: 批量导入时建议间隔50ms，避免请求过快
5. **数据验证**: 导入后务必验证数据数量和内容

## 依赖

- **MCP**: `ztoa` 或 `tongtu-platform`
- **环境变量**:
  - `ZTOA_APP_KEY` 或 `TONGTU_APP_KEY`
  - `ZTOA_SIGN` 或 `TONGTU_SIGN`
- **Python库**: pandas, requests, openpyxl

## 错误处理

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| 签名不合法 | appKey或sign错误 | 检查环境变量配置 |
| 数据操作异常 | 字段格式错误 | 检查controls格式 |
| 工号为空 | Excel中工号列为空 | 补充工号数据 |

## 更新历史

- 2026-03-24: 新增操作日志记录功能，所有写操作自动记录到日志文件
- 2026-03-24: 初始版本，支持Excel导入、数据查询、更新、删除