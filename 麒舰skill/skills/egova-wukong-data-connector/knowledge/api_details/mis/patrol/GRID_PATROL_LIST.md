# 责任网格人员列表

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | GRID_PATROL_LIST |
| domain | MIS人员 |
| bizObject | 责任网格人员 |
| apiName | 责任网格人员列表 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/grid-patrol/list` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/责任网格人员列表` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 责任网格人员列表、地图点位、网格人员弹窗、人员表格 |

---

## 2. 接口说明

该接口用于统计责任网格下监督员数据。

可以通过入参增加监督员详细信息返回，例如：

- 姓名；
- 电话；
- 地址；
- 人员类型；
- 区划信息；
- 人员状态；
- 头像；
- 上级区划；
- 上级部门；
- 登录信息。

适合：

- 查看某个责任网格下人员；
- 责任网格人员列表；
- 网格人员地图点位；
- 网格人员弹窗。

不适合：

- 人员总数统计；
- 人员类型分组；
- 区划/部门分组统计；
- 全量人员分页表格。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_patrol | 业务库监督员表 |
| cgdb | tc_human | 业务库人员表 |
| cgdb | tc_patrol_type | 业务库监督员类型字典表 |
| cgdb | tc_region | 业务库区划表 |
| cgdb | tc_patrol_state | 业务库监督员状态表 |
| cgdb | tc_unit | 业务库部门表 |
| cgdb | tc_duty_grid_patrol | 责任网格-人员中间表 |

---

## 4. 请求参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| id | String | 否 | 无 | 责任网格 id |
| ids | String[] | 否 | 无 | 责任网格 id 列表 |
| patrolId | String | 否 | 无 | 人员 id |
| patrolIds | String | 否 | 无 | 人员 id 列表 |
| humanDetail | Boolean | 否 | false | 是否获取人员详细信息 |
| regionHigherFlag | Boolean | 否 | false | 是否展示上级区划 |
| attachmentFlag | Boolean | 否 | false | 是否查询人员图片 |
| unitHigherFlag | Boolean | 否 | false | 是否展示上级部门 |
| singleLogFlag | Boolean | 否 | false | 是否查询人员登录信息 |
| patrolName | String | 否 | 无 | 人员名称 / 监督员名字 |
| patrolTypeId | String | 否 | 无 | 人员类型 id / 监督员类型 |

---

## 5. 请求示例

```json
{
  "humanDetail": true,
  "id": 172,
  "attachmentFlag": true,
  "patrolName": "考评员1",
  "patrolTypeId": "8"
}
```

---

## 6. 返回字段

### 6.1 顶层字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果 | 列表数据源 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 辅助统计 |

### 6.2 result[] 主字段

| 字段路径 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|
| result[].id | String | 是 | 责任网格 id | gridId |
| result[].patrolId | String | 是 | 监督员 id | patrolId / id |
| result[].gridRegionTypeId | Integer | 是 | 网格区域类型 id | 可展示或联动 |
| result[].gridLevelId | Integer | 是 | 网格等级 id | 可展示或联动 |
| result[].dutyGrid | Object | 否 | 责任网格信息 | 网格字段 |
| result[].patrol | Object | 否 | 监督员信息 | 人员字段 |

### 6.3 dutyGrid 责任网格信息

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result[].dutyGrid.id | String | 否 | 责任网格 id |
| result[].dutyGrid.circleNum | Integer | 否 | 巡更圈数 |
| result[].dutyGrid.code | String | 否 | 编码 |
| result[].dutyGrid.desc | String | 否 | 描述 |
| result[].dutyGrid.name | String | 否 | 责任网格名称 |
| result[].dutyGrid.type | Integer | 否 | 类型 |
| result[].dutyGrid.areaType | Integer | 否 | 区域类型 |
| result[].dutyGrid.regionId | String | 否 | 上级 region |
| result[].dutyGrid.geoRange | String | 否 | 地理区域范围 |
| result[].dutyGrid.cellColor | String | 否 | 单元网格颜色 |

### 6.4 patrol 监督员信息

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result[].patrol.id | String | 否 | 人员 id |
| result[].patrol.cardId | String | 否 | 人员卡号 |
| result[].patrol.patrolCode | String | 否 | 人员编码 |
| result[].patrol.patrolName | String | 否 | 人员名称 |
| result[].patrol.patrolTypeId | String | 否 | 人员类型 id |
| result[].patrol.regionId | String | 否 | 人员区域 id |
| result[].patrol.imei | String | 否 | imei |
| result[].patrol.isAutoSendCheck | String | 否 | 是否自动发送核查 |
| result[].patrol.blacklistFlag | String | 否 | 黑名单标识 |
| result[].patrol.classTypeId | String | 否 | classTypeId |
| result[].patrol.gridTypeId | String | 否 | gridTypeId |
| result[].patrol.longitude | Double | 否 | 经度 |
| result[].patrol.latitude | Double | 否 | 纬度 |
| result[].patrol.unitId | String | 否 | 部门 id |
| result[].patrol.latestLogonTime | String | 否 | 最近登录时间 |
| result[].patrol.patrolType | Object | 否 | 人员类型 |
| result[].patrol.region | Object | 否 | 区划信息 |
| result[].patrol.patrolState | Object | 否 | 人员状态 |
| result[].patrol.human | Object | 否 | 人员基础信息 |
| result[].patrol.attachments | Object[] | 否 | 人员图片 |

### 6.5 patrolType 人员类型

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result[].patrol.patrolType.id | String | 否 | 人员类型 id |
| result[].patrol.patrolType.displayName | String | 否 | 人员类型名称 |
| result[].patrol.patrolType.displayOrder | Integer | 否 | 展示顺序 |

### 6.6 patrolState 人员状态

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result[].patrol.patrolState.id | String | 否 | 监督员 id |
| result[].patrol.patrolState.x | String / Double | 否 | 人员经度 |
| result[].patrol.patrolState.y | String / Double | 否 | 人员纬度 |
| result[].patrol.patrolState.updateTime | String | 否 | 人员更新时间 |
| result[].patrol.patrolState.patrolStateId | String / Integer | 否 | 人员状态 id，通常 1 表示在线 |

### 6.7 human 人员基础信息

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result[].patrol.human.id | String | 是 | 人员 id |
| result[].patrol.human.address | String | 是 | 人员地址 |
| result[].patrol.human.birthday | String | 是 | 生日 |
| result[].patrol.human.humanCode | String | 是 | 人员编码 |
| result[].patrol.human.humanDesc | String | 是 | 人员描述 |
| result[].patrol.human.humanName | String | 是 | 人员名称 |
| result[].patrol.human.regionId | String | 是 | 所属区域 id |
| result[].patrol.human.regionType | Integer | 是 | 所属区域类型 |
| result[].patrol.human.telHome | String | 是 | 家庭电话 |
| result[].patrol.human.telMobile | String | 是 | 手机号码 |
| result[].patrol.human.telOffice | String | 是 | 办公电话 |
| result[].patrol.human.unitId | String | 是 | 所属部门 id |
| result[].patrol.human.unitName | String | 是 | 所属部门 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "id": "172",
      "patrolId": "104667",
      "gridRegionTypeId": null,
      "gridLevelId": null,
      "dutyGrid": {
        "id": "172",
        "circleNum": 1,
        "code": "1001",
        "desc": "1001",
        "name": "1001",
        "type": 1,
        "areaType": -1,
        "regionId": "1",
        "geoRange": null,
        "cellColor": ""
      },
      "patrol": {
        "id": "104667",
        "cardId": "6802",
        "patrolCode": "",
        "patrolName": "6802",
        "patrolTypeId": "8",
        "regionId": "0",
        "patrolType": {
          "id": "8",
          "displayName": "管理干部",
          "displayOrder": 8
        },
        "patrolState": {
          "id": "104667",
          "x": null,
          "y": null,
          "updateTime": "2022-04-17 23:50:00",
          "patrolStateId": 0
        },
        "human": {
          "id": "104667",
          "humanCode": "104667",
          "humanName": "6802",
          "telMobile": "",
          "unitId": "104663",
          "unitName": "智慧城管信息采集部门"
        },
        "longitude": null,
        "latitude": null,
        "attachments": [],
        "unitId": "104663",
        "latestLogonTime": null
      }
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
| 其他报错 | 需联系后台排查数据 | 检查责任网格 id、人员筛选条件、数据权限、后台日志 |

---

## 9. 适配建议

### 适合组件

- 责任网格人员列表；
- 网格人员点位；
- 网格人员弹窗；
- 责任网格详情面板。

### 字段映射建议：列表

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| gridId | item.id | 字符串兜底 |
| gridName | item.dutyGrid.name | 对象判空 |
| patrolId | item.patrolId | 字符串兜底 |
| id | item.patrol.id | 对象判空 |
| name | item.patrol.patrolName | 对象判空 |
| cardId | item.patrol.cardId | 对象判空 |
| patrolTypeName | item.patrol.patrolType.displayName | 对象判空 |
| unitName | item.patrol.human.unitName | 对象判空 |
| mobile | item.patrol.human.telMobile | 对象判空 |
| online | item.patrol.patrolState.patrolStateId | 1 转在线 |
| lng | item.patrol.longitude | Number 转换 |
| lat | item.patrol.latitude | Number 转换 |

### 推荐过滤脚本：列表结构，data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        var patrol = item.patrol || {};
        var dutyGrid = item.dutyGrid || {};
        var patrolType = patrol.patrolType || {};
        var human = patrol.human || {};
        var patrolState = patrol.patrolState || {};
        var stateId = patrolState.patrolStateId;

        return {
            gridId: item.id || '',
            gridName: dutyGrid.name || '',
            patrolId: item.patrolId || patrol.id || '',
            id: patrol.id || item.patrolId || '',
            name: patrol.patrolName || human.humanName || '',
            cardId: patrol.cardId || '',
            patrolTypeName: patrolType.displayName || '',
            unitName: human.unitName || '',
            mobile: human.telMobile || '',
            online: stateId === 1 || stateId === '1',
            lng: Number(patrol.longitude || 0),
            lat: Number(patrol.latitude || 0)
        };
    });
}
```

### 推荐过滤脚本：地图点位结构

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        var patrol = item.patrol || {};
        var dutyGrid = item.dutyGrid || {};
        var patrolType = patrol.patrolType || {};
        var human = patrol.human || {};
        var patrolState = patrol.patrolState || {};
        var stateId = patrolState.patrolStateId;

        return {
            id: patrol.id || item.patrolId || '',
            name: patrol.patrolName || human.humanName || '',
            gridId: item.id || '',
            gridName: dutyGrid.name || '',
            patrolTypeName: patrolType.displayName || '',
            unitName: human.unitName || '',
            mobile: human.telMobile || '',
            online: stateId === 1 || stateId === '1',
            lng: Number(patrol.longitude || 0),
            lat: Number(patrol.latitude || 0)
        };
    }).filter(function (item) {
        return item.lng !== 0 && item.lat !== 0 && item.lng !== -1 && item.lat !== -1;
    });
}
```

---

## 10. 性能和联调注意点

1. 如果只需要责任网格与人员关系，不建议开启过多扩展字段。
2. `humanDetail=true` 会返回较完整的人员信息。
3. `attachmentFlag=true` 会返回人员图片，可能增加响应体大小。
4. 地图打点时要过滤经纬度为空、0 或 -1 的人员。
5. `patrolIds` 在原始文档中类型标为 String，但语义是人员 id 列表，联调时建议确认实际入参格式。
6. 原始文档中 `patrolName`、`patrolTypeId` 出现重复描述，按同名字段处理即可。