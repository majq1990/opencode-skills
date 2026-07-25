# 对接配置关键表与排查方法

## 用途
这份文件专门回答：
- 给第三方分配对接配置时，涉及哪些关键表
- 每张表至少要关注哪些字段
- 配完后如何查询验证是否生效
- 联调失败时应该先查哪几张表

## 一、对接系统配置表
### 场景
第三方直连我方、我方拉取第三方后转上报、第三方处置反馈直连我方，都先从这里开始。

### 关键字段
| 字段 | 含义 | 备注 |
| --- | --- | --- |
| `code` / `sys_code` | 对接系统编码 | 通常也是 `senderCode` / `receiver_code` 的来源 |
| `name` | 对接系统名称 | 对应第三方平台名称 |
| `sys_client_id` | 认证标识 | 对应自动生成的 `client_id` |
| `client_id` | 认证客户端标识 | 第三方获取 token 时使用 |
| `client_secret` | 认证密钥 | 第三方获取 token 时使用 |
| `agent_username` | 对接代理人账号 | 必须是登录账号，不是姓名 |
| `local_flag` | 是否本地平台 | 整表只允许一条记录为 `1` |
| `auto_assign_flag` | 是否自动办理 | 按现场流程决定是否开启 |

### 配置后必须做的事
- 调用 `/unity/openapi/config/clear-sys-config` 刷新配置缓存。

## 二、本地平台与采集开关表
### 适用场景
我方系统派案件到第三方、我方处置反馈到第三方、通知类采集。

### 关键表与字段
| 表 / 配置 | 作用 | 关键项 |
| --- | --- | --- |
| `api_sys_config_item` | 采集触发器开关 | 配置名 `OPEN_ACTION_TRIGGER_FLAG` |
| 对接系统配置中的 `local_flag` | 标识本地平台 | 必须存在一条 `local_flag=1` |

### 常见问题
- 没有本地平台记录，导致下派通知链路无法成立。
- 开关没开，导致“流程走了但没有采集记录”。

## 三、采集阶段配置表
### 适用场景
下派通知、处置反馈通知、其他流程采集动作。

### 关键表
| 表名 | 作用 | 关键点 |
| --- | --- | --- |
| `api_sys_action_trigger` | 采集阶段配置 | 在特定阶段记录一次动作采集 |
| `API_SYS_TRIGGER_EVENT_SRC` | 问题来源限制 | 只采集指定来源的案件 |
| `API_SYS_TRIGGER_PART` | 参与者限制 | 只采集指定岗位/部门的案件 |

### 现场判断逻辑
只有当以下条件同时满足时，系统才会在采集表生成记录：
1. 案件流转到已配置的目标阶段
2. 案件来源命中 `API_SYS_TRIGGER_EVENT_SRC`
3. 当前参与者命中 `API_SYS_TRIGGER_PART`

## 四、采集结果验证表
### 查询验证 SQL
```sql
select * from api_message_send
where receiver_code = :receiver_code
  and action = :action
  and relation_id = :relation_id;

select * from api_message_send_his
where receiver_code = :receiver_code
  and action = :action
  and relation_id = :relation_id;
```

### 参数说明
| 参数 | 含义 | 备注 |
| --- | --- | --- |
| `receiver_code` | 接收方编码 | 通常对应应用编码 / 对接系统编码 |
| `action` | 采集动作 | 如下派通知、处置反馈通知等 |
| `relation_id` | 案件标识 | 通常是案件 `rec_id` |

### 判断方式
- `api_message_send` 有记录：说明当前待发送/待处理采集记录已生成
- `api_message_send_his` 有记录：说明历史采集记录存在
- 两边都没有：优先回查触发条件、来源限制、参与者限制、开关与本地平台配置

## 五、工作流定位辅助表
### `wf_act_inst`
用于确认：
- 案件当前实际到了哪个阶段
- `act_def_id` 是否和配置阶段一致
- `proc_def_id` 是否匹配当前流程定义
- `act_property_id` 是否命中了目标节点属性

### 最小查询方式
- 已知案件主键时，优先按 `biz_entry_id` 或案件关联主键查 `wf_act_inst`。
- 重点看 `act_def_id`、`proc_def_id`、`act_property_id`，不要只凭页面显示判断节点已经命中。
- 作废、不受理、办结等节点采集异常时，先以现场 `wf_act_inst` 的真实值为准，再反推 action。

### 什么时候查
- 你认为“已经走到这个阶段了”，但采集表没有记录。
- 用户说“明明配了，但没有触发通知/反馈采集”。
- 作废、不受理、办结等节点通知异常，需要先确认真实节点属性。
## 六、处置反馈专用配置表
### 场景
第三方处置反馈至我方、我方处置反馈通知第三方。

### 关键表与字段
| 表 / 字段 | 作用 | 备注 |
| --- | --- | --- |
| `api_sys_action_info` | 配置动作推送信息 | 我方推送第三方时常用 |
| `sys_code` | 第三方处置平台编码 | 对应第三方应用编码 |
| `action` | 动作名 | 如 `DISPOSE_FEEDBACK_NOTICE` |
| `action_name` | 动作中文名 | 如工单处置反馈通知 |
| `api_url` | 推送地址 | 可配置星桥代理免密地址 |
| `retry_num` | 重试次数 | 默认常见为 `3` |
| `valid_flag` | 是否生效 | 常见 `1` 为生效 |
| `item_name=AUTO_TRANS_INFO` | 处置反馈流向配置 | 决定反馈后流转去向 |
| `item_name=AUTO_TRANS_OPINION` | 默认反馈意见 | 第三方未传 `disposeOpinion` 时使用 |
| `item_value` | 流向值 | 如：下一阶段标识、参与者标识、主协办标识 |

## 七、对接代理人排查
### 高风险点
- `agent_username` 配成了人员姓名，不是登录账号
- 账号里带脏字符
- 代理人没有目标岗位权限

### 典型现象
- 获取 token 报代理用户认证失败
- 第三方调用业务接口报“非当前案件办理人”
- 第三方调用业务接口报“无权限进行该操作”

## 八、最小排查顺序
1. 先查对接系统配置是否正确，尤其 `sys_code`、`client_id`、`client_secret`、`agent_username`
2. 确认已调用 `/unity/openapi/config/clear-sys-config`
3. 如果是通知/反馈采集，查 `local_flag` 与 `OPEN_ACTION_TRIGGER_FLAG`
4. 查 `api_sys_action_trigger`、`API_SYS_TRIGGER_EVENT_SRC`、`API_SYS_TRIGGER_PART`
5. 查 `wf_act_inst` 看阶段是否真的走到了目标节点
6. 查 `api_message_send` / `api_message_send_his` 看是否已生成采集记录
7. 如果是处置反馈推送，再查 `api_sys_action_info` 和 `AUTO_TRANS_INFO`

## 九、现场自测推荐顺序
1. 创建一条测试案件，并把案件推进到目标节点。
2. 先查 `wf_act_inst`，确认真实节点、流程定义和节点属性。
3. 再查 `api_message_send` / `api_message_send_his`，确认采集记录是否生成。
4. 若两张采集表都无记录，回查 `local_flag`、`OPEN_ACTION_TRIGGER_FLAG`、`api_sys_action_trigger`、`API_SYS_TRIGGER_EVENT_SRC`、`API_SYS_TRIGGER_PART`。
5. 若现场确认作废节点对应特定 `act_property_id`，再用该结论对照 `CANCEL_NOTICE` 等 action；未确认前不要把文档样例当成现场真值。

## 何时引用本文件
- 用户问“第三方对接配置应该怎么分配”
- 用户问“关键配置表有哪些”
- 用户问“配完后怎么验证有没有生效”
- 用户问“该查哪些表定位问题”
