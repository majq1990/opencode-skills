"""
Redmine API 客户端
支持主服务器和备份服务器自动切换
"""
import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import time
import re
import warnings
warnings.filterwarnings('ignore')

@dataclass
class WikiPage:
    """Wiki 页面"""
    title: str
    parent: Optional[str]
    version: int
    updated_on: str
    created_on: str
    text: Optional[str] = None
    score: int = 0
    status: str = "Unknown"
    project_id: Optional[int] = None
    project_name: Optional[str] = None

@dataclass
class IssueInfo:
    """案件信息"""
    id: int
    subject: str
    project: str
    status: str
    author: str
    assigned_to: Optional[str] = None
    created_on: str = ""
    updated_on: str = ""
    description: str = ""
    done_ratio: int = 0
    journals: List[Dict] = field(default_factory=list)
    linglong_forms: Dict[str, Any] = field(default_factory=dict)
    source: str = "primary"  # primary 或 backup

# 灵珑表单类型定义
LINGLONG_FORMS = {
    "single": [
        "form_demand_analysis",      # 需求分析
        "form_product_design",       # 产品设计
        "form_develop_design",       # 研发设计
        "form_develop_finish",       # 研发完成
        "form_product_verify",       # 产品验证
        "form_tester_verify",        # 测试验证
    ],
    "multi": [
        "form_demand_analysis_audit",    # 需求审核
        "form_product_design_audit",     # 产品设计审核
        "form_develop_design_audit",     # 研发设计审核
        "form_demand_analysis_review",   # 需求审核抽查
    ]
}

class RedmineClient:
    """Redmine API 客户端，支持主备服务器切换"""
    
    def __init__(
        self, 
        url: str, 
        api_key: str, 
        project: str = "redmine",
        backup_url: Optional[str] = None
    ):
        self.base_url = url.rstrip('/')
        self.api_key = api_key
        self.project = project
        self.backup_url = backup_url.rstrip('/') if backup_url else None
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-Redmine-API-Key': api_key,
            'Content-Type': 'application/json'
        })
        self.session.verify = False
        
    def _make_request(
        self, 
        endpoint: str, 
        use_backup: bool = False,
        timeout: int = 30,
        retries: int = 3
    ) -> Optional[Dict]:
        """
        发送请求，支持自动切换到备份服务器
        
        Args:
            endpoint: API 端点（如 /issues/123.json）
            use_backup: 是否使用备份服务器
            timeout: 超时时间
            retries: 重试次数
            
        Returns:
            JSON 响应数据，失败返回 None
        """
        urls_to_try = []
        
        if use_backup and self.backup_url:
            urls_to_try = [self.backup_url]
        else:
            urls_to_try = [self.base_url]
            if self.backup_url:
                urls_to_try.append(self.backup_url)
        
        last_error = None
        for url in urls_to_try:
            full_url = f"{url}{endpoint}"
            
            for attempt in range(retries):
                try:
                    resp = self.session.get(full_url, timeout=timeout)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        # 标记数据来源
                        if '__source__' not in data:
                            data['__source__'] = 'backup' if url == self.backup_url else 'primary'
                        return data
                    elif resp.status_code == 404:
                        # 404 表示数据不存在，尝试下一个 URL
                        break
                    elif resp.status_code == 401:
                        print(f"    [ERROR] 认证失败: {full_url}")
                        return None
                    else:
                        last_error = f"HTTP {resp.status_code}"
                        
                except requests.exceptions.Timeout:
                    last_error = "Timeout"
                except requests.exceptions.ConnectionError:
                    last_error = "ConnectionError"
                except Exception as e:
                    last_error = str(e)
                    
                time.sleep(0.5 * (attempt + 1))
        
        return None
    
    def get_wiki_list(self) -> List[Dict]:
        """获取 Wiki 列表"""
        data = self._make_request(f"/projects/{self.project}/wiki/index.json")
        return data.get('wiki_pages', []) if data else []
    
    def get_wiki_page(self, title: str) -> Optional[Dict]:
        """获取单个 Wiki 页面内容"""
        import urllib.parse
        encoded_title = urllib.parse.quote(title)
        data = self._make_request(f"/projects/{self.project}/wiki/{encoded_title}.json?include=attachments")
        return data.get('wiki_page') if data else None
    
    def get_issue(
        self, 
        issue_id: int,
        include_journals: bool = True,
        include_linglong: bool = True
    ) -> Optional[IssueInfo]:
        """
        获取案件信息，支持主备服务器自动切换
        
        Args:
            issue_id: 案件 ID
            include_journals: 是否包含批转记录
            include_linglong: 是否包含灵珑表单
            
        Returns:
            IssueInfo 对象，失败返回 None
        """
        # 构建请求 URL
        includes = ["children", "attachments", "relations", "changesets"]
        if include_journals:
            includes.append("journals")
            includes.append("watchers")
        
        endpoint = f"/issues/{issue_id}.json?include={','.join(includes)}"
        data = self._make_request(endpoint)
        
        if not data:
            return None
        
        issue_data = data.get('issue', {})
        source = data.get('__source__', 'primary')
        
        # 构建 IssueInfo
        issue = IssueInfo(
            id=issue_id,
            subject=issue_data.get('subject', 'N/A'),
            project=issue_data.get('project', {}).get('name', 'N/A'),
            status=issue_data.get('status', {}).get('name', 'N/A'),
            author=issue_data.get('author', {}).get('name', 'N/A'),
            assigned_to=issue_data.get('assigned_to', {}).get('name') if issue_data.get('assigned_to') else None,
            created_on=issue_data.get('created_on', ''),
            updated_on=issue_data.get('updated_on', ''),
            description=issue_data.get('description', ''),
            done_ratio=issue_data.get('done_ratio', 0),
            journals=issue_data.get('journals', [])[:15],  # 最多15条批转记录
            source=source
        )
        
        # 获取灵珑表单
        if include_linglong:
            issue.linglong_forms = self._fetch_linglong_forms(issue_id)
        
        return issue
    
    def _fetch_linglong_forms(self, issue_id: int) -> Dict[str, Any]:
        """获取灵珑表单详情"""
        forms = {}
        
        all_forms = LINGLONG_FORMS["single"] + LINGLONG_FORMS["multi"]
        
        for form_type in all_forms:
            endpoint = f"/issues/{issue_id}/linglong_forms?form={form_type}"
            data = self._make_request(endpoint, timeout=10)
            
            if data and data.get('success') and data.get('data'):
                forms[form_type] = {
                    'name': data.get('name', form_type),
                    'multi_record': data.get('multi_record', False),
                    'data': data.get('data')
                }
        
        return forms
    
    def fetch_all_wikis(self, limit: int = 0) -> List[WikiPage]:
        """获取所有 Wiki 页面"""
        print(f"[Redmine] Fetching wiki list from {self.base_url}...")
        wiki_list = self.get_wiki_list()
        print(f"[Redmine] Found {len(wiki_list)} wiki pages")
        
        pages = []
        for i, wiki in enumerate(wiki_list):
            if limit > 0 and i >= limit:
                break
            pages.append(WikiPage(
                title=wiki.get('title', ''),
                parent=wiki.get('parent', {}).get('title') if wiki.get('parent') else None,
                version=wiki.get('version', 1),
                updated_on=wiki.get('updated_on', ''),
                created_on=wiki.get('created_on', '')
            ))
            
            if (i + 1) % 500 == 0:
                print(f"[Redmine] Processed {i+1}/{len(wiki_list)} pages...")
                
        return pages
    
    def fetch_wiki_content(
        self, 
        pages: List[WikiPage], 
        delay: float = 0.1
    ) -> List[WikiPage]:
        """获取 Wiki 页面内容"""
        print(f"[Redmine] Fetching content for {len(pages)} pages...")
        
        success = 0
        for i, page in enumerate(pages):
            content = self.get_wiki_page(page.title)
            if content:
                page.text = content.get('text', '')
                page.version = content.get('version', page.version)
                page.project_id = content.get('project_id')
                success += 1
            time.sleep(delay)
            
            if (i + 1) % 50 == 0:
                print(f"[Redmine] Fetched {i+1}/{len(pages)} pages ({success} successful)...")
                
        print(f"[Redmine] Completed: {success}/{len(pages)} pages fetched")
        return pages
    
    def extract_issue_ids_from_wiki(self, wiki_text: str) -> List[int]:
        """
        从 Wiki 文本中提取案件 ID
        
        支持格式：
        - #12345
        - issues/12345
        - /issues/12345
        """
        if not wiki_text:
            return []
        
        pattern = r'(?:#(\d{5,})|/issues/(\d+)|issues/(\d+))'
        matches = re.findall(pattern, wiki_text)
        
        ids = set()
        for match in matches:
            for group in match:
                if group and group.isdigit():
                    ids.add(int(group))
        
        return sorted(ids)
    
    def fetch_issues_from_wikis(
        self,
        wiki_pages: List[WikiPage],
        max_issues: int = 0,
        delay: float = 0.2
    ) -> List[IssueInfo]:
        """
        从 Wiki 中提取案件 ID 并获取案件信息
        
        Args:
            wiki_pages: Wiki 页面列表
            max_issues: 最大案件数（0=无限制）
            delay: 请求间隔
            
        Returns:
            IssueInfo 列表
        """
        # 提取所有案件 ID
        all_issue_ids = set()
        for page in wiki_pages:
            if page.text:
                ids = self.extract_issue_ids_from_wiki(page.text)
                all_issue_ids.update(ids)
        
        print(f"[Redmine] Found {len(all_issue_ids)} unique issue IDs in wikis")
        
        # 获取案件信息
        issues = []
        failed = []
        from_backup = 0
        
        for i, issue_id in enumerate(sorted(all_issue_ids)):
            if max_issues > 0 and i >= max_issues:
                break
                
            issue = self.get_issue(issue_id)
            if issue:
                issues.append(issue)
                if issue.source == 'backup':
                    from_backup += 1
            else:
                failed.append(issue_id)
            
            if (i + 1) % 20 == 0:
                print(f"[Redmine] Fetched {i+1}/{len(all_issue_ids)} issues...")
            time.sleep(delay)
        
        print(f"[Redmine] Completed: {len(issues)} issues fetched")
        if from_backup > 0:
            print(f"[Redmine]   - From backup server: {from_backup}")
        if failed:
            print(f"[Redmine]   - Failed: {len(failed)}")
        
        return issues
    
    def search_wiki_references(self, wiki_title: str) -> int:
        endpoint = f"/search.json?q=[[{wiki_title}]]&issues=1&limit=100"
        data = self._make_request(endpoint)
        return data.get('total_count', 0) if data else 0
    
    def test_connection(self) -> Dict[str, bool]:
        """测试服务器连接"""
        results = {
            'primary': False,
            'backup': False
        }
        
        # 测试主服务器
        data = self._make_request("/projects.json?limit=1", use_backup=False)
        if data:
            results['primary'] = True
            print(f"[Redmine] Primary server ({self.base_url}): OK")
        
        # 测试备份服务器
        if self.backup_url:
            data = self._make_request("/projects.json?limit=1", use_backup=True)
            if data:
                results['backup'] = True
                print(f"[Redmine] Backup server ({self.backup_url}): OK")
        
        return results