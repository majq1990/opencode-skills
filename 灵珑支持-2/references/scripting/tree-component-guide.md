# 树组件联动指南

## 树组件与表单部件联动

### 场景描述
当点击树节点时，获取选中节点字段的值，给表单中的组件赋值。如果需要根据树节点反查表单的数据，需要传递 `documentNo` 参数。

### 实现代码
```javascript
function main(params) {
  // 找到页面中的表单渲染组件
  var pageFormWidget = this.$$("form_part_f286fq");
  if (pageFormWidget && pageFormWidget.$children) {
    // 真正的表单部件
    var formRender = pageFormWidget.$children[0];
    
    // 给表单传参
    // 参数名 single_select_7u0r6t 为表单组件的 id，参数值为树节点的字段值
    // 如果点树节点需要反查表单的数据，需要传参数 documentNo
    formRender.$$setFormValue({
      "single_select_7u0r6t": params.data.id
    });
  }
}
```

## 树组件与详情部件联动

### 实现代码
```javascript
function main(params) {
  // 获取页面根元素
  const pageRootList = this.$$roots();
  let rootPageElement = pageRootList[0];
  
  // 找到页面中的详情部件元素
  var pageDetail = rootPageElement.$$element("page_detail_dgyay4");
  var detailRootElement = pageDetail.$children[0];
  
  if (detailRootElement) {
    var dataEngine = detailRootElement.dataEngine
    
    // 将树节点参数赋给详情，有一个参数名匹配即可查出数据
    dataEngine.defaultParams = params;
    dataEngine.queryData();
  }
}
```

## 树组件与另一个树部件联动

### 实现代码
```javascript
function main(params) {
  // 获取页面根元素
  const pageRoot = this.$$roots();
  let rootPageElement = pageRoot[0];
  
  // 找到页面中的被联动树部件元素
  let pageTree = rootPageElement.$$element("page_tree_dhmkrk");
  
  if (pageTree) {
    if (pageTree.dataEngine && pageTree.dataEngine.state) {
      // 给树部件设置参数
      // 参数名 meter_id 为要过滤树中的列名，后面为参数值，取自树节点参数
      pageTree.$children[0].$$setExtraParams({
        meter_id: params.data.id
      })
      
      // 找到树部件中的树面板元素（打开树形部件设计器，选中树面板在右侧高级面板中）
      let treeComp = pageTree.dataEngine.state.getElement("tree_panel_h499yn");
      if (treeComp) {
        // 执行树数据刷新
        treeComp.$$refreshData();
      }
    }
  }
}
```

## 树组件与动态部件渲染组件联动

### 实现代码
```javascript
function main(params) {

  // 找到页面中的动态部件渲染组件
  var dynamicWidgetForm = this.$$element("dynamic_widget_render_fq70hr");
  
  // 给动态部件渲染组件赋值
  // 参数 id 需要赋值为要打开的部件 id（取自树节点参数）
  // 参数 type 为部件类型，普通表单为 NORMAL_FORM、列表为 LIST
  if (dynamicWidgetForm) {
    dynamicWidgetForm.data.props.widgetPageProps = {
      id: params.data.columns['widget_form_id'],
      type: "NORMAL_FORM"
    }
  }
}
```

## 树形部件新增数据后刷新并选中新增节点

### 使用场景
在树形部件中通过表单弹窗新增节点后，刷新树数据并自动选中新增的节点。

### 实现代码
```javascript
function main(defaultParams) {
  // 在表单部件中的数据保存成功时刷新树
  if (defaultParams.moduleActionType === 'form-save') {
    // 表单保存成功的回调
    var self = this; // 重置作用域
    var treePanel = self.findElement("tree_panel_1g58v4"); // 获取树面板元素
    
    // 保持树当前滚动到的位置
    treePanel.keepTreePositon();
    
    // 执行数据刷新
    treePanel.$$refreshData().then(() => {
      // 选中新增的数据节点
      if (defaultParams.id && treePanel.$$clickNode) {
        // 如果是异步树，需要增加下面注释的这一行展开节点的方法调用
        // 指定节点的所有上级节点均会展开
        // treePanel.$$setExpandKeys([defaultParams.id]);
        
        // 点击选中新增节点
        treePanel.$$clickNode(defaultParams);
      }
    });
  }
}
```

## 树节点点击事件配置

### 配置步骤
1. 打开树组件的高级面板
2. 绑定动作 `onclick()` 点击树节点事件
3. 配置自定义动作脚本

### 参数说明
树节点点击事件中的 `params` 参数包含：
- `params.data`: 节点数据对象
- `params.data.id`: 节点ID
- `params.data.name`: 节点名称
- `params.data.columns`: 节点的自定义字段数据

## 树组件常用方法

### 获取树面板元素
```javascript
var treePanel = this.findElement("tree_panel_1g58v4");
```

### 刷新树数据
```javascript
treePanel.$$refreshData();
```

### 设置额外参数（用于过滤）
```javascript
treePanel.$$setExtraParams({
  filter_field: filter_value
});
```

### 保持树滚动位置
```javascript
treePanel.keepTreePositon();
```

### 点击选中节点
```javascript
treePanel.$$clickNode(nodeParams);
```

### 设置展开的节点（异步树）
```javascript
treePanel.$$setExpandKeys([nodeId1, nodeId2, ...]);
```

## 树组件数据操作

### 获取选中节点数据
```javascript
function main() {
  // 假设这是某个按钮的点击事件
  // 获取树组件实例
  var treeComponent = this.$$("tree_component_id");
  
  // 获取选中的节点数据
  var selectedNodes = treeComponent.getSelectedNodes();
  
  if (selectedNodes && selectedNodes.length > 0) {
    var nodeId = selectedNodes[0].id;
    var nodeName = selectedNodes[0].name;
    
    // 使用节点数据进行后续操作
  }
}
```

### 设置树数据过滤
```javascript
function main() {
  var treeComponent = this.$$("tree_component_id");
  
  // 设置过滤参数
  treeComponent.$$setExtraParams({
    "regionId": regionId,
    "regionType": regionType,
    "status": "active"
  });
  
  // 刷新树数据
  treeComponent.$$refreshData();
}
```

## 常见场景示例

### 场景1：组织架构树-部门信息表单
```javascript
function main(params) {

  
  // 找到页面中的表单渲染组件
  var pageFormWidget = this.$$("form_part_department_info");
  if (pageFormWidget && pageFormWidget.$children) {
    var formRender = pageFormWidget.$children[0];
    
    // 给表单传参，根据部门ID查询部门信息
    formRender.$$setFormValue({
      "department_id": params.data.id,
      "documentNo": params.data.id  // 用于反查表单数据
    });
  }
}
```

### 场景2：地区树-案件列表
```javascript
function main(params) {

  const pageRootList = this.$$roots();
  let rootPageElement = pageRootList[0];
  
  // 找到页面中的案件列表组件
  var caseList = rootPageElement.$$element("card_container_case_list");
  
  if (caseList) {
    var listElement = caseList.$$getListElement();
    if (listElement) {
      // 设置查询参数
      listElement.$$setExtraParams({
        "regionId": params.data.id,
        "regionName": params.data.name
      });
      // 刷新列表
      listElement.$$refreshData();
    }
  }
}
```

### 场景3：产品分类树-产品详情
```javascript
function main(params) {

  // 获取页面根元素
  const pageRoot = this.$$roots();
  let rootPageElement = pageRoot[0];
  
  // 找到产品详情部件
  var pageDetail = rootPageElement.$$element("page_detail_product");
  var detailRootElement = pageDetail.$children[0];
  
  if (detailRootElement) {
    var dataEngine = detailRootElement.dataEngine
    
    // 将分类ID设置为查询参数
    dataEngine.defaultParams = {
      "categoryId": params.data.id,
      "categoryName": params.data.name
    };
    dataEngine.queryData();
  }
}
```

### 场景4：设备树-设备状态树（级联）
```javascript
function main(params) {
  
  const pageRoot = this.$$roots();
  let rootPageElement = pageRoot[0];
  
  // 找到设备状态树部件
  let statusTree = rootPageElement.$$element("page_tree_device_status");
  
  if (statusTree) {
    if (statusTree.dataEngine && statusTree.dataEngine.state) {
      // 根据选中的设备ID过滤状态树
      statusTree.$children[0].$$setExtraParams({
        "deviceId": params.data.id
      })
      
      let treeComp = statusTree.dataEngine.state.getElement("tree_panel_status");
      if (treeComp) {
        treeComp.$$refreshData();
      }
    }
  }
}
```

## 最佳实践

### 1. 节点数据获取
- 使用 `console.log(params)` 先查看节点数据结构
- 根据实际数据结构访问相应的字段
- 注意区分节点ID和节点名称

### 2. 性能优化
- 避免频繁的树数据刷新
- 使用 `keepTreePositon()` 保持用户浏览位置
- 合理设置树的加载方式（同步/异步）

### 3. 用户体验
- 提供清晰的节点点击反馈
- 合理设置树的默认展开级别
- 考虑树的深度和节点数量对性能的影响

### 4. 错误处理
- 检查组件是否存在再进行操作
- 处理空数据情况
- 提供友好的错误提示

### 5. 数据一致性
- 确保树节点的唯一标识正确
- 更新树数据后及时刷新相关组件
- 注意参数名称的一致性

### 6. 联动逻辑
- 明确树组件与其他组件的数据流向
- 避免循环联动导致的数据不一致
- 合理使用参数传递机制
