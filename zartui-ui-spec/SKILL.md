---
name: zartui-ui-spec
description: >
  ZartUI 设计规范辅助技能（v2 — 40+ 组件完整版）。当用户需要按照 ZartUI 规范生成、检查或调整 UI 组件时触发。
  适用场景：生成符合规范的 HTML/CSS 组件、检查已有代码是否符合规范、提供组件 token 参数、构建业务页面。
  触发词：ZartUI、按规范、设计规范、组件规范、考勤系统 UI 等。
agent_created: true
spec_path: /Users/864220965qq.com/Documents/AI规范/ZartUI-Spec
last_updated: 2026-05-26
---

# ZartUI UI 规范技能（v2 完整版）

> **覆盖 40+ 组件**，基于 spec JSON 最新版本生成。每个组件对应 `*-spec.json` + `*-preview.html`。

## 规范文件位置

所有规范 JSON 文件存放于：`/Users/864220965qq.com/Documents/AI规范/ZartUI-Spec/`

---

## 目录

- [一、全局规范与设计 Token](#一全局规范与设计-token)
- [二、基础控件](#二基础控件)
- [三、数据录入](#三数据录入)
- [四、数据选择](#四数据选择)
- [五、数据展示](#五数据展示)
- [六、反馈提示](#六反馈提示)
- [七、导航布局](#七导航布局)
- [八、其他组件](#八其他组件)
- [九、页面骨架](#九页面骨架)
- [十、工作流程](#十工作流程)
- [十一、常见陷阱速查](#十一常见陷阱速查)

---

## 一、全局规范与设计 Token

### 错误提示文字（global-spec.json v1.1.0）
- 位置：组件下方，`margin-top: 4px`
- `font-size: 12px; font-weight: 400; color: #FF4433`
- ⚠️ **必须与组件包裹在同一 wrapper 内**，不能暴露在外部 flex/grid gap 环境
- 适用范围：输入框、数字输入框、下拉选择、日期选择器等一切带错误状态的表单组件

### 设计 Token（颜色语义）

| Token 用途 | 颜色值 |
|---|---|
| 品牌主色 | `#3388FF` |
| 品牌 Hover | `#5CA5FF` |
| 品牌 Active / 深蓝 | `#2167D9` |
| 外发光阴影 | `0 0 0 2px #D6EDFF` |
| 文字主色 | `#223355` |
| 文字标题 | `#081126` |
| 文字副色 | `#6B7A99` |
| 文字占位/禁用 | `#A8B4C8` |
| 描边默认 | `#DDE1EB` |
| 描边禁用 | `#E9ECF2` |
| 背景浅灰 | `#F5F7FA` |
| 背景品牌浅 | `#F0F9FF` |
| 错误红 | `#FF4433` |
| 成功绿 | `#06A17F` / `#11C79B` |
| 警告橙 | `#FF6600` / `#FFAA33` |
| 分隔线 | `#E9ECF2` |

### 字体规范
- 主字体：PingFangSC-Regular
- 标题字重：500（14px）/ 400（正文）
- 正文字号：14px，辅助字号：12px/13px

### 圆角规范
- 小圆角：`4px`（按钮、输入框、标签）
- 中圆角：`8px`（面板、卡片）
- 全圆角：`100px` / `16px`（pill 按钮、搜索框）
- 圆形：`50%`（头像、徽标、单选框）

---

## 二、基础控件

### 2.1 矩形按钮（button-spec.json v2.0.0）
- `border-radius: 4px; padding: 0 16px; border: 1px solid`
- **尺寸**：md = `height:32px; font-size:14px`，sm = `height:24px; font-size:12px`
- **过渡**：`background 0.15s, border-color 0.15s, color 0.15s`

**面状按钮（solid）** — 用于提交/保存/确定：
| 状态 | background | border-color | color |
|---|---|---|---|
| Normal | #3388FF | #3388FF | #FFF |
| Hover | #5CA5FF | #5CA5FF | #FFF |
| Click | #2167D9 | #2167D9 | #FFF |
| Disabled | #ADD8FF | #ADD8FF | #FFF + pointer-events:none |

**线状按钮（outline）** — 用于取消/重置等次要操作：
| 状态 | background | border-color | color |
|---|---|---|---|
| Normal | #FFF | #DDE1EB | #223355 |
| Hover | #F0F9FF | #3388FF | #3388FF |
| Click | #D6EDFF | #3388FF | #3388FF |
| Disabled | #FFF | #F5F7FA | #CED4E0 + pointer-events:none |

**内容变体**：仅文字 / 图标+文字

### 2.2 全圆角按钮（button-pill-spec.json v3.0.0）
- `border-radius: 100px`，尺寸同矩形按钮

**主按钮（primary）** — 新增/创建/添加：
- Normal: `bg:#FFF; border:#DDE1EB; color:#3388FF`
- Hover: `bg:#F0F9FF; border:#3388FF; color:#3388FF`
- Click: `bg:#D6EDFF; border:#3388FF; color:#3388FF`
- Disabled: `bg:#FFF; border:#F5F7FA; color:#ADD8FF`

**次要按钮（secondary）** — 导入/导出/编辑/设置：
- Normal: `bg:#FFF; border:#DDE1EB; color:#223355`
- Hover/Click: bg 变浅蓝，border/color 变 `#3388FF`

**危险按钮（danger）** — 删除/禁用（Normal 同次要，仅 hover/click 变红）：
- Hover: `bg:#FFF4F0; border:#FF4433; color:#FF4433`
- Click: `bg:#FFDFD6; border:#FF4433; color:#FF4433`

**内容变体**：仅文字 / 图标+文字 / 文字+下拉箭头

### 2.3 复选框（checkbox-spec.json v1.0.0）
- 尺寸：`16×16px; border-radius: 4px; label-gap: 8px`

| 状态 | border | background | 图标 |
|---|---|---|---|
| Default | 1px solid #A8B4C8 | #FFF | 无 |
| Hover | 1px solid #3388FF | #FFF | 无 |
| Indeterminate | 1px solid #3388FF | #3388FF | 白色横线 8×2px |
| Checked | 1px solid #3388FF | #3388FF | 白色勾 SVG path M1.5 4L4 6.5L8.5 1.5 |
| Disabled Default | 1px solid #DDE1EB | #F5F7FA | 无 |
| Disabled Checked | 1px solid #ADD8FF | #ADD8FF | 白色图标 |

- 勾选图标用 inline SVG，stroke-width:2, stroke-linecap/strokejoin: round
- 半选横线高度 2px + border-radius: 1px（圆润末端）

### 2.4 单选框（radio-spec.json v1.1.0）
- 尺寸：`16×16px; border-radius: 50%; label-gap: 6px`

| 状态 | border | background |
|---|---|---|
| Default | 1px solid #A8B4C8 | #FFF |
| Hover | 1px solid #3388FF | #FFF |
| Checked | **5px solid #3388FF** | #FFF（加粗描边，无内圆点） |
| Disabled Default | 1px solid #DDE1EB | #F5F7FA |
| Disabled Checked | 5px solid #ADD8FF | #FFF |

**卡片单选（card-radio）**：
- sm: `width:200px; padding:16px`，lg: `width:320px; padding:20px`
- Card: `border-radius:8px; border:1px solid #DDE1EB`; hover 边框 `#3388FF`; checked 边框 `#3388FF`
- 单选圆点位于右侧垂直居中 `top:50%; right:16px; transform:translateY(-50%)`

### 2.5 开关（switch-spec.json v1.0.0）

**20px 规格**（常用）：
- 轨道：`width:36-44px; height:20px; border-radius:10px`
- 滑块：`16×16px; bg:#FFF; border-radius:50%; offset:2px`
- 过渡：`background 0.2s, left 0.2s`

| 状态 | 背景 |
|---|---|
| On | #3388FF |
| Off | #A8B4C8 |
| On Hover | #5CA5FF |
| Off Hover | #CED4E0 |
| On Disabled | #ADD8FF |
| Off Disabled | #DDE1EB |

**三种变体**：with_text（宽44px）、with_icon（宽36px）、plain（宽36px）

**16px 规格**（小尺寸）：轨道高16px，滑块12px，宽度按比例缩小

### 2.6 标签（tag-spec.json v1.0.0）

**尺寸**：
- md: `height:24px; padding:0 6px; font-size:14px; border-radius:4px`
- sm: `height:20px; padding:0 6px; font-size:12px; border-radius:4px`

**基础标签**：
| 类型 | background | color |
|---|---|---|
| 实心 | #3388FF | #FFF |
| 浅色 | #F0F9FF | #3388FF |
| 可关闭 | #F5F7FA | #223355（右侧 12×12px 关闭图标） |
| 带图标 | #F5F7FA | #223355（左侧 12×12px 图标） |

**重要提示（实色背景，文字固定 #FFF）**：
| 名称 | default | hover | active |
|---|---|---|---|
| 主要 | #3388FF | #5CA5FF | #2167D9 |
| 警示 | #FF6600 | #FF8629 | #D94F00 |
| 错误 | #FF4433 | #FF6F5C | #D92A21 |
| 成功 | #06A17F | #11C79B | #007A64 |
| 默认 | #6B7A99 | #C3CAD9 | #223355 |

**一般提示（浅色背景固定，文字变色）**：
| 名称 | background | text-default | text-hover |
|---|---|---|---|
| 主要 | #F0F9FF | #3388FF | #5CA5FF |
| 警示 | #FFD4A3 | #D94F00 | #FF6600 |
| 错误 | #FFF4F0 | #FF4433 | #FF6F5C |
| 成功 | #B6FAE0 | #06A17F | #11C79B |
| 默认 | #F5F7FA | #223355 | #6B7A99 |

**弱提示**：`border:1px; background:transparent` + 同色文字

**标签组**：4~5 个可关闭标签 + 末尾新增按钮（点击变为 32px 高输入框）

### 2.7 分页（pagination-spec.json v1.0.0）

**基础分页** = 总条目(14px/#6B7A99) + 页码按钮(32×32px) + 箭头(14×14px线状)
- 按钮：`border:1px solid #DDE1EB; border-radius:4px; gap:6px`
- Active/Hover: `border-color:#3388FF; color:#3388FF`
- Disabled: `border-color:#E9ECF2; color:#C0C7D6`
- 省略号：`···` / `#6B7A99` / 不可点击

**高级分页** = 基础 + 每页条数下拉 + 跳转输入框
- 条数下拉：`height:32px; border-radius:4px; appearance:none` + 伪元素箭头
- 跳转输入框：`52×32px; border-radius:4px; text-align:center`

**迷你分页** = 左箭头(28×28px无边框) + 当前页输入框(28×28px正方形) + `/`(分隔符) + 总页数 + 右箭头
- 当前页输入框：`color:#3388FF; border:1px solid #DDE1EB; border-radius:4px`

### 2.8 进度条（progress-spec.json v1.1.0）

**常规进度条**：
- 轨道：`width:320px; height:4px; border-radius:2px; track:#E9ECF2`
- 状态：default(#E9ECF2), progress(#3388FF), error(#FF4433), success(#11C79B)
- 右侧状态区：13px 数字 / 16×16px 图标

**圆形进度条**：
- 尺寸：`64×64px; stroke-width:4px; radius:30px`
- 实现：图标与进度弧在同一 SVG 内（避免叠层遮挡）
- 中心文字：14px/500 居中
- 状态：default(track+#F5F7FA/bar+#F5F7FA), progress(bar:#3388FF), error(bar:#FF4433), success(bar:#11C79B)

---

## 三、数据录入

### 3.1 输入框（input-spec.json v2.0.0）

**单行输入框**：
- `height:32px; border-radius:4px; font-size:14px; padding:0 12px 0 8px`

| 状态 | border | background | 其他 |
|---|---|---|---|
| Default | 1px solid #DDE1EB | #FFF | placeholder:#A8B4C8 |
| Hover | 1px solid #3388FF | #FFF | 有内容时显示清除图标 |
| Active/Focus | 1px solid #3388FF | #FFF | box-shadow:0 0 0 2px #D6EDFF |
| Disabled | 1px solid #E9ECF2 | #F5F7FA | color:#A8B4C8; pointer-events:none |
| Error | 1px solid #FF4433 | #FFF | 下方错误提示 |

**清除图标**：16×16px，面状灰色实心圆+白色×，fill:#A8B4C8
- 仅「hover 且有内容」或「focus 且有内容」时显示
- 有后缀时放入 suffix flex 容器作第一子元素

**多行输入框（Textarea）**：
- `min-height:84px; padding:4px 12px 24px 8px; resize:vertical; border-radius:4px`
- 字数统计绝对定位于右下角内部：12px
  - 正常:#A8B4C8 | 接近上限(≥80%):#FF6600 | 超出:#FF4433

**前置选择（prepend）**：
- Default: `bg:#F5F7FA; border:1px solid #DDE1EB; border-radius:4px 0 0 4px`
- Active: `bg:#FFF; border:#3388FF`（只有前置激活时变白）
- 与输入框拼接：`margin-left:-1px` 消除双线
- 下拉面板：`offset:4px; bg:#FFF; border:1px solid #E9ECF2; box-shadow:0 4px 12px rgba(34,51,85,0.1); item-height:36px`

**后置选择（append）**：
- `bg:#F5F7FA`（**始终不变**，激活时也不变白！）
- `border-radius:0 4px 4px 4px`
- 与输入框拼接：`margin-left:-1px`

**搜索框变体**：
- 即时搜索框：`border-radius:16px; height:32px;` 左侧 14×14px 图标
- 常规搜索框：全圆角；右侧 44px 搜索图标区域 + 1px 分隔线

### 3.2 数字输入框（number-input-spec.json v1.0.0）

**通用规格**：`height:32px; border-radius:4px; font-size:14px`

**Type1 — 固定单位**：`数字输入 | 上下箭头(20px宽) | 固定单位`
- 上下箭头：icon 10×10px，hover bg #F5F7FA，active icon #3388FF
- 单位区：`padding:0 10px; font-size:13px; color:#6B7A99; border-left:1px solid #E9ECF2`

**Type2 — 后置单位下拉**：`数字输入+箭头 | 单位下拉选择`
- 下拉区：`bg:#F5F7FA; padding:0 6px; hover:bg:#EEF5FF`
- 拼接：`margin-left:-1px`
- 下拉面板：`bg:#FFF; border:1px solid #E9ECF2; border-radius:4px; item-height:32px`

**Type3 — 加减按钮**（表单内常用）：`减号(32px) | 分隔线 | 输入区(flex:1,min-w:48px) | 分隔线 | 加号(32px)`
- 按钮 icon 14×14px，stroke #6B7A99，hover bg #F5F7FA，active icon #3388FF
- 分隔线：1px #E9ECF2

### 3.3 验证码（captcha-spec.json v1.0.0）
- 布局复用 formitem 规范（水平/垂直两种）
- **行内验证码**：输入框(flex:1) + 验证码图(96×32px)，gap:8px
- **大图验证码**：输入框(240px宽) + 验证码图(240×96px)，垂直排列
- 验证码图：`border:1px solid #DDE1EB; border-radius:4px; bg:#F5F7FA`
- 点击刷新：hover overlay `bg:rgba(255,255,255,0.72)` + 刷新图标 20×20px #3388FF

### 3.4 上传（upload-spec.json v1.0.0）
- 上传按钮复用 button outline 规格（32px高, 16px水平padding）
- 文件列表项：`width:378px; height:40px; bg:#F5F7FA; border-radius:4px`
- 文件图标：彩色面状 16×16px（doc=#3388FF/W, xls=#11C79B/X, pdf=#FF4433/PDF, ppt=#FF6600/P, zip=#6B7A99/Z）
- 状态：uploading（底部进度条 2px #3388FF），done（预览/删除操作），error（红色背景#FFF5F5）

**图片上传 — 缩略图网格**：
- 新增按钮/缩略图均为 60×60px，`border-radius:4px; border:1px solid #E9ECF2`
- hover overlay: `bg:rgba(34,51,85,0.55)` + 文件名 9px + 预览图标 16px

**图片上传 — 行式列表**：item 378×60px，缩略图 40×40px

**拖拽上传**：400×84px
- Default: `bg:#F5F7FA; border:1px solid #DDE1EB`
- Dragover: `bg:#D6EDFF; border:1px dashed #3388FF`（注意要切虚线！）

### 3.5 评分（rating-spec.json v1.0.0）
- 基础：5 个图标，gap:6px，item-size:24px，hover scale:1.15
- 未选中色：#DDE1EB，禁用选中色：#FFD580

**图标形状及激活色**：
| 形状 | 激活色 |
|---|---|
| 星星 | #FFAA00 |
| 心形 | #FF4433 |
| 火焰 | #FF4433 |
| 闪电 | #3388FF |
| 点赞手 | #FF6600 |

**表情样式**：28×28px，5 种表情（极差/较差/中等/满意/非常满意），hover 时全部同步切换形态
- 极差=发怒脸(#FF4433)，较差=哭脸(#FFAA00)，中等=平脸，满意=笑脸，非常满意=大笑脸

### 3.6 富文本（rich-text-spec.json）
- 工具栏 + 编辑区结构
- 详细参数见 `rich-text-spec.json`

### 3.7 表单控件容器（formitem-spec.json v1.0.0）

**水平布局**（标题在左）：
- display:flex; align-items:flex-start; gap:20px
- Label: `height:32px; margin-right:8px; flex-shrink:0`
- Control: `flex:1; max-width:280px`

**垂直布局**（标题在上）：
- display:grid; grid-template-columns:14px 1fr; gap:20px
- Label: `grid-column:1/3; margin-bottom:8px`
- Control: `grid-column:2/3`

**标签结构**：`*`(14px宽,#FF4433) + 标题文字(14px,#223355) + `:`(::after)
**预设宽度**：4字=56px, 6字=84px, 8字=112px, auto=max-content

**10 种控件规格**：

| 控件 | 高度 | max-width | 特殊 |
|---|---|---|---|
| 输入框 | 32px | 280px | — |
| 下拉框 | 32px | 280px | 右侧箭头 16×16px |
| 日期选择 | 32px | 280px | 右侧日历 16×16px |
| 数字输入(Type3) | 32px | 280px | 减号\|输入\|加号 |
| 多行文本 | min 80px | 280px | vertical resize |
| 上传按钮 | 32px | 由内容决定 | outline 样式 |
| Radio | 32px | — | 选项间距 20px |
| Checkbox | 32px | — | 选项间距 20px |
| Switch | 20px | — | 36×20, #3388FF开/#A8B4C8关 |
| Rate(五星) | 32px | — | 20×20px, #FFAA00选中 |

---

## 四、数据选择

### 4.1 下拉选择框（select-spec.json v2.0.0）

#### 单选下拉
**触发框**：`height:32px; border-radius:4px; padding:0 32px 0 8px`
- 箭头：16×16px, stroke:#A8B4C8, absolute right:8px
- 有值+hover → 箭头替换为清除图标（16×16px 面状实心圆×）
- 清除实现：`.has-value:hover .z-sel-clear{display:flex}` + `.has-value:hover .z-sel-chevron{display:none}`

**状态流转**：default → hover → active_open(外发光+箭头旋转变蓝) → rehover(显示清除) → reopen → completed

**下拉面板**：
- `position:fixed`（JS getBoundingClientRect 定位，绕过 overflow:hidden）
- `border-radius:8px; box-shadow:0 2px 20px rgba(34,51,85,0.16); padding:8px; z-index:3000`
- 选项：`height:40px; padding:0 8px; border-radius:4px; font-size:14px`
- 选项状态：default(#FFF), hover(#F5F7FA), selected(#F0F9FF), disabled(#A8B4C8)
- 加载态：spinner(16×16px) + "加载中…"(13px/#A8B4C8)

#### 多选下拉
**触发框**：`min-height:32px; padding:4px 32px 4px 6px; gap:4px; overflow:hidden`
- 已选标签：`height:22px; padding:0 6px; border-radius:3px; bg:#F5F7FA; font-size:12px`
- 关闭图标：10×10px, hover:bg:rgba(255,68,51,0.10), hover-color:#FF4433
- 溢出徽标：`bg:#F0F9FF; color:#3388FF`

**面板**：含搜索框(全圆角32px高) + 选项列表(max-h:192px) + 全选行 + 分割线 + 新增行
- 选项带复选框 14×14px, border-radius:3px
- 两种搜索方案：面板顶部搜索框 / 触发框内联输入

#### 树选择（tree_select / tree_multi_select）
- 触发框同普通单选/多选
- 面板：padding:4px 0; 无内边距选项
- 行高 40px, padding:0 8px(外)/margin:0 8px(内), border-radius:4px
- 节点图标 14×14px #3388FF, 展开/收起箭头 12×12px
- 子节点缩进：padding-left:20px
- 多选模式：复选框在展开箭头与节点图标之间，支持半选

#### 弹窗选择（modal_select）
- 触发框：`height:32px; padding:0 8px;` 右侧为操作区无箭头
- 方案一：图标+文字"选择"按钮（始终显示）
- 方案二：纯图标选择器；完成态显示清空+撤回+选择三图标+分隔线
- 操作图标按钮：28×28px, border-radius:4px, hover-bg:#F5F7FA

#### 自定义下拉 JS 实现
```javascript
// HTML 结构模板
<div class='z-sel' id='sel-xxx'>
  <div class='z-sel-trigger' onclick='toggleSel("sel-xxx")'>请选择</div>
  <svg class='z-sel-clear' onclick='clearSel("sel-xxx",callback)'></svg>
  <svg class='z-sel-chevron'></svg>
  <div class='z-sel-panel'>
    <div class='z-sel-option' onclick='selectOpt("sel-xxx","value",callback)'>选项</div>
  </div>
</div>

// 关键函数
function toggleSel(id){ /* 关其他 → 打开目标 → getBoundingClientRect 重定位 */ }
function selectOpt(id,value,callback){ /* 写值 → 更新DOM → 关闭面板 → callback */ }
// 外部点击关闭
document.addEventListener('click',e=>{ if(!e.target.closest('.z-sel'))关闭所有.is-open });
```

### 4.2 多选下拉框（multiselect-spec.json v1.0.0）
- 独立组件，类似 select 的 multi 但更轻量
- 触发框宽 260px，面板 fixed 定位 z-index:3000
- 含全选（顶部第一项）+ 搜索框（面板内顶部）

### 4.3 日期选择器（datepicker-spec.json）
- 复用 input 规格的触发框样式（32px高, 右侧日历图标 16×16px）
- 面板含月份切换、日期网格、时间选择（如需）
- 详细参数见 `datepicker-spec.json`

### 4.4 时间选择器（timepicker-spec.json）
- 类似 datepicker 的触发框规格
- 详细参数见 `timepicker-spec.json`

### 4.5 穿梭框（transfer-spec.json v1.1.0）
- 布局：左侧面板(240px) | 中间箭头区(40px宽) | 右侧面板(240px)

**面板结构**：
- Header(40px): 标题(14px/500/#223355) + 计数(12px/#6B7A99 "已选M/共N项") + 全选复选框
- Search: 全圆角 32px 高, 内联搜索图标 14×14px
- List: min/max-height 200px, scrollbar 4px/#E9ECF2
- Item: height 40px, padding 0 20px, checkbox 16×16px + 文字(gap:8px)
- Footer(44px): 迷你分页靠右

**穿梭按钮**：32×32px, border-radius:4px
- default: transparent/bg, color:#A8B4C8
- hover: bg:#F0F9FF, color:#3388FF
- active: bg:#3388FF, color:#FFF
- disabled: color:#C0C7D6

**树形变体**：左侧展示树结构（indent:20px, toggle-icon:12×12px），支持父节点半选

### 4.6 级联选择（cascader-spec.json）
- 面板多列联动选择
- 详细参数见 `cascader-spec.json`

---

## 五、数据展示

### 5.1 表格（table-spec.json v1.1.0）

**表头**：`height:40px; bg:#F5F7FA; border-top/bottom:1px solid #DDE1EB`
- 字体：14px/400/#223355; padding:0 12px
- 列间隔线：高16px, #E9ECF2, ::before 伪元素, left:4px, 末列不显示

**数据行**：
- 单行：`height:48px; border:1px solid #DDE1EB; hover:bg:#F5F7FA`
- 双行：`height:70px; white-space:normal; word-break:break-all`
- 文本溢出：`overflow:hidden; text-overflow:ellipsis; white-space:nowrap`

**单元格类型**：
- **链接**：color:#3388FF; hover:#2167D9; text-decoration:none
- **状态点**：直径6px, gap:6px; 成功=#06A17F, 默认=#A8B4C8, 危险=#FF4433
- **创建者**：头像(24px圆形,#3388FF) + 名字标签(24px高,bg:#F5F7FA,border-radius:100px)
- **操作**：font-size:13px; color:#3388FF; 删除hover:#FF4433; 1px #E9ECF2 分隔
- **照片列**：54×54px, border-radius:4px, 最多显示3张, 溢出显示三点气泡

**表格锁定（Sticky）**：
- ⚠️ 必须 `border-collapse:separate; border-spacing:0`
- z-index: 普通 thead th=3, sticky tbody td=4, sticky thead th=5
- 阴影：`position:fixed` + JS 监听 scroll + getBoundingClientRect 重算

**删除二次确认气泡**：
- position:fixed; width:242px; border-radius:4px
- box-shadow:0 2px 50px rgba(0,67,202,0.16); padding:12px 16px
- 标题：红色感叹号 16px + "确认删除" 14px/500/#081126
- 确定：bg:#FF4433; color:#FFF; 28px高
- 取消：border:1px solid #DDE1EB; bg:#FFF; color:#223355; 28px高

**列筛选**：
- 触发器：14×14px 漏斗图标, 默认#A8B4C8, 激活#3388FF
- 表头激活：bg:#E9ECF2
- 下拉面板：position:fixed; border-radius:4px; padding:8px; z-index:2000
- 筛选项：height:32px; padding:0 8px; checked:bg:#F0F9FF color:#3388FF
- 有勾选时筛选图标保持 #3388FF

### 5.2 表单表格（table-form-spec.json）
- 表格内嵌表单控件
- 详细参数见 `table-form-spec.json`

### 5.3 缺省页（empty-spec.json v1.0.0）
- 图标尺寸：120×120px(@2x)，路径：`数据展示-缺省页/` 系列
- 容器：flex-column 居中, padding:48px 0, gap:12px, border:1px solid #E9ECF2, border-radius:4px
- 标题：14px/400/#223355
- 按钮：32px高, border:1px solid #DDE1EB
  - pill: border-radius:100px, color:#3388FF（用于"+ 新增"）
  - rect: border-radius:4px, color:#223355（用于操作按钮）

**6 种场景**：暂无内容 / 无搜索结果 / 无消息 / 无审批 / 无评论 / 无图片

### 5.4 头像（avatar-spec.json v1.0.0）

**三种类型**：
- 默认人形：bg:#F0F9FF, icon-color:#85C0FF, icon占75%
- 文字：bg:#3388FF, 姓名首字, 白色, font-weight:600
- 图片：object-fit:cover, 圆形裁切

**尺寸**：lg=48px, md=36px, sm=28px; 统一 border-radius:50%

**交互**：
- Tooltip：悬停显示姓名, bg:rgba(34,51,85,0.85), 12px白字, arrow向下
- 上传删除：右上角 16px 圆形(bg:#FFF, border:1px #E9ECF2), ×图标, hover变红

**头像组**：
- 水平排列, 除首个外 margin-left:-16px
- border:1.5px solid #FFF（白色描边隔离）
- 更多气泡：bg:#F0F9FF, color:#3388FF, font-weight:600, z-index:10

### 5.5 徽标（badge-spec.json v1.0.0）
- 定位：absolute; top:0; right:0; z-index:10; border:1.5px solid #FFF

| 类型 | 尺寸 | 说明 |
|---|---|---|
| 红点 | 10×10px | offset translate(0%,-20%), lg头像额外左偏4px |
| 数字 | 18px高/min宽 | border-radius:9px; 超99显示99+ |
| 文字 | 同数字 | HOT/NEW等 |
| 图标 | 18×18px | 圆形, 内嵌10px白色图标 |

### 5.6 折叠面板（collapse-spec.json v1.0.0）
- 容器：`border:1px solid #E9ECF2; border-radius:4px`
- 标题行：`height:48px; padding:0 16px; justify-content:space-between`
- 标题：14px/500/#081126
- 箭头：14px, #C3CAD9, collapsed朝右, expanded rotate(90deg), transition 0.2s
- 内容区：`border-top:1px solid #E9ECF2; padding:12px 16px 16px; font-size:14px/#223355; line-height:1.8`
- 动画：max-height 过渡 0.25s ease
- 禁用态：header bg:#FAFAFA, 标题色:#A8B4C8, cursor:not-allowed
- **无边框变体**：去掉整体外边框，保留项间分隔线，padding归零

### 5.7 步骤条（steps-spec.json v1.0.0）
- 节点圆：24×24px; border-radius:50%; font-size:12px

| 状态 | background | color | 图标 |
|---|---|---|---|
| 未完成(pending) | #F5F7FA | #6B7A99 | 数字 |
| 进行中(active) | #3388FF | #FFF | 数字 |
| 已完成(done) | #F0F9FF | #3388FF | 对勾SVG(stroke 2px round) |

- 连接线：1px thick; pending=#E9ECF2; active/done=#3388FF
- 标签标题：14px; pending/default=#223355, active=#338355→#3388FF
- 标签描述：12px/#6B7A99; margin-top:4px

**三种方向**：
- 横向：圆+横线(flex:1)居中对齐
- 横向(带描述)：align-self:flex-start + margin-top:11px 对齐圆心
- 纵向：竖线 margin-left:11px 对齐圆心, 上下各留4px
- 上下：align-items:flex-start, 线 margin-top:11px

### 5.8 面包屑（breadcrumb-spec.json v1.0.0）
- 容器：inline-flex; font-size:14px
- 上级节点：default=#6B7A99, hover=#3388FF transition 0.15s
- 当前节点：#223355（不可点击, hover无变化）
- 分隔符：`/`, #6B7A99, margin:0 8px
- 省略号：`···`, #6B7A99, 不可点击
- 下拉菜单（同级多页面时）：min-width:140px; border:1px solid #E9ECF2; border-radius:8px; padding:8px; box-shadow:0 8px 24px rgba(18,74,180,0.12)
- 菜单项：height:36px; padding:0 8px; border-radius:4px; hover:bg:#F5F7FA color:#3388FF

---

## 六、反馈提示

### 6.1 警告提示（alert-spec.json v1.1.0）
- 容器宽 780px, border-radius:4px, padding-horizontal:16px

**单行**：`height:52px; flex; align-items:center; gap:8px`
- 结构：面状图标(16px) + 文字(flex:1) + 操作按钮(可选) + 关闭图标

**双行**（标题+内容）：
- padding:14px 16px; flex-direction:column
- 第一行：图标(16px) + 标题(14px/500/#081126, flex:1) + 关闭图标
- 第二行：内容(flex:1) + 操作按钮(右对齐), padding-left:24px

**四种类型**：
| 类型 | background | 图标色 |
|---|---|---|
| info | #D6EDFF | #3388FF |
| success | #B6FAE0 | #11C79B |
| warning | #FFE4C0 | #FFAA33 |
| error | #FFDFD6 | #FF4433 |

- 图标：16×16px 面状, 内部符号白色描边 stroke-width:1.4
- 文字：14px/400/#223355
- 操作按钮：纯文字 14px/#3388FF, underline hover
- 关闭：× path(16px), #223355, opacity 淡出 0.2s

### 6.2 全局消息提示（message-spec.json v1.1.0）
- 容器：`width:240px; height:52px; bg:#FFF; border-radius:8px; box-shadow:0 5px 20px rgba(0,67,202,0.10); flex; gap:8px; padding:0 16px`
- 图标：16×16px 面状（info=#3388FF, warning=#FFAA33, error=#FF4433, success=#11C79B）
- 文字：14px/400/#223355; nowrap
- 位置：fixed 顶部居中 `top:24px; left:50%; transform:translateX(-50%)`
- 堆叠：多条垂直堆叠 gap:8px
- 入场：从上方12px淡入下移, opacity 0→1, translateY(-12px)→0, 0.25s ease
- 退场：淡出上移, 0.25s
- 自动关闭：3000ms

### 6.3 通知提醒（notification-spec.json v1.1.0）
- 容器：`width:369px; height:78px; bg:#FFF; border-radius:4px; box-shadow:0 5px 20px rgba(0,67,202,0.10); padding:14px 36px 14px 16px`
- 图标：16×16px（info=#3388FF, warning=#FFAA33, success=#1DBF8E, error=#FF4433）
- 标题：14px/500/#081126（图标右侧,gap:8px）
- 内容：14px/400/#223355, padding-left:24px
- 关闭：absolute top:12px right:12px, 14×14px ×, default:#A8B4C8, hover:#6B7A99
- 位置：fixed 右上角 `top:24px; right:24px`
- 入场：从右侧24px淡入左移, 0.25s
- 自动关闭：4500ms

### 6.4 气泡卡片（popover-spec.json v1.1.0）
- 容器：`width:242px; bg:#FFF; border-radius:4px; box-shadow:0 2px 50px rgba(0,67,202,0.16); padding:12px 16px; z-index:1000`
- 箭头：三角形 #FFF, 随弹出方向旋转

**内容变体**：仅标题 / 仅内容(多行) / 标题+内容 / 含链接(13px/#3388FF) / 含操作按钮 / 危险提示(红感叹号)

**按钮**（28px高, 12px水平padding, 4px圆角, 13px字）：
- 默认(取消): bg:#FFF, border:1px solid #DDE1EB, color:#223355
- 主要(确定): bg:#3388FF, color:#FFF
- 危险确定: bg:#FF4433, color:#FFF
- ⚠️ 危险提示按钮顺序：确定在左，取消在右（与普通相反！）

**12 个方向**：top/start/end, bottom/start/end, left/start/end, right/start/end
**触发方式**：Hover（移入显/移出关）/ Click（点击开关/外部关）
**与Tooltip区别**：Popover 可承载链接/按钮等可操作元素

### 6.5 文字提示（tooltip-spec.json v1.1.0）
- 容器：`width:80px; bg:rgba(8,17,38,0.8); border-radius:4px; padding:12px`
- 文字：PingFangSC-Regular 14px/#FFF, line-height:22px
- 箭头：CSS border 三角法 6px, 色=背景色
- 间距：6px（tooltip 与触发元素）
- 触发：hover; 动画：opacity 0→1, 0.15s
- **8 方向**：left_top/bottom, right_top/bottom, top, bottom, left_center, right_center
- **超大提示**：width:240px, max-height:180px可滚动, scrollbar 3px, 可选缩略图 100px高

---

## 七、导航布局

### 7.1 页面骨架（page-layout-spec.json v1.0.0）⭐ 重要！

**三层结构**：`body(flex-column, h:100vh, overflow:hidden)` → topnav → main-layout(flex-row)

```
<body>  —— flex-direction:column; height:100vh; overflow:hidden
  <nav.topnav>     —— 60px高, 渐变蓝, flex-shrink:0
  <div.main-layout> —— flex:1; display:flex; overflow:hidden
    <aside.sidenav>   —— 200px宽, 白色导航
    <div.right-panel> —— flex:1; flex-direction:column; overflow:hidden
      <div.tab-bar>   —— 一级页签栏, 40px高
      <main.content>  —— flex:1; overflow-y:auto; padding:20px; bg:#F5F7FA
```

**⚠️ 关键规则**：
- 页签栏必须在 right-panel 内部（sidenav 右侧），不得放在 main-layout 外层
- right-panel 必须设置 `overflow:hidden`，由内部 content 的 `overflow-y:auto` 负责滚动
- body 必须设置 `height:100vh; overflow:hidden`，避免双滚动条

### 7.2 顶部导航（topnav-spec.json v1.1.0）
- 容器：`height:60px; bg:linear-gradient(to right, #2167D9, #3388FF); padding:0 20px; flex; align-items:center`
- Logo：40×40px, border-radius:8px
- 标题：18px/400/#FFF, margin-left:10px
- 一级菜单：紧跟标题右侧, margin-left:80px
  - 菜单项：height:60px; padding:0 20px; font-size:16px; color:#FFF
  - Hover: bg:rgba(0,0,0,0.08); Active: bg:rgba(0,0,0,0.10) + font-weight:400（⚠️ 不替换渐变背景！）
- 右侧工具区：margin-left:auto; gap:4px
  - 图标按钮：28×28px 或 44×44px(hit-area), 面状白色
  - 通知徽标：8×8px #FF4433
  - 分隔线：1px×20px rgba(255,255,255,0.25)
- 用户信息：avatar(32px圆形) + name(14px) + dept(12px半透白) + more-icon(16×16px)
  - hover:bg:rgba(255,255,255,0.12)
- 个人中心下拉菜单：
  - 168px宽, 右对齐, border-radius:8px, padding:8px, box-shadow:0 8px 24px rgba(18,74,180,0.16)
  - 菜单项：height:36px; padding:0 8px; border-radius:4px; **线状图标**(fill:none, stroke)
  - 退出登录：color:#FF4433, separated:true

### 7.3 一级页签栏（tab-bar / tab-spec.json v2.1.0）
- 容器：`height:40px; width:100%; bg:linear-gradient(to bottom, #E9ECF2, #FFF); padding:0 8px; align-items:flex-end; gap:2px; overflow-x:auto`
- 标签：`width:154px; height:32px; padding:0 6px 0 12px; border-radius:8px 8px 0 0; font-size:14px; gap:4px`
- Default: bg:#E9ECF2, color:#6B7A99
- Active: bg:linear-gradient(to bottom, #FFF, #F1F6FA), color:#3388FF
- Icon按钮：24×24px, icon:16×16px, color:#A8B4C8, border-radius:4px
- 规则：默认标签仅关闭图标；选中标签显示全屏图标(左)+关闭图标(右)

### 7.4 侧边导航三级菜单（sidenav-spec.json v1.3.0）
- 容器：`width:200px; bg:#FFF; border-right:1px solid #E9ECF2; flex-direction:column; padding:12px 8px; overflow-y:auto`

**菜单项公共规格**：`height:36px; padding:0 8px; border-radius:4px; font-size:14px; icon-text-gap:8px`
- Default: transparent; Hover: #F5F7FA; Active: #F0F9FF, text/icon:#3388FF

**一级菜单**：线状图标 16×16px (fill:none, stroke:currentColor, stroke-width:1.5) + 文字 + 可选展开箭头
- Padding-left:8px, 文字起始 x=32px
- ⚠️ **有子菜单的一级项永远不加 active 态**，active 只在实际选中的子菜单项上

**二级菜单**：无图标, padding-left:40px; 文字色 default:#6B7A99, hover:#223355, active:#3388FF

**三级菜单**：padding-left:48px; 文字色同二级

**展开箭头**：16×16px, #6B7A99, rotate(180deg)打开, margin-left:auto

**间距控制**（⚠️ 不用 flex gap！）：
- 菜单组间：`.nav-group + .nav-group { margin-top:8px }`
- 子菜单展开时：`.nav-group.is-open > .nav-submenu { margin-top:8px }`（收起时为0）
- 二级项间：`.nav-item-l2 + .nav-item-l2 { margin-top:8px }`
- 子菜单动画：max-height 0→600px, 0.25s ease

### 7.5 主系统侧边导航（main-sidenav-spec.json v1.0.0）
- 容器：`width:60px; h:1080px; bg:linear-gradient(0deg, #223355 0%, rgba(52,68,104,0.95) 100%)`
- Logo：20×20px, 顶部居中, margin-bottom:20px
- 菜单项：60×50px; icon:18×18px 面状白色 fill
- Default: 透明; Hover: rgba(255,255,255,0.08); Active: #3388FF
- 底部分隔线：32×1px, rgba(255,255,255,0.15), margin:8px 0

### 7.6 页头（page-header-spec.json v1.0.0）
- 通用：bg:#FFF; border-bottom:1px solid #E9ECF2; 左侧flex + 右侧margin-left:auto; gap:8px

**页头内按钮规格**：
| 类型 | 高度 | 圆角 | 样式 |
|---|---|---|---|
| pill-primary(新增) | 32px | 16px | 白底, border:#DDE1EB, color:#3388FF |
| pill-secondary(辅助) | 32px | 16px | 白底, border:#DDE1EB, color:#223355 |
| rect-primary(确定) | 32px | 4px | bg:#3388FF, color:#FFF |
| rect-secondary(取消) | 32px | 4px | 白底, border:#DDE1EB, color:#223355 |

**一级页头（5变体）**：
1. 按钮+搜索栏（默认高度）
2. 标题(18px/500/#081126) + 搜索栏（56px高）
3. 标题 + 取消/重置/确定（56px高）
4. 仅标题（56px高）
5. 标题 + 取消/重置/确定 + 二级标签行（96px高）

**二级页头（4变体）**：
1. 返回箭头(16×16px/#6B7A99) + 标题(14px/500/#081126) + 操作按钮
2. 二级标签行（40px高, padding:0） + 说明/关闭图标(32×32px)
3. 标题 + 取消/重置/保存
4. 标题 + 搜索/高级搜索/设置

**搜索框**（页头内）：常规搜索框, 左输入(圆角左) + 右按钮(圆角右)
- 输入框 `border-right:none`, 按钮承担右侧描边

### 7.7 标签页（tab-spec.json v2.1.0）

**横向内容标签**（底部蓝色标记线）：
- 容器：h:40px, border-bottom:1px solid #E9ECF2, flex, align-items:flex-end
- 标签：h:40px, padding:0 16px, font-size:14px
- States: default(#6B7A99), hover(#223355), active(#3388FF + 底部2px #3388FF标记线), disabled(#C3CAD9)
- ⚠️ 标记线用文字 span::after 实现(width:100%), 不可加在 button 上

**纵向内容标签**（右侧蓝色标记线）：
- 容器：w:120px, border-right:1px solid #E9ECF2, flex-direction:column
- 标签：h:40px, padding:0 16px
- States: 同横向, active 时右侧 2px #3388FF 标记线(height:100%)
- ⚠️ 分隔线用容器::before 伪元素绘制贯通竖线, 不在 tab_item 上用 border-right

**胶囊组标签页（capsule_tabs）**：
- 容器：inline-flex, bg:#F5F7FA, border-radius:4px, padding:2px, gap:2px
- 标签：h:32px, padding:0 20px, border-radius:4px, border:1px solid transparent
- States: default(bg:#F5F7FA/#223355), hover(bg:#E9ECF2), active(bg:#F0F9FF/#3388FF, border:#3388FF), disabled(#C3CAD9)
- ⚠️ 选中项 z-index:1 使 1px 描边浮于相邻之上

### 7.8 抽屉（drawer-spec.json v1.0.0）
- 推荐宽度：400 / 520 / 720 / 800px
- `height:100vh; position:fixed; top:0; right:0; bg:#FFF`
- `box-shadow:-10px 2px 20px rgba(0,67,202,0.10)`
- 动画：`transform:translateX(100%)→0; transition:0.25s ease`
- 遮罩：`bg:rgba(0,0,0,0.3); position:fixed; inset:0; z-index:1000`

**头部**：h:56px; padding:0 20px; border-bottom:1px solid #F5F7FA
- 标题：14px/500/#081126
- 关闭：16×16px, default:#A8B4C8, hover:#6B7A99, hit-area:28×28px

**内容区**：flex:1; overflow-y:auto; padding:20px

**底部操作栏**：h:64px; padding:0 20px; border-top:1px solid #F5F7FA; flex-end; gap:8px
- 取消：outline 按钮 32px高; 确定：solid 按钮 32px高 bg:#3388FF

### 7.9 字段设置抽屉（field-setting-spec.json v1.0.0）
- 从右侧滑入 400px 抽屉, z-index:1001
- 字段列表项：h:40px; padding:0 8px; border-radius:4px
- Default:#FFF, Hover:#F5F7FA, Dragging:#F0F9FF + shadow:0 4px 16px rgba(0,67,202,0.12)
- Cursor: grab(dragging:grabbing)
- 布局：drag-icon(16px) + field-name(flex:1,14px/#223355) + switch(20px plain)

---

## 八、其他组件

### 8.1 回到顶部（back-to-top-spec.json）
- 详细参数见 `back-to-top-spec.json`

### 8.2 下拉菜单（dropdown-spec.json）
- 详细参数见 `dropdown-spec.json`

### 8.3 工具栏搜索（toolbar-search-spec.json）
- 详细参数见 `toolbar-search-spec.json`

### 8.4 滚动条（scrollbar-spec.json）
- 宽度 4px, thumb:#DDE1EB

### 8.5 视频预览（video-viewer-spec.json v1.0.0）
- 蒙层：bg:rgba(0,0,0,0.6), fixed inset:0, z-index:2000
- 播放器：1072×724px, border-radius:16px, bg:#0a0a0a, 居中
- 播放按钮：96×96px圆形, bg:rgba(255,255,255,0.8), 内嵌三角箭头
- 底部渐变：h:120px, linear-gradient(to top, rgba(0,0,0,0.65), transparent)
- 进度条：h:4px, padding:8px 0(扩大点击), track:rgba(255,255,255,0.6), bar:#3388FF, thumb:12×12px
- 工具栏：h:48px, btn:32×32px透明, hover:rgba(255,255,255,0.15)

### 8.6 图片查看器（image-viewer-spec.json）
- 详细参数见 `image-viewer-spec.json`

### 8.7 音频播放器（audio-viewer-spec.json）
- 详细参数见 `audio-viewer-spec.json`

---

## 九、页面骨架

构建业务页面时的标准 HTML 骨架（参考 page-layout-spec.json）：

```html
<body style="display:flex; flex-direction:column; height:100vh; overflow:hidden; margin:0; font-family:PingFangSC-Regular;">
  <!-- 1. 顶部导航 -->
  <nav class="topnav" style="height:60px; background:linear-gradient(to right,#2167D9,#3388FF); ...">
    ...
  </nav>

  <!-- 2. 主布局区 -->
  <div class="main-layout" style="flex:1; display:flex; overflow:hidden;">
    <!-- 2a. 侧边导航 -->
    <aside class="sidenav" style="width:200px; background:#FFF; border-right:1px solid #E9ECF2; ...">
      ...
    </aside>

    <!-- 2b. 右侧面板 = 页签栏 + 内容区 -->
    <div class="right-panel" style="flex:1; display:flex; flex-direction:column; overflow:hidden;">
      <!-- 2b-i. 一级页签栏 -->
      <div class="tab-bar" style="height:40px; background:linear-gradient(to bottom,#E9ECF2,#FFF); ...">
        ...
      </div>

      <!-- 2b-ii. 内容滚动区 -->
      <main class="content" style="flex:1; overflow-y:auto; padding:20px; background:#F5F7FA;">
        <!-- 页头 + 业务内容 -->
        <header class="page-header" style="background:#FFF; border-bottom:1px solid #E9ECF2; ...">...</header>
        ...
      </main>
    </div>
  </div>
</body>
```

---

## 十、工作流程

当用户要求「按 ZartUI 规范生成 XX」时：

1. **识别组件类型** → 对应上方章节查找规范
2. **读取精确参数**：复杂组件用 Read 工具读取对应 `*-spec.json` 获取完整细节
3. **生成 HTML/CSS**：
   - 直接使用 token 值（#3388FF, #223355 等），无需 CSS 变量
   - 下拉/弹窗面板统一 `position:fixed + getBoundingClientRect` 定位
   - 表格锁定必须 `border-collapse:separate; border-spacing:0`
   - 错误提示包裹在同一 wrapper 内（不被外部 gap 影响）
4. **参考预览**：`*-preview.html` 作为视觉参考
5. **自查 known_pitfalls**：每个 spec 末尾记录了常见错误，生成后逐一核对

---

## 十一、常见陷阱速查（更新版）

| # | 问题 | 解决方案 |
|---|---|---|
| 1 | 下拉被父级 overflow 裁剪 | `position:fixed + getBoundingClientRect` |
| 2 | 表格 sticky 阴影消失 | `border-collapse:separate; border-spacing:0` |
| 3 | 错误提示间距被 gap 影响 | 控件+错误包在同一独立 wrapper 内 |
| 4 | 全圆角新增按钮用了蓝底白字 | 应为白底蓝字蓝边 pill 按钮 (primary) |
| 5 | 面状按钮用于导出等辅助操作 | 面状(solid)仅用于提交/保存/确定；辅助操作用线(outline)或pill |
| 6 | 后置选择激活时背景变白 | **后置背景始终 #F5F7FA**，只有前置激活时变 #FFFFFF |
| 7 | 清除图标与后缀重叠 | 清除图标放入 suffix flex 容器作为第一子元素 |
| 8 | 字数统计与 resize 手柄重叠 | padding-bottom ≥ 24px |
| 9 | 原生 select 箭头无法自定义 | `appearance:none` + `::after` 伪元素绘制箭头 |
| 10 | 迷你分页当前页输入框非正方形 | 固定 28×28px 正方形 |
| 11 | 页签栏放在 topnav 下方全宽 | **必须在 right-panel 内部**（sidenav 右侧） |
| 12 | 页面出现双滚动条 | body 设 `height:100vh; overflow:hidden`，各区域自行处理滚动 |
| 13 | topnav 菜单选中渐变消失 | 用 `rgba(0,0,0,0.10)` 叠加而非替换背景色 |
| 14 | 侧导航用 flex gap 导致折叠空白 | 改用相邻兄弟选择器 `+ {margin-top:8px}`，is-open 时才加 |
| 15 | 二三级菜单缩进用 margin-left 导致 hover 背景不延伸 | **用 padding-left** 实现缩进，让背景色覆盖整行 |
| 16 | 一级菜单有子菜单却被加了 active 态 | **有子菜单的一级项永不加 active**，只加在实际选中的子菜单上 |
| 17 | 纵向标签分隔线被 gap 截断 | 用容器 `::before` 伪元素绘制**贯通竖线** |
| 18 | 横向标签标记线宽度与文字不等宽 | 标记线用**文字 span::after** (width:100%)，不可加在 button 上 |
| 19 | 胶囊组选中描边被相邻遮挡 | 选中项设 `z-index:1` |
| 20 | 复选框对勾末端锐角 | 用 inline SVG + `stroke-linecap:round; stroke-linejoin:round` |
| 21 | 单选框选中态区分不明显 | 用 `border:5px solid #3388FF` **加粗描边**表达选中，不用内圆点 |
| 22 | 禁用选中态与正常选中同色 | 禁用选中改用 **#ADD8FF** |
| 23 | 拖拽上传 dragover 边框非虚线 | is-dragover 同时设置 `border-style:dashed` 和 `border-color:#3388FF` |
| 24 | 面包屑/顶部下拉外部点击不关闭 | 挂载一次性 document click 监听 + setTimeout 延迟注册 |
| 25 | 用户更多图标被加了旋转动画 | 更多图标是**静态图标**（三竖点+三横线），不需要 rotate |
| 26 | 评分表情样式悬停未同步 | 需根据 hover 分值重新渲染**全部 5 个表情 SVG** |
| 27 | 上传 done 态仍显示 100% | done 状态**隐藏进度文字**，仅显示操作图标 |
| 28 | 重要提示标签 hover 改文字色 | **实色背景文字固定 #FFF**，只切换背景色 |
| 29 | 一般提示标签 hover 改背景色 | **背景固定不变**，只切换文字色 |
| 30 | 头像组更多气泡被遮挡 | 更多气泡设 `z-index:10`，头像设 `position:relative` |
| 31 | tag-icon svg 被 text-baseline 撑开 | tag-icon 显式设置 `width:12px; height:12px` |

---

## 附录：组件速查索引

| 分类 | 组件名 | Spec 文件 | 版本 |
|---|---|---|---|
| 全局 | 全局规范 | global-spec.json | v1.1.0 |
| 基础控件 | 矩形按钮 | button-spec.json | v2.0.0 |
| 基础控件 | 全圆角按钮 | button-pill-spec.json | v3.0.0 |
| 基础控件 | 复选框 | checkbox-spec.json | v1.0.0 |
| 基础控件 | 单选框 | radio-spec.json | v1.1.0 |
| 基础控件 | 开关 | switch-spec.json | v1.0.0 |
| 基础控件 | 标签 | tag-spec.json | v1.0.0 |
| 基础控件 | 分页 | pagination-spec.json | v1.0.0 |
| 基础控件 | 进度条 | progress-spec.json | v1.1.0 |
| 数据录入 | 输入框 | input-spec.json | v2.0.0 |
| 数据录入 | 数字输入框 | number-input-spec.json | v1.0.0 |
| 数据录入 | 验证码 | captcha-spec.json | v1.0.0 |
| 数据录入 | 上传 | upload-spec.json | v1.0.0 |
| 数据录入 | 评分 | rating-spec.json | v1.0.0 |
| 数据录入 | 富文本 | rich-text-spec.json | — |
| 数据录入 | 表单容器 | formitem-spec.json | v1.0.0 |
| 数据选择 | 下拉选择 | select-spec.json | v2.0.0 |
| 数据选择 | 多选下拉 | multiselect-spec.json | v1.0.0 |
| 数据选择 | 日期选择 | datepicker-spec.json | — |
| 数据选择 | 时间选择 | timepicker-spec.json | — |
| 数据选择 | 穿梭框 | transfer-spec.json | v1.1.0 |
| 数据选择 | 级联选择 | cascader-spec.json | — |
| 数据展示 | 表格 | table-spec.json | v1.1.0 |
| 数据展示 | 表单表格 | table-form-spec.json | — |
| 数据展示 | 缺省页 | empty-spec.json | v1.0.0 |
| 数据展示 | 头像 | avatar-spec.json | v1.0.0 |
| 数据展示 | 徽标 | badge-spec.json | v1.0.0 |
| 数据展示 | 折叠面板 | collapse-spec.json | v1.0.0 |
| 数据展示 | 步骤条 | steps-spec.json | v1.0.0 |
| 数据展示 | 面包屑 | breadcrumb-spec.json | v1.0.0 |
| 反馈提示 | 警告提示 | alert-spec.json | v1.1.0 |
| 反馈提示 | 全局消息 | message-spec.json | v1.1.0 |
| 反馈提示 | 通知提醒 | notification-spec.json | v1.1.0 |
| 反馈提示 | 气泡卡片 | popover-spec.json | v1.1.0 |
| 反馈提示 | 文字提示 | tooltip-spec.json | v1.1.0 |
| 导航布局 | 页面骨架 | page-layout-spec.json | v1.0.0 |
| 导航布局 | 顶部导航 | topnav-spec.json | v1.1.0 |
| 导航布局 | 一级页签栏 | tab-bar-spec.json → tab-spec.json | v2.1.0 |
| 导航布局 | 侧边导航 | sidenav-spec.json | v1.3.0 |
| 导航布局 | 主系统侧导航 | main-sidenav-spec.json | v1.0.0 |
| 导航布局 | 页头 | page-header-spec.json | v1.0.0 |
| 导航布局 | 标签页 | tab-spec.json | v2.1.0 |
| 导航布局 | 抽屉 | drawer-spec.json | v1.0.0 |
| 导航布局 | 字段设置抽屉 | field-setting-spec.json | v1.0.0 |
| 其他 | 视频预览 | video-viewer-spec.json | v1.0.0 |
| 其他 | 图片查看器 | image-viewer-spec.json | — |
| 其他 | 音频播放器 | audio-viewer-spec.json | — |
| 其他 | 回到顶部 | back-to-top-spec.json | — |
| 其他 | 下拉菜单 | dropdown-spec.json | — |
| 其他 | 工具栏搜索 | toolbar-search-spec.json | — |
| 其他 | 滚动条 | scrollbar-spec.json | — |
