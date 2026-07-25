"""
DingTalk Knowledge Graph

A skill for scanning DingTalk knowledge bases, tracking document updates, 
and building knowledge graphs from documents.
"""

from .lib.scanner import DingTalkScanner, TokenExpiredError, APIError
from .lib.fetcher import ContentFetcher
from .lib.sync_manager import SyncManager
from .lib.graph_builder import KnowledgeGraphBuilder


__version__ = '0.1.0'
__all__ = [
    'DingTalkScanner',
    'TokenExpiredError',
    'APIError',
    'ContentFetcher',
    'SyncManager',
    'KnowledgeGraphBuilder'
]


class KnowledgeGraphSync:
    """Main class for DingTalk knowledge graph synchronization"""
    
    def __init__(self, appkey: str, appsecret: str, storage_path: str = "./dingtalk_data"):
        """
        Initialize the sync manager
        
        Args:
            appkey: DingTalk app key
            appsecret: DingTalk app secret
            storage_path: Path to store synchronized data
        """
        self.appkey = appkey
        self.appsecret = appsecret
        self.storage_path = storage_path
        
        self.sync_manager = SyncManager(storage_path)
        self.scanner = None
        self.fetcher = None
    
    def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        import requests
        
        if self.sync_manager.is_token_valid():
            token = self.sync_manager.get_access_token()
        else:
            token_url = f"https://oapi.dingtalk.com/gettoken?appkey={self.appkey}&appsecret={self.appsecret}"
            response = requests.get(token_url)
            token_data = response.json()
            
            if token_data.get('errcode') != 0:
                raise APIError(
                    token_data.get('errcode', -1), 
                    token_data.get('errmsg', 'Failed to get token')
                )
            
            access_token = token_data['access_token']
            expires_in = token_data['expires_in']
            self.sync_manager.update_token(access_token, expires_in)
            token = access_token
        
        if self.scanner is None:
            self.scanner = DingTalkScanner(token)
            self.fetcher = ContentFetcher(self.scanner, self.storage_path)
    
    def scan(self, full: bool = False) -> list:
        """
        Scan knowledge bases
        
        Args:
            full: Perform full scan (default: incremental)
        
        Returns:
            List of document nodes
        """
        self._ensure_authenticated()
        
        last_sync_time = self.sync_manager.get_last_sync_time() if not full else None
        documents = self.scanner.scan_all(full_scan=full, last_sync_time=last_sync_time)
        
        self.sync_manager.update_sync_time(full_sync=full)
        return documents
    
    def fetch_content(self, documents: list, skip_existing: bool = True) -> list:
        """
        Fetch document content
        
        Args:
            documents: List of document nodes
            skip_existing: Skip already fetched documents
        
        Returns:
            List of documents with content
        """
        self._ensure_authenticated()
        return self.fetcher.fetch_batch(documents, skip_existing=skip_existing)
    
    def build_graph(self, documents: list = None) -> KnowledgeGraphBuilder:
        """
        Build knowledge graph
        
        Args:
            documents: List of documents (optional, will load from storage if not provided)
        
        Returns:
            KnowledgeGraphBuilder instance
        """
        if documents is None:
            documents = self.fetcher.get_all_documents()
        
        graph = KnowledgeGraphBuilder()
        graph.build(documents)
        return graph
    
    def sync(self, full: bool = False, build_graph: bool = True):
        """
        Perform full synchronization
        
        Args:
            full: Perform full scan
            build_graph: Build knowledge graph after sync
        """
        print("Step 1/3: Scanning...")
        documents = self.scan(full=full)
        
        print("Step 2/3: Fetching content...")
        self.fetch_content(documents)
        
        if build_graph:
            print("Step 3/3: Building graph...")
            graph = self.build_graph()
            graph_path = f"{self.storage_path}/graph/graph.json"
            graph.export_json(graph_path)
        
        print("Sync completed!")
    
    def get_status(self) -> dict:
        """Get sync status"""
        return self.sync_manager.get_statistics()
