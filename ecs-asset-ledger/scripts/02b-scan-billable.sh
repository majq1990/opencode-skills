#!/bin/bash
# 02b-scan-billable.sh - 其他后付费资源扫描
# 扫 EIP / 独立云盘 / RDS / Redis / SLB / NAT / OSS Bucket
# 输出：$LOG_DIR/other-billable.json

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

load_config || exit 1

OUT="$LOG_DIR/other-billable.json"
INIT='{"eip":[],"orphaned_eip":[],"disks":[],"orphaned_disks":[],"rds":[],"redis":[],"slb":[],"nat":[],"oss_buckets":[],"summary":{}}'
echo "$INIT" > "$OUT"

log_info "==== 02b-scan-billable.sh 开始 $(beijing_now) ===="

# ===== EIP =====
ALL_EIP="[]"
for region in $REGIONS; do
  RESP=$(scan_eip "$region")
  if [[ -z "$RESP" || "$RESP" == "null" ]]; then continue; fi
  TAGGED=$(echo "$RESP" | jq -c '[.[] | {
    eip_id: .AllocationId,
    ip_address: .IpAddress,
    region: "'"$region"'",
    status: .Status,
    instance_id: (.InstanceId // ""),
    instance_type: (.InstanceType // ""),
    bandwidth: .Bandwidth,
    internet_charge_type: .InternetChargeType,
    create_time: .AllocationTime,
    name: (.Name // "")
  }]')
  ALL_EIP=$(jq -s '.[0] + .[1]' <(echo "$ALL_EIP") <(echo "$TAGGED"))
done
# Orphaned EIP：未绑定实例（InstanceId 为空）或已删除
ORPHANED_EIP=$(echo "$ALL_EIP" | jq -c '[.[] | select(.instance_id == "" or .status == "Available")]')
log_info "EIP 总数=$(echo "$ALL_EIP" | jq 'length') 未绑定=$(echo "$ORPHANED_EIP" | jq 'length')"

# ===== 独立云盘 =====
ALL_DISK="[]"
for region in $REGIONS; do
  RESP=$(scan_disks "$region")
  if [[ -z "$RESP" || "$RESP" == "null" ]]; then continue; fi
  TAGGED=$(echo "$RESP" | jq -c '[.[] | select(.Portable == true) | {
    disk_id: .DiskId,
    region: "'"$region"'",
    category: .Category,
    size: .Size,
    status: .Status,
    instance_id: (.InstanceId // ""),
    device: (.Device // ""),
    name: (.DiskName // ""),
    create_time: .CreationTime,
    encrypted: .Encrypted
  }]')
  ALL_DISK=$(jq -s '.[0] + .[1]' <(echo "$ALL_DISK") <(echo "$TAGGED"))
done
# Orphaned disk：未挂载（InstanceId 为空）
ORPHANED_DISK=$(echo "$ALL_DISK" | jq -c '[.[] | select(.instance_id == "" or .status == "Available")]')
log_info "独立云盘 总数=$(echo "$ALL_DISK" | jq 'length') 未挂载=$(echo "$ORPHANED_DISK" | jq 'length')"

# ===== RDS =====
ALL_RDS="[]"
for region in $REGIONS; do
  RESP=$(scan_rds "$region")
  if [[ -z "$RESP" || "$RESP" == "null" ]]; then continue; fi
  TAGGED=$(echo "$RESP" | jq -c '[.[] | {
    db_instance_id: .DBInstanceId,
    region: "'"$region"'",
    engine: .Engine,
    db_instance_type: .DBInstanceType,
    db_instance_status: .DBInstanceStatus,
    pay_type: .PayType,
    create_time: .CreationTime,
    expire_time: .ExpireTime,
    instance_net_type: .InstanceNetworkType
  }]')
  ALL_RDS=$(jq -s '.[0] + .[1]' <(echo "$ALL_RDS") <(echo "$TAGGED"))
done
log_info "RDS 实例数=$(echo "$ALL_RDS" | jq 'length')"

# ===== Redis =====
ALL_REDIS="[]"
for region in $REGIONS; do
  RESP=$(scan_redis "$region")
  if [[ -z "$RESP" || "$RESP" == "null" ]]; then continue; fi
  TAGGED=$(echo "$RESP" | jq -c '[.[] | {
    instance_id: .InstanceId,
    instance_name: .InstanceName,
    region: "'"$region"'",
    status: .Status,
    instance_class: .InstanceClass,
    capacity: .Capacity,
    create_time: .CreateTime,
    expire_time: .EndTime,
    charge_type: .ChargeType
  }]')
  ALL_REDIS=$(jq -s '.[0] + .[1]' <(echo "$ALL_REDIS") <(echo "$TAGGED"))
done
log_info "Redis 实例数=$(echo "$ALL_REDIS" | jq 'length')"

# ===== SLB =====
ALL_SLB="[]"
for region in $REGIONS; do
  RESP=$(scan_slb "$region")
  if [[ -z "$RESP" || "$RESP" == "null" ]]; then continue; fi
  TAGGED=$(echo "$RESP" | jq -c '[.[] | select(.LoadBalancerStatus != "Inactive") | {
    load_balancer_id: .LoadBalancerId,
    load_balancer_name: .LoadBalancerName,
    region: "'"$region"'",
    address: .Address,
    status: .LoadBalancerStatus,
    internet_charge_type: .InternetChargeType,
    bandwidth: .Bandwidth,
    pay_type: .PayType,
    create_time: .CreateTime
  }]')
  ALL_SLB=$(jq -s '.[0] + .[1]' <(echo "$ALL_SLB") <(echo "$TAGGED"))
done
log_info "SLB 实例数=$(echo "$ALL_SLB" | jq 'length')"

# ===== NAT 网关 =====
ALL_NAT="[]"
for region in $REGIONS; do
  RESP=$(scan_nat "$region")
  if [[ -z "$RESP" || "$RESP" == "null" ]]; then continue; fi
  TAGGED=$(echo "$RESP" | jq -c '[.[] | select(.Status != "Deleted") | {
    nat_gateway_id: .NatGatewayId,
    name: .Name,
    region: "'"$region"'",
    status: .Status,
    spec: .Spec,
    business_status: .BusinessStatus,
    create_time: .CreationTime
  }]')
  ALL_NAT=$(jq -s '.[0] + .[1]' <(echo "$ALL_NAT") <(echo "$TAGGED"))
done
log_info "NAT 网关数=$(echo "$ALL_NAT" | jq 'length')"

# ===== OSS Bucket =====
OSS_RAW=$(scan_oss_buckets)
OSS_LIST=$(echo "$OSS_RAW" | sort -u | jq -R 'split("/") | {bucket_name: (.[2] // ""), region: "unknown"}' | jq -s '.')
log_info "OSS Bucket 数=$(echo "$OSS_RAW" | sort -u | wc -l)"

# ===== Summary =====
SUMMARY=$(jq -n \
  --argjson eip "$(echo "$ALL_EIP" | jq 'length')" \
  --argjson orph_eip "$(echo "$ORPHANED_EIP" | jq 'length')" \
  --argjson disk "$(echo "$ALL_DISK" | jq 'length')" \
  --argjson orph_disk "$(echo "$ORPHANED_DISK" | jq 'length')" \
  --argjson rds "$(echo "$ALL_RDS" | jq 'length')" \
  --argjson redis "$(echo "$ALL_REDIS" | jq 'length')" \
  --argjson slb "$(echo "$ALL_SLB" | jq 'length')" \
  --argjson nat "$(echo "$ALL_NAT" | jq 'length')" \
  --argjson oss "$(echo "$OSS_RAW" | sort -u | wc -l)" \
  '{
    eip: $eip, orphaned_eip: $orph_eip,
    disks: $disk, orphaned_disks: $orph_disk,
    rds: $rds, redis: $redis, slb: $slb, nat: $nat, oss_buckets: $oss
  }')

# 写最终 JSON
jq -n \
  --argjson eip "$ALL_EIP" \
  --argjson orph_eip "$ORPHANED_EIP" \
  --argjson disk "$ALL_DISK" \
  --argjson orph_disk "$ORPHANED_DISK" \
  --argjson rds "$ALL_RDS" \
  --argjson redis "$ALL_REDIS" \
  --argjson slb "$ALL_SLB" \
  --argjson nat "$ALL_NAT" \
  --argjson oss "$OSS_LIST" \
  --argjson summary "$SUMMARY" \
  '{
    eip: $eip,
    orphaned_eip: $orph_eip,
    disks: $disk,
    orphaned_disks: $orph_disk,
    rds: $rds,
    redis: $redis,
    slb: $slb,
    nat: $nat,
    oss_buckets: $oss,
    summary: $summary
  }' > "$OUT"

log_info "==== 02b-scan-billable.sh 完成 summary=$SUMMARY ===="