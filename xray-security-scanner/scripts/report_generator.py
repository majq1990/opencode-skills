#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xray 报告生成器
支持将 JSON 报告转换为多种格式，并提供统计分析
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

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

def load_json_report(filepath):
    """加载 JSON 报告"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 处理不同格式的 JSON
        if isinstance(data, dict) and 'vulnerabilities' in data:
            return data['vulnerabilities']
        elif isinstance(data, list):
            return data
        else:
            return [data] if data else []
    except Exception as e:
        print_error(f"加载报告失败: {e}")
        return None

def generate_html_report(vulnerabilities, output_path, title="xray 安全扫描报告"):
    """生成 HTML 报告"""
    
    # 统计信息
    severity_count = defaultdict(int)
    plugin_count = defaultdict(int)
    
    for vuln in vulnerabilities:
        severity = vuln.get('severity', 'unknown').lower()
        plugin = vuln.get('plugin', 'unknown')
        severity_count[severity] += 1
        plugin_count[plugin] += 1
    
    # 严重程度颜色
    severity_colors = {
        'critical': '#dc3545',
        'high': '#fd7e14',
        'medium': '#ffc107',
        'low': '#17a2b8',
        'info': '#6c757d',
        'unknown': '#6c757d'
    }
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{ margin-bottom: 10px; font-size: 28px; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .stat-card .number {{
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .stat-card .label {{ color: #666; font-size: 14px; }}
        .content {{ padding: 30px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .severity-distribution {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }}
        .severity-badge {{
            display: inline-flex;
            align-items: center;
            padding: 8px 16px;
            border-radius: 20px;
            color: white;
            font-weight: 500;
        }}
        .severity-badge .count {{
            background: rgba(255,255,255,0.3);
            padding: 2px 8px;
            border-radius: 10px;
            margin-left: 8px;
        }}
        .vulnerability-list {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        .vuln-card {{
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            background: white;
            transition: box-shadow 0.2s;
        }}
        .vuln-card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .vuln-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .vuln-title {{
            font-size: 18px;
            font-weight: 600;
            color: #333;
        }}
        .vuln-meta {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }}
        .vuln-tag {{
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }}
        .vuln-detail {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
        }}
        .vuln-detail h4 {{
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        .vuln-detail p {{
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #333;
            word-break: break-all;
        }}
        .proof {{ background: #fff3cd; padding: 10px; border-radius: 4px; }}
        .suggestion {{ background: #d4edda; padding: 10px; border-radius: 4px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #666;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
            border-top: 1px solid #e9ecef;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="meta">
                生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                发现漏洞: {len(vulnerabilities)} 个
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="number">{len(vulnerabilities)}</div>
                <div class="label">漏洞总数</div>
            </div>
            <div class="stat-card">
                <div class="number">{severity_count.get('critical', 0)}</div>
                <div class="label">严重</div>
            </div>
            <div class="stat-card">
                <div class="number">{severity_count.get('high', 0)}</div>
                <div class="label">高危</div>
            </div>
            <div class="stat-card">
                <div class="number">{severity_count.get('medium', 0)}</div>
                <div class="label">中危</div>
            </div>
            <div class="stat-card">
                <div class="number">{severity_count.get('low', 0)}</div>
                <div class="label">低危</div>
            </div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>严重程度分布</h2>
                <div class="severity-distribution">
"""
    
    # 添加严重程度徽章
    for severity, count in sorted(severity_count.items(), 
                                   key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4, 'unknown': 5}.get(x[0], 6)):
        color = severity_colors.get(severity, '#6c757d')
        severity_name = severity.upper() if severity != 'unknown' else '未分类'
        html_content += f'                    <div class="severity-badge" style="background: {color}">{severity_name}<span class="count">{count}</span></div>\n'
    
    html_content += """                </div>
            </div>
            
            <div class="section">
                <h2>漏洞详情</h2>
                <div class="vulnerability-list">
"""
    
    # 添加漏洞详情
    for i, vuln in enumerate(vulnerabilities, 1):
        severity = vuln.get('severity', 'unknown').lower()
        color = severity_colors.get(severity, '#6c757d')
        plugin = vuln.get('plugin', '未知插件')
        target = vuln.get('target', vuln.get('url', '未知目标'))
        vuln_class = vuln.get('vuln_class', '未知类型')
        detail = vuln.get('detail', {})
        
        html_content += f"""                    <div class="vuln-card">
                        <div class="vuln-header">
                            <div class="vuln-title">#{i} {vuln_class}</div>
                            <div class="vuln-tag" style="background: {color}; color: white;">{severity.upper()}</div>
                        </div>
                        <div class="vuln-meta">
                            <div class="vuln-tag" style="background: #e9ecef; color: #333;">插件: {plugin}</div>
                        </div>
                        <div class="vuln-detail">
                            <h4>目标</h4>
                            <p>{target}</p>
                        </div>
"""
        
        # 添加 payload
        if 'payload' in detail:
            html_content += f"""                        <div class="vuln-detail proof">
                            <h4>Payload</h4>
                            <p>{detail['payload']}</p>
                        </div>
"""
        
        # 添加证据
        if 'evidence' in detail:
            html_content += f"""                        <div class="vuln-detail">
                            <h4>证据</h4>
                            <p>{detail['evidence']}</p>
                        </div>
"""
        
        html_content += "                    </div>\n"
    
    html_content += f"""                </div>
            </div>
            
            <div class="section">
                <h2>检测插件统计</h2>
                <table>
                    <thead>
                        <tr>
                            <th>插件名称</th>
                            <th>发现漏洞数</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    # 添加插件统计
    for plugin, count in sorted(plugin_count.items(), key=lambda x: x[1], reverse=True):
        html_content += f"""                        <tr>
                            <td>{plugin}</td>
                            <td>{count}</td>
                        </tr>
"""
    
    html_content += f"""                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>本报告由 xray 安全扫描工具生成 | 请确保已获得目标系统的合法测试授权</p>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print_success(f"HTML 报告已生成: {output_path}")
        return True
    except Exception as e:
        print_error(f"生成 HTML 报告失败: {e}")
        return False

def generate_markdown_report(vulnerabilities, output_path, title="xray 安全扫描报告"):
    """生成 Markdown 报告"""
    
    # 统计
    severity_count = defaultdict(int)
    plugin_count = defaultdict(int)
    
    for vuln in vulnerabilities:
        severity = vuln.get('severity', 'unknown').lower()
        plugin = vuln.get('plugin', 'unknown')
        severity_count[severity] += 1
        plugin_count[plugin] += 1
    
    md_content = f"""# {title}

**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 扫描统计

| 指标 | 数值 |
|------|------|
| 漏洞总数 | {len(vulnerabilities)} |
| 严重 (Critical) | {severity_count.get('critical', 0)} |
| 高危 (High) | {severity_count.get('high', 0)} |
| 中危 (Medium) | {severity_count.get('medium', 0)} |
| 低危 (Low) | {severity_count.get('low', 0)} |
| 信息 (Info) | {severity_count.get('info', 0)} |

## 严重程度分布

"""
    
    for severity, count in sorted(severity_count.items(), 
                                   key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4, 'unknown': 5}.get(x[0], 6)):
        md_content += f"- **{severity.upper()}**: {count} 个\n"
    
    md_content += "\n## 漏洞详情\n\n"
    
    for i, vuln in enumerate(vulnerabilities, 1):
        severity = vuln.get('severity', 'unknown').upper()
        plugin = vuln.get('plugin', '未知插件')
        target = vuln.get('target', vuln.get('url', '未知目标'))
        vuln_class = vuln.get('vuln_class', '未知类型')
        detail = vuln.get('detail', {})
        
        md_content += f"""### #{i} {vuln_class}

- **严重程度:** {severity}
- **检测插件:** {plugin}
- **目标:** `{target}`

"""
        
        if 'payload' in detail:
            md_content += f"**Payload:**\n```\n{detail['payload']}\n```\n\n"
        
        if 'evidence' in detail:
            md_content += f"**证据:**\n```\n{detail['evidence']}\n```\n\n"
        
        md_content += "---\n\n"
    
    md_content += "## 插件统计\n\n| 插件 | 漏洞数 |\n|------|--------|\n"
    for plugin, count in sorted(plugin_count.items(), key=lambda x: x[1], reverse=True):
        md_content += f"| {plugin} | {count} |\n"
    
    md_content += f"\n---\n\n*本报告由 xray 安全扫描工具生成*\n\n**注意:** 请确保已获得目标系统的合法测试授权"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print_success(f"Markdown 报告已生成: {output_path}")
        return True
    except Exception as e:
        print_error(f"生成 Markdown 报告失败: {e}")
        return False

def generate_text_report(vulnerabilities, output_path, title="xray 安全扫描报告"):
    """生成纯文本报告"""
    
    # 统计
    severity_count = defaultdict(int)
    plugin_count = defaultdict(int)
    
    for vuln in vulnerabilities:
        severity = vuln.get('severity', 'unknown').lower()
        plugin = vuln.get('plugin', 'unknown')
        severity_count[severity] += 1
        plugin_count[plugin] += 1
    
    text_content = f"""{'='*70}
{title.center(70)}
{'='*70}

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

扫描统计
{'-'*70}
漏洞总数: {len(vulnerabilities)}
严重 (Critical): {severity_count.get('critical', 0)}
高危 (High): {severity_count.get('high', 0)}
中危 (Medium): {severity_count.get('medium', 0)}
低危 (Low): {severity_count.get('low', 0)}
信息 (Info): {severity_count.get('info', 0)}

严重程度分布
{'-'*70}
"""
    
    for severity, count in sorted(severity_count.items(), 
                                   key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4, 'unknown': 5}.get(x[0], 6)):
        text_content += f"{severity.upper():12} {count} 个\n"
    
    text_content += f"\n{'='*70}\n漏洞详情\n{'='*70}\n\n"
    
    for i, vuln in enumerate(vulnerabilities, 1):
        severity = vuln.get('severity', 'unknown').upper()
        plugin = vuln.get('plugin', '未知插件')
        target = vuln.get('target', vuln.get('url', '未知目标'))
        vuln_class = vuln.get('vuln_class', '未知类型')
        detail = vuln.get('detail', {})
        
        text_content += f"""[{i}] {vuln_class}
    严重程度: {severity}
    检测插件: {plugin}
    目标: {target}
"""
        
        if 'payload' in detail:
            text_content += f"    Payload: {detail['payload']}\n"
        
        if 'evidence' in detail:
            text_content += f"    证据: {detail['evidence']}\n"
        
        text_content += "\n"
    
    text_content += f"""{'='*70}
插件统计
{'-'*70}
"""
    for plugin, count in sorted(plugin_count.items(), key=lambda x: x[1], reverse=True):
        text_content += f"{plugin:30} {count}\n"
    
    text_content += f"""
{'='*70}
注意: 请确保已获得目标系统的合法测试授权
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*70}
"""
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        print_success(f"文本报告已生成: {output_path}")
        return True
    except Exception as e:
        print_error(f"生成文本报告失败: {e}")
        return False

def print_statistics(vulnerabilities):
    """打印统计信息"""
    if not vulnerabilities:
        print_warning("未发现漏洞")
        return
    
    print("\n" + "="*60)
    print("扫描统计")
    print("="*60)
    
    # 严重程度统计
    severity_count = defaultdict(int)
    plugin_count = defaultdict(int)
    
    for vuln in vulnerabilities:
        severity = vuln.get('severity', 'unknown').lower()
        plugin = vuln.get('plugin', 'unknown')
        severity_count[severity] += 1
        plugin_count[plugin] += 1
    
    print(f"\n{Colors.CYAN}漏洞总数: {len(vulnerabilities)}{Colors.END}")
    print("\n严重程度分布:")
    for severity in ['critical', 'high', 'medium', 'low', 'info']:
        count = severity_count.get(severity, 0)
        if count > 0:
            color = {
                'critical': Colors.RED,
                'high': Colors.RED,
                'medium': Colors.YELLOW,
                'low': Colors.BLUE,
                'info': Colors.CYAN
            }.get(severity, Colors.END)
            print(f"  {color}{severity.upper():12}{Colors.END} {count} 个")
    
    print("\n插件统计:")
    for plugin, count in sorted(plugin_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {plugin:30} {count}")

def main():
    parser = argparse.ArgumentParser(
        description='xray 报告生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成 HTML 报告
  python report_generator.py scan_result.json --format html -o report.html

  # 生成 Markdown 报告
  python report_generator.py scan_result.json --format markdown -o report.md

  # 只显示统计信息
  python report_generator.py scan_result.json --stats-only

  # 批量转换多个报告
  python report_generator.py *.json --format html --output-dir ./reports/
        """
    )
    
    parser.add_argument('input', nargs='+', help='输入的 JSON 报告文件')
    parser.add_argument('--format', '-f', choices=['html', 'markdown', 'md', 'text', 'txt', 'all'],
                       default='html', help='输出格式（默认: html）')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--output-dir', '-d', help='输出目录（用于批量转换）')
    parser.add_argument('--title', '-t', default='xray 安全扫描报告', help='报告标题')
    parser.add_argument('--stats-only', action='store_true', help='仅显示统计信息')
    
    args = parser.parse_args()
    
    # 加载所有报告
    all_vulns = []
    for input_file in args.input:
        if not os.path.exists(input_file):
            print_error(f"文件不存在: {input_file}")
            continue
        
        vulns = load_json_report(input_file)
        if vulns is not None:
            all_vulns.extend(vulns)
            print_info(f"已加载: {input_file} ({len(vulns)} 个漏洞)")
    
    if not all_vulns:
        print_error("未加载到有效数据")
        return 1
    
    print_success(f"共加载 {len(all_vulns)} 个漏洞")
    
    # 显示统计
    print_statistics(all_vulns)
    
    if args.stats_only:
        return 0
    
    # 生成报告
    output_dir = args.output_dir or os.getcwd()
    os.makedirs(output_dir, exist_ok=True)
    
    formats_to_generate = []
    if args.format == 'all':
        formats_to_generate = ['html', 'markdown', 'text']
    else:
        fmt = 'markdown' if args.format == 'md' else ('text' if args.format == 'txt' else args.format)
        formats_to_generate = [fmt]
    
    success_count = 0
    for fmt in formats_to_generate:
        if args.output:
            output_path = args.output
        else:
            base_name = os.path.splitext(os.path.basename(args.input[0]))[0]
            output_path = os.path.join(output_dir, f"{base_name}.{fmt[:4] if fmt != 'markdown' else 'md'}")
        
        if fmt == 'html':
            if generate_html_report(all_vulns, output_path, args.title):
                success_count += 1
        elif fmt == 'markdown':
            if generate_markdown_report(all_vulns, output_path, args.title):
                success_count += 1
        elif fmt == 'text':
            if generate_text_report(all_vulns, output_path, args.title):
                success_count += 1
    
    print(f"\n{Colors.GREEN}成功生成 {success_count} 份报告{Colors.END}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
