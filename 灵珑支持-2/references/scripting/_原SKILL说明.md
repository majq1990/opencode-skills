---
name: egova-config-linglong-js
description: 灵珑平台脚本开发助手，提供表单、列表、详情、页面、树组件、地图等各组件的脚本编写解决方案和代码模板，帮助用户编写、调试和优化灵珑前端js脚本。
---

# 灵珑脚本开发助手

## 任务目标
帮助开发者在灵珑平台中快速编写、调试和优化各类组件的脚本代码，解决常见交互问题和复杂业务场景。

## 执行流程

### 步骤1: 理解需求
- 识别用户需求，明确具体的功能需求（数据交互、UI控制、组件联动等）
- 对需求进行拆解
- 参考 [components-api-reference.md](references/components-api-reference.md) 了解全局常用API和可快速查找的基础脚本

### 步骤2: 选择合适的解决方案
询问用户使用场景，了解用户需求，并选择最合适的解决方案
根据需求选择对应的脚本模式：
- 基础脚本：调用API、显隐、提交、默认值、传参、弹窗相关脚本，查看 [form-scripts-guide.md](references/form-scripts-guide.md)
- 列表脚本：列表hook、跳转详情、列表刷新相关脚本，查看 [list-scripts-guide.md](references/list-scripts-guide.md)
- 页面交互：跳转、路由传参、自定义样式相关脚本，查看 [page-interaction-guide.md](references/page-interaction-guide.md)
- 树组件联动：查看 [tree-component-guide.md](references/tree-component-guide.md)

### 步骤3: 提供代码模板
根据具体需求，从对应参考文档中提取代码模板
- 根据实际情况修改组件ID和参数
- 添加必要的业务逻辑
- 处理错误和边界情况

### 步骤4: 最佳实践建议
- 代码优化建议参考 [best-practices.md](references/best-practices.md)
- 移动端和PC端差异化处理
- 性能优化和错误处理

## 错误处理
- API调用失败：添加 `.catch()` 错误处理
- 组件不存在：添加存在性检查
- 参数验证：确保参数完整性和正确性

## 版本兼容性说明
- 1.6.0版本前后的消息提示和对话框API有差异
- 部分功能在不同版本中可能有不同的实现方式

### this 上下文（⚠️ 必须遵守）
**始终在函数第一行保存 this 引用**，后续使用 `self` 访问 API：
```javascript
function main() {
  const self = this; // ✅ 必须
  // 使用 self.$$ / self.$$element 等访问API
  // 箭头函数内 this 安全，function 回调内 this 会变
}
```

### 核心约束
1. **禁止使用未文档化的私有 API/属性**
2. 隐藏组件用 `$$m()` / `$$model()` 获取模型，`$$()` 无法找到
3. 用 `$$addEventListener` 替代 `window.addEventListener` 防内存泄漏
4. 用 `api.DATA_EXECUTOR` 替代废弃的 `DATA_SOURCE_EXECUTE`
5. 不要用 `modal.confirm` 替代 `$$confirm`

### 代码审查清单
优化已有脚本时逐项检查：
- [ ] 保存了 `this` 引用？
- [ ] 使用了废弃 API？→ 替换为 `DATA_EXECUTOR`
- [ ] Promise 有 `.catch()`？
- [ ] 用了 `window.addEventListener`？→ 换 `$$addEventListener`
- [ ] 删除有 `$$confirm` 确认？
- [ ] 耗时操作有 loading 管理？
- [ ] 考虑了 vue2/vue3 和 PC/移动端差异？
- [ ] 组件查找结果做了空值判断？
