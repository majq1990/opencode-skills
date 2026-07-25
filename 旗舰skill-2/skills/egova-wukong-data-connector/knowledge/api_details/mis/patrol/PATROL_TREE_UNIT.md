# 人员部门分组树形

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | PATROL_TREE_UNIT |
| domain | MIS人员 |
| bizObject | 监督员 |
| apiName | 人员部门分组树形 |
| apiType | tree |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/patrol/tree?@state=unit` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/人员部门分组树形` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 部门树、部门人员统计树、左侧部门树右侧人员列表 |

---

## 2. 接口说明

该接口用于统计监督员中指定查询条件查出来的部门下，每一个部门的人员总数及部门下的人员列表。

支持部门深钻：

- 统计某个部门下人员总数时，如果人员属于该部门下属部门，也可以认为该人员属于当前部门；
- 由 `unitExtendFlag` 控制。

支持区划深钻：

- 通过区划过滤时，如果人员属于该区划下属区划，也可以认为该人员属于当前区划；
- 由 `regionExtendFlag` 控制。

支持展示部门节点下人员简单列表：

- `showListFlag=true` 时，返回节点下 `patrolList`；
- `topUnitId` 可用于指定某个部门作为顶级节点展示。

适合：

- 部门树；
- 部门人员统计树；
- 左侧部门树 + 右侧人员列表；
- 部门节点展示人员数。

不适合：

- 区划树；
- 人员类型统计；
- 人员完整详情；
- 分页表格。

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
| unitId | String | 否 | 无 | 指定所属部门 |
| state | Boolean | 否 | 无 | 是否在线 |
| unitExtendFlag | Boolean | 否 | false | 是否支持部门下钻 |
| showListFlag | Boolean | 否 | false | 是否展示部门树节点下的人员简单列表 |
| topUnitId | String | 否 | 无 | 用于展示某个部门节点作为顶级节点，展示该部门下的所有人员和部门树 |

### 4.2 unitCondition 部门查询条件

| 参数路径 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| unitCondition | Object | 是 | 部门条件对象 |
| unitCondition.id | String | 否 | 指定部门主键 |
| unitCondition.ids | String[] | 否 | 指定部门主键列表 |
| unitCondition.typeCode | String | 否 | 指定部门编码 |
| unitCondition.address | String | 否 | 模糊查询部门地址 |
| unitCondition.validFlag | Boolean | 否 | 是否有效 |
| unitCondition.deleteFlag | Boolean | 否 | 是否删除 |
| unitCondition.unitName | String | 否 | 模糊查询部门名称 |
| unitCondition.regionId | String | 否 | 指定部门所属区划 |
| unitCondition.parentId | String | 否 | 指定部门所属父级部门 |

---

## 5. 请求示例

```json
{
  "unitCondition": {
    "deleteFlag": false,
    "validFlag": true
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
| result[].name | name | String | 是 | 部门 id | 可映射为 `id` |
| result[].text | text | String | 是 | 部门名称 | 可映射为 `label` / `name` |
| result[].value | value | Integer | 是 | 人员总数 | 可映射为 `value` / `count` |
| result[].patrolList | patrolList | Object[] | 否 | 部门节点下人员简单列表，`showListFlag=true` 时返回 | 节点明细 |
| result[].children | children | Object[] | 否 | 子部门节点 | 树 children |
| result[].patrolList[].id | id | String | 否 | 人员 id | 人员明细 id |
| result[].patrolList[].cardId | cardId | String | 否 | 人员卡号 | 人员字段 |
| result[].patrolList[].patrolCode | patrolCode | String | 否 | 人员编码 | 人员字段 |
| result[].patrolList[].patrolName | patrolName | String | 否 | 人员名称 | 人员展示名称 |
| result[].patrolList[].patrolTypeId | patrolTypeId | String | 否 | 人员类型 id | 类型联动 |
| result[].patrolList[].patrolTypeName | patrolTypeName | String | 否 | 人员类型名称 | 展示字段 |
| result[].patrolList[].regionId | regionId | String | 否 | 区划 id | 区划联动 |
| result[].patrolList[].regionName | regionName | String | 否 | 区划名称 | 展示字段 |
| result[].patrolList[].onlineFlag | onlineFlag | Boolean | 否 | 是否在线 | 在线状态 |
| result[].patrolList[].longitude | longitude | Double | 否 | 经度 | 地图 lng |
| result[].patrolList[].latitude | latitude | Double | 否 | 纬度 | 地图 lat |
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
      "name": "1",
      "text": "网格化城市管理",
      "value": 4,
      "patrolList": [
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
      "children": [
        {
          "name": "2",
          "text": "市监督中心",
          "value": 0
        },
        {
          "name": "3",
          "text": "市指挥中心",
          "value": 0
        }
      ]
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
| 其他报错 | 需联系后台排查数据 | 检查 `unitCondition`、筛选条件、数据权限、后台日志 |

---

## 9. 适配建议

### 适合组件

- 部门树；
- 部门人员统计树；
- 左侧部门树 + 右侧人员列表；
- 部门节点人员数展示。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.name | 字符串兜底 |
| value | item.name | 字符串兜底，树选择值 |
| label | item.text | 字符串兜底 |
| name | item.text | 字符串兜底 |
| count | item.value | Number 转换 |
| patrolList | item.patrolList | 数组兜底 |
| children | item.children | 递归处理 |

### 推荐过滤脚本：树节点结构，data 为 result 本体

```javascript
function filter(data) {
    function convert(list) {
        if (!Array.isArray(list)) {
            return [];
        }

        return list.map(function (item) {
            return {
                id: item.name || '',
                value: item.name || '',
                label: item.text || '',
                name: item.text || '',
                count: Number(item.value || 0),
                patrolList: Array.isArray(item.patrolList) ? item.patrolList : [],
                children: convert(item.children)
            };
        });
    }

    return convert(data);
}
```

### 推荐过滤脚本：节点人员列表扁平化

```javascript
function filter(data) {
    var result = [];

    function collect(list, unitId, unitName) {
        if (!Array.isArray(list)) {
            return;
        }

        list.forEach(function (node) {
            var currentUnitId = node.name || unitId || '';
            var currentUnitName = node.text || unitName || '';
            var patrolList = Array.isArray(node.patrolList) ? node.patrolList : [];

            patrolList.forEach(function (item) {
                result.push({
                    id: item.id || '',
                    name: item.patrolName || '',
                    cardId: item.cardId || '',
                    patrolTypeName: item.patrolTypeName || '',
                    regionName: item.regionName || '',
                    unitId: currentUnitId,
                    unitName: currentUnitName,
                    online: item.onlineFlag === true,
                    lng: Number(item.longitude || 0),
                    lat: Number(item.latitude || 0)
                });
            });

            collect(node.children, currentUnitId, currentUnitName);
        });
    }

    collect(data, '', '');

    return result;
}
```

---

## 10. 性能和联调注意点

1. 必须传 `unitCondition` 指定要展示的部门范围。
2. 建议 `unitCondition` 默认带 `deleteFlag=false`、`validFlag=true`。
3. 如果只需要部门人员数量，不建议开启 `showListFlag`。
4. 如果需要节点下人员列表，开启 `showListFlag=true`。
5. `topUnitId` 可用于指定某个部门作为顶级节点。
6. `children` 存在时可以直接递归成树；不存在时按平铺节点处理。