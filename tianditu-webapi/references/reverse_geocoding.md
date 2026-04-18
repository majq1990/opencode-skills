# 逆地理编码服务

将坐标点（经纬度）转换为结构化的地址信息。

## 请求地址

```
http://api.tianditu.gov.cn/geocoder?postStr={JSON参数}&type=geocode&tk={密钥}
```

## 请求参数

postStr需要传递JSON字符串格式的参数：

| 参数 | 说明 | 类型 | 必填 | 取值范围 |
|---|---|---|---|---|
| lon | 坐标的x值（经度） | Double | 是 | -180 至 180 |
| lat | 坐标的y值（纬度） | Double | 是 | -90 至 90 |
| ver | 接口版本 | Int | 是 | 1 |

## 请求示例

```bash
# 将坐标116.37304,39.92594转换为地址
curl "http://api.tianditu.gov.cn/geocoder?postStr={'lon':116.37304,'lat':39.92594,'ver':1}&type=geocode&tk=$TIANDITU_API_KEY"
```

## 响应参数

### 基础响应

| 参数 | 说明 | 类型 | 返回条件 |
|---|---|---|---|
| result | 响应具体信息 | Json | 有结果时返回 |
| status | 状态 | String | 必返回（0:正确, 1:错误, 404:出错） |
| msg | 响应信息 | String | 必返回（OK:有信息） |

### result 对象

| 参数 | 说明 | 类型 |
|---|---|---|
| addressComponent | 此点具体信息（分类） | Json |
| formatted_address | 详细地址 | String |
| location | 此点坐标 | Json |

### addressComponent 对象

| 参数 | 说明 | 类型 |
|---|---|---|
| address | 此点最近地点信息 | String |
| address_distince | 距离最近地点的距离 | Int |
| address_position | 在最近地点的方向 | String |
| city | 所在城市/区县 | String |
| poi | 距离最近的POI点 | String |
| poi_distince | 距离最近POI点的距离 | Int |
| poi_position | 在最近POI点的方向 | String |
| road | 距离最近的路 | String |
| road_distince | 距离最近路的距离 | Int |

### location 对象

| 参数 | 说明 | 类型 |
|---|---|---|
| lon | 坐标x值（经度） | Double |
| lat | 坐标y值（纬度） | Double |

## 响应示例

```json
{
  "status": "0",
  "msg": "OK",
  "result": {
    "formatted_address": "北京市海淀区中关村",
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

## 注意事项

1. **坐标格式**：使用CGCS2000坐标系（lon,lat格式）
2. **版本参数**：ver参数目前固定为1
3. **JSON格式**：postStr使用单引号包裹JSON字符串
4. **精度**：返回的地址信息包含最近的地点、POI、道路等信息及距离