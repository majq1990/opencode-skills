# 综合设计系统文档

> 基于 Google Style Guides + Material Design 3 + ZartUI + 多主题架构的完整设计规范
> 整合日期：2026-03-18

## 📋 文档结构

1. [设计系统总览](#1-设计系统总览)
2. [Material Design 3 设计原则](#2-material-design-3-设计原则)
3. [ZartUI 多主题架构](#3-zartui-多主题架构)
4. [颜色系统设计](#4-颜色系统设计)
5. [字体与排版系统](#5-字体与排版系统)
6. [组件设计规范](#6-组件设计规范)
7. [交互与动效](#7-交互与动效)
8. [响应式设计](#8-响应式设计)
9. [开发工具链](#9-开发工具链)
10. [代码规范集成](#10-代码规范集成)
11. [最佳实践指南](#11-最佳实践指南)

---

## 1. 设计系统总览

### 🎯 设计理念融合

本设计系统融合了三大设计体系的精髓：

- **Google Style Guides**: 代码层面的设计一致性与可读性
- **Material Design 3**: 现代化的视觉语言与交互体验
- **ZartUI**: 企业级多主题组件库实践

### 🏗️ 技术架构栈

| 层级 | 技术方案 | 主要用途 |
|-----|---------|----------|
| **组件库** | ZartUI (`zartd`) + ZartUI-Biz (`zartd-biz`) + Ant Design Vue 3 | 企业级组件库 |
| **样式语言** | Less (Ant Design Vue) + SCSS (ZartUI & 应用层) | 样式预处理 |
| **CSS 变量** | `--zartd-*` 前缀统一管理 | Token 管理 |
| **响应式单位** | `pxtorem`，根值 `100px` | 自适应布局 |
| **主题系统** | CSS 变量 + 类名切换 | 多主题支持 |

### 🎨 主题支持矩阵

| 主题名称 | 选择器 | 主色调 | 适用场景 |
|---------|--------|--------|----------|
| **Light (默认)** | `:root` | `#3388ff` | 标准亮色主题 |
| **Dark** | `:root.dark` 或 `:root[theme-color='dark']` | `#3388ff` | 深色模式 |
| **Gov (政府)** | `:root.gov` 或 `:root[theme-color='gov']` | `#ff4300` | 政府项目专用 |

---

## 2. Material Design 3 设计原则

### 🌟 核心设计原则

#### 1. 适应性设计 (Adaptive Design)
- **动态色彩**: 基于壁纸的动态色彩提取
- **响应式布局**: 适配各种屏幕尺寸和设备类型
- **个性化主题**: 支持用户自定义主题色彩

#### 2. 材料隐喻 (Material Metaphor)
- **层次感**: 通过阴影和高度表达元素层级
- **动画过渡**: 自然的动效表达空间关系
- **触觉反馈**: 模拟真实材料的交互体验

#### 3. 大胆图形 (Bold Graphics)
- **鲜明色彩**: 使用饱和的色彩表达品牌个性
- **几何形状**: 简洁的几何图形构成界面元素
- **留白艺术**: 合理的空间布局提升视觉舒适度

### 🎨 Material 3 色彩系统

#### 动态色彩 (Dynamic Color)
```css
/* Material 3 动态色彩示例 */
:root {
  /* 主要色彩 */
  --md-sys-color-primary: #6750A4;
  --md-sys-color-on-primary: #FFFFFF;
  --md-sys-color-primary-container: #EADDFF;
  --md-sys-color-on-primary-container: #21005D;
  
  /* 次要色彩 */
  --md-sys-color-secondary: #625B71;
  --md-sys-color-on-secondary: #FFFFFF;
  --md-sys-color-secondary-container: #E8DEF8;
  --md-sys-color-on-secondary-container: #1D192B;
  
  /* 表面色彩 */
  --md-sys-color-surface: #FFFBFE;
  --md-sys-color-surface-variant: #E7E0EC;
  --md-sys-color-background: #FFFBFE;
}
```

#### 色彩角色 (Color Roles)
- **Primary**: 主要品牌色彩，用于主要按钮和强调元素
- **Secondary**: 次要品牌色彩，用于次要按钮和装饰元素
- **Tertiary**: 第三品牌色彩，用于特殊场景和强调
- **Surface**: 背景色彩，用于卡片和容器背景
- **Error**: 错误状态色彩，用于警告和错误提示

---

## 3. ZartUI 多主题架构

### 🎯 主题切换机制

#### HTML 属性切换
```html
<!-- 标准亮色主题 (默认) -->
<html>

<!-- 暗色主题 -->
<html theme-color="dark">
<!-- 或 -->
<html class="dark">

<!-- 政府主题 -->
<html theme-color="gov">
<!-- 或 -->
<html class="gov">

<!-- 字体大小控制 -->
<html theme-size="small">  <!-- 小字号 (≈85.71%) -->
<html theme-size="large">  <!-- 大字号 (≈114.29%) -->
```

#### CSS 变量系统
```css
/* 基础色彩系统 */
:root {
  /* 灰度色彩 (10级体系) */
  --zartd-g-0: #ffffff;   /* 纯白 */
  --zartd-g-05: #f5f7fa;  /* 最浅灰 (背景层) */
  --zartd-g-10: #e9ecf2;  /* 浅分割线色 */
  --zartd-g-20: #dde1eb;  /* 输入框边框色 */
  --zartd-g-30: #ced4e0;  /* 中浅灰 */
  --zartd-g-40: #a8b4c8;  /* 禁用文字、占位文字 */
  --zartd-g-50: #6b7a99;  /* 次要文字 */
  --zartd-g-60: #223355;  /* 主文字 */
  --zartd-g-70: #081126;  /* 标题色 */
  --zartd-g-80: #000000;  /* 纯黑 */
  
  /* 语义色彩 */
  --zartd-success-color: #11c79b;
  --zartd-warning-color: #ff6600;
  --zartd-error-color: #ff4433;
  --zartd-info-color: #3388ff;
}
```

### 🎨 主题色板生成

#### 主色色板生成规则
```less
/* 每个主题色生成10级色板 */
--zartd-primary-1:  /* 最浅色 */
--zartd-primary-2:  /* 浅色 */
--zartd-primary-3:  /* 中浅色 */
--zartd-primary-4:  /* 中色 */
--zartd-primary-5:  /* 标准色 */
--zartd-primary-6:  /* 中深色 */
--zartd-primary-7:  /* 深色 */
--zartd-primary-8:  /* 深色 */
--zartd-primary-9:  /* 深色 */
--zartd-primary-10: /* 最深色 */
```

#### 透明度渐变系统
```css
/* 20级透明度渐变 */
--zartd-primary-fade-5:   /* 5% 透明度 */
--zartd-primary-fade-10:  /* 10% 透明度 */
--zartd-primary-fade-20:  /* 20% 透明度 */
--zartd-primary-fade-30:  /* 30% 透明度 */
--zartd-primary-fade-40:  /* 40% 透明度 */
--zartd-primary-fade-50:  /* 50% 透明度 */
--zartd-primary-fade-60:  /* 60% 透明度 */
--zartd-primary-fade-70:  /* 70% 透明度 */
--zartd-primary-fade-80:  /* 80% 透明度 */
--zartd-primary-fade-90:  /* 90% 透明度 */
--zartd-primary-fade-100: /* 100% 透明度 */
```

---

## 4. 颜色系统设计

### 🎯 色彩体系架构

#### 基础色彩分类
1. **灰度色彩** (10级体系)
2. **主题色彩** (3套主题)
3. **语义色彩** (状态指示)
4. **功能色彩** (10色系色板)
5. **透明度色彩** (渐变效果)

#### 主题色对照表

| 色彩属性 | Light 主题 | Dark 主题 | Gov 主题 |
|---------|------------|-----------|----------|
| **主色** | `#3388ff` | `#3388ff` | `#ff4300` |
| **成功色** | `#11c79b` | `#11c79b` | `#11c79b` |
| **警告色** | `#ff6600` | `#ff6600` | `#ff6600` |
| **错误色** | `#ff4433` | `#ff4433` | `#ff4433` |
| **背景色** | `#ffffff` | `#22272e` | `#ffffff` |
| **菜单背景** | 默认 | `url(bg.jpg)` 图片 | 深蓝渐变 |

### 🌈 功能色系 (10色系)

| 色系名称 | 基础色值 | CSS 变量前缀 | 用途 |
|---------|----------|-------------|------|
| 红色系 | `#ff4433` | `--zartd-r-*` | 危险、删除操作 |
| 橙色系 | `#ff6600` | `--zartd-o-*` | 警告、重要提醒 |
| 黄色系 | `#ffaa00` | `--zartd-y-*` | 提示、关注信息 |
| 黄绿色系 | `#6be62e` | `--zartd-gn-*` | 成功、通过状态 |
| 青绿色系 | `#11c79b` | `--zartd-gb-*` | 安全、正常状态 |
| 天蓝色系 | `#33bbff` | `--zartd-b-*` | 信息、链接色彩 |
| 深蓝色系 | `#3388ff` | `--zartd-db-*` | 主色、品牌色彩 |
| 紫蓝色系 | `#4433ff` | `--zartd-pb-*` | 特殊状态、VIP |
| 紫色系 | `#aa33ff` | `--zartd-p-*` | 高级功能、特权 |
| 粉色系 | `#ff33dd` | `--zartd-pink-*` | 个性化、装饰性 |

### 📋 色彩使用规范

#### 文本色彩层级
```css
/* 文本色阶级联关系 */
--zartd-text-color-1: #ffffff;  /* 正向（反白）文字 */
--zartd-text-color-2: #f5f7fa;  /* 表格头背景、禁用背景 */
--zartd-text-color-3: #e9ecf2;  /* 分割线、边框 */
--zartd-text-color-4: #dde1eb;  /* 输入框边框 */
--zartd-text-color-5: #ced4e0;  /* 中间过渡灰 */
--zartd-text-color-6: #a8b4c8;  /* placeholder、辅助文字 */
--zartd-text-color-7: #6b7a99;  /* 二级文字 */
--zartd-text-color-8: #223355;  /* 主文字（#235） */
--zartd-text-color-9: #081126;  /* 标题文字 */
--zartd-text-color-10: #000000; /* 极深文字 */
```

#### 语义色彩别名
```css
/* 文本色彩语义别名 */
--zartd-text-color: var(--zartd-text-color-8);           /* 主文字 */
--zartd-text-color-light: var(--zartd-text-color-7);       /* 次要文字 */
--zartd-text-color-lighter: var(--zartd-text-color-6);   /* 辅助文字 */
--zartd-text-color-heavy: var(--zartd-text-color-9);     /* 标题文字 */
--zartd-text-color-positive: var(--zartd-text-color-1);    /* 正向文字 */
--zartd-text-color-negative: var(--zartd-text-color-10); /* 反向文字 */
```

---

## 5. 字体与排版系统

### 📝 字体系统架构

#### 字体族定义
```css
/* 代码专用字体 */
--zartd-font-family-code: 'Consolas', 'Monaco', 'Andale Mono', 'Ubuntu Mono', monospace;

/* 数字专用字体 */
--zartd-font-family-number: 'HarmonyOS Sans';

/* 系统字体继承 */
--zartd-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

#### 字体大小体系
```css
/* 基础字号系统 */
--zartd-font-size-base: 14px;           /* 全局默认字号 */
--zartd-font-size-lg: 16px;           /* 大字号 */
--zartd-font-size-sm: 12px;           /* 小字号 */
--zartd-page-header-heading-title: 18px; /* 页面标题 */
--zartd-avatar-font-size-base: 18px;  /* 头像文字 */
```

### 📏 行高与间距

#### 行高系统
```css
/* 标准行高 */
--zartd-line-height-base: 1.57142857;  /* 约22px for 14px字体 */
--zartd-line-height-lg: 1.6;          /* 大字号行高 */
--zartd-line-height-sm: 1.5;           /* 小字号行高 */
```

#### 间距体系
```less
/* 内边距系统 */
@padding-lg: 24px;   /* 大容器内边距 */
@padding-md: 18px;   /* 标准内边距 */
@padding-sm: 12px;   /* 小组件内边距 */
@padding-xs: 8px;    /* 紧凑内边距 */
@padding-xss: 4px;   /* 最小内边距 */

/* 外边距系统 */
@margin-lg: 24px;    /* 大容器外边距 */
@margin-md: 18px;    /* 标准外边距 */
@margin-sm: 12px;    /* 小组件外边距 */
@margin-xs: 8px;     /* 紧凑外边距 */
@margin-xss: 4px;    /* 最小外边距 */
```

### 🎯 字体渲染优化

#### 字体平滑设置
```css
/* 全局字体渲染优化 */
body {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}
```

#### 响应式字体缩放
```css
/* 字体大小档位控制 */
:root[theme-size='small'] {
  font-size: 85.71%;  /* 约12px */
}

:root[theme-size='large'] {
  font-size: 114.29%; /* 约16px */
}
```

---

## 6. 组件设计规范

### 🧩 按钮组件 (Button)

按钮用于触发业务逻辑或界面交互。ZartUI 按钮系统基于 Ant Design 深度定制，支持多种类型和明确的交互状态。

#### 1. 按钮类型 (Types)
- **主按钮 (Primary)**: 用于主要行动点。
  - 背景：`var(--zartd-primary-color)` (#3388ff)
  - 边框：`var(--zartd-primary-color)`
  - 文本：`#ffffff`
- **默认按钮 (Default)**: 用于常规行动点。
  - 背景：`transparent`
  - 边框：`var(--zartd-border-color)` (#e9ecf2)
  - 文本：`var(--zartd-text-color)` (#223355)
- **虚线按钮 (Dashed)**: 用于添加/上传等辅助性操作。
  - 背景：`transparent` (暗色下为 `#303030`)
  - 边框：`dashed var(--zartd-border-color)`
  - 文本：`var(--zartd-text-color)`
- **文本按钮 (Text)**: 用于不需要明显边界的次要操作。
  - 背景/边框：`transparent`
  - 文本：`var(--zartd-text-color)`
- **链接按钮 (Link)**: 用于页面间导航或轻量级外链。
  - 背景/边框：`transparent`
  - 文本：`var(--zartd-primary-color)`
- **危险按钮 (Dangerous)**: 用于具有破坏性的操作（如删除）。
  - 背景：`transparent` (暗色下为 `#303030`)
  - 边框：`#ff4d4f`
  - 文本：`#ff4d4f`

#### 2. 交互状态规范 (Interaction States)

| 按钮类型 | Hover / Focus 状态 | Active (点击) 状态 | Disabled (禁用) 状态 |
|---------|-------------------|--------------------|---------------------|
| **Primary** | 背景: `#3388ff` (亮度+10%)<br>文本: `#ffffff` | 背景: `#0958d9` (暗度+10%)<br>文本: `#ffffff` | 背景: `rgb(22 119 255 / 40%)`<br>文本: `rgb(255 255 255 / 40%)`<br>光标: `not-allowed` |
| **Default** | 背景: `var(--common-active-background-image)`<br>边框: `var(--zartd-primary-color)`<br>文本: `var(--zartd-primary-color)` | 背景: `#262626` (暗色下)<br>边框: `#383838`<br>文本: `var(--zartd-primary-color)` | 文本: `rgb(255 255 255 / 25%)` (暗色下) / `var(--zartd-text-color-6)` |
| **Dashed** | 背景: `#3b3b3b` (暗色下)<br>边框: `#525252`<br>文本: `#ffffff` | 背景: `#262626`<br>边框: `#383838`<br>文本: `#ffffff` | 文本: `rgb(255 255 255 / 25%)` |
| **Text** | 背景: `rgb(255 255 255 / 8%)`<br>文本: `#ffffff` (暗色下) | 背景: `rgb(255 255 255 / 12%)`<br>文本: `#ffffff` | 文本: `rgb(255 255 255 / 25%)` |
| **Link** | 文本: `#3388ff` (提亮)<br>背景: `transparent` | 文本: `#0958d9` (压暗)<br>背景: `transparent` | 文本: `rgb(22 119 255 / 40%)` |
| **Dangerous** | 边框: `#ff7875`<br>文本: `#ff7875`<br>背景: `#3b3b3b` | 边框: `#d9363e`<br>文本: `#d9363e`<br>背景: `#262626` | 边框: `var(--zartd-error-color-active)`<br>文本: `var(--zartd-error-color-active)` |

#### 3. 按钮尺寸与 Token (Tokens & Sizes)
- **标准高度 (@height-base)**: `32px`
- **大尺寸 (@height-lg)**: `40px`
- **小尺寸 (@height-sm)**: `24px`
- **水平内边距 (@btn-padding-horizontal-base)**: `20px`
- **圆角 (@border-radius-base)**: `4px`
- **阴影 (@btn-shadow)**: `none` (无阴影扁平化设计)

---

### 🧩 基础组件规范

#### 圆角设计系统
```less
/* 基础圆角规范 */
@border-radius-base: 4px;           /* 全局基础圆角 */
@border-radius-lg: 6px;             /* 大圆角 */
@border-radius-sm: 2px;             /* 小圆角 */
@checkbox-border-radius: 2px;       /* 复选框圆角 */
@table-border-radius-base: 0;       /* 表格（无圆角） */
```

#### 阴影设计系统
```css
/* 全局阴影系统 */
--zartd-box-shadow: 0 2px 24px 2px rgb(0 0 0 / 10%);
--zartd-shadow-color: rgb(0 0 0 / 10%);

/* 组件特定阴影 */
--zartd-modal-content-box-shadow-color: rgb(0 67 202 / 20%);
--zartd-panel-background-box-shadow: 2px 2px 4px 0 rgb(0 114 255 / 6%);
--zartd-nav-overall-box-shadow: 0 2px 40px 0 rgb(0 0 0 / 10%);
```

#### 边框设计系统
```less
/* 边框基础规范 */
@border-width-base: 1px;
@border-style-base: solid;
@border-color-base: var(--zartd-input-border-color);     /* #dde1eb */
@border-color-split: var(--zartd-border-color);          /* #e9ecf2 */
@disabled-color: #a8b4c8;                               /* 禁用状态 */
```

### 📐 组件尺寸规范

#### 高度规范
```less
/* 组件高度系统 */
@height-base: 32px;     /* 标准控件高度 */
@height-lg: 40px;      /* 大号控件高度 */
@height-sm: 24px;      /* 小号控件高度 */
```

#### 表单控件规范
```less
/* 表单控件内边距 */
@control-padding-horizontal: 9px;      /* 标准水平内边距 */
@control-padding-horizontal-sm: 6px;   /* 小尺寸水平内边距 */
```

### 🧱 特定组件规范

#### 按钮组件
```less
/* 按钮专用规范 */
@btn-padding-horizontal-base: 20px;    /* 按钮水平内边距 */
@btn-border-radius-base: @border-radius-base; /* 按钮圆角 */
```

#### 菜单组件
```less
/* 菜单专用规范 */
@menu-item-group-height: 40px;         /* 菜单项高度 */
@menu-collapsed-width: 56px;           /* 收起状态宽度 */
@menu-item-vertical-margin: 8px;       /* 菜单项垂直间距 */
@menu-item-padding-horizontal: 10px;   /* 菜单项水平内边距 */
@menu-icon-margin-right: 10px;         /* 菜单图标右边距 */
```

#### 表格组件
```less
/* 表格专用规范 */
@table-padding-vertical: 9px;          /* 表格垂直内边距 */
@table-padding-horizontal: 8px;        /* 表格水平内边距 */
@table-border-radius-base: 0;          /* 表格圆角（无圆角） */
```

---

## 7. 交互与动效

### 🎯 滚动条统一规范

#### 自定义滚动条样式
```css
/* 统一滚动条样式 */
::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--zartd-text-color-6);  /* #a8b4c8 */
  border-radius: 5px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--zartd-text-color-7);  /* #6b7a99 */
}

::-webkit-scrollbar-corner {
  background: transparent;
}
```

### ✨ 动画与过渡

#### Material Design 动效原则
```css
/* 标准过渡动画 */
.transition-standard {
  transition-duration: 200ms;
  transition-timing-function: cubic-bezier(0.4, 0.0, 0.2, 1);
}

.transition-decelerate {
  transition-duration: 250ms;
  transition-timing-function: cubic-bezier(0.0, 0.0, 0.2, 1);
}

.transition-accelerate {
  transition-duration: 200ms;
  transition-timing-function: cubic-bezier(0.4, 0.0, 1, 1);
}
```

#### 交互状态反馈
```css
/* 悬停状态 */
.hover-effect:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.2s ease;
}

/* 激活状态 */
.active-effect:active {
  transform: scale(0.98);
  transition: all 0.1s ease;
}

/* 焦点状态 */
.focus-effect:focus {
  outline: 2px solid var(--zartd-primary-color);
  outline-offset: 2px;
}
```

---

## 8. 响应式设计

### 📱 响应式策略

#### 主要策略
- **桌面优先**: 主要面向PC桌面端用户
- **rem单位**: 使用rem实现等比缩放
- **弹性布局**: Flex/Grid布局适配不同屏幕
- **字体缩放**: 通过theme-size属性控制全局字体

#### 转换机制
```css
/* pxtorem转换规则 */
设计稿 1px → 生产 0.01rem
根字体大小: 100px (默认)

/* 字体大小档位 */
:root[theme-size='small'] {
  font-size: 85.71%;  /* 约缩小至86% */
}

:root[theme-size='large'] {
  font-size: 114.29%; /* 约放大至114% */
}
```

### 🎯 布局适配

#### 弹性布局系统
```css
/* Flex布局规范 */
.flex-container {
  display: flex;
  flex-wrap: wrap;
  gap: var(--zartd-spacing-md);
}

.flex-item {
  flex: 1 1 300px;  /* 基础宽度300px，可伸缩 */
  min-width: 0;     /* 防止内容溢出 */
}
```

#### Grid布局系统
```css
/* Grid布局规范 */
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--zartd-spacing-lg);
}
```

---

## 9. 开发工具链

### 🛠️ SCSS Mixin 工具集

#### 基础工具Mixin
```scss
// 尺寸设置
@mixin size($width: 100%, $height: 100%) {
  width: $width;
  height: $height;
}

// Flex布局
@mixin flex($row: row, $justify-content: flex-start, $align-items: flex-start, $wrap: nowrap) {
  display: flex;
  flex-direction: $row;
  justify-content: $justify-content;
  align-items: $align-items;
  flex-wrap: $wrap;
}

// 字体设置
@mixin font($font-size: $font-size-g, $font-weight: normal, $font-family: inherit) {
  font-size: $font-size;
  font-weight: $font-weight;
  font-family: $font-family;
}
```

#### 高级功能Mixin
```scss
// 单行省略号
@mixin ellipsis() {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// 多行省略号
@mixin multiellipsis($line: 2) {
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: $line;
  -webkit-box-orient: vertical;
}

// 绝对定位
@mixin absolute($top: unset, $right: unset, $bottom: unset, $left: unset) {
  position: absolute;
  top: $top;
  right: $right;
  bottom: $bottom;
  left: $left;
}

// 线性渐变
@mixin linear-gradient($start, $end, $degrees: 0deg) {
  background: linear-gradient($degrees, $start 0%, $end 100%);
}

// 完美居中
@mixin center($center: all) {
  position: absolute;
  @if $center == all {
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  } @else if $center == vertical {
    top: 50%;
    transform: translateY(-50%);
  } @else if $center == horizontal {
    left: 50%;
    transform: translateX(-50%);
  }
}
```

### 🔧 自动化工具链

#### 代码格式化工具
```json
{
  "scripts": {
    "format:css": "prettier --write \"**/*.{css,scss,less}\"",
    "format:js": "prettier --write \"**/*.{js,ts,vue}\"",
    "format": "npm run format:css && npm run format:js"
  }
}
```

#### 样式检查工具
```json
{
  "scripts": {
    "lint:css": "stylelint \"**/*.{css,scss,less}\"",
    "lint:js": "eslint \"**/*.{js,ts,vue}\"",
    "lint": "npm run lint:css && npm run lint:js"
  }
}
```

---

## 10. 代码规范集成

### 📝 Google Style Guide 集成

#### JavaScript/TypeScript 规范
```javascript
// 命名规范
class UserProfile { }                    // 类名：UpperCamelCase
function getUserData() { }              // 函数名：lowerCamelCase
const MAX_RETRY_COUNT = 3;              // 常量：CONSTANT_CASE
private userId_: string;                 // 私有属性：下划线后缀

// 代码结构
const user = getUser();                  // 使用const/let，避免var
let counter = 0;
const add = (a, b) => a + b;             // 箭头函数优先
const message = `Hello, ${userName}!`;   // 模板字符串
```

#### HTML/CSS 规范
```html
<!-- HTML语义化 -->
<nav>导航内容</nav>
<article>文章内容</article>
<section>章节内容</section>
```

```css
/* CSS属性排序 */
.example {
  background: fuchsia;
  border: 1px solid;
  color: black;
  text-align: center;
  text-indent: 2em;
}

/* 有意义的类名 */
.gallery { }      /* 推荐：具体含义 */
.login { }        /* 推荐：功能导向 */
```

#### Python 规范
```python
# 代码布局
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total

# 命名约定
import my_module                        # 模块名：小写+下划线
class MyClass: pass                    # 类名：UpperCamelCase
def my_function(): pass                # 函数名：小写+下划线
MAX_SIZE = 100                         # 常量：大写+下划线
```

---

## 11. 最佳实践指南

### 🎯 设计原则最佳实践

#### 1. 一致性原则
- **跨组件统一**: 所有组件遵循相同的设计语言
- **跨平台统一**: Web、移动端保持视觉一致性
- **跨主题统一**: 不同主题间保持交互逻辑一致

#### 2. 可用性原则
- **可访问性**: 支持键盘导航、屏幕阅读器
- **响应式**: 适配不同设备和屏幕尺寸
- **性能优先**: 优化加载速度和运行性能

#### 3. 可维护性原则
- **模块化**: 组件化开发，便于维护和复用
- **文档化**: 完善的文档和示例代码
- **自动化**: 使用工具链保证代码质量

### 🛠️ 开发流程最佳实践

#### 1. 组件开发流程
```
需求分析 → 设计规范 → 组件开发 → 测试验证 → 文档编写 → 发布上线
```

#### 2. 代码质量保证
```bash
# 代码提交前检查
npm run lint          # 代码规范检查
npm run test          # 单元测试
npm run build         # 构建验证
npm run type-check    # 类型检查（TypeScript项目）
```

#### 3. 性能优化策略
- **懒加载**: 按需加载组件和资源
- **代码分割**: 使用动态导入进行代码分割
- **缓存策略**: 合理使用浏览器缓存
- **图片优化**: 使用适当的图片格式和压缩

### 🔍 质量检查清单

#### 设计质量检查
- [ ] 色彩对比度符合WCAG 2.1 AA标准
- [ ] 字体大小和行高合理
- [ ] 交互状态完整（默认、悬停、激活、禁用）
- [ ] 动画效果自然流畅
- [ ] 响应式布局适配良好

#### 代码质量检查
- [ ] 遵循命名规范
- [ ] 代码格式化一致
- [ ] 注释清晰完整
- [ ] 无死代码和冗余代码
- [ ] 错误处理完善

#### 可访问性检查
- [ ] 支持键盘导航
- [ ] 提供适当的ARIA标签
- [ ] 色彩不是唯一的信息传达方式
- [ ] 支持屏幕阅读器
- [ ] 动画可关闭（prefers-reduced-motion）

---

## 📚 参考资源

### Material Design 资源
- [Material Design 3 官方网站](https://m3.material.io/)
- [Material Design 组件库](https://material.io/components)
- [Material Design 色彩工具](https://material.io/design/color/the-color-system.html)

### ZartUI 资源
- [ZartUI 官方文档](https://web.zartui.egova.com.cn/overview.html)
- [ZartUI 组件示例](https://web.zartui.egova.com.cn/components/button)
- [ZartUI 主题系统](https://web.zartui.egova.com.cn/theme)

### Google Style Guides
- [HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html)
- [JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html)
- [TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- [Python Style Guide](https://google.github.io/styleguide/pyguide.html)

### 开发工具
- [Prettier 代码格式化](https://prettier.io/)
- [ESLint JavaScript检查](https://eslint.org/)
- [Stylelint CSS检查](https://stylelint.io/)
- [TypeScript 类型检查](https://www.typescriptlang.org/)

---

*本设计系统文档整合了Google Style Guides、Material Design 3、ZartUI多主题架构以及企业级开发最佳实践，为构建一致、高效、可维护的用户界面提供完整的设计和开发规范。*