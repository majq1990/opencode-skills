---
name: maxkb-knowledge-graph
description: Build knowledge graphs in MaxKB from DingTalk knowledge bases, with structured data storage and vector embedding for unstructured content
license: MIT
compatibility: opencode
metadata:
  category: integration
  platform: maxkb,dingtalk
  features: knowledge-graph, vector-database, rag, dingtalk-sync, tag-management
---

## 功能概述

此 skill 用于将钉钉知识库同步到 MaxKB 知识图谱系统，实现以下功能：

1. **钉钉知识库扫描**: 获取组织内所有知识库及文档
2. **智能数据分类**: 自动识别结构化/非结构化数据
3. **知识图谱构建**: 将结构化数据存入 MaxKB 知识图谱
4. **向量化存储**: 将非结构化数据通过 MaxKB API 写入向量库
5. **标签管理**: 添加"支持部测试"标签，支持按标签删除
6. **增量同步**: 根据更新时间检测变更，只同步更新内容

## 系统架构

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  DingTalk KB    │────▶│  Data Classifier │────▶│   MaxKB         │
│  (钉钉知识库)    │     │  (数据分类器)     │     │   Knowledge     │
│                 │     │                  │     │   Graph         │
└─────────────────┘     └──────────────────┘     │   (知识图谱)    │
                              │                  └─────────────────┘
                              │                          ▲
                              ▼                          │
                       ┌──────────────────┐             │
                       │  Vector Embedding│─────────────┘
                       │  (向量化)         │
                       │                  │
                       │  MaxKB Vector DB │
                       │  (向量数据库)    │
                       └──────────────────┘
```

## 快速开始

### 1. 配置环境变量

创建 `.env.maxkb` 文件：

```env
# MaxKB 配置
MAXKB_BASE_URL=http://111.4.141.154:18080
MAXKB_USERNAME=egova-jszc
MAXKB_PASSWORD=eGova@2026

# 钉钉认证配置
DINGTALK_APPKEY=your_appkey
DINGTALK_APPSECRET=your_appsecret

# 知识库配置
KNOWLEDGE_BASE_NAME=支持部测试
TAG_NAME=支持部测试
```

### 2. 运行同步

```bash
# 完整同步（扫描 + 分类 + 构建图谱 + 向量化）
python -m maxkb_knowledge_graph sync

# 只扫描钉钉知识库
python -m maxkb_knowledge_graph scan

# 只构建知识图谱
python -m maxkb_knowledge_graph build-graph

# 查看状态
python -m maxkb_knowledge_graph status

# 删除带标签的数据
python -m maxkb_knowledge_graph delete --tag "支持部测试"
```

## MaxKB API 参考

### 认证

MaxKB 使用 JWT Token 进行认证：

```python
import requests

# 获取 Token
def get_maxkb_token(base_url, username, password):
    response = requests.post(
        f"{base_url}/api/login",
        json={"username": username, "password": password}
    )
    token = response.json().get('access_token')
    return token
```

### 创建知识库

```python
def create_dataset(base_url, token, name, description=""):
    response = requests.post(
        f"{base_url}/api/v1/dataset",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
            "description": description,
            "type": "GENERAL"  # GENERAL 或 AUTO
        }
    )
    return response.json()
```

### 上传文档

```python
def upload_document(base_url, token, dataset_id, file_path, name):
    with open(file_path, 'rb') as f:
        files = {'file': (name, f, 'application/pdf')}
        data = {
            'name': name,
            'dataset_id': dataset_id
        }
        response = requests.post(
            f"{base_url}/api/v1/dataset/{dataset_id}/document",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )
    return response.json()
```

### 上传文本片段

```python
def upload_text(base_url, token, dataset_id, title, content, tags=None):
    response = requests.post(
        f"{base_url}/api/v1/dataset/{dataset_id}/document/paragraph",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "content": content,
            "tags": tags or []
        }
    )
    return response.json()
```

### 查询知识库

```python
def search_knowledge(base_url, token, dataset_id, query, top_k=3):
    response = requests.post(
        f"{base_url}/api/v1/knowledge/search",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_ids": [dataset_id],
            "query": query,
            "top_k": top_k
        }
    )
    return response.json()
```

### 删除文档

```python
def delete_document(base_url, token, document_id):
    response = requests.delete(
        f"{base_url}/api/v1/dataset/document/{document_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.status_code == 200
```

### 按标签删除

```python
def delete_by_tag(base_url, token, tag_name):
    # 先查询带标签的文档
    response = requests.get(
        f"{base_url}/api/v1/dataset/document?tag={tag_name}",
        headers={"Authorization": f"Bearer {token}"}
    )
    documents = response.json()
    
    # 批量删除
    for doc in documents:
        delete_document(base_url, token, doc['id'])
```

## 钉钉知识库集成

### 扫描钉钉知识库

```python
from maxkb_knowledge_graph import DingTalkScanner, MaxKBClient

# 初始化扫描器
scanner = DingTalkScanner(
    appkey='your_appkey',
    appsecret='your_appsecret'
)

# 获取所有文档
documents = scanner.scan_all()
```

### 数据分类

```python
from maxkb_knowledge_graph import DataClassifier

classifier = DataClassifier()

# 分类文档
for doc in documents:
    category = classifier.classify(doc)
    # 返回：'STRUCTURED' 或 'UNSTRUCTURED'
```

### 构建知识图谱

```python
from maxkb_knowledge_graph import KnowledgeGraphBuilder

# 构建图谱
graph = KnowledgeGraphBuilder()
graph.build(structured_documents)

# 导出为 JSON
graph.export_json('graph.json')
```

### 向量化上传

```python
from maxkb_knowledge_graph import MaxKBClient

# 初始化 MaxKB 客户端
client = MaxKBClient(
    base_url='http://111.4.141.154:18080',
    username='egova-jszc',
    password='eGova@2026'
)

# 创建知识库
dataset = client.create_dataset(
    name='支持部测试',
    description='支持部测试知识库'
)

# 上传非结构化数据
for doc in unstructured_docs:
    client.upload_text(
        dataset_id=dataset['id'],
        title=doc['title'],
        content=doc['content'],
        tags=['支持部测试']
    )
```

## 完整示例

### 示例 1: 完整同步流程

```python
from maxkb_knowledge_graph import KnowledgeGraphSync

# 初始化
sync = KnowledgeGraphSync(
    # MaxKB 配置
    maxkb_base_url='http://111.4.141.154:18080',
    maxkb_username='egova-jszc',
    maxkb_password='eGova@2026',
    
    # 钉钉配置
    dingtalk_appkey='your_appkey',
    dingtalk_appsecret='your_appsecret',
    
    # 知识库配置
    dataset_name='支持部测试',
    tag_name='支持部测试'
)

# 执行同步
sync.sync()

# 查看统计
stats = sync.get_statistics()
print(f"同步完成!")
print(f"  知识库：{stats['dataset_name']}")
print(f"  文档数：{stats['total_documents']}")
print(f"  结构化：{stats['structured_count']}")
print(f"  非结构化：{stats['unstructured_count']}")
```

### 示例 2: 增量同步

```python
sync = KnowledgeGraphSync(...)

# 增量同步（只同步更新的文档）
updated_docs = sync.scan(incremental=True)
print(f"发现 {len(updated_docs)} 个更新的文档")

sync.build_graph(updated_docs)
sync.upload_vectors(updated_docs)
```

### 示例 3: 删除标签数据

```python
sync = KnowledgeGraphSync(...)

# 删除所有带"支持部测试"标签的数据
deleted_count = sync.delete_by_tag("支持部测试")
print(f"删除了 {deleted_count} 个文档")
```

### 示例 4: 搜索知识

```python
sync = KnowledgeGraphSync(...)

# 搜索知识
results = sync.search("如何请假？", top_k=5)

for result in results:
    print(f"文档：{result['title']}")
    print(f"相似度：{result['similarity']}")
    print(f"内容：{result['content'][:200]}...")
```

## 数据结构

### 结构化数据示例

```json
{
  "type": "STRUCTURED",
  "metadata": {
    "nodeId": "doc123",
    "title": "员工手册",
    "knowledgeBaseName": "人力资源部",
    "creatorId": "user456",
    "createdAt": 1710662400000,
    "updatedAt": 1710662400000
  },
  "entities": [
    {
      "id": "policy:leave_policy",
      "type": "Policy",
      "properties": {
        "name": "请假政策",
        "department": "人力资源部"
      }
    }
  ],
  "relations": [
    {
      "source": "doc:doc123",
      "target": "policy:leave_policy",
      "type": "CONTAINS"
    }
  ]
}
```

### 非结构化数据示例

```json
{
  "type": "UNSTRUCTURED",
  "metadata": {
    "nodeId": "doc124",
    "title": "会议纪要",
    "knowledgeBaseName": "支持部"
  },
  "content": "# 会议纪要\n\n## 时间\n2024-03-17\n\n## 内容\n讨论了新的项目计划...",
  "tags": ["支持部测试", "会议纪要", "2024-03"]
}
```

## 配置选项

### 完整配置示例 (config.yaml)

```yaml
# MaxKB 配置
maxkb:
  base_url: http://111.4.141.154:18080
  username: egova-jszc
  password: ${MAXKB_PASSWORD}
  timeout: 30

# 钉钉配置
dingtalk:
  appkey: ${DINGTALK_APPKEY}
  appsecret: ${DINGTALK_APPSECRET}
  api_base_url: https://api.dingtalk.com

# 知识库配置
dataset:
  name: 支持部测试
  description: 支持部测试知识库
  type: GENERAL

# 标签配置
tags:
  primary: 支持部测试
  auto_generate: true
  categories:
    - 部门
    - 项目
    - 文档类型

# 同步配置
sync:
  batch_size: 50
  max_retries: 3
  rate_limit: 90
  incremental_interval: 86400

# 向量化配置
embedding:
  model: text-embedding-v2
  chunk_size: 500
  chunk_overlap: 50

# 日志配置
logging:
  level: INFO
  file: ./logs/maxkb_sync.log
```

## 命令行参考

### sync - 完整同步

```bash
python -m maxkb_knowledge_graph sync [OPTIONS]

选项:
  --full              全量同步 (默认增量)
  --no-graph          不构建知识图谱
  --no-vector         不上传向量库
  --output, -o        输出目录
  --verbose, -v       详细输出
```

### scan - 扫描知识库

```bash
python -m maxkb_knowledge_graph scan [OPTIONS]

选项:
  --full              全量扫描
  --output, -o        输出目录
  --dry-run           只检测不下载
```

### build-graph - 构建图谱

```bash
python -m maxkb_knowledge_graph build-graph [OPTIONS]

选项:
  --input, -i         输入目录
  --output, -o        输出文件
  --format, -f        输出格式 (json/graphml)
```

### delete - 删除数据

```bash
python -m maxkb_knowledge_graph delete [OPTIONS]

选项:
  --tag, -t           标签名称 (必填)
  --dataset           知识库 ID
  --confirm           确认删除 (跳过确认)
```

### status - 查看状态

```bash
python -m maxkb_knowledge_graph status

显示:
  - MaxKB 连接状态
  - 知识库信息
  - 文档统计
  - 标签分布
```

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| Authentication failed | MaxKB 认证失败 | 检查用户名/密码 |
| Dataset not found | 知识库不存在 | 先创建知识库 |
| Token expired | 钉钉 Token 过期 | 重新获取 Token |
| Rate limit exceeded | 请求频率超限 | 降低 rate_limit |

### 错误处理示例

```python
from maxkb_knowledge_graph import MaxKBError

try:
    sync.sync()
except MaxKBError as e:
    if e.code == 'AUTH_FAILED':
        print("MaxKB 认证失败，请检查账号密码")
    elif e.code == 'DATASET_NOT_FOUND':
        print("知识库不存在，请先创建")
    else:
        print(f"错误：{e.message}")
```

## 最佳实践

### 1. 首次同步

```bash
# 全量同步
python -m maxkb_knowledge_graph sync --full
```

### 2. 日常增量同步

配置定时任务，每天执行：

```bash
0 2 * * * cd /path && python -m maxkb_knowledge_graph sync >> sync.log 2>&1
```

### 3. 定期清理

每月清理一次旧数据：

```bash
python -m maxkb_knowledge_graph delete --tag "支持部测试" --confirm
```

## 安全注意事项

1. **保护认证信息**: 不要将密码提交到代码仓库
2. **使用环境变量**: 通过 .env 文件管理敏感信息
3. **权限控制**: MaxKB 账号使用最小权限原则
4. **数据备份**: 定期备份 MaxKB 数据

## 故障排查

### 问题 1: MaxKB 连接失败

**症状**: `Connection refused` 或 `Timeout`

**解决方案**:
1. 检查 MaxKB 服务是否运行
2. 确认防火墙允许访问 18080 端口
3. 检查 base_url 配置是否正确

### 问题 2: 钉钉 API 权限不足

**症状**: `API Error: 50002 - permission denied`

**解决方案**:
1. 在钉钉后台检查应用权限
2. 确认应用已发布或添加可见范围
3. 等待权限生效 (可能需要几分钟)

## 相关资源

- [MaxKB 官方文档](https://docs.maxkb.pro/)
- [钉钉开放平台](https://open.dingtalk.com/)
- [RAG 最佳实践](https://docs.langchain.com/rag)
- [向量数据库指南](https://www.pinecone.io/learn/vector-database/)

## 版本历史

- **v0.1.0** (2026-03-17): 初始版本，支持 MaxKB 集成和钉钉同步
- **v0.2.0** (计划): 添加工作流编排支持
- **v0.3.0** (计划): 添加 MCP 工具集成

## 许可证

MIT License - 详见 LICENSE 文件
