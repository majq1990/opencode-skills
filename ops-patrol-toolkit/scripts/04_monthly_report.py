#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_monthly_report · 月度运维报告（ops-patrol-toolkit 子工具 04）

两个子命令（通用模式移植自月度运维报告实践，实现按本仓库契约全部重写）：
  check-servers  批量网址/服务器巡检：对配置里的每个 target 做一次 HTTP GET，
                 记录 ok/status/elapsed_ms/error，结果 JSON 落盘
  fill           业务统计数据（JSON 文件输入）回填 Word 月报模板

设计要点（与源实践的差异，均为脱敏/通用化改造）:
  1. 巡检用标准库 urllib，不引入第三方 HTTP 库；不做 TLS 校验关闭（verify=False）
     之类的危险开关，自签名 HTTPS 场景不在 v1 范围
  2. 网络异常不算脚本失败：单目标失败进 results（ok:false + error），
     全部目标失败时信封仍 ok:true 但 failed == total
  3. 业务统计数据一律 JSON 文件输入，本工具不直连任何业务系统
     （数字城管 API / CDP 等客户环境定制不进通用版）
  4. docx 回填一律走共享库 docx_io.fill_template（模板原件不动，
     段落与表格结构不变）；本脚本不自带任何 OOXML 代码。回填后复查输出：
     misses（stats 里没在模板中命中的键）与输出残留的 {{...}}（模板里
     stats 没给值的占位符）任一非空，信封即带 unresolved_placeholders /
     leftover_placeholders 并标记 review_required，正文提示【待复核】
  5. stdout 最后一行固定为 JSON 信封：成功 {"ok": true, ...}；
     失败 {"ok": false, "gap": "..."} 并以退出码 2 结束；控制台不使用 emoji

用法:
  python scripts/04_monthly_report.py check-servers --config config/patrol/servers.json \
      [--out work/monthly/servers.json] [--timeout 5]
  python scripts/04_monthly_report.py fill --template assets/monthly-report-template.docx \
      --stats stats.json --out work/monthly/月报.docx
  fill 也可给 --config config/patrol/monthly_report.json 提供模板路径/输出路径/
  默认替换值的兜底（命令行显式值优先；配置内相对路径以仓库根为基准）。

stats.json 契约:
  {
    "month": "2026-09",              # 可选，仅随信封回显
    "project": "项目名",              # 可选，仅随信封回显
    "replacements": {"{{k}}": "v"},  # 必填：段落全文替换（含表格内段落）
    "cells": [                       # 可选：按 表序号/行/列 覆写单元格文本
      {"table": 0, "row": 1, "col": 1, "text": "99.98%"}
    ]
  }
"""

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import docx_io  # noqa: E402  共享 docx 读写库（本工具禁止自带 OOXML 代码）
import patrol_lib  # noqa: E402  公共库：信封(emit/stop)/路径(work_path/read_json/write_json)

__version__ = "1.0.0"

DEFAULT_CHECK_TIMEOUT_S = 5.0
DEFAULT_OUT = "monthly/servers.json"  # 相对 work/ 的默认巡检结果路径

USER_AGENT = "ops-patrol-toolkit/%s monthly-report" % __version__

# 残留占位符形态：{{xxx}}（限长防误扫超长文本），用于回填后复查输出文件
_PLACEHOLDER_RE = re.compile(r"\{\{[^{}]{1,80}\}\}")


# ---------------------------------------------------------------------------
# check-servers
# ---------------------------------------------------------------------------

def check_target(target, timeout_s):
    """对单个目标做一次 HTTP GET，返回结果字典。

    ok 的判定：最终状态码 == expect_status（配置缺省 200）。
    HTTP 4xx/5xx 是"有响应但不达标"（status 记真实码）；连接失败/超时/DNS
    解析失败等网络异常是"无有效响应"（status=0 + error），两者都只影响该
    目标的 ok，不抛出到脚本级失败。
    """
    url = str(target.get("url") or "").strip()
    name = str(target.get("name") or url)
    try:
        expect = int(target.get("expect_status") or 200)
    except (TypeError, ValueError):
        expect = 200

    start = time.monotonic()
    try:
        req = urllib.request.Request(url, method="GET",
                                     headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            status = int(getattr(resp, "status", 0) or 0)
    except urllib.error.HTTPError as e:  # 4xx/5xx：urlopen 抛 HTTPError，但状态码是有效观测值
        status = int(e.code or 0)
    except Exception as e:  # noqa: BLE001  URLError/timeout/连接拒绝等一律记为单目标失败
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"name": name, "url": url, "expect_status": expect, "status": 0,
                "ok": False, "elapsed_ms": elapsed_ms,
                "error": "%s: %s" % (type(e).__name__, e)}

    elapsed_ms = int((time.monotonic() - start) * 1000)
    if status == expect:
        return {"name": name, "url": url, "expect_status": expect, "status": status,
                "ok": True, "elapsed_ms": elapsed_ms, "error": None}
    return {"name": name, "url": url, "expect_status": expect, "status": status,
            "ok": False, "elapsed_ms": elapsed_ms,
            "error": "状态码 %d 与期望 %d 不符" % (status, expect)}


def cmd_check_servers(args):
    cfg = patrol_lib.read_json(args.config)  # 缺文件/坏 JSON -> gap 退出码 2
    targets = cfg.get("targets")
    if not isinstance(targets, list) or not targets:
        patrol_lib.stop("巡检目标为空：请在 %s 的 targets 中至少配置一条 "
                        "{\"name\": ..., \"url\": ...}（换项目只改该配置文件）" % args.config)

    for i, t in enumerate(targets):
        if not isinstance(t, dict) or not str(t.get("url") or "").strip():
            patrol_lib.stop("targets 第 %d 条缺少 url 字段（应为 {\"name\":..., \"url\":...}）" % (i + 1))

    if args.timeout is not None:
        timeout_s = float(args.timeout)
    else:
        timeout_s = patrol_lib.to_float(cfg.get("timeout_s"), DEFAULT_CHECK_TIMEOUT_S)
        if timeout_s <= 0:
            timeout_s = DEFAULT_CHECK_TIMEOUT_S

    results = []
    total = len(targets)
    for i, t in enumerate(targets):
        r = check_target(t, timeout_s)
        results.append(r)
        if r["ok"]:
            print("[%d/%d] %-14s %s -> %d（%dms）正常"
                  % (i + 1, total, r["name"], r["url"], r["status"], r["elapsed_ms"]))
        else:
            print("[%d/%d] %-14s %s -> %s（%dms）异常: %s"
                  % (i + 1, total, r["name"], r["url"], r["status"] or "无响应",
                     r["elapsed_ms"], r["error"] or "未知"))

    failed = sum(1 for r in results if not r["ok"])
    out_path = Path(args.out) if args.out else patrol_lib.work_path(DEFAULT_OUT)
    payload = {
        "config": str(Path(args.config).resolve()),
        "timeout_s": timeout_s,
        "results": results,
        "total": total,
        "failed": failed,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    patrol_lib.write_json(out_path, payload)

    # 网络异常不是脚本失败：全失败也 ok:true，由 failed == total 表达，供上层判断
    print("巡检完成：共 %d 个目标，正常 %d 个，异常 %d 个；结果已写入 %s"
          % (total, total - failed, failed, out_path))
    patrol_lib.emit({"results": results, "total": total, "failed": failed,
                     "output": str(out_path.resolve())})
    return 0


# ---------------------------------------------------------------------------
# fill
# ---------------------------------------------------------------------------

def _resolve_repo_path(p):
    """monthly_report.json 里的相对路径以仓库根为基准（与 SKILL.md 快速开始的写法一致）；
    命令行显式传入的路径仍按调用者工作目录解析。"""
    pp = Path(p)
    return pp if pp.is_absolute() else (patrol_lib.ROOT / pp)


def _validate_stats(stats, stats_path):
    """校验 stats.json 结构；不符合约定即 stop（退出码 2），不猜测不兜底。"""
    if not isinstance(stats, dict):
        patrol_lib.stop("%s 结构不符合约定：顶层必须是 JSON 对象，"
                        "必填键 replacements（{\"{{占位符}}\": \"替换值\"}）" % stats_path)
    reps = stats.get("replacements")
    if not isinstance(reps, dict) or not reps:
        patrol_lib.stop("%s 结构不符合约定：缺少必填键 replacements，或它不是非空对象"
                        "（应为 {\"{{占位符}}\": \"替换值\"}）" % stats_path)
    for k, v in reps.items():
        if not isinstance(k, str) or not isinstance(v, str):
            patrol_lib.stop("%s 的 replacements 必须是 {字符串: 字符串}，"
                            "键 %r 或其值类型不符" % (stats_path, k))
    cells = stats.get("cells")
    if cells is None:
        cells = []
    if not isinstance(cells, list):
        patrol_lib.stop("%s 的 cells 必须是数组，每项 "
                        "{\"table\": int, \"row\": int, \"col\": int, \"text\": str}" % stats_path)
    for i, c in enumerate(cells):
        if not isinstance(c, dict):
            patrol_lib.stop("%s 的 cells 第 %d 项必须是对象" % (stats_path, i + 1))
        for key in ("table", "row", "col"):
            if not isinstance(c.get(key), int):
                patrol_lib.stop("%s 的 cells 第 %d 项缺少整数键 %s"
                                % (stats_path, i + 1, key))
        if not isinstance(c.get("text"), str):
            patrol_lib.stop("%s 的 cells 第 %d 项缺少字符串键 text" % (stats_path, i + 1))
    return reps, cells


def cmd_fill(args):
    stats_path = Path(args.stats)
    stats = patrol_lib.read_json(stats_path)  # 缺文件/坏 JSON -> gap 退出码 2
    reps, cells = _validate_stats(stats, stats_path)

    # --config 提供模板/输出/默认替换值兜底；命令行显式值优先
    cfg = {}
    if args.config:
        cfg = patrol_lib.read_json(args.config)
        if not isinstance(cfg, dict):
            cfg = {}

    template = args.template or cfg.get("template")
    if not template:
        patrol_lib.stop("缺少 --template（或用 --config 提供 monthly_report.json 的 template 字段）")
    template = Path(template if args.template else _resolve_repo_path(template))
    if not template.is_file():
        patrol_lib.stop("模板文件不存在: %s（请先准备 Word 月报模板 docx）" % template.resolve())

    out = args.out
    if not out:
        out_dir, out_name = cfg.get("out_dir"), cfg.get("out_name")
        if out_dir and out_name:
            out = str(_resolve_repo_path(out_dir) / out_name)
    if not out:
        patrol_lib.stop("缺少 --out（或用 --config 提供 monthly_report.json 的 "
                        "out_dir + out_name 字段）")
    out = Path(out)
    if out.resolve() == template.resolve():
        patrol_lib.stop("--out 与模板路径相同：模板原件不允许被改写，请另指定输出路径")
    if out.parent and not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)  # 与 write_json 同口径：父目录自动创建

    defaults = cfg.get("defaults") or {}
    base_reps = defaults.get("replacements") if isinstance(defaults, dict) else None
    merged = dict(base_reps) if isinstance(base_reps, dict) else {}
    merged.update(reps)  # stats.json 的显式替换值优先于配置默认值

    try:
        out_path, hits, misses = docx_io.fill_template(
            template, out, replacements=merged, cells=cells)
    except docx_io.DocxError as e:
        patrol_lib.stop("模板回填失败: %s（检查 cells 的表/行/列是否越界，"
                        "或模板是否为标准 docx）" % e)

    cell_written = len(cells)
    print("回填完成：替换命中 %d 项，未命中 %d 项，单元格覆写 %d 处 -> %s"
          % (len(hits) - cell_written, len(misses), cell_written, out_path))

    # 复查输出文件里残留的 {{...}}（stats 少给的模板占位符同样按待复核口径暴露）
    leftover = set()
    try:
        out_doc = docx_io.extract(out_path)
    except docx_io.DocxError as e:  # 输出已生成但回读异常：如实报告，不伪装全命中
        patrol_lib.stop("输出文件回读失败: %s（%s）" % (out_path, e))
    for p in out_doc.get("paragraphs", []):
        leftover.update(_PLACEHOLDER_RE.findall(p.get("text") or ""))
    for grid in out_doc.get("tables", []):
        for row in grid:
            for c in row:
                leftover.update(_PLACEHOLDER_RE.findall(c or ""))
    leftover = sorted(leftover)
    if leftover:
        print("输出仍残留未回填的模板占位符: %s" % "、".join(leftover))

    envelope = {
        "output": str(Path(out_path).resolve()),
        "template": str(template.resolve()),
        "month": stats.get("month"),
        "project": stats.get("project"),
        "replacements_hit": len(hits) - cell_written,
        "cells_written": cell_written,
        "misses": misses,
    }
    if misses or leftover:
        # 未命中占位：信封带 unresolved_placeholders，产物按【待复核】口径提示，不伪装成功
        if misses:
            print("输出含未命中占位: %s" % "、".join(misses))
        print("输出为【待复核】：存在未回填的占位符，请补齐 stats.json 后重跑")
        envelope["unresolved_placeholders"] = misses
        envelope["leftover_placeholders"] = leftover
        envelope["review_required"] = True
    patrol_lib.emit(envelope)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="04_monthly_report",
        description="月度运维报告：批量网址/服务器巡检（check-servers）+ Word 月报模板回填（fill）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("check-servers", help="批量 HTTP GET 巡检，结果 JSON 落盘")
    p1.add_argument("--config", required=True,
                    help="巡检配置 JSON（targets: [{name, url, expect_status}]）")
    p1.add_argument("--out", default=None,
                    help="结果输出路径（缺省 work/monthly/servers.json）")
    p1.add_argument("--timeout", type=float, default=None,
                    help="单目标超时秒数（缺省取配置 timeout_s，再缺省 5）")
    p1.set_defaults(func=cmd_check_servers)

    p2 = sub.add_parser("fill", help="业务统计 JSON 回填 Word 月报模板")
    p2.add_argument("--template", default=None, help="Word 月报模板 docx 路径")
    p2.add_argument("--stats", required=True,
                    help="业务统计 JSON（replacements 必填，cells 可选）")
    p2.add_argument("--out", default=None, help="输出 docx 路径（模板原件不动）")
    p2.add_argument("--config", default=None,
                    help="可选默认配置 JSON（template/out_dir/out_name/defaults）")
    p2.set_defaults(func=cmd_fill)

    a = ap.parse_args(argv)
    return a.func(a) or 0


if __name__ == "__main__":
    sys.exit(main())
