# {{TARGET_NAME}} 渗透测试报告

---

## 一、测试概述（Executive Summary）

| 项目 | 内容 |
|------|------|
| **测试范围** | {{TARGET_URL}} |
| **测试时间** | {{SCAN_START_TIME}} ~ {{SCAN_END_TIME}} |
| **测试类型** | 灰盒测试（已知凭证） |
| **测试方法** | OWASP Top 10、PTES、NIST SP 800-115 |
| **测试工具** | Playwright + 自定义扫描引擎 |
| **测试人员** | AI Security Scanner v1.0 |

### 风险等级汇总

| 风险等级 | 数量 | 说明 |
|----------|------|------|
| 🔴 高危 | {{HIGH_COUNT}} | 可导致敏感数据泄露或系统沦陷 |
| 🟠 中危 | {{MEDIUM_COUNT}} | 可被利用进行定向攻击 |
| 🟡 低危 | {{LOW_COUNT}} | 安全隐患，需改进 |
| ℹ️ 信息 | {{INFO_COUNT}} | 不构成直接威胁，但需关注 |

---

## 二、信息收集阶段

### 2.1 目标信息

| 项目 | 内容 |
|------|------|
| **目标 URL** | {{TARGET_URL}} |
| **技术栈** | {{TECH_STACK}} |
| **服务器** | {{SERVER_INFO}} |
| **前端框架** | {{FRONTEND_FRAMEWORK}} |

### 2.2 端口与服务

| 端口 | 服务 | 版本 |
|------|------|------|
| {{PORT}} | {{SERVICE}} | {{VERSION}} |

### 2.3 WAF 识别

| WAF 类型 | 规则数量 | 拦截次数 |
|----------|----------|----------|
| {{WAF_TYPE}} | {{WAF_RULES_COUNT}} | {{WAF_BLOCKS_COUNT}} |

---

## 三、漏洞发现与验证

### 3.1 高危漏洞

{{#HIGH_FINDINGS}}
#### {{INDEX}}. {{TITLE}}

**漏洞编号**: {{VULN_ID}}  
**CVE/CWE**: {{CVE_CWE}}  
**OWASP 分类**: {{OWASP_CATEGORY}}  
**CVSS 评分**: {{CVSS_SCORE}}

**漏洞描述**:
{{DESCRIPTION}}

**漏洞位置**:
```
{{LOCATION}}
```

**复现步骤**:
1. {{STEP_1}}
2. {{STEP_2}}
3. {{STEP_3}}

**请求/响应证据**:
```http
{{REQUEST}}
```
```http
{{RESPONSE}}
```

**影响范围**:
- {{IMPACT_1}}
- {{IMPACT_2}}

**利用条件**:
- {{CONDITION_1}}
- {{CONDITION_2}}

**修复建议**:
{{RECOMMENDATION}}

**修复优先级**: 🔴 紧急

---

{{/HIGH_FINDINGS}}

### 3.2 中危漏洞

{{#MEDIUM_FINDINGS}}
#### {{INDEX}}. {{TITLE}}

**漏洞编号**: {{VULN_ID}}  
**CVE/CWE**: {{CVE_CWE}}  
**OWASP 分类**: {{OWASP_CATEGORY}}  
**CVSS 评分**: {{CVSS_SCORE}}

**漏洞描述**:
{{DESCRIPTION}}

**漏洞位置**:
```
{{LOCATION}}
```

**复现步骤**:
1. {{STEP_1}}
2. {{STEP_2}}

**请求/响应证据**:
```http
{{REQUEST}}
```
```http
{{RESPONSE}}
```

**影响范围**:
- {{IMPACT_1}}

**修复建议**:
{{RECOMMENDATION}}

**修复优先级**: 🟠 高

---

{{/MEDIUM_FINDINGS}}

### 3.3 低危漏洞

{{#LOW_FINDINGS}}
#### {{INDEX}}. {{TITLE}}

**漏洞编号**: {{VULN_ID}}  
**CVE/CWE**: {{CVE_CWE}}  
**OWASP 分类**: {{OWASP_CATEGORY}}  
**CVSS 评分**: {{CVSS_SCORE}}

**漏洞描述**:
{{DESCRIPTION}}

**漏洞位置**:
```
{{LOCATION}}
```

**修复建议**:
{{RECOMMENDATION}}

**修复优先级**: 🟡 中

---

{{/LOW_FINDINGS}}

### 3.4 信息级发现

{{#INFO_FINDINGS}}
#### {{INDEX}}. {{TITLE}}

**描述**: {{DESCRIPTION}}  
**位置**: {{LOCATION}}  
**建议**: {{RECOMMENDATION}}

{{/INFO_FINDINGS}}

---

## 四、漏洞利用与影响分析

### 4.1 攻击路径分析

```
{{ATTACK_PATH_DIAGRAM}}
```

### 4.2 利用链分析

| 利用链 | 漏洞组合 | 最终影响 | 风险等级 |
|--------|----------|----------|----------|
| {{CHAIN_1}} | {{VULN_COMBINATION_1}} | {{FINAL_IMPACT_1}} | {{RISK_LEVEL_1}} |
| {{CHAIN_2}} | {{VULN_COMBINATION_2}} | {{FINAL_IMPACT_2}} | {{RISK_LEVEL_2}} |

### 4.3 数据泄露评估

| 数据类型 | 泄露风险 | 影响范围 |
|----------|----------|----------|
| 用户凭证 | {{CREDENTIAL_RISK}} | {{CREDENTIAL_SCOPE}} |
| 个人信息 | {{PII_RISK}} | {{PII_SCOPE}} |
| 系统配置 | {{CONFIG_RISK}} | {{CONFIG_SCOPE}} |

---

## 五、风险评估矩阵

```
         高影响
           │
    中危   │   高危
           │
低概率─────┼─────高概率
           │
    低危   │   中危
           │
         低影响
```

| 风险等级 | 漏洞数量 | 占比 |
|----------|----------|------|
| 高危 | {{HIGH_COUNT}} | {{HIGH_PERCENT}}% |
| 中危 | {{MEDIUM_COUNT}} | {{MEDIUM_PERCENT}}% |
| 低危 | {{LOW_COUNT}} | {{LOW_PERCENT}}% |
| 信息 | {{INFO_COUNT}} | {{INFO_PERCENT}}% |

---

## 六、修复建议（按优先级）

### 6.1 紧急修复（24小时内）

| 序号 | 漏洞 | 修复措施 | 负责人 |
|------|------|----------|--------|
{{#URGENT_FIXES}}
| {{INDEX}} | {{VULN_NAME}} | {{FIX_MEASURE}} | {{OWNER}} |
{{/URGENT_FIXES}}

### 6.2 高优先级修复（1周内）

| 序号 | 漏洞 | 修复措施 | 负责人 |
|------|------|----------|--------|
{{#HIGH_FIXES}}
| {{INDEX}} | {{VULN_NAME}} | {{FIX_MEASURE}} | {{OWNER}} |
{{/HIGH_FIXES}}

### 6.3 中优先级修复（1个月内）

| 序号 | 漏洞 | 修复措施 | 负责人 |
|------|------|----------|--------|
{{#MEDIUM_FIXES}}
| {{INDEX}} | {{VULN_NAME}} | {{FIX_MEASURE}} | {{OWNER}} |
{{/MEDIUM_FIXES}}

### 6.4 低优先级修复（季度内）

| 序号 | 漏洞 | 修复措施 | 负责人 |
|------|------|----------|--------|
{{#LOW_FIXES}}
| {{INDEX}} | {{VULN_NAME}} | {{FIX_MEASURE}} | {{OWNER}} |
{{/LOW_FIXES}}

---

## 七、测试覆盖矩阵

| 测试类别 | 测试项 | 测试用例数 | 发现漏洞 | 结果 |
|----------|--------|------------|----------|------|
| **Web 应用** | SQL 注入 | {{SQL_TESTS}} | {{SQL_VULNS}} | {{SQL_RESULT}} |
| | XSS (反射/存储) | {{XSS_TESTS}} | {{XSS_VULNS}} | {{XSS_RESULT}} |
| | CSRF | {{CSRF_TESTS}} | {{CSRF_VULNS}} | {{CSRF_RESULT}} |
| | SSRF | {{SSRF_TESTS}} | {{SSRF_VULNS}} | {{SSRF_RESULT}} |
| | 文件上传 | {{UPLOAD_TESTS}} | {{UPLOAD_VULNS}} | {{UPLOAD_RESULT}} |
| | 反序列化 | {{DESERIAL_TESTS}} | {{DESERIAL_VULNS}} | {{DESERIAL_RESULT}} |
| | XXE | {{XXE_TESTS}} | {{XXE_VULNS}} | {{XXE_RESULT}} |
| **身份认证** | 弱口令 | {{WEAKPWD_TESTS}} | {{WEAKPWD_VULNS}} | {{WEAKPWD_RESULT}} |
| | 暴力破解 | {{BRUTE_TESTS}} | {{BRUTE_VULNS}} | {{BRUTE_RESULT}} |
| | JWT 漏洞 | {{JWT_TESTS}} | {{JWT_VULNS}} | {{JWT_RESULT}} |
| | 会话管理 | {{SESSION_TESTS}} | {{SESSION_VULNS}} | {{SESSION_RESULT}} |
| **权限控制** | 越权访问 | {{PRIVESC_TESTS}} | {{PRIVESC_VULNS}} | {{PRIVESC_RESULT}} |
| | IDOR | {{IDOR_TESTS}} | {{IDOR_VULNS}} | {{IDOR_RESULT}} |
| **服务器配置** | 目录遍历 | {{DIR_TRAV_TESTS}} | {{DIR_TRAV_VULNS}} | {{DIR_TRAV_RESULT}} |
| | 敏感文件 | {{SENSITIVE_TESTS}} | {{SENSITIVE_VULNS}} | {{SENSITIVE_RESULT}} |
| | 组件暴露 | {{COMPONENT_TESTS}} | {{COMPONENT_VULNS}} | {{COMPONENT_RESULT}} |
| **API 安全** | 未授权访问 | {{API_AUTH_TESTS}} | {{API_AUTH_VULNS}} | {{API_AUTH_RESULT}} |
| | 参数篡改 | {{API_PARAM_TESTS}} | {{API_PARAM_VULNS}} | {{API_PARAM_RESULT}} |
| | 批量数据泄露 | {{API_LEAK_TESTS}} | {{API_LEAK_VULNS}} | {{API_LEAK_RESULT}} |
| **安全头** | CSP | {{CSP_TESTS}} | {{CSP_VULNS}} | {{CSP_RESULT}} |
| | HSTS | {{HSTS_TESTS}} | {{HSTS_VULNS}} | {{HSTS_RESULT}} |
| | X-Frame-Options | {{XFO_TESTS}} | {{XFO_VULNS}} | {{XFO_RESULT}} |
| | CORS | {{CORS_TESTS}} | {{CORS_VULNS}} | {{CORS_RESULT}} |

**测试覆盖率**: {{COVERAGE}}%

---

## 八、附录

### 8.1 工具清单及版本

| 工具 | 版本 | 用途 |
|------|------|------|
| Playwright | {{PLAYWRIGHT_VERSION}} | 浏览器自动化 |
| Custom Scanner | v1.0 | 漏洞检测引擎 |
| {{OTHER_TOOL}} | {{OTHER_VERSION}} | {{OTHER_PURPOSE}} |

### 8.2 WAF 规则拦截统计

| 规则 ID | 规则描述 | 拦截次数 |
|---------|----------|----------|
{{#WAF_RULES}}
| {{RULE_ID}} | {{RULE_DESC}} | {{BLOCK_COUNT}} |
{{/WAF_RULES}}

### 8.3 测试账号信息

| 用途 | 用户名 | 权限级别 |
|------|--------|----------|
| 测试登录 | {{TEST_USERNAME}} | {{TEST_ROLE}} |

### 8.4 参考标准

| 标准 | 说明 |
|------|------|
| OWASP Top 10 2021 | Web 应用安全风险 Top 10 |
| PTES | 渗透测试执行标准 |
| NIST SP 800-115 | 信息安全测试与评估技术指南 |
| CVSS v3.1 | 通用漏洞评分系统 |
| CWE | 通用弱点枚举 |

### 8.5 原始扫描日志

> 详细扫描日志请查阅: {{LOG_PATH}}

---

## 九、免责声明

本报告仅用于授权渗透测试场景，未经授权的渗透测试属于违法行为。

报告中的漏洞信息仅供安全团队内部使用，请勿外传。

---

**报告生成时间**: {{GENERATED_AT}}  
**报告生成工具**: web-security-scanner v1.0  
**报告版本**: v1.0
