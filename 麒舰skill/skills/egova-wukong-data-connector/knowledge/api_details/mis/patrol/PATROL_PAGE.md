# 人员分页查询

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | PATROL_PAGE |
| domain | MIS人员 |
| bizObject | 监督员 |
| apiName | 人员分页查询 |
| apiType | page |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/patrol/page` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/人员分页查询` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 分页表格、人员列表、人员管理表格 |

---

## 2. 接口说明

该接口查询逻辑与人员列表查询相同，区别是该接口会根据请求中的分页参数返回指定页的数据。

基础查询会返回：

- 人员名称；
- 人员卡号；
- 人员编码；
- 人员类型；
- 人员区划；
- 人员点位；
- 人员基础信息；
- 在线状态；
- 经纬度。

通过传参可配置是否返回：

- 上级区划；
- 上级部门；
- 责任网格；
- 人员头像。

支持通过以下条件筛选：

- 人员名称；
- 人员类型；
- 在线/离线；
- 区划；
- 部门。

适合：

- 分页表格；
- 人员管理列表；
- 大数据量人员列表展示。

不适合：

- 地图高频点位；
- 人员数量指标卡；
- 单个人员详情弹窗。

> 注意：扩展查询开关比较耗性能，确实需要时再开启。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_patrol | 业务库监督员表 |
| cgdb | tc_human | 业务库人员表 |
| cgdb | tc_patrol_type | 业务库监督员类型字典表 |
| cgdb | tc_region | 业务库区划表 |
| cgdb | tc_patrol_state | 业务库监督员状态表 |
| cgdb | tc_duty_grid_patrol | 业务库责任网格-人员中间表 |
| cgdb | tc_duty_grid | 业务库责任网格表 |
| cgdb | tc_unit | 业务库部门表 |

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
| sorts[].mode | String | 否 | 无 | 排序规则，`Ascending` 升序，`Descending` 降序 |
| sorts[].fields | String[] | 否 | 无 | 排序字段 |

### 4.2 condition 查询条件

| 参数路径 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| condition.id | String | 否 | 无 | 人员主键 |
| condition.ids | String[] | 否 | 无 | 人员主键列表 |
| condition.cardId | String | 否 | 无 | 卡号 |
| condition.patrolCode | String | 否 | 无 | 人员编码 |
| condition.patrolName | String | 否 | 无 | 模糊查询人员名称 |
| condition.patrolTypeId | String | 否 | 无 | 人员类型 |
| condition.regionId | String | 否 | 无 | 指定所属区划 |
| condition.regionExtendFlag | Boolean | 否 | false | 是否支持区划下钻 |
| condition.regionIdList | String[] | 否 | 无 | 指定所属区划列表 |
| condition.unitId | String | 否 | 无 | 指定所属部门 |
| condition.unitExtendFlag | Boolean | 否 | 无 | 是否支持部门下钻 |
| condition.state | Boolean | 否 | 无 | 是否在线 |
| condition.regionHigherFlag | Boolean | 否 | false | 是否展示上级区划 |
| condition.unitHigherFlag | Boolean | 否 | false | 是否展示上级部门 |
| condition.dutyCellFlag | Boolean | 否 | false | 是否统计责任网格 |
| condition.attachmentFlag | Boolean | 否 | false | 是否查询人员头像 |

---

## 5. 请求示例

```json
{
  "condition": {
    "regionId": "0"
  },
  "paging": {
    "pageIndex": 1,
    "pageSize": 10
  }
}
```

---

## 6. 返回字段

返回字段与人员列表查询基本一致，额外重点关注 `totalCount`。

### 6.1 顶层字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 当前页人员列表 | 分页表格 list |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 分页表格 total |

### 6.2 result[] 常用字段

| 字段路径 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|
| result[].id | String | 是 | 人员 id | id |
| result[].cardId | String | 是 | 人员卡号 | 表格列 |
| result[].patrolCode | String | 是 | 人员编码 | 表格列 |
| result[].patrolName | String | 是 | 人员名称 | 表格列/标题 |
| result[].patrolTypeId | String | 是 | 人员类型 id | 类型筛选 |
| result[].regionId | String | 是 | 人员区域 id | 区域筛选 |
| result[].longitude | Double | 是 | 人员经度 | 地图扩展 |
| result[].latitude | Double | 是 | 人员纬度 | 地图扩展 |
| result[].unitId | String | 是 | 人员部门 id | 部门筛选 |
| result[].patrolType.displayName | String | 是 | 人员类型名称 | 表格列 |
| result[].region.regionName | String | 是 | 区划名称 | 表格列 |
| result[].patrolState.patrolStateId | Integer | 是 | 人员是否在线，1 在线 | 状态展示 |
| result[].human.telMobile | String | 是 | 手机号码 | 表格列 |
| result[].human.unitName | String | 是 | 所属部门 | 表格列 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "id": "100433",
      "cardId": "100433",
      "patrolCode": "",
      "patrolName": "egova",
      "patrolTypeId": "8",
      "regionId": "0",
      "patrolType": {
        "id": "8",
        "displayName": "管理干部",
        "displayOrder": "8"
      },
      "region": {
        "id": "0",
        "regionName": "温州市",
        "regionType": 1,
        "parentId": "-1"
      },
      "patrolState": {
        "id": "100433",
        "x": 120.69843166666666,
        "y": 27.999376666666663,
        "updateTime": "2022-04-18 14:24:46",
        "patrolStateId": 1
      },
      "human": {
        "id": "100433",
        "humanCode": "100433",
        "humanName": "egova",
        "telMobile": "15167863112",
        "unitId": "1",
        "unitName": "网格化城市管理"
      },
      "longitude": 120.69843166666666,
      "latitude": 27.999376666666663,
      "unitId": "1"
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
| 其他报错 | 需联系后台排查数据 | 检查请求参数、分页参数、数据权限、后台日志 |

---

## 9. 适配建议

### 适合组件

- 分页表格；
- 人员管理列表；
- 大数据量人员列表；
- 支持翻页的人员清单。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| list | data.result | 数组兜底 |
| total | data.totalCount | Number 转换 |
| id | item.id | 字符串兜底 |
| name | item.patrolName | 字符串兜底 |
| patrolTypeName | item.patrolType.displayName | 对象判空 |
| regionName | item.region.regionName | 对象判空 |
| unitName | item.human.unitName | 对象判空 |
| onlineStatus | item.patrolState.patrolStateId | 1 转在线，否则离线 |

### 推荐过滤脚本：data 为完整响应包

分页表格通常需要 `list + total`，因此建议让悟空传入完整响应包。

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
            var stateId = item.patrolState ? item.patrolState.patrolStateId : 0;

            return {
                id: item.id || '',
                name: item.patrolName || '',
                cardId: item.cardId || '',
                patrolCode: item.patrolCode || '',
                patrolTypeName: item.patrolType && item.patrolType.displayName || '',
                regionName: item.region && item.region.regionName || '',
                unitName: item.human && item.human.unitName || '',
                mobile: item.human && item.human.telMobile || '',
                onlineStatus: stateId === 1 ? '在线' : '离线',
                longitude: Number(item.longitude || 0),
                latitude: Number(item.latitude || 0)
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
3. 如果与人员总数接口配套，`condition` 应保持一致。
4. 不需要上级区划、上级部门、责任网格、头像时，不要开启对应 flag。
5. 分页表格如果只传入 `result` 本体，将无法拿到 `totalCount`。