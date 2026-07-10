# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**egova-config-dex-script** 是星桥（Starbridge）平台 Groovy 脚本开发的文档/技能库。此项目不包含可编译的源代码，而是作为编写 Groovy 脚本的规范、API 参考和最佳实践指南。

**重要原则**：通过 Markdown 文档记录脚本逻辑和规范，**不要直接生成 .groovy 或 .java 代码文件**。

---

## 项目结构

```
.claude/skills/starbridge-script/
├── SKILL.md              # 主技能定义和脚本开发规范
└── references/           # API 参考文档
    ├── context-api.md     # 请求/响应上下文操作
    ├── http-api.md       # HTTP 请求 API
    ├── database-api.md   # 数据库操作 API
    ├── redis-api.md      # Redis 操作 API
    ├── spring-api.md     # Spring Bean 获取 API
    ├── crypto-utils.md   # 加密工具类
    ├── hutool-usage.md   # Hutool 工具类使用
    └── business-cases.md # 业务场景案例
```

---

## 核心开发规范

### 1. 配置项统一管理

所有配置项（地址、密钥、常量等）**必须定义在鉴权脚本中**，通过 `variables` 全局变量在脚本间传递。

```groovy
// ✅ 鉴权脚本：使用下标访问设置变量
variables["serverUrl"] = "https://api.example.com"

// ✅ 前置/后置脚本：使用 var 声明
var url = variables["serverUrl"]
```

**禁止**在前置/后置脚本中硬编码配置项。**统一使用 `var` 替代 `def`**。

### 2. 沙箱环境与 API 替代方案

星桥脚本运行在沙箱中，部分 JDK 方法（如 `URLEncoder`）被限制。**必须使用 `com.egova.*` 工具类、Hutool 或 Spring 提供的替代方案**：

| 受限操作 | 推荐替代方案 |
|---------|-------------|
| `java.net.URLEncoder` | `org.springframework.web.util.UriUtils` |
| `java.security.MessageDigest` | `com.egova.api.util.Md5Utils` |
| 直接 Redis 访问 | `Application.resolve(StringRedisTemplate.class)` |
| 外部库调用 | 将 JAR 包放入星桥 `/lib` 目录并重启 |

### 3. 高级 API 使用原则

1. **数据库**：优先使用 `sql` 变量。复杂更新逻辑应获取 `jdbcTemplate` 执行。
2. **三方 Token**：优先使用 `tokenStore.load()`，它内置了缓存和自动刷新机制。
3. **错误处理**：脚本主逻辑必须包裹在 `try-catch` 中，关键步骤应使用 `out.println()` 记录日志。

---

## 常见任务

### 查阅 API 参考

根据需要查阅 `references/` 目录下对应文档：
- 请求/响应操作 → `context-api.md`
- HTTP 请求 → `http-api.md`
- 数据库操作 (MySQL/Oracle) → `database-api.md`
- Redis / Spring Bean 获取 → `spring-api.md`
- 加密解密 (SM3/SM4/RSA) → `crypto-utils.md`
- 业务案例 (JAR 扩展等) → `business-cases.md`

---

## 注意事项

1. **代码风格**：Groovy 脚本片段应保持简洁，避免复杂的类定义，优先使用函数式编程风格。
2. **规范性**：所有变量存取必须符合 `variables['key']` 标准。
3. **可维护性**：所有外部接口调用必须包含超时处理和状态码校验。
