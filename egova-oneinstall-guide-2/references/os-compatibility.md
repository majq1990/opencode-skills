# 操作系统兼容性矩阵

## 一、支持的操作系统

| 操作系统 | 版本要求 | 架构 | 包管理器 | 状态 |
|---|---|---|---|---|
| **银河麒麟 V10** | SP3 | x86_64 / ARM | yum (dnf) | ✅ 完全支持 |
| **统信 UOS 20** | 1060e / 1060a / 1070a | x86_64 / ARM | apt (deb) | ✅ 完全支持 |
| **Ubuntu** | 20.04 LTS | x86_64 | apt | ✅ 完全支持 |
| **openEuler** | LTS 版本 | x86_64 / ARM | yum (dnf) | ✅ 完全支持 |
| **龙蜥 Anolis** | 全系列 | x86_64 | yum (dnf) | ✅ 完全支持 |
| **CentOS** | 7.x / 8.x | x86_64 | yum | ✅ 完全支持 |

## 二、版本检查细节

### 2.1 麒麟 V10
```bash
# 检查版本
cat /etc/.productinfo
# 需要包含 "SP3"

# 检查架构
uname -m
# x86_64 或 aarch64
```
**注意**: 非 SP3 版本可能缺少某些依赖包。

### 2.2 统信 UOS 20
```bash
# 检查版本
cat /etc/product-info | grep -E "1060e|1060a|1070a"
# 必须匹配其中一个

# 检查架构
uname -m
```

### 2.3 Ubuntu
```bash
# 检查版本
lsb_release -r
# 必须是 20.04

# 检查架构
uname -m
# 仅支持 x86_64
```

### 2.4 openEuler
```bash
# 检查版本（必须是 LTS）
cat /etc/os-release | grep LTS

# 检查架构
uname -m
```

### 2.5 Anolis
```bash
# 检查版本
cat /etc/os-release

# 注意: Anolis 7 使用 ansible（非 ansible-core）
# Anolis 非 7 版本使用 ansible-core + community collections
```

## 三、操作系统识别机制

系统通过 `tool_utils.sh` 中的 `get_distribution_info()` 函数识别操作系统，返回格式为 `{ID}_{VERSION}_{ARCH}`：

| 系统识别结果 | ID | VERSION | ARCH |
|---|---|---|---|
| `kylin_V10_x86` | kylin | V10 | x86 |
| `kylin_V10_arm` | kylin | V10 | arm |
| `uos_20_x86` | uos | 20 | x86 |
| `uos_20_arm` | uos | 20 | arm |
| `ubuntu_20_x86` | ubuntu | 20 | x86 |
| `openEuler_22_x86` | openEuler | 22 | x86 |
| `anolis_8_x86` | anolis | 8 | x86 |
| `centos_7_x86` | centos | 7 | x86 |

### 判断函数
```bash
is_kylin()    # 麒麟
is_uos()      # 统信
is_ubuntu()   # Ubuntu
is_centos()   # CentOS
is_openEuler()# 欧拉
is_anolis()   # 龙蜥
```

## 四、架构差异处理

### x86_64 vs ARM 主要差异
- 二进制文件不同（`src/bin/` 下按架构分类）
- 部分依赖包名称不同
- JDK 路径可能不同

### 系统脚本中的架构判断
```bash
if [ "$(uname -m)" == "x86_64" ]; then
  arch="x86"
else
  arch="arm"
fi
```

## 五、不支持的操作系统处理

如果运行 `install.sh` 时遇到不支持的操作系统，脚本会报错退出：
```
发现xxx不支持的操作系统，请检查系统版本
```

**解决方法**:
1. 确认操作系统版本在支持列表内
2. 联系技术支持评估是否可以适配
3. 适配需要修改:
   - `install.sh` 中的 `check_os_release()` 函数
   - `shell/tools/tool_utils.sh` 中的系统识别函数
   - 可能需要添加对应的仓库配置文件

## 六、各 OS 的包管理差异

| 操作系统 | 安装命令 | 源配置文件 | 源格式 |
|---|---|---|---|
| CentOS/Kylin/openEuler/Anolis | `yum install -y {pkg}` | `/etc/yum.repos.d/*.repo` | `[repo]\nname=\nbaseurl=\nenabled=1\ngpgcheck=0` |
| Ubuntu | `apt install -y {pkg}` | `/etc/apt/sources.list` | `deb http://IP:7777/ ubuntu main` |
| UOS | `apt install -y {pkg}` | `/etc/apt/sources.list` | 同 Ubuntu |

### 本地源配置文件模板

**yum 源** (`egova-oneinstall-local.repo`):
```ini
[egova-local]
name=Egova Local Repository
baseurl=http://{master_ip}:7777/repo/{os_name}
enabled=1
gpgcheck=0
```

**apt 源** (`egova-oneinstall-local.list`):
```
deb http://{master_ip}:7777/repo/ubuntu main
```

## 七、防火墙配置

各系统防火墙操作：

```bash
# firewalld (CentOS/Kylin/openEuler/Anolis)
firewall-cmd --add-port={port}/tcp --permanent
firewall-cmd --reload
firewall-cmd --list-ports

# ufw (Ubuntu/UOS)
ufw allow {port}/tcp
ufw status
```

**部署工具需要的端口**:

| 端口 | 用途 | 必须开放 |
|---|---|---|
| 22 | SSH | 主控↔子控 之间 |
| 7777 | 本地源 Nginx | 主控→子控 |
| 3306 | MySQL | 按需 |
| 6379 | Redis | 按需 |
| 8080 | 微服务/Tomcat | 按需 |
| 8848 | Nacos | 按需 |
| 80/443 | 出口 Nginx | 外部访问 |
