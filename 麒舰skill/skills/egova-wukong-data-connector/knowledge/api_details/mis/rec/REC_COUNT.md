# 案件数量统计

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_COUNT |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 案件数量统计 |
| apiType | count |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/count` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/案件数量统计` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | number |
| 适配组件 | 指标卡、总数卡片、分页总数辅助 |

---

## 2. 接口说明

该接口用于查询案件数量。

查询逻辑与分页接口和列表查询相同，主要用于：

- 悟空分页组件获取条件查询后的数据总数；
- 指标卡展示案件总数；
- 根据筛选条件统计案件数量。

该接口与分页接口配套使用时，请求参数需要与分页接口请求体中的 `condition` 字段保持一致。

适合：

- 指标卡；
- 总数卡片；
- 分页组件总数辅助。

不适合：

- 案件明细列表；
- 地图点位展示；
- 分类统计图；
- 案件详情。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdbstat | to_stat_info | 统计库案件表 |

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
  "districtId": "14"
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Integer | 是 | 案件数量 | 可映射为指标卡 `value` |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 通常为 1 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": 7422,
  "message": null,
  "tag": null,
  "totalCount": 1
}
```

---

## 8. 报错说明

| message | 说明 | 处理建议 |
|---|---|---|
| 其他报错 | 需联系后台排查数据 | 查看后台日志、检查筛选参数 |

---

## 9. 适配建议

### 适合组件

- 指标卡；
- 总数卡片；
- 分页组件总数辅助。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| title | 固定值 | 例如“案件总数” |
| value | data | Number 转换 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    return {
        title: '案件总数',
        value: Number(data || 0)
    };
}
```

### 兼容完整响应包的过滤脚本

```javascript
function filter(data) {
    if (!data || data.hasError === true) {
        return {
            title: '案件总数',
            value: 0
        };
    }

    return {
        title: '案件总数',
        value: Number(data.result || 0)
    };
}
```

---

## 10. 性能和联调注意点

1. 该接口只返回数量，不返回案件明细。
2. 与分页接口配套时，参数必须和分页接口的 `condition` 保持一致。
3. 如果用于指标卡，标题通常由组件静态结构或 filter 固定输出。
4. 如果需要分类统计，应使用案件指标统计相关 group 接口。