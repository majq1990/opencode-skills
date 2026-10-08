# ops-patrol-toolkit · 运维巡检与故障排查工具集（R48）

工程技术中心通用 Skill。九个子工具可独立调用，零第三方依赖。

## 能力一览

| 编号 | 能力 | 入口 | 输入 | 输出 |
|---|---|---|---|---|
| 01 | 巡查三源汇总 | `scripts/01_patrol_merge.py` | 人巡/机巡/部件 xlsx 或 csv | 统一 9 列明细表（xlsx/csv） |
| 02 | MySQL 高 I/O 分诊 | `scripts/02_mysql_io_triage.py` | iostat / digest / DDL 文本 | report.md + triage.json |
| 03 | 维护手册规范化 | `scripts/03_manual_standardize.py` | 立项资料 docx + 项目信息 json | 手册初稿 docx + 差异清单 md |
| 04 | 月度运维报告 | `scripts/04_monthly_report.py` | servers.json + 统计 json + Word 模板 | 巡检状态 json + 月报 docx |
| 05 | 历史相似案例检索 | `scripts/05_kb_similar_search.py` | 症状描述或 02 的 triage.json | 历史工单/知识库案例报告 md（联网，需 token 环境变量） |
| 06 | auto-check 巡检告警分诊 | `scripts/06_autocheck_triage.py` | auto-check JSON 巡检报告 | 告警项 + WIKI 链接 + 处置引导 md（离线） |
| 07 | Zabbix 告警分诊 | `scripts/07_zabbix_triage.py` | Zabbix API（problems/triage 两阶段） | 告警 json + 处置引导 md |
| 08 | Prometheus 告警分诊 | `scripts/08_prometheus_triage.py` | /api/v1/alerts（alerts/triage 两阶段） | 告警 json + 处置引导 md |
| 09 | SkyWalking 告警分诊 | `scripts/09_skywalking_triage.py` | OAP GraphQL queryAlarms（两阶段） | 告警 json + 处置引导 md |
| 公共 | 脱敏 | `scripts/redact.py` | 任意文本材料 | 脱敏后文本 |
| 公共 | 监控出站安全闸 | `scripts/monitor_http.py` | — | 06-09 共享 HTTP 客户端 |

## 自测

```bash
python -m pytest tests/ -p no:cacheprovider -q
```

全部用例离线合成数据（监控类经本地 http.server 假服务），不连任何真实系统。

## 设计原则

- **零依赖**：xlsx/docx 读写为自研 OOXML 实现（`scripts/xlsx_io.py`、`scripts/docx_io.py`）；监控客户端为自研 JSON-RPC/REST/GraphQL 调用（`scripts/monitor_http.py`）
- **gap-stop**：缺前置条件输出 `{"ok": false, "gap": "..."}` 并退出码 2，不静默兜底
- **模板/配置永不改写**：产物只写 `work/` 或显式 `--out`
- **报告默认【待复核】**：未经人工复核不得外发
- **换项目只改配置**：字段签名、巡检清单、阈值、月报映射、监控端点全部外置 `config/patrol/`
- **出站安全闸**：仅 http/https、拒绝回环/云元数据地址、内网私有网段须配置显式放行（`allow_private_targets`）；统一浏览器 UA（公司 WAF 拦截 urllib 特征）

## 版本历史

- 1.2.0（2026-10）：监控告警分诊与处置引导——06 auto-check 巡检报告摄取（预警表达式递归下降安全求值器，替代源 eval；WIKI 链接引导）+ 07 Zabbix（JSON-RPC）+ 08 Prometheus（REST）+ 09 SkyWalking（GraphQL）四条告警链路；共享 monitor_http URL 安全闸；通用处置剧本库（references/playbooks）+ 边界感知关键词匹配（驼峰词首可命中、词中片段不误命中）。auto-check 专属指标目录/处置剧本待其解决文档调整定稿后同步（CLI 已预留外挂参数）。
- 1.1.0（2026-10）：真实场景兼容性修复——中文 Word 纯数字 styleId 标题识别（docx_io 读 styles.xml，03 双 token 检测）；02 DDL 首字段丢失修复（外层左括号污染）；DTD/实体声明拒绝闸（安全加固）。
- 1.0.0（2026-10）：五子工具首发（含 05 历史案例检索）；公共库 patrol_lib/xlsx_io/docx_io/redact；合成 fixtures 离线自测。
