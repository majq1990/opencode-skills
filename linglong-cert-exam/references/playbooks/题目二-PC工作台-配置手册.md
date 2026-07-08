# 题目二（必考）：PC 工作台 — 建筑垃圾监管工作台 配置手册（40 分）

> 原题存档：`../exam/题目二-PC工作台-原题.md`（nodeId=Y1OQX0akWm3gYmA4ivD7MZrkJGlDd3mE）
> 面向对象：正在考试的工程师。所有 `xxx_替换我` 形式的 ID 都要换成你自己页面里的真实 ID（任意动作绑定窗口按 **Ctrl+Shift+C** 可弹出资源选择器回填数据模型/API/页面 ID；组件 ID 在组件属性面板「唯一标识」处查看）。

---

## 0. 开工前 5 分钟：ID 清单（先抄下来再动手）

| 占位符 | 含义 | 获取方式 |
|---|---|---|
| `DS_OVERVIEW` | 「联单概览统计」视图对应数据模型 ID | Ctrl+Shift+C 选数据模型 |
| `DS_TREND` | 「联单趋势」DDCAT 数据模型 ID | 同上 |
| `DS_LIST` | 「电子联单列表」视图/数据模型 ID | 同上 |
| `PAGE_LIST` | 联单列表页（“更多>”跳转目标页面）ID | Ctrl+Shift+C 选页面 |
| `site_select` / `vehicle_select` / `muck_select` / `date_range` | 查询区 4 个筛选组件 ID | 组件属性-唯一标识 |
| `single_select_cicle` | 天/周/月 粒度下拉组件 ID | 同上 |
| `container_trend` | 趋势图容器组件 ID | 同上 |
| `text_total` / `text_abnormal` / `text_clean` / `text_disposal` | 4 个指标数值文本组件 ID | 同上 |
| `table_list` | 联单列表部件在页面里的渲染组件 ID | 同上 |

**任务拆解（按操作顺序，总预算约 2.5h）**：
1. 页面骨架布局（15min）→ 2. 查询区表单部件（30min）→ 3. 数据概览 4 卡片（30min）→ 4. ECharts 趋势图（40min）→ 5. 联单列表 + 导出 + 更多（30min）→ 6. 查询/重置全页联动调试（25min）。
**先把联动 JS 骨架贴进页面（第 7 节），再逐模块填 ID**，避免最后重构。

---

## 1. 页面骨架布局

1. 新建页面「建筑垃圾监管工作台」。
2. 拖入一个 **容器** 作为页面根 → 容器内拖入 **网格布局（简）**，按行划 3 个区块：
   - **第 1 行（约 10% 高）**：查询区（放查询表单部件）。
   - **第 2 行（约 40% 高）**：再嵌套一层网格布局（简）分左右两列 —— **左列（约 35% 宽）** 放 4 张指标卡；**右列（约 65% 宽）** 放趋势图容器。
   - **第 3 行（约 50% 高）**：联单列表。
3. 左列内部：卡片可用「网格布局（简）」2×2，或容器开启 **弹性模式（flex）→ 纵向/横向排列、主轴对称排布**，每张卡一个子容器。
4. 每个区块尺寸对照考题截图微调即可，布局不计分，别抠像素。

**关键前置（趋势图必须）**：页面里必须存在一个 ECharts 类型组件，系统才会加载 ECharts 库。随便拖一个 **环形图** 到页面 → 外面套一个容器 → 容器默认状态设为 **隐藏** 且 **开启强制渲染模式**（该图表组件本身没有隐藏属性，必须借容器隐藏）。现在就拖，别等写脚本时报 `echarts is not defined`。

---

## 2. 查询区配置（8 分）

### 2.1 组件摆放

在第 1 行区块拖入一个 **表单部件渲染组件**（新建一个查询表单部件），横向依次放：

| 组件 | 类型 | 关键属性 |
|---|---|---|
| 项目名称 | **下拉多选** | 占位“请选择项目名称”；允许清空 |
| 车牌号 | 下拉单选（开启可搜索） | 占位“请选择车牌号”；允许清空 |
| 垃圾类型 | 下拉单选 | 占位“垃圾类型”；允许清空 |
| 运输时间 | **日期范围选择** | 见 2.3 默认近 30 天 |
| 重置 | 按钮 | 绑定自定义动作（脚本见 7.3） |
| 查询 | 按钮 | 绑定自定义动作（脚本见 7.2） |

### 2.2 下拉绑定视图数据源

三个下拉的「数据源」选择 **数据集/视图**，分别绑定考试内置视图：**项目下拉**（label=项目名称，value=`site_id`）、**车辆选择下拉**（label/value=`vehicle_num`）、**垃圾类型下拉**（label=类型名，value=`muck_type`）。在下拉组件属性里把「显示字段/值字段」映射对即可，**value 必须是入参要用的字段值**，不要绑成 id 以外的展示字段。

### 2.3 运输时间默认近 30 天

日期范围组件若支持“动态默认值”，直接配 `近30天`。不支持就在页面 didMounted（第 7.1 节脚本里已包含）用 JS 赋值：

```js
function setDefaultDateRange(self) {
  var end = moment().format('YYYY-MM-DD');
  var start = moment().subtract(29, 'days').format('YYYY-MM-DD');
  self.$$('date_range').$$setValue([start, end]);
  return [start, end];
}
```

### 2.4 交互要求落点

- 「查询」→ 调 `window.refreshAll(this)`（7.2）。
- 「重置」→ 清空三个下拉 + 日期恢复近 30 天 + 再 `refreshAll`（7.3）。
- 空条件不生效：由 7.1 的 `buildQueryParams` 统一处理 —— 值为空就不 push 该参数。

---

## 3. 数据概览配置（8 分）

**推荐方案：容器卡片 + 文本组件 + JS 赋值**（空数据兜底完全可控，评分“详情组件展示 4 指标”同样认可此展示形态；若时间富余也可用详情部件绑「联单概览统计」视图再 `$$setExtraParams` 传参，但兜底 0/0.00 不好控，考试用 JS 版）。

1. 左列 4 张卡：每张 = 一个子容器（设宽高 + 背景图/背景色）→ 内放 **图片组件**（考题给的 4 张图标素材）+ **文本组件×2**（指标名、数值）。做好第一张后 **复制容器** 改样式即可。
2. 数值文本组件 ID 记为 `text_total / text_abnormal / text_clean / text_disposal`。
3. 刷新函数（已并入第 7 节全局脚本）：

```js
// 数据概览刷新：入参 queryParams 为 [{name,valueContent}] 数组
function refreshOverview(self, queryParams) {
  api.DATA_SOURCE_EXECUTE("DS_OVERVIEW", "ddcat", queryParams, [], "").then(function (res) {
    var row = (res && !res.hasError && res.result && res.result.length) ? res.result[0] : {};
    // 空数据兜底：整数显示 0，吨位显示 0.00，绝不出现 undefined/null/NaN
    var fmtInt = function (v) { var n = Number(v); return isFinite(n) ? String(Math.round(n)) : '0'; };
    var fmtTon = function (v) { var n = Number(v); return isFinite(n) ? n.toFixed(2) : '0.00'; };
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

> 注：`Number(null)=0`、`Number(undefined)=NaN`、`Number('')=0`，`isFinite` 一网打尽；`fmtTon` 对 `null/''` 输出 `0.00`。

---

## 4. ECharts 趋势图完整配置（16 分，本题最大分块）

### 4.1 前置

- 隐藏的环形图组件已就位（第 1 节）。
- 右列拖一个 **容器**，记下唯一标识 `container_trend`，渲染后 DOM id 为 **`container_trend_csshandler_generate`**（后缀固定，别写错）。给容器设固定高度（如 320px），高度为 0 图出不来。

### 4.2 天/周/月粒度切换（2 分）

在趋势图容器右上角放一个小 **表单部件**（或直接放下拉组件），下拉单选 `single_select_cicle`，选项值与 DDCAT 入参对应：`day / week / month`，默认 `day`。绑定 **值改变事件**：

```js
export function onChange() {
  var typeValue = this.$$('single_select_cicle').$$getValue();
  window.circleTypeValue = typeValue; // 挂 window 供全局使用
  if (window.queryCircleData) {
    window.queryCircleData(this);     // 粒度变化只重查趋势图
  }
}
```

### 4.3 趋势图查询 + 渲染（完整可复制）

```js
// 联单趋势查询：cicleType 追加进 queryParams 后重查 DDCAT
function queryCircleData(self) {
  var queryParams = window.buildQueryParams(self); // 见第 7 节
  queryParams.push({ name: 'cicleType', valueContent: window.circleTypeValue || 'day' });
  queryParams.push({ name: 'pageSize', valueContent: 1000 }); // 趋势不分页，取足量
  initTrendChart(queryParams);
}

// 联单趋势渲染（柱线混合）
function initTrendChart(queryParams) {
  var chartDom = document.getElementById('container_trend_csshandler_generate');
  if (!chartDom) return;
  var myChart = echarts.init(chartDom);

  api.DATA_SOURCE_EXECUTE("DS_TREND", 'ddcat', queryParams, [], "").then(function (res) {
    var xData = [], countData = [], abcountData = [];
    if (res && !res.hasError && res.result && res.result.length) {
      xData = res.result.map(function (i) { return i.statDate || i.stat_date; });
      countData = res.result.map(function (i) { return i.electronicWaybillCount || i.record_count || 0; });
      abcountData = res.result.map(function (i) { return i.abnormalWaybillCount || i.abnormal_count || 0; });
    }
    var isEmpty = xData.length === 0;
    var gradient1 = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: '#85C0FF' },
      { offset: 1, color: '#3388FF' }
    ]);

    var option = {
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
          var content = '<div style="padding:5px;font-size:12px;color:#fff">' + params[0].axisValue + '</div>';
          params.forEach(function (item) {
            var color = item.seriesName === '电子联单' ? '#3388FF' : '#FF6600';
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
  });
}
```

> 趋势输出字段以你考试环境 DDCAT 实际返回为准，上面 `statDate/electronicWaybillCount/abnormalWaybillCount` 与 `stat_date/record_count/abnormal_count` 做了双兜底；**先在浏览器 F12 里 console.log(res) 确认真实字段名再定稿**。

---

## 5. 联单列表配置（8 分）

### 5.1 列表部件

1. 部件设计 → 新建 **表格列表**，数据集选「电子联单列表」视图。
2. 列：序号（内置）、联单编号 `record_num`、工地名称、运输企业 `unit_name`、车牌号 `vehicle_num`、处置场所名称 `consumptive_name`、创建时间 `create_time`（格式 `yyyy-MM-dd HH:mm:ss`，在列格式化里配）。
3. 属性开启 **分页**，每页条数 10；分页器展示总条数/页码/跳页（默认样式即含）。
4. 页面第 3 行拖入 **列表部件渲染组件**，唯一标识记为 `table_list`。

### 5.2 Hook 查询（把顶部查询参数带进列表）

列表部件「Hook 配置」开 → 设置方法：

```js
function main(pageId, param) {
    return new Promise(function (resolve, reject) {
        console.log(pageId, param);
        // 把工作台顶部查询条件合并进查询参数（导出数据走同一 hook，条件自动一致）
        var extra = window.workbenchParams || [];
        param.queryParams = (param.queryParams || []).concat(extra);
        // 用数据模型代替默认查询逻辑，DS_LIST 为「电子联单列表」数据模型 ID
        api.DATA_EXECUTOR().executeDataModelForList("DS_LIST", param)
            .then(function (res) { resolve(res); })
            .catch(function () { reject(); });
    });
}
```

- 数据模型（DDCAT/视图）里对应 SQL 变量：`siteIds / vehicleNum / muckType / startDate / endDate`（考试已内置，确认参数名即可）。
- **数据模型「是否分页」开关与列表「分页」开关必须同开**，否则分页/导出错乱。

### 5.3 顶部操作按钮

- **导出数据**：列表部件「顶部操作」里勾选内置 **【导出数据】** 按钮即可 —— 导出走同一查询链路，天然带当前筛选条件。
- **“更多 >”**：顶部操作加一个自定义按钮，命名 `更多 >`，绑定 **自定义动作** 跳转联单列表页并带当前筛选：

```js
function main() {
  var element = this, rootPageElement = null;
  while (element) {
    if (element.getPageInfo && element.goHistory) { rootPageElement = element; break; }
    element = element.$parent;
  }
  var p = window.currentFilter || {};
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

- 目标「联单列表页」：单独新建页面，拖同一个列表部件，页面里的 **列表部件渲染组件-参数设置** 接收 `siteIds/vehicleNum/muckType/startDate/endDate` 并映射到列表查询条件（或同样用 hook 读 `this.$route.query`/extraParams）。列表页只要能打开 + 展示列表即可拿分，参数带入是加分保障。

---

## 6. 查询/重置全页联动 JS 完整模板（核心，先贴这个）

页面「高级 → 页面 JS / didMounted（页面加载完成）」贴入：

### 6.1 全局骨架（didMounted）

```js
function main() {
  var self = this;

  // ---------- 工具：读取查询区当前值 ----------
  window.getFilter = function () {
    var siteIds = self.$$('site_select').$$getValue();        // 多选 -> 数组
    var vehicleNum = self.$$('vehicle_select').$$getValue();
    var muckType = self.$$('muck_select').$$getValue();
    var range = self.$$('date_range').$$getValue() || [];
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
    var p = window.getFilter();
    window.currentFilter = p;                    // 给“更多>”跳转用
    var qp = [];
    ['siteIds', 'vehicleNum', 'muckType', 'startDate', 'endDate'].forEach(function (k) {
      if (p[k] !== '' && p[k] != null) qp.push({ name: k, valueContent: p[k] }); // 空条件不生效
    });
    return qp;
  };

  // ---------- 全页刷新 ----------
  window.refreshAll = function (ctx) {
    var qp = window.buildQueryParams();
    window.workbenchParams = qp;                 // 列表 hook 读它
    refreshOverview(self, qp);                   // 1) 概览（第 3 节函数）
    window.queryCircleData(self);                // 2) 趋势（第 4 节函数）
    var tableComp = self.$$element('table_list'); // 3) 列表：重查并回到第一页
    if (tableComp && tableComp.onRefresh) { tableComp.onRefresh(); }
    else if (tableComp && tableComp.$$refreshData) { tableComp.$$refreshData(); }
  };

  window.queryCircleData = function (ctx) { queryCircleData(self); }; // 供粒度下拉 onChange 调

  // ---------- 初始化：默认近 30 天 + 首屏加载 ----------
  setTimeout(function () {
    setDefaultDateRange(self);       // 第 2.3 节函数
    window.circleTypeValue = 'day';
    window.refreshAll(self);
  }, 300);                           // 等组件渲染完成再取/赋值
}

// —— 把第 2.3 的 setDefaultDateRange、第 3 节 refreshOverview、
//     第 4.3 的 queryCircleData / initTrendChart 四个函数原样贴在 main 下方 ——
```

### 6.2 查询按钮（自定义动作）

```js
function main() {
  window.refreshAll(this);
}
```

### 6.3 重置按钮（自定义动作）

```js
function main() {
  var self = this;
  self.$$('site_select').$$setValue([]);      // 多选清空传空数组
  self.$$('vehicle_select').$$setValue('');
  self.$$('muck_select').$$setValue('');
  // 运输时间恢复默认近 30 天
  var end = moment().format('YYYY-MM-DD');
  var start = moment().subtract(29, 'days').format('YYYY-MM-DD');
  self.$$('date_range').$$setValue([start, end]);
  window.circleTypeValue = 'day';
  setTimeout(function () { window.refreshAll(self); }, 100); // 等赋值生效再查
}
```

> 注意重置按钮在查询表单部件内，`this.$$()` 是从表单部件根查找；若组件找不到，改用 `this.$$element('组件id')` 向上查找，或把脚本挂到页面级按钮上。调试时 `console.log(window.getFilter())` 确认取值。

---

## 7. 联动调试流程（考前最后 25 分钟照做）

1. F12 打开控制台 → 刷新页面：确认无 `echarts is not defined`、无 `chartDom null`。
2. 首屏：4 指标有值（或 0/0.00）、趋势图出柱+线、列表有数据、日期默认近 30 天。
3. 选一个项目 → 点查询：`console.log` 确认 queryParams 只含非空项；四个模块同时变化。
4. 点重置：下拉清空、日期回近 30 天、全部数据恢复全量、列表回第 1 页。
5. 切天/周/月：仅趋势图重查，x 轴粒度变化。
6. 选一个查不到数据的条件组合：指标显示 0/0.00、图表“暂无数据”、列表空 —— 无 undefined/NaN。
7. 点导出数据：Excel 行数 = 当前筛选后的总条数。点“更多>”：跳到列表页且筛选生效。

---

## 8. 评分点对照 Checklist（40 分）

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
| 列表-交互 | 4 | □ 查询条件控制列表 □ 查询/重置后回第 1 页 | §5.2/§6 |

**抢分策略**：先把 §6 联动骨架 + §4 趋势图跑通（8+6+2=16 分集中在趋势），再补概览兜底和“更多>”。

---

## 9. 常见坑（血泪对照表）

1. **`echarts is not defined`**：忘了拖隐藏的环形图组件。容器隐藏必须 **开启强制渲染**，否则 `getElementById` 拿到 null。
2. **DOM id 后缀**：是 `组件唯一标识 + _csshandler_generate`，漏后缀图表永远画不出来。
3. **参数名就叫 `cicleType`**：考题原文如此（不是 circleType），DDCAT 入参照抄，手滑写对英语反而 0 分。
4. **hook 里改 param 的副作用**：官方提示 hook 中不建议改 param（影响导出与查询一致性）。本手册的合并方式恰恰是利用同一 hook 保证导出=查询条件；**不要**在 hook 里改 `pageIndex/pageSize`。
5. **数据模型分页开关与列表分页开关必须同步**（全开或全关），否则导出/翻页数据错乱。
6. **视图字段别名**：作为列表查询面板条件的字段**不能起别名**，否则条件匹配不上。
7. **多选传参**：`siteIds` 用 `join(',')` 传逗号串，DDCAT 内一般用 `FIND_IN_SET`/`IN` 解析——传数组对象会直接查空。
8. **日期取值格式**：统一 `moment(v).format('YYYY-MM-DD')`；日期组件取出的可能是时间戳/Date 对象，直接拼 SQL 必炸。
9. **didMounted 时序**：页面加载脚本里立即取组件值可能组件还没渲染完，包一层 `setTimeout(…, 300)`。
10. **`setOption(option, true)`**：第二参数不传 true，粒度切换/重查后旧 series 残留叠影。
11. **空数据兜底**：`row.cleanAmount.toFixed(2)` 在 undefined 上直接抛错 → 整个概览白屏。必须先 `Number()+isFinite()` 再 `toFixed`。
12. **找不到组件**：`this.$$()` 从页面根向下找、`this.$$element()` 从当前向上找；隐藏组件只能 `this.$$model()` 取属性。
13. **窗口缩放图表不自适应**（丢体验分不丢功能分）：可在 init 后加 `window.addEventListener('resize', function(){ myChart.resize(); })`。
14. 资源 ID 全部用 **Ctrl+Shift+C** 回填，手抄 UUID 极易错一位。
