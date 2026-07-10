# 上下文变量 API

> 星桥脚本中操作请求上下文的内部 API 说明

## 内置变量清单

| 变量名 | 类型 | 可用阶段 | 说明 |
|-------|------|---------|------|
| `request` | ScriptRequest | 鉴权/前置/后置 | 当前请求对象，包含 URI、Path、Header、Query、Body |
| `out` | 日志输出对象 | 鉴权/前置/后置 | 使用 `out.println()` 输出日志（所有阶段可用） |
| `tokenStore` | TokenStore | 鉴权/前置/后置 | 三方系统 Token 存储，用于管理第三方接口 Token |
| `sql` | SqlExecutor | 鉴权/前置/后置 | SQL 查询执行器，用于数据库操作 |
| `variables` | Map<String, Object> | 鉴权/前置/后置 | 全局变量存储，脚本间数据传递 |

---

## 日志输出

使用 `out.println()` 在所有阶段输出日志信息：

```groovy
// 输出调试信息
out.println("脚本开始执行")

// 输出变量值
def userId = request.getQueryParam("userId")
out.println("当前用户ID: ${userId}")

// 输出复杂对象
def config = variables.get("config")
out.println("配置信息: ${config}")

// 输出异常信息
try {
    // 业务逻辑
} catch (Exception e) {
    out.println("处理异常: ${e.message}")
}
```

---

## 终止执行

使用 `return 'api_stop'` 终止请求处理：

```groovy
// 参数校验失败时终止
def userId = request.getQueryParam("userId")
if (!userId) {
    out.println("错误: userId 参数不能为空")
    return 'api_stop'
}

// Token 不存在时终止
def token = variables.get("accessToken")
if (!token) {
    out.println("错误: 未获取到访问令牌")
    return 'api_stop'
}

// 业务校验失败时终止
def config = sql.of("SELECT * FROM config WHERE id = ?").forMap("001")
if (!config) {
    out.println("错误: 未找到配置信息")
    return 'api_stop'
}
```

---

## 请求参数操作

### 修改请求 URI

```groovy
// 修改完整请求地址
request.setUri("https://api.example.com/new-endpoint")
var uri = request.getUri()

// 修改路径部分
request.setPath("/v2/users")
var path = request.getPath()
```

### 修改请求头

```groovy
// 添加单个请求头
request.setHeader("Authorization", "Bearer token123")
request.setHeader("Content-Type", "application/json")

// 读取请求头
def authHeader = request.getHeader("Authorization")

// 删除请求头
request.removeHeader("X-Old-Header")
```

### 修改 Query 参数

```groovy
// 添加单个参数
request.setQueryParam("page", "1")
request.setQueryParam("size", "10")

// 读取 Query 参数
def page = request.getQueryParam("page")

// 获取所有 Query 参数
var params = request.getQueryParams()

// 删除 Query 参数
request.removeQueryParam("oldKey")
```

### 修改请求体

```groovy
// 读取请求体
var str = request.getBody().getString()

// 设置新的请求体
request.setBody("new body string")

// 设置 JSON 请求体
import cn.hutool.json.JSONUtil
def jsonData = [name: "张三", age: 30]
request.setBody(JSONUtil.toJsonStr(jsonData))
```

### 移除并重设 Header (模拟真实请求)

在调用严格限制客户端的第三方接口时，可移除星桥默认的 Header 并设置模拟的 `User-Agent`。

```groovy
// 移除代理及真实 IP 暴露头
request.removeHeader("user-agent");
request.removeHeader("x-real-ip");
request.removeHeader("x-forwarded-for");
request.removeHeader("x-forwarded-proto");

// 设置模拟浏览器 User-Agent
request.setHeader('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36');
```

### 生成动态字段 (时间戳/随机数)

```groovy
import java.time.Instant;
import java.util.UUID;

// 生成毫秒时间戳
request.setHeader("timestamp", Instant.now().toEpochMilli().toString());

// 生成 16 位不带杠的随机 nonce
request.setHeader("nonce", UUID.randomUUID().toString().replaceAll("-", "").substring(0, 16));
```

---

## 常用内置功能

### 空请求逻辑接口

星桥提供了一个特殊的空接口，仅用于触发前后置脚本执行代码逻辑，而不实际调用任何后端服务。

**接口地址**：`/free/req-resp` (POST 请求)

**示例**：
`http://127.0.0.1:8018/dex-api/free/req-resp`

---

## 全局变量操作

全局变量 `variables` 用于在脚本间传递数据（鉴权 → 前置 → 后置）。

### 存储和读取变量

```groovy
// 存储变量（通常在鉴权脚本中）
variables["serverUrl"] = "https://api.example.com"
variables["appKey"] = "your-app-key"
variables["appSecret"] = "your-app-secret"

// 读取变量（在前置/后置脚本中）
var url = variables["serverUrl"]
var key = variables["appKey"]

// 存储复杂对象
variables["config"] = [
    url: "https://api.example.com",
    timeout: 30000,
    retry: 3
]
var config = variables["config"]
```

### 变量使用场景

```groovy
// ========== 鉴权脚本 ==========
// 统一管理所有配置项
variables["baseUrl"] = "https://third-party.com"
variables["accessKey"] = "xxx"
variables["secretKey"] = "xxx"

// ========== 前置脚本 ==========
// 读取配置并使用
var url = variables["baseUrl"] + "/api/user"
request.setUri(url)
request.setHeader("AccessKey", variables["accessKey"])

// ========== 后置脚本 ==========
// 读取配置进行处理
var baseUrl = variables["baseUrl"]
out.println("处理完成，目标服务器: ${baseUrl}")
```

---

## 三方系统 Token 获取

星桥平台提供 `tokenStore` 用于管理第三方接口的 Token，内置缓存机制，Token 过期会自动重新获取。

### 使用 tokenStore.load() 获取 Token

```groovy
// 系统标识
var type = 'mis'
// 系统参数
var params = [
    'url': 'https://127.0.0.1:8080/eUrbanMIS/mobile/pub/gettokenbyhumanid',
    'humanId': '100433'
]
// 获取 token
var token = tokenStore.load(type, params)
out.println(token.value)
```

### 完整示例：城管认证 Token

```groovy
// ========== 前置脚本：访问城管认证 ==========
// 系统标识
var type = 'mis'
// 参数
var params = [
    // 地址
    'url': 'https://127.0.0.1:8080/eUrbanMIS/mobile/pub/gettokenbyhumanid',
    // 人员ID
    'humanId': '100433'
]
// 获取 token，底层会 token 缓存，401 时清理
var token = tokenStore.load(type, params)
// 设置 token 到 query 参数上
request.setQueryParam('token', token.value)
```

### 参数说明

| 参数 | 类型 | 说明 |
|-----|------|------|
| `type` | String | 系统标识，用于区分不同的三方系统 |
| `params` | Map | 获取 Token 所需的参数，通常包含 `url`、`clientId`、`clientSecret` 等 |

---

## 注意事项

1. **变量作用域**：`variables` 在鉴权、前置、后置脚本中共享，适合存储配置项
2. **tokenStore 缓存**：`tokenStore.load()` 内置缓存机制，Token 过期会自动重新获取，无需手动管理
3. **终止执行位置**：`return 'api_stop'` 可在所有阶段使用
4. **日志输出**：`out.println()` 在所有阶段都可用，用于调试和问题排查
5. **API 调用方式**：request 对象的方法必须使用方法调用方式（如 `setUri()`），不能使用属性赋值
