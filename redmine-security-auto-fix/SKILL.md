---
name: redmine-security-auto-fix
version: 2.1.0
author: majianquan
license: MIT
category: support-dept
visibility: tech-manager
description: Redmine 安全案件自动化处理与修复建议检索，v2.0 新增安全案件三源研判与滚动跟踪。凡涉及 Redmine 安全案件、漏洞报告解析、历史安全案件学习、相似漏洞修复方案、代码/非代码修复分流、钉钉知识库归档、安全漏洞自动修复、CVE/CNVD 情报采集、扫描结果与资产台账对照、处置报告与责任人待办、案件次日滚动跟踪，都应使用本 Skill。它兼容多种漏洞报告格式，内部检索走两条链路并合并：服务器安全池（tracker 26 安全案件 + 语义审计回填的漏召案件 + 297 篇★安全文档 + NVD/GHSA 情报，秒级）与全库（19.9 万工单 + 7,700 篇文档），安全池结果优先；非代码类始终并行检索互联网，代码类仅在内部无可执行方案时才用互联网兜底；v2.0 增量能力来自三源研判子系统（CVE 情报 × 扫描结果 × 资产台账 → 分级 → 报告/待办 → 次日跟踪），全部配置外置、默认关闭、人工确认后才推送。v2.1：《安全漏洞台账》多维表为检索第一优先（台账→内部检索→互联网搜索兜底，台账命中即免搜），anysearch 为默认搜索源（key 可选），新增 8 类扫描器报告专项解析（Fortify/AppScan/ZAP/Trivy/osv/Markdown 渗透报告等），超大案件分片并行检索，已移除群机器人通知（发布即交付）。
---

# Redmine 安全案件自动化处理

## 目标

把当前 Redmine 安全案件的附件作为漏洞事实来源，但不把报告里的建议视为唯一答案。流程需要：

1. 兼容不同厂商、不同结构的漏洞报告。
2. 保留当前报告自带的全部加固建议。
3. 优先从服务器安全池（安全案件 + ★安全文档 + CVE 情报）和全库（历史案件 + 钉钉
   知识库）查找实际修复操作。
4. 非代码类漏洞内部无匹配时，检索互联网公开权威来源。
5. 代码类漏洞只允许使用当前报告和内部知识；内部无结果时不额外提供建议。
6. 每条建议标明来源，不能把推测包装成历史事实。

## 依赖

- `D:\git\redmine-similar-assist`
- **安全池检索**：`demo.egova.com.cn` 上的 `sec_kb` 工具（容器 `redmine-assist`，
  路径 `/app/scripts/sec_kb`），经 `scripts\sec_kb_bridge.py` 只读调用。该池由服务器
  cron 每日增量采集、每周审计回填，本地无需任何数据库或密钥；不可达时自动降级为
  仅走全库链路，不阻塞主流程。
- Python 3.10+
- 基础：`requests`、`pyyaml`
- DOCX：`python-docx`
- Excel：`pandas`、`openpyxl`、旧 `.xls` 另需 `xlrd`
- PDF：`pdfplumber`
- 快速 PDF 文本：`pypdf`
- HTML：`beautifulsoup4`
- 旧 Excel：`xlrd>=2.0.1`
- RAR：`rarfile` + unrar/unar/7-Zip 后端

不要在本 Skill 中复制 Redmine、数据库、Embedding 或 LLM 密钥。统一读取
`redmine-similar-assist\config.yaml`。

- **互联网搜索兜底**：anysearch（默认，国内直连）。key 优先级：环境变量
  `ANYSEARCH_API_KEY` → skill 根目录 `.env` → 匿名访问（可用但有速率限制）。
  **初始化时推荐配置 key**：到 https://anysearch.com/console/api-keys 申请后，
  写入环境变量或 skill 根目录 `.env` 的 `ANYSEARCH_API_KEY=` 即可。

## 首次学习历史报告格式

先查询最近一年全部安全案件，固定条件：

- `tracker_id = 26`
- `created_on >= 当前时间 - 365 天`
- 不限制项目、状态或责任人

运行：

```powershell
python scripts\download_security_corpus.py `
  --days 365 `
  --tracker-id 26 `
  --workers 8 `
  --download-config config.yaml `
  --output-dir D:\opencode\_archive\security-corpus
```

脚本通过 `redmine-similar-assist` 的 MySQL 连接查询案件和附件，下载至：

```text
D:\opencode\_archive\security-corpus\<issue_id>\
```

并生成 `download-manifest.json`，其中记录：

- 案件数、附件数、扩展名分布
- 每个附件的下载状态与本地路径
- 下载失败原因

下载器具有断点续跑能力：本地文件大小与 Redmine 元数据一致时直接跳过。附件名会加
attachment id 前缀，避免同一案件中的重名附件并发覆盖。

Redmine 下载接口会 `302` 跳转至 OSS。下载器优先使用 `curl.exe -L`，在 Redmine
请求上携带 API Key，随后访问 OSS 地址。二进制文件严格校验大小；HTML/TXT 等文本
允许 1KB 或 1% 的换行/编码差异。

## 解析层回归与值守

- **解析回归**：`python scripts
egression_check.py`——14 个样本组（各格式代表附件）
  与 `tests/baseline/parse_regression.json` 比对，改动解析器/合并逻辑后必跑；
  有意的行为变化用 `--update-baseline` 重录。检索/方案层回归走 12 案 journal 核对流程。
- **新案件值守**：`python scripts\watch_new_cases.py --days 2 --limit 5`——发现
  tracker26 新案件逐案出**草稿**（发布须人工确认后 finalize），
  已处理案件记入 state 自动跳过，限流按约定等 8 分钟。

## 验证历史语料解析

下载完成后运行：

```powershell
python scripts\validate_corpus_extraction.py `
  --corpus-dir D:\opencode\_archive\security-corpus `
  --workers 6 `
  --timeout-seconds 30
```

输出 `extraction-validation.json`，记录：

- 每个附件的解析状态
- 原始提取数量和具体漏洞数量
- 按格式统计成功、空结果、错误、超时
- 每种格式抽取到的实际漏洞样本

验证器将每份报告放入独立子进程。单文件超过时限会终止并记为 `timeout`，避免异常
PDF 阻塞整个批次。

看到 `parse_error` 后，先查看对应样本结构，再在 `report_parser.py` 增加通用适配器。
不要针对单一案件硬编码漏洞列表。

## 支持格式

统一入口：`scripts\report_parser.py`

当前支持：

- Word：`.docx`
- 旧 Word：`.doc`（需要 LibreOffice 或 antiword）
- Excel：`.xlsx`、`.xls`
- 表格文本：`.csv`、`.tsv`
- PDF：`.pdf`
- 网页报告：`.html`、`.htm`
- 结构化数据：`.json`
- 纯文本：`.txt`、`.md`
- 日志/配置文本：`.log`、`.out`、`.properties`
- 压缩报告包：`.zip`、`.rar`（递归解析包内支持格式）

解析时同时兼容中英文列名，例如：

- 漏洞名称 / 风险名称 / title / name
- 风险等级 / severity / risk
- 漏洞描述 / description / detail
- 加固建议 / 修复建议 / remediation / solution
- 漏洞地址 / URL / URI

除通用表格解析外，以下报告格式有专项解析器（`report_parser.py`，按实际
样本的结构实现，识别失败时自动落到通用解析，不会误收）：

- **国产代码审计/渗透测试**：编号条目清单（`1、SQL 注入` + 漏洞描述/等级/整改建议）、
  中正检测源代码扫描（缺陷类型 + N例）、深圳网安代码审计（缺陷类型汇总表）
- **Fortify Audit Workbench**：CWE Top 25 导出（按 CWE 分节，名称取官方弱点短名，
  例数取 Package 实例数，等级取实例最高档）；Developer Workbook（Results Outline
  按 `分类 (N issues)` 分块，带 Explanation/Recommendation）
- **Fortify Security Report**：`Category: X (N Issues)` 分节（已有问题数的报告；
  "scan found 0 issues" 的空报告是真零，不是解析失败）
- **HCL AppScan Standard 中文**：摘要表被压成一行文字，按「数字后跟级别字」
  边界拆条，名称里带"中"字不受影响
- **OWASP ZAP**：2.16 PDF（按 `CWE Id/WASC Id/Id` 收尾行切块）与 2.17 HTML
  （`alert-type-counts` 汇总表 + 详情段的 Solution/CVE 标签）
- **Trivy / osv-scanner 文本报告**：组件依赖漏洞表，逐 CVE 出条，
  带已装版本、修复版本和组件名

所有格式归一为：

```json
{
  "name": "漏洞名称",
  "level": "critical|high|medium|low|info",
  "description": "漏洞描述",
  "harm": "漏洞影响",
  "fix_suggestion": "报告自带建议",
  "urls": [],
  "cve": "",
  "cwe": "",
  "source_file": "原附件名"
}
```

## 单案件处理

运行：

```powershell
python scripts\process_issue.py <ISSUE_ID>
```

流程：

1. 下载当前案件所有附件。
2. 对支持格式逐个解析，记录解析成功和失败。
3. 合并同名漏洞，但保留不同报告中的全部建议和来源文件。
4. 对每条漏洞判断为 `code` 或 `non_code`。
5. 按技术层判断责任中心：工程中心或研发中心。
6. 查询内部两条链路：安全池（`sec_kb_bridge.py`）+ 全库（`similar_assist_bridge.py`），
   结果合并去重。
7. 同步检索互联网（非代码漏洞）：与内部检索并行发起，不等内部结果。
8. 输出 enriched JSON 和 Markdown 修复方案。
   - **KB 有命中**：互联网结果追加为补充参考。
   - **KB 无命中**：互联网结果提升为优先建议（排在报告建议之后）。
9. `process_issue.py` 生成 `pending_mcp_publish` 发布请求。
10. 调用钉钉 MCP `get_document_info` 确认目标节点是目录，再调用
   `create_document` 把完整 Markdown 创建到钉钉“项目案例”目录
   `dQPGYqjpJYg0vw9osZbj1mpgWakx1Z5N` 下，取得真实 `nodeId/docUrl`。
10. 调用 `get_document_info` 和 `get_document_content` 回读校验标题、父目录和正文。
12. 校验通过后运行 `finalize_publication.py` 把真实链接写回结果 JSON——发布即交付，不发群机器人通知。

## 内部检索

内部检索有两条链路，**都必须跑，结果合并后按下面的优先级组织**：

### 链路一：安全池检索（`scripts\sec_kb_bridge.py`，优先）

只检索服务器上的安全专用池：tracker_id=26 的安全案件、语义审计回填的漏召案件
（散落在 tracker 1/2/3/7/8/16/22 等，靠 LLM 精判确认，不是关键词猜的）、297 篇已打
安全标记的文档，以及 NVD / GitHub GHSA 外部情报。走安全专用小索引，秒级返回。

```powershell
python scripts\sec_kb_bridge.py "<查询词>" --top-cases 8 --top-docs 5
```

返回结构与全库链路同构，另多一路 `external_intel`：

- `history`：安全案件处理记录，带 `vuln_kind` / `product_line` / `severity_hint` /
  `has_fix_record` / `match_reason` 打标，以及 `tracker_id`（可用于识别"支持类工单里
  夹带的安全案件"）
- `knowledge`：★安全文档（`is_sec_doc=true`）优先
- `external_intel`：CVE 情报，含 `cve_id` / `severity` / `cvss` / `source` / `url` /
  `matched`。`matched` 是这条情报命中的公司关注面组件（由 sec_kb 从安全案件与
  安全文档语料自动派生，不手工维护清单），**只有 `matched` 非空才说明这条 CVE
  与公司实际环境相关**；`matched` 为空表示它只是提问里显式点名了 CVE 编号被带出来的。
  服务端已按关注面过滤：关键词命中的情报不过闸门不会返回。2026-09-24 实测，旧的
  无差别按日期抓取的 530 条情报里只有 43 条与公司组件相关，OpenStack Octavia、
  Moore Threads、nocobase、Suricata 之类一律拦掉；改用关注面定向抓取后，843 条
  情报里 331 条命中，命中组件 Top 为 spring / apache / jenkins / mysql / nginx /
  tomcat / redis / mariadb / jquery / kafka / zookeeper / gitlab / oracle / openssl。

### 链路二：全库检索（`scripts\similar_assist_bridge.py`，补充）

用漏洞名称、CVE、CWE、描述和影响构造查询文本，从 19.9 万工单和 7,700 篇文档中召回，
经 LLM gate 判断真实相关性并提取实际解决操作。覆盖安全池之外的一般性技术问题。

内部结果分两类保存：

- `redmine_history`：历史案件处理记录
- `knowledge_base`：内部知识库文档

两条链路的 `history` / `knowledge` 合并时保留各自来源标记，不得互相覆盖。

不得仅凭标题相似就生成方案；没有 `solution` 的候选不算有效修复建议（两个桥接都已
按此过滤：处理记录少于 8 个字符的候选直接丢弃）。

## 建议优先级

**检索顺序：台账第一**。处理任何漏洞前，先查《安全漏洞台账》多维表
（`scriptsuln_ledger.py lookup`，表"CVE 跟踪"）——CVE 已登记且带
处理方案/状态的，直接沿用台账（来源标记 `ledger`，置顶展示），并跳过
互联网搜索；台账没有的，才走下面的内部检索与搜索兜底。日常 CVE 获取
也以台账为准（`python scriptsuln_ledger.py recent --days 7`）。

每条漏洞按以下顺序组织建议：

0. **安全漏洞台账**登记（状态/修复文档/关联案件），来源标记 `ledger`——
   命中即置顶，且免互联网搜索
1. 当前漏洞报告自带建议，来源标记 `report`
2. **安全池**历史案件的实际处理操作，来源标记 `sec_pool_history`
3. **安全池**文档修复操作，来源标记 `sec_pool_kb`
4. 全库检索到的历史案件处理记录，来源标记 `redmine_history`
5. 全库检索到的内部知识库修复操作，来源标记 `knowledge_base`
6. 外部 CVE 情报（NVD / GHSA），来源标记 `external_intel`——只用于补充漏洞事实
   （CVSS、受影响版本、厂商公告链接），**不算修复建议**，不得凭情报编造修复命令。
   只有 `matched` 非空（命中公司关注面组件）的情报才值得引用；`matched` 为空的
   说明与本环境无关，不要写进报告
7. 互联网公开权威建议，来源标记 `internet`

**KB 未命中特殊规则**：当内部（安全池 + 全库）均无可用修复操作时，互联网建议优先级
提升至第 2 位（紧跟报告建议），由 `apply_web_results.py` 自动处理。

报告建议和内部建议可以同时保留，不互相覆盖。安全池结果优先于全库结果，是因为安全池
的案件带 `vuln_kind` / `severity_hint` / `has_fix_record` 打标，可判断性和可复用性更高；
但全库结果不得因此被丢弃，一般性技术问题（非安全类根因）只有全库能答。

## 代码类分流

以下类型通常属于代码类：

- SQL 注入、XSS、命令注入、RCE
- 反序列化、文件上传、路径穿越
- SSRF、CSRF、越权、IDOR
- 业务逻辑、权限绕过、硬编码密钥

代码类规则：

- 可以保留报告自带建议。
- 可以提供历史案件库或内部知识库找到的修复操作。
- **内部（安全池 + 全库）有可执行方案时**：禁止互联网检索补充，仅用报告原建议和内部知识。
- **内部完全没有可执行方案时**：允许互联网检索作为**兜底**。互联网结果排在报告建议之后、标注
  `priority: kb_empty_primary`；查询词只含通用漏洞名 / CVE / CWE / 组件，禁止发送客户名称、内网地址、
  案件正文或附件内容；只采信厂商官方文档、CVE/CWE/NVD、OWASP 等一手来源。若互联网也无可用结果，
  才写“内部与公开来源均未找到，不提供额外建议”。

## 责任中心分流

- **工程中心**：Nginx、网关、WAF、HTTPS/TLS、安全响应头、Tomcat及中间件
  默认错误页和版本信息等服务器配置。
- **研发中心**：SQL注入、XSS、路径穿越、文件读取、越权、未授权访问、
  敏感信息回显、业务逻辑、接口语义，以及Java/前端应用配置和代码。
- 应用代码规则优先于描述中泛化出现的“服务器”“配置”等词。
- 未命中明确服务器配置规则时，默认交研发中心确认，禁止默认归工程中心。
- 文档必须分别输出“工程中心处理”和“研发中心处理”章节，并给出判定依据。

## 互联网检索（非代码类并行 / 代码类兜底）

触发时机：

- **非代码类**：互联网搜索与内部知识库检索**同步并行发起**，不等待内部结果。
- **代码类**：仅当内部（安全池 + 全库）**无可执行方案时**才触发互联网检索，作为兜底；
  内部有方案则不搜。`recommendation_engine.py` 据此决定 `web_search.required`。
- **报告只给了案情描述**：有些附件（风险告知函、隐患报告）把"利用××漏洞获取××主机权限、
  横向进入××内网"整段当作漏洞名。这类名称截不出可用的漏洞类型词，`_build_web_query`
  直接返回空，`web_search.required` 置为 `false` 并在 `reason` 里说明需人工确认，
  **不发起检索**。此时内部链路照常用完整案情做检索（内部不受此限），人工确认类型后再补搜。

检索结果合并策略：

- **KB 命中**（仅非代码类会出现）：互联网结果追加在内部建议之后，作为补充参考。
- **KB 未命中**：互联网结果提升为优先建议（排在报告建议之后、内部空结果之前），
  `apply_web_results.py` 自动标注 `priority: kb_empty_primary`。代码类走到这里必是 KB 未命中。

搜索时：

- 查询词只包含通用漏洞名称、CVE/CWE 和技术组件。
- 不得发送客户名称、内网地址、案件正文、附件内容或其他内部信息。
- 有 CVE 时查询词只发编号（`CVE-xxxx-xxxx 安全 漏洞 修复 加固 官方建议`），不带报告里的
  漏洞名——名称常夹带案情。没有编号时才用名称：剥掉章节号、等级/状态括号和页码残留，
  取第一句再按逗号切开，超过 40 字截断；切出来仍含"获取/突破/横向/内网/主机/权限/政务"
  这类词的，判定仍是案情描述，整条弃用。
- 优先厂商官方文档、CVE/CWE/NVD、OWASP、IETF、Mozilla、Microsoft、Oracle、
  Apache、Nginx、Spring 等一手来源。
- 每条建议必须记录标题、URL、发布方和访问日期。
- 搜索结果只用于非代码类配置、组件升级、协议和部署加固。

**默认搜索源 anysearch**（`scripts\web_search.py`，国内直连，key 可选）：

```powershell
# 单次搜索
python scripts\web_search.py search "CVE-2024-38819 修复 官方建议"
# 对结果 JSON 里全部待搜漏洞批量生成草稿（每漏洞取1条，可 --limit 控量）
python scripts\web_search.py draft <ID>_enriched.json
```

draft 产出 `_web_results_draft.json`（标记 `draft-unreviewed`），人工或 Agent
审核修订（剔除无关来源、补全建议正文）后，再用 `apply_web_results.py` 合并。
查询词必须使用 `web_search.query` 里引擎已生成的值，不得手工改写夹带案情。

将人工或 Agent 审核后的搜索结果保存为：

```json
[
  {
    "id": 1,
    "title": "来源标题",
    "url": "https://...",
    "publisher": "OWASP",
    "accessed_at": "2026-06-12",
    "suggestion": "可执行的修复操作"
  }
]
```

回填：

```powershell
python scripts\apply_web_results.py <issue_enriched.json> <web_results.json>
```

工具会拒绝向代码类漏洞写入互联网建议。

## 输出与发布

生成文件：

- `<ISSUE_ID>_enriched.json`：完整、可审计的数据
- `<ISSUE_ID>_fix_plan.md`：钉钉文档内容

发布规则：

- 只发布钉钉在线文档，**不发群机器人通知**（通知模块已按需求移除，发布即交付）。
- 默认父目录：
  `https://alidocs.dingtalk.com/i/nodes/dQPGYqjpJYg0vw9osZbj1mpgWakx1Z5N`
  （目录名“项目案例”）。
- 对外输出时必须分别标注：
  - **存放目录**：固定输出上述“项目案例”目录 URL。
  - **修复文档**：输出本次新建文档的真实 URL。
- 修复文档结构参考：
  `https://alidocs.dingtalk.com/i/nodes/AR4GpnMqJzML1Xr9saQ9r6wLVKe0xjE3`，
  至少包含案件链接、漏洞清单、修复总览、分项方案、实施顺序和验证清单。
- 优先直接调用钉钉 MCP `create_document(folderId=<父节点 nodeId>)`；禁止把
  nodeId 猜测或转换为其他 ID。
- 文档发布并回读校验通过后，运行 `finalize_publication.py` 把真实
  `nodeId/docUrl` 写回结果 JSON；不得在未发布、未回读的情况下宣称完成。
- 禁止把本 skill 的产出自动推送到任何群/机器人渠道。

发布并校验后执行：

```powershell
python scripts\finalize_publication.py <ISSUE_ID>_enriched.json `
  --node-id <MCP返回的nodeId> `
  --doc-url <MCP返回的docUrl>
```

发布钉钉文档时，必须真实调用钉钉文档 API。不能像旧版 `main.py` 一样拼接一个
假 URL 冒充发布成功。

文档至少包含：

- 案件链接与附件解析状态
- 漏洞等级和代码/非代码分类
- 当前报告建议
- 安全池历史案件建议及案件链接（含 `vuln_kind` / `severity_hint` 打标）
- 安全池文档建议及文档链接（★安全文档优先）
- 外部 CVE 情报（CVSS / 受影响版本 / 厂商公告链接）
- 全库历史案件建议及案件链接
- 全库知识库建议及文档链接
- 互联网建议及公开来源
- 无建议项及原因
- 修复验证方法

## v2.0：安全案件三源研判与滚动跟踪

> v2.0 在 v1.1.0 案件处理链路之外，新增一条**扫描驱动的三源研判链路**（能力来源：
> security-case-handling，quiz266 T3 40 分提交，config 驱动）。两条链路共用本 skill
> 的配置与钉钉出口；v1.1.0 全部规则不变，下述新能力默认关闭、按需启用。

### 能力与脚本

| 步骤 | 脚本 | 说明 |
|---|---|---|
| 资产台账采集 | `scripts/collect_asset_info.py` | CMDB → 归一化；同 IP 保留最新；owner 一律以台账为准；`--fetch` 需环境变量 CMDB token 且内网放行，否则停止 |
| 扫描结果采集 | `scripts/collect_scanner_results.py` | nessus/openvas/xray 兼容 → 归一化；只读，不触发新扫描 |
| CVE 主动情报（可选） | `scripts/collect_cve_intel.py` | 跨目录引用 `~/.zcode/skills/vuln-response` 的 fetch 脚本（os 分支厂商公告 / software 分支 NVD+GHSA+CNVD），产物经 `VULN_RESPONSE_ARCHIVE_DIR` 重定向到本 skill 的 work 目录；情报 → cve_items 的转换是人工/LLM 研判步骤，不自动转换 |
| 三源融合研判 | `scripts/triage_cases.py` | CVE × 扫描 × 资产 → `risk_score = cvss × 资产关键度 × 暴露面 × EXP系数`，阈值/SLA/去重窗口全在 `config/security_case/triage_rules.json`，改 JSON 不碰代码；cvss 缺失/脏值转人工，融合后 0 案件即停止 |
| 报告+待办+状态 | `scripts/gen_security_report.py` | 产出处置报告（默认【待复核】）、按责任人分组的待办清单、案件状态 JSON；模板在 `assets/security_case_{report,todo}_template.md` |
| 次日滚动跟踪 | `scripts/track_case_state.py` | 读状态文件 + 人工回填 progress → 超期/进行中/待验证/已闭环四类清单与次日提醒 |
| 案件关联（可选） | `scripts/asset_triage_link.py` | `process_issue.py --with-asset-triage --triage-cases <cases.json>` 时，把三源案件按 CVE 关联回 enriched 结果并追加到 fix_plan.md；默认关闭，关闭时 v1.1.0 行为不变 |

### 标准运行序列（离线样例可直接跑通）

```powershell
python scripts/collect_asset_info.py --file tests/fixtures/security_case/sample_asset.json --date 2026-09-22
python scripts/collect_scanner_results.py --file tests/fixtures/security_case/sample_scan.json --date 2026-09-22
# CVE 情报：真实抓取用 collect_cve_intel.py（出站）；离线样例用 tests/fixtures/security_case/sample_cve.json
python scripts/triage_cases.py --cve <cve_items.json> --scan <scan.json> --asset <asset.json> --date 2026-09-22
python scripts/gen_security_report.py --cases work/security_case/output/cases_<date>.json --date <date>
# 次日：
python scripts/track_case_state.py --date <date+1> --state work/security_case/output/case_state_<date>.json --progress <progress.json>
```

### 配置与产物位置

- 规则配置：`config/security_case/{asset,scanner,notify,triage_rules,cve_intel}.json`——只写
  环境变量引用名，禁止写入真实 Key/Token；"换项目只改配置"即改这些 JSON。
- 运行期产物：`work/security_case/{cache,output,progress}/`（已 gitignore，不入库）。
- 测试：`tests/test_security_case_triage.py`、`tests/test_security_case_report_track.py`
  （合成 fixture，不连真实 Redmine/钉钉）。

### v2.0 新增停止条件

1. CMDB/扫描器 `--fetch` 缺环境变量凭证或未获内网放行 → 输出 gap 停止，不猜测不兜底。
2. 三源融合后 0 有效案件 → 停止；如属正常无风险场景，须在报告中显式写明【无有效案件】并经人工确认后归档。
3. 台账外资产命中 → 不定责不推送，进"未定责清单"等人工确认归属。
4. 报告默认【待复核】；推送必须经人工复核，且先推测试目标
   （`config/security_case/notify.json` 的 allowed_targets），确认真实目标前禁止推真实群。
5. CVE 情报未经研判转换成 cve_items 前，不得直接喂 triage 当作已研判结论。

## 安全约束

- 不把内部案件内容发送到互联网搜索服务。
- 不把数据库、Redmine、钉钉或 LLM 密钥写入输出。
- 不编造相似案件、知识库文档、CVE、修复命令或发布链接。
- 下载的历史附件只存放在归档目录，不提交到 Git。
- 当前案件报告是漏洞事实来源；历史资料只用于补充修复方法，不能改变漏洞事实。
