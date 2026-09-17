# 排障前置核查与现场自测

## 适用信号
- 已经出现 404、认证错误、token 接口报错、代理用户认证失败。
- 已经出现多媒体下载失败、base64 上传异常、多媒体地址过长。
- 已经出现流程不推进、通知没采集、反馈不推进、登记栏看不到第三方案件。
- 用户还没贴完整 JSON，但已经明确进入联调排障阶段。

## 最小核查顺序
1. 先确认这是“排障”而不是“联调前准备”。如果只是纯预检，转 preparation skill。
2. 核网络双向可达：第三方能否访问我方接口、我方能否访问第三方附件地址。
3. 核现场真实地址：不要误用文档示例地址，不要误带 `v22-api/`。
4. 核应用与凭证：`client_id`、`client_secret`、公钥 -> 加密 -> token 链路是否完整。
5. 核对接代理人：`agent_username` 必须是登录账号，不能是人员名称，不能带脏字符。
6. 核配置刷新：修改对接系统配置后执行 `/unity/openapi/config/clear-sys-config`。
7. 若涉及流程/采集，创建一条测试案件并查 `wf_act_inst`、`api_message_send`、`api_message_send_his`。

## 404 / 地址问题
- 第三方要回传实际请求 URL，再逐段核对路径。
- `/oauth/extras/openapi/pubkey`、`/oauth/extras/openapi/client` 这类地址前不要额外拼 `v22-api/`。
- 若现场走政务外网，还要核源 IP 防火墙策略。

## 认证 / token 问题
- 标准链路：公钥 -> SM2 加密 `client_secret` -> token -> 业务接口。
- 业务接口 token 可二选一：
  - `X-EGOVA-Authorization: Bearer <token>`
  - `egova_openapi_token=<token>`
- 若仍失败，再查第三方侧是否还需要签名头或网关签名。

## 流程 / 采集自测
1. 创建一条测试案件并推进到目标节点。
2. 先查 `wf_act_inst`，确认真实命中的 `act_def_id`、`proc_def_id`、`act_property_id`。
3. 再查采集表：
```sql
select * from api_message_send where receiver_code = :receiver_code and action = :action and relation_id = :relation_id;
select * from api_message_send_his where receiver_code = :receiver_code and action = :action and relation_id = :relation_id;
```
4. 若两边都没有记录，再回查 `local_flag`、`OPEN_ACTION_TRIGGER_FLAG`、`api_sys_action_trigger`、`API_SYS_TRIGGER_EVENT_SRC`、`API_SYS_TRIGGER_PART`。

## 关键字段预警
- 上报字段至少先核：`event_src_id/name`、`rec_type_id/name`、`event_type_id/name`、`main_type_id/name`、`sub_type_id/name`。
- 若现场流程依赖区划，必须补 `district_id/name`，否则可能出现“未找到合适处理人”。

## 多媒体 / base64
- 先在我方服务器执行 `curl -I <多媒体URL>` 验证可达性。
- base64 内容放 `medias.content`，不要放 `mediaPath`。
- `mediaName` 使用英文文件名加扩展名。

## 快速结论
只要网络、真实地址、凭证链路、代理人、配置刷新、自测链路这 6 类前置项还没过，就不要直接把问题判成业务参数错误。
