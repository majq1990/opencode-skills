# 案件热力图

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_HEATMAP |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 案件热力图 |
| apiType | heatmap |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/heatmap` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/案件热力图` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 热力图、地图热力层、案件分布图 |

---

## 2. 接口说明

该接口用于案件热力图展示。

它会统计某个经纬度下有多少条案件，返回：

- 经度；
- 纬度；
- 案件数量。

可根据区划、案件来源、问题类型、案件状态、人员、部门等条件过滤。

查询过滤逻辑与案件列表查询、案件分页查询相同。

注意：

- 时间跨度较大时查询效率会降低；
- 使用该接口时建议查询时间跨度小于一个月。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdbstat | to_stat_info | 统计库案件表 |

---

## 4. 请求参数

### 4.1 基础参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| ids | String[] | 否 | 无 | 查询案件主键在 ids 列表中的案件信息 |
| point | Integer | 否 | 2 | 经纬字段返回保留的小数点位数 |
| startCreateTime | String | 否 | 无 | 创建开始时间，格式 `yyyy-MM-dd HH:mm:ss` |
| endCreateTime | String | 否 | 无 | 创建结束时间，格式 `yyyy-MM-dd HH:mm:ss` |
| taskNum | String | 否 | 无 | 查询指定任务号 |
| taskNos | String[] | 否 | 无 | 查询任务号在 taskNos 列表中的案件 |
| bizId | Integer | 否 | 无 | 案件业务标识 |

### 4.2 区划过滤参数

| 参数名 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| dutyGridId | String | 否 | 责任网格 id |
| dutyGridIds | String[] | 否 | 责任网格 id 列表 |
| excludeDutyGridIds | String[] | 否 | 排除责任网格 id 列表 |
| cellId | String | 否 | 单元网格 id |
| cellIds | String[] | 否 | 单元网格 id 列表 |
| excludeCellIds | String[] | 否 | 排除单元网格 id 列表 |
| communityId | String | 否 | 社区 id |
| communityIds | String[] | 否 | 社区 id 列表 |
| excludeCommunityIds | String[] | 否 | 排除社区 id 列表 |
| streetId | String | 否 | 街道 id |
| streetIds | String[] | 否 | 街道 id 列表 |
| excludeStreetIds | String[] | 否 | 排除街道 id 列表 |
| districtId | String | 否 | 区县 id |
| districtIds | String[] | 否 | 区县 id 列表 |
| excludeDistrictIds | String[] | 否 | 排除区县 id 列表 |
| cityId | Integer | 否 | 市 id |

### 4.3 问题类型 / 来源过滤参数

| 参数名 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| eventSrcId | String | 否 | 案件来源 id |
| eventSrcIds | String[] | 否 | 案件来源 id 列表 |
| excludeEventSrcIds | String[] | 否 | 排除案件来源 id 列表 |
| eventTypeId | String | 否 | 问题类型 id |
| notEventTypeId | String | 否 | 排除指定问题类型 |
| eventTypeIds | String[] | 否 | 问题类型 id 列表 |
| excludeEventTypeIds | String[] | 否 | 排除问题类型 id 列表 |
| mainTypeId | String | 否 | 问题大类 id |
| mainTypeIds | String[] | 否 | 问题大类 id 列表 |
| excludeMainTypeIds | String[] | 否 | 排除问题大类 id 列表 |
| subTypeId | String | 否 | 问题小类 id |
| subTypeIds | String[] | 否 | 问题小类 id 列表 |
| excludeSubTypeIds | String[] | 否 | 排除问题小类 id 列表 |
| recTypeId | Integer | 否 | 案件类型 id |
| recTypeIds | String[] | 否 | 多个案件类型 id |

### 4.4 指标状态过滤参数

传 `1` 表示按对应指标过滤。

| 参数名 | 类型 | 参数说明 |
|---|---|---|
| reportNum | Integer | 查询已上报案件 |
| disposeNum | Integer | 查询已处置案件 |
| toDisposeNum | Integer | 查询未处置案件 |
| operateNum | Integer | 查询已受理案件 |
| instNum | Integer | 查询已立案案件 |
| overtimeArchiveNum | Integer | 查询超期结案案件 |
| overtimeToDisposeNum | Integer | 查询超期未处置案件 |
| dispatchNum | Integer | 查询已派遣案件 |
| archiveNum | Integer | 查询已结案案件 |
| needArchiveNum | Integer | 查询应结案案件 |
| intimeArchiveNum | Integer | 查询按期结案案件 |
| intimeDisposeNum | Integer | 查询按期处置案件 |
| accurDispatchNum | Integer | 查询准确派遣案件 |
| overtimeDisposeNum | Integer | 查询超期处置案件 |
| intimeInstNum | Integer | 查询按时立案案件 |
| patrolDealFlag | Integer | 查询自行处置案件 |
| intimeCheckNum | Integer | 查询按期核查案件 |
| intimeDispatchNum | Integer | 查询按期派遣案件 |
| intimeOperateNum | Integer | 查询按时受理案件 |
| reworkNum | Integer | 查询返工案件 |

### 4.5 人员 / 部门过滤参数

| 参数名 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| reportPatrolId | String | 否 | 指定监督员上报的案件 |
| disposeUnitId | String | 否 | 指定部门处置的案件 |
| instHumanId | Integer | 否 | 指定人员立案的案件 |
| archiveHumanId | String | 否 | 指定人员结案的案件 |
| operateHumanId | Integer | 否 | 指定人员受理的案件 |
| checkPatrolId | String | 否 | 指定人员核查的案件 |
| dispatchHumanId | String | 否 | 指定派遣人员的案件 |

### 4.6 案件阶段参数

| 参数名 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| eventStateId | Integer | 否 | 指定案件阶段 |
| excludeEventStateId | Integer | 否 | 排除指定案件阶段 |

#### eventStateId 说明

| 值 | 含义 |
|---|---|
| 1 | 待受理 |
| 3 | 立案派遣 |
| 4 | 处理中 |
| 5 | 核查结案 |
| 6 | 结案 |
| 7 | 作废 |
| 8 | 挂账 |
| 9 | 督查 |

### 4.7 searchKeyword

| 参数路径 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| searchKeyword.taskNum | String | 否 | 模糊查询任务号 |
| searchKeyword.eventDesc | String | 否 | 模糊查询案件描述 |
| searchKeyword.address | String | 否 | 模糊查询地址 |

---

## 5. 请求示例

```json
{
  "startCreateTime": "2022-01-01 00:00:00",
  "endCreateTime": "2022-01-31 23:59:59"
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 热力点数组 | 热力图数据源 |
| result[].latitude | latitude | Double | 是 | 纬度 | 可映射为 `lat` |
| result[].longitude | longitude | Double | 是 | 经度 | 可映射为 `lng` |
| result[].value | value | Double | 是 | 数量 | 可映射为 `value` |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 辅助统计 |

> 注意：原始文档中 `latitude` / `longitude` 的中文备注疑似写反。字段名应按英文含义使用：`latitude=纬度`，`longitude=经度`。

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "latitude": 27.96,
      "value": 1,
      "longitude": 120.61
    },
    {
      "latitude": 119.7,
      "value": 13,
      "longitude": 27.54
    },
    {
      "latitude": 119.7,
      "value": 89,
      "longitude": 27.55
    }
  ],
  "message": null,
  "tag": null,
  "totalCount": 3
}
```

---

## 8. 报错说明

| message | 说明 | 处理建议 |
|---|---|---|
| 其他报错 | 需联系后台排查数据 | 查看后台日志、检查时间范围和筛选条件 |

---

## 9. 适配建议

### 适合组件

- 热力图；
- 地图热力层；
- 案件分布热力图。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| lng | item.longitude | Number 转换 |
| lat | item.latitude | Number 转换 |
| value | item.value | Number 转换 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            lng: Number(item.longitude || 0),
            lat: Number(item.latitude || 0),
            value: Number(item.value || 0)
        };
    }).filter(function (item) {
        return item.lng !== 0 && item.lat !== 0;
    });
}
```

### 兼容完整响应包的过滤脚本

```javascript
function filter(data) {
    if (!data || data.hasError === true) {
        return [];
    }

    var list = data.result;
    if (!Array.isArray(list)) {
        return [];
    }

    return list.map(function (item) {
        return {
            lng: Number(item.longitude || 0),
            lat: Number(item.latitude || 0),
            value: Number(item.value || 0)
        };
    }).filter(function (item) {
        return item.lng !== 0 && item.lat !== 0;
    });
}
```

---

## 10. 性能和联调注意点

1. 时间跨度较大时查询效率会降低。
2. 建议查询时间跨度小于一个月。
3. 热力图只返回经纬度和数量，不返回案件详情。
4. 如果需要点位弹窗或案件详情，应使用案件简要列表或案件详情接口。
5. 原始示例中存在异常经纬度值，联调时建议确认坐标范围和坐标系。
6. `point` 可以控制经纬度保留的小数位数，会影响聚合精度和热力点数量。