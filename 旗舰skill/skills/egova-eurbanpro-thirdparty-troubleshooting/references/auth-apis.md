# 鉴权接口速查

## 适用信号
- 用户只问麒舰标准公钥 / token 接口。
- 用户在排查 token 获取失败、认证错误、代理用户认证失败。
- 不需要展开第三方签名细节时，优先读本文件。

## 5.1 获取公钥接口
- 路径：`/oauth/extras/openapi/pubkey`
- 作用：返回公钥，用于加密 `client_secret`
- 读取顺序：先拿公钥，再加密，再去拿 token

## 5.2 获取 token 接口
- 路径：`/oauth/extras/openapi/client`
- 作用：用加密后的凭证换 token
- 入参重点：
  - `client_id`
  - 加密后的 `client_secret`
  - 固定值 `client_credentials`
  - `uuid`

## 业务接口带 token 的方式
- Header：`X-EGOVA-Authorization: Bearer <token>`
- Query：`egova_openapi_token=<token>`

## 常见问题
- 误把文档示例地址当成现场真实地址，或路径里带了 `v22-api/`。
- 代理人字段配置错误会导致 token 链路异常。
- 只实现 token、不实现现场额外签名规则时，仍然可能被判认证失败。

## 补充阅读
- 第三方签名、AK/SK：`references/auth-sign.md`
- 常见问题：`references/common-issues.md`
- 前置核查：`references/precheck-and-selftest.md`
