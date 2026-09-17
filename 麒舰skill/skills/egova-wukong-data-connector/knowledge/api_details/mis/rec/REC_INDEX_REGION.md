# 基于区划的案件指标统计

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_INDEX_REGION |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 基于区划的案件指标统计 |
| apiType | group |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/index/group?@state=region` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/基于区划的案件指标统计` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 柱状图、排行列表、区划统计图、区域指标卡、TopN 列表 |

---

## 2. 接口说明

该接口是“案件指标统计接口”的区划维度深化版。

与普通案件指标统计不同：

- 普通案件指标统计：统计经过条件筛选后的总指标值；
- 本接口：统计经过条件筛选后，各个区划的指标值。

该接口可以按区划维度统计案件指标，例如：

- 各区上报数；
- 各区结案数；
- 各区处置数；
- 各区结案率；
- 各街道案件总数排行；
- 各社区超期未处置数排行。

接口支持：

1. 指定需要展示的区划范围；
2. 根据问题类型、案件来源、案件类型、时间范围等条件过滤；
3. 查询指标同比；
4. 查询指标环比；
5. 查询指标平均值；
6. 根据指定指标排序；
7. 取 TopN。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdbstat | to_stat_info | 统计库案件表 |
| cgdb | tc_region | 业务库区划表 |

---

## 4. 请求参数

### 4.1 区划展示范围参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| parentRegionIdList | String[] | 否 | 无 | 查询指定父区划 id 列表的子区划 |
| regionIdList | String[] | 否 | 无 | 查询指定 id 列表的区划 |
| excludeRegionIdList | String[] | 否 | 无 | 查询时排除指定 id 列表的区划 |
| regionGradeIdList | String[] | 否 | 无 | 查询指定级别的区划 |
| customFlag | Boolean | 否 | false | 传 true 时，上述区划查询条件不生效，改用 `regionCondition` |

### 4.2 regionGradeIdList / regionCondition.regionType 说明

| 值 | 含义 |
|---|---|
| 1 | 市 |
| 2 | 区县 |
| 3 | 街道 |
| 4 | 社区 |
| 5 | 网格 |

### 4.3 regionCondition

| 参数路径 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| regionCondition.id | String | 否 | 指定区划主键 |
| regionCondition.ids | String[] | 否 | 指定区划主键列表 |
| regionCondition.regionType | Integer | 否 | 查询指定级别的区划 |
| regionCondition.parentId | String | 否 | 指定查询父区划下属子区划 |
| regionCondition.parentIds | String[] | 否 | 指定查询父区划列表下属子区划 |

### 4.4 指标参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| groupList | String[] | 是 | 无 | 需要统计的指标列表 |
| startTimestamp | String | 否 | 当前时间减去 30 天的当天 0 时 0 分 0 秒 | 统计指标开始时间，格式 `yyyy-MM-dd HH:mm:ss` |
| endTimestamp | String | 否 | 当天 23 时 59 分 59 秒 | 统计指标结束时间，格式 `yyyy-MM-dd HH:mm:ss` |
| sortField | String | 否 | 无 | 指定根据哪个指标排序，值通常为 `groupList` 中的某个指标 |
| desc | Integer | 否 | 无 | 传 `1` 为降序，否则为升序 |
| top | Integer | 否 | 无 | 排序后取前几个 |

### 4.5 支持的 groupList 指标
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

### 4.6 业务筛选参数

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

### 4.7 同比、环比、平均值参数

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

### 4.8 timeType 说明

| 值 | 同比比较 | 平均值含义 |
|---|---|---|
| 4 | 跟去年同个时间段比较 | 每年平均值 |
| 3 | 跟上个月同个时间段比较 | 每月平均值 |
| 2 | 跟昨天同一个时间段比较 | 每天平均值；只计算工作日时为每个工作日平均值 |
| 1 | 无 | 每时平均值；只计算工作日时为每个工作时平均值 |

---

## 5. 请求示例

```json
{
  "groupList": [
    "report"
  ],
  "startTimestamp": "2022-01-01 00:00:00",
  "endTimestamp": "2022-01-31 23:59:59",
  "customFlag": true,
  "TB": true,
  "HB": true,
  "compareGroupList": [
    "report"
  ],
  "regionCondition": {
    "regionType": "2"
  },
  "sortField": "report",
  "desc": 1,
  "top": 4
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果数组 | 图表数据源 |
| result[].name | name | String | 是 | 区划 id | 可映射为 `id` |
| result[].text | text | String | 是 | 区划名称 | 可映射为 `name` / `label` |
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
      "text": "鹿城区",
      "value": null,
      "report_HBRise": false,
      "report_TBRise": true,
      "report_HB": 81535,
      "report": 71207,
      "report_TB": 0,
      "report_HBRate": 12.67,
      "report_TBRate": 7120700.0
    },
    {
      "name": "4",
      "text": "龙湾区",
      "value": null,
      "report_HBRise": false,
      "report_TBRise": true,
      "report_HB": 43879,
      "report": 39032,
      "report_TB": 0,
      "report_HBRate": 11.05,
      "report_TBRate": 3903200.0
    }
  ],
  "message": null,
  "tag": null,
  "totalCount": 4
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
| 没有属于此层级的区域 | `regionGradeIdList` 未查到区划 | 检查区划层级参数 |
| 所输入的父级区域id没有找到子区域 | `parentRegionIdList` 未查到子区划 | 检查父级区划 id |

---

## 9. 适配建议

### 适合组件

- 柱状图；
- 横向柱状图；
- 区划排行；
- TopN 列表；
- 区域指标卡。

### 字段映射建议

以统计 `report` 上报数为例：

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.name | 字符串兜底 |
| name | item.text | 字符串兜底 |
| value | item.report | Number 转换 |
| tb | item.report_TB | Number 转换 |
| tbRate | item.report_TBRate | Number 转换 |
| tbRise | item.report_TBRise | Boolean |
| hb | item.report_HB | Number 转换 |
| hbRate | item.report_HBRate | Number 转换 |
| hbRise | item.report_HBRise | Boolean |

### 推荐过滤脚本：统计单指标，data 为 result 本体

默认示例按 `report` 映射。

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            id: item.name || '',
            name: item.text || '',
            value: Number(item.report || 0),
            tb: Number(item.report_TB || 0),
            tbRate: Number(item.report_TBRate || 0),
            tbRise: item.report_TBRise === true,
            hb: Number(item.report_HB || 0),
            hbRate: Number(item.report_HBRate || 0),
            hbRise: item.report_HBRise === true
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

### 通用过滤脚本：支持指定动态指标字段

如果悟空支持在过滤脚本里固定一个指标字段，可把 `metricKey` 改为需要展示的指标，例如 `archive`、`disposeRate`。

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

1. `groupList` 必填，否则接口会报“需要统计的指标为空！”。
2. 返回字段会随 `groupList` 动态变化，不能固定认为一定有 `report`。
3. 如果开启同比或环比，必须传 `compareGroupList`。
4. 如果开启平均值，必须传 `timeType`、`avgGroupList`、`timeSysId`。
5. 需展示的区划应是同一级别。
6. 排序字段 `sortField` 应是 `groupList` 中的指标。
7. 使用 TopN 时需同时确认排序字段和排序方向。
