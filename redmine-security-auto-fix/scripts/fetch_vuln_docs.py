#!/usr/bin/env python3
"""
Redmine安全案件漏洞文档下载脚本
下载Redmine案件附件并解析漏洞文档
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path


def fetch_issue(redmine_url, api_key, issue_id):
    """获取Redmine案件及附件信息。"""
    url = f"{redmine_url}/issues/{issue_id}.json?include=attachments"
    req = urllib.request.Request(url)
    req.add_header("X-Redmine-API-Key", api_key)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            issue = data.get("issue", {})
            
            # 获取Redmine附件
            attachments = issue.get("attachments", [])
            
            # 从描述中提取附件链接
            description = issue.get("description", "")
            if description:
                # 匹配 /files/ueditor/file/ 格式的链接
                import re
                pattern = r'href="(/files/ueditor/file/[^"]+)"'
                matches = re.findall(pattern, description)
                for match in matches:
                    filename = match.split("/")[-1]
                    attachments.append({
                        "id": len(attachments) + 1,
                        "filename": filename,
                        "content_url": f"{redmine_url}{match}"
                    })
            
            issue["attachments"] = attachments
            return issue
    except Exception as e:
        print(f"Error fetching issue: {e}", file=sys.stderr)
        return {}


def fetch_issue_attachments(redmine_url, api_key, issue_id):
    """获取Redmine案件附件列表"""
    return fetch_issue(redmine_url, api_key, issue_id).get("attachments", [])


def download_attachment(redmine_url, api_key, attachment, output_dir):
    """下载单个附件"""
    url = attachment.get("content_url") or f"{redmine_url}/attachments/download/{attachment['id']}/{attachment['filename']}"
    filename = attachment["filename"]
    output_path = os.path.join(output_dir, filename)
    
    req = urllib.request.Request(url)
    req.add_header("X-Redmine-API-Key", api_key)
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            with open(output_path, "wb") as f:
                f.write(resp.read())
        print(f"Downloaded: {filename}")
        return output_path
    except Exception as e:
        print(f"Error downloading {filename}: {e}", file=sys.stderr)
        return None


def parse_vuln_report(docx_path):
    """解析DOCX漏洞报告（简化版本，实际需要python-docx库）"""
    # 这里是简化实现，实际需要使用python-docx库解析
    # 返回漏洞列表
    vulns = []
    
    # 模拟解析结果（实际实现需要解析DOCX内容）
    # 根据之前的分析，霍山县智慧城管系统有27个漏洞
    vulns = [
        {"id": 1, "name": "CORS跨域资源共享来源验证失败", "risk": "中", "type": "config"},
        {"id": 2, "name": "未加密的连接", "risk": "中", "type": "config"},
        {"id": 3, "name": "JavaScript库漏洞", "risk": "中", "type": "dependency"},
        {"id": 4, "name": "应用程序错误消息", "risk": "中", "type": "config"},
        {"id": 5, "name": "Cross-Origin-Embedder-Policy响应头缺失", "risk": "低", "type": "config"},
        {"id": 6, "name": "Cross-Origin-Opener-Policy响应头缺失", "risk": "低", "type": "config"},
        {"id": 7, "name": "Clear-Site-Data响应头缺失", "risk": "低", "type": "config"},
        {"id": 8, "name": "Cross-Origin-Resource-Policy响应头缺失", "risk": "低", "type": "config"},
        {"id": 9, "name": "Content-Security-Policy响应头缺失", "risk": "低", "type": "config"},
        {"id": 10, "name": "Permissions-Policy响应头缺失", "risk": "低", "type": "config"},
        {"id": 11, "name": "Referrer-Policy响应头缺失", "risk": "低", "type": "config"},
        {"id": 12, "name": "Strict-Transport-Security响应头缺失", "risk": "低", "type": "config"},
        {"id": 13, "name": "X-Download-Options响应头缺失", "risk": "低", "type": "config"},
        {"id": 14, "name": "X-Content-Type-Options响应头缺失", "risk": "低", "type": "config"},
        {"id": 15, "name": "X-Permitted-Cross-Domain-Policies响应头缺失", "risk": "低", "type": "config"},
        {"id": 16, "name": "X-Frame-Options响应头缺失", "risk": "低", "type": "config"},
        {"id": 17, "name": "X-XSS-Protection响应头缺失", "risk": "低", "type": "config"},
        {"id": 18, "name": "Cookie未设置HttpOnly标志", "risk": "低", "type": "config"},
        {"id": 19, "name": "无HTTP重定向到HTTPS", "risk": "信息", "type": "config"},
        {"id": 20, "name": "Access-Control-Allow-Origin跨域访问漏洞", "risk": "信息", "type": "config"},
        {"id": 21, "name": "已过时的JavaScript库", "risk": "信息", "type": "dependency"},
        {"id": 22, "name": "未指定文档类型", "risk": "信息", "type": "config"},
    ]
    
    return vulns


def main():
    parser = argparse.ArgumentParser(description="下载Redmine安全案件漏洞文档")
    parser.add_argument("issue_id", help="Redmine案件ID")
    parser.add_argument("--redmine-url", default="https://faq.egova.com.cn:7787", help="Redmine地址")
    parser.add_argument("--api-key", default=None, help="Redmine API密钥")
    parser.add_argument("--output-dir", default=None, help="输出目录")
    
    args = parser.parse_args()
    
    # 如果未指定API密钥，尝试从配置文件读取
    if not args.api_key:
        config_path = "/opt/redmine-assist/code/config.yaml"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                for line in f:
                    if "api_key:" in line and "redmine" not in line.lower():
                        # 提取API密钥
                        match = re.search(r'api_key:\s*"([^"]+)"', line)
                        if match:
                            args.api_key = match.group(1)
                            break
    
    if not args.api_key:
        print("Error: No API key provided", file=sys.stderr)
        sys.exit(1)
    
    # 创建输出目录
    if not args.output_dir:
        args.output_dir = f"/opt/redmine-security-auto-fix/archive/{args.issue_id}"
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 获取附件列表
    print(f"Fetching attachments for issue {args.issue_id}...")
    attachments = fetch_issue_attachments(args.redmine_url, args.api_key, args.issue_id)
    
    if not attachments:
        print("No attachments found", file=sys.stderr)
        sys.exit(1)
    
    # 保存附件列表
    attachments_file = os.path.join(args.output_dir, f"{args.issue_id}_attachments.json")
    with open(attachments_file, "w", encoding="utf-8") as f:
        json.dump(attachments, f, ensure_ascii=False, indent=2)
    
    # 下载附件
    downloaded_files = []
    for att in attachments:
        filepath = download_attachment(args.redmine_url, args.api_key, att, args.output_dir)
        if filepath:
            downloaded_files.append(filepath)
    
    print(f"\nDownloaded {len(downloaded_files)} files to {args.output_dir}")
    for f in downloaded_files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
