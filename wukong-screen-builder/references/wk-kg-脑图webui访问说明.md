# wk-kg 脑图 webui 访问说明（LightRAG 知识图谱可视化）

> wk-kg 语义层(LightRAG)的知识图谱可视化界面 + 文档处理状态查看，钉钉认证保护。

## 一、能看什么
- **Knowledge Graph**：实体+关系的图谱可视化（"脑图"）——组件/模板/素材/官方文档抽取出的实体关系
- **Documents**：所有文档的处理状态（pending/processing/processed/failed）——重建/灌库进度在这看

## 二、访问方式（推荐：钉钉认证网址）
**https://gczx.egova.com.cn/wk-kg-graph/webui/**

流程：打开 → 没登录自动跳**钉钉扫码**（白名单=工程技术中心，跟 wk-kg MCP 同一套）→ 登录完**直接跳回脑图**。

## 三、备用：SSH 隧道（免 nginx 直连，调试用）
LightRAG webui：
\`\`\`bash
ssh -L 9100:127.0.0.1:9100 root@gczx.egova.com.cn   # DNS坏时用 root@8.160.174.102
\`\`\`
浏览器开 http://localhost:9100/webui/

Neo4j Browser（底层图数据库，可跑 Cypher）：
\`\`\`bash
ssh -L 7474:127.0.0.1:7474 -L 7687:127.0.0.1:7687 root@gczx.egova.com.cn
\`\`\`
浏览器开 http://localhost:7474/ ，连 bolt://localhost:7687，用户 neo4j，**密码见容器 env**：\`docker exec wk-kg-neo4j printenv | grep NEO4J_AUTH\`

## 四、技术实现（复用钉钉认证）
| 层 | 做法 |
|----|------|
| 认证 | 复用 wk-kg 钉钉 OAuth+session：oauth 回调 set cookie(\`wk_kg_sess\` 90天) + 新增 \`/wk-kg/auth/check\` 端点 + login 支持 \`redirect\` 参数(登录完跳回) |
| nginx | \`/wk-kg-graph/\` 用 **auth_request** 校验 cookie；未登录 302 跳钉钉登录(带 redirect=原地址) |
| SPA 适配 | sub_filter 改写 \`__LIGHTRAG_CONFIG__.apiPrefix\` → 让 webui 的 API 调用走子路径(webui/API/资源实测全 200) |
| 端口 | webui = LightRAG 容器 127.0.0.1:9100；认证服务 = wk-kg-mcp 127.0.0.1:3100 |

## 五、Durability（防被清/重建恢复）
- 服务端 patch(cookie/auth_check/redirect) **已进 git**：\`src/wk_kg_mcp/http_server.py\`，deploy 同步不还原
- nginx 路由 deploy **不自动应用**，片段存档在 \`deploy/nginx-graph-route.conf\`
- **恢复 nginx 路由**：把 \`deploy/nginx-graph-route.conf\` 的 location 块合进 \`/etc/nginx/conf.d/gczx.egova.com.cn.conf\`(插在 \`location /wk-kg-mcp/\` 前) → \`nginx -t\` → \`kill -HUP <nginx master pid>\`
