<!--
模板使用约定（仅供模板维护者，HTML 注释不会渲染到钉钉）：
- 所有 {{...}} 占位符由 build_software_doc_md.py 渲染
- publish.py 写入前会做正则扫描，发现残留占位符直接拒绝
- 软件漏洞文档跟 OS 漏洞文档结构对齐（三级编号、不写"反思"章）
- 一个文档对应一个软件 × 多 CVE 合并；多软件请生成多份文档
-->
# {{DOC_TITLE}}

# 1\. 漏洞说明

## 1.1 涉及软件

- 软件名称：{{SOFTWARE_DISPLAY_NAME}}（标识 `{{SOFTWARE_KEY}}`）
- 受影响版本：{{AFFECTED_VERSIONS}}
- 修复版本：{{FIXED_VERSIONS}}

## 1.2 漏洞清单

{{CVE_TABLE}}

## 1.3 漏洞概述

{{VULN_SUMMARY}}

参考链接：
{{REFERENCE_LINKS}}

---

# 2\. 漏洞解决方案

## 2.1 漏洞排查方法

### 2.1.1 检查软件版本

```bash
{{VERSION_CHECK_CMD}}
```

{{VERSION_CHECK_RULE}}

### 2.1.2 检查关键配置

{{CONFIG_CHECK_BODY}}

---

## 2.2 升级修复

### 2.2.1 在线升级（可联网）

```bash
{{ONLINE_UPGRADE_CMD}}
```

### 2.2.2 升级后验证

```bash
{{VERIFY_CMD}}
```

{{VERIFY_RULE}}

---

## 2.3 临时缓解措施

如无法立即升级，可采取以下临时缓解措施：

{{MITIGATION_BODY}}

---

## 2.4 离线环境补丁包下载清单

{{OFFLINE_PATCH_TABLE}}

### 2.4.1 离线升级通用步骤

{{OFFLINE_UPGRADE_STEPS}}

### 2.4.2 注意事项

- 升级前停止业务、做好数据备份
- 生产环境先在测试环境验证兼容性
- 集群部署需逐节点滚动升级，避免一次性全停
- 国产软件（达梦/瀚高/金仓/东方通/金蝶/中创等）建议同时联系厂商技术支持获取已验证的补丁包
