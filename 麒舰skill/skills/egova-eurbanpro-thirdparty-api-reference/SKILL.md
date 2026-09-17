---
name: egova-eurbanpro-thirdparty-api-reference
description: Use when 用户在问麒舰第三方对接的具体 API 事实（action 对应接口、字段/参数、返回值、最小请求示例、认证规则、通知签收、流程动作、多媒体上传）并需要快速得到可调用答案。遇到接入准备、模式选择、实施步骤或故障归因问题时不应由本 skill 主导。
---

# egova-eurbanpro-thirdparty-api-reference

## Overview
面向麒舰第三方对接的 API 事实查询与最小回答生成 skill。

核心原则：先命中接口，再给最小必要字段、最小请求示例和关键约束。不展开背景，不复述文档原文。

本 skill 只回答"接口是什么、字段怎么填、请求怎么写"三类事实问题。

## When to Use

**适用：**
- 查询某个 action 对应什么接口
- 查询接口字段、参数、返回值、请求示例
- 确认认证规则（`egova_openapi_token`）、时间格式、公共信封等协议事实
- 用户贴了 action、接口路径、字段名、请求 JSON，想知道属于哪类接口或字段是否齐全

**不适用 — 应分流到其他 skill：**
- 接入模式选择、前置配置、材料准备 → `preparation-guide`
- 报错排障、现象归因、配置排查 → `troubleshooting`

## Routing Strategy

先读 `references/router-cheatsheet.md` 确定主 reference，再读目标文件。

| 用户信号 | 主 reference | 辅助 reference | 输出类型 |
| --- | --- | --- | --- |
| action 不确定 | `references/actions-map.md` | `references/common-protocol.md` | 规则类 |
| REPORT / 查询工单 / 办理经过同步 | `references/reporting-and-query.md` | `references/common-protocol.md` | 接口类 |
| 处置反馈 / 督办催办 / 上传附件 | `references/process-actions.md` | `references/common-protocol.md` | 接口类 |
| 通知 / 签收 / 告知 | `references/notice-and-signing.md` | `references/common-protocol.md` | 接口类 |
| token / 公钥 / egova_openapi_token | `references/auth-apis.md` | `references/common-protocol.md` | 接口类 |
| 用户明确要求完整参数表 | `references/report-full-params.md` | `references/reporting-and-query.md` | 规则类 |
| 公共请求规则 | `references/common-protocol.md` | — | 规则类 |

**读取纪律：**
- 每次只读 1 个主 reference，最多补 1 个辅助
- 小文件已覆盖时，不要默认读 `references/v22duijie.md`
- `v22duijie.md` 仅在所有小文件均未覆盖时作为兜底原文

## Output Contract

### 接口类问题（查具体接口时）

固定输出四段，不多不少：

1. **命中接口** — action / 接口名 / 一句话用途
2. **最小必要字段** — 只列当前问题需要的参数，不展开完整参数表
3. **最小请求示例** — 一个可直接使用的请求 JSON
4. **关键约束** — 类型、格式、二选一、易错点（最多 3 条）

### 规则类问题（查 action 映射或公共协议时）

固定输出三段：

1. **直接结论** — 映射结果或规则要点
2. **最小规则列表** — 只列必要的 2-5 条
3. **下一步** — 指出该读哪个 `references/...` 文件

### 默认不做

- 不展开完整参数表（除非用户明确要求）
- 不复述长段背景或文档原文
- 不在 reference skill 中推演接入方案或现场原因

## Boundary Handoff

当用户问题本质上属于以下类别时，**不读 reference 文件**，只用 2-3 句话给出最简 API 事实（接口路径或认证口径）+ 分流话术，然后立即停止。

**边界判断规则：**
- 问题在问"怎么准备、怎么选、怎么规划" → 接入准备类
- 问题在问"为什么报错、为什么不通、怎么排查" → 故障排障类

**分流回答上限：2-3 句 API 事实 + 1 句分流引导。不要展开参数、不要给请求示例、不要读 reference。**

- **接入准备 / 模式选择 / 实施步骤：**
  > "这部分属于接入准备与方案决策，建议切换到 preparation-guide。本 skill 只确认：公钥路径为 `/oauth/extras/openapi/pubkey`，token 通过 query 参数 `egova_openapi_token` 传递。"

- **故障归因 / 报错排查 / 配置诊断：**
  > "这部分属于现象排障，建议切换到 troubleshooting。本 skill 只确认：[接口路径或认证事实]。"

不在本 skill 内继续承担方案设计与故障归因。**边界场景下克制比帮助更重要——过度回答会抢走其他 skill 的职责。**

## Quick Reference

### 读取顺序
1. 不确定 action → `references/actions-map.md`
2. 公共协议 → `references/common-protocol.md`
3. 根据类别读对应小文件
4. 用户明确要完整参数表 → `references/report-full-params.md`
5. 小文件未覆盖 → `references/v22duijie.md`（兜底）

### 核心文件
- `references/router-cheatsheet.md`：路由速查
- `references/actions-map.md`：action 映射
- `references/common-protocol.md`：协议与公共规则
- `references/reporting-and-query.md`：REPORT、GET_REC_INFO、ITEM_INST_SYNC
- `references/process-actions.md`：DISPOSE_FEEDBACK、GET_REC_PROCESS_INFO、SUPERVISE、PRESS、SIGN、NOTIFY、UPLOAD_MEDIA
- `references/notice-and-signing.md`：GET_NOTICE_INFO、NOTICE_SIGNING
- `references/auth-apis.md`：公钥与 token 接口
- `references/report-full-params.md`：REPORT 完整参数（按需展开）

### 使用约束
- 认证口径统一为 query 参数 `egova_openapi_token`，不回退 Authorization 方式
- 只回答接口、字段、示例和规则
- 默认给最小必要说明，按需再展开

## Final Rule
- 先用小文件命中接口，再回答字段
- 查具体接口时，默认给最小字段和请求示例
- 方案设计与故障定位不在本 skill 内处理
