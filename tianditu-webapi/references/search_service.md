# 地名搜索服务 V2.0

提供多种搜索类型的HTTP接口，包括普通搜索、视野内搜索、周边搜索、多边形搜索、行政区域搜索、分类搜索、统计搜索。

**注意：这是天地图新版API v2.0，使用 `/v2/search` 端点。**

## 请求地址

```
http://api.tianditu.gov.cn/v2/search?postStr={JSON参数}&type=query&tk={密钥}
```

## 请求参数

postStr需要传递JSON字符串格式的参数：

### 基础参数

| 参数 | 说明 | 类型 | 必填 | 取值范围 |
|---|---|---|---|---|
| keyWord | 搜索关键字 | String | 是 | 不支持'与&符号 |
| mapBound | 查询地图范围 | String | 是 | "-x,-y,x,y"，范围：-180,-90至180,90 |
| level | 查询级别 | String | 是 | 1-20 |
| queryType | 搜索类型 | String | 是 | 见下表 |
| start | 返回结果起始位置 | String | 是 | 0-300，默认0 |
| count | 返回结果数量 | String | 是 | 1-300 |
| specifyAdminCode | 指定行政区国标码 | String | 否 | 9位国标码，如北京：156110000 |

### queryType 搜索类型（v2.0版本）

| queryType | 类型说明 | 特殊参数要求 |
|---|---|---|
| 2 | 视野内搜索 | 需提供 `level` 和 `mapBound` |
| 3 | 周边搜索 | 需提供 `queryRadius` 和 `pointLonlat` |
| 10 | 多边形搜索 | 需提供 `polygon` 参数 |
| 12 | 行政区划区域搜索 | 需提供 `specify` 参数（行政区码） |

**注意：v2.0版本不再支持queryType=1（普通搜索）、4（建议词搜索）、7（纯地名搜索）。请使用视野内搜索（queryType=2）替代普通搜索。**

### 周边搜索专用参数

| 参数 | 说明 | 类型 | 必填 |
|---|---|---|---|
| queryRadius | 查询半径（米） | String | 是（queryType=3时） |
| pointLonlat | 中心点坐标 | String | 是（queryType=3时） |

## 请求示例

### 普通搜索
```bash
curl "http://api.tianditu.gov.cn/search?postStr={'keyWord':'超市','level':'11','mapBound':'116.04577,39.70307,116.77361,40.09583','queryType':'1','count':'20','start':'0'}&type=query&tk=$TIANDITU_API_KEY"
```

### 视野内搜索（v2.0）
```bash
# 在视野范围内搜索银行（queryType=2）
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'银行','level':'15','mapBound':'116.37552,39.8935,116.42102,39.91804','queryType':'2','count':'20','start':'0'}&type=query&tk=$TIANDITU_API_KEY"
```

### 周边搜索（v2.0）
```bash
# 在坐标116.42844,39.92314周边1000米范围内搜索超市
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'超市','queryRadius':'1000','pointLonlat':'116.42844,39.92314','queryType':'3','start':'0','count':'20'}&type=query&tk=$TIANDITU_API_KEY"
```

### 行政区划区域搜索（v2.0）
```bash
# 在指定行政区（156110108）搜索商厦（queryType=12）
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'商厦','queryType':'12','start':'0','count':'10','specify':'156110108'}&type=query&tk=$TIANDITU_API_KEY"
```

### 多边形搜索（v2.0）
```bash
# 在多边形范围内搜索学校（queryType=10）
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'学校','polygon':'x1,y1,x2,y2,x3,y3,x4,y4,x5,y5,x1,y1','queryType':'10','start':'0','count':'10'}&type=query&tk=$TIANDITU_API_KEY"
```

## 响应参数

### 基础响应

| 参数 | 说明 | 类型 | 返回条件 |
|---|---|---|---|
| resultType | 显示类型 | Int | 必返回 |
| count | 搜索总条数 | Int | 必返回 |
| keyword | 搜索关键词 | String | 必返回 |

### resultType 含义

| resultType | 说明 | 返回字段 |
|---|---|---|
| 1 | 普通POI | `pois` |
| 2 | 统计 | `statistics` |
| 3 | 行政区 | `area` |
| 4 | 建议词 | `suggests` |
| 5 | 线路结果 | `lineData` |

### pois（POI点集合）

| 参数 | 说明 | 类型 |
|---|---|---|
| name | POI点名称 | String |
| phone | 电话 | String |
| address | 地址 | String |
| lonlat | 坐标（经度,纬度） | String |
| distance | 距离（周边搜索时） | Int |
| poiType | POI类型（102=公交站） | Int |
| stationUuid | 公交站UUID | String |

### suggests（建议词）

| 参数 | 说明 | 类型 |
|---|---|---|
| name | 名称 | String |
| address | 地址 | String |
| gbCode | 国标码 | String |

### area（行政区）

| 参数 | 说明 | 类型 |
|---|---|---|
| name | 名称 | String |
| bound | 定位范围（矩形） | String |
| lonlat | 定位中心点坐标 | String |
| level | 显示级别 | Int |

## 注意事项

1. **JSON字符串格式**：postStr参数使用单引号包裹JSON字符串
2. **mapBound范围**：格式为"minLon,minLat,maxLon,maxLat"
3. **坐标系**：天地图使用CGCS2000坐标系
4. **分页**：使用start和count参数控制分页，start最大300
5. **配额限制**：个人和企业开发者有配额限制，需要更高配额可到控制台升级