# HANDOFF：节后接续说明（写于 2026-09-22，节前窗口）

## 当前状态（一句话）

redmine-security-auto-fix v2.0 三源研判链路已在本地 feature 分支完成开发、测试、
端到端冒烟并提交；**分支已推送 GitHub**（2026-09-24 补推成功，SSH 直连可用，
`feat/security-case-response-v2` → origin，可开 PR）。

## 分支与提交

- 仓库：`D:\git\opencode-skills`（本地裸仓备份 + GitHub 远程）
- 分支：`feat/security-case-response-v2`
- 提交：`83e505b` feat(redmine-security-auto-fix): v2.0 安全案件三源研判与滚动跟踪
  （25 文件，+2413 行；范围已用 `git show --name-status` 复核，仅 redmine-security-auto-fix 下）
- 工作区状态：分支上除提交内容外，还有**与本任务无关的既有未提交修改**
  （dingtalk-aisearch 等 4 个文件的 M 状态，早于本任务存在）——不要动它们，也不要卷进本任务的后续提交。

## 2026-09-24 追加：内部检索接入服务器安全池（sec_kb）

v1.1/v2.0 的内部检索原先只有全库一条链路（`similar_assist_bridge.py`），不区分安全与非
安全。现在服务器上有了安全专用池，本 skill 改为两条链路并行、按优先级合并。

**服务器侧**（`demo.egova.com.cn`，代码 `/opt/redmine-assist/code/scripts/sec_kb`，
随 `/app` bind mount 生效，无需重建容器；**服务器那份是唯一权威副本**，本机开发副本在
`D:\opencode\file\2026-09-23\sec_kb\`，改动后需 scp 回服务器再进容器验证）：

- 安全池规模：9,000+ 安全案件（tracker 26 + 关键词 + LLM 精判回填的漏召案件）、
  297 篇★安全文档、843 条 NVD/GHSA 情报（其中命中公司关注面 331 条）
- 安全专用小索引（faiss），快路径秒级；全库 faiss 冷启动约 12 分钟，故定时任务只做
  采集与索引重建
- cron：每日增量采集 + 每日关注面重建 + 每日情报；每周一 05:00 语义审计 → LLM 精判
  → 回填 → 重建索引，06:00 NVD 关注面全量补齐（`/etc/cron.d/sec_kb`）
- `sec_query(..., structured=True)` 附带 `cases` / `docs` / `intel` 原始列表，
  召回口径（阈值、★文档优先、按 node_id 去重）只在 sec_kb 侧实现一份

**skill 侧新增/改动**：

| 文件 | 改动 |
|---|---|
| `scripts/sec_kb_bridge.py` | 新增。ssh + docker exec 只读调用安全池；返回结构与 `similar_assist_bridge` 同构，另多 `external_intel`；不可达时返回 `_error` 并降级为仅全库 |
| `scripts/recommendation_engine.py` | 新增 `merge_internal()` 与 `_SOURCE_ORDER`；`enrich_all(with_sec_pool=True)` 并行跑两条链路；建议序列按「报告 → sec_pool_history → sec_pool_kb → redmine_history → knowledge_base → internet」排序 |
| `SKILL.md` | 「内部检索」改为双链路；「建议优先级」加入 sec_pool 两类与 external_intel；「依赖」「单案件处理」「文档结构」同步 |
| `tests/test_recommendation_policy.py` | 新增 3 个用例：合并顺序、情报不算修复建议、安全池失败降级。全套 31 passed |

**实测**（2026-09-24，"Nacos 未授权访问漏洞"）：两条链路都通，合并出 9 条 sec_pool_history
+ 5 条 sec_pool_kb + 2 条 redmine_history，命中真实 Nacos 升级脚本与「未鉴权接口安全配置」
wiki；`web_search.required=False`（代码类已有内部方案，按红线不搜互联网）。

**外部情报的正确用法**：`external_intel` 只补充漏洞事实（CVSS、受影响版本、厂商公告
链接），不得当作修复建议、不得凭情报编造修复命令。见下一节关注面闸门。

## 2026-09-24 再追加：外部情报改为「关注面定向」，闸门挡掉无关 CVE

**问题**：初版情报采集是"NVD 最近 N 天 + GHSA critical/high"全量拉取，攒下 504 条后
实测公司环境关注的 tomcat / nginx / redis / mysql / nacos / kafka / log4j / spring /
openssl **命中数全为 0**，Top1 是 mcp-atlassian（17 条）——这个池子对使用者 100% 是
噪声。根因是抓取口径没有靶子。

**做法**：新增 `sec_kb/watchlist.py`，从安全案件主题 + 安全文档标题（9,361 条）反推
公司真实在跑的第三方组件，用它同时管两头——抓取时当 NVD `keywordSearch` 的关键词，
查询时当情报闸门（`query` 的 `intel` 段只返回 `matched` 非空的情报）。

- 关注面 121 项 = 语料派生 46（命中次数 ≥3）+ 种子 75 + 中文 12（达梦/人大金仓/统信…）
- 三层停用词：常规英文、漏洞类型/语言/协议词（websocket/grpc/jwt…）、公司内部词
  （mis/seninfo/egova/灵珑/麒舰…）。协议词单列：公司确实在用，但任意 CVE 里都会出现
- 版本后缀折叠（`fortify23`→`fortify`）、连字符删除（`element-ui`→`elementui`，
  否则切词后永远匹配不上）、别名组（`org.springframework`→`spring`，`XXL-JOB`→`xxljob`）
- 别名组用显式表不用前缀放宽：放宽会让 `consul` 命中 `consult`、`boot` 命中 `bootstrap`；
  组里不放 `element`——NVD 固定句式 "The affected element is an unknown function"
  实测在 530 条里混进 14 条无关产品，已删
- 相关性在查询时实时计算，关注面刷新后历史情报的判定随之改变，无需重新采集

**实测**：

| 口径 | 情报总量 | 闸门放行 | 命中组件 Top |
|---|---|---|---|
| 改造前（按日期/严重级别全拉） | 530 | 43（8.1%） | — |
| 改造后（关注面定向抓取） | 843 | 331（39.3%） | spring 93 / apache 53 / jenkins 53 / mysql 41 / nginx 30 / tomcat 29 |

被拦掉的典型：OpenStack Octavia 提权、Moore Threads 驱动、nocobase SQL 注入、
Suricata、OpenPanel、mcp-atlassian。NVD 定向抓取实测 25 个关键词 → scanned 342 /
written 337 / errors 0（受 5 req/30s 限速约束，60 词约 13 分钟）。

**skill 侧改动**：`sec_kb_bridge.py` 的 `external_intel` 透传 `matched`；
`SKILL.md` 建议优先级第 6 位明确"只有 `matched` 非空才值得引用"。
服务器自测 `python /app/data/wl_selftest.py`（5 节全通过）。

**已核验不可行**：把 `sec_intel` 推送到 `vuln-response` 的钉钉「安全漏洞台账」AI 表格。
该表要求 `[修复]|[验证]|[公告]` 三段式，修复命令必须来自厂商公告，而 NVD/GHSA 情报
不带逐操作系统补丁命令，凭情报编造即违反 skill 红线；且 504 条情报命中公司 OS 的为 0，
强行写入只会把第三方库 CVE 灌进一张操作系统台账。README 相应段落已改写。

## 节后第一步（按顺序）

1. ~~补推送~~ **已完成（2026-09-24）**：`git -C D:/git/opencode-skills push -u origin
   feat/security-case-response-v2` 直连成功，SSH 22/443 当时均可用。
2. 真实试跑：Redmine tracker_id=26 最近的 1-2 个案件，v1.1 链路照旧跑
   `process_issue.py`；如需三源对照，先跑 `triage_cases.py` 产出 cases JSON，再
   `process_issue.py --with-asset-triage --triage-cases <cases.json>`。
3. 推送/通知类验证一律先测试目标（`config/security_case/notify.json` allowed_targets），
   确认真实目标前禁止推真实群。
4. 端到端演练一个真实进行中案件，写 `docs/drill-report.md`。
5. 收尾：钉钉《AI 提效落地计划》R50 进度"已完成"、落地情况"已落地"、K50 填实测结论；
   写落地报告到 `D:\opencode\file\2026-09-21\安全案件研判与处置-落地报告.md`；
   更新 memory 并 `node ~/.claude/scripts/mem0-sync.js` 同步。

## 已知问题 / 未解决

- ~~**git push 未完成**~~ **已解决（2026-09-24）**：SSH 直连恢复，分支已推送。
- **仓库工作区有约 680 个 tracked 文件缺失**（`memory-*` 等 skill 目录不在磁盘上），
  其中约 285 个此前已被暂存为删除。这与本任务无关、早于本任务存在，本次提交已用
  `git reset` 清空索引并只暂存本任务文件规避。**恢复前不要 `git add -A` 或
  `git commit -a`**，否则会把整批缺失提交成删除。是否 `git checkout -- .` 恢复需用户
  确认（可能覆盖有意的本地删除）。
- CVE 情报真实抓取未验证：`collect_cve_intel.py` 需出站访问 NVD/厂商接口，节前只做了
  存在性与配置校验（未跑真实抓取）；情报 → cve_items 的转换目前是人工/LLM 研判步骤
  （设计如此，脚本 docstring 有 schema）。
- CMDB/扫描器 `--fetch` 分支保留原实现的保守策略：缺内网放行即输出 gap 停止，节后如
  要真连需先申请网络放行。
- `.pytest_cache/` 目录有 Windows 权限问题（pytest 写缓存被拒），已用 `-p no:cacheprovider`
  规避；不影响测试结果。
- `triage_rules.json` 的 `approved_by` 为"待批准"——阈值数值沿用提交初值，正式启用前
  需责任人书面批准（改 JSON 即可）。

## 关键文件索引

| 内容 | 位置 |
|---|---|
| 架构决策/能力矩阵 | `docs/v2-adr.md` |
| 步骤级进度日志（含偏差记录） | `docs/v2-progress.md` |
| v2.0 能力与运行序列 | `SKILL.md` 的"v2.0：安全案件三源研判与滚动跟踪"章节 |
| 规则配置 | `config/security_case/*.json` |
| 运行期产物（不入 git） | `work/security_case/{cache,output,progress}/` |
| 测试 | `tests/test_security_case_{triage,report_track}.py`（28 passed） |
