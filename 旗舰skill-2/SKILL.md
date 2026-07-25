---
name: 旗舰skill
description: 面向麒舰/EUrban/MIS 工程实施场景的技能集合。包含 SpEL 表达式生成与校验、第三方接口接入参考、部署前置准备指南、接入问题排查，以及悟空大屏数据对接五大能力。当工程实施人员处理 SpEL 配置、第三方系统对接、悟空数据接入等典型工程场景时触发。
version: 1.0.0
compatibility: opencode
metadata:
  category: support-dept
  tags: egova,eurban,mis,spel,thirdparty,wukong,engineering
---

# 旗舰 Skill 集合

面向麒舰/EUrban/MIS 工程实施场景的技能集合，包含以下子技能：

## 1. egova-eurbanpro-spel-generator — SpEL 表达式生成与校验

**适用场景**：Egova / EUrban / MIS 业务配置中的 SpEL 场景识别、主体选择、字段映射与候选表达式生成。

**触发条件**：
- 写、改、解释、校验 Egova 业务里的 SpEL 表达式
- 判断某个场景一般支持哪些主体、占位符、上下文对象
- 把业务口语规则整理成可配置条件
- 处理菜单/按钮显示条件、流程自动批转条件、案件样式标红高亮条件、消息提醒触发规则
- 处理 `#bizEntry`/`#actInst`/`#state` 等占位符问题

**核心原则**：先识别场景，再确认主体与字段；能生成就先给候选表达式，不能可靠生成再追问。

---

## 2. egova-eurbanpro-thirdparty-api-reference — 第三方接口接入参考

**适用场景**：麒舰第三方对接的具体 API 事实查询（action 对应接口、字段/参数、返回值、最小请求示例、认证规则、通知签收、流程动作、多媒体上传）。

**触发条件**：
- 查询某个 action 对应什么接口
- 查询接口字段、参数、返回值、请求示例
- 确认认证规则（`egova_openapi_token`）、时间格式、公共信封等协议事实
- 需要快速得到可调用答案

**核心原则**：先命中接口，再给最小必要字段、最小请求示例和关键约束。不展开背景，不复述文档原文。

**不适用**：接入准备、模式选择、实施步骤或故障归因问题。

---

## 3. egova-eurbanpro-thirdparty-preparation-guide — 接入前置准备指南

**适用场景**：麒舰第三方对接前期方案与接入准备的顾问型指导。

**触发条件**：
- 判断麒舰第三方对接应该怎么接、先做什么
- 该配哪些应用/代理人/关键表
- 该走直连还是星桥拉取、通知查询还是主动推送
- 联调前怎么自测、字段要先对齐哪些
- 配置完怎么验证是否生效

**核心职责**：
1. 先判断当前属于哪个对接场景
2. 给出推荐接入路径与前置动作
3. 明确还缺哪些现场信息，避免在信息不足时假装确定
4. 指向真正需要的参考文档

**不承担**：具体接口参数说明和持续性故障归因。

---

## 4. egova-eurbanpro-thirdparty-troubleshooting — 接入问题排查

**适用场景**：麒舰第三方对接联调问题排查的诊断型指导。

**触发条件**：
- 出现 404、认证错误、token 接口报错、代理用户认证失败
- 参数错误、多媒体下载失败、base64 上传异常、多媒体地址过长
- 流程不推进、通知没采集、反馈不推进、登记栏看不到第三方案件
- 用户已提供接口地址/接口名/action/JSON 需要做定向排查

**核心职责**：
1. 判断问题属于地址、认证、报文、多媒体、流程还是采集
2. 对常见问题先给 3-5 条默认前置核查
3. 对接口地址/action/JSON 做定向诊断
4. 指向真正需要的参考文档

**不适用**：纯联调前准备、纯风险预检或完整接口手册查询。

---

## 5. egova-wukong-data-connector — 悟空大屏数据对接

**适用场景**：悟空大屏组件数据对接，识别组件 `result` 数据形状，匹配悟能接口，输出数据源结论、字段映射和 ES5 过滤脚本。

**触发条件**：
- 用户提到悟空大屏、组件静态数据、result 契约
- 接口对接、字段映射、过滤脚本/filter(data)
- 星桥接口、悟能接口、ddcat 或 SQL 查询

**核心原则**：
- 先确认目标 result 形状，优先检索悟能接口
- 评估字段/筛选/统计粒度/返回结构
- 输出数据源结论、字段映射和 ES5 `function filter(data)`
- **不得编造**接口地址、参数、响应字段、统计口径或星桥路径

**必读资料**：
- `domain_indexes/wuneng_api_index.md`：悟能接口粗筛索引
- `knowledge/api_flat.md`：悟能接口扁平摘要
- `knowledge/api_details/**/*.md`：接口详情文档
- `knowledge/component_static_schema.md`：组件推荐 result 数据样例库

---

## 技能协作关系

```
接入准备 (preparation-guide) ──> 接口查询 (api-reference) ──> 问题排查 (troubleshooting)
                                       ↓
                               悟空对接 (wukong-data-connector)
                                       ↓
                               SpEL配置 (spel-generator)
```

各子技能详情见 `skills/` 目录下对应的 `SKILL.md`。
