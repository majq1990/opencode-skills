#!/bin/bash
# =============================================================================
#  web 目录备份脚本 (Linux)
#  - 源目录:   /egova/web
#  - 目标目录: /egova/backup/web
#  - 日志目录: /egova/backup/logs
#  - 压缩格式: tar.gz (全备份, 不排除任何文件)
#  - 执行后自动转后台, 无需在终端等待
# =============================================================================

set -euo pipefail

# ---------- 可调参数 ----------
SRC_DIR="/egova/web"              # 备份源
DST_DIR="/egova/backup/web"       # 备份目标
LOG_DIR="/egova/backup/logs"      # 日志目录
KEEP_COUNT=15                      # 保留最近几份备份 (0 = 不清理)
LOG_KEEP_DAYS=0                    # 日志保留天数 (0 = 不清理)

# ---------- 初始化路径 ----------
DATE=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="web_${DATE}.tar.gz"
ARCHIVE_PATH="${DST_DIR}/${ARCHIVE_NAME}"
LOCK_FILE="/tmp/backup_web.lock"
LOG_FILE="${LOG_DIR}/backup_web_$(date +%Y%m%d).log"

mkdir -p "${DST_DIR}" "${LOG_DIR}"

# ---------- 后台运行检测 ----------
# 首次执行: 转 nohup 后台, 立即返回提示
# 后台执行: BACKGROUND=1, 继续往下跑真正的备份
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
    find "${LOG_DIR}" -maxdepth 1 -name "backup_web_*.log" -mtime +${LOG_KEEP_DAYS} -delete 2>/dev/null
fi

log "===== 开始备份 ====="

# ---------- 锁, 防并发 ----------
cleanup() { rm -f "${LOCK_FILE}"; }
trap cleanup EXIT

if [ -e "${LOCK_FILE}" ]; then
    log "ERROR: 已有备份进程在运行 (lock: ${LOCK_FILE})"
    exit 1
fi
touch "${LOCK_FILE}"

# ---------- 前置检查 ----------
if [ ! -d "${SRC_DIR}" ]; then
    log "ERROR: 源目录不存在: ${SRC_DIR}"
    exit 1
fi

# ---------- 磁盘空间预估 ----------
SRC_SIZE_MB=$(du -sm "${SRC_DIR}" 2>/dev/null | awk '{print $1}')
DST_AVAIL_MB=$(df -m "${DST_DIR}" | tail -1 | awk '{print $4}')
log "源目录: ${SRC_DIR} (${SRC_SIZE_MB} MB)"
log "目标: ${ARCHIVE_PATH}"
log "目标剩余空间: ${DST_AVAIL_MB} MB"

if [ "${DST_AVAIL_MB}" -lt $((SRC_SIZE_MB / 2 + 500)) ]; then
    log "WARN: 剩余空间可能不足, 继续执行..."
fi

# ---------- 执行备份 (全备份, 不排除) ----------
START_TS=$(date +%s)
if tar -czf "${ARCHIVE_PATH}" \
        -C "$(dirname "${SRC_DIR}")" "$(basename "${SRC_DIR}")" 2>>"${LOG_FILE}"; then
    END_TS=$(date +%s)
    ARCHIVE_SIZE=$(du -h "${ARCHIVE_PATH}" | awk '{print $1}')
    log "打包完成 | 大小: ${ARCHIVE_SIZE} | 耗时: $((END_TS - START_TS))s"
else
    log "ERROR: 备份失败, 详见上方日志"
    rm -f "${ARCHIVE_PATH}"
    exit 1
fi

# ---------- 校验 ----------
if [ ! -s "${ARCHIVE_PATH}" ]; then
    log "ERROR: 备份文件为空或异常"
    exit 1
fi

# ---------- 清理旧备份 ----------
if [ "${KEEP_COUNT}" -gt 0 ]; then
    ls -1t "${DST_DIR}"/web_*.tar.gz 2>/dev/null \
        | tail -n +$((KEEP_COUNT + 1)) \
        | while read -r f; do
            log "清理旧备份: $(basename "${f}")"
            rm -f "${f}"
        done
fi

# ---------- 最后一行: 备份成功 ----------
log "备份成功: ${ARCHIVE_PATH}"
