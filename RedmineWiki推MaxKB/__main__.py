#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
import json
import time
from datetime import datetime
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config, PRODUCT_MAPPINGS
from lib.redmine_client import RedmineClient, WikiPage, IssueInfo
from lib.converter import html_to_markdown
from lib.maxkb_client import MaxKBClient

def calculate_activity_score(page: WikiPage, active_days: int = 365) -> int:
    from datetime import datetime, timedelta
    threshold = datetime.now() - timedelta(days=active_days)
    
    try:
        updated = datetime.fromisoformat(page.updated_on.replace('Z', '+00:00').replace('+08:00', ''))
        time_score = 100 if updated > threshold else 30
    except:
        time_score = 50
    
    version_score = min(100, page.version * 10)
    ref_score = 50
    
    total = int(time_score * 0.4 + ref_score * 0.4 + version_score * 0.2)
    
    if total >= 60:
        page.status = "Active"
    elif total >= 30:
        page.status = "Dormant"
    else:
        page.status = "Deprecated"
    
    page.score = total
    return total

def filter_by_product(pages: List[WikiPage], product: str) -> List[WikiPage]:
    if product not in PRODUCT_MAPPINGS:
        print(f"[WARN] Unknown product: {product}")
        return pages
    
    keywords = PRODUCT_MAPPINGS[product].keywords
    filtered = []
    
    for page in pages:
        if page.parent:
            for kw in keywords:
                if kw in page.parent:
                    filtered.append(page)
                    break
    
    return filtered

def issue_to_markdown(issue: IssueInfo, base_url: str) -> str:
    import re
    
    md = f"# 案件 #{issue.id}\n\n"
    md += "| 属性 | 值 |\n|------|------|\n"
    md += f"| 标题 | {issue.subject} |\n"
    md += f"| 项目 | {issue.project} |\n"
    md += f"| 状态 | {issue.status} |\n"
    md += f"| 作者 | {issue.author} |\n"
    
    if issue.assigned_to:
        md += f"| 负责人 | {issue.assigned_to} |\n"
    
    md += f"| 创建时间 | {issue.created_on} |\n"
    md += f"| 更新时间 | {issue.updated_on} |\n"
    md += f"| 完成率 | {issue.done_ratio}% |\n"
    md += f"| [链接]({base_url}/issues/{issue.id}) |\n"
    
    if issue.source == 'backup':
        md += "\n> ⚠️ 数据来源：备份服务器\n"
    
    if issue.description:
        desc = re.sub(r'</?p[^>]*>', '\n', issue.description)
        desc = re.sub(r'<br\s*/?>', '\n', desc)
        desc = re.sub(r'<[^>]+>', '', desc)
        md += f"\n## 描述\n\n{desc.strip()}\n"
    
    if issue.journals:
        md += f"\n## 批转记录 ({len(issue.journals)}条)\n\n"
        for j in issue.journals[:15]:
            user = j.get('user', {}).get('name', 'N/A')
            created = j.get('created_on', 'N/A')
            notes = j.get('notes', '')
            if notes:
                notes = re.sub(r'</?p[^>]*>', '\n', notes)
                notes = re.sub(r'<br\s*/?>', '\n', notes)
                notes = re.sub(r'<[^>]+>', '', notes)
            md += f"### {user} @ {created}\n{notes}\n\n"
    
    if issue.linglong_forms:
        md += "\n## 灵珑表单详情\n\n"
        for form_key, form_data in issue.linglong_forms.items():
            md += f"### {form_data.get('name', form_key)}\n\n"
            md += f"```json\n{json.dumps(form_data.get('data'), ensure_ascii=False, indent=2)}\n```\n\n"
    
    return md

def main():
    parser = argparse.ArgumentParser(
        description='从 Redmine Wiki 同步文档到 MaxKB'
    )
    parser.add_argument('--product', '-p', help='产品名称')
    parser.add_argument('--dataset', '-d', help='MaxKB 知识库名称')
    parser.add_argument('--min-score', type=int, default=60, help='最低活跃度得分')
    parser.add_argument('--days', type=int, default=365, help='活跃时间阈值')
    parser.add_argument('--limit', type=int, default=0, help='最大上传数量')
    parser.add_argument('--include-issues', action='store_true', help='包含关联案件信息')
    parser.add_argument('--include-linglong', action='store_true', help='包含灵珑表单详情')
    parser.add_argument('--full-sync', action='store_true', help='完整同步')
    parser.add_argument('--dry-run', action='store_true', help='只分析不上传')
    parser.add_argument('--test-connection', action='store_true', help='测试服务器连接')
    parser.add_argument('--headless', action='store_true', default=True)
    
    args = parser.parse_args()
    
    config = Config()
    
    print("=" * 60)
    print("Redmine Wiki -> MaxKB Sync")
    if args.full_sync or args.include_issues:
        print(" (含案件信息 + 灵珑表单)")
    print("=" * 60)
    
    if args.test_connection:
        client = RedmineClient(
            config.redmine.url,
            config.redmine.api_key,
            config.redmine.project,
            config.redmine.backup_url
        )
        results = client.test_connection()
        print(f"\n连接测试结果: {results}")
        return
    
    if not args.product:
        print("\n可用产品:")
        for i, name in enumerate(PRODUCT_MAPPINGS.keys(), 1):
            print(f"  {i}. {name}")
        print("\n使用: redmine-wiki-to-maxkb --product 麒舰")
        return
    
    print(f"\n产品: {args.product}")
    print(f"知识库: {args.dataset or args.product + '工程Wiki知识库'}")
    print(f"最低得分: {args.min_score}")
    print(f"活跃天数: {args.days}")
    print(f"包含案件: {'是' if (args.include_issues or args.full_sync) else '否'}")
    print(f"包含灵珑: {'是' if (args.include_linglong or args.full_sync) else '否'}")
    
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(config.output_dir) / today
    output_dir.mkdir(parents=True, exist_ok=True)
    
    wiki_md_dir = output_dir / f"{args.product.lower()}_wiki_md"
    issues_md_dir = output_dir / f"{args.product.lower()}_issues_md"
    
    client = RedmineClient(
        config.redmine.url,
        config.redmine.api_key,
        config.redmine.project,
        config.redmine.backup_url
    )
    
    print("\n[1] 获取 Wiki 列表...")
    all_pages = client.fetch_all_wikis()
    
    print(f"\n[2] 筛选产品: {args.product}...")
    product_pages = filter_by_product(all_pages, args.product)
    print(f"    找到 {len(product_pages)} 个相关 Wiki")
    
    print("\n[3] 计算活跃度得分...")
    for page in product_pages:
        calculate_activity_score(page, args.days)
    
    active_pages = [p for p in product_pages if p.score >= args.min_score]
    print(f"    活跃 Wiki: {len(active_pages)} 个 (得分 >= {args.min_score})")
    
    print("\n[4] 获取 Wiki 内容...")
    wiki_md_dir.mkdir(exist_ok=True)
    success = 0
    for i, page in enumerate(active_pages):
        try:
            content = client.get_wiki_page(page.title)
            if content and content.get('text'):
                md_content = html_to_markdown(content.get('text', ''))
                safe_title = page.title.replace('/', '_').replace('\\', '_').replace(':', '_')[:100]
                md_path = wiki_md_dir / f"{safe_title}.md"
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {page.title}\n\n")
                    f.write(f"> 得分: {page.score} | 状态: {page.status} | 版本: {page.version}\n\n")
                    f.write(md_content)
                page.text = content.get('text')
                success += 1
        except Exception as e:
            pass
        
        if (i + 1) % 50 == 0:
            print(f"    进度: {i+1}/{len(active_pages)}")
    
    print(f"    成功: {success}/{len(active_pages)}")
    
    issues = []
    if args.include_issues or args.full_sync:
        print("\n[5] 从 Wiki 提取案件并获取详情...")
        issues_md_dir.mkdir(exist_ok=True)
        
        issues = client.fetch_issues_from_wikis(active_pages, delay=0.2)
        
        success = 0
        for i, issue in enumerate(issues):
            md_content = issue_to_markdown(issue, config.redmine.url)
            safe_title = issue.subject[:50].replace('/', '_').replace('\\', '_')
            md_path = issues_md_dir / f"{issue.id}_{safe_title}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            success += 1
            
            if (i + 1) % 20 == 0:
                print(f"    进度: {i+1}/{len(issues)}")
        
        print(f"    成功: {success}/{len(issues)}")
    
    if args.dry_run:
        print("\n[DRY-RUN] 分析完成，未上传")
        print(f"    Wiki 文件: {wiki_md_dir}")
        print(f"    案件文件: {issues_md_dir if issues else 'N/A'}")
        return
    
    print("\n[6] 上传到 MaxKB...")
    print("    请手动登录 MaxKB 完成上传:")
    print(f"    URL: {config.maxkb.url}/ui/login")
    print(f"    用户: {config.maxkb.username}")
    print(f"    文件: {wiki_md_dir}")
    if issues:
        print(f"    案件: {issues_md_dir}")
    
    print("\n" + "=" * 60)
    print("完成!")
    print(f"  Wiki: {len(active_pages)} 个 ({success} 个已下载)")
    print(f"  案件: {len(issues)} 个")
    print(f"  输出: {output_dir}")

if __name__ == '__main__':
    main()