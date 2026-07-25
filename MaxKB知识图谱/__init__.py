"""
MaxKB Knowledge Graph Sync

Main module for syncing DingTalk knowledge bases to MaxKB
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path

from .lib.maxkb_client import MaxKBClient, MaxKBConfig
from .lib.scanner import DingTalkScanner, TokenExpiredError
from .lib.classifier import DataClassifier, DataCategory

logger = logging.getLogger(__name__)


class KnowledgeGraphSync:
    """钉钉知识库到 MaxKB 的同步器"""
    
    def __init__(self,
                 maxkb_base_url: str,
                 maxkb_username: str,
                 maxkb_password: str,
                 dingtalk_appkey: str,
                 dingtalk_appsecret: str,
                 dataset_name: str = "支持部测试",
                 tag_name: str = "支持部测试",
                 storage_path: str = "./maxkb_data"):
        """
        初始化同步器
        
        Args:
            maxkb_base_url: MaxKB 基础 URL
            maxkb_username: MaxKB 用户名
            maxkb_password: MaxKB 密码
            dingtalk_appkey: 钉钉 AppKey
            dingtalk_appsecret: 钉钉 AppSecret
            dataset_name: 知识库名称
            tag_name: 标签名称
            storage_path: 存储路径
        """
        # MaxKB 配置
        self.maxkb_config = MaxKBConfig(
            base_url=maxkb_base_url,
            username=maxkb_username,
            password=maxkb_password
        )
        
        # 钉钉配置
        self.dingtalk_appkey = dingtalk_appkey
        self.dingtalk_appsecret = dingtalk_appsecret
        
        # 知识库配置
        self.dataset_name = dataset_name
        self.tag_name = tag_name
        self.storage_path = Path(storage_path)
        
        # 确保存储目录存在
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化客户端
        self.maxkb_client = MaxKBClient(self.maxkb_config)
        self.dataset = None
        
        # 分类器
        self.classifier = DataClassifier()
        
        # 统计信息
        self.statistics = {
            'total_scanned': 0,
            'structured_count': 0,
            'unstructured_count': 0,
            'uploaded_count': 0,
            'failed_count': 0
        }
    
    def _ensure_dataset(self):
        """确保知识库存在"""
        if self.dataset is None:
            logger.info(f"Finding or creating dataset: {self.dataset_name}")
            self.dataset = self.maxkb_client.find_or_create_dataset(
                name=self.dataset_name,
                description=f"从钉钉同步的知识库 - {self.dataset_name}"
            )
            logger.info(f"Dataset: {self.dataset['name']} (ID: {self.dataset['id']})")
    
    def scan_dingtalk(self, 
                     incremental: bool = True,
                     last_sync_time: Optional[int] = None) -> List[Dict]:
        """
        扫描钉钉知识库
        
        Args:
            incremental: 是否增量扫描
            last_sync_time: 上次同步时间
        
        Returns:
            文档列表
        """
        logger.info("Scanning DingTalk knowledge bases...")
        
        try:
            # 获取钉钉 Token
            import requests
            token_url = f"https://oapi.dingtalk.com/gettoken?appkey={self.dingtalk_appkey}&appsecret={self.dingtalk_appsecret}"
            response = requests.get(token_url)
            token_data = response.json()
            
            if token_data.get('errcode') != 0:
                raise Exception(f"获取钉钉 Token 失败：{token_data.get('errmsg')}")
            
            access_token = token_data['access_token']
            
            # 创建扫描器
            scanner = DingTalkScanner(access_token)
            
            # 执行扫描
            documents = scanner.scan_all(
                full_scan=not incremental,
                last_sync_time=last_sync_time
            )
            
            logger.info(f"Scanned {len(documents)} documents from DingTalk")
            self.statistics['total_scanned'] = len(documents)
            
            return documents
            
        except TokenExpiredError:
            logger.error("DingTalk token expired")
            raise
        except Exception as e:
            logger.error(f"Failed to scan DingTalk: {e}")
            raise
    
    def classify_documents(self, 
                          documents: List[Dict]) -> Dict[str, List[Dict]]:
        """
        分类文档
        
        Args:
            documents: 文档列表
        
        Returns:
            分类后的文档字典
        """
        logger.info(f"Classifying {len(documents)} documents...")
        
        classified = {
            'STRUCTURED': [],
            'UNSTRUCTURED': [],
            'SEMI_STRUCTURED': []
        }
        
        for doc in documents:
            result = self.classifier.classify(doc)
            category_name = result.category.value
            
            classified[category_name].append({
                'document': doc,
                'classification': result
            })
            
            logger.debug(f"Classified '{doc.get('metadata', {}).get('name', 'Unknown')}': {category_name}")
        
        self.statistics['structured_count'] = len(classified['STRUCTURED'])
        self.statistics['unstructured_count'] = len(classified['UNSTRUCTURED'])
        self.statistics['semi_structured_count'] = len(classified['SEMI_STRUCTURED'])
        
        logger.info(f"Classification results:")
        logger.info(f"  Structured: {len(classified['STRUCTURED'])}")
        logger.info(f"  Unstructured: {len(classified['UNSTRUCTURED'])}")
        logger.info(f"  Semi-structured: {len(classified['SEMI_STRUCTURED'])}")
        
        return classified
    
    def build_graph(self, 
                   structured_docs: List[Dict],
                   export_path: str = None):
        """
        构建结构化数据的知识图谱
        
        Args:
            structured_docs: 结构化文档列表
            export_path: 导出路径
        """
        logger.info(f"Building knowledge graph from {len(structured_docs)} structured documents...")
        
        # TODO: 实现知识图谱构建
        # 目前将结构化数据也上传到向量库，添加结构化标签
        
        for item in structured_docs:
            doc = item['document']
            metadata = doc.get('metadata', {})
            
            # 添加结构化标签
            tags = [self.tag_name, 'structured']
            
            kb_name = metadata.get('knowledgeBaseName', '')
            if kb_name:
                tags.append(kb_name)
            
            # 上传到 MaxKB
            try:
                self.maxkb_client.upload_text(
                    dataset_id=self.dataset['id'],
                    title=f"[结构化] {metadata.get('title', metadata.get('name', 'Untitled'))}",
                    content=doc.get('content', ''),
                    tags=tags
                )
                
                self.statistics['uploaded_count'] += 1
                logger.debug(f"Uploaded structured doc: {metadata.get('name')}")
                
            except Exception as e:
                self.statistics['failed_count'] += 1
                logger.error(f"Failed to upload {metadata.get('name')}: {e}")
        
        logger.info(f"Knowledge graph built: {len(structured_docs)} documents processed")
    
    def upload_vectors(self, 
                      unstructured_docs: List[Dict]):
        """
        上传非结构化数据到向量库
        
        Args:
            unstructured_docs: 非结构化文档列表
        """
        logger.info(f"Uploading {len(unstructured_docs)} unstructured documents to vector DB...")
        
        self._ensure_dataset()
        
        for item in unstructured_docs:
            doc = item['document']
            metadata = doc.get('metadata', {})
            content = doc.get('content', '')
            
            # 生成标签
            tags = [self.tag_name, 'unstructured']
            
            kb_name = metadata.get('knowledgeBaseName', '')
            if kb_name:
                tags.append(kb_name)
            
            # 切分为 chunks
            chunks = self.classifier.generate_chunks(content)
            
            # 上传每个 chunk
            for chunk in chunks:
                try:
                    self.maxkb_client.upload_text(
                        dataset_id=self.dataset['id'],
                        title=f"{metadata.get('title', 'Untitled')} (Part {chunk['index'] + 1})",
                        content=chunk['content'],
                        tags=tags + [f'chunk_{chunk["index"]}']
                    )
                    
                    self.statistics['uploaded_count'] += 1
                    
                except Exception as e:
                    self.statistics['failed_count'] += 1
                    logger.error(f"Failed to upload chunk: {e}")
        
        logger.info(f"Vector upload completed: {self.statistics['uploaded_count']} uploaded")
    
    def sync(self, 
            incremental: bool = True,
            build_graph: bool = True,
            upload_vector: bool = True):
        """
        完整同步流程
        
        Args:
            incremental: 增量同步
            build_graph: 构建知识图谱
            upload_vector: 上传向量库
        """
        logger.info("Starting full sync...")
        
        # 1. 扫描钉钉
        documents = self.scan_dingtalk(incremental=incremental)
        
        if not documents:
            logger.info("No documents to sync")
            return
        
        # 2. 确保知识库存在
        self._ensure_dataset()
        
        # 3. 分类
        classified = self.classify_documents(documents)
        
        # 4. 构建知识图谱/上传结构化数据
        if build_graph and classified['STRUCTURED']:
            self.build_graph(classified['STRUCTURED'])
        
        # 5. 上传非结构化数据到向量库
        if upload_vector and classified['UNSTRUCTURED']:
            self.upload_vectors(classified['UNSTRUCTURED'])
        
        # 6. 处理半结构化数据 (作为非结构化处理)
        if upload_vector and classified['SEMI_STRUCTURED']:
            logger.info(f"Processing {len(classified['SEMI_STRUCTURED'])} semi-structured documents...")
            self.upload_vectors(classified['SEMI_STRUCTURED'])
        
        # 7. 打印统计
        self._print_statistics()
    
    def delete_by_tag(self, 
                     tag: str = None,
                     dry_run: bool = False) -> int:
        """
        按标签删除数据
        
        Args:
            tag: 标签名称 (默认使用配置的标签)
            dry_run: 只预览不执行
        
        Returns:
            删除的数量
        """
        tag = tag or self.tag_name
        logger.info(f"{'Would delete' if dry_run else 'Deleting'} documents with tag: {tag}")
        
        self._ensure_dataset()
        
        deleted = self.maxkb_client.delete_by_tag(
            dataset_id=self.dataset['id'],
            tag=tag,
            dry_run=dry_run
        )
        
        logger.info(f"{'Would delete' if dry_run else 'Deleted'} {deleted} documents")
        return deleted
    
    def search(self, 
              query: str,
              top_k: int = 5) -> List[Dict]:
        """
        搜索知识
        
        Args:
            query: 搜索查询
            top_k: 返回数量
        
        Returns:
            搜索结果
        """
        self._ensure_dataset()
        
        results = self.maxkb_client.search(
            query=query,
            dataset_ids=[self.dataset['id']],
            top_k=top_k
        )
        
        logger.info(f"Search '{query}': found {len(results)} results")
        return results
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        self._ensure_dataset()
        
        maxkb_stats = self.maxkb_client.get_statistics()
        
        return {
            **self.statistics,
            'dataset_name': self.dataset_name,
            'dataset_id': self.dataset.get('id'),
            'maxkb_stats': maxkb_stats
        }
    
    def _print_statistics(self):
        """打印统计信息"""
        print("\n" + "="*60)
        print("Sync Statistics")
        print("="*60)
        print(f"Dataset: {self.dataset_name}")
        print(f"Total Scanned: {self.statistics['total_scanned']}")
        print(f"Structured: {self.statistics['structured_count']}")
        print(f"Unstructured: {self.statistics['unstructured_count']}")
        print(f"Uploaded: {self.statistics['uploaded_count']}")
        print(f"Failed: {self.statistics['failed_count']}")
        print("="*60 + "\n")
