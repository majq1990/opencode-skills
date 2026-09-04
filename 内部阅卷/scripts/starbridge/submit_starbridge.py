"""把人工复核后的星桥场景分提交到 Moodle 的 Q2~Q6。"""
from __future__ import annotations

import html
import json
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GENERIC_SCRIPT_DIR = os.path.join(SCRIPT_DIR, "..", "common")
sys.path.insert(0, GENERIC_SCRIPT_DIR)
from moodle_submit import fetch_form, post_grade  # noqa: E402

SECTIONS = [
    "ddcat 数据模型",
    "MIS 接口代理",
    "案卷上报调度",
    "多媒体增量同步",
    "binlog 多表实时同步",
]
SLOTS = [2, 3, 4, 5, 6]


def comment(name: str, section: str, score: float, total: float) -> str:
    summary = ""
    if section == "binlog 多表实时同步":
        summary = (
            "已核验实时运行日志及人口、房屋、楼栋三表的变更同步结果。"
            if score >= 20
            else "未达到可运行的 binlog 多表实时同步标准，已按脚本、截图和运行日志的实际证据评分。"
        )
    return (
        f"<p>{html.escape(section)}：{score:.1f}/20 分。</p>"
        f"<p>已对 {html.escape(name)} 的配置截图、脚本和验证结果进行人工复核。{summary}</p>"
        f"<p>本次五个场景合计：{total:.1f}/100 分。</p>"
    )


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("用法: submit_starbridge.py <阅卷目录> [--only <attempt>] [--commit]")
    root = sys.argv[1]
    commit = "--commit" in sys.argv
    only_attempt = None
    if "--only" in sys.argv:
        index = sys.argv.index("--only")
        if index + 1 >= len(sys.argv):
            raise SystemExit("--only 后必须指定答卷 attempt 编号")
        only_attempt = int(sys.argv[index + 1])
    source = os.path.join(root, "_grading_starbridge_v2_manual.json")
    result_path = os.path.join(root, "_submit_results_starbridge.json")
    if not os.environ.get("MOODLE_COOKIE"):
        raise SystemExit("缺少 MOODLE_COOKIE")
    with open(source, "r", encoding="utf-8") as f:
        reports = json.load(f)
    if only_attempt is not None:
        reports = [rec for rec in reports if int(rec["name"].split("_", 1)[0]) == only_attempt]
        if not reports:
            raise SystemExit(f"未找到 attempt={only_attempt} 的人工复核成绩")

    results = []
    for rec in reports:
        attempt = int(rec["name"].split("_", 1)[0])
        for section, slot in zip(SECTIONS, SLOTS):
            mark = rec["section_scores"][section]
            form = fetch_form(attempt, slot)
            fields = form["fields"]
            prefix = f"q{form['quba']}:{slot}_" if form["quba"] else ""
            maxmark = fields.get(f"{prefix}-maxmark")
            if not form["quba"] or str(maxmark) not in {"20", "20.0"}:
                raise RuntimeError(
                    f"预检失败 attempt={attempt}, slot={slot}: quba={form['quba']}, maxmark={maxmark}"
                )
            item = {
                "attempt": attempt,
                "name": rec["name"],
                "slot": slot,
                "section": section,
                "mark": mark,
                "maxmark": maxmark,
            }
            if commit:
                item["result"] = post_grade(
                    attempt, slot, mark, comment(rec["name"], section, mark, rec["total"]), dry_run=False
                )
                if not item["result"].get("ok"):
                    results.append(item)
                    with open(result_path, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                    raise RuntimeError(f"提交失败 attempt={attempt}, slot={slot}: {item['result']}")
                time.sleep(0.5)
            else:
                item["result"] = "dry-run ok"
            results.append(item)
            print(f"{'POST' if commit else 'CHECK'} attempt={attempt} slot={slot} {section}={mark:.1f}/20")

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    mode = "提交" if commit else "预检"
    print(f"[OK] {mode}完成：{len(results)} 个题目，结果：{result_path}")


if __name__ == "__main__":
    main()
