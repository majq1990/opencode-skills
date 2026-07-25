# 人员简要列表查询

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | PATROL_SIMPLE_LIST |
| domain | MIS人员 |
| bizObject | 监督员 |
| apiName | 人员简要列表查询 |
| apiType | simple_list |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/patrol/simple/list` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/人员简要列表查询` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 地图点位、人员图层、轻量人员列表、人员弹窗入口 |

---

## 2. 接口说明

该接口与人员列表查询逻辑相同，用于按条件查询监督员简要列表，常用于地图打点。

区别是该接口只返回部分关键字段，减少网络传输数据量。

返回关键字段包括：

- 人员 id；
- 卡号；
- 人员编码；
- 人员名称；
- 人员类型；
- 区域；
- 在线状态；
- 经纬度。

支持通过以下条件筛选：

- 人员名称；
- 人员类型；
- 在线/离线；
- 区划；
- 部门。

支持区划深钻和部门深钻。

适合：

- 地图点位；
- 人员图层；
- 轻量人员列表；
- 点位点击后再查详情。

不适合：

- 完整人员表格；
- 人员详情面板；
- 需要部门/上级区划/责任网格/头像等扩展信息的场景。

> 注意：该接口只返回关键字段，其余字段需调用人员详情查询接口查询。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_patrol | 业务库监督员表 |
| cgdb | tc_human | 业务库人员表 |
| cgdb | tc_patrol_type | 业务库监督员类型字典表 |
| cgdb | tc_region | 业务库区划表 |
| cgdb | tc_patrol_state | 业务库监督员状态表 |

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
| unitId | String | 否 | 无 | 指定所属部门 |
| unitExtendFlag | Boolean | 否 | 无 | 是否支持部门下钻 |
| regionIdList | String[] | 否 | 无 | 指定所属区划列表 |
| state | Boolean | 否 | 无 | 是否在线 |

---

## 5. 请求示例

```json
{
  "regionId": "0"
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 简要人员列表 | 地图点位数据源 |
| result[].id | id | String | 是 | 人员 id | id |
| result[].cardId | cardId | String | 是 | 卡号 | 弹窗字段 |
| result[].patrolCode | patrolCode | String | 是 | 人员代码 | 弹窗字段 |
| result[].patrolName | patrolName | String | 是 | 人员名称 | name |
| result[].patrolTypeId | patrolTypeId | String | 是 | 人员类型 id | 类型筛选 |
| result[].patrolTypeName | patrolTypeName | String | 是 | 人员类型 | typeName |
| result[].regionId | regionId | String | 是 | 区域 id | 区域筛选 |
| result[].regionName | regionName | String | 是 | 区域名称 | regionName |
| result[].onlineFlag | onlineFlag | Boolean | 是 | 是否在线 | online |
| result[].longitude | longitude | Double | 是 | 经度 | lng |
| result[].latitude | latitude | Double | 是 | 纬度 | lat |
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
      "id": "100433",
      "cardId": "100433",
      "patrolCode": "",
      "patrolName": "egova",
      "patrolTypeId": "8",
      "patrolTypeName": "管理干部",
      "regionId": "0",
      "regionName": "温州市",
      "onlineFlag": true,
      "longitude": 120.69843166666666,
      "latitude": 27.999376666666663
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

- 地图点位；
- 人员图层；
- 人员点位弹窗；
- 轻量人员列表。

### 字段映射建议：地图点位

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.id | 字符串兜底 |
| name | item.patrolName | 字符串兜底 |
| cardId | item.cardId | 字符串兜底 |
| patrolTypeName | item.patrolTypeName | 字符串兜底 |
| regionName | item.regionName | 字符串兜底 |
| online | item.onlineFlag | Boolean |
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
            name: item.patrolName || '',
            cardId: item.cardId || '',
            patrolCode: item.patrolCode || '',
            patrolTypeName: item.patrolTypeName || '',
            regionName: item.regionName || '',
            online: item.onlineFlag === true,
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

1. 地图打点优先使用该接口，而不是人员完整列表接口。
2. 该接口不返回完整人员详情。
3. 点击点位展示详情时，可用 `id` 调用人员详情接口。
4. 联调时注意过滤经纬度为空或为 0 的人员。