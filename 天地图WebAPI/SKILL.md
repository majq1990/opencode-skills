---
name: tianditu-webapi
description: 天地图 Web服务API 开发指南。在编写、审查或调试使用天地图WebAPI的代码时应运用此技能，也适用于直接调用天地图API获取结果的场景。涵盖：地名搜索、逆地理编码、地理编码、行政区划查询、地图瓦片服务、公交规划等。当用户提及天地图、国家地理信息公共服务平台、坐标转换、地名查询、行政区划等需求时自动触发。
license: MIT
version: 1.0.0
homepage: http://lbs.tianditu.gov.cn
repository: http://lbs.tianditu.gov.cn
metadata:
  openclaw:
    requires:
      bins: ["curl"]
      env: TIANDITU_API_KEY
    primaryEnv: TIANDITU_API_KEY
---

# 天地图 Web服务API 开发指南

天地图是国家地理信息公共服务平台，提供各类地理信息数据服务的HTTP/HTTPS接口。包含地名搜索、地理编码、逆地理编码、行政区划查询、地图瓦片服务等核心模块的API说明和代码示例。

## 何时适用

遇到以下任意场景时，均应读取本指南并调用对应API：

### 地名与POI搜索
- 搜索特定关键词的地点（如"超市"、"银行"）
- 在指定视野范围内搜索地点
- 在指定坐标周边搜索POI
- 在矩形区域内拉框搜索
- 输入联想/地名建议词搜索
- 纯地名搜索（不包含公交线路）

### 地址与坐标转换
- 经纬度坐标解析为地址信息（逆地理编码）
- 地址文本解析为经纬度坐标（地理编码）

### 行政区划查询
- 查询行政区划信息
- 获取行政区划边界

### 地图瓦片服务
- 获取矢量底图瓦片
- 获取影像底图瓦片
- 获取地形晕渲瓦片
- 获取各类注记图层瓦片
- 获取全球境界图层

### 公交规划
- 公交线路查询
- 公交站点查询

## 开发准则

在使用本技能的任何场景中，请遵守以下通用准则：

### 准则 1：API 端点

天地图API服务端点：

| 服务类型 | Base URL | 说明 |
|---|---|---|
| **地名搜索服务V2.0** | `http://api.tianditu.gov.cn/v2/search` | 地名搜索、POI检索（新版API） |
| **地理编码服务** | `http://api.tianditu.gov.cn/geocoder` | 地理编码、逆地理编码 |
| **行政区划服务** | `http://api.tianditu.gov.cn/v2/search` | 行政区划查询（使用queryType=12） |
| **地图瓦片服务** | `http://t[0-7].tianditu.gov.cn/[图层名]/wmts` | WMTS标准地图瓦片 |
| **公交规划服务** | `http://api.tianditu.gov.cn/transit` | 公交线路规划 |

**使用规则：**
- 所有请求需要携带 `tk` 参数（API密钥）
- 地名搜索服务必须使用 **v2.0版本** 端点 `/v2/search`（旧版 `/search` 已废弃）
- 地图瓦片服务支持 t0-t7 多个服务器，可随机选择以分散负载

### 准则 2：API Key 安全处理

API Key是使用服务的必须参数：

1. 优先读取环境变量 `TIANDITU_API_KEY` 中的密钥
2. 若环境变量为空，提示用户：**请前往[天地图官网](http://lbs.tianditu.gov.cn/home.html)申请Key**
3. 设置环境变量：
```bash
# Windows PowerShell
$env:TIANDITU_API_KEY="您的天地图API密钥"
# 或永久设置（需要重启终端生效）
[Environment]::SetEnvironmentVariable("TIANDITU_API_KEY", "您的天地图API密钥", "User")

# Linux/Mac
export TIANDITU_API_KEY="您的天地图API密钥"
```
4. 调用API时使用 `$TIANDITU_API_KEY`，示例：
```bash
curl "http://api.tianditu.gov.cn/search?postStr={...}&type=query&tk=$TIANDITU_API_KEY"
```

### 准则 3：坐标系统

天地图使用 **CGCS2000坐标系**（国家大地坐标系），与WGS84坐标系基本兼容：
- 经度范围：-180 至 180
- 纬度范围：-90 至 90
- 格式：`lon,lat`（经度在前，纬度在后）

### 准则 4：JSON参数处理

天地图API的 `postStr` 参数需要传递JSON字符串：
- 使用单引号包裹JSON字符串（URL中双引号需要转义）
- 或使用URL编码方式传递JSON参数

---

## 场景示例（推荐优先阅读）

遇到以下场景时，**优先使用对应recipe**，内含完整调用链、参数说明和可运行代码示例。

### 地名搜索

| recipe 文件 | 适用场景 |
|---|---|
| `recipes/search_poi.md` | 关键词搜索地点信息 |
| `recipes/nearby_search.md` | 在指定坐标周边搜索POI |
| `recipes/suggestion_search.md` | 输入建议词/地名联想 |

### 地址与坐标

| recipe 文件 | 适用场景 |
|---|---|
| `recipes/reverse_geocoding.md` | 坐标转详细地址 |
| `recipes/geocoding.md` | 地址转坐标 |

### 地图服务

| recipe 文件 | 适用场景 |
|---|---|
| `recipes/map_tiles.md` | 获取各类地图瓦片URL |

---

## 快速参考

### 地图服务

- `references/map_service.md` - 地图瓦片服务：各类底图和注记图层

### 地名搜索

- `references/search_service.md` - 地名搜索服务：普通搜索、视野内搜索、周边搜索等

### 地址编码

- `references/geocoding.md` - 地理编码：地址转坐标
- `references/reverse_geocoding.md` - 逆地理编码：坐标转地址

## 如何使用

**推荐决策路径**：
1. 用户需求是**多步串联场景**（如"搜索附近银行"、"坐标转地址"）→ 直接找 `recipes/` 目录下对应recipe
2. 用户需求是**单个API的参数细节**（如"这个接口的 queryType 参数有哪些值"）→ 查阅 `references/` 目录

每个 **references** 参考文件包含：
- 功能简要说明
- API参数说明和注意事项
- 请求示例和响应格式

每个 **recipes** 场景包含：
- 触发意图（什么场景适用）
- 完整调用链与分步说明
- 常见错误和变体