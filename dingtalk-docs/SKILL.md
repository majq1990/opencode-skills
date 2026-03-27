---
name: dingtalk-docs
description: Read and sync DingTalk (钉钉) documents from organization knowledge bases, track updates by modification time, fetch document content incrementally, and generate RAG-ready chunks for vector database
license: MIT
compatibility: opencode
metadata:
  category: integration
  platform: dingtalk
  features: document-sync, incremental-read, rag-export, vector-database-ready
---

## 功能概述

此 skill 用于读取钉钉文档，实现以下功能：

1. 获取组织内所有知识库列表
2. 获取知识库下的所有文档节点（递归遍历）
3. 批量获取文档详情（包括更新时间）
4. 增量同步：根据更新时间只获取变更的文档内容
5. 获取文档的具体内容
6. **RAG 数据切分**：将文档切分为适合向量数据库的块（chunks）
7. **多格式导出**：支持 JSONL、JSON、LangChain 等格式

## 认证配置

在使用此skill前，需要配置钉钉企业内部应用的认证信息：

### 1. 创建企业内部应用

在钉钉开发者后台创建企业内部应用，获取以下信息：
- **AppKey**: 应用的唯一标识
- **AppSecret**: 应用的密钥

### 2. 配置权限

确保应用具有以下权限：
- `wiki:knowledgeBase:read` - 读取知识库
- `wiki:doc:read` - 读取文档
- `contact:user:read` - 读取用户信息（可选）

### 3. 存储认证信息

在项目中创建 `.env.dingtalk` 文件（添加到 .gitignore）：

```env
DINGTALK_APPKEY=your_appkey
DINGTALK_APPSECRET=your_appsecret
```

或通过环境变量配置：

```bash
export DINGTALK_APPKEY=your_appkey
export DINGTALK_APPSECRET=your_appsecret
```

## API参考

### 1. 获取Access Token

**请求:**
```http
GET https://oapi.dingtalk.com/gettoken?appkey={appkey}&appsecret={appsecret}
```

**响应:**
```json
{
  "errcode": 0,
  "errmsg": "ok",
  "access_token": "abc123...",
  "expires_in": 7200
}
```

**注意事项:**
- access_token有效期为2小时（7200秒）
- 建议缓存token，避免频繁请求
- 调用频率限制：300次/分钟

### 2. 获取知识库列表

**请求:**
```http
GET https://api.dingtalk.com/v1.0/wiki/knowledgeBase/list?size=100
Header: x-acs-dingtalk-access-token: {access_token}
```

**参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| cursor | string | 否 | 分页游标 |
| size | int | 否 | 分页大小，最大100，默认20 |

**响应:**
```json
{
  "knowledgeBaseList": [
    {
      "knowledgeBaseId": "string",
      "name": "string",
      "description": "string",
      "creatorId": "string",
      "createdAt": 1234567890000,
      "updatedAt": 1234567890000
    }
  ],
  "hasMore": false,
  "nextCursor": "string"
}
```

**频率限制:** 100次/分钟/企业

### 3. 批量获取知识库信息

**请求:**
```http
POST https://api.dingtalk.com/v1.0/wiki/knowledgeBase/batchGet
Header: x-acs-dingtalk-access-token: {access_token}
Content-Type: application/json

{
  "knowledgeBaseIds": ["id1", "id2"]
}
```

**响应:**
```json
{
  "knowledgeBaseList": [
    {
      "knowledgeBaseId": "string",
      "name": "string",
      "description": "string",
      "creatorId": "string",
      "createdAt": 1234567890000,
      "updatedAt": 1234567890000
    }
  ]
}
```

**频率限制:** 100次/分钟/企业

### 4. 获取知识库节点列表

**请求:**
```http
GET https://api.dingtalk.com/v1.0/wiki/knowledgeBase/{knowledgeBaseId}/nodes
Header: x-acs-dingtalk-access-token: {access_token}
```

**参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| knowledgeBaseId | string | 是 | 知识库ID（路径参数） |
| cursor | string | 否 | 分页游标 |
| size | int | 否 | 分页大小，最大100 |

**响应:**
```json
{
  "nodeList": [
    {
      "nodeId": "string",
      "knowledgeBaseId": "string",
      "parentId": "string",
      "name": "string",
      "type": 2,
      "creatorId": "string",
      "createdAt": 1234567890000,
      "updatedAt": 1234567890000,
      "status": 0
    }
  ],
  "hasMore": false,
  "nextCursor": "string"
}
```

**节点类型(type):**
- 1: 文件夹
- 2: 文档

**状态(status):**
- 0: 正常
- 1: 已删除

**频率限制:** 100次/分钟/企业

### 5. 批量获取节点详情

**请求:**
```http
POST https://api.dingtalk.com/v1.0/wiki/node/batchGet
Header: x-acs-dingtalk-access-token: {access_token}
Content-Type: application/json

{
  "knowledgeBaseId": "string",
  "nodeIds": ["nodeId1", "nodeId2"]
}
```

**响应:**
```json
{
  "nodeList": [
    {
      "nodeId": "string",
      "knowledgeBaseId": "string",
      "parentId": "string",
      "name": "string",
      "type": 2,
      "creatorId": "string",
      "createdAt": 1234567890000,
      "updatedAt": 1234567890000,
      "status": 0
    }
  ]
}
```

**频率限制:** 100次/分钟/企业

### 6. 获取文档内容

**请求:**
```http
GET https://api.dingtalk.com/v1.0/wiki/doc/{docId}
Header: x-acs-dingtalk-access-token: {access_token}
```

**参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| docId | string | 是 | 文档ID（即nodeId，类型为2的节点） |

**响应:**
```json
{
  "docId": "string",
  "title": "string",
  "content": "string (JSON格式的文档内容)",
  "creatorId": "string",
  "createdAt": 1234567890000,
  "updatedAt": 1234567890000
}
```

**注意:** content字段为JSON格式的文档结构，需要解析处理

**频率限制:** 100次/分钟/企业

## 实现步骤

### 步骤1: 初始化同步状态文件

创建 `.dingtalk-sync.json` 文件用于存储同步状态：

```json
{
  "lastSyncTime": 1234567890000,
  "knowledgeBases": {},
  "documents": {}
}
```

### 步骤2: 获取Access Token

```javascript
async function getAccessToken(appkey, appsecret) {
  const url = `https://oapi.dingtalk.com/gettoken?appkey=${appkey}&appsecret=${appsecret}`;
  const response = await fetch(url);
  const data = await response.json();
  
  if (data.errcode !== 0) {
    throw new Error(`获取token失败: ${data.errmsg}`);
  }
  
  return {
    accessToken: data.access_token,
    expiresIn: data.expires_in
  };
}
```

### 步骤3: 获取所有知识库

```javascript
async function getAllKnowledgeBases(accessToken) {
  const knowledgeBases = [];
  let cursor = '';
  
  do {
    const url = `https://api.dingtalk.com/v1.0/wiki/knowledgeBase/list?size=100${cursor ? '&cursor=' + cursor : ''}`;
    const response = await fetch(url, {
      headers: {
        'x-acs-dingtalk-access-token': accessToken
      }
    });
    
    const data = await response.json();
    knowledgeBases.push(...(data.knowledgeBaseList || []));
    cursor = data.nextCursor;
    hasMore = data.hasMore;
  } while (hasMore);
  
  return knowledgeBases;
}
```

### 步骤4: 获取知识库下的所有节点

```javascript
async function getKnowledgeBaseNodes(accessToken, knowledgeBaseId) {
  const nodes = [];
  let cursor = '';
  let hasMore = true;
  
  do {
    const url = `https://api.dingtalk.com/v1.0/wiki/knowledgeBase/${knowledgeBaseId}/nodes?size=100${cursor ? '&cursor=' + cursor : ''}`;
    const response = await fetch(url, {
      headers: {
        'x-acs-dingtalk-access-token': accessToken
      }
    });
    
    const data = await response.json();
    nodes.push(...(data.nodeList || []));
    cursor = data.nextCursor;
    hasMore = data.hasMore;
  } while (hasMore);
  
  return nodes;
}
```

### 步骤5: 批量获取节点详情

```javascript
async function batchGetNodes(accessToken, knowledgeBaseId, nodeIds) {
  const batchSize = 100;
  const results = [];
  
  for (let i = 0; i < nodeIds.length; i += batchSize) {
    const batch = nodeIds.slice(i, i + batchSize);
    
    const response = await fetch('https://api.dingtalk.com/v1.0/wiki/node/batchGet', {
      method: 'POST',
      headers: {
        'x-acs-dingtalk-access-token': accessToken,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        knowledgeBaseId: knowledgeBaseId,
        nodeIds: batch
      })
    });
    
    const data = await response.json();
    results.push(...(data.nodeList || []));
    
    // 频率限制：100次/分钟
    if (i + batchSize < nodeIds.length) {
      await sleep(600);
    }
  }
  
  return results;
}
```

### 步骤6: 增量同步文档

```javascript
async function syncDocuments(accessToken, lastSyncTime) {
  // 1. 获取所有知识库
  const knowledgeBases = await getAllKnowledgeBases(accessToken);
  
  const updatedDocs = [];
  
  // 2. 遍历每个知识库
  for (const kb of knowledgeBases) {
    // 3. 获取知识库下的所有节点
    const nodes = await getKnowledgeBaseNodes(accessToken, kb.knowledgeBaseId);
    
    // 4. 过滤出更新的文档（type=2是文档，且updatedAt > lastSyncTime）
    const docNodes = nodes.filter(
      node => node.type === 2 && 
             node.status === 0 && 
             node.updatedAt > lastSyncTime
    );
    
    if (docNodes.length > 0) {
      // 5. 批量获取节点详情
      const nodeDetails = await batchGetNodes(
        accessToken, 
        kb.knowledgeBaseId, 
        docNodes.map(n => n.nodeId)
      );
      
      updatedDocs.push(...nodeDetails.map(doc => ({
        ...doc,
        knowledgeBaseName: kb.name
      })));
    }
  }
  
  return updatedDocs;
}
```

### 步骤7: 获取文档内容

```javascript
async function getDocumentContent(accessToken, docId) {
  const url = `https://api.dingtalk.com/v1.0/wiki/doc/${docId}`;
  const response = await fetch(url, {
    headers: {
      'x-acs-dingtalk-access-token': accessToken
    }
  });
  
  const data = await response.json();
  return data;
}
```

## 使用示例

### 示例1: 首次全量同步

```javascript
// 初始化
const accessToken = await getAccessToken(APPKEY, APPSECRET);

// 获取所有知识库
const knowledgeBases = await getAllKnowledgeBases(accessToken);
console.log(`发现 ${knowledgeBases.length} 个知识库`);

// 同步所有文档
for (const kb of knowledgeBases) {
  const nodes = await getKnowledgeBaseNodes(accessToken, kb.knowledgeBaseId);
  const docs = nodes.filter(n => n.type === 2 && n.status === 0);
  console.log(`${kb.name}: ${docs.length} 个文档`);
  
  // 保存到本地
  // ... 存储逻辑
}

// 更新同步时间
saveSyncState({ lastSyncTime: Date.now() });
```

### 示例2: 增量同步

```javascript
const syncState = loadSyncState();
const updatedDocs = await syncDocuments(accessToken, syncState.lastSyncTime);

console.log(`发现 ${updatedDocs.length} 个更新的文档`);

for (const doc of updatedDocs) {
  // 获取文档内容
  const content = await getDocumentContent(accessToken, doc.nodeId);
  
  console.log(`[${doc.knowledgeBaseName}] ${doc.name}`);
  console.log(`  更新时间: ${new Date(doc.updatedAt).toISOString()}`);
  console.log(`  内容预览: ${content.content.substring(0, 100)}...`);
  
  // 更新本地存储
  // ... 存储逻辑
}

// 更新同步时间
saveSyncState({ lastSyncTime: Date.now() });
```

### 示例3: 获取特定文档

```javascript
const docId = 'xxxxx';
const content = await getDocumentContent(accessToken, docId);

console.log(`文档标题: ${content.title}`);
console.log(`创建者: ${content.creatorId}`);
console.log(`内容: ${content.content}`);
```

## 数据存储结构

建议使用以下结构存储同步数据：

```
.dingtalk/
├── sync-state.json          # 同步状态
├── knowledge-bases.json     # 知识库列表
└── documents/
    ├── {docId1}.json        # 文档元数据
    ├── {docId2}.json
    └── content/
        ├── {docId1}.md      # 文档内容（转换为Markdown）
        └── {docId2}.md
```

**sync-state.json:**
```json
{
  "lastSyncTime": 1234567890000,
  "accessToken": "xxx",
  "tokenExpiresAt": 1234567890000
}
```

**knowledge-bases.json:**
```json
[
  {
    "knowledgeBaseId": "xxx",
    "name": "产品文档",
    "description": "产品相关文档",
    "creatorId": "user123",
    "createdAt": 1234567890000,
    "updatedAt": 1234567890000,
    "documentCount": 50
  }
]
```

**documents/{docId}.json:**
```json
{
  "nodeId": "xxx",
  "knowledgeBaseId": "xxx",
  "knowledgeBaseName": "产品文档",
  "parentId": "parent-xxx",
  "name": "API文档",
  "type": 2,
  "creatorId": "user123",
  "createdAt": 1234567890000,
  "updatedAt": 1234567890000,
  "status": 0,
  "contentPath": "content/xxx.md"
}
```

## 错误处理

### 常见错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 0 | 成功 | - |
| 40035 | 缺少参数 | 检查请求参数 |
| 40036 | 参数格式错误 | 检查参数格式 |
| 40078 | 不存在的知识库 | 确认知识库ID |
| 40079 | 不存在的节点 | 确认节点ID |
| 50001 | access_token过期 | 重新获取token |
| 50002 | 权限不足 | 检查应用权限配置 |

### 错误处理示例

```javascript
async function apiCall(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const result = await fn();
      return result;
    } catch (error) {
      if (error.code === 50001) {
        // token过期，重新获取
        accessToken = await getAccessToken(APPKEY, APPSECRET);
        continue;
      }
      
      if (error.code === 40078 || error.code === 40079) {
        // 资源不存在，跳过
        console.warn(`资源不存在: ${error.message}`);
        return null;
      }
      
      if (i === maxRetries - 1) {
        throw error;
      }
      
      // 等待后重试
      await sleep(1000 * (i + 1));
    }
  }
}
```

## 频率限制处理

钉钉API有调用频率限制，建议：

1. **批量处理**: 使用批量API减少请求次数
2. **限流控制**: 控制调用频率在限制内
3. **缓存Token**: 缓存access_token避免频繁请求

```javascript
// 简单的限流器
class RateLimiter {
  constructor(maxRequests, perMinute) {
    this.maxRequests = maxRequests;
    this.perMinute = perMinute;
    this.requests = [];
  }
  
  async wait() {
    const now = Date.now();
    this.requests = this.requests.filter(t => now - t < this.perMinute * 1000);
    
    if (this.requests.length >= this.maxRequests) {
      const waitTime = this.perMinute * 1000 - (now - this.requests[0]);
      await sleep(waitTime);
    }
    
    this.requests.push(now);
  }
}

// 使用限流器
const limiter = new RateLimiter(90, 1); // 90次/分钟（留余量）

async function rateLimitedFetch(url, options) {
  await limiter.wait();
  return fetch(url, options);
}
```

## 何时使用此Skill

当用户需要：
- 同步组织内的钉钉文档到本地
- 定期检查文档更新
- 批量导出钉钉文档
- 构建文档搜索索引
- 分析文档变更历史

## 相关资源

- [钉钉开放平台文档](https://open.dingtalk.com/document/development/dingtalk-document-overview)
- [获取知识库列表API](https://open.dingtalk.com/document/development/get-knowledge-base-list)
- [批量获取知识库API](https://open.dingtalk.com/document/development/batch-acquisition-of-knowledge-base)
- [获取节点列表API](https://open.dingtalk.com/document/orgapp/queries-the-list-of-knowledge-base-nodes)
- [获取文档内容API](https://open.dingtalk.com/document/orgapp/obtains-the-content-of-a-document)