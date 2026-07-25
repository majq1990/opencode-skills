# wk-kg 调用说明（悟空组件知识图谱 MCP）

> 2026-06-16 | wk-kg = 输入"想做什么视觉效果"→输出"用哪个组件+怎么配+能力边界"。覆盖 395 组件、5 数据源。

## 一、它能回答什么
- 「这块视觉效果用哪个悟空组件？」→ 候选组件 + 能力边界
- 「Swiper11 的数据格式长什么样？」→ 完整能力卡（schema/坑/样例）
- 「有没有能做 XX 的组件？」→ 语义检索
- 「某类组件都有哪些？」→ 分类清单
- 「写 cardData 用 PUT 还是 POST？」→ fork-cd 写入范式

## 二、接入方式
- **MCP 端点**：`https://gczx.egova.com.cn/wk-kg-mcp/`（type=http）
- **鉴权**：Bearer token（90 天有效），钉钉扫码获取：`https://gczx.egova.com.cn/wk-kg/oauth/dingtalk/login`（白名单=工程技术中心）
- **客户端配置**（`~/.claude.json` 的 mcpServers 或 Cursor MCP 设置）：
```json
{
  "mcpServers": {
    "wk-kg": {
      "type": "http",
      "url": "https://gczx.egova.com.cn/wk-kg-mcp/",
      "headers": { "Authorization": "Bearer <你的token>" }
    }
  }
}
```
- **健康自检**：`curl -s -o /dev/null -w "%{http_code}" https://gczx.egova.com.cn/wk-kg-mcp/`
  - 返回 **401** = 服务正常（要 token）；**502** = 后端挂了（去 gczx 看 pm2 wk-kg-mcp）

## 三、5 个工具（参数 + 何时调 + 返回）

| 工具 | 参数 | 何时调 | 返回 |
|------|------|--------|------|
| `recommend_components` | `visual_description`(必填,视觉块描述), `limit`(可选) | 拆完视觉块，每块调一次 | 候选组件 id + 能力 + `cannotDo` 边界 |
| `get_component_schema` | `component_id` | 选定候选后，看具体怎么用 | 完整能力卡：cardDataSchema/styleKnobs/quirks/writeMethod/example/realExamples |
| `search_components` | `query` | 模糊找"有某能力的组件" | 语义/关键词检索结果 |
| `list_components` | `category`(可选) | 看某类组件全清单 | 按 category 过滤的清单 + 替代关系 |
| `get_write_pattern` | 无 | 装配 cardData 前 | fork-cd 写入范式（POST 建副本→batch-modify 改 dataId，PUT 不支持）|

### 调用示例（MCP 工具调用）
```
recommend_components(visual_description="左侧 19 个区的力量分布排名表，每行区名+数值")
→ [{id:"Swiper11", name:"万能表格", cannotDo:["单元格内嵌迷你折线","跨行合并"], verified:true}, ...]

get_component_schema(component_id="Swiper11")
→ {cardDataSchema:{shape:[[{name,text,value,styleValue}],...]}, cannotDo:[...], realExamples:[...真实大屏样例...], writeMethod:"fork-cd"}
```

## 四、典型调用流程（大屏复现/搭建时）
```
1. 视觉拆分目标图 → 每个独立视觉块一行
2. 每块 recommend_components(视觉块描述) → 拿候选 + cannotDo
3. 用户逐项确认组件（门控）
4. 每个确认的组件 get_component_schema(id) → 拿数据格式 shape + 真实样例
5. 装配前 get_write_pattern() → 按 fork-cd 写 cardData
```

## 五、覆盖的 5 个数据源（卡里能拿到什么）
| 源 | 体现在能力卡哪个字段 | 覆盖 |
|----|---------------------|------|
| ① 组件库元数据 | id/name/category/aliases | 395/395 |
| ② 官方默认配置探测 | cardDataSchema | 395/395 |
| ③ 真实大屏样例 | realExamples | 251/395 |
| ④ 人工踩坑经验 | cannotDo/quirks/example/verified | 9 深度卡 |
| ⑤ 官方内部文档 | 语义层（LightRAG，file_source=doc/）| 176 篇 |

> ①②③④烤进 395 张 JSON 能力卡（精确层，get_component_schema 直读）；⑤在 LightRAG 语义层（recommend_components/search_components 召回时引用官方文档）。

## 六、注意事项
- `recommend_components` 是**语义召回**，可能漏/偏——结果必须看 `cannotDo` 边界，别盲信
- `get_component_schema` 才是**精确能力卡**（直读 JSON，含真实样例），落地前必查
- 某视觉块所有候选都被 `cannotDo` 否决 → 直接判"做不到"，不硬拼凑
- 服务部署在 gczx（pm2 `wk-kg-mcp` 端口3100 + docker lightrag/neo4j），重启自起（pm2 save + systemctl）

## 七、原始 HTTP 协议（不走 MCP 客户端时）
wk-kg-mcp 是 **MCP streamable-http**（JSON-RPC over HTTP）。需先 `initialize` 握手拿 session，再 `tools/call`。建议直接用支持 MCP 的客户端（Claude Code / Cursor），别手撸协议。
