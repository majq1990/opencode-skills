# 车辆分页查询

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | VEHICLE_PAGE |
| domain | 城管车辆 |
| bizObject | 车辆 |
| apiName | 车辆分页查询 |
| apiType | page |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/vehicle/page` |
| 星桥接口路径地址 | `API平台/悟能接口/车辆相关/车辆分页查询` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 分页表格、车辆列表 |

---

## 2. 接口说明

该接口查询逻辑与车辆列表查询相同，区别是该接口会根据请求中的分页参数返回指定页的数据。

基础查询可以返回：

- 车牌号；
- 车辆品牌；
- 车辆颜色；
- 车辆状态；
- 车辆地址；
- 车速；
- 里程数；
- 油耗；
- 车辆点位信息；
- 车辆类型信息；
- 车辆区划信息；
- 车辆部门信息等。

通过传参配置可以查询：

- 上级部门信息；
- 上级区划信息；
- 车辆关联人员；
- 车辆图片等。

适合：

- 分页表格；
- 车辆管理列表；
- 数据量较大的车辆列表展示。

不适合：

- 饼图/柱状图分组统计；
- 地图高频点位打点；
- 单个详情弹窗。

> 注意：上级部门、上级区划、车辆关联人员、车辆图片等字段查询较耗性能，确实需要时再开启。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_vehicle | 业务库车辆表 |
| cgdb | tc_region | 业务库区划表 |
| cgdb | to_vehicle_pos | 业务库车辆最新点位表 |
| cgdb | tc_dic_vehicle_type | 业务库城管车辆类型表 |
| cgdb | tc_vehicle_unit | 业务库车辆单位表 |
| cgdb | tc_vehicle_human_rel | 业务库车辆-人员中间表 |
| cgdb | tc_vehicle_human | 业务库车辆人员表 |

---

## 4. 请求参数

### 4.1 顶层参数

| 参数路径 | 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|---|
| condition | condition | Object | 是 | 无 | 查询条件 |
| paging | paging | Object | 是 | 无 | 分页参数 |
| paging.pageIndex | pageIndex | Integer | 是 | 1 | 页码 |
| paging.pageSize | pageSize | Integer | 是 | 10 | 每页条数 |

### 4.2 condition 查询条件

| 参数路径 | 参数名 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
|---|---|---|---|---|---|---|
| condition.id | id | String | 否 | 无 |  | 车辆id |
| condition.ids | ids | String[] | 否 | 无 | `["xx","xx"]` | 多个车辆id |
| condition.vehicleNum | vehicleNum | String | 否 | 无 | 模糊查询 | 车牌号 |
| condition.vehicleUsage | vehicleUsage | String | 否 | 无 | 模糊查询 | 车辆用途 |
| condition.vehicleBrand | vehicleBrand | String | 否 | 无 | 模糊查询 | 车辆品牌 |
| condition.regionId | regionId | String | 否 | 无 |  | 区域id |
| condition.unitId | unitId | String | 否 | 无 |  | 部门id |
| condition.regionIdList | regionIdList | String[] | 否 | 无 | `["xx","xx"]` | 多个区域id |
| condition.unitIdList | unitIdList | String[] | 否 | 无 | `["xx","xx"]` | 多个部门id |
| condition.startWorkTime | startWorkTime | String | 否 | 无 |  | 开始工作时间 |
| condition.endWorkTime | endWorkTime | String | 否 | 无 |  | 结束工作时间 |
| condition.vehicleOwner | vehicleOwner | String | 否 | 无 |  | 车辆所属者/司机 |
| condition.onlineFlag | onlineFlag | Boolean | 否 | 无 |  | 车辆状态 |
| condition.telPhoneOwner | telPhoneOwner | String | 否 | 无 |  | 电话 |
| condition.vehicleTypeId | vehicleTypeId | String | 否 | 无 |  | 车辆类型 |
| condition.vehicleTypeIds | vehicleTypeIds | String[] | 否 | 无 | `["xx","xx"]` | 多个车辆类型 |
| condition.deleteFlag | deleteFlag | Boolean | 否 | 无 |  | 是否删除 |
| condition.validFlag | validFlag | Boolean | 否 | 无 |  | 是否有效 |
| condition.regionExtendFlag | regionExtendFlag | Boolean | 否 | 无 |  | 是否统计下级区划 |
| condition.unitExtendFlag | unitExtendFlag | Boolean | 否 | 无 |  | 是否统计下级部门 |
| condition.regionHigherFlag | regionHigherFlag | Boolean | 否 | 无 |  | 是否展示上级区划 |
| condition.unitHigherFlag | unitHigherFlag | Boolean | 否 | 无 |  | 是否展示上级部门 |
| condition.mediaFlag | mediaFlag | Boolean | 否 | 无 |  | 是否查询车辆图片 |
| condition.humanFlag | humanFlag | Boolean | 否 | 无 |  | 是否查询车辆人员 |

---

## 5. 请求示例

```json
{
  "condition": {
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
    "regionHigherFlag": "",
    "unitHigherFlag": "",
    "mediaFlag": "",
    "humanFlag": ""
  },
  "paging": {
    "pageIndex": 1,
    "pageSize": 10
  }
}
```

---

## 6. 返回字段

返回字段与车辆列表查询基本一致，额外重点关注 `totalCount`。

### 6.1 顶层字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 当前页车辆列表 | 分页表格 list |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 分页表格 total |

### 6.2 车辆主字段 result[]

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|---|
| result[].id | id | String | 是 | 车辆id |
| result[].unitId | unitId | String | 是 | 部门id |
| result[].vehicleNum | vehicleNum | String | 是 | 车牌号 |
| result[].simCardNum | simCardNum | String | 是 | sim号 |
| result[].vehicleUsage | vehicleUsage | String | 是 | 车辆用途 |
| result[].vehicleBrand | vehicleBrand | String | 是 | 车辆品牌 |
| result[].vehicleColor | vehicleColor | String | 是 | 车辆颜色 |
| result[].regionId | regionId | String | 是 | 区域id |
| result[].startWorkTime | startWorkTime | String | 是 | 开始工作时间 |
| result[].endWorkTime | endWorkTime | String | 是 | 结束工作时间 |
| result[].vehicleOwner | vehicleOwner | String | 是 | 车辆所有者 |
| result[].telPhoneOwner | telPhoneOwner | String | 是 | 电话 |
| result[].vehicleTypeId | vehicleTypeId | String | 是 | 车辆类型 |
| result[].onlineFlag | onlineFlag | Boolean | 是 | 车辆状态 |
| result[].deleteFlag | deleteFlag | Boolean | 是 | 是否删除 |
| result[].validFlag | validFlag | Boolean | 是 | 是否有效 |
| result[].vehicleRemarks | vehicleRemarks | String | 是 | 车辆备注 |
| result[].vehicleTypeName | vehicleTypeName | String | 是 | 车辆类型名称 |
| result[].address | address | String | 是 | 地址 |
| result[].speed | speed | Double | 是 | 车速 |
| result[].todayCourse | todayCourse | String | 是 | 里程数 |
| result[].consumption | consumption | String | 是 | 油耗 |
| result[].recordTime | recordTime | String | 是 | 记录时间 |
| result[].longitude | longitude | Double | 是 | 经度 |
| result[].latitude | latitude | Double | 是 | 纬度 |

### 6.3 嵌套对象

| 字段路径 | 类型 | 说明 |
|---|---|---|
| result[].vehiclePosList | Object[] | 车辆点位列表 |
| result[].vehicleType | Object | 车辆类型 |
| result[].region | Object | 区域 |
| result[].vehicleUnit | Object | 车辆单位 |
| result[].parentRegionList | Object[] | 父区域，regionHigherFlag 为 true 时返回 |
| result[].parentUnitList | Object[] | 父车辆单位，unitHigherFlag 为 true 时返回 |
| result[].vehicleHumanList | Object[] | 车辆人员，humanFlag 为 true 时返回 |
| result[].attachments | Object[] | 附件 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "id": "2",
      "unitId": "100540",
      "vehicleNum": "鄂A77H47",
      "simCardNum": "202104301115",
      "vehicleUsage": null,
      "vehicleBrand": "山西汽车",
      "vehicleColor": "绿色",
      "regionId": "1",
      "startWorkTime": null,
      "endWorkTime": null,
      "vehicleOwner": "欧超航",
      "telPhoneOwner": "15137100888",
      "vehicleTypeId": "5",
      "onlineFlag": false,
      "deleteFlag": false,
      "validFlag": true,
      "vehicleRemarks": null,
      "vehicleTypeName": "垃圾车",
      "address": null,
      "speed": 20.08,
      "todayCourse": null,
      "consumption": null,
      "recordTime": "2021-06-07 13:37:30",
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
| 其他报错 | 需联系后台排查数据 | 检查请求参数、分页参数、数据权限、后台日志 |

---

## 9. 适配建议

### 适合组件

- 分页表格；
- 车辆管理列表；
- 大数据量车辆列表；
- 支持翻页的车辆清单。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| list | data.result | 数组兜底 |
| total | data.totalCount | Number 转换 |
| vehicleNum | item.vehicleNum | 字符串兜底 |
| vehicleTypeName | item.vehicleTypeName | 字符串兜底 |
| onlineStatus | item.onlineFlag | true/false 转在线/离线 |

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
            return {
                id: item.id || '',
                vehicleNum: item.vehicleNum || '',
                vehicleTypeName: item.vehicleTypeName || '',
                vehicleBrand: item.vehicleBrand || '',
                vehicleColor: item.vehicleColor || '',
                unitName: item.vehicleUnit && item.vehicleUnit.unitName || '',
                regionName: item.region && item.region.regionName || '',
                onlineStatus: item.onlineFlag === true ? '在线' : '离线',
                recordTime: item.recordTime || ''
            };
        }),
        total: Number(data.totalCount || 0)
    };
}
```

---

## 10. 性能和联调注意点

1. 分页接口必须传 `condition` 和 `paging`。
2. `paging.pageIndex` 和 `paging.pageSize` 是必填字段。
3. 如果与车辆总数接口配套，`condition` 应保持一致。
4. 不需要上级区划、上级部门、人员、图片时，不要开启对应 flag。
5. 分页表格如果只传入 `result` 本体，将无法拿到 `totalCount`。