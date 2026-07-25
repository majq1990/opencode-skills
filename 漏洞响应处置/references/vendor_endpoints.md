# 厂商安全公告接口清单

> 6 家发行版的公开 URL + 已知内部 JSON API。**首次跑某家时必须校验接口仍可用**——浏览器开 DevTools Network、刷一次详情页、抄 XHR/fetch 请求即可。
>
> 这些接口都没有官方对外约定，**随时可能改 schema 或加风控**。fetch_vendor_advisory.py 的 fallback 顺序：JSON API → scrapling PlayWrightFetcher → 人工补录。

## 1. 银河麒麟 KylinOS

| 项 | 值 |
|---|---|
| 厂商代号 | `kylin` |
| 公开页面（SPA） | `https://support.kylinos.cn/#/security/cveDetail?allTitle={CVE_ID}` |
| 列表接口（POST） | `https://support.kylinos.cn/protalweb/security/cve/list` |
| Body | `{"page":1,"size":10,"keyword":"{CVE_ID}"}` |
| Content-Type | `application/json` |
| 关键字段 | `data.records[].cveNumber`, `affectedProduct`, `fixedVersion`, `publishTime` |

## 2. openEuler

| 项 | 值 |
|---|---|
| 厂商代号 | `openeuler` |
| 公开页面（SPA） | `https://www.openeuler.org/zh/security/security-bulletins/?searchKey={CVE_ID}` |
| 详情页 | `https://www.openeuler.org/zh/security/security-bulletins/detail/?id=openEuler-SA-{YYYY-NNNN}` |
| 列表接口（GET） | `https://www.openeuler.org/api-cve/cve-security-notice-server/securitynotice/findAll` |
| 关键字段 | `result.records[].securityNoticeNo`, `affectedProduct`, `cveId`, `noticeUpdateTime` |

## 3. 龙蜥 OpenAnolis (ANSA)

| 项 | 值 |
|---|---|
| 厂商代号 | `anolis` |
| CVE 详情页（SPA） | `https://anas.openanolis.cn/cves/detail/{CVE_ID}` |
| 公告详情页 | `https://anas.openanolis.cn/errata/detail/ANSA-{YYYY:NNNN}` |
| Errata 列表 | `https://anas.openanolis.cn/errata` |
| JSON API | 待反向（部分 CVE 走 `/api/v1/cve/{cve}` 或 `/cves-server/...`，尚未稳定） |
| 抓取建议 | 优先 PlayWrightFetcher 渲染详情页，正则提取 `ANSA-` 编号和受影响版本 |

## 4. 统信 UOS

| 项 | 值 |
|---|---|
| 厂商代号 | `uos` |
| 公告中心（SPA） | `https://src.uniontech.com/#/security_advisory` |
| 详情接口 | 站内 SPA 自查 DevTools，常见路径 `/api/v1/cve/...` |
| 抓取建议 | 站点没有独立 CVE 详情页，只能在公告中心搜索后渲染；建议同时记录"截至 YYYY-MM-DD 公告中心未收录" |

> **不是** `chinauos.com`。那个域名没有安全公告路由，过去踩过一次。

## 5. Ubuntu

| 项 | 值 |
|---|---|
| 厂商代号 | `ubuntu` |
| 公开页面 | `https://ubuntu.com/security/{CVE_ID}` |
| **JSON 接口（推荐）** | `https://ubuntu.com/security/cves/{CVE_ID}.json` |
| 关键字段 | `notes`, `packages[].name`, `packages[].statuses[]`, `priority` |

Ubuntu 是 6 家里唯一直接给官方 JSON 的，绝对不要走 SPA。

## 6. RedHat / CentOS Stream

| 项 | 值 |
|---|---|
| 厂商代号 | `redhat` |
| 公开页面 | `https://access.redhat.com/security/cve/{cve_id_lowercase}` |
| **JSON 接口** | `https://access.redhat.com/hydra/rest/securitydata/cve/{cve_id_uppercase}.json` |
| 关键字段 | `cvss3.cvss3_base_score`, `affected_release[]`, `package_state[]`, `bugzilla.description` |

> CentOS Stream 8/9/10 用 RedHat 的数据；老 CentOS 6/7 已 EOL，单独标注"内核 X.Y.Z 不含缺陷代码"或"不受支持"。

## 抓取统一输出格式（fetch_vendor_advisory.py 的 schema）

```json
{
  "cve_id": "CVE-2026-31431",
  "fetched_at": "2026-05-06T16:30:00+08:00",
  "vendors": [
    {
      "vendor": "openeuler",
      "status": "ok",
      "advisory_id": "openEuler-SA-2026-1544",
      "advisory_url": "https://www.openeuler.org/zh/security/security-bulletins/detail/?id=openEuler-SA-2026-1544",
      "affected_versions": ["22.03 LTS", "24.03 LTS"],
      "fixed_in": "kernel-5.10.0-218",
      "cvss": 7.8,
      "summary": "...",
      "_raw": { }
    },
    {
      "vendor": "uos",
      "status": "not_found",
      "advisory_url": "https://src.uniontech.com/#/security_advisory",
      "note": "截至 2026-05-06 公告中心未收录"
    }
  ]
}
```

`status` 取值：`ok` / `not_found` / `fetch_error`。失败时保留 `error` 和 `_raw` 便于人工排查。

## 通用判据

公告滞后时不要直接判"不受影响"。受影响判断要双线：

1. 厂商公告显式标注的 `affected_versions`
2. 该 OS 默认内核版本是否落在 CVE 受影响代码窗口（commit hash 或版本号区间）

两条线任一命中就标"受影响 = 是"，并在「信息来源」字段说明判据来源。
