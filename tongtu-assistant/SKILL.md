# 通途助手 (TongTu Assistant)

通途平台数据操作助手，提供数据查询、写入、更新、删除能力，并自动记录所有写操作日志。

## 概述

本 Skill 封装了通途平台的完整数据操作能力：
- **查询**: 工作表数据查询，遵循"表优先、链兜底"原则
- **写入**: 单条/批量数据添加
- **更新**: 数据修改
- **删除**: 数据删除
- **日志**: 所有写操作自动记录到日志文件

## 核心能力

### 1. 智能数据查询

```
数据查询决策流程：

┌─────────────────────────────────────────────────────────────────┐
│                        数据查询流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: 确定数据需求                                            │
│  ├── 用户需要什么数据？                                          │
│  └── 数据可能存在于哪个工作表或链接？                             │
│                                                                  │
│  Step 2: 优先尝试工作表查询                                      │
│  ├── 调用 tongtu-platform MCP 的 get_worksheet_rows             │
│  ├── 检查返回结果                                                │
│  │   ├── 有数据 → 返回结果                                      │
│  │   └── 无数据/表不存在 → 进入 Step 3                          │
│                                                                  │
│  Step 3: 查找免密链接                                            │
│  ├── 查询分组信息，找到 type=2 的链接项                          │
│  ├── 使用 playwright 访问链接                                    │
│  └── 提取页面数据                                                │
│                                                                  │
│  Step 4: 数据整合与返回                                          │
│  └── 格式化输出结果                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 常用数据源映射

| 数据类型 | 优先来源 | 备用来源 |
|----------|----------|----------|
| 人员职级 | 工作表 `ryzjb` | - |
| 人员认证 | 工作表 `ryrzqkb_yc` | - |
| 工程能力认证 | 工作表 `6315b359a67a71d4d9b690d6` | - |
| 项目验收率 | - | "项目验收统计-明道" 分组链接 |
| 预算使用情况 | - | "预算统计" 分组链接 |
| 项目基本信息 | 工作表 `jfxx` (交付项目信息) | - |
| 故障统计 | 工作表 `gztj` | - |

### 3. 关键工作表参考

| 工作表名称 | ID | 别名 | 用途 |
|------------|----|----|------|
| 人员职级表 | `63eb293d6028cc4370630dcf` | `ryzjb` | 查询人员职级 |
| 人员认证总表 | `63e0b25fcc4ec422a4d43e6e` | `ryrzqkb_yc` | 查询认证情况 |
| 工程能力认证 | `6315b359a67a71d4d9b690d6` | - | 工程认证数据 |
| 交付项目信息 | - | `jfxx` | 项目基本信息 |
| 故障统计 | - | `gztj` | 故障处理情况 |

### 4. 数据写入操作

```
数据写入流程：

┌─────────────────────────────────────────────────────────────────┐
│                        数据写入流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: 获取工作表结构                                          │
│  └── 调用 getWorksheetInfo 获取字段ID和类型                      │
│                                                                  │
│  Step 2: 构建数据                                                │
│  └── controls 数组，包含 controlId 和 value                      │
│                                                                  │
│  Step 3: 执行写入                                                │
│  ├── addRow: 新增数据                                            │
│  ├── updateRow: 更新数据（需要rowId）                            │
│  └── deleteRow: 删除数据（需要rowId）                            │
│                                                                  │
│  Step 4: 记录日志                                                │
│  └── 自动记录到 D:\opencode\file\tongtu_operations.log          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5. 操作日志记录

所有写操作自动记录日志，格式：

```
[2026-03-24 10:30:00] [ADD] 工作表:gcpbcb 工号:283 年份:2025 职级:B 结果:成功
[2026-03-24 10:30:01] [UPDATE] 工作表:gcpbcb rowId:xxx 字段:职级 值:A 结果:成功
[2026-03-24 10:30:02] [DELETE] 工作表:gcpbcb rowId:xxx 结果:成功
```

日志文件位置: `D:\opencode\file\tongtu_operations.log`

### 6. 免密链接分组

| 分组名称 | 包含链接 | 用途 |
|----------|----------|------|
| 项目验收统计-明道 | 大区初验/终验看板 | 获取验收率数据 |
| 项目相关统计 | 项目综合统计看板 | 项目综合数据 |
| 预算统计 | 预算使用情况看板 | 预算分析 |

## 使用指南

### 场景 1: 查询人员职级

```typescript
// 直接查询工作表
skill_mcp({
  mcp_name: "ztoa",
  tool_name: "get_worksheet_rows",
  arguments: {
    worksheetId: "ryzjb",
    pageIndex: 1,
    pageSize: 100,
    filters: [{
      controlId: "63eb2ab31c09549442d52caf",
      dataType: 6,
      spliceType: 1,
      filterType: 3,
      value: "8"
    }]
  }
})
```

### 场景 2: 添加数据

```python
import requests
import json
from datetime import datetime

def add_row(worksheet_id, controls):
    """添加数据并记录日志"""
    response = requests.post(
        f"{base_url}/api/v2/open/worksheet/addRow",
        json={
            "appKey": app_key,
            "sign": sign,
            "worksheetId": worksheet_id,
            "controls": controls
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    result = response.json()
    
    # 记录日志
    log_operation("ADD", worksheet_id, controls, result.get("success"))
    
    return result

def log_operation(op_type, worksheet_id, data, success):
    """记录操作日志"""
    log_file = r"D:\opencode\file\tongtu_operations.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "成功" if success else "失败"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{op_type}] 工作表:{worksheet_id} 数据:{json.dumps(data, ensure_ascii=False)} 结果:{status}\n")
```

### 场景 3: 更新数据

```python
def update_row(worksheet_id, row_id, controls):
    """更新数据并记录日志"""
    response = requests.post(
        f"{base_url}/api/v2/open/worksheet/updateRow",
        json={
            "appKey": app_key,
            "sign": sign,
            "worksheetId": worksheet_id,
            "rowId": row_id,
            "controls": controls
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    result = response.json()
    log_operation("UPDATE", worksheet_id, {"rowId": row_id, "controls": controls}, result.get("success"))
    
    return result
```

### 场景 4: 删除数据

```python
def delete_row(worksheet_id, row_id):
    """删除数据并记录日志"""
    response = requests.post(
        f"{base_url}/api/v2/open/worksheet/deleteRow",
        json={
            "appKey": app_key,
            "sign": sign,
            "worksheetId": worksheet_id,
            "rowId": row_id
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    result = response.json()
    log_operation("DELETE", worksheet_id, {"rowId": row_id}, result.get("success"))
    
    return result
```

### 场景 5: 查询项目验收情况

```typescript
// Step 1: 尝试工作表查询
// 如果工作表不存在或无数据...

// Step 2: 查找免密链接
skill_mcp({
  mcp_name: "ztoa",
  tool_name: "get_worksheet_rows",
  arguments: {
    worksheetId: "分组工作表ID",
    pageIndex: 1,
    pageSize: 50
  }
})

// Step 3: 使用 playwright 访问链接
skill(name: "playwright")
// 然后导航到链接页面获取数据
```

### 场景 3: 分析预算使用情况

```typescript
// 预算数据通常通过免密链接获取
// 1. 找到"预算统计"分组中的链接
// 2. 使用 playwright 访问链接
// 3. 提取页面中的统计数据
```

## 筛选条件参数说明

### dataType 值

| 值 | 类型 | 示例字段 |
|----|------|----------|
| 2 | 文本 | 名称、描述 |
| 6 | 数值 | 职级、金额 |
| 11 | 单选 | 状态、类型 |
| 10 | 多选 | 认证等级 |

### filterType 值

| 值 | 操作 | 示例 |
|----|------|------|
| 1 | 包含 | 名称包含"项目" |
| 2 | 不包含 | - |
| 3 | 等于 | 职级等于8 |
| 7 | 大于 | 金额大于1000 |
| 8 | 小于 | - |
| 9 | 大于等于 | - |
| 10 | 小于等于 | - |
| 13 | 区间 | 时间区间 |

### spliceType 值

| 值 | 逻辑 |
|----|------|
| 1 | AND (所有条件同时满足) |
| 2 | OR (任一条件满足) |

## 依赖

- **MCP**: `ztoa` 或 `tongtu-platform`
- **Skill**: `/playwright` (用于访问免密链接)
- **环境变量**:
  - `TONGTU_APP_KEY` 或 `ZTOA_APP_KEY`
  - `TONGTU_SIGN` 或 `ZTOA_SIGN`

## 注意事项

1. **API 端点**: 获取行数据必须使用 `/api/v2/open/worksheet/getFilterRows`，不是 `getRows`
2. **必填参数**: `pageIndex` 和 `pageSize` 是必填参数
3. **分页**: 单次最多返回 1000 条，大数据量需要分页查询
4. **认证**: sign 参数直接使用提供的值，无需加密处理
5. **链接类型**: 分组中 `type=2` 的项是免密链接，`type=1` 是工作表

## 示例任务

### 任务：查询职级8人员的认证情况

```
1. 查询人员职级表，筛选职级=8且是当前最新职级
2. 获取人员ID列表
3. 查询人员认证总表，匹配人员ID
4. 整合输出认证情况报告
```

### 任务：分析项目验收率

```
1. 尝试查询"项目验收统计"工作表
2. 如果不存在，查找"项目验收统计-明道"分组
3. 获取分组中的免密链接
4. 使用 playwright 访问链接页面
5. 提取初验率、终验率数据
6. 生成验收情况报告
```

## 更新历史

- 2026-03-24: 新增数据写入能力（addRow/updateRow/deleteRow），添加操作日志记录
- 2026-03-20: 初始版本，定义数据查询规则和流程