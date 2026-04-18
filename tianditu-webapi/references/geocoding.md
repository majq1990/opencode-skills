# 地理编码服务

将地址文本转换为经纬度坐标。

## 说明

地理编码服务与地名搜索服务配合使用。通过地名搜索获取POI的坐标信息。

## 使用方式

1. 使用地名搜索服务搜索地址关键词
2. 从返回的POI结果中获取 `lonlat` 字段即为坐标

## 示例

```bash
# 搜索"北京市海淀区中关村"获取坐标
curl "http://api.tianditu.gov.cn/search?postStr={'keyWord':'中关村','level':'11','mapBound':'116.04577,39.70307,116.77361,40.09583','queryType':'1','count':'1','start':'0'}&type=query&tk=$TIANDITU_API_KEY"
```

返回结果中的 `pois[0].lonlat` 即为坐标。

## 注意事项

1. **地址精度**：结构化地址（含门牌号）可获得更精确的坐标
2. **搜索范围**：通过mapBound参数限制搜索范围可提高结果精度
3. **行政区码**：使用specifyAdminCode参数指定行政区可获得更准确的结果
4. **参考文档**：详细参数请查阅 `references/search_service.md`