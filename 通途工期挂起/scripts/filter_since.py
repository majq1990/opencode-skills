#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按创建时间过滤工期/挂起行 JSON。
用法: python filter_since.py [--workdir <probe json 所在目录>] [--since 2026-07-01]
输出: <workdir>/dur_since.json / sus_since.json
  schema: [{rowId, projectName, ctime, attaches?}]  (挂起含 attaches 兼容导出脚本 rowsfile)
"""
import sys, os, json, io, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ap = argparse.ArgumentParser()
ap.add_argument("--workdir", default=os.path.join("D:/opencode/file", __import__("datetime").date.today().isoformat()))
ap.add_argument("--since", default="2026-07-01")
a = ap.parse_args()

DUR_PROJ = "69fc40831e6716810741b843"
SUS_PROJ = "6a1808ba964e268c28697ebe"

def load(name):
    p = os.path.join(a.workdir, name)
    if not os.path.exists(p):
        print(f"!! 缺 {p}，先跑 probe_tables.mjs")
        sys.exit(1)
    return json.load(open(p, encoding="utf-8"))

dur = [r for r in load("probe_duration.json") if str(r.get("ctime", "")) >= a.since]
sus = [r for r in load("probe_suspend.json") if str(r.get("ctime", "")) >= a.since]

def mk(rows, proj_cid, with_att):
    out = []
    for r in rows:
        it = {"rowId": r.get("rowid"), "projectName": (r.get(proj_cid) or "").strip(), "ctime": r.get("ctime", "")}
        if with_att:
            it["attaches"] = r.get("6a27a90e964e268c286ae204") or []
        out.append(it)
    return out

dur_out = mk(dur, DUR_PROJ, False)
sus_out = mk(sus, SUS_PROJ, True)

json.dump(dur_out, open(os.path.join(a.workdir, "dur_since.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(sus_out, open(os.path.join(a.workdir, "sus_since.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{a.since} 之后: 工期 {len(dur_out)} 条, 挂起 {len(sus_out)} 条")
for it in dur_out: print(f"  工期 {it['ctime'][:10]} {it['projectName']}")
for it in sus_out: print(f"  挂起 {it['ctime'][:10]} {it['projectName']} 附件{len(it['attaches'])}")
