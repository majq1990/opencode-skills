#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_product_config.py — 16 产品信创迁移配置对照检查。

按 config/product-config-map.json 的映射，扫描现场配置文件（默认 /egova 下），
核对迁移完成态口径：达梦 JDBC URL 在、MySQL URL 消失、驱动类/方言正确。

用法：
  python check_product_config.py --root /egova                       # 人读报告
  python check_product_config.py --root /egova --json                # JSON 输出
  python check_product_config.py --root <fixture目录> --profile <自定义映射>

设计：
  - 只读：不修改任何文件（SKILL.md 停止条件 6 同源纪律）
  - 某产品一个文件都找不到 → SKIP 并给 note 提示（如星桥 dex 配置需现场定位）
  - 单条检查 = {regex, present, desc}：present=true 要求命中，false 要求不命中
  - 退出码：0=无 FAIL；2=存在 FAIL（--strict 时生效，默认报告工具不设退出门槛）
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_PROFILE = Path(__file__).resolve().parent.parent / "config" / "product-config-map.json"


def load_profile(path: str | None) -> dict:
    p = Path(path) if path else DEFAULT_PROFILE
    if not p.exists():
        raise SystemExit(f"gap: 配置映射不存在: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_product(product: dict, root: Path, default_checks: list[dict]) -> dict:
    """单个产品核对。返回 {product, files, results, status}，供单测复用。"""
    globs = product.get("config_globs") or []
    found: list[Path] = []
    for g in globs:
        pattern = str(g).replace("\\", "/").lstrip("/")
        found.extend(sorted(p for p in root.glob(pattern) if p.is_file()))
    found = sorted(set(found))

    checks = list(default_checks) + list(product.get("extra_checks") or [])
    results = []
    for f in found:
        text = _read_text(f)
        for chk in checks:
            hit = re.search(chk["regex"], text) is not None
            expect = bool(chk.get("present"))
            results.append({
                "file": str(f),
                "desc": chk.get("desc", chk["regex"]),
                "expected": "命中" if expect else "不命中",
                "actual": "命中" if hit else "不命中",
                "ok": hit == expect,
            })
    status = "SKIP" if not found else ("PASS" if all(r["ok"] for r in results) else "FAIL")
    return {
        "product": product.get("product", "?"),
        "dm_schema": product.get("dm_schema", ""),
        "files": [str(f) for f in found],
        "results": results,
        "status": status,
        "note": product.get("note", ""),
    }


def check_products(profile: dict, root: Path) -> list[dict]:
    default_checks = profile.get("default_checks") or []
    return [check_product(p, root, default_checks) for p in profile.get("products") or []]


def render(results: list[dict]) -> str:
    lines = ["产品配置对照检查（迁移完成态口径：达梦在、MySQL 消失）", ""]
    status_mark = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭"}
    for r in results:
        lines.append(f"{status_mark.get(r['status'], '?')} {r['product']} "
                     f"[{r['status']}] 目标模式={r['dm_schema']}")
        if r["note"]:
            lines.append(f"    note: {r['note']}")
        if r["status"] == "SKIP":
            continue
        for f in r["files"]:
            lines.append(f"    文件: {f}")
        for bad in [x for x in r["results"] if not x["ok"]]:
            lines.append(f"    ✗ {bad['file']}: {bad['desc']}（期望{bad['expected']}，"
                         f"实际{bad['actual']}）")
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    n_skip = sum(1 for r in results if r["status"] == "SKIP")
    lines += ["", f"汇总: PASS {n_pass} / FAIL {n_fail} / SKIP {n_skip} "
              f"（SKIP=配置未定位到，按 note 现场手工核对）"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="16 产品信创迁移配置对照检查")
    parser.add_argument("--root", default="/egova", help="现场根目录（默认 /egova）")
    parser.add_argument("--profile", default=None, help="product-config-map.json 路径")
    parser.add_argument("--json", action="store_true", dest="as_json", help="JSON 输出")
    parser.add_argument("--strict", action="store_true", help="存在 FAIL 时退出码 2")
    args = parser.parse_args(argv)

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    profile = load_profile(args.profile)
    results = check_products(profile, Path(args.root))
    if args.as_json:
        print(json.dumps(results, ensure_ascii=False, indent=1))
    else:
        print(render(results))
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    return 2 if (args.strict and n_fail) else 0


if __name__ == "__main__":
    sys.exit(main())
