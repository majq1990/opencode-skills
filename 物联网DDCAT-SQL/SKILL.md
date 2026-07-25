---
name: ddcat-iot
description: 编写物联网1.0的DDCAT SQL脚本，当用户说"编写物联网1.0的DDCAT"或"编写物联网1.0的查询语句"或"物联网1.0"时触发
version: 1.0.0
compatibility: workbuddy
license: MIT
metadata:
  audience: developers
  workflow: ddcat-sql
  category: global
  tags: iot,ddcat,sql,物联网
---

## 概述

本技能指导 DDCAT SQL 脚本编写，适用于物联设备监控系统的数据查询开发。如果需求不清楚，例如过滤条件是什么、需要查询哪些字段，需要先和用户确认清楚。

**触发方式**：当用户说以下提示词时加载本技能：
- "编写物联网1.0的DDCAT"
- "编写物联网1.0的查询语句"
- "物联网1.0"
- "物联网1.0 ddcat"

---

## 核心业务表

### 设备基础信息表 (iot_equip_info)

存储设备的基本配置信息，是设备统计的核心表。

主键：`equip_id`

关键字段：
- `equip_id` - 设备ID
- `equip_name` - 设备名称
- `equip_type_id` - 设备类型ID
- `valid_flag` - 是否有效（1=有效）
- `manufacturer_id` - 厂家/企业ID
- `manufacturer_name` - 厂家/企业名称
- `city_id/city_name` - 城市
- `district_id/district_name` - 区县
- `street_id/street_name` - 街道
- `community_id/community_name` - 社区
- `response_unit_id/response_unit_name` - 责任单位
- `longitude/latitude` - 经纬度

### 设备状态表 (iot_equip_status)

存储设备的实时状态信息，与 iot_equip_info 为一对一关系。

主键：`equip_id`

关键字段：
- `equip_id` - 设备ID
- `online_state` - 在线状态
- `alarm_flag` - 报警状态，该设备当前是否正在报警；设备维度的“当前报警”统计优先使用该字段
- `time` - **设备最新一次通讯时间**
- `battery` - 电量
- `sign` - 信号

### 设备监测项表 (iot_equip_field)

存储设备的监测项配置，一个设备可有多个监测项（一对多）。

主键：`field_id`

关键字段：
- `field_id` - 监测项ID
- `equip_id` - 设备ID
- `field_name` - 监测项名称
- `gen_alarm` - 是否生成报警
- `max_value` - 最大值（阈值）
- `min_value` - 最小值（阈值）
- `value` - 当前值
- `value_type_id` - 报警类型ID
- `alarm_state` - 报警状态，该监测项当前是否正在报警；监测项维度的“当前报警”统计优先使用该字段
- `display_order` - 显示顺序，用于控制监测项在界面上的展示顺序

### 设备报警记录表 (iot_equip_alarm)

存储设备的报警记录，一个设备可能存在多个报警记录。

主键：`id`

关键字段：
- `id` - 记录ID
- `equip_id` - 设备ID
- `field_id` - 监测项ID
- `alarm_time` - **报警开始时间**
- `end_time` - **报警结束时间（null表示报警进行中）**
- `value_type_id` - 报警类型ID（-1表示离线）
- `value` - 报警值
- `detail` - 报警详情
- `deal_flag` - 处置状态

### 报警类型表 (iot_dic_equip_value)

存储报警类型定义，用于根据报警类型ID获取报警类型名称等信息。

主键：`value_type_id`

关键字段：
- `value_type_id` - 报警类型ID
- `value_type_name` - 报警类型名称
- `field_code` - 监测项编码
- `equip_id` - 设备ID
- `equip_type_id` - 设备类型ID
- `valid_flag` - 是否有效（1=有效）
- `alarm_level` - 报警等级
- `warn_type` - 规则类型（1固定值 2区间 3差值）

### 设备类型表 (iot_dic_equip)

存储设备类型定义，用于根据设备类型ID获取设备类型名称等信息。

主键：`equip_type_id`

关键字段：
- `equip_type_id` - 设备类型ID
- `equip_type_name` - 设备类型名称
- `display_order` - 显示顺序
- `display_flag` - 是否展示（1=展示，0=不展示）

### 表关联关系

- `iot_equip_alarm.equip_id` → `iot_equip_info.equip_id`
- `iot_equip_alarm.field_id` → `iot_equip_field.field_id`
- `iot_equip_alarm.value_type_id` → `iot_dic_equip_value.value_type_id`
- `iot_equip_field.equip_id` → `iot_equip_info.equip_id`
- `iot_equip_status.equip_id` → `iot_equip_info.equip_id`
- `iot_equip_info.equip_type_id` → `iot_dic_equip.equip_type_id`

---

## 业务约定（必须遵守）

### 设备总数

所有查询中"设备总数"统一指 `iot_equip_info` 表中 `valid_flag = 1` 的记录。

### 设备基础信息表相关统计默认设备类型筛选

凡是与 `iot_equip_info` 直接相关的统计查询，或最终统计口径的设备总数来自 `iot_equip_info`，如果需求中**没有明确说明“不按设备类型筛选”**，则必须默认加入设备类型筛选参数，不能省略。

执行要求：

- 单设备类型筛选时，加入 `equipTypeId` 参数，并在 SQL 中使用 `equip_type_id = '${equipTypeId}'`
- 多设备类型筛选时，加入 `equipTypeIds` 参数，并在 SQL 中使用 `equip_type_id IN (...)`
- 如果用户明确说明“不按设备类型筛选”或“统计全部设备类型”，才可以不加该参数
- 如果需求未说明是单选还是多选，优先加入单值参数 `equipTypeId`；只有明确需要多选时才使用 `equipTypeIds`
- 只要统计结果依赖设备基础信息表口径，就要主动检查并补上设备类型参数，不要等用户提醒

### 报警记录数

所有查询中"报警记录数"统一指 `iot_equip_alarm` 表的记录。

```sql
SELECT COUNT(*) FROM iot_equip_info WHERE valid_flag = 1
```

### 当前报警状态与报警记录的区分（必须遵守）

- 如果需求是“当前正在报警的设备数 / 报警设备列表 / 当前设备是否报警”，优先查询 `iot_equip_status.alarm_flag`，不要先查 `iot_equip_alarm`
- 如果需求是“当前正在报警的监测项 / 按监测项统计正在报警的设备数 / 当前监测项是否报警”，优先查询 `iot_equip_field.alarm_state`，不要先查 `iot_equip_alarm`
- 如果结果需要按监测项编码、监测项名称分组统计当前报警设备数，通常应从 `iot_equip_field` 关联 `iot_equip_info`，按 `field_code`、`field_name` 分组，并统计 `COUNT(DISTINCT equip_id)`
- 只有当需求明确涉及“报警记录、告警次数、历史报警、某时间段内发生的报警、报警开始时间、报警结束时间、处置情况、报警类型记录”等记录口径时，才使用 `iot_equip_alarm`
- 如果用户只说“正在报警”且没有要求时间范围、开始结束时间、报警明细，默认按“当前状态”处理，不要误写成“报警记录统计”
- 如果需求同时出现“当前状态”和“历史记录”两种口径，必须先区分再写 SQL，必要时先向用户确认

### 参数和输出字段确定
如果需求不清楚，例如过滤条件是什么，需要查询哪些字段，需要先和用户确认清楚。

### sql方言
如果用户没有明确是哪种数据库，需要先询问，如果没回答，默认是mysql方言

### 报警筛选

报警筛选统一通过 `value_type_id` 参数：
- 排除离线：`value_type_id != '-1'`
- 仅离线：`value_type_id = '-1'`
- 其他类型报警，通过 `value_type_id` 传入具体类型ID

补充说明：

- 上述 `value_type_id` 规则主要用于 `iot_equip_alarm` 这类报警记录查询，或需求明确要求按报警类型筛选时
- 如果需求只是判断“当前是否报警”或统计“当前正在报警数量”，优先使用状态字段：设备维度用 `iot_equip_status.alarm_flag`，监测项维度用 `iot_equip_field.alarm_state`
- 如果结果需要输出报警类型名称 `value_type_name`，应根据 `value_type_id` 关联 `iot_dic_equip_value`
- 关联报警类型表时，默认优先使用 `LEFT JOIN iot_dic_equip_value dv ON a.value_type_id = dv.value_type_id`；如果主查询不是 `iot_equip_alarm`，也按实际别名基于 `value_type_id` 关联
- 如需保证字典口径有效，可补充 `dv.valid_flag = 1`

### 设备类型筛选

通过设备表字段 `equip_type_id` 筛选设备类型。

- 单值参数使用 `equipTypeId`
- 多值参数使用 `equipTypeIds`
- 涉及 `iot_equip_info` 口径的统计时，默认必须带上其中一个参数，除非用户明确要求不按设备类型筛选
- 如果结果需要输出设备类型名称 `equip_type_name`，应根据 `equip_type_id` 关联 `iot_dic_equip`
- 关联设备类型表时，默认优先使用 `LEFT JOIN iot_dic_equip de ON ei.equip_type_id = de.equip_type_id`

### 厂家/企业

厂家和企业是同一概念，对应字段：`manufacturer_id`、`manufacturer_name`

### 指标和监测项
设备的指标和监测项是同一概念，对应表 `iot_equip_field`，编码是`field_code`。

### 设备类型名称
设备类型名称对应表 `iot_dic_equip` 的字段 `equip_type_name`；当需求中出现“设备类型名称”“类型名称”等展示字段时，应主动检查是否需要关联该表。

### 报警类型名称
报警类型名称对应表 `iot_dic_equip_value` 的字段 `value_type_name`；当需求中出现“报警类型名称”“告警名称”等展示字段时，应主动检查是否需要关联该表。

### 时间字段

- `iot_equip_alarm.alarm_time` - 报警开始时间
- `iot_equip_alarm.end_time` - 报警结束时间（null=进行中）
- `iot_equip_status.time` - 设备最新通讯时间

### 常用参数

| 参数名 | 说明 |
|--------|------|
| startTime | 查询开始时间 |
| endTime | 查询结束时间 |
| equipTypeId | 设备类型ID |
| equipTypeIds | 设备类型ID列表 |
| manufacturerId | 厂家/企业ID |
| valueTypeId | 报警类型ID |

---

## 模板语法

### 变量

```sql
-- 字符串需加引号
WHERE equip_name = '${equipName}'
-- 数值无需引号
WHERE count > ${minCount}
```

### 条件控制

```sql
#if (status == "valid")
  valid_flag = 1
#elseif (status == "invalid")
  valid_flag = 0
#else
  valid_flag IN (0, 1)
#end
```

### 循环

```sql
WHERE equip_id IN (
#for (String id : equipIds)
  #if (for.index > 1),#end '${id}'
#end
)
```

### WHERE标签

自动处理WHERE关键字，移除第一个AND：

```sql
#tag where()
  #if (equipTypeId != null && equipTypeId != '')
    AND equip_type_id = '${equipTypeId}'
  #end
  #if (equipTypeIds != null && equipTypeIds.size() > 0)
    AND equip_type_id IN (
    #for (String typeId : equipTypeIds)
      #if (for.index > 1),#end '${typeId}'
    #end
    )
  #end
  #if (startTime != null && startTime != '')
    AND alarm_time >= '${startTime}'
  #end
#end
```

### 时间函数

```sql
${today("yyyy-MM-dd")}           -- 2026-03-28
${today("yyyy-MM-dd HH:mm:ss")} -- 2026-03-28 14:30:00
```

---

## 返回结果处理

结果默认返回 `page` 对象（Groovy语法）。

### 提取单条

```groovy
com.egova.ddcat.util.ScriptUtils.getOne(page)
```

### KEY转驼峰

```groovy
com.egova.ddcat.util.ScriptUtils.toCamelCase(page)
```

### 时间格式化

```groovy
com.egova.ddcat.util.ScriptUtils.dateFormat(page)
com.egova.ddcat.util.ScriptUtils.dateFormat(page, 'yyyy年MM月dd日 HH:mm:ss')
```

### GIS坐标转换

```groovy
com.egova.ddcat.util.GisUtils.gcjll284ll(page, "longitude", "latitude")
com.egova.ddcat.util.GisUtils.convert(page, "F", null, "longitude", "latitude")
```

---

## 编写示例

### 按企业统计报警记录数（简化版）

需求：统计每个企业的报警记录条数（排除离线）

说明：直接统计 `iot_equip_alarm` 表的记录数；由于结果口径关联 `iot_equip_info`，默认保留设备类型筛选参数。

参数：startTime, endTime, equipTypeId

```sql
SELECT 
    ei.manufacturer_id,
    ei.manufacturer_name,
    COUNT(*) as 物联告警数
FROM iot_equip_alarm a
INNER JOIN iot_equip_info ei ON a.equip_id = ei.equip_id
#tag where()
    AND a.value_type_id != '-1'
    AND ei.valid_flag = 1
    #if (startTime != null && startTime != '')
        AND a.alarm_time >= '${startTime}'
    #end
    #if (endTime != null && endTime != '')
        AND a.alarm_time < '${endTime}'
    #end
    #if (equipTypeId != null && equipTypeId != '')
        AND ei.equip_type_id = '${equipTypeId}'
    #end
#end
GROUP BY ei.manufacturer_id, ei.manufacturer_name
ORDER BY 物联告警数 DESC
```

---

## 快速参考

| 场景 | 约束条件 |
|------|----------|
| 有效设备 | `valid_flag = 1` |
| 排除离线报警 | `value_type_id != '-1'` |
| 报警进行中 | `end_time IS NULL` |
| 报警已结束 | `end_time IS NOT NULL` |
| 设备在线 | `online_state = 1` |
| 当前报警设备统计 | 优先使用 `iot_equip_status.alarm_flag` |
| 当前报警监测项统计 | 优先使用 `iot_equip_field.alarm_state` |
| 报警记录/历史报警统计 | 使用 `iot_equip_alarm` |
| `iot_equip_info` 相关统计 | 默认增加 `equipTypeId` 或 `equipTypeIds` 参数 |

## 产出结果
- 用户需求描述
- 参数说明
- DDCAT SQL 脚本，如果统计较复杂，涉及到聚合等操作，需要标明 DDCAT中需添加缓存，默认5-30分钟，根据复杂程序决定。
- 返回结果示例
- 计算逻辑说明
- 可执行执行的sql，参数自定义给出
- 如果用户有要求输出md结果文档，需要包含以上内容，并且格式清晰，层次分明，便于阅读理解

---

## 真实项目案例（491340 威海供热）

`references/cases/491340-威海供热/` 收录威海供热项目物联网后端 DDCAT 接口的完整实战脚本，编写同类需求前优先参考：

| 案例文件 | 场景 |
|---------|------|
| `物联网1.0-设备报警统计-DDCAT-达梦.md` / `-mysql.md` | 设备报警统计（达梦 + MySQL 双数据库版本） |
| `设备异常数据分析-换热站监测.md` | 换热站监测异常分析（最完整，23KB） |
| `设备异常数据分析-首站监测.md` / `-管网监测.md` | 首站、管网监测异常分析 |
| `设备异常数据-室温监测.md` / `-楼宇监测.md` | 室温、楼宇监测异常数据 |
| `设备异常分析-设备监测项当前报警设备数及离线设备数统计.md` | 当前报警/离线设备数统计 |
| `一张图-月度物联告警次数排名.md` | 月度告警次数排名 |
| `一张图-月度设备离线时长排名.md` | 月度设备离线时长排名 |
| `一张图-月度户端低温报警排名.md` | 月度户端低温报警排名 |
