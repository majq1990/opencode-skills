# REPORT 最小请求示例与必填字段

## 1. 命中接口

- **action**: `REPORT`
- **接口用途**: 工单上报，第三方向我方系统推送新工单
- **请求方法**: POST，`Content-Type: application/json`
- **认证**: query 参数 `egova_openapi_token`

## 2. 最小必要字段

### 顶层必传

| 字段 | 说明 |
|---|---|
| `data` | 业务数据对象 |
| `senderCode` | 发送方编码 |
| `action` | 固定值 `REPORT` |
| `uid` | 用户唯一标识 |

### data 中高频必传

| 字段 | 说明 |
|---|---|
| `caseId` | 案卷编号 |
| `registerTime` | 登记时间，格式 `yyyy-MM-dd HH:mm:ss` |
| `eventDesc` | 事件描述 |
| `recTypeId` / `recTypeName` | 案卷类型 ID / 名称 |
| `eventSrcId` / `eventSrcName` | 事件来源 ID / 名称 |
| `address` | 事发地址 |

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
    "eventSrcId": 104,
    "eventSrcName": "链接下单",
    "address": "xx路xx宠物馆"
  },
  "action": "REPORT",
  "senderCode": "mssq"
}
```

调用方式：`POST /openapi?egova_openapi_token=<your_token>`

## 4. 关键约束

1. **registerTime 格式**: 必须严格 `yyyy-MM-dd HH:mm:ss`，不含毫秒
2. **recTypeId 与 recTypeName**: 需与我方系统已配置的案卷类型对应，值不匹配会导致上报失败
3. **返回关键值**: 成功后关注响应中的 `recId`（我方工单 ID）和 `taskNum`（任务编号），后续查询/反馈需使用 `recId`
