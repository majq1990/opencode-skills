# Token 传递规则

## 1. 命中规则

**`egova_openapi_token` 必须通过 query 参数传递**，不使用 Authorization Header。

所有业务接口调用时，token 作为 URL query 参数附加在请求地址上，例如：

```
POST /api/xxx?egova_openapi_token=your_token_value
```

## 2. 最小规则列表

- **传递方式**：`egova_openapi_token` 放在 **URL query 参数**中，不是 Header、不是 body。
- **不使用 Authorization**：不回退 `Authorization: Bearer xxx` 方式。
- **Token 获取流程**：先调公钥接口加密 clientSecret → 再调 token 接口换取 token → 业务接口通过 query 携带 token 调用。
- **统一编码**：`Content-Type: application/json`，`UTF-8`。

## 3. 最小 Token 请求示例

### 第一步：获取公钥

```http
GET /oauth/extras/openapi/pubkey
```

### 第二步：获取 token

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

### 第三步：携带 token 调业务接口

```http
POST /api/report?egova_openapi_token=你拿到的token值
Content-Type: application/json

{
  "data": { ... },
  "senderCode": "第三方编码",
  "action": "REPORT",
  "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402"
}
```

## 4. 关键约束

- **query 参数，不是 Header** — `egova_openapi_token` 只能拼在 URL 问号后面，不要放在 Header 里。
- **clientSecret 必须加密** — 用公钥接口返回的公钥做 SM2 加密后，才能传给 token 接口。
- **代理人 uid 配置** — `uid` 字段配置错误会导致整条 token 链路异常。
