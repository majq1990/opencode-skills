# 快速开始

## 适用信号
- 第三方刚开始对接麒舰，不知道先做什么。
- 现场已经有接口文档，但联调一开始就报 404、认证失败、代理用户认证失败。
- 需要先判断应该走第三方直连、星桥拉取还是通知查询。

## 最小阅读路径
### 1. 先确认对接模式
- 第三方主动调用我方接口上报案件：读 `references/reporting.md`
- 我方通过星桥定时拉取第三方后转上报：读 `references/reporting.md`
- 我方派单给第三方、第三方来查通知：读 `references/dispatch-notice.md`
- 双向处置反馈：读 `references/dispose-feedback.md`
- token、签名、AK/SK：读 `references/auth-sign.md`

### 2. 所有模式都要先做的事
- 打通网络双向访问：第三方能调我方接口，我方能回拉第三方附件地址。
- 在用户中心/构建中心新增应用，拿到 `clientId`、`clientSecret`。
- 配置对接系统和对接代理人，并刷新 `/unity/openapi/config/clear-sys-config`。
- 与第三方对齐字段口径：案件来源、案件类型、大小类、区划、附件字段。
- 先做现场自测，再联调第三方。

### 3. 高风险前置项
- 对接代理人必须是登录账号，不是人员名称。
- 现场工作流可能依赖 `districtId/districtName`，缺了会导致无法流转。
- 文档示例地址常带 `v22-api/`，联调时要换成现场真实地址。
- 若已经进入 V22 应用、代理人、采集器和推送表逐项配置，直接转 `references/v22duijieconfig.md`。

## 继续阅读
- 前置检查：`references/precheck-network-auth.md`
- 采集与自测：`references/precheck-collection-trigger.md`
- V22 采集配置实操：`references/v22duijieconfig.md`
- 字段对齐：`references/field-alignment-checklist.md`
- 关键配置表与查询验证：`references/config-tables-and-checks.md`
- 如需接口参数：转 `egova-eurbanpro-thirdparty-api-reference`
- 如需持续性问题排查：转 `egova-eurbanpro-thirdparty-troubleshooting`
