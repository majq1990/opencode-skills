# 业务案例集合

> 星桥 Groovy 脚本的典型业务场景实现示例

## 访问城管认证

### 场景描述

调用第三方城管系统接口时，需要先进行认证获取 Token，然后在请求参数中携带 Token。

### 前置脚本

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

---

## 获取第三方接口 Token

### 场景描述

调用第三方接口时使用 OAuth2 client_credentials 模式获取访问令牌。

### 前置脚本

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

---

## 通通停车接口签名

### 场景描述

调用通通停车接口需要根据特定算法生成签名，包含时间戳、密钥等参数。

### 鉴权脚本

```groovy
// ========== 鉴权脚本：通通签名配置 ==========
def config = [
    apiUrl: "https://api.tongtong.com",
    appKey: "TT001",
    appSecret: "your_secret_key",
    partnerId: "PARTNER001"
]

// 存储配置
variables["tongtongApiUrl"] = config.apiUrl
variables["tongtongAppKey"] = config.appKey
variables["tongtongAppSecret"] = config.appSecret
variables["tongtongPartnerId"] = config.partnerId
```

### 前置脚本

```groovy
// ========== 前置脚本：通通签名生成 ==========
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

out.println("签名生成完成: ${map['sign']}")
```

---

## 获取5分钟之前的时间

### 场景描述

查询数据时需要获取当前时间前5分钟的时间，用于筛选最近的数据。

### 前置脚本

```groovy
// ========== 前置脚本：获取5分钟之前的时间 ==========
import com.flagwind.commons.Monment

// 当前时间减 5 分钟
def date = Monment.now().addMinutes(-5)
def str = date.toString('yyyy-MM-dd HH:mm:ss')
```

---

## 动态修改请求地址

### 场景描述

根据请求参数动态修改目标接口地址。

### 前置脚本

```groovy
// ========== 前置脚本：动态修改请求地址 ==========

// 获取环境参数
def env = request.getQueryParam("env")
def targetUrl

switch (env) {
    case "dev":
        targetUrl = "https://dev-api.example.com"
        break
    case "test":
        targetUrl = "https://test-api.example.com"
        break
    case "prod":
        targetUrl = "https://api.example.com"
        break
    default:
        out.println("错误: 无效的环境参数 ${env}")
        return 'api_stop'
}

// 修改请求 URI
def currentPath = request.getPath()
request.setUri(targetUrl + currentPath)

out.println("请求地址修改为: ${targetUrl}${currentPath}")
```

---

## 参数校验与转换

### 场景描述

在请求发送前进行参数校验，并进行必要的格式转换。

### 前置脚本

```groovy
// ========== 前置脚本：参数校验与转换 ==========

// 校验必填参数
def userId = request.getQueryParam("userId")
if (!userId) {
    out.println("错误: userId 参数不能为空")
    return 'api_stop'
}

// 校验参数格式
def dateStr = request.getQueryParam("date")
if (dateStr && !dateStr.matches("\\d{4}-\\d{2}-\\d{2}")) {
    out.println("错误: date 参数格式不正确，应为 yyyy-MM-dd")
    return 'api_stop'
}

// 参数转换：驼峰转下划线
def originalBody = request.getBody().getString()
import com.egova.json.utils.JsonUtils
def bodyMap = JsonUtils.deserialize(originalBody, Map.class)

def convertedBody = bodyMap.collectEntries { k, v ->
    [k.replaceAll(/([A-Z])/, /_$1/).toLowerCase(), v]
}

// 设置转换后的请求体
request.setBody(JsonUtils.serialize(convertedBody))
out.println("参数转换完成")
```

---

## 日志记录与调试

### 场景描述

在脚本执行过程中输出关键信息，便于问题排查。

### 前置脚本

```groovy
// ========== 前置脚本：日志记录 ==========

// 输出请求基本信息
out.println("========== 请求开始 ==========")
out.println("请求 URI: ${request.getUri()}")
out.println("请求 Path: ${request.getPath()}")

// 输出请求头
out.println("---------- 请求头 ----------")
def contentType = request.getHeader("Content-Type")
out.println("Content-Type: ${contentType}")

// 输出 Query 参数
out.println("---------- Query 参数 ----------")
def allParams = request.getQueryParams()
allParams.each { k, v ->
    out.println("  ${k}: ${v}")
}

// 输出请求体（敏感信息脱敏）
out.println("---------- 请求体 ----------")
def body = request.getBody().getString()
def safeBody = body.replaceAll(/"password":"[^"]*"/, /"password":"***"/)
out.println("请求体: ${safeBody}")
out.println("========== 请求结束 ==========")
```

---

## 查库获取配置信息

### 场景描述

从数据库查询配置信息，用于后续请求处理。

### 前置脚本

```groovy
// ========== 前置脚本：查库获取配置 ==========

// 根据请求参数获取对应的接口配置
def apiCode = request.getQueryParam("apiCode")

var queryTemplate = sql.of('数据源名称')

def config = queryTemplate.forMap('''
    SELECT
        api_url,
        app_key,
        app_secret,
        timeout,
        retry_times
    FROM sys_api_config
    WHERE api_code = ?
    AND status = 1
''', [apiCode] as Object[])

if (!config) {
    out.println("错误: 未找到 API 配置，apiCode=${apiCode}")
    return 'api_stop'
}

// 存储配置供后续使用
variables["apiConfig"] = config
out.println("获取到配置: ${config.api_url}")

// 修改请求地址
request.setUri(config.api_url + request.getPath())
```

---

## 上报字段调整

### 场景描述

将第三方系统的案卷数据转换为城管上报格式。

### 前置脚本

```groovy
// ========== 前置脚本：上报字段调整 ==========
import com.egova.json.utils.JsonUtils

// 获取第三方的案件参数
var body = request.getBody().getString()
var bodyMap = JsonUtils.deserialize(body, Map.class)

// 转换为城管上报案件格式
// 设置 senderCode
request.setQueryParam('senderCode', '120110-02')

var reportData = [:]

// 转换字段
reportData['otherTaskNum'] = bodyMap['data']['recordId']
reportData['eventDesc'] = bodyMap['data']['eventName']
reportData['address'] = bodyMap['data']['address']
reportData['lontitude'] = bodyMap['data']['lng']
reportData['latitude'] = bodyMap['data']['lat']
reportData['eventSrcID'] = 1
reportData['recTypeID'] = 1

// 多媒体附件按需修改
var mediaList = []
var picUrl = bodyMap['data']['picList']
if(picUrl != null && picUrl.length() > 0) {
    var mediaUrls = picUrl.split(",")
    mediaUrls.each {
        def index = it.lastIndexOf("/")
        if (index >= 0) {
            def suffixPath = it.substring(index + 1)
            def pointIdx = suffixPath.lastIndexOf(".")
            if(pointIdx >= 0) {
                def type = suffixPath.substring(pointIdx + 1)
                def name = suffixPath.substring(0, pointIdx)
                mediaList.add([
                    "mediaType": type + "",
                    "content": "",
                    "mediaURL": it,
                    "mediaName": suffixPath + "",
                    "mediaUsage": "上报"
                ])
            }
        }
    }
}

// 以下勿动
reportData['medias'] = mediaList
request.setQueryParam('actionType', 'UP_REC_REPORT')
var dataJsonMap = ["data": JsonUtils.serialize(reportData)]
request.setHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
request.setBody(dataJsonMap)
```

---

## WebService 请求（SOAP）

### 场景描述

调用第三方 WebService 接口。

### 前置脚本

```groovy
// ========== 前置脚本：WebService 请求 ==========
// 获取定义的请求 JSON 数据
var str = request.getBody().getString()
var map = com.egova.json.utils.JsonUtils.deserialize(str, Map.class)

// webservice XML 请求数据
str = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
    <soapenv:Header/>
    <soapenv:Body>
        <tem:loginByAccount>
            <userid>${map.userId}</userid>
            <password>${map.password}</password>
        </tem:loginByAccount>
    </soapenv:Body>
</soapenv:Envelope>
"""

// 设置 XML 请求数据到请求体
request.setBody(str)
// 设置 XML 请求头
request.setHeader('Content-Type', 'application/xml')
```

## 扩展外部 JAR 包

### 场景描述

当内置工具类（Hutool、egova）无法满足需求（如特定的 UKey 驱动、复杂的加解密库）时，可以手动扩展 JAR。

### 步骤
1. **放置文件**：在星桥 `data-exchange.jar` 同级创建 `lib` 目录。
2. **复制 JAR**：将第三方 JAR 包放入 `lib`。
3. **启用配置**：确保启动脚本（如 `start.sh`）加载了 `lib` 目录中的库。
4. **导入调用**：
   ```groovy
   import com.custom.utils.UniqueKeyClient; // 从 JAR 包中导入
   UniqueKeyClient.login(user, pwd);
   ```

---

## 数据库维护第三方 Token

### 场景描述

由外部定时任务将第三方 Token 写入本地业务库，脚本直接读取库中最新的 Token 使用。

### 前置脚本

```groovy
// 获取 Token
var queryTemplate = sql.of('业务库');
var sqlMap = queryTemplate.forMap('SELECT token FROM aggregation_token WHERE id = ?', ['1'] as Object[]);

var token = sqlMap['token'];
request.setHeader("Authorization", "Bearer " + token);
```

---

## 定时更新 Token (后置脚本案例)

### 场景描述

对接接口成功获取 Token 后，将 Token 格式化为入库的标准 JSON 结构，以便后续通过定时任务或后续逻辑入库。

### 后置脚本

```groovy
import com.egova.json.utils.JsonUtils

// 提取响应中的 Token
var map = JsonUtils.deserialize(data, Map.class);
var token = map?.data?.token;

// 构造入库列表格式
var tempMap = [
    id: 1,
    token: token
];

var resultMap = [
    'data': [tempMap]
];

// 返回处理后的 JSON
return JsonUtils.serialize(resultMap);
```

---

## 自定义函数定义

脚本内支持定义辅助函数，使主逻辑更简洁。

```groovy
// 定义计算开始时间的辅助方法
def getStartTime(lastTime) {
    var monment = Monment.parseDate(lastTime).addDays(-1);
    return Math.round(monment.getTime() / 1000)
}

var startTime = getStartTime('2024-05-20');
```

1. **日志输出**：使用 `out.println()` 输出日志（所有阶段可用）
2. **终止执行**：使用 `return 'api_stop'` 终止请求处理
3. **API 调用方式**：request 对象必须使用方法调用，不能用属性赋值
4. **错误处理**：所有外部调用都应有 try-catch 处理
5. **配置管理**：所有配置项应通过 `variables` 集中管理
6. **Token 管理**：优先使用 `tokenStore.load()` 方法，内置缓存机制
