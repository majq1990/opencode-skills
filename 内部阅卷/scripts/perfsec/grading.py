"""
基于文字结构的初版评分
- 读取每份 text_only.txt
- 按采分点关键词匹配，统计段落附近图片数
- 输出 Markdown + Excel
"""
import os, sys, json, re, csv

# 用法: python grading.py <workdir>
ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\阅卷"
EXT = os.path.join(ROOT, "_extracted")

# 采分点定义：(代码, 章节, 描述, 分值, 关键词正则, 特殊要求, 是否论述题)
# 论述题：有文字论述（≥60字）即给分，不强求截图
Q1_POINTS = [
    ("P1-1", "性能应急", "内网访问登录", 3, r"内网访问|用户中心.*登录|admin", "需登录页 URL", False),
    ("P1-2", "性能应急", "mysql 状态导出", 3, r"mysql.{0,10}状态|mysql.{0,4}导出", "", False),
    ("P1-3", "性能应急", "达梦状态导出", 3, r"达梦.{0,10}状态|dameng|DM_", "", False),
    ("P1-4", "性能应急", "nginx 状态导出(含统计分布+10s耗时分布)", 5, r"nginx.{0,10}状态", "需统计分布+10s耗时", False),
    ("P1-5", "性能应急", "应用日志错误提取", 3, r"日志.{0,6}错误|应用.{0,6}日志|error.{0,6}log", "", False),
    ("P1-6", "性能应急", "jvm 信息导出", 3, r"jvm|jstack|jmap|heap", "", False),
    ("P1-7", "性能应急", "redis 状态导出", 3, r"redis.{0,10}状态|redis.{0,8}信息", "", False),
    ("P1-8", "性能应急", "磁盘 I/O 状态导出", 3, r"磁盘.{0,4}I.{0,2}O|iostat|disk.{0,6}io", "", False),
    ("P1-9", "性能应急", "系统恢复思路", 4, r"恢复.{0,4}思路|系统.{0,4}恢复", "", True),

    ("P2-1", "auto_check", "生成最新 zip 巡检报告", 2, r"zip|巡检.{0,4}报告|生成.{0,4}巡检|一键巡检", "", False),
    ("P2-2", "auto_check", "report_dameng.html", 2, r"dameng\.html|达梦.{0,6}报告", "", False),
    ("P2-3", "auto_check", "report_microservice.html(解决dump预警)", 3, r"microservice\.html|微服务.{0,6}报告|dump", "需含dump路径修复", False),
    ("P2-4", "auto_check", "report_mysql.html", 2, r"mysql\.html|mysql.{0,4}报告", "", False),
    ("P2-5", "auto_check", "report_nginx.html(解决日志切割预警)", 3, r"nginx\.html|日志.{0,4}切割", "需含日志切割处理", False),
    ("P2-6", "auto_check", "report_os.html", 2, r"os\.html|系统.{0,4}报告", "", False),
    ("P2-7", "auto_check", "report_redis.html", 2, r"redis\.html|redis.{0,4}报告", "", False),

    ("P3-1", "基准测试", "测试前置操作", 2, r"前置|准备|测试前", "", False),
    ("P3-2", "基准测试", "数据库基准测试", 3, r"数据库.{0,6}基准|sysbench", "", False),
    ("P3-3", "基准测试", "redis 基准测试", 2, r"redis.{0,6}基准|redis-benchmark", "", False),
    ("P3-4", "基准测试", "磁盘 IO 性能测试", 2, r"磁盘.{0,6}性能|disk.{0,4}performance|fio", "", False),
    ("P3-5", "基准测试", "IOPS 测试", 2, r"IOPS|iops", "", False),
    ("P3-6", "基准测试", "宽带测试", 2, r"宽带|带宽|iperf", "", False),
]

Q2_POINTS = [
    ("S1-1", "雷池部署", "离线部署+登录(带URL)", 6, r"雷池|safeline|离线.{0,4}部署", "登录页需带URL", False),
    ("S1-2", "雷池部署", "模拟攻击+找日志/真实IP", 6, r"模拟攻击|攻击.{0,4}日志|真实.{0,4}ip|攻击记录", "拦截效果图需带URL", False),
    ("S1-3", "雷池部署", "拦截租户管理接口", 5, r"租户.{0,4}管理|tenant|拦截.{0,4}接口", "", False),

    ("S2-1", "lua_waf", "应用中心放开拦截", 6, r"应用中心|lua_waf.*应用|放开|放行", "", False),
    ("S2-2", "lua_waf", "拦截系统操作日志接口", 6, r"操作.{0,4}日志|system.{0,4}log|拦截.{0,4}日志", "", False),
    ("S2-3", "lua_waf", "登录接口 CC 防护", 6, r"CC.{0,4}防护|cc.{0,4}防护|cc.{0,4}attack", "", False),

    ("S3-1", "弱密码", "弱密码扫描+清单(不少于5个)", 15, r"弱密码|weak.{0,4}password|安全.{0,4}工具箱", "清单不少于5个", False),
]

POINTS_BY_QUIZ = {1: Q1_POINTS, 2: Q2_POINTS}

def grade_one(text_only_path, qno):
    """返回 [{code, desc, max, awarded, hit_lines, nearby_imgs, notes}, ...]"""
    if not os.path.exists(text_only_path):
        return None
    with open(text_only_path, "r", encoding="utf-8") as f:
        raw = f.read()
    lines = raw.split("\n")
    # 行 -> 类型(text/image)
    is_img = [bool(re.match(r"^\[图:", ln)) for ln in lines]

    points = POINTS_BY_QUIZ[qno]
    rows = []
    for code, sect, desc, mx, kw, note, is_essay in points:
        pat = re.compile(kw, re.I)
        hits = [i for i, ln in enumerate(lines) if not is_img[i] and pat.search(ln)]
        if not hits:
            rows.append({"code": code, "sect": sect, "desc": desc, "max": mx, "awarded": 0, "hit_lines": [], "imgs": 0, "note": note, "verdict": "❌ 未作答(关键词未命中)"})
            continue
        # 统计每个 hit 后 N 行内的图片数 + 文字字数
        max_imgs = 0
        max_essay_chars = 0
        ctx_text = ""
        for h in hits:
            cnt_img = 0
            cnt_chars = 0
            for j in range(h+1, min(len(lines), h+12)):
                if is_img[j]:
                    cnt_img += 1
                elif lines[j].strip() and re.match(r"^[一二三四五六七八九十]+、|^\d+\.\s|^[A-Z]\d", lines[j]):
                    break
                elif not is_img[j]:
                    cnt_chars += len(lines[j])
            if cnt_img > max_imgs:
                max_imgs = cnt_img
                ctx_text = lines[h]
            if cnt_chars > max_essay_chars:
                max_essay_chars = cnt_chars

        # 论述题：文字论述 ≥60 字即可给满分
        if is_essay:
            if max_essay_chars >= 60:
                awarded = mx
                verdict = f"✓ 论述完整({max_essay_chars}字)"
            elif max_essay_chars >= 20:
                awarded = round(mx * 0.6, 1)
                verdict = f"⚠ 论述简略({max_essay_chars}字)"
            else:
                awarded = 0
                verdict = "❌ 无有效论述"
        else:
            # 截图题：0 图 = 0 / 1 图 = 70% / 2 图 = 90% / 3+ 图 = 满分
            if max_imgs == 0:
                awarded = 0
                verdict = "❌ 写了标题但无截图"
            elif max_imgs == 1:
                awarded = round(mx * 0.7, 1)
                verdict = "⚠ 仅1张截图(可能不全)"
            elif max_imgs == 2:
                awarded = round(mx * 0.9, 1)
                verdict = "✓ 2张截图"
            else:
                awarded = mx
                verdict = f"✓ {max_imgs}张截图"
        if note:
            verdict += f" ⚠特殊要求:{note}"
            awarded = round(awarded * 0.9, 1)
        rows.append({"code": code, "sect": sect, "desc": desc, "max": mx, "awarded": awarded, "hit_lines": hits[:3], "imgs": max_imgs, "note": note, "verdict": verdict, "ctx": ctx_text})
    return rows


def main():
    # 学员 → 解析目录 映射
    students = {}  # name -> {Q1: dir, Q2: dir, attempt}
    for d in sorted(os.listdir(EXT)):
        if not os.path.isdir(os.path.join(EXT, d)):
            continue
        m = re.match(r"(\d+)_(.+?)__Q(\d)_", d)
        if not m:
            continue
        attempt, name, q = m.group(1), m.group(2), int(m.group(3))
        key = f"{attempt}_{name}"
        students.setdefault(key, {"attempt": attempt, "name": name})[f"Q{q}"] = d

    # 评分
    report = []
    for key, s in sorted(students.items()):
        rec = {"key": key, "attempt": s["attempt"], "name": s["name"], "Q1": [], "Q2": [], "q1_score": 0, "q2_score": 0}
        # 合并提交识别：检测每份文件内容里同时包含 Q1+Q2 关键词
        # Q1 关键词：性能监控、auto_check、巡检、基准
        # Q2 关键词：雷池、egova_lua_waf、弱密码
        files = {q: s.get(f"Q{q}") for q in (1, 2)}
        contents = {}
        for q, sub in files.items():
            if sub:
                with open(os.path.join(EXT, sub, "text_only.txt"), "r", encoding="utf-8") as f:
                    contents[q] = f.read()
            else:
                contents[q] = ""
        # 检查每份文件是否覆盖 Q1+Q2
        def has_q1(txt):
            return bool(re.search(r"性能监控|性能应急|auto_check|巡检|基准测试", txt))
        def has_q2(txt):
            return bool(re.search(r"雷池|egova_lua_waf|lua_waf|弱密码", txt))

        # 决定每题用哪个文件评分
        # 优先用本题文件；如本题文件没本题关键词，但另一题文件含本题内容，则用另一题文件
        merged_into = None  # 标记是否合并提交
        for q in (1, 2):
            sub = files[q]
            text_src = sub  # 用于评分的源
            note = ""
            if not sub:
                # 没交本题文件
                # 看另一题文件里是否含本题内容
                other = files.get(3-q)
                if other and ((q == 1 and has_q1(contents.get(3-q, ""))) or (q == 2 and has_q2(contents.get(3-q, "")))):
                    text_src = other
                    note = f"⚠ 合并提交：Q{q} 答案在 Q{3-q} 文件中"
                    merged_into = 3-q
                else:
                    rec[f"Q{q}"] = [{"code": "MISS", "desc": "未提交本题", "max": 50, "awarded": 0, "verdict": "❌ 未提交"}]
                    rec[f"q{q}_score"] = 0
                    rec[f"q{q}_raw"] = 0
                    continue
            else:
                # 本题文件存在，但内容是否真的对应本题？
                # 如果 Q1 文件里没 Q1 内容但有 Q2 内容，说明上传错了
                this_has = (q == 1 and has_q1(contents[q])) or (q == 2 and has_q2(contents[q]))
                if not this_has:
                    other = files.get(3-q)
                    if other and ((q == 1 and has_q1(contents.get(3-q, ""))) or (q == 2 and has_q2(contents.get(3-q, "")))):
                        text_src = other
                        note = f"⚠ Q{q} 上传文件不含本题内容，改读 Q{3-q} 文件"

            rows = grade_one(os.path.join(EXT, text_src, "text_only.txt"), q)
            if note:
                for r in rows:
                    r["src_note"] = note
            rec[f"Q{q}"] = rows or []
            raw_score = sum(r["awarded"] for r in (rows or []))
            rec[f"q{q}_score"] = min(raw_score, 50.0)
            rec[f"q{q}_raw"] = raw_score
            rec[f"q{q}_src"] = text_src
        rec["total"] = rec["q1_score"] + rec["q2_score"]
        rec["merged"] = merged_into
        report.append(rec)

    # 写 JSON 总报告
    with open(os.path.join(ROOT, "_grading_v1.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 写 Markdown 汇总
    md_lines = ["# 性能安全认证实操-26年二季度 阅卷报告（初版-文字结构评分）", "",
                "**说明**：此版本基于文字段落关键词匹配 + 段落附近图片数评估，未做视觉细判。",
                "标 ⚠ 的采分点有特殊要求（如带 URL、清单≥5 等），需视觉确认。",
                "命中文字但无截图的部分默认给 30%，需视觉补判。", "",
                "## 总分排行", "",
                "| 排名 | Attempt | 姓名 | Q1 性能监控 | Q2 安全运维 | 总分 | 状态 |", "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(sorted(report, key=lambda x: -x["total"]), 1):
        miss_q1 = any(p["code"] == "MISS" for p in r["Q1"])
        miss_q2 = any(p["code"] == "MISS" for p in r["Q2"])
        status = []
        if miss_q1: status.append("Q1未交")
        if miss_q2: status.append("Q2未交")
        md_lines.append(f"| {i} | {r['attempt']} | {r['name']} | {r['q1_score']:.1f}/50 | {r['q2_score']:.1f}/50 | **{r['total']:.1f}/100** | {','.join(status) or '正常'} |")

    # 每人明细
    md_lines += ["", "## 每位考生扣分明细", ""]
    for r in sorted(report, key=lambda x: -x["total"]):
        md_lines.append(f"### {r['attempt']} - {r['name']}  总分 {r['total']:.1f}/100")
        md_lines.append("")
        for q in (1, 2):
            qrows = r[f"Q{q}"]
            qscore = r[f"q{q}_score"]
            qname = "性能监控" if q == 1 else "安全运维"
            md_lines.append(f"**Q{q} {qname} — {qscore:.1f}/50**")
            md_lines.append("")
            md_lines.append("| 采分点 | 分值 | 得分 | 评判 |")
            md_lines.append("|---|---|---|---|")
            for p in qrows:
                desc = p.get("desc", "?")
                code = p.get("code", "")
                mx = p.get("max", 0)
                aw = p.get("awarded", 0)
                v = p.get("verdict", "")
                md_lines.append(f"| {code} {desc} | {mx} | {aw} | {v} |")
            md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    with open(os.path.join(ROOT, "_grading_v1.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    # 写 CSV（魔方表：行=学员，列=采分点）
    headers = ["attempt", "name"]
    for p in Q1_POINTS + Q2_POINTS:
        code, sect, desc, mx = p[0], p[1], p[2], p[3]
        headers.append(f"{code}({mx})")
    headers += ["Q1", "Q2", "Total"]
    with open(os.path.join(ROOT, "_grading_v1.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in sorted(report, key=lambda x: -x["total"]):
            row = [r["attempt"], r["name"]]
            q1_map = {p.get("code"): p for p in r["Q1"]}
            q2_map = {p.get("code"): p for p in r["Q2"]}
            for p in Q1_POINTS:
                code, mx = p[0], p[3]
                pr = q1_map.get(code, {})
                row.append(f"{pr.get('awarded', 0)}/{mx}")
            for p in Q2_POINTS:
                code, mx = p[0], p[3]
                pr = q2_map.get(code, {})
                row.append(f"{pr.get('awarded', 0)}/{mx}")
            row += [f"{r['q1_score']:.1f}", f"{r['q2_score']:.1f}", f"{r['total']:.1f}"]
            w.writerow(row)
    print(f"[✓] 已生成: _grading_v1.md / _grading_v1.csv / _grading_v1.json")


if __name__ == "__main__":
    main()
