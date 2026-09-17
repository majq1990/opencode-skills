# 视频设备详情
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | VIDEO_VIDEODEVICE_INFO |
| domain | 视频 |
| bizObject | 视频设备 |
| apiName | 视频设备详情 |
| apiType | detail |
| 请求方式 | GET |
| 接口地址 | `/api/video/videoDevice/info` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | object |
| 适配组件 | 详情弹窗,详情卡片 |

---

## 2. 接口说明

该接口用于查询视频设备详情，按视频设备id定位，可传 loginId 关联关注状态；返回视频设备对象，适合详情弹窗、详情卡片或视频播放前置查询。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| video | video_device | 从返回实体 `@Table` 推断 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| id | String | 是 |  |  | 视频设备id |
| loginId | String | 否 | -1 |  | 登录用户id，用于判断关注状态 |

---

## 5. 请求示例

```json
{
  "id": "",
  "loginId": ""
}
```

---

## 6. 返回字段

- `result` 类型：`VideoDevice`
- 标准化响应形态：`object`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回对象或列表 |
| +id | String | 否 | 数据库字段：`id` | 主键 |
| +name | String | 否 | 数据库字段：`name` | 名称 |
| +code | String | 否 | 数据库字段：`code` | 编码 |
| +manufacturerId | String | 否 |  | 生产厂商 |
| +contractorId | String | 否 |  | 建设厂商 |
| +type | String | 否 |  | 设备类型；@Transient |
| +departmentId | String | 否 | 数据库字段：`department_id` | 所属单位 |
| +url | String | 否 | 数据库字段：`url` | 地址 |
| +status | Boolean | 否 | 数据库字段：`status` | 状态 |
| +longitude | Double | 否 | 数据库字段：`longitude` | 经度 |
| +latitude | Double | 否 | 数据库字段：`latitude` | 纬度 |
| +lastActiveTime | LocalDateTime | 否 |  | lastactivetime |
| +disabled | Boolean | 否 | 数据库字段：`disabled` | 是否禁用 |
| +location | String | 否 | 数据库字段：`location` | 地点 |
| +distance | Double | 否 |  | 地点；@Transient |
| +catalogId | String | 否 | 数据库字段：`catalog_id` | 所属分类catalogId |
| +catalogIds | List<String> | 否 |  | 多个分类；@Transient |
| +isStar | Boolean | 否 |  | 是否收藏；@Transient |
| +sourceType | String | 否 |  | 收藏的topic；@Transient |
| +videoDeviceServerDic | VideoDeviceServerDic | 否 |  | 接入服务video_deviceserver表 |
| +serverId | String | 否 |  | 接入服务video_deviceserver表id |
| +hasFollow | Boolean | 否 |  | 关注信息；@Transient |
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
    "name": "",
    "code": "",
    "manufacturerId": "",
    "contractorId": "",
    "type": "",
    "departmentId": "",
    "url": "",
    "status": false,
    "longitude": 0,
    "latitude": 0,
    "lastActiveTime": ""
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
