#!/usr/bin/env bash
# 跑任何批量操作脚本前，先 source 这个脚本。
#
# 它做三件事：
#   1. 加载 API Key（按 环境变量 → scripts/.env.local 的顺序找）
#   2. 实测 key 是否真的能用（调一次 /users/current.json）
#   3. 打印当前登录身份，避免拿错人的 key 干活
#
# 用法：
#   source scripts/check_env.sh
#
# 校验失败会 exit 1，并打印首次配置指引。

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_setup_guide() {
  cat >&2 <<'EOF'

────────────────────────────────────────────────────────────
 需要先配置 API Key（只需做一次）
────────────────────────────────────────────────────────────

 1. 打开 Redmine 网页，登录你自己的账号
 2. 右上角「个人账户」 → 右侧「API 访问密钥」 → 点「显示」
    （没有的话点「生成」）
 3. 复制那串密钥，然后执行：

      cp scripts/.env.example scripts/.env.local
      vi scripts/.env.local        # 把 REDMINE_API_KEY 换成你的密钥

 4. 重新 source 本脚本：

      source scripts/check_env.sh

 说明：.env.local 只放在你本机，不要提交 git、不要发给别人。
       key 决定「操作人是谁」——批量操作的评论会记在你的名下。
EOF
}

# ---------------------------------------------------------------- 1. 找密钥
ENV_SOURCE=""
if [[ -n "${REDMINE_API_KEY:-}" ]]; then
  ENV_SOURCE="当前 shell 环境变量"
elif [[ -f "$SCRIPT_DIR/.env.local" ]]; then
  set -a; source "$SCRIPT_DIR/.env.local"; set +a
  ENV_SOURCE="$SCRIPT_DIR/.env.local"
fi

# ---------------------------------------------------------------- 2. 校验密钥
if [[ -z "${REDMINE_API_KEY:-}" ]]; then
  echo "❌ 未找到 REDMINE_API_KEY" >&2
  print_setup_guide
  exit 1
fi

if [[ ${#REDMINE_API_KEY} -lt 30 ]]; then
  echo "⚠️  REDMINE_API_KEY 长度异常（${#REDMINE_API_KEY} 字符，正常约 40 字符），可能没复制完整。"
fi

BASE="${REDMINE_BASE_URL:-https://faq.egova.com.cn:7787}"
BASE="${BASE%/}"

# ---------------------------------------------------------------- 3. 实测
TMPFILE=$(mktemp)
HTTP_CODE=$(curl -sS -o "$TMPFILE" -w "%{http_code}" \
  --max-time 15 \
  -H "X-Redmine-API-Key: $REDMINE_API_KEY" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36" \
  "$BASE/users/current.json" 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "❌ API Key 校验失败（HTTP $HTTP_CODE）" >&2
  case "$HTTP_CODE" in
    401) echo "   密钥不对或已失效 → 回 Redmine 个人账户重新复制，更新 $SCRIPT_DIR/.env.local" >&2 ;;
    403) echo "   被 WAF 拦截。确认 REDMINE_BASE_URL 是 https://faq.egova.com.cn:7787" >&2 ;;
    000) echo "   连不上服务器 → 检查网络 / 是否在公司内网或已连 VPN" >&2 ;;
    *)   echo "   响应片段：" >&2; head -3 "$TMPFILE" | sed 's/^/   /' >&2 ;;
  esac
  [[ -z "$ENV_SOURCE" ]] && print_setup_guide
  rm -f "$TMPFILE"
  exit 1
fi

# ---------------------------------------------------------------- 4. 就绪
LOGIN_NAME=$(jq -r '.user.firstname + " " + .user.lastname' "$TMPFILE" 2>/dev/null || echo "未知")
export REDMINE_LOGIN_NAME="$LOGIN_NAME"
export REDMINE_BASE_URL="$BASE"
echo "✅ 环境就绪：登录身份 $LOGIN_NAME | 地址 $BASE | 密钥来源 ${ENV_SOURCE:-未知}"
rm -f "$TMPFILE"
