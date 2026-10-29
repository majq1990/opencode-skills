# 页面交互指南

## 页间跳转和参数传递

### 基本页面跳转

#### 移动端页面跳转模板
```javascript
let param = {
  title: '参数1',
  content: '参数2'
}

this.$router.push({
  name: "page-preview", // 目标类型: page-preview(页面), form-preview(表单部件), detail-preview(详情部件), card-list-preview(列表部件), login-preview(移动登录页), app-home-preview(移动首页)
  query: {
    linkTitle: "标题",
    pageId: '1821371596523139072', // 页面Id
    showHeader: this.$route.query.showHeader,
    isFromAction: 1,
    _t: new Date().getTime() + "",
  },
  params: {
    param  // 自定义参数，目标页面通过this.$route.params获取
  }
});
```

#### 路由参数传递方式
1. **query参数**: 可在目标页面通过 `this.$route.query` 获取
2. **params参数**: 在目标页面通过 `this.$route.params` 获取

### 页面返回和刷新

#### 移动端返回并刷新
```javascript
function main() {
  // 返回前设置刷新标志
  this.$route.query.refresh = "1";
  this.$router.go(-1);
}

// 在目标页面的didMount生命周期中监听返回事件
export function didMount() {
  this._routerRoot._router.afterEach((to, from) => {
    if (from.query.refresh === "1") {
      Vue.nextTick(() => {
        let list = document.getElementById("card_container_egivo_csshandler_generate")
        if (list) {
          let com = list.__vue__
          com && com.onRefresh()
        }
      })
    }
  });
}
```

#### PC端页面刷新
在页面跳转按钮的后置脚本中配置：

```javascript
function main() {
    var pageListEle = this.$$("page_widget_list_5vmthz");
    console.log(pageListEle, "pageList")
    
    // 获取列表渲染页实例
    var listRenderView = pageListEle.$$getRenderElement();
    // 获取当前显示的组件，表格或者卡片
    var currentListEle = listRenderView.$$getListElement();
    // 调用刷新方法
    currentListEle.$$refreshData();
}
```

#### 多标签页面返回刷新
```javascript
function main() {
    this._routerRoot._router.afterEach((to, from) => {
        Vue.nextTick(() => {
            let arr = document.querySelectorAll("#card_container_ciun70_csshandler_generate");
            arr.forEach(e => {
                if (e && e.__vue__) {
                    e.__vue__.onRefresh()
                }
            })
        })
    });
}
```

## 弹窗交互

### 打开部件弹窗

#### 基本弹窗配置
```javascript
api.MODULE_DIALOG(that, "LIST", "eb3eb476-c9cf-446a-baf2-316e1f9c55ec", {
  linkAction: {
    // 弹窗标题
    moduleModalTitle: "案件列表",
    // 弹窗位置 left right middle top bottom
    moduleModalPosition: "bottom",
    // 弹窗尺寸 fullscreen 全屏 custom 自定义（可设置宽高）
    moduleModalSize: "custom",
    // 弹窗宽度
    moduleModalWidth: 800,
    // 弹窗高度
    moduleModalHeight: 500,
    // 是否启用遮罩
    moduleOpenMask: true,
    // 模式 对表单部件有效（true 详情；false 编辑）
    isDetail: true
  },
  // 部件弹窗的回调（对表单部件有效）
  callback: (actionType, params) => {
    // actionType 的值包含 form-close（表单部件关闭后）、form-save（表单部件保存完成后）
    // params为保存后的结果
    console.log(actionType, params);
    
    if (actionType === 'form-save') {
      // 表单保存成功后的处理
      console.log('保存的数据：', params);
    }
  },
  // 其他参数
  // 对于表单部件来说，参数为表单中的组件id与要设置的组件值
  // 对于列表部件来说，参数为列表的查询条件
  // 对于详情部件来说，参数为详情显示数据的条件
  params: {
    "recIdStr": recIdStr
  }
});
```
## 参数传递和接收

### 发送参数到目标页面

#### 页面跳转传参
```javascript
function main() {
    const dom = this.$$('csdn_form_custom_date_cfto56'); // 时间筛选组件

    const extra = {
        tabs: JSON.parse(JSON.stringify(dom.data.props.tabs)),
        currentTime: {
            start: dom.currentTime.start.clone(),  // 重要：使用clone方法克隆时间对象
            end: dom.currentTime.end.clone(),
        },
        selectDate: dom.selectDate,
    }
    
    const queryParams = Object.assign({}, extra);
    
    this.$router.push({
        name: "page-preview",
        query: {
            title: "案件列表",
            pageId: '案件列表页面Id',
            showHeader: this.$route.query.showHeader,
            isFromAction: 1,
            _t: new Date().getTime() + "",
        },
        params: {
            params: queryParams
        }
    });
}
```

### 接收参数

#### 接收自定义参数
```javascript
function main() {
  // 从路由参数中获取数据
  const params = this.$route.params;
  console.log(params);
  // 会打印 {title: '参数1', content: '参数2'}
  
  const title = this.$route.query.title;
  console.log(title);
  // 会打印 '标题'
}
```

#### PC端接收自定义参数
```javascript
function main() {
    const params = this.$$getRouteView().currentParams;
    console.log(params);
}
```
## 自定义样式

### 动态添加样式
```javascript
function Style() {
  // 创建一个style元素
  var style = document.createElement('style');
  style.type = 'text/css';

  const tabStyle = `margin-right: 4px;height: 28px;background: rgb(45, 75, 115, 0.05);border-radius: 14px;color: #2D4B73;`;

  // 添加CSS样式
  var cssContent = document.createTextNode(
    '#tabs_awow2g_csshandler_generate {' +
    `.zt2-tabs__line {display: none}` +
    `.zt2-tabs__nav { align-items: center; padding: 0 12px;}` +
    `.zt2-tab {${tabStyle}}` +
    `.zt2-tab--active{background: #0091FA;color: #FFFFFF}}` +
    `#tabs_210o5u_csshandler_generate{` +
    `.zt2-tabs__nav {background: #FFFFFF;box-shadow: 0 8px 16px 0 #2d4b731a;border-radius: 0 0 16px 16px;}}` +
    `#tabs_4ryt32_csshandler_generate{` +
    `.zt2-tabs__nav {background: #F5FAFF;}}`
  );

  style.appendChild(cssContent);
  // 将style元素插入到head中
  document.head.appendChild(style);
}
```

## 滚动控制

### 自定义回到顶部功能
```javascript
export function scrollTo() {
  Vue.nextTick(() => {
    let arr = document.querySelectorAll("#card_container_ciun70_csshandler_generate");
    arr.forEach(e => {
      if (e && e.__vue__) {
        const item = e.querySelector(".card-body-item")
        item.scrollIntoView({
          block: 'start',
          behavior: 'smooth'
        })
      }
    })
  })
}
```

## 页面生命周期

### 主要生命周期
- `didMount`: 页面加载完成后执行
- `didUpdate`: 页面更新后执行
- `willUnmount`: 页面卸载前执行

### 使用示例
```javascript
export function didMount() {
  // 页面加载完成后执行的初始化操作
  console.log('页面已加载');
  
  // 初始化数据
  this.initData();
  
  // 监听路由变化
  this._routerRoot._router.afterEach((to, from) => {
    // 路由变化后的处理
  });
}
```

## 移动端特殊交互

### 附件查看
```javascript
function main() {
    const token = window.localStorage.getItem("linglong:access_token");
    const fileId = "1";
    const url = `${window.location.origin}/linglong-api/unity/establish/file/${fileId}/download?access_token=${token}`;
    window.open(url)
}
```

### 拨打电话
```javascript
function main() {
  const phoneNumber = "13800138000";
  window.location.href = 'tel:' + phoneNumber;
}
```

### WebView关闭
```javascript
function closeWebView() {
  // 在灵珑的脚本中调用该方法，可能会提示jsi不存在，可以忽视
  window.jsi.callNative(
    JSON.stringify({ method: "close", params: { resultCode: -1 } })
  )
}
```

### 移动端调试工具注入
```javascript
function vconsole() {
  var LoadScript = (function () {
    var instances = {}
    return function (src, callback) {
      if (!instances[src]) {
        instances[src] = new Promise((resolve, reject) => {
          const script = document.createElement('script')
          var onload = () => {
            if (callback) {
              callback()
            }
            resolve()
          }
          script.src = src
          script.onload = onload
          script.onerror = reject
          document.head.appendChild(script)
        })
        instances[src].deleteInstance = function () {
          delete instances[src]
        }
      }
      return instances[src]
    }
  })()

  LoadScript("https://cdn.bootcdn.net/ajax/libs/eruda/2.3.3/eruda.js", () => {
    eruda.init()
  })
}
```

## PC端特殊交互

### 确认对话框
```javascript
this.$$confirm({
  headerTitle: "确定执行该动作吗？",
  content: "此操作不可撤销，请谨慎操作",
  type: "danger", // danger info warning
  onOk: () => {
    console.log("用户点击了确定");
    // 执行确认操作
  },
  onCancel: () => {
    console.log("用户点击了取消");
    // 执行取消操作
  }
}).then(() => {})
  .catch(() => {})
```

### 消息提示
```javascript
// 成功消息
this.$message.success('操作成功');

// 错误消息
this.$message.error('操作失败，请重试');

// 警告消息
this.$message.warning('请注意检查输入内容');

// 加载中
const loading = this.$message.loading('正在处理中...');
// 3秒后关闭
setTimeout(() => loading(), 3000);
```

## 最佳实践

### 1. 参数传递
- 时间对象传递时使用 `clone()` 方法避免引用问题
- 敏感信息不要通过URL参数传递
- 参数传递前进行验证和清理

### 2. 页面刷新
- 返回刷新时设置明确的刷新标志
- 刷新操作要考虑网络延迟和加载状态
- 提供用户友好的加载提示

### 3. 弹窗管理
- 弹窗关闭时及时清理相关状态
- 避免弹窗嵌套过深
- 提供清晰的弹窗操作说明

### 4. 样式管理
- 自定义样式避免与系统样式冲突
- 使用特定的CSS类名命名空间
- 及时清理不再使用的样式元素

### 5. 性能优化
- 避免频繁的页面跳转和刷新
- 合理使用路由缓存
- 减少不必要的DOM操作

### 6. 用户体验
- 提供清晰的操作反馈
- 合理的加载和等待状态
- 友好的错误提示和处理
