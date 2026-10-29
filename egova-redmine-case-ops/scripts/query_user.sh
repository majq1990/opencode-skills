#!/usr/bin/env bash
# 按姓名 / 拼音查 Redmine 用户，拿到 user_id（转派、指定指派人时要用）。
#
# 关键点：**离职人员默认查不到**（离职账号被 Redmine 锁定为 status=3，不在常规搜索结果里）。
# 本脚本在常规搜索为空时会自动再查一遍锁定账号，把「离职XXX」的人也能翻出来。
#
# 用法：
#   bash scripts/query_user.sh --q 张三
#   bash scripts/query_user.sh --q zhangsan       # 拼音/login 也行
#   bash scripts/query_user.sh --q 张三 --status all
#
# 输出：JSON（与 Redmine /users.json 同结构，便于被其它脚本解析）
#   {"total_count": 1, "users": [{"id": 8842, "login": "maweidong", ...}]}
#
# 环境变量：REDMINE_API_KEY（必填）、REDMINE_BASE_URL、EGOVA_USER_AGENT

set -euo pipefail

usage() {
  cat <<'EOF'
用法:
  query_user.sh --q KEYWORD [--limit N] [--status active|locked|all]

参数:
  --q       必填，姓名 / 拼音 / login，支持部分匹配
  --limit   返回条数上限，1~100，默认 20
  --status  active（默认，活跃账号）| locked（离职/锁定账号）| all（都查）
EOF
}

Q=""
LIMIT="20"
STATUS="active"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --q) Q="${2:-}"; shift 2 ;;
    --limit) LIMIT="${2:-}"; shift 2 ;;
    --status) STATUS="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if [[ -z "$Q" ]]; then echo "--q is required" >&2; usage >&2; exit 1; fi
if ! [[ "$LIMIT" =~ ^[0-9]+$ ]] || (( LIMIT < 1 || LIMIT > 100 )); then
  echo "--limit must be 1~100" >&2; exit 1
fi
case "$STATUS" in active|locked|all) ;; *) echo "--status 只能是 active/locked/all" >&2; exit 1 ;; esac

if [[ -z "${REDMINE_API_KEY:-}" ]]; then
  echo "❌ REDMINE_API_KEY 未设置，先执行：source scripts/check_env.sh" >&2
  exit 1
fi

BASE="${REDMINE_BASE_URL:-https://faq.egova.com.cn:7787}"
BASE="${BASE%/}"
UA="${EGOVA_USER_AGENT:-Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36}"

ENCODED_Q="$(python3 - <<'PY' "$Q"
import sys, urllib.parse
print(urllib.parse.quote(sys.argv[1], safe=''))
PY
)"

TMP_ACTIVE=$(mktemp); TMP_LOCKED=$(mktemp)
trap 'rm -f "$TMP_ACTIVE" "$TMP_LOCKED"' EXIT
echo '{"users":[]}' > "$TMP_ACTIVE"
echo '{"users":[]}' > "$TMP_LOCKED"

# 按 API key 取一个 URL 到文件；失败时保留空 users，不中断脚本
fetch_to() {
  local url="$1" out="$2"
  if ! curl --fail --silent --show-error --max-time 20 \
      -H "X-Redmine-API-Key: ${REDMINE_API_KEY}" \
      -H "User-Agent: ${UA}" \
      "$url" -o "$out" 2>/dev/null; then
    echo '{"users":[]}' > "$out"
  fi
  [[ -s "$out" ]] || echo '{"users":[]}' > "$out"
}

if [[ "$STATUS" == "active" || "$STATUS" == "all" ]]; then
  fetch_to "${BASE}/users/search.json?q=${ENCODED_Q}&limit=${LIMIT}" "$TMP_ACTIVE"
fi

ACTIVE_COUNT=$(python3 -c "import json,sys;print(len(json.load(open(sys.argv[1])).get('users',[])))" "$TMP_ACTIVE" 2>/dev/null || echo 0)

# 常规搜索为空时自动补查锁定账号（离职人员）；非管理员会拿不到，静默降级
if [[ "$STATUS" == "locked" || "$STATUS" == "all" || ( "$STATUS" == "active" && "$ACTIVE_COUNT" == "0" ) ]]; then
  fetch_to "${BASE}/users.json?status=3&name=${ENCODED_Q}&limit=${LIMIT}" "$TMP_LOCKED"
fi

python3 - "$TMP_ACTIVE" "$TMP_LOCKED" "$STATUS" <<'PY'
import json, sys
active_f, locked_f, mode = sys.argv[1], sys.argv[2], sys.argv[3]

def load(p):
    try:
        return json.load(open(p)).get("users", [])
    except Exception:
        return []

active, locked = load(active_f), load(locked_f)
# 常规搜索为空时会把锁定账号当作回落结果一并返回（脚本里已抓取）
use_locked = mode in ("locked", "all") or (mode == "active" and not active)
users = []
if mode in ("active", "all"):
    users += active
if use_locked:
    users += locked

seen, merged = set(), []
for u in users:
    if u.get("id") not in seen:
        seen.add(u.get("id"))
        merged.append(u)

print(json.dumps({"total_count": len(merged), "users": merged}, ensure_ascii=False))

if not merged:
    print("提示：没查到。试试用拼音/login（如 maweidong），或换个关键词。", file=sys.stderr)
elif mode == "active" and not active and locked:
    print(f"提示：常规搜索为空，已自动翻出 {len(locked)} 个离职/锁定账号（status=3）。", file=sys.stderr)
PY
