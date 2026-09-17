# 车辆简要列表查询

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | VEHICLE_SIMPLE_LIST |
| domain | 城管车辆 |
| bizObject | 车辆 |
| apiName | 车辆简要列表查询 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/vehicle/simple/list` |
| 星桥接口路径地址 | `API平台/悟能接口/车辆相关/车辆简要列表查询` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 地图打点、轻量列表 |

---

## 2. 接口说明

该接口与车辆列表查询接口逻辑相同，用于按指定查询条件查询车辆列表，常用于地图上打点。

区别是：该接口只返回部分关键字段，用于减少网络传输数据量。

适合：

- 地图打点；
- 车辆当前位置展示；
- 车辆轻量列表；
- 地图点位弹窗基础信息。

不适合：

- 车辆完整详情页；
- 复杂表格字段展示；
- 车辆图片、人员、上级区划/部门等扩展信息展示。

如需更多详情字段，应调用车辆详情查询接口。

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
| result | result | Object[] | 是 | 返回结果数组 | 地图点位数据源 |
| result[].id | id | String | 是 | 车辆id | 可映射为 `id` |
| result[].simCardNum | simCardNum | String | 是 | sim号 | 可作为设备标识 |
| result[].vehicleNum | vehicleNum | String | 是 | 车牌号 | 可映射为 `name` / `vehicleNum` |
| result[].unitId | unitId | String | 是 | 部门id | 可用于联动 |
| result[].unitName | unitName | String | 是 | 部门名称 | 可用于点位弹窗 |
| result[].vehicleTypeId | vehicleTypeId | String | 是 | 车辆类型id | 可用于筛选/联动 |
| result[].vehicleTypeName | vehicleTypeName | String | 是 | 车辆类型名称 | 可用于点位弹窗 |
| result[].regionId | regionId | String | 是 | 区域id | 可用于筛选/联动 |
| result[].regionName | regionName | String | 是 | 区域名称 | 可用于点位弹窗 |
| result[].onlineFlag | onlineFlag | Boolean | 是 | 车辆状态 | 可映射为在线/离线 |
| result[].longitude | longitude | Double | 是 | 经度 | 可映射为 `lng` |
| result[].latitude | latitude | Double | 是 | 纬度 | 可映射为 `lat` |
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
      "id": "2",
      "simCardNum": "202104301115",
      "vehicleNum": "鄂A77H47",
      "unitId": "100540",
      "unitName": "恒旺渣土运输有限公司",
      "vehicleTypeId": "5",
      "vehicleTypeName": "垃圾车",
      "regionId": "1",
      "regionName": "鹿城区",
      "onlineFlag": false,
      "longitude": 12738779,
      "latitude": 3542300.5
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
- 车辆位置大屏；
- 车辆轻量列表；
- 地图点位弹窗。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.id | 字符串兜底 |
| name | item.vehicleNum | 字符串兜底 |
| vehicleNum | item.vehicleNum | 字符串兜底 |
| typeName | item.vehicleTypeName | 字符串兜底 |
| unitName | item.unitName | 字符串兜底 |
| regionName | item.regionName | 字符串兜底 |
| online | item.onlineFlag | Boolean 判断 |
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
            name: item.vehicleNum || '',
            vehicleNum: item.vehicleNum || '',
            typeName: item.vehicleTypeName || '',
            unitName: item.unitName || '',
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
            id: item.id || '',
            name: item.vehicleNum || '',
            vehicleNum: item.vehicleNum || '',
            typeName: item.vehicleTypeName || '',
            unitName: item.unitName || '',
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

1. 该接口只返回关键字段，适合地图打点。
2. 如果需要详情页字段，应调用车辆详情查询接口。
3. 经度、纬度为空或为 0 的数据建议过滤。
4. 需要确认地图组件使用的坐标系是否与接口经纬度一致。
5. 如果数据量很大，应增加区域、部门、车辆类型或状态筛选。