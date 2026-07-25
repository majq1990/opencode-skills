/**
 * 钉钉文档同步工具 v2.0 API
 */

const DINGTALK_API_BASE = 'https://api.dingtalk.com/v2.0';
const DINGTALK_OAPI_BASE = 'https://oapi.dingtalk.com';

class DingTalkDocsSync {
  constructor(appKey, appSecret, operatorId) {
    this.appKey = appKey;
    this.appSecret = appSecret;
    this.operatorId = operatorId;
    this.accessToken = null;
    this.tokenExpiresAt = 0;
    this.rateLimiter = new RateLimiter(90, 1);
  }

  async getAccessToken() {
    if (this.accessToken && Date.now() < this.tokenExpiresAt) {
      return this.accessToken;
    }

    const url = `${DINGTALK_OAPI_BASE}/gettoken?appkey=${this.appKey}&appsecret=${this.appSecret}`;
    const response = await fetch(url);
    const data = await response.json();

    if (data.errcode !== 0) {
      throw new Error(`获取 access_token 失败：${data.errmsg} (errcode: ${data.errcode})`);
    }

    this.accessToken = data.access_token;
    this.tokenExpiresAt = Date.now() + (data.expires_in - 300) * 1000;

    return this.accessToken;
  }

  async request(url, options = {}) {
    await this.rateLimiter.wait();
    
    const token = await this.getAccessToken();
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'x-acs-dingtalk-access-token': token,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    const data = await response.json();

    if (data.code && data.code !== 'ok') {
      if (data.code.includes('Authentication')) {
        this.accessToken = null;
        return this.request(url, options);
      }
      throw new Error(`API 调用失败：${data.message} (code: ${data.code})`);
    }

    if (data.errcode && data.errcode !== 0) {
      if (data.errcode === 50001) {
        this.accessToken = null;
        return this.request(url, options);
      }
      throw new Error(`API 调用失败：${data.errmsg} (errcode: ${data.errcode})`);
    }

    return data;
  }

  async getAllWorkspaces() {
    const workspaces = [];
    let nextToken = '';
    let hasMore = true;

    while (hasMore) {
      const url = `${DINGTALK_API_BASE}/wiki/workspaces?maxResults=100${nextToken ? '&nextToken=' + nextToken : ''}&operatorId=${this.operatorId}`;
      const data = await this.request(url);
      
      if (data.workspaces) {
        workspaces.push(...data.workspaces);
      }
      
      nextToken = data.nextToken || '';
      hasMore = data.hasMore || false;
    }

    return workspaces;
  }

  async getWorkspaceNodes(workspaceId) {
    const nodes = [];
    let nextToken = '';
    let hasMore = true;

    while (hasMore) {
      const url = `${DINGTALK_API_BASE}/wiki/nodes?workspaceId=${workspaceId}&maxResults=100${nextToken ? '&nextToken=' + nextToken : ''}&operatorId=${this.operatorId}`;
      const data = await this.request(url);

      if (data.nodes) {
        nodes.push(...data.nodes);
      }

      nextToken = data.nextToken || '';
      hasMore = data.hasMore || false;
    }

    return nodes;
  }

  async batchGetNodes(workspaceId, nodeIds) {
    const batchSize = 100;
    const results = [];

    for (let i = 0; i < nodeIds.length; i += batchSize) {
      const batch = nodeIds.slice(i, i + batchSize);
      const url = `${DINGTALK_API_BASE}/wiki/nodes/batchGet`;

      const data = await this.request(url, {
        method: 'POST',
        body: JSON.stringify({
          workspaceId: workspaceId,
          nodeIds: batch,
          operatorId: this.operatorId
        })
      });

      if (data.nodes) {
        results.push(...data.nodes);
      }
    }

    return results;
  }

  async getDocumentContent(docId) {
    const url = `${DINGTALK_API_BASE}/wiki/docs/${docId}?operatorId=${this.operatorId}`;
    return await this.request(url);
  }

  async syncDocuments(lastSyncTime = 0) {
    const workspaces = await this.getAllWorkspaces();
    const updatedDocs = [];

    for (const workspace of workspaces) {
      console.log(`正在处理知识库：${workspace.name} (${workspace.workspaceId})`);
      
      const nodes = await this.getWorkspaceNodes(workspace.workspaceId);
      console.log(`  发现 ${nodes.length} 个节点`);
      
      const docNodes = nodes.filter(
        node => node.nodeType === 'DOCUMENT' && 
               (lastSyncTime === 0 || new Date(node.gmtModified).getTime() > lastSyncTime)
      );

      console.log(`  其中 ${docNodes.length} 个更新的文档`);

      if (docNodes.length > 0) {
        const nodeDetails = await this.batchGetNodes(
          workspace.workspaceId,
          docNodes.map(n => n.nodeId)
        );

        updatedDocs.push(...nodeDetails.map(doc => ({
          ...doc,
          workspaceName: workspace.name
        })));
      }
    }

    return {
      workspaces,
      updatedDocs,
      syncTime: Date.now()
    };
  }

  async getDocTree(workspaceId) {
    const nodes = await this.getWorkspaceNodes(workspaceId);
    const nodeMap = new Map();
    const rootNodes = [];

    nodes.forEach(node => {
      nodeMap.set(node.nodeId, { ...node, children: [] });
    });

    nodes.forEach(node => {
      const currentNode = nodeMap.get(node.nodeId);
      if (node.parentId && nodeMap.has(node.parentId)) {
        nodeMap.get(node.parentId).children.push(currentNode);
      } else {
        rootNodes.push(currentNode);
      }
    });

    return rootNodes;
  }
}

class RateLimiter {
  constructor(maxRequests, perMinute) {
    this.maxRequests = maxRequests;
    this.perMinute = perMinute;
    this.requests = [];
  }

  async wait() {
    const now = Date.now();
    this.requests = this.requests.filter(t => now - t < this.perMinute * 60 * 1000);

    if (this.requests.length >= this.maxRequests) {
      const waitTime = this.perMinute * 60 * 1000 - (now - this.requests[0]);
      console.log(`达到频率限制，等待 ${(waitTime / 1000).toFixed(1)} 秒...`);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }

    this.requests.push(Date.now());
  }
}

async function main() {
  const appKey = process.env.DINGTALK_APPKEY;
  const appSecret = process.env.DINGTALK_APPSECRET;
  const operatorId = process.env.DINGTALK_OPERATOR_ID;

  if (!appKey || !appSecret) {
    console.error('请设置环境变量 DINGTALK_APPKEY 和 DINGTALK_APPSECRET');
    process.exit(1);
  }

  if (!operatorId) {
    console.error('请设置环境变量 DINGTALK_OPERATOR_ID (用户 ID)');
    process.exit(1);
  }

  const sync = new DingTalkDocsSync(appKey, appSecret, operatorId);

  try {
    console.log('开始同步钉钉文档...\n');

    const lastSyncTime = 0;
    const result = await sync.syncDocuments(lastSyncTime);

    console.log(`\n=== 同步结果 ===`);
    console.log(`发现 ${result.workspaces.length} 个知识库`);
    console.log(`发现 ${result.updatedDocs.length} 个更新的文档\n`);

    for (const doc of result.updatedDocs.slice(0, 5)) {
      console.log(`[${doc.workspaceName}] ${doc.title}`);
      console.log(`  节点 ID: ${doc.nodeId}`);
      console.log(`  更新时间：${doc.gmtModified}`);
      
      const content = await sync.getDocumentContent(doc.nodeId);
      console.log(`  内容预览：${content.content ? content.content.substring(0, 100) + '...' : '(无内容)'}\n`);
    }

    if (result.updatedDocs.length > 5) {
      console.log(`... 还有 ${result.updatedDocs.length - 5} 个文档`);
    }

    console.log(`\n同步完成！时间：${new Date(result.syncTime).toLocaleString('zh-CN')}`);
  } catch (error) {
    console.error('同步失败:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

if (typeof require !== 'undefined' && require.main === module) {
  main();
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { DingTalkDocsSync, RateLimiter };
}
