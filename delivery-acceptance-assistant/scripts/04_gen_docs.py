#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""04_gen_docs.py — 立项材料生成（四类文档）。

设计约束（来自实测教训，不可放宽）：
  - **严禁新建空白文档重写内容**。那会丢失模板的目录、图片、表格、样式、页眉页脚、域。
    只能复制模板副本 → 纯文本级局部替换 → 版面保留校验。
  - 生成后强制比对图片数/表格数/域数，任一项减少即判定失败并删除产物，退出码 1。
  - 只读 templates/，只写 --outdir；不联网、不执行系统命令。
  - 模板原文件永不被覆盖。

替换粒度说明：Word 段落文字常被拆进多个 run，纯字符串替换只能命中「恰好连续」的情形。
  库层已实现段落级跨 run 替换与数字实体变体；替换后仍缺失的键如实报告为「未覆盖」，
  **不会**为了凑命中率去重建段落结构。

用法:
  python 04_gen_docs.py --templates <模板目录> --manifest <模板清单.json> \
      --replacements <替换内容.json> --outdir <输出目录> [--only 实施方案 立项申请报告]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daa_common import (  # noqa: E402
    GapError, emit, envelope, exit_gap, load_json, ooxml_layout, parts_filter_for,
    rewrite_zip, setup_io, skill_root, today_str, write_text,
)

SUPPORTED = {".docx", ".xlsx", ".pptx"}


def generate_one(doc_type, tpl_path, replacements, out_path):
    """复制模板 → 文本替换 → 返回 (命中统计, 版面前后)。失败抛 GapError。"""
    ext = os.path.splitext(tpl_path)[1].lower()
    if ext not in SUPPORTED:
        raise GapError("不支持的模板类型：%s（仅支持 %s）" % (ext, "/".join(sorted(SUPPORTED))))
    if not os.path.isfile(tpl_path):
        raise GapError("模板文件不存在：%s" % tpl_path)
    before = ooxml_layout(tpl_path)
    hit = rewrite_zip(tpl_path, out_path, replacements, parts_filter_for(ext))
    after = ooxml_layout(out_path)
    uncovered = [k for k, n in hit.items() if n == 0]
    lost = {k: (before[k], after[k]) for k in before if after[k] < before[k]}
    if lost:
        try:
            os.remove(out_path)
        except OSError:
            pass
        raise GapError("版面元素丢失，已删除产物 %s：%s" % (out_path, lost))
    return {"hit": hit, "uncovered": uncovered, "layout_before": before,
            "layout_after": after, "output": out_path}


def main():
    setup_io()
    ap = argparse.ArgumentParser(description="立项材料生成（模板复制+文本替换+版面校验）")
    ap.add_argument("--templates", required=True, help="模板源目录（只读）")
    ap.add_argument("--manifest", default=None, help="模板清单 JSON：{类型: 模板文件名}")
    ap.add_argument("--replacements", required=True, help="替换内容 JSON：{类型: {原文:新文}}")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--only", nargs="*", default=None, help="只生成指定类型")
    ap.add_argument("--project-name", default="", help="输出文件名前缀")
    a = ap.parse_args()

    try:
        repl_all = load_json(a.replacements)
        if not isinstance(repl_all, dict) or not repl_all:
            raise GapError("替换内容必须是非空对象：{文档类型: {原文: 新文}}")
        if a.manifest:
            manifest = load_json(a.manifest)
        else:
            manifest = load_json(os.path.join(skill_root(), "config", "doc_templates.json"))
        if not os.path.isdir(a.templates):
            raise GapError("模板目录不存在：%s" % a.templates)
        # 清单里的注释键（_comment/version/note/…）不是文档类型。
        # 判定标准：值必须是受支持格式的模板文件名。
        manifest = {k: v for k, v in manifest.items()
                    if isinstance(v, str) and not k.startswith("_")
                    and os.path.splitext(v)[1].lower() in SUPPORTED}
        if not manifest:
            raise GapError("模板清单中没有可用条目（键=文档类型，值=模板文件名）")
    except GapError as e:
        return exit_gap("gen_docs", str(e))

    os.makedirs(a.outdir, exist_ok=True)
    types = a.only or list(manifest.keys())
    results, failed = [], []
    for dtype in types:
        if dtype not in manifest:
            failed.append({"type": dtype, "error": "模板清单中无此类型"})
            continue
        tpl_name = manifest[dtype]
        tpl_path = os.path.join(a.templates, tpl_name)
        repl = repl_all.get(dtype)
        if not isinstance(repl, dict) or not repl:
            failed.append({"type": dtype, "error": "替换内容缺少该类型或为空"})
            continue
        ext = os.path.splitext(tpl_name)[1].lower()
        prefix = (a.project_name or repl_all.get("_project_name") or dtype)
        out_name = "%s_%s%s" % (prefix, dtype, ext)
        out_path = os.path.join(a.outdir, out_name)
        try:
            r = generate_one(dtype, tpl_path, repl, out_path)
            r["type"] = dtype
            r["template"] = tpl_name
            r["uncovered_count"] = len(r["uncovered"])
            results.append(r)
        except GapError as e:
            failed.append({"type": dtype, "template": tpl_name, "error": str(e)})

    # 生成台账，便于复核与二次迭代
    ledger = {
        "generated_at": today_str(), "templates_dir": os.path.abspath(a.templates),
        "outdir": os.path.abspath(a.outdir),
        "succeeded": [{k: v for k, v in r.items() if k != "hit"} for r in results],
        "failed": failed,
    }
    write_text(a.outdir, "_gen_ledger.json",
               json.dumps(ledger, ensure_ascii=False, indent=2))

    kw = {"generated": len(results), "failed": failed,
          "uncovered_total": sum(r["uncovered_count"] for r in results),
          "outdir": os.path.abspath(a.outdir),
          "outputs": [r["output"] for r in results]}
    if failed:
        kw["gap"] = "；".join(f.get("error", "") for f in failed)
    emit(envelope("gen_docs", not failed, **kw))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
