# 车辆部门分组树形

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | VEHICLE_TREE_UNIT |
| domain | 城管车辆 |
| bizObject | 车辆 |
| apiName | 车辆部门分组树形 |
| apiType | tree |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/vehicle/group?@state=unit` |
| 星桥接口路径地址 | `API平台/悟能接口/车辆相关/车辆部门分组` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 部门树、部门车辆分布、部门统计树 |

---

## 2. 接口说明

该接口用于统计车辆中指定查询条件下，每个部门的车辆总数，并可返回车辆简单列表。

支持部门深钻：

- 统计某个部门车辆总数时，如果车辆属于该部门下属部门，也可以认为该车辆属于当前部门；
- 由 `unitExtendFlag` 控制。

支持区划深钻：

- 通过区划过滤时，如果车辆属于该区划下属区划，也可以认为该车辆属于当前区划；
- 由 `regionExtendFlag` 控制。

支持是否返回车辆列表：

- `showListFlag`：是否在树节点中返回车辆列表。

适合：

- 部门树统计；
- 部门车辆分布；
- 左侧部门树 + 右侧车辆列表；
- 部门车辆数量展示。

不适合：

- 区划树统计；
- 单纯车辆类型统计；
- 车辆完整详情。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_vehicle | 业务库车辆表 |
| cgdb | tc_region | 业务库区划表 |
| cgdb | to_vehicle_pos | 业务库车辆最新点位表 |
| cgdb | tc_dic_vehicle_type | 业务库城管车辆类型表 |
| cgdb | tc_vehicle_unit | 业务库车辆单位表 |

---

## 4. 请求参数

### 4.1 车辆筛选参数

| 参数路径 | 参数名 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
|---|---|---|---|---|---|---|
| id | id | String | 否 | 无 |  | 车辆id |
| ids | ids | String[] | 否 | 无 | `["xx","xx"]` | 多个车辆id |
| vehicleNum | vehicleNum | String | 否 | 无 | 模糊查询 | 车牌号 |
| vehicleUsage | vehicleUsage | String | 否 | 无 | 模糊查询 | 车辆用途 |
| vehicleBrand | vehicleBrand | String | 否 | 无 | 模糊查询 | 车辆品牌 |
| regionId | regionId | String | 否 | 无 |  | 区域id |
| unitId | unitId | String | 否 | 无 |  | 部门id |
| regionIdList | regionIdList | String[] | 否 | 无 | `["xx","xx"]` | 多个区域id |
| unitIdList | unitIdList | String[] | 否 | 无 | `["xx","xx"]` | 多个部门id |
| startWorkTime | startWorkTime | String | 否 | 无 |  | 开始工作时间 |
| endWorkTime | endWorkTime | String | 否 | 无 |  | 结束工作时间 |
| vehicleOwner | vehicleOwner | String | 否 | 无 |  | 车辆所属者/司机 |
| onlineFlag | onlineFlag | Boolean | 否 | 无 |  | 车辆状态 |
| telPhoneOwner | telPhoneOwner | String | 否 | 无 |  | 电话 |
| vehicleTypeId | vehicleTypeId | String | 否 | 无 |  | 车辆类型 |
| vehicleTypeIds | vehicleTypeIds | String[] | 否 | 无 | `["xx","xx"]` | 多个车辆类型 |
| deleteFlag | deleteFlag | Boolean | 否 | 无 |  | 是否删除 |
| validFlag | validFlag | Boolean | 否 | 无 |  | 是否有效 |
| regionExtendFlag | regionExtendFlag | Boolean | 否 | 无 |  | 是否统计下级区划 |
| unitExtendFlag | unitExtendFlag | Boolean | 否 | 无 |  | 是否统计下级部门 |
| showListFlag | showListFlag | Boolean | 否 | false |  | 是否在节点展示车辆列表 |

### 4.2 部门条件 vehicleUnitCondition

| 参数路径 | 参数名 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
|---|---|---|---|---|---|---|
| vehicleUnitCondition.id | id | String | 否 | 无 | 属于 vehicleUnitCondition | 部门id |
| vehicleUnitCondition.ids | ids | String[] | 否 | 无 | 属于 vehicleUnitCondition | 多个部门id |
| vehicleUnitCondition.seniorId | seniorId | String | 否 | 无 | 属于 vehicleUnitCondition | 上级id |
| vehicleUnitCondition.seniorIds | seniorIds | String[] | 否 | 无 | 属于 vehicleUnitCondition | 多个上级id |

---

## 5. 请求示例

```json
{
  "id": "2",
  "ids": ["2", "3"],
  "vehicleNum": "",
  "vehicleUsage": "",
  "vehicleBrand": "",
  "regionId": "",
  "unitId": "",
  "regionIdList": [],
  "unitIdList": [],
  "startWorkTime": "",
  "endWorkTime": "",
  "vehicleOwner": "",
  "onlineFlag": "",
  "telPhoneOwner": "",
  "vehicleTypeId": "",
  "vehicleTypeIds": [],
  "deleteFlag": "",
  "validFlag": "",
  "regionExtendFlag": "",
  "unitExtendFlag": "",
  "showListFlag": "true",
  "vehicleUnitCondition": {
    "id": "",
    "ids": [],
    "seniorId": "",
    "seniorIds": []
  }
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果数组 | 树节点数据源 |
| result[].name | name | String | 是 | 部门id 或部门标识，需以实际返回为准 | 可映射为 `id` |
| result[].text | text | String | 是 | 部门名称，需以实际返回为准 | 可映射为 `label` |
| result[].value | value | Integer | 是 | 车辆数量 | 可映射为 `value` |
| result[].vehicleList | vehicleList | Object[] | 否 | 车辆简单列表，showListFlag 为 true 时返回 | 可用于节点明细 |
| result[].vehicleList[].vehicleId | vehicleId | String | 否 | 车辆id | 车辆明细 id |
| result[].vehicleList[].vehicleNum | vehicleNum | String | 否 | 车牌号 | 车辆展示名称 |
| result[].vehicleList[].unitId | unitId | String | 否 | 部门id | 车辆所属部门 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 可辅助统计 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "name": "100540",
      "text": "恒旺渣土运输有限公司",
      "value": 35,
      "vehicleList": [
        {
          "vehicleId": "2",
          "vehicleNum": "鄂A77H47",
          "unitId": "100540"
        }
      ]
    }
  ],
  "message": null,
  "tag": null,
  "totalCount": 1
}
```

> 注意：若现场真实返回中的 `name/text` 与示例不同，应以真实返回为准调整映射。

---

## 8. 报错说明

| message | 说明 | 处理建议 |
|---|---|---|
| 其他报错 | 需联系后台排查数据 | 检查请求参数、数据权限、后台日志 |
| 请传入部门条件! | 未传入 `vehicleUnitCondition` | 补充部门条件 |
| 未找到对应部门! | 传入的 `vehicleUnitCondition` 无法找到对应部门 | 检查部门 id、seniorId、ids 是否正确 |

---

## 9. 适配建议

### 适合组件

- 部门树；
- 部门车辆分布；
- 左侧部门树 + 右侧车辆列表；
- 部门车辆数量统计。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.name | 字符串兜底 |
| label | item.text | 字符串兜底 |
| name | item.text | 字符串兜底 |
| value | item.value | Number 转换 |
| vehicleList | item.vehicleList | 数组兜底 |
| children | item.children | 如果接口无 children，可默认空数组 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            id: item.name || '',
            label: item.text || item.name || '',
            name: item.text || item.name || '',
            value: Number(item.value || 0),
            vehicleList: Array.isArray(item.vehicleList) ? item.vehicleList : [],
            children: Array.isArray(item.children) ? item.children : []
        };
    });
}
```

### 兼容完整响应包的过滤脚本

```javascript
function filter(data) {
    if (!data || data.hasError === true) {
        return [];
    }

    var list = data.result;
    if (!Array.isArray(list)) {
        return [];
    }

    return list.map(function (item) {
        return {
            id: item.name || '',
            label: item.text || item.name || '',
            name: item.text || item.name || '',
            value: Number(item.value || 0),
            vehicleList: Array.isArray(item.vehicleList) ? item.vehicleList : [],
            children: Array.isArray(item.children) ? item.children : []
        };
    });
}
```

---

## 10. 性能和联调注意点

1. 如果 `showListFlag=true`，接口会返回节点下车辆列表，数据量可能明显增加。
2. 只需要部门统计数量时，建议 `showListFlag=false`。
3. 使用该接口前应确认 `vehicleUnitCondition`。
4. 如需统计下级部门，应确认 `unitExtendFlag`。
5. 如组件需要真正多级树结构，需要确认接口是否返回 `children`；当前示例主要是平铺节点。
6. `name/text` 语义需结合现场真实返回确认。