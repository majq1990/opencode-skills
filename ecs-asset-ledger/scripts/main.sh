#!/bin/bash
# main.sh - cron 主入口
# 工作日（周一至周五）09:00 顺序跑：01 → 02 → 03

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

load_config || exit 1

log_info "==== ECS 资产台账 cron 开始 $(beijing_now) ===="

bash "$SCRIPT_DIR/01-scan-release.sh"
bash "$SCRIPT_DIR/02-scan-active.sh"
bash "$SCRIPT_DIR/02b-scan-billable.sh"
bash "$SCRIPT_DIR/03-dingtalk-push.sh"

log_info "==== ECS 资产台账 cron 完成 ===="