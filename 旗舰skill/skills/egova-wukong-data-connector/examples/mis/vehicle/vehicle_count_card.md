# 示例：车辆总数指标卡

## 用户需求示例

```text
我要做一个车辆总数指标卡，统计当前车辆总数。
```

## 应命中接口

| 项目 | 内容 |
|---|---|
| apiCode | VEHICLE_COUNT |
| 接口名称 | 条件查询车辆总数 |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/vehicle/count` |
| 星桥接口路径地址 | `API平台/悟能接口/车辆相关/条件查询车辆总数` |
| 详细接口文档 | `knowledge/api_details/mis/vehicle/VEHICLE_COUNT.md` |
| 响应主路径 | `result` |
| 响应形态 | number |

## 判断要点

1. 用户要的是“车辆总数”，属于 count 场景。
2. 不需要车辆明细，因此不应使用 `VEHICLE_LIST` 或 `VEHICLE_PAGE`。
3. 未说明筛选条件时，默认不限制。
4. 指标卡目标格式推荐为对象：`{ title, value }`。

## 推荐请求参数

```json
{}
```

## 映射

| 组件目标字段 | 来源字段 | 转换规则 | 说明 |
|---|---|---|---|
| title | 固定值 | 固定为“车辆总数” | 指标卡标题 |
| value | data | Number 转换 | `data` 是 result 本体 |

## 过滤脚本

```javascript
function filter(data) {
    return {
        title: '车辆总数',
        value: Number(data || 0)
    };
}
```

## 需要核对的内容

```text
无
```