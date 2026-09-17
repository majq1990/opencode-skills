# 基于人员的案件指标统计

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_INDEX_PATROL |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 基于人员的案件指标统计 |
| apiType | group |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/index/group?@state=patrol` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/基于人员的案件指标统计` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 柱状图、人员排行、绩效排行、TopN 列表 |

---

## 2. 接口说明

该接口是“案件指标统计接口”的人员维度深化版。

与普通案件指标统计不同：

- 普通案件指标统计：统计经过条件筛选后的总指标值；
- 本接口：统计经过条件筛选后，各个人员的指标值。

该接口需要通过传参获取想要展示的人员，否则默认展示所有人员。

接口支持：

1. 按人员统计案件指标；
2. 根据区划、案件类型、问题类型、案件来源等条件过滤；
3. 查询指标同比；
4. 查询指标环比；
5. 根据指标排序；
6. 取 TopN。

注意：

- 目前人员指标固定，暂未做完全动态统计；
- 如遇到不支持的指标，需要联系后端重新开发；
- 原始文档中部分参数说明仍写“案件来源”，但本接口业务含义是人员维度，应以返回示例中的人员字段为准。

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
| sortField | String | 否 | 无 | 指定根据哪个指标排序 |
| desc | Integer | 否 | 无 | 传 `1` 为降序，否则为升序 |
| top | Integer | 否 | 无 | 排序后取前几个 |

### 4.2 人员展示范围参数

| 参数名 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| id | String | 否 | 指定人员 id |
| ids | String[] | 否 | 指定人员 id 列表 |
| excludeIds | String[] | 否 | 指定排除的人员 id 列表 |
| seniorId | String | 否 | 指定人员父级来源 id，字段语义需现场确认 |
| seniorIds | String[] | 否 | 指定人员父级来源 id 列表，字段语义需现场确认 |
| humanCodes | String[] | 否 | 指定人员 id / 人员编码 |

### 4.3 支持的 groupList 指标
> 完整案件、比率、监督员/人员指标枚举参考 `knowledge/record_index_metrics.md`；本节只列常用指标，动态返回字段通常与 `groupList` 中的指标 `value` 同名。

| 指标 | 含义 |
|---|---|
| report | 上报数 |
| validReport | 有效上报数 |
| validReportRate | 有效上报率 |
| verify | 核实数 |
| inTimeVerify | 按期核实数 |
| intimeVerifyRate | 按期核实率 |
| check | 核查数 |
| inTimeCheck | 按期核查数 |
| intimeCheckRate | 按期核查率 |

### 4.4 业务筛选参数

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

### 4.5 同比、环比参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| TB | Boolean | 否 | false | 是否查询指标同比 |
| HB | Boolean | 否 | false | 是否查询指标环比 |
| compareGroupList | String[] | 否 | 无 | 需要做同比/环比比较的指标 |
| timeType | String | 否 | 无 | 查询同比或平均值时使用的时间类型 |

---

## 5. 请求示例

原始文档请求示例中使用 `dispose`，但人员指标当前支持列表里未包含 `dispose`，联调时应优先使用文档列出的人员指标，例如 `report`、`validReport`、`verify`、`check`。

```json
{
  "groupList": [
    "report"
  ],
  "startTimestamp": "2022-09-01 00:00:00",
  "endTimestamp": "2022-10-01 23:59:59",
  "sortField": "report",
  "desc": 1
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果数组 | 图表数据源 |
| result[].name | name | String | 是 | 人员 id | 可映射为 `id` |
| result[].text | text | String | 是 | 人员名称 | 可映射为 `name` |
| result[].value | value | String / Number | 否 | 通用值，示例中为 null | 通常不直接使用 |
| result[].unitId | unitId | String | 否 | 所属部门 id | 可用于联动 |
| result[].unitName | unitName | String | 否 | 所属部门名称 | 可展示 |
| result[].regionId | regionId | String | 否 | 所属区域 id | 可用于联动 |
| result[].regionName | regionName | String | 否 | 所属区域名称 | 可展示 |
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

```json
{
  "hasError": false,
  "result": [
    {
      "name": "112689",
      "text": "张维清",
      "value": null,
      "unitId": "107435",
      "unitName": "南门峡镇麻其村",
      "regionId": "11194",
      "regionName": "麻其村",
      "synthesis": 40
    },
    {
      "name": "112665",
      "text": "张生昌",
      "value": null,
      "unitId": "107429",
      "unitName": "南门峡镇卷槽村",
      "regionId": "11192",
      "regionName": "卷槽村",
      "synthesis": 40
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

- 人员排行；
- 人员绩效榜；
- 柱状图；
- TopN 列表；
- 人员指标表格。

### 字段映射建议

以示例中的 `synthesis` 综合分为例：

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.name | 字符串兜底 |
| name | item.text | 字符串兜底 |
| value | item.synthesis | Number 转换 |
| unitName | item.unitName | 字符串兜底 |
| regionName | item.regionName | 字符串兜底 |

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
            value: Number(item.synthesis || 0),
            unitName: item.unitName || '',
            regionName: item.regionName || ''
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

### 通用过滤脚本：支持指定动态指标字段

如果实际使用 `report`、`validReport`、`verify` 等指标，将 `metricKey` 改成对应字段。

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
            value: Number(item[metricKey] || 0),
            unitName: item.unitName || '',
            regionName: item.regionName || ''
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

---

## 10. 性能和联调注意点

1. `groupList` 必填。
2. 人员维度指标当前固定，未完全动态化。
3. 原始请求示例中的 `dispose` 与人员指标支持列表不一致，联调时需以现场接口真实支持情况为准。
4. 如果展示指定人员，需要传 `humanCodes` 或人员范围参数。
5. 如果开启同比或环比，必须传 `compareGroupList`。
6. 排序字段 `sortField` 应是接口实际返回的指标字段。
