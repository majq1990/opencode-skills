# REPORT（工单上报）最小请求示例与必填字段

## 1. 命中接口

- **action**: `REPORT`
- **用途**: 工单上报（第三方向麒舰平台提交新工单）
- **请求方法**: POST，`Content-Type: application/json`

## 2. 最小必填字段

### 顶层必传
| 字段 | 说明 |
|------|------|
| `action` | 固定 `REPORT` |
| `uid` | 用户唯一标识 |
| `senderCode` | 发送方编码 |
| `data` | 业务数据对象 |

### data 中必传
| 字段 | 说明 |
|------|------|
| `caseId` | 案件编号 |
| `registerTime` | 登记时间，格式 `yyyy-MM-dd HH:mm:ss` |
| `eventDesc` | 事件描述 |
| `recTypeId` / `recTypeName` | 案件来源类型 ID / 名称 |
| `eventSrcId` / `eventSrcName` | 事件来源 ID / 名称 |
| `address` | 地址 |

### medias（媒体附件，至少一条）
| 字段 | 说明 |
|------|------|
| `mediaName` | 媒体文件名 |
| `mediaUsage` | 媒体用途（如 `上报`） |
| `mediaTypeId` | 媒体类型 ID |
| `mediaPath` 或 `content` | 二选一：URL 路径 或 Base64 内容 |

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

## 4. 补充说明

- 请求通过 query 参数 `egova_openapi_token` 进行认证（不要使用 Authorization header）。
- 请求编码统一 UTF-8。
- `medias` 中 `mediaPath`（URL）与 `content`（Base64）二选一。
- 返回关键值：`recId`（案卷 ID）、`taskNum`（任务编号）。

## 5. Reference

- `references/reporting-and-query.md` -- REPORT、GET_REC_INFO、ITEM_INST_SYNC 接口速查
- `references/common-protocol.md` -- 协议规范与统一请求信封
