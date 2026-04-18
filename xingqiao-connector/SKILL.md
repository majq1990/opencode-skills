---
name: xingqiao-connector
description: 星桥数据接入平台综合对接工具（星桥对接）。支持场景：1）数据模型SQL构造（需提供表结构）；2）API接口前置/后置脚本（需提供三方接口调用示例）；3）接口合并脚本（需提供需合并的接口调用示例）；4）物联网特殊场景脚本（设备对接/实时数据/海康设备）。调用前必须完成相关前置输入才能输出。
---

# 星桥对接 - 平台内脚本生成器

本 Skill 生成可直接在**星桥平台内**使用的 SQL 和 Groovy 脚本。

## ⚠️ 使用方式

**直接在对话中描述你的需求，我会输出生成的脚本代码。**

### 代码传输规范

由于钉钉消息有字数限制，**超长代码（>500字符）** 采用以下方式传输：

- ✅ **下载链接**：代码保存为文件，提供 `http://47.110.57.11:8888/文件名` 下载
- ✅ **文件位置**：`/root/.openclaw/workspace/`
- ❌ **避免直接粘贴**：代码直接粘贴到消息会导致被拆分成多块，显示混乱

**示例**：
```
📥 下载地址：http://47.110.57.11:8888/script_name.groovy

使用说明：
1. 下载文件
2. 复制内容到星桥前置/后置脚本
3. 配置参数
```

## 脚本执行流程

```
请求进入 → [鉴权脚本] → [前置脚本] → 实际接口调用 → [后置脚本] → 返回响应
```

| 脚本类型 | 执行时机 | 核心职责 |
|---------|---------|---------|
| **鉴权脚本** | 最先执行 | 存储配置项（服务地址、密钥、Token等），供后续脚本使用 |
| **前置脚本** | 接口调用前 | 调整请求参数、执行前置逻辑（如签名计算、参数转换） |
| **后置脚本** | 接口调用后 | 修改返回值、数据扩展、格式转换、错误处理 |

## 配置传递方式

**所有配置项必须在鉴权脚本中统一管理**，使用 `variables` 进行跨脚本传递：

```groovy
// ========== 鉴权脚本：存储配置 ==========
variables["config"] = [
    serverUrl: "https://api.example.com",
    apiKey: "your-api-key",
    timeout: 30000
]

// ========== 前置/后置脚本：读取配置 ==========
var config = variables["config"]
var serverUrl = config.serverUrl
```

## 支持的脚本类型（五大类）

根据星桥平台实际使用场景，脚本分为以下五大类：

### 1. 数据模型 SQL ⭐

**用于**: 星桥 SQL 模板、数据查询、统计报表、数据模型定义

**典型场景**:
- 单表查询与多表关联
- 聚合统计（SUM/COUNT/AVG等）
- 时间范围查询（最近7天/30天等）
- 分页查询
- 复杂业务数据模型构建

**输入示例**:
> "表A有id、name、status字段，表B有a_id、value、create_time字段，需要关联查询最近7天的数据，按天统计value总和"

**输出**: 可直接复制到星桥 SQL 模板的 SQL 语句

---

### 2. API 前置 Groovy 脚本 ⭐

**用于**: 请求处理、认证设置、参数转换、数据预处理、SM3/SM4加解密验签

**典型场景**:
- OAuth2 认证头设置
- 请求参数转换（字段名映射）
- 请求体格式转换（XML↔JSON）
- 时间戳转换
- 分页参数处理
- SM3/SM4国密加解密
- 请求签名验证

**输入示例**:
> "调用第三方接口前需要设置Authorization头，从tokenStore获取token，clientId是10001，secret是abc123"

**输出**: 可直接复制到星桥 API 前置脚本的 Groovy 代码

---

### 3. API 后置 Groovy 脚本 ⭐

**用于**: 响应处理、数据转换、格式转换、错误包装

**典型场景**:
- 响应字段映射（第三方字段→星桥字段）
- 数据格式转换
- 错误处理包装
- 数组/List处理
- 嵌套数据扁平化
- **单条数据转数组格式**（重要：星桥标准格式要求data必须是数组）

**输入示例**:
> "第三方接口返回{status:0, data:{items:[{id:1, name:'test'}]}}, 需要转换成星桥格式{hasError:false, data:[{id:1, name:'test'}]}"

**输出**: 可直接复制到星桥 API 后置脚本的 Groovy 代码

**重要**: 星桥API标准输出格式使用 `data` 字段而非 `result` 字段，且 **`data` 必须是数组**（即使只有一条数据）：
```json
{
  "hasError": false,
  "data": [],
  "message": null,
  "tag": null,
  "totalCount": 0
}
```

---

### 4. API 接口合并 Groovy 脚本 ⭐

**用于**: 调用多个接口并合并数据、跨系统数据整合

**典型场景**:
- 多表关联查询替代（A接口取基础数据+B接口取详情数据）
- 跨系统数据整合
- 主从数据合并
- 批量设备数据查询

**输入示例**:
> "先调用接口A获取设备列表返回[{deviceId, deviceName}]，再调用接口B获取监测数据返回[{deviceId, sensorData}]，需要按deviceId合并成[{deviceId, deviceName, sensorData}]"

**输出**: 多接口调用 + 数据合并的 Groovy 代码

**推荐方案**: 
1. 在前置脚本中设置第一个设备的查询参数
2. 在后置脚本中循环查询剩余设备，合并结果
3. 使用 `return JsonUtils.serialize(mergedResponse)` 返回标准格式

---

### 5. 物联网设备对接 Groovy 脚本 ⭐

**用于**: 物联网平台设备数据接入、实时数据推送、海康设备对接

**典型场景**:
- 物联网1.0/2.0基础数据导入
- 实时监测数据推送
- 海康设备数据对接
- 第三方IoT平台对接

**输入示例**:
> "物联网2.0对接，第三方推送格式是{devCode:'123', reportTime:1764043804, data:[{name:'水位', value:10}]}, 需要转换成星桥格式{equipCode:'123', time:1764043804000, data:[{fieldCode:'waterlevel', value:10}]}"

**输出**: 完整的物联网数据转换 Groovy 脚本

**支持版本**:
- 物联网 1.0
- 物联网 2.0
- 海康设备
- 第三方自定义格式

---

## 输入规范

### SQL 生成

请提供：
- 表名和字段列表
- 字段类型（int/varchar/datetime等）
- 表之间的关系（一对一/一对多/多对多）
- 查询条件需求（时间范围、状态筛选等）
- 是否需要分页
- 是否需要分组统计
- 排序要求

### Groovy 脚本生成

请提供：
- **输入格式**：原始数据/请求的结构示例
- **输出格式**：目标数据结构示例
- **转换规则**：字段映射关系、计算逻辑
- **特殊处理**：时间格式转换、类型转换、空值处理
- **认证信息**（如需要）：token获取方式、密钥等

---

## 输出格式

我会输出可直接复制使用的代码：

```groovy
// 生成的 Groovy 脚本
// 可直接复制到星桥平台的前置/后置脚本编辑器

import com.egova.json.utils.JsonUtils
// ... 代码
```

或

```sql
-- 生成的 SQL
-- 可直接复制到星桥 SQL 模板

SELECT ...
```

---

## 内置变量与对象

在星桥脚本中可直接使用的内置变量：

| 变量 | 类型 | 适用脚本 | 说明 |
|------|------|---------|------|
| `request` | ScriptRequest | 前置脚本 | 请求对象，可获取/设置 URI、Header、Body |
| `response` | ScriptResponse | ❌ 已废弃 | **后置脚本中请勿使用**，请使用 `data` |
| `data` | String | 后置脚本 | **后置脚本专用**，直接是响应内容的 JSON 字符串 |
| `out` | PrintStream | 所有脚本 | 日志输出，使用 `out.println()` 输出调试信息 |
| `tokenStore` | TokenStore | 前置脚本 | 第三方 Token 管理，支持 OAuth2 自动刷新 |
| `sql` | SqlExecutor | 所有脚本 | SQL 查询执行器，用于脚本内查询数据库 |
| `variables` | Map | 所有脚本 | 全局变量存储，用于脚本间数据传递 |
| `context` | Map | 前置脚本 | 上下文对象，可获取配置的参数值 |

### ⚠️ 重要：前置脚本 vs 后置脚本变量区别

| 场景 | 获取响应数据的方式 |
|------|------------------|
| **前置脚本** | 无法获取响应，只能操作 `request` |
| **后置脚本** | 使用 `data` 变量，直接是 JSON 字符串 |

**常见错误**：在后置脚本中使用 `response.body` 或 `response.getBody()`

```groovy
// ❌ 错误：后置脚本中使用 response
response.body

// ✅ 正确：后置脚本中使用 data
data
```

### 获取 Spring Bean（高级用法）

```groovy
import com.flagwind.application.Application
import org.springframework.data.redis.core.StringRedisTemplate

// 从 Spring 容器获取 RedisTemplate
var redisTemplate = Application.resolve(StringRedisTemplate.class)
redisTemplate.opsForValue().set("key", "value", 25, TimeUnit.HOURS)
```

---

## 常用工具类参考

### JSON 操作
```groovy
import com.egova.json.utils.JsonUtils

def jsonStr = JsonUtils.serialize(obj)                    // 对象转JSON
def map = JsonUtils.deserialize(jsonStr, Map.class)      // JSON转Map
def list = JsonUtils.deserializeList(jsonStr, Map.class) // JSON转List
```

### HTTP 请求
```groovy
import com.egova.api.util.http.HttpUtils
import org.springframework.http.HttpHeaders

// GET 请求
def body = HttpUtils.get(url, String.class).getBody()

// POST Form
def resp = HttpUtils.postForm(url, params, String.class, headers -> {})

// POST JSON
def resp = HttpUtils.postJson(url, jsonStr, String.class)
```

### 时间戳转换
```groovy
import java.time.LocalDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter

// 字符串时间 → 13位毫秒时间戳
def toTimestamp13 = { String dtStr ->
  def formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")
  def ldt = LocalDateTime.parse(dtStr, formatter)
  return ldt.atZone(ZoneId.of("Asia/Shanghai")).toInstant().toEpochMilli()
}
```

### Token 认证
```groovy
// OAuth2 Token 获取
var tokenType = 'default'
var tokenParams = [
  'url': 'http://xxx/oauth/extras/token',
  'clientId': 'xxx',
  'clientSecret': 'xxx'
]
var token = tokenStore.load(tokenType, tokenParams)
request.addHeader('Authorization', 'Bearer ' + token.value)
```

### SQL 查询（脚本内）
```groovy
var queryTemplate = sql.of('dataSourceName')
var list = queryTemplate.forList(sql, [] as Object[])
var list = queryTemplate.forList(sql, limit, [] as Object[])
```

### 加解密工具
```groovy
// Base64
com.egova.api.util.Base64Utils.encode('data')
com.egova.api.util.Base64Utils.decode('encoded')

// SM3/SM4国密
import com.egova.dex.util.Sm3Utils
import com.egova.dex.util.Sm4Utils
import java.util.Base64

def sm3Hash = Sm3Utils.encode('data')
def sm4Encrypted = Sm4Utils.encrypt(dataBytes, keyBytes)
def sm4Decrypted = Sm4Utils.decrypt(encryptedBytes, keyBytes)
```

### ID 生成
```groovy
import com.egova.dex.util.SnowflakeIdUtils
def id = SnowflakeIdUtils.nextStringId()
```

### 字典工具
```groovy
// 获取单个字典项
var value = com.egova.api.util.dict.DictUtils.get('dictCode', 'itemCode')

// 获取整个字典
var dicMap = com.egova.api.util.dict.DictUtils.getAll('dictCode')
```

### 字符串/集合工具
```groovy
import org.apache.commons.lang3.StringUtils
import org.springframework.util.CollectionUtils

StringUtils.isEmpty(str)
StringUtils.isNotEmpty(str)
CollectionUtils.isEmpty(list)
CollectionUtils.isNotEmpty(list)
```

---

## ⚠️ 重要注意事项

### 1. 标准响应格式

星桥API的标准输出格式统一为：
```json
{
  "hasError": false,
  "data": [],
  "message": null,
  "tag": null,
  "totalCount": 0
}
```

**重要注意**：
- 使用 `data` 字段而非 `result` 字段
- **`data` 必须是数组**（List），即使只有一条数据也要封装成 `[{...}]` 格式
- ❌ 错误：`data: {id: 1, name: "test"}` （单条对象）
- ✅ 正确：`data: [{id: 1, name: "test"}]` （单条对象的数组）

**常见问题**：第三方接口返回单条数据时，容易直接返回对象而非数组，导致后续流程（如数据写入数据库）无法正常获取数据。

### 2. 脚本限制

**前置脚本限制**（重要）：
- ❌ 无法使用 `response.setBody()` 修改响应
- ❌ 无法直接返回数据跳过后续HTTP调用
- ✅ 只能修改请求参数 (`request.setBody()`)

**后置脚本限制**（重要）：
- ❌ 无法使用 `response.setBody()` 修改响应（某些版本）
- ❌ 无法使用 `context.put()` 存储上下文
- ❌ 无法使用 `sqlTemplate.execute()` 直接执行INSERT（方法不存在）
- ✅ 只能使用 `return` 返回数据

### 3. 常见错误与解决方案

#### 错误 1：`No signature of method: xxx.getBody()`

**原因**：Groovy 中访问对象属性使用 `.属性名` 而非 `.get方法名()`

**示例**：
```groovy
// ❌ 错误写法
response.getBody()

// ✅ 正确写法（前置脚本）
request.body
```

**其他常见属性访问**：
| 对象 | 错误写法 | 正确写法 |
|------|---------|---------|
| request | `request.getBody()` | `request.body` |
| request | `request.getUri()` | `request.uri` |

#### 错误 2：`No such property: body for class: java.lang.String`

**原因**：后置脚本中错误地使用了 `response.body`，实际上后置脚本应该直接使用 `data` 变量

**示例**：
```groovy
// ❌ 错误写法（后置脚本）
def responseMap = JsonUtils.deserialize(response.body, Map.class)

// ✅ 正确写法（后置脚本）
def responseMap = JsonUtils.deserialize(data, Map.class)
```

**前置脚本 vs 后置脚本对比**：

```groovy
// ========== 前置脚本 ==========
// 获取请求体
import com.egova.json.utils.JsonUtils
def body = request.body  // 获取请求体字符串
def bodyMap = JsonUtils.deserialize(body, Map.class)

// ========== 后置脚本 ==========
// 获取响应体
import com.egova.json.utils.JsonUtils
def responseMap = JsonUtils.deserialize(data, Map.class)  // data 直接是响应 JSON 字符串
```

#### 错误 3：`Unrecognized token 'xxx': was expecting (JSON String...)`

**原因**：尝试将一个非 JSON 字符串解析为 JSON，常见于变量名错误导致传入了变量名本身而非变量值

**示例**：
```groovy
// ❌ 错误：传入字符串 "response" 而非变量 response 的值
JsonUtils.deserialize("response", Map.class)

// ✅ 正确：传入变量 data 的值
JsonUtils.deserialize(data, Map.class)
```

### 5. 推荐方案

**多设备批量查询方案**：
1. 在前置脚本中设置第一个设备的查询参数
2. 在后置脚本中循环查询剩余设备，合并结果
3. 使用 `return JsonUtils.serialize(mergedResponse)` 返回标准格式

**数据库写入方案**：
- ❌ 不推荐在脚本中直接写入数据库（方法受限）
- ✅ 推荐：脚本只返回数据，通过星桥任务功能写入数据库

### 6. 日志输出

使用 `out.println("日志内容")` 输出调试信息，可在星桥日志中查看。

### 7. 时间处理

```groovy
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit
import java.time.Instant

// 获取当前时间并截断到分钟
def now = LocalDateTime.now()
def endTime = now.truncatedTo(ChronoUnit.MINUTES)
def startTime = endTime.minusMinutes(10)

// 格式化时间
def formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")
def timeStr = startTime.format(formatter)

// 生成13位时间戳
def timestamp13 = Instant.now().toEpochMilli()

// 生成16位随机数
def nonce = UUID.randomUUID().toString().replaceAll("-", "").substring(0, 16)
```

### 8. 使用 JdbcTemplate（高级数据库操作）

```groovy
var queryTemplate = sql.of(variables['env'].dbName)
var jdbcTemplate = queryTemplate.session.jdbcTemplate

// 执行插入
var sql = "INSERT INTO table_name(col1, col2, create_time) VALUES (?, ?, ?)"
jdbcTemplate.update(sql, value1, value2, '2024-01-01 12:00:00')
```

### 9. 使用 Redis

```groovy
import org.springframework.data.redis.core.StringRedisTemplate
import com.flagwind.application.Application
import java.util.concurrent.TimeUnit

var redisTemplate = Application.resolve(StringRedisTemplate.class)
redisTemplate.opsForValue().set("key", "value", 25, TimeUnit.HOURS)
var value = redisTemplate.opsForValue().get("key")
```

---

## 示例请求

### 示例 1：生成 SQL
> "帮我生成一个SQL，查询用户表和订单表，用户表有user_id、user_name，订单表有order_id、user_id、amount、create_time，需要查询最近30天每个用户的订单总金额"

### 示例 2：生成前置脚本
> "前置脚本需要从请求体中提取data数组，给每个元素添加一个timestamp字段，值为当前时间戳13位毫秒，然后再发送给下游接口"

### 示例 3：生成后置脚本
> "第三方接口返回{status:0, data:{items:[{id:1, name:'test'}]}}, 需要转换成星桥标准格式{hasError:false, data:[{id:1, name:'test'}]}"

### 示例 4：生成接口合并脚本
> "先调用接口A获取项目列表返回[{projectId, projectName}]，再调用接口B获取进度列表返回[{projectId, progress}]，合并成[{projectId, projectName, progress}]"

### 示例 5：物联网对接
> "物联网2.0实时数据对接，原始格式{deviceCode:'D001', data:{temperature:25, humidity:60}}，需要转换成{equipCode:'D001', data:[{fieldCode:'temp', value:25}, {fieldCode:'humidity', value:60}]}"

### 示例 6：SM3/SM4加解密
> "前置脚本需要对接收到的请求进行SM4解密，secret是'abc123'，解密后验证SM3签名，签名通过后才转发给下游接口"

---

## 参考文档

### 核心文档
- **知识图谱**: [references/knowledge-graph.md](references/knowledge-graph.md) - 星桥完整知识体系（产品架构、核心概念、认证机制、脚本类型、问题诊断等）
- **快速参考**: [references/quick-reference.md](references/quick-reference.md) - 常用代码片段速查手册

### API 参考文档
- **HTTP 请求**: [references/http-api.md](references/http-api.md) - `HttpUtils` 完整用法（GET/POST/PUT/DELETE）
- **数据库操作**: [references/database-api.md](references/database-api.md) - `sql.of()` 和 `JdbcTemplate` 操作
- **Redis 操作**: [references/redis-api.md](references/redis-api.md) - `StringRedisTemplate` 读写、过期设置
- **Spring 对象**: [references/spring-api.md](references/spring-api.md) - `Application.resolve()` 获取 Bean
- **上下文变量**: [references/context-api.md](references/context-api.md) - 请求参数获取、响应体操作
- **加密工具**: [references/crypto-utils.md](references/crypto-utils.md) - MD5/Base64/AES/RSA/国密等
- **前置/后置脚本 API**: [references/pre-script-api.md](references/pre-script-api.md) - 通用 API 参考
- **Hutool 使用**: [references/hutool-usage.md](references/hutool-usage.md) - Hutool 工具类替代方案
- **业务案例**: [references/business-cases.md](references/business-cases.md) - 典型场景案例

### 详细文档
- **脚本示例库**: [references/script-examples.md](references/script-examples.md) - 实际项目脚本示例
- **物联网对接指南**: [references/iot-integration-guide.md](references/iot-integration-guide.md) - 物联网对接完整方案
- **脚本模板**: [references/script-templates.md](references/script-templates.md) - 常用脚本模板
- **接口规范**: [references/api-spec.md](references/api-spec.md) - API接口规范
- **错误码手册**: [references/error-codes.md](references/error-codes.md) - 常见错误及解决方案
- **对接方案完整版**: [references/对接方案完整版.md](references/对接方案完整版.md) - 星桥数据接入接口对接完整方案
- **Wiki链接汇总**: [references/wiki-links.md](references/wiki-links.md) - 星桥大数据2.0相关Wiki页面链接

## 相关链接

- **政通官网**: https://www.egova.com.cn
- **星桥平台**: 内部部署，请联系管理员获取访问地址
- **项目管理平台**: https://faq.egova.com.cn:7787
  - **API Key**: `a687d1fc20e3953a9a2796e0c2b7b54c0a754283` (Header: X-Redmine-API-Key)
- **Wiki首页**: https://faq.egova.com.cn:7787/projects/redmine/wiki/基础平台-星桥大数据20

---

## 实用脚本模板

### 模板1：多设备批量查询（后置脚本）

**场景**：一次查询多个设备，合并结果返回

```groovy
import com.egova.json.utils.JsonUtils
import com.egova.api.util.http.HttpUtils
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit

// 配置设备列表和API地址
def DEVICE_CODES = ['12000001', '12000002', '12000003', '12000004', '12000005']
def API_URL = 'http://host:port/api/xxx/page'

// 计算时间范围（最近10分钟）
def now = LocalDateTime.now()
def endTime = now.truncatedTo(ChronoUnit.MINUTES)
def startTime = endTime.minusMinutes(10)
def formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")

// 查询所有设备
def allResults = []
DEVICE_CODES.each { deviceCode ->
    try {
        def requestBody = [
            condition: [
                startTime: startTime.format(formatter),
                endTime: endTime.format(formatter),
                deviceCode: deviceCode
            ],
            paging: [pageIndex: 1, pageSize: 1000]
        ]
        
        def resp = HttpUtils.postJson(API_URL, JsonUtils.serialize(requestBody), String.class)
        def respMap = JsonUtils.deserialize(resp.getBody(), Map.class)
        
        if (!respMap.hasError && respMap.result) {
            allResults.addAll(respMap.result)
        }
    } catch (Exception e) {
        out.println("设备${deviceCode}查询失败: ${e.message}")
    }
}

// 返回标准格式
return JsonUtils.serialize([
    hasError: false,
    data: allResults,
    message: null,
    tag: null,
    totalCount: allResults.size()
])
```

### 模板2：前置脚本设置动态参数

**场景**：动态计算时间参数并设置到请求体

```groovy
import com.egova.json.utils.JsonUtils
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit

// 计算时间
def now = LocalDateTime.now()
def endTime = now.truncatedTo(ChronoUnit.MINUTES)
def startTime = endTime.minusMinutes(10)
def formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")

// 构建请求体
def requestBody = [
    condition: [
        startTime: startTime.format(formatter),
        endTime: endTime.format(formatter),
        deviceCode: '12000001'
    ],
    paging: [pageIndex: 1, pageSize: 1000]
]

// 设置到请求
request.setBody(JsonUtils.serialize(requestBody))
```

### 模板3：后置脚本数据转换

**场景**：转换第三方接口返回的字段名

```groovy
import com.egova.json.utils.JsonUtils

// 获取原始响应
def responseBody = response.getBody()
def responseMap = JsonUtils.deserialize(responseBody, Map.class)

// 数据转换
if (!responseMap.hasError && responseMap.result) {
    def convertedData = responseMap.result.collect { item ->
        [
            id: item.id,
            deviceCode: item.deviceCode,
            longitude: item.longitude,
            latitude: item.latitude,
            reportTime: item.reportTime,
            createTime: item.createTime
        ]
    }
    
    // 返回标准格式
    return JsonUtils.serialize([
        hasError: false,
        data: convertedData,
        message: null,
        tag: null,
        totalCount:
