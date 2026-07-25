# 钉钉知识库 Skill

这个skill帮助你遍历钉钉组织内的所有知识库文件。

## 配置要求

在使用此skill之前，需要配置以下环境变量或创建配置文件：

### 方式1: 环境变量
```bash
export DINGTALK_APP_KEY="your_app_key"
export DINGTALK_APP_SECRET="your_app_secret"
```

### 方式2: 配置文件
在项目根目录创建 `.dingtalk.json`:
```json
{
  "appKey": "your_app_key",
  "appSecret": "your_app_secret"
}
```

### 获取应用凭证
1. 登录钉钉开放平台: https://open.dingtalk.com
2. 创建企业内部应用
3. 在应用详情页获取 AppKey 和 AppSecret
4. 确保应用已开通"知识库"相关权限

## API说明

### 1. 获取Access Token
```
POST https://api.dingtalk.com/v1.0/oauth2/accessToken
Content-Type: application/json

{
  "appKey": "your_app_key",
  "appSecret": "your_app_secret"
}
```

**响应:**
```json
{
  "accessToken": "abc123",
  "expireIn": 7200
}
```

### 2. 获取知识库列表
```
GET https://api.dingtalk.com/v1.0/wiki/docuspaces
Authorization: Bearer {accessToken}
```

**响应:**
```json
{
  "docuspaces": [
    {
      "docuspaceId": "知识库ID",
      "name": "知识库名称",
      "desc": "描述",
      "createTime": 1234567890,
      "updateTime": 1234567890
    }
  ]
}
```

### 3. 获取知识库节点列表（文档树）
```
GET https://api.dingtalk.com/v1.0/wiki/docuspaces/{docuspaceId}/nodes
Authorization: Bearer {accessToken}
```

**参数:**
- `docuspaceId`: 知识库ID
- `parentNodeKey`: 父节点key（可选，不传则返回根节点）

**响应:**
```json
{
  "nodes": [
    {
      "nodeKey": "节点key",
      "parentNodeKey": "父节点key",
      "name": "节点名称",
      "type": "folder/document",
      "createTime": 1234567890,
      "updateTime": 1234567890
    }
  ]
}
```

### 4. 获取文档详情
```
GET https://api.dingtalk.com/v1.0/wiki/docuspaces/{docuspaceId}/nodes/{nodeKey}
Authorization: Bearer {accessToken}
```

**响应:**
```json
{
  "nodeKey": "节点key",
  "name": "文档名称",
  "content": "文档内容",
  "createTime": 1234567890,
  "updateTime": 1234567890,
  "creator": "创建者userId",
  "modifier": "修改者userId"
}
```

### 5. 递归获取所有文件（分页）
```
GET https://api.dingtalk.com/v1.0/wiki/docuspaces/{docuspaceId}/nodes
Authorization: Bearer {accessToken}
Query Parameters:
  - parentNodeKey: 父节点key
  - pageSize: 每页大小（默认20，最大100）
  - nextToken: 分页token
```

## 工作流程

当用户请求遍历知识库时，按照以下步骤执行：

### Step 1: 获取Access Token
使用配置的 appKey 和 appSecret 调用认证接口获取 access_token。

### Step 2: 获取知识库列表
调用 `/v1.0/wiki/docuspaces` 获取组织内所有知识库。

### Step 3: 遍历每个知识库
对每个知识库：
1. 调用节点列表API获取根节点
2. 递归遍历文件夹结构
3. 收集所有文档节点

### Step 4: 输出结果
将所有文件整理成树形结构或列表格式展示给用户。

## 权限要求

应用需要申请以下权限：
- `Wiki.Read`: 读取知识库列表
- `Wiki.Node.Read`: 读取知识库节点
- `Contact.User.Read`: 读取用户信息（如需显示创建者信息）

## 错误处理

### 常见错误码
- `40014`: 不合法的access_token
- `42001`: access_token已过期
- `60011**: 没有权限访问该知识库
- `60012**: 知识库不存在

### 重试策略
- access_token过期时自动重新获取
- 网络错误时最多重试3次
- 权限错误时提示用户检查应用配置

## 示例用法

用户可以这样请求：
- "遍历钉钉知识库的所有文件"
- "列出钉钉知识库中的文档"
- "获取知识库'产品文档'下的所有文件"

## 代码实现参考

### Python示例
```python
import requests
import json
import os

class DingTalkWikiClient:
    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = None
        self.base_url = "https://api.dingtalk.com/v1.0"
    
    def get_access_token(self):
        url = f"{self.base_url}/oauth2/accessToken"
        resp = requests.post(url, json={
            "appKey": self.app_key,
            "appSecret": self.app_secret
        })
        data = resp.json()
        self.access_token = data["accessToken"]
        return self.access_token
    
    def _request(self, method, path, **kwargs):
        if not self.access_token:
            self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        url = f"{self.base_url}{path}"
        resp = requests.request(method, url, headers=headers, **kwargs)
        
        if resp.status_code == 401:
            # Token expired, retry
            self.get_access_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
            resp = requests.request(method, url, headers=headers, **kwargs)
        
        return resp.json()
    
    def list_docuspaces(self):
        return self._request("GET", "/wiki/docuspaces")
    
    def list_nodes(self, docuspace_id, parent_node_key=None, page_size=100, next_token=None):
        params = {"pageSize": page_size}
        if parent_node_key:
            params["parentNodeKey"] = parent_node_key
        if next_token:
            params["nextToken"] = next_token
        return self._request("GET", f"/wiki/docuspaces/{docuspace_id}/nodes", params=params)
    
    def get_node_detail(self, docuspace_id, node_key):
        return self._request("GET", f"/wiki/docuspaces/{docuspace_id}/nodes/{node_key}")
    
    def traverse_all_files(self, docuspace_id, parent_node_key=None, depth=0):
        """递归遍历获取所有文件"""
        all_files = []
        next_token = None
        
        while True:
            data = self.list_nodes(docuspace_id, parent_node_key, next_token=next_token)
            nodes = data.get("nodes", [])
            
            for node in nodes:
                file_info = {
                    "name": node["name"],
                    "type": node["type"],
                    "nodeKey": node["nodeKey"],
                    "depth": depth
                }
                
                if node["type"] == "folder":
                    # 递归遍历文件夹
                    sub_files = self.traverse_all_files(
                        docuspace_id, 
                        node["nodeKey"], 
                        depth + 1
                    )
                    file_info["children"] = sub_files
                    all_files.append(file_info)
                else:
                    all_files.append(file_info)
            
            next_token = data.get("nextToken")
            if not next_token:
                break
        
        return all_files

# 使用示例
def main():
    # 从环境变量读取配置
    app_key = os.getenv("DINGTALK_APP_KEY")
    app_secret = os.getenv("DINGTALK_APP_SECRET")
    
    client = DingTalkWikiClient(app_key, app_secret)
    
    # 获取所有知识库
    spaces = client.list_docuspaces()
    
    for space in spaces.get("docuspaces", []):
        print(f"\n知识库: {space['name']}")
        print(f"ID: {space['docuspaceId']}")
        
        # 遍历所有文件
        files = client.traverse_all_files(space["docuspaceId"])
        for f in files:
            indent = "  " * f.get("depth", 0)
            print(f"{indent}{'📁' if f['type'] == 'folder' else '📄'} {f['name']}")

if __name__ == "__main__":
    main()
```

### Node.js示例
```javascript
const axios = require('axios');

class DingTalkWikiClient {
  constructor(appKey, appSecret) {
    this.appKey = appKey;
    this.appSecret = appSecret;
    this.accessToken = null;
    this.baseUrl = 'https://api.dingtalk.com/v1.0';
  }

  async getAccessToken() {
    const resp = await axios.post(`${this.baseUrl}/oauth2/accessToken`, {
      appKey: this.appKey,
      appSecret: this.appSecret
    });
    this.accessToken = resp.data.accessToken;
    return this.accessToken;
  }

  async request(method, path, options = {}) {
    if (!this.accessToken) {
      await this.getAccessToken();
    }

    try {
      const resp = await axios({
        method,
        url: `${this.baseUrl}${path}`,
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        },
        ...options
      });
      return resp.data;
    } catch (error) {
      if (error.response?.status === 401) {
        await this.getAccessToken();
        const resp = await axios({
          method,
          url: `${this.baseUrl}${path}`,
          headers: {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
          },
          ...options
        });
        return resp.data;
      }
      throw error;
    }
  }

  async listDocuspaces() {
    return this.request('GET', '/wiki/docuspaces');
  }

  async listNodes(docuspaceId, parentNodeKey = null, pageSize = 100, nextToken = null) {
    const params = { pageSize };
    if (parentNodeKey) params.parentNodeKey = parentNodeKey;
    if (nextToken) params.nextToken = nextToken;
    return this.request('GET', `/wiki/docuspaces/${docuspaceId}/nodes`, { params });
  }

  async traverseAllFiles(docuspaceId, parentNodeKey = null, depth = 0) {
    const allFiles = [];
    let nextToken = null;

    do {
      const data = await this.listNodes(docuspaceId, parentNodeKey, 100, nextToken);
      const nodes = data.nodes || [];

      for (const node of nodes) {
        const fileInfo = {
          name: node.name,
          type: node.type,
          nodeKey: node.nodeKey,
          depth
        };

        if (node.type === 'folder') {
          fileInfo.children = await this.traverseAllFiles(
            docuspaceId,
            node.nodeKey,
            depth + 1
          );
        }
        allFiles.push(fileInfo);
      }

      nextToken = data.nextToken;
    } while (nextToken);

    return allFiles;
  }
}

// 使用示例
async function main() {
  const client = new DingTalkWikiClient(
    process.env.DINGTALK_APP_KEY,
    process.env.DINGTALK_APP_SECRET
  );

  const spaces = await client.listDocuspaces();

  for (const space of spaces.docuspaces || []) {
    console.log(`\n知识库: ${space.name}`);
    console.log(`ID: ${space.docuspaceId}`);

    const files = await client.traverseAllFiles(space.docuspaceId);
    printFiles(files);
  }
}

function printFiles(files, indent = '') {
  for (const file of files) {
    const icon = file.type === 'folder' ? '📁' : '📄';
    console.log(`${indent}${icon} ${file.name}`);
    if (file.children) {
      printFiles(file.children, indent + '  ');
    }
  }
}

main().catch(console.error);
```

## 注意事项

1. **访问频率限制**: 钉钉API有调用频率限制，建议实现请求限流
2. **大知识库**: 对于文件较多的知识库，遍历可能需要较长时间
3. **权限检查**: 确保应用有权限访问目标知识库
4. **Token缓存**: access_token 有效期2小时，建议缓存避免频繁获取
5. **敏感信息**: 不要将 appKey 和 appSecret 提交到代码仓库

## 参考文档

- 钉钉开放平台: https://open.dingtalk.com
- 知识库API文档: https://open.dingtalk.com/document/orgapp/knowledge-base-api-overview
- 权限管理: https://open.dingtalk.com/document/orgapp/permission-management