---
name: zartui-spec
description: 调用 ZartUI 组件规范。当用户需要生成页面、组件、或询问 ZartUI 样式规范时使用此 skill。触发词包括："根据规范生成"、"ZartUI"、"按规范"、"生成页面"、"生成组件"、"design-to-code"、"Vue3 zartd"。
version: 1.0.2
author: majianquan
category: global
visibility: global
---

# ZartUI 规范 Skill

> **设计体系总纲**：本目录的 `Comprehensive_Design_System.md` 是整体设计哲学、Material Design 3 原则、多主题架构、SCSS Mixin 工具链、代码规范集成的"为什么"层概述。需要理解设计理念、跨组件的全局约束、或生成完整 Vue3 + zartd 页面工程时先通读它；本文件下方的组件 `spec.json` 索引则是精确到尺寸/颜色/状态的"是什么"层权威数据。两者配合使用。

## 规范文件根目录

所有规范文件位于本 skill 目录下的 `ZartUI-Spec/` 子目录（与本 SKILL.md 同级）。

读取时使用本 skill 目录的相对路径，例如 `ZartUI-Spec/input-spec.json`、`ZartUI-Spec/button-spec.json`。每个组件还配有同名 `*-preview.html` 可参考实际渲染效果。

## 使用规则

**生成任何页面或组件前，必须先读取对应的 spec.json 文件，不得凭记忆或自定义样式。**

### 缺失 spec 的降级规则

以下组件当前**没有 spec.json**（源规范包未提供），用到时按此顺序回退，不得凭空编造数值：

1. 若存在同名 `*-preview.html`（multiselect / switch / tab / field-setting / video-viewer），直接读取该 HTML，从其内联样式提取尺寸、颜色、状态后再实现。
2. 若两者都没有（progress / alert / message / notification / tooltip / drawer），改用本文档「Design Token」表的全局令牌 + 通用组件约束实现，并在交付时明确标注"该组件无官方 spec，按设计令牌近似实现"。
3. `page-layout-spec.json` 不存在，但页面骨架已完整内联在下方「页面布局规范」一节，直接按该节执行即可。

---

## Design Token（全局设计令牌）

来源：`global-spec.json`

| Token | 值 | 用途 |
|---|---|---|
| Primary | #3388FF | 主色、链接、激活态 |
| Body Text | #223355 | 正文文字 |
| Secondary Text | #6B7A99 | 次要文字、说明 |
| Disabled Text | #A8B4C8 | 禁用文字、占位符 |
| Border | #DDE1EB | 默认边框（G8） |
| Border Light | #E9ECF2 | 浅色边框（G10） |
| Hover BG | #F5F7FA | 悬停背景（G20） |
| Active BG | #F0F9FF | 选中背景 |
| Focus BG | #D6EDFF | 聚焦背景 |
| Error | #FF4433 | 错误色 |
| Success | #06A17F | 成功色 |
| Warning | #FF6600 | 警告色 |
| Page BG | #F5F7FA | 页面背景 |
| White | #FFFFFF | 面板、卡片背景 |
| Heading | #081126 | 页面标题 |

---

## 页面布局规范

来源：`page-layout-spec.json`

所有业务页面必须遵循以下四层结构：

```
body（flex-direction: column; height: 100vh; overflow: hidden）
├── topnav（顶部蓝色渐变导航，60px）
└── main-layout（flex: 1; display: flex; overflow: hidden）
    ├── sidenav（左侧白色导航，200px）
    └── right-panel（flex: 1; flex-direction: column; overflow: hidden）
        ├── tab-bar（一级页签栏，40px）
        └── content（flex: 1; overflow-y: auto; padding: 20px）
            └── page-panel（白色面板，border-radius: 8px）
                ├── page-panel-header（标题栏 56px，左标题右按钮，border-bottom: 1px solid #E9ECF2）
                └── page-panel-body（padding: 20px，内容区）
```

**关键约束：**
- tab-bar 必须在 sidenav 右侧的 right-panel 内，不能全宽放在 topnav 下方
- 内容块之间用 `border: 1px solid #E9ECF2` 描边区分，不用阴影

---

## 导航规范

### 顶部导航 `topnav-spec.json`
- 容器：60px 高，`linear-gradient(to right, #2167D9, #3388FF)`
- 菜单项：60px 高，padding 0 20px，激活态 `rgba(0,0,0,0.10)` 叠加
- 工具图标按钮：44×44px 容器，SVG 24×24px，hover `rgba(255,255,255,0.15)`
- 用户区：头像 32×32px 圆形，下拉箭头 chevron-down 16×16px

### 左侧导航 `sidenav-spec.json`
- 容器：200px 宽，白色背景，右边框 `1px solid #E9ECF2`
- 菜单项：36px 高，border-radius 4px
- 激活态：background #F0F9FF，color #3388FF，icon stroke #3388FF
- 子菜单动画：max-height 0→600px，transition 0.25s ease
- 缩进用 padding-left（不用 margin-left），间距用相邻兄弟选择器

### 一级页签栏 `tab-bar-spec.json > tab_bar`
- 容器：40px 高，`linear-gradient(to bottom, #E9ECF2, #FFFFFF)`
- 标签：154×32px，border-radius 8px 8px 0 0，gap 2px
- 默认态：background #E9ECF2，color #6B7A99
- 激活态：`linear-gradient(to bottom, #FFFFFF, #F1F6FA)`，color #3388FF
- 激活标签：全屏图标 + 关闭图标；默认标签：仅关闭图标
- 图标按钮：24×24px，hover `rgba(168,180,200,0.2)`

---

## 组件规范索引

### 表单组件
| 组件 | 规范文件 |
|---|---|
| 输入框 Input | `input-spec.json` |
| 数字输入 NumberInput | `number-input-spec.json` |
| 下拉选择 Select | `select-spec.json` |
| 多选下拉 MultiSelect | `multiselect-spec.json` |
| 级联选择 Cascader | `cascader-spec.json` |
| 复选框 Checkbox | `checkbox-spec.json` |
| 单选框 Radio | `radio-spec.json` |
| 开关 Switch | `switch-spec.json` |
| 日期选择 DatePicker | `datepicker-spec.json` |
| 时间选择 TimePicker | `timepicker-spec.json` |
| 文件上传 Upload | `upload-spec.json` |
| 富文本 RichText | `rich-text-spec.json` |
| 验证码 Captcha | `captcha-spec.json` |
| 表单项 FormItem | `formitem-spec.json` |

**注意：所有含输入框的组件必须读取 `input-spec.json`，不得自定义输入框样式。**
**注意：表单错误提示文字 margin-top 统一为 4px（来源：`global-spec.json`）。**

### 按钮
| 组件 | 规范文件 |
|---|---|
| 矩形按钮 Button | `button-spec.json` |
| 全圆角按钮 ButtonPill | `button-pill-spec.json` |

### 数据展示
| 组件 | 规范文件 |
|---|---|
| 表格 Table | `table-spec.json` |
| 表格表单 TableForm | `table-form-spec.json` |
| 标签 Tag | `tag-spec.json` |
| 徽标 Badge | `badge-spec.json` |
| 头像 Avatar | `avatar-spec.json` |
| 进度条 Progress | `progress-spec.json` |
| 评分 Rating | `rating-spec.json` |
| 步骤条 Steps | `steps-spec.json` |
| 折叠面板 Collapse | `collapse-spec.json` |
| 穿梭框 Transfer | `transfer-spec.json` |

### 反馈组件
| 组件 | 规范文件 |
|---|---|
| 警告提示 Alert | `alert-spec.json` |
| 消息 Message | `message-spec.json` |
| 通知 Notification | `notification-spec.json` |
| 文字提示 Tooltip | `tooltip-spec.json` |
| 气泡卡片 Popover | `popover-spec.json` |
| 下拉菜单 Dropdown | `dropdown-spec.json` |
| 抽屉 Drawer | `drawer-spec.json` |

### 导航组件
| 组件 | 规范文件 |
|---|---|
| 标签页 Tab | `tab-spec.json` |
| 标签栏 TabBar + 胶囊标签 | `tab-bar-spec.json` |
| 面包屑 Breadcrumb | `breadcrumb-spec.json` |
| 分页 Pagination | `pagination-spec.json` |
| 页头 PageHeader | `page-header-spec.json` |
| 工具栏搜索 ToolbarSearch | `toolbar-search-spec.json` |
| 字段设置 FieldSetting | `field-setting-spec.json` |

### 媒体组件
| 组件 | 规范文件 |
|---|---|
| 图片查看器 ImageViewer | `image-viewer-spec.json` |
| 视频查看器 VideoViewer | `video-viewer-spec.json` |
| 音频查看器 AudioViewer | `audio-viewer-spec.json` |

### 其他
| 组件 | 规范文件 |
|---|---|
| 滚动条 Scrollbar | `scrollbar-spec.json` |
| 空状态 Empty | `empty-spec.json` |
| 回到顶部 BackToTop | `back-to-top-spec.json` |
| 主系统顶部导航 | `main-topnav-spec.json` |
| 主系统侧边导航 | `main-sidenav-spec.json` |

---

## 生成页面的标准流程

1. **读取 `page-layout-spec.json`** — 确定页面骨架结构
2. **读取 `topnav-spec.json`** — 生成顶部蓝色渐变导航
3. **读取 `sidenav-spec.json`** — 生成左侧白色导航
4. **读取 `tab-bar-spec.json > tab_bar`** — 生成一级页签栏（位于 sidenav 右侧）
5. **生成白色 page-panel**，顶部标题栏（左标题右按钮），内容区用 `border: 1px solid #E9ECF2` 描边区分
6. **按需读取其他组件规范** — 用到哪个组件读取对应 spec.json

## 生成组件的标准流程

1. 读取对应 **spec.json** 文件
2. 严格按照 spec 中的尺寸、颜色、间距、状态实现
3. 如果涉及输入框，额外读取 `input-spec.json`
4. 检查 `known_pitfalls` 节点，避免常见错误

---

## 常见错误速查

| 错误 | 正确做法 |
|---|---|
| tab-bar 放在全宽 topnav 下方 | tab-bar 放在 right-panel 内（sidenav 右侧） |
| 自定义输入框样式 | 读取 input-spec.json |
| 表单错误提示间距随意 | margin-top 统一 4px |
| 菜单缩进用 margin-left | 用 padding-left，保证 hover 背景全行覆盖 |
| 有子菜单的一级项加 active 态 | active 只加在实际选中的叶子节点上 |
| 子菜单间距用 flex gap | 用相邻兄弟选择器 + margin-top |
| tooltip 箭头与框体有间隙 | 每条 ::after 规则单独写完整 border: 6px solid transparent |
| multiselect tag 用蓝色 | tag bg #F5F7FA，color #223355（非 #F0F9FF / #3388FF） |
