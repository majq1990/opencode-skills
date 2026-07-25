# 视频根据类型分组
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | VIDEO_VIDEODEVICE_GROUP_STATE_TYPE |
| domain | 视频 |
| bizObject | 视频设备类型分组 |
| apiName | 视频根据类型分组 |
| apiType | group |
| 请求方式 | POST |
| 接口地址 | `/api/video/videoDevice/group?@state=type` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | object |
| 适配组件 | 图表,统计卡片 |

---

## 2. 接口说明

该接口用于按视频设备类型分组，先查询视频设备列表，再按设备类型聚合为“类型名称 -> 视频设备列表”的对象结构；支持按设备名称、状态、目录、区域、关键字、关注等条件筛选，适合分类图表或统计卡片。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| video | video_device | 从返回实体和 Service 查询主表推断 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| id | String | 否 |  |  | 主键id |
| ids | List<String> | 否 |  |  | 多个主键id |
| name | String | 否 |  |  | 视频设备名称，支持模糊查询 |
| type | String | 否 |  |  | 视频设备类型 |
| status | Boolean | 否 |  |  | 视频设备状态 |
| videoType | String | 否 |  |  | 视频类型 |
| catalogId | String | 否 |  |  | 所属目录id |
| catalogIdLike | String | 否 |  |  | 所属目录id模糊匹配 |
| catalogIds | List<String> | 否 |  |  | 多个所属目录id |
| severId | String | 否 |  |  | 接入服务id |
| hanhua | String | 否 |  |  | 汉华标识 |
| follow | Boolean | 否 | false |  | 是否关注 |
| loginId | String | 否 |  |  | 登录用户id |
| attentionFlag | Boolean | 否 | false |  | 是否只查关注数据 |
| top | Integer | 否 | 1000 |  | 返回结果条数 |
| regionId | String | 否 |  |  | 区域id，会向下取网格范围 |
| keyword | String | 否 |  |  | 关键字，匹配id或名称 |
| isStar | Boolean | 否 | false |  | 是否收藏 |

---

## 5. 请求示例

```json
{
  "type": "",
  "status": true,
  "catalogId": "",
  "regionId": "",
  "keyword": ""
}
```

---

## 6. 返回字段

- `result` 类型：`Map<String, List<VideoDevice>>`
- 标准化响应形态：`object`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回对象或列表 |
| message | String | 是 |  | 当hasError为true时这里展示报错信息 |
| tag | / | 是 |  | 未使用到 |
| totalCount | Integer | 是 |  | 返回数据的总条数 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": {},
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
