/**
 * 钉钉文档同步 + RAG 数据切分工具
 * 验证知识库读取并生成向量库格式数据
 */

const DINGTALK_API_BASE = 'https://api.dingtalk.com/v2.0';
const DINGTALK_OAPI_BASE = 'https://oapi.dingtalk.com';

class DingTalkRAGSync {
  constructor(appKey, appSecret, operatorId) {
    this.appKey = appKey;
    this.appSecret = appSecret;
    this.operatorId = operatorId;
    this.accessToken = null;
    this.tokenExpiresAt = 0;
  }

  async getAccessToken() {
    if (this.accessToken && Date.now() < this.tokenExpiresAt) {
      return this.accessToken;
    }

    const url = `${DINGTALK_OAPI_BASE}/gettoken?appkey=${this.appKey}&appsecret=${this.appSecret}`;
    const response = await fetch(url);
    const data = await response.json();

    if (data.errcode !== 0) {
      throw new Error(`获取 access_token 失败：${data.errmsg}`);
    }

    this.accessToken = data.access_token;
    this.tokenExpiresAt = Date.now() + (data.expires_in - 300) * 1000;
    return this.accessToken;
  }

  async request(url, options = {}) {
    const token = await this.getAccessToken();
    const response = await fetch(url, {
      ...options,
      headers: {
        'x-acs-dingtalk-access-token': token,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    return await response.json();
  }

  // 获取所有知识库
  async getAllWorkspaces() {
    const workspaces = [];
    let nextToken = '';
    
    do {
      const url = `${DINGTALK_API_BASE}/wiki/workspaces?maxResults=100${nextToken ? '&nextToken=' + nextToken : ''}&operatorId=${this.operatorId}`;
      const data = await this.request(url);
      if (data.workspaces) workspaces.push(...data.workspaces);
      nextToken = data.nextToken || '';
    } while (nextToken);
    
    return workspaces;
  }

  // 获取节点列表（支持递归）
  async getNodes(workspaceId, parentNodeId = 'root', depth = 0) {
    const url = `${DINGTALK_API_BASE}/wiki/nodes?workspaceId=${workspaceId}&maxResults=100&operatorId=${this.operatorId}&parentNodeId=${parentNodeId}`;
    const data = await this.request(url);
    return data.nodes || [];
  }

  // 递归获取所有节点
  async getAllNodes(workspaceId, rootNodeId) {
    const allNodes = [];
    
    const traverse = async (parentId) => {
      const nodes = await this.getNodes(workspaceId, parentId);
      for (const node of nodes) {
        allNodes.push(node);
        if (node.hasChildren && node.type === 'FOLDER') {
          await traverse(node.nodeId);
        }
      }
    };
    
    await traverse(rootNodeId);
    return allNodes;
  }

  // 获取文档内容（需要额外权限）
  async getDocumentContent(nodeId) {
    try {
      const url = `${DINGTALK_API_BASE}/wiki/docs/${nodeId}/content?operatorId=${this.operatorId}`;
      const data = await this.request(url, { method: 'POST', body: '{}' });
      return data.content || '';
    } catch (e) {
      console.log(`  获取文档内容失败：${e.message}`);
      return null;
    }
  }

  // 完整同步一个知识库
  async syncWorkspace(workspace) {
    console.log(`\n📚 知识库：${workspace.name}`);
    console.log(`   ID: ${workspace.workspaceId}`);
    console.log(`   描述：${workspace.description}`);
    console.log(`   根节点：${workspace.rootNodeId}`);

    const nodes = await this.getAllNodes(workspace.workspaceId, workspace.rootNodeId);
    
    const folders = nodes.filter(n => n.type === 'FOLDER');
    const files = nodes.filter(n => n.type === 'FILE');

    console.log(`   📁 文件夹：${folders.length} 个`);
    console.log(`   📄 文档：${files.length} 个`);

    return { workspace, folders, files, allNodes: nodes };
  }

  // 生成 RAG 数据块
  generateRAGChunks(workspaceData, options = {}) {
    const { 
      chunkSize = 500,      // 每块字符数
      chunkOverlap = 50,    // 重叠字符数
      includeMetadata = true // 包含元数据
    } = options;

    const chunks = [];
    const { workspace, files } = workspaceData;

    for (const file of files) {
      // 模拟文档内容（实际使用时调用 getDocumentContent）
      const mockContent = `文档标题：${file.name}\n文档路径：${file.url}\n创建时间：${file.createTime}\n更新时间：${file.modifiedTime}`;
      
      // 如果内容太长，进行切分
      const textChunks = this.splitText(mockContent, chunkSize, chunkOverlap);
      
      textChunks.forEach((chunk, idx) => {
        const ragChunk = {
          id: `${file.nodeId}_chunk_${idx}`,
          content: chunk,
          metadata: includeMetadata ? {
            nodeId: file.nodeId,
            workspaceId: workspace.workspaceId,
            workspaceName: workspace.name,
            fileName: file.name,
            fileUrl: file.url,
            chunkIndex: idx,
            totalChunks: textChunks.length,
            createTime: file.createTime,
            modifiedTime: file.modifiedTime
          } : undefined
        };
        chunks.push(ragChunk);
      });
    }

    return chunks;
  }

  // 文本切分（支持中文）
  splitText(text, chunkSize, overlap) {
    if (text.length <= chunkSize) {
      return [text];
    }

    const chunks = [];
    let start = 0;

    while (start < text.length) {
      let end = start + chunkSize;
      
      // 尝试在句子边界处切分
      if (end < text.length) {
        const sentenceEnd = text.lastIndexOf('\n', end);
        if (sentenceEnd > start) {
          end = sentenceEnd + 1;
        }
      }

      chunks.push(text.slice(start, Math.min(end, text.length)));
      start = end - overlap;

      if (start >= text.length) break;
    }

    return chunks;
  }

  // 导出为向量库格式
  exportToVectorFormat(chunks, format = 'jsonl') {
    if (format === 'jsonl') {
      return chunks.map(c => JSON.stringify(c)).join('\n');
    } else if (format === 'json') {
      return JSON.stringify(chunks, null, 2);
    } else if (format === 'langchain') {
      // LangChain Document 格式
      return chunks.map(c => ({
        pageContent: c.content,
        metadata: c.metadata || {}
      }));
    }
    return chunks;
  }
}

// 主函数
async function main() {
  const appKey = process.env.DINGTALK_APPKEY;
  const appSecret = process.env.DINGTALK_APPSECRET;
  const operatorId = process.env.DINGTALK_OPERATOR_ID;

  if (!appKey || !appSecret || !operatorId) {
    console.error('请设置环境变量：DINGTALK_APPKEY, DINGTALK_APPSECRET, DINGTALK_OPERATOR_ID');
    process.exit(1);
  }

  const sync = new DingTalkRAGSync(appKey, appSecret, operatorId);

  console.log('=== 钉钉文档 RAG 数据同步验证 ===\n');

  // 1. 获取所有知识库
  const workspaces = await sync.getAllWorkspaces();
  console.log(`发现 ${workspaces.length} 个知识库\n`);

  // 2. 同步每个知识库
  const allWorkspaceData = [];
  for (const ws of workspaces) {
    const data = await sync.syncWorkspace(ws);
    allWorkspaceData.push(data);
  }

  // 3. 生成 RAG 数据块
  console.log('\n=== 生成 RAG 数据块 ===\n');
  const allChunks = [];
  
  for (const wsData of allWorkspaceData) {
    if (wsData.files.length === 0) continue;
    
    const chunks = sync.generateRAGChunks(wsData, {
      chunkSize: 500,
      chunkOverlap: 50,
      includeMetadata: true
    });
    
    console.log(`[${wsData.workspace.name}] 生成 ${chunks.length} 个数据块`);
    allChunks.push(...chunks);
  }

  // 4. 显示示例数据块
  console.log('\n=== RAG 数据块示例（前 3 个）===\n');
  for (const chunk of allChunks.slice(0, 3)) {
    console.log(JSON.stringify(chunk, null, 2));
    console.log('---');
  }

  // 5. 导出为不同格式
  console.log('\n=== 导出格式示例 ===\n');
  
  // JSONL 格式（适合向量数据库导入）
  const jsonlOutput = sync.exportToVectorFormat(allChunks, 'jsonl');
  console.log('JSONL 格式（前 500 字符）:');
  console.log(jsonlOutput.substring(0, 500) + '...\n');

  // LangChain 格式
  const langchainDocs = sync.exportToVectorFormat(allChunks, 'langchain');
  console.log(`LangChain 格式：${langchainDocs.length} 个文档`);
  console.log('示例:', JSON.stringify(langchainDocs[0], null, 2).substring(0, 300) + '...\n');

  // 6. 统计信息
  console.log('\n=== 统计信息 ===');
  console.log(`总知识库数：${workspaces.length}`);
  console.log(`总文档数：${allWorkspaceData.reduce((sum, d) => sum + d.files.length, 0)}`);
  console.log(`总文件夹数：${allWorkspaceData.reduce((sum, d) => sum + d.folders.length, 0)}`);
  console.log(`生成 RAG 数据块：${allChunks.length} 个`);
  console.log(`预计向量数量：${allChunks.length}`);

  console.log('\n✅ 验证完成！');
}

main().catch(err => {
  console.error('错误:', err.message);
  console.error(err.stack);
  process.exit(1);
});
