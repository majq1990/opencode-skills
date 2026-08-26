---
name: redmine-security-auto-fix
version: 1.1.0
author: majianquan
license: MIT
category: support-dept
visibility: tech-manager
description: Redmine 安全案件自动化处理与修复建议检索。凡涉及 Redmine 安全案件、漏洞报告解析、历史安全案件学习、相似漏洞修复方案、代码/非代码修复分流、钉钉知识库归档或安全漏洞自动修复，都应使用本 Skill。它兼容多种漏洞报告格式，优先检索 redmine-similar-assist 的历史案件库和钉钉知识库，非代码类始终并行检索互联网，代码类仅在内部无可执行方案时才用互联网兜底。
---

# Redmine 安全案件自动化处理

## 目标

把当前 Redmine 安全案件的附件作为漏洞事实来源，但不把报告里的建议视为唯一答案。流程需要：

1. 兼容不同厂商、不同结构的漏洞报告。
2. 保留当前报告自带的全部加固建议。
3. 优先从 `redmine-similar-assist` 的历史案件库和钉钉知识库查找实际修复操作。
4. 非代码类漏洞内部无匹配时，检索互联网公开权威来源。
5. 代码类漏洞只允许使用当前报告和内部知识；内部无结果时不额外提供建议。
6. 每条建议标明来源，不能把推测包装成历史事实。

## 依赖

- `D:\git\redmine-similar-assist`
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
6. 查询历史案件库与钉钉知识库。
7. 同步检索互联网（非代码漏洞）：与内部检索并行发起，不等内部结果。
8. 输出 enriched JSON 和 Markdown 修复方案。
   - **KB 有命中**：互联网结果追加为补充参考。
   - **KB 无命中**：互联网结果提升为优先建议（排在报告建议之后）。
9. `process_issue.py` 生成 `pending_mcp_publish` 发布请求。
10. 调用钉钉 MCP `get_document_info` 确认目标节点是目录，再调用
   `create_document` 把完整 Markdown 创建到钉钉“项目案例”目录
   `dQPGYqjpJYg0vw9osZbj1mpgWakx1Z5N` 下，取得真实 `nodeId/docUrl`。
10. 调用 `get_document_info` 和 `get_document_content` 回读校验标题、父目录和正文。
12. 校验通过后运行 `finalize_publication.py` 写回真实链接并推送机器人通知。

## 内部检索

使用 `scripts\similar_assist_bridge.py`：

1. 用漏洞名称、CVE、CWE、描述和影响构造查询文本。
2. 使用 `redmine-similar-assist` 的 Embedding。
3. 从历史案件向量库召回相似案件。
4. 从钉钉文档向量库召回相关知识。
5. 使用其 LLM gate 判断真实相关性并提取实际解决操作。

内部结果分两类保存：

- `redmine_history`：历史案件处理记录
- `knowledge_base`：内部知识库文档

不得仅凭标题相似就生成方案；没有 `solution` 的候选不算有效修复建议。

## 建议优先级

每条漏洞按以下顺序组织建议：

1. 当前漏洞报告自带建议，来源标记 `report`
2. 相似历史案件的实际处理操作，来源标记 `redmine_history`
3. 内部知识库修复操作，来源标记 `knowledge_base`
4. 互联网公开权威建议，来源标记 `internet`

**KB 未命中特殊规则**：当内部知识库无可用修复操作时，互联网建议优先级
提升至第 2 位（紧跟报告建议），由 `apply_web_results.py` 自动处理。

报告建议和内部建议可以同时保留，不互相覆盖。

## 代码类分流

以下类型通常属于代码类：

- SQL 注入、XSS、命令注入、RCE
- 反序列化、文件上传、路径穿越
- SSRF、CSRF、越权、IDOR
- 业务逻辑、权限绕过、硬编码密钥

代码类规则：

- 可以保留报告自带建议。
- 可以提供历史案件库或内部知识库找到的修复操作。
- **内部（历史案件 + 知识库）有可执行方案时**：禁止互联网检索补充，仅用报告原建议和内部知识。
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
- **代码类**：仅当内部（历史案件 + 知识库）**无可执行方案时**才触发互联网检索，作为兜底；
  内部有方案则不搜。`recommendation_engine.py` 据此决定 `web_search.required`。

检索结果合并策略：

- **KB 命中**（仅非代码类会出现）：互联网结果追加在内部建议之后，作为补充参考。
- **KB 未命中**：互联网结果提升为优先建议（排在报告建议之后、内部空结果之前），
  `apply_web_results.py` 自动标注 `priority: kb_empty_primary`。代码类走到这里必是 KB 未命中。

搜索时：

- 查询词只包含通用漏洞名称、CVE/CWE 和技术组件。
- 不得发送客户名称、内网地址、案件正文、附件内容或其他内部信息。
- 优先厂商官方文档、CVE/CWE/NVD、OWASP、IETF、Mozilla、Microsoft、Oracle、
  Apache、Nginx、Spring 等一手来源。
- 每条建议必须记录标题、URL、发布方和访问日期。
- 搜索结果只用于非代码类配置、组件升级、协议和部署加固。

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

通知规则：

- 默认先发布钉钉在线文档，再发送机器人通知。
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
- 文档发布失败时必须中止通知；禁止发送缺少真实文档链接的“成功通知”。
- 通知内容包含案件链接、漏洞数量、风险等级统计和真实钉钉文档链接。
- 机器人 Webhook、加签密钥和关键词统一读取
  `redmine-similar-assist\config.yaml` 的 `notify` 段。
- 不允许在 `process_issue.py` 本地生成结束后直接通知。

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
- 历史案件建议及案件链接
- 知识库建议及文档链接
- 互联网建议及公开来源
- 无建议项及原因
- 修复验证方法

## 安全约束

- 不把内部案件内容发送到互联网搜索服务。
- 不把数据库、Redmine、钉钉或 LLM 密钥写入输出。
- 不编造相似案件、知识库文档、CVE、修复命令或发布链接。
- 下载的历史附件只存放在归档目录，不提交到 Git。
- 当前案件报告是漏洞事实来源；历史资料只用于补充修复方法，不能改变漏洞事实。
