# REPORT / 查询 / 办理经过接口速查

## 适用信号
- 用户提到 `REPORT`、`GET_REC_INFO`、`ITEM_INST_SYNC`。
- 需要快速判断这些接口最小必填字段。

## REPORT（工单上报）
### 顶层必传
- `data`
- `senderCode`
- `action=REPORT`
- `uid`

### data 中高频必传
- `caseId`
- `registerTime`，格式 `yyyy-MM-dd HH:mm:ss`
- `eventDesc`
- `recTypeId` / `recTypeName`
- `eventSrcId` / `eventSrcName`
- `address`
- `medias`

### medias 中高频必传
- `mediaName`
- `mediaUsage`
- `mediaTypeId`
- `mediaPath` 或 `content` 二选一

### 请求示例
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
    "title": "反映拖欠工资的问题",
    "districtName": "xx区",
    "streetName": "xx街道",
    "contact": "13211112222",
    "medias": [
      {
        "mediaName": "618cf8c4e1d935754.jpg",
        "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",
        "mediaUsage": "上报",
        "mediaTypeId": 1
      }
    ]
  },
  "action": "REPORT",
  "senderCode": "mssq"
}
```

### 返回关键值
- `recId`
- `taskNum`

## GET_REC_INFO（工单信息查询）
### 顶层必传
- `data`
- `senderCode`
- `action=GET_REC_INFO`
- `uid`

### data 中高频必传
- `caseId`（没有时可用工单编号）

### 请求示例
```json
{
  "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",
  "data": {
    "caseId": "20240731001"
  },
  "action": "GET_REC_INFO",
  "senderCode": "mssq"
}
```

## ITEM_INST_SYNC（办理经过同步）
### 顶层必传
- `data`
- `senderCode`
- `action=ITEM_INST_SYNC`
- `uid`

### 适用建议
- 当第三方需要把办理经过同步到我方时使用。
- 若用户只是查询办理经过，优先转到 `references/process-actions.md` 看 `GET_REC_PROCESS_INFO`。

### 请求示例
```json
{
  "data": {
    "taskDefineId": "artificial_357c3b17-bbba-468b-b592-9bb1a22c52b4",
    "taskDefineName": "市信息中心（受理）",
    "action": "transit",
    "actionName": "批转",
    "actionTime": "2023-09-22 14:05:38",
    "humanId": "1673529228661366784",
    "humanName": "ls20230627777",
    "partId": "wizdom:130072",
    "partUid": 50455,
    "partName": "拱墅区采集公司",
    "partTypeId": 1,
    "roleId": "wizdom:130072",
    "roleName": "拱墅区采集公司",
    "unitId": "wizdom:662",
    "unitName": "采集公司",
    "itemContent": "新增办理经过测试",
    "nextTaskDefineId": "artificial_357c3b17-bbba-468b-b592-9bb1a22c52b5",
    "nextTaskDefineName": "市信息中心（派遣）",
    "nextHumanId": "dbadf436-513d-4a8b-8d47-5c8c911fe90b",
    "nextHumanName": "egova",
    "nextPartId": "wizdom:131512",
    "nextPartUid": 50595,
    "nextPartName": "仓前街道派遣员",
    "nextPartTypeId": 1,
    "nextRoleId": "wizdom:131512",
    "nextRoleName": "仓前街道派遣员",
    "nextUnitId": "wizdom:3024",
    "nextUnitName": "北干街道分派遣",
    "caseId": "20240731001"
  },
  "senderCode": "mssq",
  "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",
  "action": "ITEM_INST_SYNC"
}
```

## 继续阅读
- 若要生成字段更完整的联调示例：`references/report-full-params.md`
- 若要判断现场依赖字段：转 `egova-eurbanpro-thirdparty-preparation-guide` 的 `references/field-alignment-checklist.md`

## 结论
只要用户问的是上报/查询/办理经过，同一组小文件足够；最小字段看本文件，完整示例补齐看 `report-full-params.md`。

