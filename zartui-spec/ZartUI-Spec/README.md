# ZartUI 规范知识库

存放 ZartUI 设计规范的 AI 可读 JSON 知识库文件。

## 文件列表

| 文件 | 规范内容 |
|---|---|
| [scrollbar-spec.json](./scrollbar-spec.json) | 滚动条规范（Inside/Outside × 垂直/水平） |
| [button-pill-spec.json](./button-pill-spec.json) | 全圆角按钮规范（主按钮、次要按钮、危险状态 × 所有交互状态） |
| [button-spec.json](./button-spec.json) | 矩形按钮规范（面状 / 线状 × md/sm 尺寸 × 所有交互状态） |
| [tab-bar-spec.json](./tab-bar-spec.json) | 标签组件规范（顶部导航标签栏、横向内容标签、纵向内容标签、胶囊组标签页） |
| [steps-spec.json](./steps-spec.json) | 步骤条规范（横向/纵向/上下结构 × 完成/进行中/未完成三态） |
| [sidenav-spec.json](./sidenav-spec.json) | 侧边导航规范（页面内三级 SideNav） |
| [pagination-spec.json](./pagination-spec.json) | 分页规范（基础、高级、迷你三种形态） |
| [dropdown-spec.json](./dropdown-spec.json) | 常规下拉菜单规范（基础/带图标/带子菜单/带搜索/带新增 6 种变体） |
| [page-header-spec.json](./page-header-spec.json) | 页头规范（一级 5 个变体 + 二级 4 个变体） |
| [topnav-spec.json](./topnav-spec.json) | 顶部导航规范（容器、Logo、一级菜单、工具区、用户信息、下拉菜单） |
| [main-sidenav-spec.json](./main-sidenav-spec.json) | 主系统侧边导航规范（容器、Logo、主菜单图标、底部菜单、交互状态） |
| [main-topnav-spec.json](./main-topnav-spec.json) | 主系统顶部导航规范（容器、左侧菜单入口、右侧工具区、用户信息、下拉菜单） |
| [back-to-top-spec.json](./back-to-top-spec.json) | 回到顶部规范（容器、显示逻辑、图标、气泡提示） |
| [breadcrumb-spec.json](./breadcrumb-spec.json) | 面包屑规范（基础样式、下拉切换、交互规则） |
| [tag-spec.json](./tag-spec.json) | 标签规范（基础、重要提示、一般提示、弱提示、icon 类、标签组） |
| [cascader-spec.json](./cascader-spec.json) | 级联选择规范（触发框、下拉面板、选项、复选框、单选/多选交互） |
| [checkbox-spec.json](./checkbox-spec.json) | 复选框规范（默认/Hover/半选/全选/禁用 五种状态） |

## 使用说明

- 每个 JSON 文件对应一个组件或规范模块
- 所有文件结构统一包含：`variants`（变体）、`shared_tokens`（设计 token）、`known_pitfalls`（注意事项）
- 后续新增规范直接放入本目录，并在上方表格中补充索引
