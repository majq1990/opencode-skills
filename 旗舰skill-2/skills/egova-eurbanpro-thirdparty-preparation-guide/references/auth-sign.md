# 场景：鉴权与签名

## 适用信号
- 需要说明麒舰标准 token 获取方式。
- 需要适配第三方自定义签名、网关签名或 AK/SK。
- 现场报认证错误、代理用户认证失败、签名校验失败。

## 麒舰标准鉴权链路
1. 调 `/oauth/extras/openapi/pubkey` 获取公钥。
2. 用公钥加密 `clientSecret`。
3. 调 `/oauth/extras/openapi/client` 获取 token。
4. 业务接口通过 query 参数传 `egova_openapi_token`。

## 扩展签名模式
### token + 网关签名
- 先拿第三方 token，再基于时间戳和密钥计算签名。
- 常见 header：`gateway_appid`、`gateway_rtime`、`gateway_sig`。

### 时间戳 + nonce + sha256
- 常见 header：`x-rio-nonce`、`x-rio-timestamp`、`x-rio-signature`。

### 海康 AK/SK
- 典型 header：`X-Ca-Key`、`X-Ca-Timestamp`、`X-Ca-Nonce`、`X-Ca-Signature`。
- 常用于智能设备事件订阅/取消订阅类接口。

## 高风险点
- 对接代理人填错，导致“代理用户认证失败”。
- 只实现 token，遗漏第三方要求的签名头。
- 混淆 query 参数 `egova_openapi_token` 与其他现场认证方式。

## 继续阅读
- 公钥与 token 接口：转 `egova-eurbanpro-thirdparty-api-reference` 的 `references/auth-apis.md`
- 通用问题：转 `egova-eurbanpro-thirdparty-troubleshooting` 的 `references/common-issues.md`
