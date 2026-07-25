# 资源列表

## 1. 标准化基本信息

| 项目 | 内容 |
| --- | --- |
| apiCode | AGG_RANGE_LIST |
| domain | 汇聚周边搜索 |
| bizObject | 周边资源 |
| apiName | 资源列表 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/mixture/range/list` |
| 星桥接口路径地址 | API平台/悟能接口/汇聚接口/周边搜索/资源列表 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | object |
| 适配组件 | 资源列表,表格,地图弹窗,详情入口 |
| 原始文档 | docs/汇聚接口/周边搜索/2.资源列表.docx |

---

## 2. 接口说明

该接口用于按中心点经纬度和半径查询周边资源完整列表。v22 当前启用的列表分支为案件、人员、视频设备和城管视频；车辆分支在当前源码中未启用，`keys` 传 `vehicle` 会返回“暂不支持该资源周边查询”。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| cgdbstat | to_stat_info | 统计库案件表 |
| cgdbstat | to_media | 统计库附件表 |
| cgdb | to_media | 业务库附件表 |
| cgdb | to_his_media | 业务库历史附件表 |
| cgdb | tc_patrol | 业务库监督员表 |
| cgdb | tc_human | 业务库人员表 |
| cgdb | tc_patrol_type | 业务库监督员类型字典表 |
| cgdb | tc_patrol_state | 业务库监督员状态表 |
| cgdb | tc_duty_grid_patrol | 业务库责任网格-人员中间表 |
| cgdb | tc_duty_grid | 业务库责任网格表 |
| cgdb | tc_unit | 业务库部门表 |
| video | video_device | 视频中台库视频设备表 |
| video | video_cell | 城管视频表，表名按 `VideoCellFacade` 资源推断，需现场核对实际库表 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| searchAroundRequest | Object | 是 |  |  | 中心点范围查询资源 |
| +geoInfo | Object | 是 |  |  | 中心点范围 |
| ++latitude | Double | 是 |  |  | 中心点纬度 |
| ++longitude | Double | 是 |  |  | 中心点经度 |
| ++radius | Double | 是 |  |  | 圆心半径 |
| +keys | String[] | 是 |  |  | 查询资源类型；v22 列表支持 `records`:案件、`patrol`:人员、`video`:视频设备、`tcvideo`:城管视频；`vehicle`:车辆当前未启用 |
| toStatInfoPageCondition | Object | 否 |  |  | 案件分页查询条件，`keys` 包含 `records` 时生效 |
| +condition | Object | 否 |  |  | 案件过滤条件，字段同案件查询条件 |
| +pageSize | Integer | 否 |  |  | 每页条数 |
| +pageNo | Integer | 否 |  |  | 页码 |
| toStatInfoCondition | Object | 否 |  |  | 案件非分页条件，完整列表接口当前主要使用 `toStatInfoPageCondition` |
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
| patrolPageCondition | Object | 否 |  |  | 人员分页查询条件，`keys` 包含 `patrol` 时生效 |
| +condition | Object | 否 |  |  | 人员过滤条件，字段同人员查询条件 |
| +pageSize | Integer | 否 |  |  | 每页条数 |
| +pageNo | Integer | 否 |  |  | 页码 |
| patrolCondition | Object | 否 |  |  | 人员非分页条件，完整列表接口当前主要使用 `patrolPageCondition` |
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
| +regionHigherFlag | Boolean | 否 | false |  | 是否展示上级区划 |
| unitHigherFlag | Boolean | 否 | false |  | 是否展示上级部门 |
| +dutyCellFlag | Boolean | 否 | false |  | 是否统计责任网格 |
| +attachmentFlag | Boolean | 否 | false |  | 是否查询人员头像 |
| vehiclePageCondition | Object | 否 |  |  | 车辆分页查询条件；v22 当前车辆列表分支未启用 |
| vehicleCondition | Object | 否 |  |  | 车辆查询条件；v22 当前车辆列表分支未启用 |
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
| +regionHigherFlag | Boolean | 否 | 无 |  | 是否展示上级区划 |
| +unitHigherFlag | Boolean | 否 | 无 |  | 是否展示上级部门 |
| +mediaFlag | Boolean | 否 | 无 |  | 是否查询车辆图片 |
| +humanFlag | Boolean | 否 | 无 |  | 是否查询车辆人员 |
| videoDevicePageCondition | Object | 否 |  |  | 视频设备分页查询条件，`keys` 包含 `video` 时生效 |
| +condition | Object | 否 |  |  | 视频设备过滤条件，字段同视频设备查询条件 |
| +pageSize | Integer | 否 |  |  | 每页条数 |
| +pageNo | Integer | 否 |  |  | 页码 |
| videoDeviceCondition | Object | 否 |  |  | 视频设备非分页条件，完整列表接口当前主要使用 `videoDevicePageCondition` |
| +id | String | 否 | 无 |  | 视频表主键 |
| +name | String | 否 | 无 | 模糊查询 | 视频名称 |
| +type | String | 否 | 无 |  | 设备类型 |
| +status | String | 否 | 无 | 1表示在线0表示离线 | 设备状态 |
| +videoType | String | 否 | 无 |  | 视频类型 |
| videoCellPageCondition | Object | 否 |  |  | 城管视频分页查询条件，`keys` 包含 `tcvideo` 时生效 |
| +condition | Object | 否 |  |  | 城管视频过滤条件 |
| +pageSize | Integer | 否 |  |  | 每页条数 |
| +pageNo | Integer | 否 |  |  | 页码 |
| videoCellCondition | Object | 否 |  |  | 城管视频非分页条件 |

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
      "video",
      "tcvideo"
    ]
  },
  "toStatInfoPageCondition": {"condition": {}, "pageNo": 1, "pageSize": 100},
  "patrolPageCondition": {"condition": {}, "pageNo": 1, "pageSize": 100},
  "videoDevicePageCondition": {"condition": {}, "pageNo": 1, "pageSize": 100},
  "videoCellPageCondition": {"condition": {}, "pageNo": 1, "pageSize": 100}
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
| ++id | String | 是 |  | 主键 |
| ++address | String | 是 |  | 案发地址 |
| ++taskNum | String | 是 |  | 任务号 |
| ++archiveTime | String | 是 |  | 结案时间 |
| ++bizId | Integer | 是 |  | 业务标识 |
| ++dutyGridName | String | 是 |  | 责任网格 |
| ++cellName | String | 是 |  | 单元网格 |
| ++communityName | String | 是 |  | 社区 |
| ++streetName | String | 是 |  | 街道 |
| ++districtName | String | 是 |  | 区县 |
| ++longitude | Double | 是 |  | 经度 |
| ++latitude | Double | 是 |  | 纬度 |
| ++createTime | String | 是 |  | 上报时间 |
| ++eventDesc | String | 是 |  | 案件描述 |
| ++eventSrcName | String | 是 |  | 案件来源 |
| ++eventTypeName | String | 是 |  | 问题类型 |
| ++mainTypeName | String | 是 |  | 问题大类 |
| ++subTypeName | String | 是 |  | 问题小类 |
| ++recTypeName | String | 是 |  | 案件类型 |
| ++checkPatrolName | String | 是 |  | 核查监督员姓名 |
| ++checkTime | String | 是 |  | 核查时间 |
| ++dispatchHumanName | String | 是 |  | 派遣员名称 |
| ++dispatchTime | String | 是 |  | 派遣时间 |
| ++disposeBeginTime | String | 是 |  | 处置开始时间 |
| ++disposeEndTime | String | 是 |  | 处置结束时间 |
| ++disposeDeadline | String | 是 |  | 处置截至时间 |
| ++disposeOpinion | String | 是 |  | 处置意见 |
| ++disposeRegionName | String | 是 |  | 处置区域 |
| ++disposeUnitName | String | 是 |  | 处置部门 |
| ++eventGradeName | String | 是 |  | 问题等级 |
| ++eventLevelName | String | 是 |  | 问题级别 |
| ++eventStateName | String | 是 |  | 案件状态 |
| ++firstUnitName | String | 是 |  | 一级部门 |
| ++instHumanName | String | 是 |  | 立案人 |
| ++instTime | String | 是 |  | 立案时间 |
| ++operateHumanName | String | 是 |  | 受理人 |
| ++operateTime | String | 是 |  | 受理时间 |
| ++reportPatrolName | String | 是 |  | 上报监督员 |
| ++superviseHumanName | String | 是 |  | 督查人 |
| ++superviseTime | String | 是 |  | 督查时间 |
| ++verifyPatrolName | String | 是 |  | 核实监督员 |
| ++verifyTime | String | 是 |  | 核实时间 |
| ++disposeUsed | Double | 是 |  | 处置用时 |
| ++bizName | String | 是 |  | 业务名称 |
| ++disposeRoleName | String | 是 |  | 处置岗位 |
| ++attachments | Object[] | 否 |  | 附件列表 |
| +++mediaPath | String | 否 |  | 附件存储路径 |
| +++mediaUsage | String | 否 |  | 图片用途：上报、处置等 |
| +vehicleList | Object[] | 否 |  | 车辆列表；v22 当前完整列表车辆分支未启用，通常不会返回 |
| ++id | String | 是 |  | 车辆id |
| ++unitId | String | 是 |  | 部门id |
| ++vehicleNum | String | 是 |  | 车牌号 |
| ++simCardNum | String | 是 |  | sim号 |
| ++vehicleUsage | String | 是 |  | 车辆用途 |
| ++vehicleBrand | String | 是 |  | 车辆品牌 |
| ++vehicleColor | String | 是 |  | 车辆颜色 |
| ++regionId | String | 是 |  | 区域id |
| ++startWorkTime | String | 是 |  | 开始工作时间 |
| ++endWorkTime | String | 是 |  | 结束工作时间 |
| ++vehicleOwner | String | 是 |  | 车辆所有者 |
| ++telPhoneOwner | String | 是 |  | 电话 |
| ++vehicleTypeId | String | 是 |  | 车辆类型 |
| ++onlineFlag | Boolean | 是 |  | 车辆状态 |
| ++deleteFlag | Boolean | 是 |  | 是否删除 |
| ++validFlag | Boolean | 是 |  | 是否有效 |
| ++vehicleRemarks | String | 是 |  | 车辆备注 |
| ++vehicleTypeName | String | 是 |  | 车辆类型名称 |
| ++address | String | 是 |  | 地址 |
| ++speed | Boolean | 是 |  | 车速 |
| ++todayCourse | String | 是 |  | 里程数 |
| ++consumption | String | 是 |  | 油耗 |
| ++recordTime | String | 是 |  | 记录时间 |
| ++vehiclePosList | Object[] | 是 |  | 车辆点位 |
| +++id | String | 是 | 属于vehiclePosList | 车辆id |
| +++latitude | Double | 是 | 属于vehiclePosList | 纬度 |
| +++longitude | Double | 是 | 属于vehiclePosList | 经度 |
| +++speed | Double | 是 | 属于vehiclePosList | 车速 |
| +++todayCourse | Double | 是 | 属于vehiclePosList | 今日路程 |
| +++totalCourse | Double | 是 | 属于vehiclePosList | 总路程 |
| +++consumption | Double | 是 | 属于vehiclePosList | 瞬时油耗 |
| +++recordTime | String | 是 | 属于vehiclePosList | 记录时间 |
| +++uploadTime | String | 是 | 属于vehiclePosList | 上传时间 |
| ++vehicleType | String | 是 |  | 车辆类型 |
| +++id | String | 是 | 属于vehicleType | 车辆类型id |
| +++vehicleTypeName | String | 是 | 属于vehicleType | 车辆类型名称 |
| ++region | String | 是 |  | 区域 |
| +++id | String | 是 | 属于region | 区域id |
| +++regionCode | String | 是 | 属于region | 区域编码 |
| +++longitude | Double | 是 | 属于region | 经度 |
| +++latitude | Double | 是 | 属于region | 纬度 |
| +++regionName | String | 是 | 属于region | 区域名称 |
| +++regionType | Integer | 是 | 属于region | 区域类型 |
| +++parentId | String | 是 | 属于region | 父级区域id |
| +++validFlag | Boolean | 是 | 属于region | 逻辑删除字段 |
| ++vehicleUnit | String | 是 |  | 车辆单位 |
| +++id | String | 是 | 属于vehicleUnit | 单位id |
| +++unitName | String | 是 | 属于vehicleUnit | 单位名称 |
| +++unitDesc | String | 是 | 属于vehicleUnit | 单位描述 |
| +++seniorId | String | 是 | 属于vehicleUnit | 上级单位标识 |
| +++regionId | String | 是 | 属于vehicleUnit | 所属区域标识 |
| +++regionType | String | 是 | 属于vehicleUnit | 所属区域类型 |
| +++unitTypeId | String | 是 | 属于vehicleUnit | 单位类型标识 |
| +++unitTypeName | String | 是 | 属于vehicleUnit | 单位类型名称 |
| +++validFlag | Boolean | 是 | 属于vehicleUnit | 有效标识 |
| +++address | String | 是 | 属于vehicleUnit | 地址 |
| +++officeTel | String | 是 | 属于vehicleUnit | 办公电话 |
| +++remark | String | 是 | 属于vehicleUnit | 备注 |
| +++principal | String | 是 | 属于vehicleUnit | 负责人 |
| +++principalContact | String | 是 | 属于vehicleUnit | 负责人电话 |
| +++x | Double | 是 | 属于vehicleUnit | x |
| +++y | Double | 是 | 属于vehicleUnit | y |
| ++longitude | Double | 是 |  | 经度 |
| ++latitude | Double | 是 |  | 纬度 |
| ++parentRegionList | Object[] | 否 |  | 父区域，只有regionHigherFlag为true时，这个字段才有值 |
| +++id | String | 否 | 属于region | 区域id |
| +++regionCode | String | 否 | 属于region | 区域编码 |
| +++longitude | Double | 否 | 属于region | 经度 |
| +++latitude | Double | 否 | 属于region | 纬度 |
| +++regionName | String | 否 | 属于region | 区域名称 |
| +++regionType | Integer | 否 | 属于region | 区域类型 |
| +++parentId | String | 否 | 属于region | 父级区域id |
| +++validFlag | Boolean | 否 | 属于region | 逻辑删除字段 |
| ++parentUnitList | Object[] | 否 |  | 父车辆单位，只有当unitHigherFlag为true时，这个字段才会有值 |
| +++id | String | 否 | 属于vehicleUnit | 单位id |
| +++unitName | String | 否 | 属于vehicleUnit | 单位名称 |
| +++unitDesc | String | 否 | 属于vehicleUnit | 单位描述 |
| +++seniorId | String | 否 | 属于vehicleUnit | 上级单位标识 |
| +++regionId | String | 否 | 属于vehicleUnit | 所属区域标识 |
| +++regionType | String | 否 | 属于vehicleUnit | 所属区域类型 |
| +++unitTypeId | String | 否 | 属于vehicleUnit | 单位类型标识 |
| +++unitTypeName | String | 否 | 属于vehicleUnit | 单位类型名称 |
| +++validFlag | Boolean | 否 | 属于vehicleUnit | 有效标识 |
| +++address | String | 否 | 属于vehicleUnit | 地址 |
| +++officeTel | String | 否 | 属于vehicleUnit | 办公电话 |
| +++remark | String | 否 | 属于vehicleUnit | 备注 |
| +++principal | String | 否 | 属于vehicleUnit | 负责人 |
| +++principalContact | String | 否 | 属于vehicleUnit | 负责人电话 |
| +++x | Double | 否 | 属于vehicleUnit | x |
| +++y | Double | 否 | 属于vehicleUnit | y |
| ++vehicleHumanList | Object[] | 否 |  | 车辆人员，只有当humanFlag为true时，这个字段才会有值 |
| +++id | String | 否 |  | 人员主键 |
| +++code | String | 否 |  | 人员编码 |
| +++name | String | 否 |  | 人员名称 |
| +++desc | String | 否 |  | 人员描述 |
| +++humanCategoryId | String | 否 |  | 人员类别标识 |
| +++idCard | String | 否 |  | 人员卡号 |
| +++genderId | Integer | 否 |  | 性别 1-男 2-女 |
| +++unitId | String | 否 |  | 人员所属部门主键 |
| +++unitName | String | 否 |  | 人员所属部门名称 |
| +++mobile | String | 否 |  | 电话号码 |
| +++address | String | 否 |  | 人员地址 |
| +++misHumanId | String | 否 |  | 城管人员id |
| +videoList | Object[] | 是 |  | 视频设备列表 |
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
| +tcVideoList | Object[] | 否 |  | 城管视频列表，`keys` 包含 `tcvideo` 时返回 |
| +patrolList | Object[] | 是 |  | 人员列表 |
| ++id | String | 是 |  | 人员id |
| ++cardId | String | 是 |  | 人员卡号 |
| ++patrolCode | String | 是 |  | 人员编码 |
| ++patrolName | String | 是 |  | 人员名称 |
| ++patrolTypeId | String | 是 |  | 人员类型id |
| ++regionId | String | 是 |  | 人员区域id |
| ++longitude | Double | 是 |  | 人员经度 |
| ++latitude | Double | 是 |  | 人员纬度 |
| ++unitId | String | 是 |  | 人员部门id |
| ++patrolType | Object | 是 |  | 人员类型信息 |
| +++id | String | 是 |  | 人员类型id |
| +++displayName | String | 是 |  | 人员类型名称 |
| ++region | Object | 是 |  | 人员区划信息 |
| +++id | String | 是 |  | 区划主键 |
| +++regionCode | String | 是 |  | 区划编码 |
| +++longitude | Double | 是 |  | 经度 |
| +++latitude | Double | 是 |  | 纬度 |
| +++regionName | String | 是 |  | 区划名称 |
| +++regionType | Integer | 是 |  | 区划类型0：省1：市2：区县3：街道4：社区5：网格 |
| +++parentId | String | 是 |  | 父区划id |
| ++patrolState | Object | 是 |  | 人员点位信息 |
| +++id | String | 是 |  | 人员主键 |
| +++x | Double | 是 |  | 人员经度 |
| +++y | Double | 是 |  | 人员纬度 |
| +++updateTime | String | 是 |  | 更新时间 |
| +++patrolStateId | Integer | 是 |  | 人员是否在线 1：在线 |
| ++human | Object | 是 |  | 人员信息 |
| +++id | String | 是 |  | 人员id |
| +++address | String | 是 |  | 人员地址 |
| +++birthday | String | 是 |  | 生日 |
| +++humanCode | String | 是 |  | 人员编码 |
| +++humanDesc | String | 是 |  | 人员描述 |
| +++humanName | String | 是 |  | 人员名称 |
| +++regionId | String | 是 |  | 所属区域id |
| +++regionType | Integer | 是 |  | 所属区域类型 |
| +++telHome | String | 是 |  | 家庭电话 |
| +++telMobile | String | 是 |  | 手机号码 |
| +++telOffice | String | 是 |  | 办公电话 |
| +++unitId | String | 是 |  | 所属部门id |
| +++unitName | String | 是 |  | 所属部门 |
| ++parentRegionList | Object[] | 否 |  | 人员所属区划的上级区划，当regionHigherFlag传true时，这个字段才会有返回值 |
| +++id | String | 否 |  | 区划主键 |
| +++regionCode | String | 否 |  | 区划编码 |
| +++longitude | Double | 否 |  | 经度 |
| +++latitude | Double | 否 |  | 纬度 |
| +++regionName | String | 否 |  | 区划名称 |
| +++regionType | Integer | 否 |  | 区划类型0：省1：市2：区县3：街道4：社区5：网格 |
| +++parentId | String | 否 |  | 父区划id |
| ++parentUnitList | Object[] | 否 |  | 人员所属部门的上级，当unitHigherFlag传true时，这个字段才会有返回值 |
| +++id | String | 否 |  | 部门id |
| +++unitName | String | 否 |  | 部门名称 |
| +++unitShortened | String | 否 |  | 部门简称 |
| +++unitDesc | String | 否 |  | 部门描述 |
| +++unitCode | String | 否 |  | 部门编码 |
| +++parentId | String | 否 |  | 上级部门id，默认为0 |
| +++displayOrder | Integer | 否 |  | 显示次序 |
| +++address | String | 否 |  | 部门地址 |
| +++telOffice | String | 否 |  | 部门电话 |
| +++validFlag | Boolean | 否 |  | 是否有效 |
| +++deleteFlag | Boolean | 否 |  | 是否删除 |
| +++regionId | String | 否是 |  | 所属区划 |
| +++regionType | String | 否 |  | 所属区划类型 |
| ++dutyGridList | Object[] | 否 |  | 人员所属责任网格，当dutyCellFlag传true时，这个字段才会有返回值 |
| +++id | String | 否 |  | 责任网格id |
| +++code | String | 否 |  | 责任网格编码 |
| +++desc | String | 否 |  | 责任网格描述 |
| +++name | String | 否 |  | 责任网格名称 |
| ++attachments | Object[] | 否 |  | 人员头像，attachmentFlag为true，这个字段才会有值 |
| +++mediaPath | String | 否 |  | 头像路径 |
| message | String | 是 |  | 当hasError为true时这里展示报错信息 |
| tag | / | 是 |  | 未使用到 |
| totalCount | Integer | 是 |  | 返回数据的总条数 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": {
    "recordsList": [],
    "videoList": [],
    "tcVideoList": [],
    "patrolList": [
      {
        "id": "100433",
        "cardId": "100433",
        "patrolCode": "",
        "patrolName": "egova",
        "patrolTypeId": "8",
        "regionId": "0",
        "imei": "866570038861071",
        "isAutoSendCheck": "1",
        "blacklistFlag": "0",
        "classTypeId": "0",
        "gridTypeId": "0",
        "patrolType": {
          "id": "8",
          "displayName": "管理干部",
          "displayOrder": 8
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
          "createDate": "2018-04-04 00:00:00",
          "deleteDate": "2018-04-04 00:00:00",
          "deleteFlag": false,
          "genderId": 1,
          "humanCode": "100433",
          "humanDesc": "egova",
          "humanName": "egova",
          "patrolFlag": true,
          "regionId": "0",
          "regionType": 1,
          "telHome": "",
          "telMobile": "15167863112",
          "telOffice": "",
          "unitId": "1",
          "unitName": "网格化城市管理",
          "userName": "egova",
          "identityNo": "342326197412205013"
        },
        "longitude": 120.69843166666666,
        "latitude": 27.999376666666663,
        "parentRegionList": null,
        "dutyGridList": null,
        "parentUnitList": null,
        "attachments": null,
        "unitId": "1",
        "distance": 0.0,
        "latestLogonTime": null
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
- 周边搜索必须确认 `geoInfo.longitude`、`geoInfo.latitude`、`geoInfo.radius` 和 `keys`；v22 完整列表支持 `records`、`patrol`、`video`、`tcvideo`，不建议传 `vehicle`。
- 如果用于地图点位，需确认坐标系和组件静态数据模板；如组件字段与接口字段不同，再按返回字段做映射。
