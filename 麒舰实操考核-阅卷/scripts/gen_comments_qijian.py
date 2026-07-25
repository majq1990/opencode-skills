"""
麒舰实操考核评语生成器。
- 读取 _grading_v1.json
- 为每位考生生成评语文档（含分数+扣分明细+建议）
- 不接入任何平台，仅输出参考文件

用法: python gen_comments_qijian.py <workdir>
"""
import os, sys, json

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\麒舰"
JSON_PATH = os.path.join(ROOT, "_grading_v1.json")
OUT_MD = os.path.join(ROOT, "_grading_final.md")


def generate_comment(rec):
    """为单个人生成评语"""
    name = rec["name"]
    total = rec["total"]
    total_max = rec["total_max"]
    rows = rec["rows"]
    pct = total / total_max * 100 if total_max > 0 else 0

    lines = []
    lines.append(f"## {name} — {total:.1f}/{total_max:.1f}（{pct:.0f}%）")
    lines.append("")

    # 模块汇总
    lines.append("### 模块得分")
    lines.append("")
    lines.append("| 模块 | 得分 | 满分 | 完成度 |")
    lines.append("|---|---|---|---|")
    for mod in rec.get("module_scores", {}):
        sc = rec["module_scores"][mod]
        mx = rec["module_max"].get(mod, 0)
        pct_mod = sc / mx * 100 if mx > 0 else 0
        icon = "✓" if pct_mod >= 90 else "⚠" if pct_mod >= 60 else "✗"
        lines.append(f"| {mod} | {sc:.1f} | {mx:.1f} | {icon} {pct_mod:.0f}% |")
    lines.append(f"| **合计** | **{total:.1f}** | **{total_max:.1f}** | **{pct:.0f}%** |")
    lines.append("")

    # 明细
    lines.append("### 各采分点明细")
    lines.append("")

    # 按模块分组
    modules_ordered = []
    for r in rows:
        if r["module"] not in modules_ordered:
            modules_ordered.append(r["module"])

    for mod in modules_ordered:
        mod_rows = [r for r in rows if r["module"] == mod]
        lines.append(f"**{mod}** （{sum(r['awarded'] for r in mod_rows):.1f}/{sum(r['max'] for r in mod_rows):.1f}）")
        lines.append("")
        lines.append("| 代码 | 要求 | 满分 | 得分 | 截图 | 评判 |")
        lines.append("|---|---|---|---|---|---|")
        for r in mod_rows:
            short = r["desc"][:50]
            img_tag = f"{r['imgs']}张" if r["imgs"] > 0 else "0"
            lines.append(f"| {r['code']} | {short} | {r['max']} | {r['awarded']} | {img_tag} | {r['verdict'][:40]} |")
        lines.append("")

    # 建议
    missing = [r for r in rows if r["awarded"] == 0 and r["max"] >= 2]
    partial = [r for r in rows if 0 < r["awarded"] < r["max"] * 0.8 and r["max"] >= 2]

    lines.append("### 改进建议")
    lines.append("")
    if missing:
        lines.append("**尚未完成的采分点（建议补充）**：")
        for r in missing:
            lines.append(f"- {r['code']} {r['desc']}（{r['max']}分）：{r['note']}")
        lines.append("")
    if partial:
        lines.append("**部分完成的采分点（建议补充截图）**：")
        for r in partial:
            lines.append(f"- {r['code']} {r['desc']}（{r['awarded']}/{r['max']}分）：当前{r['imgs']}张截图，建议补充至3张以上")
        lines.append("")

    if not missing and not partial:
        lines.append("✅ 各模块完成度高，无明显扣分点。")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def main():
    if not os.path.exists(JSON_PATH):
        print(f"[✗] 未找到 {_grading_v1.json}，请先运行 grading_qijian.py")
        sys.exit(1)

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    md_lines = [
        "# 麒舰实操考核 — 终版评语",
        "",
        f"共 {len(report)} 份答卷，满分 100 分。",
        "",
        "## 总分排行",
        "",
        "| 排名 | 姓名 | 总分 | 满分 | 正确率 | 评级 |",
        "|---|---|---|---|---|---|"
    ]

    # 评级函数
    def grade_level(pct):
        if pct >= 90: return "🟢 优"
        if pct >= 80: return "🟡 良"
        if pct >= 70: return "🟠 中"
        if pct >= 60: return "🔴 及格"
        return "⬜ 不及格"

    for i, r in enumerate(sorted(report, key=lambda x: -x["total"]), 1):
        pct = r["total"] / r["total_max"] * 100
        level = grade_level(pct)
        md_lines.append(f"| {i} | {r['name']} | **{r['total']:.1f}** | {r['total_max']} | {pct:.0f}% | {level} |")

    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    for r in sorted(report, key=lambda x: -x["total"]):
        md_lines.append(generate_comment(r))

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"[✓] 评语已生成: {OUT_MD}")


if __name__ == "__main__":
    main()
