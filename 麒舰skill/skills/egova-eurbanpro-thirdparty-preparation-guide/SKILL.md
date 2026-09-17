---
name: egova-eurbanpro-thirdparty-preparation-guide
description: Use when 用户想判断麒舰第三方对接应该怎么接、先做什么、该配哪些应用/代理人/关键表、该走直连还是星桥拉取、通知查询还是主动推送、联调前怎么自测、字段要先对齐哪些、配置完怎么验证是否生效。即使用户没有明确说“做方案”或“做准备”，只要本质是在问接入路径、前置动作、配置分配、联调准备或查表验证，就应触发；不要承担具体接口参数说明和持续性故障归因。
---

# egova-eurbanpro-thirdparty-preparation-guide

## Overview
这是一个面向麒舰第三方对接前期方案与接入准备的顾问型 skill。

优先做四件事：
1. 先判断当前属于哪个对接场景。
2. 给出推荐接入路径与前置动作。
3. 明确还缺哪些现场信息，避免在信息不足时假装确定。
4. 指向本 skill 下真正需要的 `references/...` 小文件。

不要在主文件堆接口参数细节；接口字段与逐项报文诊断交给其他 skill。

## When to Use
适用于：
- 第三方刚开始接麒舰，不知道先做什么。
- 需要区分第三方直连、星桥拉取、通知查询、主动推送。
- 需要确认应用、对接系统、代理人、采集开关、关键配置表。
- 需要准备联调、自测、字段对齐和风险点清单。
- 用户在问“这个场景该怎么配”“配置完怎么验证”“要先查哪些表”“字段要先对齐什么”。

不适用于：
- 用户已经贴了接口地址/接口名 + JSON，要逐项报错定位。
- 只想查某个 action、接口参数、完整请求示例。
- 已经进入持续性故障排查，需要根据报错现象倒推原因。

## 强约束
- 必须先做场景判断，不能直接输出泛化集成建议。
- Reference 只允许使用当前 skill 下的相对路径：`references/...`。
- 默认输出“当前判断 / 推荐路径 / 下一步 / 风险点 / Reference”。
- 若当前信息不足，必须明确写出还缺的关键信息，而不是直接给唯一方案。
- 若用户开始贴接口名、报文或报错现象，应转向问题排查 skill 或 API skill，而不是在本 skill 主文件展开校验。

## 场景路由
| 用户信号 | 判断为 | 优先读取 |
| --- | --- | --- |
| 准备、开通、配置、自测、联调前要做什么 | 接入前准备 | `references/quick-start.md` |
| 第三方把案件上报到我方、星桥拉取后转上报 | 案件上报方案 | `references/reporting.md` |
| 我方派单给第三方、第三方查询通知 | 下派通知方案 | `references/dispatch-notice.md` |
| 第三方反馈处置结果、我方通知第三方反馈 | 处置反馈方案 | `references/dispose-feedback.md` |
| token、公钥、签名、AK/SK、代理认证 | 鉴权与签名准备 | `references/auth-sign.md` |
| 网络、404、代理用户认证失败、无权限、地址不通 | 网络与代理人前置检查 | `references/precheck-network-auth.md` |
| 采集开关、local_flag、触发器、参与者、节点、自测 | 采集配置与触发链路检查 | `references/precheck-collection-trigger.md` |
| 应用、API_SYS_INFO、agent_username、clear-sys-config、服务名、OPEN_ACTION_TRIGGER_FLAG、API_SYS_ACTION_TRIGGER、API_SYS_ACTION_INFO | V22 采集配置实操 | `references/v22duijieconfig.md` |
| 字段对齐、区划、来源、类型、附件字段 | 字段口径对齐 | `references/field-alignment-checklist.md` |
| 关键表、查表、SQL、配置是否生效 | 配置表与验证方法 | `references/config-tables-and-checks.md` |

## 推荐输出骨架
1. 当前判断：属于哪个场景
2. 推荐路径：直连 / 星桥拉取 / 通知查询 / 主动推送
3. 下一步：2-4 条关键动作
4. 缺失信息：还需要用户补充什么，才能继续收敛方案
5. 风险点：当前场景最容易踩坑的点
6. Reference：列 1-3 个当前最相关的小文件

## Quick Reference
### 读取顺序
1. 如果用户只是在问“该怎么接”，先读 `references/quick-start.md`。
2. 如果用户已经明确场景，直接读对应场景文件，不要先绕回总览。
3. 如果用户问的是配置、自测、字段或查表验证，优先读对应专题文件。
4. 如果用户已经提到具体配置项、表名或开关名，优先读 `references/v22duijieconfig.md`。
5. 需要接口参数或请求示例时，转 API skill；需要现象排查时，转 troubleshooting skill。
### 入口文件
- `references/quick-start.md`：最小阅读路径与高风险前置项
- `references/precheck-network-auth.md`：网络、认证、地址、代理人前置检查
- `references/precheck-collection-trigger.md`：采集开关、节点触发与现场自测
- `references/v22duijieconfig.md`：V22 应用、对接系统、代理人、采集与推送配置实操
- `references/field-alignment-checklist.md`：字段对齐清单
- `references/config-tables-and-checks.md`：关键配置表、字段与验证方法

### 场景文件
- `references/reporting.md`：第三方直连上报 / 星桥拉取后转上报
- `references/dispatch-notice.md`：下派通知方案
- `references/dispose-feedback.md`：处置反馈双向链路
- `references/auth-sign.md`：鉴权、签名、AK/SK 方案准备

### 使用约束
- 只回答方案、准备、路径、前置条件与风险点。
- 不在本 skill 下做逐字段 JSON 诊断。
- 若用户开始问具体 action 参数或完整报文，转向 API skill。

## Final Rule
- 先判断场景，再给路径。
- 场景明确时直接读对应小文件，不走大而全总览。
- 只回答方案、准备、配置与风险点；接口参数和故障归因交给专职 skill。
