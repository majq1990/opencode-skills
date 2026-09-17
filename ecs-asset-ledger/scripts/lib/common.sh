#!/bin/bash
# common.sh - aliyun 封装 + 日志 + 配置加载 + 钉钉推送
# 所有脚本 source 本文件
set -u

# 用 LIB_DIR 而非 SCRIPT_DIR，避免覆盖调用方已定义的 SCRIPT_DIR
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$(dirname "$LIB_DIR")")"
CONFIG_FILE="${SKILL_DIR}/config.json"
LOG_DIR="${SKILL_DIR}/logs"

mkdir -p "$LOG_DIR"

log_ts() { date "+%Y-%m-%d %H:%M:%S"; }
log_info() { echo "[$(log_ts)] [INFO] $*" | tee -a "$LOG_DIR/skill.log"; }
log_warn() { echo "[$(log_ts)] [WARN] $*" | tee -a "$LOG_DIR/skill.log"; }
log_error() { echo "[$(log_ts)] [ERROR] $*" | tee -a "$LOG_DIR/skill.log"; }

load_config() {
  if [[ ! -f "$CONFIG_FILE" ]]; then
    log_error "config.json 不存在: $CONFIG_FILE"
    return 1
  fi
  WEBHOOK_URL=$(jq -r '.WEBHOOK_URL' "$CONFIG_FILE")
  WEBHOOK_KEYWORD=$(jq -r '.WEBHOOK_KEYWORD // "egova"' "$CONFIG_FILE")
  AT_USERIDS=$(jq -r '.AT_USERIDS // [] | join(",")' "$CONFIG_FILE")
  REGIONS=$(jq -r '.REGIONS // [] | join(" ")' "$CONFIG_FILE")
  WILDCARD_INSTANCE_DAYS=$(jq -r '.WILDCARD_INSTANCE_DAYS // 3' "$CONFIG_FILE")

  if [[ -z "$WEBHOOK_URL" || "$WEBHOOK_URL" == "null" ]]; then
    log_error "config.json 缺 WEBHOOK_URL"; return 1
  fi
  if [[ -z "$REGIONS" ]]; then
    log_warn "config.json 没配 REGIONS，默认 cn-beijing cn-wulanchabu"
    REGIONS="cn-beijing cn-wulanchabu"
  fi
  return 0
}

# ===== aliyun 封装 =====
# 注意：aliyun-cli 3.0+ 默认就是 JSON 输出，加 --output json 反而报错
# "bad flag format --output with field cols= required"
aliyun_ecs() {
  local args=("$@")
  local out
  out=$(aliyun ecs "${args[@]}" 2>&1)
  local rc=$?
  if [[ $rc -ne 0 ]]; then
    log_warn "aliyun ecs ${args[*]} 失败 rc=$rc: $out"
    return $rc
  fi
  echo "$out"
  return 0
}

# 列某 region 所有实例（JSON array）
list_region_instances() {
  local region="$1"
  aliyun ecs DescribeInstances \
    --RegionId "$region" \
    --MaxResults 100 \
    2>/dev/null | jq -c '.Instances.Instance // []'
}

# ===== 多产品 aliyun 封装 =====
aliyun_vpc() { aliyun vpc "$@" 2>&1; }
aliyun_rds() { aliyun rds "$@" 2>&1; }
aliyun_rkvstore() { aliyun r-kvstore "$@" 2>&1; }
aliyun_slb() { aliyun slb "$@" 2>&1; }
aliyun_oss_cli() { aliyun oss "$@" 2>&1; }

# ===== 资源扫描封装（每个函数负责扫一类资源，输出 JSON 行 array）=====

# EIP 列表（含绑定信息），region 限定
scan_eip() {
  local region="$1"
  aliyun vpc DescribeEipAddresses \
    --RegionId "$region" \
    2>/dev/null | jq -c '.EipAddresses.EipAddress // []'
}

# 独立云盘列表，region 限定
scan_disks() {
  local region="$1"
  aliyun ecs DescribeDisks \
    --RegionId "$region" \
    2>/dev/null | jq -c '.Disks.Disk // []'
}

# RDS 实例列表
scan_rds() {
  local region="$1"
  aliyun rds DescribeDBInstances \
    --RegionId "$region" \
    2>/dev/null | jq -c '.Items.DBInstance // []'
}

# Redis 实例列表
scan_redis() {
  local region="$1"
  aliyun r-kvstore DescribeInstances \
    --RegionId "$region" \
    2>/dev/null | jq -c '.Instances.KVStoreInstance // []'
}

# SLB 实例列表
scan_slb() {
  local region="$1"
  aliyun slb DescribeLoadBalancers \
    --RegionId "$region" \
    2>/dev/null | jq -c '.LoadBalancers.LoadBalancer // []'
}

# NAT 网关列表
scan_nat() {
  local region="$1"
  aliyun vpc DescribeNatGateways \
    --RegionId "$region" \
    2>/dev/null | jq -c '.NatGateways.NatGateway // []'
}

# OSS Bucket 列表（用 ossutil，失败降级为 aliyun oss）
scan_oss_buckets() {
  if command -v ossutil64 >/dev/null 2>&1; then
    ossutil64 ls oss:// --limit 1000 2>/dev/null | \
      awk '/oss:\/\//{print $NF}' | sort -u
    return
  fi
  if command -v ossutil >/dev/null 2>&1; then
    ossutil ls oss:// 2>/dev/null | \
      awk '/oss:\/\//{print $NF}' | sort -u
    return
  fi
  # 降级：遍历 region 查 GetService
  for region in cn-beijing cn-hangzhou cn-shanghai cn-shenzhen; do
    aliyun oss ls oss:// --region "$region" 2>/dev/null | \
      awk '/oss:\/\//{print $NF}' | sort -u
  done
}

# 查询 AutoReleaseTime（UTC ISO8601 字符串，无则为空）
get_auto_release_time() {
  local region="$1"
  local iid="$2"
  local resp
  resp=$(aliyun ecs DescribeInstanceAutoReleaseTime \
    --RegionId "$region" \
    --InstanceId "$iid" \
    2>/dev/null)
  if [[ $? -ne 0 ]]; then
    echo ""
    return 1
  fi
  echo "$resp" | jq -r '.AutoReleaseTime // ""'
}

# ===== 钉钉推送 =====
dingtalk_push_markdown() {
  local title="$1"
  local md="$2"

  # 关键词兜底（钉钉机器人安全设置要求消息含关键词）
  if [[ -n "$WEBHOOK_KEYWORD" ]]; then
    if [[ "$title" != *"$WEBHOOK_KEYWORD"* && "$md" != *"$WEBHOOK_KEYWORD"* ]]; then
      md="$WEBHOOK_KEYWORD

$md"
    fi
  fi

  # @ 人
  local at_block='{"atMobiles":[],"atUserIds":[],"isAtAll":false}'
  if [[ -n "$AT_USERIDS" ]]; then
    at_block=$(echo "$AT_USERIDS" | jq -R 'split(",") | {atMobiles: [], atUserIds: ., isAtAll: false}')
  fi

  local payload
  payload=$(jq -n \
    --arg title "$title" \
    --arg text "$md" \
    --argjson at "$at_block" \
    '{msgtype:"markdown",markdown:{title:$title,text:$text},at:$at}')

  local resp
  resp=$(curl -s -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "$payload" 2>&1)
  local rc=$?
  log_info "钉钉推送 rc=$rc resp=$resp"
  return $rc
}

# ===== 时间工具 =====
beijing_now() { TZ='Asia/Shanghai' date "+%Y-%m-%dT%H:%M:%S+08:00"; }
beijing_today() { TZ='Asia/Shanghai' date "+%Y-%m-%d"; }
utc_now() { date -u "+%Y-%m-%dT%H:%M:%SZ"; }

# 加 N 天（输入：YYYY-MM-DD HH:MM:SS）
add_days_beijing() {
  local d="$1"
  local n="$2"
  TZ='Asia/Shanghai' date -d "$d +$n days" "+%Y-%m-%dT%H:%M:%S+08:00"
}

iso_to_epoch() {
  date -d "$1" +%s 2>/dev/null || echo 0
}

# 实例运行时长（天，按 CreationTime 算）
instance_age_days() {
  local creation="$1"
  local now_epoch
  now_epoch=$(date +%s)
  local c_epoch
  c_epoch=$(iso_to_epoch "$creation")
  if [[ "$c_epoch" == "0" ]]; then
    echo "-1"
    return
  fi
  echo $(( (now_epoch - c_epoch) / 86400 ))
}