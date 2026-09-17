# 悟能接口扁平摘要

> 用途：命中 `domain_indexes/wuneng_api_index.md` 候选后，先读取本文件快速确认接口名称、方法、地址、星桥路径、result 形状、适配组件、阻塞项和风险。若要输出具体请求参数、字段映射或过滤脚本，仍需读取对应 `detailDoc`。

## MIS车辆

### VEHICLE_LIST

- 接口名称：车辆列表查询
- 方法：POST
- 接口地址：`/api/cgdb/vehicle/list`
- 星桥路径：API平台/悟能接口/车辆相关/车辆列表查询
- detailDoc：`knowledge/api_details/mis/vehicle/VEHICLE_LIST.md`
- result 形状：array
- 关键返回：车辆完整列表，包含车辆、类型、区划、部门、点位等字段
- 适配组件：表格、车辆列表、详情入口
- 支持筛选：车辆id、车牌号、区划、部门、车辆类型、在线状态
- 阻塞项：大数据量建议用分页或简要列表
- 风险：返回字段较多，不适合无条件全量查询

### VEHICLE_SIMPLE_LIST

- 接口名称：车辆简要列表查询
- 方法：POST
- 接口地址：`/api/cgdb/vehicle/simple/list`
- 星桥路径：API平台/悟能接口/车辆相关/车辆简要列表查询
- detailDoc：`knowledge/api_details/mis/vehicle/VEHICLE_SIMPLE_LIST.md`
- result 形状：array
- 关键返回：`id`=车辆id，`vehicleNum`=车牌号，`longitude`=经度，`latitude`=纬度，`onlineFlag`=在线状态
- 适配组件：地图点位、车辆图层、轻量列表
- 支持筛选：车辆id、车牌号、区划、部门、车辆类型、在线状态
- 阻塞项：需确认地图坐标系
- 风险：只返回关键字段

### VEHICLE_COUNT

- 接口名称：条件查询车辆总数
- 方法：POST
- 接口地址：`/api/cgdb/vehicle/count`
- 星桥路径：API平台/悟能接口/车辆相关/条件查询车辆总数
- detailDoc：`knowledge/api_details/mis/vehicle/VEHICLE_COUNT.md`
- result 形状：number
- 关键返回：`result`=车辆数量
- 适配组件：指标卡、总数卡片
- 支持筛选：车辆id、车牌号、区划、部门、车辆类型、在线状态
- 阻塞项：与分页接口配套时条件需保持一致
- 风险：只返回数量

### VEHICLE_PAGE

- 接口名称：车辆分页查询
- 方法：POST
- 接口地址：`/api/cgdb/vehicle/page`
- 星桥路径：API平台/悟能接口/车辆相关/车辆分页查询
- detailDoc：`knowledge/api_details/mis/vehicle/VEHICLE_PAGE.md`
- result 形状：array
- 关键返回：`condition`=查询条件，`paging`=分页，`result[]`=车辆列表，`totalCount`=总条数
- 适配组件：分页表格、车辆列表
- 支持筛选：车辆id、车牌号、区划、部门、车辆类型、在线状态
- 阻塞项：分页组件需要完整响应包拿 `totalCount`
- 风险：扩展开关会增加查询成本

### VEHICLE_INFO

- 接口名称：车辆详情查询
- 方法：GET
- 接口地址：`/api/cgdb/vehicle/info`
- 星桥路径：API平台/悟能接口/车辆相关/车辆详情查询
- detailDoc：`knowledge/api_details/mis/vehicle/VEHICLE_INFO.md`
- result 形状：object
- 关键返回：单个车辆详情对象
- 适配组件：详情弹窗、详情卡片、地图点位详情
- 支持筛选：车辆id
- 阻塞项：必须确认车辆 id 来源
- 风险：只查询单车详情

### VEHICLE_GROUP_TYPE

- 接口名称：车辆类型分组
- 方法：POST
- 接口地址：`/api/cgdb/vehicle/group`
- 星桥路径：API平台/悟能接口/车辆相关/车辆类型分组
- detailDoc：`knowledge/api_details/mis/vehicle/VEHICLE_GROUP_TYPE.md`
- result 形状：array
- 关键返回：`name`=车辆类型名称，`text`=车辆类型id，`value`=车辆数量
- 适配组件：饼图、柱状图、排行列表
- 支持筛选：区划、部门、车辆状态、车辆类型
- 阻塞项：需确认 `name/text` 语义
- 风险：不返回车辆明细

### VEHICLE_GROUP_REGION

- 接口名称：车辆区划分组
- 方法：POST
- 接口地址：`/api/cgdb/vehicle/group?@state=region`
- 星桥路径：API平台/悟能接口/车辆相关/车辆区划分组
- detailDoc：`knowledge/api_details/mis/vehicle/VEHICLE_GROUP_REGION.md`
- result 形状：array
- 关键返回：`name`=区划id，`text`=区划名称，`value`=车辆数量
- 适配组件：柱状图、区划排行、地图区域统计
- 支持筛选：区划条件、部门、车辆类型、在线状态
- 阻塞项：`regionCondition` 需要确认
- 风险：不返回车辆明细

### VEHICLE_GROUP_UNIT

- 接口名称：车辆部门分组
- 方法：POST
- 接口地址：`/api/cgdb/vehicle/group?@state=unit`
- 星桥路径：API平台/悟能接口/车辆相关/车辆部门分组
- detailDoc：`knowledge/api_details/mis/vehicle/VEHICLE_GROUP_UNIT.md`
- result 形状：array
- 关键返回：`name/text/value` 返回部门维度统计，`name/text` 语义需现场确认
- 适配组件：柱状图、部门排行
- 支持筛选：部门条件、区划、车辆类型、在线状态
- 阻塞项：`vehicleUnitCondition` 需要确认
- 风险：`name/text` 语义需联调确认

### VEHICLE_TYPE_LIST

- 接口名称：车辆类型列表查询
- 方法：POST
- 接口地址：`/api/cgdb/vehicle-type/list`
- 星桥路径：待确认
- detailDoc：`knowledge/api_details/mis/vehicle/VEHICLE_TYPE_LIST.md`
- result 形状：array
- 关键返回：`id`=车辆类型id，`vehicleTypeName`=车辆类型名称
- 适配组件：下拉筛选、字典列表
- 支持筛选：车辆类型id
- 阻塞项：星桥路径待确认
- 风险：字典接口不返回车辆数量

### VEHICLE_TREE_REGION

- 接口名称：车辆区划分组树形
- 方法：POST
- 接口地址：`/api/cgdb/vehicle/tree?@state=region`
- 星桥路径：API平台/悟能接口/车辆相关/车辆区划分组树形
- detailDoc：`knowledge/api_details/mis/vehicle/VEHICLE_TREE_REGION.md`
- result 形状：array
- 关键返回：`name`=区划id，`text`=区划名称，`value`=车辆数量，`vehicleList`=车辆简要列表
- 适配组件：区划树、地图钻取、左树右列表
- 支持筛选：区划条件、车辆类型、部门、`showListFlag`
- 阻塞项：`showListFlag=true` 会增加数据量
- 风险：是否返回 `children` 需确认

### VEHICLE_TREE_UNIT

- 接口名称：车辆部门分组树形
- 方法：POST
- 接口地址：`/api/cgdb/vehicle/group?@state=unit`
- 星桥路径：API平台/悟能接口/车辆相关/车辆部门分组
- detailDoc：`knowledge/api_details/mis/vehicle/VEHICLE_TREE_UNIT.md`
- result 形状：array
- 关键返回：`name`=部门id，`text`=部门名称，`value`=车辆数量，`vehicleList`=车辆简要列表
- 适配组件：部门树、部门车辆分布
- 支持筛选：部门条件、区划条件、`showListFlag`
- 阻塞项：`showListFlag=true` 会增加数据量
- 风险：`name/text` 语义需联调确认

## MIS案件

### REC_LAYER_LIST

- 接口名称：案件简要列表
- 方法：POST
- 接口地址：`/api/cgdbstat/records/layer/list`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/案件简要列表
- detailDoc：`knowledge/api_details/mis/rec/REC_LAYER_LIST.md`
- result 形状：array
- 关键返回：`id`=案件主键，`taskNum`=任务号，`longitude`=经度，`latitude`=纬度，`eventDesc`=案件描述
- 适配组件：地图图层、地图点位、案件弹窗
- 支持筛选：时间、区划、问题类型、来源、状态、人员、部门
- 阻塞项：默认字段必须保留 id 和经纬度
- 风险：默认最多 30000 条且不支持附件

### REC_LIST

- 接口名称：案件列表
- 方法：POST
- 接口地址：`/api/cgdbstat/records/list`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/案件列表
- detailDoc：`knowledge/api_details/mis/rec/REC_LIST.md`
- result 形状：array
- 关键返回：返回 `to_stat_info` 案件字段，可选附件
- 适配组件：表格、案件列表、详情入口
- 支持筛选：时间、区划、问题类型、来源、状态、人员、部门
- 阻塞项：建议 100 条以内
- 风险：大数据量用分页接口

### REC_PAGE

- 接口名称：案件分页查询
- 方法：POST
- 接口地址：`/api/cgdbstat/records/page`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/案件分页查询
- detailDoc：`knowledge/api_details/mis/rec/REC_PAGE.md`
- result 形状：array
- 关键返回：`condition`=查询条件，`paging`=分页，`result[]`=案件列表，`totalCount`=总条数
- 适配组件：分页表格、案件列表
- 支持筛选：时间、区划、问题类型、来源、状态、人员、部门
- 阻塞项：分页组件需要完整响应包拿 `totalCount`
- 风险：`condition` 需与 count 接口一致

### REC_INFO

- 接口名称：案件详情
- 方法：GET
- 接口地址：`/api/cgdbstat/records/info`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/案件详情
- detailDoc：`knowledge/api_details/mis/rec/REC_INFO.md`
- result 形状：object
- 关键返回：单个案件详情对象
- 适配组件：详情弹窗、地图点位详情、表格行详情
- 支持筛选：案件id
- 阻塞项：必须确认案件 id 来源
- 风险：附件结构需现场确认

### REC_COUNT

- 接口名称：案件数量统计
- 方法：POST
- 接口地址：`/api/cgdbstat/records/count`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/案件数量统计
- detailDoc：`knowledge/api_details/mis/rec/REC_COUNT.md`
- result 形状：number
- 关键返回：`result`=案件数量
- 适配组件：指标卡、总数卡片、分页总数辅助
- 支持筛选：时间、区划、问题类型、来源、状态、人员、部门
- 阻塞项：与分页接口配套时 condition 需一致
- 风险：只返回数量

### REC_INDEX_SUMMARY

- 接口名称：案件指标统计
- 方法：POST
- 接口地址：`/api/cgdbstat/records/index/group`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/案件指标统计
- detailDoc：`knowledge/api_details/mis/rec/REC_INDEX_SUMMARY.md`
- result 形状：object
- 关键返回：动态字段来自 `groupList`，如 `report/archive/disposeRate` 及同比环比字段
- 适配组件：指标卡、多指标卡、统计概览
- 支持筛选：时间、区划、问题类型、来源、案件类型
- 阻塞项：`groupList` 必填
- 风险：返回字段随 `groupList` 动态变化

### REC_INDEX_SOURCE

- 接口名称：基于案件来源的案件指标统计
- 方法：POST
- 接口地址：`/api/cgdbstat/records/index/group?@state=recordsSource`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/基于案件来源的案件指标统计
- detailDoc：`knowledge/api_details/mis/rec/REC_INDEX_SOURCE.md`
- result 形状：array
- 关键返回：`name`=来源id，`text`=来源名称，动态字段来自 `groupList`
- 适配组件：饼图、柱状图、来源排行
- 支持筛选：时间、区划、问题类型、案件类型
- 阻塞项：`groupList` 必填
- 风险：需展示来源应为同级

### REC_INDEX_EVENT_TYPE

- 接口名称：基于问题类型的案件指标统计
- 方法：POST
- 接口地址：`/api/cgdbstat/records/index/group?@state=eventType`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/基于问题类型的案件指标统计
- detailDoc：`knowledge/api_details/mis/rec/REC_INDEX_EVENT_TYPE.md`
- result 形状：array
- 关键返回：`name`=问题类型id，`text`=问题类型名称，动态字段来自 `groupList`
- 适配组件：饼图、柱状图、问题类型排行
- 支持筛选：时间、区划、来源、案件类型
- 阻塞项：`groupList` 必填
- 风险：问题类型需同级

### REC_INDEX_REGION

- 接口名称：基于区划的案件指标统计
- 方法：POST
- 接口地址：`/api/cgdbstat/records/index/group?@state=region`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/基于区划的案件指标统计
- detailDoc：`knowledge/api_details/mis/rec/REC_INDEX_REGION.md`
- result 形状：array
- 关键返回：`name`=区划id，`text`=区划名称，动态字段来自 `groupList`
- 适配组件：柱状图、排行列表、区划统计
- 支持筛选：时间、区划、问题类型、来源、案件类型
- 阻塞项：`groupList` 必填
- 风险：需确认 `regionCondition` 或区划级别

### REC_INDEX_DISPOSE_UNIT

- 接口名称：基于处置部门的案件指标统计
- 方法：POST
- 接口地址：`/api/cgdbstat/records/index/group?@state=disposeUnit`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/基于处置部门的案件指标统计
- detailDoc：`knowledge/api_details/mis/rec/REC_INDEX_DISPOSE_UNIT.md`
- result 形状：array
- 关键返回：`name`=部门id，`text`=部门名称，动态字段来自 `groupList`
- 适配组件：柱状图、部门排行
- 支持筛选：时间、区划、问题类型、来源、案件类型、`parentUnitIds`
- 阻塞项：`groupList` 必填
- 风险：排序 TopN 需确认 `sortField`

### REC_INDEX_TIME

- 接口名称：基于时间的案件指标统计
- 方法：POST
- 接口地址：`/api/cgdbstat/records/index/group?@state=time`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/基于时间的案件指标统计
- detailDoc：`knowledge/api_details/mis/rec/REC_INDEX_TIME.md`
- result 形状：array
- 关键返回：`name/text`=时间节点，动态字段来自 `groupList`
- 适配组件：折线图、趋势图、时间序列柱状图
- 支持筛选：时间类型、时间间隔、区划、问题类型、来源
- 阻塞项：`interval` 和 `timeType` 必填
- 风险：返回字段随 `groupList` 动态变化

### REC_HEATMAP

- 接口名称：案件热力图
- 方法：POST
- 接口地址：`/api/cgdbstat/records/heatmap`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/案件热力图
- detailDoc：`knowledge/api_details/mis/rec/REC_HEATMAP.md`
- result 形状：array
- 关键返回：`latitude`=纬度，`longitude`=经度，`value`=数量
- 适配组件：热力图、地图热力层
- 支持筛选：时间、区划、问题类型、来源、状态、人员、部门
- 阻塞项：建议时间跨度小于一个月
- 风险：只返回热力点不返回案件详情

### REC_DIAGNOSIS

- 接口名称：案件诊断信息
- 方法：POST
- 接口地址：`/api/cgdbstat/records/diagnosis`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/案件诊断信息
- detailDoc：`knowledge/api_details/mis/rec/REC_DIAGNOSIS.md`
- result 形状：array
- 关键返回：`name`=诊断名称，`text`=诊断模板，`value`=诊断内容
- 适配组件：诊断卡片、文本列表、轮播列表
- 支持筛选：时间、区划、问题类型、来源
- 阻塞项：`groupList` 必填
- 风险：返回文本不是数值图表

### REC_INDEX_ROAD

- 接口名称：基于道路的案件指标统计
- 方法：POST
- 接口地址：`/api/cgdbstat/records/index/group?@state=road`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/基于道路的案件指标统计
- detailDoc：`knowledge/api_details/mis/rec/REC_INDEX_ROAD.md`
- result 形状：array
- 关键返回：`name`=道路id，`text`=道路名称，动态字段来自 `groupList`
- 适配组件：柱状图、道路排行、TopN
- 支持筛选：时间、区划、问题类型、来源、道路级别
- 阻塞项：`groupList` 必填
- 风险：道路范围需确认

### REC_INDEX_PATROL

- 接口名称：基于人员的案件指标统计
- 方法：POST
- 接口地址：`/api/cgdbstat/records/index/group?@state=patrol`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/基于人员的案件指标统计
- detailDoc：`knowledge/api_details/mis/rec/REC_INDEX_PATROL.md`
- result 形状：array
- 关键返回：`name`=人员id，`text`=人员名称，`unitName`=部门，`regionName`=区划，动态字段来自 `groupList`
- 适配组件：人员排行、绩效排行、柱状图
- 支持筛选：时间、区划、问题类型、来源、人员范围
- 阻塞项：人员指标当前固定
- 风险：原始示例指标与支持列表需联调确认

### REC_INDEX_REGION_EVENT_TYPE

- 接口名称：基于区划、问题类型的案件指标统计
- 方法：POST
- 接口地址：`/api/cgdbstat/records/index/group?@state=multiField`
- 星桥路径：API平台/悟能接口/城管接口/案件相关/基于区划、问题类型的案件指标统计
- detailDoc：`knowledge/api_details/mis/rec/REC_INDEX_REGION_EVENT_TYPE.md`
- result 形状：array
- 关键返回：`name`=区划id，`text`=问题类型id，`regionName`=区划名称，`eventName`=问题类型名称，动态字段来自 `groupList`
- 适配组件：堆叠柱状图、二维统计表、矩阵
- 支持筛选：时间、区划范围、问题类型范围、来源、案件类型
- 阻塞项：`groupList` 必填
- 风险：返回行数可能为区划数量乘问题类型数量

### REC_SOURCE_LIST

- 接口名称：案件来源列表接口
- 方法：POST
- 接口地址：`/api/cgdb/recordsSource/list`
- 星桥路径：API平台/悟能接口/城管接口/案件来源相关/案件来源列表接口
- detailDoc：`knowledge/api_details/mis/rec/REC_SOURCE_LIST.md`
- result 形状：array
- 关键返回：`id`=来源id，`eventSrcName`=来源名称，`seniorId`=父来源id
- 适配组件：下拉筛选、字典列表、级联筛选
- 支持筛选：来源id、父来源、来源名称
- 阻塞项：如需级联使用 `seniorId`
- 风险：字典接口不返回案件数量

### REC_EVENT_TYPE_LIST

- 接口名称：案件类型列表接口
- 方法：POST
- 接口地址：`/api/cgdb/eventType/list`
- 星桥路径：API平台/悟能接口/城管接口/案件类型相关/案件类型列表接口
- detailDoc：`knowledge/api_details/mis/rec/REC_EVENT_TYPE_LIST.md`
- result 形状：array
- 关键返回：`id`=问题类型id，`typeName`=名称，`grade`=等级，`parentId`=父类型id
- 适配组件：下拉筛选、级联筛选、树形筛选
- 支持筛选：id、grade、parentId、typeName
- 阻塞项：`grade=1/2/3` 分别为问题类型/大类/小类
- 风险：`children` 是否完整需联调确认

## MIS人员

### PATROL_LIST

- 接口名称：人员列表查询
- 方法：POST
- 接口地址：`/api/cgdb/patrol/list`
- 星桥路径：API平台/悟能接口/城管接口/人员相关/人员列表查询
- detailDoc：`knowledge/api_details/mis/patrol/PATROL_LIST.md`
- result 形状：array
- 关键返回：人员完整列表，包含人员、类型、区划、状态、human 等字段
- 适配组件：表格、人员列表、详情入口
- 支持筛选：人员id、姓名、类型、区划、部门、在线状态
- 阻塞项：大数据量建议分页或简要列表
- 风险：扩展开关会增加查询成本

### PATROL_SIMPLE_LIST

- 接口名称：人员简要列表查询
- 方法：POST
- 接口地址：`/api/cgdb/patrol/simple/list`
- 星桥路径：API平台/悟能接口/城管接口/人员相关/人员简要列表查询
- detailDoc：`knowledge/api_details/mis/patrol/PATROL_SIMPLE_LIST.md`
- result 形状：array
- 关键返回：`id`=人员id，`patrolName`=人员名称，`longitude`=经度，`latitude`=纬度，`onlineFlag`=是否在线
- 适配组件：地图点位、人员图层、轻量列表
- 支持筛选：人员id、姓名、类型、区划、部门、在线状态
- 阻塞项：只返回关键字段
- 风险：详情需调用人员详情

### PATROL_COUNT

- 接口名称：条件查询人员总数
- 方法：POST
- 接口地址：`/api/cgdb/patrol/count`
- 星桥路径：API平台/悟能接口/城管接口/人员相关/条件查询人员总数
- detailDoc：`knowledge/api_details/mis/patrol/PATROL_COUNT.md`
- result 形状：number
- 关键返回：`result`=人员数量
- 适配组件：指标卡、总数卡片、分页总数辅助
- 支持筛选：人员id、姓名、类型、区划、部门、在线状态
- 阻塞项：与分页接口配套时 condition 需一致
- 风险：只返回数量

### PATROL_PAGE

- 接口名称：人员分页查询
- 方法：POST
- 接口地址：`/api/cgdb/patrol/page`
- 星桥路径：API平台/悟能接口/城管接口/人员相关/人员分页查询
- detailDoc：`knowledge/api_details/mis/patrol/PATROL_PAGE.md`
- result 形状：array
- 关键返回：`condition`=查询条件，`paging`=分页，`result[]`=人员列表，`totalCount`=总条数
- 适配组件：分页表格、人员列表
- 支持筛选：人员id、姓名、类型、区划、部门、在线状态
- 阻塞项：分页组件需要完整响应包拿 `totalCount`
- 风险：扩展开关会增加查询成本

### PATROL_INFO

- 接口名称：人员详情查询
- 方法：GET
- 接口地址：`/api/cgdb/patrol/info`
- 星桥路径：API平台/悟能接口/城管接口/人员相关/人员详情查询
- detailDoc：`knowledge/api_details/mis/patrol/PATROL_INFO.md`
- result 形状：object
- 关键返回：单个人员详情对象
- 适配组件：详情弹窗、地图点位详情、表格行详情
- 支持筛选：人员id
- 阻塞项：必须确认人员 id 来源
- 风险：头像附件结构需联调确认

### PATROL_GROUP_TYPE

- 接口名称：人员类型分组
- 方法：POST
- 接口地址：`/api/cgdb/patrol/group`
- 星桥路径：API平台/悟能接口/城管接口/人员相关/人员类型分组
- detailDoc：`knowledge/api_details/mis/patrol/PATROL_GROUP_TYPE.md`
- result 形状：array
- 关键返回：`name`=人员类型id，`text`=人员类型名称，`value`=总数，`online`=在线数
- 适配组件：饼图、柱状图、在线统计
- 支持筛选：人员类型、区划、部门、在线状态
- 阻塞项：`groupOnlineFlag=true` 才返回 online
- 风险：不返回人员明细

### PATROL_GROUP_REGION

- 接口名称：人员区划分组
- 方法：POST
- 接口地址：`/api/cgdb/patrol/group?@state=region`
- 星桥路径：API平台/悟能接口/城管接口/人员相关/人员区划分组
- detailDoc：`knowledge/api_details/mis/patrol/PATROL_GROUP_REGION.md`
- result 形状：array
- 关键返回：`name`=区划id，`text`=区划名称，`value`=人员总数
- 适配组件：柱状图、区划排行
- 支持筛选：regionCondition、人员类型、部门、在线状态
- 阻塞项：`regionCondition` 必需
- 风险：展示区划建议同级

### PATROL_GROUP_UNIT

- 接口名称：人员部门分组
- 方法：POST
- 接口地址：`/api/cgdb/patrol/group?@state=unit`
- 星桥路径：API平台/悟能接口/城管接口/人员相关/人员部门分组
- detailDoc：`knowledge/api_details/mis/patrol/PATROL_GROUP_UNIT.md`
- result 形状：array
- 关键返回：`name`=部门id，`text`=部门名称，`value`=人员总数
- 适配组件：柱状图、部门排行
- 支持筛选：unitCondition、人员类型、区划、在线状态
- 阻塞项：`unitCondition` 必需
- 风险：建议带 `deleteFlag=false` 和 `validFlag=true`

### PATROL_TYPE_LIST

- 接口名称：人员类型列表查询
- 方法：POST
- 接口地址：`/api/cgdb/patrol-type/list`
- 星桥路径：API平台/悟能接口/城管接口/人员相关/人员类型列表查询
- detailDoc：`knowledge/api_details/mis/patrol/PATROL_TYPE_LIST.md`
- result 形状：array
- 关键返回：`id`=人员类型id，`displayName`=人员类型名称，`displayOrder`=显示顺序
- 适配组件：下拉筛选、字典列表
- 支持筛选：人员类型id
- 阻塞项：字典接口不返回人员数量
- 风险：按 `displayOrder` 排序

### PATROL_TREE_REGION

- 接口名称：人员区划分组树形
- 方法：POST
- 接口地址：`/api/cgdb/patrol/tree?@state=region`
- 星桥路径：API平台/悟能接口/城管接口/人员相关/人员区划分组树形
- detailDoc：`knowledge/api_details/mis/patrol/PATROL_TREE_REGION.md`
- result 形状：array
- 关键返回：`name`=区划id，`text`=区划名称，`value`=人员总数，`patrolList`=人员简要列表
- 适配组件：区划树、左树右列表、地图区域树
- 支持筛选：regionCondition、showListFlag、人员类型、在线状态
- 阻塞项：`regionCondition` 必需
- 风险：`showListFlag=true` 会增加数据量

### PATROL_TREE_UNIT

- 接口名称：人员部门分组树形
- 方法：POST
- 接口地址：`/api/cgdb/patrol/tree?@state=unit`
- 星桥路径：API平台/悟能接口/城管接口/人员相关/人员部门分组树形
- detailDoc：`knowledge/api_details/mis/patrol/PATROL_TREE_UNIT.md`
- result 形状：array
- 关键返回：`name`=部门id，`text`=部门名称，`value`=人员总数，`patrolList`=人员简要列表，`children`=子部门
- 适配组件：部门树、左树右列表
- 支持筛选：unitCondition、showListFlag、人员类型、在线状态
- 阻塞项：`unitCondition` 必需
- 风险：`showListFlag=true` 会增加数据量

### GRID_PATROL_LIST

- 接口名称：责任网格人员列表
- 方法：POST
- 接口地址：`/api/cgdb/grid-patrol/list`
- 星桥路径：API平台/悟能接口/城管接口/人员相关/责任网格人员列表
- detailDoc：`knowledge/api_details/mis/patrol/GRID_PATROL_LIST.md`
- result 形状：array
- 关键返回：`id`=责任网格id，`patrolId`=人员id，`dutyGrid`=责任网格信息，`patrol`=人员信息
- 适配组件：责任网格人员列表、网格人员点位、网格人员弹窗
- 支持筛选：责任网格id、人员id、人员名称、人员类型
- 阻塞项：`humanDetail=true` 返回较完整人员信息
- 风险：`attachmentFlag=true` 会增加响应体大小

## MIS基础资料

### UNIT_LIST

- 接口名称：部门列表接口
- 方法：POST
- 接口地址：`/api/cgdb/unit/list`
- 星桥路径：API平台/悟能接口/城管接口/部门相关/部门列表接口
- detailDoc：`knowledge/api_details/mis/rec/UNIT_LIST.md`
- result 形状：array
- 关键返回：`id`=部门id，`unitName`=部门名称，`parentId`=上级部门，`unitCode`=部门编码
- 适配组件：部门下拉、部门筛选、组织列表
- 支持筛选：部门id、部门名称、父部门、区划、有效状态
- 阻塞项：建议默认传 `deleteFlag=false,validFlag=true`
- 风险：如需树结构需根据 `parentId` 构建或使用树接口

### ROLE_LIST

- 接口名称：岗位列表接口
- 方法：POST
- 接口地址：`/api/cgdb/role/list`
- 星桥路径：API平台/悟能接口/城管接口/岗位相关/岗位列表接口
- detailDoc：`knowledge/api_details/mis/unit/ROLE_LIST.md`
- result 形状：array
- 关键返回：`id`=岗位id，`roleName`=岗位名称，`roleCode`=岗位编码，`unitId`=所属部门
- 适配组件：岗位下拉、岗位筛选、岗位字典
- 支持筛选：岗位id、岗位名称、部门id、有效状态
- 阻塞项：建议默认传 `deleteFlag=false,validFlag=true`
- 风险：该接口不返回人员明细

### REGION_LIST

- 接口名称：区划列表接口
- 方法：POST
- 接口地址：`/api/cgdb/region/list`
- 星桥路径：API平台/悟能接口/城管接口/区划相关/区划列表接口
- detailDoc：`knowledge/api_details/mis/region/REGION_LIST.md`
- result 形状：array
- 关键返回：`id`=区划id，`regionName`=区划名称，`regionType`=区划类型，`parentId`=父区划
- 适配组件：区划下拉、区域筛选、区划字典
- 支持筛选：区划id、区划名称、区划层级、父区划
- 阻塞项：查询某级区划通常传 `regionType`
- 风险：完整树优先使用 REGION_TREE

### REGION_TREE

- 接口名称：生成区划树接口
- 方法：POST
- 接口地址：`/api/cgdb/region/tree`
- 星桥路径：API平台/悟能接口/城管接口/区划相关/生成区划树接口
- detailDoc：`knowledge/api_details/mis/region/REGION_TREE.md`
- result 形状：array
- 关键返回：`id`=区划id，`regionName`=区划名称，`children`=子区划
- 适配组件：区划树、级联选择器、地图区域树
- 支持筛选：完整区划树
- 阻塞项：暂无传参
- 风险：层级较多时数据量较大













## 汇聚周边搜索

### AGG_RANGE_COUNT

- 接口名称：资源数量
- 方法：POST
- 接口地址：`/api/mixture/range/count`
- 星桥路径：API平台/悟能接口/汇聚接口/周边搜索/资源数量
- detailDoc：`knowledge/api_details/aggregation/range/AGG_RANGE_COUNT.md`
- result 形状：array
- 关键返回：name=资源标识;text=资源名称;value=数量
- 适配组件：指标卡,资源数量卡片,周边搜索统计
- 支持筛选：中心点范围查询资源,中心点范围,中心点纬度,中心点经度,圆心半径,查询资源类型records:案件patrol:人员video:视频设备tcvideo:城管视频,案件查询条件,该参数表示查询案件主键在ids列表中的案件信息,统计指标的开始时间,统计指标的结束时间
- 阻塞项：必须确认中心点经纬度、半径和 keys
- 风险：v22 当前不支持 vehicle 统计，只返回资源类型数量，不返回明细

### AGG_RANGE_LIST

- 接口名称：资源列表
- 方法：POST
- 接口地址：`/api/mixture/range/list`
- 星桥路径：API平台/悟能接口/汇聚接口/周边搜索/资源列表
- detailDoc：`knowledge/api_details/aggregation/range/AGG_RANGE_LIST.md`
- result 形状：object
- 关键返回：recordsList=案件列表;id=主键;address=案发地址;taskNum=任务号;archiveTime=结案时间;bizId=业务标识;dutyGridName=责任网格;cellName=单元网格
- 适配组件：资源列表,表格,地图弹窗,详情入口
- 支持筛选：中心点范围查询资源,中心点范围,中心点纬度,中心点经度,圆心半径,查询资源类型records:案件patrol:人员video:视频设备tcvideo:城管视频,案件查询条件,该参数表示查询案件主键在ids列表中的案件信息,统计指标的开始时间,统计指标的结束时间
- 阻塞项：必须确认中心点经纬度、半径、keys 和各资源分页筛选条件
- 风险：v22 当前不支持 vehicle 完整列表，数据量受半径、keys 和分页条件影响

### AGG_RANGE_SIMPLE_LIST

- 接口名称：资源简要列表
- 方法：POST
- 接口地址：`/api/mixture/range/simple/list`
- 星桥路径：API平台/悟能接口/汇聚接口/周边搜索/资源简要列表
- detailDoc：`knowledge/api_details/aggregation/range/AGG_RANGE_SIMPLE_LIST.md`
- result 形状：object
- 关键返回：recordsList=案件列表;xxx=取决于com_option表里主键为10001的数据的value字段，该字段的一般配置为：[{    "rec_id": "id",    "task_num": "taskNum",    "coordinate_x": "longitude ",    "coordinate_y":"latitude",      "address":"address",      "event_desc":"eventDesc","event_type_name":"eventTypeName","main_type_name":"mainTypeName","sub_type_name":"subTypeName","event_state_name":"eventStateName"}]展示的字段即为value值，更详细描述见城管接口文档-案件接口-案件简要列表;vehicleList=车辆列表;id=车辆id;simCardNum=sim号;vehicleNum=车牌号;unitId=部门id;unitName=部门名称
- 适配组件：地图点位,图层打点,周边资源列表
- 支持筛选：中心点范围查询资源,中心点范围,中心点纬度,中心点经度,圆心半径,查询资源类型records:案件patrol:人员video:视频设备tcvideo:城管视频,案件查询条件,该参数表示查询案件主键在ids列表中的案件信息,统计指标的开始时间,统计指标的结束时间
- 阻塞项：必须确认中心点经纬度、半径、keys 和坐标系
- 风险：v22 简要列表不支持 vehicle/tcvideo，详情字段需调用完整列表或详情接口

## 星揆

### XINGKUI_XK_DEVICE_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-device/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_COUNT.md`
- result 形状：number
- 关键返回：result=设备数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,设备序列号（机场、飞行器、遥控器）,设备型号（对应设备字典表）,绑定设备的用户,设备的自定义名称,当前设备所属的工作区(项目),设备类型（对应设备字典表）,子类型（对应于设备字典表）
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-device/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_INFO.md`
- result 形状：object
- 关键返回：result=单个设备详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_LIST.md`
- result 形状：array
- 关键返回：id=id;deviceSn=设备序列号（机场、飞行器、遥控器）;deviceName=设备型号（对应设备字典表）;userId=绑定设备的用户;nickname=设备的自定义名称;workspaceId=当前设备所属的工作区(项目)
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,设备序列号（机场、飞行器、遥控器）,设备型号（对应设备字典表）,绑定设备的用户,设备的自定义名称,当前设备所属的工作区(项目),设备类型（对应设备字典表）,子类型（对应于设备字典表）
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_PAGE.md`
- result 形状：array
- 关键返回：id=id;deviceSn=设备序列号（机场、飞行器、遥控器）;deviceName=设备型号（对应设备字典表）;userId=绑定设备的用户;nickname=设备的自定义名称;workspaceId=当前设备所属的工作区(项目)
- 适配组件：分页表格,列表
- 支持筛选：id,设备序列号（机场、飞行器、遥控器）,设备型号（对应设备字典表）,绑定设备的用户,设备的自定义名称,当前设备所属的工作区(项目),设备类型（对应设备字典表）,子类型（对应于设备字典表）
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_DEVICE_DICTIONARY_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-dictionary/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/dict/XINGKUI_XK_DEVICE_DICTIONARY_COUNT.md`
- result 形状：number
- 关键返回：result=设备字典数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,设备域（对应于设备字典表 0：飞行器；1：负载；2：遥控器；3：机场）,类型,子类型,设备型号,设备描述
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_DICTIONARY_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-device-dictionary/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/dict/XINGKUI_XK_DEVICE_DICTIONARY_INFO.md`
- result 形状：object
- 关键返回：result=单个设备字典详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_DICTIONARY_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-dictionary/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/dict/XINGKUI_XK_DEVICE_DICTIONARY_LIST.md`
- result 形状：array
- 关键返回：id=id;domain=设备域（对应于设备字典表 0：飞行器；1：负载；2：遥控器；3：机场）;deviceType=类型;subType=子类型;deviceName=设备型号;deviceDesc=设备描述
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,设备域（对应于设备字典表 0：飞行器；1：负载；2：遥控器；3：机场）,类型,子类型,设备型号,设备描述
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_DICTIONARY_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-dictionary/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/dict/XINGKUI_XK_DEVICE_DICTIONARY_PAGE.md`
- result 形状：array
- 关键返回：id=id;domain=设备域（对应于设备字典表 0：飞行器；1：负载；2：遥控器；3：机场）;deviceType=类型;subType=子类型;deviceName=设备型号;deviceDesc=设备描述
- 适配组件：分页表格,列表
- 支持筛选：id,设备域（对应于设备字典表 0：飞行器；1：负载；2：遥控器；3：机场）,类型,子类型,设备型号,设备描述
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_DEVICE_FIRMWARE_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-firmware/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/firmware/XINGKUI_XK_DEVICE_FIRMWARE_COUNT.md`
- result 形状：number
- 关键返回：result=设备固件数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,固件id,固件包的文件名，包括文件后缀,固件版本（需要根据官方固件版本进行格式化：00.00.0000）,存储桶中固件包的对象密钥,固件包的大小,固件包的md5码,工作区id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_FIRMWARE_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-device-firmware/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/firmware/XINGKUI_XK_DEVICE_FIRMWARE_INFO.md`
- result 形状：object
- 关键返回：result=单个设备固件详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_FIRMWARE_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-firmware/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/firmware/XINGKUI_XK_DEVICE_FIRMWARE_LIST.md`
- result 形状：array
- 关键返回：id=id;firmwareId=固件id;fileName=固件包的文件名，包括文件后缀;firmwareVersion=固件版本（需要根据官方固件版本进行格式化：00.00.0000）;objectKey=存储桶中固件包的对象密钥;fileSize=固件包的大小
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,固件id,固件包的文件名，包括文件后缀,固件版本（需要根据官方固件版本进行格式化：00.00.0000）,存储桶中固件包的对象密钥,固件包的大小,固件包的md5码,工作区id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_FIRMWARE_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-firmware/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/firmware/XINGKUI_XK_DEVICE_FIRMWARE_PAGE.md`
- result 形状：array
- 关键返回：id=id;firmwareId=固件id;fileName=固件包的文件名，包括文件后缀;firmwareVersion=固件版本（需要根据官方固件版本进行格式化：00.00.0000）;objectKey=存储桶中固件包的对象密钥;fileSize=固件包的大小
- 适配组件：分页表格,列表
- 支持筛选：id,固件id,固件包的文件名，包括文件后缀,固件版本（需要根据官方固件版本进行格式化：00.00.0000）,存储桶中固件包的对象密钥,固件包的大小,固件包的md5码,工作区id
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_DEVICE_HMS_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-hms/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_HMS_COUNT.md`
- result 形状：number
- 关键返回：result=设备告警数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,告警id,设备报告hms消息时的tid,设备报告hms消息时的bid,报告消息的设备序列号,hms级别（0：通知；1：提醒；2：警告）,信息所属模块（0：飞行任务；1：设备管理；2：媒体；3:hms）,hms消息的密钥，根据该密钥可以获得消息文本
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_HMS_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-device-hms/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_HMS_INFO.md`
- result 形状：object
- 关键返回：result=单个设备告警详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_HMS_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-hms/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_HMS_LIST.md`
- result 形状：array
- 关键返回：id=id;hmsId=告警id;tid=设备报告hms消息时的tid;bid=设备报告hms消息时的bid;sn=报告消息的设备序列号;level=hms级别（0：通知；1：提醒；2：警告）
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,告警id,设备报告hms消息时的tid,设备报告hms消息时的bid,报告消息的设备序列号,hms级别（0：通知；1：提醒；2：警告）,信息所属模块（0：飞行任务；1：设备管理；2：媒体；3:hms）,hms消息的密钥，根据该密钥可以获得消息文本
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_HMS_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-hms/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_HMS_PAGE.md`
- result 形状：array
- 关键返回：id=id;hmsId=告警id;tid=设备报告hms消息时的tid;bid=设备报告hms消息时的bid;sn=报告消息的设备序列号;level=hms级别（0：通知；1：提醒；2：警告）
- 适配组件：分页表格,列表
- 支持筛选：id,告警id,设备报告hms消息时的tid,设备报告hms消息时的bid,报告消息的设备序列号,hms级别（0：通知；1：提醒；2：警告）,信息所属模块（0：飞行任务；1：设备管理；2：媒体；3:hms）,hms消息的密钥，根据该密钥可以获得消息文本
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_DEVICE_LOGS_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-logs/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_LOGS_COUNT.md`
- result 形状：number
- 关键返回：result=设备日志数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,日志id,创建者,设备序列号,日志问题的描述,日志记录问题发生的时间,日志问题状态（1：上传；2：完成；3：取消；4:失败）,更新时间
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_LOGS_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-device-logs/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_LOGS_INFO.md`
- result 形状：object
- 关键返回：result=单个设备日志详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_LOGS_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-logs/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_LOGS_LIST.md`
- result 形状：array
- 关键返回：id=id;logsId=日志id;username=创建者;deviceSn=设备序列号;logsInfo=日志问题的描述;happenTime=日志记录问题发生的时间
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,日志id,创建者,设备序列号,日志问题的描述,日志记录问题发生的时间,日志问题状态（1：上传；2：完成；3：取消；4:失败）,更新时间
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_LOGS_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-logs/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_LOGS_PAGE.md`
- result 形状：array
- 关键返回：id=id;logsId=日志id;username=创建者;deviceSn=设备序列号;logsInfo=日志问题的描述;happenTime=日志记录问题发生的时间
- 适配组件：分页表格,列表
- 支持筛选：id,日志id,创建者,设备序列号,日志问题的描述,日志记录问题发生的时间,日志问题状态（1：上传；2：完成；3：取消；4:失败）,更新时间
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_DEVICE_MATERIAL_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-material/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_MATERIAL_COUNT.md`
- result 形状：number
- 关键返回：result=设备物料数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,自定义图片名称,图片本身名称,存储路径,创建人员名称,创建时间,更新人员名称,更新时间
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_MATERIAL_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-device-material/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_MATERIAL_INFO.md`
- result 形状：object
- 关键返回：result=单个设备物料详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_MATERIAL_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-material/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_MATERIAL_LIST.md`
- result 形状：array
- 关键返回：id=id;name=自定义图片名称;realName=图片本身名称;url=存储路径;creator=创建人员名称;createTime=创建时间
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,自定义图片名称,图片本身名称,存储路径,创建人员名称,创建时间,更新人员名称,更新时间
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_MATERIAL_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-material/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_MATERIAL_PAGE.md`
- result 形状：array
- 关键返回：id=id;name=自定义图片名称;realName=图片本身名称;url=存储路径;creator=创建人员名称;createTime=创建时间
- 适配组件：分页表格,列表
- 支持筛选：id,自定义图片名称,图片本身名称,存储路径,创建人员名称,创建时间,更新人员名称,更新时间
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_DEVICE_PAYLOAD_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-payload/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_PAYLOAD_COUNT.md`
- result 形状：number
- 关键返回：result=设备负载数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,负载设备序列号,负载设备型号（对应设备字典里的设备型号）,负载设备类型（对应设备字典里的设备类型）,负载设备子类型（对应设备字典里的设备子类型）,负载设备的固件版本,负载设备的位置,负载设备所属设备的序列号
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_PAYLOAD_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-device-payload/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_PAYLOAD_INFO.md`
- result 形状：object
- 关键返回：result=单个设备负载详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_PAYLOAD_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-payload/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_PAYLOAD_LIST.md`
- result 形状：array
- 关键返回：id=id;payloadSn=负载设备序列号;payloadName=负载设备型号（对应设备字典里的设备型号）;payloadType=负载设备类型（对应设备字典里的设备类型）;subType=负载设备子类型（对应设备字典里的设备子类型）;firmwareVersion=负载设备的固件版本
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,负载设备序列号,负载设备型号（对应设备字典里的设备型号）,负载设备类型（对应设备字典里的设备类型）,负载设备子类型（对应设备字典里的设备子类型）,负载设备的固件版本,负载设备的位置,负载设备所属设备的序列号
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_PAYLOAD_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-payload/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_PAYLOAD_PAGE.md`
- result 形状：array
- 关键返回：id=id;payloadSn=负载设备序列号;payloadName=负载设备型号（对应设备字典里的设备型号）;payloadType=负载设备类型（对应设备字典里的设备类型）;subType=负载设备子类型（对应设备字典里的设备子类型）;firmwareVersion=负载设备的固件版本
- 适配组件：分页表格,列表
- 支持筛选：id,负载设备序列号,负载设备型号（对应设备字典里的设备型号）,负载设备类型（对应设备字典里的设备类型）,负载设备子类型（对应设备字典里的设备子类型）,负载设备的固件版本,负载设备的位置,负载设备所属设备的序列号
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_DEVICE_PAYLOAD_CONFIG_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-payload-config/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_PAYLOAD_CONFIG_COUNT.md`
- result 形状：number
- 关键返回：result=设备负载配置数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,设备负载编码,对应AI的设备编码,设备编码
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_PAYLOAD_CONFIG_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-device-payload-config/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_PAYLOAD_CONFIG_INFO.md`
- result 形状：object
- 关键返回：result=单个设备负载配置详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_PAYLOAD_CONFIG_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-payload-config/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_PAYLOAD_CONFIG_LIST.md`
- result 形状：array
- 关键返回：id=id;payloadSn=设备负载编码;deviceCode=对应AI的设备编码;deviceSn=设备编码
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,设备负载编码,对应AI的设备编码,设备编码
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DEVICE_PAYLOAD_CONFIG_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-device-payload-config/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DEVICE_PAYLOAD_CONFIG_PAGE.md`
- result 形状：array
- 关键返回：id=id;payloadSn=设备负载编码;deviceCode=对应AI的设备编码;deviceSn=设备编码
- 适配组件：分页表格,列表
- 支持筛选：id,设备负载编码,对应AI的设备编码,设备编码
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_DOCK_DEVICE_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-dock-device/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DOCK_DEVICE_COUNT.md`
- result 形状：number
- 关键返回：result=机场设备数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,设备序列号,机场状态代码(0:空闲中；1:现场调试；2:远程调试；3:固件升级中；4:作业中),使用范围,应急范围,是否模拟飞行：0（否），1（是）
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DOCK_DEVICE_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-dock-device/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DOCK_DEVICE_INFO.md`
- result 形状：object
- 关键返回：result=单个机场设备详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DOCK_DEVICE_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-dock-device/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DOCK_DEVICE_LIST.md`
- result 形状：array
- 关键返回：id=id;deviceSn=设备序列号;modeCode=机场状态代码(0:空闲中；1:现场调试；2:远程调试；3:固件升级中；4:作业中);useRange=使用范围;emergencyRange=应急范围;simulateEnable=是否模拟飞行：0（否），1（是）
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,设备序列号,机场状态代码(0:空闲中；1:现场调试；2:远程调试；3:固件升级中；4:作业中),使用范围,应急范围,是否模拟飞行：0（否），1（是）
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DOCK_DEVICE_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-dock-device/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DOCK_DEVICE_PAGE.md`
- result 形状：array
- 关键返回：id=id;deviceSn=设备序列号;modeCode=机场状态代码(0:空闲中；1:现场调试；2:远程调试；3:固件升级中；4:作业中);useRange=使用范围;emergencyRange=应急范围;simulateEnable=是否模拟飞行：0（否），1（是）
- 适配组件：分页表格,列表
- 支持筛选：id,设备序列号,机场状态代码(0:空闲中；1:现场调试；2:远程调试；3:固件升级中；4:作业中),使用范围,应急范围,是否模拟飞行：0（否），1（是）
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_DRONE_DEVICE_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-drone-device/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DRONE_DEVICE_COUNT.md`
- result 形状：number
- 关键返回：result=飞行器设备数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,设备序列号,飞行器状态（0:待机；1:起飞准备；2:起飞准备完毕；3:手动飞行；4:自动起飞；                 5:航线飞行；6:全景拍照；7:智能跟随；8:ADS-B躲避；9:自动返航；10:自动降落；11:强制降落；                 12:三桨叶降落；13:升级中；14:未连接；15:APAS；16:虚拟摇杆状态；17:指令飞行）,是否开启限远,限远距离,飞行器限高,遥控器失控动作,飞行器夜航灯状态
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DRONE_DEVICE_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-drone-device/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DRONE_DEVICE_INFO.md`
- result 形状：object
- 关键返回：result=单个飞行器设备详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DRONE_DEVICE_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-drone-device/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DRONE_DEVICE_LIST.md`
- result 形状：array
- 关键返回：id=id;deviceSn=设备序列号;modeCode=飞行器状态（0:待机；1:起飞准备；2:起飞准备完毕；3:手动飞行；4:自动起飞；                 5:航线飞行；6:全景拍照；7:智能跟随；8:ADS-B躲避；9:自动返航；10:自动降落；11:强制降落；                 12:三桨叶降落；13:升级中；14:未连接；15:APAS；16:虚拟摇杆状态；17:指令飞行）;distanceLimitState=是否开启限远;distanceLimit=限远距离;heightLimit=飞行器限高
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,设备序列号,飞行器状态（0:待机；1:起飞准备；2:起飞准备完毕；3:手动飞行；4:自动起飞；                 5:航线飞行；6:全景拍照；7:智能跟随；8:ADS-B躲避；9:自动返航；10:自动降落；11:强制降落；                 12:三桨叶降落；13:升级中；14:未连接；15:APAS；16:虚拟摇杆状态；17:指令飞行）,是否开启限远,限远距离,飞行器限高,遥控器失控动作,飞行器夜航灯状态
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_DRONE_DEVICE_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-drone-device/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_DRONE_DEVICE_PAGE.md`
- result 形状：array
- 关键返回：id=id;deviceSn=设备序列号;modeCode=飞行器状态（0:待机；1:起飞准备；2:起飞准备完毕；3:手动飞行；4:自动起飞；                 5:航线飞行；6:全景拍照；7:智能跟随；8:ADS-B躲避；9:自动返航；10:自动降落；11:强制降落；                 12:三桨叶降落；13:升级中；14:未连接；15:APAS；16:虚拟摇杆状态；17:指令飞行）;distanceLimitState=是否开启限远;distanceLimit=限远距离;heightLimit=飞行器限高
- 适配组件：分页表格,列表
- 支持筛选：id,设备序列号,飞行器状态（0:待机；1:起飞准备；2:起飞准备完毕；3:手动飞行；4:自动起飞；                 5:航线飞行；6:全景拍照；7:智能跟随；8:ADS-B躲避；9:自动返航；10:自动降落；11:强制降落；                 12:三桨叶降落；13:升级中；14:未连接；15:APAS；16:虚拟摇杆状态；17:指令飞行）,是否开启限远,限远距离,飞行器限高,遥控器失控动作,飞行器夜航灯状态
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_FIRMWARE_MODEL_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-firmware-model/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/firmware/XINGKUI_XK_FIRMWARE_MODEL_COUNT.md`
- result 形状：number
- 关键返回：result=固件型号数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,固件id,设备型号,创建时间,更新时间
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_FIRMWARE_MODEL_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-firmware-model/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/firmware/XINGKUI_XK_FIRMWARE_MODEL_INFO.md`
- result 形状：object
- 关键返回：result=单个固件型号详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_FIRMWARE_MODEL_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-firmware-model/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/firmware/XINGKUI_XK_FIRMWARE_MODEL_LIST.md`
- result 形状：array
- 关键返回：id=id;firmwareId=固件id;deviceName=设备型号;createTime=创建时间;updateTime=更新时间
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,固件id,设备型号,创建时间,更新时间
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_FIRMWARE_MODEL_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-firmware-model/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/firmware/XINGKUI_XK_FIRMWARE_MODEL_PAGE.md`
- result 形状：array
- 关键返回：id=id;firmwareId=固件id;deviceName=设备型号;createTime=创建时间;updateTime=更新时间
- 适配组件：分页表格,列表
- 支持筛选：id,固件id,设备型号,创建时间,更新时间
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_MEDIA_FILE_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-media-file/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/media/XINGKUI_XK_MEDIA_FILE_COUNT.md`
- result 形状：number
- 关键返回：result=媒体文件数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,文件id,文件名称,文件路径,文件所属工作区id,文件的指纹，此属性仅适用于Pilot上载的媒体文件。,文件的微小指纹，此属性仅适用于Pilot上载的媒体文件。,存储桶中的key
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_MEDIA_FILE_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-media-file/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/media/XINGKUI_XK_MEDIA_FILE_INFO.md`
- result 形状：object
- 关键返回：result=单个媒体文件详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_MEDIA_FILE_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-media-file/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/media/XINGKUI_XK_MEDIA_FILE_LIST.md`
- result 形状：array
- 关键返回：id=id;fileId=文件id;fileName=文件名称;filePath=文件路径;workspaceId=文件所属工作区id;fingerprint=文件的指纹，此属性仅适用于Pilot上载的媒体文件。
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,文件id,文件名称,文件路径,文件所属工作区id,文件的指纹，此属性仅适用于Pilot上载的媒体文件。,文件的微小指纹，此属性仅适用于Pilot上载的媒体文件。,存储桶中的key
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_MEDIA_FILE_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-media-file/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/media/XINGKUI_XK_MEDIA_FILE_PAGE.md`
- result 形状：array
- 关键返回：id=id;fileId=文件id;fileName=文件名称;filePath=文件路径;workspaceId=文件所属工作区id;fingerprint=文件的指纹，此属性仅适用于Pilot上载的媒体文件。
- 适配组件：分页表格,列表
- 支持筛选：id,文件id,文件名称,文件路径,文件所属工作区id,文件的指纹，此属性仅适用于Pilot上载的媒体文件。,文件的微小指纹，此属性仅适用于Pilot上载的媒体文件。,存储桶中的key
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_RC_DEVICE_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-rc-device/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_RC_DEVICE_COUNT.md`
- result 形状：number
- 关键返回：result=遥控器设备数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,设备序列号
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_RC_DEVICE_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-rc-device/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_RC_DEVICE_INFO.md`
- result 形状：object
- 关键返回：result=单个遥控器设备详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_RC_DEVICE_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-rc-device/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_RC_DEVICE_LIST.md`
- result 形状：array
- 关键返回：id=id;deviceSn=设备序列号
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,设备序列号
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_RC_DEVICE_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-rc-device/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/device/XINGKUI_XK_RC_DEVICE_PAGE.md`
- result 形状：array
- 关键返回：id=id;deviceSn=设备序列号
- 适配组件：分页表格,列表
- 支持筛选：id,设备序列号
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_WAYLINE_CONFIG_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-config/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_CONFIG_COUNT.md`
- result 形状：number
- 关键返回：result=航线配置数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,航线名称,航线类型,前端显示的航线类型。0：航点航线；1：块状航线 2：带状航线,机场系列号,巡检半径,参考起飞点经度,参考起飞点纬度
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_CONFIG_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-wayline-config/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_CONFIG_INFO.md`
- result 形状：object
- 关键返回：result=单个航线配置详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_CONFIG_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-config/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_CONFIG_LIST.md`
- result 形状：array
- 关键返回：id=id;name=航线名称;waylineType=航线类型;waylineCategory=前端显示的航线类型。0：航点航线；1：块状航线 2：带状航线;dockSn=机场系列号;inspectionRadius=巡检半径
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,航线名称,航线类型,前端显示的航线类型。0：航点航线；1：块状航线 2：带状航线,机场系列号,巡检半径,参考起飞点经度,参考起飞点纬度
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_CONFIG_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-config/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_CONFIG_PAGE.md`
- result 形状：array
- 关键返回：id=id;name=航线名称;waylineType=航线类型;waylineCategory=前端显示的航线类型。0：航点航线；1：块状航线 2：带状航线;dockSn=机场系列号;inspectionRadius=巡检半径
- 适配组件：分页表格,列表
- 支持筛选：id,航线名称,航线类型,前端显示的航线类型。0：航点航线；1：块状航线 2：带状航线,机场系列号,巡检半径,参考起飞点经度,参考起飞点纬度
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_WAYLINE_CONFIG_ITEM_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-config-item/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_CONFIG_ITEM_COUNT.md`
- result 形状：number
- 关键返回：result=航线配置项数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,键,值
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_CONFIG_ITEM_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-wayline-config-item/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_CONFIG_ITEM_INFO.md`
- result 形状：object
- 关键返回：result=单个航线配置项详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_CONFIG_ITEM_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-config-item/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_CONFIG_ITEM_LIST.md`
- result 形状：array
- 关键返回：id=id;key=键;value=值
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,键,值
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_CONFIG_ITEM_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-config-item/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_CONFIG_ITEM_PAGE.md`
- result 形状：array
- 关键返回：id=id;key=键;value=值
- 适配组件：分页表格,列表
- 支持筛选：id,键,值
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_WAYLINE_FILE_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-file/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_FILE_COUNT.md`
- result 形状：number
- 关键返回：result=航线文件数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,航线名称,航线id,设备产品枚举（格式：domain-device_type-sub_type）,负载产品枚举（格式：domain-device_type-sub_type）,当前航线所属的工作区,航线文件的md5码,是否最受欢迎
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_FILE_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-wayline-file/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_FILE_INFO.md`
- result 形状：object
- 关键返回：result=单个航线文件详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_FILE_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-file/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_FILE_LIST.md`
- result 形状：array
- 关键返回：id=id;name=航线名称;waylineId=航线id;droneModelKey=设备产品枚举（格式：domain-device_type-sub_type）;payloadModelKeys=负载产品枚举（格式：domain-device_type-sub_type）;workspaceId=当前航线所属的工作区
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,航线名称,航线id,设备产品枚举（格式：domain-device_type-sub_type）,负载产品枚举（格式：domain-device_type-sub_type）,当前航线所属的工作区,航线文件的md5码,是否最受欢迎
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_FILE_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-file/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_FILE_PAGE.md`
- result 形状：array
- 关键返回：id=id;name=航线名称;waylineId=航线id;droneModelKey=设备产品枚举（格式：domain-device_type-sub_type）;payloadModelKeys=负载产品枚举（格式：domain-device_type-sub_type）;workspaceId=当前航线所属的工作区
- 适配组件：分页表格,列表
- 支持筛选：id,航线名称,航线id,设备产品枚举（格式：domain-device_type-sub_type）,负载产品枚举（格式：domain-device_type-sub_type）,当前航线所属的工作区,航线文件的md5码,是否最受欢迎
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_WAYLINE_JOB_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-job/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_JOB_COUNT.md`
- result 形状：number
- 关键返回：result=航线任务数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,任务id,任务名称,任务使用的航线文件id,任务执行的主体0:dock,1:rc,执行任务的设备序列号,执行任务的用户id,任务所属的工作区
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_JOB_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-wayline-job/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_JOB_INFO.md`
- result 形状：object
- 关键返回：result=单个航线任务详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_JOB_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-job/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_JOB_LIST.md`
- result 形状：array
- 关键返回：id=id;jobId=任务id;name=任务名称;fileId=任务使用的航线文件id;jobType=任务执行的主体0:dock,1:rc;sn=执行任务的设备序列号
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,任务id,任务名称,任务使用的航线文件id,任务执行的主体0:dock,1:rc,执行任务的设备序列号,执行任务的用户id,任务所属的工作区
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_JOB_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-job/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_JOB_PAGE.md`
- result 形状：array
- 关键返回：id=id;jobId=任务id;name=任务名称;fileId=任务使用的航线文件id;jobType=任务执行的主体0:dock,1:rc;sn=执行任务的设备序列号
- 适配组件：分页表格,列表
- 支持筛选：id,任务id,任务名称,任务使用的航线文件id,任务执行的主体0:dock,1:rc,执行任务的设备序列号,执行任务的用户id,任务所属的工作区
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_WAYLINE_JOB_CONFIG_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-job-config/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_JOB_CONFIG_COUNT.md`
- result 形状：number
- 关键返回：result=航线任务配置数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,配置id,任务名称,任务使用的航线文件id,执行任务的设备序列号,任务执行的主体0:dock,1:rc,任务所属的工作区id,任务类型
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_JOB_CONFIG_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-wayline-job-config/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_JOB_CONFIG_INFO.md`
- result 形状：object
- 关键返回：result=单个航线任务配置详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_JOB_CONFIG_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-job-config/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_JOB_CONFIG_LIST.md`
- result 形状：array
- 关键返回：id=id;configId=配置id;name=任务名称;fileId=任务使用的航线文件id;sn=执行任务的设备序列号;jobType=任务执行的主体0:dock,1:rc
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,配置id,任务名称,任务使用的航线文件id,执行任务的设备序列号,任务执行的主体0:dock,1:rc,任务所属的工作区id,任务类型
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_JOB_CONFIG_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-job-config/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_JOB_CONFIG_PAGE.md`
- result 形状：array
- 关键返回：id=id;configId=配置id;name=任务名称;fileId=任务使用的航线文件id;sn=执行任务的设备序列号;jobType=任务执行的主体0:dock,1:rc
- 适配组件：分页表格,列表
- 支持筛选：id,配置id,任务名称,任务使用的航线文件id,执行任务的设备序列号,任务执行的主体0:dock,1:rc,任务所属的工作区id,任务类型
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_WAYLINE_JOB_GROUP_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-job-group/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_JOB_GROUP_COUNT.md`
- result 形状：number
- 关键返回：result=航线任务分组数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,分组名称,上级分组id,排序因子,分组所属工作区id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_JOB_GROUP_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-wayline-job-group/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_JOB_GROUP_INFO.md`
- result 形状：object
- 关键返回：result=单个航线任务分组详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_JOB_GROUP_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-job-group/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_JOB_GROUP_LIST.md`
- result 形状：array
- 关键返回：id=id;name=分组名称;parentId=上级分组id;orderBy=排序因子;workspaceId=分组所属工作区id
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,分组名称,上级分组id,排序因子,分组所属工作区id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_JOB_GROUP_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-job-group/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_JOB_GROUP_PAGE.md`
- result 形状：array
- 关键返回：id=id;name=分组名称;parentId=上级分组id;orderBy=排序因子;workspaceId=分组所属工作区id
- 适配组件：分页表格,列表
- 支持筛选：id,分组名称,上级分组id,排序因子,分组所属工作区id
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### XINGKUI_XK_WAYLINE_POINT_COUNT

- 接口名称：数量统计
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-point/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_POINT_COUNT.md`
- result 形状：number
- 关键返回：result=航点数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id,航点经度,航点纬度,航点序号,航点绝对高度,航点相对高度,配置id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_POINT_INFO

- 接口名称：详情查询
- 方法：GET
- 接口地址：`/api/xingkui/xk-wayline-point/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_POINT_INFO.md`
- result 形状：object
- 关键返回：result=单个航点详情对象
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_POINT_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-point/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_POINT_LIST.md`
- result 形状：array
- 关键返回：id=id;longitude=航点经度;latitude=航点纬度;orderBy=航点序号;height=航点绝对高度;heightRef=航点相对高度
- 适配组件：表格,列表,下拉筛选
- 支持筛选：id,航点经度,航点纬度,航点序号,航点绝对高度,航点相对高度,配置id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### XINGKUI_XK_WAYLINE_POINT_PAGE

- 接口名称：分页查询
- 方法：POST
- 接口地址：`/api/xingkui/xk-wayline-point/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/xingkui/wayline/XINGKUI_XK_WAYLINE_POINT_PAGE.md`
- result 形状：array
- 关键返回：id=id;longitude=航点经度;latitude=航点纬度;orderBy=航点序号;height=航点绝对高度;heightRef=航点相对高度
- 适配组件：分页表格,列表
- 支持筛选：id,航点经度,航点纬度,航点序号,航点绝对高度,航点相对高度,配置id
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

## 视频

### VIDEO_API_VIDEO_DEVICECATALOG_INFO

- 接口名称：主键查询
- 方法：GET
- 接口地址：`/api/video-devicecatalog/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/catalog/VIDEO_API_VIDEO_DEVICECATALOG_INFO.md`
- result 形状：object
- 关键返回：id=主键;name=名称;grade=级别;parentCode=上级节点Code;code=代码;videoDeviceList=节点视频设备列表；@Transient
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_API_VIDEO_DEVICECATALOG_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/video-devicecatalog/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/catalog/VIDEO_API_VIDEO_DEVICECATALOG_LIST.md`
- result 形状：array
- 关键返回：id=主键;name=名称;grade=级别;parentCode=上级节点Code;code=代码;videoDeviceList=节点视频设备列表；@Transient
- 适配组件：表格,列表,地图图层
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICECATALOG_LIST

- 接口名称：分组列表
- 方法：POST
- 接口地址：`/api/video/videoDeviceCatalog/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/catalog/VIDEO_VIDEODEVICECATALOG_LIST.md`
- result 形状：array
- 关键返回：id=主键;name=名称;grade=级别;parentId=上级节点id;code=代码;videoDeviceList=节点视频设备列表；@Transient
- 适配组件：表格,列表,地图图层
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICECATALOG_TREE

- 接口名称：视频设备分组树
- 方法：POST
- 接口地址：`/api/video/videoDeviceCatalog/tree`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/catalog/VIDEO_VIDEODEVICECATALOG_TREE.md`
- result 形状：array
- 关键返回：id=主键;name=名称;grade=级别;parentId=上级节点id;code=代码;videoDeviceList=节点视频设备列表；@Transient
- 适配组件：树组件,图层树
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICE_COUNT

- 接口名称：视频设备总数
- 方法：POST
- 接口地址：`/api/video/videoDevice/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_COUNT.md`
- result 形状：number
- 关键返回：result=视频设备数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICE_GRIDCODE

- 接口名称：批量修改grid_code
- 方法：PUT
- 接口地址：`/api/video/videoDevice/gridCode`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_GRIDCODE.md`
- result 形状：boolean
- 关键返回：result=批量修改grid_code是否成功
- 适配组件：表格,列表,地图图层
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICE_GROUP_TREE

- 接口名称：视频分组树
- 方法：POST
- 接口地址：`/api/video/videoDevice/group/tree`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_GROUP_TREE.md`
- result 形状：array
- 关键返回：id=主键;name=名称;grade=级别;parentId=上级节点id;code=代码;videoDeviceList=节点视频设备列表；@Transient
- 适配组件：树组件,图层树
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICE_GROUP_STATE_REGION

- 接口名称：视频根据区划分组
- 方法：POST
- 接口地址：`/api/video/videoDevice/group?@state=region`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_GROUP_STATE_REGION.md`
- result 形状：array
- 关键返回：返回区划统计项数据
- 适配组件：图表,统计卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICE_GROUP_STATE_TYPE

- 接口名称：视频根据类型分组
- 方法：POST
- 接口地址：`/api/video/videoDevice/group?@state=type`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_GROUP_STATE_TYPE.md`
- result 形状：object
- 关键返回：result=视频设备类型分组对象
- 适配组件：图表,统计卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICE_INFO

- 接口名称：视频设备详情
- 方法：GET
- 接口地址：`/api/video/videoDevice/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_INFO.md`
- result 形状：object
- 关键返回：id=主键;name=名称;code=编码;manufacturerId=生产厂商;contractorId=建设厂商;type=设备类型；@Transient
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICE_LIST

- 接口名称：视频设备列表
- 方法：POST
- 接口地址：`/api/video/videoDevice/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_LIST.md`
- result 形状：array
- 关键返回：id=主键;name=名称;code=编码;manufacturerId=生产厂商;contractorId=建设厂商;type=设备类型；@Transient
- 适配组件：表格,列表,地图图层
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICE_PAGE

- 接口名称：视频设备分页
- 方法：POST
- 接口地址：`/api/video/videoDevice/page`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_PAGE.md`
- result 形状：array
- 关键返回：id=主键;name=名称;code=编码;manufacturerId=生产厂商;contractorId=建设厂商;type=设备类型；@Transient
- 适配组件：分页表格,列表
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：分页组件需要完整响应包拿 totalCount

### VIDEO_VIDEODEVICE_RANGE_COUNT

- 接口名称：视频搜周边总数
- 方法：POST
- 接口地址：`/api/video/videoDevice/range/count`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_RANGE_COUNT.md`
- result 形状：number
- 关键返回：result=视频设备周边范围数量
- 适配组件：指标卡,总数卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICE_RANGE_LIST

- 接口名称：视频搜周边列表
- 方法：POST
- 接口地址：`/api/video/videoDevice/range/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_RANGE_LIST.md`
- result 形状：array
- 关键返回：id=主键;name=名称;code=编码;manufacturerId=生产厂商;contractorId=建设厂商;type=设备类型；@Transient
- 适配组件：表格,列表,地图图层
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICE_SIMPLE_LIST

- 接口名称：视频设备简要列表
- 方法：POST
- 接口地址：`/api/video/videoDevice/simple/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_SIMPLE_LIST.md`
- result 形状：array
- 关键返回：返回自定义字段数据
- 适配组件：表格,列表,地图图层
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICE_URL

- 接口名称：获取视频直播流地址
- 方法：GET
- 接口地址：`/api/video/videoDevice/url`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_URL.md`
- result 形状：object
- 关键返回：result=直播流地址
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICE_V1_TREE_CATALOG

- 接口名称：视频根据catalog展示树形V1
- 方法：POST
- 接口地址：`/api/video/videoDevice/v1/tree/catalog`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_V1_TREE_CATALOG.md`
- result 形状：array
- 关键返回：id=主键;name=名称;grade=级别;parentId=上级节点id;code=代码;videoDeviceList=节点视频设备列表；@Transient
- 适配组件：树组件,图层树
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_VIDEODEVICE_V2_TREE

- 接口名称：视频分组树
- 方法：POST
- 接口地址：`/api/video/videoDevice/v2/tree`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/device/VIDEO_VIDEODEVICE_V2_TREE.md`
- result 形状：array
- 关键返回：id=主键;name=名称;grade=级别;parentCode=上级节点Code;code=代码;videoDeviceList=节点视频设备列表；@Transient
- 适配组件：树组件,图层树
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_API_VIDEO_CATALOGRELATIONSHIP_INFO

- 接口名称：主键查询
- 方法：GET
- 接口地址：`/api/video-catalogrelationship/info`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/relationship/VIDEO_API_VIDEO_CATALOGRELATIONSHIP_INFO.md`
- result 形状：object
- 关键返回：id=主键;deviceId=设备id;catalogId=目录id
- 适配组件：详情弹窗,详情卡片
- 支持筛选：id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件

### VIDEO_API_VIDEO_CATALOGRELATIONSHIP_LIST

- 接口名称：列表查询
- 方法：POST
- 接口地址：`/api/video-catalogrelationship/list`
- 星桥路径：暂无，需自行在星桥上注册
- detailDoc：`knowledge/api_details/video/relationship/VIDEO_API_VIDEO_CATALOGRELATIONSHIP_LIST.md`
- result 形状：array
- 关键返回：id=主键;deviceId=设备id;catalogId=目录id
- 适配组件：表格,列表,地图图层
- 支持筛选：主键,设备id,目录id
- 阻塞项：星桥接口路径需自行注册
- 风险：按现场数据量控制查询条件
