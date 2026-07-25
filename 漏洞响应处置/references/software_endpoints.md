# 软件漏洞抓取接口清单

> OS 分支看 `vendor_endpoints.md`；本文件只覆盖三方依赖软件。

## 1. NVD CVE 2.0 API（主路径）

NVD 是软件 CVE 的"事实标准"数据源——CVSS、CWE、CPE、references 都齐全，且接口稳定。

| 项 | 值 |
|---|---|
| 接口（GET） | `https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={CVE_ID}` |
| 限速 | 未注册：5 req / 30s；申请 API key 后：50 req / 30s |
| 国内可达性 | 偶发慢/超时，必要时挂代理 |
| 关键字段 | `vulnerabilities[0].cve.metrics.cvssMetricV31[0].cvssData.baseScore` / `cve.descriptions[lang=zh-CN or en]` / `cve.references[]` / `cve.configurations[].nodes[].cpeMatch[].criteria` (CPE) |

CPE 第三段就是软件标识，例如 `cpe:2.3:a:redis:redis:6.2.5:*:*:*:*:*:*:*` → 软件标识 = `redis`，可直接对到 `software_inventory.md` 白名单。

## 2. CNVD（国家信息安全漏洞共享平台，国产软件兜底）

国产软件（达梦/瀚高/金仓/东方通/金蝶/中创等）NVD 覆盖差，必须看 CNVD。

| 项 | 值 |
|---|---|
| 漏洞列表 SPA | `https://www.cnvd.org.cn/flaw/list` |
| 详情页 | `https://www.cnvd.org.cn/flaw/show/CNVD-YYYY-NNNNN` |
| 内部接口 | `https://www.cnvd.org.cn/flaw/list.htm?flag=true&number={CNVD-ID-OR-CVE}` |
| 抓取建议 | SPA 必须 PlayWrightFetcher 渲染；按 CVE 反查的精度差，常需要先在搜索引擎里找到 CNVD 编号 |

## 3. 各软件官方公告

### 数据库

| 软件 | 公告页 / 接口 |
|---|---|
| `mysql` | https://www.oracle.com/security-alerts/ （CPU 季度公告，搜 MySQL 章节）；release notes 同步看 https://dev.mysql.com/doc/relnotes/ |
| `postgresql` | https://www.postgresql.org/support/security/ （HTML 表格，可解析） |
| `redis` | https://github.com/redis/redis/security/advisories （GitHub Security Advisories 有 JSON API：`https://api.github.com/repos/redis/redis/security-advisories?cve_id={CVE_ID}`） |
| `tdengine2` / `tdengine3` | https://docs.taosdata.com/release-history/ + https://github.com/taosdata/TDengine/security |
| `dameng` | https://www.dameng.com/list_103.html （SPA 新闻列表，安全公告少；CVE 主要靠 CNVD） |
| `kingbase` | https://www.kingbase.com.cn/xzzx/index.htm （下载中心 changelog） |
| `highgo` | 无公开公告页，需邮件支持 |

### 中间件

| 软件 | 公告页 / 接口 |
|---|---|
| `tomcat` | https://tomcat.apache.org/security.html （静态 HTML，可直接 fetch） |
| `tongweb` | https://www.tongtech.com/dl_serv2.html?id=10 + CNVD |
| `kingdee-mw` | 无公开页 |
| `zhongchuang-mw` | 无公开页 |

### 服务发现 / 配置 / MQ / 协调

| 软件 | 公告页 / 接口 |
|---|---|
| `nacos` | https://github.com/alibaba/nacos/security/advisories |
| `eureka` | https://github.com/Netflix/eureka/security |
| `zookeeper` | https://zookeeper.apache.org/security.html |
| `kafka` | https://kafka.apache.org/cve-list （静态页） |

### 运行时

| 软件 | 公告页 / 接口 |
|---|---|
| `jdk8` (Oracle) | https://www.oracle.com/security-alerts/ |
| `jdk8` (OpenJDK) | https://openjdk.org/groups/vulnerability/advisories/ |

## 4. GitHub Security Advisories（GHSA）通用接口

很多开源软件（redis/nacos/eureka 等）维护 GHSA，比 NVD 更及时。

```
GET https://api.github.com/repos/{owner}/{repo}/security-advisories?cve_id={CVE_ID}
Headers: Accept: application/vnd.github+json
```

需要 GitHub token 提高限速（未认证 60 req/h，认证后 5000 req/h）。

## 5. 抓取统一输出格式（fetch_software_advisory.py 输出 schema）

```json
{
  "cve_id": "CVE-2024-31449",
  "fetched_at": "2026-05-06T17:00:00+08:00",
  "vendor_lookups": [
    {
      "source": "nvd",
      "status": "ok",
      "cvss_v31": 8.1,
      "severity": "HIGH",
      "description": "Lua library in Redis ...",
      "published": "2024-10-08",
      "cwes": ["CWE-122"],
      "cpes": [
        "cpe:2.3:a:redis:redis:7.2.5:*:*:*:*:*:*:*",
        "cpe:2.3:a:redis:redis:7.4.0:*:*:*:*:*:*:*"
      ],
      "references": [
        {"url": "https://github.com/redis/redis/security/advisories/GHSA-...", "tags": ["Vendor Advisory"]}
      ],
      "_raw": { }
    },
    {
      "source": "ghsa",
      "status": "ok",
      "ghsa_id": "GHSA-...-...-...",
      "fixed_versions": ["6.2.16", "7.2.6", "7.4.1"],
      "_raw": { }
    },
    {
      "source": "cnvd",
      "status": "needs_render",
      "advisory_url": "https://www.cnvd.org.cn/flaw/list.htm?number=CVE-2024-31449"
    }
  ]
}
```

`status` 取值：`ok` / `not_found` / `fetch_error` / `needs_render`。
