---
name: egova-eurbanpro-thirdparty-api-reference
description: Use when 用户提到麒舰第三方对接的某个 action、接口名、字段、请求参数、返回值、请求示例、联调示例、公钥、token、通知签收、处置反馈、办理经过、督办催办、签收告知、上传多媒体，或贴出接口名想知道该看哪份文档时都应触发。即使用户没有明确说“查文档”，只要本质是在问 API 细节、字段规则或示例，就用这个 skill；不要承担总体接入方案设计和故障归因。
---

# egova-eurbanpro-thirdparty-api-reference

## Overview
这是一个面向麒舰第三方对接 API 文档检索与示例生成的 reference skill。

优先做四件事：
1. 先根据 action、接口名或场景把问题路由到正确的 `references/...` 文件。
2. 默认输出最小必要字段，不先展开整页参数表。
3. 只要用户问的是“某个具体接口怎么调”，默认给一个最小请求示例。
4. 若用户要完整字段、完整联调示例、返回值细项，再补充展开。

不要承担总体方案设计与故障归因；方案问题转 preparation-guide，现象排查转 troubleshooting。

## When to Use
适用于：
- 查询某个 action 对应什么接口。
- 查询 REPORT、处置反馈、通知签收、督办催办、签收告知、办理经过、上传多媒体等接口参数。
- 生成最小请求示例或完整联调示例。
- 确认 `egova_openapi_token`、`mediaPath/content`、时间格式、统一请求信封等公共规则。
- 用户贴了 action、接口路径、字段名、请求 JSON，想知道它属于哪类接口或字段是否齐全。

不适用于：
- 需要判断接入模式、实施步骤、前置配置、字段对齐方案。
- 已经出现报错，需要根据现象倒推原因或排查配置。

## 强约束
- 先定位接口，再给字段；不要上来就讲大段背景。
- Reference 只允许使用当前 skill 下的相对路径：`references/...`。
- 回答参数问题时优先给“最小必要字段 + 请求示例 + 关键约束”。
- 只有用户明确要求完整参数表、完整联调示例时，再展开 `references/report-full-params.md` 等大表。
- 认证口径统一为 query 参数 `egova_openapi_token`，不要回退到 Authorization 方式。
- 若小文件已覆盖，不要默认读取 `references/v22duijie.md`；它只作为兜底原文参考。

## 路由
| 用户信号 | 判断为 | 优先读取 |
| --- | --- | --- |
| REPORT、上报、查询工单、办理经过同步、多媒体字段 | 上报与查询接口 | `references/reporting-and-query.md` |
| 处置反馈、办理经过查询、督办、催办、签收、告知、上传附件 | 流程操作接口 | `references/process-actions.md` |
| 通知、签收通知、下派通知、反馈通知、noticeName | 通知与签收接口 | `references/notice-and-signing.md` |
| token、公钥、clientSecret、egova_openapi_token | 认证接口 | `references/auth-apis.md` |
| 要完整字段清单、完整示例 | REPORT 完整参数 | `references/report-full-params.md` |
| 不确定 action 名称 | action 速查 | `references/actions-map.md` |
| 要看公共请求规则 | 协议规范 | `references/common-protocol.md` |

## 输出骨架
### 查具体接口时
1. 命中接口：action / 接口名 / 用途
2. 最小必要字段：只列当前问题需要的参数
3. 请求示例：给最小可用请求
4. 补充说明：类型、格式、二选一约束、返回关键值
5. Reference：1-2 个小文件

### 查 action 映射或公共规则时
1. 先给映射结果或规则结论
2. 再指出下一步该读哪个 `references/...` 文件

## Quick Reference
### 读取顺序
1. 不确定 action 时先读 `references/actions-map.md`。
2. 看公共请求规范时读 `references/common-protocol.md`。
3. 根据接口类别读对应小文件。
4. 只有用户明确要完整示例时，再读 `references/report-full-params.md`。
5. 小文件未覆盖时，最后再回退到 `references/v22duijie.md`。

### 核心文件
- `references/actions-map.md`：action 映射速查
- `references/common-protocol.md`：协议与公共规则
- `references/reporting-and-query.md`：REPORT、GET_REC_INFO、ITEM_INST_SYNC
- `references/process-actions.md`：DISPOSE_FEEDBACK、GET_REC_PROCESS_INFO、SUPERVISE、PRESS、SIGN、NOTIFY、UPLOAD_MEDIA
- `references/notice-and-signing.md`：GET_NOTICE_INFO、NOTICE_SIGNING
- `references/auth-apis.md`：公钥与 token 接口
- `references/report-full-params.md`：REPORT 完整参数

### 使用约束
- 只回答接口、字段、示例和规则。
- 默认给最小必要说明，按需再展开完整参数表。
- 若用户开始描述报错现象，应转向 troubleshooting skill。

## Final Rule
- 先用小文件命中接口，再回答字段。
- 查具体接口时，默认给最小字段和请求示例。
- 方案设计与故障定位不在本 skill 内处理。
