# i 厦门 OAuth2 单点登录对接

## 场景描述

对接 i 厦门开放平台 OAuth2 单点登录，通过授权码模式获取用户信息。

### 业务需求

前端传入授权码（code），后端调用 i 厦门接口获取用户信息（姓名、手机号、身份证等）。

### OAuth2 模式

授权码模式（Authorization Code）

### 接口文档地址

https://buss.ixiamen.org.cn/pbc/liteapp-dev-mgr/web/#/document

---

## OAuth2 流程

```
┌─────────┐              ┌──────────────┐              ┌─────────────┐
│  前端   │              │ 星桥脚本     │              │ i厦门平台   │
└────┬────┘              └──────┬───────┘              └──────┬──────┘
     │                          │                             │
     │  1. 用户授权              │                             │
     ├─────────────────────────>│                             │
     │  跳转授权页面             │                             │
     │                          │                             │
     │                          │  2. 获取授权码              │
     │                          ├─────────────────────────>  │
     │                          │  /oauth/authorize           │
     │                          │                             │
     │                          │  3. 返回 code               │
     │                          │<─────────────────────────  │
     │                          │                             │
     │  4. 传入 code             │                             │
     ├─────────────────────────>│                             │
     │                          │                             │
     │                          │  5. code 换 token           │
     │                          ├─────────────────────────>  │
     │                          │  /oauth/token               │
     │                          │                             │
     │                          │  6. 返回 accessToken         │
     │                          │<─────────────────────────  │
     │                          │                             │
     │                          │  7. token 换用户信息         │
     │                          ├─────────────────────────>  │
     │                          │  /server/public/user/get    │
     │                          │                             │
     │                          │  8. 返回用户信息              │
     │                          │<─────────────────────────  │
     │                          │                             │
     │  9. 返回用户信息          │                             │
     │<─────────────────────────│                             │
     │                          │                             │
```

### 流程说明

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 用户授权 | 前端跳转到 i 厦门授权页面 |
| 2-3 | 获取授权码 | 用户授权后，i 厦门回调返回授权码 code |
| 4-6 | 换取 Token | 前置脚本使用 code 换取 accessToken |
| 7-8 | 获取用户信息 | 前置脚本使用 accessToken 获取用户信息 |
| 9 | 返回结果 | 后置脚本格式化返回用户信息 |

---

## 配置参数

### 用户中心地址

| 环境 | base_uri |
|------|----------|
| 测试环境 | https://tbuss.ixiamen.org.cn:8090/pbc/usercenter/ |
| 正式环境 | https://buss.ixiamen.org.cn/pbc/usercenter/ |

### 回调地址

```
https://files12345.fujian.gov.cn/eurbanpro/mobile/report/index.html?areaCode=350200&isIXM=1#/generalHome
```

### 授权范围（scope）

| scope | 描述 |
|-------|------|
| basic | 用户的 openId |
| name | 真实姓名 |
| mobile | 手机号 |
| certif-id | 证件类型和证件号码 |
| external-user | 获取 ixm、xmsmk 等原始渠道的信息（透传的闽政通 token 信息获取必加） |
| enterprise | 法人信息，法人登录才会有这个信息 |

### 接入渠道参数（channel）

| 渠道 | channel 参数 | 备注 |
|------|-------------|------|
| i 厦门 | IXM | 适用于 i 厦门 APP、微信 |
| i 厦门公众号单点登录 | IXM_WECHAT_OFFICIAL_ACCOUNTS | 适用于微信 |
| 厦门市民卡 APP、i 厦门微信小程序 | XMSMK | - |
| i 厦门网页 PC 端 | IXM_PC | 仅限于电脑 PC 端对接 |

---

## 接口说明

### 1. 授权接口

**请求地址**：`{{base_uri}}/oauth/authorize`

**请求方式**：GET（浏览器前端跳转）

**请求参数**：

| 参数 | 说明 |
|------|------|
| client_id | 用户中心分配的 clientId |
| redirect_uri | 登录完成后的回调地址 |
| response_type | 固定值 code |
| scope | basic name mobile certif-id |
| channel | 接入渠道，如 IXM |

**示例 URL**：

```
https://buss.ixiamen.org.cn/pbc/usercenter/oauth/authorize?client_id={{client_id}}&redirect_uri={{redirect_uri}}&response_type=code&scope=basic%20name%20mobile&channel=IXM
```

### 2. Token 接口

**请求地址**：`{{base_uri}}/oauth/token`

**请求方式**：POST

**请求参数**：

| 参数 | 说明 |
|------|------|
| grant_type | 固定值 authorization_code |
| scope | 请求授权数据范围 |
| client_id | 用户中心分配的 clientId |
| client_secret | 用户中心分配的 clientSecret |
| code | 授权码 |
| redirect_uri | 必须与授权接口中的 redirect_uri 一致 |

**响应示例**：

```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGci...",
  "expires_in": 3599,
  "scope": "basic name mobile",
  "jti": "58b533cb-2495-41ce-9cad-f00c6dafdda2"
}
```

### 3. 用户信息接口

**请求地址**：`{{base_uri}}/server/public/user/get`

**请求方式**：POST

**请求头**：

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**请求体**：空 JSON 对象 `{}`

**响应示例**：

```json
{
  "openId": "17D22C4EEFFA39A0E",
  "personName": "系统运维9",
  "personNameFuzzy": "****9",
  "certifType": 0,
  "certifId": "350200199001011234",
  "enabled": false,
  "userType": 0,
  "mobile": "13800138000",
  "mobileFuzzy": "138****8000",
  "unifiedCreditCode": "",
  "externalUsers": [{
    "source": "IXM",
    "externalUserId": "333321",
    "extParams": "{...}"
  }]
}
```

**响应字段说明**：

| 字段 | 说明 |
|------|------|
| openId | 用户在接入端与用户中心对接的唯一 id |
| personName | 用户姓名 |
| personNameFuzzy | 用户姓名脱敏 |
| certifType | 证件类型（0=大陆身份证，详见下方证件类型表） |
| certifId | 证件号码 |
| mobile | 手机号 |
| mobileFuzzy | 脱敏手机号 |
| userType | 用户类型：0-个人用户，1-法人用户 |
| unifiedCreditCode | 统一信用代码（企业用户专用） |
| externalUsers | 原始渠道登录用户信息 |
| source | 渠道来源 code（与 channel 一致） |
| extParams | 原始渠道登录用户信息详情（JSON 格式） |

### 4. 证件类型（certifType）

| 值 | 描述 |
|----|------|
| 0 | 大陆身份证 |
| 1 | 香港身份证 |
| 2 | 台湾居民往来大陆通行证 |
| 3 | 澳门身份证 |
| 4 | 港澳居民往来大陆通行证 |
| 5 | 普通护照 |
| 6 | 台湾居民居住证 |
| 7 | 军官证 |
| 8 | 港澳居民居住证 |
| 9 | 外国人永久居住证 |
| 88 | 其他证件类型 |
| 999 | 未知证件类型 |

---

## 鉴权脚本

**职责**：统一管理 i 厦门 OAuth2 配置参数

```groovy
// ========== 鉴权脚本：i厦门 OAuth2 配置 ==========

// 环境配置（根据实际环境选择）
var env = 'test'  // 'test' 或 'prod'

var config = [
    // 测试环境
    test: [
        clientId: 'bc433ca348f2439',
        clientSecret: '7da162cf624946db82cc83772',
        baseUri: 'https://tbuss.ixiamen.org.cn:8090/pbc/usercenter/',
        redirectUri: 'https://files12345.fujian.gov.cn/eurbanpro/mobile/report/index.html?areaCode=350200&isIXM=1#/generalHome',
        channel: 'IXM',
        scope: 'basic name mobile certif-id'
    ],
    // 正式环境
    prod: [
        clientId: '16dd00fd4069402',
        clientSecret: 'ea8e68ed6f114038bab011a8a',
        baseUri: 'https://buss.ixiamen.org.cn/pbc/usercenter/',
        redirectUri: 'https://files12345.fujian.gov.cn/eurbanpro/mobile/report/index.html?areaCode=350200&isIXM=1#/generalHome',
        channel: 'IXM',
        scope: 'basic name mobile certif-id'
    ]
]

// 存储配置到全局变量
variables['ixiamenConfig'] = config[env]
variables['ixiamenEnv'] = env

out.println("i厦门配置已加载，环境: ${env}")
```

**配置说明**：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `ixiamenConfig` | 完整配置对象 | 包含 clientId、clientSecret、baseUri 等 |
| `ixiamenEnv` | 当前环境标识 | `test` 或 `prod` |

---

## 前置脚本

### 步骤1：授权码换取 accessToken

```groovy
// ========== 前置脚本：授权码换取 accessToken ==========
import com.egova.api.util.http.HttpUtils
import com.egova.json.utils.JsonUtils
import org.springframework.web.util.UriUtils

// 获取配置
var config = variables['ixiamenConfig']

// 获取前端传入的授权码
var code = request.getQueryParam('code')
if (!code) {
    out.println("错误: 缺少授权码参数 code")
    return 'api_stop'
}

// 构建 token 接口地址
var tokenUrl = "${config.baseUri}oauth/token"

// 构建 form 参数
var tokenParams = [
    'grant_type': 'authorization_code',
    'scope': config.scope,
    'client_id': config.clientId,
    'client_secret': config.clientSecret,
    'code': code,
    'redirect_uri': config.redirectUri
]

out.println("开始换取 token，code: ${code}")

// 调用 i 厦门 token 接口
try {
    var response = HttpUtils.postForm(tokenUrl, tokenParams, String.class)

    if (response.statusCode.value == 200) {
        var result = JsonUtils.deserialize(response.body, Map.class)
        var accessToken = result?.access_token

        if (accessToken) {
            // 存储 accessToken 供后续使用
            variables['ixiamenAccessToken'] = accessToken
            out.println("Token 获取成功")
        } else {
            out.println("错误: Token 响应解析失败")
            out.println("响应内容: ${response.body}")
            return 'api_stop'
        }
    } else {
        out.println("错误: Token 请求失败，状态码: ${response.statusCode.value}")
        out.println("响应内容: ${response.body}")
        return 'api_stop'
    }
} catch (Exception e) {
    out.println("异常: Token 请求出错 - ${e.message}")
    return 'api_stop'
}
```

### 步骤2：accessToken 获取用户信息

```groovy
// ========== 前置脚本：accessToken 获取用户信息 ==========
import com.egova.api.util.http.HttpUtils
import com.egova.json.utils.JsonUtils

// 获取配置和 token
var config = variables['ixiamenConfig']
var accessToken = variables['ixiamenAccessToken']

if (!accessToken) {
    out.println("错误: 未找到 accessToken，请先获取 token")
    return 'api_stop'
}

// 用户信息接口地址
var userInfoUrl = "${config.baseUri}server/public/user/get"

out.println("开始获取用户信息")

try {
    // 使用 POST JSON 方法调用用户信息接口（空 JSON 对象）
    var response = HttpUtils.postJson(userInfoUrl, [:], String.class) { headers ->
        headers.add('Authorization', "Bearer ${accessToken}")
    }

    if (response.statusCode.value == 200) {
        var result = JsonUtils.deserialize(response.body, Map.class)

        // 提取用户信息
        var userInfo = [
            openId: result?.openId,
            personName: result?.personName,
            mobile: result?.mobile,
            mobileFuzzy: result?.mobileFuzzy,
            certifId: result?.certifId,
            certifType: result?.certifType,
            userType: result?.userType
        ]

        // 存储用户信息供后置脚本使用
        variables['ixiamenUserInfo'] = userInfo

        out.println("用户信息获取成功")
    } else {
        out.println("错误: 用户信息请求失败，状态码: ${response.statusCode.value}")
        out.println("响应内容: ${response.body}")
        return 'api_stop'
    }
} catch (Exception e) {
    out.println("异常: 用户信息请求出错 - ${e.message}")
    return 'api_stop'
}
```

**前置脚本说明**：

| 步骤 | 操作 | 涉及变量 |
|------|------|----------|
| 1 | code 换 accessToken | `ixiamenAccessToken` |
| 2 | token 换用户信息 | `ixiamenUserInfo` |

---

## 后置脚本

**职责**：格式化用户信息响应

```groovy
// ========== 后置脚本：格式化用户信息响应 ==========
import com.egova.json.utils.JsonUtils

// 获取用户信息
var userInfo = variables['ixiamenUserInfo']

if (!userInfo) {
    out.println("警告: 未找到用户信息")
    return
}

// 构建标准响应格式
var response = [
    success: true,
    data: [
        openId: userInfo.openId,
        personName: userInfo.personName,
        mobile: userInfo.mobile,
        certifId: userInfo.certifId,
        certifType: userInfo.certifType
    ],
    message: "获取用户信息成功"
]

// 设置响应体
request.setBody(JsonUtils.serialize(response))

out.println("响应已格式化")
```

**响应格式**：

```json
{
  "success": true,
  "data": {
    "openId": "17D22C4EEFFA39A0E",
    "personName": "系统运维9",
    "mobile": "13800138000",
    "certifId": "350200199001011234",
    "certifType": 0
  },
  "message": "获取用户信息成功"
}
```

---

## 退出登录

> **注意**：目前只支持 channel=IXM 和 IXM_PC，只支持 H5 和 PC 的退出登录，微信小程序不支持。

```javascript
const redirectUri = "https://xxxx/" // 业务平台自己的地址
const logoutUri = `https://buss.ixiamen.org.cn/pbc/usercenter/web/#/logout?channel=IXM&redirectUri=${redirectUri}`
window.location.href = logoutUri
```

---

## 参考资料

| 资源 | 地址 |
|------|------|
| **i 厦门接口文档** | https://buss.ixiamen.org.cn/pbc/liteapp-dev-mgr/web/#/document |
| **i 厦门开放平台** | https://open.ixiamen.org.cn/ |

---

## 相关 API 参考

- **HTTP 请求** → `../.claude/skills/starbridge-script/references/http-api.md`
- **上下文操作** → `../.claude/skills/starbridge-script/references/context-api.md`
- **业务案例** → `../.claude/skills/starbridge-script/references/business-cases.md`
