# 公钥接口 404 排查

> 这部分属于现象排障，建议切换到 troubleshooting。当前我先给你可确认的接口事实：

---

## 1. 命中接口

- **接口名**：获取公钥接口
- **路径**：`/oauth/extras/openapi/pubkey`
- **用途**：返回公钥，用于 SM2 加密 `clientSecret`，是整个认证链路的第一步（公钥 -> 加密 -> 拿 token）

## 2. 最小必要字段

此接口为 `GET` 请求，无需业务参数。注意以下环境要求：

- 接口部署在**政务外网**，对外提供政务外网地址
- 需要按**源 IP 开通防火墙策略**
- 联调前应检查网络、安全、账号配置是否满足要求

## 3. 最小请求示例

```http
GET /oauth/extras/openapi/pubkey
```

无 query 参数、无 body，直接 GET 请求即可。

## 4. 关键约束

1. **路径必须精确**：完整路径为 `/oauth/extras/openapi/pubkey`，注意 `extras` 和 `openapi` 两级前缀，少拼或多拼均会 404
2. **网络前置条件**：接口在政务外网环境，需确认调用方 IP 已开通防火墙策略，否则可能返回 404 或连接超时
3. **认证链路顺序**：本接口不需要 token，但拿 token 的接口（`/oauth/extras/openapi/client`）需要本接口返回的公钥来加密 `clientSecret`，顺序不可颠倒

---

## 分流建议

404 排查涉及网络环境、防火墙策略、部署地址确认等故障归因内容，**不在本 skill 处理范围内**。建议切换到 `egova-eurbanpro-thirdparty-troubleshooting`，其 `references/common-issues.md` 中有完整的故障现象排查流程。

可快速自检的方向：
- 请求 URL 前缀（域名/IP + 端口 + context path）是否与实际部署地址一致
- 调用方源 IP 是否已在防火墙白名单中
- 是否漏拼了中间的路径段（如漏掉 `/extras` 或 `/openapi`）
