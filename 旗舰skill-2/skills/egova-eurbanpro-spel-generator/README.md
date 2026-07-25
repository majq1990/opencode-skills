# egova-eurbanpro-spel-generator

## 目标

该目录保存一个面向 Egova / EUrban / MIS 业务配置场景的 SpEL skill。

它主要解决三类问题：

- 识别当前需求属于哪个业务场景
- 判断该场景下更可能支持哪些 SpEL 主体 / 占位符
- 把工程师的业务口语需求整理成可落地的候选 SpEL 表达式

## 适用范围

当前重点覆盖 4 类场景：

- 菜单 / 按钮显示与过滤
- 流程引擎自动批转 / 自动流转 / 分支判断
- 案件显示样式（标红、高亮、标签等）
- 消息配置 / 规则配置

## 目录说明

- `SKILL.md`
  - 主 skill 文档，负责触发说明、执行流程、输出模式、guardrails 与 reference 路由
- `references/scene-index.md`
  - 场景总览入口
- `references/scene-menu.md`
  - 菜单场景说明
- `references/scene-workflow-auto-transfer.md`
  - 流程自动批转场景说明
- `references/scene-case-display-style.md`
  - 案件显示样式场景说明
- `references/scene-message-rule.md`
  - 消息配置 / 规则配置场景说明
- `references/spel-subjects.md`
  - 主体说明与证据口径
- `references/spel-fields.md`
  - 常见业务字段映射
- `references/ambiguity-handling.md`
  - 何时必须追问、何时可带假设生成
- `references/spel-examples.md`
  - 示例库与推荐输出范式
- `doc/research/`
  - 来自 core / mis-core 代码调研的结论记录
- `doc/real-engineer-colloquial-test-*.txt`
  - 面向真实工程口语需求的测试样例、执行指南、结果模板

## 维护关系

建议按下面顺序维护：

1. 先更新 `doc/research/` 中的代码证据结论
2. 再回补对应 `references/scene-*.md` 与 `spel-subjects.md`
3. 若口径变化影响示例，再更新 `references/spel-examples.md`
4. 最后检查 `SKILL.md` 是否仍只保留流程导航与 guardrails，而没有和 references 重复过多正文

## 后续迭代建议

后续优先沿两条线继续补强：

- **触发与输出稳定性**：继续优化 `SKILL.md` 的 description、输出模式与“产出优先”策略
- **评测闭环**：继续用 `doc/real-engineer-colloquial-test-*` 对 skill 做真实口语样例验证，记录失败模式，再回补 references

## 注意

当前 skill 已尽量基于现有 research 收口主体范围，但最终支持范围仍应以项目代码与真实配置链路为准。
