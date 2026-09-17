# NOTICE_SIGNING 接口速查

## 1. 命中接口

- **action:** `NOTICE_SIGNING`
- **接口用途:** 通知签收。第三方在通过 `GET_NOTICE_INFO` 拉取到待处理通知后，调用本接口对通知进行签收确认，避免同一通知被重复消费。

## 2. 最小必要字段

| 层级 | 字段 | 说明 |
| --- | --- | --- |
| 顶层 | `action` | 固定值 `NOTICE_SIGNING` |
| 顶层 | `senderCode` | 发送方编码，对接时分配 |
| 顶层 | `uid` | 请求唯一标识（UUID） |
| data | `noticeList[].noticeId` | 待签收通知的 ID，从 `GET_NOTICE_INFO` 返回中获取 |

## 3. 最小请求示例

```json
{
  "data": {
    "noticeList": [
      {
        "noticeId": 412
      }
    ]
  },
  "action": "NOTICE_SIGNING",
  "senderCode": "mssq",
  "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402"
}
```

## 4. 关键约束

- `GET_NOTICE_INFO` 与 `NOTICE_SIGNING` 应成对调用：先查通知，处理完毕后必须签收，否则同一通知会重复推送。
- `noticeList` 为数组结构，支持批量签收多条通知。
- 请求需携带 `egova_openapi_token` 凭证（query 参数方式），具体见 `auth-apis.md`。
