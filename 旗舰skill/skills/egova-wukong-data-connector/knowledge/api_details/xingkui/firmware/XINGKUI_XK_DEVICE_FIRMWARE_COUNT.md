# 数量统计
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | XINGKUI_XK_DEVICE_FIRMWARE_COUNT |
| domain | 星揆 |
| bizObject | 设备固件 |
| apiName | 数量统计 |
| apiType | count |
| 请求方式 | POST |
| 接口地址 | `/api/xingkui/xk-device-firmware/count` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | number |
| 适配组件 | 指标卡,总数卡片 |

---

## 2. 接口说明

该接口用于统计设备固件数量，支持按id、固件id、固件包的文件名，包括文件后缀、固件版本（需要根据官方固件版本进行格式化：00.00.0000）、存储桶中固件包的对象密钥、固件包的大小、固件包的md5码、工作区id等条件筛选；返回值为数量数值，不返回明细列表，适合总数卡片或指标卡。

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
| firmwareId | String | 否 |  |  | 固件id |
| fileName | String | 否 |  |  | 固件包的文件名，包括文件后缀 |
| firmwareVersion | String | 否 |  |  | 固件版本（需要根据官方固件版本进行格式化：00.00.0000） |
| objectKey | String | 否 |  |  | 存储桶中固件包的对象密钥 |
| fileSize | Long | 否 |  |  | 固件包的大小 |
| fileMd5 | String | 否 |  |  | 固件包的md5码 |
| workspaceId | String | 否 |  |  | 工作区id |
| releaseNote | String | 否 |  |  | 固件包的发布说明 |
| releaseDate | Long | 否 |  |  | 固件包的发布日期 |
| userName | String | 否 |  |  | 创建者的姓名 |
| status | Integer | 否 |  |  | 固件包的可用性（1：可用；0:不可用） |
| createTime | Long | 否 |  |  | 创建时间 |
| updateTime | Long | 否 |  |  | 更新时间 |

---

## 5. 请求示例

```json
{
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
