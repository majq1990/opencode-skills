# 分页查询
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | XINGKUI_XK_WAYLINE_JOB_CONFIG_PAGE |
| domain | 星揆 |
| bizObject | 航线任务配置 |
| apiName | 分页查询 |
| apiType | page |
| 请求方式 | POST |
| 接口地址 | `/api/xingkui/xk-wayline-job-config/page` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 分页表格,列表 |

---

## 2. 接口说明

该接口用于分页查询航线任务配置数据，支持按id、配置id、任务名称、任务使用的航线文件id、执行任务的设备序列号、任务执行的主体0:dock,1:rc、任务所属的工作区id、任务类型等条件筛选；返回分页结果，适合分页表格或列表组件。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| xingkui | gis_xk_wayline_job_config | 从返回实体 `@Table` 推断 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| id | String | 否 |  |  | id |
| configId | String | 否 |  |  | 配置id |
| name | String | 否 |  |  | 任务名称 |
| fileId | String | 否 |  |  | 任务使用的航线文件id |
| sn | String | 否 |  |  | 执行任务的设备序列号 |
| jobType | Integer | 否 |  |  | 任务执行的主体0:dock,1:rc |
| workspaceId | String | 否 |  |  | 任务所属的工作区id |
| taskType | Integer | 否 |  |  | 任务类型 |
| waylineType | Integer | 否 |  |  | 路线的模板类型 |
| executeTime | Long | 否 |  |  | 实际开始时间 |
| completedTime | Long | 否 |  |  | 实际结束时间 |
| username | String | 否 |  |  | 创建者 |
| beginTime | Long | 否 |  |  | 计划开始时间 |
| endTime | Long | 否 |  |  | 计划结束时间 |
| errorCode | Integer | 否 |  |  | 错误代码 |
| status | Integer | 否 |  |  | 任务状态（1：待定；2：正在进行中；3：成功；4：取消；5:失败） |
| rthAltitude | Integer | 否 |  |  | 返航高度（min: 20m; max: 500m） |
| outOfControl | Integer | 否 |  |  | 失去控制的动作（0：回家；1：悬停；2：着陆） |
| mediaCount | Integer | 否 |  |  | 媒体文件数量 |
| createTime | Long | 否 |  |  | 创建时间 |
| updateTime | Long | 否 |  |  | 更新时间 |
| repeatType | Integer | 否 |  |  | 重复类型：0 天；1 周；2 月；3 不重复 |
| repeatGap | Integer | 否 |  |  | 间隔时间 |
| taskDayPeriod | String | 否 |  |  | 执行日期区间 |
| taskMoments | String | 否 |  |  | 执行时刻集合 |
| taskTimes | String | 否 |  |  | 执行的时间，当repeat_type=0时为空，=1时为1，2，3...，=2时为1，2，3... |
| maxDelayDuration | Integer | 否 |  |  | 最长延期时长 |
| minBatteryCapacity | Integer | 否 |  |  | 可执行任务的飞行器电池电量百分比阈值 |
| minStorageCapacity | Integer | 否 |  |  | 可执行任务的机场或飞行器最低存储容量 |
| breakpointFlight | Integer | 否 |  |  | 是否开启自动断点续飞，0未开启，1开启 |
| jobConfigType | Integer | 否 |  |  | 任务类型（0-立即；1-单次定时；2-重复定时） |
| groupId | Integer | 否 |  |  | 所属分组id |

---

## 5. 请求示例

```json
{
  "id": "",
  "configId": "",
  "name": "",
  "fileId": "",
  "sn": "",
  "jobType": 0,
  "workspaceId": "",
  "taskType": 0,
  "waylineType": 0,
  "executeTime": 0,
  "completedTime": 0,
  "username": ""
}
```

---

## 6. 返回字段

- `result` 类型：`PageResult<XkWaylineJobConfig>`
- 标准化响应形态：`array`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回对象或列表 |
| +id | String | 否 | 数据库字段：`id` | id |
| +configId | String | 否 | 数据库字段：`config_id` | 配置id |
| +name | String | 否 | 数据库字段：`name` | 任务名称 |
| +fileId | String | 否 | 数据库字段：`file_id` | 任务使用的航线文件id |
| +sn | String | 否 | 数据库字段：`sn` | 执行任务的设备序列号 |
| +jobType | Integer | 否 | 数据库字段：`job_type` | 任务执行的主体0:dock,1:rc |
| +workspaceId | String | 否 | 数据库字段：`workspace_id` | 任务所属的工作区id |
| +taskType | Integer | 否 | 数据库字段：`task_type` | 任务类型 |
| +waylineType | Integer | 否 | 数据库字段：`wayline_type` | 路线的模板类型 |
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
| +repeatType | Integer | 否 | 数据库字段：`repeat_type` | 重复类型：0 天；1 周；2 月；3 不重复 |
| +repeatGap | Integer | 否 | 数据库字段：`repeat_gap` | 间隔时间 |
| +taskDayPeriod | String | 否 | 数据库字段：`task_day_period` | 执行日期区间 |
| +taskMoments | String | 否 | 数据库字段：`task_moments` | 执行时刻集合 |
| +taskTimes | String | 否 | 数据库字段：`task_times` | 执行的时间，当repeat_type=0时为空，=1时为1，2，3...，=2时为1，2，3... |
| +maxDelayDuration | Integer | 否 | 数据库字段：`max_delay_duration` | 最长延期时长 |
| +minBatteryCapacity | Integer | 否 | 数据库字段：`min_battery_capacity` | 可执行任务的飞行器电池电量百分比阈值 |
| +minStorageCapacity | Integer | 否 | 数据库字段：`min_storage_capacity` | 可执行任务的机场或飞行器最低存储容量 |
| +breakpointFlight | Integer | 否 | 数据库字段：`breakpoint_flight` | 是否开启自动断点续飞，0未开启，1开启 |
| +jobConfigType | Integer | 否 | 数据库字段：`job_config_type` | 任务类型（0-立即；1-单次定时；2-重复定时） |
| +groupId | Integer | 否 | 数据库字段：`group_id` | 所属分组id |
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
      "configId": "",
      "name": "",
      "fileId": "",
      "sn": "",
      "jobType": 0,
      "workspaceId": "",
      "taskType": 0,
      "waylineType": 0,
      "executeTime": 0,
      "completedTime": 0,
      "username": ""
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
- 分页接口如组件需要总数，需确认悟空是否传入完整外层响应包；仅传 `result` 本体时可能拿不到 `totalCount`。
- 本文件字段主要从 Java 实体/DTO 字段注释推断；落地前需用实际接口返回样例核对字段是否全部返回、是否有动态扩展字段。
- 星桥接口路径当前按规则标记为“暂无，需自行在星桥上注册”。
