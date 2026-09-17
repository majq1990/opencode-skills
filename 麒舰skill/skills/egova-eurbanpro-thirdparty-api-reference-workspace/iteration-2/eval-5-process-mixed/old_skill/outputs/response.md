# DISPOSE_FEEDBACK 接口速查

## 1. 命中接口

- **action**: `DISPOSE_FEEDBACK`
- **接口名**: 工单处置反馈
- **用途**: 第三方对已签收工单提交处置结果，工单将向下个核查/结案阶段流转。

## 2. 最小必要字段

### 顶层必传

| 字段 | 说明 |
| --- | --- |
| `data` | 业务数据对象 |
| `senderCode` | 发送方编码（系统分配） |
| `action` | 固定值 `DISPOSE_FEEDBACK` |
| `uid` | 请求唯一标识（UUID） |

### data 中必传

| 字段 | 说明 |
| --- | --- |
| `caseId` | 工单编号 |
| `disposeOpinion` | 处置意见/反馈内容 |

### data 中建议传

| 字段 | 说明 |
| --- | --- |
| `disposeTime` | 处置时间，格式 `yyyy-MM-dd HH:mm:ss` |
| `medias` | 附件数组（可选） |

## 3. 最小请求示例

```json
{
  "data": {
    "caseId": "20240731001",
    "disposeTime": "2024-07-31 14:30:00",
    "disposeOpinion": "已现场处理完毕"
  },
  "senderCode": "mssq",
  "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",
  "action": "DISPOSE_FEEDBACK"
}
```

> 请求通过 query 参数携带 `egova_openapi_token` 进行认证，body 为 `application/json`。

## 4. 关键约束

1. **工单状态前置条件**: 必须先完成签收（`SIGN`），未签收工单无法提交处置反馈。
2. **disposeTime 格式**: 必须为 `yyyy-MM-dd HH:mm:ss`，不要传时间戳或 ISO 格式。
3. **medias 中的 mediaTypeId**: 必须是数值类型（如 `1`），不要传字符串 `"1"`。

## Reference

- `references/process-actions.md`：流程操作接口速查（含 DISPOSE_FEEDBACK 完整字段与示例）
- `references/common-protocol.md`：统一请求信封与公共规则

---

## 关于"现场为什么会失败"

这部分属于现象排障，不在本 skill 的职责范围内。根据 SKILL.md 的强约束，"方案设计与故障定位不在本 skill 内处理"，应转向 **troubleshooting** skill。

从接口约束角度，DISPOSE_FEEDBACK 调用失败的常见技术原因包括：
- 工单未完成签收（`SIGN`）就直接调用处置反馈
- `senderCode` 与系统分配的不一致
- `egova_openapi_token` 过期或未正确传递（query 参数方式）
- `disposeTime` 格式不符合 `yyyy-MM-dd HH:mm:ss`

要进一步定位具体失败原因，需要查看现场的错误返回信息和调用日志，建议使用 **troubleshooting** skill 进行诊断。
