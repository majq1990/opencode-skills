/**
 * 钉钉知识库内容提取 - 导出向量库格式
 * 输出到 F:\dingding
 */

const fs = require('fs');
const path = require('path');

const DINGTALK_API_BASE = 'https://api.dingtalk.com/v2.0';
const DINGTALK_OAPI_BASE = 'https://oapi.dingtalk.com';
const OUTPUT_DIR = 'F:\\dingding';

class DingTalkExporter {
  constructor(appKey, appSecret, operatorId) {
    this.appKey = appKey;
    this.appSecret = appSecret;
    this.operatorId = operatorId;
    this.accessToken = null;
    this.tokenExpiresAt = 0;
    this.apiCallCount = 0;
    this.allData = {
      exportTime: new Date().toISOString(),
      operatorId: operatorId,
      workspaces: []
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

  async getDocumentContent(nodeId) {
    // 尝试获取文档内容
    const endpoints = [
      `${DINGTALK_API_BASE}/wiki/docs/${nodeId}/content`,
      `${DINGTALK_API_BASE}/wiki/nodes/${nodeId}/content`,
      `${DINGTALK_API_BASE}/wiki/contents/${nodeId}`
    ];

    for (const url of endpoints) {
      try {
        const data = await this.request(url, { method: 'POST', body: '{}' });
        if (data.content) return data.content;
      } catch (e) {
        continue;
      }
    }
    return null;
  }

  // 文本切分
  splitText(text, chunkSize = 500, overlap = 50) {
    if (!text || text.length <= chunkSize) {
      return [text || ''];
    }
    const chunks = [];
    let start = 0;
    while (start < text.length) {
      let end = start + chunkSize;
      if (end < text.length) {
        const sentenceEnd = text.lastIndexOf('\n', end);
        if (sentenceEnd > start) end = sentenceEnd + 1;
      }
      chunks.push(text.slice(start, Math.min(end, text.length)));
      start = end - overlap;
      if (start >= text.length) break;
    }
    return chunks;
  }

  // 生成 RAG chunk
  generateChunk(node, workspace, content, chunkIndex, totalChunks) {
    return {
      id: `${node.nodeId}_chunk_${chunkIndex}`,
      content: content,
      metadata: {
        nodeId: node.nodeId,
        workspaceId: workspace.workspaceId,
        workspaceName: workspace.name,
        fileName: node.name,
        fileExtension: node.extension,
        category: node.category,
        fileUrl: node.url,
        chunkIndex: chunkIndex,
        totalChunks: totalChunks,
        createTime: node.createTime,
        modifiedTime: node.modifiedTime,
        creatorId: node.creatorId
      }
    };
  }

  async export() {
    console.log('🚀 开始导出钉钉知识库内容...\n');
    const startTime = Date.now();

    // 获取所有知识库
    const workspaces = await this.getAllWorkspaces();
    console.log(`📚 发现 ${workspaces.length} 个知识库\n`);

    const allChunks = [];
    const workspaceSummaries = [];

    for (const ws of workspaces) {
      console.log(`\n[${workspaceSummaries.length + 1}/${workspaces.length}] 处理：${ws.name}`);
      
      const nodes = await this.getAllNodes(ws.workspaceId, ws.rootNodeId);
      const files = nodes.filter(n => n.type === 'FILE');
      const folders = nodes.filter(n => n.type === 'FOLDER');

      console.log(`   文档数：${files.length}, 文件夹数：${folders.length}`);

      const fileNodes = [];

      // 处理每个文件
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        console.log(`   [${i + 1}/${files.length}] ${file.name}`);

        // 构建文档元数据
        const docContent = `# ${file.name}\n\n文档路径：${file.url}\n创建时间：${file.createTime}\n更新时间：${file.modifiedTime}\n文件类型：${file.extension || file.category}\n\n${file.description || ''}`;
        
        // 尝试获取实际内容
        const content = await this.getDocumentContent(file.nodeId);
        const fullContent = content ? `${docContent}\n\n${content}` : docContent;

        // 切分文本
        const chunks = this.splitText(fullContent, 500, 50);
        
        for (let j = 0; j < chunks.length; j++) {
          const chunk = this.generateChunk(file, ws, chunks[j], j, chunks.length);
          allChunks.push(chunk);
        }

        fileNodes.push({
          ...file,
          contentAvailable: !!content,
          chunkCount: chunks.length
        });

        // 避免频率限制
        if (i % 10 === 0) await new Promise(r => setTimeout(r, 200));
      }

      workspaceSummaries.push({
        workspace: ws,
        folders: folders.map(f => ({ name: f.name, nodeId: f.nodeId })),
        files: fileNodes.map(f => ({
          name: f.name,
          nodeId: f.nodeId,
          extension: f.extension,
          chunkCount: f.chunkCount
        })),
        totalChunks: fileNodes.reduce((s, f) => s + f.chunkCount, 0)
      });

      console.log(`   ✅ 生成 ${fileNodes.reduce((s, f) => s + f.chunkCount, 0)} 个 chunks`);
      await new Promise(r => setTimeout(r, 500));
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    
    // 汇总数据
    this.allData = {
      exportTime: new Date().toISOString(),
      operatorId: this.operatorId,
      apiCallCount: this.apiCallCount,
      processingTimeSeconds: elapsed,
      summary: {
        totalWorkspaces: workspaceSummaries.length,
        totalFiles: workspaceSummaries.reduce((s, w) => s + w.files.length, 0),
        totalFolders: workspaceSummaries.reduce((s, w) => s + w.folders.length, 0),
        totalChunks: allChunks.length
      },
      workspaces: workspaceSummaries,
      chunks: allChunks
    };

    console.log(`\n⏱️  总耗时：${elapsed} 秒`);
    console.log(`📊 API 调用：${this.apiCallCount} 次`);
    console.log(`📦 总 chunks: ${allChunks.length} 个\n`);

    return this.allData;
  }

  // 保存为 JSON
  saveAsJson(filename = 'dingtalk-knowledge-base.json') {
    const filepath = path.join(OUTPUT_DIR, filename);
    fs.writeFileSync(filepath, JSON.stringify(this.allData, null, 2), 'utf8');
    console.log(`💾 已保存：${filepath} (${(fs.statSync(filepath).size/1024).toFixed(1)} KB)`);
    return filepath;
  }

  // 保存为 JSONL（每行一个 JSON 对象，适合向量库导入）
  saveAsJsonl(filename = 'dingtalk-knowledge-base.jsonl') {
    const filepath = path.join(OUTPUT_DIR, filename);
    const lines = this.allData.chunks.map(c => JSON.stringify(c)).join('\n');
    fs.writeFileSync(filepath, lines, 'utf8');
    console.log(`💾 已保存：${filepath} (${(fs.statSync(filepath).size/1024).toFixed(1)} KB)`);
    return filepath;
  }

  // 保存为 YAML
  saveAsYaml(filename = 'dingtalk-knowledge-base.yaml') {
    const filepath = path.join(OUTPUT_DIR, filename);
    // 简单 YAML 转换
    const yamlContent = this.toJsonYaml(this.allData);
    fs.writeFileSync(filepath, yamlContent, 'utf8');
    console.log(`💾 已保存：${filepath}`);
    return filepath;
  }

  // 简单的 JSON 转 YAML
  toJsonYaml(obj, indent = 0) {
    let yaml = '';
    const spaces = '  '.repeat(indent);
    
    if (Array.isArray(obj)) {
      for (const item of obj) {
        if (typeof item === 'object' && item !== null) {
          yaml += `${spaces}- ${Object.keys(item)[0]}:\n${this.toJsonYaml(item, indent + 1)}`;
        } else {
          yaml += `${spaces}- ${item}\n`;
        }
      }
    } else if (typeof obj === 'object' && obj !== null) {
      for (const [key, value] of Object.entries(obj)) {
        if (Array.isArray(value)) {
          yaml += `${spaces}${key}:\n${this.toJsonYaml(value, indent + 1)}`;
        } else if (typeof value === 'object' && value !== null) {
          yaml += `${spaces}${key}:\n${this.toJsonYaml(value, indent + 1)}`;
        } else {
          yaml += `${spaces}${key}: ${value}\n`;
        }
      }
    }
    return yaml;
  }

  // 保存所有格式
  saveAllFormats() {
    console.log('\n💾 保存文件中...\n');
    this.saveAsJson();
    this.saveAsJsonl();
    // YAML 文件可能较大，可选
    // this.saveAsYaml();
  }
}

async function main() {
  const appKey = process.env.DINGTALK_APPKEY;
  const appSecret = process.env.DINGTALK_APPSECRET;
  const operatorId = process.env.DINGTALK_OPERATOR_ID;

  if (!appKey || !appSecret || !operatorId) {
    console.error('❌ 请设置环境变量：DINGTALK_APPKEY, DINGTALK_APPSECRET, DINGTALK_OPERATOR_ID');
    process.exit(1);
  }

  console.log('═'.repeat(60));
  console.log('     钉钉知识库内容提取 - 向量库格式导出');
  console.log('═'.repeat(60));
  console.log(`\n输出目录：${OUTPUT_DIR}`);
  console.log(`Operator: ${operatorId}\n`);

  const exporter = new DingTalkExporter(appKey, appSecret, operatorId);
  await exporter.export();
  exporter.saveAllFormats();

  console.log('\n' + '═'.repeat(60));
  console.log('✅ 导出完成！');
  console.log('═'.repeat(60));

  // 显示统计
  console.log('\n📊 导出统计:');
  console.log(`  知识库：${exporter.allData.summary.totalWorkspaces} 个`);
  console.log(`  文档：  ${exporter.allData.summary.totalFiles} 个`);
  console.log(`  文件夹：${exporter.allData.summary.totalFolders} 个`);
  console.log(`  Chunks: ${exporter.allData.summary.totalChunks} 个`);
  
  console.log('\n📁 输出文件:');
  console.log(`  - ${OUTPUT_DIR}\\dingtalk-knowledge-base.json`);
  console.log(`  - ${OUTPUT_DIR}\\dingtalk-knowledge-base.jsonl`);
}

main().catch(err => {
  console.error('\n❌ 错误:', err.message);
  console.error(err.stack);
  process.exit(1);
});
