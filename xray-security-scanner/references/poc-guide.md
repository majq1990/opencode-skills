# xray POC 编写指南

POC（Proof of Concept）是用于检测特定漏洞的规则定义文件。

## POC 格式

POC 使用 YAML 格式，基本结构如下：

```yaml
name: poc-yaml-example-vulnerability
rules:
  - method: GET
    path: /vulnerable/path
    headers:
      User-Agent: "Mozilla/5.0"
    expression: |
      response.status == 200 && response.body.bcontains(b"vulnerable")
detail:
  author: your_name
  description: "漏洞描述"
  links:
    - "https://example.com/cve-2024-1234"
```

## 字段说明

### name

POC 的唯一标识符，建议格式：`poc-<类别>-<名称>`

- 必须唯一
- 只能包含字母、数字、连字符、下划线
- 建议以 `poc-` 开头

### rules

检测规则列表，每条规则包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| method | string | 是 | HTTP 方法 (GET/POST/PUT/DELETE/HEAD/OPTIONS/PATCH) |
| path | string | 是 | 请求路径 |
| headers | map | 否 | 请求头 |
| body | string | 否 | 请求体（POST/PUT 等） |
| expression | string | 是 | 检测表达式（CEL 语法） |
| follow_redirects | bool | 否 | 是否跟随重定向，默认 true |

### detail

POC 的元信息：

| 字段 | 类型 | 说明 |
|------|------|------|
| author | string | 作者名称 |
| description | string | 漏洞描述 |
| links | list | 参考链接列表 |
| vulnerability | map | 漏洞详细信息 |

## 表达式语法

使用 CEL（Common Expression Language）语法：

### 响应对象

| 属性 | 类型 | 说明 |
|------|------|------|
| response.status | int | HTTP 状态码 |
| response.body | bytes | 响应体（字节） |
| response.body_string | string | 响应体（字符串） |
| response.headers | map | 响应头 |
| response.latency | int | 响应时间（毫秒） |

### 常用函数

| 函数 | 说明 | 示例 |
|------|------|------|
| bcontains | 字节包含 | `response.body.bcontains(b"admin")` |
| contains | 字符串包含 | `response.body_string.contains("error")` |
| matches | 正则匹配 | `response.body_string.matches("id=\\d+")` |
| startsWith | 前缀匹配 | `response.body_string.startsWith("{")` |
| endsWith | 后缀匹配 | `response.body_string.endsWith("}")` |
| in | 包含判断 | `"admin" in response.body_string` |
| int | 转整数 | `int(response.headers["Content-Length"]) > 100` |
| string | 转字符串 | `string(response.body)` |

### 表达式示例

```yaml
# 检查状态码和响应内容
expression: |
  response.status == 200 && 
  response.body.bcontains(b"admin") && 
  response.body.bcontains(b"password")

# 检查响应头
expression: |
  "X-Powered-By" in response.headers &&
  response.headers["X-Powered-By"].contains("PHP")

# 检查响应时间（时间盲注）
expression: |
  response.latency > 5000

# 组合条件
expression: |
  (response.status == 200 || response.status == 302) &&
  response.body.bcontains(b"success")
```

## 多规则 POC

支持多条规则按顺序执行：

```yaml
name: poc-yaml-multi-step
rules:
  # 第一步：获取 token
  - method: GET
    path: /api/get-token
    expression: |
      response.status == 200
    output:
      token: response.body_string.matches("token\":\"([^\"]+)\"")
  
  # 第二步：使用 token 访问
  - method: POST
    path: /api/admin
    headers:
      Authorization: "Bearer {{token}}"
    body: |
      {"action": "delete"}
    expression: |
      response.status == 200 &&
      response.body.bcontains(b"success")
```

## 变量和输出

### 定义变量

```yaml
rules:
  - method: GET
    path: /api/user/{{id}}
    expression: |
      response.status == 200
    output:
      user_id: response.body_string.matches("id\":(\d+)")
```

### 使用变量

```yaml
rules:
  - method: GET
    path: /api/user/1
    expression: response.status == 200
    output:
      token: response.headers["X-Auth-Token"]
  
  - method: POST
    path: /api/admin
    headers:
      X-Auth-Token: "{{token}}"
    expression: response.status == 200
```

## POC 示例

### SQL 注入检测

```yaml
name: poc-yaml-sqli-error
rules:
  - method: GET
    path: /page.php?id=1' AND 1=1--
    expression: |
      response.body_string.contains("SQL syntax") ||
      response.body_string.contains("mysql_fetch")
detail:
  author: security_researcher
  description: "MySQL 错误回显 SQL 注入"
  links:
    - "https://owasp.org/www-community/attacks/SQL_Injection"
```

### XSS 检测

```yaml
name: poc-yaml-xss-reflected
rules:
  - method: GET
    path: /search?q=<script>alert(1)</script>
    expression: |
      response.body.bcontains(b"<script>alert(1)</script>") &&
      response.headers.get("Content-Type", "").contains("text/html")
detail:
  author: security_researcher
  description: "反射型 XSS"
```

### 目录遍历

```yaml
name: poc-yaml-path-traversal
rules:
  - method: GET
    path: /download?file=../../../etc/passwd
    expression: |
      response.body.bcontains(b"root:") &&
      response.body.bcontains(b":/bin/bash")
detail:
  author: security_researcher
  description: "路径遍历导致任意文件读取"
```

### 未授权访问

```yaml
name: poc-yaml-unauthorized-admin
rules:
  - method: GET
    path: /admin/config
    expression: |
      response.status == 200 &&
      response.body.bcontains(b"admin") &&
      response.body.bcontains(b"password")
detail:
  author: security_researcher
  description: "管理后台未授权访问"
```

## 最佳实践

### 1. POC 命名规范

- 使用 `poc-<类别>-<具体名称>` 格式
- 类别示例：yaml, go, cms, oa, framework
- 名称使用小写字母和连字符

### 2. 提高准确性

- 使用多个条件组合验证
- 避免使用容易变化的特征（如时间戳、随机数）
- 添加响应头检查，减少误报

### 3. 避免误报

```yaml
# 好的示例 - 多条件验证
expression: |
  response.status == 200 &&
  response.body.bcontains(b"admin") &&
  response.body.bcontains(b"dashboard") &&
  response.headers.get("Content-Type", "").contains("text/html")

# 差的示例 - 容易误报
expression: |
  response.body.bcontains(b"success")
```

### 4. 文档完善

- 在 detail 中添加详细的漏洞描述
- 提供漏洞影响的版本信息
- 添加修复建议

### 5. 测试验证

使用 POC 管理工具验证：

```bash
python poc_manager.py validate ./your-poc.yml
```

## 在线工具

- **规则实验室**: https://poc.xray.cool
  - 在线编写和验证 POC
  - POC 查重
  - 一键测试

## 参考资源

- 官方文档: https://docs.xray.cool/#/guide/poc
- POC 仓库: https://github.com/chaitin/xray/tree/master/pocs
- 靶场测试: https://github.com/chaitin/xray/tree/master/tests/evilpot
