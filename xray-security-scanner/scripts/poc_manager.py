#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xray POC 管理工具
支持 POC 的查看、验证、批量操作和管理
"""

import os
import sys
import yaml
import json
import argparse
import requests
import zipfile
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse, urlunparse

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.END} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN}[OK]{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}[WARN]{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.END} {msg}")

def get_poc_dirs():
    """获取 POC 目录"""
    home_dir = Path.home()
    system = os.name
    
    if system == 'nt':  # Windows
        default_dir = home_dir / '.xray' / 'pocs'
    else:
        default_dir = home_dir / '.xray' / 'pocs'
    
    return [default_dir]

def find_pocs(dirs=None):
    """查找所有 POC 文件"""
    if dirs is None:
        dirs = get_poc_dirs()
    
    pocs = []
    for dir_path in dirs:
        if not dir_path.exists():
            continue
        
        for file_path in dir_path.rglob('*.yml'):
            pocs.append(file_path)
        for file_path in dir_path.rglob('*.yaml'):
            pocs.append(file_path)
    
    return pocs

def load_poc(file_path):
    """加载 POC 文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print_error(f"加载 POC 失败 {file_path}: {e}")
        return None

def validate_poc(poc_data, file_path):
    """验证 POC 格式"""
    errors = []
    warnings = []
    
    if not isinstance(poc_data, dict):
        errors.append("POC 必须是字典格式")
        return errors, warnings
    
    # 检查必要字段
    if 'name' not in poc_data:
        errors.append("缺少必要字段: name")
    
    if 'rules' not in poc_data:
        errors.append("缺少必要字段: rules")
    else:
        if not isinstance(poc_data['rules'], list):
            errors.append("rules 必须是列表")
        elif len(poc_data['rules']) == 0:
            errors.append("rules 不能为空列表")
    
    # 检查 name 格式
    if 'name' in poc_data:
        name = poc_data['name']
        if not name.startswith('poc-'):
            warnings.append(f"POC 名称建议以 'poc-' 开头: {name}")
        if not any(c in name for c in ['-', '_']):
            warnings.append(f"POC 名称建议包含连字符或下划线: {name}")
    
    # 检查 rules 格式
    if 'rules' in poc_data and isinstance(poc_data['rules'], list):
        for i, rule in enumerate(poc_data['rules']):
            if not isinstance(rule, dict):
                errors.append(f"rule[{i}] 必须是字典")
                continue
            
            # 检查 rule 字段
            if 'expression' not in rule:
                errors.append(f"rule[{i}] 缺少必要字段: expression")
            
            if 'method' in rule and rule['method'] not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                warnings.append(f"rule[{i}] 使用非标准 HTTP 方法: {rule['method']}")
    
    # 检查 detail 字段
    if 'detail' in poc_data:
        detail = poc_data['detail']
        if isinstance(detail, dict):
            if 'author' not in detail:
                warnings.append("建议在 detail 中添加 author 字段")
            if 'links' not in detail:
                warnings.append("建议在 detail 中添加 links 字段（漏洞参考链接）")
    else:
        warnings.append("建议添加 detail 字段（包含 author、links 等信息）")
    
    return errors, warnings

def list_pocs(args):
    """列出 POC"""
    print_info("正在扫描 POC 文件...")
    
    pocs = find_pocs()
    
    if not pocs:
        print_warning("未找到 POC 文件")
        print_info(f"POC 目录: {get_poc_dirs()[0]}")
        return 0
    
    print_success(f"找到 {len(pocs)} 个 POC 文件")
    print()
    
    # 分类统计
    categories = defaultdict(list)
    
    for poc_path in pocs:
        poc_data = load_poc(poc_path)
        if poc_data:
            name = poc_data.get('name', 'unknown')
            # 提取类别（假设 POC 名称格式为 poc-category-name）
            parts = name.split('-')
            if len(parts) >= 2:
                category = parts[1]
            else:
                category = 'other'
            categories[category].append((name, poc_path))
    
    # 显示分类
    if args.category:
        if args.category in categories:
            print(f"{Colors.CYAN}类别: {args.category}{Colors.END}")
            for name, path in sorted(categories[args.category]):
                print(f"  {name}")
                if args.verbose:
                    print(f"    路径: {path}")
        else:
            print_error(f"类别不存在: {args.category}")
            return 1
    else:
        print(f"{'类别':<20} {'数量':<10}")
        print("-" * 30)
        for category, pocs_list in sorted(categories.items()):
            print(f"{category:<20} {len(pocs_list):<10}")
        
        if args.verbose:
            print("\n详细列表:")
            for category, pocs_list in sorted(categories.items()):
                print(f"\n{Colors.CYAN}{category}{Colors.END}")
                for name, path in sorted(pocs_list):
                    print(f"  {name}")
    
    return 0

def show_poc(args):
    """显示 POC 详情"""
    poc_name = args.name
    
    # 如果提供了完整路径
    if os.path.exists(poc_name):
        poc_path = Path(poc_name)
        poc_data = load_poc(poc_path)
    else:
        # 在 POC 目录中搜索
        pocs = find_pocs()
        poc_path = None
        poc_data = None
        
        for p in pocs:
            data = load_poc(p)
            if data and data.get('name') == poc_name:
                poc_path = p
                poc_data = data
                break
        
        if not poc_path:
            print_error(f"未找到 POC: {poc_name}")
            return 1
    
    print(f"{Colors.CYAN}POC 名称:{Colors.END} {poc_data.get('name', 'N/A')}")
    print(f"{Colors.CYAN}文件路径:{Colors.END} {poc_path}")
    print()
    
    # 显示 rules
    rules = poc_data.get('rules', [])
    print(f"{Colors.CYAN}Rules ({len(rules)} 条):{Colors.END}")
    for i, rule in enumerate(rules, 1):
        print(f"\n  Rule {i}:")
        for key, value in rule.items():
            if key == 'expression':
                print(f"    {key}:")
                for line in str(value).split('\n'):
                    print(f"      {line}")
            else:
                print(f"    {key}: {value}")
    
    # 显示 detail
    detail = poc_data.get('detail', {})
    if detail:
        print(f"\n{Colors.CYAN}Detail:{Colors.END}")
        for key, value in detail.items():
            if isinstance(value, list):
                print(f"  {key}:")
                for item in value:
                    print(f"    - {item}")
            else:
                print(f"  {key}: {value}")
    
    return 0

def validate_command(args):
    """验证 POC"""
    if args.poc:
        # 验证单个 POC
        file_paths = [Path(args.poc)]
    else:
        # 验证所有 POC
        print_info("正在扫描所有 POC 文件...")
        file_paths = find_pocs()
    
    if not file_paths:
        print_warning("未找到 POC 文件")
        return 0
    
    total = 0
    passed = 0
    failed = 0
    
    for file_path in file_paths:
        total += 1
        print(f"\n{Colors.BLUE}验证: {file_path}{Colors.END}")
        
        poc_data = load_poc(file_path)
        if poc_data is None:
            failed += 1
            continue
        
        errors, warnings = validate_poc(poc_data, file_path)
        
        if errors:
            print_error(f"发现 {len(errors)} 个错误:")
            for error in errors:
                print(f"  - {error}")
            failed += 1
        elif warnings:
            print_warning(f"发现 {len(warnings)} 个警告:")
            for warning in warnings:
                print(f"  - {warning}")
            print_success("格式基本正确")
            passed += 1
        else:
            print_success("验证通过")
            passed += 1
    
    print(f"\n{Colors.CYAN}验证结果: 总计 {total}, 通过 {passed}, 失败 {failed}{Colors.END}")
    return 0 if failed == 0 else 1

def create_poc(args):
    """创建新 POC"""
    name = args.name
    
    # 确保名称格式正确
    if not name.startswith('poc-'):
        name = f'poc-yaml-{name}'
    
    # 构建 POC 模板
    poc_template = f"""name: {name}
# 详细规则请参考: https://docs.xray.cool/#/guide/poc

rules:
  - method: GET
    path: /
    headers:
      User-Agent: "Mozilla/5.0"
    expression: |
      response.status == 200 && response.body.bcontains(b"keyword")

detail:
    author: "your_name"
    description: "POC description"
    links:
        - "https://example.com/vulnerability"
"""
    
    # 确定输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        poc_dir = get_poc_dirs()[0]
        output_path = poc_dir / f"{name}.yml"
    
    # 创建目录
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入文件
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(poc_template)
        print_success(f"POC 已创建: {output_path}")
        print_info("请编辑文件完善规则")
        return 0
    except Exception as e:
        print_error(f"创建 POC 失败: {e}")
        return 1

def search_pocs(args):
    """搜索 POC"""
    keyword = args.keyword.lower()
    
    print_info(f"搜索关键词: {keyword}")
    
    pocs = find_pocs()
    found = []
    
    for poc_path in pocs:
        poc_data = load_poc(poc_path)
        if not poc_data:
            continue
        
        # 搜索名称
        name = poc_data.get('name', '')
        if keyword in name.lower():
            found.append((name, poc_path, 'name'))
            continue
        
        # 搜索 detail
        detail = poc_data.get('detail', {})
        if isinstance(detail, dict):
            desc = detail.get('description', '')
            if keyword in desc.lower():
                found.append((name, poc_path, 'description'))
                continue
            
            author = detail.get('author', '')
            if keyword in author.lower():
                found.append((name, poc_path, 'author'))
                continue
        
        # 搜索 rules
        rules = poc_data.get('rules', [])
        for rule in rules:
            if isinstance(rule, dict):
                path = rule.get('path', '')
                if keyword in path.lower():
                    found.append((name, poc_path, 'path'))
                    break
    
    if found:
        print_success(f"找到 {len(found)} 个匹配的 POC")
        print()
        for name, path, match_type in found:
            print(f"{Colors.CYAN}{name}{Colors.END}")
            print(f"  匹配: {match_type}")
            print(f"  路径: {path}")
            print()
    else:
        print_warning("未找到匹配的 POC")
    
    return 0

def apply_github_mirror(url):
    """应用 GitHub 镜像加速
    
    转换规则：
    - https://github.com/... -> https://ghfast.top/https://github.com/...
    - https://raw.githubusercontent.com/... -> https://ghfast.top/https://raw.githubusercontent.com/...
    """
    parsed = urlparse(url)
    if 'github.com' in parsed.netloc or 'raw.githubusercontent.com' in parsed.netloc:
        # 在原始 URL 前加上 ghfast.top 前缀
        return f"https://ghfast.top/{url}"
    return url

def download_pocs(args):
    """从远程仓库下载 POC"""
    url = args.url
    
    # 所有 GitHub 地址自动走 ghfast.top 镜像加速
    original_url = url
    url = apply_github_mirror(url)
    if url != original_url:
        print_info(f"已自动使用 ghfast.top 镜像加速")
        print_info(f"原始地址: {original_url}")
        print_info(f"加速地址: {url}")
    
    print_info(f"下载 POC 从: {url}")
    
    # 确定保存目录
    poc_dir = get_poc_dirs()[0]
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = poc_dir / 'downloaded'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 下载文件
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 如果是 ZIP 文件，解压
        if url.endswith('.zip'):
            zip_path = output_dir / 'temp_pocs.zip'
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            
            zip_path.unlink()
            print_success(f"POC 已下载并解压到: {output_dir}")
        else:
            # 单个 YAML 文件
            content = response.text
            if url.endswith(('.yml', '.yaml')):
                file_name = Path(urlparse(url).path).name
            else:
                file_name = 'downloaded_poc.yml'
            
            output_path = output_dir / file_name
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print_success(f"POC 已下载到: {output_path}")
        
        return 0
    except requests.exceptions.Timeout:
        print_error("下载超时，请检查网络连接或尝试使用镜像")
        return 1
    except requests.exceptions.RequestException as e:
        print_error(f"下载失败: {e}")
        print_info("提示: 如果是 GitHub 资源，已自动尝试使用 ghfast.top 镜像加速")
        print_info("      如果仍失败，请检查网络或手动下载")
        return 1
    except Exception as e:
        print_error(f"处理失败: {e}")
        return 1

def update_pocs(args):
    """更新本地 POC"""
    print_info("正在更新 POC...")
    
    # 默认更新官方 POC 仓库
    repo_urls = [
        'https://ghfast.top/https://github.com/chaitin/xray/tree/master/pocs',
    ]
    
    if args.url:
        repo_urls = [args.url]
    
    poc_dir = get_poc_dirs()[0]
    update_dir = poc_dir / 'updated'
    update_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    
    for url in repo_urls:
        print_info(f"更新来源: {url}")
        # 这里可以实现完整的仓库同步逻辑
        # 简化版本：提示用户手动使用 download 命令
        print_info("建议使用 download 命令更新特定 POC 文件")
    
    print_success(f"更新完成: {success_count} 成功, {fail_count} 失败")
    return 0

def main():
    parser = argparse.ArgumentParser(
        description='xray POC 管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出所有 POC
  python poc_manager.py list

  # 列出特定类别的 POC
  python poc_manager.py list --category yaml

  # 显示 POC 详情
  python poc_manager.py show poc-yaml-example-rule

  # 验证单个 POC
  python poc_manager.py validate ./my-poc.yml

  # 验证所有 POC
  python poc_manager.py validate --all

  # 创建新 POC
  python poc_manager.py create my-new-rule

  # 搜索 POC
  python poc_manager.py search sql

  # 下载 POC（GitHub 地址自动走 ghfast.top 镜像加速）
  python poc_manager.py download https://github.com/chaitin/xray/tree/master/pocs/webhook.yaml

  # 更新本地 POC
  python poc_manager.py update
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出 POC')
    list_parser.add_argument('--category', '-c', help='按类别过滤')
    list_parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    
    # show 命令
    show_parser = subparsers.add_parser('show', help='显示 POC 详情')
    show_parser.add_argument('name', help='POC 名称或路径')
    
    # validate 命令
    validate_parser = subparsers.add_parser('validate', help='验证 POC')
    validate_parser.add_argument('poc', nargs='?', help='POC 文件路径')
    validate_parser.add_argument('--all', '-a', action='store_true', help='验证所有 POC')
    
    # create 命令
    create_parser = subparsers.add_parser('create', help='创建新 POC')
    create_parser.add_argument('name', help='POC 名称')
    create_parser.add_argument('--output', '-o', help='输出文件路径')
    
    # search 命令
    search_parser = subparsers.add_parser('search', help='搜索 POC')
    search_parser.add_argument('keyword', help='搜索关键词')
    
    # download 命令
    download_parser = subparsers.add_parser('download', help='从远程下载 POC（GitHub自动加速）')
    download_parser.add_argument('url', help='POC URL（支持 GitHub，自动走 ghfast.top 镜像）')
    download_parser.add_argument('--output', '-o', help='保存目录（默认: ~/.xray/pocs/downloaded/）')
    
    # update 命令
    update_parser = subparsers.add_parser('update', help='更新本地 POC')
    update_parser.add_argument('--url', help='指定更新源 URL（默认使用官方仓库）')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 执行命令
    if args.command == 'list':
        return list_pocs(args)
    elif args.command == 'show':
        return show_poc(args)
    elif args.command == 'validate':
        return validate_command(args)
    elif args.command == 'create':
        return create_poc(args)
    elif args.command == 'search':
        return search_pocs(args)
    elif args.command == 'download':
        return download_pocs(args)
    elif args.command == 'update':
        return update_pocs(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())
