# 鉴权接口速查

## 适用信号
- 用户只问麒舰标准公钥 / token 接口。
- 不需要展开第三方签名细节时，优先读本文件。

## 5.1 获取公钥接口
- 路径：`/oauth/extras/openapi/pubkey`
- 作用：返回公钥，用于加密 `clientSecret`
- 读取顺序：先拿公钥，再加密，再去拿 token

### 请求示例
```http
GET /oauth/extras/openapi/pubkey
```

## 5.2 获取 token 接口
- 路径：`/oauth/extras/openapi/client`
- 作用：用加密后的凭证换 token
- 返回 token 后，业务接口再携带用户凭证进行调用

### 请求示例
```json
{
  "client_id": "统一用户中心分配的clientId",
  "client_secret": "SM2加密后的clientSecret",
  "grant_type": "client_credentials",
  "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402"
}
```

## 常见问题
- 代理人字段配置错误会导致 token 链路异常。
- 只实现 token，不实现现场额外签名规则，仍然会被判认证失败。

## 补充阅读
- 第三方签名、AK/SK：转 `egova-eurbanpro-thirdparty-preparation-guide` 的 `references/auth-sign.md`
- 故障现象排查：转 `egova-eurbanpro-thirdparty-troubleshooting` 的 `references/common-issues.md`
