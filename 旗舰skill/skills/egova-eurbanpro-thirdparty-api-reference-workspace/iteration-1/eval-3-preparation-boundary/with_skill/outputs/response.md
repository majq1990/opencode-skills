# 第三方联调前准备材料与账号

## 当前可确认的 API 事实

联调前你需要准备的账号凭证会涉及以下两个接口：

### 命中接口

| 接口 | 路径 | 用途 |
| --- | --- | --- |
| 获取公钥 | `GET /oauth/extras/openapi/pubkey` | 返回公钥，用于加密 clientSecret |
| 获取 token | `POST /oauth/extras/openapi/client` | 用加密后的凭证换 token，后续业务接口均需携带 |

### 最小必要字段

- `client_id`：统一用户中心分配的 clientId
- `client_secret`：经 SM2 公钥加密后的 clientSecret
- `grant_type`：固定值 `client_credentials`
- `uid`：统一用户中心分配的用户标识

### 关键约束

1. 读取顺序：先拿公钥 → 加密 clientSecret → 再拿 token，顺序不能错
2. 后续所有业务接口通过 query 参数 `egova_openapi_token` 携带 token 进行认证
3. 第三方签名（AK/SK）机制与 token 是独立的两套认证，均需实现

---

## 分流建议

这部分属于**接入准备与方案决策**，建议切换到 `preparation-guide` skill，它覆盖：

- 需要准备哪些材料与账号（clientId / clientSecret / AK / SK 等）
- 接入模式选择（标准模式 vs 签名模式）
- 环境配置与前置检查清单
- 第三方签名机制的完整说明

当前 skill 仅能提供接口层面的认证事实，完整的准备工作流程请使用 `preparation-guide` 获取。
