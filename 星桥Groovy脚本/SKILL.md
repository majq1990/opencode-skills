---
name: egova-config-dex-script
description: 星桥数据接入平台综合对接工具（星桥对接 / 星桥Groovy脚本）。覆盖五大场景：1）数据模型SQL构造（需提供表结构）；2）API前置Groovy脚本（认证/参数转换/SM3-SM4验签，需提供三方接口示例）；3）API后置Groovy脚本（返回值改写/字段映射/数据扩展）；4）多接口合并脚本；5）物联网特殊场景（设备对接/实时数据/海康/MQTT）。同时提供脚本规范、最佳实践、内部 API 索引与 7 个真实项目对接案例。触发词：星桥 / 星桥对接 / 星桥脚本 / 前置脚本 / 后置脚本 / 鉴权脚本 / SQL模板 / 设备对接。
version: 1.2.0
compatibility: workbuddy
metadata:
  category: global
  tags: xingqiao,groovy,sql,device-integration,script,api-connector
---

# 星桥对接 · 平台内 SQL / Groovy 脚本生成规范
# 用 md 文档记录对应脚本代码，不要凭空生成整段 groovy / java；先要齐前置输入再产出

## 使用方式（喂需求 → 出脚本）

**直接描述对接需求，本 skill 产出可直接粘进星桥平台的 SQL / Groovy 脚本。** 每类场景都需要先给齐前置输入才能生成：

| 场景 | 必需的前置输入 | 产出 |
|------|--------------|------|
| ① 数据模型 SQL | 表结构（字段名/类型）+ 查询/统计口径 | 可粘进星桥 SQL 模板的语句 |
| ② API 前置脚本 | 三方接口调用示例（URL/Header/Body/认证方式） | 鉴权 + 前置 Groovy 脚本 |
| ③ API 后置脚本 | 三方返回样例 + 目标字段结构 | 后置 Groovy 脚本 |
| ④ 接口合并 | 需合并的多个接口调用示例 | 编排合并脚本 |
| ⑤ 物联网特殊场景 | 设备协议/实时数据格式（海康/MQTT/651 等） | 设备对接脚本，优先套 `references/cases/` 同场景 |

> **钉钉/WorkBuddy 内使用**：超长代码（>500 字符）不要直接粘（会被拆块显示混乱），改为存文件给下载链接，附「下载→复制到星桥前置/后置脚本→配置参数」三步说明。

## 脚本体系概览

星桥平台提供三类 Groovy 脚本，在接口请求的不同阶段执行：

```
请求进入 → [鉴权脚本(非必须)] → [前置脚本] → 实际接口调用 → [后置脚本] → 返回响应
```

| 脚本类型 | 执行时机 | 核心职责 |
|---------|---------|---------|
| **鉴权脚本** | 最先执行 | 存储和管理配置项（服务地址、密钥、Token 等） |
| **前置脚本** | 接口调用前 | 调整请求参数、执行前置逻辑（如签名计算） |
| **后置脚本** | 接口调用后 | 修改返回值、数据扩展、格式转换 |

---

## 最佳实践

### 1. 配置项统一管理

所有配置项（地址、密钥、常量等）**必须定义在鉴权脚本中统一管理**。使用 `variables` 下标访问方式进行跨脚本传递。

```groovy
// ========== 鉴权脚本：存储配置 ==========
variables["config"] = [
    serverUrl: "https://api.example.com",
    timeout: 30000
]

// ========== 前置/后置脚本：读取配置 ==========
var config = variables["config"]
```

#### 获取高级 Spring 对象

若内置变量（如 `sql`）无法满足需求，可从 Spring 容器获取原生对象（如 `RedisTemplate`、`JdbcTemplate`）。

```groovy
import com.flagwind.application.Application
import org.springframework.data.redis.core.StringRedisTemplate

var redis = Application.resolve(StringRedisTemplate.class)
```

### 2. 外部 JAR 包扩展

若需调用第三方私有库（如 UKey 驱动、特定 SDK），应将 JAR 包放入星桥运行目录下的 `lib/` 文件夹中，重启星桥后即可在脚本中通过 `import` 调用。

### 3. API 调用替代方案

星桥沙箱环境可能限制部分核心 JDK 类库。

| 受限操作 | 推荐替代方案 |
|---------|-------------|
| `java.net.URLEncoder` | `org.springframework.web.util.UriUtils` |
| `java.util.Base64` | `java.util.Base64` (原生) 或 `Hutool Base64` |
| 直接拼接 SQL | 参数化查询 或 `JdbcTemplate` |
| 复杂 HTTP 调用 | `HttpUtils.postJson` 或 `Hutool HttpRequest` |

### 4. 变量声明规范

统一使用 `var` 替代 `def` 进行局部变量声明，保持代码整洁且符合 Groovy 3+ 风格。

```groovy
// ❌ 受限：直接使用 JDK 方法（可能被沙箱拦截）
// import java.net.HttpURLConnection
// import java.security.MessageDigest

// ✅ 使用 Hutool 替代
// HTTP 请求 → 使用平台内置 API（见 references/http-api.md）
// 加密签名 → 使用 Hutool 的 SecureUtil
// JSON 处理 → 使用 Hutool 的 JSONUtil
// 日期处理 → 使用 Hutool 的 DateUtil
```

### 5. 脚本结构规范

每个脚本应遵循以下结构：

```groovy
// ========== 1. 配置区（仅鉴权脚本） ==========
// 所有配置项集中定义在此

// ========== 2. 工具方法区 ==========
// 复用的辅助方法定义在此

// ========== 3. 主逻辑区 ==========
// 脚本的核心业务逻辑
```

### 6. 错误处理

```groovy
// ✅ 脚本中必须有适当的错误处理
try {
    // 业务逻辑
} catch (Exception e) {
    // 记录错误信息，返回有意义的错误提示
}
```

---

## 可用 API 索引

以下列出星桥脚本中可调用的内部 API 分类。**每个 API 的详细说明、参数和用例请查阅 `references/` 目录下对应的资源文档**。

### Spring 对象获取
- 使用 `Application.resolve` 从 Spring 容器中直接获取 Bean（如 RedisTemplate, JdbcTemplate）
- 详见：[`references/spring-api.md`](references/spring-api.md)

### Redis 操作
- 通过 `Application.resolve(StringRedisTemplate.class)` 获取 Redis 模板，进行读写、过期设置、原子操作
- 详见：[`references/redis-api.md`](references/redis-api.md)

### 数据库操作
- 标准 `sql.of` 及高级 `JdbcTemplate` 复杂更新/事务
- 详见：[`references/database-api.md`](references/database-api.md)

### HTTP 请求
- `HttpUtils`、`Hutool HttpRequest` 及 `UriUtils` 替代
- 详见：[`references/http-api.md`](references/http-api.md)

### 上下文变量
- 请求参数获取与修改、响应体操作、脚本间数据传递
- 详见：[`references/context-api.md`](references/context-api.md)

### 加密工具类
- JSON/XML 处理、编码加密（MD5/Base64/AES/DES/RSA/国密）、字典/GIS/Kafka 工具
- 详见：[`references/crypto-utils.md`](references/crypto-utils.md)

### 前置/后置脚本 API
- 前置/后置脚本通用 API 参考（基于 com.egova.* 工具类）
- 详见：[`references/pre-script-api.md`](references/pre-script-api.md)

### 业务案例
- 上报字段调整、城管认证、第三方 Token、接口签名、WebService 等典型场景
- 详见：[`references/business-cases.md`](references/business-cases.md)

### 真实项目对接案例（设备对接）
`references/cases/` 收录了 7 个真实交付项目的完整对接脚本与需求文档，编写同类对接前优先参考同场景案例：

| 案例 | 场景 | 关键文件 |
|------|------|---------|
| 仙桃设备对接 | 设备基础数据 + 实时数据对接 | `cases/仙桃设备对接/仙桃设备对接.md`、`仙桃对接脚本优化.md` |
| 内蒙古 iotpro 数据同步 | iotpro 平台设备基础数据前置脚本 | `cases/内蒙古iotpro数据同步/前置脚本-设备基础数据.groovy`、`需求.md` |
| 管网泄漏灾害预警平台 | 设备基础+实时报警/浓度+统一推送（含完整 groovy 套件） | `cases/管网泄漏灾害预警平台对接脚本/前置脚本-统一推送.groovy`、`使用说明.md` |
| 甘肃对接 | 651 协议数据对接 | `cases/甘肃对接/651协议数据对接.md`、`接口文档说明(1).doc` |
| 锦州燃气对接 | 燃气基础数据 + 实时数据 | `cases/锦州燃气对接/对接燃气基础数据和实时数据.md` |
| 方城 MQTT 设备 | MQTT 设备数据对接 | `cases/方城对接mqtt设备数据/方城设备对接.md` |
| 宝丰对接 | 设备对接（含 PDF 方案） | `cases/宝丰对接/宝丰设备对接.pdf` |

---

## 内置变量清单

| 变量名 | 类型 | 可用阶段 | 说明 |
|-------|------|---------|------|
| `request` | ScriptRequest | 鉴权/前置/后置 | 当前请求对象，包含 URI、Path、Header、Query、Body |
| `out` | 日志输出对象 | 鉴权/前置/后置 | 使用 `out.println()` 输出日志（所有阶段可用） |
| `tokenStore` | TokenStore | 鉴权/前置/后置 | 三方系统 Token 存储，用于管理第三方接口 Token |
| `sql` | SqlExecutor | 鉴权/前置/后置 | SQL 查询执行器，用于数据库操作 |
| `variables` | Map<String, Object> | 鉴权/前置/后置 | 全局变量存储，脚本间数据传递 |

---

## 脚本类型详细说明

### 鉴权脚本

**职责**：管理配置项和鉴权信息

典型用途：
- 存储服务地址、AppKey、AppSecret
- Token 的获取和缓存
- 签名算法的实现

### 前置脚本

**职责**：在实际接口调用前处理请求

典型用途：
- 根据配置动态修改请求参数
- 添加鉴权 Header（如签名、时间戳）
- 参数校验和转换
- 调用其他接口获取前置数据

### 后置脚本

**职责**：对接口返回值进行处理

典型用途：
- 数据格式转换（如字段重命名、结构调整）
- 数据扩展（如根据 ID 查询补充详情）
- 错误码转换
- 结果过滤和聚合

---

## 禁止行为

- ❌ 禁止在前置/后置脚本中硬编码配置项（统一放鉴权脚本）
- ❌ 禁止直接使用被沙箱限制的 JDK 方法（使用 Hutool 替代）
- ❌ 禁止在脚本中写死环境相关的 URL（通过配置项管理）
- ❌ 禁止忽略异常不处理
