# 灵珑脚本最佳实践

## 代码质量

### 1. 命名规范

#### 变量命名
- 使用驼峰式命名：`let userName = "张三";`
- 避免使用缩写，除非是广为人知的缩写
- 常量使用全大写和下划线分隔：`const MAX_RETRY_COUNT = 3;`

#### 函数命名
- 动词开头，描述功能：`function getListData() {}`
- 避免使用含糊的名称如 `func`, `process`, `handle`
- 回调函数使用 `on` 前缀：`function onFormSubmit() {}`

### 2. 代码结构

#### 模块化
- 将不同功能的代码拆分为独立函数
- 避免过长的函数（保持在50行以内）
- 通用功能封装为可复用的模块

```javascript
// 不好的写法
function main() {
  // 处理表单验证
  // 处理数据提交
  // 处理结果展示
}

// 好的写法
function main() {
  if (validateForm()) {
    submitFormData();
  }
}

function validateForm() {
  // 表单验证逻辑
}

function submitFormData() {
  // 数据提交逻辑
}
```

#### 注释规范
- 复杂逻辑添加解释性注释
- 公共函数添加JSDoc注释
- 避免注释明显的代码

```javascript
/**
 * 验证表单数据
 * @param {Object} formData - 表单数据对象
 * @returns {boolean} - 验证结果
 */
function validateForm(formData) {
  // 复杂验证逻辑
  return valid;
}
```

### 3. 错误处理

#### 完善的错误处理
- 所有异步操作添加 `.catch()`
- 提供明确的错误信息
- 记录错误日志便于调试

```javascript
// 不好的写法
api.DATA_SOURCE_EXECUTE(apiId, "api", params, [], "").then(res => {
  // 处理结果
});

// 好的写法
api.DATA_SOURCE_EXECUTE(apiId, "api", params, [], "")
  .then(res => {
    if (!res.hasError) {
      // 处理成功结果
    } else {
      console.error("API调用错误:", res.message);
      this.$message.error("操作失败，请重试");
    }
  })
  .catch(err => {
    console.error("API调用异常:", err);
    this.$message.error("系统繁忙，请稍后再试");
  });
```

#### 边界情况处理
```javascript
function getUserName(user) {
  // 确保不会因为user为null/undefined而报错
  return user?.name || "未知用户";
}
```

### 4. 性能优化

#### 减少DOM操作
- 批量操作DOM，避免频繁修改
- 隐藏后再批量更新

```javascript
// 不好的写法
for (let i = 0; i < 1000; i++) {
  document.getElementById('container').innerHTML += `<div>${i}</div>`;
}

// 好的写法
let html = '';
for (let i = 0; i < 1000; i++) {
  html += `<div>${i}</div>`;
}
document.getElementById('container').innerHTML = html;
```

#### 防抖和节流
```javascript
// 防抖函数
function debounce(func, wait) {
  let timeout;
  return function() {
    const context = this;
    const args = arguments;
    clearTimeout(timeout);
    timeout = setTimeout(function() {
      func.apply(context, args);
    }, wait);
  };
}

// 节流函数
function throttle(func, limit) {
  let lastRun = 0;
  return function() {
    const context = this;
    const args = arguments;
    const now = Date.now();
    if (now - lastRun >= limit) {
      func.apply(context, args);
      lastRun = now;
    }
  };
}
```

### 5. 灵珑平台特定优化

#### 减少不必要的刷新
```javascript
// 仅在数据变化时刷新
if (newData !== oldData) {
  this.$ztToast("数据已更新");
  this.onRefresh();
}
```

### 6. 移动端和PC端适配

#### 环境判断
```javascript
function getDeviceType() {
  const userAgent = navigator.userAgent.toLowerCase();
  if (userAgent.match(/(phone|pad|pod|iPhone|iPod|ios|iPad|Android|Mobile|BlackBerry|IEMobile|MQQBrowser|JUC|Fennec|wOSBrowser|BrowserNG|WebOS|Symbian|Windows Phone)/i)) {
    return 'mobile';
  }
  return 'pc';
}
```

#### 不同设备的消息提示
```javascript
function showMessage(message, type = 'info') {
  const deviceType = getDeviceType();
  if (deviceType === 'mobile') {
    this.$ztToast[type](message);
  } else {
    this.$message[type](message);
  }
}
```

### 7. 安全性

#### 数据验证
- 前端验证不能替代后端验证
- 对用户输入进行严格验证

```javascript
function validateInput(input) {
  // 验证输入格式
  if (!/^[a-zA-Z0-9]+$/.test(input)) {
    return "只能包含字母和数字";
  }
  if (input.length < 6) {
    return "长度至少为6位";
  }
  return true;
}
```

#### 避免XSS攻击
```javascript
function escapeHtml(html) {
  return html.replace(/[<>&"']/g, function(match) {
    const escapeMap = {
      '<': '&lt;',
      '>': '&gt;',
      '&': '&amp;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return escapeMap[match];
  });
}
```

### 8. 调试技巧

#### 日志调试
```javascript
// 使用不同级别的日志
console.debug('调试信息', data);
console.info('普通信息');
console.warn('警告信息');
console.error('错误信息');
```

#### 断点调试
```javascript
function debugFunction() {
  // 在这里设置断点
  debugger;
  // 后续代码
}
```

## 总结

编写高质量的灵珑脚本需要：
1. 遵循统一的编码规范
2. 注重代码的可读性和可维护性
3. 完善的错误处理和边界情况处理
4. 考虑性能和安全因素
5. 定期学习和更新知识