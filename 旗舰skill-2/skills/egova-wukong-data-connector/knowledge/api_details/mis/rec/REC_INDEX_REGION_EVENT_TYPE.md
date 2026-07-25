# 基于区划、问题类型的案件指标统计

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_INDEX_REGION_EVENT_TYPE |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 基于区划、问题类型的案件指标统计 |
| apiType | group |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/index/group?@state=multiField` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/基于区划、问题类型的案件指标统计` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 分组柱状图、堆叠柱状图、排行列表、二维统计表、区划问题类型矩阵 |

---

## 2. 接口说明

该接口是“案件指标统计接口”的多字段深化版本。

与普通案件指标统计接口不同：

- 普通案件指标统计：统计经过条件筛选后的总指标值；
- 本接口：统计经过条件筛选后，各个区划、问题类型组合维度下的指标值。

该接口需要通过传参获取想要展示的区划和问题类型，也可以根据条件过滤，例如：

- 统计某些问题类型；
- 统计某些案件来源；
- 统计某些区划；
- 按指定指标排序；
- 取 TopN。

典型用途：

- 各区问题类型分布；
- 区划 + 问题大类 TopN；
- 每个区不同问题类型的上报数；
- 区划问题类型矩阵；
- 堆叠柱状图。

注意：

1. 该接口传参不同，对应查询逻辑和返回字段会有区别；
2. 如遇到接口暂不支持的指标，需要联系后端重新开发；
3. 需展示的问题类型应是同一级别；
4. 需展示的区划应是同一级别；
5. `name` 是区划 id，`text` 是问题类型 id；
6. `regionName` 是区划名称；
7. `eventName` 是问题类型名称。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdbstat | to_stat_info | 统计库案件表 |
| cgdb | tc_region | 业务库区划表 |
| cgdb | tc_dic_event_any_type | 业务库问题类型表 |

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

### 4.4 问题类型展示范围参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| eventGradeIdList | String | 否 | 无 | 问题类型级别 |
| parentEventTypeIdList | String[] | 否 | 无 | 指定查询对应父类型 id 列表的子类型 |
| eventTypeIdList | String[] | 否 | 无 | 指定查询问题类型 id 列表 |
| excludeEventTypeIdList | String[] | 否 | 无 | 指定排除的问题类型 id 列表 |
| grandEventTypeIdList | String[] | 否 | 无 | 指定查询对应父类型 id 列表的孙子类型 |
| customFlag | Boolean | 否 | false | 传 true 时上述问题类型查询条件不生效，改用 `eventTypeCondition` |

> 注意：原始文档中区划条件和问题类型条件都出现了 `customFlag`。实际联调时如果二者同时需要自定义条件，建议现场确认后端是否共用同一个字段，避免语义冲突。

### 4.5 eventGradeIdList / eventTypeCondition.grade 说明

| 值 | 含义 |
|---|---|
| 1 | 问题类型 |
| 2 | 问题大类 |
| 3 | 问题小类 |

### 4.6 eventTypeCondition

| 参数路径 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| eventTypeCondition.id | String | 否 | 指定问题类型主键 |
| eventTypeCondition.ids | String[] | 否 | 指定问题类型主键列表 |
| eventTypeCondition.grade | String | 否 | 指定问题类型等级 |
| eventTypeCondition.parentId | String | 否 | 指定问题类型父类型，查询其子问题类型 |
| eventTypeCondition.parentIds | String[] | 否 | 指定问题类型父类型列表，查询其子问题类型 |

### 4.7 核心指标参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| groupList | String[] | 是 | 无 | 需要统计的指标列表 |
| startTimestamp | String | 否 | 当前时间减去 30 天的当天 0 时 0 分 0 秒 | 统计指标开始时间，格式 `yyyy-MM-dd HH:mm:ss` |
| endTimestamp | String | 否 | 当天 23 时 59 分 59 秒 | 统计指标结束时间，格式 `yyyy-MM-dd HH:mm:ss` |
| sortField | String | 否 | 无 | 指定根据哪个指标排序，即 `groupList` 中的某个指标 |
| desc | Integer | 否 | 无 | 传 `1` 为降序，否则为升序 |
| top | Integer | 否 | 无 | 排序后取前几个 |

### 4.8 支持的 groupList 指标
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

#### 百分比指标

| 指标 | 含义 |
|---|---|
| inTimeArchiveRate | 按期结案率 |
| archiveRate | 结案率 |
| disposeRate | 处置率 |
| inTimeRegisterRate | 按时立案率 |
| accurDispatchRate | 准确派遣率 |
| inTimeDisposeRate | 按期处置率 |

### 4.9 业务筛选参数

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
    "report",
    "archive",
    "archiveRate",
    "register"
  ],
  "eventGradeIdList": "2",
  "regionGradeIdList": [
    "2"
  ],
  "startTimestamp": "2021-07-01 23:00:00",
  "endTimestamp": "2021-08-01 23:00:00",
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
| result | result | Object[] | 是 | 返回结果数组 | 图表/二维表数据源 |
| result[].name | name | String | 是 | 区划 id | 可映射为 `regionId` |
| result[].text | text | String | 是 | 问题类型 id | 可映射为 `eventTypeId` |
| result[].regionName | regionName | String | 是 | 区划名称 | 可映射为 `regionName` |
| result[].eventName | eventName | String | 是 | 问题类型名称 | 可映射为 `eventName` |
| result[].xxx | 动态字段 | String / Long / Double | 是 | `xxx` 来自 `groupList` 指标名称 | 可映射为 `value` |
| result[].value | value | / | 否 | 示例中为 null | 通常不使用 |
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
      "text": "351",
      "value": null,
      "regionName": "鹿城区",
      "report": 12649,
      "eventName": "街面秩序",
      "archive": 11883,
      "archiveRate": 99.98,
      "register": 11885
    },
    {
      "name": "1",
      "text": "353",
      "value": null,
      "regionName": "鹿城区",
      "report": 11139,
      "eventName": "其他事件",
      "archive": 455,
      "archiveRate": 100,
      "register": 455
    },
    {
      "name": "4",
      "text": "353",
      "value": null,
      "regionName": "龙湾区",
      "report": 10668,
      "eventName": "其他事件",
      "archive": 269,
      "archiveRate": 98.9,
      "register": 272
    },
    {
      "name": "2",
      "text": "353",
      "value": null,
      "regionName": "瓯海区",
      "report": 7771,
      "eventName": "其他事件",
      "archive": 171,
      "archiveRate": 100,
      "register": 171
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
| 动态查询出错 | 动态 SQL 或指标查询异常 | 联系后端排查 |
| 请传入时间类型参数! | 开启计算平均值后未传 `timeType` | 补充 `timeType` |
| 请传入计时类型参数! | 开启计算平均值后未传 `timeSysId` | 补充 `timeSysId` |
| 无法获取系统日历! | `timeSysId` 无法获取系统日历数据 | 检查 `timeSysId` |
| 无法获取系统作息时间! | `timeSysId` 无法获取系统作息时间 | 检查 `timeSysId` |
| 没有属于此层级的区域 | `regionGradeIdList` 未查到对应区划 | 检查区域层级 |
| 所输入的父级区域id没有找到子区域 | `parentRegionIdList` 未查到子区划 | 检查父级区域 id |
| 所输入的父级类型id没有找到子类型 | 父问题类型列表未查到对应子类型 | 检查 `parentEventTypeIdList` / `grandEventTypeIdList` |
| 数据库不存在该事件层级 | `eventGradeIdList` 找不到对应问题类型 | 检查问题类型等级 |
| 暂不支持该事件等级查询! | 接口暂不支持该问题类型等级 | 联系后端评估开发 |

---

## 9. 适配建议

### 适合组件

- 堆叠柱状图；
- 分组柱状图；
- 二维统计表；
- 区划 + 问题类型排行；
- 问题类型矩阵；
- TopN 列表。

### 字段映射建议

以统计 `report` 上报数为例：

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| regionId | item.name | 字符串兜底 |
| regionName | item.regionName | 字符串兜底 |
| eventTypeId | item.text | 字符串兜底 |
| eventName | item.eventName | 字符串兜底 |
| value | item.report | Number 转换 |
| archive | item.archive | Number 转换 |
| archiveRate | item.archiveRate | Number 转换 |
| register | item.register | Number 转换 |

### 推荐过滤脚本：二维明细结构，data 为 result 本体

适合二维表、排行列表、普通列表。

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            regionId: item.name || '',
            regionName: item.regionName || '',
            eventTypeId: item.text || '',
            eventName: item.eventName || '',
            value: Number(item.report || 0),
            report: Number(item.report || 0),
            archive: Number(item.archive || 0),
            archiveRate: Number(item.archiveRate || 0),
            register: Number(item.register || 0)
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

### 推荐过滤脚本：堆叠柱状图结构

将同一区划下的不同问题类型合并为一条记录，适合堆叠柱状图。  
字段名会使用问题类型名称作为动态 key。

```javascript
function filter(data) {
    var map = {};
    var result = [];

    if (!Array.isArray(data)) {
        return [];
    }

    data.forEach(function (item) {
        var regionId = item.name || '';
        var regionName = item.regionName || '';
        var eventName = item.eventName || '未知类型';
        var value = Number(item.report || 0);

        if (!map[regionId]) {
            map[regionId] = {
                regionId: regionId,
                name: regionName
            };
            result.push(map[regionId]);
        }

        map[regionId][eventName] = value;
    });

    return result;
}
```

### 推荐过滤脚本：按区划汇总总量

如果组件只想看每个区的总量，不区分问题类型，可用：

```javascript
function filter(data) {
    var map = {};
    var result = [];

    if (!Array.isArray(data)) {
        return [];
    }

    data.forEach(function (item) {
        var regionId = item.name || '';
        var regionName = item.regionName || '';
        var value = Number(item.report || 0);

        if (!map[regionId]) {
            map[regionId] = {
                id: regionId,
                name: regionName,
                value: 0
            };
            result.push(map[regionId]);
        }

        map[regionId].value += value;
    });

    return result.sort(function (a, b) {
        return b.value - a.value;
    });
}
```

---

## 10. 性能和联调注意点

1. `groupList` 必填。
2. 返回字段随 `groupList` 动态变化。
3. `name` 是区划 id，不是展示名。
4. `text` 是问题类型 id，不是展示名。
5. `regionName` 才是区划展示名称。
6. `eventName` 才是问题类型展示名称。
7. 该接口是二维组合统计，返回行数可能是“区划数量 × 问题类型数量”。
8. 使用 TopN 时需确认是按组合维度 TopN，还是每个区划下分别 TopN。
9. 堆叠柱状图需要确认悟空组件是否支持动态系列字段。
10. 原始文档中区划和问题类型都存在 `customFlag`，联调时建议确认是否会产生参数语义冲突。
