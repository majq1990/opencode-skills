# 案件简要列表

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_LAYER_LIST |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 案件简要列表 |
| apiType | layer_list |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/layer/list` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/案件简要列表` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 地图图层、地图点位、案件弹窗、轻量案件列表 |

---

## 2. 接口说明

该接口主要用于展示案件图层。

接口默认查询案件主键及经纬度信息，并可通过配置项和传参方式查询额外字段，用于点击地图图层上的某个案件后弹出案件信息。

当前默认查询字段包括：

- 主键；
- 任务号；
- 经度；
- 纬度；
- 地点；
- 案件描述；
- 问题类型；
- 问题大类；
- 问题小类；
- 案件阶段。

接口支持多种条件筛选：

- 区划条件：责任网格、单元网格、社区、街镇、区县、市；
- 问题类型：问题类型、大类、小类；
- 问题来源；
- 上报人；
- 处置部门；
- 结案人；
- 案件状态。

注意：

1. 默认字段支持修改；
2. 默认字段配置在 `wuneng.com_option` 表中，查找 `groupType=defaultFields`、`groupName=defaultFields` 的数据，修改 `value` 字段；
3. 默认字段必须保留主键和经纬度字段，否则会影响图层基础功能；
4. 该接口不支持查询附件，如需查看图片，应在详情中调用其他接口；
5. 大数据量查询性能较差，默认最多查询 30000 条；
6. 默认按照案件发生时间倒序排列。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdbstat | to_stat_info | 统计库案件表 |

---

## 4. 请求参数

### 4.1 动态字段参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| multiFields | Object[] | 否 | 无 | 配置除默认字段外还需要查询哪些字段及字段别名 |
| top | Integer | 否 | 30000 | 查询数据条数，不传默认 30000 |

`multiFields` 用法说明：

```json
{
  "multiFields": [
    {
      "event_state_name": "eventStateName"
    }
  ]
}
```

其中：

- key 为 `to_stat_info` 表字段名；
- value 为返回给前端的字段别名。

### 4.2 基础筛选参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| ids | String[] | 否 | 无 | 查询案件主键在 ids 列表中的案件信息 |
| startCreateTime | String | 否 | 当前时间减去 30 天的当天 0 时 0 分 0 秒 | 创建开始时间，格式 `yyyy-MM-dd HH:mm:ss` |
| endCreateTime | String | 否 | 当天 23 时 59 分 59 秒 | 创建结束时间，格式 `yyyy-MM-dd HH:mm:ss` |
| taskNum | String | 否 | 无 | 查询指定任务号 |
| taskNos | String[] | 否 | 无 | 查询任务号在 taskNos 列表中的案件 |
| bizId | Integer | 否 | 无 | 案件业务标识 |

### 4.3 区划筛选参数

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

### 4.4 问题类型 / 来源筛选参数

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

### 4.5 指标状态筛选参数

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

### 4.6 人员 / 部门筛选参数

| 参数名 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| reportPatrolId | String | 否 | 查询指定监督员上报的案件 |
| disposeUnitId | String | 否 | 查询指定部门处置的案件 |
| instHumanId | Integer | 否 | 查询指定人员立案的案件 |
| archiveHumanId | String | 否 | 查询指定人员结案的案件 |
| operateHumanId | Integer | 否 | 查询指定人员受理的案件 |
| checkPatrolId | String | 否 | 查询指定人员核查的案件 |
| dispatchHumanId | String | 否 | 查询指定派遣人员的案件 |

### 4.7 案件阶段参数

| 参数名 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| eventStateId | Integer | 否 | 查询指定案件阶段 |
| excludeEventStateId | Integer | 否 | 查询不在指定案件阶段的案件 |

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

### 4.8 searchKeyword

| 参数路径 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| searchKeyword.taskNum | String | 否 | 模糊查询任务号 |
| searchKeyword.eventDesc | String | 否 | 模糊查询案件描述 |
| searchKeyword.address | String | 否 | 模糊查询地址 |

---

## 5. 请求示例

```json
{
  "multiFields": [
    {
      "event_state_name": "eventStateName"
    }
  ],
  "startCreateTime": "2022-01-01 00:00:00",
  "endCreateTime": "2022-01-31 23:59:59",
  "eventSrcId": "1",
  "districtId": "14",
  "archiveNum": 1
}
```

---

## 6. 返回字段

由于返回字段由默认字段配置和 `multiFields` 决定，因此 `result[]` 是动态对象。

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 案件图层数据 | 地图点位数据源 |
| result[].id | id | String / Integer | 是 | 案件主键 | 可映射为 `id` |
| result[].longitude | longitude | Double | 是 | 经度 | 可映射为 `lng` |
| result[].latitude | latitude | Double | 是 | 纬度 | 可映射为 `lat` |
| result[].taskNum | taskNum | String | 否 | 任务号 | 可映射为弹窗标题/编号 |
| result[].address | address | String | 否 | 案发地址 | 可用于弹窗 |
| result[].eventDesc | eventDesc | String | 否 | 案件描述 | 可用于弹窗 |
| result[].eventTypeName | eventTypeName | String | 否 | 问题类型 | 可用于弹窗 |
| result[].mainTypeName | mainTypeName | String | 否 | 问题大类 | 可用于弹窗 |
| result[].subTypeName | subTypeName | String | 否 | 问题小类 | 可用于弹窗 |
| result[].eventStateName | eventStateName | String | 否 | 案件阶段 | 可用于弹窗 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 可辅助统计 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "eventStateName": "结案",
      "subTypeName": "暴露垃圾",
      "eventDesc": "乐成街道兴业路核桃树音乐门前，存在垃圾未入桶的现象。",
      "address": "瑞祥路11号的东北方向13.76米",
      "mainTypeName": "市容环境",
      "latitude": 28.116796,
      "eventTypeName": "事件",
      "id": 1306523,
      "taskNum": "22012901750",
      "longitude": 120.955465
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
| 默认字段为空，查不了 | `com_option` 表未配置默认字段 | 检查 `wuneng.com_option` 的 defaultFields 配置 |
| 其他报错 | 需联系后台排查数据 | 查看后台日志、检查筛选参数 |

---

## 9. 适配建议

### 适合组件

- 地图点位；
- 案件图层；
- 地图弹窗；
- 轻量案件列表。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.id | 字符串兜底 |
| name | item.taskNum | 字符串兜底 |
| taskNum | item.taskNum | 字符串兜底 |
| desc | item.eventDesc | 字符串兜底 |
| address | item.address | 字符串兜底 |
| eventTypeName | item.eventTypeName | 字符串兜底 |
| mainTypeName | item.mainTypeName | 字符串兜底 |
| subTypeName | item.subTypeName | 字符串兜底 |
| eventStateName | item.eventStateName | 字符串兜底 |
| lng | item.longitude | Number 转换 |
| lat | item.latitude | Number 转换 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            id: item.id || '',
            name: item.taskNum || '',
            taskNum: item.taskNum || '',
            desc: item.eventDesc || '',
            address: item.address || '',
            eventTypeName: item.eventTypeName || '',
            mainTypeName: item.mainTypeName || '',
            subTypeName: item.subTypeName || '',
            eventStateName: item.eventStateName || '',
            lng: Number(item.longitude || 0),
            lat: Number(item.latitude || 0)
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
            id: item.id || '',
            name: item.taskNum || '',
            taskNum: item.taskNum || '',
            desc: item.eventDesc || '',
            address: item.address || '',
            eventTypeName: item.eventTypeName || '',
            mainTypeName: item.mainTypeName || '',
            subTypeName: item.subTypeName || '',
            eventStateName: item.eventStateName || '',
            lng: Number(item.longitude || 0),
            lat: Number(item.latitude || 0)
        };
    }).filter(function (item) {
        return item.lng !== 0 && item.lat !== 0;
    });
}
```

---

## 10. 性能和联调注意点

1. 默认最多返回 30000 条，数据量过大时地图加载和网络传输都会慢。
2. 如需更多或更少数据，可通过 `top` 控制。
3. 不支持查询附件；需要图片时应调用案件详情接口或其他附件接口。
4. 默认字段配置必须保留 `id`、`longitude`、`latitude`。
5. 如需弹窗展示更多字段，可通过 `multiFields` 增加字段。
6. 返回字段具有动态性，字段映射应以实际返回为准。