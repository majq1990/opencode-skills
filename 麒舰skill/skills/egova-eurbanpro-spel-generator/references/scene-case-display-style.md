# 案件显示样式场景

> 用于根据案件条件控制列表、详情页或其他界面中的展示效果，如标红、高亮、标签、颜色和特殊样式。
> 本文档会区分“通用样式场景的稳妥主体”与“MIS 样式扩展场景的额外上下文”，避免把局部扩展能力误写成所有样式场景的通用能力。

## 场景说明

该场景主要关注“案件应如何展示”，而不是“流程如何流转”或“菜单是否显示”。

常见目标包括：

- 某类案件标红显示
- 到某个阶段时高亮
- 满足条件时显示特殊标签
- 重要案件使用不同样式展示

---

## research 结论摘要

根据当前已完成的代码 research：

- **通用层面最稳妥的样式主体**
  - `#bizEntry`
  - `#actInst`
- **`#state`**
  - 在 MIS 范围内证据更强
  - 尤其在 MIS 样式计划场景中已看到明确上下文装配
  - 但不宜不加说明地推广成所有样式场景都统一支持
- **`#timing`**
  - 当前 research 尚未确认统一稳定的 `#timing` 主体注入点
  - 不能因为样式场景经常涉及“超时”“临近超时”，就直接把 `#timing` 写成已统一确认主体

### MIS 样式扩展场景的重要补充

在 MIS 样式计划相关实现中，已明确看到的上下文不只有：

- `bizEntry`
- `actInst`
- `state`

还包括一些样式专有或扩展上下文：

- `actInstTiming`
- `actSup`
- `recExtra`
- `recCond`
- `recRemark`
- `dispose`

这些扩展主体已根据代码补齐“类型 / 字段 / 注释”口径。需要特别注意：

- `#actInstTiming`、`#actSup`、`#recExtra`、`#recCond` 是对象型上下文，可继续访问其字段
- `#recRemark`、`#dispose` 在样式 SpEL 上下文中是布尔值，不是对象，不能继续写成 `#recRemark?.content` 或 `#dispose?.xxx`
- 以下字段来自 MIS 样式计划链路的实体代码，可作为该特定场景下的字段候选；不要直接推广成所有项目、所有样式场景通用字段

这说明：

- MIS 样式场景支持面明显比“只写 `#bizEntry` / `#state` / `#actInst`”更丰富
- 但这些扩展主体不宜在主 skill 中包装成所有项目都通用的默认能力
- 对这些扩展主体，应补清楚“实际类型、可用字段或写法、字段注释 / 适用条件”，而不是凭经验编造字段名


---

## 常见需求表述

- 投诉案件在列表里标红
- 已超时案件高亮显示
- 特殊来源案件显示特殊标签
- 某阶段案件用另一种颜色展示
- 满足条件时在详情页显示重点标识

---

## 场景识别信号

如果需求重点是控制“颜色、标签、是否高亮、展示形式”，通常优先归为案件显示样式场景。

典型关键词：

- 标红
- 高亮
- 样式
- 标签
- 颜色
- 展示效果
- 特殊显示

---

## 常用判断对象

该场景通常优先关注：

- 案件信息
- 流程 / 节点信息
- 状态信息
- 部分项目里的时限或扩展样式信息

### 通用层优先主体

可优先检查的主体包括：

- `#bizEntry`
- `#actInst`

### MIS 范围内证据更强的主体

- `#state`

### 需保守对待的主体

- `#timing`
  - 当前尚未确认统一稳定的主体名

### MIS 样式扩展场景可见的额外上下文

| 主体 | 实际类型 / 来源 | 可用字段或写法 | 字段注释 / 适用条件 |
|------|-----------------|----------------|---------------------|
| `#actInstTiming` | `WfActTiming`，按当前活动 `actId` 查询活动时限记录 | `timeStateId`、`timeSysId`、`deadlineTime`、`warningTime`、`startTime`、`endTime`、`used`、`usedChar`、`remain`、`remainChar`、`bundleTimeStateId`、`bundleDeadlineTime`、`bundleWarningTime`、`bundleRemain`、`bundleRemainChar`、`timingUnitId` | 活动实例时限 / 计时信息。适合“已超时”“临近超时”“剩余时限”“阶段截止时间”等样式条件；字段为空时要注意空安全。 |
| `#actSup` | `WfActSup`，按当前活动查询最新督办记录 | `supID`、`recID`、`actID`、`supHumanID`、`replyHumanID`、`replyPartID`、`replyPartName`、`actSupStateID`、`actSupStateName`、`supMemo`、`supDate`、`theoryReplyDays`、`theoryReplyDate`、`replyMemo`、`replyDate`、`supType`、`supTitle`、`supDeadlineTime`、`supLevel`、`urgentType`、`lastSupActFlag` | 活动督办 / 催办信息。适合“有督办记录”“督办状态为某值”“紧急督办”“督办未回复”等样式条件。 |
| `#recExtra` | `AbstractMisRecExtra`，按案件 `recId` 查询案件附加信息 | `forthTypeId`、`forthTypeName`、`fifthTypeId`、`fifthTypeName`、`sixthTypeId`、`sixthTypeName`、`seventhTypeId`、`seventhTypeName`、`replyTwoHoursDeadline`、`replyTwoHoursFlag`、`housingEstateId`、`housingEstateName`、`disposeDeadline`、`disposeDeadlineUnit`、`mainRecId`、`relationRecId`、`mergeId`、`mergeType`、`stageArchiveDeadlineTime`、`relationRecTypeId`、`roadSectionId`、`roadSectionName`、`difficultRecFlag`、`orderTypeId`、`orderTypeName`、`reworkFlag`、`thirdPartyRepeatFlag`、`thirdPartyMinorFlag`、`replyDeadline`、`replyDeadlineUnit`、`cameraCode`、`plateNo` | 案件扩展字段。适合“四/五/六/七级类别”“小区/路段”“合并/关联案件”“疑难件”“工单属性”“限时回复”“第三方标识”等样式条件。 |
| `#recCond` | `SysEventNewInstCondition`，按案件 `condId` 查询事项立案条件 | `id`、`domainId` / `bizId`、`newInstCond`、`archiveCond`、`belongToDeptName`、`belongToDeptId`、`sendToDeptName`、`sendToDeptId`、`typeId`、`newInstCondId`、`archiveCondId`、`levelId` | 事项立案 / 结案条件配置。适合“按立案条件、结案条件、主管单位、责任单位、事项等级命中样式”的场景。 |
| `#recRemark` | 布尔值，代码中由备注列表是否非空计算：`CollectionUtils.isNotEmpty(recRemarks)` | 只能作为布尔条件使用：`#recRemark == true`、`#recRemark`、`!#recRemark` | 表示当前权限范围内是否能查到该案件备注。不是备注对象列表，不能直接访问 `content`、`humanName` 等字段。 |
| `#dispose` | 布尔值，代码中遍历案件活动，存在专业部门阶段则为 `true` | 只能作为布尔条件使用：`#dispose == true`、`#dispose`、`!#dispose` | 表示案件流程中是否存在“专业部门阶段”活动。不是处置对象，不能直接访问处置字段。 |

> 注意：这些扩展上下文是 MIS 样式计划类能力中的代码证据，不应直接推广成所有项目、所有样式场景的默认支持范围。
>
> 注意：字段表只列出当前代码证据中更适合样式判断的候选字段，不代表实体全部字段；生成表达式时仍要结合业务值域确认具体编码 / 名称。

---

## 常见条件类型

### 1. 案件属性条件

例如：

- 问题来源
- 案件类型
- 区域
- 上报渠道

通常优先考虑 `#bizEntry`。

### 2. 流程条件

例如：

- 当前流程在某节点时显示某种样式
- 当前处于某办理环节时高亮

通常优先考虑 `#actInst`。

### 3. 状态条件

例如：

- 当前阶段
- 当前核实状态
- 当前处置状态

在 MIS 样式场景中通常可优先考虑 `#state`；但如果当前项目不是 MIS 样式计划这类明确链路，就不应把 `#state` 当成无争议通用主体。

### 4. 时间 / 时限条件

例如：

- 是否超时
- 上报后多久未处理
- 当前是否处于某个时间区间

这类条件不能直接默认写成 `#timing`。

应先判断：

- 当前项目是否真的提供了统一 `#timing` 主体
- 还是实际通过 MIS 样式扩展上下文中的 `actInstTiming` 等对象来承载时限信息

### 5. MIS 样式扩展条件

例如：

- 督办相关信息
- 备注 / 附加信息 / 处置信息命中某条件

这类条件可能落到 `#actSup`、`#recExtra`、`#recCond` 等 MIS 样式扩展主体上；如果只是判断是否存在备注或是否进入过专业部门阶段，则分别使用布尔主体 `#recRemark`、`#dispose`。只有在已确认当前场景就是 MIS 样式计划类能力时才建议使用。

---

## 生成表达式时的推荐步骤

1. 先确认需求目标是样式展示，而不是菜单过滤或流程流转
2. 明确要控制的展示效果是什么
3. 把“效果”和“命中条件”拆开
4. 提取触发该样式的业务条件
5. 映射到案件、流程、状态或样式扩展上下文
6. 对“超时”“阶段”类表述先确认其真实落点
7. 若值不明确，先标注假设
8. 输出候选表达式并解释命中后会出现什么效果

---

## 常见歧义点

### 1. 样式效果和触发条件混在一起

例如“重点案件标红”里，“标红”是效果，“重点案件”才是判定条件。

### 2. “超时”“重点”“紧急”等词缺少字段定义

这些业务词通常不能直接生成表达式，需要确认具体字段或规则来源。

### 3. 阶段、状态、节点混用

用户说“受理阶段标红”，但项目里可能对应：

- 状态字段
- 流程节点
- 阶段编码

不能只凭“阶段”二字直接写死。

### 4. 样式配置本身不在 SpEL 中

SpEL 通常只负责“是否命中条件”；具体显示成什么颜色、什么标签，通常在其他配置项里定义。

### 5. 误把 MIS 扩展上下文当成全项目通用

例如看到 MIS 样式里有 `actInstTiming`，就直接在其他项目样式场景里默认使用，这是不稳妥的。

---

## 输出建议

推荐输出结构：

- 场景识别：案件显示样式
- 条件提取
- 主体 / 字段映射
- 歧义点 / 假设项
- 候选 SpEL
- 命中效果说明

---

## 示例

**需求**：

> 投诉来源的案件在受理阶段时标红显示。

**推荐处理思路**：

- 场景识别：案件显示样式
- 效果：标红显示
- 条件 1：问题来源 = 投诉
- 条件 2：案件处于受理阶段
- “问题来源”通常优先映射到 `#bizEntry`
- “受理阶段”可能落到 `#state`，也可能落到 `#actInst`
  - 如果当前是 MIS 样式计划类场景，`#state` 证据更强
  - 如果用户说的是流程环节，则也可能更接近 `#actInst`
- 若“投诉”“受理阶段”的实际值域不明确，应提醒先确认

例如在“投诉按名称比较、受理阶段按 MIS 状态名称比较”的假设下，可先给候选写法：

```spel
#bizEntry?.eventSrcName == '投诉' && #state?.verifyMsgStateName == '受理'
```

该表达式只表示“是否命中标红条件”；至于标红颜色、样式名、标签文案，通常仍在样式配置项中单独定义。

---

## 注意事项

- 样式场景下要区分“命中条件”和“展示效果”
- `#bizEntry`、`#actInst` 是当前更稳妥的通用优先主体
- `#state` 在 MIS 样式场景中证据更强，但不宜无差别推广成所有样式场景通用主体
- 不要因为需求涉及超时，就直接把 `#timing` 写成已确认统一支持的主体
- 若业务词没有明确字段定义，不应直接编造成表达式
