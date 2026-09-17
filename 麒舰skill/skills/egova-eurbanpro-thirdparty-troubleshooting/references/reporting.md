# 场景：案件上报

## 适用信号
- 第三方主动把案件上报到我方。
- 第三方只提供查询接口，我方通过星桥拉取后转上报。
- 需要处理多媒体上传或补传。

## 模式 A：第三方直连我方
### 步骤
1. 新增应用，获取 `clientId`、`clientSecret`。
2. 新增对接系统，填好应用编码、凭证、代理人。
3. 刷新对接配置。
4. 第三方按标准认证链路获取 token。
5. 调用 `REPORT` 上报工单。
6. 记录返回的 `recId`、`taskNum`，继续后续业务操作。

### 关键提醒
- `caseId` 是第三方侧工单唯一标识，后续所有对接动作都依赖它。
- 代理人要有岗位权限，否则即使参数正确也会失败。
- 先和第三方对齐来源、类型、大小类、区划字段。

## 模式 B：我方星桥拉取后转上报
### 步骤
1. 在星桥配置第三方查询代理。
2. 后置脚本把第三方返回字段转换成 `REPORT` 所需结构。
3. 配置麒舰认证脚本。
4. 配置麒舰上报接口。
5. 配置定时任务，先试跑，再正式调度。

### 高频前置脚本
```groovy
var data = request.getBody().getParams().data;
var map = com.egova.json.utils.JsonUtils.deserialize(data, Map.class);

map = [
    "uid": java.util.UUID.randomUUID().toString(),
    "data": map,
    "action": "REPORT",
    "senderCode": "对接系统编码"
]
request.setBody(com.egova.json.utils.JsonUtils.serialize(map));
request.setHeader('Content-Type', 'application/json')
```

## 多媒体
- `medias` 通常是上报必传。
- `mediaPath` / `content` 二选一。
- 若 URL 方式不通，先排网络，再转 base64。

## 继续阅读
- 协议与公共规则：`references/common-protocol.md`
- REPORT 参数：`references/reporting-and-query.md`
- REPORT 完整参数：`references/report-full-params.md`
- 诊断模板：`references/diagnostic-playbook.md`
