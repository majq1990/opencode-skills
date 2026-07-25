# 部署前检查清单

## 一、主控服务器检查

### 1.1 操作系统
- [ ] 操作系统版本在支持列表内（见 `os-compatibility.md`）
- [ ] 系统架构确认（x86_64 或 ARM）
- [ ] 内核版本无已知兼容性问题

**验证命令**:
```bash
cat /etc/os-release
uname -m
```

### 1.2 系统配置
- [ ] 已使用 root 用户登录（或 sudo 权限）
- [ ] 磁盘空间充足（建议 ≥ 100GB）
- [ ] 内存充足（建议 ≥ 8GB）
- [ ] CPU 核心数充足（建议 ≥ 4 核）

**验证命令**:
```bash
whoami                              # 确认 root
df -h                               # 查看磁盘
free -h                             # 查看内存
nproc                               # 查看 CPU 核数
```

### 1.3 网络配置
- [ ] 主控服务器有静态 IP
- [ ] 可以 SSH 到自身（`ssh root@127.0.0.1`）
- [ ] 如果有互联网，可访问 `ntp.aliyun.com`（时间同步）

**验证命令**:
```bash
ip addr                             # 查看网卡 IP
ssh root@127.0.0.1 "echo ok"       # 自身 SSH
ping ntp.aliyun.com                 # 互联网连通性（可选）
```

### 1.4 时间同步
- [ ] 系统时间与标准时间一致（偏差 ≤ 5 分钟）

**验证命令**:
```bash
date
# 如果有互联网
ntpdate ntp.aliyun.com
```

### 1.5 防火墙
- [ ] 防火墙已放行 SSH 端口（默认 22）
- [ ] 如需本地源跨机访问，防火墙放行 7777 端口

**验证命令**:
```bash
# firewalld
firewall-cmd --list-ports

# ufw
ufw status
```

---

## 二、部署包检查

### 2.1 部署包完整性
- [ ] `oneinstall_v2` 目录结构完整
- [ ] `src/repo/` 目录下有对应操作系统的依赖包
- [ ] `src/bin/` 目录下有需要的二进制工具
- [ ] `src/web/` 目录下有应用包

**验证命令**:
```bash
ls -la install.sh
ls src/repo/
ls src/bin/
ls src/web/
```

### 2.2 脚本权限
- [ ] `install.sh` 有执行权限

**修复命令**:
```bash
chmod +x install.sh
```

### 2.3 依赖包检查
- [ ] 对应 OS 的 repo 目录下有足够数量的 rpm/deb 包

**检查命令**:
```bash
# CentOS/Kylin 等
ls src/repo/centos/ | wc -l        # 应该有大量 rpm 包
ls src/repo/kylin/ | wc -l

# Ubuntu
ls src/repo/ubuntu/ | wc -l
```

---

## 三、子控服务器检查（多机部署时）

### 3.1 网络连通性
- [ ] 主控可以 ping 通所有子控
- [ ] 主控可以 SSH 到所有子控（端口正确）
- [ ] 主控到子控的 SSH 免密可配置成功

**验证命令**:
```bash
# 从主控执行
ping {子控IP}
ssh -p {端口} root@{子控IP} "echo ok"
```

### 3.2 子控系统配置
- [ ] 子控操作系统在支持列表内（建议与主控相同或兼容）
- [ ] 子控已使用 root 用户或允许 root SSH 登录
- [ ] 子控磁盘空间充足

**验证命令**:
```bash
ssh root@{子控IP} "cat /etc/os-release"
ssh root@{子控IP} "df -h"
```

### 3.3 子控防火墙
- [ ] 子控防火墙放行主控的 SSH 连接
- [ ] 按需放行其他端口（MySQL 3306、Redis 6379 等）

---

## 四、服务器规划确认

### 4.1 规划确认
- [ ] 已确定部署模式（一站式/分布式/轻量化）
- [ ] 已规划各服务器的角色分配
- [ ] 已确认数据库方案（单机/主从）
- [ ] 已确认需要的微服务列表

### 4.2 资源规划确认
- [ ] 数据库服务器满足最低配置（8U32G，推荐 16U64G+ SSD）
- [ ] 应用服务器满足最低配置（4U16G，推荐 8U32G+）
- [ ] 磁盘 IO 满足要求（≥ 100 MB/s，推荐 ≥ 300 MB/s）
- [ ] 网络带宽满足要求（≥ 500 Mbps）

---

## 五、性能基线检查（推荐）

在正式部署前，建议运行基准检查：

```bash
# 方法1: 使用内置预检查脚本
./shell/tools/precheck.sh {目标服务器IP}

# 方法2: 使用菜单中的基准检查（需先完成 Ansible 安装）
./install.sh
# 选择 b，输入 Redis 连接信息
```

### 基线标准

| 检查项 | 区县级 | 一般地市 | 中心城市 |
|---|---|---|---|
| 网络带宽 | ≥ 500 Mbps | ≥ 1000 Mbps | ≥ 1000 Mbps |
| 磁盘 IO | ≥ 100 MB/s | ≥ 300 MB/s | ≥ 500 MB/s |
| CPU | ≥ 8 核 | ≥ 16 核 | ≥ 32 核 |
| 内存 | ≥ 32 GB | ≥ 64 GB | ≥ 128 GB |

---

## 六、数据库规划确认（如需信创数据库）

如需使用达梦/PostgreSQL/瀚高等信创数据库：

- [ ] 已确认目标数据库类型
- [ ] 已安装并启动数据库服务
- [ ] 已创建业务库和统计库实例
- [ ] 已创建数据库用户和 Schema
- [ ] 数据库服务器网络可达（从应用服务器可连接数据库端口）
- [ ] 防火墙已放行数据库端口

---

## 七、快速检查脚本

将以下内容保存为 `pre_check.sh`，在主控服务器上执行：

```bash
#!/bin/bash
echo "===== 部署前快速检查 ====="

# OS 检查
echo -e "\n[1] 操作系统"
cat /etc/os-release | grep -E "^(NAME|VERSION_ID)=" 
uname -m

# 用户检查
echo -e "\n[2] 当前用户"
whoami
if [ "$(whoami)" != "root" ]; then
    echo "⚠ 警告: 当前不是 root 用户！"
fi

# 磁盘检查
echo -e "\n[3] 磁盘空间"
df -h / | tail -1

# 内存检查
echo -e "\n[4] 内存"
free -h | head -2

# CPU 检查
echo -e "\n[5] CPU"
echo "核心数: $(nproc)"

# 时间检查
echo -e "\n[6] 系统时间"
date

# 部署包检查
echo -e "\n[7] 部署包"
if [ -f "install.sh" ]; then
    echo "✓ install.sh 存在"
else
    echo "⚠ install.sh 不存在！"
fi

# SSH 检查
echo -e "\n[8] SSH 自身连通性"
if ssh -o "StrictHostKeyChecking no" -o "ConnectTimeout=3" root@127.0.0.1 "echo ok" 2>/dev/null; then
    echo "✓ SSH 自身连通正常"
else
    echo "⚠ SSH 自身连通失败！"
fi

echo -e "\n===== 检查完成 ====="
```

执行：
```bash
chmod +x pre_check.sh
./pre_check.sh
```
