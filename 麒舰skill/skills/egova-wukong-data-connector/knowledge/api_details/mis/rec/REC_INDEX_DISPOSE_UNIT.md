# 基于处置部门的案件指标统计

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_INDEX_DISPOSE_UNIT |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 基于处置部门的案件指标统计 |
| apiType | group |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/index/group?@state=disposeUnit` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/基于处置部门的案件指标统计` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 柱状图、部门排行、处置部门统计、TopN 列表 |

---

## 2. 接口说明

该接口是“案件指标统计接口”的处置部门维度深化版。

与普通案件指标统计不同：

- 普通案件指标统计：统计经过条件筛选后的总指标值；
- 本接口：统计各个处置部门的指标值。

可按条件过滤某些问题类型、问题来源、案件类型、区划范围等案件数据，再按处置部门分组统计指标。

接口支持：

1. 根据处置部门分组；
2. 查询多个动态指标；
3. 查询同比、环比；
4. 查询平均值；
5. 根据指标排序；
6. 取 TopN；
7. 根据上级部门 id 集合过滤。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdbstat | to_stat_info | 统计库案件表 |
| cgdb | tc_wf_act_def | 业务库工作流活动定义表 |
| cgdb | tc_wf_act_part | 业务库工作流活动参与者表 |
| cgdb | tc_role | 业务库岗位表 |
| cgdb | tc_unit | 业务库部门表 |

---

## 4. 请求参数

### 4.1 核心统计参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| groupList | String[] | 是 | 无 | 需要统计的指标列表 |
| startTimestamp | String | 否 | 当前时间减去 30 天的当天 0 时 0 分 0 秒 | 统计指标开始时间，格式 `yyyy-MM-dd HH:mm:ss` |
| endTimestamp | String | 否 | 当天 23 时 59 分 59 秒 | 统计指标结束时间，格式 `yyyy-MM-dd HH:mm:ss` |
| sortField | String | 否 | 无 | 指定根据哪个指标排序，值通常为 `groupList` 中的某个指标 |
| desc | Integer | 否 | 无 | 传 `1` 为降序，否则为升序 |
| top | Integer | 否 | 无 | 排序后取前几个 |
| parentUnitIds | String[] | 否 | 无 | 上级部门 id 集合 |

### 4.2 支持的 groupList 指标
> 完整案件、比率、监督员/人员指标枚举参考 `knowledge/record_index_metrics.md`；本节只列常用指标，动态返回字段通常与 `groupList` 中的指标 `value` 同名。

#### 数量指标

| 指标 | 含义 |
|---|---|
| report | 上报数 |
| dispose | 处置数 |
| toDispose | 未处置数 |
| event | 事件数 |
| part | 部件数 |
| accept | 受理数 |
| register | 立案数 |
| overTimeArchived | 超期结案数 |
| overTimeToDispose | 超期未处置数 |
| dispatch | 派遣数 |
| archive | 结案数 |
| needArchiveNum | 应结案数 |
| imTimeArchiveNum | 按期处置数 |
| inTimeDispose | 按期处置数 |
| accurDispatch | 准确派遣数 |
| overtimeDispose | 超期处置数 |
| inTimeRegister | 按时立案数 |
| patrolDealFlag | 自行处置数 |
| total | 案件总数 |

#### 百分比/时长指标

| 指标 | 含义 |
|---|---|
| inTimeArchiveRate | 按期结案率 |
| archiveRate | 结案率 |
| disposeRate | 处置率 |
| inTimeRegisterRate | 按时立案率 |
| accurDispatchRate | 准确派遣率 |
| inTimeDisposeRate | 按期处置率 |
| avgHandleTime | 平均处置时长 |
| avgAcceptTime | 平均受理时长 |

### 4.3 业务筛选参数

| 参数名 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| dutyGridId | String | 否 | 责任网格 id |
| cellId | String | 否 | 单元网格 id |
| communityId | String | 否 | 社区 id |
| streetId | String | 否 | 街道 id |
| districtId | String | 否 | 区县 id |
| cityId | Integer | 否 | 市 id |
| recTypeId | Integer | 否 | 案件类型 id |
| eventTypeId | String | 否 | 问题类型 id |
| mainTypeId | String | 否 | 问题大类 id |
| subTypeId | String | 否 | 问题小类 id |
| eventTypeIds | String[] | 否 | 问题类型 id 列表 |
| notEventTypeId | String | 否 | 排除指定问题类型 |
| eventSrcId | String | 否 | 案件来源 id |
| eventSrcIds | String[] | 否 | 案件来源 id 列表 |

### 4.4 同比、环比、平均值参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| TB | Boolean | 否 | false | 是否查询指标同比 |
| HB | Boolean | 否 | false | 是否查询指标环比 |
| compareGroupList | String[] | 否 | 无 | 需要做同比/环比比较的指标 |
| timeType | String | 否 | 无 | 查询同比或平均值时使用的时间类型 |
| avgFlag | Boolean | 否 | false | 是否计算指标平均值 |
| avgGroupList | String[] | 否 | 无 | 需要计算平均值的指标 |
| timeSysId | String | 否 | 无 | 计时类型 id，来自 `tc_dic_time_sys_name.time_sys_id` |
| workFlag | Boolean | 否 | false | 是否只统计工作日 |

---

## 5. 请求示例

```json
{
  "groupList": [
    "report"
  ],
  "startTimestamp": "2022-01-01 00:00:00",
  "endTimestamp": "2022-01-31 23:59:59",
  "sortField": "report",
  "desc": 1,
  "top": 5
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果数组 | 图表数据源 |
| result[].name | name | String | 是 | 部门 id | 可映射为 `id` |
| result[].text | text | String | 是 | 部门名称 | 可映射为 `name` / `label` |
| result[].xxx | 动态字段 | String / Long / Double | 是 | `xxx` 来自 `groupList` 指标名称 | 可映射为 `value` |
| result[].xxx_TB | 动态字段 | Long / Double | 否 | 指标同比比较时段结果 | 可用于同比展示 |
| result[].xxx_TBRise | 动态字段 | Boolean | 否 | 同比是否上升 | 可用于趋势箭头 |
| result[].xxx_TBRate | 动态字段 | Double | 否 | 同比百分比 | 可用于同比率 |
| result[].xxx_HB | 动态字段 | Long / Double | 否 | 指标环比比较时段结果 | 可用于环比展示 |
| result[].xxx_HBRise | 动态字段 | Boolean | 否 | 环比是否上升 | 可用于趋势箭头 |
| result[].xxx_HBRate | 动态字段 | Double | 否 | 环比百分比 | 可用于环比率 |
| result[].xxx_avg | 动态字段 | Double | 否 | 指标平均值 | 可用于平均值展示 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 辅助统计 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "name": "1",
      "text": "网格化城市管理",
      "value": null,
      "report": 0
    }
  ],
  "message": null,
  "tag": null,
  "totalCount": 1
}
```

---

## 8. 报错说明

| message | 说明 | 处理建议 |
|---|---|---|
| 其他报错 | 需联系后台排查数据 | 查看后台日志 |
| 需要统计的指标为空！ | `groupList` 未传参 | 补充 `groupList` |
| 需要统计同比的指标为空！ | 开启同比后 `compareGroupList` 未传参 | 补充 `compareGroupList` |
| 需要统计环比的指标为空！ | 开启环比后 `compareGroupList` 未传参 | 补充 `compareGroupList` |
| 动态查询出错 | 动态 SQL 或指标查询异常 | 联系后端排查 |
| 请传入时间类型参数! | 开启平均值后未传 `timeType` | 补充 `timeType` |
| 请传入计时类型参数! | 开启平均值后未传 `timeSysId` | 补充 `timeSysId` |
| 无法获取系统日历! | `timeSysId` 无法获取系统日历数据 | 检查 `timeSysId` |
| 无法获取系统作息时间! | `timeSysId` 无法获取系统作息时间 | 检查 `timeSysId` |

---

## 9. 适配建议

### 适合组件

- 柱状图；
- 横向柱状图；
- 部门排行；
- TopN 列表；
- 部门案件处置统计。

### 字段映射建议

以统计 `report` 上报数为例：

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.name | 字符串兜底 |
| name | item.text | 字符串兜底 |
| value | item.report | Number 转换 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            id: item.name || '',
            name: item.text || '',
            value: Number(item.report || 0)
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

### 通用过滤脚本：支持指定动态指标字段

```javascript
function filter(data) {
    var metricKey = 'report';

    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            id: item.name || '',
            name: item.text || '',
            value: Number(item[metricKey] || 0)
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

---

## 10. 性能和联调注意点

1. `groupList` 必填。
2. 返回字段随 `groupList` 动态变化。
3. 如果开启同比或环比，必须传 `compareGroupList`。
4. 如果开启平均值，必须传 `timeType`、`avgGroupList`、`timeSysId`。
5. 统计处置部门排行时，建议明确 `sortField`、`desc`、`top`。
6. 如需按上级部门筛选，使用 `parentUnitIds`。
