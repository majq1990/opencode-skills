# 车辆列表查询

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | VEHICLE_LIST |
| domain | 城管车辆 |
| bizObject | 车辆 |
| apiName | 车辆列表查询 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/vehicle/list` |
| 星桥接口路径地址 | `API平台/悟能接口/车辆相关/车辆列表查询` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 表格、详情入口、车辆完整列表 |

---

## 2. 接口说明

该接口用于按指定查询条件查询车辆列表。

基础条件查询会查出：

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

通过传参方式可以配置是否查出：

- 上级部门信息；
- 上级区划信息；
- 车辆关联人员等。

支持通过以下条件筛选：

- 车辆主键；
- 车辆主键列表；
- 车牌号；
- 区划；
- 部门；
- 车辆状态；
- 车辆类型等。

支持区划深钻：

- 通过区划过滤时，如果车辆属于该区划下属区划，也可以认为车辆属于当前区划；
- 由 `regionExtendFlag` 控制。

支持部门深钻：

- 通过部门过滤时，如果车辆属于该部门下属部门，也可以认为车辆属于当前部门；
- 由 `unitExtendFlag` 控制。

适合：

- 车辆完整表格；
- 条件筛选后的车辆列表；
- 车辆详情入口；
- 需要字段较全的列表展示。

不适合：

- 不加条件直接展示全部车辆；
- 地图高频点位打点；
- 指标总数；
- 分类统计图表。

> 注意：该接口单个对象会返回大量信息，直接查询全部车辆数据量很大，网络传输会慢。展示所有车辆建议使用分页查询或车辆简要列表查询。

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
| regionExtendFlag | regionExtendFlag | Boolean | 否 | 无 |  | 是否统计下级区划 |
| unitExtendFlag | unitExtendFlag | Boolean | 否 | 无 |  | 是否统计下级部门 |
| regionHigherFlag | regionHigherFlag | Boolean | 否 | 无 |  | 是否展示上级区划 |
| unitHigherFlag | unitHigherFlag | Boolean | 否 | 无 |  | 是否展示上级部门 |
| humanFlag | humanFlag | String | 否 | 无 |  | 是否查询车辆人员 |
| mediaFlag | mediaFlag | String | 否 | 无 |  | 是否查询车辆图片 |

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
  "regionHigherFlag": "",
  "unitHigherFlag": "",
  "mediaFlag": "",
  "humanFlag": ""
}
```

---

## 6. 返回字段

### 6.1 顶层字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 车辆列表 | 表格/list 数据源 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 列表总数 |

### 6.2 车辆主字段 result[]

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| result[].id | id | String | 是 | 车辆id | id |
| result[].unitId | unitId | String | 是 | 部门id | 部门筛选/联动 |
| result[].vehicleNum | vehicleNum | String | 是 | 车牌号 | 表格列/名称 |
| result[].simCardNum | simCardNum | String | 是 | sim号 | 设备标识 |
| result[].vehicleUsage | vehicleUsage | String | 是 | 车辆用途 | 表格列 |
| result[].vehicleBrand | vehicleBrand | String | 是 | 车辆品牌 | 表格列 |
| result[].vehicleColor | vehicleColor | String | 是 | 车辆颜色 | 表格列 |
| result[].regionId | regionId | String | 是 | 区域id | 区域筛选/联动 |
| result[].startWorkTime | startWorkTime | String | 是 | 开始工作时间 | 表格列 |
| result[].endWorkTime | endWorkTime | String | 是 | 结束工作时间 | 表格列 |
| result[].vehicleOwner | vehicleOwner | String | 是 | 车辆所有者/司机 | 表格列 |
| result[].telPhoneOwner | telPhoneOwner | String | 是 | 电话 | 表格列 |
| result[].vehicleTypeId | vehicleTypeId | String | 是 | 车辆类型id | 类型筛选/联动 |
| result[].onlineFlag | onlineFlag | Boolean | 是 | 车辆状态 | 在线/离线 |
| result[].deleteFlag | deleteFlag | Boolean | 是 | 是否删除 | 通常不展示 |
| result[].validFlag | validFlag | Boolean | 是 | 是否有效 | 通常不展示 |
| result[].vehicleRemarks | vehicleRemarks | String | 是 | 车辆备注 | 表格列/详情 |
| result[].vehicleTypeName | vehicleTypeName | String | 是 | 车辆类型名称 | 表格列 |
| result[].address | address | String | 是 | 地址 | 表格列/地图弹窗 |
| result[].speed | speed | Double | 是 | 车速 | 表格列 |
| result[].todayCourse | todayCourse | String | 是 | 里程数 | 表格列 |
| result[].consumption | consumption | String | 是 | 油耗 | 表格列 |
| result[].recordTime | recordTime | String | 是 | 记录时间 | 表格列 |
| result[].longitude | longitude | Double | 是 | 经度 | 地图 lng |
| result[].latitude | latitude | Double | 是 | 纬度 | 地图 lat |
| result[].attachments | attachments | Object[] | 是 | 附件 | 图片/附件 |

### 6.3 车辆点位 vehiclePosList[]

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|---|
| result[].vehiclePosList[].id | id | String | 是 | 车辆点位id/sim |
| result[].vehiclePosList[].latitude | latitude | Double | 是 | 纬度 |
| result[].vehiclePosList[].longitude | longitude | Double | 是 | 经度 |
| result[].vehiclePosList[].speed | speed | Double | 是 | 车速 |
| result[].vehiclePosList[].todayCourse | todayCourse | Double | 是 | 今日路程 |
| result[].vehiclePosList[].totalCourse | totalCourse | Double | 是 | 总路程 |
| result[].vehiclePosList[].consumption | consumption | Double | 是 | 瞬时油耗 |
| result[].vehiclePosList[].recordTime | recordTime | String | 是 | 记录时间 |
| result[].vehiclePosList[].uploadTime | uploadTime | String | 是 | 上传时间 |

### 6.4 车辆类型 vehicleType

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|---|
| result[].vehicleType.id | id | String | 是 | 车辆类型id |
| result[].vehicleType.vehicleTypeName | vehicleTypeName | String | 是 | 车辆类型名称 |

### 6.5 区域 region

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|---|
| result[].region.id | id | String | 是 | 区域id |
| result[].region.regionCode | regionCode | String | 是 | 区域编码 |
| result[].region.longitude | longitude | Double | 是 | 经度 |
| result[].region.latitude | latitude | Double | 是 | 纬度 |
| result[].region.regionName | regionName | String | 是 | 区域名称 |
| result[].region.regionType | regionType | Integer | 是 | 区域类型 |
| result[].region.parentId | parentId | String | 是 | 父级区域id |
| result[].region.validFlag | validFlag | Boolean/String | 是 | 逻辑删除字段 |

### 6.6 车辆单位 vehicleUnit

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|---|
| result[].vehicleUnit.id | id | String | 是 | 单位id |
| result[].vehicleUnit.unitName | unitName | String | 是 | 单位名称 |
| result[].vehicleUnit.unitDesc | unitDesc | String | 是 | 单位描述 |
| result[].vehicleUnit.seniorId | seniorId | String | 是 | 上级单位标识 |
| result[].vehicleUnit.regionId | regionId | String | 是 | 所属区域标识 |
| result[].vehicleUnit.regionType | regionType | String | 是 | 所属区域类型 |
| result[].vehicleUnit.unitTypeId | unitTypeId | String | 是 | 单位类型标识 |
| result[].vehicleUnit.unitTypeName | unitTypeName | String | 是 | 单位类型名称 |
| result[].vehicleUnit.validFlag | validFlag | Boolean | 是 | 有效标识 |
| result[].vehicleUnit.address | address | String | 是 | 地址 |
| result[].vehicleUnit.officeTel | officeTel | String | 是 | 办公电话 |
| result[].vehicleUnit.remark | remark | String | 是 | 备注 |
| result[].vehicleUnit.principal | principal | String | 是 | 负责人 |
| result[].vehicleUnit.principalContact | principalContact | String | 是 | 负责人电话 |
| result[].vehicleUnit.x | x | Double | 是 | x 坐标 |
| result[].vehicleUnit.y | y | Double | 是 | y 坐标 |

### 6.7 可选扩展字段

| 字段路径 | 字段名 | 类型 | 出现条件 | 字段说明 |
|---|---|---|---|---|
| result[].parentRegionList | parentRegionList | Object[] | regionHigherFlag 为 true | 父区域列表 |
| result[].parentUnitList | parentUnitList | Object[] | unitHigherFlag 为 true | 父车辆单位列表 |
| result[].vehicleHumanList | vehicleHumanList | Object[] | humanFlag 为 true | 车辆关联人员 |

### 6.8 车辆人员 vehicleHumanList[]

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 |
|---|---|---|---|---|
| result[].vehicleHumanList[].id | id | String | 否 | 人员主键 |
| result[].vehicleHumanList[].code | code | String | 否 | 人员编码 |
| result[].vehicleHumanList[].name | name | String | 否 | 人员名称 |
| result[].vehicleHumanList[].desc | desc | String | 否 | 人员描述 |
| result[].vehicleHumanList[].humanCategoryId | humanCategoryId | String | 否 | 人员类别标识 |
| result[].vehicleHumanList[].idCard | idCard | String | 否 | 人员卡号 |
| result[].vehicleHumanList[].genderId | genderId | Integer | 否 | 性别，1 男，2 女 |
| result[].vehicleHumanList[].unitId | unitId | String | 否 | 人员所属部门主键 |
| result[].vehicleHumanList[].unitName | unitName | String | 否 | 人员所属部门名称 |
| result[].vehicleHumanList[].mobile | mobile | String | 否 | 电话号码 |
| result[].vehicleHumanList[].address | address | String | 否 | 人员地址 |
| result[].vehicleHumanList[].misHumanId | misHumanId | String | 否 | 城管人员id |

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
      "vehiclePosList": [
        {
          "id": "202104301115",
          "latitude": 3542300.5,
          "longitude": 12738779,
          "speed": 20.08,
          "todayCourse": null,
          "totalCourse": null,
          "consumption": null,
          "recordTime": "2021-06-07 13:37:30",
          "uploadTime": "2021-06-07 13:37:30"
        }
      ],
      "vehicleType": {
        "id": "5",
        "vehicleTypeName": "垃圾车"
      },
      "region": {
        "id": "1",
        "regionCode": "330302",
        "longitude": 120.592180578154,
        "latitude": 28.0645365021072,
        "regionName": "鹿城区",
        "regionType": 2,
        "parentId": "0",
        "validFlag": "1",
        "children": []
      },
      "vehicleUnit": {
        "id": "100540",
        "unitName": "恒旺渣土运输有限公司",
        "unitDesc": "",
        "seniorId": "0",
        "regionId": "0",
        "regionType": 1,
        "unitTypeId": null,
        "unitTypeName": null,
        "validFlag": true,
        "address": "无位置描述",
        "officeTel": "",
        "remark": null,
        "principal": "荆松",
        "principalContact": "18521383333",
        "x": null,
        "y": null,
        "count": null
      },
      "longitude": 12738779,
      "latitude": 3542300.5,
      "parentRegionList": null,
      "parentUnitList": null,
      "vehicleHumanList": null,
      "attachments": null
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
- 车辆完整列表；
- 详情入口列表；
- 条件筛选车辆列表。

### 字段映射建议：普通表格

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.id | 字符串兜底 |
| vehicleNum | item.vehicleNum | 字符串兜底 |
| vehicleTypeName | item.vehicleTypeName | 字符串兜底 |
| vehicleBrand | item.vehicleBrand | 字符串兜底 |
| vehicleColor | item.vehicleColor | 字符串兜底 |
| unitName | item.vehicleUnit.unitName | 对象判空 |
| regionName | item.region.regionName | 对象判空 |
| onlineStatus | item.onlineFlag | true/false 转在线/离线 |
| longitude | item.longitude | Number 转换 |
| latitude | item.latitude | Number 转换 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            id: item.id || '',
            vehicleNum: item.vehicleNum || '',
            vehicleTypeName: item.vehicleTypeName || '',
            vehicleBrand: item.vehicleBrand || '',
            vehicleColor: item.vehicleColor || '',
            unitName: item.vehicleUnit && item.vehicleUnit.unitName || '',
            regionName: item.region && item.region.regionName || '',
            onlineStatus: item.onlineFlag === true ? '在线' : '离线',
            longitude: Number(item.longitude || 0),
            latitude: Number(item.latitude || 0),
            recordTime: item.recordTime || ''
        };
    });
}
```

### 地图点位过滤脚本：data 为 result 本体

如果列表查询返回字段用于地图打点，可用：

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
            unitName: item.vehicleUnit && item.vehicleUnit.unitName || '',
            regionName: item.region && item.region.regionName || '',
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

1. 该接口返回字段很多，不建议无条件查询全量车辆。
2. 展示全部车辆时建议使用车辆分页查询。
3. 地图打点优先使用车辆简要列表查询。
4. `regionHigherFlag`、`unitHigherFlag`、`humanFlag` 等扩展开关会增加查询成本，按需开启。
5. 表格列较少时，不要直接把完整对象全部透传到组件。