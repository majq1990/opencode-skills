#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""01_collect.py — 采集交付物目录 → manifest.json + spec_effective.json。

设计约束：
  - 交付目录**只读**。运行前后各做一次 sha256 树快照，不一致即中止（零写入自证）。
  - 输出目录不得位于交付目录内部。
  - 纯标准库；不联网。

用法:
  python 01_collect.py --deliverable-dir <交付目录> --project <项目档案.json> \
      --outdir <输出目录> [--max-text-chars 600] [--rules sensitive_rules.json]

退出码：0=成功；1=零写入自证失败；2=前置条件不满足（gap）。
"""
import os
import sys
import zipfile
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daa_common import (  # noqa: E402
    F_LOG, F_MANIFEST, F_SPEC, GapError, dump_json, emit, envelope, ensure_outdir_safe,
    ensure_target_readable, exit_gap, get_text, load_json, log, now_str, rel_of,
    safe_path, setup_io, sha256_file, sha256_tree, skill_root, today_str, load_rules,
)

DEFAULT_MAX_TEXT_CHARS = 600


def iter_files(root):
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            yield os.path.join(dp, f)


def collect(deliverable_dir, max_text_chars, sensitive_rules):
    """扫描目录 → manifest 字典。只读。"""
    files, zip_entries, skipped = [], [], []
    ext_summary = {}
    total_bytes = 0
    for p in iter_files(deliverable_dir):
        rel = rel_of(p, deliverable_dir)
        ext = os.path.splitext(p)[1].lower()
        try:
            st = os.stat(p)
            size = st.st_size
            mtime = st.st_mtime
        except OSError as e:
            skipped.append({"path": rel, "reason": "无法读取：%s" % e})
            continue
        total_bytes += size
        ext_summary[ext] = ext_summary.get(ext, 0) + 1
        import datetime
        mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        mtime_date = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

        text, text_chars = "", 0
        text_exts = (sensitive_rules or {}).get("scan", {}).get("text_extensions")
        try:
            t = get_text(p, ext=ext, text_exts=text_exts)
            if t is not None:
                text_chars = len(t)
                text = t[:max_text_chars]
        except Exception:
            pass

        files.append({
            "path": rel, "name": os.path.basename(p), "ext": ext, "size": size,
            "mtime": mtime_str, "sha256": sha256_file(p), "mtime_date": mtime_date,
            "text_chars": text_chars, "text_excerpt": text,
        })

        if ext == ".zip":
            try:
                z = zipfile.ZipFile(p)
                for n in z.namelist():
                    ie = os.path.splitext(n)[1].lower()
                    zip_entries.append({"archive": rel, "inner_path": n,
                                        "ext": ie, "size": z.getinfo(n).file_size})
                z.close()
            except Exception:
                pass

    return {
        "target": deliverable_dir, "collected_at": now_str(), "today": today_str(),
        "file_count": len(files), "total_bytes": total_bytes,
        "ext_summary": dict(sorted(ext_summary.items())),
        "files": files, "zip_entries": zip_entries, "skipped": skipped,
    }


def main():
    setup_io()
    ap = argparse.ArgumentParser(description="采集交付物目录 → manifest.json")
    ap.add_argument("--deliverable-dir", required=True, help="交付物目录（只读）")
    ap.add_argument("--project", required=True, help="项目档案 JSON（验收清单+标准）")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--max-text-chars", type=int, default=DEFAULT_MAX_TEXT_CHARS)
    ap.add_argument("--rules", default=None, help="敏感信息规则（默认 config/sensitive_rules.json）")
    a = ap.parse_args()

    outdir = safe_path(a.outdir)
    try:
        target = ensure_target_readable(a.deliverable_dir)
        ensure_outdir_safe(outdir, target)
        project = load_json(a.project, required=True)
        for k in ("deliverable_list", "acceptance_criteria"):
            if k not in project:
                raise GapError("项目档案缺少字段：%s" % k)
        if a.rules:
            sensitive_rules = load_json(a.rules, required=True)
        else:
            sensitive_rules = load_json(
                os.path.join(skill_root(), "config", "sensitive_rules.json"),
                required=False, default={})
    except GapError as e:
        return exit_gap("collect", str(e))

    before = sha256_tree(target)
    try:
        manifest = collect(target, a.max_text_chars, sensitive_rules)
    except Exception as e:
        return exit_gap("collect", "采集失败：%s" % e)
    after = sha256_tree(target)

    readonly_proof = {
        "file_count_before": len(before),
        "file_count_after": len(after),
        "tree_identical": before == after,
        "changed_paths": sorted(
            set(before) ^ set(after)
            | {k for k in set(before) & set(after) if before[k] != after[k]}),
    }

    manifest["readonly_proof"] = readonly_proof
    spec = {
        "target": target, "collected_at": manifest["collected_at"],
        "project_file": os.path.basename(str(a.project)),
        "project": project.get("project", {}),
        "deliverable_list": project.get("deliverable_list", []),
        "acceptance_criteria": project.get("acceptance_criteria", {}),
        "extra_constraints": project.get("extra_constraints", {}),
    }

    if not readonly_proof["tree_identical"]:
        dump_json(outdir, F_MANIFEST, manifest)
        emit(envelope("collect", False,
                      gap="采集过程修改了目标目录，已中止",
                      readonly_proof=readonly_proof))
        return 1

    dump_json(outdir, F_MANIFEST, manifest)
    dump_json(outdir, F_SPEC, spec)
    log(outdir, "collect: files=%d bytes=%d zips=%d skipped=%d"
        % (manifest["file_count"], manifest["total_bytes"],
           len(manifest["zip_entries"]), len(manifest["skipped"])))
    emit(envelope("collect", True,
                  counts={"files": manifest["file_count"],
                          "bytes": manifest["total_bytes"],
                          "zip_entries": len(manifest["zip_entries"]),
                          "skipped": len(manifest["skipped"])},
                  readonly_proof=readonly_proof,
                  outdir=outdir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
