"""
Redmine Wiki to MaxKB Sync Skill

从 Redmine Wiki 分析提取活跃文档，推送到 MaxKB 知识库。
"""

__version__ = "1.0.0"
__author__ = "OpenCode"

from .lib.config import Config, PRODUCT_MAPPINGS
from .lib.redmine_client import RedmineClient, WikiPage
from .lib.maxkb_client import MaxKBClient
from .lib.converter import HTMLToMarkdownConverter, save_as_markdown

__all__ = [
    'Config',
    'PRODUCT_MAPPINGS',
    'RedmineClient',
    'WikiPage', 
    'MaxKBClient',
    'HTMLToMarkdownConverter',
    'save_as_markdown'
]
