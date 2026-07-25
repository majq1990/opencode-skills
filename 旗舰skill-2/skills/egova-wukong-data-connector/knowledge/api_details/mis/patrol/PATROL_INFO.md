# 人员详情查询

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | PATROL_INFO |
| domain | MIS人员 |
| bizObject | 监督员 |
| apiName | 人员详情查询 |
| apiType | detail |
| 请求方式 | GET |
| 接口地址 | `/api/cgdb/patrol/info` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/人员详情查询` |
| 数据提交方式 | query/form，以实际网关配置为准 |
| 响应主路径 | `result` |
| 响应形态 | object |
| 适配组件 | 详情面板、详情弹窗、人员信息卡片、地图点位详情 |

---

## 2. 接口说明

该接口用于根据监督员主键查询监督员全部信息。

返回内容包括：

- 人员名称；
- 工号/人员编码；
- 卡号；
- 人员基本信息；
- 点位信息；
- 人员区划信息；
- 人员类型信息；
- 部门信息；
- 上级区划信息；
- 责任网格信息；
- 最近登录时间；
- 人员头像。

适合：

- 人员详情弹窗；
- 地图点位点击详情；
- 表格行点击详情；
- 人员信息卡片。

不适合：

- 人员列表展示；
- 分页表格；
- 人员数量统计；
- 图表分组统计。

> 注意：该接口目前只返回项目中已知会用于详情页展示的字段。如果新项目详情页需要展示的字段当前不存在，需要联系后台添加字段。

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
| id | String | 是 | 无 | 人员主键 |

---

## 5. 请求示例

```http
GET /api/cgdb/patrol/info?id=100433
```

或按平台配置传参：

```json
{
  "id": "100433"
}
```

---

## 6. 返回字段

### 6.1 顶层字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object | 是 | 人员详情对象 | 详情数据源 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 通常忽略 |

### 6.2 result 主字段

| 字段路径 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|
| result.id | String | 是 | 人员 id | id |
| result.cardId | String | 是 | 人员卡号 | 详情项 |
| result.patrolCode | String | 是 | 人员编码 | 详情项 |
| result.patrolName | String | 是 | 人员名称 | 标题 |
| result.patrolTypeId | String | 是 | 人员类型 id | 类型联动 |
| result.regionId | String | 是 | 人员区域 id | 区域联动 |
| result.longitude | Double | 是 | 人员经度 | 地图点位 |
| result.latitude | Double | 是 | 人员纬度 | 地图点位 |
| result.unitId | String | 是 | 人员部门 id | 部门联动 |
| result.latestLogonTime | String | 是 | 最近登录时间 | 详情项 |

### 6.3 patrolType 人员类型

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result.patrolType.id | String | 是 | 人员类型 id |
| result.patrolType.displayName | String | 是 | 人员类型名称 |

### 6.4 region 人员区划

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result.region.id | String | 是 | 区划主键 |
| result.region.regionCode | String | 是 | 区划编码 |
| result.region.longitude | Double | 是 | 经度 |
| result.region.latitude | Double | 是 | 纬度 |
| result.region.regionName | String | 是 | 区划名称 |
| result.region.regionType | Integer | 是 | 区划类型 |
| result.region.parentId | String | 是 | 父区划 id |

### 6.5 patrolState 人员点位状态

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result.patrolState.id | String | 是 | 人员主键 |
| result.patrolState.x | Double | 是 | 人员经度 |
| result.patrolState.y | Double | 是 | 人员纬度 |
| result.patrolState.updateTime | String | 是 | 更新时间 |
| result.patrolState.patrolStateId | Integer | 是 | 人员是否在线，1 在线 |

### 6.6 human 人员信息

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result.human.id | String | 是 | 人员 id |
| result.human.address | String | 是 | 人员地址 |
| result.human.birthday | String | 是 | 生日 |
| result.human.humanCode | String | 是 | 人员编码 |
| result.human.humanDesc | String | 是 | 人员描述 |
| result.human.humanName | String | 是 | 人员名称 |
| result.human.regionId | String | 是 | 所属区域 id |
| result.human.regionType | Integer | 是 | 所属区域类型 |
| result.human.telHome | String | 是 | 家庭电话 |
| result.human.telMobile | String | 是 | 手机号码 |
| result.human.telOffice | String | 是 | 办公电话 |
| result.human.unitId | String | 是 | 所属部门 id |
| result.human.unitName | String | 是 | 所属部门 |

### 6.7 扩展字段

| 字段路径 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|
| result.parentRegionList | Object[] | 是 | 人员所属区划的上级区划 |
| result.dutyGridList | Object[] | 是 | 人员所属责任网格 |
| result.parentUnitList | Object[] | 否 | 人员所属部门的上级部门 |
| result.attachments | Object[] | 否 | 人员头像 |
| result.attachments[].mediaPath | String | 否 | 头像路径 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": {
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
    "parentRegionList": [],
    "dutyGridList": [
      {
        "id": "181",
        "code": "1010",
        "desc": "1010",
        "name": "1010"
      }
    ],
    "parentUnitList": null,
    "unitId": "1"
  },
  "message": null,
  "tag": null,
  "totalCount": 1
}
```

---

## 8. 报错说明

| message | 说明 | 处理建议 |
|---|---|---|
| 其他报错 | 需联系后台排查数据 | 检查 id 是否存在、数据权限、后台日志 |

---

## 9. 适配建议

### 适合组件

- 详情弹窗；
- 详情面板；
- 人员信息卡片；
- 地图点位详情。

### 字段映射建议：详情卡片

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| title | data.patrolName | 字符串兜底 |
| lng | data.longitude | Number 转换 |
| lat | data.latitude | Number 转换 |
| items[].label | 固定文本 | 详情项名称 |
| items[].value | data.xxx | 字段兜底 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!data) {
        return {
            title: '',
            items: []
        };
    }

    var stateId = data.patrolState ? data.patrolState.patrolStateId : 0;

    return {
        title: data.patrolName || '',
        lng: Number(data.longitude || 0),
        lat: Number(data.latitude || 0),
        items: [
            { label: '人员名称', value: data.patrolName || '' },
            { label: '人员卡号', value: data.cardId || '' },
            { label: '人员编码', value: data.patrolCode || '' },
            { label: '人员类型', value: data.patrolType && data.patrolType.displayName || '' },
            { label: '所属区划', value: data.region && data.region.regionName || '' },
            { label: '所属部门', value: data.human && data.human.unitName || '' },
            { label: '手机号', value: data.human && data.human.telMobile || '' },
            { label: '地址', value: data.human && data.human.address || '' },
            { label: '在线状态', value: stateId === 1 ? '在线' : '离线' },
            { label: '更新时间', value: data.patrolState && data.patrolState.updateTime || '' },
            { label: '最近登录时间', value: data.latestLogonTime || '' }
        ]
    };
}
```

### 兼容完整响应包的过滤脚本

```javascript
function filter(data) {
    if (!data || data.hasError === true || !data.result) {
        return {
            title: '',
            items: []
        };
    }

    var item = data.result;
    var stateId = item.patrolState ? item.patrolState.patrolStateId : 0;

    return {
        title: item.patrolName || '',
        lng: Number(item.longitude || 0),
        lat: Number(item.latitude || 0),
        items: [
            { label: '人员名称', value: item.patrolName || '' },
            { label: '人员卡号', value: item.cardId || '' },
            { label: '人员编码', value: item.patrolCode || '' },
            { label: '人员类型', value: item.patrolType && item.patrolType.displayName || '' },
            { label: '所属区划', value: item.region && item.region.regionName || '' },
            { label: '所属部门', value: item.human && item.human.unitName || '' },
            { label: '手机号', value: item.human && item.human.telMobile || '' },
            { label: '地址', value: item.human && item.human.address || '' },
            { label: '在线状态', value: stateId === 1 ? '在线' : '离线' },
            { label: '更新时间', value: item.patrolState && item.patrolState.updateTime || '' },
            { label: '最近登录时间', value: item.latestLogonTime || '' }
        ]
    };
}
```

---

## 10. 性能和联调注意点

1. 必须确认人员 id 来源。
2. 人员 id 可来自人员列表、人员分页、人员简要列表或责任网格人员列表。
3. 如果详情组件需要头像，需要确认 `attachments` 的真实结构。
4. 如果详情字段不满足现场展示，需要联系后台补充字段。