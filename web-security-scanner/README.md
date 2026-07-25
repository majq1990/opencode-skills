# Web Security Scanner

基于浏览器自动化的 Web 应用安全扫描器，封装了完整的渗透测试能力。

## 功能特性

### 扫描模式

- **未认证扫描**: 测试公开暴露的漏洞（配置泄露、安全头、组件暴露）
- **已认证扫描**: 登录后测试信息泄露、IDOR、权限提升等

### 测试覆盖 (18 类)

| 类别 | 测试项 |
|------|--------|
| 注入 | SQL注入、XSS、命令注入、SSTI |
| 认证 | JWT漏洞、会话管理、认证绕过 |
| 权限 | IDOR、水平/垂直提权、路径遍历 |
| 组件 | 反序列化、XXE、SSRF、Log4j |
| 配置 | 安全头、CORS、目录枚举 |
| API | 未授权访问、参数篡改 |

## 使用方法

### 1. 加载 Skill

```
/web-security-scanner
```

### 2. 提供目标信息

```
扫描 http://example.com 的安全漏洞
```

### 3. (可选) 提供登录凭证

```
Token: your-sso-token-here
```

### 4. 查看报告

报告自动保存到:
```
D:\opencode\file\{YYYY-MM-DD}\{目标}-安全扫描报告.md
```

## 文件结构

```
web-security-scanner/
├── SKILL.md              # Skill 主文件
├── scripts/
│   └── scan.js           # 扫描核心逻辑
├── payloads/
│   └── payloads.json     # 测试 payload 库
└── templates/
    └── report-template.md # 报告模板
```

## 技术实现

- **浏览器自动化**: Playwright
- **请求拦截**: page.evaluate + fetch
- **WAF 检测**: 自动识别拦截规则
- **签名处理**: 拦截已签名请求复用

## 注意事项

⚠️ **授权要求**: 仅扫描自有资产或已获书面授权的目标
⚠️ **WAF 绕过**: 自动记录 WAF 规则，不主动绕过
⚠️ **数据安全**: 报告仅保存到本地，不上传外部服务
