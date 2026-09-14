# -*- coding: utf-8 -*-
"""quiz266 初评 v1：T1(30,按34raw缩放)+T2(30)+T3(40)。证据覆盖度启发式，只作候选。"""
import os, sys, json, re, csv

if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

WORKDIR = sys.argv[1] if len(sys.argv) > 1 else r"D:\opencode\file\2026-09-14\阅卷_266"
UNPACK = os.path.join(WORKDIR, "_unpacked")
attempts_meta = {a["attempt"]: a for a in
                 json.load(open(os.path.join(WORKDIR, "_attempts.json"), encoding="utf-8"))}

TEXT_EXT = {".md", ".txt", ".html", ".htm", ".py", ".sql", ".yaml", ".yml",
            ".json", ".xml", ".js", ".bat", ".csv"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
MAXCH = 200000

def read_text(path):
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".docx":
            from docx import Document
            return "\n".join(p.text for p in Document(path).paragraphs)[:MAXCH]
        if ext not in TEXT_EXT:
            return ""
        with open(path, encoding="utf-8", errors="ignore") as f:
            t = f.read(MAXCH)
        if ext in (".html", ".htm"):
            t = re.sub(r"<script.*?</script>", " ", t, flags=re.S | re.I)
            t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
            t = re.sub(r"<[^>]+>", " ", t)
        return t
    except Exception:
        return ""

def collect(attempt_dir, slot):
    """返回 (text, files, shots)。slot数字；loose按Q<slot>_前缀归属。"""
    texts, files, shots = [], [], 0
    ad = os.path.join(WORKDIR, attempt_dir)
    if os.path.isdir(ad):
        for fn in os.listdir(ad):
            if not re.match(rf"^Q{slot}_", fn):
                continue
            p = os.path.join(ad, fn)
            if os.path.isfile(p):
                files.append(fn)
                if os.path.splitext(fn)[1].lower() in IMG_EXT:
                    shots += 1
                t = read_text(p)
                if t: texts.append(t)
    ud = os.path.join(UNPACK, attempt_dir)
    if os.path.isdir(ud):
        for root, _, fns in os.walk(ud):
            if f"Q{slot}__" not in root and os.path.basename(root) != attempt_dir:
                # 只收本slot解包目录
                if not any(f"Q{slot}__" in part for part in [root]):
                    pass
            for fn in fns:
                p = os.path.join(root, fn)
                rel = os.path.relpath(p, ud)
                if not rel.startswith(f"Q{slot}__"):
                    continue
                files.append(rel)
                if os.path.splitext(fn)[1].lower() in IMG_EXT:
                    shots += 1
                t = read_text(p)
                if t: texts.append(t)
    return "\n".join(texts)[:MAXCH], files, shots

def cov(text, groups):
    t = text.lower()
    hit = sum(1 for g in groups if re.search(g, t, re.I))
    return hit / max(len(groups), 1), hit

def tier(r):
    if r >= 0.8: return 1.0
    if r >= 0.5: return 0.6
    if r >= 0.25: return 0.3
    return 0.0

T1_GROUPS = {
    "T1-1": [r"态势|总览", r"受理", r"分派", r"处置", r"反馈", r"督办", r"流程|状态", r"边界|字段"],
    "T1-2": [r"pc|导航|工具栏", r"卡片|仪表盘", r"表格", r"图表|echarts", r"zartui|vue|原型"],
    "T1-3": [r"375|移动|底部|tabbar", r"触控|44", r"安全区", r"首页|事件|任务|我的"],
    "T1-4": [r"图标|icon|svg", r"受理", r"分派", r"督办|超期", r"拍照|定位", r"办结|预警"],
    "T1-5": [r"评审|复核|确认", r"清单", r"需求|设计", r"复用|模板"],
}
T1_MAX = {"T1-1": 8, "T1-2": 7, "T1-3": 7, "T1-4": 7, "T1-5": 5}
T2_GROUPS = {
    "T2-1": [r"鉴权|认证", r"token|签名|appkey|secret", r"登录|权限|只读|写入|边界"],
    "T2-2": [r"接口|清单", r"字段|口径|映射", r"字典|枚举|错误码"],
    "T2-3": [r"模型|ddl|表结构", r"调度|增量|幂等|定时", r"合并|视图|台账|代理"],
    "T2-4": [r"埋坑|坑点", r"定位|排查", r"多轮|对话|迭代", r"修正|修复|复现"],
    "T2-5": [r"验证|复现", r"截图|留痕|人工确认|日志"],
}
T2_MAX = {"T2-1": 8, "T2-2": 8, "T2-3": 7, "T2-4": 5, "T2-5": 2}
T3_GROUPS = {
    "T3-1": [r"定位", r"背景", r"目标"],
    "T3-2": [r"来源|链接|位置", r"版本|日期", r"适用|范围"],
    "T3-3": [r"skill", r"权限|只读|写入", r"版本", r"输入|输出"],
    "T3-4": [r"任务卡", r"提示词|首轮", r"迭代|补充|多轮"],
    "T3-5": [r"复核|核验", r"修改|变更", r"责任人|复核人", r"时间"],
    "T3-6": [r"风险|授权", r"脱敏", r"禁止", r"确认点|门禁|停止"],
    "T3-7": [r"复用|模板", r"交付|产物", r"清单|台账|流程"],
}
T3_MAX = {"T3-1": 5, "T3-2": 5, "T3-3": 5, "T3-4": 6, "T3-5": 6, "T3-6": 6, "T3-7": 7}

def detect_dir(files, text):
    blob = "\n".join(files) + "\n" + text[:5000]
    if re.search(r"方向D|redmine|aicert|d-lab", blob, re.I): return "D-RedmineMCP"
    if re.search(r"方向E|全流程|监管|通途|tongtu", blob, re.I): return "E-全流程监管"
    if re.search(r"方向B|生命线|lifeline", blob, re.I): return "B-生命线"
    if re.search(r"方向C|麒舰|eurban|spel|流程对接", blob, re.I): return "C-麒舰"
    if re.search(r"方向A|星桥|dex|执法案件|http.*调度|数据模型", blob, re.I): return "A-星桥"
    return "未识别"

results = []
dirs = sorted([d for d in os.listdir(WORKDIR)
               if os.path.isdir(os.path.join(WORKDIR, d)) and re.match(r"^\d+_", d)])
for dn in dirs:
    att = int(dn.split("_")[0])
    meta = attempts_meta.get(att, {})
    name = meta.get("name", dn)
    row = {"attempt": att, "name": name, "dir": dn, "flags": [], "items": {}}
    # Q1
    t1, f1, s1 = collect(dn, 1)
    t1_raw, t1_det = 0, {}
    for code, mx in T1_MAX.items():
        r, h = cov(t1, T1_GROUPS[code])
        boost = 0
        blob = "\n".join(f1).lower()
        if code == "T1-2" and re.search(r"\.html", blob): boost = max(boost, 0.6)
        if code == "T1-3" and re.search(r"mobile|移动|375", blob): boost = max(boost, 0.6)
        if code == "T1-4" and (sum(1 for f in f1 if f.lower().endswith(".svg")) >= 8 or "icon" in blob or "图标" in blob): boost = max(boost, 0.6)
        if code == "T1-5" and re.search(r"评审|清单|需求", blob): boost = max(boost, 0.6)
        r = max(r, boost)
        aw = round(mx * tier(r), 2)
        t1_det[code] = {"ratio": round(r, 2), "hits": h, "awarded": aw}
        t1_raw += aw
    t1_score = round(t1_raw / 34 * 30, 2)
    if s1 == 0 and t1_score > 0:
        t1_score = round(min(t1_score, 30 * 0.3), 2); row["flags"].append("Q1无截图 capped30%")
    if s1 < 3: row["flags"].append(f"Q1截图{s1}张 needs_visual")
    row["items"]["T1"] = {"raw34": round(t1_raw, 2), "score30": t1_score, "shots": s1, "detail": t1_det}
    # Q2
    t2, f2, s2 = collect(dn, 2)
    direction = detect_dir(f2, t2)
    row["direction"] = direction
    if direction == "未识别" and (t2.strip() or f2): row["flags"].append("Q2方向未识别")
    t2_score, t2_det = 0, {}
    for code, mx in T2_MAX.items():
        r, h = cov(t2, T2_GROUPS[code])
        aw = round(mx * tier(r), 2)
        t2_det[code] = {"ratio": round(r, 2), "hits": h, "awarded": aw}
        t2_score += aw
    t2_score = round(t2_score, 2)
    if not f2 and not t2.strip():
        row["flags"].append("Q2缺交")
    elif s2 == 0 and t2_score > 0:
        t2_score = round(min(t2_score, 30 * 0.3), 2); row["flags"].append("Q2无截图 capped30%")
    if f2 and s2 < 3: row["flags"].append(f"Q2截图{s2}张 needs_visual")
    row["items"]["T2"] = {"score30": t2_score, "shots": s2, "detail": t2_det}
    # Q3
    t3, f3, s3 = collect(dn, 3)
    blob3 = "\n".join(f3).lower()
    has_skill = bool(re.search(r"skill\.md", blob3)) or "skill" in t3.lower()[:0] or re.search(r"skill\.md", blob3)
    has_skill = bool(re.search(r"skill", blob3))
    has_ev = bool(re.search(r"evidence|证据|截图", blob3 + t3[:20000]))
    t3_score, t3_det = 0, {}
    for code, mx in T3_MAX.items():
        r, h = cov(t3, T3_GROUPS[code])
        if code == "T3-7" and has_skill: r = max(r, 0.6)
        if code == "T3-5" and has_ev: r = max(r, 0.5)
        aw = round(mx * tier(r), 2)
        t3_det[code] = {"ratio": round(r, 2), "hits": h, "awarded": aw}
        t3_score += aw
    t3_score = round(t3_score, 2)
    if not f3 and not t3.strip():
        row["flags"].append("Q3缺交")
    elif s3 == 0 and t3_score > 0:
        t3_score = round(min(t3_score, 40 * 0.3), 2); row["flags"].append("Q3无截图 capped30%")
    if f3 and s3 < 3: row["flags"].append(f"Q3截图{s3}张 needs_visual")
    row["items"]["T3"] = {"score40": t3_score, "shots": s3, "has_skill": has_skill, "detail": t3_det}
    row.update({"T1": t1_score, "T2": t2_score, "T3": t3_score,
                "total": round(t1_score + t2_score + t3_score, 2)})
    results.append(row)

# 空交卷 attempt 也列出
have = {r["attempt"] for r in results}
for att, meta in sorted(attempts_meta.items()):
    if att not in have:
        results.append({"attempt": att, "name": meta.get("name", ""), "dir": "",
                        "direction": "-", "flags": ["未交卷"], "items": {},
                        "T1": 0, "T2": 0, "T3": 0, "total": 0})

results.sort(key=lambda r: -r["total"])
json.dump(results, open(os.path.join(WORKDIR, "_grading_266_v2.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
with open(os.path.join(WORKDIR, "_grading_266_v2.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["attempt", "name", "direction", "T1/30", "T2/30", "T3/40", "total/100", "flags"])
    for r in results:
        w.writerow([r["attempt"], r["name"], r.get("direction", "-"), r["T1"], r["T2"],
                    r["T3"], r["total"], ";".join(r["flags"])])
lines = ["# Quiz266 初评 v2（严格口径，候选，非最终）", "", "| 排名 | attempt | 姓名 | 方向 | T1/30 | T2/30 | T3/40 | 总分 | 标记 |",
         "|---|---|---|---|---|---|---|---|---|"]
for i, r in enumerate(results, 1):
    lines.append(f"| {i} | {r['attempt']} | {r['name']} | {r.get('direction','-')} | "
                 f"{r['T1']} | {r['T2']} | {r['T3']} | {r['total']} | {';'.join(r['flags'])} |")
lines += ["", "> 口径：T1按34raw缩放到30；无截图题 capped30%。自动初评只作候选，最终以人工复核为准，不回写。",
          "> 15个空交卷已计0分。"]
open(os.path.join(WORKDIR, "_grading_266_v2.md"), "w", encoding="utf-8").write("\n".join(lines))
print(f"[✓] 初评完成：{len(results)} 人，TOP3: " +
      ", ".join(f"{r['name']}{r['total']}" for r in results[:3]), flush=True)
