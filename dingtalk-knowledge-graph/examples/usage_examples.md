# 钉钉知识库同步与知识图谱构建 - 使用示例

## 快速开始

### 1. 配置认证

复制 `.env.example` 为 `.env.dingtalk` 并填入你的钉钉应用认证信息：

```bash
cp .env.example .env.dingtalk
```

编辑 `.env.dingtalk`:

```env
DINGTALK_APPKEY=your_appkey
DINGTALK_APPSECRET=your_appsecret
```

### 2. 安装依赖

```bash
pip install requests
```

### 3. 运行同步

```bash
# 首次全量同步
python -m dingtalk_knowledge_graph sync --full

# 日常增量同步
python -m dingtalk_knowledge_graph sync

# 只扫描（不构建图谱）
python -m dingtalk_knowledge_graph scan
```

## Python API 使用

### 基础用法

```python
from dingtalk_knowledge_graph import KnowledgeGraphSync

# 初始化
sync = KnowledgeGraphSync(
    appkey='your_appkey',
    appsecret='your_appsecret',
    storage_path='./dingtalk_data'
)

# 全量扫描
documents = sync.scan(full=True)
print(f"Found {len(documents)} documents")

# 拉取内容
docs_with_content = sync.fetch_content(documents)

# 构建知识图谱
graph = sync.build_graph(docs_with_content)

# 导出图谱
graph.export_json('./output/graph.json')
graph.export_neo4j_cypher('./output/graph.cypher')
graph.export_graphml('./output/graph.graphml')
```

### 增量同步

```python
from dingtalk_knowledge_graph import KnowledgeGraphSync

sync = KnowledgeGraphSync(appkey, appsecret)

# 增量扫描（只获取上次同步后更新的文档）
updated_docs = sync.scan(full=False)
print(f"Found {len(updated_docs)} updated documents")

# 拉取更新的内容
sync.fetch_content(updated_docs)
```

### 查看状态

```python
sync = KnowledgeGraphSync(appkey, appsecret)

# 获取同步状态
status = sync.get_status()

print(f"Last Sync: {status['lastSyncTimeFormatted']}")
print(f"Total Documents: {status['totalDocuments']}")
print(f"Updated: {status['updatedDocuments']}")
```

## 定时任务配置

### 使用 cron (Linux/macOS)

编辑 crontab:

```bash
crontab -e
```

添加以下行（每天凌晨 2 点执行）:

```
0 2 * * * cd /path/to/dingtalk-knowledge-graph && python -m dingtalk_knowledge_graph sync >> sync.log 2>&1
```

### 使用 Windows 任务计划程序

```powershell
# 创建任务
$action = New-ScheduledTaskAction -Execute "python" -Argument "-m dingtalk_knowledge_graph sync" -WorkingDirectory "C:\path\to\dingtalk-knowledge-graph"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "DingTalk Sync" -Action $action -Trigger $trigger
```

## 知识图谱查询

### Neo4j 查询示例

导入图谱到 Neo4j 后：

```cypher
// 查询所有文档
MATCH (d:Document) RETURN d.title, d.createdAt

// 查询某个知识库的所有文档
MATCH (d:Document)-[:BELONGS_TO]->(kb:KnowledgeBase {name: '产品文档库'})
RETURN d.title

// 查询文档的创建者
MATCH (d:Document)-[:CREATED_BY]->(p:Person)
RETURN d.title, p.userId

// 查询文档提及的概念
MATCH (d:Document)-[:MENTIONS]->(c:Concept)
RETURN d.title, c.name
```

### 图谱数据格式

导出的 JSON 格式：

```json
{
  "entities": [
    {
      "id": "doc:abc123",
      "type": "Document",
      "title": "API 文档",
      "knowledgeBaseName": "产品文档库"
    },
    {
      "id": "kb:xyz789",
      "type": "KnowledgeBase",
      "name": "产品文档库"
    }
  ],
  "relations": [
    {
      "source": "doc:abc123",
      "target": "kb:xyz789",
      "type": "BELONGS_TO"
    }
  ]
}
```

## 高级用法

### 自定义实体提取

```python
from dingtalk_knowledge_graph import KnowledgeGraphBuilder

# 自定义要提取的实体类型
graph = KnowledgeGraphBuilder(
    extract_entities=True,
    extract_relations=True,
    entity_types=['Document', 'KnowledgeBase', 'Person', 'CustomType']
)

graph.build(documents)
```

### 批量处理大知识库

```python
from dingtalk_knowledge_graph import DingTalkScanner, ContentFetcher, SyncManager

# 分批次处理
scanner = DingTalkScanner(access_token)
fetcher = ContentFetcher(scanner, './data')

# 扫描
all_docs = scanner.scan_all()

# 分批拉取内容
batch_size = 50
for i in range(0, len(all_docs), batch_size):
    batch = all_docs[i:i+batch_size]
    fetcher.fetch_batch(batch)
    print(f"Processed batch {i//batch_size + 1}")
```

## 故障排查

### Token 过期

```
TokenExpiredError: Token expired
```

解决方法：删除 `.dingtalk_data/sync-state.json` 重新认证

### 权限不足

```
API Error: 50002 - permission denied
```

解决方法：检查钉钉应用权限配置

### 速率限制

```
API Error: 429 - too many requests
```

解决方法：降低 `rate_limit` 配置值

## 输出文件结构

```
dingtalk_data/
├── sync-state.json          # 同步状态
├── documents/               # 文档元数据
│   ├── doc1.json
│   └── doc2.json
├── content/                 # 文档内容 (Markdown)
│   ├── doc1.md
│   └── doc2.md
└── graph/                   # 知识图谱
    ├── graph.json
    ├── graph.cypher
    └── graph.graphml
```

## 相关资源

- [钉钉开放平台文档](https://open.dingtalk.com/)
- [Neo4j 文档](https://neo4j.com/docs/)
- [知识图谱最佳实践](./docs/kg-best-practices.md)
