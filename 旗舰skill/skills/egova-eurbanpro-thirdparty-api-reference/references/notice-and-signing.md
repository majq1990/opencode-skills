# 通知、签收与告知接口速查

## 适用信号
- 用户提到 `GET_NOTICE_INFO`、`NOTICE_SIGNING`、下派通知、处置反馈通知。
- 需要判断通知查询和通知签收的配套关系。

## GET_NOTICE_INFO
### 顶层必传
- `data`
- `senderCode`
- `action=GET_NOTICE_INFO`
- `uid`

### data 中关键字段
- `noticeName`

### 常见 noticeName
- `REPORT_NOTICE`
- `DISPOSE_FEEDBACK_NOTICE`
- 具体以现场通知字典为准

### 请求示例
```json
{
  "data": {
    "noticeName": "REPORT_NOTICE"
  },
  "action": "GET_NOTICE_INFO",
  "senderCode": "mssq",
  "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402"
}
```

## NOTICE_SIGNING
### 顶层必传
- `data`
- `senderCode`
- `action=NOTICE_SIGNING`
- `uid`

### data 中关键字段
- `noticeList[].noticeId`

### 请求示例
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

## 使用原则
- 查询通知和签收通知应成对出现。
- 不签收会导致同一通知重复被消费。
- 下派通知、处置反馈通知、其他通知要通过 `noticeName` 区分。

## 结论
只要是“第三方查通知再处理”的模式，就先看这个文件，再决定是否需要补读具体场景文件。

