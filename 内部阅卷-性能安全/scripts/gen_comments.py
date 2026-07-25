"""根据 _grading_v2.json 生成每位考生 Q1/Q2 的 Moodle 评语 HTML"""
import os, sys, json, html

# 用法: python gen_comments.py <workdir>
ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\阅卷"


def gen_comment_html(rec, qno):
    """生成单题评语 HTML"""
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

    # 扣分明细
    lost = []
    full = []
    for r in rows:
        code = r.get("code", "")
        desc = r.get("desc", "")
        mx = r.get("max", 0)
        aw = r.get("awarded", 0)
        verdict = r.get("verdict", "")
        if aw < mx:
            lost.append((code, desc, aw, mx, verdict))
        else:
            full.append((code, desc, mx))

    if lost:
        lines.append("<p><b>扣分明细：</b></p>")
        lines.append("<ul>")
        for code, desc, aw, mx, v in lost:
            v_short = v[:120].replace('<', '&lt;').replace('>', '&gt;')
            lines.append(f"<li><b>{code} {desc}</b>：得分 {aw:.1f}/{mx} — {v_short}</li>")
        lines.append("</ul>")

    if full:
        full_codes = ", ".join(f"{c}({m})" for c, _, m in full)
        lines.append(f"<p><b>满分项</b>（{len(full)}项）：{full_codes}</p>")

    return "\n".join(lines)


def main():
    src = os.path.join(ROOT, "_grading_v2.json")  # 后续换成 v3
    with open(src, "r", encoding="utf-8") as f:
        data = json.load(f)

    plan = []
    for rec in data:
        attempt = int(rec["attempt"])
        name = rec["name"]
        item = {"attempt": attempt, "name": name}
        for q in (1, 2):
            comment = gen_comment_html(rec, q)
            mark = round(rec.get(f"q{q}_score", 0), 1)
            item[f"Q{q}"] = {"mark": mark, "comment": comment}
        item["total"] = rec.get("total", 0)
        plan.append(item)

    with open(os.path.join(ROOT, "_submit_plan.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    # 输出预览
    preview = os.path.join(ROOT, "_submit_preview.md")
    with open(preview, "w", encoding="utf-8") as f:
        f.write("# Moodle 录入预览\n\n")
        for item in plan:
            f.write(f"## {item['attempt']} - {item['name']} (总分 {item['total']:.1f})\n\n")
            for q in (1, 2):
                f.write(f"### Q{q} → 录入分数 {item[f'Q{q}']['mark']}\n\n")
                f.write("**评语 HTML:**\n\n```html\n")
                f.write(item[f"Q{q}"]["comment"])
                f.write("\n```\n\n")
                f.write("**评语渲染预览:**\n\n")
                f.write(item[f"Q{q}"]["comment"])
                f.write("\n\n---\n\n")

    print(f"[✓] 生成 _submit_plan.json + _submit_preview.md（{len(plan)}人）")


if __name__ == "__main__":
    main()
