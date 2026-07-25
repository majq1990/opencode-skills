<!--
模板使用约定（仅供模板维护者，HTML 注释不会渲染到钉钉）：
- 所有 {{...}} 占位符由 build_doc_md.py 渲染
- publish.py 在写入前会做正则扫描，发现残留占位符直接拒绝
-->
# {{VULN_TITLE}}

# 1\. 漏洞说明

## 1.1 漏洞编号

{{CVE_ID}}

## 1.2 漏洞概述

{{VULN_SUMMARY}}

参考链接：
{{REFERENCE_LINKS}}

## 1.3 漏洞影响范围

{{AFFECTED_RANGE_INTRO}}

{{AFFECTED_TABLE}}

**不受影响系统：**
{{NOT_AFFECTED_LIST}}

---

# 2\. 漏洞解决方案

## 2.1 漏洞排查方法

### 2.1.1 检查内核版本

```bash
uname -r
```

{{KERNEL_VERSION_RULE}}

### 2.1.2 检查内核配置

```bash
{{KERNEL_CONFIG_CHECK_CMD}}
```

{{KERNEL_CONFIG_RULE}}

### 2.1.3 检查模块加载情况

```bash
{{MODULE_CHECK_CMD}}
```

{{MODULE_CHECK_RULE}}

### 2.1.4 社区检测工具

推荐使用 **{{DETECT_TOOL_REPO}}**（{{DETECT_TOOL_LICENSE}}）作为自动化检测脚本。综合 GitHub 指标（Stars={{DETECT_TOOL_STARS}}、Forks={{DETECT_TOOL_FORKS}}、最近更新 {{DETECT_TOOL_UPDATED}}），同类工具中最活跃。

**工具特点：**
{{DETECT_TOOL_FEATURES}}

**下载渠道：**

| 渠道 | 地址 | 适用 |
|------|------|------|
| GitHub 仓库 | {{DETECT_TOOL_GITHUB}} | 海外、可访问 GitHub |
| GitHub Raw | {{DETECT_TOOL_RAW}} | 海外、可访问 GitHub |
| jsDelivr CDN | {{DETECT_TOOL_JSDELIVR}} | **国内可达，首选** |
| ghproxy 镜像 | {{DETECT_TOOL_GHPROXY}} | 国内备选 |
| 文档附件 | 见本节顶部附件块（如已上传） | 离线环境 |

> **离线/内网环境**：建议工程师在本文档钉钉客户端中点击「上传附件」直接将脚本作为附件块挂在本节顶部。

**使用方法：**

```bash
{{DETECT_TOOL_USAGE}}
```

> 注意：本脚本仅做检测，不执行修复。如检测结果为 VULNERABLE，请按本文 2.2 节执行内核升级。

---

## 2.2 各操作系统漏洞确认及修复说明

{{OS_FIX_SECTIONS}}

---

## 2.3 临时缓解措施

如无法立即升级内核，可采取以下临时缓解措施：

### 2.3.1 模块黑名单（通用 Linux）

```bash
echo "install {{MITIGATION_MODULE_NAME}} /bin/false" | sudo tee /etc/modprobe.d/disable-{{MITIGATION_MODULE_NAME}}.conf
sudo rmmod {{MITIGATION_MODULE_NAME}} 2>/dev/null
sudo reboot
lsmod | grep {{MITIGATION_MODULE_GREP}}
```

### 2.3.2 RHEL 家族（含基于 RHEL 的国产系统：麒麟服务器版、龙蜥等）

```bash
sudo grubby --update-kernel=ALL --args="initcall_blacklist={{MITIGATION_INITCALL}}"
sudo reboot
cat /proc/cmdline | grep {{MITIGATION_INITCALL}}
```

### 2.3.3 容器环境 - seccomp 阻断

{{MITIGATION_SECCOMP}}

### 2.3.4 验证缓解措施是否生效

```bash
sudo modprobe {{MITIGATION_MODULE_NAME}}
# 预期：modprobe: FATAL: Module {{MITIGATION_MODULE_NAME}} is blacklisted

lsmod | grep {{MITIGATION_MODULE_GREP}}
# 预期：无输出
```

---

## 2.4 离线环境补丁包下载清单

以下为各操作系统内核补丁包下载链接，适用于无法直接联网的离线环境，可下载后导入内网进行离线升级。

{{OFFLINE_PATCH_TABLE}}

### 2.4.1 离线升级通用步骤

```bash
# 步骤1：在有网络的机器上下载对应内核包
# 步骤2：将下载的包文件拷贝至离线服务器
# 步骤3：执行离线安装
# Debian/Ubuntu系
sudo dpkg -i linux-image-*.deb linux-headers-*.deb
# RHEL/CentOS系
sudo rpm -Uvh kernel-*.rpm
# 或
sudo yum localinstall kernel-*.rpm -y

# 步骤4：重启
sudo reboot

# 步骤5：确认修复
uname -r
```

### 2.4.2 注意事项

- 以上链接为基础仓库地址，具体补丁包名请根据实际架构（x86_64/aarch64）和内核版本选择
- 建议优先联系各厂商技术支持获取已验证的修复内核包
- 生产环境升级前建议先在测试环境验证兼容性
- 如使用容器环境，建议同时配置 seccomp 策略作为纵深防御
