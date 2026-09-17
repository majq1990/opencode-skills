# 案件指标统计

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_INDEX_SUMMARY |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 案件指标统计 |
| apiType | metrics |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/index/group` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/案件指标统计` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | object |
| 适配组件 | 指标卡、多指标卡、统计概览、同比环比指标卡 |

---

## 2. 接口说明

该接口用于统计经过条件筛选后的案件指标值。

与各类分组接口不同：

- 本接口返回总体指标；
- 不按区划、来源、问题类型、部门、人员等维度分组；
- 如果需要分组统计，应使用对应 `@state` 接口。

适合：

- 案件总览指标；
- 多指标卡；
- 今日上报数、结案数、处置数；
- 结案率、处置率、平均处置时长；
- 同比/环比指标卡。

接口支持：

1. 动态指定需要统计的指标；
2. 按时间范围过滤；
3. 按区划、案件来源、问题类型、案件类型过滤；
4. 查询指标同比；
5. 查询指标环比；
6. 查询指标平均值。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdbstat | to_stat_info | 统计库案件表 |

---

## 4. 请求参数

### 4.1 核心指标参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| groupList | String[] | 是 | 无 | 需要统计的指标列表 |
| startTimestamp | String | 否 | 当前时间减去 30 天的当天 0 时 0 分 0 秒 | 统计指标开始时间，格式 `yyyy-MM-dd HH:mm:ss` |
| endTimestamp | String | 否 | 当天 23 时 59 分 59 秒 | 统计指标结束时间，格式 `yyyy-MM-dd HH:mm:ss` |

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
| timeSysId | String | 否 | 无 | 计时类型 id |
| workFlag | Boolean | 否 | false | 是否只统计工作日 |

### 4.5 timeType 说明

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
    "report",
    "archive",
    "disposeRate"
  ],
  "startTimestamp": "2022-01-01 00:00:00",
  "endTimestamp": "2022-01-31 23:59:59",
  "TB": true,
  "HB": true,
  "compareGroupList": [
    "report",
    "archive"
  ],
  "timeType": "2"
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object | 是 | 指标结果对象 | 指标卡数据源 |
| result.xxx | 动态字段 | Long / Double | 是 | `xxx` 来自 `groupList` 指标名称 | 可映射为指标值 |
| result.xxx_TB | 动态字段 | Long / Double | 否 | 同比比较时段结果 | 同比值 |
| result.xxx_TBRise | 动态字段 | Boolean | 否 | 同比是否上升 | 趋势箭头 |
| result.xxx_TBRate | 动态字段 | Double | 否 | 同比百分比 | 同比率 |
| result.xxx_HB | 动态字段 | Long / Double | 否 | 环比比较时段结果 | 环比值 |
| result.xxx_HBRise | 动态字段 | Boolean | 否 | 环比是否上升 | 趋势箭头 |
| result.xxx_HBRate | 动态字段 | Double | 否 | 环比百分比 | 环比率 |
| result.xxx_avg | 动态字段 | Double | 否 | 指标平均值 | 平均值 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 通常为 1 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": {
    "report": 71207,
    "archive": 65000,
    "disposeRate": 91.27,
    "report_HB": 81535,
    "report_HBRise": false,
    "report_HBRate": 12.67,
    "report_TB": 0,
    "report_TBRise": true,
    "report_TBRate": 7120700.0
  },
  "message": null,
  "tag": null,
  "totalCount": 1
}
```

---

## 8. 报错说明

| message | 说明 | 处理建议 |
|---|---|---|
| 需要统计的指标为空！ | `groupList` 未传参 | 补充 `groupList` |
| 需要统计同比的指标为空！ | 开启同比后 `compareGroupList` 未传参 | 补充 `compareGroupList` |
| 需要统计环比的指标为空！ | 开启环比后 `compareGroupList` 未传参 | 补充 `compareGroupList` |
| 动态查询出错 | 动态 SQL 或指标查询异常 | 联系后端排查 |
| 请传入时间类型参数! | 开启平均值后未传 `timeType` | 补充 `timeType` |
| 请传入计时类型参数! | 开启平均值后未传 `timeSysId` | 补充 `timeSysId` |
| 无法获取系统日历! | `timeSysId` 无法获取系统日历数据 | 检查 `timeSysId` |
| 无法获取系统作息时间! | `timeSysId` 无法获取系统作息时间 | 检查 `timeSysId` |
| 其他报错 | 需联系后台排查数据 | 查看后台日志 |

---

## 9. 适配建议

### 适合组件

- 指标卡；
- 多指标卡；
- 总览卡片；
- 同比环比卡片。

### 字段映射建议：单指标卡

以 `report` 上报数为例：

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| title | 固定值 | 例如“上报数” |
| value | data.report | Number 转换 |
| hb | data.report_HB | Number 转换 |
| hbRate | data.report_HBRate | Number 转换 |
| hbRise | data.report_HBRise | Boolean |
| tb | data.report_TB | Number 转换 |
| tbRate | data.report_TBRate | Number 转换 |
| tbRise | data.report_TBRise | Boolean |

### 推荐过滤脚本：单指标卡，data 为 result 本体

```javascript
function filter(data) {
    if (!data) {
        return {
            title: '上报数',
            value: 0
        };
    }

    return {
        title: '上报数',
        value: Number(data.report || 0),
        hb: Number(data.report_HB || 0),
        hbRate: Number(data.report_HBRate || 0),
        hbRise: data.report_HBRise === true,
        tb: Number(data.report_TB || 0),
        tbRate: Number(data.report_TBRate || 0),
        tbRise: data.report_TBRise === true
    };
}
```

### 推荐过滤脚本：多指标卡，data 为 result 本体

```javascript
function filter(data) {
    if (!data) {
        data = {};
    }

    return [
        {
            title: '上报数',
            value: Number(data.report || 0)
        },
        {
            title: '结案数',
            value: Number(data.archive || 0)
        },
        {
            title: '处置率',
            value: Number(data.disposeRate || 0)
        }
    ];
}
```

---

## 10. 性能和联调注意点

1. `groupList` 必填。
2. 返回字段随 `groupList` 动态变化。
3. 多指标卡要确保 `groupList` 包含全部展示字段。
4. 如果开启同比或环比，必须传 `compareGroupList`。
5. 如果开启平均值，必须传 `avgFlag`、`avgGroupList`、`timeType`、`timeSysId`。
6. 该接口不分组；如果要按区划、来源、问题类型、部门、时间分组，应使用对应 `@state` 接口。
