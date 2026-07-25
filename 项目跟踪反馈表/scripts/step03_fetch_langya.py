"""Step 3：拉「大区省份表-琅琊榜特殊使用」+ 解析责任人姓名 → 钉钉 userId。

输入  : work_dir/userid_to_depts.json (复用 step2 的部门 cache)
输出  : work_dir/langya_mapping.json   key="大区|区域", value={大区工程总_userids, 省份工程总_userids, ...}
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts import _config as cfg
from scripts._common import call_dws, make_ztoa_client, parse_user_cell, run_async, work_path


async def _fetch_all_rows():
    c = make_ztoa_client()
    try:
        rows, page = [], 1
        while True:
            r = await c.query_records(cfg.WS_LANGYA, page_size=200, page_index=page)
            chunk = (r.get("data") or {}).get("rows") or []
            if not chunk:
                break
            rows.extend(chunk)
            if len(chunk) < 200:
                break
            page += 1
        return rows
    finally:
        await c.aclose()


def search_userid(name: str) -> list[dict]:
    d, out, err = call_dws(["contact", "user", "search", "--query", name, "-y"], timeout=40)
    return (d or {}).get("result") or []


def fetch_user_depts(uid: str) -> list[str]:
    d, out, err = call_dws(["contact", "user", "get", "--ids", uid, "-y"], timeout=40)
    if not d:
        return []
    res = d.get("result") or []
    if not res:
        return []
    m = res[0].get("orgEmployeeModel") or {}
    return [dept.get("deptName") for dept in (m.get("depts") or []) if dept.get("deptName")]


def main(plan: dict) -> Path:
    if not plan.get("include_engineering_leads", True):
        print("[step3] include_engineering_leads=False，跳过琅琊榜")
        out_p = work_path(plan, "langya_mapping.json")
        out_p.write_text("{}", encoding="utf-8")
        return out_p

    print("[step3] fetching langya rows...")
    rows = run_async(_fetch_all_rows())
    print(f"  rows: {len(rows)}")

    pm_cache_p = work_path(plan, "pm_resolved.json")
    pm_cache: dict[str, dict] = json.loads(pm_cache_p.read_text(encoding="utf-8")) if pm_cache_p.exists() else {}
    dept_p = work_path(plan, "userid_to_depts.json")
    dept_cache: dict[str, list[str]] = json.loads(dept_p.read_text(encoding="utf-8")) if dept_p.exists() else {}

    raw_mapping = {}
    for r in rows:
        if (r.get(cfg.F_LY_USABLE) or "").strip() != cfg.LY_USABLE_TRUE:
            continue
        daqu = (r.get(cfg.F_LY_DAQU) or "").strip()
        quyu = (r.get(cfg.F_LY_PROVINCE) or r.get(cfg.F_LY_QUYU_NAME) or "").strip()
        daqu_eng = parse_user_cell(r.get(cfg.F_LY_DAQU_ENG))
        prov_eng = parse_user_cell(r.get(cfg.F_LY_PROV_ENG))
        raw_mapping[f"{daqu}|{quyu}"] = {
            "大区工程总_names": [u.get("fullname") for u in daqu_eng if u.get("status") in (1, "1") and u.get("fullname")],
            "省份工程总_names": [u.get("fullname") for u in prov_eng if u.get("status") in (1, "1") and u.get("fullname")],
            "大区": daqu, "区域": quyu,
        }
    print(f"  usable mappings: {len(raw_mapping)}")

    # 收集所有责任人姓名，解析 userId（复用 pm_cache）
    all_names = {n for v in raw_mapping.values() for n in v["大区工程总_names"] + v["省份工程总_names"]}
    todo = [n for n in all_names if n not in pm_cache]
    print(f"  need resolve langya names: {len(todo)}")
    for i, n in enumerate(todo, 1):
        results = search_userid(n)
        matched = [u for u in results if (u.get("name") or "").strip() == n]
        if matched:
            pm_cache[n] = {
                "userids": [u.get("userId") for u in matched],
                "fullmatch_count": len(matched),
                "names": [u.get("name") for u in matched],
                "titles": [u.get("title") for u in matched],
            }
        else:
            pm_cache[n] = {"userids": []}
        for uid in pm_cache[n].get("userids", []):
            if uid and uid not in dept_cache:
                dept_cache[uid] = fetch_user_depts(uid)
        time.sleep(0.05)
    pm_cache_p.write_text(json.dumps(pm_cache, ensure_ascii=False, indent=2), encoding="utf-8")
    dept_p.write_text(json.dumps(dept_cache, ensure_ascii=False, indent=2), encoding="utf-8")

    def pick(name: str, daqu: str, region: str) -> list[str]:
        info = pm_cache.get(name) or {}
        uids = info.get("userids") or []
        if len(uids) <= 1:
            return uids
        rkey = region.replace("区域", "").strip()
        m = [u for u in uids if any(rkey and (rkey in (d or "").replace("区域", "") or (d or "").replace("区域", "") in rkey) for d in (dept_cache.get(u) or []))]
        if m: return m
        m = [u for u in uids if any(daqu and daqu in (d or "") for d in (dept_cache.get(u) or []))]
        return m or uids

    enriched = {}
    for k, v in raw_mapping.items():
        daqu, region = k.split("|", 1)
        eng_d = []
        for n in v["大区工程总_names"]:
            for u in pick(n, daqu, region):
                if u not in eng_d: eng_d.append(u)
        eng_p = []
        for n in v["省份工程总_names"]:
            for u in pick(n, daqu, region):
                if u not in eng_p: eng_p.append(u)
        enriched[k] = {**v, "大区工程总_userids": eng_d, "省份工程总_userids": eng_p}

    out_p = work_path(plan, "langya_mapping.json")
    out_p.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {out_p}")
    return out_p


if __name__ == "__main__":
    from scripts._common import load_plan
    main(load_plan(sys.argv[1]))
