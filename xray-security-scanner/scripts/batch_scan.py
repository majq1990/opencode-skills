#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xray 批量扫描脚本
支持从文件读取目标列表，并发执行扫描任务
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time

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

def find_xray_binary():
    """查找 xray 二进制文件"""
    system = os.name
    exe_suffix = '.exe' if system == 'nt' else ''
    
    # 常见安装路径
    search_paths = [
        os.path.expanduser(f'~/.xray/xray{exe_suffix}'),
        os.path.expanduser(f'~/xray/xray{exe_suffix}'),
        f'/usr/local/bin/xray{exe_suffix}',
        f'/usr/bin/xray{exe_suffix}',
    ]
    
    # 添加到 PATH 中的搜索
    for path in os.environ.get('PATH', '').split(os.pathsep):
        search_paths.append(os.path.join(path, f'xray{exe_suffix}'))
    
    for path in search_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    
    # 尝试直接调用
    try:
        result = subprocess.run(['xray', 'version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            return 'xray'
    except:
        pass
    
    return None

def scan_target(xray_path, target, options, output_dir):
    """扫描单个目标"""
    target_name = target.replace('://', '_').replace('/', '_').replace(':', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f"{target_name}_{timestamp}")
    
    # 构建命令
    cmd = [xray_path, 'webscan']
    
    # 添加扫描模式
    if options.get('crawler'):
        cmd.extend(['--basic-crawler', target])
        if options.get('depth'):
            cmd.extend(['--depth', str(options['depth'])])
    else:
        cmd.extend(['--url', target])
    
    # 添加插件
    if options.get('plugins'):
        cmd.extend(['--plugins', options['plugins']])
    
    if options.get('disable_plugins'):
        cmd.extend(['--disable-plugins', options['disable_plugins']])
    
    # 添加输出
    if options.get('format') == 'json':
        cmd.extend(['--json-output', f"{output_file}.json"])
    elif options.get('format') == 'text':
        cmd.extend(['--text-output', f"{output_file}.txt"])
    else:
        cmd.extend(['--html-output', f"{output_file}.html"])
    
    # 添加其他选项
    if options.get('headers'):
        for header in options['headers']:
            cmd.extend(['--header', header])
    
    if options.get('cookie'):
        cmd.extend(['--cookie', options['cookie']])
    
    if options.get('max_qps'):
        cmd.extend(['--max-qps', str(options['max_qps'])])
    
    if options.get('timeout'):
        cmd.extend(['--timeout', str(options['timeout'])])
    
    # 执行扫描
    print_info(f"开始扫描: {target}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=options.get('timeout', 300)
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0 or result.returncode == 1:  # 1 通常表示发现漏洞
            print_success(f"扫描完成: {target} ({elapsed:.1f}s)")
            return {
                'target': target,
                'status': 'success',
                'output': output_file,
                'time': elapsed,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        else:
            print_error(f"扫描失败: {target}")
            return {
                'target': target,
                'status': 'error',
                'error': result.stderr,
                'time': elapsed
            }
            
    except subprocess.TimeoutExpired:
        print_error(f"扫描超时: {target}")
        return {
            'target': target,
            'status': 'timeout',
            'time': options.get('timeout', 300)
        }
    except Exception as e:
        print_error(f"扫描异常: {target} - {e}")
        return {
            'target': target,
            'status': 'exception',
            'error': str(e)
        }

def merge_reports(output_dir, format_type):
    """合并报告"""
    print_info("合并扫描报告...")
    
    if format_type == 'json':
        merged = {'vulnerabilities': [], 'scan_info': {}}
        
        for file in os.listdir(output_dir):
            if file.endswith('.json'):
                filepath = os.path.join(output_dir, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'vulnerabilities' in data:
                            merged['vulnerabilities'].extend(data['vulnerabilities'])
                        elif isinstance(data, list):
                            merged['vulnerabilities'].extend(data)
                except Exception as e:
                    print_warning(f"读取报告失败 {file}: {e}")
        
        merged_file = os.path.join(output_dir, 'merged_report.json')
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        
        print_success(f"合并报告已保存: {merged_file}")
        return merged_file
    
    return None

def main():
    parser = argparse.ArgumentParser(
        description='xray 批量扫描脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础批量扫描
  python batch_scan.py targets.txt

  # 爬虫模式批量扫描
  python batch_scan.py targets.txt --crawler --depth 3

  # 指定插件并输出 JSON
  python batch_scan.py targets.txt --plugins sqldet,xss --format json

  # 并发扫描 5 个目标
  python batch_scan.py targets.txt --workers 5 --format html

targets.txt 格式:
  http://target1.com
  http://target2.com/page?id=1
  https://target3.com/api
        """
    )
    
    parser.add_argument('targets_file', help='目标列表文件路径')
    parser.add_argument('--output', '-o', default='scan_results', help='输出目录（默认: scan_results）')
    parser.add_argument('--format', choices=['html', 'json', 'text'], default='html', help='输出格式')
    parser.add_argument('--crawler', action='store_true', help='启用爬虫模式')
    parser.add_argument('--depth', type=int, default=3, help='爬虫深度（默认: 3）')
    parser.add_argument('--plugins', help='启用的插件，逗号分隔（如: sqldet,xss）')
    parser.add_argument('--disable-plugins', help='禁用的插件，逗号分隔')
    parser.add_argument('--workers', type=int, default=3, help='并发数（默认: 3）')
    parser.add_argument('--timeout', type=int, default=300, help='单个目标超时时间（秒，默认: 300）')
    parser.add_argument('--max-qps', type=int, help='每秒最大请求数')
    parser.add_argument('--header', action='append', dest='headers', help='自定义 HTTP 头')
    parser.add_argument('--cookie', help='Cookie 字符串')
    parser.add_argument('--merge', action='store_true', help='合并所有报告')
    parser.add_argument('--xray-path', help='xray 二进制文件路径')
    
    args = parser.parse_args()
    
    # 检查目标文件
    if not os.path.exists(args.targets_file):
        print_error(f"目标文件不存在: {args.targets_file}")
        return 1
    
    # 查找 xray
    xray_path = args.xray_path or find_xray_binary()
    if not xray_path:
        print_error("未找到 xray 二进制文件，请先安装 xray")
        print_info("安装命令: python install_xray.py")
        return 1
    
    print_info(f"使用 xray: {xray_path}")
    
    # 读取目标列表
    with open(args.targets_file, 'r', encoding='utf-8') as f:
        targets = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not targets:
        print_error("目标文件为空")
        return 1
    
    print_info(f"读取到 {len(targets)} 个扫描目标")
    
    # 创建输出目录
    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)
    print_info(f"输出目录: {output_dir}")
    
    # 构建选项
    options = {
        'crawler': args.crawler,
        'depth': args.depth,
        'plugins': args.plugins,
        'disable_plugins': args.disable_plugins,
        'format': args.format,
        'headers': args.headers,
        'cookie': args.cookie,
        'max_qps': args.max_qps,
        'timeout': args.timeout
    }
    
    # 执行扫描
    results = []
    completed = 0
    failed = 0
    
    print_info(f"开始批量扫描（并发数: {args.workers}）...")
    print("=" * 60)
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(scan_target, xray_path, target, options, output_dir): target
            for target in targets
        }
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            
            if result['status'] == 'success':
                completed += 1
            else:
                failed += 1
            
            # 显示进度
            progress = (completed + failed) / len(targets) * 100
            print(f"\n{Colors.CYAN}进度: {progress:.1f}% ({completed + failed}/{len(targets)}){Colors.END}")
    
    elapsed = time.time() - start_time
    
    # 扫描完成统计
    print("\n" + "=" * 60)
    print_success("批量扫描完成！")
    print(f"\n扫描统计:")
    print(f"  总目标数: {len(targets)}")
    print(f"  成功: {completed}")
    print(f"  失败: {failed}")
    print(f"  总耗时: {elapsed:.1f}秒")
    print(f"  平均耗时: {elapsed/len(targets):.1f}秒/目标")
    
    # 合并报告
    if args.merge and args.format == 'json':
        merge_reports(output_dir, args.format)
    
    # 保存扫描日志
    log_file = os.path.join(output_dir, 'scan_log.json')
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump({
            'scan_time': datetime.now().isoformat(),
            'total_targets': len(targets),
            'completed': completed,
            'failed': failed,
            'total_time': elapsed,
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n扫描日志: {log_file}")
    print(f"报告目录: {output_dir}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
