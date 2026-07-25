# DISPOSE_FEEDBACK（工单处置反馈）

## 1. 命中接口

`action=DISPOSE_FEEDBACK` 对应工单处置反馈接口，用于第三方向平台回复工单处置结果。调用成功后工单会继续向下个核查/结案阶段流转。

## 2. 最小必要字段

**顶层必传：**

| 字段 | 说明 |
|------|------|
| `action` | 固定值 `DISPOSE_FEEDBACK` |
| `data` | 业务数据对象 |
| `senderCode` | 发送方编码（第三方系统编码） |
| `uid` | 请求唯一标识（UUID） |

**data 中高频必传：**

| 字段 | 说明 |
|------|------|
| `caseId` | 工单编号 |
| `disposeOpinion` | 处置意见 |
| `disposeTime` | 处置时间，格式 `yyyy-MM-dd HH:mm:ss` |

**medias（可选，如需附带附件）：**

| 字段 | 说明 |
|------|------|
| `mediaName` | 文件名 |
| `mediaPath` | 文件访问地址 |
| `mediaUsage` | 用途，常见值：`处置` |
| `mediaTypeId` | 媒体类型 ID，如 `1` |

## 3. 最小请求示例

```json
{
  "data": {
    "caseId": "20240731001",
    "disposeTime": "2024-07-31 14:00:00",
    "disposeOpinion": "已处置完成"
  },
  "senderCode": "mssq",
  "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",
  "action": "DISPOSE_FEEDBACK"
}
```

> 请求方式：POST，Content-Type: application/json，token 通过 query 参数 `egova_openapi_token` 传递。

## 4. 关键约束

1. **uid 必须唯一** — 每次请求使用不同的 UUID，重复 uid 会被平台视为重复请求。
2. **disposeTime 格式** — 必须为 `yyyy-MM-dd HH:mm:ss`，不能使用时间戳或其他格式。
3. **工单状态前置条件** — 工单必须处于可处置状态（已签收/已下发），否则接口虽可能返回成功但业务不会实际流转。

---

关于"现场为什么会失败"，这部分属于现象排障，建议切换到 troubleshooting。本 skill 只确认：接口路径需在已开通防火墙策略的政务外网环境下调用，token 通过 query 参数 `egova_openapi_token` 传递。
