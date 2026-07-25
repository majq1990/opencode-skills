---
name: xray-security-scanner
description: 基于长亭 xray 的安全漏洞扫描工具封装。当用户需要扫描网站漏洞、执行安全评估、检测 Web 安全问题（SQL 注入、XSS、命令注入、目录遍历、XXE、SSRF 等）、生成安全报告或管理 POC 时自动触发。支持主动扫描（爬虫）、被动扫描（代理）、自定义 POC 和多种输出格式。触发关键词：xray、安全扫描、漏洞检测、渗透测试、Web 安全、SQL 注入、XSS、POC。
---

# xray 安全扫描工具

基于长亭 xray 的 Web 安全漏洞扫描封装，支持主动扫描、被动扫描、自定义 POC 和丰富的报告输出。

## 功能概览

- **主动扫描**：爬虫模式自动发现链接并扫描
- **被动扫描**：代理模式拦截流量并分析
- **漏洞检测**：支持 SQL 注入、XSS、命令注入、XXE、SSRF 等 10+ 类漏洞
- **自定义 POC**：支持编写和运行自定义检测规则
- **指纹识别**：Web 技术栈识别
- **多种输出**：HTML、JSON、TXT 报告格式

## 快速开始

### 1. 安装 xray

首次使用前需安装 xray：

```bash
python "D:\opencode\config\skills\xray-security-scanner\scripts\install_xray.py"
```

安装脚本会自动：
- 检测操作系统和架构
- 下载最新版 xray 二进制文件
- 解压到 `~/.xray/` 目录
- 生成默认配置文件
- 验证安装

## 配置网络代理（可选）

### GitHub 下载加速

当访问 GitHub 原始资源（如 POC 仓库）速度较慢时，可使用国内镜像加速：

**ghfast.top 代理：**
- 在原始 GitHub URL 前加上 `https://ghfast.top/`

**示例：**
```bash
# 原始 URL（可能慢）
https://github.com/chaitin/xray/tree/master/pocs

# 代理后 URL（国内加速）
https://ghfast.top/https://github.com/chaitin/xray/tree/master/pocs
```

### POC 下载方式

xray 支持三种 POC 加载模式：

1. **本地 POC（推荐）**：下载到本地目录，可离线使用
2. **内置 POC**：xray 自带约 200+ 基础检测规则
3. **远程加载**：需联网，从 URL 实时获取

**使用 POC 管理脚本下载：**
```bash
# 下载官方 POC 库到本地
python "D:\opencode\config\skills\xray-security-scanner\scripts\poc_manager.py" download --url https://ghfast.top/raw/chaitin/xray/master/pocs/

# 更新本地 POC
python "D:\opencode\config\skills\xray-security-scanner\scripts\poc_manager.py" update
```

### 2. 执行扫描

#### 主动扫描（爬虫模式）
自动爬取网站并扫描发现的链接：

```bash
xray webscan --basic-crawler http://example.com --html-output report.html
```

#### 被动扫描（代理模式）
设置代理拦截浏览器流量：

```bash
# 启动代理
xray webscan --listen 127.0.0.1:7777 --html-output proxy.html

# 浏览器设置 HTTP 代理为 127.0.0.1:7777
```

#### 单 URL 扫描
针对单个目标快速扫描：

```bash
xray webscan --url "http://example.com/page?id=1" --json-output result.json
```

## 扫描模式详解

### 主动扫描模式

**基础爬虫扫描**
```bash
xray webscan --basic-crawler <目标URL> [选项]
```

选项说明：
- `--basic-crawler`: 启用基础爬虫模式
- `--depth`: 爬虫深度，默认 3
- `--limit`: 限制爬虫页面数量

**示例：**
```bash
# 深度为 5 的爬虫扫描
xray webscan --basic-crawler http://target.com --depth 5 --html-output deep_scan.html
```

### 被动扫描模式

**代理扫描**
```bash
xray webscan --listen <IP:端口> [选项]
```

**HTTPS 流量扫描**
1. 下载 xray CA 证书：
```bash
xray ca --download
```

2. 安装证书到浏览器/系统
3. 配置浏览器代理为 xray 监听地址
4. 正常浏览，xray 自动分析流量

### 批量扫描

**从文件读取目标**
```bash
xray webscan --url-file targets.txt --html-output batch.html
```

targets.txt 格式：
```
http://target1.com
http://target2.com/page?id=1
https://target3.com/api
```

## 插件（检测模块）管理

### 查看可用插件

```bash
xray webscan --list-plugins
```

### 指定插件扫描

```bash
# 仅启用 SQL 注入和 XSS 检测
xray webscan --plugins sqldet,xss --url http://target.com

# 禁用某些插件
xray webscan --disable-plugins brute-force --url http://target.com
```

### 常用插件说明

| 插件名 | 说明 | 版本 |
|--------|------|------|
| sqldet | SQL 注入检测（报错、布尔、时间盲注） | 社区版 |
| xss | XSS 漏洞检测（语义分析） | 社区版 |
| cmd-injection | 命令/代码注入检测 | 社区版 |
| dirscan | 目录枚举（备份文件、配置文件等） | 社区版 |
| path-traversal | 路径穿越检测 | 社区版 |
| xxe | XML 实体注入检测 | 社区版 |
| upload | 文件上传检测 | 社区版 |
| brute-force | 弱口令检测 | 社区版 |
| ssrf | SSRF 检测 | 社区版 |
| baseline | 基线检查（SSL、HTTP 头） | 社区版 |
| phantasm | POC 管理 | 社区版 |
| struts | Struts2 系列漏洞 | 高级版 |
| thinkphp | ThinkPHP 漏洞检测 | 高级版 |
| shiro | Shiro 反序列化检测 | 高级版 |
| fastjson | Fastjson 漏洞检测 | 高级版 |

## 输出与报告

### 输出格式选项

```bash
# HTML 报告（推荐，可视化）
xray webscan --url http://target.com --html-output report.html

# JSON 格式（便于程序处理）
xray webscan --url http://target.com --json-output report.json

# 纯文本格式
xray webscan --url http://target.com --text-output report.txt

# 同时输出多种格式
xray webscan --url http://target.com \
  --html-output report.html \
  --json-output report.json \
  --text-output report.txt
```

### 报告内容

**HTML 报告包含：**
- 漏洞列表（按严重程度分类）
- 漏洞详情（URL、参数、Payload、证据）
- 修复建议
- 统计信息
- 原始请求/响应

**JSON 报告结构：**
```json
{
  "vulnerabilities": [
    {
      "plugin": "sqldet",
      "target": "http://target.com/page?id=1",
      "vuln_class": "sql_injection",
      "severity": "high",
      "detail": {
        "payload": "...",
        "evidence": "..."
      }
    }
  ]
}
```

## 自定义 POC

### POC 目录

自定义 POC 存放位置：
- Windows: `%USERPROFILE%\.xray\pocs\`
- Linux/macOS: `~/.xray/pocs/`

### POC 格式

POC 使用 YAML 格式，示例：

```yaml
name: poc-yaml-example-rule
rules:
  - method: GET
    path: /api/user?id=1
    expression: |
      response.status == 200 && response.body.bcontains(b"username")
detail:
  author: your_name
  links:
    - https://example.com/vuln
```

### 运行自定义 POC

```bash
# 指定自定义 POC 目录
xray webscan --poc-path ./my-pocs --url http://target.com

# 指定单个 POC 文件
xray webscan --poc-path ./my-pocs/custom.yml --url http://target.com
```

### POC 编写辅助

使用规则实验室在线编写和验证：
- 在线版：https://poc.xray.cool
- 支持 POC 查重和验证

## 配置文件

### 配置文件位置

- Windows: `%USERPROFILE%\.xray\config.yml`
- Linux/macOS: `~/.xray/config.yml`

### 常用配置项

```yaml
# HTTP 配置
http:
  proxy: ""  # 代理服务器
  timeout: 10  # 超时时间（秒）
  max_redirect: 10  # 最大重定向次数
  max_concurrent: 20  # 最大并发数

# 扫描配置
scan:
  max_depth: 3  # 爬虫最大深度
  max_count: 1000  # 最大扫描页面数
  allow_domains: []  # 允许的域名
  deny_domains: []  # 禁止的域名

# 插件配置
plugins:
  sqldet:
    enabled: true
    detect_blind: true
  xss:
    enabled: true
  brute-force:
    enabled: false  # 默认禁用弱口令爆破
    username_file: ""
    password_file: ""

# 反连平台配置（用于检测无回显漏洞）
reverse:
  enabled: false
  token: "your_token"
  platform: ""
```

## 高级用法

### 反连平台（检测无回显漏洞）

对于 SSRF、XXE 等无回显漏洞，需要配置反连平台：

```bash
# 使用公网反连平台
xray webscan --url http://target.com --reverse-token your_token

# 本地启动反连服务
xray reverse --token your_token
```

### 指定 HTTP 头

```bash
xray webscan --url http://target.com \
  --header "Authorization: Bearer token" \
  --header "X-Custom: value"
```

### Cookie 认证扫描

```bash
xray webscan --url http://target.com --cookie "session=abc123"
```

### 限速扫描

```bash
# 每秒最大请求数
xray webscan --url http://target.com --max-qps 10
```

## 辅助脚本

### 批量扫描脚本

使用 `scripts/batch_scan.py` 批量扫描多个目标：

```bash
python "D:\opencode\config\skills\xray-security-scanner\scripts\batch_scan.py" targets.txt
```

### 报告生成脚本

使用 `scripts/report_generator.py` 合并和美化报告：

```bash
python "D:\opencode\config\skills\xray-security-scanner\scripts\report_generator.py" report.json --format html
```

### POC 管理脚本

使用 `scripts/poc_manager.py` 管理自定义 POC：

```bash
# 列出所有 POC
python "D:\opencode\config\skills\xray-security-scanner\scripts\poc_manager.py" list

# 验证 POC 语法
python "D:\opencode\config\skills\xray-security-scanner\scripts\poc_manager.py" validate ./my-poc.yml
```

## 使用建议

### 扫描前准备

1. **获取授权**：确保已获得目标系统的合法测试授权
2. **备份数据**：生产环境扫描前备份重要数据
3. **通知相关人员**：避免扫描触发安全告警造成恐慌
4. **测试环境先行**：先在测试环境验证扫描策略

### 扫描策略建议

**快速初筛**
```bash
xray webscan --url http://target.com --plugins sqldet,xss,cmd-injection \
  --json-output quick_scan.json
```

**深度扫描**
```bash
xray webscan --basic-crawler http://target.com --depth 5 \
  --html-output deep_scan.html
```

**API 安全扫描**
```bash
xray webscan --url http://api.target.com --header "Accept: application/json" \
  --plugins sqldet,xss,ssrf,xxe --json-output api_scan.json
```

### 误报处理

如发现误报，可通过以下方式反馈：
1. 在 GitHub 提交 Issue：https://github.com/chaitin/xray/issues
2. 提供完整的请求/响应数据和扫描日志
3. 参考靶场验证：https://github.com/chaitin/xray/tree/master/tests/evilpot

## 故障排查

### 安装问题

**问题**：下载失败或权限不足
```bash
# 手动下载并解压到 ~/.xray/
# Windows: %USERPROFILE%\.xray\
# Linux/macOS: ~/.xray/
```

### 扫描问题

**问题**：无法扫描 HTTPS 站点
- 解决：安装 xray CA 证书到系统/浏览器信任库

**问题**：扫描速度过慢
- 解决：增加并发数 `--max-concurrent 50` 或限制深度 `--depth 2`

**问题**：大量误报
- 解决：调整插件配置或禁用敏感插件

### 查看帮助

```bash
# 全局帮助
xray --help

# webscan 模块帮助
xray webscan --help

# 查看版本
xray version
```

## 安全声明

**⚠️ 重要提示**

1. **合法授权**：使用 xray 扫描任何系统前，必须获得系统所有者的明确书面授权
2. **遵守法律**：遵守当地法律法规，禁止用于非法目的
3. **数据保护**：妥善保管扫描结果，避免敏感信息泄露
4. **责任自负**：未经授权使用造成的任何后果由使用者自行承担

**免责声明**：本 skill 仅用于安全研究和授权的渗透测试，开发者不对任何非法使用承担责任。

## 参考资源

- 官方文档：https://docs.xray.cool
- GitHub 仓库：https://github.com/chaitin/xray
- POC 插件库：https://github.com/chaitin/xray-plugins
- 规则实验室：https://poc.xray.cool
- xray 2.0 xpoc：https://github.com/chaitin/xpoc
- xray 2.0 xapp：https://github.com/chaitin/xapp

## 更新日志

### v1.0.0 (2024-06)
- 初始版本发布
- 支持 xray 基础扫描功能
- 提供安装、配置、扫描、报告生成完整流程
- 集成常用插件和自定义 POC 支持
