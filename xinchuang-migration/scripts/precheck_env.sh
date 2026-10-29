#!/bin/bash
# =============================================================================
#  precheck_env.sh — 信创迁移前环境预检（只读，不修改任何系统配置）
#  用法：bash precheck_env.sh            # 在目标 Linux 节点执行
#  口径：PASS=满足；WARN=建议处理；FAIL=需先解决再迁移；INFO=现状记录
#  纪律：本脚本只读；修复动作一律由人按 SKILL.md 对应章节手工执行
# =============================================================================

PASS=0; WARN=0; FAIL=0

say()  { echo "$*"; }
ok()   { PASS=$((PASS+1)); echo "[PASS] $*"; }
warn() { WARN=$((WARN+1)); echo "[WARN] $*"; }
bad()  { FAIL=$((FAIL+1)); echo "[FAIL] $*"; }
info() { echo "[INFO] $*"; }

say "===== 信创迁移前环境预检 $(date '+%Y-%m-%d %H:%M:%S') ====="
say "主机: $(hostname 2>/dev/null) | 时间区: $(timedatectl show -p Timezone --value 2>/dev/null || date +%Z)"

# ---------- 1. OS 版本 ----------
if [ -r /etc/os-release ]; then
    . /etc/os-release
    ok "OS: ${PRETTY_NAME:-未知}（对照 config/site_profile.md 现场档位确认是否在支持列表）"
else
    bad "无法读取 /etc/os-release"
fi
if [ -r /etc/os-version ]; then
    info "os-version: $(cat /etc/os-version | tr '\n' ' ')"
fi

# ---------- 2. CPU 架构 ----------
ARCH=$(uname -m)
case "$ARCH" in
    x86_64|aarch64) ok "CPU 架构: ${ARCH}（达梦/金蝶安装包需与架构匹配）" ;;
    *)              warn "CPU 架构: ${ARCH}（非 x86_64/aarch64，安装包适配需确认）" ;;
esac

# ---------- 3. 内存与磁盘 ----------
MEM_GB=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}')
if [ -n "${MEM_GB}" ] && [ "${MEM_GB}" -ge 16 ]; then
    ok "内存: ${MEM_GB} GB"
else
    warn "内存: ${MEM_GB:-未知} GB（达梦+金蝶+基础组件建议 ≥16G）"
fi
SWAP_MB=$(free -m 2>/dev/null | awk '/^Swap:/{print $2}')
if [ -n "${SWAP_MB}" ] && [ "${SWAP_MB}" -gt 0 ]; then
    ok "Swap: ${SWAP_MB} MB"
else
    warn "未启用 Swap（达梦官方建议配置 swap）"
fi
for D in / /egova; do
    if [ -d "$D" ]; then
        AVAIL=$(df -BG "$D" 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G')
        if [ -n "$AVAIL" ] && [ "$AVAIL" -ge 50 ]; then
            ok "磁盘 ${D}: 可用 ${AVAIL}G"
        else
            warn "磁盘 ${D}: 可用 ${AVAIL:-未知}G（部署+备份建议 ≥50G）"
        fi
    else
        info "目录 ${D} 不存在（新机器属正常；达梦规划路径见 SKILL.md 阶段三）"
    fi
done

# ---------- 4. dmdba 用户（阶段三前置）----------
if id dmdba >/dev/null 2>&1; then
    ok "dmdba 用户已存在（uid=$(id -u dmdba) gid=$(id -g dmdba)）"
else
    info "dmdba 用户未创建（达梦部署时创建；禁止 root 安装）"
fi

# ---------- 5. 文件打开数 ----------
NOFILE=$(ulimit -n 2>/dev/null)
if [ -z "${NOFILE}" ]; then
    warn "无法读取 ulimit -n"
elif [ "${NOFILE}" -ge 65536 ]; then
    ok "文件打开数: ${NOFILE}"
else
    warn "文件打开数: ${NOFILE}（达梦/金蝶建议 ≥65536，limits.conf 见 SKILL.md 阶段三）"
fi

# ---------- 6. 端口占用（5236=达梦 6848=金蝶控制台 8080=默认应用）----------
if command -v ss >/dev/null 2>&1; then
    for P in 5236 6848 8080; do
        if ss -ltn 2>/dev/null | awk '{print $4}' | grep -q ":${P}$"; then
            info "端口 ${P}: 已被占用（复用前先确认归属）"
        else
            ok "端口 ${P}: 空闲"
        fi
    done
else
    warn "无 ss 命令，端口检查跳过"
fi

# ---------- 7. SELinux / 防火墙（现状记录）----------
if command -v getenforce >/dev/null 2>&1; then
    MODE=$(getenforce 2>/dev/null)
    info "SELinux: ${MODE}（Enforcing 时达梦/金蝶异常需现场评估策略）"
fi
if command -v systemctl >/dev/null 2>&1; then
    FW=$(systemctl is-active firewalld 2>/dev/null)
    info "firewalld: ${FW:-unknown}（active 时迁移窗口需放行 5236/6848 及应用端口）"
fi

# ---------- 8. oneops 可达性（一键部署 dl_v2.sh 前置）----------
if getent hosts oneops.egova.com.cn >/dev/null 2>&1; then
    ok "oneops.egova.com.cn 可解析: $(getent hosts oneops.egova.com.cn | awk '{print $1}' | head -1)"
else
    warn "oneops.egova.com.cn 无法解析（政务网常态）——按 config/site_profile.md 在 /etc/hosts 写入现场 oneops 地址"
fi

# ---------- 9. Python3（采集服务 dmPython 前置）----------
if command -v python3 >/dev/null 2>&1; then
    ok "python3: $(python3 --version 2>&1)（statgather 切达梦需 dmPython，版本对照 testOne.sh）"
else
    warn "无 python3（采集服务 dmPython 依赖）"
fi

# ---------- 汇总 ----------
say "----------------------------------------"
say "汇总: PASS ${PASS} / WARN ${WARN} / FAIL ${FAIL}"
if [ "${FAIL}" -gt 0 ]; then
    say "结论: 存在 FAIL 项，先解决再启动迁移"
else
    say "结论: 无阻断项（WARN 项建议迁移窗口前处理）"
fi
exit 0
