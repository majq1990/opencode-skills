#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""证据包生成器（认证用）：依次跑 skill 关键命令，收集日志/产物/截图到 evidence/。

用法: python scripts/collect_run_evidence.py [--out-dir evidence]
产物: evidence/transcript_utf8.txt（全链路日志）、evidence/products/*（生成物）、
      evidence/map_preview.png（地图HTML截图，需 playwright）。
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent      # skill 根目录
TDT = HERE / "scripts" / "tdt.py"
EVID = HERE / "evidence"

# 每一步: (名称, 命令列表, 产物文件列表)
STEPS = [
    ("01_keys_查看key池", ["python", str(TDT), "keys"], []),
    ("02_geocode_地址转坐标", ["python", str(TDT), "geocode", "宁夏银川市西夏小区15-1-203"], []),
    ("03_reverse_逆地理编码", ["python", str(TDT), "reverse", "106.10047", "38.48822"], []),
    ("04_search_POI搜索", ["python", str(TDT), "search", "超市", "--map-bound", "106.1,38.4,106.4,38.6", "--count", "3"], []),
    ("05_batch_批量编码_待复核", ["python", str(TDT), "batch",
        str(HERE / "assets" / "sample_addresses.csv"),
        "--col", "address", "--out", str(EVID / "products" / "batch_out.csv"),
        "--prefix", "宁夏银川市", "--encoding", "utf-8-sig"],
        ["products/batch_out.csv", "products/batch_out.csv.review.md"]),
    ("06_applydb_预览门禁", ["python", str(TDT), "apply-db",
        str(EVID / "products" / "batch_out.csv"),
        "--table", "iotbase.iot_equip_info", "--key-cols", "equip_name,address",
        "--coord-cols", "lon,lat"], []),
    ("07_applydb_非法表名拦截", ["python", str(TDT), "apply-db",
        str(EVID / "products" / "batch_out.csv"),
        "--table", "iot_equip_info;drop table", "--key-cols", "a,b", "--coord-cols", "lon,lat"], []),
    ("08_applydb_无DSN停止", ["python", str(TDT), "apply-db",
        str(EVID / "products" / "batch_out.csv"),
        "--table", "iotbase.iot_equip_info", "--key-cols", "a,b", "--coord-cols", "lon,lat"], []),
]


def run_step(name, cmd, logf):
    print(f"\n===== {name} =====", flush=True)
    logf.write(f"\n===== {name} =====\n")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=180)
        out = (r.stdout or "") + (("\n[stderr] " + r.stderr) if r.stderr else "")
    except subprocess.TimeoutExpired as e:
        out = f"TIMEOUT: {e}"
    print(out, flush=True)
    logf.write(out + "\n")
    return out


def make_map_screenshot(png_path):
    """用 playwright 打开上次生成的地图 HTML 截图（可选，失败不阻塞）。"""
    html = EVID / "products" / "comm_map.html"
    if not html.exists():
        # 先生成一张小区地图
        run_step("05b_map_生成小区地图", ["python", str(TDT), "map",
                 str(EVID / "products" / "comm.csv"),
                 "--out", str(html), "--title", "银川小区分布(演示)"],
                 open(EVID / "transcript_utf8.txt", "a", encoding="utf-8"))
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1280, "height": 800})
            pg.goto(html.as_uri(), timeout=30000)
            pg.wait_for_timeout(6000)
            pg.screenshot(path=str(png_path))
            b.close()
        print(f"[截图] {png_path}", flush=True)
    except Exception as e:
        print(f"[截图跳过] {e}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(EVID))
    args = ap.parse_args()
    EVID2 = Path(args.out_dir)
    prod = EVID2 / "products"
    prod.mkdir(parents=True, exist_ok=True)

    # 生成演示小区数据（小规模，练/证据一致性）
    # 用 crawl-communities 小范围跑一次（约 8 格）
    cmds = [
        ("00_crawl_小区POI爬取(小范围)", ["python", str(TDT), "crawl-communities",
          "106.1,38.4,106.4,38.55", "--out-prefix", str(prod / "comm"),
          "--keywords", "小区", "--grid-size", "0.1"], []),
    ]
    all_steps = cmds + STEPS
    logf = open(EVID2 / "transcript_utf8.txt", "w", encoding="utf-8")
    for name, cmd, _ in all_steps:
        run_step(name, cmd, logf)
    logf.close()

    make_map_screenshot(EVID2 / "map_preview.png")
    print("\n证据包生成完成 →", EVID2)
    print("文件：", sorted(str(p.relative_to(EVID2.parent)) for p in EVID2.rglob('*') if p.is_file()))


if __name__ == "__main__":
    main()
