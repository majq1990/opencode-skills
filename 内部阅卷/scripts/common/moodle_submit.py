"""
Moodle Quiz 鎵归噺褰曞叆鍒嗘暟+璇勮锛坈omment.php锛?
宸ヤ綔娴侊細
1. 瀵规瘡涓?attempt 鐨?Q1/Q2 鍏?GET comment.php 鎷?sesskey + itemid + sequencecheck
2. 鐢?POST 鎻愪氦 mark + comment HTML
3. 杈撳嚭姣忔鎻愪氦鐨勭粨鏋?

鏀寔 --dry-run 鍙墦鍗颁笉鎻愪氦
"""
import os, sys, re, json, urllib.parse
import urllib.request

# 鐢ㄦ硶: python moodle_submit.py <workdir>
# 蹇呴渶鐜鍙橀噺: MOODLE_COOKIE (鍚?MoodleSession=xxx; MOODLEID1_=xxx)
# 鍙€? MOODLE_BASE (榛樿 http://onekey.egova.com.cn:8888)
COOKIE = os.environ.get("MOODLE_COOKIE", "")
BASE = os.environ.get("MOODLE_BASE", "http://onekey.egova.com.cn:8888")
ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\闃呭嵎"
if not COOKIE:
    print("ERR: 蹇呴』璁剧疆鐜鍙橀噺 MOODLE_COOKIE", file=sys.stderr)
    # 涓嶇珛鍗抽€€鍑猴紝鍥犱负 import 鏃朵篃浼氳窇鍒拌繖閲岋紱鍙湁鐪熻皟鐢?fetch_form 鏃舵墠妫€鏌?


def fetch_form(attempt, slot):
    url = f"{BASE}/mod/quiz/comment.php?attempt={attempt}&slot={slot}"
    req = urllib.request.Request(url, headers={"Cookie": COOKIE, "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"fetch_form err {e}", file=sys.stderr)
        html = ""
    fields = {}
    # 绗竴涓?hidden inputs
    for m in re.finditer(r'<input[^>]+name="([^"]+)"[^>]+value="([^"]*)"', html):
        fields[m.group(1)] = m.group(2)
    # textarea
    for m in re.finditer(r'<textarea[^>]+name="([^"]+)"[^>]*>([\s\S]*?)</textarea>', html):
        fields[m.group(1)] = m.group(2)
    # 鎵?quba id
    qm = re.search(r'name="(q\d+):(\d+)_-mark"', html)
    if qm:
        quba = int(qm.group(1)[1:])
    else:
        quba = None
    # sesskey
    sk = re.search(r'sesskey["\s:=]+([A-Za-z0-9]+)', html)
    sesskey = sk.group(1) if sk else None
    return {"quba": quba, "sesskey": sesskey, "fields": fields, "raw": html}


def post_grade(attempt, slot, mark, comment_html, dry_run=True):
    info = fetch_form(attempt, slot)
    quba = info["quba"]
    if not quba:
        return {"ok": False, "err": f"no quba for attempt={attempt}"}
    prefix = f"q{quba}:{slot}_"
    f = info["fields"]

    # 鏋勯€?POST data
    post = {
        f"{prefix}:sequencecheck": f.get(f"{prefix}:sequencecheck", "1"),
        f"{prefix}-comment": comment_html,
        f"{prefix}-comment:itemid": f.get(f"{prefix}-comment:itemid", "0"),
        f"{prefix}-commentformat": f.get(f"{prefix}-commentformat", "1"),
        f"{prefix}-mark": str(mark),
        f"{prefix}-maxmark": f.get(f"{prefix}-maxmark", "50"),
        f"{prefix}:minfraction": f.get(f"{prefix}:minfraction", "0"),
        f"{prefix}:maxfraction": f.get(f"{prefix}:maxfraction", "1"),
        "attempt": str(attempt),
        "slot": str(slot),
        "slots": str(slot),
        "sesskey": f.get("sesskey") or info["sesskey"],
        "submit": "淇濆瓨",
    }

    if dry_run:
        return {"ok": True, "dry": True, "post": {k: (v[:60]+"..." if len(str(v))>60 else v) for k, v in post.items()}}

    data = urllib.parse.urlencode(post).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/mod/quiz/comment.php",
        data=data,
        headers={
            "Cookie": COOKIE,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{BASE}/mod/quiz/comment.php?attempt={attempt}&slot={slot}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", errors="ignore")
            status = r.status
        # comment.php 鎴愬姛鍚庝細閲嶅畾鍚戝埌 review.php锛屾甯稿簲璇ユ槸 302 鎴栬繑鍥炴垚鍔熼〉
        return {"ok": True, "status": status, "redirect": r.url, "len": len(body)}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "err": e.read().decode("utf-8", errors="ignore")[:200]}
    except Exception as e:
        return {"ok": False, "err": str(e)}


def main():
    dry = "--dry-run" in sys.argv
    plan_path = os.path.join(ROOT, "_submit_plan.json")
    if not os.path.exists(plan_path):
        print(f"ERR: missing {plan_path}, 璇峰厛鐢熸垚鎻愪氦璁″垝")
        return

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    for item in plan:
        attempt = item["attempt"]
        name = item.get("name", "")
        for q in (1, 2):
            if f"Q{q}" not in item:
                continue
            mark = item[f"Q{q}"]["mark"]
            comment = item[f"Q{q}"]["comment"]
            print(f"\n[{attempt} {name}] slot={q} 鈫?鍒嗘暟 {mark}")
            res = post_grade(attempt, q, mark, comment, dry_run=dry)
            print(f"  result: {json.dumps(res, ensure_ascii=False)[:200]}")


if __name__ == "__main__":
    main()
