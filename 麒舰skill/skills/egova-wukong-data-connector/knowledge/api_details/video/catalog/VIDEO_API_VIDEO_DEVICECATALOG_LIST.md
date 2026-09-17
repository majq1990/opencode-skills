# 列表查询
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | VIDEO_API_VIDEO_DEVICECATALOG_LIST |
| domain | 视频 |
| bizObject | 视频分组V2 |
| apiName | 列表查询 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/video-devicecatalog/list` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 表格,列表,地图图层 |

---

## 2. 接口说明

该接口用于查询视频分组V2列表，支持按id等条件筛选；返回列表数据，适合表格、地图图层或列表组件。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| video | video_devicecatalog | 从返回实体 `@Table` 推断 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| id | String | 否 |  |  | 主键id |

---

## 5. 请求示例

```json
{}
```

---

## 6. 返回字段

- `result` 类型：`List<VideoDeviceCatalogV2>`
- 标准化响应形态：`array`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回对象或列表 |
| +id | String | 否 | 数据库字段：`id` | 主键 |
| +name | String | 否 | 数据库字段：`name` | 名称 |
| +grade | Integer | 否 | 数据库字段：`grade` | 级别 |
| +parentCode | String | 否 | 数据库字段：`parent_code` | 上级节点Code |
| +code | String | 否 | 数据库字段：`code` | 代码 |
| +videoDeviceList | List<VideoDevice> | 否 |  | 节点视频设备列表；@Transient |
| +count | Long | 否 |  | 节点视频设备数量；@Transient |
| +onlineCount | Long | 否 |  | 节点视频设备在线数量；@Transient |
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
      "grade": 0,
      "parentCode": "",
      "code": "",
      "videoDeviceList": [],
      "count": 0,
      "onlineCount": 0
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
