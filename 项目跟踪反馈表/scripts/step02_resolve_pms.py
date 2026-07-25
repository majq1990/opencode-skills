"""Step 2：把 PM 姓名映射到钉钉 userId（含部门去歧）。

输入  : work_dir/projects.json
输出  : work_dir/pm_resolved.json   (姓名 → {userids, names, titles})
        work_dir/userid_to_depts.json
        work_dir/projects_with_userids.json   (每个项目按区域→部门匹配选最佳 userId)

铁律：ztoa OpenAPI 关闭了 user/department 接口，必须走 dws contact user。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts._common import call_dws, dws_ok, work_path


def search_userid(name: str) -> list[dict]:
    d, out, err = call_dws(["contact", "user", "search", "--query", name, "-y"], timeout=40)
    if not d:
        return []
    return d.get("result") or []


def fetch_user_depts(uids: list[str]) -> dict[str, list[str]]:
    if not uids:
        return {}
    d, out, err = call_dws(["contact", "user", "get", "--ids", ",".join(uids), "-y"], timeout=30)
    if not d:
        return {u: [] for u in uids}
    res: dict[str, list[str]] = {}
    for u in (d.get("result") or []):
        m = u.get("orgEmployeeModel") or {}
        uid = m.get("orgUserId")
        if uid:
            res[uid] = [dept.get("deptName") for dept in (m.get("depts") or []) if dept.get("deptName")]
    for u in uids:
        res.setdefault(u, [])
    return res


def main(plan: dict) -> Path:
    projects = json.loads(work_path(plan, "projects.json").read_text(encoding="utf-8"))
    unique_names = sorted({n for p in projects for n in p["pm_names"]})
    print(f"[step2] PM unique names: {len(unique_names)}")

    cache_p = work_path(plan, "pm_resolved.json")
    cache: dict[str, dict] = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {}

    todo = [n for n in unique_names if n not in cache]
    print(f"  need resolve: {len(todo)} (cached {len(cache)})")
    for i, n in enumerate(todo, 1):
        results = search_userid(n)
        matched = [u for u in results if (u.get("name") or "").strip() == n]
        if matched:
            cache[n] = {
                "userids": [u.get("userId") for u in matched],
                "fullmatch_count": len(matched),
                "names": [u.get("name") for u in matched],
                "titles": [u.get("title") for u in matched],
            }
        else:
            cache[n] = {"userids": [], "candidates": [
                {"name": u.get("name"), "title": u.get("title"), "userId": u.get("userId")}
                for u in results
            ]}
        if i % 25 == 0:
            cache_p.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  [progress] {i}/{len(todo)}")
        time.sleep(0.05)
    cache_p.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

    # 拿所有 userId 的部门
    dept_p = work_path(plan, "userid_to_depts.json")
    dept_cache: dict[str, list[str]] = json.loads(dept_p.read_text(encoding="utf-8")) if dept_p.exists() else {}
    all_uids = {u for v in cache.values() for u in (v.get("userids") or []) if u}
    todo_uids = [u for u in all_uids if u not in dept_cache]
    print(f"  need dept fetch: {len(todo_uids)}")
    B = 50
    for i in range(0, len(todo_uids), B):
        batch = todo_uids[i: i + B]
        dept_cache.update(fetch_user_depts(batch))
        if (i // B) % 2 == 1:
            dept_p.write_text(json.dumps(dept_cache, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(0.05)
    dept_p.write_text(json.dumps(dept_cache, ensure_ascii=False, indent=2), encoding="utf-8")

    # 按 (name, region) → 最佳 userIds
    def pick_best(name: str, region: str) -> list[str]:
        info = cache.get(name) or {}
        uids = info.get("userids") or []
        if len(uids) <= 1:
            return uids
        rkey = (region or "").replace("区域", "").strip()
        matched = [u for u in uids if any(rkey and (rkey in (d or "").replace("区域", "") or (d or "").replace("区域", "") in rkey) for d in (dept_cache.get(u) or []))]
        return matched or uids  # 区域去歧失败则全部保留

    out = []
    miss_count = 0
    for p in projects:
        all_uids: list[str] = []
        notes = []
        for n in p["pm_names"]:
            best = pick_best(n, p["区域"])
            if not best:
                notes.append(f"未匹配钉钉账号: {n}")
                miss_count += 1
            for u in best:
                if u not in all_uids:
                    all_uids.append(u)
        out.append({**p, "dingtalk_userids": all_uids, "pm_match_note": "; ".join(notes)})

    out_p = work_path(plan, "projects_with_userids.json")
    out_p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    have = sum(1 for x in out if x["dingtalk_userids"])
    print(f"  projects with userId: {have}/{len(out)}; pm not matched (累计): {miss_count}")
    print(f"  -> {out_p}")
    return out_p


if __name__ == "__main__":
    from scripts._common import load_plan
    main(load_plan(sys.argv[1]))
