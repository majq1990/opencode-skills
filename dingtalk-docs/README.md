# 钉钉文档同步 Skill

这是一个用于读取和同步钉钉文档的 OpenCode skill，支持 RAG 数据导出。

## 功能特性

- 获取组织内所有知识库列表
- 获取知识库下的所有文档节点（递归遍历）
- 批量获取文档详情（包括更新时间）
- 增量同步：根据更新时间只获取变更的文档内容
- 获取文档的具体内容
- **RAG 数据切分**：将文档切分为适合向量数据库的块
- **多格式导出**：支持 JSONL、JSON、LangChain 等格式

## 安装

此skill已安装到全局配置目录：
```
~/.config/opencode/skills/dingtalk-docs/
```

## 配置

### 1. 创建钉钉企业内部应用

1. 访问 [钉钉开发者后台](https://open-dev.dingtalk.com/)
2. 创建企业内部应用
3. 获取 AppKey 和 AppSecret
4. 配置应用权限：
   - `wiki:knowledgeBase:read` - 读取知识库
   - `wiki:doc:read` - 读取文档

### 2. 配置环境变量

方式一：创建 `.env.dingtalk` 文件（推荐）

```bash
# 在项目根目录创建
echo "DINGTALK_APPKEY=your_appkey" > .env.dingtalk
echo "DINGTALK_APPSECRET=your_appsecret" >> .env.dingtalk

# 添加到 .gitignore
echo ".env.dingtalk" >> .gitignore
```

方式二：设置环境变量

```bash
export DINGTALK_APPKEY=your_appkey
export DINGTALK_APPSECRET=your_appsecret
```

## 使用方法

### 在 OpenCode 中使用

在 OpenCode 会话中，可以直接请求 AI 使用此 skill：

```
请使用 dingtalk-docs skill 同步我们组织的钉钉文档
```

### 使用提供的 JavaScript 库

```javascript
const { DingTalkDocsSync } = require('./lib/dingtalk-sync');

const sync = new DingTalkDocsSync(appKey, appSecret);

// 同步所有文档
const result = await sync.syncDocuments();

// 获取文档内容
const content = await sync.getDocumentContent(docId);

// 获取文档树结构
const tree = await sync.getDocTree(knowledgeBaseId);
```

### 直接运行示例代码

```bash
# 设置环境变量
export DINGTALK_APPKEY=your_appkey
export DINGTALK_APPSECRET=your_appsecret
export DINGTALK_OPERATOR_ID=your_unionid

# 运行基础同步
node ~/.config/opencode/skills/dingtalk-docs/lib/dingtalk-sync.js

# 运行 RAG 数据导出（推荐）
node ~/.config/opencode/skills/dingtalk-docs/lib/rag-sync.js
```

### RAG 数据导出

运行 `rag-sync.js` 会生成适合向量数据库的数据格式：

```bash
# 运行 RAG 同步
node lib/rag-sync.js > rag-output.jsonl

# 输出格式示例
{
  "id": "nodeId_chunk_0",
  "content": "文档内容片段...",
  "metadata": {
    "nodeId": "...",
    "workspaceId": "...",
    "workspaceName": "知识库名称",
    "fileName": "文档名",
    "chunkIndex": 0,
    "totalChunks": 5
  }
}
```

**支持的导出格式：**
- `jsonl` - 每行一个 JSON 对象，适合批量导入向量数据库
- `json` - 完整的 JSON 数组格式
- `langchain` - LangChain Document 格式

## API 参考

完整的 API 文档请参考 `SKILL.md` 文件。

### 主要 API

| 方法 | 说明 |
|------|------|
| `getAccessToken()` | 获取访问令牌 |
| `getAllKnowledgeBases()` | 获取所有知识库 |
| `getKnowledgeBaseNodes(id)` | 获取知识库节点列表 |
| `batchGetNodes(id, nodeIds)` | 批量获取节点详情 |
| `getDocumentContent(docId)` | 获取文档内容 |
| `syncDocuments(lastSyncTime)` | 增量同步文档 |
| `getDocTree(id)` | 获取文档树结构 |

## 数据结构

### 同步状态 (sync-state.json)

```json
{
  "lastSyncTime": 1234567890000,
  "accessToken": "xxx",
  "tokenExpiresAt": 1234567890000
}
```

### 知识库 (knowledge-bases.json)

```json
[
  {
    "knowledgeBaseId": "xxx",
    "name": "产品文档",
    "description": "产品相关文档",
    "creatorId": "user123",
    "createdAt": 1234567890000,
    "updatedAt": 1234567890000
  }
]
```

### 文档节点

```json
{
  "nodeId": "xxx",
  "knowledgeBaseId": "xxx",
  "parentId": "parent-xxx",
  "name": "API文档",
  "type": 2,
  "creatorId": "user123",
  "createdAt": 1234567890000,
  "updatedAt": 1234567890000,
  "status": 0
}
```

## 频率限制

钉钉 API 有以下频率限制：

- 获取 access_token: 300次/分钟
- 其他 API: 100次/分钟/企业

代码中已实现自动限流处理。

## 错误处理

常见错误码：

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 50001 | access_token 过期（自动重试） |
| 50002 | 权限不足 |
| 40078 | 知识库不存在 |
| 40079 | 节点不存在 |

## 相关链接

- [钉钉开放平台](https://open.dingtalk.com/)
- [钉钉文档 API 文档](https://open.dingtalk.com/document/development/dingtalk-document-overview)
- [OpenCode Skills 文档](https://opencode.ai/docs/skills/)

## License

MIT