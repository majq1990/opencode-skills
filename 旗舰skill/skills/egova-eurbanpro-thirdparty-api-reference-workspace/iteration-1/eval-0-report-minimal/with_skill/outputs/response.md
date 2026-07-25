# REPORT -- 最小请求示例与必填字段

## 1. 命中接口

- **action:** `REPORT`
- **接口用途:** 工单上报，将第三方事件/投诉/工单推送到我方系统。

## 2. 最小必要字段

**顶层必传（4 个）：**

| 字段 | 说明 |
|---|---|
| `action` | 固定 `"REPORT"` |
| `uid` | 用户唯一标识 |
| `senderCode` | 发送方编码（如 `"mssq"`） |
| `data` | 业务数据对象 |

**data 中高频必传（6 个）：**

| 字段 | 说明 |
|---|---|
| `caseId` | 工单编号 |
| `registerTime` | 上报时间，格式 `yyyy-MM-dd HH:mm:ss` |
| `eventDesc` | 事件描述 |
| `recTypeId` | 事件类型 ID |
| `recTypeName` | 事件类型名称 |
| `address` | 事件地址 |

## 3. 最小请求示例

```json
{
  "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",
  "data": {
    "caseId": "20240731104001",
    "registerTime": "2024-07-18 09:04:36",
    "eventDesc": "反映拖欠工资的问题",
    "recTypeId": 23,
    "recTypeName": "市一体化平台",
    "address": "xx路xx宠物馆"
  },
  "action": "REPORT",
  "senderCode": "mssq"
}
```

## 4. 关键约束

1. **时间格式** -- `registerTime` 必须为 `yyyy-MM-dd HH:mm:ss`，含空格分隔的日期和时间部分。
2. **认证方式** -- 请求需通过 query 参数 `egova_openapi_token` 传递用户凭证（获取方式见 `auth-apis.md`）。
3. **返回关键值** -- 成功响应中关注 `recId`（我方工单 ID）和 `taskNum`（任务编号），用于后续查询与流转。
