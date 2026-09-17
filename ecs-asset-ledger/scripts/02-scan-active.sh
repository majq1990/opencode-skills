#!/bin/bash
# 02-scan-active.sh - 在用扫描（无台账版）
# 扫所有 region 的 Running 实例，按实例名前缀粗分类
# 输出到 $LOG_DIR/active-summary.json

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

load_config || exit 1

OUT="$LOG_DIR/active-summary.json"
echo '{"by_category":{},"by_region":{},"by_spec":{},"total_running":0,"instances":[]}' > "$OUT"

log_info "==== 02-scan-active.sh 开始 $(beijing_now) ===="

# 收集所有 region 的 Running 实例
ALL_FILTERED="[]"
for region in $REGIONS; do
  log_info "扫 region=$region"
  RESP=$(list_region_instances "$region")
  if [[ -z "$RESP" || "$RESP" == "null" || "$RESP" == "[]" ]]; then
    continue
  fi

  FILTERED=$(echo "$RESP" | jq -c '[.[] | select(.Status=="Running") | {
    instance_id: .InstanceId,
    instance_name: .InstanceName,
    instance_type: .InstanceType,
    region: .RegionId,
    zone: .ZoneId,
    public_ip: (.PublicIpAddress.IpAddress[0] // .NetworkInterfaces.NetworkInterface[0].PrimaryIpAddress // ""),
    creation_time: .CreationTime,
    instance_charge_type: .InstanceChargeType,
    spot_strategy: .SpotStrategy
  }]')

  # 合并：两个数组相加（用 + 直接连接数组）
  ALL_FILTERED=$(jq -nc --argjson a "$ALL_FILTERED" --argjson b "$FILTERED" '$a + $b')
done

echo "$ALL_FILTERED" | jq '.' > "$LOG_DIR/active-instances.json"

# 一站式：分类 + 三种聚合 + 统计
# ALL_FILTERED 已经是单行 JSON 数组，不用 -s
SUMMARY=$(printf '%s' "$ALL_FILTERED" | jq -c '
  [.[] | .category = (
    (.instance_name // "" | tostring) |
    if startswith("qijian_") then "麒舰考核"
    elif startswith("xingqiao_") then "星桥考核"
    elif startswith("faq-") or startswith("qijian-deploy") or startswith("qijian-node") then "麒舰部署"
    elif startswith("wukong-") or startswith("wk-") then "悟空考核"
    else "其他/未命名"
    end
  )] as $arr |
  {
    by_category: ($arr | group_by(.category) | map({key: .[0].category, value: length}) | from_entries),
    by_region: ($arr | group_by(.region) | map({key: .[0].region, value: length}) | from_entries),
    by_spec: ($arr | group_by(.instance_type) | map({key: .[0].instance_type, value: length}) | from_entries),
    total_running: ($arr | length),
    instances: $arr
  }
')

echo "$SUMMARY" > "$OUT"
log_info "==== 02-scan-active.sh 完成 总 Running=$(echo "$SUMMARY" | jq '.total_running') ===="