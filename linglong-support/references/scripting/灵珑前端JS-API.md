# 灵珑前端 JS-API 文档

> 来源：钉钉知识库《灵珑前端JS-API》
> 文档URL：https://alidocs.dingtalk.com/i/nodes/MNDoBb60VLrOowp4Srz63xKG8lemrZQ3

---

## 1. 开始之前注意事项

- 所有 API 均挂载在 `api` 对象上
- `this` 是动作执行上下文，多数 API 需要传入
- render API 以 `$$` 前缀区分

---

## 2. 全局路由 API

### $$setBehavior / $$getBehavior / $$resetBehavior
设置/获取/重置路由行为。

### $$getRouteView
获取路由视图上下文。

### $$refresh
刷新当前页面。

---

## 3. 表单 Render API

| API | 说明 |
|---|---|
| `$$setDefaultValues` | 设置表单默认值 |
| `$$setFormValue` | 设置表单字段值 |
| `$$getFormValue` | 获取表单字段值 |
| `$$setDetailValue` | 设置明细表值 |
| `$$getExtraParams` | 获取额外参数 |

---

## 4. 列表 Render API

| API | 说明 |
|---|---|
| `$$setExtraParams` | 设置列表额外查询参数 |
| `$$getListElement` | 获取列表元素引用 |

---

## 5. 全局 API

### 5.1 DATA_EXECUTOR
核心数据执行器，统一替换以下废弃 API：
- `DATA_SOURCE_EXECUTE` → `api.DATA_EXECUTOR`
- `MODEL_DATA_EXCUTE` → `DATA_EXECUTOR().executeDataModelForList`
- `MODEL_DETAIL_DATA_EXCUTE` → `DATA_EXECUTOR().executeDataModelForDetail`
- `API_DATA_EXECUTE` → `DATA_EXECUTOR().executeApiModelForList`
- `API_DETAIL_DATA_EXECUTE` → `DATA_EXECUTOR().executeApiModelForDetail`

支持执行数据源、数据模型、API 模型，返回异步 Promise。

### 5.2 DATA_SOURCE_EXECUTE（已废弃）
参数：apiId, apiType("BUNCHES"|"WIDZOM"), params, extraParams, headers
- `extraParams.lostAbility`：第一位=1 表示缺失分页能力，第二位=1 表示缺失排序能力

### 5.3 WIDGET_DIALOG / MODULE_DIALOG
使用脚本打开部件/页面弹窗。

```javascript
api.MODULE_DIALOG(this, "NORMAL_FORM", "widgetId", {
    linkAction: {
        moduleModalTitle: "标题",
        moduleModalPosition: "middle",  // left/right/middle/top/bottom
        moduleModalSize: "custom",       // fullscreen/custom
        moduleModalWidth: 800,
        moduleModalHeight: 600,
        moduleOpenMask: true,
        isDetail: false
    },
    callback: (actionType, params) => { },
    params: { "fieldId": "value" }
});
```

**区别**：`MODULE_DIALOG` 支持打开页面（`moduleType="PAGE"`），一般用 `MODULE_DIALOG` 即可。

### 5.4 USER_INFO
获取当前登录用户信息，无参数。

### 5.5 EXEC_FORMULA
执行公式函数，异步返回 `{hasError, result}`。
```javascript
api.EXEC_FORMULA("NOW()").then(res => console.log(res.result));
```

### 5.6 OPEN_HTML
打开站点 HTML 页面。
```javascript
api.OPEN_HTML("design.html", "design/xxx", "_blank");
```
支持页面：index.html, admin.html, design.html, workspace.html, app.html, app-preview.html, third.html(vue2), render.html(vue3), mobile.html

### 5.7 ROUTE_PUSH / ROUTE_REPLACE
导航跳转，仅应用导航内有效。
```javascript
api.ROUTE_PUSH(this, "menuId", { query: {}, params: {} });
```

### 5.8 ROUTE_VIEW
在当前页面内打开新页面或部件（实际调用 `$$open`）。
```javascript
api.ROUTE_VIEW(this, "pageId", "PAGE", {
    title: "返回",
    showHeader: true,
    cached: true,
    backStep: 1,
    callback: () => { }
});
```

### 5.9 TOKEN_INFO / APP_TOKEN / APP_AUTHORIZATION
- `TOKEN_INFO()` → 返回 `{authorizationType, tokenType, tokenValue}`
- `APP_TOKEN()` → 返回 token 值字符串
- `APP_AUTHORIZATION()` → 返回认证头 `cas ${token}` 或 `Bearer ${token}`

### 5.10 URL_PARAMS
解析 URL 参数。`api.URL_PARAMS(url)`，默认当前页面 URL。

### 5.11 COMPONENT_TYPES
组件类型常量，供渲染脚本使用：
`LAYOUT_GRID_LITE`, `FORM_FIELD`, `FORM_MAIN`, `FORM_DETAIL`, `QUERY_FIELD`, `DATA_FIELD`, `HIDDEN_FIELD`, `TABLE_COLUMN`, `FIELD_OPTION`, `FORM_UPLOAD_FILE`, `FORM_UPLOAD_IMAGE`

---

## 6. 移动端 API

| API | 说明 |
|---|---|
| `MB_JSI()` | 获取移动端 JavaScript Interface |
| `MB_JSI_REGISTER(jsi)` | 注册 JSI，对接第三方平台 |
| `MB_JSI_UNREGISTER(jsi)` | 注销已注册的 JSI |

---

## 7. 高级功能 API

### 7.1 PUBLISH_COUNTING_EVENT
设置导航菜单/标签页角标（追加模式，清空需显式设为 `""` 或 `null`）。
```javascript
api.PUBLISH_COUNTING_EVENT(self, {
    type: "appMenu",  // appMenu 或 tabs
    counting: { "menuKey": 5, "tabTitle": 12 }
});
```

### 7.2 ELEMENT_RENDER
应用导航扩展组件注册（目前仅支持 `"linglongAppHeaderLeft"`）。
```javascript
api.ELEMENT_RENDER("linglongAppHeaderLeft", function(h) {
    return h("a-select", { props: { options: [...] } });
});
```

### 7.3 FILE_HANDLE
拦截文件预览/下载/编辑操作。
```javascript
api.FILE_HANDLE("preview", (fileRecord, options) => {
    // 返回 true 拦截原逻辑，返回 false 走默认
    return true;
});
```

---

## 8. 系统变量 & 插件

### 8.1 api.CONST
访问系统变量值，键名为变量标识（在「应用设置 - 基础配置 - 系统变量」查看）。
```javascript
api.CONST["bd_var_xxx"];
```

### 8.2 PLUGIN_LOAD_AUTHING_COM_PROXY
获取用户中心接口代理。
```javascript
api.PLUGIN_LOAD_AUTHING_COM_PROXY({ baseUrl: '/usercenter-api' }).then(proxy => {
    proxy.getUnitTree({ tenantId: 0 });
});
```

### 8.3 PLUGIN_LOAD_ECHARTS
获取 echarts 插件。
```javascript
api.PLUGIN_LOAD_ECHARTS().then(res => { /* 使用 echarts */ });
```

### 8.4 PROXY_API
执行代理 API（free/unity 资源类型），参考三方服务动态代理方案文档。

### 8.5 OPEN_IMAGE
脚本打开图片预览弹窗（仅 PC 端）。
```javascript
api.OPEN_IMAGE(this, [
    { mediaType: "102", fileId: "ma_file_xxx" }
], { size: "fullscreen" });
```

---

## 9. 废弃 API 对照表

| 废弃 API | 替换方案 |
|---|---|
| `DATA_SOURCE_Execute` | `api.DATA_EXECUTOR` |
| `MODEL_DATA_EXCUTE` | `DATA_EXECUTOR().executeDataModelForList` |
| `MODEL_DETAIL_DATA_EXCUTE` | `DATA_EXECUTOR().executeDataModelForDetail` |
| `API_DATA_EXCUTE` | `DATA_EXECUTOR().executeApiModelForList` |
| `API_DETAIL_DATA_EXCUTE` | `DATA_EXECUTOR().executeApiModelForDetail` |