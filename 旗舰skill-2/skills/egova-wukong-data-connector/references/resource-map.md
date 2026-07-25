# 资源目录说明

> 用途：说明本 skill 的资源如何分层，避免把入口、参考规则、知识库、模板和示例混在一起。

## 入口文件

- `SKILL.md`：skill 入口，只保留角色、核心原则、资料读取顺序、固定阶段、硬门禁和最终输出总规则。

## references/

参考规则文档，按需读取：

- `workflow.md`：阶段状态、Gate -1、Candidate Review、Gate 0、静态模板优先级和总体执行顺序。
- `data-source-rules.md`：悟能、现场接口、ddcat 或 SQL 的选择规则。
- `output-format.md`：最终输出与补充清单格式。
- `filter-script-rules.md`：ES5 `function filter(data)` 脚本规则。
- `fallback-rules.md`：悟能未命中或无法满足时的现场补充分支。
- `checklist.md`：门禁检查清单。

## knowledge/

领域知识和数据字典：

- `api_flat.md`：悟能接口扁平摘要。用于命中候选后的快速复核，降低直接读取 detailDoc 的成本。
- `component_static_schema.md`：组件推荐 `result` 数据样例库。
- `record_index_metrics.md`：案件与人员指标枚举参考。
- `api_details/**/*.md`：悟能接口详情文档。

## domain_indexes/

索引型知识库：

- `wuneng_api_index.md`：悟能接口粗筛索引。它只用于发现候选，不能替代详情文档或现场材料。

## templates/

输出模板：

- `final_output_template.md`：最终四段式输出模板。
- `ddcat_fallback_template.md`：悟能未命中或无法满足时的补充模板。
- `filter_patterns.md`：常见 `filter(data)` 转换模式和 ES5 脚本骨架。

## assets/

面向打包或复用的资源入口。当前不搬迁已有模板，避免破坏历史引用；`assets/README.md` 指向现有模板和资源。

## examples/

few-shot 示例，只演示写法，不代表业务边界。

## evals/

回归评测用例。用于检查 Gate、接口命中、fallback、过滤脚本和输出格式是否稳定。