# 流程操作接口速查

## 适用信号
- 用户提到 `DISPOSE_FEEDBACK`、`GET_REC_PROCESS_INFO`、`SUPERVISE`、`PRESS`、`SIGN`、`NOTIFY`、`UPLOAD_MEDIA`。
- 需要快速判断这些流程操作接口的最小必填字段和最小请求示例。

## DISPOSE_FEEDBACK（工单处置反馈）
### 顶层必传
- `data`
- `senderCode`
- `action=DISPOSE_FEEDBACK`
- `uid`

### data 中高频必传
- `caseId`
- `disposeOpinion`

### medias 中常用字段
- `mediaName`
- `mediaPath`
- `mediaUsage=处置`
- `mediaTypeId`

### 请求示例
```json
{
  "data": {
    "caseId": "20240731001",
    "disposeTime": "2023-10-28 11:00:00",
    "disposeOpinion": "处置反馈",
    "medias": [
      {
        "mediaName": "618cf8c4e1d935754.jpg",
        "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",
        "mediaUsage": "处置",
        "mediaTypeId": 1
      }
    ]
  },
  "senderCode": "mssq",
  "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",
  "action": "DISPOSE_FEEDBACK"
}
```

### 补充说明
- 调用成功后，工单会继续向下个核查/结案阶段流转。
- 如果是“我方发通知、第三方查通知后再处理”的模式，先看 `references/notice-and-signing.md` 里的 `DISPOSE_FEEDBACK_NOTICE`。

## GET_REC_PROCESS_INFO（工单办理经过查询）
### 顶层必传
- `data`
- `senderCode`
- `action=GET_REC_PROCESS_INFO`
- `uid`

### data 中高频必传
- `caseId`

### 请求示例
```json
{
  "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",
  "data": {
    "caseId": "20240801002"
  },
  "action": "GET_REC_PROCESS_INFO",
  "senderCode": "zhwx"
}
```

### 返回关键值
- `itemInstList`
- `taskDefineName`
- `actionName`
- `actionTime`
- `humanName`
- `unitName`
- `itemContent`

## SUPERVISE（工单督办）
### 顶层必传
- `data`
- `senderCode`
- `action=SUPERVISE`
- `uid`

### data 中高频必传
- `caseId`
- `opinion`

### 常用可选
- `endTime`，格式 `yyyy-MM-dd HH:mm:ss`

### 请求示例
```json
{
  "data": {
    "caseId": "20240801002",
    "endTime": "2024-08-03 19:16:00",
    "opinion": "处理太慢，需要督办"
  },
  "senderCode": "zhwx",
  "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19403",
  "action": "SUPERVISE"
}
```

## PRESS（工单催办）
### 顶层必传
- `data`
- `senderCode`
- `action=PRESS`
- `uid`

### data 中高频必传
- `caseId`
- `opinion`

### 请求示例
```json
{
  "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",
  "data": {
    "caseId": "20240801002",
    "opinion": "超期严重，请加快处理。"
  },
  "action": "PRESS",
  "senderCode": "zhwx"
}
```

## SIGN（工单签收）
### 顶层必传
- `data`
- `senderCode`
- `action=SIGN`
- `uid`

### data 中高频必传
- `caseId`

### 请求示例
```json
{
  "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",
  "data": {
    "caseId": "202406200007"
  },
  "action": "SIGN",
  "senderCode": "zhwx"
}
```

### 补充说明
- 通常签收后的工单才能继续做后续告知等操作。

## NOTIFY（工单告知）
### 顶层必传
- `data`
- `senderCode`
- `action=NOTIFY`
- `uid`

### data 中高频必传
- `caseId`
- `notifyContent`
- `notifyTypeId`
- `notifyMethod`

### 常用可选
- `leaderCheck`

### 请求示例
```json
{
  "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",
  "data": {
    "caseId": "202406200006",
    "notifyContent": "告知内容",
    "notifyTypeId": 2,
    "notifyMethod": 1,
    "leaderCheck": 0
  },
  "action": "NOTIFY",
  "senderCode": "zhwx"
}
```

### 补充说明
- `notifyTypeId` 常见值：`1` 受理告知、`2` 办理告知、`96` 阶段回复。
- `notifyMethod` 常见值：`1` 短信、`2` 仅记录、`3` 微信、`4` 电话。

## UPLOAD_MEDIA（上传工单多媒体）
### 顶层必传
- `data`
- `senderCode`
- `action=UPLOAD_MEDIA`
- `uid`

### data 中高频必传
- `caseId`
- `medias`

### medias 中高频必传
- `mediaName`
- `mediaPath` 或 `content` 二选一
- `mediaUsage`
- `mediaTypeId`

### 请求示例
```json
{
  "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",
  "data": {
    "caseId": "20240801002",
    "medias": [
      {
        "mediaName": "618cf8c4e1d9357541.jpg",
        "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",
        "mediaUsage": "处置",
        "mediaTypeId": 1
      }
    ]
  },
  "action": "UPLOAD_MEDIA",
  "senderCode": "zhwx"
}
```

### 补充说明
- `mediaPath` / `content` 二选一即可。
- `mediaUsage` 常见值：`上报`、`核查`、`核实`、`处置`、`自处置`。

## 使用建议
- 问“通知怎么查、查完怎么签收”时优先看 `references/notice-and-signing.md`。
- 问“办理经过查询”看本文件，不要回到 `ITEM_INST_SYNC`。
- 问“附件是跟着业务接口一起传，还是单独上传”时：业务内嵌附件先看 `references/reporting-and-query.md` / 本文件；若是单独上传，再看 `UPLOAD_MEDIA`。
