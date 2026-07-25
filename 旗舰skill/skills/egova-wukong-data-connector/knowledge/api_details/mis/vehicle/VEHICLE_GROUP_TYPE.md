# 车辆类型分组

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | VEHICLE_GROUP_TYPE |
| domain | 城管车辆 |
| bizObject | 车辆 |
| apiName | 车辆类型分组 |
| apiType | group |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/vehicle/group` |
| 星桥接口路径地址 | `API平台/悟能接口/车辆相关/车辆类型分组` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 饼图、柱状图、排行列表、分类统计卡片 |

---

## 2. 接口说明

该接口用于统计车辆中每一种车辆类型的车辆总数。

支持通过车辆主键、车辆主键列表、车牌号、区划、部门、车辆状态、车辆类型、工作时间等条件进行筛选。

支持区划深钻和部门深钻：

- `regionExtendFlag`：是否统计下级区划；
- `unitExtendFlag`：是否统计下级部门。

适合：

- 饼图；
- 柱状图；
- 分类排行；
- 车辆类型数量统计。

不适合：

- 车辆明细列表；
- 车辆分页表格；
- 地图打点；
- 车辆详情弹窗。

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
| onlineFlag | onlineFlag | String | 否 | 无 |  | 车辆状态 |
| telPhoneOwner | telPhoneOwner | String | 否 | 无 |  | 电话 |
| vehicleTypeId | vehicleTypeId | String | 否 | 无 |  | 车辆类型 |
| vehicleTypeIds | vehicleTypeIds | String[] | 否 | 无 | `["xx","xx"]` | 多个车辆类型 |
| deleteFlag | deleteFlag | String | 否 | 无 |  | 是否删除 |
| validFlag | validFlag | String | 否 | 无 |  | 是否有效 |
| regionExtendFlag | regionExtendFlag | String | 否 | 无 |  | 是否统计下级区划 |
| unitExtendFlag | unitExtendFlag | String | 否 | 无 |  | 是否统计下级部门 |

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
  "unitExtendFlag": ""
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错；true 表示报错，false 表示正常 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果数组 | 图表数据源 |
| result[].name | name | String | 是 | 车辆类型名称 | 可映射为 `name` |
| result[].text | text | String | 是 | 车辆类型id | 可映射为 `id` |
| result[].value | value | Integer | 是 | 车辆数量 | 可映射为 `value` |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 可用于辅助统计 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "name": "垃圾车",
      "text": "5",
      "value": 1055
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

- 饼图；
- 柱状图；
- 排行列表；
- 分类统计卡片。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| name | item.name | 字符串兜底 |
| value | item.value | Number 转换 |
| id | item.text | 字符串兜底，可用于联动 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            name: item.name || '',
            value: Number(item.value || 0),
            id: item.text || ''
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

### 兼容完整响应包的过滤脚本

只有当悟空传入的是完整响应包时使用。

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
            name: item.name || '',
            value: Number(item.value || 0),
            id: item.text || ''
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

---

## 10. 性能和联调注意点

1. 该接口是聚合接口，不返回车辆明细。
2. 如果组件需要车辆列表、地图点位或详情，不应使用该接口。
3. 如果需要按区域或部门过滤，应传入 `regionId` / `unitId` 或对应列表字段。
4. 如果需要统计下级区划或部门，应确认 `regionExtendFlag` / `unitExtendFlag`。
5. `name/text/value` 的语义在不同分组接口中可能不同，不得机械复用映射。