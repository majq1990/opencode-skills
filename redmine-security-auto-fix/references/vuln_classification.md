# 漏洞分类规则

## 分类原则

漏洞按照修复责任方分为两类（参考漏洞响应一条龙skill）：

1. **工程中心处理（ops_fixes）** - 服务器层面的配置修复
2. **研发中心处理（dev_fixes）** - 应用层面的配置和代码修复

## 工程中心处理范围

工程中心负责服务器层面的配置修复，包括：

### Nginx层修复
- HTTP响应头配置（X-Frame-Options、X-Content-Type-Options等）
- CORS跨域配置
- HTTPS/SSL配置
- HSTS配置
- CSP内容安全策略
- 其他安全响应头

### Tomcat层修复
- server.xml配置（关闭服务器信息泄露）
- 错误页面配置（自定义错误页面）

## 研发中心处理范围

研发中心负责应用层面的配置和代码修复，包括：

### Java应用层修复
- web.xml中的Cookie HttpOnly配置
- Spring Boot的application.properties配置
- 错误处理配置

### 前端文件修复
- jQuery升级
- RequireJS升级
- 其他前端框架升级

## 分类流程

1. **识别漏洞类型** - 根据漏洞名称和描述判断类型
2. **匹配分类规则** - 按照Nginx层/Tomcat层/Java应用层/前端文件层分类
3. **人工确认** - 对于边界情况，需要人工确认分类

## 分类结果格式

```json
{
  "issue_id": 502856,
  "ops_fixes": [
    {
      "id": 1,
      "name": "CORS跨域资源共享来源验证失败",
      "risk": "中",
      "type": "ops",
      "layer": "nginx"
    }
  ],
  "dev_fixes": [
    {
      "id": 18,
      "name": "Cookie未设置HttpOnly标志",
      "risk": "低",
      "type": "dev",
      "layer": "java_app"
    }
  ],
  "stats": {
    "ops_fixes": 22,
    "dev_fixes": 5
  }
}
```

## 参考文档

- 漏洞响应一条龙skill：vuln-response
- 霍山县智慧城管系统安全漏洞修复方案：https://alidocs.dingtalk.com/i/nodes/AR4GpnMqJzML1Xr9saQ9r6wLVKe0xjE3
