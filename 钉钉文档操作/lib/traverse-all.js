/**
 * 钉钉文档完整遍历 + Token 计算
 */

const DINGTALK_API_BASE = 'https://api.dingtalk.com/v2.0';
const DINGTALK_OAPI_BASE = 'https://oapi.dingtalk.com';

// 估算 token 数（中文约 1.5 字符/token，英文约 4 字符/token）
function estimateTokens(text) {
  if (!text) return 0;
  const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
  const otherChars = text.length - chineseChars;
  // 中文约 1.5 字符/token，英文约 4 字符/token
  return Math.round(chineseChars / 1.5 + otherChars / 4);
}

class DingTalkTokenSync {
  constructor(appKey, appSecret, operatorId) {
    this.appKey = appKey;
    this.appSecret = appSecret;
    this.operatorId = operatorId;
    this.accessToken = null;
    this.tokenExpiresAt = 0;
    this.apiCallCount = 0;
    this.stats = {
      workspaces: 0,
      folders: 0,
      files: 0,
      totalContentLength: 0,
      estimatedInputTokens: 0
    };
  }

  async getAccessToken() {
    if (this.accessToken && Date.now() < this.tokenExpiresAt) {
      return this.accessToken;
    }

    this.apiCallCount++;
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
    await this.getAccessToken();
    this.apiCallCount++;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'x-acs-dingtalk-access-token': this.accessToken,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    return await response.json();
  }

  async getAllWorkspaces() {
    const workspaces = [];
    let nextToken = '';
    
    do {
      const url = `${DINGTALK_API_BASE}/wiki/workspaces?maxResults=100${nextToken ? '&nextToken=' + nextToken : ''}&operatorId=${this.operatorId}`;
      const data = await this.request(url);
      if (data.workspaces) {
        workspaces.push(...data.workspaces);
        this.stats.workspaces = workspaces.length;
      }
      nextToken = data.nextToken || '';
    } while (nextToken);
    
    return workspaces;
  }

  async getNodes(workspaceId, parentNodeId) {
    const url = `${DINGTALK_API_BASE}/wiki/nodes?workspaceId=${workspaceId}&maxResults=100&operatorId=${this.operatorId}&parentNodeId=${parentNodeId}`;
    const data = await this.request(url);
    return data.nodes || [];
  }

  async getAllNodes(workspaceId, rootNodeId) {
    const allNodes = [];
    const queue = [rootNodeId];
    
    while (queue.length > 0) {
      const parentId = queue.shift();
      const nodes = await this.getNodes(workspaceId, parentId);
      
      for (const node of nodes) {
        allNodes.push(node);
        if (node.hasChildren && node.type === 'FOLDER') {
          queue.push(node.nodeId);
        }
      }
    }
    
    return allNodes;
  }

  async getDocumentContent(nodeId) {
    // 尝试多个可能的 API 端点
    const endpoints = [
      { url: `${DINGTALK_API_BASE}/wiki/docs/${nodeId}/content`, method: 'POST', body: '{}' },
      { url: `${DINGTALK_API_BASE}/wiki/nodes/${nodeId}/content`, method: 'GET' },
      { url: `${DINGTALK_API_BASE}/wiki/contents/${nodeId}`, method: 'GET' }
    ];

    for (const endpoint of endpoints) {
      try {
        const data = await this.request(endpoint.url, {
          method: endpoint.method,
          body: endpoint.body
        });
        if (data.content) {
          return data.content;
        }
      } catch (e) {
        continue;
      }
    }
    
    return null;
  }

  async traverseAllWorkspaces() {
    console.log('=== 开始遍历所有知识库 ===\n');
    const startTime = Date.now();
    
    const workspaces = await this.getAllWorkspaces();
    console.log(`发现 ${workspaces.length} 个知识库\n`);

    const results = [];

    for (const ws of workspaces) {
      console.log(`\n📚 [${results.length + 1}/${workspaces.length}] 知识库：${ws.name}`);
      console.log(`   描述：${ws.description || '(无描述)'}`);
      console.log(`   创建时间：${ws.createTime}`);
      console.log(`   URL: ${ws.url}`);

      const nodes = await this.getAllNodes(ws.workspaceId, ws.rootNodeId);
      const folders = nodes.filter(n => n.type === 'FOLDER');
      const files = nodes.filter(n => n.type === 'FILE');

      console.log(`   📁 文件夹：${folders.length} 个`);
      console.log(`   📄 文档：${files.length} 个`);

      this.stats.folders += folders.length;
      this.stats.files += files.length;

      // 获取文档内容
      console.log(`   📖 获取文档内容...`);
      const docsWithContent = [];
      
      for (const file of files.slice(0, 20)) { // 限制获取前 20 个文档内容
        const content = await this.getDocumentContent(file.nodeId);
        if (content) {
          const tokens = estimateTokens(content);
          this.stats.totalContentLength += content.length;
          this.stats.estimatedInputTokens += tokens;
          
          docsWithContent.push({
            ...file,
            content: content.substring(0, 200) + (content.length > 200 ? '...' : ''),
            contentLength: content.length,
            estimatedTokens: tokens
          });
          console.log(`      ✓ ${file.name} (${content.length} 字符，约${tokens} tokens)`);
        }
      }

      if (files.length > 20) {
        console.log(`      ... 还有 ${files.length - 20} 个文档（跳过内容获取）`);
      }

      results.push({
        workspace: ws,
        folders,
        files,
        docsWithContent
      });

      // 避免频率限制
      await new Promise(resolve => setTimeout(resolve, 200));
    }

    const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(1);
    
    console.log('\n=== 遍历完成 ===\n');
    console.log(`总耗时：${elapsedTime} 秒`);
    console.log(`API 调用次数：${this.apiCallCount} 次`);
    
    return results;
  }
}

// 计算 token 成本
function calculateCost(tokens) {
  // 参考价格（每 1000 tokens）
  const prices = {
    embedding: 0.0001,  // $0.0001/1K tokens
    gpt4: 0.03,         // $0.03/1K tokens (input)
    gpt4_output: 0.06,  // $0.06/1K tokens (output)
    claude: 0.003       // $0.003/1K tokens (input)
  };

  return {
    embedding: (tokens * prices.embedding / 1000).toFixed(4),
    gpt4_input: (tokens * prices.gpt4 / 1000).toFixed(4),
    claude_input: (tokens * prices.claude / 1000).toFixed(4)
  };
}

async function main() {
  const appKey = process.env.DINGTALK_APPKEY;
  const appSecret = process.env.DINGTALK_APPSECRET;
  const operatorId = process.env.DINGTALK_OPERATOR_ID;

  if (!appKey || !appSecret || !operatorId) {
    console.error('请设置环境变量：DINGTALK_APPKEY, DINGTALK_APPSECRET, DINGTALK_OPERATOR_ID');
    process.exit(1);
  }

  const sync = new DingTalkTokenSync(appKey, appSecret, operatorId);
  const results = await sync.traverseAllWorkspaces();

  // 统计信息
  console.log('\n╔═══════════════════════════════════════════════╗');
  console.log('║           知识库遍历统计报告                  ║');
  console.log('╚═══════════════════════════════════════════════╝\n');

  console.log('📊 基础统计');
  console.log('─'.repeat(50));
  console.log(`  知识库总数：    ${sync.stats.workspaces} 个`);
  console.log(`  文件夹总数：    ${sync.stats.folders} 个`);
  console.log(`  文档总数：      ${sync.stats.files} 个`);
  console.log(`  API 调用次数：    ${sync.apiCallCount} 次`);
  
  console.log('\n📈 Token 估算');
  console.log('─'.repeat(50));
  
  // 估算所有文档的 token（假设平均每个文档 2000 字符）
  const avgCharsPerDoc = 2000;
  const totalEstimatedChars = sync.stats.files * avgCharsPerDoc;
  const totalEstimatedTokens = Math.round(totalEstimatedChars / 2); // 平均 2 字符/token
  
  console.log(`  已获取内容字符：${sync.stats.totalContentLength.toLocaleString()} 字符`);
  console.log(`  已估算 Tokens:  ${sync.stats.estimatedInputTokens.toLocaleString()} tokens`);
  console.log(`  预计总字符数：  ${totalEstimatedChars.toLocaleString()} 字符（按平均${avgCharsPerDoc}字符/文档）`);
  console.log(`  预计总 Tokens:  ${totalEstimatedTokens.toLocaleString()} tokens`);

  console.log('\n💰 成本估算（按每 1000 tokens 计）');
  console.log('─'.repeat(50));
  const costs = calculateCost(totalEstimatedTokens);
  console.log(`  向量 Embedding:  $${costs.embedding} 美元`);
  console.log(`  GPT-4 输入：     $${costs.gpt4_input} 美元`);
  console.log(`  Claude 输入：    $${costs.claude_input} 美元`);

  console.log('\n📋 知识库详情');
  console.log('─'.repeat(50));
  for (const result of results) {
    console.log(`  ${result.workspace.name}`);
    console.log(`    文档数：${result.files.length}, 文件夹数：${result.folders.length}`);
  }

  console.log('\n✅ 完成！');
}

main().catch(err => {
  console.error('错误:', err.message);
  console.error(err.stack);
  process.exit(1);
});
