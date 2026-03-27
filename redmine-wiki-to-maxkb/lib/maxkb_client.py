"""
MaxKB API 客户端
"""
import requests
from typing import List, Dict, Optional
from pathlib import Path
import time

class MaxKBClient:
    """MaxKB API 客户端"""
    
    def __init__(self, url: str, username: str, password: str):
        self.base_url = url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.logged_in = False
        
    def login(self) -> bool:
        """登录 MaxKB"""
        url = f"{self.base_url}/api/user/login"
        resp = self.session.post(url, json={
            "username": self.username,
            "password": self.password
        })
        
        if resp.json().get("code") == 200:
            self.logged_in = True
            print(f"[MaxKB] Login successful: {self.username}")
            return True
        else:
            print(f"[MaxKB] Login failed: {resp.json()}")
            return False
    
    def get_datasets(self) -> List[Dict]:
        """获取知识库列表"""
        if not self.logged_in:
            return []
            
        url = f"{self.base_url}/api/dataset"
        resp = self.session.get(url)
        
        if resp.json().get("code") == 200:
            return resp.json().get("data", [])
        return []
    
    def get_dataset_by_name(self, name: str) -> Optional[Dict]:
        """按名称查找知识库"""
        datasets = self.get_datasets()
        for ds in datasets:
            if ds.get("name") == name:
                return ds
        return None
    
    def create_dataset(self, name: str, desc: str = "") -> Optional[str]:
        """创建知识库"""
        url = f"{self.base_url}/api/dataset"
        resp = self.session.post(url, json={
            "name": name,
            "desc": desc,
            "type": "0"  # 0=普通知识库
        })
        
        result = resp.json()
        if result.get("code") == 200:
            dataset_id = result.get("data", {}).get("id")
            print(f"[MaxKB] Created dataset: {name} (ID: {dataset_id})")
            return dataset_id
        else:
            print(f"[MaxKB] Create failed: {result}")
            return None
    
    def get_or_create_dataset(self, name: str, desc: str = "") -> Optional[str]:
        """获取或创建知识库"""
        # 先查找现有
        existing = self.get_dataset_by_name(name)
        if existing:
            print(f"[MaxKB] Using existing dataset: {name}")
            return existing.get("id")
        
        # 创建新的
        return self.create_dataset(name, desc)
    
    def upload_document(self, dataset_id: str, file_path: Path, name: Optional[str] = None) -> bool:
        """上传文档"""
        url = f"{self.base_url}/api/dataset/{dataset_id}/document"
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (name or file_path.name, f, 'text/markdown')}
                data = {
                    'name': name or file_path.stem,
                    'dataset_id': dataset_id
                }
                resp = self.session.post(url, files=files, data=data)
            
            return resp.json().get("code") == 200
        except Exception as e:
            print(f"[MaxKB] Upload failed: {e}")
            return False
    
    def batch_upload(self, dataset_id: str, files: List[Path], batch_size: int = 10) -> Dict:
        """批量上传文档"""
        success = 0
        failed = 0
        
        for i, file_path in enumerate(files, 1):
            if self.upload_document(dataset_id, file_path):
                success += 1
                print(f"    [{i}/{len(files)}] [OK] {file_path.name}")
            else:
                failed += 1
                print(f"    [{i}/{len(files)}] [FAIL] {file_path.name}")
            
            # 批次间隔
            if i % batch_size == 0:
                time.sleep(1)
        
        return {"success": success, "failed": failed}
