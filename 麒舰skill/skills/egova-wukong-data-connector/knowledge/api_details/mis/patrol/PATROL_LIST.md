# 人员列表查询

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | PATROL_LIST |
| domain | MIS人员 |
| bizObject | 监督员 |
| apiName | 人员列表查询 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/patrol/list` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/人员列表查询` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 表格、人员列表、人员详情入口、人员完整列表 |

---

## 2. 接口说明

该接口用于按指定查询条件查询监督员列表。

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

- 人员主键；
- 人员主键列表；
- 卡号；
- 人员编码；
- 人员名称；
- 人员类型；
- 区划；
- 部门；
- 在线/离线状态。

支持区划深钻：

- 通过区划过滤时，如果人员属于该区划下属区划，也可以认为该人员属于当前区划；
- 由 `regionExtendFlag` 控制。

支持部门深钻：

- 通过部门过滤时，如果人员属于该部门下属部门，也可以认为该人员属于当前部门；
- 由 `unitExtendFlag` 控制。

适合：

- 条件筛选后的人员列表；
- 人员完整信息表格；
- 人员详情入口；
- 少量人员数据展示。

不适合：

- 无条件查询全量人员；
- 高频地图打点；
- 分页表格；
- 人员数量统计。

> 注意：上级部门、上级区划、责任网格、头像等扩展信息查询比较耗性能，确实需要时再开启。

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

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| id | String | 否 | 无 | 人员主键 |
| ids | String[] | 否 | 无 | 人员主键列表 |
| cardId | String | 否 | 无 | 卡号 |
| patrolCode | String | 否 | 无 | 人员编码 |
| patrolName | String | 否 | 无 | 模糊查询人员名称 |
| patrolTypeId | String | 否 | 无 | 人员类型 |
| regionId | String | 否 | 无 | 指定所属区划 |
| regionExtendFlag | Boolean | 否 | false | 是否支持区划下钻 |
| regionIdList | String[] | 否 | 无 | 指定所属区划列表 |
| unitId | String | 否 | 无 | 指定所属部门 |
| unitExtendFlag | Boolean | 否 | 无 | 是否支持部门下钻 |
| state | Boolean | 否 | 无 | 是否在线 |
| regionHigherFlag | Boolean | 否 | false | 是否展示上级区划 |
| unitHigherFlag | Boolean | 否 | false | 是否展示上级部门 |
| dutyCellFlag | Boolean | 否 | false | 是否统计责任网格 |
| attachmentFlag | Boolean | 否 | false | 是否查询人员头像 |
| top | Integer | 否 | 100 | 最大数据条数 |

---

## 5. 请求示例

```json
{
  "dutyCellFlag": true,
  "regionId": "0"
}
```

---

## 6. 返回字段

### 6.1 顶层字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 人员列表 | 表格/list 数据源 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 列表总数 |

### 6.2 人员主字段 result[]

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| result[].id | id | String | 是 | 人员 id | id |
| result[].cardId | cardId | String | 是 | 人员卡号 | 表格列 |
| result[].patrolCode | patrolCode | String | 是 | 人员编码 | 表格列 |
| result[].patrolName | patrolName | String | 是 | 人员名称 | 名称/标题 |
| result[].patrolTypeId | patrolTypeId | String | 是 | 人员类型 id | 类型筛选 |
| result[].regionId | regionId | String | 是 | 人员区域 id | 区划筛选 |
| result[].longitude | longitude | Double | 是 | 人员经度 | 地图 lng |
| result[].latitude | latitude | Double | 是 | 人员纬度 | 地图 lat |
| result[].unitId | unitId | String | 是 | 人员部门 id | 部门筛选 |

### 6.3 patrolType 人员类型

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result[].patrolType.id | String | 是 | 人员类型 id |
| result[].patrolType.displayName | String | 是 | 人员类型名称 |

### 6.4 region 人员区划

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result[].region.id | String | 是 | 区划主键 |
| result[].region.regionCode | String | 是 | 区划编码 |
| result[].region.longitude | Double | 是 | 区划经度 |
| result[].region.latitude | Double | 是 | 区划纬度 |
| result[].region.regionName | String | 是 | 区划名称 |
| result[].region.regionType | Integer | 是 | 区划类型 |
| result[].region.parentId | String | 是 | 父区划 id |

### 6.5 patrolState 人员点位状态

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result[].patrolState.id | String | 是 | 人员主键 |
| result[].patrolState.x | Double | 是 | 人员经度 |
| result[].patrolState.y | Double | 是 | 人员纬度 |
| result[].patrolState.updateTime | String | 是 | 更新时间 |
| result[].patrolState.patrolStateId | Integer | 是 | 人员是否在线，1 在线 |

### 6.6 human 人员信息

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result[].human.id | String | 是 | 人员 id |
| result[].human.address | String | 是 | 人员地址 |
| result[].human.birthday | String | 是 | 生日 |
| result[].human.humanCode | String | 是 | 人员编码 |
| result[].human.humanDesc | String | 是 | 人员描述 |
| result[].human.humanName | String | 是 | 人员名称 |
| result[].human.regionId | String | 是 | 所属区域 id |
| result[].human.regionType | Integer | 是 | 所属区域类型 |
| result[].human.telHome | String | 是 | 家庭电话 |
| result[].human.telMobile | String | 是 | 手机号码 |
| result[].human.telOffice | String | 是 | 办公电话 |
| result[].human.unitId | String | 是 | 所属部门 id |
| result[].human.unitName | String | 是 | 所属部门 |

### 6.7 可选扩展字段

| 字段路径 | 类型 | 出现条件 | 字段说明 |
|---|---|---|---|
| result[].parentRegionList | Object[] | regionHigherFlag 为 true | 人员所属区划的上级区划 |
| result[].parentUnitList | Object[] | unitHigherFlag 为 true | 人员所属部门的上级部门 |
| result[].dutyGridList | Object[] | dutyCellFlag 为 true | 人员所属责任网格 |
| result[].attachments | Object[] | attachmentFlag 为 true | 人员头像 |

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
        "regionCode": "",
        "longitude": 0.0,
        "latitude": 0.0,
        "regionName": "温州市",
        "regionType": 1,
        "parentId": "-1",
        "validFlag": "1",
        "children": []
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
        "address": "",
        "birthday": null,
        "humanCode": "100433",
        "humanDesc": "egova",
        "humanName": "egova",
        "regionId": "0",
        "regionType": 1,
        "telMobile": "15167863112",
        "unitId": "1",
        "unitName": "网格化城市管理"
      },
      "longitude": 120.69843166666666,
      "latitude": 27.999376666666663,
      "parentRegionList": null,
      "dutyGridList": null,
      "parentUnitList": null,
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
| 其他报错 | 需联系后台排查数据 | 检查请求参数、数据权限、后台日志 |

---

## 9. 适配建议

### 适合组件

- 表格；
- 人员完整列表；
- 详情入口列表；
- 条件筛选人员列表。

### 字段映射建议：普通表格

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.id | 字符串兜底 |
| name | item.patrolName | 字符串兜底 |
| cardId | item.cardId | 字符串兜底 |
| patrolCode | item.patrolCode | 字符串兜底 |
| patrolTypeName | item.patrolType.displayName | 对象判空 |
| regionName | item.region.regionName | 对象判空 |
| unitName | item.human.unitName | 对象判空 |
| onlineStatus | item.patrolState.patrolStateId | 1 转在线，否则离线 |
| longitude | item.longitude | Number 转换 |
| latitude | item.latitude | Number 转换 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
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
    });
}
```

### 地图点位过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        var stateId = item.patrolState ? item.patrolState.patrolStateId : 0;

        return {
            id: item.id || '',
            name: item.patrolName || '',
            typeName: item.patrolType && item.patrolType.displayName || '',
            regionName: item.region && item.region.regionName || '',
            unitName: item.human && item.human.unitName || '',
            online: stateId === 1,
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

1. 该接口返回字段较多，不建议无条件查询全量人员。
2. 展示全部人员时建议使用人员分页查询。
3. 地图打点优先使用人员简要列表查询。
4. `regionHigherFlag`、`unitHigherFlag`、`dutyCellFlag`、`attachmentFlag` 会增加查询成本，按需开启。
5. 表格列较少时，不要把完整对象全部透传给组件。