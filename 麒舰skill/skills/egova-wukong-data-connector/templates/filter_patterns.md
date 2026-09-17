# 过滤脚本模式模板

> 用途：生成 `function filter(data)` 前先确定轻量过滤策略，再套用对应 ES5 模式。`data` 默认是公司响应外层的 `result` 本体，不默认访问 `data.result`、`data.totalCount` 或 `data.hasError`。

## 通用策略结构

生成脚本前先明确：

```json
{
  "inputShape": "array | object | number | tree | pageRows",
  "outputShape": "组件期望的 result 结构",
  "mapping": [
    {"from": "sourceField", "to": "targetField", "type": "string | number | object | array"}
  ],
  "fallbacks": {
    "array": [],
    "string": "",
    "number": 0,
    "object": {}
  },
  "operations": ["map", "sort", "topN", "group", "flattenTree"]
}
```

策略不一定输出给用户，但脚本必须体现这些约束。

## 模式一：array → array 字段映射

适用于柱状图、排行列表、普通列表等。

```js
function filter(data) {
  var list = data;
  if (!list || !list.length) {
    return [];
  }

  var result = [];
  for (var i = 0; i < list.length; i++) {
    var item = list[i] || {};
    var value = Number(item.value);
    result.push({
      name: item.text || item.name || '',
      value: isNaN(value) ? 0 : value
    });
  }
  return result;
}
```

## 模式二：number → 指标卡对象

适用于接口 `result` 直接返回数量，但组件需要对象结构。

```js
function filter(data) {
  var value = Number(data);
  return {
    name: '总数',
    value: isNaN(value) ? 0 : value
  };
}
```

## 模式三：object → 多指标数组

适用于案件指标统计等动态字段对象转多卡片。

```js
function filter(data) {
  var obj = data || {};
  var report = Number(obj.report);
  var archive = Number(obj.archive);

  return [
    {
      name: '上报数',
      value: isNaN(report) ? 0 : report
    },
    {
      name: '结案数',
      value: isNaN(archive) ? 0 : archive
    }
  ];
}
```

## 模式四：array → 图表 series

适用于组件需要 `{xAxis: [], series: []}` 或类似结构。

```js
function filter(data) {
  var list = data;
  if (!list || !list.length) {
    return {
      xAxis: [],
      series: []
    };
  }

  var xAxis = [];
  var seriesData = [];
  for (var i = 0; i < list.length; i++) {
    var item = list[i] || {};
    var value = Number(item.value);
    xAxis.push(item.text || item.name || '');
    seriesData.push(isNaN(value) ? 0 : value);
  }

  return {
    xAxis: xAxis,
    series: [
      {
        name: '数量',
        data: seriesData
      }
    ]
  };
}
```

## 模式五：array → 地图点位

适用于人员、车辆、案件地图点位。

```js
function filter(data) {
  var list = data;
  if (!list || !list.length) {
    return [];
  }

  var result = [];
  for (var i = 0; i < list.length; i++) {
    var item = list[i] || {};
    var longitude = Number(item.longitude);
    var latitude = Number(item.latitude);
    result.push({
      id: item.id || '',
      name: item.name || item.text || item.vehicleNum || item.patrolName || item.taskNum || '',
      longitude: isNaN(longitude) ? 0 : longitude,
      latitude: isNaN(latitude) ? 0 : latitude
    });
  }
  return result;
}
```

## 模式六：tree → flat array

适用于树形接口返回但组件需要平铺列表。字段名需按 detailDoc 或现场样例调整。

```js
function filter(data) {
  var list = data;
  if (!list || !list.length) {
    return [];
  }

  var result = [];
  function walk(nodes) {
    if (!nodes || !nodes.length) {
      return;
    }
    for (var i = 0; i < nodes.length; i++) {
      var item = nodes[i] || {};
      var value = Number(item.value);
      result.push({
        id: item.name || item.id || '',
        name: item.text || item.regionName || item.unitName || '',
        value: isNaN(value) ? 0 : value
      });
      walk(item.children);
    }
  }

  walk(list);
  return result;
}
```

## 模式七：排序和 TopN

适用于排行类组件。只有用户明确要排行或组件是排行列表时使用。

```js
function filter(data) {
  var list = data;
  if (!list || !list.length) {
    return [];
  }

  var result = [];
  for (var i = 0; i < list.length; i++) {
    var item = list[i] || {};
    var value = Number(item.value);
    result.push({
      name: item.text || item.name || '',
      value: isNaN(value) ? 0 : value
    });
  }

  result.sort(function(a, b) {
    return b.value - a.value;
  });

  return result.slice(0, 10);
}
```

## 使用注意

- 模板里的字段名只是模式示例；最终脚本必须基于 `detailDoc`、现场样例或已确认映射调整。
- 分页总数 `totalCount` 默认不在 `filter(data)` 中读取，因为 `data` 默认是外层 `result` 本体。
- 若组件确实需要分页总数，必须先确认悟空是否把完整外层响应包传入脚本；否则停在 Gate 0。
- 不要为了兜底访问未确认的深层路径；深层路径未确认时先要求接口样例或 detailDoc。