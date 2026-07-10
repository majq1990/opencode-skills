# Hutool 工具类使用指南

> 星桥脚本中替代受限 JDK 方法的补充工具类说明

## 说明

部分 JDK 方法在脚本沙箱中不可用。星桥平台主要使用 **`com.egova.*`** 包下的工具类，这些是基于 Hutool 或其他框架的封装。

> **重要**：优先使用 `com.egova.*` 包下的工具类（详见 `pre-script-api.md`），本文档列出的 Hutool 工具类仅作为补充选择。

---

## JSON 处理

> 推荐：优先使用 `com.egova.json.utils.JsonUtils`

```groovy
import com.egova.json.utils.JsonUtils

// JSON 序列化
var str = JsonUtils.serialize(map)

// JSON 反序列化
var map = JsonUtils.deserialize(data, Map.class)

// JSON 反序列化（多条）
var list = JsonUtils.deserializeList(data, Map.class)
```

**Hutool 替代（补充）**：

```groovy
import cn.hutool.json.JSONUtil

// Map 转 JSON
def obj = [name: "张三", age: 30]
def jsonStr = JSONUtil.toJsonStr(obj)

// JSON 字符串转 Map
def map = JSONUtil.toBean(jsonStr, Map.class)
```

---

## 加密签名

> 推荐：优先使用 `com.egova.api.util.*` 包下的工具类

```groovy
// MD5
var encode = com.egova.api.util.Md5Utils.encode('admin:123456')

// AES
var str = com.egova.api.util.AESUtils.encrypt('sSrc')

// DES
var str = com.egova.api.util.DESUtils.encrypt('data', 'key')

// 3DES
var str = com.egova.api.util.TripleDesUtils.encodeByECB('data', 'key')

// RSA
var str = com.egova.api.util.RSAUtils.encrypt('s', 'publicKey')
```

**Hutool 替代（补充）**：

```groovy
import cn.hutool.crypto.SecureUtil

// MD5
def md5 = SecureUtil.md5("password")

// AES 加密
def key = "1234567890123456"  // 16 位密钥
def aes = SecureUtil.aes(key.bytes)
def encrypted = aes.encryptBase64("Hello")
def decrypted = aes.decryptStr(encrypted)
```

---

## 日期处理

> 推荐：优先使用 `com.flagwind.commons.Monment`

```groovy
import com.flagwind.commons.Monment

// 获取5分钟之前的时间
def date = Monment.now().addMinutes(-5)
def str = date.toString('yyyy-MM-dd HH:mm:ss')
```

**Hutool 替代（补充）**：

```groovy
import cn.hutool.core.date.DateUtil

// 当前时间
def now = DateUtil.date()

// 格式化日期
def formatted = DateUtil.format(now, "yyyy-MM-dd HH:mm:ss")

// 日期偏移
def fiveMinutesAgo = DateUtil.offsetMinute(now, -5)
```

---

## 字符串工具（StrUtil）

```groovy
import cn.hutool.core.util.StrUtil

// 判空
if (StrUtil.isEmpty(str)) { ... }
if (StrUtil.isNotBlank(str)) { ... }

// 去除前后空格
def trimmed = StrUtil.trim(str)

// 分割字符串
def parts = StrUtil.split("a,b,c", ",")

// 字符串拼接
def joined = StrUtil.join(",", ["a", "b", "c"])

// 生成随机字符串
def random = StrUtil.randomString(32)  // 32 位随机字符串
```

---

## 编码工具

> 推荐：优先使用 `com.egova.api.util.*` 包下的工具类

```groovy
// Base64 加密
var encode = com.egova.api.util.Base64Utils.encode('admin:12345')

// Base64 解密
var decode = com.egova.api.util.Base64Utils.decode('YWRtaW46MTIzNDU2')
```

**Hutool 替代（补充）**：

```groovy
import cn.hutool.core.codec.Base64
import cn.hutool.core.net.URLUtil

// Base64 编码
def encoded = Base64.encode("Hello")

// URL 编码
def encoded = URLUtil.encode("测试")
```

---

## XML 处理（XMLUtil）

```groovy
import cn.hutool.core.xml.XMLUtil

// XML 字符串转对象
def xmlStr = '<root><name>张三</name></root>'
def obj = XMLUtil.toObj(xmlStr, Map.class)

// 对象转 XML
def xml = XMLUtil.toObj(obj)

// JSON 与 XML 互转
def json = JSONUtil.toBean(jsonStr, Map.class)
def xml = XMLUtil.toXml(json)
```

---

## 星桥平台工具类（com.egova.*）

> 优先使用以下工具类

### DictUtils - 数据字典

```groovy
import com.egova.api.util.dict.DictUtils

// 获取字典
var value = DictUtils.get('字典类型', '字典项名称')

// 获取字典（全部）
var map = DictUtils.getAll('字典类型')
```

### MapUtils - Map 操作

```groovy
// 修改 map 中 key 名称
map = com.egova.api.util.MapUtils.rename(map, ['NAME': 'name', 'AGE': 'age', 'SEX': 'sex'])
```

### GisUtils - 坐标转换

```groovy
// WGS84转当地平面
var xy = com.egova.api.util.gis.GisUtils.convert('A', '-82415.3914051056#2969.1174163818#0.00541075559597633#1.00000425185696#0#120', 114.215982, 30.461412)
var x = xy[0]
var y = xy[1]
```

---

## 受限 JDK 方法 → 工具类替代对照表

| 受限的 JDK 方法 | com.egova.* 替代 | Hutool 补充 |
|----------------|-----------------|-------------|
| `java.security.MessageDigest` | `Md5Utils.encode()` | `SecureUtil.md5()` |
| `javax.crypto.Cipher` | `AESUtils.encrypt()` | `SecureUtil.aes()` |
| `java.util.Base64` | `Base64Utils.encode()` | `Base64.encode()` |
| `java.net.URLEncoder` | `UriUtils.encode()` | `URLUtil.encode()` |
| `java.text.SimpleDateFormat` | `Monment.format()` | `DateUtil.format()` |
| 直接 JSON 解析 | `JsonUtils.deserialize()` | `JSONUtil.toBean()` |
| 直接 XML 解析 | `XmlUtils.toJson()` | `XMLUtil.toObj()` |

---

## 注意事项

1. **工具类选择**：优先使用 `com.egova.*` 包下的工具类，Hutool 仅作为补充
2. **加密密钥**：密钥应存储在 `variables` 中，不要硬编码
3. **日期格式**：常用格式为 `yyyy-MM-dd HH:mm:ss`
4. **参考文档**：完整 API 参考 请查阅 `pre-script-api.md`
