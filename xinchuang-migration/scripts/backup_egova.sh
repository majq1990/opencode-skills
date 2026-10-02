#!/bin/bash
# =============================================================================
#  多目录备份脚本 (Linux)
#  - 备份目录: /egova/web -> /egova/backup/web
#              /egova/apps -> /egova/backup/app
#  - 日志目录: /egova/backup/logs (统一一份)
#  - 压缩格式: tar.gz (全备份, 不排除任何文件)
#  - 执行后自动转后台, 无需在终端等待
# =============================================================================

set -euo pipefail

# ---------- 可调参数 ----------
# 格式: "源目录:目标目录"  (加几个都行)
BACKUP_DIRS=(
    "/egova/web:/egova/backup/web"
    "/egova/apps:/egova/backup/app"
)
LOG_DIR="/egova/backup/logs"        # 日志目录 (统一一份)
KEEP_COUNT=15                        # 保留最近几份备份 (0 = 不清理)
LOG_KEEP_DAYS=0                      # 日志保留天数 (0 = 不清理)

# ---------- 初始化路径 ----------
DATE=$(date +%Y%m%d_%H%M%S)
LOCK_FILE="/tmp/backup_egova.lock"
LOG_FILE="${LOG_DIR}/backup_$(date +%Y%m%d).log"

mkdir -p "${LOG_DIR}"

# ---------- 后台运行检测 ----------
if [ "${BACKGROUND:-0}" != "1" ]; then
    BACKGROUND=1 nohup bash "$0" >> /dev/null 2>&1 &
    echo "========================================"
    echo "  备份已在后台启动, 无需等待"
    echo "  实时查看: tail -f ${LOG_FILE}"
    echo "========================================"
    exit 0
fi

# ========== 以下为后台实际执行 ==========

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

# 清理过期日志 (LOG_KEEP_DAYS=0 则跳过)
if [ "${LOG_KEEP_DAYS}" -gt 0 ]; then
    find "${LOG_DIR}" -maxdepth 1 -name "backup_*.log" -mtime +${LOG_KEEP_DAYS} -delete 2>/dev/null
fi

log "===== 开始备份 (共 ${#BACKUP_DIRS[@]} 个目录) ====="

# ---------- 锁, 防并发 ----------
cleanup() { rm -f "${LOCK_FILE}"; }
trap cleanup EXIT

if [ -e "${LOCK_FILE}" ]; then
    log "ERROR: 已有备份进程在运行 (lock: ${LOCK_FILE})"
    exit 1
fi
touch "${LOCK_FILE}"

# ---------- 逐个目录备份 ----------
FAIL_COUNT=0
SUCCESS_COUNT=0

for ENTRY in "${BACKUP_DIRS[@]}"; do
    SRC_DIR="${ENTRY%%:*}"
    DST_DIR="${ENTRY##*:}"
    DIR_NAME=$(basename "${DST_DIR}")
    ARCHIVE_NAME="${DIR_NAME}_${DATE}.tar.gz"
    ARCHIVE_PATH="${DST_DIR}/${ARCHIVE_NAME}"

    mkdir -p "${DST_DIR}"

    # 前置检查
    if [ ! -d "${SRC_DIR}" ]; then
        log "ERROR: 源目录不存在: ${SRC_DIR}, 跳过"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        continue
    fi

    # 磁盘空间
    SRC_SIZE_MB=$(du -sm "${SRC_DIR}" 2>/dev/null | awk '{print $1}')
    DST_AVAIL_MB=$(df -m "${DST_DIR}" | tail -1 | awk '{print $4}')
    log "[${DIR_NAME}] ${SRC_DIR} (${SRC_SIZE_MB} MB) -> ${ARCHIVE_PATH}"
    log "[${DIR_NAME}] 目标剩余: ${DST_AVAIL_MB} MB"

    if [ "${DST_AVAIL_MB}" -lt $((SRC_SIZE_MB / 2 + 500)) ]; then
        log "[${DIR_NAME}] WARN: 剩余空间可能不足, 继续执行..."
    fi

    # 打包
    START_TS=$(date +%s)
    if tar -czf "${ARCHIVE_PATH}" \
            -C "$(dirname "${SRC_DIR}")" "$(basename "${SRC_DIR}")" 2>>"${LOG_FILE}"; then
        END_TS=$(date +%s)
        ARCHIVE_SIZE=$(du -h "${ARCHIVE_PATH}" | awk '{print $1}')
        log "[${DIR_NAME}] 打包完成 | 大小: ${ARCHIVE_SIZE} | 耗时: $((END_TS - START_TS))s"
    else
        log "[${DIR_NAME}] ERROR: 备份失败"
        rm -f "${ARCHIVE_PATH}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        continue
    fi

    # 校验
    if [ ! -s "${ARCHIVE_PATH}" ]; then
        log "[${DIR_NAME}] ERROR: 备份文件为空或异常"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        continue
    fi

    # 清理旧备份
    if [ "${KEEP_COUNT}" -gt 0 ]; then
        ls -1t "${DST_DIR}"/${DIR_NAME}_*.tar.gz 2>/dev/null \
            | tail -n +$((KEEP_COUNT + 1)) \
            | while read -r f; do
                log "[${DIR_NAME}] 清理旧备份: $(basename "${f}")"
                rm -f "${f}"
            done
    fi

    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
done

# ---------- 汇总 ----------
log "----------------------------------------"
TOTAL=${#BACKUP_DIRS[@]}
if [ "${FAIL_COUNT}" -eq 0 ]; then
    log "全部备份成功 (${SUCCESS_COUNT}/${TOTAL})"
    log "备份成功"
else
    log "备份完成, 但有 ${FAIL_COUNT} 个目录失败 (${SUCCESS_COUNT}/${TOTAL} 成功)"
    log "备份失败"
fi
