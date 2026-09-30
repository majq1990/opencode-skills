#!/usr/bin/env python3
"""
生成钉钉文档脚本
根据DOCX解析结果生成修复方案文档（使用实际漏洞内容）
"""

import argparse
from collections import Counter
import json
import os
import re
import sys
from datetime import datetime


def _redact_sensitive_text(value):
    text = str(value or "")
    patterns = (
        (r"(?i)(password|passwd|pwd|密码)(\s*[:=]\s*)[^\s;,&]+", r"\1\2[REDACTED]"),
        (r"(?i)(token|secret|licenseKey)(\s*[:=]\s*)[^\s;,&\"]+", r"\1\2[REDACTED]"),
        (r"(?i)(Cookie:\s*)[^\"]+", r"\1[REDACTED]"),
        (r"(?i)(SESSION|JSESSIONID)(=)[^;\s]+", r"\1\2[REDACTED]"),
    )
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


def generate_doc_markdown(vuln_data, issue_url):
    """生成钉钉文档Markdown内容（使用DOCX实际内容）"""
    issue_id = vuln_data.get("issue_id", "unknown")
    vulns = vuln_data.get("vulns", [])
    stats = vuln_data.get("stats") or Counter(
        vuln.get("level", "medium") for vuln in vulns
    )
    
    instance_total = sum(_instance_count(vuln) for vuln in vulns)
    # 漏扫清单里同一型漏洞会在多台主机/多份报告各出一条，按类合并后 instances
    # 会小于原始记录数；原始记录数单独展示，不虚增也不隐瞒
    raw_total = sum(int(vuln.get("occurrences") or 1) for vuln in vulns)
    raw_note = (
        f"（{len(vulns)} 类由 {raw_total} 条原始记录合并，"
        "同型漏洞在多主机/多批次重复出现时按类出条）"
        if raw_total > len(vulns)
        else ""
    )
    source_files = sorted(
        {
            source
            for vuln in vulns
            for source in (vuln.get("source_files") or [vuln.get("source_file")])
            if source
        }
    )
    md = f"""# 安全漏洞修复方案 - 案件{issue_id}

案件号：

[{issue_url}]({issue_url})

相关的漏洞清单：

"""
    for source_file in source_files:
        md += f"- {source_file}\n"
    md += f"""
定制的修复建议：

## 一、修复总览

| 优先级 | 风险等级 | 漏洞类型 | 实例数 | 修复建议来源 |
|---|---|---|---:|---|
"""
    priority = {"critical": "P0", "high": "P1", "medium": "P2", "low": "P3"}
    level_names = {
        "critical": "严重",
        "high": "高危",
        "medium": "中危",
        "low": "低危",
        "info": "信息",
    }
    for vuln in vulns:
        sources = []
        for recommendation in vuln.get("recommendations") or []:
            source = recommendation.get("source")
            label = {
                "report": "当前报告",
                "redmine_history": "历史案件",
                "knowledge_base": "内部知识库",
                "internet": "互联网权威来源",
            }.get(source, source)
            if label and label not in sources:
                sources.append(label)
        md += (
            f"| {priority.get(vuln.get('level'), 'P3')} "
            f"| {level_names.get(vuln.get('level'), vuln.get('level', ''))} "
            f"| {vuln.get('name', '')} "
            f"| {_instance_count(vuln)} "
            f"| {'、'.join(sources) or '无额外建议'} |\n"
        )
    responsibility_stats = Counter(
        (vuln.get("responsibility") or {}).get("owner", "dev")
        for vuln in vulns
    )
    md += f"""
共识别 **{len(vulns)} 类、{instance_total} 个漏洞实例**{raw_note}。

责任分工：

- **工程中心处理**：{responsibility_stats.get('ops', 0)} 类
- **研发中心处理**：{responsibility_stats.get('dev', 0)} 类

## 二、工程中心处理

"""
    ops_vulns = [
        vuln for vuln in vulns
        if (vuln.get("responsibility") or {}).get("owner") == "ops"
    ]
    dev_vulns = [
        vuln for vuln in vulns
        if (vuln.get("responsibility") or {}).get("owner") != "ops"
    ]
    md += _render_vulnerability_section(ops_vulns, "2")
    md += """
## 三、研发中心处理

"""
    md += _render_vulnerability_section(dev_vulns, "3")
    md += """## 四、修复实施顺序

"""

    md += """1. 工程中心先完成服务器或中间件层配置，保留配置变更和重载记录。
2. 研发中心完成应用代码、鉴权、数据输出和接口逻辑修复。
3. 双方按原漏洞报告入口联合回归，确认不存在同类遗漏。
4. 所有修改完成后执行全量扫描，保存验证结果并回填 Redmine。

## 五、修复验证清单

1. 按原漏洞报告中的复现步骤逐项验证。
2. 检查所有同类接口，确认修复不是仅针对单个测试参数。
3. 使用漏洞扫描工具执行全量扫描。
4. 保存修复版本、配置变更、验证结果和扫描报告。

"""
    return md


def _render_vulnerability_section(vulns, section_number):
    if not vulns:
        return "无。\n\n"
    md = ""
    for i, vuln in enumerate(vulns, 1):
        level_display = {
            'critical': '严重',
            'high': '高危',
            'medium': '中危',
            'low': '低危',
            'info': '信息'
        }.get(vuln['level'], vuln['level'])
        
        responsibility = vuln.get("responsibility") or {}
        md += f"""### {section_number}.{i} {vuln['name']}（{level_display}）

**责任判定**
{responsibility.get('owner_name', '研发中心')}，{responsibility.get('reason', '应用实现确认')}。

"""
        
        if vuln.get('description'):
            md += f"""**漏洞描述**
{_redact_sensitive_text(vuln['description'])}

"""
        
        if vuln.get('harm'):
            md += f"""**漏洞危害**
{_redact_sensitive_text(vuln['harm'])}

"""
        
        if vuln.get('test_process'):
            md += f"""**测试过程**
{_redact_sensitive_text(vuln['test_process'])}

"""
        
        if vuln.get('urls'):
            md += """**涉及URL**
"""
            for url in vuln['urls']:
                md += f"- {url}\n"
            md += "\n"
        
        recommendations = vuln.get("recommendations") or []
        if recommendations:
            md += "**修复建议（按来源优先级）**\n"
            source_names = {
                "report": "当前漏洞报告",
                "redmine_history": "历史安全案件",
                "knowledge_base": "内部知识库",
                "internet": "互联网权威来源",
            }
            for recommendation in recommendations:
                source = source_names.get(
                    recommendation.get("source"), recommendation.get("source", "未知来源")
                )
                md += f"- **{source}**：{recommendation.get('suggestion', '')}\n"
                reference = recommendation.get("reference") or {}
                if reference.get("issue_id"):
                    md += (
                        f"  - 参考案件："
                        f"https://faq.egova.com.cn:7787/issues/{reference['issue_id']}\n"
                    )
                if reference.get("url"):
                    md += f"  - 参考文档：{reference['url']}\n"
            md += "\n"
        elif vuln.get('fix_suggestion'):
            md += f"""**加固建议（当前漏洞报告）**
{vuln['fix_suggestion']}

"""

        web_search = vuln.get("web_search") or {}
        if web_search.get("required"):
            md += f"""**待互联网检索**
- 查询词：{web_search.get('query', '')}
- 原因：{web_search.get('reason', '')}

"""
        elif web_search.get("reason"):
            md += f"""**检索策略**
{web_search.get('reason', '')}

"""
        
        md += """---

"""
    
    return md


def _instance_count(vuln):
    """一"类"漏洞背后的实例数。

    优先用解析阶段带上来的实例数列；其次从名称的 `*N` 写法（漏扫表常用）
    和描述的"共 N 例"里取；都取不到按 1 个计。
    """
    if not isinstance(vuln, dict):
        return _instance_count({"name": vuln})
    count = vuln.get("instances")
    if isinstance(count, int) and count > 0:
        return count
    for text in (vuln.get("name"), vuln.get("description")):
        found = re.search(r"(\d+)\s*例", str(text or ""))
        if found and int(found.group(1)) > 0:
            return int(found.group(1))
    found = re.search(r"\*(\d+)", str(vuln.get("name") or ""))
    return int(found.group(1)) if found else 1


def main():
    parser = argparse.ArgumentParser(description="生成钉钉文档")
    parser.add_argument("vuln_json", help="漏洞解析结果JSON文件")
    parser.add_argument("--issue-url", default=None, help="Redmine案件链接")
    parser.add_argument("--output", "-o", default=None, help="输出Markdown文件路径")
    
    args = parser.parse_args()
    
    with open(args.vuln_json, "r", encoding="utf-8") as f:
        vuln_data = json.load(f)
    
    issue_id = vuln_data.get("issue_id", "unknown")
    if not args.issue_url:
        args.issue_url = f"https://faq.egova.com.cn:7787/issues/{issue_id}"
    
    md_content = generate_doc_markdown(vuln_data, args.issue_url)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"Document saved to {args.output}")
    else:
        print(md_content)


if __name__ == "__main__":
    main()
