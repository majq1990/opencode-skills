# API 脚本开发手册

本手册包含了前置脚本和后置脚本的常用语法、工具类调用及业务案例。脚本基于 **Groovy** 语法开发。

---

## 1. 前置脚本 (Pre-script)

**描述**：前置脚本在接口请求发起前执行，用于修改请求参数、获取 Token 或进行前置逻辑判断。
**系统变量**：`request`、`out`、`tokenStore`、`sql`、`variables`

### 1.1 变量与请求操作

| 功能 | 代码示例 |
| :--- | :--- |
| **获取全局变量** | `var value = variables['name'];` |
| **设置全局变量** | `variables['name'] = 'value';` |
| **日志输出** | `out.println(x);` |
| **终止执行 API** | `// 执行完毕后提前终止，后续接口调用等不执行` <br> `return 'api_stop';` |
| **获取请求 URI** | `var uri = request.getUri();` |
| **设置请求 URI** | `request.setUri('http://127.0.0.1:8018/path');` |
| **获取请求 Path** | `var path = request.getPath();` |
| **设置请求 Path** | `request.setPath('/some/path');` |
| **获取请求头** | `var header = request.getHeader('Content-Type');` |
| **设置请求头** | `request.setHeader('Content-Type', 'application/json');` |
| **移除请求头** | `request.removeHeader('Authorization');` |
| **获取 Query 参数** | `var value = request.getQueryParam('参数名');` |
| **获取所有 Query 参数** | `var params = request.getQueryParams();` |
| **设置 Query 参数** | `request.setQueryParam('参数名', '值');` |
| **移除 Query 参数** | `request.removeQueryParam('参数名');` |
| **获取请求体 (String)** | `var str = request.getBody().getString();` |
| **获取请求体 (Form)** | `var map = request.getBody().getParams();` |
| **设置请求体 (String)** | `request.setBody('新的 body 字符串');` |
| **设置请求体 (Form)** | `request.setBody(map);` |
| **禁用重定向** | `request.setRedirectsEnabled(false);` |
| **获取三方 Token** | `var params = ['url': '...', 'clientId': '...'];` <br> `var token = tokenStore.load('default', params);` |

### 1.2 数据库操作 (SQL)

| 功能 | 代码示例 |
| :--- | :--- |
| **获取 SQL 模板** | `var queryTemplate = sql.of('数据源名称');` |
| **查询单条数据** | `var map = queryTemplate.forMap('select * from table where name = ?', ['zhangsan'] as Object[]);` |
| **查询多条 (默认10条)** | `var list = queryTemplate.forList('select * from table where name LIKE ?', ['zhang%'] as Object[]);` |
| **查询多条 (限制条数)** | `var list = queryTemplate.forList('sql', limit, params);` |
| **分页查询** | `var page = queryTemplate.forPage('sql', pageIndex, pageSize, params);` |
| **命名 SQL 查询模板** | `var namedSql = sql.ofNamed('数据源');` |
| **命名 SQL 查询示例** | `namedSql.forMap('select * from t where id in (:ids)', ['ids': [1, 2]]);` |

### 1.3 工具类 (Common Utils)

#### JSON & XML
- **JSON 反序列化**: `var map = com.egova.json.utils.JsonUtils.deserialize(data, Map.class);`
- **JSON 序列化**: `var str = com.egova.json.utils.JsonUtils.serialize(map);`
- **XML 转 JSON**: `var jsonStr = com.egova.api.util.XmlUtils.toJson(xmlStr);`
- **JSON 转 XML**: `var xmlStr = com.egova.api.util.XmlUtils.toXml(jsonStr);`
- **修改 Map 中 Key 名称**: `map = com.egova.api.util.MapUtils.rename(map, ['OLD': 'new']);`

#### 加密解密 (Security)
- **MD5 (32位小写)**: `com.egova.api.util.Md5Utils.encode('text');`
- **Base64 加解密**: `com.egova.api.util.Base64Utils.encode/decode('text');`
- **AES (CBC)**: `com.egova.api.util.AESUtils.encrypt/decrypt('src', 'key', 'iv');`
- **DES**: `com.egova.api.util.DESUtils.encrypt/decrypt('data', 'key');`
- **3DES**: `com.egova.api.util.TripleDesUtils.encodeByECB/CBC('data', 'key');`
- **RSA**: `com.egova.api.util.RSAUtils.encrypt/decrypt('s', 'key');`
- **SHA1/SHA256**: `org.apache.commons.codec.digest.DigestUtils.sha1Hex/sha256Hex('text');`
- **国密 SM4 (ECB/CBC)**: 使用 `com.egova.dex.util.Sm4Utils` 进行加解密。
- **国密 SM3**: 使用 `com.egova.dex.util.Sm3Utils.encode` 返回 256bit 哈希。

#### 其他辅助
- **字典获取**: `com.egova.api.util.dict.DictUtils.get('字典类型', '项名称');`
- **GIS 坐标转换**: `com.egova.api.util.gis.GisUtils.convert('A', 'config', lon, lat);`
- **HTTP 请求**: 支持 `HttpUtils.get/postJson/postForm/putJson/delete` 等。
- **发送 Kafka**: `var kafka = com.egova.api.util.Kafka.of('数据源'); kafka.send('topic', 'data');`

---

## 2. 后置脚本 (Post-script)

**描述**：后置脚本在接口响应返回后执行，用于处理结果数据、转换格式或存入全局变量。
**系统变量**：`data` (原始响应内容), `out`, `headers` (响应头), `sql`, `variables`

### 2.1 核心操作
- **获取响应内容**: 直接使用 `data` 变量。
- **获取响应头**: 直接使用 `headers` 变量。
- **修改响应结果**: 后置脚本可以通过 `return` 返回处理后的字符串作为最终接口输出。

---

## 3. 业务案例 (Business Cases)

### 3.1 上报字段调整 (前置)
```groovy
import com.egova.json.utils.JsonUtils

// 获取原始 body
var body = request.getBody().getString()
var bodyMap = JsonUtils.deserialize(body, Map.class)

// 组装城管上报格式
var reportData = [:]
reportData['eventDesc'] = bodyMap['data']['eventName']
reportData['address'] = bodyMap['data']['address']
reportData['medias'] = [] // 附件转换逻辑...

request.setQueryParam('actionType', 'UP_REC_REPORT')
request.setBody(["data": JsonUtils.serialize(reportData)])
request.setHeader('Content-Type', 'application/x-www-form-urlencoded')
```

### 3.2 接口签名加密 (通通停车案例)
```groovy
import com.egova.api.util.Md5Utils
import org.springframework.web.util.UriUtils

// 签名逻辑示例
var paramString = request.getBody().getString()
var str = "accessID=" + UriUtils.encode(id, 'UTF-8') + "&param=" + UriUtils.encode(paramString, 'UTF-8')
var sign = Md5Utils.encode(str + "&secretKey=" + key)
request.setBody(str + "&sign=" + sign)
```

### 3.3 数据库查询并批量上报
```groovy
// 查库获取案卷，循环调用上报接口
var queryTemplate = sql.of('数据源')
var recList = queryTemplate.forList('select * from dlmis.torec where recid in (...)')
for(rec in recList) {
    // 组装 medias 并调用 HttpUtils.postJson(...)
}
```

### 3.4 响应结果转换 (后置)
```groovy
import com.egova.json.utils.JsonUtils
import com.egova.model.OperateResult

// 将 XML 或非标 JSON 转换为标准格式
var map = JsonUtils.deserialize(data, Map.class)
var resultList = map?.data?.rateRank?.collect { [ "name": it.regionName, "value": it.rate ] }
return JsonUtils.serialize(new OperateResult().success(resultList))
```
