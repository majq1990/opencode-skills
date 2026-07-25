# 场景：处置反馈双向

## 适用信号
- 第三方要把处置结果反馈到我方。
- 我方要把处置反馈通知给第三方。
- 需要通过星桥把第三方非标准参数转换成麒舰标准。

## 模式 A：第三方 -> 我方
### 直连标准接口
- 核心 action：`DISPOSE_FEEDBACK`
- 需要先配置处置反馈流向，如 `AUTO_TRANS_INFO`、`AUTO_TRANS_OPINION`。

### 星桥代理转换
- 若第三方参数和我方标准不一致，可通过星桥前置脚本包装：`senderCode`、`action`、`uid`、`data`。
- 并行多派场景可传 `disposePartUid`，指定具体活动。

### 高频脚本片段
```groovy
var map = request.getBody().getParams();
var data = com.egova.json.utils.JsonUtils.deserialize(map.data, Map.class);

var reportMap = [
    'senderCode':'xinfangxinxiang',
    'action':'DISPOSE_FEEDBACK',
    'data':JsonUtils.serialize(data),
    'uid':java.util.UUID.randomUUID().toString(),
]

request.setHeader('Content-Type', 'application/json; charset=utf-8');
request.setBody(com.egova.json.utils.JsonUtils.serialize(reportMap));
```

## 模式 B：我方 -> 第三方
### 方案 1：第三方查通知
- 第三方通过 `GET_NOTICE_INFO` 查询 `DISPOSE_FEEDBACK_NOTICE`。
- 业务处理后调用 `NOTICE_SIGNING`。

### 方案 2：我方主动推送
- 在 `api_sys_action_info` 中配置 `DISPOSE_FEEDBACK_NOTICE` 推送地址。
- 配置重试次数、是否生效等参数。

## 高风险点
- `AUTO_TRANS_INFO` 配错，反馈后流程不推进。
- 并行节点没有 `disposePartUid`，会反馈到错误活动。
- 只查通知不签收，导致重复处理。

## 继续阅读
- 通知机制：转 `egova-eurbanpro-thirdparty-api-reference` 的 `references/notice-and-signing.md`
- 诊断模板：转 `egova-eurbanpro-thirdparty-troubleshooting` 的 `references/diagnostic-playbook.md`
