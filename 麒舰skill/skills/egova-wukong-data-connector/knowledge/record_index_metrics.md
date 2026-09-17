# 悟能案件与人员指标枚举参考

本文件整理来自现场 Java 枚举的指标定义，用于在案件指标统计、分组统计、人员/监督员排行、诊断和 SQL/ddcat 表查询场景中识别 `groupList`、排序字段、展示标题、人员归属字段和底层表字段。这里的 `value` 可作为悟能动态指标字段名；`text` 可作为默认展示名称；`fieldName` / `table` 表示指标使用的底层表字段线索。走悟能 `REC_INDEX_*` 接口时，返回字段通常仍是 `groupList` 的 `value`，不要把底层字段当成接口返回字段；走 SQL/ddcat/现场表查询时，可用底层字段解释口径和生成查询。

## 使用规则

- 用户提到“上报数、处置数、办结数、结案数、按期处置率、满意率、平均处置时长”等案件指标时，先在本文件查 `value`，不要把已收录指标当成未知字段反复追问。
- “办结数”默认按案件指标里的 `archive`（结案数）处理；如现场明确区分“办结”和“结案”，再按现场口径调整。
- `REC_INDEX_SUMMARY` 和各类 `REC_INDEX_*` 分组接口的动态返回字段通常与 `groupList` 中的指标 `value` 同名。
- 案件数量指标默认来自 `to_stat_info` 表，`fieldName` 的 Java 驼峰名可对应数据库下划线字段，例如 `report`/上报数使用 `to_stat_info.report_num`，`dispose`/处置数使用 `to_stat_info.dispose_num`，`archive`/结案数使用 `to_stat_info.archive_num`。
- `fieldName` 是底层字段线索，不是悟能接口响应字段；悟能指标接口返回仍优先按 `result.<value>` 或 `result[].<value>` 映射。
- 比率/时长/金额/评分类指标返回值可能是小数或金额，过滤脚本仍按 Number 兜底。
- 监督员/人员分组场景若按人员角色统计，优先参考“监督员指标分组”和“人员工作量指标”。
- 诊断接口 `REC_DIAGNOSIS` 的 `groupList` 或诊断类型可参考“诊断类型”。
- 本文件只确认指标枚举名和默认展示名，不替代接口详情文档；请求包装、筛选参数、返回结构仍以 detailDoc 或现场样例为准。

## 案件数量指标 RecordsIndexType

| value | text | fieldName |
|---|---|---|
| report | 上报数 | reportNum |
| dispose | 处置数 | disposeNum |
| inTimeDispose | 按期处置数 | intimeDisposeNum |
| inTimeToDispose | 按期处置中 | inTimeToDispose |
| overtimeDispose | 超期处置数 | overtimeDisposeNum |
| isImportantRec | 重点案件数 | isImportantRec |
| archive | 结案数 | archiveNum |
| toArchive | 未结案数 | toArchiveNum |
| cancel | 作废数 | cancelNum |
| accept | 受理数 | operateNum |
| inTimeAccept | 按时受理数 | operateNum |
| register | 立案数 | instNum |
| inTimeRegister | 按时立案数 | intimeInstNum |
| overTimeArchived | 超期结案案件 | overtimeArchiveNum |
| dispatch | 派遣数 | dispatchNum |
| needDispatch | 应派遣数 | needDispatchNum |
| inTimeDispatch | 按时派遣数 | intimeDispatchNum |
| accurDispatch | 准确派遣数 | accurDispatchNum |
| dispatchArchive | 派发数 | curActDefId |
| patrolDealFlag | 自行处置数 | patrolDealFlag |
| urgentFlag | 急要件 | urgentFlag |
| total | 案件总数 | recId |
| needArchiveNum | 应结案数 | needArchiveNum |
| inTimeArchiveNum | 按期结案数 | intimeArchiveNum |
| overtimeToArchiveNum | 超期未结案数 | overtimeToArchiveNum |
| toDispose | 未处置数 | toDisposeNum |
| needDispose | 应处置数 | needDisposeNum |
| overtimeToDispose | 超期未处置数 | overtimeToDisposeNum |
| validReport | 有效上报数 | validReportNum |
| validPublicReport | 公众有效上报数 | validPublicReportNum |
| verify | 核实数 | verifyNum |
| needVerify | 应核实数 | needVerifyNum |
| inTimeVerify | 按期核实数 | intimeVerifyNum |
| check | 核查数 | checkNum |
| needCheck | 应核查数 | needCheckNum |
| inTimeCheck | 按期核查数 | intimeCheckNum |
| event | 事件数量 | eventTypeId |
| eventDispose | 事件处置数量 | eventTypeId |
| part | 部件数量 | eventTypeId |
| partDispose | 部件处置数量 | eventTypeId |
| gridOvertimeAlarm | 网格红灯 | overtimeToDisposeNum |
| publicOvertimeAlarm | 公众红灯 | overtimeToDisposeNum |
| rework | 返工数 | reworkNum |
| back | 回退数 | backNum |
| peakHour | 高发时段 |  |
| toAccept | 待受理数 | toOperateNum |
| toRegister | 待立案数 | toInstNum |
| toDispatch | 待派遣数 | toDispatchNum |
| toCheck | 待核查数 | toCheckNum |
| publicReportNum | 公众举报数 | publicReportNum |
| reportStage | 上报阶段 | recId |
| dispatchStage | 派遣阶段 | recId |
| registerStage | 立案阶段 | recId |
| disposeStage | 处置阶段 | recId |
| checkStage | 核查阶段 | recId |
| archiveStage | 结案阶段 | recId |
| operateDirect | 当即办理数 | operateDirectArchiveNum |
| turn | 转办数 | recId |
| returnVisit | 回访数 | recId |
| verySatisfaction | 非常满意 | recId |
| satisfaction | 满意 | recId |
| satisfactionTotal | 满意总数 | recId |
| noSatisfaction | 不满意 | recId |

## 案件比率、时长、金额和评分指标 RecordsRateIndexType

| value | text | 口径说明 |
|---|---|---|
| disposeRate | 处置率 | 处置数 / 应处置数 |
| archiveRate | 结案率 | 结案数 / 应结案数 |
| dispatchRate | 派遣率 | 待现场确认分母 |
| accurDispatchRate | 准确派遣率 | 准确派遣数 / 应派遣数 |
| inTimeDispatchRate | 按期派遣率 | 按时派遣数 / 应派遣数 |
| verificationRate | 核查率 | 待现场确认分母 |
| publicReportRate | 公众举报率 | 待现场确认分母 |
| acceptRate | 受理率 | 待现场确认分母 |
| inTimeAcceptRate | 按期受理率 | 待现场确认分母 |
| inTimeDisposeRate | 按期处置率 | 按期处置数 / 应处置数 |
| inTimeArchiveRate | 按期结案率 | 按期结案数 / 应结案数 |
| overTimeArchiveRate | 超期结案率 | 超期结案数 / 应结案数 |
| toArchiveRate | 未结案率 | 未结案数 / 上报数 |
| registerRate | 立案率 | 待现场确认分母 |
| inTimeRegisterRate | 按时立案率 | 按时立案数 / 立案数 |
| AccurRegisterRate | 准确立案率 | 准确立案数 / 立案数 |
| overTimeRate | 超期未处置率 | 待现场确认分母 |
| satisfactionRate | 满意率 | 待现场确认分母 |
| avgHandleTime | 平均处置时长 | 时长指标 |
| rectificationRate | 整改率 | 待现场确认分母 |
| validReportRate | 有效上报率 | 有效上报数 / 上报数 |
| intimeVerifyRate | 按期核实率 | 按时核实数 / 应核实数 |
| intimeCheckRate | 按期核查率 | 按时核查数 / 应核查数 |
| synthesis | 综合评分 | 评分指标 |
| penaltyAmount | 处罚金额 | 金额指标 |
| avgAcceptTime | 平均受理时长 | 时长指标 |
| reworkRate | 返工率 | 待现场确认分母 |
| comprehensiveScore | 综合评分 | 自定义综合评分 |
| scoreOrder | 排名 | 根据排序字段确认排名 |
| satisfactionDegree | 满意度 | 待现场确认单位 |
| overtimeDisposeRate | 超期处置率 | 待现场确认分母 |

## 监督员指标分组 RecordsIndexSupervisorType

这些配置用于判断“按监督员/人员统计”时某类人员支持哪些指标、按哪个人员字段归属。

| value | text | fieldName | 支持指标 |
|---|---|---|---|
| report | 上报监督员 | reportPatrolId | report, validReport, validReportRate |
| verify | 核实监督员 | verifyPatrolId | verify, inTimeVerify, intimeVerifyRate |
| check | 核查监督员 | checkPatrolId | check, inTimeCheck, intimeCheckRate |
| dispose | 处置人员 | disposeHumanId | dispose, inTimeDispose, overtimeDispose, toDispose, needDispose, overtimeToDispose, inTimeDisposeRate, avgHandleTime, patrolDealFlag |
| dispatch | 派遣人员 | dispatchHumanId | dispatch, needDispatch, inTimeDispatch, accurDispatch, dispatchArchive, accurDispatchRate |
| archive | 结案人员 | archiveHumanId | archive, toArchive, overTimeArchived, needArchiveNum, imTimeArchiveNum, inTimeArchiveRate |
| register | 立案人员 | instHumanId | register, toRegister, registerRate, inTimeRegisterRate |
| accept | 受理人员 | operateHumanId | accept, toAccept |
| cancel | 作废人员 | cancelHumanId | cancel |

## 诊断类型 RecordsDiagnosisType

| value | text |
|---|---|
| trendDiagnosis | 趋势诊断 |
| eventDiagnosis | 类型诊断 |
| regionDiagnosis | 区域诊断 |

## 人员工作量指标 HumanIndexType

| value | text | fieldName | table |
|---|---|---|---|
| patrolReport | 监督员上报数 | patrol_report_num | to_patrol_eval |
| dispose | 处置数 | dispose_num | to_patrol_eval |
| check | 核查数 | check_num | to_patrol_eval |
| needVerify | 应核实数 | need_verify_num | to_patrol_eval |
| inTimeVerify | 按期核实数 | intime_verify_num | to_patrol_eval |
| overTimeVerify | 超时核实数 | overtime_verify_num | to_patrol_eval |
| overtimeToCheck | 超时未核查数 | overtime_to_check_num | to_patrol_eval |
| overtimeToVerify | 超时未核实数 | overtime_to_verify_num | to_patrol_eval |
| overtimeVerify | 超时核实数 | overtime_verify_num | to_patrol_eval |
| toCheck | 未核查数 | to_check_num | to_patrol_eval |
| toVerify | 未核实数 | to_verify_num | to_patrol_eval |
| validPatrolReport | 监督员有效上报数 | valid_patrol_report_num | to_patrol_eval |
| verify | 核实数 | verify_num | to_patrol_eval |
| needCheck | 应核查数 | need_check_num | to_patrol_eval |
| inTimeCheck | 按期核查数 | intime_check_num | to_patrol_eval |
| invalidCheck | 无效核查数 | invalid_check_num | to_patrol_eval |
| patrolDealReport | 自行处置上报数 | patrol_deal_report_num | to_patrol_eval |
| patrolDealCancel | 监督员自处置作废数 | patrol_deal_cancel_num | to_patrol_eval |
| patrolDealArchive | 监督员自处置结案数 | patrol_deal_archive_num | to_patrol_eval |
| accurateOperation | 准确受理 | accur_operate_num | to_acceptor_eval |
| checkTrans | 核查批转 | check_trans_num | to_acceptor_eval |
| intimeCheckTrans | 按时核查批转数 | intime_check_trans_num | to_acceptor_eval |
| intimeOperate | 按时受理数 | intime_operate_num | to_acceptor_eval |
| intimeSendCheck | 发核查数 | intime_send_check_num | to_acceptor_eval |
| intimeSendVerify | 发核实数 | intime_send_verify_num | to_acceptor_eval |
| needSendCheck | 应发核查数 | need_send_check_num | to_acceptor_eval |
| needSendVerify | 应发核实数 | need_send_verify_num | to_acceptor_eval |
| notOperate | 不予受理数 | not_operate_num | to_acceptor_eval |
| operate | 受理数 | operate_num | to_acceptor_eval |
| patrolDealToCheck | 自处置待审核数 | patrol_deal_to_check_num | to_acceptor_eval |
| sendCheck | 发核查数 | send_check_num | to_acceptor_eval |
| sendVerify | 发核实数 | send_verify_num | to_acceptor_eval |
| toOperate | 待受理数 | to_operate_num | to_acceptor_eval |
| back | 回退数 | back_num | to_acceptor_eval |
| needOperate | 应受理数 | need_operate_num | to_acceptor_eval |
| overtimeOperate | 超时受理数 | overtime_operate_num | to_acceptor_eval |
| overtimeToOperate | 超时待受理数 | overtime_to_operate_num | to_acceptor_eval |
| wrongOperate | 错误受理数 | wrong_operate_num | to_acceptor_eval |
| accurInst | 准确立案数 | accur_inst | to_ganger_eval |
| archive | 结案数 | archive_num | to_ganger_eval |
| inst | 立案数 | inst_num | to_ganger_eval |
| intimeArchive | 按时结案数 | intime_archive_num | to_ganger_eval |
| intimeInst | 按时立案数 | intime_inst_num | to_ganger_eval |
| notInst | 不予立案数 | not_inst_num | to_ganger_eval |
| toArchive | 待结案数 | to_archive_num | to_ganger_eval |
| toInst | 待立案数 | to_inst_num | to_ganger_eval |
| trans | 批转数 | trans_num | to_ganger_eval |
| needArchive | 应结案数 | need_archive_num | to_ganger_eval |
| overtimeArchive | 超时结案数 | overtime_archive_num | to_ganger_eval |
| overtimeToArchive | 超时待结案数 | overtime_to_archive_num | to_ganger_eval |
| cancel | 作废数 | cancel_num | to_ganger_eval |
| intimeDc | 按时督查数 | intime_dc_num | to_dispatcher_eval |
| intimeDispatch | 按时派遣数 | intime_dispatch_num | to_dispatcher_eval |
| Dispatch | 派遣数 | dispatch_num | to_dispatcher_eval |
| accurDispatch | 准确派遣数 | accur_dispatch_num | to_dispatcher_eval |
| needDc | 应督查数 | need_dc_num | to_dispatcher_eval |
| Dc | 督查数 | dc_num | to_dispatcher_eval |
| needDispatch | 应派遣数 | need_dispatch_num | to_dispatcher_eval |
| overtimeDispatch | 超时派遣数 | overtime_dispatch_num | to_dispatcher_eval |
| overtimeToDispatch | 超时未派遣数 | overtime_to_dispatch_num | to_dispatcher_eval |
| toDc | 待督查数 | to_dc_num | to_dispatcher_eval |
| toDispatch | 待派遣数 | to_dispatch_num | to_dispatcher_eval |
| wrongDispatch | 错误派遣数 | wrong_dispatch_num | to_dispatcher_eval |

## 人员比率、时长、金额和评分指标 HumanIndexRateType

| value | text | 口径说明 |
|---|---|---|
| disposeRate | 处置率 | 处置数 / 应处置数 |
| archiveRate | 结案率 | 结案数 / 应结案数 |
| dispatchRate | 派遣率 | 待现场确认分母 |
| accurDispatchRate | 准确派遣率 | 准确派遣数 / 应派遣数 |
| inTimeDispatchRate | 按期派遣率 | 按时派遣数 / 应派遣数 |
| verificationRate | 核查率 | 待现场确认分母 |
| acceptRate | 受理率 | 待现场确认分母 |
| inTimeAcceptRate | 按期受理率 | 按期受理数 / 受理数 |
| accurOperateRate | 准确受理率 | 准确受理数 / 受理数 |
| inTimeDisposeRate | 按期处置率 | 按期处置数 / 应处置数 |
| inTimeArchiveRate | 按期结案率 | 按期结案数 / 应结案数 |
| overTimeArchiveRate | 超期结案率 | 超期结案数 / 应结案数 |
| registerRate | 立案率 | 待现场确认分母 |
| inTimeRegisterRate | 按时立案率 | 按时立案数 / 立案数 |
| AccurInstRate | 准确立案率 | 准确立案数 / 立案数 |
| overTimeRate | 超期未处置率 | 待现场确认分母 |
| satisfactionRate | 满意率 | 待现场确认分母 |
| avgHandleTime | 平均处置时长 | 时长指标 |
| rectificationRate | 整改率 | 待现场确认分母 |
| validReportRate | 有效上报率 | 有效上报数 / 上报数 |
| intimeVerifyRate | 按期核实率 | 按时核实数 / 应核实数 |
| intimeCheckRate | 按期核查率 | 按时核查数 / 应核查数 |
| synthesis | 综合评分 | 评分指标 |
| penaltyAmount | 处罚金额 | 金额指标 |
| avgAcceptTime | 平均受理时长 | 时长指标 |
| reworkRate | 返工率 | 待现场确认分母 |
| comprehensiveScore | 综合评分 | 自定义综合评分 |
| scoreOrder | 排名 | 根据排序字段确认排名 |
| satisfactionDegree | 满意度 | 待现场确认单位 |
| overtimeDisposeRate | 超期处置率 | 待现场确认分母 |
