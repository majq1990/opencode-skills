#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_props_coverage.py — 两份 properties 的键集合对照（配置漏键审计）。

真实故障背景：切库时只换了 JDBC 连接相关的那几个键，另一个方言/参数文件（如
DM.properties）是照着一个更老或更小的模板拷来的，键数比源库侧那份（如
MYSQLV14.properties）少一批。缺键不会报错，只会让应用在某个功能分支上拿到 null，
表现为"能启动、某个页面或某个查询不正常"。本脚本把缺键点名出来。

只读：不修改任何文件、不连库，结果只走 stdout。默认不打印值（避免凭据落到日志），
要看值加 --show-values。

用法：
  python check_props_coverage.py --base conf/MYSQLV14.properties --target conf/DM.properties
  python check_props_coverage.py --base a.properties --target b.properties --show-values
  python check_props_coverage.py --base a.properties --target b.properties --json --strict

判定口径：
  MISSING  只在 base 有——target 缺键，需按现场补齐
  EXTRA    只在 target 有——target 多出的键，确认是否有意为之
  DIFF     两侧都有但值不同——连接类键（url/user/driver）属预期差异，其余要逐个确认
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _split_kv(line: str) -> tuple:
    """按 java.util.Properties 口径切 key/value：键止于空白或 =/:，其后空白与一个分隔符都吃掉。"""
    i, n = 0, len(line)
    while i < n and line[i] not in "=: \t":
        i += 1
    key = line[:i]
    while i < n and line[i] in " \t":
        i += 1
    if i < n and line[i] in "=:":
        i += 1
        while i < n and line[i] in " \t":
            i += 1
    return key, line[i:]


def parse_properties(text: str) -> dict:
    """解析 java properties：注释(#/!)、空行、key=value / key:value / key value、续行。"""
    props: dict[str, str] = {}
    buf = ""
    for raw in text.splitlines():
        line = raw.strip()
        if buf:
            line = buf + line
            buf = ""
        if not line or line[0] in "#!":
            continue
        if line.endswith("\\"):
            buf = line[:-1]
            continue
        key, value = _split_kv(line)
        key = key.strip()
        value = value.strip()
        if not key or key in props:
            continue
        props[key] = value
    return props


def compare_props(base: dict, target: dict) -> dict:
    missing = sorted(k for k in base if k not in target)
    extra = sorted(k for k in target if k not in base)
    diff = sorted(k for k in base if k in target and base[k] != target[k])
    return {
        "base_count": len(base),
        "target_count": len(target),
        "missing": missing,
        "extra": extra,
        "diff": diff,
    }


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def render(base_path: str, target_path: str, res: dict, base: dict,
           target: dict, show_values: bool) -> str:
    lines = ["properties 键集合对照", ""]
    lines.append("base  : %s（%d 键）" % (base_path, res["base_count"]))
    lines.append("target: %s（%d 键）" % (target_path, res["target_count"]))
    lines.append("")

    if res["missing"]:
        lines.append("❌ MISSING %d 个（target 缺键，需按现场补齐）：" % len(res["missing"]))
        for k in res["missing"]:
            if show_values:
                lines.append("  - %s = %s" % (k, base[k]))
            else:
                lines.append("  - " + k)
    else:
        lines.append("✅ MISSING 0（target 覆盖了 base 的全部键）")

    if res["extra"]:
        lines.append("")
        lines.append("⚠ EXTRA %d 个（只在 target 有，确认是否有意为之）：" % len(res["extra"]))
        for k in res["extra"]:
            if show_values:
                lines.append("  - %s = %s" % (k, target[k]))
            else:
                lines.append("  - " + k)

    if res["diff"]:
        lines.append("")
        lines.append("⚠ DIFF %d 个（两侧都有但值不同，逐个确认是否预期）：" % len(res["diff"]))
        for k in res["diff"]:
            if show_values:
                lines.append("  - %s: base=%s | target=%s" % (k, base[k], target[k]))
            else:
                lines.append("  - " + k)

    lines.append("")
    lines.append("口径：连接类键（url/driver/user）值不同属切库预期差异；")
    lines.append("      真正的风险是 MISSING——缺键不报错，只让应用在对应分支拿到空值。")
    if not show_values:
        lines.append("提示：加 --show-values 可打印两侧值（注意别把含凭据的输出落进共享日志）。")
    return "\n".join(lines)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="两份 properties 的键集合对照（配置漏键审计，只读）")
    parser.add_argument("--base", required=True, help="基准 properties 路径（键更全的那份）")
    parser.add_argument("--target", required=True, help="待审计 properties 路径")
    parser.add_argument("--show-values", action="store_true", dest="show_values",
                        help="打印键值（默认只打印键名，避免凭据外泄）")
    parser.add_argument("--json", action="store_true", dest="as_json", help="JSON 输出")
    parser.add_argument("--strict", action="store_true",
                        help="存在 MISSING 时退出码 2（可作切换前门禁）")
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding \
            and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    bp, tp = Path(args.base), Path(args.target)
    for p in (bp, tp):
        if not p.is_file():
            raise SystemExit("gap: 文件不存在: " + str(p))

    base = parse_properties(_read_text(bp))
    target = parse_properties(_read_text(tp))
    res = compare_props(base, target)

    if args.as_json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print(render(str(bp), str(tp), res, base, target, args.show_values))
    return 2 if (args.strict and res["missing"]) else 0


if __name__ == "__main__":
    sys.exit(main())
