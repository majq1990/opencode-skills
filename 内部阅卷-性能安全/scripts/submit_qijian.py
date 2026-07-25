"""
麒舰阅卷批量录入（单题满分 100）
读 <workdir>/_submit_plan_qijian.json，逐个 POST 到 Moodle comment.php。
满分由 comment.php 表单的 maxmark 决定（moodle_submit.post_grade 自动读取）。

用法:
  python submit_qijian.py <workdir> [--dry-run] [--skip attempt[,attempt]]
环境变量: MOODLE_COOKIE
"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from moodle_submit import post_grade

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\阅卷_259"
DRY = "--dry-run" in sys.argv
SKIP = set()
if "--skip" in sys.argv:
    for a in sys.argv[sys.argv.index("--skip") + 1].split(","):
        a = a.strip()
        if a:
            SKIP.add(int(a))

with open(os.path.join(ROOT, "_submit_plan_qijian.json"), "r", encoding="utf-8") as f:
    plan = json.load(f)

ok_count, fail = 0, []
for item in plan:
    attempt = item["attempt"]
    name = item.get("name", "")
    slot = item.get("slot", 1)
    if attempt in SKIP:
        print(f"SKIP [{attempt} {name[:15]}]")
        continue
    mark, comment = item["mark"], item["comment"]
    print(f"POST [{attempt} {name[:15]}] slot={slot} -> {mark}/100 ... ", end="", flush=True)
    res = post_grade(attempt, slot, mark, comment, dry_run=DRY)
    if res.get("ok"):
        print("DRY-OK" if res.get("dry") else f"OK (status={res.get('status')})")
        ok_count += 1
    else:
        print(f"FAIL: {res.get('err', '')[:100]}")
        fail.append((attempt, str(res)[:160]))
    time.sleep(0.5)

print(f"\n==== {'预览' if DRY else '提交'}完成 ====  成功 {ok_count}/{len(plan)}")
if fail:
    print("失败：")
    for a, e in fail:
        print(f"  {a}: {e}")

if not DRY:
    with open(os.path.join(ROOT, "_submit_results_qijian.json"), "w", encoding="utf-8") as f:
        json.dump({"ok": ok_count, "fail": fail}, f, ensure_ascii=False, indent=2)
