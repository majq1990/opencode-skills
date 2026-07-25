/**
 * 钉钉文档完整遍历 - 详细报告
 */

const DINGTALK_API_BASE = 'https://api.dingtalk.com/v2.0';
const DINGTALK_OAPI_BASE = 'https://oapi.dingtalk.com';

class DingTalkFullTraversal {
  constructor(appKey, appSecret, operatorId) {
    this.appKey = appKey;
    this.appSecret = appSecret;
    this.operatorId = operatorId;
    this.accessToken = null;
    this.apiCallCount = 0;
  }

  async getAccessToken() {
    if (this.accessToken && Date.now() < this.tokenExpiresAt) {
      return this.accessToken;
    }
    this.apiCallCount++;
    const url = `${DINGTALK_OAPI_BASE}/gettoken?appkey=${this.appKey}&appsecret=${this.appSecret}`;
    const response = await fetch(url);
    const data = await response.json();
    if (data.errcode !== 0) throw new Error(`获取 token 失败：${data.errmsg}`);
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
      if (data.workspaces) workspaces.push(...data.workspaces);
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

  async traverse() {
    const workspaces = await this.getAllWorkspaces();
    console.log(`\n发现 ${workspaces.length} 个知识库\n`);

    const report = [];
    
    for (const ws of workspaces) {
      console.log(`\n📚 ${ws.name} (${ws.workspaceId})`);
      console.log(`   ${ws.description || '(无描述)'}`);
      console.log(`   ${ws.url}\n`);

      const nodes = await this.getAllNodes(ws.workspaceId, ws.rootNodeId);
      const folders = nodes.filter(n => n.type === 'FOLDER');
      const files = nodes.filter(n => n.type === 'FILE');

      console.log(`   📁 文件夹 (${folders.length}个):`);
      for (const f of folders) {
        console.log(`      - ${f.name} [${f.nodeId}]`);
      }

      console.log(`\n   📄 文档 (${files.length}个):`);
      const fileTypes = {};
      for (const file of files) {
        const ext = file.extension || 'unknown';
        fileTypes[ext] = (fileTypes[ext] || 0) + 1;
        console.log(`      - ${file.name} (${file.category}) [${file.nodeId.substring(0, 16)}...]`);
      }

      console.log(`\n   📊 文件类型统计:`);
      for (const [ext, count] of Object.entries(fileTypes)) {
        console.log(`      ${ext}: ${count} 个`);
      }

      report.push({ workspace: ws, folders, files });
      await new Promise(r => setTimeout(r, 300));
    }

    return report;
  }
}

function estimateTokens(chars) {
  // 中文约 1.5 字符/token，英文约 4 字符/token，平均 2 字符/token
  return Math.round(chars / 2);
}

async function main() {
  const appKey = process.env.DINGTALK_APPKEY;
  const appSecret = process.env.DINGTALK_APPSECRET;
  const operatorId = process.env.DINGTALK_OPERATOR_ID;

  if (!appKey || !appSecret || !operatorId) {
    console.error('请设置环境变量');
    process.exit(1);
  }

  const sync = new DingTalkFullTraversal(appKey, appSecret, operatorId);
  const startTime = Date.now();
  const report = await sync.traverse();
  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

  // 汇总统计
  const totalFolders = report.reduce((s, r) => s + r.folders.length, 0);
  const totalFiles = report.reduce((s, r) => s + r.files.length, 0);

  console.log('\n' + '═'.repeat(60));
  console.log('           钉钉知识库完整遍历报告');
  console.log('═'.repeat(60));

  console.log(`\n【认证信息】`);
  console.log(`  Operator ID: ${operatorId}`);
  console.log(`  遍历时间：${new Date().toLocaleString('zh-CN')}`);
  console.log(`  总耗时：${elapsed} 秒`);
  console.log(`  API 调用：${sync.apiCallCount} 次`);

  console.log(`\n【知识库概览】`);
  console.log(`  知识库数量：${report.length} 个`);
  console.log(`  文件夹数量：${totalFolders} 个`);
  console.log(`  文档数量：  ${totalFiles} 个`);

  console.log(`\n【Token 估算】（按平均每文档 2000 字符估算）`);
  const avgCharsPerDoc = 2000;
  const totalChars = totalFiles * avgCharsPerDoc;
  const totalTokens = estimateTokens(totalChars);

  console.log(`  预计总字符：${totalChars.toLocaleString()} 字符`);
  console.log(`  预计 Tokens: ${totalTokens.toLocaleString()} tokens`);

  console.log(`\n【向量库构建成本】`);
  const embeddingCost = (totalTokens * 0.0001 / 1000).toFixed(4);
  const gpt4Cost = (totalTokens * 0.03 / 1000).toFixed(4);
  const claudeCost = (totalTokens * 0.003 / 1000).toFixed(4);
  
  console.log(`  Embedding:   $${embeddingCost} USD (约¥${(embeddingCost*7.2).toFixed(2)})`);
  console.log(`  GPT-4 Input: $${gpt4Cost} USD (约¥${(gpt4Cost*7.2).toFixed(2)})`);
  console.log(`  Claude Input: $${claudeCost} USD (约¥${(claudeCost*7.2).toFixed(2)})`);

  console.log(`\n【各知识库详情】`);
  for (const r of report) {
    console.log(`\n  ${r.workspace.name}`);
    console.log(`    创建时间：${r.workspace.createTime}`);
    console.log(`    文档数：${r.files.length} | 文件夹数：${r.folders.length}`);
    console.log(`    预计 Tokens: ${estimateTokens(r.files.length * avgCharsPerDoc).toLocaleString()}`);
  }

  console.log('\n' + '═'.repeat(60));
  console.log('✅ 遍历完成！');
}

main().catch(err => {
  console.error('错误:', err.message);
  process.exit(1);
});
