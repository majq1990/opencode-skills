# 灵珑全局常用API参考

## 常用的API方法

### 组件查找方法

#### `this.$$(componentId)`
**用途**: 通过组件ID查找组件实例
**返回**: 组件对象

```javascript
// 获取组件实例
const component = this.$$('form_part_9kufhe');

// 获取组件的值
const value = component.$$getValue();

// 设置组件的值
component.$$setValue('新值');

// 设置组件行为（隐藏/显示/禁用）
component.$$setBehavior("HIDDEN"); // HIDDEN/NORMAL/DISABLED
```

#### `this.$$m(componentId)`
**用途**: 获取组件的模型对象，可以访问组件的属性
**返回**: 组件模型对象

```javascript
const model = this.$$m(componentId);
// 访问组件属性
model.props.behavior.value = "HIDDEN";
model.props.dataSource.options = [...];
```

#### `this.$$element(componentId)`
**用途**: 获取组件的DOM元素
**返回**: Vue组件实例

```javascript
const element = this.$$element("form_part_7pylcw");
const formInputView = element.$$getRenderElement();
```

#### `api.EXEC_FORMULA(formula)`
**用途**: 执行灵珑公式，用于数据操作
**参数**: 公式字符串

```javascript
// 更新数据
const formula = "UPSERT('table_id',QUERY_EQ('id'," + id + "),'',['delete_flag','1'],['id'])";
api.EXEC_FORMULA(formula).then(() => {}).catch(err => {})

// 插入数据，INSERT (目标表id, [目标列1,目标值1,目标列2,目标值2....])，目标表为实体表对应的id，字段取id或名称都可以 
const formula = "INSERT('table_id', ['field1', 'field2'], ['value1', 'value2'])";
api.EXEC_FORMULA(formula);
```
### 消息提示方法

#### PC端消息提示
```javascript
this.$message.success('成功消息');
this.$message.error('错误消息');
this.$message.info('常规消息');
this.$message.warn('警告消息');
this.$message.warning('警告消息');
this.$message.loading('加载中');
```

#### 移动端消息提示
```javascript
this.$ztToast.success('操作成功');
this.$ztToast.fail('操作失败');
this.$ztToast.loading('加载中');
```

### 对话框方法

#### PC端对话框
```javascript
this.$$confirm({
  headerTitle: "确定执行该动作吗？",
  content: "内容",
  type: "info", // danger info warning
  onOk: () => {
    alert("确定操作");
  },
  onCancel: () => {
    alert("取消操作");
  }
}).then(() => {}).catch(() => {})
```

#### 移动端对话框
```javascript
this.$ztDialog.confirm({
  title: "提示",
  message: "确认关注吗？",
  confirmButtonText: "确定",
  cancelButtonText: "取消",
}).then(() => {}).catch(() => {})
```

### 表单操作方法

#### 表单数据校验
```javascript
const widgetForm = this.state.getElement("form_part_9kufhe")
const form = widgetForm.$refs.form

form.$$validateData().then((validate) => {
  if (validate && validate.message) {
    // 校验失败
    this.$ztToast(validate.message);
  } else {
    // 校验成功
    dom.onSubmit().then(() => {
      this.$ztToast("提交成功")
    }).catch(err => {
      this.$ztToast("提交失败：" + err)
    })
  }
})
```

#### 表单模式切换
```javascript
var targetForm = this.$$("form_part_hljfd4");
if (targetForm.data.props.mode == 'edit') {
  targetForm.data.props.mode = 'view'; // 切换为只读模式
}
```


### 看板组件数据赋值

#### 图表和表格组件赋值
```javascript
// 看板指标展示、柱状图、横向柱状图、排序表格、带类型的饼图组件
this.$$m('组件id标识').props.dataSource.options = 要赋的值;
```

### 路由参数获取

#### 获取路由参数
```javascript
// 获取params参数
const params = this.$route.params;

// 获取query参数
const title = this.$route.query.title;

// PC端获取自定义参数
const params = this.$$getRouteView().currentParams;
```
### 页面中表单部件脚本
#### 页面中表单部件的数据提交
```javascript
this.$$("form_part_bv3373").onSubmit();    //form_part_bv3373为页面中表单部件的id
this.$$("form_part_bv3373"). $$getRenderElement().$$saveData(isSilent: boolean = false) ; //保存数据，自动给出执行结果提示信息
```

#### 页面中表单部件的数据连续提交
```javascript
this.$$element("form_part_bv3373").onContinuousSubmit();
```

#### 页面中表单部件的数据重置
```javascript
this.$$element("form_part_bv3373").onReset();
```
### 其他实用方法

#### 移动端附件下载
```javascript
const token = window.localStorage.getItem("linglong:access_token");
const fileId = "1";
const url = `${window.location.origin}/linglong-api/unity/establish/file/${fileId}/download?access_token=${token}`;
window.open(url)
```

#### 移动端拨打电话
```javascript
window.location.href = 'tel:11111111'
```

#### 原生移动端WebView关闭
```javascript
window.jsi.callNative(
  JSON.stringify({ method: "close", params: { resultCode: -1 } })
)
```

#### 根组件获取
```javascript
const pageRootList = this.$$roots();
let rootPageElement = pageRootList[0];
```
