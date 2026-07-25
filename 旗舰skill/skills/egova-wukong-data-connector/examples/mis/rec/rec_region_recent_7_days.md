# 示例：近 7 天各区案件上报数排行

## 用户需求示例

```text
我要做一个近7天各区案件上报数排行，按上报数倒序展示。
```

## 应命中接口

| 项目 | 内容 |
|---|---|
| apiCode | REC_INDEX_REGION |
| 接口名称 | 基于区划的案件指标统计 |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/index/group?@state=region` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/基于区划的案件指标统计` |
| 详细接口文档 | `knowledge/api_details/mis/rec/REC_INDEX_REGION.md` |
| 响应主路径 | `result` |
| 响应形态 | array |

## 判断要点

1. “各区”表示按区划维度分组。
2. “上报数”对应 `groupList=["report"]`。
3. “近 7 天”需要设置统计开始时间和结束时间。
4. “排行”需要按 `report` 倒序排序。
5. 用户未说明具体区划范围，默认所有区。
6. 需求涉及区划统计，行政层级默认按区县，即 `regionType=2`。

## 推荐请求参数

```json
{
  "groupList": [
    "report"
  ],
  "customFlag": true,
  "regionCondition": {
    "regionType": 2
  },
  "sortField": "report",
  "desc": 1
}
```

> 实际联调时需要由现场传入近 7 天的 `startTimestamp` 和 `endTimestamp`。

## 映射

| 组件目标字段 | 来源字段 | 转换规则 | 说明 |
|---|---|---|---|
| id | item.name | 字符串兜底 | 区划 id |
| name | item.text | 字符串兜底 | 区划名称 |
| value | item.report | Number 转换 | 上报数 |

## 过滤脚本

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            id: item.name || '',
            name: item.text || '',
            value: Number(item.report || 0)
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

## 需要核对的内容

| 序号 | 待确认项 | 影响范围 | 建议处理 |
|---|---|---|---|
| 1 | 近 7 天时间范围由谁传入 | 请求参数 | 由现场或大屏变量传入 `startTimestamp`、`endTimestamp` |