# 地址转坐标（地理编码）

将地址文本转换为经纬度坐标。

## 适用场景

- 用户想知道某个地址的坐标
- 用户需要将地名转换为坐标进行地图标注
- 计算两个地点之间的距离或路线

## 调用步骤

天地图地理编码服务与地名搜索服务配合使用。

### 步骤 1：分析地址类型

**结构化地址**：包含完整地址信息，如"北京市海淀区中关村大街1号"
**地名/POI名称**：地点名称或地标，如"天安门"、"清华大学"

### 步骤 2：确定搜索范围

根据地址所在城市确定搜索范围：
- 全局搜索：使用较大范围 `-180,-90,180,90`
- 城市搜索：使用城市矩形范围，可提高精度

### 步骤 3：构建地名搜索请求

使用地名搜索服务v2.0（queryType=2）搜索地址：

**必填参数：**
- `keyWord`：地址文本
- `mapBound`：搜索范围
- `level`：搜索级别
- `queryType`：视野内搜索使用2
- `start`：起始位置（0）
- `count`：返回数量（1-5）

### 步骤 4：发送请求

```bash
# 示例：搜索"中关村"获取坐标（v2.0 API）
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'中关村','level':'11','mapBound':'116.04577,39.70307,116.77361,40.09583','queryType':'2','count':'5','start':'0'}&type=query&tk=$TIANDITU_API_KEY"
```

### 步骤 5：解析结果

返回结果中：
- `resultType=1`：表示返回POI列表
- `pois`：POI数组
- `pois[0].lonlat`：坐标（格式：`lon,lat`）

**选择最佳结果：**
1. 如果只有1个结果，直接使用
2. 如果有多个结果，根据地址匹配度或距离选择最合适的
3. 可根据 `name` 和 `address` 字段判断是否匹配用户输入

## 使用行政区划码提高精度（v2.0）

对于已知城市的地址，使用 `queryType=12` 和 `specify` 参数指定行政区：

```bash
# 在北京市范围内搜索（v2.0 API）
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'中关村','queryType':'12','start':'0','count':'5','specify':'156110000'}&type=query&tk=$TIANDITU_API_KEY"
```

## 常用行政区码

| 城市/行政区 | 国标码 |
|---|---|
| 北京市 | 156110000 |
| 上海市 | 156310000 |
| 广州市 | 156440100 |
| 深圳市 | 156440300 |
| 天津市 | 156120000 |
| 重庆市 | 156500000 |
| 杭州市 | 156330100 |
| 南京市 | 156320100 |

## 示例：从地址到坐标

用户需求："天安门广场的坐标"

```bash
# 搜索天安门（v2.0 API）
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'天安门广场','level':'11','mapBound':'116.04577,39.70307,116.77361,40.09583','queryType':'2','count':'1','start':'0'}&type=query&tk=$TIANDITU_API_KEY"

# 返回结果（假设）
{
  "resultType": 1,
  "count": 1,
  "pois": [
    {
      "name": "天安门广场",
      "address": "北京市东城区天安门广场",
      "lonlat": "116.397,39.909"
    }
  ]
}

# 提取坐标：116.397,39.909
```

## 多地址批量转换

需要转换多个地址时，可逐个搜索：

```bash
# 批量搜索示例（v2.0 API）
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'大学','level':'15','mapBound':'...','queryType':'2','count':'20','start':'0'}&type=query&tk=$TIANDITU_API_KEY"
```

## 注意事项

1. **地址精度**：结构化地址可获得更精确的坐标
2. **搜索范围**：缩小搜索范围（mapBound）可提高结果精度
3. **行政区码**：使用queryType=12和specify参数可避免跨城市结果混淆
4. **多结果**：可能返回多个匹配结果，需要根据名称/地址判断最佳匹配
5. **坐标格式**：返回的lonlat格式为 `lon,lat`，需要解析使用

## 错误处理

- 搜索无结果：尝试扩大搜索范围或调整关键词
- 多结果混淆：使用行政区码限定搜索范围
- 地址格式：尝试简化地址关键词（去掉门牌号等细节）

## 与逆地理编码配合

```javascript
// 地址转坐标，再转回地址验证
async function verifyAddress(addressText) {
  // 地址转坐标
  const coord = await geocode(addressText);
  
  // 坐标转地址验证
  const verifiedAddr = await reverseGeocode(coord.lon, coord.lat);
  
  return {
    original: addressText,
    coord: coord,
    verified: verifiedAddr.formatted_address
  };
}
```