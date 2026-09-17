# -*- coding: utf-8 -*-
"""quiz266 实操成绩回写 Moodle（slot1=Q1/30, slot2=Q2/30, slot3=Q3/40）。
数据源：_grading/G{0..3}_{Q1,Q2,Q3}.json（attempt级独立阅卷分）。
默认 dry-run（只GET预检表单+maxmark）；加 --commit 才POST。--only <attempt> 限单个。
"""
import json, os, sys, time, html as _html

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, r"D:\git\opencode-skills\内部阅卷\scripts\common")
from moodle_submit import fetch_form, post_grade  # noqa: E402

WORKDIR = r"D:\opencode\file\2026-09-14\阅卷_266"
GDIR = os.path.join(WORKDIR, "_grading")
SLOTS = [(1, "Q1", 30, "T1"), (2, "Q2", 30, "T2"), (3, "Q3", 40, "T3")]
NAMES = {a["attempt"]: a["name"] for a in
         json.load(open(os.path.join(WORKDIR, "_attempts.json"), encoding="utf-8"))}


def load_grades():
    grades = {}
    import glob as _glob
    files = []
    for gi in range(4):
        for q in ["Q1", "Q2", "Q3"]:
            files.append(os.path.join(GDIR, f"G{gi}_{q}.json"))
    for gi in ["INCR0", "INCR1"]:
        for q in ["Q1", "Q2", "Q3"]:
            files.append(os.path.join(GDIR, f"{gi}_{q}.json"))
    for fp in files:
        if not os.path.isfile(fp):
            continue
        q = os.path.basename(fp).split("_")[-1].split(".")[0]
        for r in json.load(open(fp, encoding="utf-8")):
            g = grades.setdefault(r["attempt"], {})
            if q == "Q1":
                g["Q1"] = r
            elif q == "Q2":
                g["Q2"] = r
            else:
                g["Q3"] = r
    return grades


REQ = {
    1: [("T1-1 需求完整", 8, "7大模块+流程/状态+边界说明"),
        ("T1-2 PC原型", 7, "导航+统计卡片+数据表格+图表+图标化"),
        ("T1-3 移动原型", 7, "375视口+底部TabBar+44触控+安全区"),
        ("T1-4 图标覆盖", 7, "受理/分派/督办/超期/拍照/定位/办结/预警8类"),
        ("T1-5 可复用", 5, "需求文档+原型+图标清单成体系")],
    2: [("T2-1 接入鉴权", 8, "模拟服务可运行+鉴权通过+文档齐全"),
        ("T2-2 文档口径", 8, "接口清单+字段口径+字典/错误码"),
        ("T2-3 模型台账", 7, "模型正确+调度幂等+合并口径"),
        ("T2-4 埋坑多轮", 5, "≥3处埋坑+多轮定位过程完整"),
        ("T2-5 验证复现", 2, "鉴权失败到可复现完整链路截图")],
    3: [("T3-1 场景", 5, "一句话定位+业务背景+目标"),
        ("T3-2 来源", 5, "固定位置+版本日期+适用范围"),
        ("T3-3 Skill范围", 5, "全局发布+理由版本+权限+输入输出"),
        ("T3-4 提示词", 6, "任务卡+首轮提示词+关键迭代≥2轮"),
        ("T3-5 人工复核", 6, "复核人/时间/核验修改记录"),
        ("T3-6 风险边界", 6, "授权/脱敏/禁止输入/人工确认点"),
        ("T3-7 可复用", 7, "模板/检查表/流程/SOP/台账")],
}
KEYS = {1: ("Q1", "T1", 30, "实操题1 UI需求设计与原型"),
        2: ("Q2", "T2", 30, "实操题2场景任选"),
        3: ("Q3", "T3", 40, "构造题Skill/Agent构造")}


def cause(flag):
    if "缺交" in flag:
        return "该题未提交"
    if "方向未识别" in flag:
        return "未识别所选方向"
    if "红线" in flag:
        return "触安全红线"
    if "needs_visual" in flag:
        return "截图证据不足（待人工复核）"
    if "仅截图无文档" in flag:
        return "仅截图无文档说明"
    return "对应证据不完整"


def slot_comment(slot, g, name, direction):
    q, tkey, maxmark, title = KEYS[slot]
    rec = g.get(q, {})
    flag = rec.get("flag", "")
    if q == "Q2" and direction and direction != "-":
        head = f"<p>{_html.escape(name)}{title}（{direction}）：{rec.get(tkey, 0)}/{maxmark} 分。</p>"
    else:
        head = f"<p>{_html.escape(name)}{title}：{rec.get(tkey, 0)}/{maxmark} 分。</p>"
    lines = [head]
    ds = [rec.get(f"d{i+1}", 0) for i in range(len(REQ[slot]))]
    for (item, mx, req), got in zip(REQ[slot], ds):
        if got >= mx:
            lines.append(f"<p>{item}：{got}/{mx}，达标（{req}）。</p>")
        else:
            lines.append(f"<p>{item}：{got}/{mx}，扣{round(mx-got, 2)}分——{cause(flag)}；要求：{req}。</p>")
    awarded = rec.get(tkey, 0)
    raw_sum = round(sum(ds), 2)
    raw_scaled = round(raw_sum / 34 * 30, 2) if slot == 1 else raw_sum
    if awarded < raw_scaled - 0.01:
        lines.append(
            f"<p>注：以上分项合计原始分{raw_scaled}分；分项满分但有效截图不足，"
            f"扣10%计{awarded}/{maxmark}分，待人工复核截图后可调。</p>")
    return "".join(lines)


def main():
    commit = "--commit" in sys.argv
    only = None
    frm = None
    to = None
    if "--only" in sys.argv:
        only = int(sys.argv[sys.argv.index("--only") + 1])
    if "--from" in sys.argv:
        frm = int(sys.argv[sys.argv.index("--from") + 1])
    if "--to" in sys.argv:
        to = int(sys.argv[sys.argv.index("--to") + 1])
    if not os.environ.get("MOODLE_COOKIE"):
        raise SystemExit("缺少 MOODLE_COOKIE")
    grades = load_grades()
    if only is not None:
        grades = {only: grades[only]}
    if frm is not None:
        grades = {a: g for a, g in grades.items() if a >= frm}
    if to is not None:
        grades = {a: g for a, g in grades.items() if a <= to}
    results, n_post, n_skip = [], 0, 0
    for att in sorted(grades):
        if att == 7168:
            results.append({"attempt": att, "skip": "不参考评语保留"})
            continue
        g = grades[att]
        name = NAMES.get(att, str(att))
        direction = g.get("Q2", {}).get("direction", "-")
        marks = {1: g.get("Q1", {}).get("T1", 0),
                 2: g.get("Q2", {}).get("T2", 0),
                 3: g.get("Q3", {}).get("T3", 0)}
        for slot, q, maxmark, _ in SLOTS:
            flag = g.get(q, {}).get("flag", "")
            if "缺交" in flag and marks[slot] == 0:
                results.append({"attempt": att, "slot": slot, "skip": "缺交"})
                n_skip += 1
                continue
            try:
                form = fetch_form(att, slot)
            except Exception as e:
                results.append({"attempt": att, "slot": slot, "err": f"fetch失败 {e}"})
                print(f"FAIL fetch attempt={att} slot={slot}: {e}", flush=True)
                continue
            mm = form["fields"].get(
                f"q{form['quba']}:{slot}_-maxmark" if form["quba"] else "-maxmark")
            if not form["quba"] or str(mm) not in {str(maxmark), f"{maxmark}.0"}:
                results.append({"attempt": att, "slot": slot, "err":
                                f"预检失败 quba={form['quba']} maxmark={mm} 期望{maxmark}"})
                print(f"FAIL 预检 attempt={att} slot={slot} quba={form['quba']} maxmark={mm}",
                      flush=True)
                continue
            c = slot_comment(slot, g, name, direction)
            if commit:
                try:
                    r = post_grade(att, slot, marks[slot], c, dry_run=False)
                except Exception as e:
                    results.append({"attempt": att, "slot": slot, "mark": marks[slot],
                                    "err": f"POST异常 {e}"})
                    print(f"FAIL POST attempt={att} slot={slot}: {e}", flush=True)
                    continue
                results.append({"attempt": att, "slot": slot, "mark": marks[slot],
                                "result": r})
                print(f"POST attempt={att} slot={slot} mark={marks[slot]} ok={r.get('ok')}",
                      flush=True)
                n_post += 1
                time.sleep(0.5)
                if n_post % 25 == 0:
                    json.dump(results, open(os.path.join(
                        WORKDIR, "_submit_266_commit_part.json"), "w", encoding="utf-8"),
                        ensure_ascii=False, indent=1)
            else:
                results.append({"attempt": att, "slot": slot, "mark": marks[slot],
                                "result": "dry-run ok"})
                n_post += 1
    mode = "commit" if commit else "dry-run"
    json.dump(results, open(os.path.join(WORKDIR, f"_submit_266_{mode}.json"), "w",
                                              encoding="utf-8"),
              ensure_ascii=False, indent=1)
    fails = [r for r in results if "err" in r]
    print(f"[{mode}] slot项 {len(results)}（POST/预检 {n_post}，跳过 {n_skip}，失败 {len(fails)}）",
          flush=True)


if __name__ == "__main__":
    main()
