# 数量统计
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | XINGKUI_XK_WAYLINE_CONFIG_COUNT |
| domain | 星揆 |
| bizObject | 航线配置 |
| apiName | 数量统计 |
| apiType | count |
| 请求方式 | POST |
| 接口地址 | `/api/xingkui/xk-wayline-config/count` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | number |
| 适配组件 | 指标卡,总数卡片 |

---

## 2. 接口说明

该接口用于统计航线配置数量，支持按id、航线名称、航线类型、前端显示的航线类型。0：航点航线；1：块状航线 2：带状航线、机场系列号、巡检半径、参考起飞点经度、参考起飞点纬度等条件筛选；返回值为数量数值，不返回明细列表，适合总数卡片或指标卡。

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

- `result` 类型：`Long`
- 标准化响应形态：`number`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Long | 是 |  | 接口返回值 |
| message | String | 是 |  | 当hasError为true时这里展示报错信息 |
| tag | / | 是 |  | 未使用到 |
| totalCount | Integer | 是 |  | 返回数据的总条数 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": 0,
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
