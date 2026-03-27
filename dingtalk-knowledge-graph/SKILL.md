---
name: dingtalk-knowledge-graph
description: Periodically scan DingTalk knowledge bases, track document updates, fetch updated content, and build knowledge graphs from documents
license: MIT
compatibility: opencode
metadata:
  category: integration
  platform: dingtalk
  features: knowledge-base-scanning, incremental-sync, knowledge-graph, rag-ready, change-tracking
---

## 功能概述

此 skill 用于定期扫描钉钉知识库，实现以下功能：

1. **全量/增量扫描**: 获取组织内所有知识库及文档列表
2. **变更检测**: 根据更新时间检测文档更新或新增
3. **自动拉取**: 获取更新文档的完整内容
4. **知识图谱构建**: 从文档中提取实体和关系，构建知识图谱
5. **RAG 数据准备**: 将文档切分为适合向量数据库的块 (chunks)
6. **定时任务**: 支持 cron 表达式配置定期扫描
7. **多格式导出**: 支持 Neo4j、JSON-LD、GraphML 等图谱格式

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    DingTalk Knowledge Graph                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Scanner    │───▶│   Fetcher    │───▶│ Graph Builder │      │
│  │  扫描模块    │    │  拉取模块    │    │   图谱模块    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Sync Manager │    │   Content    │    │   Export     │      │
│  │  同步管理    │    │   Storage    │    │   导出模块    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 安装依赖

```bash
pip install dingtalk-knowledge-graph
# 或从源码安装
pip install -e .
```

### 2. 配置认证信息

创建 `.env.dingtalk` 文件：

```env
# 钉钉企业认证信息
DINGTALK_APPKEY=your_appkey
DINGTALK_APPSECRET=your_appsecret

# 可选：知识图谱配置
KNOWLEDGE_GRAPH_DB=neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# 可选：向量数据库配置
VECTOR_DB=chromadb
CHROMA_DB_PATH=./chroma_db
```

### 3. 运行扫描

```bash
# 首次全量扫描
python -m dingtalk_knowledge_graph scan --full

# 增量扫描 (只获取更新的文档)
python -m dingtalk_knowledge_graph scan

# 构建知识图谱
python -m dingtalk_knowledge_graph build-graph

# 完整流程：扫描 + 构建图谱
python -m dingtalk_knowledge_graph sync
```

## 认证配置

### 1. 创建钉钉企业内部应用

在 [钉钉开发者后台](https://open.dingtalk.com/) 创建企业内部应用：

1. 进入「应用开发」→「企业内部开发」
2. 创建应用，选择「H5 微应用」或「小程序」
3. 获取 AppKey 和 AppSecret

### 2. 配置应用权限

确保应用具有以下权限：

| 权限 Code | 权限名称 | 用途 |
|-----------|----------|------|
| `wiki:knowledgeBase:read` | 读取知识库 | 获取知识库列表 |
| `wiki:doc:read` | 读取文档 | 获取文档内容和元数据 |
| `wiki:node:read` | 读取节点 | 获取文档树结构 |
| `contact:user:read` | 读取用户信息 | 获取创建者/编辑者信息 (可选) |

### 3. 存储认证信息

**方式一：.env 文件 (推荐)**

在项目根目录创建 `.env.dingtalk` 文件：

```env
DINGTALK_APPKEY=your_appkey
DINGTALK_APPSECRET=your_appsecret
```

⚠️ **重要**: 将 `.env.dingtalk` 添加到 `.gitignore`，不要提交到代码仓库。

**方式二：环境变量**

```bash
export DINGTALK_APPKEY=your_appkey
export DINGTALK_APPSECRET=your_appsecret
```

**方式三：配置文件**

创建 `config/dingtalk.json`:

```json
{
  "appkey": "your_appkey",
  "appsecret": "your_appsecret"
}
```

## API 参考

### 钉钉知识库 API

#### 1. 获取 Access Token

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

#### 2. 获取知识库列表

```http
GET https://api.dingtalk.com/v1.0/wiki/knowledgeBase/list?size=100
Header: x-acs-dingtalk-access-token: {access_token}
```

#### 3. 获取知识库节点列表

```http
GET https://api.dingtalk.com/v1.0/wiki/knowledgeBase/{knowledgeBaseId}/nodes
Header: x-acs-dingtalk-access-token: {access_token}
```

#### 4. 获取文档内容

```http
GET https://api.dingtalk.com/v1.0/wiki/doc/{docId}
Header: x-acs-dingtalk-access-token: {access_token}
```

## 使用方式

### 方式一：命令行工具

```bash
# 查看所有命令
python -m dingtalk_knowledge_graph --help

# 扫描知识库
python -m dingtalk_knowledge_graph scan [OPTIONS]

# 构建知识图谱
python -m dingtalk_knowledge_graph build-graph [OPTIONS]

# 导出图谱
python -m dingtalk_knowledge_graph export [OPTIONS]

# 查看同步状态
python -m dingtalk_knowledge_graph status
```

### 方式二：Python API

```python
from dingtalk_knowledge_graph import KnowledgeGraphSync

# 初始化
sync = KnowledgeGraphSync(
    appkey='your_appkey',
    appsecret='your_appsecret',
    storage_path='./dingtalk_data'
)

# 全量扫描
sync.scan(full=True)

# 增量扫描
updated_docs = sync.scan()
print(f'发现 {len(updated_docs)} 个更新的文档')

# 构建知识图谱
graph = sync.build_graph()

# 导出图谱
sync.export_graph(format='neo4j')
```

### 方式三：定时任务

**使用 cron:**

```bash
# 每天凌晨 2 点执行
0 2 * * * cd /path/to/project && python -m dingtalk_knowledge_graph sync >> sync.log 2>&1
```

**使用 systemd timer (Linux):**

创建 `/etc/systemd/system/dingtalk-sync.service`:

```ini
[Unit]
Description=DingTalk Knowledge Graph Sync
After=network.target

[Service]
Type=oneshot
User=your_user
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 -m dingtalk_knowledge_graph sync
Environment=PATH=/usr/bin:/bin
```

创建 `/etc/systemd/system/dingtalk-sync.timer`:

```ini
[Unit]
Description=Run DingTalk Sync Daily
Requires=dingtalk-sync.service

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

启用定时器：

```bash
sudo systemctl enable dingtalk-sync.timer
sudo systemctl start dingtalk-sync.timer
```

### 方式四：作为 Skill 使用

在 OpenCode 配置中加载此 skill 后，可以直接调用：

```
使用 dingtalk-knowledge-graph skill 扫描知识库并构建图谱
```

## 知识图谱构建

### 实体提取

从钉钉文档中自动提取以下类型的实体：

| 实体类型 | 说明 | 示例 |
|----------|------|------|
| `Document` | 文档 | 《API 接口文档》 |
| `KnowledgeBase` | 知识库 | 产品文档库 |
| `Person` | 人员 | 张三 (创建者/编辑者) |
| `Organization` | 组织/部门 | 技术部、产品组 |
| `Concept` | 概念/术语 | 微服务、RESTful API |
| `Date` | 时间 | 2024-03-17 |
| `Tag` | 标签/分类 | 重要、待审核 |

### 关系提取

自动识别文档间的关系：

| 关系类型 | 说明 | 示例 |
|----------|------|------|
| `CONTAINS` | 包含 | 知识库 → 文档 |
| `CREATED_BY` | 创建者 | 文档 → 人员 |
| `UPDATED_BY` | 更新者 | 文档 → 人员 |
| `BELONGS_TO` | 所属 | 文档 → 部门 |
| `RELATED_TO` | 关联 | 文档 → 文档 |
| `MENTIONS` | 提及 | 文档 → 概念 |
| `VERSION_OF` | 版本 | 文档 → 文档 |

### 图谱导出格式

支持多种图谱格式导出：

**1. Neo4j (推荐)**

```cypher
CREATE (d:Document {
  id: 'doc123',
  title: 'API 文档',
  createdAt: 1234567890000,
  updatedAt: 1234567890000
})

CREATE (kb:KnowledgeBase {
  id: 'kb456',
  name: '产品文档库'
})

CREATE (d)-[:CONTAINED_IN]->(kb)
```

**2. JSON-LD**

```json
{
  "@context": "https://schema.org/",
  "@type": "Document",
  "@id": "doc:doc123",
  "title": "API 文档",
  "containedIn": {
    "@type": "KnowledgeBase",
    "@id": "kb:kb456",
    "name": "产品文档库"
  }
}
```

**3. GraphML**

```xml
<graphml>
  <node id="doc123">
    <data key="type">Document</data>
    <data key="title">API 文档</data>
  </node>
  <edge source="doc123" target="kb456">
    <data key="relation">CONTAINED_IN</data>
  </edge>
</graphml>
```

## 数据存储结构

```
dingtalk_data/
├── sync-state.json          # 同步状态
├── knowledge-bases.json     # 知识库列表
├── documents/               # 文档元数据
│   ├── doc1.json
│   └── doc2.json
├── content/                 # 文档内容
│   ├── doc1.md
│   └── doc2.md
├── graph/                   # 知识图谱
│   ├── graph.json
│   ├── graph.graphml
│   └── neo4j-import.csv
├── chunks/                  # RAG 数据块
│   ├── doc1_chunks.json
│   └── doc2_chunks.json
└── logs/                    # 日志
    └── sync.log
```

### sync-state.json

```json
{
  "lastSyncTime": 1710662400000,
  "lastFullSyncTime": 1710576000000,
  "accessToken": "abc123...",
  "tokenExpiresAt": 1710669600000,
  "statistics": {
    "totalKnowledgeBases": 7,
    "totalDocuments": 156,
    "updatedDocuments": 12,
    "newDocuments": 3
  }
}
```

## 配置选项

### 完整配置示例 (config.yaml)

```yaml
# 钉钉认证
dingtalk:
  appkey: ${DINGTALK_APPKEY}
  appsecret: ${DINGTALK_APPSECRET}
  api_base_url: https://api.dingtalk.com
  token_cache_file: .token_cache

# 存储配置
storage:
  base_path: ./dingtalk_data
  content_format: markdown  # markdown, html, json
  compression: false

# 扫描配置
scan:
  batch_size: 100          # 批量获取数量
  max_retries: 3           # 失败重试次数
  rate_limit: 90           # 每分钟请求数
  full_sync_interval: 86400  # 全量同步间隔 (秒)

# 知识图谱配置
graph:
  enabled: true
  extract_entities: true
  extract_relations: true
  entity_types:
    - Document
    - KnowledgeBase
    - Person
    - Concept
  relation_types:
    - CONTAINS
    - CREATED_BY
    - RELATED_TO

# 导出配置
export:
  formats:
    - neo4j
    - json-ld
    - graphml
  output_dir: ./output

# 日志配置
logging:
  level: INFO
  file: ./logs/sync.log
  max_size: 10MB
  backup_count: 5

# 定时任务配置
scheduler:
  enabled: false
  cron: "0 2 * * *"  # 每天凌晨 2 点
  timezone: Asia/Shanghai
```

## 命令行参考

### scan - 扫描知识库

```bash
python -m dingtalk_knowledge_graph scan [OPTIONS]

选项:
  --full, -f         执行全量扫描 (默认增量)
  --knowledge-base   指定知识库 ID (只扫描该知识库)
  --output, -o       输出目录
  --verbose, -v      详细输出
  --dry-run          只检测不下载内容
```

### build-graph - 构建知识图谱

```bash
python -m dingtalk_knowledge_graph build-graph [OPTIONS]

选项:
  --input, -i        输入目录 (文档内容)
  --output, -o       输出目录 (图谱文件)
  --format, -f       输出格式 (neo4j/json-ld/graphml)
  --extract-entities 提取实体 (默认开启)
  --extract-relations 提取关系 (默认开启)
```

### export - 导出图谱

```bash
python -m dingtalk_knowledge_graph export [OPTIONS]

选项:
  --format, -f       导出格式 (neo4j/graphml/json/csv)
  --output, -o       输出文件路径
  --compress         压缩输出
```

### status - 查看状态

```bash
python -m dingtalk_knowledge_graph status

显示:
  - 最后同步时间
  - 知识库数量
  - 文档数量
  - 更新统计
```

## 错误处理

### 常见错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 0 | 成功 | - |
| 40035 | 缺少参数 | 检查请求参数 |
| 40036 | 参数格式错误 | 检查参数格式 |
| 40078 | 不存在的知识库 | 确认知识库 ID |
| 40079 | 不存在的节点 | 确认节点 ID |
| 50001 | access_token 过期 | 重新获取 token |
| 50002 | 权限不足 | 检查应用权限配置 |

### 错误处理示例

```python
from dingtalk_knowledge_graph import KnowledgeGraphSync, SyncError

try:
    sync = KnowledgeGraphSync(appkey, appsecret)
    sync.scan()
except SyncError as e:
    if e.code == 50001:
        print("Token 过期，请重新认证")
    elif e.code == 50002:
        print("权限不足，请检查应用权限配置")
    else:
        print(f"同步失败：{e.message}")
```

## 最佳实践

### 1. 首次同步

```bash
# 1. 全量扫描获取所有文档
python -m dingtalk_knowledge_graph scan --full

# 2. 构建知识图谱
python -m dingtalk_knowledge_graph build-graph

# 3. 导出到 Neo4j
python -m dingtalk_knowledge_graph export --format neo4j
```

### 2. 日常增量同步

```bash
# 每天执行一次增量同步
python -m dingtalk_knowledge_graph sync
```

### 3. 监控与告警

配置日志监控，当同步失败时发送告警：

```yaml
# config.yaml
alerts:
  enabled: true
  on_failure: true
  channels:
    - type: dingtalk
      webhook: https://oapi.dingtalk.com/robot/send?access_token=xxx
    - type: email
      recipients: [admin@example.com]
```

## 安全注意事项

1. **保护认证信息**: 不要将 AppKey/AppSecret 提交到代码仓库
2. **使用最小权限**: 只申请必要的 API 权限
3. **定期轮换密钥**: 建议每 90 天更新一次 AppSecret
4. **监控 API 调用**: 检查异常调用模式
5. **加密敏感数据**: 对存储的文档内容进行加密

## 故障排查

### 问题 1: 无法获取 Access Token

**症状**: `errcode: 40035, errmsg: invalid appkey`

**解决方案**:
1. 检查 AppKey/AppSecret 是否正确
2. 确认应用状态为「启用」
3. 检查网络连通性

### 问题 2: 权限不足

**症状**: `errcode: 50002, errmsg: permission denied`

**解决方案**:
1. 在钉钉后台检查应用权限配置
2. 确认应用已发布或添加为可见范围
3. 等待权限生效 (可能需要几分钟)

### 问题 3: 同步中断

**症状**: 同步过程中断，部分文档未同步

**解决方案**:
1. 检查 `sync-state.json` 查看中断位置
2. 使用 `--resume` 参数继续同步
3. 增加 `--max-retries` 参数值

## 性能优化

### 1. 批量处理

```python
# 批量获取文档内容 (推荐)
docs = sync.batch_get_documents(doc_ids, batch_size=100)
```

### 2. 并发处理

```python
# 使用多线程加速
sync.scan(concurrency=5)
```

### 3. 缓存 Token

```python
# Token 自动缓存，无需每次获取
sync = KnowledgeGraphSync(appkey, appsecret, cache_token=True)
```

## 相关资源

- [钉钉开放平台文档](https://open.dingtalk.com/document/development/dingtalk-document-overview)
- [知识库 API 文档](https://open.dingtalk.com/document/orgapp/wiki-overview)
- [Neo4j 导入指南](https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin-import/)
- [JSON-LD 规范](https://json-ld.org/spec/latest/json-ld/)
- [GraphML 格式](http://graphml.graphdrawing.org/)

## 版本历史

- **v0.1.0** (2024-03-17): 初始版本，支持基础扫描和图谱构建
- **v0.2.0** (计划): 添加定时任务支持
- **v0.3.0** (计划): 添加向量数据库集成

## 许可证

MIT License - 详见 LICENSE 文件
