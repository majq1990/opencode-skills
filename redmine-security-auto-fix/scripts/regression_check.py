#!/usr/bin/env python3
"""解析层一键回归：对固定附件集重跑 解析+合并，与基线比对。

用法：
  python scripts/regression_check.py                 # 比对（默认）
  python scripts/regression_check.py --update-baseline  # 重录基线（行为变化确认后用）
  python scripts/regression_check.py --corpus-dir <安全语料目录>

基线存 tests/baseline/parse_regression.json。检索层（enrich_all）不在本脚本
范围内——它依赖远端服务且分钟级耗时；检索/方案层的回归用 12 案 journal
核对流程（见 skill-verify/goal-validate/验证报告.md）。

比对口径（逐附件）：
  - rows: 解析出的漏洞条数
  - names: 清洗后名称排序串（截断到 120 字/条）
  - levels: 等级分布
  - cve_count: 带 CVE 的条数
任何一项不一致即 FAIL 并打印差异摘要。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from process_issue import merge_vulnerabilities  # noqa: E402
from report_parser import parse_report  # noqa: E402

DEFAULT_CORPUS = Path(r"D:\opencode\_archive\security-corpus")
BASELINE = SCRIPTS.parent / "tests" / "baseline" / "parse_regression.json"

# (标签, 案件目录, 文件名通配) —— 覆盖全部已支持格式的代表样本
MANIFEST = [
    ("444700-xlsx漏扫", "444700", "*.xlsx"),
    ("444168-xlsx大清单", "444168", "*.xlsx"),
    ("444808-docx渗透", "444808", "*.docx"),
    ("477801-源扫pdf", "477801", "*首测*.pdf"),
    ("477801-口令docx", "477801", "口令问题.docx"),
    ("样张-CWETop25", "466274", "*CWETop25.pdf"),
    ("样张-CWETop25中文", "450683", "*CWETop25.pdf"),
    ("样张-SANS25", "448583", "*CWESANSTop25.pdf"),
    ("样张-DevWorkbook", "452297", "*DeveloperWorkbook.pdf"),
    ("样张-AppScan", "466281", "*appscan*.pdf"),
    ("样张-ZAP-PDF", "458103", "*ZAP-Report*.pdf"),
    ("样张-ZAP-HTML", "527551", "*ZAP-Report*.html"),
    ("样张-Trivy", "450544", "*sani12.txt"),
    ("样张-osv", "450544", "*sani3.txt"),
]


def metrics_for(path: Path) -> dict:
    parsed = parse_report(path)
    merged = merge_vulnerabilities(parsed.get("vulns") or [])
    names = sorted(
        (m.get("name") or "")[:120] for m in merged
    )
    levels: dict[str, int] = {}
    for m in merged:
        levels[m.get("level", "medium")] = levels.get(m.get("level", "medium"), 0) + 1
    return {
        "rows": len(merged),
        "cve_count": sum(1 for m in merged if m.get("cve")),
        "levels": levels,
        "names_hash": hashlib.sha256(
            json.dumps(names, ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16],
        "names": names,
    }


def collect(corpus_dir: Path) -> dict:
    result = {}
    for label, case_dir, pattern in MANIFEST:
        base = corpus_dir / case_dir
        files = sorted(base.glob(pattern)) if base.is_dir() else []
        if not files:
            result[label] = {"error": f"找不到样本 {base}/{pattern}"}
            continue
        merged_metrics = {
            "files": {},
            "rows": 0,
            "cve_count": 0,
            "levels": {},
        }
        all_names = []
        for f in files:
            try:
                m = metrics_for(f)
            except Exception as exc:
                merged_metrics["files"][f.name] = {"error": f"{type(exc).__name__}: {exc}"}
                continue
            m.pop("names")
            merged_metrics["files"][f.name] = m
            merged_metrics["rows"] += m["rows"]
            merged_metrics["cve_count"] += m["cve_count"]
            for level, n in m["levels"].items():
                merged_metrics["levels"][level] = merged_metrics["levels"].get(level, 0) + n
            # names 汇总后单独 hash
            all_names.extend([])
        # 重新取一次 names 做整体 hash（避免上一循环内存残留的复杂度）
        names_all = []
        for f in files:
            try:
                names_all.extend(n[:120] for n in metrics_for(f).get("names", []))
            except Exception:
                pass
        merged_metrics["names_hash"] = hashlib.sha256(
            json.dumps(sorted(names_all), ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16]
        result[label] = merged_metrics
    return result


def diff(deep: dict, base: dict) -> list[str]:
    problems = []
    for label, base_m in base.items():
        cur_m = deep.get(label)
        if cur_m is None:
            problems.append(f"[{label}] 当前环境缺失该样本")
            continue
        if cur_m.get("error") or base_m.get("error"):
            if cur_m.get("error") != base_m.get("error"):
                problems.append(f"[{label}] 错误态变化: {base_m.get('error')} -> {cur_m.get('error')}")
            continue
        for key in ("rows", "cve_count", "names_hash"):
            if cur_m.get(key) != base_m.get(key):
                problems.append(
                    f"[{label}] {key}: 基线 {base_m.get(key)} -> 当前 {cur_m.get(key)}"
                )
        if cur_m.get("levels") != base_m.get("levels"):
            problems.append(
                f"[{label}] levels: 基线 {base_m.get('levels')} -> 当前 {cur_m.get('levels')}"
            )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", default=str(DEFAULT_CORPUS))
    parser.add_argument("--update-baseline", action="store_true",
                        help="以当前解析结果重录基线（确认行为变化是有意的之后才用）")
    args = parser.parse_args()

    deep = collect(Path(args.corpus_dir))
    # 基线里不存 names 明细，只存 hash，控制基线体积
    slim = {
        label: {k: v for k, v in m.items() if k != "names"} if isinstance(m, dict) else m
        for label, m in deep.items()
    }
    for label, m in slim.items():
        if isinstance(m, dict) and "files" in m:
            m["files"] = {
                fn: {k: v for k, v in fm.items() if k != "names"}
                for fn, fm in m["files"].items()
            }

    if args.update_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(
            json.dumps(slim, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"基线已更新: {BASELINE}（{len(slim)} 个样本组）")
        return 0

    if not BASELINE.exists():
        print(f"基线不存在：{BASELINE}，先跑 --update-baseline", file=sys.stderr)
        return 2
    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    problems = diff(deep, base)
    if problems:
        print(f"回归 FAIL（{len(problems)} 项差异）：")
        for p in problems:
            print("  -", p)
        return 1
    print(f"回归 PASS：{len(base)} 个样本组与基线一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
