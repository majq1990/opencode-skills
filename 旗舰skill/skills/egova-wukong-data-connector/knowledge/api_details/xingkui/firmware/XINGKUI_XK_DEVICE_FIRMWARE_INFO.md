# 详情查询
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | XINGKUI_XK_DEVICE_FIRMWARE_INFO |
| domain | 星揆 |
| bizObject | 设备固件 |
| apiName | 详情查询 |
| apiType | detail |
| 请求方式 | GET |
| 接口地址 | `/api/xingkui/xk-device-firmware/info` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | object |
| 适配组件 | 详情弹窗,详情卡片 |

---

## 2. 接口说明

该接口用于查询单条设备固件详情，通常按id等主键条件定位；返回对象数据，适合详情弹窗或详情卡片。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| xingkui | gis_xk_device_firmware | 从返回实体 `@Table` 推断 |

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

- `result` 类型：`XkDeviceFirmware`
- 标准化响应形态：`object`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回对象或列表 |
| +id | String | 否 | 数据库字段：`id` | id |
| +firmwareId | String | 否 | 数据库字段：`firmware_id` | 固件id |
| +fileName | String | 否 | 数据库字段：`file_name` | 固件包的文件名，包括文件后缀 |
| +firmwareVersion | String | 否 | 数据库字段：`firmware_version` | 固件版本（需要根据官方固件版本进行格式化：00.00.0000） |
| +objectKey | String | 否 | 数据库字段：`object_key` | 存储桶中固件包的对象密钥 |
| +fileSize | Long | 否 | 数据库字段：`file_size` | 固件包的大小 |
| +fileMd5 | String | 否 | 数据库字段：`file_md5` | 固件包的md5码 |
| +workspaceId | String | 否 | 数据库字段：`workspace_id` | 工作区id |
| +releaseNote | String | 否 | 数据库字段：`release_note` | 固件包的发布说明 |
| +releaseDate | Long | 否 | 数据库字段：`release_date` | 固件包的发布日期 |
| +userName | String | 否 | 数据库字段：`user_name` | 创建者的姓名 |
| +status | Integer | 否 | 数据库字段：`status` | 固件包的可用性（1：可用；0:不可用） |
| +createTime | Long | 否 | 数据库字段：`create_time` | 创建时间 |
| +updateTime | Long | 否 | 数据库字段：`update_time` | 更新时间 |
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
    "firmwareId": "",
    "fileName": "",
    "firmwareVersion": "",
    "objectKey": "",
    "fileSize": 0,
    "fileMd5": "",
    "workspaceId": "",
    "releaseNote": "",
    "releaseDate": 0,
    "userName": "",
    "status": 0
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
