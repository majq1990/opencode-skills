# 题目二（必考）：PC 工作台 — 建筑垃圾监管工作台 保姆级全操作手册（40 分）

> 原题存档：`../exam/题目二-PC工作台-原题.md`（nodeId=Y1OQX0akWm3gYmA4ivD7MZrkJGlDd3mE）
> 面向对象：正在考试的工程师。本手册把每一步落到「点哪个菜单 → 弹什么界面 → 每个属性怎么填 → 保存 → 怎么验证」的粒度。
> **JS 层已按 `references/scripting/` 最新脚本规范升级（2026-07-10）**：`const self = this;` 约定、const/let、数据源调用收拢进 `execDdcat` 适配函数、Promise 链 finally 收口 loading；SQL/操作步骤/评分表/坑总表未动。变更明细见文末「脚本规范升级说明」。
> 所有 `xxx_替换我` 形式的 ID 都要换成你自己页面里的真实 ID：
> - **资源 ID（数据模型/API/页面）**：任意动作绑定脚本窗口内按 **Ctrl+Shift+C**，弹出资源选择器 → 选类型（数据模型/api/页面）→ 选中目标 → 点【确定】，ID 自动回填到光标处。
> - **组件 ID**：画布中选中组件 → 右侧属性面板切到「高级」→ 查看「唯一标识」（如 `text_7lxzjn`、`container_f3r5gg`）。
> - 文档未记载确切界面文案的地方本手册标注「（以现场界面为准）」，属性名可能随版本微调，按语义找同类属性即可，**不要因为找不到一模一样的字眼卡住**。

---

## §0 考前准备（开工前 10 分钟）

### 0.1 进入考试应用

1. 打开考试环境灵珑平台地址，用考试分配的账号登录灵珑设计端（不是应用访问端）。
2. 顶部/左侧进入 **「应用管理」** → 在应用列表找到考试内置应用（名称以监考说明为准）→ 点击进入应用的 **设计工作台**。
3. 进入后确认左侧导航可见以下入口（不同版本名称略有差异，以现场界面为准）：
   - **数据管理**：业务实体 / 数据视图 / 数据模型（DDCAT）——本题数据源已内置，只需查 ID，不需要新建；
   - **部件设计**（部件管理）：表单部件、列表部件在这里新建；
   - **页面设计**（页面管理）：工作台页面在这里新建；
   - **API 管理**：本题一般用不到。
4. 先花 2 分钟到「数据管理」里逐个点开确认四组内置数据源都在：
   - 视图：**项目下拉**、**车辆选择下拉**、**垃圾类型下拉**（查询筛选项）；
   - 视图：**联单概览统计**（数据概览）；
   - DDCAT 数据模型：**联单趋势**；
   - 视图：**电子联单列表**（联单列表）。

### 0.1.1 Ctrl+Shift+C 资源选择器（全程最常用的动作，先练一遍）

后面所有脚本里的资源 ID（数据模型 / API / 页面）都靠它回填，开工前空跑一遍熟悉手感：

1. 随便打开一个动作绑定的脚本编辑窗口（比如任选一个按钮 → 高级 → 绑定动作 → 自定义动作 → 编辑脚本）。
2. 把光标停在脚本里想插入 ID 的位置（如引号中间）。
3. 按 **Ctrl+Shift+C** → 弹出资源选择器窗口。
4. 窗口内先选资源类型页签：**数据模型**（本题查 DS_OVERVIEW/DS_TREND/DS_LIST 用）、**api**（本题基本不用）、**页面**（查 PAGE_LIST 用）。
5. 在列表里点选目标资源 → 点【确定】→ ID 字符串自动插入到光标处。
6. 把插入的 ID 复制到 0.2 的登记表里备用，然后可以撤销脚本改动。

> 备用方法（选择器打不开时）：F12 → Network 面板 → 打开「数据管理-数据模型」列表页，在接口返回 JSON 里找目标模型的 id 字段。**尽量不用手抄，UUID 错一位查一小时**。

### 0.2 ID 登记表（先抄下来再动手）

拿张纸或开个记事本，边配边填。后面所有脚本里的占位符都从这张表替换：

| 占位符 | 含义 | 获取方式 |
|---|---|---|
| `DS_OVERVIEW` | 「联单概览统计」视图对应数据模型 ID | Ctrl+Shift+C 选数据模型 |
| `DS_TREND` | 「联单趋势」DDCAT 数据模型 ID | 同上 |
| `DS_LIST` | 「电子联单列表」视图/数据模型 ID | 同上 |
| `PAGE_LIST` | 联单列表页（“更多>”跳转目标页面）ID | Ctrl+Shift+C 选页面 |
| `site_select` / `vehicle_select` / `muck_select` / `date_range` | 查询区 4 个筛选组件 ID | 组件属性-高级-唯一标识 |
| `single_select_cicle` | 天/周/月 粒度下拉组件 ID | 同上 |
| `container_trend` | 趋势图容器组件 ID | 同上 |
| `text_total` / `text_abnormal` / `text_clean` / `text_disposal` | 4 个指标数值文本组件 ID | 同上 |
| `table_list` | 联单列表部件在页面里的渲染组件 ID | 同上 |

> 组件的「唯一标识」是系统生成的随机串（如 `single_select_6o6rlx`），**不能改成上面这种语义名**。本手册用语义名指代，你登记的是真实随机串，脚本里替换成真实串。

### 0.3 关键前置：先拖隐藏环形图，加载 ECharts 库（趋势图 16 分的生死开关）

页面里必须存在至少一个 ECharts 类型组件，系统才会自动加载 ECharts 库；否则后面写脚本必报 `echarts is not defined`。**现在就做，不要等 §4**。完整操作：

1. 在「页面设计」新建好工作台页面后（见 §1.1），进入页面编辑画布。
2. 左侧组件库里找到 **「容器」** 组件 → 按住拖到画布任意角落（推荐页面最底部，不占正式布局）。
3. 左侧组件库切到图表类分组，找到 **「环形图」**（任意 ECharts 图表都行，环形图最顺手）→ 拖进刚才这个容器内部。
4. 选中**外层这个容器**（不是环形图本身）→ 右侧属性面板：
   - 找到 **「默认状态」** 属性 → 设为 **「隐藏」**；
   - 同时 **开启「强制渲染模式」** 开关（属性面板同一区域，以现场界面为准）。
5. 点页面右上角【保存】。

为什么这么绕：环形图组件本身**没有隐藏属性**，必须借外层容器隐藏；而隐藏的容器默认不渲染 DOM，不开「强制渲染」的话 ECharts 库同样不会加载、`getElementById` 也拿 null。

**✅ 本步验证**：保存后点【预览】→ F12 打开控制台 → 输入 `echarts` 回车 → 返回一个对象（而不是 `Uncaught ReferenceError: echarts is not defined`）即成功。

### 0.4 任务拆解与时间检查点（按操作顺序，总预算约 2.5h）

1. 页面骨架布局（15min）→ 2. 查询区表单部件（30min）→ 3. 数据概览 4 卡片（30min）→ 4. ECharts 趋势图（40min）→ 5. 联单列表 + 导出 + 更多（30min）→ 6. 查询/重置全页联动调试（25min）。

**策略：先把 §6 的联动 JS 骨架贴进页面 didMounted（哪怕组件 ID 还是占位符），再逐模块补 ID**，避免最后大重构。

考中对表的里程碑（超时就砍加分项，保核心分）：

| 时间点 | 应达到的状态 | 落后时砍什么 |
|---|---|---|
| +0:45 | 骨架 + 查询区 6 组件就位，下拉有数据 | 卡片底图/样式全部从简 |
| +1:15 | 概览 4 卡出真实数值 | 详情部件方案不碰，只走 JS 版 |
| +2:00 | 趋势图出柱+线，粒度能切 | resize 自适应、tooltip 美化跳过 |
| +2:30 | 列表 + 导出 + 更多 + 联动全通 | 「更多>」参数带入（5.7 第 3 步）跳过 |

**⚠️ 注意事项**
- 每完成一个小步骤就点一次【保存】，灵珑设计器没有自动保存兜底（以现场界面为准）。
- 所有脚本里的符号必须用**英文输入法**输入，中文逗号/引号直接语法报错。

---

## §1 页面骨架布局

### 1.1 新建页面

1. 左侧导航点 **「页面设计」**（页面管理）→ 建议先点【新建分组】建一个自己名字的分组（考试应用多人共用时防混淆；单人应用可跳过）。
2. 点【新建页面】→ 弹出新建窗口 → 页面名称填 **「建筑垃圾监管工作台」** → 类型选普通 PC 页面（默认即可）→ 点【确定】。
3. 自动进入页面编辑画布：左侧是组件库，中间是画布，右侧是选中组件的属性面板。

### 1.2 根容器 + 网格布局逐层搭建

官方工作台配置文档的标准套路就是「容器 → 网格布局（简）→ 嵌套网格细分」，逐层操作：

1. **根容器**：从左侧组件库拖一个 **「容器」** 到画布，作为页面根，宽高拉满整个画布（宽 100%，高 100% 或固定 1080 类，以现场界面为准）。
2. **主网格**：向根容器内拖入 **「网格布局（简）」** 组件 → 选中它 → 右侧属性面板设置**行/列划分**：
   - 属性面板里找行列配置项（可能叫「行数/列数」+ 每行的高度比例，或直接可视化拖分隔线，以现场界面为准）；
   - 划成 **3 行 1 列**，行高比例大致：**第 1 行约 10%**（查询区）、**第 2 行约 40%**（统计区）、**第 3 行约 50%**（联单列表区）；
   - 行高支持像素就给：约 90px / 380px / 剩余。
3. **统计区子网格**：点选第 2 行的网格单元格 → 向格子里**再拖入一层「网格布局（简）」** → 设 **1 行 2 列**：
   - **左列（约 35% 宽）**：4 张指标卡；
   - **右列（约 65% 宽）**：趋势图容器。
4. **占位容器**：每个最终网格单元格里都先各拖一个空 **「容器」** 占位（第 1 行 1 个、左列 1 个、右列 1 个、第 3 行 1 个），后续内容都往对应容器里丢——直接把部件丢进网格格子也行，但套一层容器后面调边距/背景更方便。

### 1.3 左列卡片区的两种排法（选一种）

- **方案 A（网格）**：左列容器内再放一个「网格布局（简）」，划 2×2 四格（或 4×1 纵向四行），每格放一张卡。
- **方案 B（flex 弹性）**：选中左列容器 → 右侧属性面板找到 **「弹性模式」** 开关 → 开启 → 出现排列方向选项：
  - 横排卡片选 **横向排列 + 主轴对称排布**；
  - 纵排卡片选 **纵向排列**；
  - 每张卡 = 一个子容器，依次拖 4 个进去。

对照考题截图微调尺寸即可，**布局本身不计分，别抠像素**。

**✅ 本步验证**：画布上能看清 3 行结构、第 2 行左右两列、左列 4 个卡片占位容器；保存后预览页面无报错、区块比例大致对得上截图。

**⚠️ 注意事项**
- 趋势图所在的右列容器**必须有固定高度**（后面 §4.1 要求 ≥300px），网格行高按百分比给的话预览时确认实际像素不为 0。
- §0.3 的隐藏环形图容器别忘了已经在这个页面里，不要误删。

---

## §2 查询区配置（8 分）

### 2.1 新建查询表单部件

查询区推荐做成一个独立的**表单部件**再挂到页面上（组件集中、`this.$$()` 查找方便）：

1. 左侧导航点 **「部件设计」** → 点【新建】→ 类型选 **表单部件** →（新建策略如有选择，选**自动策略/空白表单**——这个查询表单不落库，不需要绑业务实体）→ 名称填「工作台查询表单」→【确定】进入表单设计画布。
2. 表单画布同样是：左侧组件库 / 中间画布 / 右侧属性面板。把表单布局设为一行横排（可用表单自带栅格把 6 个组件排在一行，操作以现场界面为准）。

### 2.2 逐个拖入 6 个组件

按下表从左到右依次拖入，**每拖一个就到右侧属性面板改属性、抄唯一标识**：

| 顺序 | 组件（组件库名称） | 标签/文案 | 关键属性 | 登记 ID |
|---|---|---|---|---|
| 1 | **下拉多选** | 项目名称 | 占位提示「请选择项目名称」；允许清空 | `site_select` |
| 2 | **下拉单选**（开启可搜索开关，若有） | 车牌号 | 占位提示「请选择车牌号」；允许清空 | `vehicle_select` |
| 3 | **下拉单选** | 垃圾类型 | 占位提示「垃圾类型」；允许清空 | `muck_select` |
| 4 | **日期范围选择**（日期区间） | 运输时间 | 默认近 30 天，见 2.4 | `date_range` |
| 5 | **按钮** | 重置 | 绑定自定义动作（脚本见 §6.3） | — |
| 6 | **按钮** | 查询 | 主按钮样式；绑定自定义动作（脚本见 §6.2） | — |

**每个组件的标准 4 步（以「项目名称」为例，其余照做）**：

1. **拖**：左侧组件库找到「下拉多选」→ 按住拖到表单画布对应格子。找不到组件名就在组件库顶部搜索框搜「下拉」（以现场界面为准）。
2. **改标签**：选中组件 → 右侧属性面板「基础」区 → 「标题/标签」改成「项目名称」。
3. **改关键属性**（以现场界面为准）：
   - **占位提示**：属性面板找「占位提示 / placeholder / 提示文字」输入框，把表格里的文案**原样**敲进去——评分点核对文案，一字别差（注意第三个是「垃圾类型」，没有“请选择”）；
   - **允许清空**：找「允许清空 / 可清空」开关 → 打开。开了之后选中值时组件右侧出现 ×，这就是评分点「支持清空」的外在表现；
   - 车牌号下拉如属性面板有「可搜索 / 支持筛选」开关，顺手打开（题目允许“下拉单选 / 下拉搜索”两种形态）。
4. **抄 ID**：属性面板切「高级」页签 → 复制「唯一标识」到 §0.2 登记表对应行。

日期范围组件同样走这 4 步（标签「运输时间」，无占位/清空要求）；两个按钮只需改「按钮文字」为「重置」「查询」，查询按钮类型选主按钮（蓝色实底，以现场界面为准）。

### 2.3 三个下拉绑定视图数据源（点击级）

对每个下拉组件依次操作（以「项目名称」为例）：

1. 选中下拉组件 → 右侧属性面板找到 **「数据源」/「选项来源」** 配置区（以现场界面为准）。
2. 数据源类型选 **「数据集/视图」**（不是「静态选项」也不是「字典」）。
3. 点选择数据集 → 弹出数据集选择窗口 → 选考试内置视图：
   - 项目名称 → **项目下拉**；
   - 车牌号 → **车辆选择下拉**；
   - 垃圾类型 → **垃圾类型下拉**。
4. 选完后属性面板出现字段映射两项（名称可能叫「显示字段/标签字段」和「值字段/存储字段」，以现场界面为准）：

| 下拉 | 显示字段（label） | 值字段（value） |
|---|---|---|
| 项目名称 | 项目名称（名称类字段） | `site_id` |
| 车牌号 | `vehicle_num` | `vehicle_num` |
| 垃圾类型 | 类型名称字段 | `muck_type` |

5. 配完点表单右上角【保存】，再点【预览】（如有）确认下拉能展开且有数据。

**⚠️ value 必须是入参要用的字段值**（`site_id`/`vehicle_num`/`muck_type`），绑成展示名后面传参全查空——这是本题最阴的暗坑之一。

### 2.4 运输时间默认近 30 天（两种配法，A 不行就 B）

- **配法 A（属性面板，优先试）**：选中日期范围组件 → 属性面板找「默认值」→ 若提供 **「动态默认值」** 且有「近 30 天」快捷选项，直接选上（以现场界面为准）。保存预览确认组件里自动带出了近 30 天的起止日期。
- **配法 B（JS 赋值，兜底必备）**：属性面板没有动态默认值时，靠页面 didMounted 脚本赋值（§6.1 的骨架已包含调用），函数如下：

```js
function setDefaultDateRange(self) {
  // moment() 每次新建实例，无共享对象，直接 format 安全；若改用组件的 moment 对象（如 currentTime）必须先 .clone()
  const end = moment().format('YYYY-MM-DD');
  const start = moment().subtract(29, 'days').format('YYYY-MM-DD');
  self.$$('date_range').$$setValue([start, end]);
  return [start, end];
}
```

> 即使配法 A 成功，也保留这个函数——重置按钮（§6.3）恢复默认时还要用它。

### 2.5 两个按钮的动作绑定入口

1. 选中「查询」按钮 → 右侧属性面板切到 **「高级」**（或「事件/交互」）页签 → 找到 **「绑定动作」** → 点【添加动作】→ 事件选**单击（click）** → 动作类型选 **「自定义动作」**。
2. 弹出脚本编辑窗口（可点【全屏】放大）→ 先贴一行占位 `function main() {}` →【验证】→【确定】。真正脚本等 §6 联动骨架就位后再贴（§6.2）。
3. 「重置」按钮同样操作，脚本见 §6.3。

### 2.6 把查询表单挂到页面第 1 行

1. 回到「页面设计」→ 打开工作台页面 → 左侧组件库找 **「表单部件渲染组件」**（表单渲染/部件引用，以现场界面为准）→ 拖入第 1 行的占位容器。
2. 选中它 → 右侧属性面板选择要渲染的部件 → 选「工作台查询表单」→ 保存。

**✅ 本步验证**：预览页面 → 第 1 行出现 6 个控件一字排开；三个下拉能展开且有真实选项；日期默认近 30 天；下拉选值后出现清空 ×；占位文案与题目一字不差。

**⚠️ 注意事项**
- 项目名称必须是**下拉多选**、垃圾类型必须是**下拉单选**，组件类型拖错直接丢「查询-内容」分。
- 占位提示三处文案是评分点原文：「请选择项目名称」「请选择车牌号」「垃圾类型」（第三个没有“请选择”）。
- 按钮先占位后填脚本，别在这一步陷进联动逻辑。

---

## §3 数据概览配置（8 分）

**推荐方案：容器卡片 + 图片组件 + 文本组件 + JS 赋值**。空数据兜底完全可控，评分“详情组件展示 4 指标”同样认可此展示形态；若时间富余也可用详情部件绑「联单概览统计」视图再 `$$setExtraParams` 传参，但兜底 0/0.00 不好控，**考试用 JS 版**。

### 3.1 搭第一张卡片（点击级）

1. 打开工作台页面 → 定位到第 2 行左列的第一个卡片占位容器（§1.3）。
2. 选中该容器 → 属性面板设 **宽高**（对照截图，如 260×90 一类）→ 设 **背景**：
   - 有卡片底图素材：属性面板「背景图片」→ 点上传 → 选考题提供的卡片底图（素材下载见 3.2）；
   - 没有底图：设背景色 + 圆角即可，不计分。
3. 向卡片容器内拖入 **「图片」组件**（放左侧）：
   - 选中图片组件 → 属性面板找「图片地址/上传图片」→ 点【上传】→ 弹出素材上传窗口 → 选本地下载好的图标 →【确定】；
   - 设图片宽高约 48×48（对照截图）。
4. 向卡片容器内拖入 **两个「文本」组件**（放图标右侧，上下排）：
   - 上面的文本：内容填指标名「联单总数」，小号灰色字；
   - 下面的文本：内容先填占位「0 单」，大号加粗——**这个组件的唯一标识去「高级」页签抄下来，登记为 `text_total`**。

### 3.2 图片素材准备

考题原文档里给了 4 张图标素材（QQ2026 开头的 png）：考试时从题目文档**右键另存**到本地桌面，再在图片组件上传窗口逐一上传。找不到素材就用任意占位图标或纯色块——图标本身不在评分点里，4 个指标数值才是。

### 3.3 复制出另外 3 张卡

1. 选中做好的第一张卡片容器 → 右键（或工具栏）点 **【复制】** → 粘贴 3 次，分别拖进另外 3 个占位格。
2. 逐个修改：图标图片、指标名文本（异常运单数 / 垃圾清运量 / 垃圾处置量）、数值占位（「0 单」「0.00 吨」「0.00 吨」）。
3. **关键**：复制出来的数值文本组件会生成新的唯一标识，逐个选中 → 高级 → 抄「唯一标识」，登记为 `text_abnormal` / `text_clean` / `text_disposal`。**别偷懒沿用第一张的 ID，复制后 ID 是新的**。

### 3.4 概览刷新函数（并入 §6 全局脚本，先看懂）

```js
// 数据概览刷新：入参 queryParams 为 [{name,valueContent}] 数组
// 数据源调用统一走 execDdcat 适配函数（定义见 §6.1）；返回 Promise，供 refreshAll 的 Promise.all 统一 finally 收口 loading
function refreshOverview(self, queryParams) {
  // 空数据兜底：整数显示 0，吨位显示 0.00，绝不出现 undefined/null/NaN
  const fmtInt = function (v) { const n = Number(v); return isFinite(n) ? String(Math.round(n)) : '0'; };
  const fmtTon = function (v) { const n = Number(v); return isFinite(n) ? n.toFixed(2) : '0.00'; };
  return execDdcat('DS_OVERVIEW', queryParams).then(function (res) {
    const row = (res && !res.hasError && res.result && res.result.length) ? res.result[0] : {};
    self.$$('text_total').$$setValue(fmtInt(row.totalWaybillCount) + ' 单');
    self.$$('text_abnormal').$$setValue(fmtInt(row.abnormalWaybillCount) + ' 单');
    self.$$('text_clean').$$setValue(fmtTon(row.cleanAmount) + ' 吨');
    self.$$('text_disposal').$$setValue(fmtTon(row.disposalAmount) + ' 吨');
  }).catch(function (err) {
    console.error('概览查询失败:', err);
    self.$$('text_total').$$setValue('0 单');
    self.$$('text_abnormal').$$setValue('0 单');
    self.$$('text_clean').$$setValue('0.00 吨');
    self.$$('text_disposal').$$setValue('0.00 吨');
  });
}
```

逐段解释：
- `execDdcat('DS_OVERVIEW', queryParams)`：§6.1 定义的 ddcat 数据源适配函数，内部调 `api.DATA_SOURCE_EXECUTE(id, 'ddcat', queryParams, [], '')`；第一参换成你登记的 `DS_OVERVIEW` 真实 ID（Ctrl+Shift+C 回填）。环境若提示 DATA_SOURCE_EXECUTE 废弃，只改 execDdcat 一处即可。
- `res.result[0]`：概览视图返回单行统计，取第一行；查不到就给空对象走兜底。
- `Number(null)=0`、`Number(undefined)=NaN`、`Number('')=0`，`isFinite` 一网打尽；`fmtTon` 对 `null/''` 输出 `0.00`——这段就是「空数据显示 0/0.00，不出现 undefined/null/NaN」这 4 分的保命符。
- 四个 `$$setValue` 的组件 ID 换成 3.1/3.3 登记的真实唯一标识。

### 3.5 备选方案：详情部件绑视图（了解即可，考试不推荐）

评分描述写的是“数据概览详情组件展示 4 指标”，用详情部件也是正路：

1. 「部件设计」→ 新建 **详情部件** → 数据集选「联单概览统计」视图 → 布局里摆 4 个字段（totalWaybillCount 等）。
2. 页面左列拖入详情部件渲染组件 → 查询时对它调 `$$setExtraParams` 传筛选参数再刷新。

不推荐的原因：空数据时详情部件直接空白/横杠，「0/0.00 兜底」这 4 分交互分不可控；单位「单/吨」和两位小数也要靠字段格式化配置碰运气。**JS 版（3.1-3.4）全都攥在自己手里，考试选它**。

**✅ 本步验证**：§6 脚本贴好后预览首屏，4 张卡显示真实数值（或 0/0.00），带单位「单/吨」，吨位两位小数；F12 控制台无红色报错。

**⚠️ 注意事项**
- `row.cleanAmount.toFixed(2)` 在 undefined 上直接抛错 → 整个概览白屏。必须先 `Number()+isFinite()` 再 `toFixed`（上面代码已处理，别自己简化）。
- 复制卡片后**必须重新抄 ID**（3.3 第 3 条），这是概览不刷新的第一大原因。

---

## §4 ECharts 趋势图完整配置（16 分，本题最大分块）

### 4.1 前置：趋势图容器与 DOM id 规则

1. 确认 §0.3 的隐藏环形图容器已在页面里（ECharts 库开关）。
2. 在第 2 行**右列**占位容器内拖入一个 **「容器」** → 选中 → 高级 → 抄「唯一标识」，登记为 `container_trend`（真实值形如 `container_hmcckb`）。
3. 属性面板给这个容器设 **固定高度（如 320px）**——高度为 0 图永远出不来。
4. **DOM id 规则**：该容器渲染到浏览器后的 DOM id = `组件唯一标识 + "_csshandler_generate"`。即脚本里 `document.getElementById('container_trend_csshandler_generate')`。后缀固定拼写，一个字母都不能错。
   - 现场自查法：预览页面 → F12 → Elements 面板 Ctrl+F 搜你的容器唯一标识，能看到完整 DOM id。

### 4.2 天/周/月粒度切换（2 分）

**搭建**：

1. 「部件设计」→ 新建一个小 **表单部件**（名「趋势粒度切换」；若现场允许在页面直接拖下拉组件，也可直接拖，以现场界面为准）。
2. 表单里拖一个 **「下拉单选」** → 属性面板：
   - 选项来源选 **静态选项** → 逐条添加 3 个选项（点【添加选项】）：显示名「天」值 `day`、「周」值 `week`、「月」值 `month`。**值必须是这三个英文串**，与 DDCAT 入参对应；
   - 默认值选 `day`；
   - 高级页签抄「唯一标识」，登记为 `single_select_cicle`。
3. 保存部件 → 回到工作台页面，把这个表单部件渲染组件拖到**趋势图容器右上角**（右列容器内顶部，用 flex 或绝对位置摆右上，以现场界面为准）。

**绑定值改变事件**：

1. 选中下拉组件（在表单部件设计画布里）→ 高级 → 绑定动作 → 添加绑定动作 → 事件选 **onChange（值修改后）** → 进入动作面板，贴：

```js
export function onChange() {
  const self = this;
  const typeValue = self.$$('single_select_cicle').$$getValue();
  window.circleTypeValue = typeValue; // 挂 window 供全局使用
  if (window.queryCircleData) {
    window.queryCircleData(self);     // 粒度变化只重查趋势图
  }
}
```

2. `single_select_cicle` 换成真实唯一标识 →【验证】→【保存】。

> 动作面板里 `export function` 导出的函数名会被动作绑定窗口识别；onChange 事件选中后关联这个函数即可（以现场界面为准）。

### 4.3 趋势图查询 + 渲染（完整可复制，贴进 §6 的页面脚本）

```js
// 联单趋势查询：cicleType 追加进 queryParams 后重查 DDCAT
// 返回 Promise，供 refreshAll 的 Promise.all 统一 finally 收口 loading
function queryCircleData(self) {
  const queryParams = window.buildQueryParams(self); // 见第 6 节
  queryParams.push({ name: 'cicleType', valueContent: window.circleTypeValue || 'day' });
  queryParams.push({ name: 'pageSize', valueContent: 1000 }); // 趋势不分页，取足量
  return initTrendChart(queryParams);
}

// 联单趋势渲染（柱线混合）
// ECharts 走 getElementById + echarts.init 直接 DOM 操作是官方文档做法，规范升级保留不改
function initTrendChart(queryParams) {
  const chartDom = document.getElementById('container_trend_csshandler_generate');
  if (!chartDom) return Promise.resolve();
  const myChart = echarts.init(chartDom);

  // 数据源调用统一走 execDdcat 适配函数（定义见 §6.1）
  return execDdcat('DS_TREND', queryParams).then(function (res) {
    let xData = [], countData = [], abcountData = [];
    if (res && !res.hasError && res.result && res.result.length) {
      xData = res.result.map(function (i) { return i.statDate || i.stat_date; });
      countData = res.result.map(function (i) { return i.electronicWaybillCount || i.record_count || 0; });
      abcountData = res.result.map(function (i) { return i.abnormalWaybillCount || i.abnormal_count || 0; });
    }
    const isEmpty = xData.length === 0;
    const gradient1 = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: '#85C0FF' },
      { offset: 1, color: '#3388FF' }
    ]);

    const option = {
      legend: isEmpty ? undefined : {
        data: ['电子联单', '异常联单'],
        top: '5%', left: 'center',
        textStyle: { fontSize: 12 }, itemWidth: 12, itemHeight: 8
      },
      tooltip: isEmpty ? {} : {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(8, 17, 38, 0.8)',
        formatter: function (params) {
          let content = '<div style="padding:5px;font-size:12px;color:#fff">' + params[0].axisValue + '</div>';
          params.forEach(function (item) {
            const color = item.seriesName === '电子联单' ? '#3388FF' : '#FF6600';
            content += '<div style="color:#FFFFFF;"><span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:' + color + ';"></span><strong>' + item.seriesName + ':</strong> ' + item.value + ' 单</div>';
          });
          return content;
        }
      },
      xAxis: isEmpty ? {} : {
        type: 'category', data: xData,
        axisLabel: { fontSize: 12, interval: Math.max(Math.floor(xData.length / 10), 1), rotate: 35 }
      },
      yAxis: isEmpty ? [] : [{
        type: 'value', name: '单位：单', min: 0, max: 'dataMax',
        axisLabel: { formatter: '{value}', fontSize: 12 },
        splitLine: { show: true, lineStyle: { color: '#eee' } }
      }],
      series: isEmpty ? [] : [
        {
          name: '电子联单', type: 'bar',
          barWidth: Math.max(10, 80 / xData.length) + 'px', barGap: '10%',
          data: countData,
          itemStyle: { color: gradient1, barBorderRadius: [5, 5, 0, 0] }
        },
        {
          name: '异常联单', type: 'line', smooth: true,
          lineStyle: { width: 2, color: '#FF6600' },
          data: abcountData, symbol: 'circle', symbolSize: 6,
          itemStyle: { color: '#FF6600' }
        }
      ],
      grid: { left: '10%', right: '10%', bottom: '10%', containLabel: true },
      graphic: isEmpty ? {
        type: 'text', left: 'center', top: 'middle',
        style: { text: '暂无数据', fill: '#999', fontSize: 14 }
      } : undefined
    };

    myChart.setOption(option, true); // 第二参 true=全量替换，防止粒度切换后旧序列残留
  }).catch(function (err) {
    console.error('趋势查询失败:', err);
    // 异常兜底：清空旧序列并居中显示「暂无数据」，不留残图（loading 关闭统一在 refreshAll 的 finally）
    myChart.setOption({
      xAxis: {}, yAxis: [], series: [],
      graphic: { type: 'text', left: 'center', top: 'middle', style: { text: '暂无数据', fill: '#999', fontSize: 14 } }
    }, true);
  });
}
```

**逐段解释（每一块都对着评分点）**：

*查询段（queryCircleData）*
- `window.buildQueryParams(self)`：复用 §6 的统一参数构造，保证趋势图与概览/列表吃的是同一套筛选条件——这就是「顶部查询条件控制图表数据」8 分的实现点。
- `push cicleType`：把粒度下拉当前值（挂在 `window.circleTypeValue`）追加进参数；DDCAT 里按 day/week/month 分组统计。
- `push pageSize:1000`：趋势不分页，一次取足量，防止 DDCAT 默认分页只回 10 条导致图只有 10 根柱子。

*渲染段（initTrendChart）*
- `getElementById('..._csshandler_generate')`：拿容器 DOM，把 `container_trend` 换成真实唯一标识，后缀照抄；拿不到直接 return（页面没渲染完时的保护）。
- `echarts.init(chartDom)`：初始化实例——`echarts` 全局变量来自 §0.3 的隐藏环形图。
- `execDdcat('DS_TREND', queryParams)`：走 §6.1 适配函数，带着查询条件 + `cicleType` + `pageSize` 重查 DDCAT；适配函数内部 `DATA_SOURCE_EXECUTE` 的第四参空数组是表单参数、第五参空串是 JSON 参数，本题用不到但**位置不能省**。
- 三个 `.map`：接口字段做了驼峰/下划线双兜底（`statDate/stat_date`、`electronicWaybillCount/record_count`、`abnormalWaybillCount/abnormal_count`）；**先在 F12 里 `console.log(res)` 确认考试环境真实字段名再定稿**。

*option 各配置块 → 评分点映射*

| option 块 | 干什么 | 对应评分点 |
|---|---|---|
| `legend.data: ['电子联单','异常联单']` | 顶部居中图例，两个系列名 | 「顶部图例数据完整」 |
| `tooltip`（trigger:'axis' + formatter） | hover 出黑底浮层：第一行日期，下面两行系列名+值+「单」 | 「鼠标悬停展示数据」 |
| `xAxis`（category + xData） | x 轴放统计日期；`interval` 自适应抽稀 + `rotate:35` 防重叠 | 「x 轴展示正确」 |
| `yAxis`（value + name:'单位：单'） | y 轴数值轴，轴名「单位：单」 | 「y 轴展示正确」 |
| `series[0]`（type:'bar' + 渐变） | 电子联单柱状图，蓝色渐变、圆角柱头、宽度随数据量自适应 | 「电子联单柱状条」 |
| `series[1]`（type:'line' + smooth） | 异常联单平滑折线，橙色 #FF6600、圆点标记 | 「异常联单折线数据」 |
| `isEmpty` 三元 + `graphic '暂无数据'` | 空数据时不画轴/系列，居中显示「暂无数据」 | 空数据不出残图/NaN |
| `setOption(option, true)` | 第二参 true=全量替换 | 防粒度切换后旧 series 叠影 |

**✅ 本步验证**：预览 → 首屏趋势图出柱+线+图例；hover 出黑底 tooltip（日期+两组值+「单」）；切「周」「月」图表 x 轴粒度变化且无叠影；F12 无 `echarts is not defined`、无 `Cannot read ... of null`。

**⚠️ 注意事项**
- **参数名就叫 `cicleType`**：考题原文如此（不是 circleType），DDCAT 入参照抄，手滑写成正确英语反而 0 分。
- 容器高度为 0 / DOM id 后缀写错 / 忘拖隐藏环形图——三大「图出不来」病因，按 4.1 顺序排查。
- 想加分：`echarts.init` 后补一行 `window.addEventListener('resize', function(){ myChart.resize(); });` 解决窗口缩放不自适应（丢体验不丢功能分，时间紧可跳过）。

---

## §5 联单列表配置（8 分）

### 5.1 新建表格列表部件

1. 「部件设计」→【新建】→ 类型选 **列表部件** → 子类型选 **表格列表** → 名称「电子联单列表」→【确定】。
2. 进入列表设计界面 → 数据集选择处选视图 **「电子联单列表」**（选择入口以现场界面为准）。

### 5.2 列配置

在列表设计的**列配置**区，把展示列按下表配好（多余列删掉，缺的列从字段列表勾上/拖上）：

| 列 | 绑定字段 | 备注 |
|---|---|---|
| 序号 | 内置序号列 | 列表属性里开启「序号」（以现场界面为准） |
| 联单编号 | `record_num` | |
| 工地名称 | 工地名称字段 | 视图里的名称类字段（原题字段表此处笔误也写了 record_num，以视图实际字段为准） |
| 运输企业 | `unit_name` | |
| 车牌号 | `vehicle_num` | |
| 处置场所名称 | `consumptive_name` | |
| 创建时间 | `create_time` | 列的格式化设置里配 `yyyy-MM-dd HH:mm:ss`（以现场界面为准） |

每列的「标题」改成中文显示名（列配置里点【批量修改】可一次改完标题，以现场界面为准）。

### 5.3 分页

1. 选中表格列表 → 右侧 **「属性」** 栏 → 找到 **「分页」** 开关 → 开启 → 「每页条数」填 10。
2. 分页器默认样式即含总条数/页码/跳页，不用额外配。
3. **同时**到「数据管理-数据模型」打开 `DS_LIST` 对应的数据模型 → 开启 **「是否分页」** 开关（此时 pageIndex/pageSize 生效）。
4. **数据模型「是否分页」与列表「分页」两个开关必须同开（或同关）**，否则分页/导出错乱。

### 5.4 Hook 查询（把顶部查询参数带进列表）

1. 列表设计界面找到 **「Hook 配置」** → 开关拨到 **【开】** → 点 **【设置方法】** → 弹出脚本编辑窗口，贴：

```js
function main(pageId, param) {
    const self = this;
    // 【Hook 纪律】只允许合并 queryParams / condition.params 追加查询条件；
    // 绝不动 param.paging（pageIndex/pageSize 等分页字段），分页由平台统一管理，
    // 这样导出数据与页面查询走同一条件、结果天然一致。
    return new Promise(function (resolve, reject) {
        console.log(pageId, param);
        // 把工作台顶部查询条件合并进查询参数（导出数据走同一 hook，条件自动一致）
        const extra = window.workbenchParams || [];
        param.queryParams = (param.queryParams || []).concat(extra);
        // 用数据模型代替默认查询逻辑，DS_LIST 为「电子联单列表」数据模型 ID
        api.DATA_EXECUTOR().executeDataModelForList("DS_LIST", param)
            .then(function (res) { resolve(res); })
            .catch(function (err) { reject(err); });
    });
}
```

2. `DS_LIST` 用 Ctrl+Shift+C 回填真实数据模型 ID →【验证】→【确定】→ 保存部件。

说明：
- 数据模型（DDCAT/视图）里对应 SQL 变量：`siteIds / vehicleNum / muckType / startDate / endDate`（考试已内置，打开数据模型确认参数名即可）。
- `window.workbenchParams` 由 §6.1 的 `refreshAll` 写入——查询/导出走同一个 hook，导出条件自动与页面筛选一致。

### 5.5 顶部操作按钮

**导出数据（内置按钮）**：

1. 列表设计界面找到 **「顶部操作」** 配置区 → 按钮列表里勾选/添加内置 **【导出数据】** 按钮（以现场界面为准）。
2. 不用写任何脚本——导出走 5.4 的同一查询链路，天然带当前筛选条件。

**「更多 >」（自定义按钮）**：

1. 「顶部操作」→ 点【添加按钮】→ 按钮名称填 `更多 >` → 交互动作选 **「自定义动作」** → 编辑脚本，贴：

```js
function main() {
  const self = this;
  let element = self, rootPageElement = null;
  while (element) {
    if (element.getPageInfo && element.goHistory) { rootPageElement = element; break; }
    element = element.$parent;
  }
  const p = window.currentFilter || {};
  rootPageElement.getPageInfo('PAGE_LIST', 'PAGE', {
    isPageHeader: true,
    pageHeaderTitle: '联单列表',
    extraParams_: {
      siteIds: p.siteIds || '',
      vehicleNum: p.vehicleNum || '',
      muckType: p.muckType || '',
      startDate: p.startDate || '',
      endDate: p.endDate || ''
    }
  });
}
```

2. `PAGE_LIST` 用 Ctrl+Shift+C 选 **页面** 类型回填目标页面 ID（先做完下面 5.7 再回来填）。
3. 脚本逻辑：沿 `$parent` 向上找页面路由根元素 → `getPageInfo` 跳内部页面并带当前筛选（`window.currentFilter` 由 §6.1 维护）。

### 5.6 把列表挂到页面第 3 行

1. 打开工作台页面 → 左侧组件库拖 **「列表部件渲染组件」** 到第 3 行容器 → 属性面板选择部件「电子联单列表」。
2. 选中该渲染组件 → 高级 → 抄「唯一标识」，登记为 `table_list`（§6.1 刷新列表要用）。

### 5.7 目标「联单列表页」（“更多>”的落点）

1. 「页面设计」→【新建页面】→ 名称「联单列表」→ 进入画布 → 拖入列表部件渲染组件 → 选同一个「电子联单列表」部件 → 保存。
2. Ctrl+Shift+C（类型选**页面**）抄该页面 ID → 回填 5.5 脚本的 `PAGE_LIST`。
3. **加分项（时间富余再做）**——让跳转带过来的筛选条件在列表页生效，两种做法：
   - **做法 A（渲染组件参数设置）**：选中列表页里的列表部件渲染组件 → 属性面板「参数设置」→ 逐个添加参数 `siteIds/vehicleNum/muckType/startDate/endDate`，值来源选页面参数/extraParams（以现场界面为准），映射到列表查询条件。
   - **做法 B（页面 didMounted 读参转写 hook 变量）**：列表页的页面 JS didMounted 里读跳转参数，写回 `window.workbenchParams`，列表 hook（§5.4 同一个）自动合并：

```js
// 联单列表页 didMounted：接收“更多>”带来的筛选参数（加分项，可选）
function main() {
  const self = this;
  const p = (self.extraParams_ || (self.$route && self.$route.query)) || {}; // 参数取法以现场实际为准，F12 打印确认
  const qp = [];
  ['siteIds', 'vehicleNum', 'muckType', 'startDate', 'endDate'].forEach(function (k) {
    if (p[k]) qp.push({ name: k, valueContent: p[k] });
  });
  window.workbenchParams = qp; // 列表 hook 会 concat 它
}
```

   **列表页只要能打开 + 展示列表即可拿分，参数带入是加分保障**——联调时间不够就只做第 1、2 步。

**✅ 本步验证**：预览工作台 → 列表 7 列齐全、创建时间格式 `yyyy-MM-dd HH:mm:ss`、底部分页器显示总条数且可跳页；顶部见【导出数据】和【更多 >】两个按钮；点导出得到 Excel；点更多跳到联单列表页。

**⚠️ 注意事项**
- 作为列表查询面板条件的视图字段**不能起别名**，否则条件匹配不上。
- hook 脚本官方提示不建议改 `param`（影响导出与查询一致性）；本手册的合并方式恰恰利用同一 hook 保证导出=查询条件，但**绝不要**在 hook 里改 `pageIndex/pageSize`。
- 5.3 第 4 条的双分页开关同步，忘一个就是翻页/导出数据错乱。

---

## §6 查询/重置全页联动 JS 完整模板（核心，先贴这个）

### 6.1 全局骨架贴进页面 didMounted

**入口位置**：打开工作台页面 → 页面级配置（画布空白处点选页面本身，或页面右上角设置按钮）→ 切到 **「高级」** → 找到 **「页面 JS / 绑定动作」** → 添加 **didMounted（页面加载完成）** 事件动作（事件名可能显示为 didMount/页面加载完成，以现场界面为准）→ 打开脚本编辑器（点【全屏】好写）→ 贴入：

```js
function main() {
  const self = this;

  // ---------- 工具：读取查询区当前值 ----------
  window.getFilter = function () {
    const siteIds = self.$$('site_select').$$getValue();        // 多选 -> 数组
    const vehicleNum = self.$$('vehicle_select').$$getValue();
    const muckType = self.$$('muck_select').$$getValue();
    const range = self.$$('date_range').$$getValue() || [];
    // moment(range[0]) 是基于取出值新建的副本，直接 format 安全；
    // 若改用组件自身的 moment 对象（如 currentTime），必须先 .clone() 再 format，避免污染组件内部状态
    return {
      siteIds: Array.isArray(siteIds) ? siteIds.join(',') : (siteIds || ''),
      vehicleNum: vehicleNum || '',
      muckType: muckType || '',
      startDate: range[0] ? moment(range[0]).format('YYYY-MM-DD') : '',
      endDate: range[1] ? moment(range[1]).format('YYYY-MM-DD') : ''
    };
  };

  // ---------- 工具：过滤空值，拼 queryParams ----------
  window.buildQueryParams = function () {
    const p = window.getFilter();
    window.currentFilter = p;                    // 给“更多>”跳转用
    const qp = [];
    ['siteIds', 'vehicleNum', 'muckType', 'startDate', 'endDate'].forEach(function (k) {
      if (p[k] !== '' && p[k] != null) qp.push({ name: k, valueContent: p[k] }); // 空条件不生效
    });
    return qp;
  };

  // ---------- 全页刷新 ----------
  window.refreshAll = function () {
    const qp = window.buildQueryParams();
    window.workbenchParams = qp;                 // 列表 hook 读它
    // loading 句柄双保险：这里开，Promise.all 的 finally 里关（成功/失败都收口）
    const hideLoading = (self.$message && self.$message.loading) ? self.$message.loading('数据加载中...', 0) : null;
    const tasks = [
      refreshOverview(self, qp),                 // 1) 概览（第 3 节函数，返回 Promise）
      window.queryCircleData(self)               // 2) 趋势（第 4 节函数，返回 Promise）
    ];
    const tableComp = self.$$element('table_list'); // 3) 列表：重查并回到第一页
    if (tableComp && tableComp.onRefresh) { tableComp.onRefresh(); }
    else if (tableComp && tableComp.$$refreshData) { tableComp.$$refreshData(); }
    return Promise.all(tasks)
      .catch(function (err) { console.error('全页刷新异常:', err); }) // 各函数内部已兜底，这里兜网络级异常
      .finally(function () { if (typeof hideLoading === 'function') hideLoading(); });
  };

  window.queryCircleData = function () { return queryCircleData(self); }; // 供粒度下拉 onChange 调

  // ---------- 初始化：默认近 30 天 + 首屏加载 ----------
  setTimeout(function () {
    setDefaultDateRange(self);       // 第 2.4 节函数
    window.circleTypeValue = 'day';
    window.refreshAll();
  }, 300);                           // 等组件渲染完成再取/赋值
}

// —— ddcat 数据源统一适配函数：所有 api.DATA_SOURCE_EXECUTE 调用只出现在这一处。
//    若环境提示 DATA_SOURCE_EXECUTE 已废弃，只需改这一个函数换成 api.DATA_EXECUTOR() 对应方法，
//    refreshOverview / initTrendChart 等调用处一行不用动 ——
function execDdcat(modelId, queryParams) {
  return api.DATA_SOURCE_EXECUTE(modelId, 'ddcat', queryParams, [], '');
}

// —— 把第 2.4 的 setDefaultDateRange、第 3.4 节 refreshOverview、
//     第 4.3 的 queryCircleData / initTrendChart 四个函数原样贴在 execDdcat 下方 ——
```

**最终页面脚本的完整组装结构（自查用）**——粘贴完成后编辑器里应从上到下依次是这 6 段，缺一段联动链就断：

```text
function main() { ... }                 // 6.1 骨架：getFilter/buildQueryParams/refreshAll(loading双保险)/初始化
function execDdcat(modelId, qp) {...}   // 6.1：ddcat 数据源适配（API 废弃时只改这一处）
function setDefaultDateRange(self) {..} // 2.4：日期默认近30天
function refreshOverview(self, qp) {..} // 3.4：概览4指标（返回 Promise）
function queryCircleData(self) {...}    // 4.3：趋势查询（拼 cicleType，返回 Promise）
function initTrendChart(qp) {...}       // 4.3：趋势渲染（echarts option）
```

贴完点【验证】确认无语法错误，再点【确定】把全屏编辑内容带回，最后**保存页面**（全屏编辑器点确定不等于页面已保存）。

**贴完后的替换清单（对着 §0.2 登记表逐项换）**：
1. `site_select` / `vehicle_select` / `muck_select` / `date_range` → 查询表单 4 个组件真实唯一标识；
2. `table_list` → 列表渲染组件真实唯一标识；
3. 随后贴的 4 个函数里：`DS_OVERVIEW`、`DS_TREND`、`container_trend_csshandler_generate`、4 个 `text_*` → 全部换真实值。

**联动机理一句话**：查询/重置/首屏都汇到 `window.refreshAll` → 统一 `buildQueryParams`（空值不 push=「空条件不生效」）→ 分发给概览（直接查）、趋势（追加 cicleType 再查）、列表（写 `window.workbenchParams` 后触发 onRefresh，hook 里合并）。

### 6.2 查询按钮脚本（回填 §2.5 的占位）

选中查询按钮 → 高级 → 绑定动作 → 打开之前建的自定义动作 → 替换为：

```js
function main() {
  const self = this;
  window.refreshAll(self);
}
```

### 6.3 重置按钮脚本

```js
function main() {
  const self = this;
  self.$$('site_select').$$setValue([]);      // 多选清空传空数组
  self.$$('vehicle_select').$$setValue('');
  self.$$('muck_select').$$setValue('');
  // 运输时间恢复默认近 30 天（moment() 为新建实例，直接 format 安全）
  const end = moment().format('YYYY-MM-DD');
  const start = moment().subtract(29, 'days').format('YYYY-MM-DD');
  self.$$('date_range').$$setValue([start, end]);
  window.circleTypeValue = 'day';
  setTimeout(function () { window.refreshAll(self); }, 100); // 等赋值生效再查
}
```

> 注意重置按钮在查询表单部件内，`this.$$()` 是从表单部件根向下查找；若组件找不到，改用 `this.$$element('组件id')` 向上查找，或把脚本挂到页面级按钮上。调试时先 `console.log(window.getFilter())` 确认取值。

**✅ 本步验证**：预览 → 点查询：F12 里 `console.log` 的 queryParams 只含非空项，概览/趋势/列表三块同时刷新；点重置：三个下拉清空、日期回近 30 天、全量数据恢复、列表回第 1 页。

**⚠️ 注意事项**
- didMounted 里立即取组件值可能组件还没渲染完 → 骨架里的 `setTimeout(…, 300)` 不能删。
- `siteIds` 多选必须 `join(',')` 传逗号串（DDCAT 内一般用 `FIND_IN_SET`/`IN` 解析），传数组对象直接查空。
- 日期统一 `moment(v).format('YYYY-MM-DD')`——日期组件取出的可能是时间戳/Date 对象，直接拼 SQL 必炸。
- `this.$$()` 从根向下找、`this.$$element()` 从当前向上找；隐藏组件只能 `this.$$model()` 取属性。

---

## §7 联调验证（考前最后 25 分钟照做）

按顺序逐条打钩，任何一条不过按括号内章节回查：

1. F12 打开控制台 → 刷新预览页：确认无 `echarts is not defined`（§0.3）、无 `chartDom null`（§4.1）。
2. **首屏**：4 指标有值或 0/0.00（§3）、趋势图出柱+线（§4）、列表有数据（§5）、日期默认近 30 天（§2.4）。
3. 选一个项目 → 点查询：控制台确认 queryParams 只含非空项；**四个模块同时变化**（§6.1）。
4. 点重置：下拉清空、日期回近 30 天、全部数据恢复全量、列表回第 1 页（§6.3）。
5. 切天/周/月：**仅趋势图**重查，x 轴粒度变化、无旧序列叠影（§4.2 / setOption true）。
6. 故意选一个查不到数据的条件组合：指标显示 0/0.00、图表「暂无数据」、列表空——全程无 undefined/NaN（§3.4 / §4.3 isEmpty）。
7. 点导出数据：Excel 行数 = 当前筛选后的总条数（§5.3 双分页开关 + §5.4 hook）。
8. 点「更多 >」：跳到联单列表页且能展示列表；筛选带入则加分（§5.5/5.7）。
9. 补充自查：hover 趋势图任一柱子出 tooltip（日期+电子联单+异常联单+「单」）；y 轴左上角有「单位：单」。

调试手段速查（来自官方调试文档）：
- 脚本里插 `debugger` → F12 开着触发动作，自动断在该行；控制台输 `this` 看当前元素、`arguments` 看参数。
- `console.log('标记', 变量)` → Console 页签点右侧 `page.js:14` 类的行号直接跳源码。
- 断点后 F8 继续 / F10 逐行 / F11 进函数 / Shift+F11 跳出；Watch 面板监听 `window.workbenchParams`。
- 控制台随时可手工验证联动链：输 `window.getFilter()` 看取值、`window.buildQueryParams()` 看参数、`window.refreshAll()` 手动触发全页刷新。

**故障速查表（症状 → 最可能原因 → 回查章节）**：

| 症状 | 最可能原因 | 回查 |
|---|---|---|
| 控制台 `echarts is not defined` | 没拖隐藏环形图 / 容器没开强制渲染 | §0.3 |
| 图表区域一片空白、无报错 | 容器高度为 0，或 DOM id 后缀 `_csshandler_generate` 写错 | §4.1 |
| 趋势图有图但查询后不变 | queryCircleData 没走 buildQueryParams / DS_TREND ID 错 | §4.3 / §6.1 |
| 切粒度后柱子叠影 | `setOption` 第二参没传 true | §4.3 |
| 切粒度无反应 | onChange 里组件 ID 错，或 `window.queryCircleData` 还没被 didMounted 挂上（先刷新页面） | §4.2 / §6.1 |
| 概览 4 卡不刷新 | 复制卡片后没重抄 `text_*` 唯一标识 | §3.3 |
| 概览出现 NaN/undefined | 自己简化了 fmtInt/fmtTon 兜底 | §3.4 |
| 下拉有选项但查询查空 | 值字段绑成了展示名（该绑 site_id/vehicle_num/muck_type） | §2.3 |
| 选了多个项目查空 | siteIds 传了数组没 join(',') | §6.1 |
| 列表不受筛选控制 | hook 没开 / hook 里 DS_LIST ID 错 / refreshAll 没写 window.workbenchParams | §5.4 / §6.1 |
| 翻页数据错乱、导出条数不对 | 数据模型「是否分页」与列表「分页」开关没同步 | §5.3 |
| 重置后数据没恢复全量 | 重置脚本里 setTimeout 被删，赋值还没生效就查了 | §6.3 |
| didMounted 里取值报 undefined | 组件未渲染完，`setTimeout(...,300)` 被删 | §6.1 |
| 脚本保存时语法报错 | 中文标点混入（逗号/引号/分号） | §0.4 |
| 点「更多>」无反应 | PAGE_LIST 没换成真实页面 ID | §5.5 / §5.7 |

---

## §8 评分点对照 Checklist（40 分）

| 子项 | 分 | 逐项自检 | 对应章节 |
|---|---|---|---|
| 查询-内容 | 4 | □ 项目名称**下拉多选** □ 车牌号下拉 □ 垃圾类型下拉单选 □ 运输时间**日期范围** □ 重置按钮 □ 查询按钮 | §2 |
| 查询-交互 | 4 | □ 重置后字段清空+日期回默认+全量数据 □ 查询驱动**所有**模块 | §6.2/6.3 |
| 概览-内容 | 4 | □ 联单总数 □ 异常运单数 □ 垃圾清运量(2位小数) □ 垃圾处置量(2位小数) □ 单位“单/吨” | §3 |
| 概览-交互 | 4 | □ 查询条件控制 4 指标 □ 空数据显示 0/0.00 | §3/§6 |
| 趋势-内容 | 6 | □ 图例“电子联单/异常联单” □ hover 显示日期+值 □ x轴日期 □ y轴“单位：单” □ 柱状=电子联单 □ 折线=异常联单 | §4.3 |
| 趋势-查询联动 | 8 | □ 查询/重置后图表按条件刷新（**本题单项最大分，优先保**） | §6.1 |
| 趋势-粒度切换 | 2 | □ 天/周/月切换后按 cicleType 重查刷新 | §4.2 |
| 列表-内容 | 4 | □ 序号/联单编号/工地名称/运输企业/车牌号/处置场所/创建时间 □ 分页(总数+跳页) □ 导出数据 □ 更多>跳列表页 | §5 |
| 列表-交互 | 4 | □ 查询条件控制列表 □ 查询/重置后回第 1 页 | §5.4/§6 |

**抢分策略**：先把 §6 联动骨架 + §4 趋势图跑通（8+6+2=16 分集中在趋势），再补概览兜底和“更多>”。

---

## §9 常见坑总表（血泪对照，已在各步骤就近内嵌，考前再扫一遍）

1. **`echarts is not defined`**：忘了拖隐藏的环形图组件。容器隐藏必须 **开启强制渲染**，否则 `getElementById` 拿到 null。（→ §0.3）
2. **DOM id 后缀**：是 `组件唯一标识 + _csshandler_generate`，漏后缀图表永远画不出来。（→ §4.1）
3. **参数名就叫 `cicleType`**：考题原文如此（不是 circleType），DDCAT 入参照抄，手滑写对英语反而 0 分。（→ §4.3）
4. **hook 里改 param 的副作用**：官方提示 hook 中不建议改 param（影响导出与查询一致性）。本手册的合并方式恰恰是利用同一 hook 保证导出=查询条件；**不要**在 hook 里改 `pageIndex/pageSize`。（→ §5.4）
5. **数据模型分页开关与列表分页开关必须同步**（全开或全关），否则导出/翻页数据错乱。（→ §5.3）
6. **视图字段别名**：作为列表查询面板条件的字段**不能起别名**，否则条件匹配不上。（→ §5.2）
7. **多选传参**：`siteIds` 用 `join(',')` 传逗号串，DDCAT 内一般用 `FIND_IN_SET`/`IN` 解析——传数组对象会直接查空。（→ §6.1）
8. **日期取值格式**：统一 `moment(v).format('YYYY-MM-DD')`；日期组件取出的可能是时间戳/Date 对象，直接拼 SQL 必炸。（→ §6.1）
9. **didMounted 时序**：页面加载脚本里立即取组件值可能组件还没渲染完，包一层 `setTimeout(…, 300)`。（→ §6.1）
10. **`setOption(option, true)`**：第二参数不传 true，粒度切换/重查后旧 series 残留叠影。（→ §4.3）
11. **空数据兜底**：`row.cleanAmount.toFixed(2)` 在 undefined 上直接抛错 → 整个概览白屏。必须先 `Number()+isFinite()` 再 `toFixed`。（→ §3.4）
12. **找不到组件**：`this.$$()` 从页面根向下找、`this.$$element()` 从当前向上找；隐藏组件只能 `this.$$model()` 取属性。（→ §6.3）
13. **窗口缩放图表不自适应**（丢体验分不丢功能分）：可在 init 后加 `window.addEventListener('resize', function(){ myChart.resize(); })`。（→ §4.3）
14. 资源 ID 全部用 **Ctrl+Shift+C** 回填，手抄 UUID 极易错一位。（→ §0.2）
15. **复制卡片后组件 ID 是新的**：4 个数值文本必须逐个重新抄「唯一标识」，沿用第一张的 ID 是概览不刷新的头号原因。（→ §3.3）
16. **下拉 value 绑错字段**：值字段必须是 `site_id`/`vehicle_num`/`muck_type`，绑成展示名传参全查空。（→ §2.3）
17. **中文标点**：动作面板脚本里出现中文逗号/引号/分号直接语法报错，全程英文输入法。（→ §0.4）

---

## 脚本规范升级说明（2026-07-10）

本手册 JS 层已按 `references/scripting/`（components-api-reference.md 等 6 份）+ SKILL.md「② JS 脚本规范」核心约束升级。**只动了 JS 代码块与相关说明文字；SQL、操作步骤、评分表、坑总表全部保持原样**。变更明细：

| # | 变更 | 涉及位置 | 依据 |
|---|---|---|---|
| 1 | 所有脚本入口函数首行 `const self = this;`，后续统一用 self；全部 `var` 改 `const`/`let` | §2.4、§3.4、§4.2、§4.3、§5.4、§5.5、§5.7、§6.1、§6.2、§6.3（共 10 个 JS 块） | 核心约束 1：function 回调里 this 会变 |
| 2 | `api.DATA_SOURCE_EXECUTE` 调用收拢进适配函数 `execDdcat(modelId, queryParams)`（§6.1 新增，紧跟 main 之后）；`refreshOverview`/`initTrendChart` 只调适配函数。**环境提示该 API 废弃时，只改 execDdcat 一处换成 `api.DATA_EXECUTOR()` 对应方法** | §3.4、§4.3、§6.1（组装结构 5 段 → 6 段） | SKILL.md「API 版本差异」：新版标废弃、存量环境仍可用，以目标环境实测为准 |
| 3 | Promise 链统一 `.then().catch().finally()` 收口：`refreshOverview`/`queryCircleData`/`initTrendChart` 均返回 Promise；`refreshAll` 里开 `$message.loading` 句柄，`Promise.all(tasks).finally` 里关（双保险）；`initTrendChart` 新增 catch 兜底渲染「暂无数据」空态 | §3.4、§4.3、§6.1 | 核心约束 5：Promise 必须有 catch、耗时操作有 loading 管理 |
| 4 | 列表 Hook 加纪律注释：只合并 `queryParams`/`condition.params`，绝不动 `param.paging`（pageIndex/pageSize），保证导出与查询条件一致；`reject()` 改为 `reject(err)` 透传错误 | §5.4 | list-scripts-guide Hook 分页规范 + §9 坑 4 |
| 5 | 日期取值加注释说明：`moment(range[0])` / `moment()` 均为新建副本可直接 format；**若改用组件自身 moment 对象（如 currentTime）必须先 `.clone()`** | §2.4、§6.1、§6.3 | scripting 规范：moment 对象可变，共享实例须 clone |

**未变部分（有意保留，不是漏改）**：
- 概览空数据兜底 0/0.00（`fmtInt`/`fmtTon` + catch 兜底）逻辑原样保留——这是评分点保命符；
- 文本组件赋值 `$$setValue` 保留（规范认可的文本组件赋值方式）；本手册无图表/看板组件 `data.props` 直改写法，故无需改 `self.$$m(id).props...`；
- ECharts 走 `getElementById('..._csshandler_generate')` + `echarts.init` 的直接 DOM 操作保留（官方文档做法，规范升级不涉及）；
- §4.3 注意事项里的 `window.addEventListener('resize', ...)` 加分项提示保留原文（一次性图表 resize，非组件事件监听场景）；
- `cicleType` 参数名、`setOption(option, true)`、`setTimeout` 时序保护、双分页开关等全部业务逻辑与坑位提示未动。
