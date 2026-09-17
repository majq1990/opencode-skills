#!/bin/bash
# 03-dingtalk-push.sh - 推送 ECS 资产日报到钉钉群
# 读 01 / 02 / 02b 产物，组装 Markdown，推送

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

load_config || exit 1

ANOM_FILE="$LOG_DIR/release-anomalies.json"
ACTIVE_FILE="$LOG_DIR/active-summary.json"
OTHER_FILE="$LOG_DIR/other-billable.json"

if [[ ! -f "$ANOM_FILE" || ! -f "$ACTIVE_FILE" ]]; then
  log_error "缺扫描产物：先跑 01-scan-release.sh 和 02-scan-active.sh"
  exit 1
fi

ANOM=$(cat "$ANOM_FILE")
ACTIVE=$(cat "$ACTIVE_FILE")
OTHER="{}"
[[ -f "$OTHER_FILE" ]] && OTHER=$(cat "$OTHER_FILE")

TODAY=$(beijing_today)
WEEKDAY=$(TZ='Asia/Shanghai' date "+%A")
TOTAL=$(echo "$ACTIVE" | jq -r '.total_running // 0')
ANOM_COUNT=$(echo "$ANOM" | jq 'length')

# ===== 组装 Markdown =====
MD="# egova 阿里云后付费资源日报 · ${TODAY} (${WEEKDAY})\n\n"

# ----- 段 1：ECS 释放异常 -----
if [[ "$ANOM_COUNT" -gt 0 ]]; then
  MD+="## ⚠️ ECS 释放异常 (${ANOM_COUNT} 条)\n\n"
  MD+="| 状态 | 实例ID | 实例名 | 区域 | 付费 | 公网IP | AutoReleaseTime |\n"
  MD+="|---|---|---|---|---|---|---|\n"

  while IFS= read -r row; do
    IID=$(echo "$row" | jq -r '.instance_id')
    INAME=$(echo "$row" | jq -r '.instance_name // "-"')
    REGION=$(echo "$row" | jq -r '.region // "-"')
    CTYPE=$(echo "$row" | jq -r '.charge_type // "-"')
    PUBIP=$(echo "$row" | jq -r '.public_ip // "-"')
    ART=$(echo "$row" | jq -r '.auto_release_time // "-"')
    RS=$(echo "$row" | jq -r '.release_status')
    MD+="| ⚠️ ${RS} | ${IID} | ${INAME} | ${REGION} | ${CTYPE} | ${PUBIP} | ${ART} |\n"
  done < <(echo "$ANOM" | jq -r 'sort_by(
    if .release_status == "已过期未释放" then 0
    elif (.release_status | startswith("野实例")) then 1
    elif .release_status == "即将到期(<24h)" then 2
    else 3 end
  ) | .[] | @json')
  MD+="\n"
else
  MD+="## ✅ ECS 释放无异常\n\n"
fi

# ----- 段 2：ECS 在用清单 -----
MD+="## 📊 ECS 在用实例（合计 ${TOTAL} 台）\n\n"
if [[ "$TOTAL" -gt 0 ]]; then
  MD+="**按用途分类**：\n\n| 用途 | 数量 |\n|---|---|\n"
  while read -r line; do
    MD+="${line}\n"
  done < <(echo "$ACTIVE" | jq -r '.by_category | to_entries | sort_by(-.value) | .[] | "| \(.key) | \(.value) |"')

  MD+="\n**按区域**：\n\n| 区域 | 数量 |\n|---|---|\n"
  while read -r line; do
    MD+="${line}\n"
  done < <(echo "$ACTIVE" | jq -r '.by_region | to_entries | sort_by(-.value) | .[] | "| \(.key) | \(.value) |"')
fi

# ----- 段 3：其他后付费资源 -----
if [[ "$OTHER" != "{}" && "$OTHER" != "null" ]]; then
  MD+="\n## 💰 其他后付费资源\n\n"

  # EIP 明细
  ORPH_EIP=$(echo "$OTHER" | jq -c '.orphaned_eip // []')
  ORPH_EIP_N=$(echo "$ORPH_EIP" | jq 'length')
  EIP_TOTAL=$(echo "$OTHER" | jq -r '.summary.eip // 0')
  if [[ "$EIP_TOTAL" -gt 0 ]]; then
    MD+="**EIP**：总 ${EIP_TOTAL} 个，未绑定 ${ORPH_EIP_N} 个"
    if [[ "$ORPH_EIP_N" -gt 0 ]]; then
      MD+="（⚠️ 未绑定持续扣费）"
    fi
    MD+="\n\n| EIP | 区域 | 状态 | 带宽 | 绑定实例 |\n|---|---|---|---|---|\n"
    while read -r line; do
      MD+="${line}\n"
    done < <(echo "$OTHER" | jq -r '.eip[] | "| \(.eip_id) | \(.region) | \(.status) | \(.bandwidth // 0)M | \(if (.instance_id // "") == "" then "⚠️ 未绑定" else .instance_id end) |"')
    MD+="\n"
  fi

  # 独立云盘明细
  ORPH_DISK=$(echo "$OTHER" | jq -c '.orphaned_disks // []')
  ORPH_DISK_N=$(echo "$ORPH_DISK" | jq 'length')
  DISK_TOTAL=$(echo "$OTHER" | jq -r '.summary.disks // 0')
  if [[ "$DISK_TOTAL" -gt 0 ]]; then
    MD+="**独立云盘**：总 ${DISK_TOTAL} 个，未挂载 ${ORPH_DISK_N} 个"
    if [[ "$ORPH_DISK_N" -gt 0 ]]; then
      MD+="（⚠️ 未挂载持续扣费）"
    fi
    MD+="\n\n| 磁盘ID | 区域 | 类别 | 大小(GiB) | 状态 | 挂载实例 | 创建时间 |\n|---|---|---|---|---|---|---|\n"
    while read -r line; do
      MD+="${line}\n"
    done < <(echo "$OTHER" | jq -r '.disks[] | "| \(.disk_id) | \(.region) | \(.category) | \(.size) | \(.status) | \(if (.instance_id // "") == "" then "⚠️ 未挂载" else .instance_id end) | \(.create_time) |"')
    MD+="\n"
  fi

  # RDS
  RDS_N=$(echo "$OTHER" | jq -r '.summary.rds // 0')
  if [[ "$RDS_N" -gt 0 ]]; then
    MD+="**RDS**：${RDS_N} 个实例\n\n| 实例ID | 区域 | 引擎 | 类型 | 状态 | 计费 |\n|---|---|---|---|---|---|\n"
    while read -r line; do
      MD+="${line}\n"
    done < <(echo "$OTHER" | jq -r '.rds[] | "| \(.db_instance_id) | \(.region) | \(.engine) | \(.db_instance_type) | \(.db_instance_status) | \(.pay_type) |"')
    MD+="\n"
  fi

  # Redis
  REDIS_N=$(echo "$OTHER" | jq -r '.summary.redis // 0')
  if [[ "$REDIS_N" -gt 0 ]]; then
    MD+="**Redis**：${REDIS_N} 个实例\n\n| 实例ID | 名称 | 区域 | 规格 | 计费 |\n|---|---|---|---|---|\n"
    while read -r line; do
      MD+="${line}\n"
    done < <(echo "$OTHER" | jq -r '.redis[] | "| \(.instance_id) | \(.instance_name // "-") | \(.region) | \(.instance_class) \(.capacity)MB | \(.charge_type) |"')
    MD+="\n"
  fi

  # SLB
  SLB_N=$(echo "$OTHER" | jq -r '.summary.slb // 0')
  if [[ "$SLB_N" -gt 0 ]]; then
    MD+="**SLB**：${SLB_N} 个实例\n\n| SLB ID | 名称 | 区域 | 公网地址 | 状态 | 计费 |\n|---|---|---|---|---|---|\n"
    while read -r line; do
      MD+="${line}\n"
    done < <(echo "$OTHER" | jq -r '.slb[] | "| \(.load_balancer_id) | \(.load_balancer_name // "-") | \(.region) | \(.address // "-") | \(.status) | \(.pay_type) |"')
    MD+="\n"
  fi

  # NAT 网关
  NAT_N=$(echo "$OTHER" | jq -r '.summary.nat // 0')
  if [[ "$NAT_N" -gt 0 ]]; then
    MD+="**NAT 网关**：${NAT_N} 个\n\n| NAT ID | 名称 | 区域 | 状态 | 规格 | 业务状态 |\n|---|---|---|---|---|---|\n"
    while read -r line; do
      MD+="${line}\n"
    done < <(echo "$OTHER" | jq -r '.nat[] | "| \(.nat_gateway_id) | \(.name // "-") | \(.region) | \(.status) | \(.spec // "-") | \(.business_status) |"')
    MD+="\n"
  fi

  # OSS Bucket
  OSS_N=$(echo "$OTHER" | jq -r '.summary.oss_buckets // 0')
  if [[ "$OSS_N" -gt 0 ]]; then
    MD+="**OSS Bucket**：${OSS_N} 个\n\n| Bucket | 区域 |\n|---|---|\n"
    while read -r line; do
      MD+="${line}\n"
    done < <(echo "$OTHER" | jq -r '.oss_buckets[] | "| \(.bucket_name) | \(.region) |"')
    MD+="\n"
  fi
fi

# @ 人
if [[ -n "$AT_USERIDS" ]]; then
  MD+="\n\n@$(echo "$AT_USERIDS" | tr ',' ' ')"
fi

# 真实换行
MD=$(echo -e "$MD")

# 标题强制带关键词
dingtalk_push_markdown "egova 阿里云后付费日报-${TODAY}" "$MD"

log_info "==== 03-dingtalk-push.sh 完成 ===="