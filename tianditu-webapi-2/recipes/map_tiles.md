# 获取地图瓦片URL

构建各类地图瓦片的请求URL，用于地图应用开发。

## 适用场景

- 开发Web地图应用，需要加载地图瓦片
- 在地图上叠加不同类型的图层
- 构建自定义地图样式

## 调用步骤

### 步骤 1：确定图层类型

根据应用需求选择图层：

**底图图层：**
- `vec`：矢量底图（传统地图风格）
- `img`：影像底图（卫星影像）
- `ter`：地形晕渲（地形渲染）

**注记图层：**
- `cva`：矢量注记（配合矢量底图）
- `cia`：影像注记（配合影像底图）
- `cta`：地形注记（配合地形底图）

**其他图层：**
- `ibo`：全球境界（国界、省界等）

### 步骤 2：确定投影类型

根据应用需求选择投影：

- `_w`：球面墨卡托投影（Web地图标准，兼容主流地图库）
- `_c`：经纬度投影（适用于需要精确坐标的应用）

### 步骤 3：计算瓦片坐标

根据地图显示需求计算瓦片坐标：
- `z`：级别（1-18）
- `y`：行号（根据级别和纬度计算）
- `x`：列号（根据级别和经度计算）

### 步骤 4：构建瓦片URL

**URL格式：**
```
http://t[0-7].tianditu.gov.cn/{图层}_{投影}/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER={图层}&STYLE=default&TILEMATRIXSET={投影}&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk={密钥}
```

## 常用组合示例

### 矢量地图（推荐组合）

```bash
# 矢量底图
http://t0.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=$TIANDITU_API_KEY

# 矢量注记（叠加在底图上）
http://t0.tianditu.gov.cn/cva_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cva&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=$TIANDITU_API_KEY
```

### 影像地图

```bash
# 影像底图
http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=$TIANDITU_API_KEY

# 影像注记（叠加在底图上）
http://t0.tianditu.gov.cn/cia_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cia&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=$TIANDITU_API_KEY
```

### 地形地图

```bash
# 地形底图
http://t0.tianditu.gov.cn/ter_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ter&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=$TIANDITU_API_KEY

# 地形注记
http://t0.tianditu.gov.cn/cta_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cta&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=$TIANDITU_API_KEY
```

## 与主流地图库集成

### Leaflet

```javascript
// 矢量地图
const vecLayer = L.tileLayer(
  'http://t0.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=' + apiKey,
  { maxZoom: 18 }
);

const cvaLayer = L.tileLayer(
  'http://t0.tianditu.gov.cn/cva_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cva&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=' + apiKey,
  { maxZoom: 18 }
);

// 添加到地图
const map = L.map('map').setView([39.9, 116.4], 11);
vecLayer.addTo(map);
cvaLayer.addTo(map);
```

### OpenLayers

```javascript
// 矢量底图
const vecLayer = new ol.layer.Tile({
  source: new ol.source.WMTS({
    url: 'http://t0.tianditu.gov.cn/vec_w/wmts',
    layer: 'vec',
    matrixSet: 'w',
    format: 'tiles',
    tileGrid: new ol.tilegrid.WMTS({
      origin: ol.extent.getTopLeft(ol.proj.get('EPSG:3857').getExtent()),
      resolutions: resolutions,
      matrixIds: matrixIds
    }),
    style: 'default',
    projection: 'EPSG:3857'
  })
});

// 设置tk参数
vecLayer.getSource().setUrl(vecLayer.getSource().getUrl() + '?tk=' + apiKey);
```

### Cesium

```javascript
// 影像底图
const imgProvider = new Cesium.WebMapTileServiceImageryProvider({
  url: 'http://t0.tianditu.gov.cn/img_w/wmts?tk=' + apiKey,
  layer: 'img',
  style: 'default',
  tileMatrixSetID: 'w',
  format: 'tiles',
  maximumLevel: 18
});

viewer.imageryLayers.addImageryProvider(imgProvider);
```

## 服务器负载均衡

使用多个服务器（t0-t7）分散请求：

```javascript
// 随机选择服务器
const servers = ['t0', 't1', 't2', 't3', 't4', 't5', 't6', 't7'];
const randomServer = servers[Math.floor(Math.random() * servers.length)];

const tileUrl = `http://${randomServer}.tianditu.gov.cn/vec_w/wmts?...&tk=${apiKey}`;
```

## 注意事项

1. **图层组合**：底图图层需配合对应注记图层使用
2. **投影匹配**：底图和注记的投影类型需一致（都用_w或都用_c）
3. **级别范围**：天地图瓦片支持1-18级
4. **服务器选择**：可使用t0-t7任意服务器，建议随机选择分散负载
5. **API密钥**：所有请求需要携带tk参数

## 常用瓦片模板

**Leaflet模板格式：**

```javascript
// 矢量地图模板
const vecTemplate = `http://t{s}.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${apiKey}`;

// 使用时替换{s}为服务器编号0-7
```

## 获取服务元数据

```bash
# 查询服务能力
curl "http://t0.tianditu.gov.cn/vec_w/wmts?request=GetCapabilities&service=wmts"
```