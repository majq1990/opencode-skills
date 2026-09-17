# action=REPORT 最小请求示例与必填字段

## 命中接口

- **action**: `REPORT`
- **用途**: 工单上报
- **请求方法**: POST
- **Content-Type**: `application/json`

## 最小必填字段

### 顶层必传（4个）

| 字段 | 说明 |
|---|---|
| `action` | 固定值 `REPORT` |
| `uid` | 用户唯一标识 |
| `senderCode` | 发送方编码 |
| `data` | 业务数据对象 |

### data 中高频必传

| 字段 | 说明 |
|---|---|
| `caseId` | 案件编号 |
| `registerTime` | 登记时间，格式 `yyyy-MM-dd HH:mm:ss` |
| `eventDesc` | 事件描述 |
| `recTypeId` / `recTypeName` | 事件大类ID / 名称 |
| `eventSrcId` / `eventSrcName` | 事件来源ID / 名称 |
| `address` | 事发地址 |
| `medias` | 多媒体数组（至少含一个元素） |

### medias 中高频必传

| 字段 | 说明 |
|---|---|
| `mediaName` | 文件名 |
| `mediaUsage` | 用途（如"上报"） |
| `mediaTypeId` | 媒体类型ID |
| `mediaPath` 或 `content` | 二选一：URL地址 或 Base64内容 |

## 最小请求示例

```json
{
  "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",
  "data": {
    "caseId": "20240731104001",
    "registerTime": "2024-07-18 09:04:36",
    "eventDesc": "反映拖欠工资的问题",
    "recTypeId": 23,
    "recTypeName": "市一体化平台",
    "eventSrcId": 104,
    "eventSrcName": "链接下单",
    "address": "xx路xx宠物馆",
    "medias": [
      {
        "mediaName": "photo.jpg",
        "mediaPath": "https://example.com/photo.jpg",
        "mediaUsage": "上报",
        "mediaTypeId": 1
      }
    ]
  },
  "action": "REPORT",
  "senderCode": "mssq"
}
```

## 返回关键值

- `recId` — 我方生成的工单ID
- `taskNum` — 任务编号

## 关键约束

- 认证通过 query 参数 `egova_openapi_token` 传递，不要使用 Authorization header。
- 时间格式必须为 `yyyy-MM-dd HH:mm:ss`。
- `mediaPath` 和 `content` 二选一即可，不要同时传。

## Reference

- `references/reporting-and-query.md`
- `references/common-protocol.md`
