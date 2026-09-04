"""根据星桥初评 JSON 生成终版评语预览。"""
from __future__ import annotations

import json
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\星桥高级认证阅卷"
SRC = os.path.join(ROOT, "_grading_starbridge_v1.json")
OUT = os.path.join(ROOT, "_grading_starbridge_final.md")

def level(pct: float) -> str:
    if pct >= 0.9:
        return "优"
    if pct >= 0.8:
        return "良"
    if pct >= 0.7:
        return "中"
    if pct >= 0.6:
        return "及格"
    return "不及格"

def main() -> None:
    if not os.path.exists(SRC):
        raise SystemExit(f"[✗] 未找到 {SRC}，请先运行 grading_starbridge.py")
    with open(SRC, "r", encoding="utf-8") as f:
        report = json.load(f)
    lines = ["# 星桥高级认证 — 终版评语预览", "", f"共 {len(report)} 份答卷；本报告为自动初评后的复核预览，不自动回写 Moodle。", "", "## 总分排行", "", "| 排名 | 答卷 | 总分 | 完成度 | 评级 |", "|---:|---|---:|---:|---|"]
    for i, rec in enumerate(sorted(report, key=lambda x: -x["total"]), 1):
        pct = rec["total"] / rec["total_max"] if rec["total_max"] else 0
        lines.append(f"| {i} | {rec['name']} | **{rec['total']:.1f}/{rec['total_max']}** | {pct:.0%} | {level(pct)} |")
    for rec in sorted(report, key=lambda x: -x["total"]):
        pct = rec["total"] / rec["total_max"] if rec["total_max"] else 0
        lines += ["", "---", "", f"## {rec['name']} — {rec['total']:.1f}/{rec['total_max']}（{pct:.0%}）", "", "### 场景得分", "", "| 场景 | 得分 | 满分 |", "|---|---:|---:|"]
        for section, score in rec["section_scores"].items():
            lines.append(f"| {section} | {score:.1f} | {rec['section_max'][section]:.0f} |")
        missing = [r for r in rec["rows"] if r["awarded"] == 0]
        partial = [r for r in rec["rows"] if 0 < r["awarded"] < r["max"]]
        lines += ["", "### 扣分与复核建议", ""]
        if missing:
            lines.append("**未定位到作答证据：**")
            for r in missing:
                suffix = "；有截图但需视觉复核" if r.get("needs_visual") else ""
                lines.append(f"- {r['code']} {r['desc']}（{r['max']} 分）{suffix}")
        if partial:
            lines.append("**部分覆盖：**")
            for r in partial:
                lines.append(f"- {r['code']} {r['desc']}：{r['awarded']}/{r['max']} 分；{r['verdict']}")
        if not missing and not partial:
            lines.append("自动初评未发现明显缺项；仍建议抽查截图中的 URL、水印、返回值和运行日志。")
        lines.append("\n自动评分说明：截图内的细节无法完全由 docx 文本提取，提交成绩前应人工查看对应 media/ 图片。")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[✓] 已生成 {OUT}")

if __name__ == "__main__":
    main()
