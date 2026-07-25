# Token 传递方式

## 命中接口

- **认证方式**：业务接口统一使用 **query 参数** 传递 token
- **参数名**：`egova_openapi_token`
- **不要**回退到 `Authorization` / `X-EGOVA-Authorization` Header 方式

## Token 传递规则

token **必须是 query 参数**，拼在 URL 上，不是放在 Header 里。

```
GET /xxx?action=REPORT&egova_openapi_token=<你的token值>
```

## 最小 token 请求示例

### 第一步：获取 token

```http
POST /oauth/extras/openapi/client
Content-Type: application/json

{
  "client_id": "统一用户中心分配的clientId",
  "client_secret": "SM2加密后的clientSecret",
  "grant_type": "client_credentials",
  "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402"
}
```

### 第二步：用 token 调业务接口（query 方式）

```http
POST /xxx?action=REPORT&egova_openapi_token=你拿到的token值
Content-Type: application/json

{
  "data": { ... },
  "senderCode": "你的单位编码",
  "action": "REPORT",
  "uid": "你的uuid"
}
```

## 关键约束

- token 必须通过 query 参数 `egova_openapi_token` 传递，不要用 Header
- 先通过 `/oauth/extras/openapi/pubkey` 获取公钥，再 SM2 加密 `client_secret`，最后调 `/oauth/extras/openapi/client` 拿 token
- 拿到 token 后拼到业务接口的 URL query 中

## Reference

- `references/auth-apis.md`：公钥与 token 接口
- `references/common-protocol.md`：协议与公共规则
