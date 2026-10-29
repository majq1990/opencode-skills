"""将人工复核结果应用到星桥自动初评报告。"""
from __future__ import annotations

import csv
import json
import os
import sys


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("用法: apply_manual_review_starbridge.py <阅卷目录> <人工复核JSON>")
    root, override_path = sys.argv[1:]
    source = os.path.join(root, "_grading_starbridge_v1.json")
    target = os.path.join(root, "_grading_starbridge_v2_manual.json")
    markdown = os.path.join(root, "_grading_starbridge_v2_manual.md")
    csv_path = os.path.join(root, "_grading_starbridge_v2_manual.csv")
    with open(source, "r", encoding="utf-8") as f:
        report = json.load(f)
    with open(override_path, "r", encoding="utf-8") as f:
        overrides = json.load(f)

    for rec in report:
        changes = overrides.get(rec["name"], {})
        if not changes:
            continue
        for row in rec["rows"]:
            change = changes.get(row["code"])
            if not change:
                continue
            score = float(change["score"])
            if not 0 <= score <= row["max"]:
                raise ValueError(f"{rec['name']} {row['code']} 分值越界: {score}")
            row["auto_awarded"] = row["awarded"]
            row["awarded"] = score
            row["manual_review"] = change["reason"]
            row["verdict"] = "人工复核：" + change["reason"]

        section_scores = {name: 0.0 for name in rec["section_max"]}
        for row in rec["rows"]:
            section_scores[row["section"]] += row["awarded"]
        rec["section_scores"] = section_scores
        rec["total"] = round(sum(section_scores.values()), 1)
        rec["manual_reviewed"] = True

    report.sort(key=lambda x: (-x["total"], x["name"]))
    with open(target, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    lines = ["# 星桥高级认证 — 人工复核成绩预览", "", "本报告已排除题干关键词的误命中；尚未回写大课堂成绩。", "", "| 排名 | 答卷 | 总分 | 场景得分（1-5） |", "|---:|---|---:|---|"]
    for index, rec in enumerate(report, 1):
        values = " / ".join(f"{score:.1f}" for score in rec["section_scores"].values())
        lines.append(f"| {index} | {rec['name']} | **{rec['total']:.1f}/100** | {values} |")
    lines += ["", "## 第五场景复核结论", ""]
    for rec in report:
        rows = [row for row in rec["rows"] if row["code"].startswith("S5-")]
        lines.append(f"### {rec['name']} — {rec['section_scores']['binlog 多表实时同步']:.1f}/20")
        for row in rows:
            if "manual_review" in row:
                lines.append(f"- {row['code']}：{row['awarded']:.1f}/{row['max']}，{row['manual_review']}")
        lines.append("")
    with open(markdown, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["答卷", "总分", *report[0]["section_scores"].keys()])
        for rec in report:
            writer.writerow([rec["name"], rec["total"], *rec["section_scores"].values()])
    print(f"[✓] 已生成 {target}")
    print(f"[✓] 已生成 {markdown}")
    print(f"[✓] 已生成 {csv_path}")


if __name__ == "__main__":
    main()
