#!/usr/bin/env bash
# xinchuang-pkg-probe 主入口
# Usage: run.sh --scanner <ip> --nodes <ip1,ip2,...> [--scanner-key <path>] [--node-key <path>] [--batch <key>] [--dry-run]
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
PROBE_SH="$SKILL_DIR/probe_versions.sh"

SCANNER_KEY="${HOME}/.ssh/mjqegova-ed25519"
NODE_KEY='~/.ssh/qijian_key'
BATCH=""
DRY_RUN=0
RESULT_DIR="${HOME}/.xinchuang-pkg-probe/runs"

while [ $# -gt 0 ]; do
  case "$1" in
    --scanner) SCANNER="$2"; shift 2 ;;
    --nodes) NODES="$2"; shift 2 ;;
    --scanner-key) SCANNER_KEY="$2"; shift 2 ;;
    --node-key) NODE_KEY="$2"; shift 2 ;;
    --batch) BATCH="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --result-dir) RESULT_DIR="$2"; shift 2 ;;
    -h|--help) grep '^# ' "$0" | sed 's/^# //'; exit 0 ;;
    *) echo "未知参数: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$SCANNER" ] || [ -z "$NODES" ]; then
  echo "用法: $0 --scanner <ip> --nodes <ip1,ip2,...> [选项]" >&2
  exit 2
fi
[ -f "$SCANNER_KEY" ] || { echo "扫描机密钥不存在: $SCANNER_KEY" >&2; exit 3; }
[ -f "$PROBE_SH" ] || { echo "probe_versions.sh 缺失: $PROBE_SH" >&2; exit 3; }

mkdir -p "$RESULT_DIR"
RUN_ID="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="$RESULT_DIR/$RUN_ID"
mkdir -p "$RUN_DIR"
RAW="$RUN_DIR/probe_raw.txt"
PARSED="$RUN_DIR/parsed.json"
RESULT="$RUN_DIR/result.json"

echo "[+] 推 probe 脚本到扫描机 $SCANNER..." >&2
scp -i "$SCANNER_KEY" -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=accept-new -q \
  "$PROBE_SH" "root@$SCANNER:/tmp/probe_versions.sh"

echo "[+] 扫描机驱动节点跑 probe..." >&2
NODES_SPACE="$(echo "$NODES" | tr ',' ' ')"
ssh -i "$SCANNER_KEY" -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
  "root@$SCANNER" "
    for ip in $NODES_SPACE; do
      echo \"########## NODE \$ip ##########\"
      timeout 90 ssh -i $NODE_KEY -o IdentitiesOnly=yes -o BatchMode=yes \
        -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new \
        root@\$ip 'bash -s' < /tmp/probe_versions.sh 2>&1
      sleep 3
    done
  " > "$RAW"

echo "[+] 解析探测结果..." >&2
python3 "$SCRIPT_DIR/parse_probe.py" "$RAW" > "$PARSED"

OS_KEY=$(python3 -c "import json,sys; print(json.load(open(r'$PARSED','r',encoding='utf-8')).get('os_key','unknown'))")
echo "[+] 检测到 OS: $OS_KEY" >&2

UPDATE_ARGS=()
[ "$DRY_RUN" = 1 ] && UPDATE_ARGS+=("--dry-run")
[ -n "$BATCH" ] && UPDATE_ARGS+=("--batch" "$BATCH")

echo "[+] 推 AI 表格..." >&2
python3 "$SCRIPT_DIR/update_aitable.py" --input "$PARSED" "${UPDATE_ARGS[@]}" > "$RESULT"

echo "" >&2
echo "============ 运行汇总 ============" >&2
cat "$RESULT" >&2
echo "" >&2
echo "原始: $RAW" >&2
echo "解析: $PARSED" >&2
echo "汇总: $RESULT" >&2
echo "AI 表格: https://alidocs.dingtalk.com/i/nodes/G1DKw2zgV2RXpGMNTPNyZ0XYVB5r9YAn" >&2
