"""
MaxKB API Client

与 MaxKB 知识库系统交互的客户端
支持知识库管理、文档上传、向量化、搜索等功能
"""

import requests
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MaxKBConfig:
    """MaxKB 配置"""
    base_url: str
    username: str
    password: str
    timeout: int = 30


class MaxKBError(Exception):
    """MaxKB API 错误"""
    
    def __init__(self, code: str, message: str, status_code: int = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(f"MaxKB Error [{code}]: {message}")


class MaxKBClient:
    """MaxKB API 客户端"""
    
    def __init__(self, config: MaxKBConfig):
        """
        初始化 MaxKB 客户端
        
        Args:
            config: MaxKB 配置
        """
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        self.session = requests.Session()
        self.token = None
        
        # 自动登录
        self._login()
    
    def _login(self):
        """登录 MaxKB 获取 Token"""
        logger.info(f"Logging in to MaxKB: {self.base_url}")
        
        url = f"{self.base_url}/api/login"
        response = self.session.post(
            url,
            json={
                "username": self.config.username,
                "password": self.config.password
            },
            timeout=self.config.timeout
        )
        
        if response.status_code != 200:
            raise MaxKBError(
                code="AUTH_FAILED",
                message=f"登录失败：{response.text}",
                status_code=response.status_code
            )
        
        data = response.json()
        self.token = data.get('access_token')
        
        if not self.token:
            raise MaxKBError(
                code="NO_TOKEN",
                message="未获取到访问 Token"
            )
        
        # 设置认证头
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })
        
        logger.info("MaxKB login successful")
    
    def _ensure_authenticated(self):
        """确保已认证"""
        if not self.token:
            self._login()
    
    def create_dataset(self, 
                      name: str, 
                      description: str = "",
                      dataset_type: str = "GENERAL") -> Dict:
        """
        创建知识库
        
        Args:
            name: 知识库名称
            description: 描述
            dataset_type: 类型 (GENERAL 或 AUTO)
        
        Returns:
            知识库信息
        """
        self._ensure_authenticated()
        
        url = f"{self.base_url}/api/v1/dataset"
        payload = {
            "name": name,
            "description": description,
            "type": dataset_type
        }
        
        response = self.session.post(url, json=payload, timeout=self.config.timeout)
        
        if response.status_code not in [200, 201]:
            raise MaxKBError(
                code="CREATE_DATASET_FAILED",
                message=f"创建知识库失败：{response.text}",
                status_code=response.status_code
            )
        
        return response.json()
    
    def get_dataset(self, dataset_id: str) -> Dict:
        """获取知识库详情"""
        self._ensure_authenticated()
        
        url = f"{self.base_url}/api/v1/dataset/{dataset_id}"
        response = self.session.get(url, timeout=self.config.timeout)
        
        if response.status_code != 200:
            raise MaxKBError(
                code="GET_DATASET_FAILED",
                message=f"获取知识库失败：{response.text}",
                status_code=response.status_code
            )
        
        return response.json()
    
    def list_datasets(self, name: str = None) -> List[Dict]:
        """
        获取知识库列表
        
        Args:
            name: 按名称过滤
        
        Returns:
            知识库列表
        """
        self._ensure_authenticated()
        
        url = f"{self.base_url}/api/v1/dataset"
        params = {}
        if name:
            params['name'] = name
        
        response = self.session.get(url, params=params, timeout=self.config.timeout)
        
        if response.status_code != 200:
            raise MaxKBError(
                code="LIST_DATASETS_FAILED",
                message=f"获取知识库列表失败：{response.text}",
                status_code=response.status_code
            )
        
        data = response.json()
        return data.get('datasets', [])
    
    def find_or_create_dataset(self, 
                               name: str, 
                               description: str = "") -> Dict:
        """
        查找或创建知识库
        
        Args:
            name: 知识库名称
            description: 描述
        
        Returns:
            知识库信息
        """
        # 先查找
        datasets = self.list_datasets(name=name)
        
        if datasets:
            logger.info(f"Found existing dataset: {name}")
            return datasets[0]
        
        # 不存在则创建
        logger.info(f"Creating new dataset: {name}")
        return self.create_dataset(name, description)
    
    def upload_document(self, 
                       dataset_id: str, 
                       file_path: str, 
                       name: str = None) -> Dict:
        """
        上传文档文件
        
        Args:
            dataset_id: 知识库 ID
            file_path: 文件路径
            name: 文件名 (可选)
        
        Returns:
            上传结果
        """
        self._ensure_authenticated()
        
        if not name:
            name = Path(file_path).name
        
        url = f"{self.base_url}/api/v1/dataset/{dataset_id}/document"
        
        # 判断文件类型
        suffix = Path(file_path).suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.md': 'text/markdown'
        }
        
        mime_type = mime_types.get(suffix, 'application/octet-stream')
        
        with open(file_path, 'rb') as f:
            files = {'file': (name, f, mime_type)}
            data = {'name': name}
            
            response = self.session.post(
                url,
                files=files,
                data=data,
                timeout=self.config.timeout
            )
        
        if response.status_code not in [200, 201]:
            raise MaxKBError(
                code="UPLOAD_DOCUMENT_FAILED",
                message=f"上传文档失败：{response.text}",
                status_code=response.status_code
            )
        
        return response.json()
    
    def upload_text(self, 
                   dataset_id: str, 
                   title: str, 
                   content: str,
                   tags: List[str] = None) -> Dict:
        """
        上传文本内容到向量库
        
        Args:
            dataset_id: 知识库 ID
            title: 标题
            content: 内容
            tags: 标签列表
        
        Returns:
            上传结果
        """
        self._ensure_authenticated()
        
        url = f"{self.base_url}/api/v1/dataset/{dataset_id}/document/paragraph"
        payload = {
            "title": title,
            "content": content,
            "tags": tags or []
        }
        
        response = self.session.post(
            url,
            json=payload,
            timeout=self.config.timeout
        )
        
        if response.status_code not in [200, 201]:
            raise MaxKBError(
                code="UPLOAD_TEXT_FAILED",
                message=f"上传文本失败：{response.text}",
                status_code=response.status_code
            )
        
        return response.json()
    
    def search(self, 
              query: str,
              dataset_ids: List[str] = None,
              top_k: int = 3) -> List[Dict]:
        """
        搜索知识
        
        Args:
            query: 搜索查询
            dataset_ids: 知识库 ID 列表
            top_k: 返回数量
        
        Returns:
            搜索结果列表
        """
        self._ensure_authenticated()
        
        url = f"{self.base_url}/api/v1/knowledge/search"
        payload = {
            "query": query,
            "top_k": top_k
        }
        
        if dataset_ids:
            payload["dataset_ids"] = dataset_ids
        
        response = self.session.post(
            url,
            json=payload,
            timeout=self.config.timeout
        )
        
        if response.status_code != 200:
            raise MaxKBError(
                code="SEARCH_FAILED",
                message=f"搜索失败：{response.text}",
                status_code=response.status_code
            )
        
        return response.json()
    
    def list_documents(self, 
                      dataset_id: str,
                      tag: str = None) -> List[Dict]:
        """
        获取文档列表
        
        Args:
            dataset_id: 知识库 ID
            tag: 按标签过滤
        
        Returns:
            文档列表
        """
        self._ensure_authenticated()
        
        url = f"{self.base_url}/api/v1/dataset/{dataset_id}/document"
        params = {}
        if tag:
            params['tag'] = tag
        
        response = self.session.get(
            url,
            params=params,
            timeout=self.config.timeout
        )
        
        if response.status_code != 200:
            raise MaxKBError(
                code="LIST_DOCUMENTS_FAILED",
                message=f"获取文档列表失败：{response.text}",
                status_code=response.status_code
            )
        
        return response.json()
    
    def delete_document(self, document_id: str) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档 ID
        
        Returns:
            是否成功
        """
        self._ensure_authenticated()
        
        url = f"{self.base_url}/api/v1/dataset/document/{document_id}"
        response = self.session.delete(url, timeout=self.config.timeout)
        
        return response.status_code == 200
    
    def delete_by_tag(self, 
                     dataset_id: str,
                     tag: str,
                     dry_run: bool = False) -> int:
        """
        按标签删除文档
        
        Args:
            dataset_id: 知识库 ID
            tag: 标签名称
            dry_run: 只预览不执行
        
        Returns:
            删除的文档数量
        """
        # 获取带标签的文档
        documents = self.list_documents(dataset_id, tag=tag)
        
        if not documents:
            logger.info(f"No documents found with tag: {tag}")
            return 0
        
        if dry_run:
            logger.info(f"Would delete {len(documents)} documents with tag: {tag}")
            return len(documents)
        
        # 删除文档
        deleted_count = 0
        for doc in documents:
            try:
                if self.delete_document(doc['id']):
                    deleted_count += 1
                    logger.debug(f"Deleted document: {doc.get('name', doc['id'])}")
            except Exception as e:
                logger.error(f"Failed to delete {doc['id']}: {e}")
        
        logger.info(f"Deleted {deleted_count} documents with tag: {tag}")
        return deleted_count
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        self._ensure_authenticated()
        
        # 获取所有知识库
        datasets = self.list_datasets()
        
        stats = {
            'total_datasets': len(datasets),
            'datasets': [],
            'total_documents': 0,
            'total_paragraphs': 0
        }
        
        for dataset in datasets:
            try:
                dataset_info = self.get_dataset(dataset['id'])
                doc_count = dataset_info.get('document_count', 0)
                para_count = dataset_info.get('paragraph_count', 0)
                
                stats['datasets'].append({
                    'id': dataset['id'],
                    'name': dataset['name'],
                    'documents': doc_count,
                    'paragraphs': para_count
                })
                
                stats['total_documents'] += doc_count
                stats['total_paragraphs'] += para_count
                
            except Exception as e:
                logger.warning(f"Failed to get stats for {dataset['name']}: {e}")
        
        return stats
