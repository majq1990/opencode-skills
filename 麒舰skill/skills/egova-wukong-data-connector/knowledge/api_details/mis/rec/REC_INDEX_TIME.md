# 基于时间的案件指标统计

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_INDEX_TIME |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 基于时间的案件指标统计 |
| apiType | trend |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/index/group?@state=time` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/基于时间的案件指标统计` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 折线图、趋势图、时间序列柱状图、趋势统计 |

---

## 2. 接口说明

该接口是“案件指标统计接口”的时间维度深化版。

与普通案件指标统计不同：

- 普通案件指标统计：统计经过条件筛选后的总指标值；
- 本接口：统计每年、每月、每天或每时的指标值。

可根据区划、案件来源、案件类型、问题类型等条件过滤，再按时间节点返回指标数据。

适合：

- 近 N 天上报趋势；
- 近 N 月结案趋势；
- 按小时上报趋势；
- 年度/月度案件趋势图。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdbstat | to_stat_info | 统计库案件表 |

---

## 4. 请求参数

### 4.1 时间维度参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| customTime | String | 否 | 当前时间 | 从哪个时间点查起，格式 `yyyy-MM-dd HH:mm:ss` |
| interval | Integer | 是 | 无 | 查询多少个时间点 |
| timeType | String | 是 | 无 | 时间类型：1 按时，2 按天，3 按月，4 按年 |

### 4.2 timeType 说明

| 值 | 含义 | 返回 name/text 格式 |
|---|---|---|
| 1 | 按时 | HH |
| 2 | 按天 | yyyy-MM-dd |
| 3 | 按月 | yyyy-MM |
| 4 | 按年 | yyyy |

### 4.3 指标参数

| 参数名 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| groupList | String[] | 是 | 需要统计的指标列表 |

### 4.4 支持的 groupList 指标
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

### 4.5 业务筛选参数

| 参数名 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| startTimestamp | String | 否 | 统计指标开始时间 |
| endTimestamp | String | 否 | 统计指标结束时间 |
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

### 4.6 同比、环比参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| TB | Boolean | 否 | false | 是否查询指标同比 |
| HB | Boolean | 否 | false | 是否查询指标环比 |
| tbTimeType | String | 否 | 无 | 查询同比时比较的时间段 |
| compareGroupList | String[] | 否 | 无 | 需要做同比/环比比较的指标 |

### 4.7 tbTimeType 说明

| 值 | 含义 |
|---|---|
| 4 | 跟去年同个时间段比较 |
| 3 | 跟上个月同个时间段比较 |
| 2 | 跟昨天同一个时间段比较 |

---

## 5. 请求示例

```json
{
  "eventSrcIds": [
    "3004"
  ],
  "districtId": "14",
  "groupList": [
    "report"
  ],
  "interval": 5,
  "timeType": "1"
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果数组 | 趋势图数据源 |
| result[].name | name | String | 是 | 时间节点 | 可映射为 `name` / `date` |
| result[].text | text | String | 是 | 时间节点 | 可映射为 `label` |
| result[].xxx | 动态字段 | String / Long / Double | 是 | `xxx` 来自 `groupList` 指标名称 | 可映射为 `value` |
| result[].xxx_TB | 动态字段 | Long / Double | 否 | 指标同比比较时段结果 | 可用于同比展示 |
| result[].xxx_TBRise | 动态字段 | Boolean | 否 | 同比是否上升 | 可用于趋势箭头 |
| result[].xxx_TBRate | 动态字段 | Double | 否 | 同比百分比 | 可用于同比率 |
| result[].xxx_HB | 动态字段 | Long / Double | 否 | 指标环比比较时段结果 | 可用于环比展示 |
| result[].xxx_HBRise | 动态字段 | Boolean | 否 | 环比是否上升 | 可用于趋势箭头 |
| result[].xxx_HBRate | 动态字段 | Double | 否 | 环比百分比 | 可用于环比率 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 辅助统计 |

---

## 7. 返回示例

原始文档未给出完整返回示例。按照返回字段说明，典型结构如下：

```json
{
  "hasError": false,
  "result": [
    {
      "name": "08",
      "text": "08",
      "report": 12
    },
    {
      "name": "09",
      "text": "09",
      "report": 20
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
| 请传入时间间隔! | `interval` 传参有问题 | 补充正确的 `interval` |
| 暂不支持该时间类型查询! | `timeType` 不支持 | 仅支持按年、按月、按天、按时 |
| 动态查询出错 | 动态 SQL 或指标查询异常 | 联系后端排查 |

---

## 9. 适配建议

### 适合组件

- 折线图；
- 趋势图；
- 时间序列柱状图；
- 面积图。

### 字段映射建议

以统计 `report` 上报数为例：

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| name | item.name | 字符串兜底 |
| date | item.name | 字符串兜底 |
| value | item.report | Number 转换 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            name: item.name || item.text || '',
            value: Number(item.report || 0)
        };
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
            name: item.name || item.text || '',
            value: Number(item[metricKey] || 0)
        };
    });
}
```

---

## 10. 性能和联调注意点

1. `interval` 和 `timeType` 必填。
2. `groupList` 必填。
3. 返回字段随 `groupList` 动态变化。
4. 按小时统计时，建议控制 `interval`，避免返回点位过多。
5. 如果开启同比或环比，必须传 `compareGroupList`。
6. `customTime` 不传时默认从当前时间查起。
