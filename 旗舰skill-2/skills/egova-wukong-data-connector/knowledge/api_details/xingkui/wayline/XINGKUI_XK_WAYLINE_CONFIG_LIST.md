# 列表查询
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | XINGKUI_XK_WAYLINE_CONFIG_LIST |
| domain | 星揆 |
| bizObject | 航线配置 |
| apiName | 列表查询 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/xingkui/xk-wayline-config/list` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 表格,列表,下拉筛选 |

---

## 2. 接口说明

该接口用于查询航线配置列表，支持按id、航线名称、航线类型、前端显示的航线类型。0：航点航线；1：块状航线 2：带状航线、机场系列号、巡检半径、参考起飞点经度、参考起飞点纬度等条件筛选；返回列表数据，适合表格、下拉或列表组件。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| xingkui | gis_xk_wayline_config | 从返回实体 `@Table` 推断 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| id | String | 否 |  |  | id |
| name | String | 否 |  |  | 航线名称 |
| waylineType | Integer | 否 |  |  | 航线类型 |
| waylineCategory | Integer | 否 |  |  | 前端显示的航线类型。0：航点航线；1：块状航线 2：带状航线 |
| dockSn | String | 否 |  |  | 机场系列号 |
| inspectionRadius | BigDecimal | 否 |  |  | 巡检半径 |
| takeoffRefLongitude | BigDecimal | 否 |  |  | 参考起飞点经度 |
| takeoffRefLatitude | BigDecimal | 否 |  |  | 参考起飞点纬度 |
| takeoffRefAltitude | BigDecimal | 否 |  |  | 参考起飞点高度 |
| flytoWaylineMode | Integer | 否 |  |  | 飞向首航点模式 1：safely：安全模式；2:pointToPoint：倾斜飞行模式 |
| heightMode | Integer | 否 |  |  | 航线高度模式：0：WGS84：椭球高模式；1：relativeToStartPoint：相对起飞点高度模式；:3：realTimeFollowSurface: 使用实时仿地模式 |
| globalHeight | BigDecimal | 否 |  |  | 航线高度值 |
| takeOffSecurityHeight | BigDecimal | 否 |  |  | 安全起飞高度 [2, 1500] （高度模式：相对起飞点高度） |
| autoFlightSpeed | BigDecimal | 否 |  |  | 全局航线速度 |
| cameraMode | Integer | 否 |  |  | 相机模式 |
| cameraPitchAngle | BigDecimal | 否 |  |  | 相机俯仰角 |
| waylineLength | BigDecimal | 否 |  |  | 航线长度 |
| pointCount | Integer | 否 |  |  | 航点数量 |
| expectedTime | Integer | 否 |  |  | 预计执行时间 |
| workspaceId | String | 否 |  |  | 当前航线所属的工作区 |
| createTime | Long | 否 |  |  | 创建时间 |
| updateTime | Long | 否 |  |  | 更新时间 |
| droneModelKey | String | 否 |  |  | 设备产品枚举（格式：domain-device_type-sub_type） |
| payloadModelKeys | String | 否 |  |  | 负载产品枚举（格式：domain-device_type-sub_type） |
| globalRthHeight | Double | 否 |  |  | 全局返航高度 |

---

## 5. 请求示例

```json
{
  "id": "",
  "name": "",
  "waylineType": 0,
  "waylineCategory": 0,
  "dockSn": "",
  "inspectionRadius": 0,
  "takeoffRefLongitude": 0,
  "takeoffRefLatitude": 0,
  "takeoffRefAltitude": 0,
  "flytoWaylineMode": 0,
  "heightMode": 0,
  "globalHeight": 0
}
```

---

## 6. 返回字段

- `result` 类型：`List<XkWaylineConfig>`
- 标准化响应形态：`array`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回对象或列表 |
| +id | String | 否 | 数据库字段：`id` | id |
| +name | String | 否 | 数据库字段：`name` | 航线名称 |
| +waylineType | Integer | 否 | 数据库字段：`wayline_type` | 航线类型 |
| +waylineCategory | Integer | 否 | 数据库字段：`wayline_category` | 前端显示的航线类型。0：航点航线；1：块状航线 2：带状航线 |
| +dockSn | String | 否 | 数据库字段：`dock_sn` | 机场系列号 |
| +inspectionRadius | BigDecimal | 否 | 数据库字段：`inspection_radius` | 巡检半径 |
| +takeoffRefLongitude | BigDecimal | 否 | 数据库字段：`takeoff_ref_longitude` | 参考起飞点经度 |
| +takeoffRefLatitude | BigDecimal | 否 | 数据库字段：`takeoff_ref_latitude` | 参考起飞点纬度 |
| +takeoffRefAltitude | BigDecimal | 否 | 数据库字段：`takeoff_ref_altitude` | 参考起飞点高度 |
| +flytoWaylineMode | Integer | 否 | 数据库字段：`flyto_wayline_mode` | 飞向首航点模式 1：safely：安全模式；2:pointToPoint：倾斜飞行模式 |
| +heightMode | Integer | 否 | 数据库字段：`height_mode` | 航线高度模式：0：WGS84：椭球高模式；1：relativeToStartPoint：相对起飞点高度模式；:3：realTimeFollowSurface: 使用实时仿地模式 |
| +globalHeight | BigDecimal | 否 | 数据库字段：`global_height` | 航线高度值 |
| +takeOffSecurityHeight | BigDecimal | 否 | 数据库字段：`take_off_security_height` | 安全起飞高度 [2, 1500] （高度模式：相对起飞点高度） |
| +autoFlightSpeed | BigDecimal | 否 | 数据库字段：`auto_flight_speed` | 全局航线速度 |
| +cameraMode | Integer | 否 | 数据库字段：`camera_mode` | 相机模式 |
| +cameraPitchAngle | BigDecimal | 否 | 数据库字段：`camera_pitch_angle` | 相机俯仰角 |
| +waylineLength | BigDecimal | 否 | 数据库字段：`wayline_length` | 航线长度 |
| +pointCount | Integer | 否 | 数据库字段：`point_count` | 航点数量 |
| +expectedTime | Integer | 否 | 数据库字段：`expected_time` | 预计执行时间 |
| +workspaceId | String | 否 | 数据库字段：`workspace_id` | 当前航线所属的工作区 |
| +createTime | Long | 否 | 数据库字段：`create_time` | 创建时间 |
| +updateTime | Long | 否 | 数据库字段：`update_time` | 更新时间 |
| +droneModelKey | String | 否 | 数据库字段：`drone_model_key` | 设备产品枚举（格式：domain-device_type-sub_type） |
| +payloadModelKeys | String | 否 | 数据库字段：`payload_model_keys` | 负载产品枚举（格式：domain-device_type-sub_type） |
| +globalRthHeight | Double | 否 | 数据库字段：`global_rth_height` | 全局返航高度 |
| message | String | 是 |  | 当hasError为true时这里展示报错信息 |
| tag | / | 是 |  | 未使用到 |
| totalCount | Integer | 是 |  | 返回数据的总条数 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "id": "",
      "name": "",
      "waylineType": 0,
      "waylineCategory": 0,
      "dockSn": "",
      "inspectionRadius": 0,
      "takeoffRefLongitude": 0,
      "takeoffRefLatitude": 0,
      "takeoffRefAltitude": 0,
      "flytoWaylineMode": 0,
      "heightMode": 0,
      "globalHeight": 0
    }
  ],
  "message": null,
  "tag": null,
  "totalCount": 0
}
```

---

## 8. 报错说明

| message信息 | 说明 |
| --- | --- |
| 其他报错 | 需联系后台排查数据 |

---

## 9. 字段转换建议

- `filter(data)` 默认接收外层响应的 `result` 本体；只有现场明确传入完整外层响应包时，才读取 `data.result` 或 `data.totalCount`。

- 本文件字段主要从 Java 实体/DTO 字段注释推断；落地前需用实际接口返回样例核对字段是否全部返回、是否有动态扩展字段。
- 星桥接口路径当前按规则标记为“暂无，需自行在星桥上注册”。
