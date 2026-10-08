# HANDOFF — ops-patrol-toolkit（R48 运维巡检与故障排查工具集）

**当前状态一句话**：v1.0 五个子工具（01 三源汇总 / 02 I/O 分诊 / 03 维护手册 / 04 月报 / 05 历史案例检索）全部落地，79 个离线测试用例全绿，端到端冒烟与 05 真机（MCP）试跑通过，已交付。

## 分支与提交

- 仓库：`D:\git\opencode-skills`，分支 `feat/security-case-response-v2`
- 本 skill 全部代码在 `ops-patrol-toolkit/` 独立目录，与其他 skill 零耦合

## 交付物结构

- `scripts/`：patrol_lib（信封/配置/路径公共库）、xlsx_io（自研 OOXML xlsx 读写）、docx_io（自研 OOXML docx 读写）、redact（脱敏）+ 五个编号子工具
- `config/patrol/`：sources / triage_thresholds / manual_rules / servers / monthly_report / kb_search 六份 JSON，换项目只改配置
- `references/`：standard-structure.json（11 章节）、terminology.json、decision-tree.md
- `assets/`：monthly-report-template.docx（合成模板）
- `tests/`：79 用例全离线（含 127.0.0.1 本地假服务），fixtures 全合成

## 开发方式（供后续迭代参考）

主控 + 5 个并行子 agent 同步开发：主控先固化公共库与 CLI 契约（SKILL.md），四个移植 agent + 一个新写 agent 按文件所有权分工（互不重叠文件），各自跑测试后主控集成。并发上限 2，分两批派发。

## 与标杆实现的关系（移植溯源）

- 01 移植王宝鑫 patrol-merge-summary 解析逻辑，openpyxl 全部替换为自研 xlsx_io
- 02 近保真移植杨鹏 mysql-ro-io-triage，阈值外置 config/patrol/triage_thresholds.json
- 03 移植苏志恒规范项目维护手册，docx IO 走共享 docx_io，三脚本合一
- 04 重写高天 monthly-ops-report 的 check_servers/fill_report 通用模式（其客户 IP/HMAC 密钥/个人路径零带入）
- 05 新写：redmine-assist MCP（demo.egova.com.cn）纯标准库客户端，initialize→initialized→tools/call 三步会话 + SSE 解析

## 运行前提

- Python 3.8+，零第三方依赖；01-04 离线可跑
- 05 需环境变量 `DEMO_EGOVA_MCP_TOKEN`（demo 网关钉钉扫码 Session Token，本机 ztoa MCP 同域同 token 体系）；测试严禁联网，离线假服务覆盖协议流程

## 关键踩坑（勿重复踩）

1. **公司 WAF 拦截 Python-urllib 特征**（WinError 10054 强制断连）：05 的所有请求必须带浏览器 User-Agent（代码已内置）
2. MCP `tools/call` 前必须先发 `notifications/initialized`，且全程带 `mcp-session-id` 头
3. Windows 下 pytest 必须 `-p no:cacheprovider`（cache 目录权限问题）
4. MCP 中文入参在 curl/Git Bash 下会 GBK 乱码——用 UTF-8 文件 + `--data-binary @file`
5. xlsx_io 读取的空单元格一律 None（OOXML 无空串概念）；日期格返回 "YYYY-MM-DD" 字符串

## 已知边界

- 04 业务统计走 JSON 文件输入，数字城管 API/CDP 等客户直连不在通用版
- xlsx_io 不支持 .xls 老格式/图表透视表（忽略）；docx_io 只处理正文（页眉页脚/文本框不替换）
- ~~02 沿用源版行为：parse_ddl 首字段计数偏小 1~~（v1.1.0 已修复，见变更记录）

## 变更记录

- 2026-10-08：**v1.2.0**——监控告警分诊与处置引导（用户需求：结合 auto-check 代码，覆盖 Zabbix/Prometheus/SkyWalking 监控发现的问题并引导处理）：
  - **06 autocheck_triage**（893 行）：摄取 auto-check JSON 巡检报告；指标键 `序号:名称:单位:预警表达式:WIKI锚点` 解码；预警表达式**递归下降安全求值器**（复刻 auto-check filters.py 的 comp_dict 语法，替代其 eval，parse 失败保守判告警对齐源码行为）；26 用例
  - **07 zabbix / 08 prometheus / 09 skywalking**：三阶段同构（拉取→归一落盘→离线分诊），JSON-RPC/REST/GraphQL 各一，全走 monitor_http 安全闸；12+14+13 用例
  - **共享底座**：monitor_http.py（URL 安全闸：仅 http/https、拒 userinfo/回环/云元数据[169.254，无开关]，私有网段配置 allow_private_targets 显式放行=内网监控部署常态；统一浏览器 UA）；config/patrol/monitors.json（三端点模板）；references/playbooks/common_playbooks.json（12 个通用处置剧本）
  - **处置引导**：剧本匹配（patrol_lib.keyword_hit 边界感知：词左边界防 replication×io 误命中、驼峰词首放行 HighCpuLoad×cpu；**调用侧禁止先 lower，会销毁驼峰信息**）→ 处置步骤 + WIKI 链接 + 05 号子工具检索命令
  - 全仓 **174 用例**全绿；06 冒烟 10 告警项 ok:true
- 2026-10-08：**auto-check 解决文档同步点（遗留）**——auto-check 团队正在统一调整"问题解决文档"，auto-check 专属指标目录（autocheck_metrics.json）与处置剧本（autocheck_playbooks.json）**延后同步**；06 的 CLI 已预留 `--metrics`/`--playbooks` 可选参数，届时只换 JSON 零代码改动
- 2026-10-08：**仓库事件**——D:\git\opencode-skills 本地仓（.git+85 skill）在 10-02~10-08 间被整体清理（junction 仍在）；已从 GitHub 重克隆接回（master 已是他人 2026-09-17 堆积同步后的新版本，切回 feat/security-case-response-v2 继续）。skills-manager 的扫描路径 junction 不受影响
- 2026-10-02：**v1.1.0**——真实场景兼容性两项修复：① 03 标题识别支持中文 Word 纯数字 styleId（docx_io.read_paragraphs 新增 style_name 字段读 word/styles.xml，_heading_level 双 token 检测，旧数据无影响）；② 02 parse_ddl 首字段丢失修复（外层左括号污染首段，首列 LOB/字段计数恢复正确）。新增 6 用例，全仓 87 用例全绿。同日 1.0.0 首发与安全加固见下。
- 2026-10-02：v1.0 首发。五子工具 + 公共库 + 79 用例；05 真机试跑通过（zhengtong_query ~20s）；02→05 from-triage 闭环验证通过。
- 2026-10-02：**skills-manager 拉取就绪已验证**——junction 路径可见（custom_tool_paths.opencode → D:\opencode\config\skills）、全树遍历零错误、无 .pytest_cache/__pycache__（毒 ACL 前科预防）、frontmatter 合规。claude_code 在 disabled_tools 中，无需 .claude\skills 副本。发现层登记在应用下次启动扫描时，导入只能 UI 操作（DB 硬规则不改）。

## 安全审计（Mimosa）

- 2026-10-02 deep 扫描（scan-2026-10-02T19-34-00.816Z-556b6bca5c13，seal sha256:d1fb8274…c3）：17 条发现，triage 结论——
  - **XML 实体扩展 ×9（已修复）**：xlsx_io/docx_io 解析外部 Office 文件存在实体扩展风险 → 加 DTD/实体声明拒绝闸 + 64MB 部件上限，新增 2 个恶意构造拒绝用例（全仓 81 用例）
  - **路径穿越 ×6（按设计接受）**：CLI 入参路径按本地单用户威胁模型信任操作者，非多租户服务
  - **SSRF ×2（按设计接受）**：04 巡检目标 / 05 MCP 端点均来自操作者 config，属工具本职出站
  - run status inconclusive（调用图部分动态派发）为分析覆盖度说明，非漏洞
  - 修复后复扫确认 XML 类发现清零

## 提交纪律（重要）

- 2026-10-08 重克隆后工作区干净，历史遗留脏状态（原 2029 D / 128 M）已随旧仓清理消失。仍保持纪律：提交前 `git status --porcelain -- ops-patrol-toolkit/` 复核范围 → 只 `git add ops-patrol-toolkit/` → `git show --name-status` 复核仅限本目录 → 再 commit。
- 仓库工作分支可能被其他会话（R50/R51 等）切走——跨会话提交先 `git branch --show-current` 确认，必要时 `git merge-base --is-ancestor` 验证后 checkout 本任务的 `feat/security-case-response-v2`，提交推送后切回原分支。
- push 备忘：GitHub 直连时好时坏（443 reset / HTTP2 framing / remote hung up），失败就退避重试；"Everything up-to-date" 可能是失败后的误导信息，**以 `git rev-parse origin/feat/security-case-response-v2` 对照本地分支头确认是否真已推送**。
