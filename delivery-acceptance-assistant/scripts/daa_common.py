# -*- coding: utf-8 -*-
"""delivery-acceptance-assistant 公共库（门面模块）。

实际实现拆分在：
  - daa_io.py     路径安全 + JSON/CSV/文本 IO + 哈希 + 目录安全检查
  - daa_ooxml.py  OOXML 文本提取 + 模板替换（版面保持）
本模块保持「from daa_common import ...」的单点导入兼容，并承载
信封输出、日志、规则引擎常量等轻量公共件。

约束：仅使用 Python 标准库；不访问网络；审查类操作不修改交付目录。
"""
import os
import re
import sys
import json
import datetime

from daa_io import (  # noqa: F401
    GapError, safe_path, _normpath, skill_root,
    load_json, load_rules, ensure_parent, dump_json, write_text,
    read_csv, write_csv, rel_of, sha256_file, sha256_tree,
    ensure_target_readable, ensure_outdir_safe,
)
from daa_ooxml import (  # noqa: F401
    DOCX_PARTS, XLSX_PARTS, PPTX_PARTS,
    extract_ooxml_text, extract_doc_legacy, get_text,
    ooxml_layout, rewrite_zip, parts_filter_for,
)

SKILL_NAME = "delivery-acceptance-assistant"
SKILL_VERSION = "1.0.0"

# 中间产物固定文件名（各脚本统一读写）
F_MANIFEST = "manifest.json"
F_SPEC = "spec_effective.json"
F_AUDIT = "audit_result.json"
F_REPORT = "audit_report.md"
F_MISSING = "missing_list.csv"
F_TRACK = "nextday_tracking.md"
F_STATE = "audit_state.json"
F_RISK = "risk_register.csv"
F_LOG = "run_log.txt"

# 兼容别名：旧调用点使用 daa_common.OOXML_EXT
OOXML_EXT = {".docx", ".xlsx", ".pptx"}


def setup_io():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass


def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str():
    return datetime.date.today().isoformat()


def log(workdir, msg):
    line = "[%s] %s" % (now_str(), msg)
    print(line)
    try:
        d = safe_path(workdir)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, F_LOG)
        with open(p, "a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")
    except Exception:
        pass


def envelope(step, ok, **kw):
    out = {"ok": bool(ok), "step": step, "skill": SKILL_NAME, "version": SKILL_VERSION,
           "time": now_str()}
    out.update(kw)
    if not ok and "gap" not in out and not out.get("preview"):
        out["gap"] = "未说明原因"
    return out


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    return obj


def exit_gap(step, gap, **kw):
    """统一 gap 出口：打印信封 + 退出码 2。额外 kw 附在信封上（如明细列表）。"""
    emit(envelope(step, False, gap=gap, **kw))
    return 2


# ------------------------------------------------------------------ 规则引擎
LEVEL_ORDER = ["Pass", "Low", "Medium", "High", "Critical"]


def worst_level(levels):
    best = "Pass"
    for lv in levels:
        if lv in LEVEL_ORDER and LEVEL_ORDER.index(lv) > LEVEL_ORDER.index(best):
            best = lv
    return best


def norm_key(s):
    """去标点/空白并小写，用于跨表按名称对齐。"""
    return re.sub(r"[\s_\-—－:：,，。.、/\\()（）]+", "", str(s or "")).lower()
