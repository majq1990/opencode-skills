# v2.0 落地进度日志

| 日期 | 步骤 | 结果 |
|---|---|---|
| 2026-09-22 | 1.调研三套资产，产出能力矩阵与合并方案 | ✅ docs/v2-adr.md（决策：原地升级 v2.0，增量移植刘锐4脚本+跨目录引用 vuln-response，process_issue 加默认关闭的 --with-asset-triage） |
| 2026-09-22 | 2.建分支 feat/security-case-response-v2 | ✅ 已切换，无关未提交修改（dingtalk-aisearch 等）未卷入 |
| 2026-09-22 | 3.移植合并：security_case_lib + collect_asset_info/collect_scanner_results/triage_cases/gen_security_report/track_case_state + collect_cve_intel（跨目录引用）+ asset_triage_link + process_issue 可选接入 | ✅ 共 9 个新文件；配置外置 config/security_case/（5 个 JSON，零密钥，默认 owner 与阈值批准口径已中性化）；运行产物落 work/（gitignore） |
| 2026-09-22 | 4.移植健壮化（相对原实现的增量修复） | ✅ triage 对缺省字段 .get 化；cvss_score str/None → to_float，无效值转人工（unmapped_cve）不崩溃；兼容原始扫描数据的 owner 键（归一后 owner_from_scan） |
| 2026-09-22 | 5.SKILL.md 升 v2.0 | ✅ version 2.0.0，新增"三源研判与滚动跟踪"章节（能力表/运行序列/配置位置/5 条停止条件），v1.1.0 全部规则原样保留 |
| 2026-09-22 | 6.测试 | ✅ `python -m pytest tests -q` → 28 passed, 8 subtests（含 v1.1 原有 6 个测试文件，无回归）；新增 2 个测试文件共 11 用例（合成 fixture，不连真实服务） |
| 2026-09-22 | 7.端到端冒烟（真实 CLI，样例数据） | ✅ collect_asset 8→7（去重1）→ collect_scan 10→10 → triage 8 案件（Critical 2/High 2/Medium 3/Low 1，台账外 1）→ 报告/待办/状态 3 件产物 → 次日 track（超期2/进行中6）→ progress 回填 fixed → 待验证 1（SC-2026-09-22-001） |

## 与 ADR 的偏差记录

1. 移植脚本从计划的 4 个扩为 5 个：gen_security_report.py 一并移植——track_case_state 依赖其产出的 case_state 文件，且"责任人待办"由它生成，缺它则链路断。
2. 刘锐的 push_security_report.py 未移植：其预览/确认逻辑与既有 notify_dingtalk.py 及 notify.json 的 manual_confirm 门禁重叠；推送统一走既有链路（测试目标先行）。
3. 规则配置放 config/security_case/*.json（沿用"改 JSON 不碰代码"），未并入 config.yaml 的 security_case 节；config.yaml 仍只管 v1.1 既有密钥/连接。triage_rules 的 approved_by 已改为"待批准"（原值是提交者姓名，不能带入生产配置），阈值数值未动。
