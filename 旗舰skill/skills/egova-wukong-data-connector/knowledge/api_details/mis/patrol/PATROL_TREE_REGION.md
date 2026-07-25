# 人员区划分组树形

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | PATROL_TREE_REGION |
| domain | MIS人员 |
| bizObject | 监督员 |
| apiName | 人员区划分组树形 |
| apiType | tree |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/patrol/tree?@state=region` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/人员区划分组树形` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 区划树、区划人员统计树、地图区域树、左侧树右侧人员列表 |

---

## 2. 接口说明

该接口用于统计监督员中指定查询条件查出来的区划下，每一个区划的人员总数，并且可以展示人员简单信息列表。

人员简单列表包含：

- 人员 id；
- 人员名称；
- 所属区划；
- 经纬度；
- 是否在线；
- 上级区划。

支持区划深钻：

- 统计某个区划人员总数时，如果人员属于该区划下属区划，也可以认为该人员属于当前区划；
- 由 `regionExtendFlag` 控制。

支持通过以下条件筛选：

- 人员名称；
- 人员类型；
- 在线/离线；
- 区划；
- 部门。

适合：

- 区划树；
- 区划人员统计；
- 地图区域树；
- 左侧区划树 + 右侧人员列表；
- 区划节点展示人员数。

不适合：

- 人员类型统计；
- 部门树；
- 人员完整详情；
- 分页表格。

> 注意：该接口按照区划进行分组展示树形结构，要展示的区划由 `regionCondition` 指定。查询大数据量区划时响应时间会变长，尽量不要查询全部区划。

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

### 4.1 人员筛选参数

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
| showListFlag | Boolean | 否 | false | 是否查询区域节点下的人员列表数据 |

### 4.2 regionCondition 区划查询条件

| 参数路径 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| regionCondition | Object | 是 | 区划条件对象 |
| regionCondition.id | String | 否 | 指定区划主键 |
| regionCondition.ids | String[] | 否 | 指定区划主键列表 |
| regionCondition.regionType | Integer | 否 | 查询指定级别的区划 |
| regionCondition.parentId | String | 否 | 指定查询父区划下属子区划 |
| regionCondition.parentIds | String[] | 否 | 指定查询父区划列表下属子区划 |

### 4.3 regionType 说明

| 值 | 含义 |
|---|---|
| 1 | 市 |
| 2 | 区县 |
| 3 | 街道 |
| 4 | 社区 |
| 5 | 网格 |

---

## 5. 请求示例

```json
{
  "regionCondition": {
    "regionType": 2
  },
  "showListFlag": true
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果 | 树节点数据源 |
| result[].name | name | String | 是 | 区划 id | 可映射为 `id` |
| result[].text | text | String | 是 | 区划名称 | 可映射为 `label` / `name` |
| result[].value | value | Integer | 是 | 人员总数 | 可映射为 `value` |
| result[].patrolList | patrolList | Object[] | 否 | 区域节点下人员简单列表，`showListFlag=true` 时返回 | 可用于节点明细 |
| result[].patrolList[].patrolId | patrolId | String | 否 | 人员 id | 人员明细 id |
| result[].patrolList[].patrolName | patrolName | String | 否 | 人员名称 | 人员展示名称 |
| result[].patrolList[].regionId | regionId | String | 否 | 人员所属区划 id | 联动字段 |
| result[].patrolList[].longitude | longitude | Double | 否 | 经度 | 地图 lng |
| result[].patrolList[].latitude | latitude | Double | 否 | 纬度 | 地图 lat |
| result[].patrolList[].onlineFlag | onlineFlag | Integer / Boolean | 否 | 是否在线 | 在线状态 |
| result[].patrolList[].parentIds | parentIds | Object[] | 否 | 上级区划列表 | 可用于展示层级 |
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
      "name": "2",
      "text": "瓯海区",
      "value": 4,
      "patrolList": [
        {
          "patrolId": "100936",
          "patrolName": "瓯海区民政局",
          "regionId": "2",
          "longitude": null,
          "latitude": null,
          "onlineFlag": 0,
          "parentIds": [
            {
              "id": "0",
              "regionCode": "",
              "longitude": 0.0,
              "latitude": 0.0,
              "regionName": "温州市",
              "regionType": 1,
              "parentId": "-1",
              "validFlag": "1",
              "children": []
            }
          ]
        }
      ]
    },
    {
      "name": "3",
      "text": "生态园区",
      "value": 0,
      "patrolList": []
    }
  ],
  "message": null,
  "tag": null,
  "totalCount": 2
}
```

---

## 8. 报错说明

| message | 说明 | 处理建议 |
|---|---|---|
| 其他报错 | 需联系后台排查数据 | 检查 `regionCondition`、筛选条件、数据权限、后台日志 |

---

## 9. 适配建议

### 适合组件

- 区划树；
- 区划人员统计树；
- 地图区域树；
- 左侧区划树 + 右侧人员列表。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.name | 字符串兜底 |
| value | item.name | 字符串兜底，树选择值 |
| label | item.text | 字符串兜底 |
| name | item.text | 字符串兜底 |
| count | item.value | Number 转换 |
| patrolList | item.patrolList | 数组兜底 |
| children | item.children | 如果接口无 children，可默认空数组 |

### 推荐过滤脚本：树节点结构，data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            id: item.name || '',
            value: item.name || '',
            label: item.text || '',
            name: item.text || '',
            count: Number(item.value || 0),
            patrolList: Array.isArray(item.patrolList) ? item.patrolList : [],
            children: Array.isArray(item.children) ? item.children : []
        };
    });
}
```

### 推荐过滤脚本：节点人员列表扁平化

如果组件需要把各区划节点下的人员拉平成一个人员点位列表，可以用：

```javascript
function filter(data) {
    var result = [];

    if (!Array.isArray(data)) {
        return [];
    }

    data.forEach(function (region) {
        var regionId = region.name || '';
        var regionName = region.text || '';
        var list = Array.isArray(region.patrolList) ? region.patrolList : [];

        list.forEach(function (item) {
            result.push({
                id: item.patrolId || '',
                name: item.patrolName || '',
                regionId: regionId,
                regionName: regionName,
                lng: Number(item.longitude || 0),
                lat: Number(item.latitude || 0),
                online: item.onlineFlag === true || item.onlineFlag === 1
            });
        });
    });

    return result.filter(function (item) {
        return item.lng !== 0 && item.lat !== 0;
    });
}
```

---

## 10. 性能和联调注意点

1. 必须传 `regionCondition` 指定要展示的区划范围。
2. 查询大数据量区划时响应时间会变长，尽量不要查询全部区划。
3. 如果只需要区划人员数量，不建议开启 `showListFlag`。
4. 如果需要节点下人员列表，开启 `showListFlag=true`。
5. 当前示例主要是平铺节点；如果悟空组件需要真正多级树，需要确认接口是否返回 `children`。
6. `name` 是区划 id，`text` 是区划名称。