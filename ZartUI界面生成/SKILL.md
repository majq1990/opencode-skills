---
name: zart-ui
description: Generate UI components and layouts following the ZartUI design system. Use when creating web interfaces, frontend components, or any HTML/CSS/JS UI that must adhere to ZartUI visual standards. Covers design tokens, component specifications, layout patterns, and interaction states.
---

# ZartUI

ZartUI 是一套企业级 Web UI 设计规范，涵盖 50+ 组件、标准页面布局、设计 Token 与交互细节。本 Skill 提供生成符合 ZartUI 规范的 UI 代码时所需的全部设计约束与组件行为定义。

## Design Tokens

### Color Palette

| Token | Value | Usage |
|-------|-------|-------|
| Primary | `#3388FF` | 主按钮、激活态、链接、选中态 |
| Primary Hover | `#5CA5FF` | 主色 Hover |
| Primary Click | `#2167D9` | 主色 Click / 按下态 |
| Primary Light | `#D6EDFF` | 外发光、Alert info 背景 |
| Primary Lighter | `#F0F9FF` | 选中项背景、Alert info 浅色背景 |
| Success | `#11C79B` | 成功状态、Message success |
| Success Dark | `#06A17F` | 表格状态点 |
| Warning | `#FFAA33` | 警告状态、Message warning |
| Danger | `#FF4433` | 错误、危险操作、删除按钮 |
| Danger Hover | `#D93020` | 危险操作 Hover |
| Danger Light | `#FFDFD6` | Alert error 背景 |
| Text Primary | `#223355` | 主要文字 |
| Text Title | `#081126` | 标题文字 |
| Text Secondary | `#6B7A99` | 次要文字、占位 |
| Text Placeholder | `#A8B4C8` | Placeholder、禁用态文字 |
| Border | `#DDE1EB` | 默认边框 |
| Border Light | `#E9ECF2` | 浅边框、分隔线 |
| BG | `#F5F7FA` | 浅灰背景、Hover 背景 |
| White | `#FFFFFF` | 组件背景、面板背景 |

### Typography

| Token | Value |
|-------|-------|
| Font Family | PingFangSC-Regular, sans-serif |
| Font Size XS | 12px (标签、辅助文字) |
| Font Size SM | 13px (表格操作、次要信息) |
| Font Size Base | 14px (正文、按钮、表单文字) |
| Font Weight Normal | 400 |
| Font Weight Medium | 500 (标题、选中标签) |
| Line Height Base | 1.5 |

### Spacing

| Token | Value |
|-------|-------|
| Space XS | 4px (紧凑间距) |
| Space SM | 8px (组件内间距) |
| Space MD | 12px (面板内边距) |
| Space LG | 16px (容器内边距) |
| Space XL | 20px (页面内容区 padding) |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| Radius SM | 3px | 复选框圆角 |
| Radius Base | 4px | 默认圆角 (输入框、按钮、表格、标签) |
| Radius LG | 8px | 面板圆角、Alert、Message、下拉框 |
| Radius XL | 16px | 搜索框、胶囊搜索 |
| Radius Full | 100px | 胶囊标签、头像姓名标签 |

### Shadows

| Token | Value | Usage |
|-------|-------|-------|
| Shadow Panel | `0 2px 20px rgba(34,51,85,0.16)` | 下拉面板、树选择面板 |
| Shadow Dropdown | `0 4px 12px rgba(34,51,85,0.1)` | 前置选择下拉 |
| Shadow Toast | `0 5px 20px rgba(0,67,202,0.10)` | Message、Notification |
| Shadow Drawer | `-10px 2px 20px rgba(0,67,202,0.10)` | 抽屉右侧阴影 |
| Shadow Table | `0 2px 50px rgba(0,67,202,0.16)` | 表格图片下拉、删除确认 |

## Common Interaction States

### Component State Definitions

| State | Visual Rule |
|-------|-------------|
| Default | 默认状态，使用 Border `#DDE1EB`，Background `#FFFFFF` |
| Hover | 边框变 `#3388FF`；无额外背景变化 |
| Active / Focus | 边框 `#3388FF` + `box-shadow: 0 0 0 2px #D6EDFF` (外发光) |
| Error | 边框 `#FF4433`；下方显示 12px/400/#FF4433 错误提示，margin-top 4px |
| Disabled | 边框 `#E9ECF2`，背景 `#F5F7FA`，文字 `#A8B4C8`；cursor not-allowed，pointer-events none |
| Checked / Selected | 背景 `#F0F9FF`，文字 `#223355` 或 `#3388FF` |

### Form Error Message (Global)

- 位置：组件下方
- 样式：`margin-top: 4px`，`font-size: 12px`，`font-weight: 400`，`color: #FF4433`
- **必须包裹在同一独立 wrapper 内，不可暴露于外部 flex/grid gap 环境中**

## Component Catalog

### Foundation (基础)

| Component | Spec File | Key Points |
|-----------|-----------|------------|
| Button (Rect) | `button-spec.json` | Solid/Outline × md(32px)/sm(24px)，4px 圆角 |
| Button (Pill) | `button-pill-spec.json` | 全圆角，主/次/危险 × 所有交互态 |
| Icon | N/A | 线状为主，默认 16×16px，stroke-width 1.5，stroke-linecap round |

### Navigation (导航)

| Component | Spec File | Key Points |
|-----------|-----------|------------|
| TopNav | `topnav-spec.json` | 60px 高，渐变背景 `#2167D9` → `#3388FF` |
| SideNav | `sidenav-spec.json` | 200px 宽，白色背景，右侧 1px `#E9ECF2` 边框 |
| Main-SideNav | `main-sidenav-spec.json` | 系统级侧边导航，含 Logo、主菜单图标 |
| Tab Bar | `tab-bar-spec.json` | 一级页签栏，40px 高，渐变背景 `#E9ECF2` → `#FFFFFF` |
| Tab (Horizontal) | `tab-spec.json` | 横向内容标签，56px 高，底部 2px 标记线 |
| Tab (Vertical) | `tab-spec.json` | 纵向标签，154px 宽，右侧贯通竖线 |
| Tab (Capsule) | `tab-bar-spec.json` | 胶囊组，inline-flex，gap 2px，背景 `#F5F7FA` |
| Pagination | `pagination-spec.json` | 基础/高级/迷你三种形态 |
| Breadcrumb | `breadcrumb-spec.json` | 面包屑，支持下拉切换 |

### Data Entry (数据录入)

| Component | Spec File | Key Points |
|-----------|-----------|------------|
| Input | `input-spec.json` | 32px 高，4px 圆角，五态 (default/hover/active/disabled/error) |
| Input (Multi-line) | `input-spec.json` | min-height 84px，右下角字数统计 |
| Input (Prepend) | `input-spec.json` | 前置选择，激活时背景变 `#FFFFFF` |
| Input (Append) | `input-spec.json` | 后置选择，背景始终 `#F5F7FA` |
| Select (Single) | `select-spec.json` | 触发框 32px，面板 8px 圆角，选项 40px 高 |
| Select (Multi) | `select-spec.json` | 触发框显示已选标签，标签 22px 高 |
| Select (Tree) | `select-spec.json` | 树形选择，子节点缩进 20px |
| Select (Modal) | `select-spec.json` | 弹窗选择，触发框右侧操作区 |
| Checkbox | `checkbox-spec.json` | 16×16px，4px 圆角，选中态背景 `#3388FF` |
| Radio | `radio-spec.json` | 16×16px，选中态 5px 加粗描边 `#3388FF` |
| Switch | `switch-spec.json` | 36×20px，10px 圆角，on=`#3388FF` off=`#A8B4C8` |
| DatePicker | `datepicker-spec.json` | 复杂日期选择面板 |
| TimePicker | `timepicker-spec.json` | 时间选择器 |
| Cascader | `cascader-spec.json` | 级联选择 |
| Number Input | `number-input-spec.json` | 加减按钮型 |
| Upload | `upload-spec.json` | 线状按钮 + 文件列表 |
| Rate | `rate-spec.json` | 五星评分，选中 `#FFAA00` |
| Rich Text | `rich-text-spec.json` | 富文本编辑器 |

### Data Display (数据展示)

| Component | Spec File | Key Points |
|-----------|-----------|------------|
| Table | `table-spec.json` | Header 40px/背景 `#F5F7FA`，Row 48px/70px，支持锁定列 |
| Table (Filter) | `table-spec.json` | 字段筛选，漏斗图标，下拉面板 |
| Tag | `tag-spec.json` | 基础/重要/一般/弱提示/图标类 |
| Badge | `badge-spec.json` | 徽标 |
| Avatar | `avatar-spec.json` | 24px 圆形，背景 `#3388FF` |
| Progress | `progress-spec.json` | 进度条 |
| Steps | `steps-spec.json` | 横向/纵向/上下结构 × 三态 |
| Transfer | `transfer-spec.json` | 穿梭框 |

### Feedback (反馈)

| Component | Spec File | Key Points |
|-----------|-----------|------------|
| Alert | `alert-spec.json` | 页面内嵌横幅，780px 宽，4 种类型 |
| Message | `message-spec.json` | 顶部居中弹出，240×52px，3s 自动关闭 |
| Notification | `notification-spec.json` | 右上角弹出，369×78px，4.5s 自动关闭 |
| Tooltip | `tooltip-spec.json` | 8 个方向，背景 `rgba(8,17,38,0.8)` |
| Popover | `popover-spec.json` | 气泡卡片 |
| Drawer | `drawer-spec.json` | 右侧滑入，推荐宽度 400/520/720/800px |
| Modal | N/A | 标准弹窗，遮罩 `rgba(0,0,0,0.3)` |

### Layout (布局)

| Component | Spec File | Key Points |
|-----------|-----------|------------|
| Page Layout | `page-layout-spec.json` | TopNav → MainLayout(SideNav + RightPanel(TabBar + Content)) |
| Page Header | `page-header-spec.json` | 一级/二级页头 |
| Empty | `empty-spec.json` | 缺省页 |
| Back to Top | `back-to-top-spec.json` | 回到顶部 |

## Layout Patterns

### Standard Page Structure

```
<body>  — flex-direction: column; height: 100vh; overflow: hidden
  <nav class="topnav">     — 60px，渐变蓝
  <div class="main-layout"> — flex: 1; display: flex; overflow: hidden
    <aside class="sidenav"> — 200px，白色，右侧边框
    <div class="right-panel"> — flex: 1; flex-direction: column
      <div class="tab-bar">  — 40px，渐变灰白背景
      <main class="content"> — flex: 1; overflow-y: auto; padding: 20px; bg: #F5F7FA
```

**Critical Rules:**
- `body` 必须 `height: 100vh; overflow: hidden`
- TabBar 必须放在 `right-panel` 内，不得放在 `main-layout` 外层
- `right-panel` 必须 `overflow: hidden`，由内部 `content` 的 `overflow-y: auto` 负责滚动

### Form Layout

支持两种布局模式：

| Layout | Label Position | Rule |
|--------|---------------|------|
| Horizontal | 左侧 | Label 固定 32px 高内部居中，与控件顶部对齐 |
| Vertical | 上方 | Grid 三列：`14px(max-content) 1fr`，控件从第二列起始 |

Label 结构：`* 号列(14px) + 标题文字 + ::after 冒号`。非必填项用占位符保持对齐。

## Component Selection Guide

### When to use which button?

- **Solid (面状按钮)**: 提交、保存、确定等主要操作。视觉权重最高，不可滥用。
- **Outline (线状按钮)**: 取消、重置、导出、编辑等次要操作。
- **Pill (全圆角按钮)**: 特殊场景，如搜索框旁的搜索按钮。

### When to use which feedback component?

- **Alert**: 页面内常驻提示，需要用户关注但不需要立即处理。
- **Message**: 操作成功/失败的轻量反馈，自动消失。
- **Notification**: 需要标题和内容的复杂反馈，带关闭按钮。
- **Drawer**: 复杂表单的侧边编辑，需要保存/取消操作。
- **Modal**: 需要阻断用户操作的确认/表单。

### When to use which input variant?

- **单行输入框**: 短文本，单行输入。
- **多行输入框**: 长文本，含字数统计。
- **前置选择**: 需要前缀筛选的场景（如区号选择）。
- **后置选择**: 需要后缀单位的场景（如货币单位）。
- **搜索框**: 即时搜索（全圆角，输入即触发）或常规搜索（需点击图标）。

## Common Pitfalls

### Button
- 面状按钮仅用于提交/保存/确定，不用于导出、编辑等辅助操作。
- Disabled 状态需同时设置 `cursor: not-allowed` 和 `pointer-events: none`。

### Input
- 清除图标仅在 hover 且有内容 / focus 且有内容时显示，离开后隐藏。
- 有后缀时，清除图标移入 suffix flex 容器作为第一个子元素，不再绝对定位。
- 多行框字数统计绝对定位于框内右下角，`padding-bottom >= 24px`。
- 前置/后置与输入框拼接使用 `margin-left: -1px` 消除双线，配合 `z-index` 确保聚焦时描边在上层。
- 后置选择激活时背景**始终为** `#F5F7FA`，只有前置在激活时变为 `#FFFFFF`。

### Table
- 必须使用 `border-collapse: separate`，collapse 模式会裁剪 sticky 列的阴影。
- 阴影列使用 `position: fixed` + `getBoundingClientRect()` 定位，脱离父元素 `overflow: hidden` 裁剪。
- 删除确认气泡和字段筛选下拉均使用 `position: fixed` + `getBoundingClientRect()` 定位。

### Layout
- TabBar 放在 `right-panel` 顶部，不可遮盖 `sidenav` 区域。
- `right-panel` 必须设置 `overflow: hidden`。

### Select
- 面板使用 `position: fixed` + `getBoundingClientRect()` 定位，绕过父元素 `overflow:hidden` 裁剪。
- 面板 `padding: 8px` 已提供选项两端间距，选项本身不需要额外 margin。

## Quick Reference

### Transition Defaults
- Border/Background/Color: `0.15s`
- Transform (chevron): `0.2s`
- Opacity (tooltip): `0.15s`
- Shadow opacity: `0.2s`

### Z-Index Hierarchy
- Normal thead th: 3
- Sticky tbody td: 4
- Sticky thead th: 5
- Dropdown/Select panel: 3000
- Modal overlay: 1000

### Scrollbar Defaults
- Width: 4px
- Thumb color: `#DDE1EB`
- Border radius: 2px

## Additional Resources

For detailed component specifications, interaction states, and implementation notes, see [reference.md](reference.md).
