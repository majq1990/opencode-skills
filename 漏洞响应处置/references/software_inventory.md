# 依赖软件清单

> 用户在 2026-05-06 给出的初版清单。**非穷尽**——遇到清单外的软件直接处置即可，但要记得回填本表。
>
> 字段：
> - **软件标识**：写入「软件漏洞」表「软件」字段时使用的规范名（小写英文为主）
> - **类别**：用于 fetch 路由（数据库 / 中间件 / JDK / 服务发现）
> - **NVD 覆盖**：CVE 数据是否能从 NVD 拿到（决定 fetch 用 NVD 还是必须命中厂商站）
> - **官方安全公告**：国产软件大多数没有标准公告路径，需 SPA 渲染或人工核查

## 数据库

| 软件标识 | 类别 | 中文名 | NVD 覆盖 | 官方安全公告 / 抓取建议 |
|---|---|---|---|---|
| `dameng` | 数据库 | 达梦数据库 | 部分（DM8 系列偶有 CVE） | https://www.dameng.com/list_103.html （新闻列表 SPA），CVE 主要靠 CNVD |
| `highgo` | 数据库 | 瀚高数据库 | 否 | https://www.highgo.com/ 未公开发布安全公告页，需邮件支持 |
| `kingbase` | 数据库 | 金仓数据库 | 否 | https://www.kingbase.com.cn/xzzx/index.htm 下载中心补丁包 changelog |
| `mysql` | 数据库 | MySQL | **是** | https://www.oracle.com/security-alerts/ Oracle CPU 季度公告；MySQL 8.x 优先看 release notes |
| `postgresql` | 数据库 | PostgreSQL | **是** | https://www.postgresql.org/support/security/ |
| `tdengine2` | 数据库 | TDengine 2.x | 部分 | https://docs.taosdata.com/release-history/ + GitHub releases |
| `tdengine3` | 数据库 | TDengine 3.x | 部分 | 同上 |
| `redis` | 数据库 / KV | Redis | **是** | https://github.com/redis/redis/security/advisories |

## 中间件 / 容器

| 软件标识 | 类别 | 中文名 | NVD 覆盖 | 官方安全公告 / 抓取建议 |
|---|---|---|---|---|
| `tomcat` | 中间件 | Apache Tomcat | **是** | https://tomcat.apache.org/security.html |
| `tongweb` | 中间件 | 东方通 TongWeb | 否 | https://www.tongtech.com/dl_serv2.html?id=10 下载中心，CVE 走 CNVD |
| `kingdee-mw` | 中间件 | 金蝶 Apusic | 否 | https://www.apusic.com/ 暂无公开安全公告页 |
| `zhongchuang-mw` | 中间件 | 中创中间件 InforSuite | 否 | https://www.inforbus.com/ 暂无公开安全公告页 |

## 服务注册 / 配置中心

| 软件标识 | 类别 | 中文名 | NVD 覆盖 | 官方安全公告 / 抓取建议 |
|---|---|---|---|---|
| `nacos` | 服务发现 | Nacos | **是** | https://github.com/alibaba/nacos/security/advisories |
| `eureka` | 服务发现 | Netflix Eureka | **是** | https://github.com/Netflix/eureka/security |
| `zookeeper` | 协调服务 | Apache ZooKeeper | **是** | https://zookeeper.apache.org/security.html |

## 消息队列

| 软件标识 | 类别 | 中文名 | NVD 覆盖 | 官方安全公告 / 抓取建议 |
|---|---|---|---|---|
| `kafka` | 消息队列 | Apache Kafka | **是** | https://kafka.apache.org/cve-list |

## 运行时

| 软件标识 | 类别 | 中文名 | NVD 覆盖 | 官方安全公告 / 抓取建议 |
|---|---|---|---|---|
| `jdk8` | JDK | Oracle JDK 8 / OpenJDK 8 | **是** | https://www.oracle.com/security-alerts/ Oracle CPU；OpenJDK 走 https://openjdk.org/groups/vulnerability/advisories/ |

## 底层库（被以上软件间接依赖）

| 软件标识 | 类别 | 中文名 | NVD 覆盖 | 官方安全公告 / 抓取建议 |
|---|---|---|---|---|
| `openssl` | 加密库 | OpenSSL | **是** | https://openssl-library.org/news/vulnerabilities/ + https://www.openssl.org/news/secadv/ |

> OpenSSL 几乎被所有其它依赖（mysql/pg/redis/nacos/tomcat/jdk 等）间接引入。遇到 OpenSSL CVE 时，处置文档建议同时列出受影响的上层依赖软件（哪个产品打包了该 OpenSSL 版本）。

## 抓取策略

软件漏洞跟 OS 不同——**很多组件没有"按 CVE 检索"的接口**，要用以下两路：

1. **NVD CVE 元数据兜底**（推荐第一手，覆盖广）：
   - 接口 `https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={CVE_ID}`
   - 拿到：CVSS、描述、CWE、关联的 vendor/product CPE、官方 references
   - 限速：未注册 5 req/30s，可申请 API key 后 50 req/30s

2. **从 CPE → 软件标识 → 路由到本表**：NVD 返回的 CPE（如 `cpe:2.3:a:redis:redis:6.2.5`）的第三段就是软件标识，做白名单匹配

3. **国产软件兜底**：CNVD（`https://www.cnvd.org.cn/flaw/list`）+ 软件官网公告页（多为 SPA，需 scrapling）

## 待办

- 国产数据库/中间件的 CNVD 收录情况要逐一抓样验证
- 「金蝶中间件」「中创中间件」目前只能靠人工核查 + 邮件支持
- 把每家厂商的公告抓取脚本写进 `scripts/fetch_software_advisory.py`（v0.2 阶段）
