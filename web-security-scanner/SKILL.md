---
name: web-security-scanner
description: >
  基于浏览器自动化的 Web 应用安全扫描器。当用户要求"扫描网站安全"、"渗透测试"、"安全检测"、
  "漏洞扫描"、"SQL注入测试"、"XSS测试"时自动触发。支持未认证扫描和登录后渗透测试，
  覆盖 OWASP Top 10、SQL注入、XSS、CSRF、SSRF、路径遍历、命令注入、反序列化、
  JWT漏洞、会话管理、权限控制、组件漏洞、API安全等 18+ 类测试。
  输出结构化 Markdown 报告到 D:\opencode\file\{日期}\ 目录。
---

# Web Security Scanner

基于 Playwright 浏览器自动化的 Web 应用安全扫描器。

## 核心能力

### 1. 扫描模式

**未认证扫描** - 不带任何凭证，测试公开暴露的漏洞：
- 系统配置泄露
- 安全头检查
- CORS 配置
- 版本信息泄露
- 组件暴露 (Swagger/Actuator/Druid)

**已认证扫描** - 使用 Token/Cookie 登录后测试：
- 信息泄露 (用户/角色/配置)
- IDOR/越权
- 业务逻辑漏洞
- API 参数 Fuzzing

### 2. 测试覆盖 (18 类)

| 类别 | 测试项 |
|------|--------|
| **注入** | SQL注入(报错/盲注/堆叠)、XSS(反射/存储)、命令注入、SSTI |
| **认证** | 弱口令、JWT漏洞、会话管理、认证绕过 |
| **权限** | IDOR、水平/垂直提权、路径遍历 |
| **组件** | 反序列化、XXE、SSRF、Log4j |
| **配置** | 安全头、CORS、目录枚举、敏感文件 |
| **API** | 未授权访问、参数篡改、批量泄露 |

## 使用流程

### Step 1: 收集目标信息

必须确认:
- 目标 URL
- 是否自有资产/已授权
- 登录凭证 (如需已认证扫描)

### Step 2: 执行扫描

**未认证扫描**:
```javascript
// 1. 导航到目标
await page.goto('http://target.com');

// 2. 测试公开端点
await testPublicEndpoints(page, baseUrl);

// 3. 检查安全头
await checkSecurityHeaders(page, baseUrl);
```

**已认证扫描**:
```javascript
// 1. 设置 Token
await page.evaluate((token) => {
  document.cookie = `admin_sso_token=${token}; path=/`;
  localStorage.setItem('token', `bearer ${token}`);
}, token);

// 2. 测试已认证端点
await testAuthenticatedEndpoints(page, baseUrl);

// 3. 权限提升测试
await testPrivilegeEscalation(page, baseUrl);
```

### Step 3: 生成报告

报告自动保存到:
```
D:\opencode\file\{YYYY-MM-DD}\{目标}-安全扫描报告.md
```

## 关键技术

### 请求签名处理
某些 API 需要 nonce/timestamp/signature 签名:
```javascript
// 从页面拦截已签名的请求
const signedRequests = [];
page.on('request', req => {
  if (req.url().includes('signature')) {
    signedRequests.push(req.url());
  }
});
```

### WAF 绕过检测
记录 WAF 拦截规则:
```javascript
// 检测 WAF 响应头
if (response.status() === 403) {
  const ruleId = response.headers()['x-waf-rule-id'];
  console.log(`WAF Rule ${ruleId} blocked: ${payload}`);
}
```

### page.evaluate 用法
```javascript
// 正确用法: 不传 page 参数
await page.evaluate(async () => {
  const resp = await fetch('/api/endpoint');
  return await resp.json();
});
```

## 报告结构

```markdown
# {目标} 安全扫描报告

## 扫描概览
- 目标 URL
- 扫描时间
- 测试覆盖率

## 发现汇总
- 🔴 HIGH: 严重漏洞
- 🟠 MEDIUM: 中等风险
- 🟡 LOW: 低风险
- ✅ PASS: 安全项

## 详细发现
每个漏洞包含:
- 标题和严重级别
- 影响范围
- 复现步骤
- 修复建议

## 测试覆盖矩阵
18 类测试的通过/失败状态
```

## 触发示例

✅ "扫描 http://example.com 的安全漏洞"
✅ "对这个网站做渗透测试"
✅ "测试 SQL 注入和 XSS"
✅ "帮我检查这个 API 有没有安全问题"
❌ "什么是 OWASP Top 10" — 不触发, 这是概念问题
