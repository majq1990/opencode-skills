#!/bin/bash
# knowledge-graph Skill 一键部署脚本
# 安装依赖 + 启动 Neo4j + 配置 Ollama + 启动 LightRAG Server

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR" && pwd)"
ENV_FILE="$SKILL_DIR/.env"
DATA_DIR="$HOME/kg-data"
LIGHTRAG_DIR="$HOME/LightRAG"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail()  { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

# ============================================================
# Step 0: 检查前置依赖
# ============================================================
info "检查前置依赖..."

command -v python &>/dev/null || fail "Python 未安装，请先安装 Python 3.10+"
command -v docker &>/dev/null || fail "Docker 未安装，请先安装 Docker"
command -v git &>/dev/null || fail "Git 未安装"

PYTHON_VER=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Python $PYTHON_VER detected"

# ============================================================
# Step 1: 克隆 LightRAG
# ============================================================
if [ ! -d "$LIGHTRAG_DIR" ]; then
    info "克隆 LightRAG 到 $LIGHTRAG_DIR ..."
    git clone https://github.com/HKUDS/LightRAG.git "$LIGHTRAG_DIR"
else
    info "LightRAG 已存在，更新到最新版..."
    cd "$LIGHTRAG_DIR" && git pull --ff-only
fi

# ============================================================
# Step 2: 创建 .env 配置
# ============================================================
if [ ! -f "$ENV_FILE" ]; then
    info "创建默认配置 $ENV_FILE ..."
    mkdir -p "$DATA_DIR"
    cat > "$ENV_FILE" << 'ENVEOF'
# LLM 配置
LLM_BINDING=ollama
LLM_MODEL=qwen2.5:7b
EMBEDDING_BINDING=ollama
EMBEDDING_MODEL=bge-m3:latest
OLLAMA_BASE_URL=http://localhost:11434

# Neo4j 图数据库
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=kg_password_2026

# LightRAG 存储
RAG_STORAGE_DIR=__DATA_DIR__
LIGHTRAG_PORT=9621

# 查询参数
CHUNK_SIZE=1200
CHUNK_OVERLAP=100
MAX_ASYNC=16
ENVEOF
    # 替换数据目录路径
    if [ "$(uname)" = "MINGW" ] || [ "$(uname)" = "MSYS" ] || [[ "$(uname -s)" == CYGWIN* ]]; then
        # Windows MSYS/Git Bash: 使用 Windows 路径
        WIN_DATA_DIR=$(cygpath -w "$DATA_DIR" 2>/dev/null || echo "$DATA_DIR")
        sed -i "s|__DATA_DIR__|${WIN_DATA_DIR}|g" "$ENV_FILE"
    else
        sed -i "s|__DATA_DIR__|${DATA_DIR}|g" "$ENV_FILE"
    fi
    warn "已创建默认配置，请根据需要修改 $ENV_FILE"
else
    info "配置文件已存在: $ENV_FILE"
fi

source "$ENV_FILE"

# ============================================================
# Step 3: 启动 Neo4j Docker
# ============================================================
info "检查 Neo4j 容器..."
if docker ps -a --format '{{.Names}}' | grep -q '^kg-neo4j$'; then
    if docker ps --format '{{.Names}}' | grep -q '^kg-neo4j$'; then
        ok "Neo4j 容器已在运行"
    else
        info "启动已存在的 Neo4j 容器..."
        docker start kg-neo4j
        ok "Neo4j 已启动"
    fi
else
    info "创建并启动 Neo4j 容器..."
    docker run -d \
        --name kg-neo4j \
        -p 7474:7474 \
        -p 7687:7687 \
        -e NEO4J_AUTH="${NEO4J_USER}/${NEO4J_PASSWORD}" \
        -e NEO4J_PLUGINS='["apoc"]' \
        -v kg-neo4j-data:/data \
        --restart unless-stopped \
        neo4j:5-community
    ok "Neo4j 已启动 (http://localhost:7474)"
fi

# ============================================================
# Step 4: 安装 LightRAG + Python 依赖
# ============================================================
info "安装 LightRAG Python 包..."
pip install lightrag-hku --quiet 2>/dev/null || pip install lightrag-hku
pip install neo4j --quiet 2>/dev/null || pip install neo4j

ok "LightRAG 已安装"

# ============================================================
# Step 5: 检查 Ollama
# ============================================================
info "检查 Ollama..."
if docker ps --format '{{.Names}}' | grep -q '^kg-ollama$'; then
    ok "Ollama 容器已在运行"
elif command -v ollama &>/dev/null; then
    if ollama list &>/dev/null 2>&1; then
        ok "Ollama 本地已运行"
    else
        warn "Ollama 已安装但未运行，请手动启动: ollama serve"
    fi
else
    info "启动 Ollama Docker 容器..."
    docker run -d \
        --name kg-ollama \
        -p 11434:11434 \
        -v kg-ollama-data:/root/.ollama \
        --restart unless-stopped \
        ollama/ollama:latest
    ok "Ollama 已启动 (http://localhost:11434)"
    info "正在拉取模型（首次需要较长时间）..."
    docker exec kg-ollama ollama pull qwen2.5:7b
    docker exec kg-ollama ollama pull bge-m3:latest
fi

# ============================================================
# Step 6: 启动 LightRAG Server
# ============================================================
info "启动 LightRAG Server..."
cd "$LIGHTRAG_DIR"

# 构建启动命令
LIGHTRAG_CMD="lightrag-server"
LIGHTRAG_CMD="$LIGHTRAG_CMD --port ${LIGHTRAG_PORT:-9621}"
LIGHTRAG_CMD="$LIGHTRAG_CMD --llm-binding ${LLM_BINDING:-ollama}"
LIGHTRAG_CMD="$LIGHTRAG_CMD --llm-model ${LLM_MODEL:-qwen2.5:7b}"
LIGHTRAG_CMD="$LIGHTRAG_CMD --embedding-binding ${EMBEDDING_BINDING:-ollama}"
LIGHTRAG_CMD="$LIGHTRAG_CMD --embedding-model ${EMBEDDING_MODEL:-bge-m3:latest}"
LIGHTRAG_CMD="$LIGHTRAG_CMD --storage-dir ${RAG_STORAGE_DIR}"

# Neo4j 配置
export NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}"
export NEO4J_USER="${NEO4J_USER:-neo4j}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-kg_password_2026}"

if [ "$(uname)" = "MINGW" ] || [ "$(uname)" = "MSYS" ] || [[ "$(uname -s)" == CYGWIN* ]]; then
    # Windows: 后台启动
    info "Windows 环境检测，后台启动 LightRAG Server..."
    nohup $LIGHTRAG_CMD > "$DATA_DIR/lightrag-server.log" 2>&1 &
    SERVER_PID=$!
    echo "$SERVER_PID" > "$DATA_DIR/lightrag-server.pid"
    info "LightRAG Server PID: $SERVER_PID"
    info "日志: $DATA_DIR/lightrag-server.log"
else
    # Linux/Mac: 后台启动
    nohup $LIGHTRAG_CMD > "$DATA_DIR/lightrag-server.log" 2>&1 &
    SERVER_PID=$!
    echo "$SERVER_PID" > "$DATA_DIR/lightrag-server.pid"
fi

# 等待 Server 启动
info "等待 LightRAG Server 启动..."
for i in $(seq 1 30); do
    if curl -s "http://localhost:${LIGHTRAG_PORT:-9621}/health" >/dev/null 2>&1; then
        ok "LightRAG Server 已启动！"
        break
    fi
    sleep 2
done

# ============================================================
# Done
# ============================================================
echo ""
echo "============================================"
echo -e "${GREEN}✅ 知识图谱 Skill 部署完成！${NC}"
echo "============================================"
echo ""
echo "📊 服务地址:"
echo "   LightRAG Web UI:  http://localhost:${LIGHTRAG_PORT:-9621}"
echo "   LightRAG API:     http://localhost:${LIGHTRAG_PORT:-9621}/docs"
echo "   Neo4j Browser:    http://localhost:7474"
echo "   Ollama:           http://localhost:11434"
echo ""
echo "📝 快速开始:"
echo "   kg-ingest --text '你的知识内容'"
echo "   kg-query '你的问题'"
echo "   kg-explore"
echo ""
echo "⚙️  配置文件: $ENV_FILE"
echo "📁 数据目录:  $DATA_DIR"
echo ""
