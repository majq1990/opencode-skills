# 示例：近 30 天案件热力图

## 用户需求示例

```text
我要做一个近30天案件热力图，展示案件分布密度。
```

## 应命中接口

| 项目 | 内容 |
|---|---|
| apiCode | REC_HEATMAP |
| 接口名称 | 案件热力图 |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/heatmap` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/案件热力图` |
| 详细接口文档 | `knowledge/api_details/mis/rec/REC_HEATMAP.md` |
| 响应主路径 | `result` |
| 响应形态 | array |

## 判断要点

1. “热力图”直接命中 heatmap 接口。
2. 接口返回 `longitude`、`latitude`、`value`。
3. 热力图目标格式通常是 `[{ lng, lat, value }]`。
4. 文档建议时间跨度小于一个月，因此近 30 天合理。
5. 经纬度为空或为 0 需要过滤。

## 推荐请求参数

```json
{
  "startCreateTime": "2024-01-01 00:00:00",
  "endCreateTime": "2024-01-30 23:59:59"
}
```

## 映射

| 组件目标字段 | 来源字段 | 转换规则 | 说明 |
|---|---|---|---|
| lng | item.longitude | Number 转换 | 经度 |
| lat | item.latitude | Number 转换 | 纬度 |
| value | item.value | Number 转换 | 案件数量 |

## 过滤脚本

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            lng: Number(item.longitude || 0),
            lat: Number(item.latitude || 0),
            value: Number(item.value || 0)
        };
    }).filter(function (item) {
        return item.lng !== 0 && item.lat !== 0;
    });
}
```

## 需要核对的内容

| 序号 | 待确认项 | 影响范围 | 建议处理 |
|---|---|---|---|
| 1 | 热力图坐标系是否和悟空地图一致 | 地图展示 | 联调时确认坐标系 |
| 2 | 是否需要按区划、来源或问题类型过滤 | 请求参数 | 如需要，补充对应筛选条件 |