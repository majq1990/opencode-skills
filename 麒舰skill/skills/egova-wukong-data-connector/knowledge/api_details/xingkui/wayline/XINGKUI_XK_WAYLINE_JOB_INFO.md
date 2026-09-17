# 详情查询
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | XINGKUI_XK_WAYLINE_JOB_INFO |
| domain | 星揆 |
| bizObject | 航线任务 |
| apiName | 详情查询 |
| apiType | detail |
| 请求方式 | GET |
| 接口地址 | `/api/xingkui/xk-wayline-job/info` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | object |
| 适配组件 | 详情弹窗,详情卡片 |

---

## 2. 接口说明

该接口用于查询单条航线任务详情，通常按id等主键条件定位；返回对象数据，适合详情弹窗或详情卡片。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| xingkui | gis_xk_wayline_job | 从返回实体 `@Table` 推断 |

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

- `result` 类型：`XkWaylineJob`
- 标准化响应形态：`object`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回对象或列表 |
| +id | String | 否 | 数据库字段：`id` | id |
| +jobId | String | 否 | 数据库字段：`job_id` | 任务id |
| +name | String | 否 | 数据库字段：`name` | 任务名称 |
| +fileId | String | 否 | 数据库字段：`file_id` | 任务使用的航线文件id |
| +jobType | Integer | 否 | 数据库字段：`job_type` | 任务执行的主体0:dock,1:rc |
| +sn | String | 否 | 数据库字段：`sn` | 执行任务的设备序列号 |
| +userId | String | 否 | 数据库字段：`user_id` | 执行任务的用户id |
| +workspaceId | String | 否 | 数据库字段：`workspace_id` | 任务所属的工作区 |
| +taskType | Integer | 否 | 数据库字段：`task_type` | 任务类型 |
| +waylineType | Integer | 否 | 数据库字段：`wayline_type` | 航线的模板类型 |
| +executeTime | Long | 否 | 数据库字段：`execute_time` | 实际开始时间 |
| +completedTime | Long | 否 | 数据库字段：`completed_time` | 实际结束时间 |
| +username | String | 否 | 数据库字段：`username` | 创建者 |
| +beginTime | Long | 否 | 数据库字段：`begin_time` | 计划开始时间 |
| +endTime | Long | 否 | 数据库字段：`end_time` | 计划结束时间 |
| +errorCode | Integer | 否 | 数据库字段：`error_code` | 错误代码 |
| +status | Integer | 否 | 数据库字段：`status` | 任务状态（1：待定；2：正在进行中；3：成功；4：取消；5:失败） |
| +rthAltitude | Integer | 否 | 数据库字段：`rth_altitude` | 返航高度（min: 20m; max: 500m） |
| +outOfControl | Integer | 否 | 数据库字段：`out_of_control` | 失去控制的动作（0：回家；1：悬停；2：着陆） |
| +mediaCount | Integer | 否 | 数据库字段：`media_count` | 媒体文件数量 |
| +createTime | Long | 否 | 数据库字段：`create_time` | 创建时间 |
| +updateTime | Long | 否 | 数据库字段：`update_time` | 更新时间 |
| +parentId | String | 否 | 数据库字段：`parent_id` | 父级id |
| +flightTime | Double | 否 | 数据库字段：`flight_time` | 架次飞行时长 |
| +flightDistance | Double | 否 | 数据库字段：`flight_distance` | 架次飞行里程 |
| +deviceCode | String | 否 | 数据库字段：`device_code` | 负载在AI存储的编码值 |
| +groupId | Integer | 否 | 数据库字段：`group_id` | 所属分组id |
| +jobConfigType | Integer | 否 | 数据库字段：`job_config_type` | 任务类型（0-立即；1-单次定时；2-重复定时） |
| +recordTime | Double | 否 | 数据库字段：`record_time` | 录像时长 |
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
    "jobId": "",
    "name": "",
    "fileId": "",
    "jobType": 0,
    "sn": "",
    "userId": "",
    "workspaceId": "",
    "taskType": 0,
    "waylineType": 0,
    "executeTime": 0,
    "completedTime": 0
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
