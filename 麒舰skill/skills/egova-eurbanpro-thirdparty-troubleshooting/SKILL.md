---
name: egova-eurbanpro-thirdparty-troubleshooting
description: Use when 麒舰第三方对接联调已经出现 404、认证错误、token 接口报错、代理用户认证失败、参数错误、多媒体下载失败、base64 上传异常、多媒体地址过长、流程不推进、通知没采集、反馈不推进、登记栏看不到第三方案件，或用户已提供接口地址/接口名/action/JSON 需要做定向排查。不要用于纯联调前准备、纯风险预检或完整接口手册查询。
---

# egova-eurbanpro-thirdparty-troubleshooting

## Overview
这是一个面向麒舰第三方对接联调问题排查的诊断型 skill。

先判断用户是在排障，还是在做接入前准备。若是纯预检或接入方案咨询，不进入本 skill。

优先做四件事：
1. 判断问题属于地址、认证、报文、多媒体、流程还是采集。
2. 对 404、认证、token、流程/采集、多媒体问题先给 3-5 条默认前置核查。
3. 对接口地址 / action / JSON 做定向诊断。
4. 指向本 skill 下真正需要的 `references/...` 小文件。

不要在主文件展开完整 API 手册；完整参数清单与接口说明交给 API skill，纯准备/方案问题交给 preparation skill。

## When to Use
适用于：
- 用户已经出现 404、认证错误、token 接口报错、代理用户认证失败。
- 用户已经出现参数错误、多媒体下载失败、base64 上传异常、多媒体地址过长。
- 用户已经出现未找到合适处理人、无法流转、通知没采集、反馈不推进、登记栏看不到第三方案件。
- 用户已给接口地址、接口名、action 或 JSON，希望做定向排查。

不适用于：
- 只想了解整体接入方案和联调准备。
- 只想做联调前风险预检或准备清单。
- 只想查接口定义、参数说明和完整示例。

## 强约束
- 先判断是否已出现故障；纯预检不用本 skill。
- 404、认证、token、流程/采集、多媒体类问题默认先读 `references/precheck-and-selftest.md`。
- 只有用户提供接口名/地址 + JSON 时，才进入严格定向诊断模板。
- 定向诊断也不能跳过默认前置核查。
- Reference 只允许使用当前 skill 下的相对路径：`references/...`。
- 命中 `4.12` 或 `4.22` 的 action 冲突时，必须提示“需现场确认”。
- 不要把回答写成完整接入方案或培训文档。

## 路由
| 用户信号 | 判断为 | 先读 | 再读 | 必要时补读 |
| --- | --- | --- | --- | --- |
| 404、地址不通、接口示例失效 | 地址/网络问题 | `references/precheck-and-selftest.md` | `references/common-issues.md` | `references/common-protocol.md` |
| 认证错误、token 获取失败、代理用户认证失败 | 认证问题 | `references/precheck-and-selftest.md` | `references/auth-apis.md` | `references/auth-sign.md` |
| 参数错误、字段缺失、字段名/类型不对 | 报文问题 | `references/diagnostic-playbook.md` | `references/common-protocol.md` | 命中 action 后补场景文件 |
| 多媒体下载失败、base64 上传异常、多媒体地址过长 | 多媒体问题 | `references/precheck-and-selftest.md` | `references/common-issues.md` | `references/common-protocol.md` |
| 未找到合适处理人、无法流转、通知没采集、反馈不推进、登记栏看不到第三方案件 | 流程/采集问题 | `references/precheck-and-selftest.md` | `references/config-tables-and-checks.md` | `references/dispatch-notice.md` / `references/dispose-feedback.md` |
| 已给 action 或接口地址 + JSON | 定向诊断 | `references/diagnostic-playbook.md` | 命中场景文件 | 命中冲突时提示现场确认 |

## 输出骨架
### 开放式排障
1. 当前判断：最可能的问题类别
2. 默认前置核查：3-5 条当前必须先过的核查项
3. 排查顺序：2-5 条最小动作
4. 重点表 / 字段 / SQL：只列当前需要查的部分
5. 风险点：容易误判的地方
6. Reference：1-3 个小文件

### 定向诊断
1. 命中接口：`action > 接口名称 > 地址关键字`
2. 默认前置核查：2-3 条最相关核查项
3. 问题清单：缺失 / 类型错误 / 格式错误 / 组合约束 / 现场依赖项
4. 文档冲突提示：是否命中 `4.12` / `4.22`
5. 最小修正建议
6. Reference：1-2 个小文件

## Quick Reference
### 读取顺序
1. 先判断用户是在排障还是在做联调前准备。
2. 404、认证、token、流程/采集、多媒体问题先读 `references/precheck-and-selftest.md`。
3. 用户已给 `action + JSON` 时，先读 `references/diagnostic-playbook.md`，再按场景补读。
4. 需要查表验证时读 `references/config-tables-and-checks.md`。
5. 需要完整参数手册或准备方案时，转其他 skill。

### 核心文件
- `references/precheck-and-selftest.md`：默认前置核查与现场自测
- `references/common-issues.md`：404、认证、多媒体、流程异常速查
- `references/diagnostic-playbook.md`：接口诊断模板与冲突提示
- `references/config-tables-and-checks.md`：关键配置表与查询验证
- `references/actions-map.md`：action 速查
- `references/auth-apis.md`：公钥与 token 速查
- `references/common-protocol.md`：公共协议规则

### 按 action 补读
- `references/reporting-and-query.md`：REPORT / 查询接口要点
- `references/report-full-params.md`：REPORT 完整字段清单
- `references/notice-and-signing.md`：通知查询与签收要点

### 按场景补上下文
- `references/reporting.md`
- `references/dispatch-notice.md`
- `references/dispose-feedback.md`
- `references/auth-sign.md`

### 使用约束
- 以排查、校验、验证为主，不负责方案设计。
- 能给最小排查顺序时，不展开整份接口手册。
- 对文档冲突必须明确提示“需现场确认”。

## Final Rule
- 先判断是否已出现故障，再分类。
- 404、认证、token、流程/采集、多媒体问题先前置核查，再进入定位。
- 有 JSON 就做定向诊断，但不能跳过前置核查。
- 需要完整参数手册或纯准备方案时，转去其他 skill。
