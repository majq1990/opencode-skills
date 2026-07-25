# 列表查询
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | XINGKUI_XK_WAYLINE_FILE_LIST |
| domain | 星揆 |
| bizObject | 航线文件 |
| apiName | 列表查询 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/xingkui/xk-wayline-file/list` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 表格,列表,下拉筛选 |

---

## 2. 接口说明

该接口用于查询航线文件列表，支持按id、航线名称、航线id、设备产品枚举（格式：domain-device_type-sub_type）、负载产品枚举（格式：domain-device_type-sub_type）、当前航线所属的工作区、航线文件的md5码、是否最受欢迎等条件筛选；返回列表数据，适合表格、下拉或列表组件。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| xingkui | gis_xk_wayline_file | 从返回实体 `@Table` 推断 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| id | String | 否 |  |  | id |
| name | String | 否 |  |  | 航线名称 |
| waylineId | String | 否 |  |  | 航线id |
| droneModelKey | String | 否 |  |  | 设备产品枚举（格式：domain-device_type-sub_type） |
| payloadModelKeys | String | 否 |  |  | 负载产品枚举（格式：domain-device_type-sub_type） |
| workspaceId | String | 否 |  |  | 当前航线所属的工作区 |
| sign | String | 否 |  |  | 航线文件的md5码 |
| favorited | Integer | 否 |  |  | 是否最受欢迎 |
| templateTypes | String | 否 |  |  | 路线文件模板类型（0：航线点） |
| objectKey | String | 否 |  |  | 存储桶中文件的密钥 |
| userName | String | 否 |  |  | 创建者 |
| createTime | Long | 否 |  |  | 创建时间 |
| updateTime | Long | 否 |  |  | 更新时间（必需，不能修改） |
| configId | Integer | 否 |  |  | 配置id |
| referCount | Integer | 否 |  |  | 任务关联数量 |
| isLatest | Integer | 否 |  |  | 是否为最新版本 |
| waylineLength | BigDecimal | 否 |  |  | 航线长度 |
| pointCount | Integer | 否 |  |  | 航点数量 |
| expectedTime | Integer | 否 |  |  | 预计执行时间 |

---

## 5. 请求示例

```json
{
  "id": "",
  "name": "",
  "waylineId": "",
  "droneModelKey": "",
  "payloadModelKeys": "",
  "workspaceId": "",
  "sign": "",
  "favorited": 0,
  "templateTypes": "",
  "objectKey": "",
  "userName": "",
  "createTime": 0
}
```

---

## 6. 返回字段

- `result` 类型：`List<XkWaylineFile>`
- 标准化响应形态：`array`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回对象或列表 |
| +id | String | 否 | 数据库字段：`id` | id |
| +name | String | 否 | 数据库字段：`name` | 航线名称 |
| +waylineId | String | 否 | 数据库字段：`wayline_id` | 航线id |
| +droneModelKey | String | 否 | 数据库字段：`drone_model_key` | 设备产品枚举（格式：domain-device_type-sub_type） |
| +payloadModelKeys | String | 否 | 数据库字段：`payload_model_keys` | 负载产品枚举（格式：domain-device_type-sub_type） |
| +workspaceId | String | 否 | 数据库字段：`workspace_id` | 当前航线所属的工作区 |
| +sign | String | 否 | 数据库字段：`sign` | 航线文件的md5码 |
| +favorited | Integer | 否 | 数据库字段：`favorited` | 是否最受欢迎 |
| +templateTypes | String | 否 | 数据库字段：`template_types` | 路线文件模板类型（0：航线点） |
| +objectKey | String | 否 | 数据库字段：`object_key` | 存储桶中文件的密钥 |
| +userName | String | 否 | 数据库字段：`user_name` | 创建者 |
| +createTime | Long | 否 | 数据库字段：`create_time` | 创建时间 |
| +updateTime | Long | 否 | 数据库字段：`update_time` | 更新时间（必需，不能修改） |
| +configId | Integer | 否 | 数据库字段：`config_id` | 配置id |
| +referCount | Integer | 否 | 数据库字段：`refer_count` | 任务关联数量 |
| +isLatest | Integer | 否 | 数据库字段：`is_latest` | 是否为最新版本 |
| +waylineLength | BigDecimal | 否 | 数据库字段：`wayline_length` | 航线长度 |
| +pointCount | Integer | 否 | 数据库字段：`point_count` | 航点数量 |
| +expectedTime | Integer | 否 | 数据库字段：`expected_time` | 预计执行时间 |
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
      "waylineId": "",
      "droneModelKey": "",
      "payloadModelKeys": "",
      "workspaceId": "",
      "sign": "",
      "favorited": 0,
      "templateTypes": "",
      "objectKey": "",
      "userName": "",
      "createTime": 0
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
