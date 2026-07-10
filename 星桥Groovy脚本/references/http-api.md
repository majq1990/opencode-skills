# HTTP 请求 API

> 星桥脚本中发起 HTTP 请求的内部 API 说明

## HttpUtils 方法签名

星桥平台提供 `com.egova.api.util.http.HttpUtils` 工具类用于发起 HTTP 请求。

### 基本方法

```groovy
// HTTP GET 请求
ResponseEntity<T> response = com.egova.api.util.http.HttpUtils.get(String url, Class<T> responseType, Consumer<HttpHeaders> headersConsumer)

// HTTP POST 请求（JSON）
ResponseEntity<T> response = com.egova.api.util.http.HttpUtils.postJson(String url, Object data, Class<T> responseType, Consumer<HttpHeaders> headersConsumer)

// HTTP POST 请求（Form）
ResponseEntity<T> response = com.egova.api.util.http.HttpUtils.postForm(String url, Map<String, Object> data, Class<T> responseType, Consumer<HttpHeaders> headersConsumer)

// HTTP PUT 请求（JSON）
ResponseEntity<T> response = com.egova.api.util.http.HttpUtils.putJson(String url, Object data, Class<T> responseType, Consumer<HttpHeaders> headersConsumer)

// HTTP DELETE 请求
ResponseEntity<T> response = com.egova.api.util.http.HttpUtils.delete(String url, Class<T> responseType, Consumer<HttpHeaders> headersConsumer)
```

### 返回值 ResponseEntity

| 属性 | 类型 | 说明 |
|-----|------|------|
| `statusCode.value` | int | HTTP 状态码 |
| `body` | T | 响应体内容（泛型类型） |
| `headers` | HttpHeaders | 响应头 |

---

## GET 请求示例

### 简单 GET 请求

```groovy
import com.egova.api.util.http.HttpUtils
import com.egova.json.utils.JsonUtils

def response = HttpUtils.get("https://api.example.com/users", String.class, null)
if (response.statusCode.value == 200) {
    def data = JsonUtils.deserialize(response.body, Map.class)
    out.println("请求成功: ${data}")
}
```

### 带查询参数的 GET

```groovy
// URL 拼接方式
def url = "https://api.example.com/users?page=1&size=10"
def response = HttpUtils.get(url, String.class, null)
```

---

## POST 请求示例

### JSON 请求

```groovy
import com.egova.api.util.http.HttpUtils
import com.egova.json.utils.JsonUtils

// 发送 JSON 数据
def requestBody = [
    name: "张三",
    age: 30,
    email: "zhangsan@example.com"
]

def response = HttpUtils.postJson("https://api.example.com/users", requestBody, String.class, null)

if (response.statusCode.value == 200 || response.statusCode.value == 201) {
    def result = JsonUtils.deserialize(response.body, Map.class)
    out.println("创建成功，ID: ${result.id}")
}
```

### Form 表单请求

```groovy
// 发送 Form 表单数据
def formData = [
    username: "admin",
    password: "123456",
    grant_type: "password"
]

def response = HttpUtils.postForm("https://api.example.com/oauth/token", formData, String.class, null)

if (response.statusCode.value == 200) {
    def result = JsonUtils.deserialize(response.body, Map.class)
    out.println("Token: ${result.access_token}")
}
```

---

## PUT 请求示例

```groovy
import com.egova.api.util.http.HttpUtils

// 更新用户信息
def updateData = [
    id: "123",
    name: "李四",
    age: 35
]

def response = HttpUtils.putJson("https://api.example.com/users/123", updateData, String.class, null)

if (response.statusCode.value == 200) {
    out.println("更新成功")
}
```

---

## DELETE 请求示例

```groovy
import com.egova.api.util.http.HttpUtils

def response = HttpUtils.delete("https://api.example.com/users/123", String.class, null)

if (response.statusCode.value == 204) {
    out.println("删除成功")
}
```

---

## 完整业务示例

### 获取第三方接口 Token

```groovy
// ========== 前置脚本：获取第三方接口 token 信息 ==========
import com.egova.api.util.http.HttpUtils
import com.egova.json.utils.JsonUtils

// 认证地址(现场需要根据实际情况修改)、参数
var oauthUrl = 'http://127.0.0.1:8081/open_api/v1.0/token'
var tkParam = [
    'appId': '',
    'appSecret': ''
]
// 调用接口，得到响应字符串
var body = HttpUtils.postForm(oauthUrl, tkParam, String.class).body
// 反序列化 {"data": {"accessToken": "xxx"}}
var result = JsonUtils.deserialize(body, Map.class)
// 得到 token 值
var token = result?.data?.accessToken
// 将 token 设置到请求参数中
request.setQueryParam('accessToken', token)
```

### 通通停车接口签名

```groovy
// ========== 前置脚本：通通停车接口签名 ==========
import com.flagwind.commons.Monment
import com.egova.api.util.Md5Utils
import org.springframework.web.util.UriUtils
import com.egova.json.utils.JsonUtils

// 得到 body 参数
var paramString = request.getBody().getString()

// 签名相关的参数
var map = [
    'accessID': '',
    'apiCode': 'getparks',
    'groupCode': 'B94C09EF47745',
    'secretKey': '',
    'timestamp': Monment.now().toString("yyyy-MM-dd HH:mm:ss")
]

// 计算签名
var str = "accessID=" + UriUtils.encode(map['accessID'], 'UTF-8') +
    "&apiCode=" + UriUtils.encode(map['apiCode'], 'UTF-8') +
    "&groupCode=" + UriUtils.encode(map['groupCode'], 'UTF-8') +
    "&param=" + UriUtils.encode(paramString, 'UTF-8') +
    "&timestamp=" + UriUtils.encode(map['timestamp'], 'UTF-8') +
    "&secretKey=" + map['secretKey']

// 这是因为转码要将空格替换为 + 而不是去掉
str = str.replace('%20', '+')
map['sign'] = Md5Utils.encode(str)
var bodyStr = str + "&sign=" + map['sign']

// 设置
request.setBody(bodyStr)
request.setHeader('Content-Type', 'application/x-www-form-urlencoded')
```

---

## 超时与错误处理

### 基本错误处理

```groovy
import com.egova.api.util.http.HttpUtils
import com.egova.json.utils.JsonUtils

try {
    def response = HttpUtils.get("https://api.example.com/data", String.class, null)

    if (response.statusCode.value == 200) {
        def data = JsonUtils.deserialize(response.body, Map.class)
        out.println("请求成功")
    } else if (response.statusCode.value == 401) {
        out.println("错误: Token 已过期")
        return 'api_stop'
    } else {
        out.println("错误: 请求失败，状态码 ${response.statusCode.value}")
        return 'api_stop'
    }
} catch (Exception e) {
    // 捕获网络异常
    out.println("异常: 网络请求异常 - ${e.message}")
    return 'api_stop'
}
```

## 使用 Hutool 发起 HTTP 请求

当内置的 `HttpUtils` 无法满足极度复杂的链式调用需求时，可以使用 Hutool 的 `HttpUtil` 或 `HttpRequest`。

### Hutool GET

```groovy
import cn.hutool.http.HttpUtil;

// 执行 GET 请求并获取 body
var body = HttpUtil.createGet("https://api.example.com/public-key").execute().body();
```

### Hutool POST

```groovy
import cn.hutool.http.HttpRequest;

// 设置 Header 并发送 JSON 体
var response = HttpRequest.post("https://api.example.com/oauth/token")
                .header("Content-Type", "application/json")
                .body(JsonUtils.serialize(bodyMap))
                .execute();
var token = response.body();
```

---

## 禁用操作与替代方案

### 禁用 URLEncoder 替代

部分沙箱环境禁用了 `java.net.URLEncoder`。

**替代方案**：使用 `org.springframework.web.util.UriUtils`。

```groovy
import org.springframework.web.util.UriUtils;
import java.nio.charset.StandardCharsets;

var encodedPath = UriUtils.encode(path, StandardCharsets.UTF_8.toString());
```

---

## 注意事项

1. **Content-Type 设置**：发送 JSON 数据时确保设置 `Content-Type: application/json`
2. **签名顺序**：接口签名时参数顺序需与第三方约定一致
3. **Token 过期**：使用 `tokenStore.load()` 管理 Token，内置缓存机制
4. **超时时间**：默认超时约 30 秒，超时后会抛出异常
5. **HTTPS 证书**：第三方接口使用自签名证书时可能需要平台配置信任
6. **日志输出**：使用 `out.println()` 输出日志便于排查问题
7. **终止执行**：遇到错误时使用 `return 'api_stop'` 终止请求处理
8. **响应体获取**：使用 `response.body` 获取响应体内容，而非 `response.content`
