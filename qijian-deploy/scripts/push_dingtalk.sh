#!/bin/bash
# 钉钉推送 helper
# 用法：push_dingtalk.sh "<标题>" "<正文>"
# 自动在正文首行加 #oneinstall 标签（钉钉机器人关键词过滤需要此 tag）
# 环境变量 DINGTALK_WEBHOOK_TOKEN 可覆盖内置 token（共享/CI 环境建议用环境变量注入）
set -eu

TOKEN="${DINGTALK_WEBHOOK_TOKEN:-6529f41717e2d0582db6d251c94a6bca7a1196eb8a029a0e9998975c57c245fc}"
URL="https://oapi.dingtalk.com/robot/send?access_token=${TOKEN}"

title="${1:-麒舰部署事件}"
body="${2:-}"

content="#oneinstall
${title}
$(date '+%Y-%m-%d %H:%M:%S')

${body}"

payload=$(jq -n --arg c "$content" '{msgtype:"text",text:{content:$c}}')
curl -s -H 'Content-Type: application/json' -X POST "$URL" -d "$payload"
echo
