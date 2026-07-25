# 关键词搜索POI

使用关键词搜索特定类型的地点信息。

## 适用场景

- 用户想要查找特定类型的地点（如"超市"、"银行"、"餐厅"）
- 用户想要查找特定名称的地点（如"清华大学"、"天安门"）

## 调用步骤

### 步骤 1：确定搜索范围

根据用户需求确定搜索范围（mapBound参数）：
- 全局搜索：使用较大范围如 `-180,-90,180,90`
- 城市搜索：使用该城市的矩形范围
- 当前视野搜索：使用当前地图视野的矩形范围

### 步骤 2：构建请求

**必填参数：**
- `keyWord`：搜索关键词
- `mapBound`：搜索范围（格式：`minLon,minLat,maxLon,maxLat`）
- `level`：搜索级别（1-20，推荐11-15）
- `queryType`：搜索类型（普通搜索使用1）
- `start`：起始位置（默认0）
- `count`：返回数量（1-300）

### 步骤 3：发送请求

```bash
# 示例：在北京范围内搜索超市（使用v2/search API）
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'超市','level':'11','mapBound':'116.04577,39.70307,116.77361,40.09583','queryType':'2','count':'20','start':'0'}&type=query&tk=$TIANDITU_API_KEY"
```

### 步骤 4：解析结果

返回结果中：
- `resultType=1`：表示返回POI列表
- `pois`：POI点数组，每个POI包含：
  - `name`：地点名称
  - `address`：地址
  - `lonlat`：坐标（经度,纬度）
  - `phone`：电话（可能有）

## 常见变体

### 视野内搜索（v2.0）

使用 `queryType=2` 进行视野内搜索：

```bash
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'银行','level':'15','mapBound':'116.37552,39.8935,116.42102,39.91804','queryType':'2','count':'20','start':'0'}&type=query&tk=$TIANDITU_API_KEY"
```

### 行政区划区域搜索（v2.0）

使用 `queryType=12` 指定行政区搜索：

```bash
# 指定北京朝阳区（156110105）搜索
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'超市','queryType':'12','start':'0','count':'20','specify':'156110105'}&type=query&tk=$TIANDITU_API_KEY"
```

## 错误处理

- 搜索无结果时，`count=0`，`pois` 数组为空
- 可尝试扩大搜索范围或调整关键词
- 关键词不支持 `'` 和 `&` 符号

## 常用行政区码

| 城市/行政区 | 国标码 |
|---|---|
| 北京市 | 156110000 |
| 上海市 | 156310000 |
| 广东省 | 156440000 |
| 广州市 | 156440100 |
| 深圳市 | 156440300 |