#!/usr/bin/env python3
"""
通途PBC数据导入工具
用法: python import_pbc.py <excel_file> [--year 2025] [--clear] [--dry-run]
"""

import requests
import json
import pandas as pd
import argparse
import time
import os
from datetime import datetime

# 配置
BASE_URL = "https://ztoa.egova.com.cn"
APP_KEY = os.environ.get("ZTOA_APP_KEY", "170164d8484313dc")
SIGN = os.environ.get("ZTOA_SIGN", "YjU2OWM4YTU4MmFkZjc3Nzc4ZGViOTY5ZDEwOTk3YjNiZTE5ZjcwMGNjNmI0NmRiY2Q3ZWQzYmE2MGE5NmIzYQ==")

# 日志文件
LOG_FILE = r"D:\opencode\file\tongtu_pbc_operations.log"

# 字段ID
FIELDS = {
    "gonghao": "64194b73a35db665c3115934",
    "date": "64194bcd210ef681d9895b28",
    "year": "64194ce0210ef681d9895b95",
    "person": "64194bcd210ef681d9895b29",
    "pbc_level": "64194bcd210ef681d9895b2a"
}

WORKSHEET_ID = "gcpbcb"


def log_operation(op_type, detail, success=True):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "成功" if success else "失败"
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{op_type}] {detail} 结果:{status}\n")


def query_data(year=None, page_size=1000):
    """查询PBC数据"""
    payload = {
        "appKey": APP_KEY,
        "sign": SIGN,
        "worksheetId": WORKSHEET_ID,
        "pageSize": page_size,
        "pageIndex": 1
    }
    
    if year:
        payload["filters"] = [{
            "controlId": FIELDS["year"],
            "dataType": 6,
            "spliceType": 1,
            "filterType": 3,
            "value": str(year)
        }]
    
    response = requests.post(
        f"{BASE_URL}/api/v2/open/worksheet/getFilterRows",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    
    return response.json()


def delete_row(row_id):
    response = requests.post(
        f"{BASE_URL}/api/v2/open/worksheet/deleteRow",
        json={
            "appKey": APP_KEY,
            "sign": SIGN,
            "worksheetId": WORKSHEET_ID,
            "rowId": row_id
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    result = response.json()
    log_operation("DELETE", f"rowId:{row_id}", result.get("success"))
    return result


def add_row(gonghao, date, year, pbc_level):
    controls = [
        {"controlId": FIELDS["gonghao"], "value": str(gonghao)},
        {"controlId": FIELDS["date"], "value": date},
        {"controlId": FIELDS["year"], "value": year},
        {"controlId": FIELDS["person"], "value": str(gonghao)},
        {"controlId": FIELDS["pbc_level"], "value": pbc_level}
    ]
    
    response = requests.post(
        f"{BASE_URL}/api/v2/open/worksheet/addRow",
        json={
            "appKey": APP_KEY,
            "sign": SIGN,
            "worksheetId": WORKSHEET_ID,
            "controls": controls
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    result = response.json()
    log_operation("ADD", f"工号:{gonghao} 年份:{year} 职级:{pbc_level}", result.get("success"))
    return result


def clear_year_data(year):
    """清理指定年份的数据"""
    print(f"正在查询{year}年数据...")
    data = query_data(year=year)
    
    if not data.get("data") or not data["data"].get("rows"):
        print(f"未找到{year}年数据")
        return 0
    
    rows = data["data"]["rows"]
    print(f"找到{len(rows)}条{year}年数据")
    
    deleted = 0
    for row in rows:
        row_id = row.get("rowid")
        if row_id:
            result = delete_row(row_id)
            if result.get("success"):
                deleted += 1
            time.sleep(0.05)
    
    print(f"已删除{deleted}条")
    return deleted


def import_excel(excel_path, clear_existing=False, dry_run=False):
    """从Excel导入数据"""
    print(f"读取Excel: {excel_path}")
    
    # 读取Excel
    df = pd.read_excel(excel_path)
    print(f"数据行数: {len(df)}")
    
    # 验证列名
    required_cols = ['工号', 'PBC归属年份(年)', 'PBC职级']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"错误: 缺少列 {missing}")
        return
    
    # 获取年份
    year = int(df['PBC归属年份(年)'].dropna().iloc[0]) if 'PBC归属年份(年)' in df.columns else 2025
    
    if dry_run:
        print(f"\n[DRY-RUN] 将导入{len(df)}条{year}年数据")
        print("\n前5条预览:")
        for idx, row in df.head(5).iterrows():
            print(f"  工号:{row['工号']} | 姓名:{row.get('人员', 'N/A')} | 职级:{row['PBC职级']}")
        return
    
    # 清理现有数据
    if clear_existing:
        clear_year_data(year)
    
    # 导入数据
    success = 0
    fail = 0
    skip = 0
    
    for idx, row in df.iterrows():
        gonghao = str(int(row['工号'])) if pd.notna(row['工号']) else None
        pbc_level = row['PBC职级'] if pd.notna(row['PBC职级']) else None
        
        # 更新日期
        update_date = datetime.now().strftime('%Y-%m-%d')
        if pd.notna(row.get('更新日期')):
            if hasattr(row['更新日期'], 'strftime'):
                update_date = row['更新日期'].strftime('%Y-%m-%d')
        
        if not gonghao or gonghao == "None":
            skip += 1
            continue
        
        result = add_row(gonghao, update_date, year, pbc_level)
        
        if result.get("success") or result.get("data"):
            success += 1
        else:
            fail += 1
            print(f"  失败: 工号{gonghao} - {result.get('error_msg')}")
        
        time.sleep(0.05)
    
    print(f"\n=== 导入完成 ===")
    print(f"成功: {success}")
    print(f"失败: {fail}")
    print(f"跳过: {skip}")
    
    log_operation("IMPORT", f"文件:{os.path.basename(excel_path)} 年份:{year} 成功:{success} 失败:{fail} 跳过:{skip}")


def main():
    parser = argparse.ArgumentParser(description='通途PBC数据导入工具')
    parser.add_argument('excel', help='Excel文件路径')
    parser.add_argument('--year', type=int, help='指定年份')
    parser.add_argument('--clear', action='store_true', help='导入前清理同年度数据')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不实际导入')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.excel):
        print(f"错误: 文件不存在 {args.excel}")
        return
    
    import_excel(args.excel, clear_existing=args.clear, dry_run=args.dry_run)


if __name__ == '__main__':
    main()