# xray 命令参考

## 全局选项

```bash
xray [全局选项] <命令> [命令选项]
```

### 全局选项

| 选项 | 说明 |
|------|------|
| `--config FILE` | 指定配置文件 |
| `--log-level LEVEL` | 日志级别 (debug, info, warn, error) |
| `--version` | 显示版本信息 |
| `--help` | 显示帮助信息 |

## webscan 命令

Web 漏洞扫描主命令。

```bash
xray webscan [选项]
```

### 目标指定

| 选项 | 说明 | 示例 |
|------|------|------|
| `--url URL` | 扫描单个 URL | `--url http://example.com` |
| `--url-file FILE` | 从文件读取 URL 列表 | `--url-file targets.txt` |
| `--basic-crawler URL` | 基础爬虫模式 | `--basic-crawler http://example.com` |
| `--listen IP:PORT` | 被动代理模式 | `--listen 127.0.0.1:7777` |

### 扫描控制

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--depth N` | 爬虫深度 | 3 |
| `--limit N` | 限制扫描页面数 | 1000 |
| `--max-qps N` | 每秒最大请求数 | 无限制 |
| `--max-concurrent N` | 最大并发数 | 20 |
| `--timeout N` | 超时时间（秒） | 10 |

### 插件控制

| 选项 | 说明 | 示例 |
|------|------|------|
| `--plugins LIST` | 启用指定插件 | `--plugins sqldet,xss` |
| `--disable-plugins LIST` | 禁用指定插件 | `--disable-plugins brute-force` |
| `--list-plugins` | 列出所有可用插件 | - |
| `--poc-path PATH` | 指定 POC 目录 | `--poc-path ./my-pocs` |

### HTTP 选项

| 选项 | 说明 | 示例 |
|------|------|------|
| `--header "KEY:VALUE"` | 自定义 HTTP 头 | `--header "Authorization: Bearer token"` |
| `--cookie COOKIE` | Cookie 字符串 | `--cookie "session=abc"` |
| `--proxy URL` | 使用代理 | `--proxy http://127.0.0.1:8080` |
| `--user-agent UA` | 自定义 User-Agent | `--user-agent "Mozilla/5.0"` |

### 输出选项

| 选项 | 说明 | 示例 |
|------|------|------|
| `--html-output FILE` | HTML 格式输出 | `--html-output report.html` |
| `--json-output FILE` | JSON 格式输出 | `--json-output report.json` |
| `--text-output FILE` | 纯文本输出 | `--text-output report.txt` |

### 反连平台

| 选项 | 说明 | 示例 |
|------|------|------|
| `--reverse-token TOKEN` | 反连平台 Token | `--reverse-token xxx` |

## ca 命令

CA 证书管理。

```bash
xray ca [选项]
```

| 选项 | 说明 |
|------|------|
| `--download` | 下载 CA 证书 |
| `--print` | 打印 CA 证书内容 |

## version 命令

显示版本信息。

```bash
xray version
```

## 常用命令示例

### 基础扫描

```bash
# 扫描单个 URL
xray webscan --url http://example.com --html-output report.html

# 爬虫扫描
xray webscan --basic-crawler http://example.com --depth 5

# 代理扫描
xray webscan --listen 127.0.0.1:7777 --html-output proxy.html
```

### 指定插件

```bash
# 仅扫描 SQL 注入
xray webscan --plugins sqldet --url http://example.com

# 扫描 SQL 注入和 XSS
xray webscan --plugins sqldet,xss --url http://example.com

# 禁用弱口令扫描
xray webscan --disable-plugins brute-force --url http://example.com
```

### 批量扫描

```bash
# 从文件读取目标
xray webscan --url-file targets.txt --json-output batch.json

# 指定 Cookie 和 Header
xray webscan --url http://example.com \
  --cookie "session=abc" \
  --header "Authorization: Bearer token" \
  --html-output auth_report.html
```

### 高级用法

```bash
# 限速扫描（每秒 10 请求）
xray webscan --url http://example.com --max-qps 10

# 深度爬虫扫描
xray webscan --basic-crawler http://example.com --depth 5 --limit 500

# 使用自定义 POC
xray webscan --url http://example.com --poc-path ./custom-pocs/
```

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 扫描完成，未发现漏洞 |
| 1 | 扫描完成，发现漏洞 |
| 2 | 扫描出错 |
| 3 | 参数错误 |
