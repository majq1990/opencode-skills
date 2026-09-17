# 案件分页查询

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_PAGE |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 案件分页查询 |
| apiType | page |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/page` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/案件分页查询` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 分页表格、案件列表、案件管理表格 |

---

## 2. 接口说明

该接口用于案件分页查询。

查询逻辑与案件列表接口基本一致，区别是：

- 请求体包含 `condition` 查询条件；
- 请求体包含 `paging` 分页参数；
- 返回当前页案件数据；
- `totalCount` 返回总条数，可用于分页组件。

接口支持多种筛选条件：

- 时间范围；
- 区划；
- 问题类型；
- 问题来源；
- 上报人；
- 处置部门；
- 结案人；
- 案件状态；
- 关键字模糊查询等。

适合：

- 分页表格；
- 案件管理列表；
- 数据量较大的案件列表展示。

不适合：

- 地图图层点位；
- 热力图；
- 指标统计图；
- 单个案件详情。

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

### 4.1 顶层参数

| 参数路径 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| condition | Object | 是 | 无 | 查询条件 |
| paging | Object | 是 | 无 | 分页参数 |
| paging.pageIndex | Long | 是 | 无 | 第几页 |
| paging.pageSize | Long | 是 | 无 | 每页多少条数据 |
| sorts | Object[] | 否 | 无 | 排序规则 |
| sorts[].mode | String | 否 | 无 | 排序规则：`Ascending` 升序，`Descending` 降序 |
| sorts[].fields | String[] | 否 | 无 | 排序字段 |

### 4.2 condition 基础参数

| 参数路径 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| condition.ids | String[] | 否 | 无 | 查询案件主键在 ids 列表中的案件信息 |
| condition.startCreateTime | String | 否 | 当前时间减去 30 天的当天 0 时 0 分 0 秒 | 创建开始时间，格式 `yyyy-MM-dd HH:mm:ss` |
| condition.endCreateTime | String | 否 | 当天 23 时 59 分 59 秒 | 创建结束时间，格式 `yyyy-MM-dd HH:mm:ss` |
| condition.taskNum | String | 否 | 无 | 查询指定任务号 |
| condition.taskNos | String[] | 否 | 无 | 查询任务号在 taskNos 列表中的案件 |
| condition.bizId | Integer | 否 | 无 | 案件业务标识 |

### 4.3 condition 区划参数

| 参数路径 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| condition.dutyGridId | String | 否 | 责任网格 id |
| condition.dutyGridIds | String[] | 否 | 责任网格 id 列表 |
| condition.excludeDutyGridIds | String[] | 否 | 排除责任网格 id 列表 |
| condition.cellId | String | 否 | 单元网格 id |
| condition.cellIds | String[] | 否 | 单元网格 id 列表 |
| condition.excludeCellIds | String[] | 否 | 排除单元网格 id 列表 |
| condition.communityId | String | 否 | 社区 id |
| condition.communityIds | String[] | 否 | 社区 id 列表 |
| condition.excludeCommunityIds | String[] | 否 | 排除社区 id 列表 |
| condition.streetId | String | 否 | 街道 id |
| condition.streetIds | String[] | 否 | 街道 id 列表 |
| condition.excludeStreetIds | String[] | 否 | 排除街道 id 列表 |
| condition.districtId | String | 否 | 区县 id |
| condition.districtIds | String[] | 否 | 区县 id 列表 |
| condition.excludeDistrictIds | String[] | 否 | 排除区县 id 列表 |
| condition.cityId | Integer | 否 | 市 id |

### 4.4 condition 问题类型 / 来源参数

| 参数路径 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| condition.eventSrcId | String | 否 | 案件来源 id |
| condition.eventSrcIds | String[] | 否 | 案件来源 id 列表 |
| condition.excludeEventSrcIds | String[] | 否 | 排除案件来源 id 列表 |
| condition.eventTypeId | String | 否 | 问题类型 id |
| condition.notEventTypeId | String | 否 | 排除指定问题类型 |
| condition.eventTypeIds | String[] | 否 | 问题类型 id 列表 |
| condition.excludeEventTypeIds | String[] | 否 | 排除问题类型 id 列表 |
| condition.mainTypeId | String | 否 | 问题大类 id |
| condition.mainTypeIds | String[] | 否 | 问题大类 id 列表 |
| condition.excludeMainTypeIds | String[] | 否 | 排除问题大类 id 列表 |
| condition.subTypeId | String | 否 | 问题小类 id |
| condition.subTypeIds | String[] | 否 | 问题小类 id 列表 |
| condition.excludeSubTypeIds | String[] | 否 | 排除问题小类 id 列表 |
| condition.recTypeId | Integer | 否 | 案件类型 id |
| condition.recTypeIds | String[] | 否 | 多个案件类型 id |

### 4.5 condition 指标状态参数

传 `1` 表示按对应指标过滤。

| 参数路径 | 类型 | 参数说明 |
|---|---|---|
| condition.reportNum | Integer | 查询已上报案件 |
| condition.disposeNum | Integer | 查询已处置案件 |
| condition.toDisposeNum | Integer | 查询未处置案件 |
| condition.operateNum | Integer | 查询已受理案件 |
| condition.instNum | Integer | 查询已立案案件 |
| condition.overtimeArchiveNum | Integer | 查询超期结案案件 |
| condition.overtimeToDisposeNum | Integer | 查询超期未处置案件 |
| condition.dispatchNum | Integer | 查询已派遣案件 |
| condition.archiveNum | Integer | 查询已结案案件 |
| condition.needArchiveNum | Integer | 查询应结案案件 |
| condition.intimeArchiveNum | Integer | 查询按期结案案件 |
| condition.intimeDisposeNum | Integer | 查询按期处置案件 |
| condition.accurDispatchNum | Integer | 查询准确派遣案件 |
| condition.overtimeDisposeNum | Integer | 查询超期处置案件 |
| condition.intimeInstNum | Integer | 查询按时立案案件 |
| condition.patrolDealReportNum | Integer | 查询自行处置案件 |
| condition.intimeCheckNum | Integer | 查询按期核查案件 |
| condition.intimeDispatchNum | Integer | 查询按期派遣案件 |
| condition.intimeOperateNum | Integer | 查询按时受理案件 |
| condition.reworkNum | Integer | 查询返工案件 |

### 4.6 condition 人员 / 部门参数

| 参数路径 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| condition.reportPatrolId | String | 否 | 查询指定监督员上报的案件 |
| condition.disposeUnitId | String | 否 | 查询指定部门处置的案件 |
| condition.instHumanId | Integer | 否 | 查询指定人员立案的案件 |
| condition.archiveHumanId | String | 否 | 查询指定人员结案的案件 |
| condition.operateHumanId | Integer | 否 | 查询指定人员受理的案件 |
| condition.checkPatrolId | String | 否 | 查询指定人员核查的案件 |
| condition.dispatchHumanId | String | 否 | 查询指定派遣人员的案件 |

### 4.7 condition 案件阶段参数

| 参数路径 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| condition.eventStateId | Integer | 否 | 查询指定案件阶段 |
| condition.excludeEventStateId | Integer | 否 | 查询不在指定案件阶段的案件 |

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

### 4.8 condition.searchKeyword

| 参数路径 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| condition.searchKeyword.taskNum | String | 否 | 模糊查询任务号 |
| condition.searchKeyword.eventDesc | String | 否 | 模糊查询案件描述 |
| condition.searchKeyword.address | String | 否 | 模糊查询地址 |

---

## 5. 请求示例

```json
{
  "condition": {
    "startCreateTime": "2022-01-01 00:00:00",
    "endCreateTime": "2022-06-31 23:59:59",
    "eventSrcId": "1",
    "districtId": "14"
  },
  "paging": {
    "pageIndex": 1,
    "pageSize": 10
  }
}
```

---

## 6. 返回字段

### 6.1 顶层字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 当前页案件列表 | 分页表格 list |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 总条数 | 分页表格 total |

### 6.2 result[] 常用字段

| 字段路径 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|
| result[].id | String | 是 | 主键 | id |
| result[].address | String | 是 | 案发地址 | 表格列 |
| result[].taskNum | String | 是 | 任务号 | 表格列/标题 |
| result[].archiveTime | String | 是 | 结案时间 | 表格列 |
| result[].bizId | Integer | 是 | 业务标识 | 隐藏字段/联动字段 |
| result[].dutyGridName | String | 是 | 责任网格 | 表格列 |
| result[].cellName | String | 是 | 单元网格 | 表格列 |
| result[].communityName | String | 是 | 社区 | 表格列 |
| result[].streetName | String | 是 | 街道 | 表格列 |
| result[].districtName | String | 是 | 区县 | 表格列 |
| result[].longitude | Double | 是 | 经度 | 地图扩展 |
| result[].latitude | Double | 是 | 纬度 | 地图扩展 |
| result[].createTime | String | 是 | 上报时间 | 表格列 |
| result[].eventDesc | String | 是 | 案件描述 | 表格列 |
| result[].eventSrcName | String | 是 | 案件来源 | 表格列 |
| result[].eventTypeName | String | 是 | 问题类型 | 表格列 |
| result[].mainTypeName | String | 是 | 问题大类 | 表格列 |
| result[].subTypeName | String | 是 | 问题小类 | 表格列 |
| result[].recTypeName | String | 是 | 案件类型 | 表格列 |
| result[].eventStateName | String | 是 | 案件阶段 | 表格列 |
| result[].disposeUnitName | String | 否 | 处置部门 | 表格列 |
| result[].reportPatrolName | String | 否 | 上报人员 | 表格列 |
| result[].attachments | Object[] | 否 | 附件 | 图片展示 |

---

## 7. 返回示例

原始文档字段较多，以下为分页表格常用结构示例：

```json
{
  "hasError": false,
  "result": [
    {
      "id": "1803060",
      "address": "瑞祥路11号的东北方向13.76米",
      "taskNum": "22041800001",
      "archiveTime": "2022-04-18 15:10:00",
      "bizId": 1,
      "dutyGridName": "网格一",
      "cellName": "单元网格一",
      "communityName": "社区一",
      "streetName": "街道一",
      "districtName": "区县一",
      "longitude": 120.955465,
      "latitude": 28.116796,
      "createTime": "2022-04-18 13:01:55",
      "eventDesc": "存在垃圾未入桶的现象。",
      "eventSrcName": "监督员上报",
      "eventTypeName": "事件",
      "mainTypeName": "市容环境",
      "subTypeName": "暴露垃圾",
      "recTypeName": "事件",
      "eventStateName": "结案"
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
| 其他报错 | 需联系后台排查数据 | 查看后台日志、检查分页参数和筛选条件 |

---

## 9. 适配建议

### 适合组件

- 分页表格；
- 案件列表；
- 案件管理表格；
- 可点击详情的案件表格。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| list | data.result | 数组兜底 |
| total | data.totalCount | Number 转换 |
| id | item.id | 字符串兜底 |
| taskNum | item.taskNum | 字符串兜底 |
| address | item.address | 字符串兜底 |
| eventDesc | item.eventDesc | 字符串兜底 |
| eventTypeName | item.eventTypeName | 字符串兜底 |
| eventStateName | item.eventStateName | 字符串兜底 |
| createTime | item.createTime | 字符串兜底 |

### 推荐过滤脚本：data 为完整响应包

分页表格需要 `totalCount`，因此建议悟空传入完整响应包。

```javascript
function filter(data) {
    if (!data || data.hasError === true) {
        return {
            list: [],
            total: 0
        };
    }

    var list = Array.isArray(data.result) ? data.result : [];

    return {
        list: list.map(function (item) {
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
                streetName: item.streetName || ''
            };
        }),
        total: Number(data.totalCount || 0)
    };
}
```

---

## 10. 性能和联调注意点

1. 分页接口必须传 `condition` 和 `paging`。
2. `paging.pageIndex`、`paging.pageSize` 是必填。
3. 分页表格如果只传 `result` 本体，将无法拿到 `totalCount`。
4. 如与案件数量统计接口配套，`condition` 应保持一致。
5. 如果开启附件查询，可能影响性能。
6. 大数据量表格建议使用分页接口，不建议使用案件列表接口。