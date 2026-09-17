"""
MaxKB Knowledge Graph Sync - CLI Entry Point
"""

import argparse
import logging
import sys
import os
from pathlib import Path


def setup_logging(verbose: bool = False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('maxkb_sync.log', encoding='utf-8')
        ]
    )


def load_env(env_file: str = ".env.maxkb"):
    """加载环境变量"""
    env_path = Path(env_file)
    if not env_path.exists():
        env_path = Path.home() / ".env.maxkb"
    
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def cmd_sync(args):
    """同步命令"""
    from . import KnowledgeGraphSync
    
    load_env()
    
    # 从环境变量获取配置
    maxkb_base_url = os.environ.get('MAXKB_BASE_URL', 'http://111.4.141.154:18080')
    maxkb_username = os.environ.get('MAXKB_USERNAME', 'egova-jszc')
    maxkb_password = os.environ.get('MAXKB_PASSWORD', 'eGova@2026')
    
    dingtalk_appkey = os.environ.get('DINGTALK_APPKEY')
    dingtalk_appsecret = os.environ.get('DINGTALK_APPSECRET')
    
    dataset_name = os.environ.get('DATASET_NAME', '支持部测试')
    tag_name = os.environ.get('TAG_NAME', '支持部测试')
    
    if not dingtalk_appkey or not dingtalk_appsecret:
        print("Error: Missing DINGTALK_APPKEY or DINGTALK_APPSECRET")
        print("Please set environment variables or create .env.maxkb file")
        sys.exit(1)
    
    # 初始化同步器
    sync = KnowledgeGraphSync(
        maxkb_base_url=maxkb_base_url,
        maxkb_username=maxkb_username,
        maxkb_password=maxkb_password,
        dingtalk_appkey=dingtalk_appkey,
        dingtalk_appsecret=dingtalk_appsecret,
        dataset_name=dataset_name,
        tag_name=tag_name,
        storage_path=args.output
    )
    
    # 执行同步
    sync.sync(
        incremental=not args.full,
        build_graph=not args.no_graph,
        upload_vector=not args.no_vector
    )


def cmd_scan(args):
    """扫描命令"""
    from . import KnowledgeGraphSync
    import requests
    
    load_env()
    
    dingtalk_appkey = os.environ.get('DINGTALK_APPKEY')
    dingtalk_appsecret = os.environ.get('DINGTALK_APPSECRET')
    
    if not dingtalk_appkey or not dingtalk_appsecret:
        print("Error: Missing DingTalk credentials")
        sys.exit(1)
    
    # 获取 Token
    token_url = f"https://oapi.dingtalk.com/gettoken?appkey={dingtalk_appkey}&appsecret={dingtalk_appsecret}"
    response = requests.get(token_url)
    token_data = response.json()
    
    if token_data.get('errcode') != 0:
        print(f"Failed to get token: {token_data.get('errmsg')}")
        sys.exit(1)
    
    access_token = token_data['access_token']
    
    # 导入并使用 scanner
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from dingtalk_knowledge_graph.lib.scanner import DingTalkScanner
    
    scanner = DingTalkScanner(access_token)
    
    documents = scanner.scan_all(full_scan=args.full)
    
    print(f"\n{'='*60}")
    print(f"Scan completed!")
    print(f"Found {len(documents)} documents")
    print(f"{'='*60}\n")


def cmd_status(args):
    """状态命令"""
    from . import KnowledgeGraphSync
    
    load_env()
    
    maxkb_base_url = os.environ.get('MAXKB_BASE_URL', 'http://111.4.141.154:18080')
    maxkb_username = os.environ.get('MAXKB_USERNAME', 'egova-jszc')
    maxkb_password = os.environ.get('MAXKB_PASSWORD', 'eGova@2026')
    
    dataset_name = os.environ.get('DATASET_NAME', '支持部测试')
    
    sync = KnowledgeGraphSync(
        maxkb_base_url=maxkb_base_url,
        maxkb_username=maxkb_username,
        maxkb_password=maxkb_password,
        dingtalk_appkey='temp',
        dingtalk_appsecret='temp',
        dataset_name=dataset_name
    )
    
    stats = sync.get_statistics()
    
    print("\n" + "="*60)
    print("MaxKB Knowledge Graph Status")
    print("="*60)
    print(f"Dataset: {stats['dataset_name']} ({stats['dataset_id']})")
    print(f"MaxKB Statistics:")
    
    if 'maxkb_stats' in stats:
        mk_stats = stats['maxkb_stats']
        print(f"  Total Datasets: {mk_stats.get('total_datasets', 0)}")
        print(f"  Total Documents: {mk_stats.get('total_documents', 0)}")
        print(f"  Total Paragraphs: {mk_stats.get('total_paragraphs', 0)}")
    
    print("-"*60)
    print(f"Sync Statistics:")
    print(f"  Scanned: {stats.get('total_scanned', 0)}")
    print(f"  Structured: {stats.get('structured_count', 0)}")
    print(f"  Unstructured: {stats.get('unstructured_count', 0)}")
    print(f"  Uploaded: {stats.get('uploaded_count', 0)}")
    print(f"  Failed: {stats.get('failed_count', 0)}")
    print("="*60 + "\n")


def cmd_delete(args):
    """删除命令"""
    from . import KnowledgeGraphSync
    
    load_env()
    
    maxkb_base_url = os.environ.get('MAXKB_BASE_URL', 'http://111.4.141.154:18080')
    maxkb_username = os.environ.get('MAXKB_USERNAME', 'egova-jszc')
    maxkb_password = os.environ.get('MAXKB_PASSWORD', 'eGova@2026')
    
    dataset_name = os.environ.get('DATASET_NAME', '支持部测试')
    tag_name = args.tag or os.environ.get('TAG_NAME', '支持部测试')
    
    sync = KnowledgeGraphSync(
        maxkb_base_url=maxkb_base_url,
        maxkb_username=maxkb_username,
        maxkb_password=maxkb_password,
        dingtalk_appkey='temp',
        dingtalk_appsecret='temp',
        dataset_name=dataset_name,
        tag_name=tag_name
    )
    
    if not args.confirm:
        response = input(f"Are you sure you want to delete all documents with tag '{tag_name}'? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled")
            return
    
    deleted = sync.delete_by_tag(tag=tag_name, dry_run=args.dry_run)
    
    action = "Would delete" if args.dry_run else "Deleted"
    print(f"{action} {deleted} documents with tag: {tag_name}")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description='MaxKB Knowledge Graph Sync',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s sync --full                    # Full sync
  %(prog)s sync                           # Incremental sync
  %(prog)s scan                           # Scan DingTalk only
  %(prog)s status                         # Show status
  %(prog)s delete --tag "支持部测试"       # Delete by tag
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-o', '--output', default='./maxkb_data', help='Output directory')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # sync 命令
    sync_parser = subparsers.add_parser('sync', help='Full sync (scan + classify + upload)')
    sync_parser.add_argument('-f', '--full', action='store_true', help='Full sync')
    sync_parser.add_argument('--no-graph', action='store_true', help='Skip graph building')
    sync_parser.add_argument('--no-vector', action='store_true', help='Skip vector upload')
    sync_parser.set_defaults(func=cmd_sync)
    
    # scan 命令
    scan_parser = subparsers.add_parser('scan', help='Scan DingTalk knowledge bases')
    scan_parser.add_argument('-f', '--full', action='store_true', help='Full scan')
    scan_parser.set_defaults(func=cmd_scan)
    
    # status 命令
    status_parser = subparsers.add_parser('status', help='Show sync status')
    status_parser.set_defaults(func=cmd_status)
    
    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='Delete documents by tag')
    delete_parser.add_argument('-t', '--tag', help='Tag name')
    delete_parser.add_argument('--dry-run', action='store_true', help='Preview only')
    delete_parser.add_argument('--confirm', action='store_true', help='Skip confirmation')
    delete_parser.set_defaults(func=cmd_delete)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    setup_logging(args.verbose)
    args.func(args)


if __name__ == '__main__':
    main()
