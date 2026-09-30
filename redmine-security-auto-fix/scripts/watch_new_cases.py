#!/usr/bin/env python3
"""值守驱动：发现新的安全案件（tracker 26），逐案产出修复方案草稿。

只产草稿——发布仍走 pending_mcp_publish、通知仍被抑制，最终发布与通知
必须由人工执行 finalize_publication.py（skill 安全约束）。

用法：
  python scripts/watch_new_cases.py --days 2 --limit 5 --state <state.json> --digest <digest.md>

状态文件记录已处理的案件号，重复执行自动跳过；检索命中大模型限流
（429/too many requests）时按约定等 8 分钟重试。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from similar_assist_bridge import SimilarAssistBridge  # noqa: E402

RATE_LIMIT_WAIT_S = 8 * 60


def load_state(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"processed": {}}


def run_case(issue_id: int, output_dir: Path, repo_path: str) -> dict:
    """跑单案件，返回结果摘要。限流时等 8 分钟后重试一次。"""
    for attempt in (1, 2, 3):
        started = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, "-u", "process_issue.py", str(issue_id),
                 "--output-dir", str(output_dir), "--similar-assist", repo_path],
                cwd=str(SCRIPTS), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=3600,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"TIMEOUT after {time.time() - started:.0f}s"}
        tail = (proc.stdout + "\n" + proc.stderr).lower()
        if "429" in tail or "too many requests" in tail or "限流" in tail:
            print(f"[rate-limit] {issue_id} 命中限流，等 {RATE_LIMIT_WAIT_S // 60} 分钟后重试",
                  file=sys.stderr, flush=True)
            time.sleep(RATE_LIMIT_WAIT_S)
            continue
        plan = output_dir / f"{issue_id}_fix_plan.md"
        if proc.returncode == 0 and plan.exists():
            enriched = output_dir / f"{issue_id}_enriched.json"
            data = json.loads(enriched.read_text(encoding="utf-8")) if enriched.exists() else {}
            vulns = data.get("vulns") or []
            return {
                "ok": True,
                "seconds": round(time.time() - started),
                "vuln_classes": len(vulns),
                "pending_web": sum(
                    1 for v in vulns if (v.get("web_search") or {}).get("required")
                ),
                "title": (data.get("dingtalk_document") or {}).get("title", ""),
            }
        return {"ok": False, "error": (proc.stdout + proc.stderr)[-400:]}
    return {"ok": False, "error": "限流重试耗尽"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=2, help="回看天数")
    parser.add_argument("--limit", type=int, default=5, help="单次最多处理几个新案件")
    parser.add_argument("--tracker-id", type=int, default=26)
    parser.add_argument("--output-dir", default=r"D:\opencode\_archive\skill-watch")
    parser.add_argument("--state", default=r"D:\opencode\_archive\skill-watch\watch_state.json")
    parser.add_argument("--digest", default=r"D:\opencode\_archive\skill-watch\digest_latest.md")
    parser.add_argument("--similar-assist", default=r"D:\git\redmine-similar-assist")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = Path(args.state)
    state = load_state(state_path)

    bridge = SimilarAssistBridge(args.similar_assist)
    issues = bridge.list_recent_security_issues(args.days, args.tracker_id)
    fresh = [
        row for row in issues
        if str(row["id"]) not in state["processed"]
    ]
    print(f"近 {args.days} 天安全案件 {len(issues)} 个，未处理 {len(fresh)} 个，本轮处理前 {args.limit} 个",
          flush=True)

    results = []
    for row in fresh[: args.limit]:
        issue_id = int(row["id"])
        subject = str(row.get("subject") or "")[:60]
        print(f"[case] {issue_id} {subject}", flush=True)
        outcome = run_case(issue_id, output_dir, args.similar_assist)
        outcome["issue_id"] = issue_id
        outcome["subject"] = subject
        outcome["at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        state["processed"][str(issue_id)] = outcome
        results.append(outcome)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    ok_list = [r for r in results if r["ok"]]
    lines = [
        "# 安全案件方案草稿（值守产出）",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}　"
        f"本轮新处理：{len(results)} 个（成功 {len(ok_list)}）　"
        f"累计已处理：{len(state['processed'])} 个",
        "",
        "> 草稿仅为内部方案，未经人工确认不得发布；发布用 finalize_publication.py。",
        "",
    ]
    for r in results:
        if r["ok"] and r.get("vuln_classes", 0) > 0:
            lines.append(
                f"- ✅ #{r['issue_id']} {r['subject']} — {r['vuln_classes']} 类漏洞，"
                f"待补互联网搜索 {r['pending_web']} 条，用时 {r['seconds']}s"
            )
        elif r["ok"]:
            # 0 类漏洞 = 无附件或附件里解析不出条目（如漏洞写在正文/外平台），
            # 明确标出来让人工接手，不装作正常完成
            lines.append(
                f"- ⚠️ #{r['issue_id']} {r['subject']} — 无附件可解析（漏洞可能在案件"
                f"正文或外链平台），需人工确认，用时 {r['seconds']}s"
            )
        else:
            lines.append(f"- ❌ #{r['issue_id']} {r['subject']} — 失败：{r.get('error', '')[:160]}")
    digest = Path(args.digest)
    digest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"digest: {digest}", flush=True)
    return 0 if len(ok_list) == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
