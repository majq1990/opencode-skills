# egova-urbanpro-core 场景化 SpEL 主体研究

> 结论依据：`egova-urbanpro-core` 中规则求值、上下文 provider、菜单与 workflow/timing 相关实现代码。
> 说明：这里记录的是“代码里已看到的实际注入证据”，不是 skill 层面的推测支持范围。

## 1. 总体结论

`egova-urbanpro-core` 的 SpEL 求值核心在 `SpElRuleServiceImpl.java`：

- 使用 `StandardEvaluationContext`
- 通过 `evaluationContext.setVariables(context)` 把上下文变量整体注入
- 因此某场景“支持哪些主体”，关键取决于该场景最终往 `context` 中放了哪些 key

代码证据：
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/service/impl/SpElRuleServiceImpl.java:71-80`

---

## 2. 已确认主体

### 2.1 `#bizEntry`

已明确看到默认规则上下文 provider 支持 `#bizEntry`：

- `DefaultBizEntryRuleContextProvider` 明确把占位符 `#bizEntry` 映射到上下文 key `bizEntry`
- provider 会按 `bizEntryId / bizEntryUid` 查询业务实体并注入

代码证据：
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultBizEntryRuleContextProvider.java:39-56`

workflow 公式上下文里也会补入 `bizEntry`：
- `AbstractBaseContext` 在拿到运行时业务实体后，会 `formulaParams.put("bizEntry", runtimeBizEntry)`

代码证据：
- `modules/workflow/egova-urbanpro-workflow-engine-api/src/main/java/com/egova/workflow/engine/param/AbstractBaseContext.java:62-82`

### 2.2 `#actInst`

已明确看到 workflow 规则 provider 支持 `#actInst`：

- `DefaultWorkflowRuleContextProvider` 定义了 `#actInst -> actInst`
- 若表达式里包含 `#actInst`，则按当前 act 信息装配 `actInst`

代码证据：
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:25-56`

workflow 公式数据提供者也会按表达式内容补 `actInst`：
- 当表达式包含 `#actInst.` 且上下文尚无该值时，查询活动实例并 `map.put("actInst", wfActInst)`

代码证据：
- `modules/workflow/egova-urbanpro-workflow-engine-rest-standard/src/main/java/com/egova/workflow/engine/standard/provider/impl/WorkflowRuleParamValueDataProvider.java:22-25`
- `modules/workflow/egova-urbanpro-workflow-engine-rest-standard/src/main/java/com/egova/workflow/engine/standard/provider/impl/WorkflowRuleParamValueDataProvider.java:52-55`

### 2.3 `#parallelCheckList`

已明确看到 workflow 规则 provider 支持 `#parallelCheckList`：

- `DefaultWorkflowRuleContextProvider` 定义了 `#parallelCheckList -> parallelCheckList`
- 命中后会查询 `workflowInfoInnerService.getParallelCheckInfo(...)`，并把并行校验活动信息列表放入上下文
- 若没有并行配置或历史记录，也会回填空列表，而不是不放这个 key

代码证据：
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:27-34`
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:89-99`
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:154-157`

当前判断：
- 这是明显偏 workflow 并行判断的专用主体
- 不宜把它包装成菜单、消息、样式等所有场景的通用主体

### 2.4 `#priSub`

已明确看到 workflow 规则 provider 支持 `#priSub`：

- `DefaultWorkflowRuleContextProvider` 定义了 `#priSub -> priSub`
- 该值用于表示是否存在主协办并行语义，结果按 `1 / 0` 放入上下文
- 若当前活动本身就是主协办并行，provider 会直接给出 `1`
- 若需回溯历史，则根据并行校验列表计算后放入

代码证据：
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:30-31`
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:78-83`
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:96-100`
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:155-157`

当前判断：
- `#priSub` 更像 workflow 并行/主协办状态标志位
- 可作为正式系统里已存在的可用主体证据记录下来，但 skill 主文档里应注明其场景局限性

### 2.5 `#parallel`

已明确看到 workflow 规则 provider 支持 `#parallel`：

- `DefaultWorkflowRuleContextProvider` 定义了 `#parallel -> parallel`
- 该值用于表示当前或历史链路是否属于并行场景，结果按 `1 / 0` 注入
- 即使不存在并行配置，也会通过 `emptyParallel(...)` 明确回填 `0`

代码证据：
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:33-34`
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:80-87`
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:102-138`
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:154-157`

当前判断：
- `#parallel` 是 workflow 并行链路判断用的专用标志位主体
- 应与通用业务主体 `#bizEntry`、`#actInst` 区分开描述

### 2.6 `#userDetails`

已看到通用规则上下文补充 `userDetails`：

- `RuleEvalUtils.genRuleCalcContext(...)` 在 provider 执行后，若当前登录用户存在，则 `context.put("userDetails", OauthContext.getUserDetails())`

代码证据：
- `modules/rule/egova-urbanpro-rule-api/src/main/java/com/egova/rule/util/RuleEvalUtils.java:238-242`

### 2.7 `#username`

在 core 中已看到菜单场景直接手工注入 `username`，但目前未看到像 `userDetails` 那样的通用补充逻辑。

代码证据：
- `modules/bizbase/egova-urbanpro-tasklist-rest/src/main/java/com/egova/tasklist/service/impl/SysTaskListMenuServiceImpl.java:667-668`
- `modules/bizbase/egova-urbanpro-tasklist-rest/src/main/java/com/egova/tasklist/service/impl/SysTaskListMenuServiceImpl.java:724-725`

初步判断：
- `username` 在 core 里至少对菜单相关规则可用
- 但当前还不能仅凭已有证据断言它是所有 core 规则场景的通用主体

### 2.8 `#timing`

在 core 中暂未直接看到 `context.put("timing", ...)` 或 `#timing` 的明确注入证据。

但 timing 相关流程里已看到：
- `WfBundleTimingCalculateServiceImpl` 会把 `actInst`、`newAct` 放到额外参数里
- 说明 timing 模块存在“围绕时限计算构造额外上下文”的机制
- 但当前这批证据还不足以确认 skill 文档里的 `#timing` 在 core 中是否就是一个统一、稳定的主体名

代码证据：
- `modules/timing/egova-urbanpro-timing-rest/src/main/java/com/egova/timing/service/impl/WfBundleTimingCalculateServiceImpl.java:125-128`

当前结论：
- core 中已确认 timing 相关逻辑存在
- 但尚未确认有统一的 `#timing` 主体注入点

### 2.9 `#state`

本轮在 core 中暂未找到明确的 `#state` 注入证据。

当前结论：
- 不能仅凭 skill 文档或样例，反推 core 一定通用支持 `#state`
- 后续若要在 core skill 文档里宣称某场景支持 `#state`，还需要继续补代码证据

---

## 3. 按场景整理

## 3.1 菜单场景

### 已确认支持的主体

在 `SysTaskListMenuServiceImpl` 中，菜单限制 / 菜单可见性 / 菜单自定义名称相关逻辑已看到以下主体：

- `bizEntry`
- `actInst`
- `userDetails`
- `username`
- 另有非本次 skill 核心主体：`taskListIds`、`taskListId`、`roleIds`

关键代码：
- 二次确认 / 限制规则上下文：`SysTaskListMenuServiceImpl.java:666-678`
- 菜单显示规则 `core:menu:display`：`SysTaskListMenuServiceImpl.java:715-740`
- 菜单自定义名称：`SysTaskListMenuServiceImpl.java:748-779`

对应判断：
- 菜单场景中，`#actInst`、`#bizEntry`、`#userDetails`、`#username` 有较强代码证据
- 这是当前最明确、最稳定的一类场景

## 3.2 workflow / 规则流转场景

### 已确认支持的主体

workflow 相关代码里，较稳定的主体是：
- `bizEntry`
- `actInst`
- `parallelCheckList`
- `priSub`
- `parallel`

证据链：
- workflow 基础上下文会补 `bizEntry`
- workflow rule data provider 会按表达式补 `actInst`
- workflow refresh provider 也会刷新 `actInst`
- `DefaultWorkflowRuleContextProvider` 还会按表达式需要补 `parallelCheckList`、`priSub`、`parallel`

代码证据：
- `AbstractBaseContext.java:67-70`
- `WorkflowRuleParamValueDataProvider.java:52-55`
- `modules/workflow/egova-urbanpro-workflow-engine-rest-standard/src/main/java/com/egova/workflow/engine/standard/provider/impl/WorkflowRefreshRuleProvider.java:64,73`
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:52-58`
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:80-82`
- `modules/rule/egova-urbanpro-rule-rest/src/main/java/com/egova/rule/context/provider/DefaultWorkflowRuleContextProvider.java:90-105`

补充说明：
- `parallelCheckList`、`priSub`、`parallel` 都明显是 workflow 并行 / 主协办判定链路中的专用主体
- 它们的存在说明 core workflow 场景下可用主体不止 `#actInst`
- 但对 skill 输出层，应把这三类主体归为“特定 workflow 规则扩展主体”，不要误包装成所有业务场景通用能力

### 正式系统表达式相关补充

菜单和 workflow 规则链路里还看到了一些非通用业务实体变量，例如：
- `taskListId`
- `taskListIds`
- `roleIds`

代码证据：
- `SysTaskListMenuServiceImpl.java:730-733`
- `SysTaskListMenuServiceImpl.java:777-779`

这说明：
- 正式系统中出现类似 `#taskListId` 的表达式是合理的，不能因为它不在当前 `spel-fields.md` 里，就直接判定为无效
- 更稳妥的口径应是：把它们视为“特定场景上下文变量”，并继续按场景补 research，而不是强行塞进通用字段表

## 3.3 timing / 时限相关场景

### 当前能确认的内容

- timing 模块里已看到 `actInst` 被放入额外参数
- 但尚未看到统一的 `timing` 主体名注入证据

代码证据：
- `WfBundleTimingCalculateServiceImpl.java:127-128`

建议在 skill 文档中的写法：
- 不要直接把 core 场景笼统写成“支持 `#timing`”
- 应写成“timing 相关能力存在，但当前 research 证据还未确认统一的 `#timing` 主体注入点”

---

## 4. 当前最稳妥的 core 结论

如果只保留代码证据最强的部分，可以先写成：

- 菜单场景：明确支持 / 已看到 `bizEntry`、`actInst`、`userDetails`、`username`
- workflow / 自动流转相关规则：明确支持 / 已看到 `bizEntry`、`actInst`
- timing 相关：已看到 `actInst` 参与计算上下文，但 `#timing` 主体名尚未确认
- `#state`：本轮未在 core 中确认到通用注入证据，先不要写死

---

## 5. 对 skill 回补的建议

基于 core 代码，后续回补 skill 文档时建议：

1. `scene-menu.md`
   - 可以明确写入：菜单场景优先关注 `#bizEntry`、`#actInst`、`#userDetails`、`#username`

2. `scene-workflow-auto-transfer.md`
   - 可以先写：workflow 规则场景已确认常见主体为 `#bizEntry`、`#actInst`
   - 若提到 `wfAct / wfActInst`，应注明这是 workflow 公式内部额外变量，不等同于所有规则场景都统一使用

3. `spel-subjects.md`
   - `#timing`、`#state` 在 core 侧先保守描述，不要包装成“已普遍确认支持”

4. `SKILL.md`
   - 应把“最终支持范围以项目代码实现为准”写得更强一些
