# 列表查询
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | XINGKUI_XK_MEDIA_FILE_LIST |
| domain | 星揆 |
| bizObject | 媒体文件 |
| apiName | 列表查询 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/xingkui/xk-media-file/list` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 表格,列表,下拉筛选 |

---

## 2. 接口说明

该接口用于查询媒体文件列表，支持按id、文件id、文件名称、文件路径、文件所属工作区id、文件的指纹，此属性仅适用于Pilot上载的媒体文件。、文件的微小指纹，此属性仅适用于Pilot上载的媒体文件。、存储桶中的key等条件筛选；返回列表数据，适合表格、下拉或列表组件。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| xingkui | gis_xk_media_file | 从返回实体 `@Table` 推断 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| id | String | 否 |  |  | id |
| fileId | String | 否 |  |  | 文件id |
| fileName | String | 否 |  |  | 文件名称 |
| filePath | String | 否 |  |  | 文件路径 |
| workspaceId | String | 否 |  |  | 文件所属工作区id |
| fingerprint | String | 否 |  |  | 文件的指纹，此属性仅适用于Pilot上载的媒体文件。 |
| tinnyFingerprint | String | 否 |  |  | 文件的微小指纹，此属性仅适用于Pilot上载的媒体文件。 |
| objectKey | String | 否 |  |  | 存储桶中的key |
| subFileType | Integer | 否 |  |  | 此属性仅适用于Pilot上载的图像文件。0：正常图片；1：全景。 |
| isOriginal | Integer | 否 |  |  | 是否为原始图像 |
| drone | String | 否 |  |  | 创建文件的无人机的sn |
| payload | String | 否 |  |  | 创建文件的无人机有效载荷的名称 |
| jobId | String | 否 |  |  | wayline_job表中的job_id。文件是否属于停靠任务。 |
| longitude | BigDecimal | 否 |  |  | 拍摄经度 |
| latitude | BigDecimal | 否 |  |  | 拍摄纬度 |
| gimbalYawDegree | Double | 否 |  |  | 云台偏航角度 |
| height | Double | 否 |  |  | 绝对高度 |
| createTime | Long | 否 |  |  | 创建时间 |
| updateTime | Long | 否 |  |  | 更新时间 |
| deleteStatus | Integer | 否 |  |  | 删除状态标识 |

---

## 5. 请求示例

```json
{
  "id": "",
  "fileId": "",
  "fileName": "",
  "filePath": "",
  "workspaceId": "",
  "fingerprint": "",
  "tinnyFingerprint": "",
  "objectKey": "",
  "subFileType": 0,
  "isOriginal": 0,
  "drone": "",
  "payload": ""
}
```

---

## 6. 返回字段

- `result` 类型：`List<XkMediaFile>`
- 标准化响应形态：`array`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回对象或列表 |
| +id | String | 否 | 数据库字段：`id` | id |
| +fileId | String | 否 | 数据库字段：`file_id` | 文件id |
| +fileName | String | 否 | 数据库字段：`file_name` | 文件名称 |
| +filePath | String | 否 | 数据库字段：`file_path` | 文件路径 |
| +workspaceId | String | 否 | 数据库字段：`workspace_id` | 文件所属工作区id |
| +fingerprint | String | 否 | 数据库字段：`fingerprint` | 文件的指纹，此属性仅适用于Pilot上载的媒体文件。 |
| +tinnyFingerprint | String | 否 | 数据库字段：`tinny_fingerprint` | 文件的微小指纹，此属性仅适用于Pilot上载的媒体文件。 |
| +objectKey | String | 否 | 数据库字段：`object_key` | 存储桶中的key |
| +subFileType | Integer | 否 | 数据库字段：`sub_file_type` | 此属性仅适用于Pilot上载的图像文件。0：正常图片；1：全景。 |
| +isOriginal | Integer | 否 | 数据库字段：`is_original` | 是否为原始图像 |
| +drone | String | 否 | 数据库字段：`drone` | 创建文件的无人机的sn |
| +payload | String | 否 | 数据库字段：`payload` | 创建文件的无人机有效载荷的名称 |
| +jobId | String | 否 | 数据库字段：`job_id` | wayline_job表中的job_id。文件是否属于停靠任务。 |
| +longitude | BigDecimal | 否 | 数据库字段：`longitude` | 拍摄经度 |
| +latitude | BigDecimal | 否 | 数据库字段：`latitude` | 拍摄纬度 |
| +gimbalYawDegree | Double | 否 | 数据库字段：`gimbal_yaw_degree` | 云台偏航角度 |
| +height | Double | 否 | 数据库字段：`height` | 绝对高度 |
| +createTime | Long | 否 | 数据库字段：`create_time` | 创建时间 |
| +updateTime | Long | 否 | 数据库字段：`update_time` | 更新时间 |
| +deleteStatus | Integer | 否 | 数据库字段：`delete_status` | 删除状态标识 |
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
      "fileId": "",
      "fileName": "",
      "filePath": "",
      "workspaceId": "",
      "fingerprint": "",
      "tinnyFingerprint": "",
      "objectKey": "",
      "subFileType": 0,
      "isOriginal": 0,
      "drone": "",
      "payload": ""
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
