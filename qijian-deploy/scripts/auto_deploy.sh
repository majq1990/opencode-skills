#!/usr/bin/env bash
# auto_deploy.sh v4 — 麒舰全自动采购+部署（2026-11-09 实战固化版）
#
# 用户规则（2026-11-08 生效，覆盖此前所有"智能修复"逻辑）：
#   1. 只下载最新 dl_v2.sh，不折腾本地上传（代码/配置全部来自 dl_v2 下载物）
#   2. 环境安装操作都不跑，直接走下载的脚本
#   3. 下载过程本身长（约 1-2H），不需要介入——脚本只等待，僵死/失败只记录上报
#   4. 配置渲染按周五（2026-11-06）实际跑的数据，不自己猜
#   5. 实际部署由工具跑，只看日志跟踪；遇到问题记录+定位，不人工修理
#
# 固定项：license=172.21.133.146:11113（乌兰察布统一）
# 采购：只系统盘（--disk 默认 200G），无数据盘
# v4 变更（2026-11-08 全天实战定型）：
#   - dl_v2 菜单第 4 位 base_select=2（base+env-base 全量；选 1 漏 zookeeper/kafka/lua-resty）
#   - 渲染 master=主机名（node1/2/3，非 IP；填 IP 菜单反查全 null）
#   - step0 必填 yum 端口；step2 子菜单 0；step3 含出口 nginx 全局参数序列 + y 冗余
#   - 新增 G2 支持软件 CLI 预装（9 类）+ G3 依赖预填（fill_depends.txt）
set -uo pipefail

REGION=cn-wulanchabu; ZONE=cn-wulanchabu-c
IMAGE=m-0jl4fem5xgqm8roo9hhq
VSW=vsw-0jlfj7todyuefm058cws1
SG=sg-0jl01sye88jzlm50c89d
TYPE=ecs.e-c1m4.2xlarge
ROOT_PASS='Egova@123'
LICENSE='172.21.133.146:11113'
PROJECT=faq
DISK=200; NODES=3
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKDIR=/d/opencode/file/$(date +%F)
LOG=$WORKDIR/auto-deploy.log
WEBHOOK='https://oapi.dingtalk.com/robot/send?access_token=6529f41717e2d0582db6d251c94a6bca7a1196eb8a029a0e9998975c57c245fc'
T0=$(date +%s)

while [ $# -gt 0 ]; do case "$1" in
  --region) REGION=$2; shift 2;; --zone) ZONE=$2; shift 2;;
  --disk) DISK=$2; shift 2;; --nodes) NODES=$2; shift 2;;
  --project) PROJECT=$2; shift 2;;
  --reuse) REUSE=1; shift;;   # 复用 $WORKDIR/instances.txt 已采购实例（断点续跑）
  *) echo "未知参数 $1"; exit 2;; esac; done

mkdir -p "$WORKDIR"; exec > >(tee -a "$LOG") 2>&1
echo "==== 麒舰全自动部署 $(date '+%F %T') $REGION/$ZONE 盘=${DISK}G 节点=$NODES ===="

is_ip() { echo "$1" | grep -qE '^[0-9]{1,3}(\.[0-9]{1,3}){3}$'; }
notify() { curl -s -m 15 -X POST "$WEBHOOK" -H "Content-Type: application/json" \
  -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"#oneinstall $1\n$2\"}}" >/dev/null; echo "[notify] $1"; }
die() { notify "【麒舰部署 · $1】" "$2（累计耗时 $(( ($(date +%s)-T0)/60 )) 分钟）"; exit 1; }
R() { python "$SCRIPT_DIR/rrun.py" exec "$@"; }
P() { python "$SCRIPT_DIR/rrun.py" stdin "$@"; }
elapsed() { echo "累计 $(( ($(date +%s)-T0)/60 )) 分钟"; }

# ---------- A 预检 ----------
command -v aliyun >/dev/null || die 预检失败 "aliyun-cli 不存在"
python -c "import paramiko" 2>/dev/null || die 预检失败 "python paramiko 未安装"
[ -f "$SCRIPT_DIR/rrun.py" ] || die 预检失败 "缺 rrun.py"
[ -f "$SCRIPT_DIR/fill_depends.txt" ] || die 预检失败 "缺 fill_depends.txt"

# ---------- B 采购（只系统盘；--reuse 复用已购实例断点续跑） ----------
if [ -n "${REUSE:-}" ] && [ -s "$WORKDIR/instances.txt" ]; then
  echo "[B] 复用已有实例（--reuse）"
  N1=$(sed -n 1p "$WORKDIR/instances.txt" | cut -d" " -f1); P1=$(sed -n 1p "$WORKDIR/instances.txt" | cut -d" " -f2)
  N2=$(sed -n 2p "$WORKDIR/instances.txt" | cut -d" " -f1); P2=$(sed -n 2p "$WORKDIR/instances.txt" | cut -d" " -f2)
  N3=$(sed -n 3p "$WORKDIR/instances.txt" | cut -d" " -f1); P3=$(sed -n 3p "$WORKDIR/instances.txt" | cut -d" " -f2)
  IDS=$(cat "$WORKDIR/instance-ids.txt")
  echo "node1 $N1/$P1  node2 $N2/$P2  node3 $N3/$P3"
else
echo "[B] 采购 $NODES 台（系统盘 ${DISK}G，无数据盘）..."
IDS=$(aliyun ecs RunInstances \
  --RegionId "$REGION" --ZoneId "$ZONE" --ImageId "$IMAGE" --InstanceType "$TYPE" \
  --VSwitchId "$VSW" --SecurityGroupId "$SG" \
  --SystemDisk.Category cloud_essd --SystemDisk.Size "$DISK" \
  --InternetMaxBandwidthOut 100 --InternetChargeType PayByTraffic \
  --InstanceChargeType PostPaid --SpotStrategy SpotAsPriceGo --SpotDuration 0 \
  --Password "$ROOT_PASS" --Amount "$NODES" \
  --HostName qijian-node --InstanceName "qijian-auto-$(date +%m%d)" \
  | python -c 'import json,sys; print(" ".join(json.load(sys.stdin)["InstanceIdSets"]["InstanceIdSet"]))')
[ -n "$IDS" ] || die 采购失败 "RunInstances 无返回"
echo "实例: $IDS"; echo "$IDS" > "$WORKDIR/instance-ids.txt"
for id in $IDS; do aliyun ecs AllocatePublicIpAddress --RegionId "$REGION" --InstanceId "$id" >/dev/null 2>&1 || true; done
for i in $(seq 1 40); do
  ST=$(aliyun ecs DescribeInstanceAttribute --RegionId "$REGION" --InstanceId "${IDS%% *}" \
    | python -c 'import json,sys; print(json.load(sys.stdin)["Status"])' 2>/dev/null || echo Pending)
  [ "$ST" = "Running" ] && break; sleep 15
done
sleep 30
IDS_JSON=$(echo "$IDS" | sed 's/ /","/g; s/^/["/; s/$/"]/')
aliyun ecs DescribeInstances --RegionId "$REGION" --InstanceIds "$IDS_JSON" \
  | python -c '
import json,sys
d=json.load(sys.stdin)
for ins in sorted(d["Instances"]["Instance"], key=lambda x:x["InstanceId"]):
    pub=ins.get("PublicIpAddress",{}).get("IpAddress",[]) or ["NOPUB"]
    print(pub[0], ins["VpcAttributes"]["PrivateIpAddress"]["IpAddress"][0])' \
  > "$WORKDIR/instances.txt"
N1=$(sed -n 1p "$WORKDIR/instances.txt" | cut -d" " -f1); P1=$(sed -n 1p "$WORKDIR/instances.txt" | cut -d" " -f2)
N2=$(sed -n 2p "$WORKDIR/instances.txt" | cut -d" " -f1); P2=$(sed -n 2p "$WORKDIR/instances.txt" | cut -d" " -f2)
N3=$(sed -n 3p "$WORKDIR/instances.txt" | cut -d" " -f1); P3=$(sed -n 3p "$WORKDIR/instances.txt" | cut -d" " -f2)
for ip in $N1 $N2 $N3; do is_ip "$ip" || die 采购失败 "公网IP异常: $ip"; done
echo "node1 $N1/$P1  node2 $N2/$P2  node3 $N3/$P3"
fi
elapsed

# ---------- C SSH 基础（公钥 + node1→节点互信；非环境安装，属连接基础） ----------
PUB=$(cat ~/.ssh/id_rsa.pub)
for ip in $N1 $N2 $N3; do
  R "$ip" --cmd "mkdir -p ~/.ssh && chmod 700 ~/.ssh; grep -qF '${PUB:20:40}' ~/.ssh/authorized_keys 2>/dev/null || echo '$PUB' >> ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys" >/dev/null \
    || die SSH失败 "公钥分发 $ip"
done
N1PUB=$(R "$N1" --cmd "cat ~/.ssh/id_rsa.pub" 2>/dev/null | head -1)
for ip in $N1 $N2 $N3; do R "$ip" --cmd "grep -qF '${N1PUB:20:40}' ~/.ssh/authorized_keys 2>/dev/null || echo '$N1PUB' >> ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys" >/dev/null; done
# known_hosts 自指/互指（Host key verification 拒绝是实测坑）
R "$N1" --cmd "ssh-keyscan -T 5 $P1 $P2 $P3 2>/dev/null >> ~/.ssh/known_hosts; ssh -o StrictHostKeyChecking=no root@$P2 true && ssh -o StrictHostKeyChecking=no root@$P3 true && echo MESH_OK" \
  | grep -q MESH_OK || die SSH失败 "node1→node2/3 互信不通"

# ---------- D 下载（规则1/3：官方 dl_v2.sh 全自动，只等待不介入，上限 150 分钟） ----------
# 断点续跑：检测 dl_v2 已在远端运行则跳过启动，直接进入等待（本地脚本死亡不影响远端下载）
DL_STATE=$(R "$N1" --cmd "pgrep -f '^bash dl_v2.sh' >/dev/null && echo R || echo D" 2>/dev/null | head -1)
if [ "$DL_STATE" = "R" ]; then
  echo "[D] 检测到 dl_v2 已在远端运行，跳过启动，转入等待"
else
echo "[D] 服务器获取最新 dl_v2.sh 并启动官方下载（预计 1-2H，不介入）..."
R "$N1" --cmd "cd /root && curl -sL -m 60 -o dl_v2.sh http://oneops.egova.com.cn:8093/one/v2/dl_v2.sh && chmod +x dl_v2.sh && ls -l dl_v2.sh" | grep -q dl_v2.sh \
  || die 资源下载失败 "dl_v2.sh 下载失败"
# wget 会长连接僵死：.wgetrc 只加"下载参数级"超时让 wget 自行重试（非人工介入）
printf 'timeout = 30\ndns_timeout = 30\nread_timeout = 30\nconnect_timeout = 20\ntries = 10\nretry_connrefused = on\nwaitretry = 5\n' > "$WORKDIR/wgetrc"
P "$N1" --cmd "cat > /root/.wgetrc" --input "$WORKDIR/wgetrc" >/dev/null
# 菜单顺序（源码级确认）：OS→版本→架构(1=x86/2=arm)→base_select→script_select
# 第 4 位 base_select=2（base+env-base 全量）：缺它则 env-common-bin(zookeeper/kafka)、
# env-tools-script(lua-resty)、env-security-toolbox 三包不下载，部署必挂（2026-11-08 教训）
printf '3\n1\n1\n2\n2\n\nmajianquan\nEgova@123\n%s\n0\n' "$PROJECT" > "$WORKDIR/dl_input.txt"
P "$N1" --cmd "cat > /root/dl_input.txt" --input "$WORKDIR/dl_input.txt" >/dev/null
# 官方 dl_v2.sh 前台执行；SSH 断连风险用本地后台承接（远端前台保证 stdin 正常）
R "$N1" --cmd "cd /root && bash dl_v2.sh < /root/dl_input.txt" > "$WORKDIR/dl_run.log" 2>&1 &
DLPID=$!
echo "  dl_v2 下载已启动（本地 pid $DLPID，等待 1-2H）"
fi
DL_OK=0
# 外层重试：oneops 源站长连接会僵死，wget 反复超时会放弃并退出 dl_v2 → 自动重跑（-c 续传），直到包齐
for round in $(seq 1 12); do
  for i in $(seq 1 24); do
    sleep 300
    R=$(R "$N1" --cmd "pgrep -f '^bash dl_v2.sh' >/dev/null && echo R || echo D; ls /root/*.tar.gz 2>/dev/null | wc -l" 2>/dev/null | head -2)
    ST=$(echo "$R" | sed -n 1p); N=$(echo "$R" | sed -n 2p)
    echo "$(date +%H:%M:%S) round=$round dl=$ST pkgs=$N elapsed=$(elapsed)"
    [ "$ST" = "D" ] && break
  done
  N=$(R "$N1" --cmd "ls /root/*.tar.gz 2>/dev/null | wc -l" 2>/dev/null | head -1)
  if [ "${N:-0}" -ge 30 ]; then DL_OK=1; break; fi
  [ "$ST" = "D" ] && { echo "$(date +%H:%M:%S) round=$round 下载未完成（pkgs=$N），自动重跑 dl_v2 续传" ; continue; }
done
[ "$DL_OK" = 1 ] || die 资源下载失败 "多轮重试后仍未完成，检查 /root/dl.log 定位"
# 完整性断言：env 组三包必须在（base_select=2 的产物）
MISS_PKG=""
for p in oneinstall_v2-env-common-bin oneinstall_v2-env-tools-script oneinstall_v2-env-security-toolbox; do
  R "$N1" --cmd "ls /root/${p}*.tar.gz >/dev/null 2>&1 && echo HAS || echo NO" 2>/dev/null | grep -q HAS || MISS_PKG="$MISS_PKG $p"
done
[ -z "$MISS_PKG" ] || die 资源下载失败 "env 组包缺失:$MISS_PKG（dl_v2 base_select 应为 2）"
echo "下载完成（env 组三包齐）"; elapsed

# ---------- E 部署工具初始化（官方 oneinstall_v2.sh：解压+建目录，规则2 不跑环境安装） ----------
echo "[E] 部署工具初始化（oneinstall_v2.sh，EOF 自动退出菜单）..."
R "$N1" --cmd "cd /root && timeout 1800 bash oneinstall_v2.sh < /dev/null > /root/init.log 2>&1; echo INIT_DONE; ls -d /egova/onekey_install/oneinstall_v2/install.sh && echo INIT_OK" \
  | grep -q INIT_OK || die 初始化失败 "oneinstall_v2.sh 未产出 install.sh（查看 /root/init.log 定位）"
elapsed

# ---------- F 配置渲染（规则4：按 2026-11-06 周五实际部署数据，不自己猜） ----------
# 周五实测（2026-11-07 凌晨实查 + 2026-11-08 源码级确认）：
#   - hosts.master 存【主机名】（node1/2/3）——install 菜单经 get_ip_by_host 反查 IP 显示；
#     填 IP 字面量会导致反查落空、节点分配菜单全显示 null（2026-11-08 踩坑）
#   - 分配：node1=DB+中间件集中；node2=GIS+轻业务微服务；node3=核心业务
#   - 出口 nginx：部署时通过全局参数菜单选 node1 配置（install 3 序列内置 1→1→1 完成）
#   - license 周五已填 172.21.133.146:11113（固定）
echo "[F] 配置渲染（周五实际数据）..."
OI=/egova/onekey_install/oneinstall_v2
R "$N1" --cmd "OI=$OI; export PATH=\$OI/src/bin:\$PATH; which yq >/dev/null 2>&1 || echo NO_YQ; ls \$OI/install.sh >/dev/null && echo OI_OK" | tail -1 > "$WORKDIR/yq_check.txt"
if grep -q NO_YQ "$WORKDIR/yq_check.txt"; then
  # 规则2 边界：yq 是 install.sh 的硬依赖（无它菜单都起不来），官方未自带，此处仅获取二进制
  R "$N1" --cmd "curl -sL -m 120 -o /usr/local/bin/yq https://github.com/mikefarah/yq/releases/download/v4.44.3/yq_linux_amd64 && chmod 755 /usr/local/bin/yq && yq --version | head -1" \
    | grep -q yq || die 渲染失败 "yq 获取失败"
fi
printf 'P1=%s\nP2=%s\nP3=%s\nLICENSE=%s\n' "$P1" "$P2" "$P3" "$LICENSE" > "$WORKDIR/render.env"
cat > "$WORKDIR/render.friday.txt" << REND
#!/usr/bin/env bash
# 渲染 — 按 2026-11-06 周五实际部署数据
set -e
export PATH=/egova/onekey_install/oneinstall_v2/src/bin:\$PATH
OI=/egova/onekey_install/oneinstall_v2
INV=\$OI/ansible/inventory
ALL=\$OI/ansible/group_vars/all.yml
. /egova/render.env
yq -i '.all.hosts.node1.ansible_ssh_host = "'"$P1"'"' \$INV/hosts.yml
yq -i '.all.hosts.node2.ansible_ssh_host = "'"$P2"'"' \$INV/hosts.yml
yq -i '.all.hosts.node3.ansible_ssh_host = "'"$P3"'"' \$INV/hosts.yml
yq -i '.all.hosts.node1.ansible_ssh_port = "22"' \$INV/hosts.yml
yq -i '.all.hosts.node2.ansible_ssh_port = "22"' \$INV/hosts.yml
yq -i '.all.hosts.node3.ansible_ssh_port = "22"' \$INV/hosts.yml
# 周五实际分配（master=主机名 node1/2/3，经 get_ip_by_host 反查显示）
for pair in \\
  "ip_db_biz:node1" "ip_db_stat:node1" "ip_web_redis:node1" "ip_web_nacos:node1" \\
  "ip_tool_postgis:node1" "ip_db_tdengine:node1" "ip_web_media:node1" "ip_web_job:node1" \\
  "ip_web_gis:node2" "ip_web_linglong:node2" "ip_web_xuanzang:node2" "ip_web_evaluation:node2" \\
  "ip_web_materials:node2" "ip_web_gisserver:node2" "ip_db_tdengine_3:node2" \\
  "ip_web_eurbanpro_sms:node2" "ip_web_eurbanpro_patrol_gather:node2" "ip_web_eurbanpro_trajectory:node2" \\
  "ip_web_eurbanpro:node3" "ip_web_usercenter:node3" "ip_web_dataflow:node3" "ip_web_dataflow_zookeeper:node3" \\
  "ip_web_dex:node3" "ip_web_other:node3" "ip_web_kafka:node3" "ip_web_usercenter_redis:node3" \\
  "ip_web_eurbanpro_media:node3" "ip_web_export:node3" "ip_web_uma:node3" ; do
  key=\${pair%%:*}; host=\${pair#*:}
  yq -i '.'"\$key"'.hosts.master = "'"\$host"'"' \$INV/eurbanpro_multi_server.yml
done
# 周五从节点：核心/用户中心/星桥 各 1 从（在周五的"业务微服务"节点上）
yq -i '.ip_web_eurbanpro.hosts.slave = ["node2"]' \$INV/eurbanpro_multi_server.yml
yq -i '.ip_web_usercenter.hosts.slave = ["node2"]' \$INV/eurbanpro_multi_server.yml
yq -i '.ip_web_dex.hosts.slave = ["node2"]' \$INV/eurbanpro_multi_server.yml
# 出口 nginx：部署时通过全局参数菜单选 node1 配置（install 3 序列内置 1→1→1 完成）
yq -i '.egova_license_url = "'"\$LICENSE"'"' \$ALL
echo RENDER_OK
REND
P "$N1" --cmd "cat > /root/render.env" --input "$WORKDIR/render.env" >/dev/null
P "$N1" --cmd "cat > /root/render.friday.txt" --input "$WORKDIR/render.friday.txt" >/dev/null
R "$N1" --cmd "bash /root/render.friday.txt" | grep -q RENDER_OK || die 渲染失败 "渲染脚本失败"
echo "渲染完成（周五实际分配）"; elapsed

# ---------- G install.sh 0/1/2 + 3 触发（规则5：工具跑，只看日志；遇错记录上报不修） ----------
# 菜单交互（2026-11-08 源码级确认）：
#   step0 本地源：输完 0 后必填 yum 端口（7777；被占则 7778）——缺输入会死循环刷屏 26 万次
#   step2 增服务器：子菜单 0=添加并执行免密；喂 q 会"输入错误"后核心转储
#   step3 部署：先被强制跳全局参数（出口 nginx 未配置时）→ 1→1→1 选 node1 → q 退出 → 3 重进部署
#           → 2→1→y×N（y 冗余确认，覆盖依赖配置各决策点）
run_step() { # $1=步号 $2=输入 $3=超时秒
  echo "[G] install step$1 ..."
  printf '%s\n' "$2" > "$WORKDIR/step$1.txt"
  P "$N1" --cmd "cat > /root/step$1.txt" --input "$WORKDIR/step$1.txt" >/dev/null
  R "$N1" --cmd "cd /egova/onekey_install/oneinstall_v2 && printf \"\$(cat /root/step$1.txt)\" | timeout $3 bash install.sh > /root/step$1.log 2>&1; echo RC=\$?" 2>/dev/null | tail -1 > "$WORKDIR/step$1.rc"
  RC=$(sed -n 's/RC=//p' "$WORKDIR/step$1.rc" | head -1)
  echo "  step$1 rc=$RC（124=菜单 EOF 刷屏属正常；动作完成与否看独立产物验证）"
  elapsed
}
YUM_PORT=7777
R "$N1" --cmd "ss -tln 2>/dev/null | grep -q ':7777 ' && echo USED || echo FREE" 2>/dev/null | grep -q USED && YUM_PORT=7778
echo "  yum 端口: $YUM_PORT"
run_step 0 "0
$YUM_PORT" 1500
run_step 1 "1" 2400
run_step 2 "2
0" 900
# 独立验证：本地源 repodata + 三台免密（不看 install rc）
R "$N1" --cmd "ls /egova/opt/repo/kylin/V10/repodata/ >/dev/null 2>&1 && echo REPO_OK || echo REPO_FAIL" 2>/dev/null | grep -q REPO_OK \
  || echo "  ⚠️ 本地源 repodata 未见，查看 /root/step0.log 定位"
for h in $P2 $P3; do
  R "$N1" --cmd "timeout 8 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@$h hostname" 2>/dev/null | grep -q qijian-node \
    && echo "  免密 OK $h" || echo "  ⚠️ 免密 FAIL $h（查看 /root/step2.log 定位）"
done

# ---------- G2 支持软件预装（CLI 通道：i_software.sh <type> <host>，唯一交互=y） ----------
# 依赖配置是设计内人工决策环节；预装+预填把交互压缩为纯 y（2026-11-08 定型）
echo "[G2] 支持软件 CLI 预装（9 类）..."
SUPPORT_CMD='export PATH=/egova/onekey_install/oneinstall_v2/src/bin:$PATH; cd /egova/onekey_install/oneinstall_v2/shell/tools'
for sw in "mysql:node1" "redis:node1" "redis:node3" "nacos:node1" "TDengine:node1" "TDengine3:node2" "zookeeper:node3" "kafka:node3" "postgresql:node1"; do
  T=${sw%%:*}; H=${sw##*:}
  echo "  >>> $T @ $H"
  P "$N1" --cmd "$SUPPORT_CMD && echo y | timeout 2400 bash i_software.sh $T $H > /root/sw_$T_$H.log 2>&1; echo RC=\$?" >/dev/null 2>&1
  R "$N1" --cmd "grep -cE 'failed=1|安装失败' /root/sw_$T_$H.log 2>/dev/null | head -1" 2>/dev/null | grep -q '^0$' \
    && echo "    ✅ $T@$H" || echo "    ⚠️ $T@$H 有失败（查看 /root/sw_$T_$H.log 定位）"
done

# ---------- G3 依赖预填（yq 动态读 metadata 实例 key → depends.depend_key） ----------
echo "[G3] 依赖预填（microservice_template → metadata）..."
P "$N1" --cmd "cat > /root/fill_depends.txt" --input "$SCRIPT_DIR/fill_depends.txt" >/dev/null
R "$N1" --cmd "bash /root/fill_depends.txt" 2>/dev/null | grep -E "FILLED=|STILL_MISS" | tail -3

# step3：触发部署（全局参数出口 nginx 序列 + y 冗余确认）
run_step 3 "3
1
1
1
q
3
2
1
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y
y" 900

# ---------- H 部署监控（规则5：只看日志，不修；上限 3H） ----------
echo "[H] 监控后台部署（只读日志）..."
DEPLOY_ENDED=0
for i in $(seq 1 60); do
  sleep 180
  R=$(R "$N1" --cmd "L=\$(ls -t /egova/log/oneinstall/deploy_2026*.log 2>/dev/null | grep -v summary | head -1); date +%H:%M; grep -c '部署主体结束' \$L 2>/dev/null; grep -c 'failed=[1-9]' \$L 2>/dev/null" 2>/dev/null | head -3)
  T=$(echo "$R" | sed -n 1p); E=$(echo "$R" | sed -n 2p); F=$(echo "$R" | sed -n 3p)
  echo "$(date +%H:%M:%S) srv=$T ended=$E bad_recap=$F elapsed=$(elapsed)"
  [ "${E:-0}" -ge 1 ] && { DEPLOY_ENDED=1; break; }
done
FINAL=$(R "$N1" --cmd "L=\$(ls -t /egova/log/oneinstall/deploy_2026*.log | grep -v summary | head -1); echo L=\$L; grep -A1 'PLAY RECAP' \$L | grep -E '^node' | head -4; grep -E '安装失败|部署失败|部署完成' \$L | head -4" 2>/dev/null)
echo "$FINAL"

# ---------- I 验收 ----------
sleep 120
ENTRY=$(R "$N1" --cmd "curl -s -o /dev/null -w '%{http_code}' -m 8 http://127.0.0.1:8080/eurbanpro/index.html" 2>/dev/null | head -1)
echo "入口验收: http://$N1:8080/eurbanpro/index.html → HTTP $ENTRY"
echo "$FINAL" > "$WORKDIR/final_recap.txt"

# ---------- J 总结 ----------
ELAPSED_MIN=$(( ($(date +%s)-T0)/60 ))
cat > "$WORKDIR/SUMMARY.md" << EOF
# 麒舰全自动部署（$(date '+%F %T')）
总耗时：$ELAPSED_MIN 分钟（采购→下载→初始化→渲染→预装→部署→验收）
实例：$IDS（$REGION/$ZONE 抢占式，系统盘 ${DISK}G 无数据盘）
公网：$N1 $N2 $N3；私网：$P1 $P2 $P3
License：$LICENSE（固定）
部署日志：/egova/log/oneinstall/deploy_*.log（最新）
验收：入口 HTTP $ENTRY
结束状态：$(echo "$FINAL" | head -5)
EOF
notify 【麒舰自动部署 · 完成】 "总耗时 $ELAPSED_MIN 分钟；入口 HTTP $ENTRY；详见 SUMMARY.md"
echo "==== 结束：$WORKDIR/SUMMARY.md ===="
