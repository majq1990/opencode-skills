# 案件列表

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_LIST |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 案件列表 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/list` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/案件列表` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 表格、案件列表、案件明细列表、详情入口 |

---

## 2. 接口说明

该接口用于按查询条件查询案件列表。

接口默认查询 `to_stat_info` 表中的所有字段，适合需要展示较完整案件字段的列表场景。

支持多种筛选条件：

- 时间范围；
- 案件主键；
- 任务号；
- 区划；
- 问题来源；
- 问题类型；
- 案件类型；
- 案件阶段；
- 上报人；
- 处置部门；
- 结案人；
- 关键字模糊查询。

该接口可配置是否查询附件。

注意：

1. 该接口不是分页接口；
2. 推荐查询 100 条以内的数据；
3. 大数据量列表建议使用 `REC_PAGE.md` 对应的案件分页查询接口；
4. 地图图层场景建议使用 `REC_LAYER_LIST.md`；
5. 详情弹窗建议使用 `REC_INFO.md`。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdbstat | to_stat_info | 统计库案件表 |
| cgdbstat | to_media | 统计库附件表 |
| cgdb | to_media | 业务库附件表 |
| cgdb | to_his_media | 业务库历史附件表 |

---

## 4. 请求参数

### 4.1 基础筛选参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| ids | String[] | 否 | 无 | 查询案件主键在 ids 列表中的案件信息 |
| startCreateTime | String | 否 | 当前时间减去 30 天的当天 0 时 0 分 0 秒 | 创建开始时间，格式 `yyyy-MM-dd HH:mm:ss` |
| endCreateTime | String | 否 | 当天 23 时 59 分 59 秒 | 创建结束时间，格式 `yyyy-MM-dd HH:mm:ss` |
| taskNum | String | 否 | 无 | 查询指定任务号 |
| taskNos | String[] | 否 | 无 | 查询任务号在 taskNos 列表中的案件 |
| bizId | Integer | 否 | 无 | 案件业务标识 |
| mediaFlag | Boolean | 否 | false | 是否查询附件 |

### 4.2 区划筛选参数

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

### 4.3 问题类型 / 来源筛选参数

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

### 4.4 指标状态筛选参数

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

### 4.5 人员 / 部门筛选参数

| 参数名 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| reportPatrolId | String | 否 | 查询指定监督员上报的案件 |
| disposeUnitId | String | 否 | 查询指定部门处置的案件 |
| instHumanId | Integer | 否 | 查询指定人员立案的案件 |
| archiveHumanId | String | 否 | 查询指定人员结案的案件 |
| operateHumanId | Integer | 否 | 查询指定人员受理的案件 |
| checkPatrolId | String | 否 | 查询指定人员核查的案件 |
| dispatchHumanId | String | 否 | 查询指定派遣人员的案件 |

### 4.6 案件阶段参数

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
  "endCreateTime": "2022-06-31 23:59:59",
  "eventSrcId": "1",
  "districtId": "14",
  "archiveNum": 1,
  "mediaFlag": false
}
```

---

## 6. 返回字段

### 6.1 顶层字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 案件列表 | 表格数据源 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 可辅助统计 |

### 6.2 result[] 常用字段

| 字段路径 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|
| result[].id | String | 是 | 主键 | id |
| result[].taskNum | String | 是 | 任务号 | 表格列/标题 |
| result[].address | String | 是 | 案发地址 | 表格列 |
| result[].eventDesc | String | 是 | 案件描述 | 表格列 |
| result[].longitude | Double | 是 | 经度 | 地图扩展 |
| result[].latitude | Double | 是 | 纬度 | 地图扩展 |
| result[].createTime | String | 是 | 上报/创建时间 | 表格列 |
| result[].archiveTime | String | 否 | 结案时间 | 表格列 |
| result[].eventSrcName | String | 否 | 案件来源名称 | 表格列 |
| result[].eventTypeName | String | 否 | 问题类型名称 | 表格列 |
| result[].mainTypeName | String | 否 | 问题大类名称 | 表格列 |
| result[].subTypeName | String | 否 | 问题小类名称 | 表格列 |
| result[].recTypeName | String | 否 | 案件类型名称 | 表格列 |
| result[].eventStateName | String | 否 | 案件阶段名称 | 表格列 |
| result[].dutyGridName | String | 否 | 责任网格名称 | 表格列 |
| result[].cellName | String | 否 | 单元网格名称 | 表格列 |
| result[].communityName | String | 否 | 社区名称 | 表格列 |
| result[].streetName | String | 否 | 街道名称 | 表格列 |
| result[].districtName | String | 否 | 区县名称 | 表格列 |
| result[].disposeUnitName | String | 否 | 处置部门名称 | 表格列 |
| result[].reportPatrolName | String | 否 | 上报人员名称 | 表格列 |
| result[].attachments | Object[] | 否 | 附件列表 | 图片/附件展示 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "id": "1803060",
      "taskNum": "22041800001",
      "address": "瑞祥路11号的东北方向13.76米",
      "eventDesc": "存在垃圾未入桶的现象。",
      "longitude": 120.955465,
      "latitude": 28.116796,
      "createTime": "2022-04-18 13:01:55",
      "archiveTime": "2022-04-18 15:10:00",
      "eventSrcName": "监督员上报",
      "eventTypeName": "事件",
      "mainTypeName": "市容环境",
      "subTypeName": "暴露垃圾",
      "recTypeName": "事件",
      "eventStateName": "结案",
      "districtName": "区县一",
      "streetName": "街道一"
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
| 其他报错 | 需联系后台排查数据 | 查看后台日志、检查筛选条件 |

---

## 9. 适配建议

### 适合组件

- 表格；
- 案件明细列表；
- 案件详情入口；
- 小数据量案件列表。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.id | 字符串兜底 |
| taskNum | item.taskNum | 字符串兜底 |
| address | item.address | 字符串兜底 |
| eventDesc | item.eventDesc | 字符串兜底 |
| eventSrcName | item.eventSrcName | 字符串兜底 |
| eventTypeName | item.eventTypeName | 字符串兜底 |
| eventStateName | item.eventStateName | 字符串兜底 |
| createTime | item.createTime | 字符串兜底 |
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
            taskNum: item.taskNum || '',
            address: item.address || '',
            eventDesc: item.eventDesc || '',
            eventSrcName: item.eventSrcName || '',
            eventTypeName: item.eventTypeName || '',
            mainTypeName: item.mainTypeName || '',
            subTypeName: item.subTypeName || '',
            eventStateName: item.eventStateName || '',
            createTime: item.createTime || '',
            archiveTime: item.archiveTime || '',
            districtName: item.districtName || '',
            streetName: item.streetName || '',
            lng: Number(item.longitude || 0),
            lat: Number(item.latitude || 0)
        };
    });
}
```

---

## 10. 性能和联调注意点

1. 该接口不是分页接口，建议查询 100 条以内数据。
2. 大数据量表格应使用 `REC_PAGE.md` 对应分页接口。
3. 地图图层应优先使用 `REC_LAYER_LIST.md`。
4. 是否返回附件由 `mediaFlag` 控制，开启附件可能影响性能。
5. 返回字段很多，表格组件只映射需要展示的字段即可。