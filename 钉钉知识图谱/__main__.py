"""
DingTalk Knowledge Graph Sync

Main entry point for synchronizing DingTalk knowledge bases and building knowledge graphs
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .lib.scanner import DingTalkScanner, TokenExpiredError, APIError
from .lib.fetcher import ContentFetcher
from .lib.sync_manager import SyncManager
from .lib.graph_builder import KnowledgeGraphBuilder


def setup_logging(verbose: bool = False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('dingtalk_sync.log', encoding='utf-8')
        ]
    )


def load_env(env_file: str = ".env.dingtalk") -> dict:
    """加载环境变量"""
    env_path = Path(env_file)
    if not env_path.exists():
        env_path = Path.home() / ".env.dingtalk"
    
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    import os
    # 环境变量优先
    for key in ['DINGTALK_APPKEY', 'DINGTALK_APPSECRET']:
        if key in os.environ:
            env_vars[key] = os.environ[key]
    
    return env_vars


def cmd_scan(args):
    """扫描知识库命令"""
    env = load_env()
    appkey = env.get('DINGTALK_APPKEY')
    appsecret = env.get('DINGTALK_APPSECRET')
    
    if not appkey or not appsecret:
        print("Error: Missing DINGTALK_APPKEY or DINGTALK_APPSECRET")
        print("Please set environment variables or create .env.dingtalk file")
        sys.exit(1)
    
    sync_manager = SyncManager(args.output)
    
    # 检查是否需要刷新 token
    if sync_manager.is_token_valid() and not args.full:
        access_token = sync_manager.get_access_token()
    else:
        # 获取新 token
        import requests
        token_url = f"https://oapi.dingtalk.com/gettoken?appkey={appkey}&appsecret={appsecret}"
        response = requests.get(token_url)
        token_data = response.json()
        
        if token_data.get('errcode') != 0:
            print(f"Failed to get access token: {token_data.get('errmsg')}")
            sys.exit(1)
        
        access_token = token_data['access_token']
        expires_in = token_data['expires_in']
        sync_manager.update_token(access_token, expires_in)
    
    # 创建扫描器
    scanner = DingTalkScanner(access_token)
    
    # 执行扫描
    last_sync_time = sync_manager.get_last_sync_time() if not args.full else None
    
    try:
        documents = scanner.scan_all(
            full_scan=args.full,
            last_sync_time=last_sync_time
        )
        
        print(f"\n{'='*60}")
        print(f"Scan completed!")
        print(f"Found {len(documents)} documents")
        print(f"{'='*60}\n")
        
        # 更新同步状态
        sync_manager.update_sync_time(full_sync=args.full)
        
    except TokenExpiredError:
        print("Token expired, please re-authenticate")
        sync_manager.reset()
        sys.exit(1)
    except APIError as e:
        print(f"API Error: {e.code} - {e.message}")
        sys.exit(1)


def cmd_sync(args):
    """完整同步命令 (扫描 + 拉取内容 + 构建图谱)"""
    env = load_env()
    appkey = env.get('DINGTALK_APPKEY')
    appsecret = env.get('DINGTALK_APPSECRET')
    
    if not appkey or not appsecret:
        print("Error: Missing authentication credentials")
        sys.exit(1)
    
    sync_manager = SyncManager(args.output)
    
    # 获取 token
    import requests
    token_url = f"https://oapi.dingtalk.com/gettoken?appkey={appkey}&appsecret={appsecret}"
    response = requests.get(token_url)
    token_data = response.json()
    
    if token_data.get('errcode') != 0:
        print(f"Failed to get access token: {token_data.get('errmsg')}")
        sys.exit(1)
    
    access_token = token_data['access_token']
    expires_in = token_data['expires_in']
    sync_manager.update_token(access_token, expires_in)
    
    # 1. 扫描
    print("Step 1/3: Scanning knowledge bases...")
    scanner = DingTalkScanner(access_token)
    last_sync_time = sync_manager.get_last_sync_time() if not args.full else None
    
    documents = scanner.scan_all(full_scan=args.full, last_sync_time=last_sync_time)
    print(f"  Found {len(documents)} documents\n")
    
    # 2. 拉取内容
    print("Step 2/3: Fetching document content...")
    fetcher = ContentFetcher(scanner, args.output)
    fetcher.fetch_batch(documents, skip_existing=not args.full)
    print("  Content fetched\n")
    
    # 3. 构建图谱
    if args.build_graph:
        print("Step 3/3: Building knowledge graph...")
        all_docs = fetcher.get_all_documents()
        graph = KnowledgeGraphBuilder()
        graph.build(all_docs)
        
        graph_output = Path(args.output) / "graph"
        graph_output.mkdir(parents=True, exist_ok=True)
        
        graph.export_json(str(graph_output / "graph.json"))
        print(f"  Graph exported to {graph_output}\n")
    
    # 更新状态
    sync_manager.update_sync_time(full_sync=args.full)
    sync_manager.update_statistics(
        documents=len(documents),
        updated=len(documents) if not args.full else 0
    )
    
    print("="*60)
    print("Sync completed successfully!")
    print("="*60)


def cmd_status(args):
    """查看状态命令"""
    sync_manager = SyncManager(args.output)
    stats = sync_manager.get_statistics()
    
    print("\n" + "="*60)
    print("DingTalk Sync Status")
    print("="*60)
    print(f"Last Sync:        {stats['lastSyncTimeFormatted']}")
    print(f"Last Full Sync:   {stats['lastFullSyncTimeFormatted']}")
    print(f"Token Valid:      {'Yes' if stats['tokenValid'] else 'No'}")
    print("-"*60)
    print(f"Knowledge Bases:  {stats['totalKnowledgeBases']}")
    print(f"Total Documents:  {stats['totalDocuments']}")
    print(f"Updated:          {stats['updatedDocuments']}")
    print(f"New:              {stats['newDocuments']}")
    print("="*60 + "\n")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description='DingTalk Knowledge Graph Sync',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-o', '--output', default='./dingtalk_data', help='Output directory')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # scan 命令
    scan_parser = subparsers.add_parser('scan', help='Scan knowledge bases')
    scan_parser.add_argument('-f', '--full', action='store_true', help='Full scan')
    scan_parser.set_defaults(func=cmd_scan)
    
    # sync 命令
    sync_parser = subparsers.add_parser('sync', help='Full sync (scan + fetch + build graph)')
    sync_parser.add_argument('-f', '--full', action='store_true', help='Full sync')
    sync_parser.add_argument('--no-graph', action='store_false', dest='build_graph', help='Skip graph building')
    sync_parser.set_defaults(func=cmd_sync)
    
    # status 命令
    status_parser = subparsers.add_parser('status', help='Show sync status')
    status_parser.set_defaults(func=cmd_status)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    setup_logging(args.verbose)
    args.func(args)


if __name__ == '__main__':
    main()
