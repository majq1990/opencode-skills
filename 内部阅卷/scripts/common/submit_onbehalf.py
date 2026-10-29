# -*- coding: utf-8 -*-
"""内部阅卷 · 共享能力：Moodle 批量“代交卷”（处理“作答了但未交卷”的进行中试答）

场景：Moodle 测验截止后，部分考生“已作答但未点提交”，试答停在“进行中”，
既不能评分也无法批改。本脚本在人工确认清单后代为交卷：
  1) 给目标用户加“用户覆盖”（临时延长截止；不延长则关闭后进不去）
  2) 管理员“以此用户身份登录” → 打开 summary 页 → 提交全部答案并结束
  3) 完成后删除用户覆盖，恢复“已关闭”状态

子命令：
  list    只读：列出指定测验的“进行中”试答，保存确认清单 json
  submit  写入：按清单创建覆盖并逐个代交卷（默认 dry-run，须加 --commit）
  verify  只读：输出状态统计（进行中/已结束）与用户覆盖条数
  cleanup 写入：删除本流程创建的用户覆盖（默认 dry-run，须加 --commit）

认证（按优先级）：
  MOODLE_COOKIE                    直接给会话 Cookie（防止旧会话 POST 失效，脚本仅作备用）
  MOODLE_USER + MOODLE_PASSWORD    登录页账密登录（最稳，每个考生用全新会话）
  环境变量文件（可选）             D:\\opencode\\config\\.env 或 MOODLE_ENV_FILE 指定
其它环境变量：MOODLE_BASE（默认 http://onekey.egova.com.cn:8888）

用法示例（cmid 即测验 URL 里的 id，如 report.php?id=266 → 266）：
  python submit_onbehalf.py list    --cmid 266
  python submit_onbehalf.py submit  --cmid 266 -f _submit_onbehalf_266_inprogress.json --commit
  python submit_onbehalf.py verify  --cmid 266
  python submit_onbehalf.py cleanup --cmid 266 -f _submit_onbehalf_266_state.json --commit

红线：submit / cleanup 属写操作，必须人工确认后加 --commit；建议先 dry-run 预览。
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    sys.exit("需要 requests：pip install requests")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DEFAULT_BASE = os.environ.get("MOODLE_BASE", "http://onekey.egova.com.cn:8888")
ENV_FILE = os.environ.get("MOODLE_ENV_FILE", r"D:\opencode\config\.env")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
BASE = DEFAULT_BASE
_CRED = {}


def _load_env_file(path):
    out = {}
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def cred(name):
    if name not in _CRED:
        v = os.environ.get(name, "")
        if not v:
            v = _load_env_file(ENV_FILE).get(name, "")
        _CRED[name] = v
    return _CRED[name]


def new_session(with_cookie=False):
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    if with_cookie:
        c = cred("MOODLE_COOKIE")
        if c:
            s.headers["Cookie"] = c
    return s


def title_of(page):
    m = re.search(r"<title>(.*?)</title>", page, re.S)
    return m.group(1).strip() if m else ""
def is_logged_in(s):
    r = s.get(BASE + "/my/", timeout=60, allow_redirects=True)
    u = r.url.lower()
    t = title_of(r.text)
    if "login" in u or "登录" in t:
        return False, t
    return True, t


def login(s):
    user, pwd = cred("MOODLE_USER"), cred("MOODLE_PASSWORD")
    if not user or not pwd:
        raise RuntimeError("缺少 MOODLE_USER / MOODLE_PASSWORD（或 MOODLE_COOKIE）")
    r = s.get(BASE + "/login/index.php", timeout=60)
    m = re.search(r'name="logintoken"\s+value="([^"]+)"', r.text)
    if not m:
        raise RuntimeError("登录页无 logintoken（是否验证码？）")
    data = {"anchor": "", "logintoken": m.group(1), "username": user,
            "password": pwd, "rememberusername": "1"}
    s.post(BASE + "/login/index.php", data=data, timeout=60, allow_redirects=True)
    ok, t = is_logged_in(s)
    if not ok:
        raise RuntimeError("登录失败：" + t)


def ensure_session():
    s = new_session(with_cookie=True)
    ok, t = is_logged_in(s)
    if ok:
        return s, "cookie: " + t
    s2 = new_session(with_cookie=False)
    login(s2)
    return s2, "login: " + is_logged_in(s2)[1]


def sesskey_of(page):
    m = re.search(r"[?&]sesskey=([A-Za-z0-9]{8,})", page)
    if m:
        return m.group(1)
    m = re.search(r'name="sesskey"\s+value="([^"]+)"', page)
    return m.group(1) if m else None


def unesc(s):
    return s.replace("&amp;", "&")


def strip_tags(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()


def get_form(page, key):
    for m in re.finditer(r"<form\b([^>]*)>(.*?)</form>", page, re.S):
        attrs, body = m.group(1), m.group(2)
        act = re.search(r'action="([^"]*)"', attrs)
        if act and key in act.group(1):
            return unesc(act.group(1)), body
    return None, None


def controls_to_data(body):
    data = {}
    for m in re.finditer(r"<input\b([^>]*)>", body):
        attrs = m.group(1)
        nm = re.search(r'name="([^"]*)"', attrs)
        if not nm:
            continue
        name = nm.group(1)
        tp = re.search(r'type="([^"]*)"', attrs)
        tp = tp.group(1) if tp else "text"
        vl = re.search(r'value="([^"]*)"', attrs)
        vl = vl.group(1) if vl else ""
        if tp in ("submit", "reset", "button"):
            continue
        if tp in ("checkbox", "radio"):
            if "checked" in attrs:
                data[name] = vl or "1"
            continue
        data[name] = vl
    for m in re.finditer(r"<select\b([^>]*)>(.*?)</select>", body, re.S):
        attrs, sbody = m.group(1), m.group(2)
        nm = re.search(r'name="([^"]*)"', attrs)
        if not nm:
            continue
        chosen = None
        for om in re.finditer(r"<option\b([^>]*)>", sbody):
            oattrs = om.group(1)
            if "selected" in oattrs:
                v = re.search(r'value="([^"]*)"', oattrs)
                chosen = v.group(1) if v else ""
                break
        data[nm.group(1)] = chosen if chosen is not None else ""
    for m in re.finditer(r"<textarea\b([^>]*)>(.*?)</textarea>", body, re.S):
        nm = re.search(r'name="([^"]*)"', m.group(1))
        if nm:
            data[nm.group(1)] = m.group(2).strip()
    return data
def fetch_overview(s, cmid):
    r = s.get(BASE + "/mod/quiz/report.php",
              params={"id": cmid, "mode": "overview", "pagesize": 1000}, timeout=120)
    return r.text


def parse_overview(page):
    tbl = page.split('id="attempts"')[1].split("</table>")[0] if 'id="attempts"' in page else ""
    states = {}
    rows = []
    for r_ in re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, re.S):
        cs = [strip_tags(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r_, re.S)]
        if not cs or len(cs) < 5:
            continue
        if "选择试答" not in cs[0] and "姓氏" not in cs[0]:
            continue
        st = cs[4]
        states[st] = states.get(st, 0) + 1
        uid = re.search(r"user/view\.php\?id=(\d+)", r_)
        att = re.search(r"review\.php\?attempt=(\d+)", r_)
        rows.append({
            "uid": int(uid.group(1)) if uid else None,
            "attempt": int(att.group(1)) if att else None,
            "name": cs[2].replace("回顾试答", "").strip(),
            "status": st,
            "start": cs[5] if len(cs) > 5 else "",
        })
    return states, rows


def fetch_overrides(s, cmid):
    return s.get(BASE + "/mod/quiz/overrides.php",
                 params={"cmid": cmid, "mode": "user"}, timeout=90).text


def parse_override_rows(page):
    if 'id="quizoverrides"' not in page:
        return []
    region = page.split('id="quizoverrides"')[1].split("</table>")[0]
    out = []
    for rm in re.finditer(r"<tr[^>]*>(.*?)</tr>", region, re.S):
        row = rm.group(1)
        uid_m = re.search(r"user/view\.php\?id=(\d+)", row)
        del_m = re.search(r"overridedelete\.php\?id=(\d+)&amp;sesskey=([A-Za-z0-9]+)", row)
        if uid_m and del_m:
            out.append({"uid": uid_m.group(1), "ov": del_m.group(1), "sk": del_m.group(2)})
    return out


def discover_cid(s, cmid):
    r = s.get(BASE + "/mod/quiz/view.php", params={"id": cmid}, timeout=90)
    m = re.search(r"/course/view\.php\?id=(\d+)", r.text)
    return int(m.group(1)) if m else None


def add_overrides(s, cmid, uids, close_str):
    """给指定 uid 逐个创建“用户覆盖”（延长截止时间）；返回 {uid: ovid}"""
    r = s.get(BASE + "/mod/quiz/overrideedit.php", params={"cmid": cmid}, timeout=90)
    act, body = get_form(r.text, "overrideedit")
    if not act:
        raise RuntimeError("未找到覆盖表单（需要管理员权限）")
    base = controls_to_data(body)
    dt = datetime.strptime(close_str, "%Y-%m-%d %H:%M")
    if dt <= datetime.now():
        raise RuntimeError("覆盖截止时间必须晚于当前时间：" + close_str)
    created = {}
    for uid in uids:
        data = dict(base)
        data["userid"] = str(uid)
        for k, v in (("day", dt.day), ("month", dt.month), ("year", dt.year),
                     ("hour", dt.hour), ("minute", dt.minute)):
            data["timeclose[%s]" % k] = str(v)
        data["timeclose[enabled]"] = "1"
        data["submitbutton"] = "保存"
        rp = s.post(act, data=data, timeout=120, allow_redirects=True)
        rows = parse_override_rows(fetch_overrides(s, cmid))
        mine = [x for x in rows if x["uid"] == str(uid)]
        created[str(uid)] = mine[-1]["ov"] if mine else None
        print("  覆盖 uid=%s -> ov=%s (%s)" % (uid, created[str(uid)], rp.url))
    return created
def finish_attempt(attempt, uid, cmid, cid):
    """以此用户身份登录并把 attempt 提交（“提交所有答案并结束”）"""
    rec = {"attempt": attempt, "uid": uid}
    s = new_session(False)
    login(s)
    r0 = s.get(BASE + "/mod/quiz/overrides.php", params={"cmid": cmid}, timeout=90)
    sk = sesskey_of(r0.text)
    if not sk:
        rec["skip"] = "未取到管理员 sesskey"
        return rec
    s.get(BASE + "/course/loginas.php",
          params={"id": cid, "user": uid, "sesskey": sk}, timeout=90, allow_redirects=True)
    rs = s.get(BASE + "/mod/quiz/summary.php",
               params={"attempt": attempt, "cmid": cmid}, timeout=120, allow_redirects=True)
    act, body = get_form(rs.text, "processattempt")
    if not act:
        t = strip_tags(rs.text)
        rec["skip"] = "无提交表单（可能已结束或不可进入）"
        i = t.find("已提交")
        rec["snippet"] = t[max(0, i - 80):i + 60] if i >= 0 else t[:160]
        print("  跳过 attempt %s：%s" % (attempt, rec["snippet"]))
        return rec
    data = controls_to_data(body)
    r3 = s.post(act, data=data, timeout=180, allow_redirects=True)
    rec["post_url"] = r3.url
    r4 = s.get(BASE + "/mod/quiz/review.php",
               params={"attempt": attempt, "cmid": cmid}, timeout=120, allow_redirects=True)
    t4 = strip_tags(r4.text)
    rec["finished"] = "已结束" in t4
    return rec


def delete_override(s, ovid, sk):
    """删除覆盖：GET 确认页 → POST(confirm=1+sesskey)（两步，缺一不可）"""
    url = BASE + "/mod/quiz/overridedelete.php?id=%s&sesskey=%s" % (ovid, sk)
    r = s.get(url, timeout=90, allow_redirects=False)
    if r.status_code in (301, 302, 303, 307, 308):
        return True
    for fm in re.finditer(r"<form([^>]*)>(.*?)</form>", r.text, re.S):
        attrs, inner = fm.group(1), fm.group(2)
        if "post" not in attrs.lower():
            continue
        am = re.search(r'action="([^"]*)"', attrs)
        action = unesc(am.group(1)) if am else url
        data = {}
        for im in re.finditer(r"<input([^>]*?)/?>", inner):
            ia = im.group(1)
            n = re.search(r'name="([^"]*)"', ia)
            v = re.search(r'value="([^"]*)"', ia)
            ty = re.search(r'type="([^"]*)"', ia)
            if not n:
                continue
            if ty and ty.group(1).lower() in ("radio", "checkbox", "submit", "button", "reset"):
                continue
            data[n.group(1)] = unesc(v.group(1)) if v else ""
        if "confirm" not in data or "sesskey" not in data:
            continue
        r2 = s.post(action, data=data, timeout=90, allow_redirects=False)
        return r2.status_code in (301, 302, 303, 307, 308)
    return False
def cmd_list(args, s):
    states, rows = parse_overview(fetch_overview(s, args.cmid))
    inprog = [r for r in rows if r["status"] == "进行中"]
    out = {"cmid": args.cmid, "base": BASE, "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "states": states, "inprogress": inprog}
    path = args.file or ("_submit_onbehalf_%s_inprogress.json" % args.cmid)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("状态统计:", states)
    print("进行中 %d 份（确认清单已存 %s）" % (len(inprog), path))
    for r in inprog:
        print("  attempt %s  uid %s  %s  开始 %s" % (r["attempt"], r["uid"], r["name"], r["start"]))


def cmd_submit(args, s):
    with open(args.file, "r", encoding="utf-8") as f:
        plan = json.load(f)
    items = plan.get("inprogress", [])
    if not items:
        print("清单为空，无需提交")
        return
    states, rows = parse_overview(fetch_overview(s, args.cmid))
    active = set(r["attempt"] for r in rows if r["status"] == "进行中")
    todo = [r for r in items if r["attempt"] in active]
    skipped = [r for r in items if r["attempt"] not in active]
    for r in skipped:
        print("  跳过 attempt %s（uid %s）：已非“进行中”" % (r["attempt"], r["uid"]))
    if not todo:
        print("没有需要提交的进行中试答")
        return
    close_str = args.close or (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
    print("计划代交卷 %d 份；覆盖截止时间 = %s；模式 = %s" % (
        len(todo), close_str, "提交" if args.commit else "dry-run"))
    for r in todo:
        print("  attempt %s  uid %s  %s" % (r["attempt"], r["uid"], r["name"]))
    if not args.commit:
        print("\n[dry-run] 未做任何写操作；确认无误后加 --commit 执行。")
        return
    uids = []
    for r in todo:
        if str(r["uid"]) not in uids:
            uids.append(str(r["uid"]))
    overrides = add_overrides(s, args.cmid, uids, close_str)
    cid = args.cid or discover_cid(s, args.cmid)
    if not cid:
        raise RuntimeError("无法确定课程 id，请加 --cid 参数")
    state_path = "_submit_onbehalf_%s_state.json" % args.cmid
    state = {"cmid": args.cmid, "cid": cid, "close": close_str,
             "overrides": overrides, "submitted": [],
             "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
    for r in todo:
        rec = finish_attempt(r["attempt"], r["uid"], args.cmid, cid)
        state["submitted"].append(rec)
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        print("  提交 attempt %s -> %s" % (r["attempt"], json.dumps(rec, ensure_ascii=False)))
    states2, rows2 = parse_overview(fetch_overview(s, args.cmid))
    left = [x for x in rows2 if x["status"] == "进行中"]
    print("复核：", states2, "剩余进行中", len(left))
    print("下一步：确认无误后执行 cleanup -f %s --commit 删除覆盖" % state_path)


def cmd_verify(args, s):
    states, rows = parse_overview(fetch_overview(s, args.cmid))
    inprog = [r for r in rows if r["status"] == "进行中"]
    print("状态统计:", states)
    print("进行中 %d 份" % len(inprog))
    for r in inprog:
        print("  attempt %s  uid %s  %s  开始 %s" % (r["attempt"], r["uid"], r["name"], r["start"]))
    rows_ov = parse_override_rows(fetch_overrides(s, args.cmid))
    print("用户覆盖 %d 条" % len(rows_ov))
    for x in rows_ov:
        print("  uid %s  ov %s" % (x["uid"], x["ov"]))


def cmd_cleanup(args, s):
    if args.uids:
        want = set(x.strip() for x in args.uids.split(",") if x.strip())
    else:
        with open(args.file, "r", encoding="utf-8") as f:
            state = json.load(f)
        want = set(state.get("overrides", {}).keys())
    rows = parse_override_rows(fetch_overrides(s, args.cmid))
    targets = [x for x in rows if x["uid"] in want]
    print("当前覆盖列表 %d 行；本次要删 %d 行" % (len(rows), len(targets)))
    for x in targets:
        print("  uid %s  ov %s" % (x["uid"], x["ov"]))
    if not args.commit:
        print("\n[dry-run] 未删除；确认后加 --commit 执行。")
        return
    ok = 0
    for x in targets:
        good = delete_override(s, x["ov"], x["sk"])
        print("  删除 uid %s ov %s -> %s" % (x["uid"], x["ov"], "OK" if good else "FAIL"))
        ok += 1 if good else 0
    rows2 = parse_override_rows(fetch_overrides(s, args.cmid))
    print("已删 %d；覆盖列表剩余 %d 行" % (ok, len(rows2)))


def main():
    global BASE
    ap = argparse.ArgumentParser(description="Moodle 批量代交卷（内部阅卷共享能力）")
    ap.add_argument("--base", default=DEFAULT_BASE)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("list")
    p1.add_argument("--cmid", type=int, required=True)
    p1.add_argument("-f", "--file")
    p2 = sub.add_parser("submit")
    p2.add_argument("--cmid", type=int, required=True)
    p2.add_argument("-f", "--file", required=True)
    p2.add_argument("--close", help="覆盖截止时间，格式 2026-09-15 12:00（默认当前+2小时）")
    p2.add_argument("--cid", type=int, help="课程 id（默认自动探测）")
    p2.add_argument("--commit", action="store_true")
    p3 = sub.add_parser("verify")
    p3.add_argument("--cmid", type=int, required=True)
    p4 = sub.add_parser("cleanup")
    p4.add_argument("--cmid", type=int, required=True)
    p4.add_argument("-f", "--file")
    p4.add_argument("--uids", help="直接指定要删除覆盖的 uid，逗号分隔")
    p4.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    BASE = args.base.rstrip("/")
    s, how = ensure_session()
    print("会话：%s" % how)
    if args.cmd == "list":
        cmd_list(args, s)
    elif args.cmd == "submit":
        cmd_submit(args, s)
    elif args.cmd == "verify":
        cmd_verify(args, s)
    elif args.cmd == "cleanup":
        cmd_cleanup(args, s)


if __name__ == "__main__":
    main()
