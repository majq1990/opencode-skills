---
name: elevator-data-validation
description: Residential elevator data validation for old elevator renovation projects. Validates data completeness, time logic, uniqueness constraints, and cross-field consistency according to official specifications.
license: MIT
compatibility: opencode
metadata:
  category: data-validation
  domain: elevator-renovation
  features: data-validation, completeness-check, time-logic-check, uniqueness-check, cross-field-validation
---

## 功能概述

电梯数据校验 Skill 用于对住宅老旧电梯更新改造项目数据进行全面校验，确保数据符合官方规范要求。

### 适用范围

- 住宅老旧电梯更新改造项目数据校验
- 批量 Excel 数据质量检查
- 数据完整性、逻辑性、一致性验证

### 校验内容

1. **基础信息校验** - 必填字段、数据类型、范围检查
2. **开工信息校验** - 开工时间必填性检查
3. **完工信息校验** - 完工时间、投资、设备信息必填性检查
4. **时间逻辑校验** - 完工时间必须严格大于开工时间
5. **跨字段校验** - 设备代码唯一性、报告编号唯一性

## 数据规格

### 字段映射

| 列索引 | 字段名称 | 数据类型 | 校验规则 |
|--------|----------|----------|----------|
| 0 | 地区 | 字符型 | 必填 |
| 1 | 城市 | 字符型 | 必填 |
| 2 | 设备使用地址 | 字符型 | 必填 |
| 3 | 楼栋号 | 数值型 | >= 2 |
| 4 | 所在单元居民户数 | 数值型 | >= 0 |
| 5 | 更新改造前设备代码 | 字符型 | 全局唯一 |
| 6 | 更新改造前使用登记日期 | 日期型 | 有效日期 |
| 7 | 项目位置 | 字符型 | 必填 |
| 8 | 是否开工 | 字符型 | "是" 或 "否" |
| 9 | 开工时间 | 日期型 | 当"是否开工"="是"时必填 |
| 10 | 是否完工 | 字符型 | "是" 或 "否" |
| 11 | 完工时间 | 日期型 | 当"是否完工"="是"时必填 |
| 12 | 计划投资（万元） | 数值型 | > 15 |
| 13 | 实际完成投资（万元） | 数值型 | 当完工时 > 15 |
| 14 | 更新改造后的电梯制造单位名称及型号 | 字符型 | 当完工时必填 |
| 15 | 更新改造后设备代码 | 字符型 | 当完工时必填，全局唯一 |
| 16 | 监督检验合格报告编号 | 字符型 | 非2024年批次时必填且唯一 |
| 17 | 年份批次 | 字符型 | "2024年批次" 或 "2025年批次" |
| 18 | 备注 | 字符型 | 可选 |

## 校验规则

### 规则1: 基础信息必填检查

```python
# 1-1: 地区必填
if df['地区'].isna() or df['地区'].str.strip() == '':
    issues.append((row_num, '地区为空', '基础信息'))

# 1-2: 城市必填
if df['城市'].isna() or df['城市'].str.strip() == '':
    issues.append((row_num, '城市为空', '基础信息'))

# 1-3: 设备使用地址必填
if df['设备使用地址'].isna() or df['设备使用地址'].str.strip() == '':
    issues.append((row_num, '设备使用地址为空', '基础信息'))

# 1-4: 层数 >= 2
if df['楼栋号'] < 2:
    issues.append((row_num, f'层数({value})<2', '基础信息'))
```

### 规则2: 设备代码唯一性

```python
# 1-5: 更新改造前设备代码全局唯一
duplicates = df[df.duplicated(subset=['更新改造前设备代码'], keep=False)]
for code in duplicates['更新改造前设备代码']:
    issues.append((row_num, '更新改造前设备代码重复', '基础信息-唯一性'))
```

### 规则3: 开工信息校验

```python
# 2-1: 已开工但缺少开工时间
if df['是否开工'] == '是' and pd.isna(df['开工时间']):
    issues.append((row_num, '已开工但缺少开工时间', '开工信息'))
```

### 规则4: 完工信息校验

```python
# 3-1: 已完工但缺少完工时间
if df['是否完工'] == '是' and pd.isna(df['完工时间']):
    issues.append((row_num, '已完工但缺少完工时间', '完工信息'))

# 3-2: 计划投资 > 15万元
if df['计划投资（万元）'] <= 15:
    issues.append((row_num, f'计划投资({value})<=15万元', '完工信息-投资'))

# 3-3: 实际完成投资 - 完工时必填且 > 15
if df['是否完工'] == 's':
    if pd.isna(df['实际完成投资（万元）']) or df['实际完成投资（万元）'] <= 15:
        issues.append((row_num, f'实际完成投资({value})<=15万元', '完工信息-投资'))

# 3-4: 制造单位 - 完工时必填
if df['是否完工'] == '是' and pd.isna(df['更新改造后的电梯制造单位名称及型号']):
    issues.append((row_num, '已完工但缺少制造单位', '完工信息'))

# 3-5: 更新后设备代码 - 完工时必填
if df['是否完工'] == '是' and pd.isna(df['更新改造后设备代码']):
    issues.append((row_num, '已完工但缺少更新后设备代码', '完工信息'))
```

### 规则5: 时间逻辑校验

```python
# 4-1: 完工时间必须严格大于开工时间
if df['是否完工'] == '是' and not pd.isna(df['完工时间']) and not pd.isna(df['开工时间']):
    start_date = pd.to_datetime(df['开工时间'])
    end_date = pd.to_datetime(df['完工时间'])
    if end_date <= start_date:
        issues.append((row_num, f'完工时间({end})<=开工时间({start})', '时间逻辑'))
```

### 规则6: 跨字段唯一性校验

```python
# 5-1: 更新后设备代码与更新前不能相同
if not pd.isna(df['更新改造后设备代码']) and not pd.isna(df['更新改造前设备代码']):
    if df['更新改造后设备代码'] == df['更新改造前设备代码']:
        issues.append((row_num, '更新前后设备代码相同', '设备代码-跨字段'))

# 5-2: 更新后设备代码全局唯一
dup_after = df[df.duplicated(subset=['更新改造后设备代码'], keep=False)]
for code in dup_after['更新改造后设备代码']:
    issues.append((row_num, '更新后设备代码重复', '设备代码-唯一性'))

# 5-3: 监督检验报告编号全局唯一（排除2024年批次）
if df['年份批次'] != '2024年批次' and not pd.isna(df['监督检验合格报告编号']):
    dup_report = df[df.duplicated(subset=['监督检验合格报告编号'], keep=False)]
    for code in dup_report['监督检验合格报告编号']:
        issues.append((row_num, '监督检验报告编号重复', '报告编号-唯一性'))
```

## 实现代码

### 完整校验脚本

```python
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime
import os

def validate_elevator_data(excel_path, output_dir=None):
    """
    电梯数据校验主函数
    
    参数:
        excel_path: Excel文件路径
        output_dir: 输出目录（可选）
    
    返回:
        issues_df: 问题记录DataFrame
        summary: 校验摘要
    """
    
    # 读取Excel（跳过前2行：标题和元数据）
    df = pd.read_excel(excel_path, header=2)
    
    # 列名映射（从第3行实际列名）
    col_names = [
        '地区', '城市', '设备使用地址', '楼栋号', '所在单元居民户数', 
        '更新改造前设备代码', '更新改造前使用登记日期', '项目位置',
        '是否开工', '开工时间', '是否完工', '完工时间', 
        '计划投资（万元）', '实际完成投资（万元）',
        '更新改造后的电梯制造单位名称及型号', '更新改造后设备代码',
        '监督检验合格报告编号', '年份批次', '备注'
    ]
    df.columns = col_names
    
    # 添加原始行号
    df['_原始行号'] = range(3, len(df) + 3)
    
    # 问题记录存储
    all_issues = []
    
    def parse_date(x):
        if pd.isna(x):
            return None
        try:
            return pd.to_datetime(x)
        except:
            return None
    
    # === 开始校验 ===
    
    # 1. 基础信息校验
    # 1-1~1-3: 必填字段
    for col, name in [('地区', '地区'), ('城市', '城市'), ('设备使用地址', '设备使用地址')]:
        mask = df[col].isna() | (df[col].astype(str).str.strip() == '')
        for idx in df[mask].index:
            all_issues.append((df.loc[idx, '_原始行号'], f'{name}为空', '基础信息'))
    
    # 1-4: 层数 >= 2
    mask = df['楼栋号'] < 2
    for idx in df[mask].index:
        all_issues.append((df.loc[idx, '_原始行号'], 
            f'层数({df.loc[idx,"楼栋号"]})<2', '基础信息'))
    
    # 1-5: 更新改造前设备代码唯一性
    dup_codes = df[df.duplicated(subset=['更新改造前设备代码'], keep=False)]
    dup_code_set = set(dup_codes['更新改造前设备代码'].dropna())
    for idx in df[df['更新改造前设备代码'].isin(dup_code_set)].index:
        all_issues.append((df.loc[idx, '_原始行号'], 
            '更新改造前设备代码重复', '基础信息-唯一性'))
    
    # 2. 开工信息校验
    started = df[df['是否开工'] == '是'].copy()
    mask = started['开工时间'].isna()
    for idx in started[mask].index:
        all_issues.append((df.loc[idx, '_原始行号'], 
            '已开工但缺少开工时间', '开工信息'))
    
    # 3. 完工信息校验
    completed = df[df['是否完工'] == '是'].copy()
    
    # 3-1: 完工时间必填
    mask = completed['完工时间'].isna()
    for idx in completed[mask].index:
        all_issues.append((df.loc[idx, '_原始行号'], 
            '已完工但缺少完工时间', '完工信息'))
    
    # 3-2: 计划投资 > 15
    mask = df['计划投资（万元）'] <= 15
    for idx in df[mask].index:
        all_issues.append((df.loc[idx, '_原始行号'], 
            f'计划投资({df.loc[idx,"计划投资（万元）"]})<=15万元', '完工信息-投资'))
    
    # 3-3: 实际完成投资 > 15（完工时）
    mask = (completed['实际完成投资（万元）'] <= 15) | (completed['实际完成投资（万元）'].isna())
    for idx in completed[mask].index:
        all_issues.append((df.loc[idx, '_原始行号'], 
            f'实际完成投资({df.loc[idx,"实际完成投资（万元）"]})<=15万元', '完工信息-投资'))
    
    # 3-4: 制造单位必填
    mask = completed['更新改造后的电梯制造单位名称及型号'].isna()
    for idx in completed[mask].index:
        all_issues.append((df.loc[idx, '_原始行号'], 
            '已完工但缺少制造单位', '完工信息'))
    
    # 3-5: 更新后设备代码必填
    mask = completed['更新改造后设备代码'].isna()
    for idx in completed[mask].index:
        all_issues.append((df.loc[idx, '_原始行号'], 
            '已完工但缺少更新后设备代码', '完工信息'))
    
    # 4. 时间逻辑校验
    completed['开工日期'] = completed['开工时间'].apply(parse_date)
    completed['完工日期'] = completed['完工时间'].apply(parse_date)
    valid_dates = completed[(completed['开工日期'].notna()) & (completed['完工日期'].notna())]
    time_error = valid_dates[valid_dates['完工日期'] <= valid_dates['开工日期']]
    for idx in time_error.index:
        start = df.loc[idx, '开工时间']
        end = df.loc[idx, '完工时间']
        all_issues.append((df.loc[idx, '_原始行号'], 
            f'完工时间({end})<=开工时间({start})', '时间逻辑'))
    
    # 5. 跨字段校验
    # 5-1: 更新前后代码不能相同
    mask = (df['更新改造后设备代码'].notna()) & (df['更新改造前设备代码'].notna()) & \
           (df['更新改造后设备代码'] == df['更新改造前设备代码'])
    for idx in df[mask].index:
        all_issues.append((df.loc[idx, '_原始行号'], 
            '更新前后设备代码相同', '设备代码-跨字段'))
    
    # 5-2: 更新后代码全局唯一
    after_codes = df[df['更新改造后设备代码'].notna()]
    dup_after = after_codes[after_codes.duplicated(subset=['更新改造后设备代码'], keep=False)]
    dup_after_set = set(dup_after['更新改造后设备代码'].dropna())
    for idx in df[df['更新改造后设备代码'].isin(dup_after_set)].index:
        all_issues.append((df.loc[idx, '_原始行号'], 
            '更新后设备代码重复', '设备代码-唯一性'))
    
    # 5-3: 监督检验报告编号唯一（排除2024年批次）
    non_2024 = df[df['年份批次'] != '2024年批次']
    report_nos = non_2024[non_2024['监督检验合格报告编号'].notna()]
    dup_reports = report_nos[report_nos.duplicated(subset=['监督检验合格报告编号'], keep=False)]
    dup_report_set = set(dup_reports['监督检验合格报告编号'].dropna())
    for idx in df[df['监督检验合格报告编号'].isin(dup_report_set)].index:
        all_issues.append((df.loc[idx, '_原始行号'], 
            '监督检验报告编号重复', '报告编号-唯一性'))
    
    # === 生成结果 ===
    issues_df = pd.DataFrame(all_issues, columns=['Excel行号', '问题描述', '问题类别'])
    
    total_rows = len(df)
    passed = len(df) - len(issues_df['Excel行号'].unique())
    failed = total_rows - passed
    
    summary = {
        'total': total_rows,
        'passed': passed,
        'failed': failed,
        'pass_rate': f'{passed/total_rows*100:.2f}%',
        'issues_by_type': {}
    }
    
    # 按问题类型统计
    from collections import Counter
    issue_counts = Counter([issue[1] for issue in all_issues])
    summary['issues_by_type'] = dict(issue_counts)
    
    return issues_df, summary


def generate_report(issues_df, summary, output_path):
    """生成Markdown报告"""
    
    report = f"""# 住宅老旧电梯更新改造项目 数据校验报告

## 校验概要
- **校验时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **总记录数**: {summary['total']:,}

## 校验结果
- **通过**: {summary['passed']:,} 条 ({summary['pass_rate']})
- **不通过**: {summary['failed']:,} 条

## 问题分类统计
| 问题类型 | 数量 |
|---------|------|
"""
    for issue, count in sorted(summary['issues_by_type'].items(), key=lambda x: -x[1]):
        report += f"| {issue} | {count} |\n"
    
    report += """
## 校验规则说明

### 基础信息类
1. 地区 - 字符型，必填
2. 城市 - 字符型，必填
3. 设备使用地址 - 字符型，必填
4. 层数 - 数值型，必须 >= 2
5. 更新改造前设备代码 - 唯一值，不可重复

### 开工信息类
- 开工时间 - 仅当"是否开工"为"是"时必填

### 完工信息类
- 完工时间 - 仅当"是否完工"为"是"时必填
- 计划投资（万元）- 必须 > 15万元
- 实际完成投资（万元）- 当"是否完工"为"是"时，必须 > 15万元
- 更新改造后的电梯制造单位名称及型号 - 仅当"是否完工"为"是"时必填
- 更新改造后设备代码 - 仅当"是否完工"为"是"时必填

### 时间逻辑校验
- 完工时间必须严格大于开工时间

### 跨字段校验
- 更新后设备代码与更新前设备代码不能相同
- 更新改造前/后设备代码全局唯一
- 监督检验合格报告编号（除2024年外）全局唯一
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return report
```

## 使用示例

### 基本用法

```python
from elevator_data_validation import validate_elevator_data, generate_report

# 校验数据
issues_df, summary = validate_elevator_data(
    excel_path='D:/data/电梯数据.xlsx',
    output_dir='D:/output'
)

# 打印摘要
print(f"总记录数: {summary['total']}")
print(f"通过: {summary['passed']}")
print(f"不通过: {summary['failed']}")
print(f"通过率: {summary['pass_rate']}")

# 生成报告
report = generate_report(issues_df, summary, 'D:/output/校验报告.md')
```

### 命令行用法

```bash
# 校验Excel文件
python validate_elevator.py --input D:/data/电梯数据.xlsx --output D:/output/

# 指定输出格式
python validate_elevator.py --input D:/data/电梯数据.xlsx --format excel,markdown
```

## 输出文件

校验完成后生成以下文件：

1. **数据校验结果_全部问题记录.xlsx** - 所有问题记录的详细列表
2. **数据校验分析报告.md** - 问题分类统计和校验规则说明

## 何时使用此Skill

当用户需要：
- 对电梯更新改造项目数据进行质量检查
- 发现数据完整性问题
- 验证时间逻辑一致性
- 检查设备代码和报告编号的唯一性
- 生成数据校验报告

## 注意事项

1. Excel文件的前2行必须是标题和元数据（文件创建时间等），数据从第3行开始
2. 列名可能出现编码问题（如乱码），脚本会自动处理并使用正确的列索引
3. 校验耗时约 2-3 分钟（基于167,000条记录）
4. 建议在校验前备份原始数据
