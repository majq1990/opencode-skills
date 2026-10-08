#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""02_audit.py — 交付物审查主引擎（三源融合：验收清单 ⊕ 材料目录 ⊕ 验收标准）。

10 条规则（级别与开关见 config/acceptance_rules.json）：
  completeness(Critical) / sensitive(Critical) / empty_file(High) /
  format_mismatch(High) / forbidden_ext(High) / naming(Medium) /
  oversize(Medium) / sla_overdue(Medium) / cross_reference(Low) /
  duplicate_version(Low)

匹配算法（实测校准，勿改语义）：
  - 全局一对一分配：编号最长优先（B-26-1 先于 B-26），一个文件只归一项；
  - 先做编号精确匹配（norm(leading_id(f))==norm(cid)），无命中再回退名称包含；
  - 重复版本：同一清单项分到多文件时保留 mtime 最新，其余标 duplicate_version。

用法:
  python 02_audit.py --outdir out [--project 项目档案.json] [--rules acceptance_rules.json]

退出码：0=无 Critical；1=有 Critical（阻断验收）；2=前置条件不满足（gap）。
"""
import os
import re
import sys
import fnmatch
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daa_common import (  # noqa: E402
    F_AUDIT, F_MANIFEST, F_SPEC, LEVEL_ORDER, GapError, dump_json, emit, envelope,
    exit_gap, load_json, load_rules, log, norm_key, setup_io, skill_root, today_str,
    worst_level,
)

_ID_RE = re.compile(r"([A-Za-z]{1,4}[-_]?\d+(?:[-–]\d+)*)")

FORMAT_ALIASES = {
    "word": {"docx", "doc"}, "docx": {"docx"}, "doc": {"doc"},
    "excel": {"xlsx", "xls"}, "xlsx": {"xlsx"}, "xls": {"xls"},
    "ppt": {"pptx", "ppt"}, "pptx": {"pptx"},
    "pdf": {"pdf"}, "jpg": {"jpg", "jpeg"}, "jpeg": {"jpg", "jpeg"},
    "png": {"png"}, "txt": {"txt"}, "md": {"md"},
}

DEFAULT_RULE_LEVELS = {
    "completeness": "Critical", "sensitive": "Critical",
    "empty_file": "High", "format_mismatch": "High", "forbidden_ext": "High",
    "naming": "Medium", "oversize": "Medium", "sla_overdue": "Medium",
    "cross_reference": "Low", "duplicate_version": "Low",
}


def leading_id(name):
    m = _ID_RE.search(str(name or ""))
    return m.group(1) if m else ""


def item_key(item, idx=0):
    cid = str(item.get("id") or "").strip()
    return cid if cid else "无编号#%d" % (idx + 1)


def match_item(item, files):
    """单文件匹配策略（仅用于 informational 的 reason 提示；主分配走 assign_files）。"""
    cid = str(item.get("id") or "").strip()
    for f in files:
        if cid and norm_key(leading_id(f["path"])) == norm_key(cid):
            return "id_prefix"
    return "none"


def assign_files(checklist, files):
    """全局一对一分配。返回 ({item_key: [file,...]}, assigned_path_set)。"""
    keys = [item_key(it, i) for i, it in enumerate(checklist)]
    owner = {k: [] for k in keys}
    used = set()

    order = sorted(range(len(checklist)), key=lambda i: (-len(keys[i]), i))
    for i in order:
        k = keys[i]
        cid = str(checklist[i].get("id") or "").strip()
        if not cid:
            continue
        exact = [f for f in files
                 if f["path"] not in used
                 and norm_key(leading_id(f["path"])) == norm_key(cid)]
        if exact:
            owner[k] = exact
            used.update(f["path"] for f in exact)

    for i, it in enumerate(checklist):
        k = keys[i]
        if owner[k]:
            continue
        n = norm_key(it.get("name") or "")
        if not n:
            continue
        hits = [f for f in files
                if f["path"] not in used and n in norm_key(f["name"])]
        if hits:
            owner[k] = hits
            used.update(f["path"] for f in hits)
    return keys, owner, used


class Auditor:
    def __init__(self, rules_cfg, naming_rules, sensitive_rules, criteria):
        self.rules_cfg = rules_cfg or {}
        self.naming = naming_rules or {}
        self.sensitive = sensitive_rules or {}
        self.criteria = criteria or {}
        self.counter = 0
        self.rule_stats = {r: {"enabled": self.enabled(r), "hits": 0,
                               "by_level": {lv: 0 for lv in LEVEL_ORDER}}
                           for r in DEFAULT_RULE_LEVELS}

    def enabled(self, rule):
        return bool((self.rules_cfg.get(rule) or {}).get("enabled", True))

    def level_of(self, rule):
        cfg = self.rules_cfg.get(rule) or {}
        return cfg.get("level") or DEFAULT_RULE_LEVELS.get(rule, "Medium")

    def new_issue(self, rule, level, message, blocks=False, **kw):
        self.counter += 1
        iss = {"id": "F%04d" % self.counter, "level": level, "rule": rule,
               "message": message, "blocks_acceptance": bool(blocks)}
        iss.update({k: v for k, v in kw.items() if v not in (None, "")})
        if self.rule_stats.get(rule):
            self.rule_stats[rule]["hits"] += 1
            self.rule_stats[rule]["by_level"][level] = \
                self.rule_stats[rule].get("by_level", {}).get(level, 0) + 1
        return iss


def r_completeness(au, item, k, files):
    req = bool(item.get("required"))
    if not req or files:
        return []
    fmt = str(item.get("format") or "docx")
    return [au.new_issue(
        "completeness", au.level_of("completeness"),
        "必备交付物缺失：清单要求 %s（%s），实际目录未找到对应文件" % (k, item.get("name", "")),
        blocks=True, expected="交付 %s" % item.get("name", ""),
        advice="由 %s 补交，格式 %s" % (item.get("owner") or "待指派", fmt),
        item_key=k, item_id=k, item_name=item.get("name", ""),
        owner=item.get("owner", ""), deadline=item.get("deadline", ""))]


def r_empty_file(au, item, k, files):
    out = []
    for f in files:
        if f["size"] == 0:
            out.append(au.new_issue(
                "empty_file", au.level_of("empty_file"),
                "零字节文件，等同未交付", blocks=False,
                expected="补充实质内容", advice="补充内容后重新提交，禁止空壳占位",
                item_key=k, item_id=k, item_name=item.get("name", ""),
                path=f["path"], owner=item.get("owner", "")))
    return out


def r_format_mismatch(au, item, k, files):
    want = str(item.get("format") or "").strip().lower()
    if not want or not files:
        return []
    allow = FORMAT_ALIASES.get(want, {want})
    out = []
    for f in files:
        actual = f["ext"].lstrip(".")
        if actual and actual not in allow:
            out.append(au.new_issue(
                "format_mismatch", au.level_of("format_mismatch"),
                "格式不合规：要求 %s，实际 %s" % (want, actual),
                expected=want, actual=actual,
                item_key=k, item_id=k, item_name=item.get("name", ""),
                path=f["path"], owner=item.get("owner", "")))
    return out


def r_naming(au, item, k, files):
    out = []
    rules = (au.naming.get("rules") or []) if isinstance(au.naming.get("rules"), list) \
        else [dict(v, rule_id=rid) for rid, v in (au.naming.get("rules") or {}).items()]
    for f in files:
        name = f["name"]
        for nr in rules:
            try:
                m = re.search(nr["check"], name, re.I)
            except re.error:
                continue
            if not m:
                continue
            out.append(au.new_issue(
                "naming", au.level_of("naming"),
                "命名不合规（%s）：命中「%s」" % (nr.get("desc") or nr.get("rule_id"), m.group(0)),
                rule_id=nr.get("rule_id"), sample=m.group(0),
                item_key=k, item_id=k, item_name=item.get("name", ""),
                path=f["path"], advice=nr.get("advice", ""),
                owner=item.get("owner", "")))
    return out


def _mask_sample(text, mask):
    n = len(text)
    if mask == "keep_first6_keep_last4" and n > 10:
        return text[:6] + "*" * (n - 10) + text[-4:]
    if mask == "keep_first3_keep_last4" and n > 7:
        return text[:3] + "*" * (n - 7) + text[-4:]
    if mask == "keep_first4_keep_last4" and n > 8:
        return text[:4] + "*" * (n - 8) + text[-4:]
    if mask == "keep_first2":
        return text[:2] + "*" * max(0, n - 2)
    return "*" * n


def r_sensitive(au, item, k, files):
    out = []
    allow = au.sensitive.get("allowlist_files") or []
    for f in files:
        if any(fnmatch.fnmatch(f["path"], pat) for pat in allow):
            continue
        text = f.get("text_excerpt") or ""
        if not text:
            continue
        for pat in au.sensitive.get("patterns") or []:
            try:
                m = re.search(pat["regex"], text)
            except re.error:
                continue
            if not m:
                continue
            out.append(au.new_issue(
                "sensitive", au.level_of("sensitive"),
                "检出敏感信息（%s）" % pat.get("id", ""),
                blocks=True, pattern_id=pat.get("id", ""),
                sample=_mask_sample(m.group(0), pat.get("mask", "full")),
                item_key=k, item_id=k, item_name=item.get("name", ""),
                path=f["path"], file_name=f["name"],
                advice="脱敏后再交付；本工具只报告不回写，原文件需人工处理"))
    return out


def r_cross_reference(au, item, k, files, ref_targets):
    """引用语义：正文引用的编号对应的交付物**文件缺失**才报（清单里有 id 但没文件）。
    ref_targets: {norm_id: has_files(bool)}。"""
    out = []
    seen_refs = set()
    for f in files:
        for m in re.finditer(r"[Bb][-_]?\d+(?:[-–]\d+)*", f.get("text_excerpt") or ""):
            ref = m.group(0)
            if ref in seen_refs:
                continue
            seen_refs.add(ref)
            nk = norm_key(ref)
            if nk not in ref_targets:
                continue          # 不在清单内的编号不算断链（可能只是文字提及）
            if ref_targets[nk]:
                continue          # 引用的交付物文件存在
            out.append(au.new_issue(
                "cross_reference", au.level_of("cross_reference"),
                "正文引用的交付物编号 %s 对应的材料在目录中缺失" % ref,
                ref=ref, item_key=k, item_id=k, item_name=item.get("name", ""),
                path=f["path"]))
    return out


def r_duplicate_version(au, item, k, files):
    if len(files) < 2:
        return []
    keep = max(files, key=lambda f: f["mtime"])
    out = []
    for f in files:
        if f["path"] == keep["path"]:
            continue
        out.append(au.new_issue(
            "duplicate_version", au.level_of("duplicate_version"),
            "重复版本：与 %s 重复，判定最新版为 %s（%s）" % (f["name"], keep["name"], keep["mtime"]),
            item_key=k, item_id=k, item_name=item.get("name", ""),
            path=f["path"], advice="将旧版移出交付目录或归档，保留唯一有效版本"))
    return out


def r_forbidden_ext(au, item, k, files, forbidden):
    out = []
    for f in files:
        if f["ext"] in forbidden:
            out.append(au.new_issue(
                "forbidden_ext", au.level_of("forbidden_ext"),
                "扩展名在禁入清单内：%s" % f["ext"],
                ext=f["ext"], item_key=k, item_id=k, item_name=item.get("name", ""),
                path=f["path"], advice="移除临时/日志/备份文件后重新交付"))
    return out


def r_oversize(au, item, k, files, max_mb):
    out = []
    for f in files:
        if max_mb and f["size"] > max_mb * 1024 * 1024:
            out.append(au.new_issue(
                "oversize", au.level_of("oversize"),
                "单文件超过 %.0fMB 上限（实际 %.1fMB）" % (max_mb, f["size"] / 1048576),
                item_key=k, item_id=k, item_name=item.get("name", ""),
                path=f["path"], advice="拆分或压缩后重新提交"))
    return out


def r_sla_overdue(au, item, k, files):
    deadline = str(item.get("deadline") or "").strip()
    if not deadline or deadline > today_str():
        return []
    return [au.new_issue(
        "sla_overdue", au.level_of("sla_overdue"),
        "交付时限已过（截止 %s，审查日 %s）" % (deadline, today_str()),
        item_key=k, item_id=k, item_name=item.get("name", ""),
        owner=item.get("owner", ""), deadline=deadline,
        advice="明确补交时间并同步项目经理，纳入周报跟踪")]


def main():
    setup_io()
    ap = argparse.ArgumentParser(description="交付物审查主引擎")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--project", default=None, help="项目档案（覆盖 spec 中记录的）")
    ap.add_argument("--rules", default=None, help="审查规则覆盖文件")
    a = ap.parse_args()
    outdir = a.outdir

    try:
        manifest = load_json(os.path.join(outdir, F_MANIFEST), required=True)
        spec = load_json(os.path.join(outdir, F_SPEC), required=True)
        if a.project:
            project = load_json(a.project, required=True)
            spec["deliverable_list"] = project.get("deliverable_list", spec["deliverable_list"])
            spec["acceptance_criteria"] = project.get(
                "acceptance_criteria", spec["acceptance_criteria"])
            spec["project"] = project.get("project", spec.get("project", {}))
        rules_cfg = load_json(a.rules, required=False, default={}) if a.rules else {}
        rules_cfg = rules_cfg or load_rules("acceptance_rules.json", required=False) or {}
        if not rules_cfg:
            rules_cfg = {}
        naming_rules = load_rules("naming_rules.json", required=False) or {}
        sensitive_rules = load_rules("sensitive_rules.json", required=False) or {}
        if not os.path.isfile(os.path.join(skill_root(), "config",
                                           "acceptance_rules.json")) and not a.rules:
            raise GapError("config/acceptance_rules.json 不存在")
    except GapError as e:
        return exit_gap("audit", str(e))

    checklist = spec.get("deliverable_list") or []
    files = manifest.get("files") or []
    if not checklist:
        return exit_gap("audit", "验收清单为空，无法审查")
    criteria = spec.get("acceptance_criteria") or {}
    forbidden = set(x.lower() for x in (rules_cfg.get("forbidden_extensions")
                                        or criteria.get("forbidden_extensions") or []))
    max_mb = rules_cfg.get("oversize_max_mb") or criteria.get("oversize_max_mb") or 100
    forbidden = forbidden or {".tmp", ".log", ".bak", ".cache"}

    au = Auditor(rules_cfg, naming_rules, sensitive_rules, criteria)
    keys, owner, used = assign_files(checklist, files)
    # 引用目标表：{norm_id: 该编号对应的交付物是否有文件}
    ref_targets = {}
    for i, item in enumerate(checklist):
        cid = str(item.get("id") or "").strip()
        if cid:
            ref_targets[norm_key(cid)] = bool(owner.get(keys[i]))
    # 清单外文件也要过体检类规则（empty/forbidden/oversize/naming）

    results, all_issues = [], []
    unmatched = []
    for i, item in enumerate(checklist):
        k = keys[i]
        fs = sorted(owner.get(k) or [], key=lambda f: f["mtime"])
        issues = []
        issues += r_completeness(au, item, k, fs)
        issues += r_empty_file(au, item, k, fs)
        issues += r_format_mismatch(au, item, k, fs)
        if (criteria.get("naming_required", True)) or bool(item.get("required")):
            issues += r_naming(au, item, k, fs)
        if criteria.get("sensitive_scan_required", True):
            issues += r_sensitive(au, item, k, fs)
        issues += r_duplicate_version(au, item, k, fs)
        issues += r_forbidden_ext(au, item, k, fs, forbidden)
        issues += r_oversize(au, item, k, fs, max_mb)
        issues += r_sla_overdue(au, item, k, fs)
        if files and criteria.get("cross_reference_enabled", True):
            issues += r_cross_reference(au, item, k, fs, ref_targets)
        all_issues += issues
        results.append({
            "item_key": k, "item_id": str(item.get("id") or "") or k,
            "item_name": item.get("name", ""), "format": item.get("format", ""),
            "required": bool(item.get("required")), "owner": item.get("owner", ""),
            "deadline": item.get("deadline", ""), "note": item.get("note", ""),
            "matched_by": ("id_prefix" if fs and str(item.get("id") or "").strip()
                           and norm_key(leading_id(fs[0]["path"]))
                           == norm_key(str(item.get("id"))) else
                          ("name_contains" if fs else "none")),
            "files": fs, "file_paths": [f["path"] for f in fs],
            "level": worst_level([iss["level"] for iss in issues]) if issues else "Pass",
            "issues": issues,
        })

    for f in files:
        if f["path"] in used:
            continue
        unmatched.append({"path": f["path"], "name": f["name"], "ext": f["ext"],
                          "size": f["size"],
                          "reason": "不在交付物清单内的文件（提示项，非违规）"})
        # 清单外文件的体检类规则：挂在「清单外」虚拟项下
        orph = {"name": f["name"], "owner": ""}
        for iss in (r_empty_file(au, orph, "清单外", [f])
                    + r_forbidden_ext(au, orph, "清单外", [f], forbidden)
                    + r_oversize(au, orph, "清单外", [f], max_mb)
                    + r_naming(au, orph, "清单外", [f])):
            all_issues.append(iss)
            unmatched[-1].setdefault("issues", []).append(iss["id"])

    levels = {lv: 0 for lv in LEVEL_ORDER}
    for r in results:
        levels[r["level"]] += 1
    for iss in all_issues:
        levels[iss["level"]] += 1

    blocking = sum(1 for x in all_issues if x.get("blocks_acceptance"))
    if levels["Critical"] > 0:
        verdict = "不通过"
    elif levels["High"] > 0 or levels["Medium"] > 0:
        verdict = "有条件通过"
    else:
        verdict = "通过"

    doc = {
        "ok": True, "step": "audit", "audit_date": today_str(),
        "project": spec.get("project", {}),
        "deliverable_dir": spec.get("target", ""),
        "totals": {
            "files_scanned": manifest.get("file_count", len(files)),
            "checklist_items": len(checklist),
            "matched_items": sum(1 for r in results if r["files"]),
            "missing_items": sum(1 for r in results if not r["files"]
                                 and r["required"]),
            "unmatched_files": len(unmatched),
            "issues": len(all_issues),
            "blocking_issues": blocking,
        },
        "levels": levels,
        "rule_stats": au.rule_stats,
        "results": results,
        "all_issues": all_issues,
        "informational": unmatched,
        "verdict": verdict,
    }
    dump_json(outdir, F_AUDIT, doc)
    log(outdir, "audit: issues=%d blocking=%d verdict=%s"
        % (len(all_issues), blocking, verdict))
    emit(envelope("audit", True, verdict=verdict,
                  totals=doc["totals"], levels=levels,
                  critical=levels["Critical"]))
    return 1 if levels["Critical"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
