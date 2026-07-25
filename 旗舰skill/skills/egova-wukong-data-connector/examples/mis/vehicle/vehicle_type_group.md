# 示例：车辆类型分布饼图

## 用户需求示例

```text
我要做一个车辆类型分布饼图，展示每种车辆类型有多少辆。
```

## 应命中接口

| 项目 | 内容 |
|---|---|
| apiCode | VEHICLE_GROUP_TYPE |
| 接口名称 | 车辆类型分组 |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/vehicle/group` |
| 星桥接口路径地址 | `API平台/悟能接口/车辆相关/车辆类型分组` |
| 详细接口文档 | `knowledge/api_details/mis/vehicle/VEHICLE_GROUP_TYPE.md` |
| 响应主路径 | `result` |
| 响应形态 | array |

## 判断要点

1. 用户要的是按车辆类型分组统计。
2. 不需要车辆明细。
3. 饼图目标格式通常是 `[{ name, value }]`。
4. 接口返回 `name/text/value` 时，需要根据详细文档确认 `name` 和 `text` 语义。

## 推荐请求参数

```json
{}
```

## 映射

| 组件目标字段 | 来源字段 | 转换规则 | 说明 |
|---|---|---|---|
| id | item.text | 字符串兜底 | 车辆类型 id |
| name | item.name | 字符串兜底 | 车辆类型名称 |
| value | item.value | Number 转换 | 车辆数量 |

## 过滤脚本

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            id: item.text || '',
            name: item.name || '',
            value: Number(item.value || 0)
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

## 需要核对的内容

```text
无
```