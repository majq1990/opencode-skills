---
name: xinchuang-migration
description: 信创（信息技术应用创新）数据库迁移/国产化适配一站式知识库检索与问题处理。覆盖达梦/人大金仓/瀚高/海量/麒麟/欧拉/UOS/金蝶/Apusic/东方通/TongWeb/CPU适配/星桥/灵珑/毕升/明镜等场景，触发词：信创迁移/国产化迁移/数据库迁移/达梦迁移/人大金仓迁移/瀚高迁移/海量迁移/麒麟部署/欧拉部署/UOS部署/国产中间件/国产化适配/信创环境部署/信创改造/国产CPU适配/鲲鹏/飞腾/海光/金蝶/Apusic/东方通/TongWeb/明镜迁移/毕升迁移/星桥迁移/灵珑信创/麒舰信创。
---

# 信创迁移

信创（信息技术应用创新）数据库迁移 / 国产化适配一站式知识库检索与问题处理 skill。
**检索架构：skill → MCP（`zhengtong_query` / `precheck`）→ demo redmine-assist → live vectors.db**（知识库每次同步后自动最新，skill 无需改动）。
覆盖达梦/人大金仓/瀚高/海量/麒麟/欧拉/UOS/金蝶(Apusic)/东方通(TongWeb)/CPU 适配等场景。

## 触发词

信创迁移 / 国产化迁移 / 数据库迁移 / 达梦迁移 / 人大金仓迁移 / 瀚高迁移 / 海量迁移 / 麒麟部署 / 欧拉部署 / UOS 部署 / 国产中间件 / 国产化适配 / 信创环境部署 / 信创改造 / 国产CPU适配 / 鲲鹏 / 飞腾 / 海光 / 金蝶 / Apusic / 东方通 / TongWeb / 明镜迁移 / 毕升迁移 / 星桥迁移 / 灵珑信创 / 麒舰信创

## 工作流

1. **场景识别**：把用户问题归到以下场景之一（见下表）
2. **知识库检索**：调 demo /query 接口（多角度关键词），返回工单 + 文档链接
3. **方案输出**：内置手册给出通用步骤 + 检索结果中的产品专项说明
4. **兜底**：手册无法覆盖 → 直连 vectors.db 精确检索（SQL 示例见 scripts/query_xc.py）
5. **互联网搜索兜底**：知识库 + vectors.db 均无结果 → 调 `anysearch` / `websearch` 搜索（关键词 + "金蝶中间件" / "东方通" / "信创迁移" / 产品名），补充最新方案或厂商文档

## 兜底策略优先级

| 优先级 | 手段 | 适用条件 |
|---|---|---|
| 1 | 内置手册速查 | 通用常见问题 |
| 2 | MCP `zhengtong_query` / `precheck` | 知识库最新同步数据 |
| 3 | 直连 vectors.db SQL | 个性化/罕见报错 |
| 4 | 互联网搜索（anysearch / websearch） | 以上均无结果，搜厂商文档/最新方案 |

## 场景路由

| 用户问题关键词 | 路由场景 | 内置手册章节 |
|---|---|---|
| 达梦 / DM8 / dameng | MySQL→达梦 | B |
| 人大金仓 / Kingbase / 金仓 / KES | MySQL→金仓 | C |
| 瀚高 / HighGo | MySQL→瀚高 | D |
| 海量 / Vastbase | MySQL→海量 | E |
| 星桥 + 迁移 | 星桥专项 | F.星桥 |
| 灵珑 + 迁移 | 灵珑专项 | F.灵珑 |
| 毕升 + 迁移 | 毕升专项 | F.毕升 |
| 明镜 + 迁移 | 明镜专项 | F.明镜 |
| 用户中心 + 迁移 | 用户中心2.0 | F.用户中心 |
| 全行业 + 切换 | 全行业一体化 | F.全行业 |
| 麒麟 / 欧拉 / UOS + 部署 | OS 部署 | G |
| 金蝶 / Apusic 中间件 | 金蝶中间件 | I.金蝶 |
| 东方通 / TongWeb 中间件 | 东方通中间件 | I.东方通 |
| 鲲鹏 / 飞腾 / 海光 / ARM | CPU 适配 | G |
| 泛信创迁移 / 多产品 | 总览 + 逐个细化 | A |

## 知识库检索（优先 MCP，降级 REST）

架构：`skill → MCP zhengtong_query → live vectors.db`（知识库每次 sync/backfill 后自动更新，skill 无需改动）。

### MCP 模式（推荐）
调用 demo 上 redmine-assist 的 MCP 服务（`/mcp`，JSON-RPC 2.0 streamable-http），使用 `zhengtong_query` 工具：
```
tools/call
  name: "zhengtong_query"
  arguments: { "query": "<用户问题>" }
```
或 `precheck`（对接前置避坑，更适合"我要做 xx 迁移"类启动前扫描）：
```
tools/call
  name: "precheck"
  arguments: { "description": "<业务描述，含产品/协议/三方系统>" }
```
MCP 工具返回结构同 /query（markdown + stats），且自动处理编码/双路 KNN/LLM 精排。

### REST 降级（脚本模式）
无 MCP 客户端时用 /query REST：
```powershell
python scripts/query_xc.py "灵珑迁移到达梦后视图查询报错怎么处理"
python scripts/query_xc.py --sweep "达梦 迁移" --out D:\opencode\file\2026-09-08\xc_demo_result
```
参数：`--host`（默认 https://demo.egova.com.cn/redmine-assist）、`--token`、`--out`、`--timeout`。

### 限速与错误
| HTTP | 含义 | 处理 |
|---|---|---|
| 200 | 成功 | 返回 markdown |
| 400 | query 缺失/超 4000 字 | 精简问题重试 |
| 401 | token 失效 | 联系马健权 |
| 503 | cold load（重启后 ~8 min）| 8 分钟后重试 |
| 500 | 服务端错误 | 联系运维 |

端到端延迟 40-60 秒（含 LLM 推理）。

## 兜底：MCP / 直连 / 互联网搜索

- **日常走 MCP**（`zhengtong_query` / `precheck`），永远拿到最新同步的 vectors.db
- **仅应急调试时直连 vectors.db**（SSH 到 demo）：
```bash
sqlite3 /opt/redmine-assist/data/vectors.db "SELECT issue_id,subject,status,updated_on FROM issues_meta WHERE subject LIKE '%达梦%' ORDER BY issue_id DESC LIMIT 50;"
sqlite3 /opt/redmine-assist/data/vectors.db "SELECT title,url FROM docs_meta WHERE title LIKE '%迁移%' ORDER BY title LIMIT 30;"
sqlite3 /opt/redmine-assist/data/vectors.db "SELECT node_id,heading,substr(text,1,200) FROM doc_chunks_meta WHERE text LIKE '%达梦%' LIMIT 40;"
```
- **互联网搜索兜底**：以上均无结果时，用 `anysearch` / `websearch` 搜索（关键词组合：产品名 + "信创迁移"/"国产化"/"中间件" + 具体问题），补充厂商文档、最新方案或社区方案。
  - 各厂商官网/社区：达梦 https://www.dameng.com/ · 社区 https://eco.dameng.com/ | 金仓 https://www.kingbase.com.cn/ · 社区 https://bbs.kingbase.com.cn/ | 瀚高 https://www.highgo.com/ | 海量 https://docs.vastdata.com.cn/ | 金蝶 https://www.kingdee.com | 东方通 https://www.tongweb.com.cn
  - 搜索结果用 `anysearch_extract` 抓取详情页全文。

## 参考文件

- `references/migration-playbooks.md` — 常见迁移问题处理手册（A~J 章）
- `references/knowledge-index.md` — 知识索引（130 篇文档 + 精选工单 + 钉钉链接）
- `references/knowledge-index-docs.md` — 130 篇文档完整分类清单
- `references/key-docs-fulltext.md` — 23 篇关键文档全文（迁移步骤/报错处理/SQL）
- `scripts/query_xc.py` — 查询脚本
- `references/robot-integration.md` — 信创迁移 × 工程中心应答机器人 集成方案（含修改后完整机器人定义）
