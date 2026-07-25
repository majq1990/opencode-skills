# 坐标转详细地址（逆地理编码）

将经纬度坐标转换为结构化的地址信息。

## 适用场景

- 用户想知道某个坐标点对应的地址
- 用户点击地图位置，需要显示该位置的地址
- 将GPS定位坐标转换为可读的地址信息

## 调用步骤

### 步骤 1：准备坐标数据

用户提供坐标（经度,纬度）：
- 格式：`lon,lat`（经度在前，纬度在后）
- 示例：`116.37304,39.92594`

### 步骤 2：构建请求

**必填参数：**
- `lon`：经度（坐标x值）
- `lat`：纬度（坐标y值）
- `ver`：接口版本（固定为1）

### 步骤 3：发送请求

```bash
# 示例：将坐标116.37304,39.92594转换为地址
curl "http://api.tianditu.gov.cn/geocoder?postStr={'lon':116.37304,'lat':39.92594,'ver':1}&type=geocode&tk=$TIANDITU_API_KEY"
```

### 步骤 4：解析结果

返回结果包含丰富的地址信息：

**主要信息：**
- `formatted_address`：格式化的完整地址
- `addressComponent.city`：所在城市/区县

**周边信息：**
- `addressComponent.address`：最近的地点
- `addressComponent.address_distince`：距离最近地点的距离（米）
- `addressComponent.address_position`：相对于最近地点的方向
- `addressComponent.poi`：最近的POI点名称
- `addressComponent.poi_distince`：距离最近POI的距离（米）
- `addressComponent.poi_position`：相对于POI的方向
- `addressComponent.road`：最近的道路名称
- `addressComponent.road_distince`：距离道路的距离（米）

## 响应示例

```json
{
  "status": "0",
  "msg": "OK",
  "result": {
    "formatted_address": "北京市海淀区中关村大街",
    "addressComponent": {
      "address": "中关村",
      "address_distince": 50,
      "address_position": "东北",
      "city": "北京市海淀区",
      "poi": "中关村科技园",
      "poi_distince": 100,
      "poi_position": "东",
      "road": "中关村大街",
      "road_distince": 30
    },
    "location": {
      "lon": 116.37304,
      "lat": 39.92594
    }
  }
}
```

## 使用场景示例

### 地图点击显示地址

用户点击地图位置，获取坐标后转换为地址显示：

```javascript
// 用户点击地图，获取坐标
map.on('click', function(e) {
  const lon = e.lnglat.lng;
  const lat = e.lnglat.lat;
  
  // 转换为地址
  const url = `http://api.tianditu.gov.cn/geocoder?postStr={'lon':${lon},'lat':${lat},'ver':1}&type=geocode&tk=${apiKey}`;
  
  fetch(url)
    .then(res => res.json())
    .then(data => {
      if (data.status === '0') {
        // 显示地址信息
        showAddress(data.result.formatted_address);
      }
    });
});
```

### GPS定位显示地址

```javascript
// 获取GPS定位坐标
navigator.geolocation.getCurrentPosition(function(position) {
  const lon = position.coords.longitude;
  const lat = position.coords.latitude;
  
  // 转换为地址
  reverseGeocode(lon, lat).then(address => {
    console.log('当前位置：' + address);
  });
});
```

## 生成详细地址描述

根据返回信息生成用户友好的地址描述：

```javascript
function formatAddress(result) {
  const addr = result.addressComponent;
  
  // 方向描述
  let description = result.formatted_address;
  
  // 如果有POI信息
  if (addr.poi) {
    description += `，距离${addr.poi}约${addr.poi_distince}米，在${addr.poi}的${addr.poi_position}方向`;
  }
  
  // 如果有道路信息
  if (addr.road) {
    description += `，靠近${addr.road}`;
  }
  
  return description;
}
```

## 注意事项

1. **坐标格式**：lon,lat（经度在前，纬度在后）
2. **坐标系**：天地图使用CGCS2000坐标系
3. **精度**：返回的地址信息包含多种参考（地点、POI、道路）
4. **方向**：方向信息使用中文描述（东、西、南、北、东北等）
5. **版本参数**：ver固定为1

## 错误处理

- `status=404`：表示出错，检查坐标是否在有效范围内
- `status=1`：表示错误，检查参数格式
- 坐标超出范围（lon:-180~180, lat:-90~90）会返回错误