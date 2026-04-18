# 周边搜索POI

在指定坐标点周边搜索特定类型的地点。

## 适用场景

- 用户想要查找某位置周边的地点（如"我附近有哪些银行"）
- 用户想要查找某地点周边的设施（如"天安门附近有哪些餐厅"）

## 调用步骤

### 步骤 1：获取中心点坐标

如果是用户提供的地名，需要先通过地名搜索获取坐标：
- 参考 `recipes/search_poi.md` 搜索地名
- 从返回的POI结果中获取 `lonlat` 字段

如果是用户直接提供的坐标，可直接使用。

### 步骤 2：确定搜索半径

根据用户需求确定搜索半径（单位：米）：
- 近距离搜索：500-1000米
- 中距离搜索：2000-5000米
- 远距离搜索：10000米或更大

### 步骤 3：构建请求

**必填参数：**
- `keyWord`：搜索关键词
- `mapBound`：搜索范围（需包含中心点周边）
- `level`：搜索级别（推荐15）
- `queryType`：周边搜索使用3
- `pointLonlat`：中心点坐标（格式：`lon,lat`）
- `queryRadius`：搜索半径（单位：米）
- `start`：起始位置（默认0）
- `count`：返回数量（1-300）

### 步骤 4：发送请求

```bash
# 示例：在坐标116.42844,39.92314周边1000米范围搜索超市（v2.0 API）
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'超市','queryRadius':'1000','pointLonlat':'116.42844,39.92314','queryType':'3','start':'0','count':'20'}&type=query&tk=$TIANDITU_API_KEY"
```

### 步骤 5：解析结果

返回结果中：
- `resultType=1`：表示返回POI列表
- `pois`：POI点数组，每个POI包含：
  - `name`：地点名称
  - `address`：地址
  - `lonlat`：坐标
  - `distance`：距离中心点的距离（米）
  - `phone`：电话（可能有）

## 计算mapBound

mapBound需要包含中心点和搜索半径范围，可按以下方式估算：

```
中心点：(lon, lat)
半径：r 米

估算方法：
度数偏移 = r / 111320（约每度111公里）
minLon = lon - 度数偏移
maxLon = lon + 度数偏移
minLat = lat - 度数偏移
maxLat = lat + 度数偏移
```

## 示例：从地名到周边搜索

用户需求："天安门附近的餐厅"

1. 先搜索"天安门"获取坐标（v2.0 API）
```bash
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'天安门','level':'11','mapBound':'116.04577,39.70307,116.77361,40.09583','queryType':'2','count':'1','start':'0'}&type=query&tk=$TIANDITU_API_KEY"
```

2. 从结果中获取坐标（假设为116.397,39.909）

3. 周边搜索餐厅（v2.0 API）
```bash
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'餐厅','queryRadius':'1000','pointLonlat':'116.397,39.909','queryType':'3','start':'0','count':'20'}&type=query&tk=$TIANDITU_API_KEY"
```

## 常见变体

### 不同半径搜索（v2.0）

```bash
# 周边500米搜索
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'超市','queryRadius':'500','pointLonlat':'116.42844,39.92314','queryType':'3','start':'0','count':'20'}&type=query&tk=$TIANDITU_API_KEY"

# 周边2000米搜索
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'超市','queryRadius':'2000','pointLonlat':'116.42844,39.92314','queryType':'3','start':'0','count':'20'}&type=query&tk=$TIANDITU_API_KEY"
```

**注意：v2.0 API周边搜索不再需要 `mapBound` 和 `level` 参数。**

## 错误处理

- 搜索无结果时，可尝试扩大搜索半径
- 确保 `mapBound` 范围足够大以包含搜索半径范围
- 确保 `pointLonlat` 格式正确（lon,lat，经度在前）