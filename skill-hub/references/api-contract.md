# skill 服务器 API 契约（实测版）

> 基准日期：2026-10-08。全部端点均经真实请求验证（浏览器 UA + Bearer token）。
> skill-hub 只使用下述只读接口；上传/删除等写接口不在 hub 能力内。

## 基础

- Base：`https://demo.egova.com.cn/skill-api`
- 鉴权：`Authorization: Bearer <enterprise_token>`，token 来自本机 skills-manager 登录会话（见 [session-protocol.md](session-protocol.md)），不内置账号
- 请求头：浏览器 User-Agent + `Accept: application/json`
- 可见性：服务端按登录者身份过滤，三级 `public` / `tech-manager` / `support`，只能看到自己有权的 skill
- 安全：仅 https；禁跟随重定向（301/302/303/307/308 一律视为异常）

## 接口清单

### GET /skills —— 列出全部可见 skill

响应：

```json
{
  "success": true,
  "count": 34,
  "skills": [
    {
      "name": "agentmail",
      "version": "1.0.0",
      "description": "…",
      "author": "",
      "tags": [],
      "visibility": "tech-manager",
      "updatedAt": "2026-09-15T08:50:39.177Z"
    }
  ]
}
```

支持 `?tag=<tag>` 查询参数，但**服务端忽略该参数、仍返回全量**（实测任意 tag 值都返回 34 个）——tag 过滤须在客户端本地做（skill_server.py 的 `list --tag` 即本地过滤）。

### GET /skills/search?q=<关键词> —— 关键词搜索

响应结构与 `/skills` 相同（`{success, count, skills[]}`）。中英文关键词均可用。

**两个实测行为（客户端必须适配）**：
- 多词整串搜会 0 命中：服务端把整串当一个词匹配，`?q=redmine 批量` 返回 0，`?q=redmine` 返回 6。客户端应逐词搜后合并去重（skill_server.py 默认行为，`--exact` 可关掉）
- 大小写不敏感：`Redmine` 与 `redmine` 等价

### GET /skills/tags —— 全部 tag

```json
{ "success": true, "count": 24, "tags": ["city-lifeline", "cli", "dingtalk", "…"] }
```

注意：多数 skill 的 `tags` 为空数组，tag 覆盖率低；tag 适合浏览，不适合当唯一筛选手段。

### GET /skills/{name} —— skill 详情

注意：数据嵌套在 `skill` 键内。

```json
{
  "success": true,
  "skill": {
    "name": "build-pipeline",
    "description": "…",
    "author": "majianquan",
    "license": "MIT",
    "tags": [],
    "visibility": "support",
    "versions": [
      { "version": "1.0.1", "status": "published", "updatedAt": "…" },
      { "version": "1.0.0", "status": "published", "updatedAt": "…" }
    ],
    "latestVersion": "1.0.1"
  }
}
```

### GET /skills/{name}/versions —— 版本列表

`{ "success": true, "name": "…", "versions": [ { "version": "1.0.1", "status": "published", "updatedAt": "…" } ] }`，首个为最新。

### GET /skills/{name}/{version}/download —— 下载 skill 包

- 返回二进制 zip（`application/zip`），非 JSON
- 包结构：`SKILL.md` 在 zip 根（主流）；个别包外裹一层目录，客户端解压后需按"根目录优先、其次唯一子目录"定位 SKILL.md
- 版本号必须显式出现在路径中（`/skills/{name}/download` 单段形式不存在，实测 404）

## 错误处置

| 状态 | 含义 | hub 行为 |
|------|------|----------|
| 401 | 未带 token / 登录态过期 | 提示"打开 skills-manager 重新登录企业服务器"，不自行兜底登录 |
| 404 | 资源不存在（名字错/无权限时也可能 404） | 如实提示；搜相似名 |
| 3xx | 重定向 | 拒绝跟随，按异常处理 |

## 存在但 hub 不使用的端点（写操作）

`POST /skills/{name}/upload`、`DELETE /skills/{name}[/{version}]`、`PUT /skills/{name}/visibility`、`POST /feedback`、agents 系列。上传由 skill-publisher 负责；删除/可见性属管理操作，走 skills-manager GUI。
