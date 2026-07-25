# 资源简要列表

## 1. 标准化基本信息

| 项目 | 内容 |
| --- | --- |
| apiCode | AGG_RANGE_SIMPLE_LIST |
| domain | 汇聚周边搜索 |
| bizObject | 周边资源 |
| apiName | 资源简要列表 |
| apiType | simple_list |
| 请求方式 | POST |
| 接口地址 | `/api/mixture/range/simple/list` |
| 星桥接口路径地址 | API平台/悟能接口/汇聚接口/周边搜索/资源简要列表 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | object |
| 适配组件 | 地图点位,图层打点,周边资源列表 |
| 原始文档 | docs/汇聚接口/周边搜索/3.资源简要列表.docx |

---

## 2. 接口说明

该接口用于按中心点经纬度和半径查询周边资源简要列表，适合图层打点。v22 当前启用的简要列表分支为案件、人员和视频设备；车辆分支未启用，城管视频分支未在简要列表中实现。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| cgdbstat | to_stat_info | 统计库案件表 |
| cgdb | tc_patrol | 业务库监督员表 |
| cgdb | tc_human | 业务库人员表 |
| cgdb | tc_patrol_type | 业务库监督员类型字典表 |
| cgdb | tc_region | 业务库区划表 |
| cgdb | tc_patrol_state | 业务库监督员状态表 |
| video | video_device | 视频中台库视频设备表 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| searchAroundRequest | Object | 是 |  |  | 中心点范围查询资源 |
| +geoInfo | Object | 是 |  |  | 中心点范围 |
| ++latitude | Double | 是 |  |  | 中心点纬度 |
| ++longitude | Double | 是 |  |  | 中心点经度 |
| ++radius | Double | 是 |  |  | 圆心半径 |
| +keys | String[] | 是 |  |  | 查询资源类型；v22 简要列表支持 `records`:案件、`patrol`:人员、`video`:视频设备；`vehicle` 和 `tcvideo` 当前未启用 |
| toStatInfoCondition | Object | 是 |  |  | 案件查询条件 |
| +ids | String[] | 否 |  |  | 该参数表示查询案件主键在ids列表中的案件信息 |
| +startCreateTime | String | 否 | 当前时间减去30天的当天0时0分0秒 | 格式：yyyy-MM-dd HH:mm:ss | 统计指标的开始时间 |
| +endCreateTime | String | 否 | 当天23时59分59秒 | 格式：yyyy-MM-dd HH:mm:ss | 统计指标的结束时间 |
| +taskNum | String | 否 |  |  | 该参数表示查询案件任务号为taskNum的案件信息 |
| +taskNos | String[] | 否 |  |  | 该参数表示查询案件任务号在taskNos列表中的案件信息 |
| +bizId | Integer | 否 |  |  | 该参数表示查询案件业务标识为bizId的案件信息 |
| +dutyGridId | String | 否 |  |  | 该参数表示查询指定责任网格的案件信息 |
| +dutyGridIds | String[] | 否 |  |  | 该参数表示查询指定责任网格的案件信息 |
| +excludeDutyGridIds | String[] | 否 |  |  | 该参数表示查询不在指定责任网格的案件信息 |
| +cellId | String | 否 |  |  | 该参数表示查询指定单元网格的案件信息 |
| +cellIds | String[] | 否 |  |  | 该参数表示查询指定单元网格的案件信息 |
| +excludeCellIds | String[] | 否 |  |  | 该参数表示查询不在指定单元网格的案件信息 |
| +communityId | String | 否 |  |  | 该参数表示查询指定社区的案件信息 |
| +communityIds | String[] | 否 |  |  | 该参数表示查询指定社区的案件信息 |
| +excludeCommunityIds | String[] | 否 |  |  | 该参数表示查询不在指定社区的案件信息 |
| +streetId | String | 否 |  |  | 该参数表示查询指定街道的案件信息 |
| +streetIds | String[] | 否 |  |  | 该参数表示查询指定街道的案件信息 |
| +excludeStreetIds | String[] | 否 |  |  | 该参数表示查询不在指定街道的案件信息 |
| +districtId | String | 否 |  |  | 该参数表示查询指定区县的案件信息 |
| +districtIds | String[] | 否 |  |  | 该参数表示查询指定区县的案件信息 |
| +excludeDistrictIds | String[] | 否 |  |  | 该参数表示查询不在指定区县的案件信息 |
| +cityId | Integer | 否 |  |  | 该参数表示查询指定市的案件信息 |
| +eventSrcId | String | 否 |  |  | 该参数表示查询指定案件来源的案件信息 |
| +eventSrcIds | String[] | 否 |  |  | 该参数表示查询指定案件来源的案件信息 |
| +excludeEventSrcIds | String[] | 否 |  |  | 该参数表示查询排除指定案件来源的案件信息 |
| +eventTypeId | String | 否 |  |  | 该参数表示查询指定问题类型的案件信息 |
| +notEventTypeId | String | 否 |  |  | 该参数表示查询排除指定问题类型的案件信息 |
| +eventTypeIds | String[] | 否 |  |  | 该参数表示查询指定问题类型的案件信息 |
| +excludeEventTypeIds | String[] | 否 |  |  | 该参数表示查询排除指定问题类型的案件信息 |
| +mainTypeId | String | 否 |  |  | 该参数表示查询指定问题大类的案件信息 |
| +mainTypeIds | String[] | 否 |  |  | 该参数表示查询指定问题大类的案件信息 |
| +excludeMainTypeIds | String[] | 否 |  |  | 该参数表示查询排除指定问题大类的案件信息 |
| +subTypeId | String | 否 |  |  | 该参数表示查询指定问题小类的案件信息 |
| +subTypeIds | String[] | 否 |  |  | 该参数表示查询指定问题小类的案件信息 |
| +excludeSubTypeIds | String[] | 否 |  |  | 该参数表示查询排除指定问题小类的案件信息 |
| +recTypeId | Integer | 否 |  |  | 该参数表示查询指定案件类型的案件信息 |
| +reportNum | Integer | 否 |  |  | 该字段传1代表查询已上报的案件信息 |
| +disposeNum | Integer | 否 |  |  | 该字段传1代表查询已处置的案件信息 |
| +toDisposeNum | Integer | 否 |  |  | 该字段传1代表查询未处置的案件信息 |
| +operateNum | Integer | 否 |  |  | 该字段传1代表查询已受理的案件信息 |
| +instNum | Integer | 否 |  |  | 该字段传1代表查询已立案的案件信息 |
| +overtimeArchiveNum | Integer | 否 |  |  | 该字段传1代表查询超期结案的案件信息 |
| +overtimeToDisposeNum | Integer | 否 |  |  | 该字段传1代表查询超期未处置的案件信息 |
| +dispatchNum | Integer | 否 |  |  | 该字段传1代表查询已派遣的案件信息 |
| +archiveNum | Integer | 否 |  |  | 该字段传1代表查询已结案的案件信息 |
| +needArchiveNum | Integer | 否 |  |  | 该字段传1代表查询应结案的案件信息 |
| +intimeArchiveNum | Integer | 否 |  |  | 该字段传1代表查询按期结案的案件信息 |
| +intimeDisposeNum | Integer | 否 |  |  | 该字段传1代表查询按期处置的案件信息 |
| +accurDispatchNum | Integer | 否 |  |  | 该字段传1代表查询准确派遣的案件信息 |
| +overtimeDisposeNum | Integer | 否 |  |  | 该字段传1代表查询超期处置的案件信息 |
| +intimeInstNum | Integer | 否 |  |  | 该字段传1代表查询按时立案的案件信息 |
| +patrolDealFlag | Integer | 否 |  |  | 该字段传1代表查询自行处置的案件信息 |
| +intimeCheckNum | Integer | 否 |  |  | 该字段传1代表查询按期核查的案件信息 |
| +intimeDispatchNum | Integer | 否 |  |  | 该字段传1代表查询按期派遣的案件信息 |
| +intimeOperateNum | Integer | 否 |  |  | 该字段传1代表查询按时受理的案件信息 |
| +reworkNum | Integer | 否 |  |  | 该字段传1代表查询返工的案件信息 |
| +reportPatrolId | String | 否 |  |  | 该字段表示查询指定监督员上报的案件 |
| +disposeUnitId | String | 否 |  |  | 该字段表示查询指定部门处置的案件 |
| +instHumanId | Integer | 否 |  |  | 该字段表示查询指定人员立案的案件 |
| +archiveHumanId | String | 否 |  |  | 该字段表示查询指定人员结案的案件 |
| +operateHumanId | Integer | 否 |  |  | 该字段表示查询指定人员受理的案件 |
| +checkPatrolId | String | 否 |  |  | 该字段表示查询指定人员核查的案件 |
| +dispatchHumanId | String | 否 |  |  | 该字段表示查询指定派遣人员的案件 |
| +eventStateId | Integer | 否 |  |  | 该字段表示查询指定案件阶段的案件，其中：1：待受理3：立案派遣4：处理中5：核查结案6：结案7：作废8：挂账9：督查 |
| +excludeEventStateId | Integer | 否 |  |  | 该字段表示查询不在指定案件阶段的案件 |
| +searchKeyword | Object | 否 |  |  | 用于关键字模糊查询 |
| ++taskNum | String | 否 |  |  | 该字段表示模糊查询任务号 |
| ++eventDesc | String | 否 |  |  | 该字段表示模糊查询案件描述 |
| ++address | String | 否 |  |  | 该字段表示模糊查询地址 |
| patrolCondition | Object | 是 |  |  | 人员查询条件 |
| +id | String | 否 |  |  | 人员主键 |
| +ids | String[] | 否 |  |  | 人员主键列表 |
| +cardId | String | 否 |  |  | 卡号 |
| +patrolCode | String | 否 |  |  | 人员编码 |
| +patrolName | String | 否 |  |  | 模糊查询人员名称 |
| +patrolTypeId | String | 否 |  |  | 人员类型 |
| +regionId | String | 否 |  |  | 指定所属区划 |
| +regionExtendFlag | Boolean | 否 | false |  | 是否支持区划下钻，即通过区划过滤时，当该人员属于该区划下属的区划时，我们认为该人员也属于这个区划。 |
| +regionIdList | String[] | 否 |  |  | 指定所属区划列表 |
| +unitId | String | 否 |  |  | 指定所属部门 |
| +unitExtendFlag | Boolean | 否 |  |  | 是否支持部门下钻，即通过部门过滤时，当该人员属于该部门下属的区划时，我们认为该人员也属于这个部门。 |
| +state | Boolean | 否 |  |  | 是否在线 |
| vehicleCondition | Object | 否 |  |  | 车辆查询条件；v22 当前简要列表车辆分支未启用 |
| +id | String | 否 | 无 |  | 车辆id |
| +ids | String[] | 否 | 无 | ["xx","xx"] | 多个车辆id |
| +vehicleNum | String | 否 | 无 | 模糊查询 | 车牌号 |
| +vehicleUsage | String | 否 | 无 | 模糊查询 | 车辆用途 |
| +vehicleBrand | String | 否 | 无 | 模糊查询 | 车辆品牌 |
| +regionId | String | 否 | 无 |  | 区域id |
| +unitId | String | 否 | 无 |  | 部门id |
| +regionIdList | String[] | 否 | 无 | ["xx","xx"] | 多个区域id |
| +unitIdList | String[] | 否 | 无 | ["xx","xx"] | 部门id |
| +startWorkTime | String | 否 | 无 |  | 开始工作时间 |
| +endWorkTime | String | 否 | 无 |  | 结束工作时间 |
| +vehicleOwner | String | 否 | 无 |  | 车辆所属者 司机 |
| +onlineFlag | Boolean | 否 | 无 |  | 车辆状态 |
| +telPhoneOwner | String | 否 | 无 |  | 电话 |
| +vehicleTypeId | String | 否 | 无 |  | 车辆类型 |
| +vehicleTypeIds | String[] | 否 | 无 | ["xx","xx"] | 多个车辆类型 |
| +deleteFlag | Boolean | 否 | 无 |  | 是否删除 |
| +validFlag | Boolean | 否 | 无 |  | 是否有效 |
| +regionExtendFlag | Boolean | 否 | 无 |  | 是否统计下级区划 |
| +unitExtendFlag | Boolean | 否 | 无 |  | 是否统计下级部门 |
| videoDevicePageCondition | Object | 否 |  |  | 视频设备分页查询条件，`keys` 包含 `video` 时生效 |
| +condition | Object | 否 |  |  | 视频设备过滤条件，字段同视频设备查询条件 |
| +pageSize | Integer | 否 |  |  | 每页条数 |
| +pageNo | Integer | 否 |  |  | 页码 |
| videoDeviceCondition | Object | 否 |  |  | 视频设备非分页条件，简要列表当前主要使用 `videoDevicePageCondition` |
| +id | String | 否 | 无 |  | 视频表主键 |
| +name | String | 否 | 无 | 模糊查询 | 视频名称 |
| +type | String | 否 | 无 |  | 设备类型 |
| +status | String | 否 | 无 | 1表示在线0表示离线 | 设备状态 |
| +videoType | String | 否 | 无 |  | 视频类型 |

---

## 5. 请求示例

```json
{
  "searchAroundRequest": {
    "geoInfo": {
      "longitude": 120.69843166666666,
      "latitude": 27.999376666666663,
      "radius": 100
    },
    "keys": [
      "records",
      "patrol",
      "video"
    ]
  },
  "toStatInfoCondition": {},
  "patrolCondition": {
    "top": 10000
  },
  "videoDevicePageCondition": {"condition": {}, "pageNo": 1, "pageSize": 100}
}
```

---

## 6. 返回字段

- `result` 类型：`Object`
- 标准化响应形态：`object`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回结果 |
| +recordsList | Object[] | 是 |  | 案件列表 |
| ++xxx | String | 是 |  | 取决于com_option表里主键为10001的数据的value字段，该字段的一般配置为：[{    "rec_id": "id",    "task_num": "taskNum",    "coordinate_x": "longitude ",    "coordinate_y":"latitude",      "address":"address",      "event_desc":"eventDesc","event_type_name":"eventTypeName","main_type_name":"mainTypeName","sub_type_name":"subTypeName","event_state_name":"eventStateName"}]展示的字段即为value值，更详细描述见城管接口文档-案件接口-案件简要列表 |
| +vehicleList | Object[] | 否 |  | 车辆列表；v22 当前简要列表车辆分支未启用，通常不会返回 |
| ++id | String | 是 |  | 车辆id |
| ++simCardNum | String | 是 |  | sim号 |
| ++vehicleNum | String | 是 |  | 车牌号 |
| ++unitId | String | 是 |  | 部门id |
| ++unitName | String | 是 |  | 部门名称 |
| ++vehicleTypeId | String | 是 |  | 车辆类型 |
| ++vehicleTypeId | String | 是 |  | 车辆类型id |
| ++vehicleTypeName | String | 是 |  | 车辆类型名称 |
| ++regionId | String | 是 |  | 区域id |
| ++regionName | String | 是 |  | 区域名称 |
| ++onlineFlag | Boolean | 是 |  | 车辆状态 |
| ++longitude | Double | 是 |  | 经度 |
| ++latitude | Double | 是 |  | 纬度 |
| videoList | Object[] | 是 |  | 视频列表 |
| ++id | String | 是 |  | 设备id |
| ++name | String | 是 |  | 设备名称 |
| ++manufacturerId | String | 是 |  | 生产厂商 |
| ++contractorId | String | 是 |  | 建设厂商 |
| ++type | String | 是 |  | 设备类型 |
| ++departmentId | String | 是 |  | 所属单位的Id |
| ++url | String | 是 |  | url |
| ++status | String | 是 |  | 状态 |
| ++longitude | String | 是 |  | 经度 |
| ++latitude | String | 是 |  | 纬度 |
| ++lastActiveTime | String | 是 |  | 最近活跃时间 |
| ++disabled | Boolean | 是 |  | 是否禁用 逻辑删除 |
| ++videoType | String | 是 |  | 视频类型 |
| ++location | String | 是 |  | 视频地址 |
| +patrolList | Object[] | 是 |  | 人员列表 |
| ++id | String | 是 |  | 人员id |
| ++cardId | String | 是 |  | 岗位名称 |
| ++patrolCode | String | 是 |  | 人员代码 |
| ++patrolName | String | 是 |  | 人员名称 |
| ++patrolTypeId | String | 是 |  | 人员类型id |
| ++patrolTypeName | String | 是 |  | 人员类型 |
| ++regionId | String | 是 |  | 区域id |
| ++regionName | String | 是 |  | 区域 |
| ++onlineFlag | Boolean | 是 |  | 是否在线 |
| ++longitude | Double | 是 |  | 经度 |
| ++latitude | Double | 是 |  | 纬度 |
| message | String | 是 |  | 当hasError为true时这里展示报错信息 |
| tag | / | 是 |  | 未使用到 |
| totalCount | Integer | 是 |  | 返回数据的总条数 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": {
    "recordsList": [
      {
        "eventStateName": "结案",
        "subTypeName": "通信井盖",
        "eventDesc": "联通路与西七路路口西230米左右。路北。中国银行门前绿化带联通井盖移位。",
        "address": "淄博市张店区联通路116中国银行淄博新区支行(西南9米)",
        "mainTypeName": "公用设施",
        "latitude": 36.829441,
        "eventTypeName": "部件",
        "id": 359343,
        "taskNum": "202207130954",
        "longitude": 118.013077
      }
    ],
    "videoList": [
      {
        "id": "1012345678900",
        "name": "1012345678900",
        "manufacturerId": null,
        "contractorId": null,
        "type": "E1",
        "departmentId": null,
        "url": null,
        "status": null,
        "longitude": null,
        "latitude": null,
        "lastActiveTime": null,
        "disabled": true,
        "location": null,
        "distance": 0,
        "catalogId": "101"
      }
    ],
    "patrolList": [
      {
        "id": "100423",
        "cardId": "100001",
        "patrolCode": "100423",
        "patrolName": "智信测试01",
        "patrolTypeId": "3",
        "patrolTypeName": "视频监督员",
        "regionId": "0",
        "regionName": "淄博市",
        "onlineFlag": false,
        "longitude": 118.01227773589542,
        "latitude": 36.8299940138552
      }
    ]
  },
  "message": null,
  "tag": null,
  "totalCount": 1
}
```

---

## 8. 报错说明

| message信息 | 说明 |
| --- | --- |
| 请传入正确的周边搜索参数! | 需检查searchAroundRequest传参 |
| 请传入正确的地理范围参数! | 需检查geoInfo传参 |
| 需要统计的资源指标为空！ | 需检查keys传参 |
| 获取数据失败! | 需联系后台排查数据 |
| 其他报错 | 需联系后台排查数据 |

---

## 9. 字段转换建议

- `filter(data)` 默认接收外层响应的 `result` 本体；只有现场明确传入完整外层响应包时，才读取 `data.result` 或 `data.totalCount`。
- 周边搜索必须确认 `geoInfo.longitude`、`geoInfo.latitude`、`geoInfo.radius` 和 `keys`；v22 简要列表支持 `records`、`patrol`、`video`，不建议传 `vehicle` 或 `tcvideo`。
- 如果用于地图点位，需确认坐标系和组件静态数据模板；如组件字段与接口字段不同，再按返回字段做映射。
