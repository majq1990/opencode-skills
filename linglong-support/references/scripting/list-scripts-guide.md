# 列表脚本指南

## 列表脚本核心功能

### 1. 移动端通过脚本跳转详情

#### 配置列表到详情的跳转
在列表部件的跳转按钮中配置参数，跳转到详情页面时传入对应的数据ID。

```javascript
// 列表页面跳转脚本
function main() {
  this.$router.push({
    name: "detail-preview", // 详情部件
    query: {
      title: "案件详情",
      pageId: '详情页面Id',
      showHeader: this.$route.query.showHeader,
      isFromAction: 1,
      _t: new Date().getTime() + "",
    },
    params: {
      "id": params.id.value, // 传入详情数据的主键
    }
  });
}
```

#### 详情页面接收参数
在详情页面配置接收参数，根据传入的ID查询对应数据。
```javascript
function main() {
  const query = this.$route.query;
  const params = this.$route.params;
}
```
### 2. Hook查询列表数据

#### 基本Hook查询
```javascript
function main(pageId, param) {
  return new Promise((resolve, reject) => {
    // 设置查询参数
    param.condition.params = { 
      "pageIndex": param.paging.pageIndex,
      "pageSize": param.paging.pageSize,
      "keyword": param.condition.keyword || null
    };
    const apiId = "678e6ac5-6479-4da9-9d91-942710a95932-8dbc-5e35"; // 替换为你的API ID

    // 调用API查询数据
    api.API_DATA_EXECUTE(apiId, "BUNCHES", param, { lostAbility: "00" })
      .then(res => {
        resolve(res);
      }).catch(() => {
        reject();
      })
  });
}
```

### 3. 列表刷新方法

#### 移动端列表刷新
```javascript
function main() {
  Vue.nextTick(() => {
    let list = document.getElementById("card_container_dtqvlk_csshandler_generate")
    if (list) {
      let com = list.__vue__
      com && com.onRefresh()
    }
  })
}
```

#### PC端列表刷新
```javascript
function main() {
    var pageListEle = this.$$("page_widget_list_5vmthz");
    // 获取列表渲染页实例
    var listRenderView = pageListEle.$$getRenderElement();
    // 获取当前显示的组件，表格或者卡片
    var currentListEle = listRenderView.$$getListElement();
    // 调用刷新方法
    currentListEle.$$refreshData();
}
```

#### 移动端多标签列表刷新
```javascript
function main() {
    Vue.nextTick(() => {
        let arr = document.querySelectorAll("#card_container_ciun70_csshandler_generate");
        arr.forEach(e => {
            if (e && e.__vue__) {
                e.__vue__.onRefresh()
            }
        })
    });
}
```

### 4. 字段样式控制

#### 字段内容修改和显示控制示例
```javascript
function main(params) {
    // 修改remainTime字段的值
    const time = params.remainTime.value;
    if (time < 0) {
        const ceil = Math.ceil(time);
        const hour = Math.ceil((ceil - time) * 24);
        if (hour == 0) {
            params.remainTime.value = "已超时" + Math.abs(ceil) + "天"
        } else {
            params.remainTime.value = "已超时" + Math.abs(ceil) + "天" + hour + "小时"
        }
    } else {
        return "HIDDEN" // 隐藏字段
    }
    return "NORMAL"; // 显示字段
}
```

#### 按钮状态控制
```javascript
function main() {
  // 根据条件返回不同的状态
  // NORMAL: 普通状态
  // HIDDEN: 隐藏状态
  // DISABLED: 禁用状态
  return "NORMAL";
}
```

### 5. 按钮名称动态赋值

```javascript
function main() {
  if (this.mode == "generate" && this._props.data) {
    // 取出字段 fieldName 的值
    let title = this.params["fieldName"].value || "编辑";
    // 把取出的值作为按钮的文本内容
    this.$set(this.button, "title", title);
  }
  
  // NORMAL 普通状态
  // HIDDEN 隐藏状态
  // DISABLED 禁用状态
  return "NORMAL";
}
```

### 6. 列表行点击高亮

```javascript
function main(params) {
  // 找到表格组件元素
  var ele = this.$$element("table_c8r2w8");
  if (ele && ele.$el) {
    // 首先清除旧标记
    var oldls = ele.$el.querySelectorAll("tr[old-click='old-click']");
    if (oldls.length) {
      for (let i = 0; i < oldls.length; i++) {
        let n = oldls[i];
        if (n) {
          // 仅做标记
          n.removeAttribute("old-click", "old-click");
          n.style.backgroundColor = "unset";
        }
      }
    }
    
    // 设置新的高亮行
    // params.id 为列表中的主键列，根据实际情况调整
    var selector = "tr[data-row-key='" + params.id.value + "']";
    var ls = ele.$el.querySelectorAll(selector);
    if (ls.length) {
      for (let i = 0; i < ls.length; i++) {
        let node = ls[i];
        if (node) {
          // 仅做标记
          node.setAttribute("old-click", "old-click");
          node.style.backgroundColor = "#F0F9FF";
        }
      }
    }
  }
}
```
## 列表中hook查询分页处理

### 分页参数获取
在Hook查询中，通过 `param.paging` 获取分页参数：
- `pageIndex`: 当前页码
- `pageSize`: 每页显示数量

### 返回总数要求
确保注册的接口返回数据包含总数，灵珑才能正确处理分页。

```javascript
// 接口返回格式示例
{
  "data": [...], // 数据列表
  "total": 100   // 总数
}
```

## 最佳实践

### 1. 性能优化
- 避免在Hook中进行复杂的数据处理
- 尽量在后端完成数据筛选和转换
- 合理设置每页显示数量

### 2. 用户体验
- 提供清晰的加载状态
- 合理设置字段宽度
- 对重要信息使用样式突出显示

### 3. 错误处理
- Hook查询失败时返回空数据
- 添加适当的错误提示
- 记录错误日志便于调试

### 4. 数据安全
- 验证用户权限后再显示数据
- 敏感字段注意脱敏处理
- 避免在前端暴露过多数据
