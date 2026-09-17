#!/bin/bash
# 01-scan-release.sh - 释放核对（无台账版）
# 扫所有 region 的所有实例，调 AutoReleaseTime，标出：
#   - 已过期未释放（AutoReleaseTime 已过但实例仍 Running）
#   - 即将到期（< 24h）
#   - 野实例（PostPaid 运行超 WILDCARD_INSTANCE_DAYS 天，无 AutoReleaseTime）
# 输出到 $LOG_DIR/release-anomalies.json

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

load_config || exit 1

NOW_EPOCH=$(date +%s)
EXPIRY_THRESHOLD_SEC=$((24 * 3600))
ANOM_OUT="$LOG_DIR/release-anomalies.json"
echo "[]" > "$ANOM_OUT"

log_info "==== 01-scan-release.sh 开始 $(beijing_now) ===="

for region in $REGIONS; do
  log_info "扫 region=$region"
  RESP=$(list_region_instances "$region")
  if [[ -z "$RESP" || "$RESP" == "null" || "$RESP" == "[]" ]]; then
    continue
  fi

  echo "$RESP" | jq -c '.[]' | while IFS= read -r inst; do
    IID=$(echo "$inst" | jq -r '.InstanceId')
    INAME=$(echo "$inst" | jq -r '.InstanceName // ""')
    STATUS=$(echo "$inst" | jq -r '.Status')
    CTYPE=$(echo "$inst" | jq -r '.InstanceChargeType')
    CREATION=$(echo "$inst" | jq -r '.CreationTime')
    PUBIP=$(echo "$inst" | jq -r '.PublicIpAddress.IpAddress[0] // .NetworkInterfaces.NetworkInterface[0].PrimaryIpAddress // ""')

    # 跳过非 Running（Stopped/Pending 不算"未释放"）
    if [[ "$STATUS" != "Running" ]]; then
      continue
    fi

    ART=$(get_auto_release_time "$region" "$IID")

    # 判定
    RS=""
    if [[ -n "$ART" && "$ART" != "null" && "$ART" != "" ]]; then
      ART_EPOCH=$(iso_to_epoch "$ART")
      REMAIN=$((ART_EPOCH - NOW_EPOCH))
      if [[ $REMAIN -le 0 ]]; then
        RS="已过期未释放"
      elif [[ $REMAIN -le $EXPIRY_THRESHOLD_SEC ]]; then
        REMAIN_H=$((REMAIN / 3600))
        REMAIN_M=$(( (REMAIN % 3600) / 60 ))
        RS="即将到期(<24h)"
      fi
    else
      # 无 AutoReleaseTime：PostPaid 运行超 N 天 = 野实例
      if [[ "$CTYPE" == "PostPaid" ]]; then
        AGE=$(instance_age_days "$CREATION")
        if [[ "$AGE" != "-1" && $AGE -ge $WILDCARD_INSTANCE_DAYS ]]; then
          RS="野实例(无AutoRelease且运行${AGE}天)"
        fi
      fi
    fi

    # 异常入列
    if [[ -n "$RS" ]]; then
      jq --arg iid "$IID" \
         --arg iname "$INAME" \
         --arg region "$region" \
         --arg status "$STATUS" \
         --arg ctype "$CTYPE" \
         --arg pubip "$PUBIP" \
         --arg art "$ART" \
         --arg rs "$RS" \
         '. += [{instance_id:$iid, instance_name:$iname, region:$region,
                  status:$status, charge_type:$ctype, public_ip:$pubip,
                  auto_release_time:$art, release_status:$rs}]' \
         "$ANOM_OUT" > "$ANOM_OUT.tmp" && mv "$ANOM_OUT.tmp" "$ANOM_OUT"
      log_warn "异常 $IID ($INAME) → $RS"
    fi
  done
done

ANOM_COUNT=$(jq 'length' "$ANOM_OUT")
log_info "==== 01-scan-release.sh 完成 异常数=$ANOM_COUNT ===="