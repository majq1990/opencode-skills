---
name: knowledge-graph
description: 使用本机 LightRAG + Neo4j 个人知识图谱摄入资料、做语义检索、查看图谱状态、打开图谱 Web UI、查询或维护实体。用于知识图谱、知识库、个人知识管理、GraphRAG、LightRAG、图数据库、kg-ingest、kg-query、kg-explore、语义检索、实体关系整理等请求；当用户希望把文本、文件、URL 或目录写入共享知识图谱，或从图谱召回历史知识时使用。
---

# Knowledge Graph

## 入口

把本 skill 视为本机共享知识图谱的操作入口。优先调用同目录脚本：

```powershell
python D:\opencode\config\skills\knowledge-graph\kg_tool.py --help
```

核心组件：
- `kg_tool.py`：摄入、查询、状态、Web UI、实体管理
- `setup.ps1`：Windows 首次部署或恢复 LightRAG 服务
- `.env.example`：配置模板；真实密钥在 `.env`，不要在回复或日志里回显
- `docker-compose.yml`：Neo4j 容器依赖

## 先判断任务

按用户动作选择命令：

| 任务 | 命令 |
|---|---|
| 摄入文本 | `ingest --text` |
| 摄入文件 | `ingest --file` |
| 摄入 URL | `ingest --url` |
| 批量摄入目录 | `ingest --dir` |
| 从图谱问答 | `query` |
| 只取检索上下文 | `query --only-context` |
| 看运行状态 | `status` |
| 打开图谱 Web UI | `explore` |
| 查实体 | `entity get` |
| 改名、合并、删除实体 | `entity update` / `entity merge` / `entity delete` |

## 标准流程

1. 先查状态：

```powershell
python D:\opencode\config\skills\knowledge-graph\kg_tool.py status
```

2. 如果 LightRAG Server 未运行，先确认 `.env` 已存在，再执行 Windows 部署脚本：

```powershell
powershell -ExecutionPolicy Bypass -File D:\opencode\config\skills\knowledge-graph\setup.ps1
```

3. 服务正常后执行用户任务。
4. 摄入后说明提交了多少文档；查询后直接给答案，必要时附上查询模式和是否只取上下文。

## 常用命令

```powershell
# 摄入文本
python D:\opencode\config\skills\knowledge-graph\kg_tool.py ingest --text "这是一段要写入图谱的知识"

# 摄入单文件
python D:\opencode\config\skills\knowledge-graph\kg_tool.py ingest --file C:\notes\meeting.md

# 摄入 URL
python D:\opencode\config\skills\knowledge-graph\kg_tool.py ingest --url https://example.com

# 摄入目录中的 txt/md/markdown/rst/csv
python D:\opencode\config\skills\knowledge-graph\kg_tool.py ingest --dir C:\notes

# 默认 hybrid 查询
python D:\opencode\config\skills\knowledge-graph\kg_tool.py query "Kubernetes 和 Docker 的关系是什么？"

# local 细节查询
python D:\opencode\config\skills\knowledge-graph\kg_tool.py query --mode local "谁创建了 Python？"

# global 主题总结
python D:\opencode\config\skills\knowledge-graph\kg_tool.py query --mode global "总结微服务架构的主要取舍"

# 只返回检索上下文
python D:\opencode\config\skills\knowledge-graph\kg_tool.py query --only-context "最近的项目复盘结论"

# 打开可视化界面
python D:\opencode\config\skills\knowledge-graph\kg_tool.py explore
```

## 查询模式

默认用 `hybrid`。

| mode | 适用场景 |
|---|---|
| `local` | 人名、事实、局部细节、精确关联 |
| `global` | 主题概览、跨文档总结、宏观脉络 |
| `hybrid` | 复杂问题、既要细节又要归纳的查询 |

用户明确只要原始召回结果时，用 `--only-context`。需要脚本返回引用时，加 `--references`。

## 摄入约束

- 写入图谱前确认用户确实要摄入，而不是只想临时总结材料。
- 对目录摄入先说明脚本当前只读取 `txt`、`md`、`markdown`、`rst`、`csv`。
- 对重复、低质量或含敏感信息的材料，先提醒写入会进入共享知识图谱。
- URL 摄入由 `kg_tool.py` 直接抓取页面文本；遇到动态页面或登录页时说明抓取可能不足，再选择其他取数方式。

## 实体管理

查询实体可直接执行：

```powershell
python D:\opencode\config\skills\knowledge-graph\kg_tool.py entity get "实体名"
```

`entity update`、`entity merge`、`entity delete` 会改图谱。执行前先向用户确认目标实体和影响范围，再运行命令。

## 配置与故障

- 真实配置读取同目录 `.env`。
- Embedding 默认是 SiliconFlow `BAAI/bge-m3`，维度为 `1024`。已有图谱不要随意切换 embedding 模型或维度。
- 默认服务端口是 `9621`，Web UI 是 `http://localhost:9621`。
- 状态或查询报服务不可达时，优先跑 `status`，再用 `setup.ps1` 恢复服务。
- LightRAG 启动失败时查看 `C:\Users\majq1\kg-data\lightrag-server.err.log`。
- Neo4j 连接失败时先检查 Docker 和 `neo4j` 容器状态，不要直接清空图库。

## 清空与重建

重置存储、删除实体、清空 Neo4j 都会破坏已有知识。只有用户明确要求清空、重建或删除时才执行，并先说明影响范围。
