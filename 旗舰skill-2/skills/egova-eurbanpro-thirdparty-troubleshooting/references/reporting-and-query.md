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

## ITEM_INST_SYNC（办理经过同步）
### 顶层必传
- `data`
- `senderCode`
- `action=ITEM_INST_SYNC`
- `uid`

### 适用建议
- 当第三方需要把办理经过同步到我方时使用。
- 若用户只是查询办理经过，优先转到通用 action 映射看 `GET_REC_PROCESS_INFO`。

## 继续阅读
- 若要生成字段更完整的联调示例：`references/report-full-params.md`
- 若要判断现场依赖字段：转 `egova-eurbanpro-thirdparty-preparation-guide` 的 `references/field-alignment-checklist.md`

## 结论
只要用户问的是上报/查询/办理经过，同一组小文件足够；最小字段看本文件，完整示例补齐看 `report-full-params.md`。
