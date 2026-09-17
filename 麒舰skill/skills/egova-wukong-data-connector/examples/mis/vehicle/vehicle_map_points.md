# 示例：车辆地图点位

## 用户需求示例

```text
我要在地图上展示车辆点位，点位上显示车牌号和在线状态。
```

## 应命中接口

| 项目 | 内容 |
|---|---|
| apiCode | VEHICLE_SIMPLE_LIST |
| 接口名称 | 车辆简要列表查询 |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/vehicle/simple/list` |
| 星桥接口路径地址 | `API平台/悟能接口/车辆相关/车辆简要列表查询` |
| 详细接口文档 | `knowledge/api_details/mis/vehicle/VEHICLE_SIMPLE_LIST.md` |
| 响应主路径 | `result` |
| 响应形态 | array |

## 判断要点

1. 地图点位优先用简要列表，不用完整列表。
2. 目标字段至少需要 `id`、`name`、`lng`、`lat`。
3. 经纬度为空、0 或无效时需要过滤。
4. `data` 默认是外层响应的 `result` 本体。

## 推荐请求参数

```json
{}
```

## 映射

| 组件目标字段 | 来源字段 | 转换规则 | 说明 |
|---|---|---|---|
| id | item.id | 字符串兜底 | 车辆 id |
| name | item.vehicleNum | 字符串兜底 | 车牌号 |
| lng | item.longitude | Number 转换 | 经度 |
| lat | item.latitude | Number 转换 | 纬度 |
| online | item.onlineFlag | Boolean 判断 | 是否在线 |

## 过滤脚本

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            id: item.id || '',
            name: item.vehicleNum || '',
            vehicleNum: item.vehicleNum || '',
            online: item.onlineFlag === true,
            lng: Number(item.longitude || 0),
            lat: Number(item.latitude || 0)
        };
    }).filter(function (item) {
        return item.lng !== 0 && item.lat !== 0;
    });
}
```

## 需要核对的内容

| 序号 | 待确认项 | 影响范围 | 建议处理 |
|---|---|---|---|
| 1 | 坐标系是否和悟空地图组件一致 | 地图点位偏移 | 联调时确认坐标系 |