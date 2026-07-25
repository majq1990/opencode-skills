"""批量提交评分到 Moodle
用法: python batch_submit.py <workdir> [--skip attempt:slot[,attempt:slot]]
环境变量: MOODLE_COOKIE
"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(__file__))
from moodle_submit import post_grade

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\阅卷"

# 跳过清单：从 --skip 参数读取
SKIP = set()
if "--skip" in sys.argv:
    idx = sys.argv.index("--skip")
    if idx + 1 < len(sys.argv):
        for pair in sys.argv[idx + 1].split(","):
            try:
                a, s = pair.split(":")
                SKIP.add((int(a), int(s)))
            except Exception:
                pass

with open(os.path.join(ROOT, "_submit_plan.json"), "r", encoding="utf-8") as f:
    plan = json.load(f)

results = []
total = 0
ok_count = 0
fail = []
for item in plan:
    attempt = item["attempt"]
    name = item["name"]
    for q in (1, 2):
        if (attempt, q) in SKIP:
            print(f"SKIP [{attempt} {name[:15]}] Q{q}")
            continue
        if f"Q{q}" not in item:
            continue
        mark = item[f"Q{q}"]["mark"]
        comment = item[f"Q{q}"]["comment"]
        total += 1
        print(f"POST [{attempt} {name[:15]}] Q{q} → {mark}/50 ... ", end="", flush=True)
        res = post_grade(attempt, q, mark, comment, dry_run=False)
        if res.get("ok"):
            print(f"OK (status={res.get('status')})")
            ok_count += 1
        else:
            print(f"FAIL: {res.get('err','')[:100]}")
            fail.append((attempt, q, str(res)))
        results.append({"attempt": attempt, "slot": q, "mark": mark, "result": res})
        time.sleep(0.5)  # 避免击垮服务器

print(f"\n==== 提交完成 ====")
print(f"成功 {ok_count}/{total}")
if fail:
    print("失败：")
    for f in fail:
        print(f"  {f}")

with open(os.path.join(ROOT, "_submit_results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
