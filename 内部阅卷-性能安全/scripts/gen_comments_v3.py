"""
v3 评语生成器
- 引入标准答卷基线（reference_baseline.json）
- 对 v1 "90% 折扣"项：截图数 ≥ 标准 → 回满分并标"覆盖完整"
- 扣分文案：明确"标准应有 X，本卷 Y"对比
- 重写 _grading_v3.json / _submit_plan.json / _submit_preview.md

用法: python gen_comments_v3.py <workdir>
"""
import os, sys, json, copy

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\阅卷"
BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "references", "reference_baseline.json")
BASELINE = json.load(open(BASE_PATH, encoding="utf-8"))

# 视觉细查已覆盖的 code（grading_v2.py 已处理，不再二次校准）
VISUAL_COVERED = {
    "P1-1", "P1-4", "P2-1", "P2-2", "P2-3", "P2-4", "P2-5", "P2-6", "P2-7",
    "S1-1", "S2-1", "S2-2", "S2-3", "S3-1",
}


def baseline_recalibrate(rec):
    """对未视觉覆盖项做截图数 vs 标准基线对比；imgs >= std → 回满分"""
    rec["v3_adjustments"] = []
    for q in (1, 2):
        for r in rec[f"Q{q}"]:
            code = r.get("code", "")
            if code in VISUAL_COVERED or code == "MISS":
                continue
            imgs = int(r.get("imgs", 0) or 0)
            mx = r.get("max", 0)
            aw = r.get("awarded", 0)
            base = BASELINE.get(code, {})
            std = int(base.get("std_min_imgs", 1))
            std_desc = base.get("std_desc", "")

            # 论述题 P1-9 走原 verdict 逻辑（基于字数）
            if code == "P1-9":
                if aw < mx:
                    if imgs == 0 and "无有效论述" in r.get("verdict", ""):
                        r["verdict_v3"] = f"❌ 未论述（标准：{std_desc}）"
                    else:
                        r["verdict_v3"] = f"⚠ 论述不完整（标准：{std_desc}）"
                continue

            if aw == 0:
                # 0 截图 / 未作答：保留 0，文案补"标准应有"对比
                if imgs == 0:
                    r["verdict_v3"] = f"❌ 未提供任何截图。标准答卷此处应有 {std} 张截图，内容覆盖：{std_desc}"
                else:
                    r["verdict_v3"] = f"❌ 截图未对应采分要求。标准：{std_desc}"
                continue

            if aw == mx:
                # 已满分，不动
                continue

            # 截图数 vs 标准基线
            if imgs >= std:
                # 内容覆盖标准 → 回满分
                old = aw
                r["awarded"] = float(mx)
                r["verdict_v3"] = f"✓ 截图 {imgs} 张 ≥ 标准 {std} 张，内容覆盖完整（标准：{std_desc}）"
                rec["v3_adjustments"].append({
                    "code": code, "old": old, "new": float(mx),
                    "reason": f"imgs {imgs}≥std {std}",
                })
            else:
                # 截图数不足，保留 90% 折扣，但写清"缺什么"
                r["verdict_v3"] = (
                    f"⚠ 仅 {imgs} 张截图（标准需 {std} 张）。标准答卷此处包含：{std_desc}。"
                    f"本卷可能未覆盖完整步骤。"
                )
    return rec


def gen_comment_html(rec, qno):
    qname = "性能监控" if qno == 1 else "安全运维"
    rows = rec.get(f"Q{qno}", [])
    score = rec.get(f"q{qno}_score", 0)
    raw = rec.get(f"q{qno}_raw", 0)
    mx_sum = rec.get(f"q{qno}_max", 50)

    if rows and rows[0].get("code") == "MISS":
        return f"<p><b>Q{qno} {qname}：0/50 — 未提交本题</b></p>"

    lines = []
    lines.append(f"<p><b>Q{qno} {qname} — 总分 {score:.1f}/50</b></p>")
    if mx_sum > 50:
        lines.append(f"<p style=\"color:#888\">原始得分 {raw:.1f}/{mx_sum}，按 50 分上限缩放 → {score:.1f}/50</p>")

    lost, full = [], []
    for r in rows:
        code = r.get("code", "")
        desc = r.get("desc", "")
        mx = r.get("max", 0)
        aw = r.get("awarded", 0)
        verdict = r.get("verdict_v3") or r.get("verdict", "")
        if aw < mx:
            lost.append((code, desc, aw, mx, verdict))
        else:
            full.append((code, desc, mx))

    if lost:
        lines.append("<p><b>扣分明细（含标准答卷对比）：</b></p>")
        lines.append("<ul>")
        for code, desc, aw, mx, v in lost:
            v_short = v[:280].replace('<', '&lt;').replace('>', '&gt;')
            lines.append(f"<li><b>{code} {desc}</b>：得分 {aw:.1f}/{mx} — {v_short}</li>")
        lines.append("</ul>")

    if full:
        full_codes = ", ".join(f"{c}({m})" for c, _, m in full)
        lines.append(f"<p><b>满分项</b>（{len(full)}项）：{full_codes}</p>")

    return "\n".join(lines)


def main():
    src = os.path.join(ROOT, "_grading_v2.json")
    data = json.load(open(src, encoding="utf-8"))
    data = copy.deepcopy(data)

    total_adj = 0
    for rec in data:
        baseline_recalibrate(rec)
        total_adj += len(rec.get("v3_adjustments", []))
        # 重算 score
        for q in (1, 2):
            rows = rec[f"Q{q}"]
            if rows and rows[0].get("code") == "MISS":
                continue
            raw = sum(r["awarded"] for r in rows)
            mx_sum = sum(r["max"] for r in rows)
            scaled = round(raw / mx_sum * 50, 1) if mx_sum else 0
            rec[f"q{q}_score"] = min(scaled, 50.0)
            rec[f"q{q}_raw"] = raw
            rec[f"q{q}_max"] = mx_sum
        rec["total"] = rec["q1_score"] + rec["q2_score"]

    json.dump(data, open(os.path.join(ROOT, "_grading_v3.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    plan = []
    for rec in data:
        item = {"attempt": int(rec["attempt"]), "name": rec["name"]}
        for q in (1, 2):
            comment = gen_comment_html(rec, q)
            mark = round(rec.get(f"q{q}_score", 0), 1)
            item[f"Q{q}"] = {"mark": mark, "comment": comment}
        item["total"] = rec.get("total", 0)
        plan.append(item)

    json.dump(plan, open(os.path.join(ROOT, "_submit_plan.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    preview = os.path.join(ROOT, "_submit_preview.md")
    with open(preview, "w", encoding="utf-8") as f:
        f.write("# Moodle 录入预览 (v3 含标准答卷对比)\n\n")
        f.write(f"v3 基线回调：{total_adj} 项由 90% 折扣回满分（截图数≥标准）。\n\n")
        f.write("## 排行榜 v2 → v3\n\n| attempt | 考生 | Q1 | Q2 | total |\n|---|---|---|---|---|\n")
        for item in sorted(plan, key=lambda x: -x["total"]):
            f.write(f"| {item['attempt']} | {item['name']} | {item['Q1']['mark']} | {item['Q2']['mark']} | **{item['total']:.1f}** |\n")
        f.write("\n---\n\n")
        for item in plan:
            f.write(f"## {item['attempt']} - {item['name']} (总分 {item['total']:.1f})\n\n")
            for q in (1, 2):
                f.write(f"### Q{q} -> 录入分数 {item[f'Q{q}']['mark']}\n\n")
                f.write("**评语 HTML:**\n\n```html\n")
                f.write(item[f"Q{q}"]["comment"])
                f.write("\n```\n\n**渲染预览:**\n\n")
                f.write(item[f"Q{q}"]["comment"])
                f.write("\n\n---\n\n")

    print(f"OK: _grading_v3.json + _submit_plan.json + _submit_preview.md, baseline_adjustments={total_adj}")


if __name__ == "__main__":
    main()
