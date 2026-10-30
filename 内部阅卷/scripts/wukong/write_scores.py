#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""悟空阅卷表批量写入。

用法:
  python write_scores.py --sheet <sheetId> --col <起始扣分列> --rows rows.json [--dry-run]
  rows.json 格式: [["扣分","扣分说明"], ...] 共 36 行（对应阅卷表 4-39 行）

列位: 马健权 F/G/H、郭跃增 I/J/K、陈马钦 L/M/N、考官4 O/P/Q、考官5 R/S/T、吴贺添 U/V/W
（每考生 3 列：扣分/扣分说明/得分；得分列是公式不用写）

示例:
  python write_scores.py --sheet st-245b4f16-8174 --col I --rows song.json
"""
import argparse
import json
import subprocess
import sys

NODE_BIN = 'node'
DWS_JS = r'C:\Users\majq1\AppData\Roaming\npm\node_modules\dingtalk-workspace-cli\bin\dws.js'
NODE = 'ZX6GRezwJl7Dba5Kijdk17GPVdqbropQ'


def dws(args, timeout=90):
    r = subprocess.run([NODE_BIN, DWS_JS] + args, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=timeout)
    return r.returncode == 0, (r.stdout or '') + (r.stderr or '')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sheet', required=True)
    ap.add_argument('--col', required=True, help='扣分列字母，如 F/I/L/O/R/U')
    ap.add_argument('--rows', required=True, help='rows.json 路径')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    rows = json.load(open(args.rows, encoding='utf-8'))
    if len(rows) != 36:
        print(f'WARN: rows 数量 {len(rows)} != 36（应为 4-39 行）')
    col = args.col.upper()
    next_col = chr(ord(col) + 1)
    rng = f'{col}4:{next_col}39'
    vals = [[{'type': 'text', 'text': str(d)}, {'type': 'text', 'text': str(n)}] for d, n in rows]

    if args.dry_run:
        for i, (d, n) in enumerate(rows, start=4):
            print(f'{i}: 扣{d} | {n[:60]}')
        total = sum(float(d) for d, _ in rows)
        print(f'合计扣分: {total}  得分: {100 - total}')
        return

    ok, out = dws(['sheet', 'range', 'update', '--node', NODE, '--sheet-id', args.sheet,
                   '--range', rng, '--values', json.dumps(vals, ensure_ascii=False),
                   '--yes', '--format', 'json'])
    print('write:', ok, out[:150])
    if not ok:
        sys.exit(1)

    ok2, out2 = dws(['sheet', 'range', 'read', '--node', NODE, '--sheet-id', args.sheet,
                     '--range', f'{col}3:{chr(ord(col) + 2)}3', '--format', 'json'])
    try:
        d = json.loads(out2[out2.index('{'):out2.rindex('}') + 1])
        row = d.get('cells', [[]])[0]
        print('回读合计:', row[0].get('value'), '| 得分:', row[2].get('value'))
    except Exception:
        print('回读失败，原始输出:', out2[:300])


if __name__ == '__main__':
    main()
