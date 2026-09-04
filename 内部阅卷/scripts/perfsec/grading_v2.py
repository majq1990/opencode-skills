"""
v2 评分（综合视觉细查 + 陈智源基准校准）
"""
import os, sys, json, re, csv

# 用法: python grading_v2.py <workdir>
ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\阅卷"
EXT = os.path.join(ROOT, "_extracted")
VISUAL_DIR = os.path.join(ROOT, "_visual")

# 加载所有视觉细查结果（深合并：同一考生多文件的 code 字段合并而非覆盖）
visual_data = {}
for f in sorted(os.listdir(VISUAL_DIR)):
    if f.endswith(".json") and not f.startswith("reference"):
        with open(os.path.join(VISUAL_DIR, f), "r", encoding="utf-8") as fp:
            data_one = json.load(fp)
            for k, v in data_one.items():
                if not isinstance(v, dict):
                    continue
                if k not in visual_data:
                    visual_data[k] = {}
                visual_data[k].update(v)

# 重复提交：6753 康航源_v2 与 6752 康航源_v1 内容完全一致，复用 6752 视觉数据
if "6752_康航源" in visual_data:
    visual_data["6753_康航源v2"] = dict(visual_data["6752_康航源"])

# 陈智源基准（attempt 6748, 老师评 80 = Q1 50/50 + Q2 30/50）
# 视觉细查发现:
# P1-1 false → 老师给满；P2-3 partial → 老师给满；S1-1 partial → 老师给分
# 校准结论:
# - P1-1 URL: false 也给 60%；partial 给 85%；true 给 100%
# - P2-3 dump: partial 给 80%（报告正常即可）；true 给 100%
# - S1-1 雷池 URL: partial 给 80%（仪表盘带URL）；true 给 100%
# - P1-4/P2-5/S3-1 严格执行

VISUAL_ADJUST = {
    "P1-1": {"true": 1.0, "partial": 0.75, "false": 0.5},  # 浏览器=满分；curl/终端=半分；未作答=0
    "P1-4": {"true": 1.0, "partial": 0.5, "false": 0.1},  # 统计分布+10s 缺一段折半
    "P2-3": {"true": 1.0, "partial": 0.2, "false": 0.0},  # ⚠ 严：统计表必须有真实数据，仅基本信息=0.6/3
    "P2-5": {"true": 1.0, "partial": 0.5, "false": 0.0},  # 严：日志切割必须有修复过程
    "S1-1": {"true": 1.0, "partial": 0.8, "false": 0.3},
    "S3-1": {"true": 1.0, "partial": 0.7, "false": 0.2},
    # P2-1/2/4/6/7（只要求"查看报告"无预警修复）：true=100% partial=70% false=0%
    "P2-1": {"true": 1.0, "partial": 0.7, "false": 0.0},
    "P2-2": {"true": 1.0, "partial": 0.7, "false": 0.0},
    "P2-4": {"true": 1.0, "partial": 0.7, "false": 0.0},
    "P2-6": {"true": 1.0, "partial": 0.7, "false": 0.0},
    "P2-7": {"true": 1.0, "partial": 0.7, "false": 0.0},
    # lua_waf 三要素：用 factors_met/3 比例
    "S2-1": {},  # 走特殊逻辑
    "S2-2": {},
    "S2-3": {},
}


def load_v1():
    with open(os.path.join(ROOT, "_grading_v1.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def apply_visual(rec):
    """根据视觉细查结果调整 rec 中相应采分点的得分"""
    name = rec.get("name", "")
    attempt = rec.get("attempt", "")
    # 匹配 visual_data key: e.g. "6731_郭跃增" — 用 attempt 起头匹配
    vkey = None
    for k in visual_data:
        if k.startswith(str(attempt)+"_"):
            vkey = k
            break
    if not vkey:
        return rec

    vdata = visual_data[vkey]
    rec["visual_key"] = vkey
    rec["visual_adjustments"] = []

    # 视觉项对应 Q1 还是 Q2
    Q1_codes = {"P1-1", "P1-4", "P2-1", "P2-2", "P2-3", "P2-4", "P2-5", "P2-6", "P2-7"}
    Q2_codes = {"S1-1", "S2-1", "S2-2", "S2-3", "S3-1"}

    def adjust(code, qno):
        # 兼容 sub-agent 2 输出格式 "P2-1_zip" / "P2-2_dameng" 等
        v = vdata.get(code)
        if not v:
            for k in vdata:
                if k.startswith(code+"_"):
                    v = vdata[k]
                    break
        if not v:
            return
        # S3-1 特殊：按 count 判
        if code == "S3-1":
            try:
                cnt_raw = v.get("count", 0)
                cnt = int(re.sub(r"[^0-9]", "", str(cnt_raw)) or "0")
            except Exception:
                cnt = 0
            if cnt >= 5:
                ratio = 1.0; found = f"≥5({cnt})"
            elif cnt >= 3:
                ratio = 0.5; found = f"{cnt}个不足5"
            else:
                ratio = 0.0; found = "无清单"
        # lua_waf 三要素：按 factors_met / 3
        elif code in ("S2-1", "S2-2", "S2-3"):
            try:
                fm = int(v.get("factors_met", 0))
            except Exception:
                fm = 0
            ratio = fm / 3.0
            found = f"三要素{fm}/3"
            # S2-3 ab 攻击加分
            if code == "S2-3" and v.get("has_ab_attack"):
                ratio = min(1.0, ratio + 0.1)
                found += "+ab攻击"
        else:
            found = str(v.get("found", "false")).lower()
            # 处理 missing
            if found == "missing":
                ratio = 0.0
                found = "未作答"
            else:
                ratio = VISUAL_ADJUST.get(code, {}).get(found, 0.5)
        # 找到对应 row
        for r in rec[f"Q{qno}"]:
            if r.get("code") == code:
                old = r["awarded"]
                # 用视觉调整后的比例覆盖：基于 max 重新算
                # 如果原来是 0（关键词未命中），不改
                if old == 0 and "未作答" in r.get("verdict", ""):
                    continue
                new = round(r["max"] * ratio, 1)
                if new != old:
                    rec["visual_adjustments"].append({
                        "code": code,
                        "old": old,
                        "new": new,
                        "found": found,
                        "evidence": v.get("evidence", "")[:80],
                    })
                    r["awarded"] = new
                    r["verdict"] = f"[视觉] {found} - {v.get('evidence','')[:60]}"
                break

    for c in Q1_codes:
        adjust(c, 1)
    for c in Q2_codes:
        adjust(c, 2)

    # 重新算 q_score: 按 raw / max_sum × 50 缩放
    for q in (1, 2):
        rows = rec[f"Q{q}"]
        # 跳过 MISS 占位
        if rows and rows[0].get("code") == "MISS":
            rec[f"q{q}_score"] = 0
            rec[f"q{q}_raw"] = 0
            rec[f"q{q}_max"] = 50
            continue
        raw = sum(r["awarded"] for r in rows)
        max_sum = sum(r["max"] for r in rows)
        if max_sum > 0:
            scaled = round(raw / max_sum * 50, 1)
        else:
            scaled = 0
        # 上限保护：不超过 50
        rec[f"q{q}_score"] = min(scaled, 50.0)
        rec[f"q{q}_raw"] = raw
        rec[f"q{q}_max"] = max_sum
    rec["total"] = rec["q1_score"] + rec["q2_score"]
    return rec


def main():
    report = load_v1()
    for rec in report:
        apply_visual(rec)

    with open(os.path.join(ROOT, "_grading_v2.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 输出 Markdown
    md = ["# 性能安全认证实操-26年二季度 阅卷报告 v2（视觉细查校准版）", "",
          "**校准来源**：以陈智源 6748（老师已评 80 分）为基准校验算法，对 P1-1 / P2-3 / S1-1 三个采分点放宽。",
          "**视觉调整列**仅显示视觉细查带来的得分变化。", "",
          "## 总分排行 v2", "",
          "| 排名 | Attempt | 姓名 | Q1 | Q2 | 总分 v2 | v1 → v2 |", "|---|---|---|---|---|---|---|"]
    v1_map = {r["attempt"]: r for r in load_v1()}
    for i, r in enumerate(sorted(report, key=lambda x: -x["total"]), 1):
        v1 = v1_map.get(r["attempt"], {})
        delta = r["total"] - v1.get("total", 0)
        delta_str = f"+{delta:.1f}" if delta >= 0 else f"{delta:.1f}"
        md.append(f"| {i} | {r['attempt']} | {r['name']} | {r['q1_score']:.1f} | {r['q2_score']:.1f} | **{r['total']:.1f}** | {v1.get('total',0):.1f} → ({delta_str}) |")

    md += ["", "## 每人详细扣分", ""]
    for r in sorted(report, key=lambda x: -x["total"]):
        md.append(f"### {r['attempt']} - {r['name']}  总分 {r['total']:.1f}/100")
        md.append("")
        adj = r.get("visual_adjustments", [])
        if adj:
            md.append("**视觉细查调整**：")
            for a in adj:
                md.append(f"- {a['code']} {a['old']:.1f} → {a['new']:.1f}（视觉判定:{a['found']}）{a['evidence']}")
            md.append("")
        for q in (1, 2):
            qrows = r[f"Q{q}"]
            qscore = r[f"q{q}_score"]
            qname = "性能监控" if q == 1 else "安全运维"
            md.append(f"**Q{q} {qname} — {qscore:.1f}/50**")
            md.append("")
            md.append("| 采分点 | 分值 | 得分 | 评判 |")
            md.append("|---|---|---|---|")
            for p in qrows:
                desc = p.get("desc", "?")
                code = p.get("code", "")
                mx = p.get("max", 0)
                aw = p.get("awarded", 0)
                v = p.get("verdict", "")
                md.append(f"| {code} {desc} | {mx} | {aw} | {v} |")
            md.append("")
        md.append("---")
        md.append("")

    with open(os.path.join(ROOT, "_grading_v2.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"[✓] v2 评分生成: _grading_v2.md, _grading_v2.json")
    # 打印对照
    print("\n## v1 → v2 对照")
    print("attempt  name              v1 → v2  delta")
    for r in sorted(report, key=lambda x: -x["total"]):
        v1 = v1_map.get(r["attempt"], {})
        delta = r["total"] - v1.get("total", 0)
        print(f"{r['attempt']}  {r['name'][:18]:<20} {v1.get('total',0):>5.1f} → {r['total']:>5.1f}  ({delta:+.1f})")


if __name__ == "__main__":
    main()
