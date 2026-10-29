# 表单脚本指南

## 表单脚本核心功能

### 1. API调用脚本

### API调用方法

#### `api.DATA_SOURCE_EXECUTE(apiId, type, params, extraParams, body)`
**用途**: 调用已注册的API
**参数**:
- `apiId`: API的ID（在注册API时获得）
- `type`: API类型，如果是在api管理中注册的API，type为api；如果是数据模型，type为ddcat
- `queryParams`: 参数为query时使用
- `formDataParams`: 参数为formData时使用
- `jsonParams`: 参数为json时使用

```javascript
// 方式1: queryParams参数
let queryParams = [
  { "name": "regionId", "valueContent": '1' },
  { "name": "regionType", "valueContent": '2' },
];
api.DATA_SOURCE_EXECUTE(apiId, "api", queryParams, [], "").then(res => {}).catch(err => {});

// 方式2: formDataParams参数
let formDataParams = [
  { "name": "regionId", "type": "FormData", "valueContent": '1' },
  { "name": "regionType", "type": "FormData", "valueContent": '2' },
];
api.DATA_SOURCE_EXECUTE(apiId, "api", [], formDataParams, "").then(res => {}).catch(err => {});

// 方式3: JSON参数
let params = {'regionId': '1', 'regionType': '2'}
api.DATA_SOURCE_EXECUTE(apiId, "api", [], [], JSON.stringify(params))
```

### 2. 文本组件自定义样式

#### 提示信息样式
```javascript
const tipDom = `<div style="background: rgb(245, 250, 255)">
  <div style="color: rgba(45, 75, 115, 0.6); background: rgba(45, 75, 115, 0.04)">
    提示：上传照片数量不超过5张，<span style="color: #2d4b73;font-weight: 500;">单张照片大小不超过5MB</span>。
    建议上传2张以上照片，能反映周边环境，以便工作人员快速确定位置。
  </div>
</div>`;
this.$$('text_g8ufdb').$$setValue(tipDom)
```

#### 自定义标题样式
```javascript
const titleDom = `<div style="display: flex;background-color:rgb(245, 250, 255);align-items: center;">
  <div style="display: inline-block;margin-right: 12px;background-color:#0091fa;width: 4px;height: 16px"></div>
  <div style="font-size: 16px;font-weight: 700;line-height: 44px;color: #2d4b73">最新上报案件</div>
</div>`;
this.$$('text_component_id').$$setValue(titleDom)
```

#### 复杂统计卡片样式
```javascript
function main() {
    /** 获取数据 */
    const xslCount = 1234;
    const czzAllCount = 815;
    const czzOverTimeCount = 20;
    const ybjAllCount = 815;
    const ybjOverTimeCount = 20;

    /** 样式 */
    const domStyle = `"display: flex;padding: 16px 24px;background-image: linear-gradient(179deg, #FFFFFF 50%, #F0F0F5 100%);border: 1px solid #ffffffcc;box-shadow: 0 8px 16px 0 #2d4b731a;border-radius:8px;"`
    const dom1Style1 = "font-size:32px;font-style:Italic;font-weight:600;margin-right:2px";
    const labelStyle = "color:#2D4B73;opacity:0.6;line-height:20px;margin-bottom:4px";
    const titleStyle = "color:#2D4B73;line-height:20px;margin-bottom:4px;margin-right:8px";
    const valueStyle1 = "color:#3A75C6;line-height:20px;margin-bottom:4px";
    const valueStyle2 = "color:#FF5023;line-height:20px;margin-bottom:4px";
    const lineStyle = `"position: absolute;right: 24px;width: 1px;background: #2D4B73;opacity: 0.1;top: 8px;height: calc(100% - 16px)"`

    /** 渲染dom */
    const dom1 = `<div style="width: 150px;position: relative">
      <div style=${lineStyle}></div>
      <div style="line-height:20px;margin-bottom:12px">线索量</div>
      <div><span style=${dom1Style1}>${xslCount}</span><span>件</span></div>
    </div>`;
    
    const dom21 = `<div>
      <div style=${labelStyle}>处置中</div>
      <div><span style=${titleStyle}>总量</span><span style=${valueStyle1}>${czzAllCount}</span></div>
      <div><span style=${titleStyle}>超期</span><span style=${valueStyle2}>${czzOverTimeCount}</span></div>
    </div>`;
    
    const dom22 = `<div>
      <div style=${labelStyle}>已办结</div>
      <div><span style=${titleStyle}>总量</span><span style=${valueStyle1}>${ybjAllCount}</span></div>
      <div><span style=${titleStyle}>超期</span><span style=${valueStyle2}>${ybjOverTimeCount}</span></div>
    </div>`;
    
    const dom2 = `<div style="width: calc(100% - 150px);display: flex;justify-content:space-between">${dom21}${dom22}</div>`;
    const dom = `<div style=${domStyle}>${dom1}${dom2}</div>`;
    
    this.$$('text_g8ufdb').$$setValue(dom)
}
```

### 3. 组件操作脚本

#### 组件显示/隐藏
```javascript
// 方法1: 使用$$setBehavior
this.$$("single_select_29x4vt").$$setBehavior("HIDDEN"); // 隐藏
this.$$("single_select_29x4vt").$$setBehavior("NORMAL"); // 显示
this.$$("single_select_29x4vt").$$setBehavior("DISABLED"); // 禁用

// 方法2: 修改模型属性
this.$$model("single_select_29x4vt").props.behavior.value = "HIDDEN";
```

#### 组件赋值
```javascript
// 普通文本组件
this.$$('text_component_id').$$setValue('文本内容');

// 下拉框组件
this.$$('select_component_id').$$setValue('选项值');

// 日期组件
this.$$('date_component_id').$$setValue('2024-01-01');

// 看板指标、图表组件
this.$$m('组件id标识').props.dataSource.options = 要赋的值;
```

### 4. 下拉框默认选中第一个

```javascript
function main() {
  const CUR_SELECT_ID = "single_select_derieh";
  const FORM_ID = "form_part_7pylcw"
  var self = this;
  var counter = 1;
  var maxNum = 1000;
  let t = setInterval(() => {
    counter++;
    if (counter >= maxNum) {
      clearInterval(t);
    }
    const curModel = self.$$model(CUR_SELECT_ID);
    
    if (curModel.props.dataSource.options.length) {
      curModel.props.defaultValue.value = curModel.props.dataSource.options[0].value;
      var ele = self.$$element(FORM_ID);
      if (ele && ele.$$getRenderElement) {
        var formInputView = ele.$$getRenderElement();
        const extra = ele.state.extraParams || {};
        extra[CUR_SELECT_ID] = curModel.props.dataSource.options[0].value;
        formInputView.$$setFormValue(extra);
      }
      console.log("single-select");
      clearInterval(t);
    }
  }, 10)
}
```

### 5. 数据操作脚本

#### 更新表数据
```javascript
const formula = "UPSERT('t_6ee8543360424ab685aa5432969882e5',QUERY_EQ('id'," + id + "),'',['delete_flag','1'],['id'])";
api.EXEC_FORMULA(formula).then(() => {
  // 成功回调
}).catch(err => {
  // 错误处理
})
```

#### 批量插入数据
```javascript
function insertData(rec_id) {
    const opinion = "意见内容";
    const create_human_id = "用户ID";
    const create_human_name = "用户名";
    const create_time = "2024-01-01";
    
    const formula = "INSERT('ds_tbl_t_068bc22d46b74ebabeb986f994714d2f',[" +
        "'rec_id','" + rec_id + 
        "','opinion','" + opinion + 
        "','create_human_id'," + create_human_id + 
        ", 'create_human_name','" + create_human_name +
        "','create_time','" + create_time + 
        "', 'report_state', 1, 'delete_flag', 0])";

    return new Promise((resolve, reject) => {
        api.EXEC_FORMULA(formula).then((res) => {
            if (res) {
                resolve(res)
            } else {
                reject({hasError: true, message: '插入失败'})
            }
        }).catch(err => {
            reject(err)
        });
    })
}

// 批量执行
const recIds = [1,2,3];
const promiseAll = recIds.map(rec_id => {
    return insertData(rec_id);
});

Promise.all(promiseAll).then(res => {
    // 全部成功回调
    console.log('批量插入成功', res);
}).catch(err => {
    // 有失败回调
    console.error('批量插入失败', err);
})
```

### 6. 表单提交脚本（移动端）

```javascript
function main() {
    const widgetForm = this.state.getElement("form_part_9kufhe")
    const form = widgetForm.$refs.form
    const dom = this.$$("form_part_9kufhe")
    let that = this
    
    form.$$validateData().then((validate) => {
        if (validate && validate.message) {
            that.$ztToast(validate.message ? validate.message : "数据校验失败")
        } else {
            that.$ztDialog.confirm({
                message: '确认提交吗？'
            }).then(() => {
                dom.onSubmit().then(() => {
                    that.$ztToast("提交成功")
                    that.$route.query.refresh = "1";
                    that.$router.go(-1);
                }).catch(err => {
                    that.$ztToast("提交失败：" + err)
                })

            })
        }
    })
}
```

### 7. 表单模式切换

```javascript
function main() {
    // 找到页面中的表单组件元素
    var targetForm = this.$$("form_part_hljfd4");
    
    // 如果是编辑模式，则将表单设置为只读模式
    if (targetForm.data.props.mode == 'edit') {
        targetForm.data.props.mode = 'view';
    }
    // 反之，如果是只读模式，设置为编辑模式
    else if (targetForm.data.props.mode == 'view') {
        targetForm.data.props.mode = 'edit';
    }
}
```

### 8. AES加密实现

```javascript
function main() {
    // 获取前端加密密钥
    const GET_CRYPTOGRAM_ID = "b212e163-7dc2-4d18-85bd-dc5cd3adac6e"
    api.DATA_SOURCE_EXECUTE(GET_CRYPTOGRAM_ID, "api", [], [], "").then(res => {
        if (!res.hasError) {
            const result = JSON.parse(res.result)
            const cryptogram = result.resultInfo.data.cryptogram;
            sessionStorage.setItem("system_cryptogram", cryptogram)
        }
    }).catch(err => {
        console.error(err);
    });
    
    // 加载crypto-js库
    load("https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/crypto-js.min.js").then(() => {
        window.aesEncrypt = aesEncrypt;
    })
}

// 加载外部JS库
function load(src) {
    if (window.CryptoJS) {
        return;
    }
    const script = document.createElement('script');
    script.src = src;

    return new Promise((resolve, reject) => {
        script.onload = () => {
            console.log('finish loading lib from ' + src);
            resolve();
        };
        script.onerror = (error) => {
            console.error('Error loading lib from ' + src, error);
            reject(error);
        };
        document.head.appendChild(script);
    });
}

// AES加密函数
function aesEncrypt(word, key) {
    const _word = CryptoJS.enc.Utf8.parse(word);
    const encodeMD5 = CryptoJS.MD5(key).toString();
    let _key = encodeMD5.substring(0, 16).toUpperCase();
    _key = CryptoJS.enc.Utf8.parse(_key);
    let _iv = encodeMD5.substring(16).toUpperCase();
    _iv = CryptoJS.enc.Utf8.parse(_iv);

    const encrypted = CryptoJS.AES.encrypt(_word, _key, {
        iv: _iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
    });
    return encrypted.toString();
}
```

### 9. pc页面跳转后获取前置页面传参

```javascript
const actId = that.state.extraParams.actId;
```

### 10.弹窗操作
#### 打开部件弹窗
```javascript
api.MODULE_DIALOG(that, "LIST", "eb3eb476-c9cf-446a-baf2-316e1f9c55ec", {
  linkAction: {
    moduleModalTitle: "案件列表",
    moduleModalPosition: "bottom", // left right middle top bottom
    moduleModalSize: "custom", // fullscreen custom
    moduleModalWidth: 800,
    moduleModalHeight: 500,
    moduleOpenMask: true,
    isDetail: true
  },
  callback: (actionType, params) => {
    console.log(actionType, params);
  },
  params: {
    "recIdStr": recIdStr
  }
});
```

#### 麒舰中关闭弹窗
```javascript
// 如果在麒舰环境中使用，请使用以下代码
function closeMedal() {
  const modalDom = document.querySelector(".ant-modal-content")
  if (modalDom) {
    const closeButton = modalDom.querySelector(".ant-modal-close")
    closeButton && closeButton.click()
  }
}
// 其他情况使用以下代码
function main() {
    if (window.parent) {
        window.parent.postMessage(JSON.stringify({
            event: "close-dialog",
            param: { "XXX": "test" }
        }), "*");
    }
}
```

#### 移动端通过脚本关闭弹窗
```javascript
function main() {
  const pops = document.querySelectorAll(".zt2-popup");
  if (pops.length > 0) {
    var latestPop = pops[pops.length - 1];
    var closeButton = latestPop.querySelector(".zt2-icon");
    if (closeButton && closeButton instanceof HTMLElement) {
      closeButton.click();
    }
    latestPop.remove();
  }
}
```

### 11. 在麒舰中刷新菜单

```javascript
//发送请求格式如下， refresh 控制是否刷新页面 true刷新，false不刷新 
window.postMessage(JSON.stringify({
    app: 'linglong',
    event: 'app:window-message:tasklist:task-menu',
    param: {
        visible: false,
        refresh: false
    }
}))
```

## 最佳实践

### 1. 样式管理
- 建议将所有样式定义为变量，提高可读性和可维护性
- 对于复杂样式，优先考虑开发定制组件

### 2. 错误处理
- 所有API调用都应该添加`.catch()`错误处理
- 对组件操作前检查组件是否存在

### 3. 性能优化
- 避免在循环中频繁操作DOM
- 使用批量操作替代单个操作

### 4. 兼容性
- 注意PC端和移动端的API差异
- 某些功能在不同灵珑版本中可能有不同的实现方式
