# action 映射速查

## 高频 action
- `REPORT`：工单上报
- `GET_REC_INFO`：工单信息查询
- `ITEM_INST_SYNC`：工单办理经过同步
- `DISPOSE_FEEDBACK`：工单处置反馈
- `APPLY_ROLLBACK`：工单申请回退
- `REPLY_ROLLBACK`：工单答复回退
- `APPLY_POSTPONE`：工单申请延期
- `REPLY_POSTPONE`：工单答复延期
- `APPLY_CANCEL`：工单申请作废
- `REPLY_CANCEL`：工单答复作废
- `CHECK_FEEDBACK`：工单核查反馈
- `EVALUATE`：工单评价
- `GET_NOTICE_INFO`：通知查询
- `NOTICE_SIGNING`：通知签收
- `SUPERVISE`：工单督办
- `PRESS`：工单催办
- `SIGN`：工单签收
- `NOTIFY`：工单告知
- `GET_REC_PROCESS_INFO`：工单办理经过查询
- `UPLOAD_MEDIA`：上传工单多媒体

## 读取建议
- 看到上报 / REPORT / 多媒体：再读 `references/reporting-and-query.md`
- 看到通知 / 签收：再读 `references/notice-and-signing.md`
- 看到处置反馈：再读 `references/dispose-feedback.md`
- 看到 token / 签名：再读 `references/auth-apis.md` 和 `references/auth-sign.md`

## 文档冲突提醒
- `4.12 工单办结` 的参数表与样例 action 不一致
- `4.22 更新工单对接信息` 的参数表与样例 action 不一致

命中这两处时，必须明确提示：文档存在冲突，需现场确认。
