# 前置/后置脚本 API 参考

> 星桥平台前置/后置脚本的通用 API 参考手册，基于 `com.egova.*` 工具类的脚本开发指南

## 概述

- **前置脚本**：在接口调用前执行，用于调整请求参数、添加鉴权信息、参数校验和转换等
- **后置脚本**：在接口调用后执行，用于修改返回值、数据扩展、格式转换、错误码转换等

本文档中的 API 适用于**前置脚本和后置脚本**。

---

## 一、内置变量与全局操作

### 1.1 全局变量 (variables)

`variables` 是一个 Map<String, Object> 类型的全局变量存储，用于在鉴权、前置、后置脚本间传递数据。

```groovy
// 获取全局变量
var value = variables["name"]

// 设置全局变量
variables["name"] = "value"

// 存储复杂对象
variables["config"] = [
    url: "https://api.example.com",
    timeout: 30000
]
```

### 1.2 日志输出 (out)

使用 `out.println()` 在所有阶段输出日志信息：

```groovy
// 输出字符串
out.println("脚本开始执行")

// 输出变量值
def userId = request.getQueryParam("userId")
out.println("当前用户ID: ${userId}")

// 输出对象
def config = variables.get("config")
out.println("配置信息: ${config}")
```

### 1.3 终止执行

使用 `return 'api_stop'` 提前终止请求处理：

```groovy
// 前置脚本执行完毕后提前终止，后续接口调用、结果转换、后置脚本操作不执行
return 'api_stop'
```

**使用场景**：

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
```

---

## 二、请求操作 (request)

### 2.1 URI/Path 操作

```groovy
// 获取请求 URI
var uri = request.getUri()

// 设置请求 URI
request.setUri('http://127.0.0.1:8018/some/path?querystring=dex')

// 获取请求 path
var path = request.getPath()

// 设置请求 path
request.setPath('/some/path')
```

### 2.2 请求头操作

```groovy
// 获取请求头
def header = request.getHeader('Content-Type')

// 设置请求头
request.setHeader('Content-Type', 'application/json')
request.setHeader('Authorization', 'Bearer token123')

// 移除请求头
request.removeHeader('Authorization')
```

### 2.3 Query 参数操作

```groovy
// 获取单个 Query 参数
def value = request.getQueryParam('参数名称')

// 获取所有 Query 参数
def params = request.getQueryParams()

// 设置 Query 参数值
request.setQueryParam('参数名称', '参数值')

// 移除 Query 参数值
request.removeQueryParam('参数名称')
```

### 2.4 请求体操作

```groovy
// 获取请求体内容（字符串）
def str = request.getBody().getString()

// 获取请求体内容（application/x-www-form-urlencoded）
def map = request.getBody().getParams()

// 设置新的内容到请求体（字符串）
request.setBody('设置新的body字符串')

// 设置新的内容到请求体（application/x-www-form-urlencoded）
request.setBody(map)
```

### 2.5 重定向控制

```groovy
// 禁用重定向
request.setRedirectsEnabled(false)
```

---

## 三、数据库操作 (sql)

### 3.1 获取查询模板

```groovy
// 获取 SQL 查询操作模板
var queryTemplate = sql.of('数据源名称')

// 获取命名 SQL 查询操作模板
var namedQueryTemplate = sql.ofNamed('数据源名称')
```

### 3.2 单条查询

```groovy
// 普通 SQL 查询一条数据
var map = queryTemplate.forMap('select * from table where name = ? and sex = ?', ['zhangsan', '男'] as Object[])

// 命名 SQL 查询一条数据
var map = namedQueryTemplate.forMap('select * from table where id in (:ids) and sex = :sex', ['ids': [1, 2], 'sex': '男'])
```

### 3.3 多条查询

```groovy
// 普通 SQL 查询多条数据（默认10条）
var list = queryTemplate.forList('select * from table where name LIKE ? and sex = ?', ['zhang%', '男'] as Object[])

// 普通 SQL 查询多条数据（限制条数）
var list = queryTemplate.forList('select * from table where name LIKE ? and sex = ?', limit, ['zhang%', '男'] as Object[])

// 命名 SQL 查询多条数据（默认10条）
var list = namedQueryTemplate.forList('select * from table where id in (:ids) and sex = :sex', ['ids': [1, 2], 'sex': '男'])

// 命名 SQL 查询多条数据（限制条数）
var list = namedQueryTemplate.forList('select * from table where id in (:ids) and sex = :sex', limit, ['ids': [1, 2], 'sex': '男'])
```

### 3.4 分页查询

```groovy
// 普通 SQL 分页查询数据
var page = queryTemplate.forPage('select * from table where name LIKE ? and sex = ?', pageIndex, pageSize, ['zhang%', '男'] as Object[])

// 命名 SQL 分页查询数据
var page = namedQueryTemplate.forPage('select * from table where id in (:ids) and sex = :sex', pageIndex, pageSize, ['ids': [1, 2], 'sex': '男'])
```

---

## 四、三方 Token 管理 (tokenStore)

### 4.1 获取 Token

```groovy
// 系统标识
var type = 'default'
// 系统参数
var params = [
    'url': 'http://127.0.0.1:18014/oauth/extras/token',
    'clientId': 'unity-client',
    'clientSecret': 'unity'
]
// 获取 token
var token = tokenStore.load(type, params)
out.println(token.value)
```

**使用场景**：

```groovy
// 获取城管认证 Token
var type = 'mis'
var params = [
    'url': 'https://127.0.0.1:8080/eUrbanMIS/mobile/pub/gettokenbyhumanid',
    'humanId': '100433'
]
var token = tokenStore.load(type, params)
request.setQueryParam('token', token.value)
```

---

## 五、工具类 API

### 5.1 JSON/XML 处理

```groovy
// JSON 反序列化
var map = com.egova.json.utils.JsonUtils.deserialize(data, Map.class)

// JSON 反序列化（多条）
var list = com.egova.json.utils.JsonUtils.deserializeList(data, Map.class)

// JSON 序列化
var str = com.egova.json.utils.JsonUtils.serialize(map)

// XML 转 JSON
var jsonStr = com.egova.api.util.XmlUtils.toJson(xmlStr)

// JSON 转 XML
var xmlStr = com.egova.api.util.XmlUtils.toXml(jsonStr)
```

### 5.2 编码转换

#### Base64 编码/解码

```groovy
// Base64 加密
var encode = com.egova.api.util.Base64Utils.encode('admin:12345')

// Base64 解密
var decode = com.egova.api.util.Base64Utils.decode('YWRtaW46MTIzNDU2')
```

#### Map 字段重命名

```groovy
// 修改 map 中 key 名称
map = com.egova.api.util.MapUtils.rename(map, ['NAME': 'name', 'AGE': 'age', 'SEX': 'sex'])
```

### 5.3 哈希算法

#### MD5

```groovy
// MD5 加密（长度32位小写字符串）
var encode = com.egova.api.util.Md5Utils.encode('admin:123456')
```

#### SHA1/SHA256

```groovy
// SHA1 加密
var str = org.apache.commons.codec.digest.DigestUtils.sha1Hex('字符串')

// SHA256 加密
var str = org.apache.commons.codec.digest.DigestUtils.sha256Hex('字符串')
```

#### 国密 SM3

```groovy
import com.egova.dex.util.Sm3Utils
import com.egova.dex.util.HexUtils

// 对于任意长度的字符串，都返回256bit
var res = Sm3Utils.encode('星桥')
out.println(Arrays.toString(res))

// 结果转hex字符串
out.println(HexUtils.encodeToString(res))
```

### 5.4 对称加密

#### AES 加密/解密

```groovy
// AES[CBC] 加密（使用MIS配置）
var str = com.egova.api.util.AESUtils.encrypt('sSrc')

// AES[CBC] 加密（使用MD5加密的MIS配置）
var str = com.egova.api.util.AESUtils.encryptMD5key('sSrc')

// AES[CBC] 加密（src、key、ivParam）
var str = com.egova.api.util.AESUtils.encrypt('src', 'key', 'ivParam')

// AES[CBC] 加密（使用随机IV）
var str = com.egova.api.util.AESUtils.encrypt('src', 'key')

// AES[CBC] 解密（使用MIS配置）
var str = com.egova.api.util.AESUtils.decrypt('sSrc')

// AES[CBC] 解密（key、cipherWithIV）
var str = com.egova.api.util.AESUtils.decryptWithIV('cipherWithIV')

// AES[CBC] 解密（cipherWithIV）
var str = com.egova.api.util.AESUtils.decryptWithIVAndKey('key', 'cipherWithIV')

// AES[CBC] 解密（src、key、ivParam）
var str = com.egova.api.util.AESUtils.decrypt('src', 'key', 'ivParam')

// AES[CBC] 加密（返回base64加密字符串）
var str = com.egova.api.util.AESUtils.encryptData('data', '16位key', 'UTF-8')

// AES[CBC] 解密
var str = com.egova.api.util.AESUtils.decryptData('base64 data', '16位key', 'UTF-8')
```

#### DES 加密/解密

```groovy
// DES 加密
var str = com.egova.api.util.DESUtils.encrypt('data', 'key')

// DES 加密（指定encodeType）
var str = com.egova.api.util.DESUtils.encrypt('data', 'key', 'encodeType')

// DES 解密
var str = com.egova.api.util.DESUtils.decrypt('data', 'key')

// DES 解密（指定encodeType）
var str = com.egova.api.util.DESUtils.decrypt('data', 'key', 'encodeType')
```

#### 3DES 加密/解密

```groovy
// 3DES 加密（ECB）
var str = com.egova.api.util.TripleDesUtils.encodeByECB('data', 'key')

// 3DES 加密（CBC）
var str = com.egova.api.util.TripleDesUtils.encodeByCBC('data', 'key', 'iv')

// 3DES 解密（ECB）
var str = com.egova.api.util.TripleDesUtils.decodeByECB('data', 'key')

// 3DES 解密（CBC）
var str = com.egova.api.util.TripleDesUtils.decodeByCBC('data', 'key', 'iv')
```

#### 国密 SM4 加密/解密

**SM4/ECB/PKCS5Padding**:

```groovy
import java.util.Base64
import com.egova.dex.util.HexUtils
import com.egova.dex.util.Sm4Utils

// 原始文本
var text = "星桥"
// 这里是原始的16字节字符串密钥，如果是base64、hex则需要先解码
var key = "1234567887654321"
byte[] data = Sm4Utils.encrypt(text.getBytes(), key.getBytes())

// 结果加密成base64
var base64Str = Base64.getEncoder().encodeToString(data)
out.println(base64Str)

// 结果加密成hex
var hexStr = HexUtils.encodeToString(data)
out.println(hexStr)
```

**SM4/CBC/PKCS5Padding**:

```groovy
import java.util.Base64
import com.egova.dex.util.HexUtils
import com.egova.dex.util.Sm4Utils

// 原始文本
var text = "星桥"
// 这里是原始的16字节字符串密钥，如果是base64、hex则需要先解码
var key = "1234567887654321"
// 这里是原始的16字节字符串iv参数，如果是base64、hex则需要先解码
var iv = "1234567887654321"
byte[] data = Sm4Utils.encrypt(text.getBytes(), key.getBytes(), iv.getBytes())

// 结果加密成base64
var base64Str = Base64.getEncoder().encodeToString(data)
out.println(base64Str)

// 结果加密成hex
var hexStr = HexUtils.encodeToString(data)
out.println(hexStr)
```

**SM4 解密**:

```groovy
import java.util.Base64
import com.egova.dex.util.Sm4Utils

// sm4加密后，再base64后的秘文
var text = "ZlgdYb38KZ3YSwqMCv36xg=="
// 这里是原始的16字节字符串密钥，如果是base64、hex则需要先解码
var key = "1234567887654321"
byte[] data = Sm4Utils.decrypt(Base64.getDecoder().decode(text), key.getBytes())
var str = new String(data)
out.println(str)
```

### 5.5 非对称加密

#### RSA 加密/解密

```groovy
// RSA 加密（该方法参数均需要通过base64加密）
var str = com.egova.api.util.RSAUtils.encrypt('s', 'publicKey')

// RSA 解密（该方法参数均需要通过base64加密）
var str = com.egova.api.util.RSAUtils.decrypt('s', 'privateKey')
```

### 5.6 字典工具

```groovy
// 获取字典
var value = com.egova.api.util.dict.DictUtils.get('字典类型', '字典项名称')

// 获取字典（全部）
var map = com.egova.api.util.dict.DictUtils.getAll('字典类型')
```

### 5.7 GIS 坐标转换

```groovy
// WGS84转当地平面
var xy = com.egova.api.util.gis.GisUtils.convert('A', '-82415.3914051056#2969.1174163818#0.00541075559597633#1.00000425185696#0#120', 114.215982, 30.461412)
var x = xy[0]
var y = xy[1]
```

### 5.8 日期时间

```groovy
import com.flagwind.commons.Monment

// 获取5分钟之前的时间
def date = Monment.now().addMinutes(-5)
def str = date.toString('yyyy-MM-dd HH:mm:ss')
```

---

## 六、HTTP 请求 (HttpUtils)

### 6.1 GET 请求

```groovy
// HTTP GET 请求
ResponseEntity<T> response = com.egova.api.util.http.HttpUtils.get(String url, Class<T> responseType, Consumer<HttpHeaders> headersConsumer)
```

### 6.2 POST 请求

```groovy
// HTTP POST 请求（JSON）
ResponseEntity<T> response = com.egova.api.util.http.HttpUtils.postJson(String url, Object data, Class<T> responseType, Consumer<HttpHeaders> headersConsumer)

// HTTP POST 请求（Form）
ResponseEntity<T> response = com.egova.api.util.http.HttpUtils.postForm(String url, Map<String, Object> data, Class<T> responseType, Consumer<HttpHeaders> headersConsumer)
```

### 6.3 PUT 请求

```groovy
// HTTP PUT 请求（JSON）
ResponseEntity<T> response = com.egova.api.util.http.HttpUtils.putJson(String url, Object data, Class<T> responseType, Consumer<HttpHeaders> headersConsumer)
```

### 6.4 DELETE 请求

```groovy
// HTTP DELETE 请求
ResponseEntity<T> response = com.egova.api.util.http.HttpUtils.delete(String url, Class<T> responseType, Consumer<HttpHeaders> headersConsumer)
```

---

## 七、Kafka 消息发送

```groovy
// 发送数据到 kafka
var kafkaTemplate = com.egova.api.util.Kafka.of('ddcat数据源名称')
kafkaTemplate.send('topic', 'data')
```

---

## 八、完整业务案例

### 8.1 上报字段调整

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

### 8.2 访问城管认证

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

### 8.3 获取第三方接口 Token

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
var body = HttpUtils.postForm(oauthUrl, tkParam, String.class).getBody()
// 反序列化 {"data": {"accessToken": "xxx"}}
var result = JsonUtils.deserialize(body, Map.class)
// 得到 token 值
var token = result?.data?.accessToken
// 将 token 设置到请求参数中
request.setQueryParam('accessToken', token)
```

### 8.4 通通停车接口签名

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

### 8.5 获取时间偏移

```groovy
// ========== 前置脚本：获取5分钟之前的时间 ==========
import com.flagwind.commons.Monment

// 当前时间减 5 分钟
def date = Monment.now().addMinutes(-5)
def str = date.toString('yyyy-MM-dd HH:mm:ss')
```

### 8.6 查库上报案件

```groovy
// ========== 前置脚本：查库获取案卷信息 调上报接口生成案件 ==========
import com.egova.json.utils.JsonUtils
import com.egova.api.util.http.HttpUtils

// 智云平台编码
var senderCode = '362200'
// 标准对接操作类型
var actionType = 'UP_REC_REPORT'
// v11多媒体地址
var fileServerAddr = 'http://127.0.0.1:8088/MediaRoot/'
// 智云上报接口地址
var reportURL = 'http://127.0.0.1:8082/eUrbanMIS/openapi/v2/upstream'
var queryTemplate = sql.of('晋江v11')

// 从表里面查询数据
var recList = queryTemplate.forList('select * from dlmis.torec where recid in (1258623,1256926)')
var recListStr = JsonUtils.serialize(recList)

// 遍历查询到的数据，逐条组装上报参数，调用上报接口
for(rec in recList) {
    // 多媒体图片数据格式转换
    var medias = []
    var medialist = queryTemplate.forList('select * from dlmis.torecmedia where recid = ' + rec['RECID'])
    for(pic in medialist) {
        var mediaURL = fileServerAddr + pic['MEDIAPATH'] + pic['MSGID'] + '_' + pic['MEDIAID'] + '_' + pic['MEDIANAME']
        var media = [
            'mediaName': pic['MEDIANAME'],
            'mediaURL': mediaURL,
            'mediaType': 'IMAGE',
            'mediaUsage': '上报'
        ]
        medias.add(media)
    }

    var evenTypeCode = ''
    var mainTypeCode = ''
    var subTypeCode = ''

    var typeCodes = queryTemplate.forMap('select * from dlsys.tcdiceventanytypenew where typename = ?', [rec['EVENTTYPENAME']] as Object[])
    // 设置问题类型
    if(typeCodes != null) {
        evenTypeCode = typeCodes['UNIQUECODE']
    }

    // 设置大类
    var mainTypeCodes = queryTemplate.forMap('select * from dlsys.tcdiceventanytypenew where typename = ?', [rec['MAINTYPENAME']] as Object[])
    if(mainTypeCodes != null) {
        mainTypeCode = mainTypeCodes['UNIQUECODE']
    }

    // 设置小类
    var subTypeCodes = queryTemplate.forMap('select * from dlsys.tcdiceventanytypenew where typename = ?', [rec['SUBTYPENAME']] as Object[])
    if(subTypeCodes) {
        subTypeCode = subTypeCodes['UNIQUECODE']
    }

    transferData = [
        'otherTaskNum': rec['TASKNUM'],
        'eventLevelID': '1',
        'eventTypeCode': evenTypeCode,
        'mainTypeCode': mainTypeCode,
        'subTypeCode': subTypeCode,
        'maxTypeCode': subTypeCode,
        'newInstCondID': rec['NEWINSTCONDID'],
        'coordinateX': rec['COORDINATEX'],
        'coordinateY': rec['COORDINATEY'],
        'eventDesc': rec['EVENTDESC'],
        'address': rec['ADDRESS'],
        'createTime': rec['CREATETIME'],
        'humanName': rec['PATROLNAME'],
        'cellphone': '',
        'medias': medias,
        'mediaNum': medias.size()
    ]

    var requestMap = [
        'senderCode': senderCode,
        'actionType': actionType,
        'data': JsonUtils.serialize(transferData)
    ]

    out.println(requestMap)

    // 调用上报接口
    var response = HttpUtils.postForm(reportURL, requestMap, String.class)
}
```

### 8.7 WebService 请求

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

---

## 注意事项

1. **com.egova.* 工具类**：本文档基于星桥平台内置的 `com.egova.*` 工具类，如需使用 Hutool 风格 API，请参考其他参考文档
2. **命名 SQL 参数**：使用命名 SQL 时，参数 Map 的 key 需要匹配 SQL 中的占位符名称（如 `:ids`, `:sex`）
3. **tokenStore 缓存**：`tokenStore.load()` 内置缓存机制，Token 过期会自动重新获取
4. **国密算法**：国密 SM3/SM4 需要平台额外配置支持
5. **请求体处理**：修改请求体时注意 Content-Type 与数据格式匹配
6. **异常处理**：使用 `try-catch` 处理可能的异常，必要时使用 `return 'api_stop'` 终止执行
7. **日志输出**：使用 `out.println()` 输出调试信息，便于问题排查
