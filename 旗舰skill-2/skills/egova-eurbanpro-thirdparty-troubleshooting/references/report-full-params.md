# REPORT 完整参数清单

## 用途
这份文件保留 `REPORT` 上报接口的完整参数列表，用于：
- 生成“字段尽量完整”的联调示例
- 对照现场参数缺失项
- 在最小示例之外补齐可选字段

## 顶层请求结构
| 参数名 | 类型 | 说明 | 备注 |
| --- | --- | --- | --- |
| `uid` | `string` | 请求唯一标识 | 必传，可用 `UUID.randomUUID().toString()` 生成 |
| `senderCode` | `string` | 发送方标识 | 必传，对应第三方平台编码 |
| `action` | `string` | 接口动作 | 必传，固定为 `REPORT` |
| `data` | `object` | 工单对象 | 必传 |

## data 参数清单
### 必传字段
| 参数名 | 类型 | 说明 | 备注 |
| --- | --- | --- | --- |
| `caseId` | `string` | 工单标识 | 必传 |
| `registerTime` | `string` | 登记时间 | 必传，格式 `yyyy-MM-dd HH:mm:ss` |
| `eventDesc` | `string` | 工单内容 | 必传 |
| `recTypeId` | `integer` | 工单类型 | 必传，参考 6.1 工单类型字典表 |
| `recTypeName` | `string` | 工单类型名称 | 必传，参考 6.1 工单类型字典表 |
| `eventSrcId` | `integer` | 工单来源标识 | 必传，参考 6.1 工单来源字典表 |
| `eventSrcName` | `string` | 工单来源名称 | 必传，参考 6.1 工单来源字典表 |
| `address` | `string` | 诉求详细地址 | 必传 |
| `medias` | `array<object>` | 多媒体列表 | 必传 |

### 常用可选字段
| 参数名 | 类型 | 说明 | 备注 |
| --- | --- | --- | --- |
| `caseHandleId` | `string` | 派单唯一标识 | 非必传 |
| `casNum` | `string` | 工单编号 | 非必传 |
| `openId` | `string` | 微信 OpenId | 非必传 |
| `dispatchTime` | `string` | 派单时间 | 非必传，格式 `yyyy-MM-dd HH:mm:ss` |
| `signTime` | `string` | 签收时间 | 非必传，格式 `yyyy-MM-dd HH:mm:ss` |
| `signDeadline` | `string` | 签收截止时间 | 非必传，格式 `yyyy-MM-dd HH:mm:ss` |
| `rollbackDeadline` | `string` | 回退截止时间 | 非必传，格式 `yyyy-MM-dd HH:mm:ss` |
| `disposeDeadlineTime` | `string` | 处置截止时间 | 非必传，工单处置时限（天/小时） |
| `title` | `string` | 工单标题 | 非必传 |
| `eventTypeId` | `integer` | 问题类型标识 | 非必传 |
| `eventTypeName` | `string` | 问题类型 | 非必传 |
| `mainTypeId` | `integer` | 大类标识 | 非必传 |
| `mainTypeName` | `string` | 大类名称 | 非必传 |
| `subTypeId` | `integer` | 小类标识 | 非必传 |
| `subTypeName` | `string` | 小类名称 | 非必传 |
| `thirdTypeId` | `integer` | 细类标识 | 非必传 |
| `thirdTypeName` | `string` | 细类名称 | 非必传 |
| `coordinateX` | `double` | 工单 X 坐标 | 非必传 |
| `coordinateY` | `double` | 工单 Y 坐标 | 非必传 |
| `districtId` | `integer` | 问题所属区县编码 | 非必传，部分现场工作流可能强依赖 |
| `districtName` | `string` | 问题所属区县名称 | 非必传，部分现场工作流可能强依赖 |
| `streetId` | `integer` | 街道标识 | 非必传 |
| `streetName` | `string` | 街道名称 | 非必传 |
| `communityId` | `integer` | 社区标识 | 非必传 |
| `communityName` | `string` | 社区名称 | 非必传 |
| `cellId` | `integer` | 网格标识 | 非必传 |
| `cellName` | `string` | 网格名称 | 非必传 |
| `dispatchOpinion` | `longtext` | 派单意见 | 非必传 |
| `signState` | `int` | 签收状态 | 非必传 |
| `sendTypeCode` | `string` | 交办类型 | 非必传 |
| `sendTypeName` | `string` | 交办类型名称 | 非必传 |
| `handleOrgCode` | `string` | 待处置部门编号 | 非必传 |
| `handleOrgName` | `string` | 待处置部门名称 | 非必传 |
| `caseStatus` | `integer` | 工单状态 | 非必传 |
| `urgentLevelId` | `int` | 紧急程度 | 非必传 |
| `keyword` | `string` | 关键词 | 非必传 |
| `caseMark` | `string` | 工单标签 | 非必传 |
| `evaluateContent` | `string` | 评价内容 | 非必传 |
| `accidentFlag` | `int` | 是否突发事件 | 非必传 |
| `instableFlag` | `int` | 是否不稳定因素 | 非必传 |
| `repeatCallFlag` | `int` | 是否重复来电 | 非必传 |
| `returnVisitFlag` | `int` | 是否回访 | 非必传，默认 `0` |
| `publicFlag` | `int` | 是否允许对外公开 | 非必传，默认 `0` |
| `rollbackFlag` | `int` | 是否允许回退 | 非必传，默认 `1` |
| `postponeFlag` | `int` | 是否允许延期 | 非必传，默认 `1` |
| `reHandleFlag` | `int` | 是否重办 | 非必传，默认 `0` |
| `callSubjectId` | `integer` | 来电主体标识 | 非必传 |
| `callSubjectName` | `string` | 来电主体名称 | 非必传 |
| `contact` | `string` | 来电号码 | 非必传 |
| `IdCardNo` | `string` | 证件号 | 非必传 |
| `callTime` | `date` | 来电时间 | 非必传 |
| `reporterName` | `string` | 来电人姓名 | 非必传 |
| `reporterAddress` | `string` | 来电人详细地址 | 非必传 |
| `reporterPublicFlag` | `int` | 是否公开举报人标识 | 非必传 |
| `genderId` | `integer` | 来电人性别 | 非必传 |
| `ageRangeId` | `int` | 来电人年龄范围标识 | 非必传 |
| `telReply` | `string` | 答复号码 | 非必传，多个用逗号分隔 |

## medias 子项
| 参数名 | 类型 | 说明 | 备注 |
| --- | --- | --- | --- |
| `mediaName` | `string` | 多媒体名称 | 必传 |
| `mediaPath` | `string` | 多媒体完整地址 | 与 `content` 二选一必传 |
| `content` | `string` | Base64 内容 | 与 `mediaPath` 二选一 |
| `mediaUsage` | `string` | 文件类型 | 必传，常见值：上报 / 核查 / 核实 / 处置 / 自处置 |
| `mediaTypeId` | `integer` | 多媒体关联类型 | 必传，默认常传 `1` |

## 返回关键值
| 参数名 | 类型 | 说明 | 备注 |
| --- | --- | --- | --- |
| `recId` | `int` | 区级平台案件标识 | 上报成功后返回 |
| `taskNum` | `string` | 区级平台案件号 | 上报成功后返回 |

## 生成示例时怎么用
- 先看 `references/reporting-and-query.md` 拿到最小必填字段
- 再看本文件补齐需要展示的可选字段
- 若要判断哪些可选字段在现场其实是必填，转 `egova-eurbanpro-thirdparty-preparation-guide` 的 `references/field-alignment-checklist.md`
- 若要生成“联调展示型完整示例”，优先补 `title`、区划字段、坐标、联系人、多媒体等高频字段
