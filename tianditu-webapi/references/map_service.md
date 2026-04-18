# 地图瓦片服务

天地图地图服务采用OGC WMTS标准，提供多种地图图层。

## 服务地址

### 底图图层

| 图层名称 | 说明 | 经纬度投影 (_c) | 球面墨卡托投影 (_w) |
|---|---|---|---|
| vec | 矢量底图 | `http://t0.tianditu.gov.cn/vec_c/wmts?tk={密钥}` | `http://t0.tianditu.gov.cn/vec_w/wmts?tk={密钥}` |
| img | 影像底图 | `http://t0.tianditu.gov.cn/img_c/wmts?tk={密钥}` | `http://t0.tianditu.gov.cn/img_w/wmts?tk={密钥}` |
| ter | 地形晕渲 | `http://t0.tianditu.gov.cn/ter_c/wmts?tk={密钥}` | `http://t0.tianditu.gov.cn/ter_w/wmts?tk={密钥}` |

### 注记图层

| 图层名称 | 说明 | 经纬度投影 (_c) | 球面墨卡托投影 (_w) |
|---|---|---|---|
| cva | 矢量注记 | `http://t0.tianditu.gov.cn/cva_c/wmts?tk={密钥}` | `http://t0.tianditu.gov.cn/cva_w/wmts?tk={密钥}` |
| cia | 影像注记 | `http://t0.tianditu.gov.cn/cia_c/wmts?tk={密钥}` | `http://t0.tianditu.gov.cn/cia_w/wmts?tk={密钥}` |
| cta | 地形注记 | `http://t0.tianditu.gov.cn/cta_c/wmts?tk={密钥}` | `http://t0.tianditu.gov.cn/cta_w/wmts?tk={密钥}` |

### 其他图层

| 图层名称 | 说明 | 经纬度投影 (_c) | 球面墨卡托投影 (_w) |
|---|---|---|---|
| ibo | 全球境界 | `http://t0.tianditu.gov.cn/ibo_c/wmts?tk={密钥}` | `http://t0.tianditu.gov.cn/ibo_w/wmts?tk={密钥}` |

## 请求参数

### GetCapabilities（元数据查询）

获取服务元数据，了解服务能力和参数范围。

**请求URL：**
```
http://t0.tianditu.gov.cn/{图层名}_w/wmts?request=GetCapabilities&service=wmts
```

**示例：**
```bash
curl "http://t0.tianditu.gov.cn/img_w/wmts?request=GetCapabilities&service=wmts"
```

### GetTile（瓦片获取）

获取指定位置的地图瓦片。

**请求URL：**
```
http://t0.tianditu.gov.cn/{图层名}_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER={图层}&STYLE=default&TILEMATRIXSET={投影}&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk={密钥}
```

**参数说明：**

| 参数 | 说明 | 取值范围 |
|---|---|---|
| SERVICE | 服务类型 | `WMTS` |
| REQUEST | 请求类型 | `GetTile` |
| VERSION | 版本号 | `1.0.0` |
| LAYER | 图层名称 | `vec`, `img`, `ter`, `cva`, `cia`, `cta`, `ibo` |
| STYLE | 样式 | `default` |
| TILEMATRIXSET | 投影类型 | `w`(墨卡托) 或 `c`(经纬度) |
| FORMAT | 格式 | `tiles` |
| TILEMATRIX | 级别(z) | 1-18 |
| TILEROW | 行号(y) | 根据级别计算 |
| TILECOL | 列号(x) | 根据级别计算 |
| tk | API密钥 | 必填 |

**示例：**
```bash
# 获取影像底图第12级，第3200行，第1600列的瓦片
curl "http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX=12&TILEROW=3200&TILECOL=1600&tk=$TIANDITU_API_KEY"
```

## 使用建议

1. **服务器负载均衡**：可使用 t0-t7 多个服务器随机选择，避免单一服务器负载过高
2. **投影选择**：
   - 球面墨卡托投影(_w)：适用于Web地图应用，与主流Web地图库兼容
   - 经纬度投影(_c)：适用于需要精确经纬度坐标的应用
3. **图层组合**：底图图层需配合注记图层使用，如 `img` + `cia`

## 常用组合示例

| 组合方式 | 适用场景 |
|---|---|
| `vec_w` + `cva_w` | 矢量地图（类似传统纸质地图风格） |
| `img_w` + `cia_w` | 卫星影像地图 |
| `ter_w` + `cta_w` | 地形地图 |
| `img_w` + `cia_w` + `ibo_w` | 卫星影像带境界线 |