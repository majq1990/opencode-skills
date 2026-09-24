# v2.0 架构决策记录（ADR）：安全案件研判与处置

日期：2026-09-22 ｜ 决策人：马健权（闲时任务代拟，待确认）｜ 截止：2026-10-15

## 1. 目标（来自《AI 提效落地计划》AI落地场景 R50）

安全案件研判与处置 v2.0 = CVE/CNVD 情报采集 + 扫描结果与资产台账对照 +
处置报告 + 责任人待办 + 确认后推送 + 次日滚动跟踪 + 换项目只改配置 +
与现有漏洞扫描/修复闭环。

## 2. 决策：原地升级 redmine-security-auto-fix v1.1.0 → v2.0

不新建平行 skill、不改目录名。理由：生产在用、已发布 skill server、
有 6 个测试文件和稳定配置入口（`D:\git\redmine-similar-assist\config.yaml`）。
新建会造成入口分裂和双份维护。

## 3. 三套资产能力矩阵

| 能力 | redmine-security-auto-fix v1.1.0 | vuln-response v0.1+ | 刘锐 security-case-handling (T3=40) |
|---|---|---|---|
| 案件附件多格式解析 | ✅ report_parser.py（doc/xls/pdf/html/zip…） | ❌ | ❌ |
| 代码/非代码分流 | ✅ recommendation_engine.py | ❌ | ❌ |
| 工程/研发责任分流 | ✅ classify_vulns.py | ❌ | ❌ |
| 内部检索（历史案件+KB） | ✅ 双链路：sec_kb_bridge.py（服务器安全池，tracker26+漏召回填+★安全文档+情报，秒级）+ similar_assist_bridge.py（全库 19.9万案件，sqlite-vec） | ❌ | ❌ |
| 互联网兜底检索 | ✅（代码类兜底/非代码并行） | ❌ | ❌ |
| CVE/CNVD 情报采集 | ❌ | ✅ fetch_vendor_advisory.py（6厂商）+ fetch_software_advisory.py（NVD/GHSA/CNVD） | ✅ collect_cve.py（NVD 2.0，支持离线 sample） |
| 漏洞扫描结果采集 | ❌ | ❌ | ✅ collect_scanner_results.py（nessus/openvas/xray→归一化） |
| 资产台账采集 | ❌ | ❌ | ✅ collect_asset_info.py（CMDB→归一化，owner 权威） |
| 三源融合研判分级 | ❌ | ❌ | ✅ triage_cases.py（CVE×扫描×资产，risk_score=cvss×资产重要性×暴露×利用系数） |
| 处置报告生成 | ✅（钉钉修复方案文档，含分级建议） | ✅（CVE 处置文档模板） | ✅ gen_security_report.py（报告+待办清单+案件状态） |
| AI 表格台账 | ❌ | ✅ 钉钉「安全漏洞台账」AI表格（os/software 双表） | ❌（仅 markdown） |
| 钉钉文档发布 | ✅ 真实 API 校验后发布"项目案例"目录 | ✅ publish.py（copy-template 链路） | ❌（push 仅 markdown 预览） |
| 责任人待办 | ❌ | ❌ | ✅ todo_*.md（按 owner 分组） |
| 确认后推送 | ❌ | ⚠️ 人工确认门禁（publish 前审稿） | ✅ push_security_report.py（人工确认门禁+只读单向） |
| 次日滚动跟踪 | ❌ | ❌ | ✅ track_case_state.py（超期/进行中/待验证→次日提醒） |
| 换项目只改配置 | ⚠️ config.yaml 密钥集中 | ⚠️ 少量硬编码默认值 | ✅ config/ 全量外置（asset/cve/scanner/notify/triage_rules） |

## 4. 合并方案（增量，不破坏 v1.1.0 语义）

1. **移植**：刘锐 `collect_asset_info.py`、`collect_scanner_results.py`、
   `triage_cases.py`、`track_case_state.py` → `redmine-security-auto-fix/scripts/`，
   保留其标准库-only 约定；配置从各自 config/*.json 改为读
   `D:\git\redmine-similar-assist\config.yaml` 新增 `security_case:` 节
   （带缺省值，config.yaml 无该节时用内置默认并告警，不强制用户改配置文件）。
   `_lib.py` 合并为 `security_case_lib.py`（避免与未来同名冲突）。
2. **接入主流程**：`process_issue.py` 增加**可选**后处理步骤
   `--with-asset-triage`（默认关闭）：附件解析→分流→检索→报告→
   资产对照→责任人待办→状态跟踪。默认关闭保证 v1.1.0 行为不变。
3. **CVE 主动情报（跨目录引用）**：新增 `collect_cve_intel.py` 包装脚本，
   subprocess 调用 `C:\Users\majq1\.zcode\skills\vuln-response\scripts\fetch_vendor_advisory.py`
   / `fetch_software_advisory.py`（路径进 config），vuln-response 本身零改动。
   选跨目录引用而非合并脚本：改动最小，且 vuln-response 有独立发布节奏（demo 服务器部署）。
4. **SKILL.md** 升 v2.0：新增能力、配置项、停止条件；v1.1.0 全部既有规则原样保留。
5. **测试**：新增 tests/test_security_case_*.py，fixture 假数据，不连真实 Redmine/钉钉。

## 5. 数据流（v2.0 目标态）

```
Redmine 案件(tracker 26) ──附件──> report_parser ──> 分流(代码/非代码,工程/研发)
                                                      │
NVD/厂商公告(vuln-response) ──┐                      ▼
nessus/openvas/xray ──────────┼──> triage_cases（三源融合 risk_score 分级）
CMDB 资产台账 ────────────────┘                      │
                                     ┌───────────────┤
                                     ▼               ▼
                          修复方案(历史KB+互联网兜底)  处置报告+待办清单(按owner)
                                     │               │
                                     ▼               ▼
                          钉钉"项目案例"文档发布    push（人工确认门禁，测试目标先行）
                                                     │
                                                     ▼
                                        track_case_state → 次日滚动提醒
```

## 6. 红线与停止条件

- 不改 v1.1.0 已有文件的行为语义；`--with-asset-triage` 等新增全部默认关闭。
- 密钥零硬编码，统一读 config.yaml；扫描/CMDB 凭据走环境变量引用（沿用刘锐的 `*_env_ref` 约定）。
- push/通知类操作先用测试目标；未确认不推真实群。
- 外部依赖不可用→记录 v2-progress.md 并跳过，不假装成功。
- 发现会破坏生产链路→停下记录，不硬上。
