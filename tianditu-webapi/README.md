# 天地图 WebAPI Skill 使用说明

## Skill 已创建成功

天地图 WebAPI Skill 已经创建并安装到：
```
C:\Users\majq1\.config\opencode\skills\tianditu-webapi\
```

## 目录结构

```
tianditu-webapi/
├── SKILL.md                      # Skill 主文件
├── references/                   # API 参考文档
│   ├── map_service.md           # 地图瓦片服务
│   ├── search_service.md        # 地名搜索服务
│   ├── geocoding.md             # 地理编码服务
│   └── reverse_geocoding.md     # 逆地理编码服务
└── recipes/                      # 使用场景示例
│   ├── search_poi.md            # 关键词搜索POI
│   ├── nearby_search.md         # 周边搜索
│   ├── suggestion_search.md     # 建议词搜索
│   ├── reverse_geocoding.md     # 坐标转地址
│   ├── geocoding.md             # 地址转坐标
│   └── map_tiles.md             # 获取地图瓦片
```

## API 密钥配置

你的天地图API密钥已配置：
- **密钥**: `721342c3f30f7cb00b055428264ee911`
- **环境变量**: `TIANDITU_API_KEY`

### 配置方法

#### Windows PowerShell (永久配置)
```powershell
[Environment]::SetEnvironmentVariable("TIANDITU_API_KEY", "721342c3f30f7cb00b055428264ee911", "User")
```
重启终端后生效。

#### Windows PowerShell (临时配置)
```powershell
$env:TIANDITU_API_KEY="721342c3f30f7cb00b055428264ee911"
```

#### Linux/Mac
```bash
export TIANDITU_API_KEY="721342c3f30f7cb00b055428264ee911"
```

## API 测试结果

### ✅ 全部服务正常可用

**重要：天地图已升级到API v2.0版本！**

所有服务均可正常使用：

1. **地名搜索服务V2.0** ✅ - 关键词搜索、周边搜索、行政区划搜索
```bash
# 视野内搜索（queryType=2）
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'超市','level':'11','mapBound':'116.04577,39.70307,116.77361,40.09583','queryType':'2','count':'20','start':'0'}&type=query&tk=$TIANDITU_API_KEY"

# 周边搜索（queryType=3）
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'公园','queryRadius':'5000','pointLonlat':'116.48016,39.93136','queryType':'3','start':'0','count':'10'}&type=query&tk=$TIANDITU_API_KEY"
```

2. **逆地理编码服务** ✅ - 坐标转地址
```bash
curl "http://api.tianditu.gov.cn/geocoder?postStr={'lon':116.37304,'lat':39.92594,'ver':1}&type=geocode&tk=$TIANDITU_API_KEY"
```

3. **地图瓦片服务 (WMTS)** ✅ - 各类底图瓦片
```bash
curl "http://t0.tianditu.gov.cn/img_w/wmts?request=GetCapabilities&service=wmts"
```

### ⚠️ 已废弃的旧版API

**旧版API端点（已废弃）：**
- ❌ `http://api.tianditu.gov.cn/search` → 404错误

**新版API端点（正常使用）：**
- ✅ `http://api.tianditu.gov.cn/v2/search` → 正常工作

**原因：天地图已升级到v2.0版本，旧版API不再提供服务。你的API密钥权限是正常的！**

## Skill 更新说明

### 2026-04-01 重要更新

天地图API已升级到v2.0版本：
- ✅ 所有API端点已更新为 `/v2/search`
- ✅ 地名搜索服务参数已更新（新增queryType=12行政区划搜索）
- ✅ 周边搜索不再需要mapBound和level参数
- ✅ 你的API密钥权限正常，无需额外申请

### API版本对比

| 功能 | 旧版API（已废弃） | 新版API v2.0 |
|---|---|---|
| 地名搜索 | `/search` (404) | `/v2/search` ✅ |
| 搜索类型 | queryType=1,4,7 | queryType=2,3,10,12 |
| 周边搜索 | 需要mapBound+level | 只需queryRadius+pointLonlat |

## 使用 Skill 的方式

### 方式 1：直接调用 API（推荐）

使用新版API v2.0端点：

```bash
# 地名搜索（视野内搜索）
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'超市','level':'11','mapBound':'116.04577,39.70307,116.77361,40.09583','queryType':'2','count':'20','start':'0'}&type=query&tk=$TIANDITU_API_KEY"

# 周边搜索
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'公园','queryRadius':'5000','pointLonlat':'116.48016,39.93136','queryType':'3','start':'0','count':'10'}&type=query&tk=$TIANDITU_API_KEY"

# 行政区划搜索
curl "http://api.tianditu.gov.cn/v2/search?postStr={'keyWord':'商厦','queryType':'12','start':'0','count':'10','specify':'156110108'}&type=query&tk=$TIANDITU_API_KEY"

# 逆地理编码
curl "http://api.tianditu.gov.cn/geocoder?postStr={'lon':116.37304,'lat':39.92594,'ver':1}&type=geocode&tk=$TIANDITU_API_KEY"
```

### 方式 2：通过 Skill 调用

Skill 提供了详细的 API 参考和使用场景示例。当需要：
- 了解 API 参数详情 → 查看 `references/` 目录
- 实现特定功能场景 → 查看 `recipes/` 目录

### 方式 3：在代码中使用

参考 `recipes/` 目录中的示例，在项目中集成天地图服务。

## 常见用途

### 1. 坐标转地址（逆地理编码）

适用场景：
- 用户点击地图位置，显示地址信息
- GPS定位坐标转换为可读地址
- 显示当前位置的详细地址

### 2. 地图瓦片服务

适用场景：
- Web地图应用开发
- 在地图上显示不同类型的底图
- 构建自定义地图样式

支持的图层：
- **vec/cva**: 矢量地图 + 注记
- **img/cia**: 影像地图 + 注记
- **ter/cta**: 地形地图 + 注记
- **ibo**: 全球境界

### 3. 地址转坐标（地理编码）

通过地名搜索服务实现：
- 地址文本转换为坐标
- 地名定位到地图

### 4. 地名搜索（需要权限）

- 搜索特定类型的地点
- 在指定范围内搜索POI
- 建议词搜索

## 权限说明

**你的API密钥权限正常，无需额外申请！**

天地图控制台地址：http://console.tianditu.gov.cn/

如需查看或管理你的密钥：
1. 登录天地图控制台
2. 查看密钥权限状态
3. 管理API调用配额

## 技术支持

- 天地图官网: http://lbs.tianditu.gov.cn/
- API文档: http://lbs.tianditu.gov.cn/server/guide.html
- 控制台: http://console.tianditu.gov.cn/

## 更新日志

- 2026-04-01: **重要更新** - 天地图API升级到v2.0版本
  - ✅ 更新所有API端点为 `/v2/search`
  - ✅ 更新参数说明（新增queryType=12行政区划搜索）
  - ✅ 验证所有服务正常可用
  - ✅ 你的API密钥权限正常，无需额外申请
- 版本: 1.0.1
- 支持的服务: 地名搜索v2.0、逆地理编码、地图瓦片、地理编码、公交规划