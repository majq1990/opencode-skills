import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json

@dataclass
class RedmineConfig:
    url: str = "https://faq.egova.com.cn:7787"
    api_key: str = "a687d1fc20e3953a9a2796e0c2b7b54c0a754283"
    project: str = "redmine"
    backup_url: Optional[str] = "https://faq.egova.com.cn:7789"

@dataclass
class MaxKBConfig:
    url: str = "http://111.4.141.154:18080"
    username: str = "egova-jszc"
    password: str = "eGova@2026"

@dataclass
class FilterStrategy:
    min_score: int = 60
    active_days: int = 365
    status_filter: str = "Active"
    max_count: int = 0

@dataclass
class ProductMapping:
    name: str
    keywords: List[str]
    
PRODUCT_MAPPINGS: Dict[str, ProductMapping] = {
    "麒舰": ProductMapping("麒舰", ["麒舰", "麒舰FAQ"]),
    "灵珑": ProductMapping("灵珑", ["灵珑"]),
    "明镜": ProductMapping("明镜", ["明镜"]),
    "全行业一体化": ProductMapping("全行业一体化", ["全行业一体化"]),
    "星桥": ProductMapping("星桥", ["星桥", "星桥项目"]),
    "物联网": ProductMapping("物联网", ["物联网", "IoT"]),
    "悟空": ProductMapping("悟空", ["悟空"]),
    "GIS": ProductMapping("GIS", ["GIS", "GIS_FAQ"]),
    "市民通": ProductMapping("市民通", ["市民通", "市民通配置", "市民通FAQ"]),
    "执法": ProductMapping("执法", ["执法", "执法应用", "执法办案", "执法实施"]),
    "智信": ProductMapping("智信", ["智信", "智信FAQ", "智信配置"]),
    "智云": ProductMapping("智云", ["智云", "智云功能", "智云FAQ", "智云子系统"]),
    "环卫": ProductMapping("环卫", ["环卫", "环卫FAQ", "环卫_"]),
    "市政": ProductMapping("市政", ["市政", "市政FAQ"]),
    "渣土": ProductMapping("渣土", ["渣土", "渣土系统"]),
    "排水": ProductMapping("排水", ["排水", "排水FAQ"]),
    "园林": ProductMapping("园林", ["园林", "园林FAQ"]),
    "多网": ProductMapping("多网", ["多网", "多网FAQ"]),
    "数据采集": ProductMapping("数据采集", ["数据采集"]),
    "视频上报": ProductMapping("视频上报", ["视频上报"]),
}

class Config:
    def __init__(self):
        self.redmine = RedmineConfig()
        self.maxkb = MaxKBConfig()
        self.filter = FilterStrategy()
        self.product_mappings = PRODUCT_MAPPINGS
        self.output_dir = Path("D:/opencode/file")
        self.cache_dir = Path.home() / ".sisyphus" / "evidence"
        self._load_from_env()
        
    def _load_from_env(self):
        if os.getenv("REDMINE_URL"):
            self.redmine.url = os.getenv("REDMINE_URL", "")
        if os.getenv("REDMINE_API_KEY"):
            self.redmine.api_key = os.getenv("REDMINE_API_KEY", "")
        if os.getenv("REDMINE_BACKUP_URL"):
            self.redmine.backup_url = os.getenv("REDMINE_BACKUP_URL")
        if os.getenv("MAXKB_URL"):
            self.maxkb.url = os.getenv("MAXKB_URL", "")
        if os.getenv("MAXKB_USERNAME"):
            self.maxkb.username = os.getenv("MAXKB_USERNAME", "")
        if os.getenv("MAXKB_PASSWORD"):
            self.maxkb.password = os.getenv("MAXKB_PASSWORD", "")
            
    def load_from_file(self, path: Path):
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                if "redmine" in data:
                    rd = data["redmine"]
                    self.redmine.url = rd.get("url", self.redmine.url)
                    self.redmine.api_key = rd.get("api_key", self.redmine.api_key)
                    self.redmine.project = rd.get("project", self.redmine.project)
                    self.redmine.backup_url = rd.get("backup_url", self.redmine.backup_url)
                if "maxkb" in data:
                    md = data["maxkb"]
                    self.maxkb.url = md.get("url", self.maxkb.url)
                    self.maxkb.username = md.get("username", self.maxkb.username)
                    self.maxkb.password = md.get("password", self.maxkb.password)
                if "filter" in data:
                    fd = data["filter"]
                    self.filter.min_score = fd.get("min_score", self.filter.min_score)
                    self.filter.active_days = fd.get("active_days", self.filter.active_days)
                    self.filter.status_filter = fd.get("status_filter", self.filter.status_filter)
                    
    def save_to_file(self, path: Path):
        data = {
            "redmine": {
                "url": self.redmine.url,
                "api_key": self.redmine.api_key,
                "project": self.redmine.project,
                "backup_url": self.redmine.backup_url
            },
            "maxkb": {
                "url": self.maxkb.url,
                "username": self.maxkb.username,
                "password": "***"
            },
            "filter": {
                "min_score": self.filter.min_score,
                "active_days": self.filter.active_days,
                "status_filter": self.filter.status_filter
            }
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)