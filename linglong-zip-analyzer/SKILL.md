# Linglong Application ZIP Analyzer

## Overview
分析灵珑低代码平台导出的应用 ZIP 备份文件，提取并对比应用结构信息，帮助理解应用配置、页面组成、组件关系和数据源映射。

## Trigger Conditions
当用户提供灵珑应用 ZIP 导出文件路径，或提到"灵珑应用备份分析"、"灵珑ZIP解析"、"应用导出文件"、"灵珑备份对比"时使用此技能。

## ZIP Structure
灵珑应用 ZIP 包含以下核心 JSON 文件：

| 文件名 | 用途 | 关键字段 |
|---|---|---|
| `application.json` | 应用基本信息 | name, id, code, type, theme, dataSourceId |
| `pageInfos.json` | 页面元数据 | name, id, type, terminalType, enabled, sort |
| `pageAssets.json` | 页面组件树 | pageId, version, content(含完整组件树) |
| `widgetAssets.json` | Widget 组件树 | pageId, version, content(含组件树) |
| `widgetPages.json` | Widget 页面类型 | name, type(LIST/NORMAL_FORM) |
| `tables.json` | 数据表定义 | name, id, fields/tables |
| `columns.json` | 列定义 | 表字段详细信息 |
| `references.json` | 跨页面/Widget 引用关系 | type, fromId, fromName, toId, toName |
| `processDefinitions.json` | 流程定义 | id, version |
| `processAssets.json` | 流程资产 | 流程配置详情 |
| `layouts.json` | 布局配置 | 页面布局定义 |
| `ddcatDataModel.json` | DDCAT 数据模型 | 数据模型配置 |
| `apiRequestParam.json` | API 请求参数 | 接口参数配置 |
| `ddcatRequestParam.json` | DDCAT 请求参数 | DDCAT 接口参数 |

## Page Types
- `LOGIN`: 登录页面（PC 或 MOBILE）
- `NORMAL`: 普通页面（PC 或 MOBILE）
- `MOBILE_APPLICATION_DESIGN`: 移动端应用设计页面

## Widget Types
- `LIST`: 列表型 Widget
- `NORMAL_FORM`: 表单型 Widget

## Reference Types
- `PAGE_ENTITY`: 页面关联数据实体
- `PAGE_WIDGET`: 页面使用 Widget
- `WIDGET_DATASET`: Widget 关联数据集
- `WIDGET_DATA_MODEL`: Widget 关联数据模型
- `WIDGET_PAGE`: Widget 关联页面

## Analysis Workflow
1. 解压 ZIP 到临时目录
2. 解析 `application.json` 获取应用基本信息
3. 解析 `pageInfos.json` 获取页面列表和类型
4. 解析 `pageAssets.json` 提取每个页面的组件树
5. 解析 `widgetAssets.json` 提取 Widget 组件结构
6. 解析 `references.json` 建立跨页面/Widget 关系图
7. 解析 `tables.json` 和 `columns.json` 获取数据源信息
8. 对比浏览器探索结果与 ZIP 备份的差异

## Example Analysis
```
应用: 实操练习应用-mjq-第一题
页面: 9个（登录页x2, 案件列表, 领导看板, 差错件页面, 移动端页面x4）
Widget: 2个（案件列表 widget, 领导看板 widget）
数据表: 20张（含 constr_waybill_record, mis_error_rec, 案件列表等）
流程: 14个版本（流程ID 25d0dc75f8）
引用关系: 10条（跨页面/Widget/数据源关联）
```

## Limitations
- 仅适用于灵珑低代码平台导出的应用 ZIP
- 需要解压后读取 JSON 文件，大文件解析可能耗时
- 组件树结构可能因灵珑版本不同而变化
