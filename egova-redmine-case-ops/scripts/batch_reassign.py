#!/usr/bin/env python3
"""批量转派指定用户（作为指派人）名下的 open 案件给接手人。

适用场景：某人（多为离职）名下的案件整批交给接手人，**不关心案件当前状态**。

行为：
  - 拉取指定 user_id 作为 assigned_to_id 的所有 open 案件（自动翻页，不会漏）
  - 过滤掉"已关闭"（status_id=5）；"已解决"（status_id=3）默认一并转派
    （离职人员名下多为已解决收尾态，不转的话接手人看不到这些历史）
  - 逐条 PUT 改 assigned_to_id 为接手人，**保持原 status_id 不变**，不触发流转模板
  - 写一条统一 opinion 作为评论

参数：
  --user-id        必填，原指派人 user_id（按 assigned_to_id 过滤）
  --to-user-id     必填，接收人 user_id
  --to-user-name   可选，接收人姓名（仅打印）
  --user-name      可选，原用户姓名（仅打印）
  --opinion        必填，统一备注
  --exclude-status 可选，额外排除的状态 ID，逗号分隔（比如 1=工程新建 想保留的）
                   默认排除 5（已关闭）。想保留"已解决"不转派，加 --exclude-status 3

示例：
  # 把张三名下所有案件转给李四
  python3 batch_reassign.py \
    --user-id 1234 --to-user-id 5678 \
    --to-user-name 李四 \
    --opinion "离职人员案件批量批转"

安全流程：默认先打印待转派清单并要一次确认；--dry-run 只看不提交；--yes 跳过确认。
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FORWARD_SCRIPT = SCRIPT_DIR / "issue_case_forward.py"

# 浏览器 UA，绕 Redmine 前置 WAF 的拦截
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/149.0.0.0 Safari/537.36"
)

# 默认排除的状态（这些不需要转派）
# 只排除"已关闭"；"已解决"默认一并转派（离职人员名下绝大多数是已解决收尾态）
DEFAULT_EXCLUDE_STATUS = {"5"}  # 已关闭


def load_env():
    """加载 REDMINE_API_KEY / REDMINE_BASE_URL。

    环境变量已有就用已有的（source scripts/check_env.sh 后就是这种情况），
    否则读脚本目录下的 .env.local（cp .env.example .env.local 后填写）。
    """
    if os.environ.get("REDMINE_API_KEY"):
        return
    candidates = [SCRIPT_DIR / ".env.local"]
    for env_file in candidates:
        if not env_file.exists():
            continue
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))
        return
    print("❌ 未找到密钥。请先执行 source scripts/check_env.sh，"
          f"或 cp scripts/.env.example {candidates[0]} 后填入 API Key", file=sys.stderr)
    sys.exit(1)


def api_headers() -> dict:
    return {
        "X-Redmine-API-Key": os.environ.get("REDMINE_API_KEY", ""),
        "User-Agent": os.environ.get("EGOVA_USER_AGENT", DEFAULT_USER_AGENT),
    }


def fetch_issues(user_id: int) -> list:
    """拉取该用户名下全部 open 案件（自动翻页，不会漏）。"""
    base = os.environ.get("REDMINE_BASE_URL", "https://faq.egova.com.cn:7787").rstrip("/")
    if not os.environ.get("REDMINE_API_KEY"):
        print("❌ REDMINE_API_KEY 未设置，先执行 source scripts/check_env.sh", file=sys.stderr)
        sys.exit(1)

    issues: list = []
    offset, page_size = 0, 100
    while True:
        params = [
            ("assigned_to_id", str(user_id)),
            ("status_id", "open"),
            ("limit", str(page_size)),
            ("offset", str(offset)),
            ("include", "custom_fields"),
        ]
        qs = "&".join(f"{k}={v}" for k, v in params)
        req = urllib.request.Request(f"{base}/issues.json?{qs}", headers=api_headers())
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        batch = data.get("issues", [])
        issues.extend(batch)
        total = int(data.get("total_count", len(issues)))
        offset += len(batch)
        if not batch or offset >= total:
            break
    return issues


def reassign_one(case_id: int, to_user_id: int, opinion: str) -> tuple[bool, str]:
    """调用 issue_case_forward.py --update-only 转派。"""
    cmd = [
        sys.executable, str(FORWARD_SCRIPT),
        "--case-id", str(case_id),
        "--update-only",
        "--assigned-to-id", str(to_user_id),
        "--opinion", opinion,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=os.environ)
    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "{}")
    except json.JSONDecodeError:
        result = {"ok": False, "status": 0, "body": proc.stdout[:200]}

    if result.get("status") == 200:
        return True, f"已转派给 user_id={to_user_id}"
    return False, f"HTTP {result.get('status')}: {result.get('body', '')[:200]}"


def main():
    parser = argparse.ArgumentParser(description="批量转派指定用户名下 open 案件")
    parser.add_argument("--user-id", type=int, required=True, help="原指派人 user_id")
    parser.add_argument("--to-user-id", type=int, required=True, help="接收人 user_id")
    parser.add_argument("--to-user-name", help="接收人姓名（仅打印用）")
    parser.add_argument("--user-name", help="原用户姓名（仅打印用）")
    parser.add_argument("--opinion", required=True, help="统一备注（写入 Redmine notes）")
    parser.add_argument("--exclude-status", help="额外排除的状态 ID，逗号分隔（默认只排除 5=已关闭；加 3 可保留\"已解决\"）")
    parser.add_argument("--dry-run", action="store_true", help="只拉取并打印待转派清单，不提交")
    parser.add_argument("--yes", action="store_true", help="跳过提交前的人工确认")
    args = parser.parse_args()

    load_env()

    user_label = f"{args.user_name} (id={args.user_id})" if args.user_name else f"user_id={args.user_id}"
    to_label = f"{args.to_user_name} (id={args.to_user_id})" if args.to_user_name else f"user_id={args.to_user_id}"
    print(f"🔍 拉取 {user_label} 名下 open 案件...")
    issues = fetch_issues(args.user_id)

    exclude = set(DEFAULT_EXCLUDE_STATUS)
    if args.exclude_status:
        exclude.update(s.strip() for s in args.exclude_status.split(","))

    # 过滤：状态 ID 不在排除集合中
    targets = [i for i in issues if str(i["status"]["id"]) not in exclude]
    skipped = [i for i in issues if str(i["status"]["id"]) in exclude]
    print(f"📊 总拉取 {len(issues)} 条 open 案件")
    print(f"   跳过 {len(skipped)} 条（状态在排除集合: {sorted(exclude)}，其中 3=已解决 5=已关闭）")
    print(f"   待转派 {len(targets)} 条 → {to_label}")

    # 按状态分布打印一下
    by_status = {}
    for it in targets:
        by_status.setdefault(it["status"]["name"], 0)
        by_status[it["status"]["name"]] += 1
    for s, n in sorted(by_status.items()):
        print(f"     {s}: {n} 条")

    if not targets:
        print("✅ 没有需要转派的案件")
        return

    print(f"\n将要转派的案件（共 {len(targets)} 条）：")
    for it in targets:
        print(f"  #{it['id']} [{it['status']['name']}] {it['subject'][:50]}")

    if args.dry_run:
        print("\n🔍 dry-run 模式，未提交。")
        return

    if not args.yes:
        answer = input(f"\n确认把以上 {len(targets)} 条转给 {to_label}？(y/N) ").strip().lower()
        if answer not in ("y", "yes"):
            print("已取消，未做任何修改。")
            return

    print(f"\n🚀 开始批量转派...\n")
    success, failed = 0, 0
    for it in targets:
        cid = it["id"]
        subject = it["subject"][:40]
        ok, msg = reassign_one(cid, args.to_user_id, args.opinion)
        if ok:
            print(f"  ✅ #{cid} [{it['status']['name']}] {subject} → {msg}")
            success += 1
        else:
            print(f"  ❌ #{cid} [{it['status']['name']}] {subject} → {msg}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"📊 完成：✅ 成功 {success} / ❌ 失败 {failed}")
    if failed:
        print(f"   失败案件需人工排查原因（典型：状态机联动校验 422）")
        sys.exit(1)


if __name__ == "__main__":
    main()
