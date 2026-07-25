"""
麒舰部署实操阅卷（quiz 259，单题满分 100）

输入:
  references/reference_baseline_qijian.json  采分点基线（同目录 references/ 下）
  <workdir>/_attempts.json                   考生列表（download_attachments.py 产出）
  <workdir>/_visual/visual_*.json            视觉细查结果（每考生每采分点 found/has_url/img_count/evidence）

输出:
  <workdir>/_grading_qijian.json             明细
  <workdir>/_grading_qijian.md               排行榜 + 每人扣分明细
  <workdir>/_submit_plan_qijian.json         待提交计划（attempt/name/slot/mark/comment(HTML)）

用法: python grading_qijian.py <workdir> [--slot 1]
"""
import os, sys, json

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\阅卷_259"
SLOT = 1
if "--slot" in sys.argv:
    SLOT = int(sys.argv[sys.argv.index("--slot") + 1])

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "..", "references", "reference_baseline_qijian.json")
VISUAL_DIR = os.path.join(ROOT, "_visual")

# 新加考点 / 易错点：预览时标注需人工复核
REVIEW_FLAG = {"S2-6", "S2-10", "S3-4", "S9-5", "S10-5"}

RATIO = {"yes": 1.0, "partial": 0.5, "no": 0.0, "missing": 0.0}


def load_baseline():
    with open(BASELINE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_visual():
    """深合并 _visual/ 下所有 json：{attempt_name: {code: {...}}}"""
    merged = {}
    if not os.path.isdir(VISUAL_DIR):
        return merged
    for fn in sorted(os.listdir(VISUAL_DIR)):
        if not fn.endswith(".json") or fn.startswith("reference"):
            continue
        with open(os.path.join(VISUAL_DIR, fn), "r", encoding="utf-8") as fp:
            data = json.load(fp)
        for k, v in data.items():
            if not isinstance(v, dict):
                continue
            merged.setdefault(k, {}).update(v)
    return merged


def find_vkey(visual, attempt):
    for k in visual:
        if k.startswith(str(attempt) + "_"):
            return k
    return None


def score_item(item, vrec):
    """返回 (awarded, verdict, evidence)"""
    code = item["id"]
    score = item["score"]
    need_url = item.get("need_url", False)
    v = vrec.get(code) if vrec else None
    if not v:
        return 0.0, "未细查/未作答", ""
    found = str(v.get("found", "no")).lower()
    ratio = RATIO.get(found, 0.0)
    evidence = str(v.get("evidence", ""))[:120]
    note = found
    # URL 红线：need_url 且未截 URL，内容做了的情况下扣半分
    if need_url and ratio > 0 and not v.get("has_url", False):
        ratio *= 0.5
        note += "·缺URL(扣半)"
    awarded = round(score * ratio, 2)
    if code in REVIEW_FLAG:
        note += "·⚠人工复核"
    return awarded, note, evidence


def grade_one(attempt, name, baseline, visual):
    vkey = find_vkey(visual, attempt)
    vrec = visual.get(vkey, {}) if vkey else {}
    sections_out = []
    total = 0.0
    for sec in baseline["sections"]:
        items_out = []
        sec_awarded = 0.0
        for item in sec["items"]:
            aw, verdict, ev = score_item(item, vrec)
            sec_awarded += aw
            items_out.append({
                "code": item["id"], "name": item["name"],
                "max": item["score"], "awarded": aw,
                "verdict": verdict, "evidence": ev,
                "need_url": item.get("need_url", False),
            })
        sections_out.append({
            "id": sec["id"], "name": sec["name"],
            "max": sec["score"], "awarded": round(sec_awarded, 2),
            "items": items_out,
        })
        total += sec_awarded
    return {
        "attempt": attempt, "name": name, "visual_key": vkey,
        "total": round(min(total, 100.0), 2),
        "sections": sections_out,
        "graded": bool(vkey),
    }


def build_comment_html(rec):
    """生成单题 HTML 评语：总分 + 各大项 + 失分/缺URL/人工复核明细"""
    parts = [f"<p><b>麒舰部署实操总分：{rec['total']:.1f}/100</b></p>"]
    for sec in rec["sections"]:
        parts.append(f"<p><b>{sec['id']} {sec['name']} — {sec['awarded']:.1f}/{sec['max']}</b></p><ul>")
        for it in sec["items"]:
            if it["awarded"] >= it["max"]:
                parts.append(f"<li>{it['code']} {it['name']}：满分 {it['max']} ✓</li>")
            else:
                tag = it["verdict"]
                parts.append(
                    f"<li>{it['code']} {it['name']}：{it['awarded']:.1f}/{it['max']}"
                    f"（{tag}）{('— ' + it['evidence']) if it['evidence'] else ''}</li>"
                )
        parts.append("</ul>")
    return "".join(parts)


def main():
    baseline = load_baseline()
    visual = load_visual()
    with open(os.path.join(ROOT, "_attempts.json"), "r", encoding="utf-8") as f:
        attempts = json.load(f)

    report = []
    for a in attempts:
        rec = grade_one(a["attempt"], a.get("name", ""), baseline, visual)
        report.append(rec)

    report.sort(key=lambda r: -r["total"])

    with open(os.path.join(ROOT, "_grading_qijian.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # submit plan
    plan = []
    for rec in report:
        if not rec["graded"]:
            continue
        plan.append({
            "attempt": rec["attempt"], "name": rec["name"], "slot": SLOT,
            "mark": rec["total"], "comment": build_comment_html(rec),
        })
    with open(os.path.join(ROOT, "_submit_plan_qijian.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    # markdown report
    md = ["# 麒舰部署实操阅卷报告（quiz 259）", "", "## 总分排行", "",
          "| 排名 | Attempt | 姓名 | 总分/100 | 状态 |", "|---|---|---|---|---|"]
    for i, r in enumerate(report, 1):
        st = "已评" if r["graded"] else "⚠未细查"
        md.append(f"| {i} | {r['attempt']} | {r['name']} | **{r['total']:.1f}** | {st} |")
    md += ["", "## 每人大项得分", ""]
    for r in report:
        md.append(f"### {r['attempt']} {r['name']} — {r['total']:.1f}/100")
        md.append("")
        md.append("| 大项 | 得分 | 失分采分点 |")
        md.append("|---|---|---|")
        for sec in r["sections"]:
            lost = [f"{it['code']}({it['awarded']:.1f}/{it['max']})"
                    for it in sec["items"] if it["awarded"] < it["max"]]
            md.append(f"| {sec['id']} {sec['name']} | {sec['awarded']:.1f}/{sec['max']} | "
                      f"{('；'.join(lost)) if lost else '—'} |")
        md.append("")
    with open(os.path.join(ROOT, "_grading_qijian.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    graded = sum(1 for r in report if r["graded"])
    print(f"[OK] 评分完成：{graded}/{len(report)} 已细查")
    print(f"     _grading_qijian.json / .md / _submit_plan_qijian.json -> {ROOT}")
    for r in report[:10]:
        print(f"  {r['attempt']} {r['name'][:16]:<18} {r['total']:>6.1f}/100  {'已评' if r['graded'] else '未细查'}")


if __name__ == "__main__":
    main()
