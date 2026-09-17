# NOTICE_SIGNING 接口速查

## 1. 命中接口

- **action**: `NOTICE_SIGNING`
- **接口名**: 通知签收
- **用途**: 第三方系统在通过 `GET_NOTICE_INFO` 查询到通知后，调用此接口对通知进行签收确认。签收后该通知不会被重复消费。查询通知和签收通知应成对出现。

## 2. 最小必要字段

### 顶层必传
| 字段 | 说明 |
|------|------|
| `data` | 业务数据容器 |
| `senderCode` | 发送方编码 |
| `action` | 固定值 `NOTICE_SIGNING` |
| `uid` | 请求唯一标识（UUID） |

### data 中关键字段
| 字段 | 说明 |
|------|------|
| `noticeList[].noticeId` | 待签收的通知 ID |

## 3. 请求示例

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

## 4. 补充说明

- 查询通知（`GET_NOTICE_INFO`）和签收通知（`NOTICE_SIGNING`）应成对调用。
- 不签收会导致同一通知被重复消费。
- `noticeId` 为数值类型，具体值从 `GET_NOTICE_INFO` 的返回结果中获取。
- 请求需携带 `egova_openapi_token` 作为 query 参数进行认证。

## 5. Reference

- `references/actions-map.md` -- action 映射速查
- `references/notice-and-signing.md` -- 通知与签收接口详细说明
