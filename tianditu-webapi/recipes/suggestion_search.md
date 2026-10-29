# 地名搜索（v2.0）

使用天地图新版API v2.0进行地名和POI搜索。

**注意：v2.0版本不再支持建议词搜索（queryType=4）。请使用视野内搜索（queryType=2）替代。**

## 适用场景

- 用户想要查找特定关键词的地点（如"超市"、"银行"、"餐厅"）
- 用户想要查找特定名称的地点（如"清华大学"、"天安门"）
- 在指定范围内搜索POI

## 调用步骤

### 步骤 1：获取用户输入

用户提供部分关键词（如"超"、"北京天"等）。

### 步骤 2：构建请求

**必填参数（视野内搜索 queryType=2）：**
- `keyWord`：搜索关键词
- `mapBound`：搜索范围（格式：`minLon,minLat,maxLon,maxLat`）
- `level`：搜索级别（1-18）
- `queryType`：搜索类型（视野内搜索使用2）
- `start`：起始位置（默认0）
- `count`：返回数量（1-300）

### 步骤 3：发送请求

```bash
# 示例：搜索"超市"关键词（v2.0 API）
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'超市','level':'11','mapBound':'116.04577,39.70307,116.77361,40.09583','queryType':'2','count':'10','start':'0'}&type=query&tk=$TIANDITU_API_KEY"
```

### 步骤 5：解析结果

返回结果中：
- `resultType=1`：表示返回POI列表
- `pois`：POI点数组，每个POI包含：
  - `name`：地点名称
  - `address`：地址
  - `lonlat`：坐标（经度,纬度）
  - `phone`：电话（可能有）
  - `hotPointID`：热点ID
  - `poiType`：POI类型（101=普通POI，102=公交站）

## 搜索变体

### 行政区划区域搜索（queryType=12）

在指定行政区划内搜索：

```bash
# 在北京朝阳区（156110105）搜索超市
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'超市','queryType':'12','start':'0','count':'10','specify':'156110105'}&type=query&tk=$TIANDITU_API_KEY"
```

### 周边搜索（queryType=3）

在指定坐标周边搜索：

```bash
# 在坐标周边500米搜索公园
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'公园','queryRadius':'500','pointLonlat':'116.48016,39.93136','queryType':'3','start':'0','count':'10'}&type=query&tk=$TIANDITU_API_KEY"
```

### 多边形搜索（queryType=10）

在多边形范围内搜索：

```bash
# 在多边形范围内搜索学校
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'学校','polygon':'x1,y1,x2,y2,x3,y3,x4,y4,x5,y5,x1,y1','queryType':'10','start':'0','count':'10'}&type=query&tk=$TIANDITU_API_KEY"
```

## 注意事项

1. **关键词长度**：建议词搜索适用于较短的关键词（1-3个字符）
2. **搜索范围**：范围越大，建议词越多，但相关度可能降低
3. **返回数量**：建议使用较少的数量（10-20），避免过多无效建议
4. **空地址**：`address` 字段可能为空串，需要处理这种情况

## 集成示例

构建输入框自动补全功能：

```javascript
// 用户输入 "超"
const keyword = "超";
const mapBound = "116.40569,39.91088,116.45119,39.93542";

// 获取建议词
const url = `http://api.tianditu.gov.cn/search?postStr={'keyWord':'${keyword}','level':'15','mapBound':'${mapBound}','queryType':'4','count':'10','start':'0'}&type=query&tk=${apiKey}`;

fetch(url)
  .then(res => res.json())
  .then(data => {
    // 展示建议词列表
    const suggestions = data.suggests.map(s => ({
      label: s.name,
      address: s.address,
      gbCode: s.gbCode
    }));
    // 渲染到下拉列表中
    showSuggestions(suggestions);
  });
```

## 错误处理

- 输入过长的关键词可能返回较少建议词
- 搜索范围过小可能返回空结果
- 关键词包含特殊符号（'或&）会导致错误