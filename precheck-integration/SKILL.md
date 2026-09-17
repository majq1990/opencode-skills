---
name: precheck-integration
version: 1.0.0
description: 对接前置避坑助手。用户准备启动一个对接业务时（数据/视频/接口/三方系统集成），用一句业务描述自动查询公司 17 万历史 Redmine 工单 + 4500 篇钉钉知识库文档，聚类输出 top N 高频踩坑模式 + 典型案件链接 + 文档参考 + 避坑建议。触发词：对接前置 / 对接避坑 / 对接踩坑 / 启动对接 / precheck / 帮我看看做xx对接历史问题 / xx对接有什么坑 / 历史相似对接 / 对接经验。
author: majianquan
category: support-dept
visibility: support-dept
---

# 对接前置避坑助手（precheck）

业务人员准备启动一个对接业务（GPS/视频/数据库/三方系统/支付）前，**一句业务描述**自动从公司历史 Redmine 工单库 + 钉钉知识库聚类高频踩坑，提前规避。

## 触发时机

**必须触发**：用户说类似下面任一句式，立即调本 skill。
- "做 xx 对接，历史上有什么坑？"
- "我要做 xx 接入，帮我查一下相似案件"
- "对接 xx 业务前置避坑"
- "做 xx 协议对接想知道之前踩过什么问题"
- "/precheck xx 业务描述"

**不要触发**：
- 单纯查询某个具体工单（用 redmine MCP 或直接 issue 链接）
- 实时故障排查（用现有相似案件 AI 一楼工具，自动写楼）
- 与对接无关的闲聊

## 必备前置：业务描述足够具体

调用前确认用户描述**包含至少一个**：
- 产品/系统名（GPS/视频/支付/三方系统/物联网设备）
- 协议（808/HTTP/MQTT/库表同步/TCP）
- 业务场景（车辆轨迹/政务网/支付回调）

若描述太短（< 10 字）或太泛（"做个对接"/"接个数据"），**先反问用户补充**：
> "请告诉我具体的：① 对接什么数据（GPS轨迹/视频/业务表）；② 用什么协议（808/HTTP/库表）；③ 三方系统是谁。"

## 调用方式

```bash
curl -sS -m 180 -X POST https://demo.egova.com.cn/redmine-assist/precheck \
  -H "Content-Type: application/json" \
  -H "X-Precheck-Token: 4bcf27f056979d06bcfb14725680cc64" \
  -d '{"description": "<用户的完整业务描述>"}'
```

或 PowerShell：

```powershell
$body = @{description = "<用户的完整业务描述>"} | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "https://demo.egova.com.cn/redmine-assist/precheck" `
  -Headers @{"X-Precheck-Token"="4bcf27f056979d06bcfb14725680cc64"; "Content-Type"="application/json"} `
  -Body $body -TimeoutSec 180
```

## 响应处理

接口返回：
```json
{
  "markdown": "## 对接前置避坑提示\n\n基于历史 30 条相似工单...",
  "items": [
    {"title": "...", "count": 3, "case_ids": [...], "doc_refs_with_url": [...], "advice": "..."}
  ],
  "stats": {"n_issues": 30, "n_docs": 10, "n_clusters": 5, "elapsed_ms": 45000}
}
```

**直接把 `markdown` 字段完整原样**给用户看，**不要改写、不要总结、不要省略 [#case_id](url) 链接**——用户能点过去看真实工单详情。

可以补一句简短开场，例如：
> "已基于公司 17 万历史工单查询，约 45 秒，以下是 N 个常见的坑："

## 性能 / 限制

| 项 | 数值 |
|---|---|
| 端到端延迟 | **45-60 秒**（含 LLM 推理）|
| token 上限 | description ≤ 4000 字符 |
| 召回池 | 限"实际故障"5 类 tracker：支持/BUG/适配/安全/性能（共 5.3 万工单）|
| 知识库 | 钉钉公司知识库 4500 篇文档（按 chunk 切片召回）|

## 错误处理

| HTTP | 含义 | 行为 |
|---|---|---|
| 200 | 成功 | 返回 markdown |
| 400 | description 缺失/超 4000 字 | 提示用户补描述 |
| 401 | token 失效 | 检查 X-Precheck-Token，可能需联系马健权重新生成 |
| 503 | 服务在 cold load（重启后 ~8 min） | 提示用户"系统正在加载向量库，请 8 分钟后重试" |
| 500 | 服务端错误 | 联系运维看 `docker logs redmine-assist` |

## 典型使用示例

**用户输入**：
> 我要做车载GPS轨迹对接，对方使用808协议走TCP推送，已知现场是政务网+互联网双网环境

**Skill 行为**：
1. 描述具体度足够 ✓
2. 调用 precheck API
3. 拿到 markdown 完整返回，包含：
   - 第 1 类: 网络端口/防火墙配置（3 次） + 案件 #504431 #466157
   - 第 2 类: 服务版本/部署异常（3 次） + 案件 #352367 #418852
   - 第 3 类: 协议/报文乱码（4 次） + 案件 #418852 #432828
   - 第 4 类: 坐标系偏移（3 次） + 案件 #387531
   - 文档参考：[车载对接Wiki] [车载轨迹综合指南]

## 鉴权 token 管理

- 当前 token: `4bcf27f056979d06bcfb14725680cc64`（demo:/etc/redmine-assist/precheck_token）
- 轮换：运维 `openssl rand -hex 16` 生成新 token，同步改 nginx `/etc/nginx/conf.d/default.conf` 中 `if ($http_x_precheck_token != "..."` 行 + reload nginx，然后改本 skill。

## 相关基础设施

| 项 | 值 |
|---|---|
| 代码仓库 | `D:\git\redmine-similar-assist`（GitHub: github.com/majq1990/redmine-similar-assist）|
| 部署 | `demo.egova.com.cn:/opt/redmine-assist/`（docker 容器 `redmine-assist`）|
| 核心模块 | `src/precheck.py`（双路 KNN + LLM 聚类）|
| 故障 tracker | `{3, 1, 22, 26, 27}` (支持/BUG/适配/安全/性能) |
| LLM | DeepSeek `deepseek-v4-flash`（注意 reasoning_content 占 max_tokens，已用 12000）|
| Embedding | SiliconFlow `BAAI/bge-m3` 1024 维 |

## 维护者

马健权（北京数字政通 - 工程技术中心 - 技术支持部）

---

*本 skill 复用 redmine-similar-assist 的 precheck 接口，由 Claude Code 调用。*
