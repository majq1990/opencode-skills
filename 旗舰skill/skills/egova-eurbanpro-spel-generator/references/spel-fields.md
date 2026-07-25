# SpEL 字段映射

> 用于整理当前项目资料中已出现的 SpEL 字段映射，帮助把业务口语描述映射为可生成表达式的字段路径。

## 使用说明

> 强提醒：当前表仅整理“已收录、已整理”的字段证据，不代表项目中的全部可用字段。若正式系统现存表达式、历史配置或代码实现中出现了本表未收录的字段，应优先视为“待补充证据”，而不是直接判定该字段不存在或不可用。

生成表达式时，建议按以下顺序使用本表：

1. 先识别业务场景
2. 再判断应该使用哪个主体
3. 从本表中查找对应字段
4. 最后确认比较值是名称、编码还是标识

> 注意：本表仅整理当前 `SPEL表达式.md` 中已出现的信息，不代表项目全部可用字段。

---

## 一、`#bizEntry` 字段

`#bizEntry` 表示案件信息，适合承载案件本身属性。

### 高频字段

| 业务含义 | 字段路径 |
|---|---|
| 案件标识 | `#bizEntry?.recId` |
| 地址 | `#bizEntry?.address` |
| 区域标识 | `#bizEntry?.districtId` |
| 区域名称 | `#bizEntry?.districtName` |
| 街道标识 | `#bizEntry?.streetId` |
| 街道名称 | `#bizEntry?.streetName` |
| 社区标识 | `#bizEntry?.communityId` |
| 社区名称 | `#bizEntry?.communityName` |
| 网格标识 | `#bizEntry?.cellId` |
| 网格名称 | `#bizEntry?.cellName` |
| 案件类型标识 | `#bizEntry?.recTypeId` |
| 案件类型名称 | `#bizEntry?.recTypeName` |
| 问题来源标识 | `#bizEntry?.eventSrcId` |
| 问题来源名称 | `#bizEntry?.eventSrcName` |
| 问题类型标识 | `#bizEntry?.eventTypeId` |
| 问题类型名称 | `#bizEntry?.eventTypeName` |
| 问题等级标识 | `#bizEntry?.eventGradeId` |
| 问题等级名称 | `#bizEntry?.eventGradeName` |
| 问题级别标识 | `#bizEntry?.eventLevelId` |
| 问题级别名称 | `#bizEntry?.eventLevelName` |
| 问题性质标识 | `#bizEntry?.eventPropertyId` |
| 问题性质名称 | `#bizEntry?.eventPropertyName` |
| 问题描述 | `#bizEntry?.eventDesc` |
| 业务标识 | `#bizEntry?.bizId` |
| 业务名称 | `#bizEntry?.bizName` |

### 补充字段

| 业务含义 | 字段路径 |
|---|---|
| x坐标 | `#bizEntry?.coordinateX` |
| y坐标 | `#bizEntry?.coordinateY` |
| 上报责任网格标识 | `#bizEntry?.reportDutyGridId` |
| 上报责任网格名称 | `#bizEntry?.reportDutyGridName` |
| 上报责任网格类型标识 | `#bizEntry?.reportDutyGridTypeId` |
| 大类标识 | `#bizEntry?.mainTypeId` |
| 大类名称 | `#bizEntry?.mainTypeName` |
| 小类标识 | `#bizEntry?.subTypeId` |
| 小类名称 | `#bizEntry?.subTypeName` |
| 细类标识 | `#bizEntry?.thirdTypeId` |
| 细类名称 | `#bizEntry?.thirdTypeName` |

### 常见映射提示

- “案件类型” → 优先看 `recTypeId` / `recTypeName`
- “问题来源” → 优先看 `eventSrcId` / `eventSrcName`
- “区域/街道/社区/网格” → 优先看对应行政区划字段
- “问题类别/等级/级别/性质” → 注意这些词对应不同字段，不能混用

---

## 二、`#state` 字段

`#state` 表示案件状态信息，适合承载状态类条件。

| 业务含义 | 字段路径 |
|---|---|
| 急要件标志 | `#state?.urgentFlag` |
| 强制处置 | `#state?.forceHandleFlag` |
| 锁定标识 | `#state?.lockedFlag` |
| 是否需要发送市民核查消息 | `#state?.sendPubCheckTaskFlag` |
| 核查状态标识 | `#state?.checkMsgStateId` |
| 核实状态标识 | `#state?.verifyMsgStateId` |
| 补采状态标识 | `#state?.regatherMsgStateId` |
| 复查状态标识 | `#state?.reviewMsgStateId` |
| 多媒体丢失标志 | `#state?.mediaLostFlag` |
| 上报状态 | `#state?.reportState` |
| 派遣状态 | `#state?.disposeState` |
| 上一次派遣状态 | `#state?.preDisposeState` |
| 重复案件状态标志 | `#state?.repeatState` |
| 显示样式标识 | `#state?.displayStyleId` |
| 问责状态 | `#state?.procAccountStateId` |
| 重点案卷标识 | `#state?.isImportantRec` |
| 案件漏报审核状态 | `#state?.missReportCheckStatus` |
| 发送状态 | `#state?.sendState` |
| 能否吹哨标识 | `#state?.whistleFlag` |
| 指定派遣标志 | `#state?.appointedDispStatus` |
| 处置部门超期标识 | `#state?.disposeOvertimeFlag` |
| 催办状态标识 | `#state?.procPressStateId` |
| 案件签收状态 | `#state?.signinState` |
| 督查考核案件状态标识 | `#state?.supervisionCheckStateId` |
| 流程状态标志 | `#state?.wfStateId` |
| 流程状态关联时间 | `#state?.wfStateRelTime` |
| 案件合并标志 | `#state?.mergeFlag` |
| 案件合并审核标志 | `#state?.mergeAuditFlag` |
| 是否自处置标志 | `#state?.patrolDealFlag` |

### 常见映射提示

- “核实状态” → 优先看 `verifyMsgStateId`
- “核查状态” → 优先看 `checkMsgStateId`
- “复查状态” → 优先看 `reviewMsgStateId`
- “是否重点案件” → 优先看 `isImportantRec`
- “显示样式相关状态” → 优先看 `displayStyleId`

---

## 三、`#userDetails` 字段

`#userDetails` 表示当前用户信息。

| 业务含义 | 字段路径 |
|---|---|
| 租户标识 | `#userDetails?.tenantId` |
| 人员名称 | `#userDetails?.humanName` |
| 部门标识 | `#userDetails?.unitId` |
| 部门名称 | `#userDetails?.unitName` |
| 区域标识 | `#userDetails?.regionId` |
| 区域名称 | `#userDetails?.regionName` |
| 账号名称 | `#userDetails?.username` |

### 常见映射提示

- “当前用户所在部门” → `unitId` / `unitName`
- “当前用户所在区域” → `regionId` / `regionName`
- “当前用户账号” → `username`
- “当前人员名称” → `humanName`

---

## 四、`#actInst` 字段

`#actInst` 表示案件流程实例信息。

### 高频字段

| 业务含义 | 字段路径 |
|---|---|
| 活动标识（数字） | `#actInst?.id` |
| 活动标识（字符串） | `#actInst?.actId` |
| 阶段标识 | `#actInst?.actDefId` |
| 活动定义名称 | `#actInst?.actDefName` |
| 流程定义标识 | `#actInst?.procDefId` |
| 上阶段定义标识 | `#actInst?.preActDef` |
| 活动状态标识 | `#actInst?.actStateId` |
| 活动状态名称 | `#actInst?.actStateName` |
| 处理人标识 | `#actInst?.humanId` |
| 处理人名称 | `#actInst?.humanName` |
| 处理岗位标识 | `#actInst?.roleId` |
| 处理岗位名称 | `#actInst?.roleName` |
| 部门标识 | `#actInst?.unitId` |
| 部门名称 | `#actInst?.unitName` |

### 补充字段

| 业务含义 | 字段路径 |
|---|---|
| 开始时间 | `#actInst?.startTime` |
| 结束时间 | `#actInst?.endTime` |
| 更新时间 | `#actInst?.updateTime` |
| 业务主体标识 | `#actInst?.bizEntryId` |
| 参与者标识 | `#actInst?.partId` |
| 参与者名称 | `#actInst?.partName` |
| 参与者类型 | `#actInst?.partType` |
| 流程引擎实例标识 | `#actInst?.procInstId` |
| 流程菜单 | `#actInst?.menuSet` |
| 活动属性标识 | `#actInst?.actPropertyId` |
| 主协办类型标识 | `#actInst?.priSubTypeId` |
| 移交工作项类型标识 | `#actInst?.transItemTypeId` |
| 移交工作项类型名称 | `#actInst?.transItemTypeName` |
| 流程版本 | `#actInst?.procVersion` |
| 参与者全局唯一id | `#actInst?.partUid` |
| 人员全局唯一id | `#actInst?.humanUid` |
| 岗位全局唯一id | `#actInst?.roleUid` |
| 部门全局唯一id | `#actInst?.unitUid` |
| 流程引擎类型标识 | `#actInst?.engineTypeId` |
| 申请授权信息 | `#actInst?.applyInfo` |
| 并行标识 | `#actInst?.parallelId` |
| task_id 原始值 | `#actInst?.taskId` |
| init_task_id 初始值 | `#actInst?.initTaskId` |
| 授权类型 | `#actInst?.ardTypeId` |
| 授权状态 | `#actInst?.ardStateId` |
| 办理时间 | `#actInst?.assignTime` |

### 常见映射提示

- “当前节点 / 当前环节” → 优先看 `actDefId` / `actDefName`
- “流程定义” → `procDefId`
- “处理人 / 办理人” → `humanId` / `humanName`
- “处理岗位” → `roleId` / `roleName`

---

## 五、`#timing` 字段

`#timing` 表示在办计时信息。

### 高频字段

| 业务含义 | 字段路径 |
|---|---|
| 计时状态标识 | `#timing?.time_state_id` |
| 截止时间 | `#timing?.deadline_time` |
| 警告时间 | `#timing?.warning_time` |
| 开始时间 | `#timing?.start_time` |
| 结束时间 | `#timing?.end_time` |
| 已用时间（小时） | `#timing?.used` |
| 已用时间描述 | `#timing?.used_char` |
| 剩余时限（小时） | `#timing?.remain` |
| 剩余时限描述 | `#timing?.remain_char` |
| 截止时限（小时） | `#timing?.deadline_limit` |
| 截止时限描述 | `#timing?.deadline_limit_char` |
| 警告时限（小时） | `#timing?.warning_limit` |
| 警告时限描述 | `#timing?.warning_limit_char` |

### 补充字段

| 业务含义 | 字段路径 |
|---|---|
| 计时方案标识 | `#timing?.time_sys_id` |
| 计时刷新时间 | `#timing?.refresh_time` |
| 绑定计时状态标识 | `#timing?.bundle_time_state_id` |
| 绑定标识 | `#timing?.bundle_id` |
| 绑定截止时间 | `#timing?.bundle_deadline_time` |
| 绑定警告时间 | `#timing?.bundle_warning_time` |
| 绑定截止时限（小时） | `#timing?.bundle_deadline_limit` |
| 绑定截止时限描述 | `#timing?.bundle_deadline_limit_char` |
| 绑定警告时限（小时） | `#timing?.bundle_warning_limit` |
| 绑定警告时限描述 | `#timing?.bundle_warning_limit_char` |
| 绑定已用时间（小时） | `#timing?.bundle_used` |
| 绑定已用时间描述 | `#timing?.bundle_used_char` |
| 绑定剩余时限（小时） | `#timing?.bundle_remain` |
| 绑定剩余时限描述 | `#timing?.bundle_remain_char` |
| 原始截止时限 | `#timing?.clean_time_limit` |
| 原始警告 | `#timing?.clean_warning_limit` |
| 计时重置时间 | `#timing?.reset_time` |
| 绑定计时方案标识 | `#timing?.bundle_time_sys_id` |
| 停止用时 | `#timing?.stop_used` |

### 常见映射提示

- “是否超时” → 常需结合 `remain`、`deadline_time`、`used` 等字段理解
- “剩余时限” → `remain` / `remain_char`
- “截止时间” → `deadline_time`
- “警告时间” → `warning_time`

---

## 六、`#username`

`#username` 是当前用户名本身，不是对象字段。

### 常见写法

| 业务含义 | 表达方式 |
|---|---|
| 当前用户名等于某人 | `#username == '某人'` |
| 当前用户名不等于某人 | `#username != '某人'` |

### 使用提示

- 如果只需要比较当前人名，`#username` 比 `#userDetails` 更直接
- 如果需要部门、区域等更多属性，优先切回 `#userDetails`

---

## 现有表达式示例

以下示例已出现在当前项目资料中：

```spel
#bizEntry?.recTypeId == 1
#bizEntry?.eventSrcId == 1
#bizEntry?.recTypeId == 1 && #bizEntry?.eventSrcId == 1
#bizEntry?.recTypeId == 1 && #username == '樊考'
#bizEntry?.recTypeId == 1 || #bizEntry?.recTypeId == 2
#state?.verifyMsgStateId == 4
#actInst?.actDefId != 'artificial_597c44be-382c-462d-ad12-f0ffb7ba7407'
```

---

## 常见误区

- 名称字段和标识字段混用，例如 `eventSrcName` 与 `eventSrcId`
- 把状态字段误写到流程主体里，或反过来
- 忘记 `#username` 不是对象，不能写成 `#username?.xxx`
- `#timing` 字段是下划线命名，不能擅自改成驼峰
- 在字段未出现在资料中时，直接编造路径
