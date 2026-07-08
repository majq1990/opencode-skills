---
name: zhengtong-knowledge-query
version: 1.0.0
description: 政通问答助手。从公司 17 万历史 Redmine 工单（排除内部流程类）+ 4500 篇钉钉知识库文档中检索方案和经验，一句自然语言问题即返回综合答案 + 参考来源。适用于日常查资料、找方案、了解产品/模块实施经验、检索公司内部技术要点。触发词：政通问答 / xx怎么做 / xx有什么方案 / 帮我查一下 / 历史上怎么处理 / 查公司资料 / 找方案 / zhengtong_query / knowledge_query。
author: majianquan
category: global
visibility: global
---

# 政通问答助手（zhengtong-knowledge-query）

用一句自然语言问题从公司历史工单库 + 钉钉知识库检索方案和经验，AI 综合返回 **答案 + 参考来源**。

## 触发时机

**必须触发**：用户提出**技术/产品/实施**类问题，且问题涉及公司内部产品/模块/流程时。

典型触发例句：
- "麒舰第三方对接怎么做鉴权？"
- "星桥数据接入 SQL 脚本怎么写？"
- "悟空大屏组件数据源配置方法"
- "eUrbanMIS 部署前需要准备什么？"
- "灵珑证书批量导出怎么做？"
- "公司历史上 xx 问题是怎么处理的？"
- "查一下 xx 模块的资料"

**不要触发**：
- 通用编程/算法问题（用 Web 搜索）
- 需求确认类（"帮我做一个 xx" → 用 executor agent）
- 实时故障排查具体工单（用现有相似案件 AI 一楼工具，自动写楼）
- 对接**启动前**避坑（用 precheck-integration skill 更专业）

## 与 precheck-integration 的边界

| skill | 场景 | 输入形式 |
|---|---|---|
| **precheck-integration**（对接前置避坑）| 启动**新对接**业务前的踩坑扫描 | "我要做 xx 对接..." |
| **本 skill (zhengtong-knowledge-query)** | 日常查公司资料 | "xx 怎么做/xx 是什么" |

用户问题以「我要做 / 我准备做 / 启动 / 上线」+ 对接 起头 → 用 precheck-integration；
其他技术问题（怎么做/怎么配/什么方案/资料）→ 用本 skill。

## 必备前置：问题足够具体

调用前确认问题**至少包含一个**：产品名（麒舰/星桥/悟空/灵珑/eUrbanMIS/毕升/毕昇）、模块名、技术关键词。

若问题过短（< 6 字）或过泛（"怎么做"、"有什么资料"），**先反问**：
> "请补充具体的产品/模块/技术关键词，例如：'麒舰第三方对接怎么做鉴权' 比 '对接怎么做' 更好。"

## 调用方式

```bash
curl -sS -m 180 -X POST https://demo.egova.com.cn/redmine-assist/query \
  -H "Content-Type: application/json" \
  -H "X-Precheck-Token: 4bcf27f056979d06bcfb14725680cc64" \
  -d '{"query": "<用户的完整问题>"}'
```

或 PowerShell：
```powershell
$body = @{query = "<问题>"} | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "https://demo.egova.com.cn/redmine-assist/query" `
  -Headers @{"X-Precheck-Token"="4bcf27f056979d06bcfb14725680cc64"; "Content-Type"="application/json"} `
  -Body $body -TimeoutSec 180
```

## 响应处理

接口返回：
```json
{
  "markdown": "## 政通问答\n\n> **问题**: ...\n\n<答案 200-400 字>\n\n---\n\n### 相关工单（N 条）\n- [#xxx 标题](url) ...\n\n### 相关文档（N 篇）\n- [标题](url) ...",
  "stats": {"n_issues": 15, "n_docs": 10, "elapsed_ms": 42000}
}
```

**直接把 `markdown` 字段完整原样**给用户看，**保留所有 [#号] 案件链接和文档链接**，用户能点过去看历史详情。

可以补一句简短开场：
> "已从公司历史工单+知识库检索，以下是综合答案："

## 召回池说明

- **保留**：支持/BUG/开发/更新/适配/安全/性能/低代码配置/内部系统开发/文档/运维 等（约 **12 万工单**）
- **排除**：需求/代码审核/UI设计/里程碑/日常/产品设计（纯流程类工单）
- **文档**：钉钉公司知识库 **4500 篇**（按 chunk 切片召回）

## 性能 / 限制

| 项 | 数值 |
|---|---|
| 端到端延迟 | **40-60 秒**（含 LLM 推理）|
| query 上限 | ≤ 4000 字符 |
| 答案长度 | 200-400 字（LLM 严格控制）|

## 错误处理

| HTTP | 含义 | 行为 |
|---|---|---|
| 200 | 成功 | 返回 markdown |
| 400 | query 缺失/超 4000 字 | 提示补/精简 |
| 401 | token 失效 | 联系马健权重新生成 |
| 503 | 服务在 cold load（重启后 ~8 min）| 提示"系统正在加载，请 8 分钟后重试" |
| 500 | 服务端错误 | 联系运维 |

## 使用示例

**用户输入**：
> 麒舰第三方对接怎么做鉴权？

**Skill 返回（示意）**：
```markdown
## 政通问答
> **问题**：麒舰第三方对接怎么做鉴权？

麒舰对接第三方鉴权目前有 3 种主流方式：**① OAuth2 Code Flow**（用户跨系统跳转推荐）
**② API Key + HMAC 签名**（服务器间调用）**③ IP 白名单 + 内网互访**（政务内网）。

**关键要点**：
- OAuth 走 sso.egova/dingding 流程，token 24 小时
- HMAC 用 SHA-256，请求头含 timestamp+nonce+signature
- IP 白名单需运维协作，仅限 VPN/专线

---

### 相关工单（6 条）
- [#XXX 麒舰第三方鉴权规范]() — 定义 OAuth code flow
- [#XXX 星桥 HMAC 示例]() — 参考签名代码
...

### 相关文档（3 篇）
- [麒舰对接开发指南]() — 官方文档
...
```

## 鉴权 token

- 当前 token: `4bcf27f056979d06bcfb14725680cc64`（同 precheck）
- 存放：`demo:/etc/redmine-assist/precheck_token`
- 轮换：改 token 后同步改 nginx `if ($http_x_precheck_token != "..."` + reload

## 相关基础设施

| 项 | 值 |
|---|---|
| 代码仓库 | `D:\git\redmine-similar-assist`（GitHub: majq1990）|
| 核心模块 | `src/query.py:run_query()`（双路 KNN + LLM 精排+摘要）|
| 排除的 tracker | `{2, 20, 18, 15, 7, 17}`（需求/代码审核/UI/里程碑/日常/产品设计）|
| LLM | DeepSeek `deepseek-v4-flash`（max_tokens=8000 应对 reasoning_content）|
| Embedding | SiliconFlow `BAAI/bge-m3` 1024 维 |

## 维护者

马健权（北京数字政通 - 工程技术中心 - 技术支持部）

---

*本 skill 通过 HTTP 调用 demo:/opt/redmine-assist 的 /query 接口。*
