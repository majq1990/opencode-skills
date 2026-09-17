# 前置检查：采集配置与现场自测

## 适用信号
- 我方需要采集下派、反馈、通知等流程动作。
- 配完后不知道是否真的生效。

## 采集逻辑
先在工作流节点中把对接代理人设置为参与者，再完成节点、来源、参与者等采集配置。案件流转到目标节点且满足来源与参与者条件时，系统会在采集表生成记录。

## 自测方法
1. 创建一条测试案件。
2. 将案件操作到目标阶段。
3. 查询以下表是否生成记录：
```sql
select * from api_message_send where receiver_code = :receiver_code and action = :action and relation_id = :relation_id;
select * from api_message_send_his where receiver_code = :receiver_code and action = :action and relation_id = :relation_id;
```
其中：
- `receiver_code`：应用编码
- `action`：采集动作
- `relation_id`：案件 `rec_id`

## 辅助排查
- 可先查 `wf_act_inst`，确定实际工作流阶段标识。
- 受理、不受理、办结等阶段的 act_def_id 可能需要通过接口或查表获取。

## 典型失败点
- 节点配对不上。
- 来源限制不匹配。
- 参与者/岗位限制不匹配。
- `local_flag` 或采集开关没有打开。
