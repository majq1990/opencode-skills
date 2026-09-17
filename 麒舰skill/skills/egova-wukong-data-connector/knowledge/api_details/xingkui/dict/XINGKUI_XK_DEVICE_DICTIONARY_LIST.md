# 列表查询
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | XINGKUI_XK_DEVICE_DICTIONARY_LIST |
| domain | 星揆 |
| bizObject | 设备字典 |
| apiName | 列表查询 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/xingkui/xk-device-dictionary/list` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 表格,列表,下拉筛选 |

---

## 2. 接口说明

该接口用于查询设备字典列表，支持按id、设备域（对应于设备字典表 0：飞行器；1：负载；2：遥控器；3：机场）、类型、子类型、设备型号、设备描述等条件筛选；返回列表数据，适合表格、下拉或列表组件。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| xingkui | gis_xk_device_dictionary | 从返回实体 `@Table` 推断 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| id | String | 否 |  |  | id |
| domain | Integer | 否 |  |  | 设备域（对应于设备字典表 0：飞行器；1：负载；2：遥控器；3：机场） |
| deviceType | Integer | 否 |  |  | 类型 |
| subType | Integer | 否 |  |  | 子类型 |
| deviceName | String | 否 |  |  | 设备型号 |
| deviceDesc | String | 否 |  |  | 设备描述 |

---

## 5. 请求示例

```json
{
  "id": "",
  "domain": 0,
  "deviceType": 0,
  "subType": 0,
  "deviceName": "",
  "deviceDesc": ""
}
```

---

## 6. 返回字段

- `result` 类型：`List<XkDeviceDictionary>`
- 标准化响应形态：`array`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回对象或列表 |
| +id | String | 否 | 数据库字段：`id` | id |
| +domain | Integer | 否 | 数据库字段：`domain` | 设备域（对应于设备字典表 0：飞行器；1：负载；2：遥控器；3：机场） |
| +deviceType | Integer | 否 | 数据库字段：`device_type` | 类型 |
| +subType | Integer | 否 | 数据库字段：`sub_type` | 子类型 |
| +deviceName | String | 否 | 数据库字段：`device_name` | 设备型号 |
| +deviceDesc | String | 否 | 数据库字段：`device_desc` | 设备描述 |
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
      "domain": 0,
      "deviceType": 0,
      "subType": 0,
      "deviceName": "",
      "deviceDesc": ""
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
