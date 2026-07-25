# 场景：下派通知

## 适用信号
- 我方要把案件下派给第三方。
- 第三方需要查询下派通知并签收。

## 最小闭环
1. 在对接系统中确认存在 `local_flag=1` 的本地平台。
2. 打开采集触发器开关。
3. 配置下派动作采集阶段。
4. 配置问题来源和参与者限制。
5. 第三方调用 `GET_NOTICE_INFO` 查询通知。
6. 第三方处理后调用 `NOTICE_SIGNING` 完成签收。

## 高风险点
- 阶段、来源、参与者限制任一配置不匹配，都会导致采集不到下派记录。
- 只查询通知不签收，会造成重复消费。
- 要区分普通通知、下派通知、处置反馈通知的 `noticeName`。

## 继续阅读
- 通知与签收接口：转 `egova-eurbanpro-thirdparty-api-reference` 的 `references/notice-and-signing.md`
- 常见问题：转 `egova-eurbanpro-thirdparty-troubleshooting` 的 `references/common-issues.md`
