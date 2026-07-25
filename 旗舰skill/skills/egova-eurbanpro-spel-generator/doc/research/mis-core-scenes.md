# egova-urbanpro-mis-core 场景化 SpEL 主体研究

> 结论依据：`egova-urbanpro-mis-core` 中消息、流转、样式、时限、打印、MIS 规则 provider 等实现代码。
> 说明：这里记录的是“代码里已看到的实际注入证据”，不是从 skill 文档反推的理论支持范围。

## 1. 总体结论

相比 core，`mis-core` 中很多业务场景直接手工组装 SpEL 上下文，因此能看到更丰富、也更场景化的主体注入：

当前已明确见到的主体包括：

- `bizEntry`
- `actInst`
- `userDetails`
- `username`
- `state`

其中：
- `bizEntry` 与 `actInst` 最常见
- `userDetails` 与 `username` 在菜单、消息、流转配置、部分时限/通知场景中也较常见
- `state` 已有明确代码证据，但目前主要落在 MIS 案件规则 / 反馈规则 / 样式上下文这类场景

---

## 2. 已确认主体

### 2.1 `#bizEntry`

这是 `mis-core` 中证据最广的主体，已出现在多个业务场景：

- 消息动作 / 到达消息
- 工作流启用配置
- 流转配置页
- 延缓 / 预检 / 通知
- 时限配置过滤
- 样式计划
- 打印参数
- 反馈规则 / 到达规则 / 合并规则等

代表性代码：
- `WorkflowMsgActionExtendServiceImpl.java:173`
- `WorkflowArrivalMsgServiceImpl.java:217`
- `MisWorkflowBizServiceImpl.java:45`
- `WorkflowPostponeArdConfigHandlerImpl.java:82`
- `MisTransitPageConfigServiceImpl.java:122`
- `RecTimingCommonConfigFilter.java:159`
- `MisRecDisplayPropertyPlanServiceImpl.java:690`
- `MisRecPrintParamProvider.java:167,178`
- `MisTaskFeedbackRuleServiceImpl.java:180`

结论：
- `bizEntry` 是 `mis-core` 最稳定的通用主体之一

### 2.2 `#actInst`

`actInst` 也具有很强的跨场景证据，常见于：

- 消息规则 / 到达消息
- 流转配置
- 按钮 / 菜单 / 一键流转
- 时限过滤
- 通知、反馈、到达、合并等 workflow 关联规则
- 样式场景中的活动实例上下文

代表性代码：
- `WorkflowMsgActionExtendServiceImpl.java:177`
- `WorkflowArrivalMsgServiceImpl.java:218`
- `WorkflowPostponeArdConfigHandlerImpl.java:83`
- `MisTransitPageConfigServiceImpl.java:123`
- `OneClickTransitMenuHandler.java:113`
- `RecTimingCommonConfigFilter.java:160-162`
- `MisTaskFeedbackRuleServiceImpl.java:181`
- `RecDetailViewServiceImpl.java:87,138`

结论：
- `actInst` 是 `mis-core` 中与 `bizEntry` 并列的核心主体

### 2.3 `#userDetails`

`userDetails` 在 `mis-core` 中不是只出现在单一点位，而是分布在多类业务中：

- workflow 启用配置
- 申请信息扩展
- 发送消息规则校验
- 一键流转 / 页面扩展
- 时限过滤
- 标签聚合
- 通知预检
- 合并、IM 消息等

代表性代码：
- `MisWorkflowBizServiceImpl.java:46`
- `MisGetApplyInfoWorkflowExtendHandler.java:104`
- `MisSendMsgRuleCheckUtils.java:49`
- `RecTimingCommonConfigFilter.java:163`
- `LabelRecGatherServiceImpl.java:97`
- `RecAuditRecNotifyPreCheckHandler.java:58`
- `RecMergeServiceImpl.java:294`
- `MisImSendMsgUtils.java:291`

结论：
- `userDetails` 在 `mis-core` 里已具备较强的跨场景可见性

### 2.4 `#username`

`username` 与 `userDetails` 往往成对出现，也出现在多个业务场景：

- workflow 启用配置
- 申请信息扩展
- 发送消息规则校验
- 一键流转 / 页面扩展
- 时限过滤
- 标签聚合
- 通知 / 合并 / IM 消息等

代表性代码：
- `MisWorkflowBizServiceImpl.java:47`
- `MisGetApplyInfoWorkflowExtendHandler.java:105`
- `MisSendMsgRuleCheckUtils.java:50`
- `OneClickTransitMenuHandler.java:112`
- `RecTimingCommonConfigFilter.java:164`
- `LabelRecGatherServiceImpl.java:98`
- `RecNotifyNoRepServiceImpl.java:295`
- `RecMergeServiceImpl.java:295`
- `MisImSendMsgUtils.java:292`

结论：
- `username` 在 `mis-core` 中也有较明确的跨场景支持证据

### 2.5 `#state`

`state` 在 `mis-core` 中已找到明确证据，不只是文档猜测：

1. `MisTaskFeedbackRuleServiceImpl` 在核实办结校验中显式放入：
   - `context.put("state", misRecStateRepository.getById(recId));`

代码证据：
- `modules/mis/egova-urbanpro-mis-rest/src/main/java/com/egova/mis/rec/service/impl/MisTaskFeedbackRuleServiceImpl.java:179-183`

2. `MisRecRuleContextProvider` 会扫描表达式；若包含 `#state`，则按 `bizEntry` / 历史态自动补齐 `state`

代码证据：
- `modules/mis/egova-urbanpro-mis-rest/src/main/java/com/egova/mis/rec/rule/provider/MisRecRuleContextProvider.java:153-186`

这条证据很关键，说明：
- 在 MIS 规则上下文体系里，`#state` 是被 provider 识别并可自动装配的主体
- 它不是单个业务类里偶然塞进去的临时变量

### 2.7 `#extra`

`extra` 在 `mis-core` 中已看到明确的 provider 级证据：

- `MisRecRuleContextProvider` 会扫描表达式；若包含 `#extra`，则按 `bizEntry` / 历史态自动补齐 `extra`
- 该对象来源于 `recDataService.getRecExtra(...)`

代码证据：
- `modules/mis/egova-urbanpro-mis-rest/src/main/java/com/egova/mis/rec/rule/provider/MisRecRuleContextProvider.java:149-151`
- `modules/mis/egova-urbanpro-mis-rest/src/main/java/com/egova/mis/rec/rule/provider/MisRecRuleContextProvider.java:188-211`

当前判断：
- `#extra` 不是文档想象出来的扩展主体，而是 MIS 规则上下文里已被 provider 识别的正式主体
- 但它与样式场景中的 `#recExtra` 不是同一命名，skill 文档里需要明确区分

### 2.8 `#recTags`

`recTags` 在 `mis-core` 中已看到明确 provider 注入：

- `MisRecRuleContextProvider` 若扫描到 `#recTags`，会通过 `recTagService.getRecTagList(...)` 查询案件标签列表并放入上下文

代码证据：
- `modules/mis/egova-urbanpro-mis-rest/src/main/java/com/egova/mis/rec/rule/provider/MisRecRuleContextProvider.java:214-223`

当前判断：
- `#recTags` 是 MIS 规则场景可用的集合型主体
- 它更适合标签命中、标签包含、标签数量等特定规则判断，不宜直接混进通用字段映射表

### 2.9 `#recSups`

`recSups` 在 `mis-core` 中已看到明确 provider 注入：

- `MisRecRuleContextProvider` 若扫描到 `#recSups`，会基于当前活动查询督办列表并放入上下文

代码证据：
- `modules/mis/egova-urbanpro-mis-rest/src/main/java/com/egova/mis/rec/rule/provider/MisRecRuleContextProvider.java:224-234`

当前判断：
- `#recSups` 属于 MIS 督办/催办相关扩展主体
- 与样式场景中的单对象 `#actSup` 应分开描述，避免混淆“规则上下文列表”与“样式场景扩展对象”

### 2.10 `#applyArdInst`

`applyArdInst` 在 `mis-core` 中已看到明确 provider 注入：

- `MisRecRuleContextProvider` 若扫描到 `#applyArdInst` 且当前存在 act 信息，会查询申请授权实例并放入上下文

代码证据：
- `modules/mis/egova-urbanpro-mis-rest/src/main/java/com/egova/mis/rec/rule/provider/MisRecRuleContextProvider.java:235-248`

当前判断：
- `#applyArdInst` 是明显偏 workflow 授权申请链路的专用主体
- 适合单独记为“MIS workflow 扩展主体”，不宜默认推广到所有消息/样式/菜单场景

### 2.11 `#reportRoleIds`

`reportRoleIds` 在 `mis-core` 中已看到明确 provider 注入：

- `MisRecRuleContextProvider` 若扫描到 `#reportRoleIds`，会通过来电记录与手机号反查举报人对应岗位标识列表并放入上下文

代码证据：
- `modules/mis/egova-urbanpro-mis-rest/src/main/java/com/egova/mis/rec/rule/provider/MisRecRuleContextProvider.java:251-305`

当前判断：
- `#reportRoleIds` 是非常业务化、场景化的集合主体
- 它说明正式系统规则里除了通用主体外，还可能存在按业务能力拼装的列表型变量

### 2.12 `#recDispatchFuncTimes`

`recDispatchFuncTimes` 在 `mis-core` 中已看到明确 provider 注入：

- `MisRecRuleContextProvider` 若扫描到 `#recDispatchFuncTimes`，会基于活动历史计算“从非专业部门阶段批转至专业部门阶段次数”并放入上下文

代码证据：
- `modules/mis/egova-urbanpro-mis-rest/src/main/java/com/egova/mis/rec/rule/provider/MisRecRuleContextProvider.java:308-318`

当前判断：
- 这是典型的“预计算结果型主体”
- skill 输出时应把它归为特定 MIS 规则扩展变量，而不是通用业务实体字段

### 2.13 `#recTimedDispatchs`

`recTimedDispatchs` 在 `mis-core` 中已看到明确 provider 注入：

- `MisRecRuleContextProvider` 若扫描到 `#recTimedDispatchs`，会查询当前活动对应的定时派遣列表并放入上下文

代码证据：
- `modules/mis/egova-urbanpro-mis-rest/src/main/java/com/egova/mis/rec/rule/provider/MisRecRuleContextProvider.java:320-325`

当前判断：
- `#recTimedDispatchs` 同样属于 MIS 规则场景中的集合型扩展主体
- 适合记录为“已确认存在”，但字段层面仍需后续继续拆解

### 2.14 `#timing`

本轮在 `mis-core` 中仍未直接看到统一的 `context.put("timing", ...)` 或 `#timing` 注入证据。

但已看到：
- `RecTimingCommonConfigFilter` 会为时限配置过滤构造规则上下文
- 该上下文至少包含 `bizEntry`、`actInst`、`userDetails`、`username`

代码证据：
- `modules/mis/egova-urbanpro-mis-rest/src/main/java/com/egova/mis/timing/RecTimingCommonConfigFilter.java:158-176`

当前结论：
- `mis-core` 确实存在时限相关 SpEL 使用场景
- 但“是否存在统一 `#timing` 主体”本轮仍未确认，skill 文档里应保守表述

---

## 3. 按场景整理

## 3.1 消息配置 / 规则触发场景

### 已确认主体

消息相关代码里反复出现：
- `bizEntry`
- `actInst`
- 部分场景还会有 `userDetails`、`username`

代表性代码：
- `WorkflowMsgActionExtendServiceImpl.java:173-177`
- `WorkflowArrivalMsgServiceImpl.java:217-218`
- `MisSendMsgRuleCheckUtils.java:47-50`
- `MisImSendMsgUtils.java:289-292`

结论：
- 如果 skill 面向 MIS 消息/提醒类场景，可优先考虑 `#bizEntry`、`#actInst`
- 若涉及当前用户，还可考虑 `#userDetails`、`#username`

## 3.2 workflow / 流转配置 / 自动处理场景

### 已确认主体

workflow 相关场景里，目前证据最强的是：
- `bizEntry`
- `actInst`
- 许多扩展实现中还会补 `userDetails`、`username`
- MIS 规则 provider 体系下还已确认存在 `applyArdInst`

代表性代码：
- `MisWorkflowBizServiceImpl.java:45-47`
- `WorkflowPostponeArdConfigHandlerImpl.java:82-83`
- `MisTransitPageConfigServiceImpl.java:122-123`
- `MisTransitPageConfigExtendImpl.java:64-67`
- `MisGetApplyInfoWorkflowExtendHandler.java:102-105`
- `MisRecRuleContextProvider.java:235-248`

结论：
- 这是 MIS 中与 core 类似、最稳定的一类规则场景
- 若涉及授权申请链路，可继续关注 `#applyArdInst` 这类 workflow 扩展主体

## 3.3 菜单 / 操作入口场景

### 已确认主体

`OneClickTransitMenuHandler` 等代码表明，菜单或入口控制类场景中可见：
- `actInst`
- `userDetails`
- `username`

另有部分按钮/菜单 handler 会直接传 `bizEntry`

代表性代码：
- `OneClickTransitMenuHandler.java:111-113`
- `ApplyCancelMenuHandler.java:66`

结论：
- MIS 菜单场景可能不像 core 那样集中在一个统一 menu service 里，而是分散在各 handler
- 但 `bizEntry / actInst / userDetails / username` 这组主体已具备明确证据

## 3.4 案件显示样式场景

### 已确认主体

这是本轮最有价值的新发现之一。

`MisRecDisplayPropertyPlanServiceImpl` 里，样式计划会先扫描表达式里出现了哪些 key，再按需装配上下文。

当前明确看到的样式上下文主体有：
- `bizEntry`
- `actInst`
- `actInstTiming`
- `state`
- `recCond`
- `recExtra`
- `dispose`
- `recRemark`
- `actSup`

关键代码：
- `MisRecDisplayPropertyPlanServiceImpl.java:104-123`：定义可识别的上下文 key 枚举
- `MisRecDisplayPropertyPlanServiceImpl.java:148-166`：扫描表达式需要哪些 key
- `MisRecDisplayPropertyPlanServiceImpl.java:688-733`：构建样式 SpEL 上下文
- `MisRecDisplayPropertyPlanServiceImpl.java:763-800`：按需查询 `state` 等数据

这说明：
- MIS 的“案件显示样式”场景并不只支持 `bizEntry`
- 它是一个明显更丰富的 SpEL 场景，尤其适合状态、时限、督办、备注、附加信息等条件判断

对 skill 的启发：
- 样式场景若来自 MIS 侧，不能只写成“通常关注 `#bizEntry` / `#actInst`”
- 还应补入 `#state` 以及样式专有上下文（至少注明这是 MIS 扩展场景中的额外能力）

## 3.5 时限 / timing 场景

### 已确认主体

`RecTimingCommonConfigFilter` 中已看到时限配置过滤使用以下上下文：
- `bizEntry`
- `actInst`
- `userDetails`
- `username`

代码证据：
- `RecTimingCommonConfigFilter.java:158-176`

当前保守结论：
- MIS 时限相关规则场景已明确支持上述主体
- 但本轮仍未确认统一的 `#timing` 主体名

## 3.6 打印场景

### 已确认主体

`MisRecPrintParamProvider` 中使用 `StandardEvaluationContext` 并直接：
- `ctx.setVariable("bizEntry", rec)`

代码证据：
- `MisRecPrintParamProvider.java:167,178`

结论：
- 打印模板 / 打印参数场景中，`bizEntry` 至少是明确可用的

---

## 4. 当前最稳妥的 mis-core 结论

如果只保留代码证据最强的部分，可以先写成：

- MIS 消息 / workflow / 流转配置：稳定支持 `bizEntry`、`actInst`
- MIS 很多规则场景还常见 `userDetails`、`username`
- MIS 规则 provider 已明确支持 `#state`
- MIS 规则 provider 还已确认存在 `#extra`、`#recTags`、`#recSups`、`#applyArdInst`、`#reportRoleIds`、`#recDispatchFuncTimes`、`#recTimedDispatchs` 等扩展主体
- MIS 案件显示样式场景支持面更广，至少已见 `bizEntry`、`actInst`、`state`，还包括 `actInstTiming`、`actSup`、`recExtra`、`recCond`、`recRemark` 等样式专有上下文
- MIS 时限场景已见 `bizEntry`、`actInst`、`userDetails`、`username`，但统一 `#timing` 主体尚未确认

---

## 5. 对 skill 回补的建议

1. `scene-case-display-style.md`
   - 应补入：若对接的是 MIS 样式计划类能力，除 `#bizEntry` 外，还可能支持 `#actInst`、`#state`
   - 可以再注明：MIS 样式场景还存在一些更专用的扩展主体，不宜在主 skill 中一概写成通用能力

2. `scene-message-rule.md`
   - 可以增强为：MIS 消息/提醒类规则中，`#bizEntry`、`#actInst` 是强证据主体；若涉及当前用户，也常见 `#userDetails`、`#username`
   - 若是 MIS 规则 provider 驱动的深度规则场景，还可能出现 `#extra`、`#recTags`、`#recSups` 等集合/扩展主体

3. `spel-subjects.md`
   - `#state` 可在 MIS 范围内提高确信等级
   - 对 `#extra` 这类 provider 级扩展主体，可新增“正式系统已见 / MIS 规则扩展主体”口径说明
   - 但要注明其证据主要来自 MIS 规则 provider 与相关业务实现，不要无差别推广到所有 core 场景

4. `spel-fields.md`
   - 通用字段表仍应以 `bizEntry / state / actInst / userDetails / timing` 这类已较稳定主体为主
   - 对 `recTags / recSups / reportRoleIds / recTimedDispatchs` 这类集合型或业务化扩展主体，更适合先写入 research，不要直接伪装成稳定字段表

5. `SKILL.md`
   - 建议把“不同项目 / 子系统 / 场景对主体支持范围不同”写得更明确
   - 尤其区分 `core` 与 `mis-core` 的主体支持差异
