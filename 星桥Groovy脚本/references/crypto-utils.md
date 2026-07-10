# 加密工具类与常用工具

> 星桥脚本中可用的加密解密、编码、JSON/XML 处理等工具类说明

## JSON/XML 工具

### JsonUtils - JSON 处理

```groovy
import com.egova.json.utils.JsonUtils

// JSON 序列化
var str = com.egova.json.utils.JsonUtils.serialize(map)

// JSON 反序列化
var map = com.egova.json.utils.JsonUtils.deserialize(data, Map.class)

// JSON 反序列化（多条）
var list = com.egova.json.utils.JsonUtils.deserializeList(data, Map.class)
```

### XmlUtils - XML 处理

```groovy
import com.egova.api.util.XmlUtils

// XML 转 JSON
var jsonStr = com.egova.api.util.XmlUtils.toJson(xmlStr)

// JSON 转 XML
var xmlStr = com.egova.api.util.XmlUtils.toXml(jsonStr)
```

---

## 编码工具

### Base64 编码/解码

```groovy
// Base64 加密
var encode = com.egova.api.util.Base64Utils.encode('admin:12345')

// Base64 解密
var decode = com.egova.api.util.Base64Utils.decode('YWRtaW46MTIzNDU2')
```

### Map 字段重命名

```groovy
// 修改 map 中 key 名称
map = com.egova.api.util.MapUtils.rename(map, ['NAME': 'name', 'AGE': 'age', 'SEX': 'sex'])
```

---

## 哈希工具

### MD5

```groovy
// MD5 加密（长度32位小写字符串）
var encode = com.egova.api.util.Md5Utils.encode('admin:123456')
```

### SHA1/SHA256

```groovy
// SHA1 加密
var str = org.apache.commons.codec.digest.DigestUtils.sha1Hex('字符串')

// SHA256 加密
var str = org.apache.commons.codec.digest.DigestUtils.sha256Hex('字符串')
```

### 国密 SM3

```groovy
import com.egova.dex.util.Sm3Utils
import com.egova.dex.util.HexUtils

// 对于任意长度的字符串，都返回256bit
var res = Sm3Utils.encode('星桥')
out.println(Arrays.toString(res))

// 结果转hex字符串
out.println(HexUtils.encodeToString(res))
```

---

## 对称加密

### AES 加密/解密

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

### DES 加密/解密

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

### 3DES 加密/解密

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

### 国密 SM4 加密/解密

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

---

## 非对称加密

### Java 原生 Base64 (java.util.Base64)

```groovy
import java.util.Base64;
import java.nio.charset.StandardCharsets;

// 编码
var text = Base64.getEncoder().encodeToString(rawText.getBytes(StandardCharsets.UTF_8));

// 解码
var decoded = new String(Base64.getDecoder().decode(base64Text), StandardCharsets.UTF_8);
```

---

## 哈希工具

### SM3 截取获取 IV

某些加密算法（如 SM4）需要从 SM3 的哈希结果中截取部分字节作为 IV。

```groovy
import com.egova.dex.util.Sm3Utils;

var sm3 = Sm3Utils.encode("ZGCG@123".getBytes());
// 截取 16 到 32 字节作为 IV
byte[] iv = Arrays.copyOfRange(sm3, 16, 32);
```

---

## 非对称加密

### RSA 公钥加密 (Hutool)

```groovy
import cn.hutool.crypto.asymmetric.RSA;
import cn.hutool.crypto.asymmetric.KeyType;
import java.util.Base64;

// 公钥加密示例
var rsa = new RSA(null, publicKeyString);
byte[] encrypted = rsa.encrypt("password".getBytes(), KeyType.PublicKey);
var base64Password = Base64.getEncoder().encodeToString(encrypted);
```

---

## 字典工具

```groovy
// 获取字典
var value = com.egova.api.util.dict.DictUtils.get('字典类型', '字典项名称')

// 获取字典（全部）
var map = com.egova.api.util.dict.DictUtils.getAll('字典类型')
```

---

## GIS 坐标转换

```groovy
// WGS84转当地平面
var xy = com.egova.api.util.gis.GisUtils.convert('A', '-82415.3914051056#2969.1174163818#0.00541075559597633#1.00000425185696#0#120', 114.215982, 30.461412)
var x = xy[0]
var y = xy[1]
```

---

## 日期时间

```groovy
import com.flagwind.commons.Monment

// 获取5分钟之前的时间
def date = Monment.now().addMinutes(-5)
def str = date.toString('yyyy-MM-dd HH:mm:ss')
```

---

## 注意事项

1. **国密支持**：国密 SM3/SM4 需要平台额外配置，确认环境是否支持
2. **密钥管理**：密钥应存储在 `variables` 或配置中，不要硬编码
3. **坐标转换**：不同地图平台使用不同坐标系，根据目标平台选择正确的转换方法
4. **字典缓存**：`DictUtils` 可能有缓存机制，字典变更后可能需要刷新
5. **日志输出**：使用 `out.println()` 输出处理过程信息
6. **错误处理**：处理异常时使用 `return 'api_stop'` 终止执行
