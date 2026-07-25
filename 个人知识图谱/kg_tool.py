#!/usr/bin/env python3
"""
Knowledge Graph Skill - 核心工具脚本
通过 LightRAG REST API 操作知识图谱

用法:
    python kg_tool.py ingest --text "内容"
    python kg_tool.py ingest --file path/to/file
    python kg_tool.py ingest --url https://example.com
    python kg_tool.py ingest --dir path/to/dir
    python kg_tool.py query "问题" [--mode local|global|hybrid]
    python kg_tool.py explore [--port 9621]
    python kg_tool.py status
    python kg_tool.py entity get <name>
    python kg_tool.py entity delete <name>
"""

import argparse
import json
import os
import sys
import subprocess
import webbrowser
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import urlencode

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ============================================================
# 配置
# ============================================================

SKILL_DIR = Path(__file__).parent
ENV_FILE = SKILL_DIR / ".env"
DATA_DIR = Path(os.environ.get("RAG_STORAGE_DIR", str(Path.home() / "kg-data")))

# 从 .env 文件加载配置
def load_env():
    config = {
        "LIGHTRAG_PORT": "9621",
        "LLM_BINDING": "openai",
        "LLM_BINDING_HOST": "https://api.deepseek.com/v1",
        "LLM_MODEL": "deepseek-chat",
        "EMBEDDING_BINDING": "openai",
        "EMBEDDING_BINDING_HOST": "https://api.siliconflow.cn/v1",
        "EMBEDDING_MODEL": "BAAI/bge-m3",
        "EMBEDDING_DIM": "1024",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "neo4j123",
    }
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    config[key.strip()] = val.strip()
    return config

CONFIG = load_env()
BASE_URL = f"http://localhost:{CONFIG['LIGHTRAG_PORT']}"


# ============================================================
# HTTP 工具
# ============================================================

def api_get(path, params=None):
    """GET 请求"""
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urlencode(params)
    try:
        req = Request(url)
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        print(f"❌ API 请求失败: {e}")
        print(f"   请确认 LightRAG Server 已启动: lightrag-server --port {CONFIG['LIGHTRAG_PORT']}")
        sys.exit(1)

def api_post(path, data):
    """POST 请求"""
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode("utf-8")
    try:
        req = Request(url, data=body, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        print(f"❌ API 请求失败: {e}")
        sys.exit(1)

def api_delete(path, data=None):
    """DELETE 请求"""
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode("utf-8") if data else None
    headers = {"Content-Type": "application/json"} if data else {}
    try:
        req = Request(url, data=body, headers=headers, method="DELETE")
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        print(f"❌ API 请求失败: {e}")
        sys.exit(1)

def check_server():
    """检查 LightRAG Server 是否运行"""
    try:
        req = Request(f"{BASE_URL}/health")
        urlopen(req, timeout=5)
        return True
    except URLError:
        return False


# ============================================================
# 命令实现
# ============================================================

def cmd_ingest(args):
    """摄入知识到图谱"""
    if not check_server():
        print("❌ LightRAG Server 未运行")
        print(f"   启动命令: lightrag-server --port {CONFIG['LIGHTRAG_PORT']}")
        sys.exit(1)

    texts = []

    # 从纯文本
    if args.text:
        texts.append(("text-input", args.text))

    # 从文件
    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"❌ 文件不存在: {filepath}")
            sys.exit(1)
        content = filepath.read_text(encoding="utf-8", errors="replace")
        texts.append((filepath.name, content))

    # 从 URL
    if args.url:
        print(f"🌐 抓取 URL: {args.url}")
        try:
            req = Request(args.url, headers={"User-Agent": "KnowledgeGraph-Skill/1.0"})
            with urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                texts.append((args.url, content))
        except URLError as e:
            print(f"❌ URL 抓取失败: {e}")
            sys.exit(1)

    # 从目录
    if args.dir:
        dirpath = Path(args.dir)
        if not dirpath.is_dir():
            print(f"❌ 目录不存在: {dirpath}")
            sys.exit(1)
        exts = {".txt", ".md", ".markdown", ".rst", ".csv"}
        for f in sorted(dirpath.rglob("*")):
            if f.suffix.lower() in exts:
                content = f.read_text(encoding="utf-8", errors="replace")
                texts.append((f.name, content))

    if not texts:
        print("❌ 请指定摄入来源: --text / --file / --url / --dir")
        sys.exit(1)

    # 逐个摄入
    for name, content in texts:
        print(f"📥 摄入: {name} ({len(content)} 字符)")
        result = api_post("/documents/text", {
            "text": content,
            "doc_id": args.doc_id or None,
        })
        print(f"   ✅ 已提交，文档 ID: {result.get('doc_id', 'N/A')}")

    print(f"\n🎉 共摄入 {len(texts)} 个文档")


def cmd_query(args):
    """语义查询"""
    if not check_server():
        print("❌ LightRAG Server 未运行")
        sys.exit(1)

    mode = args.mode or "hybrid"
    print(f"🔍 查询 [{mode}]: {args.question}")

    result = api_post("/query", {
        "query": args.question,
        "mode": mode,
        "only_context": args.only_context or False,
        "response_type": "Multiple Paragraphs",
    })

    if "response" in result:
        print(f"\n{'='*60}")
        print(result["response"])
        print(f"{'='*60}")
    elif "context" in result:
        print(f"\n📋 检索结果:")
        for i, ctx in enumerate(result.get("context", []), 1):
            print(f"\n--- [{i}] ---")
            print(ctx)

    # 引用信息
    if args.references and "references" in result:
        print(f"\n📚 引用:")
        for ref in result["references"]:
            print(f"  - {ref.get('file_path', ref.get('reference_id', 'N/A'))}")


def cmd_explore(args):
    """启动 Web UI 浏览器"""
    port = args.port or CONFIG["LIGHTRAG_PORT"]
    url = f"http://localhost:{port}"

    if not check_server():
        print("❌ LightRAG Server 未运行，正在尝试启动...")
        # 尝试后台启动
        try:
            subprocess.Popen(
                ["lightrag-server", "--port", str(port)],
                stdout=open(os.devnull, "w"),
                stderr=subprocess.STDOUT,
            )
            print("⏳ 等待 Server 启动...")
            import time
            for _ in range(30):
                time.sleep(2)
                try:
                    urlopen(f"http://localhost:{port}/health", timeout=3)
                    break
                except URLError:
                    continue
        except FileNotFoundError:
            print("❌ lightrag-server 命令未找到，请先运行 setup.sh")
            sys.exit(1)

    print(f"🌐 打开知识图谱 Web UI: {url}")
    webbrowser.open(url)


def cmd_status(args):
    """查看图谱状态"""
    server_ok = check_server()

    print("\n📊 知识图谱状态")
    print("━" * 40)
    print(f"  LightRAG Server: {'✅ 运行中' if server_ok else '❌ 未运行'}")
    print(f"  服务地址:        {BASE_URL}")

    if server_ok:
        try:
            counts = api_get("/documents/status_counts")
            if isinstance(counts, dict):
                statuses = counts.get("statuses_count") or counts.get("counts") or counts
                if isinstance(statuses, dict):
                    total = sum(int(v) for v in statuses.values() if isinstance(v, (int, str)) and str(v).isdigit())
                    print(f"  文档总数:        {total}")
                    for k, v in statuses.items():
                        print(f"    {k:12}: {v}")
        except Exception as e:
            print(f"  文档状态查询失败: {e}")

        try:
            pipe = api_get("/documents/pipeline_status")
            busy = pipe.get("busy") if isinstance(pipe, dict) else None
            if busy is not None:
                print(f"  Pipeline:        {'处理中' if busy else '空闲'}")
        except Exception:
            pass

        try:
            # 获取图谱标签
            labels = api_get("/graph/label/list")
            if isinstance(labels, dict) and "labels" in labels:
                print(f"  图谱标签:        {', '.join(labels['labels'][:10])}")
        except Exception:
            pass

    # Neo4j 状态
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            CONFIG["NEO4J_URI"],
            auth=(CONFIG.get("NEO4J_USERNAME", CONFIG.get("NEO4J_USER", "neo4j")), CONFIG["NEO4J_PASSWORD"])
        )
        driver.verify_connectivity()
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()["count"]
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()["count"]
            print(f"  Neo4j:           ✅ 连接正常")
            print(f"    实体数量:      {node_count:,}")
            print(f"    关系数量:      {rel_count:,}")
        driver.close()
    except ImportError:
        print(f"  Neo4j:           ⚠️ neo4j Python 包未安装 (pip install neo4j)")
    except Exception as e:
        print(f"  Neo4j:           ❌ 连接失败 ({e})")

    # 存储大小
    storage_path = Path(CONFIG.get("RAG_STORAGE_DIR", str(Path.home() / "kg-data")))
    if storage_path.exists():
        total_size = sum(f.stat().st_size for f in storage_path.rglob("*") if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f"  存储大小:        {size_mb:.1f} MB")
        print(f"  存储目录:        {storage_path}")

    print()


def cmd_entity(args):
    """实体管理"""
    if not check_server():
        print("❌ LightRAG Server 未运行")
        sys.exit(1)

    if args.action == "get":
        result = api_post("/query", {
            "query": f"关于 {args.name} 的详细信息",
            "mode": "local",
            "only_context": True,
        })
        print(f"🔎 实体: {args.name}")
        if "context" in result:
            for ctx in result.get("context", []):
                print(ctx)

    elif args.action == "delete":
        print(f"🗑️ 删除实体: {args.name}")
        result = api_delete("/graph/entity", {"entity_name": args.name})
        print(f"   {result}")

    elif args.action == "update":
        if not args.data:
            print("❌ 请提供 --data 参数 (JSON 格式)")
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print("❌ --data 参数不是有效的 JSON")
            sys.exit(1)
        result = api_post("/graph/entity/edit", {
            "entity_name": args.name,
            "updated_data": data,
        })
        print(f"✅ 实体已更新: {result}")

    elif args.action == "merge":
        if not args.into:
            print("❌ 请提供 --into 参数指定合并目标")
            sys.exit(1)
        result = api_post("/graph/entity/edit", {
            "entity_name": args.name,
            "updated_data": {"entity_name": args.into},
            "allow_rename": True,
            "allow_merge": True,
        })
        print(f"✅ 实体已合并: {result}")

    else:
        print(f"❌ 未知操作: {args.action}")
        print("   支持: get / delete / update / merge")


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Knowledge Graph Skill - 个人知识图谱工具",
        prog="kg_tool"
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # --- ingest ---
    p_ingest = subparsers.add_parser("ingest", help="摄入知识到图谱")
    p_ingest.add_argument("--text", help="直接输入文本")
    p_ingest.add_argument("--file", help="从文件摄入")
    p_ingest.add_argument("--url", help="从 URL 摄入")
    p_ingest.add_argument("--dir", help="从目录批量摄入")
    p_ingest.add_argument("--doc-id", help="自定义文档 ID")

    # --- query ---
    p_query = subparsers.add_parser("query", help="语义查询")
    p_query.add_argument("question", help="查询问题")
    p_query.add_argument("--mode", choices=["local", "global", "hybrid"], default="hybrid", help="查询模式 (默认: hybrid)")
    p_query.add_argument("--references", action="store_true", help="返回引用信息")
    p_query.add_argument("--only-context", action="store_true", help="只返回检索结果不生成")

    # --- explore ---
    p_explore = subparsers.add_parser("explore", help="启动 Web UI 可视化")
    p_explore.add_argument("--port", type=int, help="指定端口")

    # --- status ---
    subparsers.add_parser("status", help="查看图谱状态")

    # --- entity ---
    p_entity = subparsers.add_parser("entity", help="实体管理")
    p_entity.add_argument("action", choices=["get", "delete", "update", "merge"], help="操作")
    p_entity.add_argument("name", help="实体名称")
    p_entity.add_argument("--data", help="更新数据 (JSON)")
    p_entity.add_argument("--into", help="合并目标实体名称")

    args = parser.parse_args()

    if args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "query":
        cmd_query(args)
    elif args.command == "explore":
        cmd_explore(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "entity":
        cmd_entity(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
