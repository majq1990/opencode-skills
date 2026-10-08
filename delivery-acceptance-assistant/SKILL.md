---
name: delivery-acceptance-assistant
description: 交付物审查与验收助手——三源融合审查（验收清单⊕材料目录⊕验收标准）、立项材料生成、实施交付物生成（SQL四件套/部署脚本/中间件配置）、风险登记册。纯 Python 标准库，离线零依赖。
version: 1.0.0
---

# 交付物审查与验收助手

面向工程项目（智慧城市/政务信息化类）交付验收场景的四个能力：

1. **交付物审查**：把「验收清单 + 材料目录 + 验收标准」三源对齐，跑 10 条规则，
   产出分级审查结论（🔴严重/🟠高/🟡中/🔵低）与待补清单。
2. **立项材料生成**：以真实模板为底本做文本级替换（严禁重建文档），版面零丢失校验。
3. **实施交付物生成**：建表/初始化/升级/回滚 SQL 四件套 + Linux 部署脚本 + 中间件配置，
   全部先过数据库命名闸门（P0 违规直接拒绝生成）。
4. **风险登记**：审查发现自动入册 + 人工登记合并，概率×影响分级，指派责任部门/责任人/时限，
   命中升级条件（阻断验收/涉数据/影响里程碑/需客户决策）自动进升级清单。

## 何时用

- 验收前要核查承建方交付的一目录材料是否齐套、合规；
- 新项目要基于历史模板快速出一套立项材料（换名字换日期，版面不动）；
- 开发要交一套数据库变更 + 部署脚本，需要按约定生成并过命名审查；
- 验收发现问题要转成风险台账跟踪闭环。

## 快速开始

```bash
# ① 采集：扫描交付目录（只读，自带零写入自证）
python scripts/01_collect.py --deliverable-dir <交付目录> \
    --project config/project_template.json --outdir out

# ② 审查：10 条规则引擎
python scripts/02_audit.py --outdir out
# 退出码：0=无 Critical；1=有 Critical（阻断验收）；2=前置条件不满足(gap)

# ③ 报告：审查报告 + 待补清单 + 次日跟踪
python scripts/03_report.py --outdir out

# ④ 立项材料生成（模板复制+文本替换+版面校验，模板绝不改写）
python scripts/04_gen_docs.py \
    --templates references/templates --manifest config/doc_templates.json \
    --replacements <替换内容.json> --outdir gendocs

# ⑤ 实施交付物生成（SQL四件套/部署脚本/中间件配置）
python scripts/05_gen_artifacts.py --model <数据模型.json> --outdir artifacts
# 只想跑命名校验不落盘：加 --validate-only

# ⑥ 风险登记册
python scripts/06_risk_register.py --audit out/audit_result.json \
    [--risks <人工风险.json>] [--owner-map <责任人映射.json>] --outdir risks
```

一次全链路自测：`python tests/run_all.py`（29 个用例，正向回归 + 反向堵截）。

## 产物清单

| 脚本 | 产物 |
| --- | --- |
| 01_collect | `manifest.json`、`spec_effective.json` |
| 02_audit | `audit_result.json`（含逐项核查、all_issues、verdict） |
| 03_report | `audit_report.md`、`missing_list.csv`、`nextday_tracking.md`、`audit_state.json` |
| 04_gen_docs | 4 份立项材料 + `_gen_ledger.json`（版面前后对比、未覆盖键） |
| 05_gen_artifacts | `sql/01~04 四件套`、`deploy/*.sh + README`、`middleware/*` |
| 06_risk_register | `risk_register.csv`、`risk_escalation.md`、`risk_summary.md` |

## 审查规则（config/acceptance_rules.json）

| 规则 | 级别 | 说明 |
| --- | --- | --- |
| completeness | Critical | 验收清单要求但目录缺失 |
| sensitive | Critical | 身份证/手机号/银行卡/密码/私钥/内网IP/邮箱 |
| empty_file | High | 零字节文件 |
| format_mismatch | High | 材料格式与验收标准不符（word/excel/ppt/pdf 别名归一） |
| forbidden_ext | High | .tmp/.log/.bak 等禁入扩展名 |
| naming | Medium | 副本/最终版/空格/临时前缀/双扩展名/多版本号 |
| oversize | Medium | 单文件超 100MB |
| sla_overdue | Medium | 超提交时限 |
| cross_reference | Low | 正文引用的 B-xx 编号在目录中不存在 |
| duplicate_version | Low | 同一交付物多版本并存 |

级别与结论映射：有 Critical → 「不通过」；有 High/Medium → 「有条件通过」；
全部 ≤Low → 「通过」。分级定义见 `config/acceptance_rules.json` 的 `level_definitions`。

## 硬约束（实现里已强制，调用方不要绕）

- **零写入**：审查类脚本对交付目录先做 sha256 树快照，结束后复算比对，不一致即中止报 gap。
- **严禁新建空白文档重写内容**：立项材料只能「模板复制 → 文本级替换 → 版面保留校验」，
  图片/表格/域数任一减少即删除产物并失败（`04_gen_docs.py`）。
- **gap 语义**：前置条件不满足（缺文件/坏 JSON/输出目录在目标内）一律输出
  `{"ok": false, "gap": "..."}` 信封并以退出码 2 结束，**绝不静默用默认值兜底继续**。
- **命名闸门**：表/字段/索引名先过 `config/db_rules.json`（约定前缀、长度、保留字、
  snake_case），任一 P0 违规拒绝生成 SQL，不产出「会被 DBA 打回」的脚本。
- **升级/回滚成对**：模型给了 upgrade.statements 但没有 upgrade.rollback 时拒绝生成。
- **替换命中率诚实上报**：模板里没找到的替换键计入「未覆盖」原样上报，不为凑数硬造。
- 产物只是文本/表格，**不连数据库、不执行系统命令**；SQL 执行前须人工评审。

## 配置文件（换项目只改 config/）

- `project_template.json` —— 项目档案：验收清单（deliverable_list）+ 验收标准（acceptance_criteria）。
- `acceptance_rules.json` —— 规则开关与级别。
- `sensitive_rules.json` —— 敏感信息正则与脱敏方式，`allowlist_files` 可豁免。
- `naming_rules.json` —— 交付文件命名规范。
- `db_rules.json` —— 数据库设计约定（前缀语义/长度/审计列/软删/保留字）。
- `risk_matrix.json` —— 概率×影响阈值、升级条件、默认责任部门。
- `doc_templates.json` —— 文档类型 → 模板文件名（模板放 `references/templates/`）。

## 输入文件格式

**替换内容**（04 的 `--replacements`）：

```json
{
  "_project_name": "新项目名",
  "实施方案": {"旧项目全名": "新项目全名", "二零二三年十月": "二零二六年九月"},
  "交付计划": {"2023年11月7日": "2026年10月8日", "周高峰": "张三"}
}
```

跨 run 拆分（Word/PPT 把一个词拆进多个文本块）与 xlsx 数字实体编码都会自动处理；
只做文本替换，不动任何样式、图片、表格结构。

**数据模型**（05 的 `--model`）：见 `references/model_sample.json`。

**人工风险**（06 的 `--risks`）：`[{"title": "...", "probability": 3, "impact": 4,
"owner": "...", "due": "2026-10-15", "escalate": ["customer_related"]}]`，
`escalate` 取值：blocks_acceptance / affects_data / affects_schedule / customer_related。

## 已知边界

- 旧版 `.doc`（OLE2）按 utf-16le 粗提取，准确率有限；建议转 docx 后再审。
- PDF 不做文本抽取（只查扩展名/大小/命名）；需要内容级审查请另配 pdf 工具链。
- 版面校验覆盖 图片/表格/域 三类元素计数，字号级差异不在守卫范围。
- 敏感信息只报告不回写——脱敏需人工或另用专门工具处理原文件。
