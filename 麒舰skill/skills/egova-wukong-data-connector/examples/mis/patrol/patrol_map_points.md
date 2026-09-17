# 示例：人员地图点位

## 用户需求示例

```text
我要在地图上展示人员点位，显示人员名称、人员类型和在线状态。
```

## 应命中接口

| 项目 | 内容 |
|---|---|
| apiCode | PATROL_SIMPLE_LIST |
| 接口名称 | 人员简要列表查询 |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/patrol/simple/list` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/人员简要列表查询` |
| 详细接口文档 | `knowledge/api_details/mis/patrol/PATROL_SIMPLE_LIST.md` |
| 响应主路径 | `result` |
| 响应形态 | array |

## 判断要点

1. 地图点位优先使用简要列表。
2. 只需要人员名称、类型、在线状态和经纬度，不需要完整人员详情。
3. 经纬度为空或为 0 需要过滤。
4. 点位详情可后续通过 `PATROL_INFO` 查询。

## 推荐请求参数

```json
{}
```

## 映射

| 组件目标字段 | 来源字段 | 转换规则 | 说明 |
|---|---|---|---|
| id | item.id | 字符串兜底 | 人员 id |
| name | item.patrolName | 字符串兜底 | 人员名称 |
| typeName | item.patrolTypeName | 字符串兜底 | 人员类型 |
| regionName | item.regionName | 字符串兜底 | 所属区划 |
| online | item.onlineFlag | Boolean 判断 | 是否在线 |
| lng | item.longitude | Number 转换 | 经度 |
| lat | item.latitude | Number 转换 | 纬度 |

## 过滤脚本

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            id: item.id || '',
            name: item.patrolName || '',
            typeName: item.patrolTypeName || '',
            regionName: item.regionName || '',
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
| 1 | 地图坐标系是否一致 | 点位展示 | 联调时确认坐标系 |