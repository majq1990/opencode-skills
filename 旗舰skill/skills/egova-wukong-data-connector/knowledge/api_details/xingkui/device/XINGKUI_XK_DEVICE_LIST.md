# 列表查询
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | XINGKUI_XK_DEVICE_LIST |
| domain | 星揆 |
| bizObject | 设备 |
| apiName | 列表查询 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/xingkui/xk-device/list` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 表格,列表,下拉筛选 |

---

## 2. 接口说明

该接口用于查询设备列表，支持按id、设备序列号（机场、飞行器、遥控器）、设备型号（对应设备字典表）、绑定设备的用户、设备的自定义名称、当前设备所属的工作区(项目)、设备类型（对应设备字典表）、子类型（对应于设备字典表）等条件筛选；返回列表数据，适合表格、下拉或列表组件。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| xingkui | gis_xk_device | 从返回实体 `@Table` 推断 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| id | String | 否 |  |  | id |
| deviceSn | String | 否 |  |  | 设备序列号（机场、飞行器、遥控器） |
| deviceName | String | 否 |  |  | 设备型号（对应设备字典表） |
| userId | String | 否 |  |  | 绑定设备的用户 |
| nickname | String | 否 |  |  | 设备的自定义名称 |
| workspaceId | String | 否 |  |  | 当前设备所属的工作区(项目) |
| deviceType | Integer | 否 |  |  | 设备类型（对应设备字典表） |
| subType | Integer | 否 |  |  | 子类型（对应于设备字典表） |
| domain | Integer | 否 |  |  | 设备域（对应于设备字典表 0：飞行器；1：负载；2：遥控器；3：机场） |
| firmwareVersion | String | 否 |  |  | 设备的固件版本 |
| compatibleStatus | Integer | 否 |  |  | 固件版本是否一致（1：一致；0：不一致） |
| version | String | 否 |  |  | 协议的版本（此字段当前无效） |
| deviceIndex | String | 否 |  |  | 飞行器控制（A控制或B控制） |
| childSn | String | 否 |  |  | 由网关控制的设备 |
| createTime | Long | 否 |  |  | 创建时间 |
| updateTime | Long | 否 |  |  | 更新时间 |
| boundTime | Long | 否 |  |  | 设备绑定到工作区的时间 |
| boundStatus | Integer | 否 |  |  | 设备绑定到工作区时的状态（1：绑定；0:未绑定） |
| loginTime | Long | 否 |  |  | 设备最后一次登录的时间 |
| deviceDesc | String | 否 |  |  | 设备描述 |
| urlNormal | String | 否 |  |  | 正常情况下显示在遥控器上的图标 |
| urlSelect | String | 否 |  |  | 选择时显示在遥控器上的图标 |
| longitude | Double | 否 |  |  | 设备最后一次坐标点位置经度 |
| latitude | Double | 否 |  |  | 设备最后一次坐标点位置纬度 |

---

## 5. 请求示例

```json
{
  "id": "",
  "deviceSn": "",
  "deviceName": "",
  "userId": "",
  "nickname": "",
  "workspaceId": "",
  "deviceType": 0,
  "subType": 0,
  "domain": 0,
  "firmwareVersion": "",
  "compatibleStatus": 0,
  "version": ""
}
```

---

## 6. 返回字段

- `result` 类型：`List<XkDevice>`
- 标准化响应形态：`array`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回对象或列表 |
| +id | String | 否 | 数据库字段：`id` | id |
| +deviceSn | String | 否 | 数据库字段：`device_sn` | 设备序列号（机场、飞行器、遥控器） |
| +deviceName | String | 否 | 数据库字段：`device_name` | 设备型号（对应设备字典表） |
| +userId | String | 否 | 数据库字段：`user_id` | 绑定设备的用户 |
| +nickname | String | 否 | 数据库字段：`nickname` | 设备的自定义名称 |
| +workspaceId | String | 否 | 数据库字段：`workspace_id` | 当前设备所属的工作区(项目) |
| +deviceType | Integer | 否 | 数据库字段：`device_type` | 设备类型（对应设备字典表） |
| +subType | Integer | 否 | 数据库字段：`sub_type` | 子类型（对应于设备字典表） |
| +domain | Integer | 否 | 数据库字段：`domain` | 设备域（对应于设备字典表 0：飞行器；1：负载；2：遥控器；3：机场） |
| +firmwareVersion | String | 否 | 数据库字段：`firmware_version` | 设备的固件版本 |
| +compatibleStatus | Integer | 否 | 数据库字段：`compatible_status` | 固件版本是否一致（1：一致；0：不一致） |
| +version | String | 否 | 数据库字段：`version` | 协议的版本（此字段当前无效） |
| +deviceIndex | String | 否 | 数据库字段：`device_index` | 飞行器控制（A控制或B控制） |
| +childSn | String | 否 | 数据库字段：`child_sn` | 由网关控制的设备 |
| +createTime | Long | 否 | 数据库字段：`create_time` | 创建时间 |
| +updateTime | Long | 否 | 数据库字段：`update_time` | 更新时间 |
| +boundTime | Long | 否 | 数据库字段：`bound_time` | 设备绑定到工作区的时间 |
| +boundStatus | Integer | 否 | 数据库字段：`bound_status` | 设备绑定到工作区时的状态（1：绑定；0:未绑定） |
| +loginTime | Long | 否 | 数据库字段：`login_time` | 设备最后一次登录的时间 |
| +deviceDesc | String | 否 | 数据库字段：`device_desc` | 设备描述 |
| +urlNormal | String | 否 | 数据库字段：`url_normal` | 正常情况下显示在遥控器上的图标 |
| +urlSelect | String | 否 | 数据库字段：`url_select` | 选择时显示在遥控器上的图标 |
| +longitude | Double | 否 | 数据库字段：`longitude` | 设备最后一次坐标点位置经度 |
| +latitude | Double | 否 | 数据库字段：`latitude` | 设备最后一次坐标点位置纬度 |
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
      "deviceSn": "",
      "deviceName": "",
      "userId": "",
      "nickname": "",
      "workspaceId": "",
      "deviceType": 0,
      "subType": 0,
      "domain": 0,
      "firmwareVersion": "",
      "compatibleStatus": 0,
      "version": ""
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
