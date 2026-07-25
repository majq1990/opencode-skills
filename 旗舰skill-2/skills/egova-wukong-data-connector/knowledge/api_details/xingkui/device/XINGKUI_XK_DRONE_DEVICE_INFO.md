# 详情查询
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | XINGKUI_XK_DRONE_DEVICE_INFO |
| domain | 星揆 |
| bizObject | 飞行器设备 |
| apiName | 详情查询 |
| apiType | detail |
| 请求方式 | GET |
| 接口地址 | `/api/xingkui/xk-drone-device/info` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | object |
| 适配组件 | 详情弹窗,详情卡片 |

---

## 2. 接口说明

该接口用于查询单条飞行器设备详情，通常按id等主键条件定位；返回对象数据，适合详情弹窗或详情卡片。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| xingkui | gis_xk_drone_device | 从返回实体 `@Table` 推断 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| id | String | 否 |  |  | id |

---

## 5. 请求示例

```json
{
  "id": ""
}
```

---

## 6. 返回字段

- `result` 类型：`XkDroneDevice`
- 标准化响应形态：`object`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回对象或列表 |
| +id | String | 否 | 数据库字段：`id` | id |
| +deviceSn | String | 否 | 数据库字段：`device_sn` | 设备序列号 |
| +modeCode | Integer | 否 | 数据库字段：`mode_code` | 飞行器状态（0:待机；1:起飞准备；2:起飞准备完毕；3:手动飞行；4:自动起飞；                 5:航线飞行；6:全景拍照；7:智能跟随；8:ADS-B躲避；9:自动返航；10:自动降落；11:强制降落；                 12:三桨叶降落；13:升级中；14:未连接；15:APAS；16:虚拟摇杆状态；17:指令飞行） |
| +distanceLimitState | Integer | 否 | 数据库字段：`distance_limit_state` | 是否开启限远 |
| +distanceLimit | Integer | 否 | 数据库字段：`distance_limit` | 限远距离 |
| +heightLimit | Integer | 否 | 数据库字段：`height_limit` | 飞行器限高 |
| +rcLostAction | Integer | 否 | 数据库字段：`rc_lost_action` | 遥控器失控动作 |
| +nightLightsState | Integer | 否 | 数据库字段：`night_lights_state` | 飞行器夜航灯状态 |
| +totalFlightTime | Double | 否 | 数据库字段：`total_flight_time` | totalflight时间 |
| +totalFlightDistance | Double | 否 | 数据库字段：`total_flight_distance` | 累计飞行里程 |
| +totalFlightSorties | Integer | 否 | 数据库字段：`total_flight_sorties` | 累计飞行架次 |
| message | String | 是 |  | 当hasError为true时这里展示报错信息 |
| tag | / | 是 |  | 未使用到 |
| totalCount | Integer | 是 |  | 返回数据的总条数 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": {
    "id": "",
    "deviceSn": "",
    "modeCode": 0,
    "distanceLimitState": 0,
    "distanceLimit": 0,
    "heightLimit": 0,
    "rcLostAction": 0,
    "nightLightsState": 0,
    "totalFlightTime": 0,
    "totalFlightDistance": 0,
    "totalFlightSorties": 0
  },
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
