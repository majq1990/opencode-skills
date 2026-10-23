#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plan_chunks.py —— 为超长文本（长篇小说 / 长文档）规划「节点 + 阅读块」分块计划。

要解决的问题：整本书动辄 400 万+ 字符，单个模型上下文装不下，必须切成若干
「阅读块」，由并行子 agent 分别读完后总结，再由主 agent 归约成「节点」级总结。
本脚本把这件事变成可复核的表格：块区间首尾相接、无重叠、无遗漏；并顺带体检
原文的数据质量问题（章节跳号 / 重复标题 / 异常短区间＝疑似乱码插入）。

用法示例：
  python3 plan_chunks.py "D:/book/某某小说.txt"
  python3 plan_chunks.py book.txt --node-size 50 --max-lines 7000 --out plan.md
  python3 plan_chunks.py book.txt --pattern '^第[0-9]+章' --json plan.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_PATTERN = r"^\s*第[0-9]+章"
NUM_RE = re.compile(r"第\s*(\d+)\s*章")
DEFAULT_SHORT_SPAN = 120


def read_lines(path: Path, encoding: str) -> list[str]:
    with path.open("r", encoding=encoding, errors="replace") as fh:
        return fh.readlines()


def find_chapters(lines: list[str], pattern: str) -> list[dict]:
    pat = re.compile(pattern)
    out = []
    for idx, raw in enumerate(lines, start=1):
        if pat.match(raw):
            out.append({"line": idx, "title": raw.strip()[:80]})
    return out


def chapter_number(title: str) -> int | None:
    m = NUM_RE.search(title)
    return int(m.group(1)) if m else None


def build_nodes(chapters: list[dict], total_lines: int, node_size: int) -> list[dict]:
    if not chapters:
        return [{"index": 1, "start": 1, "end": total_lines,
                 "first_title": "(无章节标题)", "last_title": "(无章节标题)",
                 "chapter_count": 0}]
    nodes = []
    for i in range(0, len(chapters), node_size):
        group = chapters[i:i + node_size]
        start = 1 if i == 0 else group[0]["line"]
        nxt = chapters[i + node_size]["line"] if i + node_size < len(chapters) else None
        end = (nxt - 1) if nxt is not None else total_lines
        nodes.append({
            "index": len(nodes) + 1,
            "start": start,
            "end": end,
            "first_title": group[0]["title"],
            "last_title": group[-1]["title"],
            "chapter_count": len(group),
        })
    return nodes


def build_chunks(nodes: list[dict], chapters: list[dict], max_lines: int) -> list[dict]:
    chunks = []
    for node in nodes:
        pos = node["start"]
        while pos <= node["end"]:
            end = min(pos + max_lines - 1, node["end"])
            inside = [c for c in chapters if pos <= c["line"] <= end]
            chunks.append({
                "index": len(chunks) + 1,
                "node": node["index"],
                "start": pos,
                "end": end,
                "first_title": inside[0]["title"] if inside else "",
                "last_title": inside[-1]["title"] if inside else "",
                "chapter_count": len(inside),
            })
            pos = end + 1
    return chunks


def audit(chapters: list[dict], short_span: int) -> list[str]:
    """原文数据质量体检：跳号 / 重复 / 异常短区间。"""
    warnings: list[str] = []
    numbers = [chapter_number(c["title"]) for c in chapters]
    known = [n for n in numbers if n is not None]

    missing: list[int] = []
    for a, b in zip(known, known[1:]):
        if b > a + 1:
            missing.extend(range(a + 1, b))
    if missing:
        preview = "、".join(str(x) for x in missing[:20])
        more = f" 等共 {len(missing)} 个" if len(missing) > 20 else ""
        warnings.append(
            f"章节编号跳号：第 {preview}{more} 章缺失。多为作者重排/合章所致，"
            f"不代表内容缺失——总结时按实际内容处理，不要当成断层。")

    dupes = sorted(n for n, cnt in Counter(known).items() if cnt > 1)
    if dupes:
        warnings.append("章节编号重复："
                        + "、".join(f"第{n}章" for n in dupes[:10])
                        + "。通常是正文里引用了章号造成的误命中，按实际内容处理。")

    for prev, cur in zip(chapters, chapters[1:]):
        span = cur["line"] - prev["line"]
        if span < short_span:
            warnings.append(
                f"疑似异常短区间：{prev['title']}（第 {prev['line']} 行）→ "
                f"{cur['title']}（第 {cur['line']} 行）仅 {span} 行。"
                f"很可能是乱码插入或其他作品的段落，需人工确认后让子 agent 忽略。")

    tail = chapters[-1]["title"] if chapters else ""
    warnings.append(
        "文件末尾（末章之后）常夹带作者新书宣传、外站导流等无关内容，"
        "请在子 agent prompt 中明确要求剔除。")
    if tail:
        warnings.append(f"末章标题：{tail}（确认是否含完结感言/宣传，酌情截断）")
    return warnings


def render_markdown(path: Path, lines: list[str], chapters: list[dict],
                    nodes: list[dict], chunks: list[dict],
                    warnings: list[str], args) -> str:
    total_chars = sum(len(x) for x in lines)
    out: list[str] = []
    out.append(f"# 分块计划：{path.name}")
    out.append("")
    out.append(f"- 总行数：{len(lines):,}")
    out.append(f"- 总字符数：{total_chars:,}")
    out.append(f"- 识别章节数：{len(chapters)}（匹配规则 `{args.pattern}`）")
    out.append(f"- 节点：{args.node_size} 章/节点，共 {len(nodes)} 个节点")
    out.append(f"- 阅读块：单块上限 {args.max_lines:,} 行，共 {len(chunks)} 个块")
    out.append("")

    out.append("## 节点表（最终交付的总结层级）")
    out.append("")
    out.append("| 节点 | 行区间 | 章节数 | 起始章 | 结束章 | 对应块 |")
    out.append("| --- | --- | --- | --- | --- | --- |")
    for n in nodes:
        ids = [c["index"] for c in chunks if c["node"] == n["index"]]
        rng = f"{ids[0]}–{ids[-1]}" if ids else "-"
        out.append(f"| {n['index']} | {n['start']}–{n['end']} | {n['chapter_count']} | "
                   f"{n['first_title']} | {n['last_title']} | {rng} |")
    out.append("")

    out.append("## 块表（每块交给一个子 agent 读取）")
    out.append("")
    out.append("| 块 | 节点 | 行区间 | 行数 | 章节数 | 覆盖范围 |")
    out.append("| --- | --- | --- | --- | --- | --- |")
    for c in chunks:
        out.append(f"| {c['index']:02d} | {c['node']} | {c['start']}–{c['end']} | "
                   f"{c['end'] - c['start'] + 1:,} | {c['chapter_count']} | "
                   f"{c['first_title']} ~ {c['last_title']} |")
    out.append("")

    out.append("## 覆盖率自检")
    out.append("")
    ok = True
    if chunks:
        if chunks[0]["start"] != 1:
            ok = False
            out.append(f"- ✗ 首块未从第 1 行开始（实际 {chunks[0]['start']}）")
        if chunks[-1]["end"] != len(lines):
            ok = False
            out.append(f"- ✗ 末块未覆盖到文件结尾"
                       f"（实际 {chunks[-1]['end']} / {len(lines)}）")
        for a, b in zip(chunks, chunks[1:]):
            if b["start"] != a["end"] + 1:
                ok = False
                out.append(f"- ✗ 块 {a['index']} 与块 {b['index']} 之间有缺口或重叠"
                           f"（{a['end']} → {b['start']}）")
    out.append("- ✓ 块区间首尾相接、无重叠、无遗漏" if ok else "- 存在上述问题，需修正后再派发")
    out.append("")

    out.append("## 原文数据质量告警")
    out.append("")
    out.extend(f"- {w}" for w in warnings)
    out.append("")

    out.append("## 块行区间速查（复制进子 agent prompt）")
    out.append("")
    out.append("```text")
    for c in chunks:
        out.append(f"块{c['index']:02d}: {c['start']}-{c['end']}  # 节点{c['node']} "
                   f"{c['first_title']} ~ {c['last_title']}")
    out.append("```")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="超长文本「节点+阅读块」分块规划")
    ap.add_argument("file", help="待总结的文本文件")
    ap.add_argument("--pattern", default=DEFAULT_PATTERN,
                    help=f"章节标题正则（默认 {DEFAULT_PATTERN}）")
    ap.add_argument("--node-size", type=int, default=50, help="每节点章数（默认 50）")
    ap.add_argument("--max-lines", type=int, default=7000, help="单块最大行数（默认 7000）")
    ap.add_argument("--short-span", type=int, default=DEFAULT_SHORT_SPAN,
                    help=f"异常短区间阈值（默认 {DEFAULT_SHORT_SPAN} 行）")
    ap.add_argument("--encoding", default="utf-8")
    ap.add_argument("--out", help="把计划写成 markdown 文件")
    ap.add_argument("--json", dest="json_out", help="把计划写成 json 文件")
    args = ap.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        ap.error(f"文件不存在：{path}")

    lines = read_lines(path, args.encoding)
    chapters = find_chapters(lines, args.pattern)
    nodes = build_nodes(chapters, len(lines), args.node_size)
    chunks = build_chunks(nodes, chapters, args.max_lines)
    warnings = audit(chapters, args.short_span)

    md = render_markdown(path, lines, chapters, nodes, chunks, warnings, args)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"已写入 {args.out}")
    else:
        print(md)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps({
            "file": str(path),
            "total_lines": len(lines),
            "total_chars": sum(len(x) for x in lines),
            "chapter_count": len(chapters),
            "nodes": nodes,
            "chunks": chunks,
            "warnings": warnings,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已写入 {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
