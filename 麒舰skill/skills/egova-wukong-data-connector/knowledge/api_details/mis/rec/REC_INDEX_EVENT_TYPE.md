# 基于问题类型的案件指标统计

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_INDEX_EVENT_TYPE |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 基于问题类型的案件指标统计 |
| apiType | group |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/index/group?@state=eventType` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/基于问题类型的案件指标统计` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 饼图、柱状图、问题类型排行、TopN 列表 |

---

## 2. 接口说明

该接口是“案件指标统计接口”的问题类型维度深化版。

与普通案件指标统计不同：

- 普通案件指标统计：统计经过条件筛选后的总指标值；
- 本接口：统计经过条件筛选后，各个案件问题类型的指标值。

该接口需要通过传参获取想要展示的案件问题类型。也可根据区划、案件来源等条件过滤后，再按问题类型统计指标。

接口支持：

1. 按问题类型 / 问题大类 / 问题小类统计；
2. 根据区划、案件来源、案件类型等条件过滤；
3. 查询同比、环比；
4. 查询平均值；
5. 根据指标排序；
6. 取 TopN。

注意：

- 需展示的问题类型应是同一级别的问题类型；
- 该接口传参不同，返回字段会随 `groupList` 动态变化。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdbstat | to_stat_info | 统计库案件表 |
| cgdb | tc_dic_event_any_type | 业务库问题类型表 |

---

## 4. 请求参数

### 4.1 问题类型展示范围参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| eventGradeIdList | String | 否 | 无 | 问题类型级别 |
| parentEventTypeIdList | String[] | 否 | 无 | 指定查询对应父类型 id 列表的子类型 |
| eventTypeIdList | String[] | 否 | 无 | 指定查询问题类型 id 列表 |
| excludeEventTypeIdList | String[] | 否 | 无 | 指定排除的问题类型 id 列表 |
| grandEventTypeIdList | String[] | 否 | 无 | 指定查询对应父类型 id 列表的孙子类型 |
| customFlag | Boolean | 否 | false | 传 true 时上述查询条件不生效，改用 `eventTypeCondition` |
| eventTypeCondition | Object | 否 | 无 | 问题类型条件对象 |

### 4.2 eventGradeIdList / eventTypeCondition.grade 说明

| 值 | 含义 |
|---|---|
| 1 | 问题类型 |
| 2 | 问题大类 |
| 3 | 问题小类 |

### 4.3 eventTypeCondition

| 参数路径 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| eventTypeCondition.id | String | 否 | 指定问题类型主键 |
| eventTypeCondition.ids | String[] | 否 | 指定问题类型主键列表 |
| eventTypeCondition.grade | String | 否 | 指定问题类型等级 |
| eventTypeCondition.parentId | String | 否 | 指定问题类型父类型，查询其子问题类型 |
| eventTypeCondition.parentIds | String[] | 否 | 指定问题类型父类型列表，查询其子问题类型 |

### 4.4 核心指标参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| groupList | String[] | 是 | 无 | 需要统计的指标列表 |
| startTimestamp | String | 否 | 当前时间减去 30 天的当天 0 时 0 分 0 秒 | 统计指标开始时间，格式 `yyyy-MM-dd HH:mm:ss` |
| endTimestamp | String | 否 | 当天 23 时 59 分 59 秒 | 统计指标结束时间，格式 `yyyy-MM-dd HH:mm:ss` |
| sortField | String | 否 | 无 | 指定根据哪个指标排序 |
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

---

## 5. 请求示例

```json
{
  "groupList": [
    "report"
  ],
  "eventGradeIdList": "2",
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
| result[].name | name | String | 是 | 问题类型 id | 可映射为 `id` |
| result[].text | text | String | 是 | 问题类型名称 | 可映射为 `name` / `label` |
| result[].xxx | 动态字段 | String / Long / Double | 是 | `xxx` 来自 `groupList` 指标名称 | 可映射为 `value` |
| result[].xxx_TB | 动态字段 | Long / Double | 否 | 同比比较时段结果 | 同比展示 |
| result[].xxx_TBRise | 动态字段 | Boolean | 否 | 同比是否上升 | 趋势箭头 |
| result[].xxx_TBRate | 动态字段 | Double | 否 | 同比百分比 | 同比率 |
| result[].xxx_HB | 动态字段 | Long / Double | 否 | 环比比较时段结果 | 环比展示 |
| result[].xxx_HBRise | 动态字段 | Boolean | 否 | 环比是否上升 | 趋势箭头 |
| result[].xxx_HBRate | 动态字段 | Double | 否 | 环比百分比 | 环比率 |
| result[].xxx_avg | 动态字段 | Double | 否 | 指标平均值 | 平均值展示 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 辅助统计 |

---

## 7. 返回示例

原始文档中返回结构为动态指标结构，典型形态如下：

```json
{
  "hasError": false,
  "result": [
    {
      "name": "351",
      "text": "街面秩序",
      "value": null,
      "report": 12649
    },
    {
      "name": "353",
      "text": "其他事件",
      "value": null,
      "report": 11139
    }
  ],
  "message": null,
  "tag": null,
  "totalCount": 2
}
```

---

## 8. 报错说明

| message | 说明 | 处理建议 |
|---|---|---|
| 其他报错 | 需联系后台排查数据 | 查看后台日志 |
| 需要统计的指标为空！ | `groupList` 未传参 | 补充 `groupList` |
| 动态查询出错 | 动态 SQL 或指标查询异常 | 联系后端排查 |
| 数据库不存在该事件层级 | `eventGradeIdList` 找不到对应问题类型 | 检查问题类型等级 |
| 暂不支持该事件等级查询! | 该事件等级接口暂不支持 | 联系后端评估开发 |
| 所输入的父级类型id没有找到子类型 | 父问题类型 id 未查到子类型 | 检查 `parentEventTypeIdList` 或 `grandEventTypeIdList` |

---

## 9. 适配建议

### 适合组件

- 饼图；
- 柱状图；
- 问题类型排行；
- TopN 列表；
- 问题类型占比图。

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
3. 需展示的问题类型应是同一级别，例如都为问题大类或都为问题小类。
4. 排序字段 `sortField` 应是 `groupList` 中的指标。
5. 使用 TopN 时需确认排序字段和排序方向。
