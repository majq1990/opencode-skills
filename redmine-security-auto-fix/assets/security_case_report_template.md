# {{project}} 安全案件处置报告（{{date}}）

> 报告状态：**{{status}}**
> 数据来源：{{source_line}}
> 分级口径：{{formula}}
> 规则版本：{{rules_version}}｜阈值批准口径：{{approved_by}}

## 零、任务与执行摘要

{{task_block}}

## 一、案件概览

{{overview_table}}

## 二、分级口径与权重

{{rule_block}}

> 说明：扫描器自带的严重度仅作参考字段，**最终级别一律以本口径自算结果为准**（同一条 CVE 落在不同资产上级别可能不同）。

## 三、关键案件详情（Critical / High）

{{critical_blocks}}

## 四、全量案件清单

{{full_table}}

## 五、未定责 / 待补台账项

{{unmapped_blocks}}

## 六、情报未命中我方资产（本次不处置）

{{unaffected_table}}

## 七、数据质量告警

{{warnings_block}}

## 八、下一步与时限（SLA）

{{next_steps}}

---

生成脚本：`scripts/gen_security_report.py`（只写本地 work/security_case/output/，不外发）
复核人：{{reviewer}} ｜ 复核时间：{{review_time}} ｜ 推送须经人工复核并先走测试目标（config/security_case/notify.json）
