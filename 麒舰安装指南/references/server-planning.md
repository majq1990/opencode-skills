# 服务器规划建议

## 一、三种部署模式对比

| 维度 | 一站式 | 分布式 | 轻量化 |
|---|---|---|---|
| **服务器数量** | 1 台 | 多台（3-10+） | 1 台 |
| **安装组件** | 全部 | 全部（按角色分配） | 仅核心组件 |
| **适用场景** | 演示/测试/小型项目 | 生产环境 | 资源受限/边缘节点 |
| **数据库** | 单机 | 支持主从 | 单机 |
| **性能** | 一般 | 高（可横向扩展） | 基础 |
| **运维复杂度** | 低 | 中高 | 低 |

## 二、项目规模与部署模式推荐

### 区县级项目
- **推荐**: 一站式 或 分布式（2-3 台）
- 服务器: 8U32G 起步
- 磁盘 IO: ≥ 100 MB/s
- 网络: ≥ 500 Mbps

### 一般地市级项目
- **推荐**: 分布式（4-6 台）
- 数据库服务器: 16U64G+
- 应用服务器: 8U32G+
- 磁盘 IO: ≥ 300 MB/s
- 网络: ≥ 1000 Mbps

### 中心城市/市区一体化
- **推荐**: 分布式（6-10 台）
- 数据库服务器: 32U128G+
- 应用服务器: 16U64G+
- 磁盘 IO: ≥ 500 MB/s
- 网络: ≥ 1000 Mbps

## 三、分布式部署服务器角色规划

### 3.1 标准角色分配（multi_server.yml）

分布式部署中，每台服务器可承担一个或多个角色。角色在 `multi_server.yml` 中定义：

| 角色键名 | 角色名称 | 说明 | 推荐配置 |
|---|---|---|---|
| `ip_web_main` | 主 Web 服务 | 智信云前端入口 | 8U32G+ |
| `ip_web_mis` | MIS 服务 | 一网统管 | 8U32G+，支持从节点 |
| `ip_web_face_server` | 人脸服务 | AI 人脸识别 | 8U32G+，GPU 可选 |
| `ip_web_uma` | UMA 服务 | 统一认证 | 4U16G |
| `ip_web_sg` | 城市运管服 | 运管服务 | 8U32G |
| `ip_web_gis` | GIS 服务 | 地图服务 | 8U32G+ |
| `ip_web_gisserver` | GIS Server | GIS 后端 | 8U32G |
| `ip_db_biz` | 业务数据库 | 核心业务数据 | 16U64G+，SSD |
| `ip_db_stat` | 统计数据库 | 统计分析数据 | 16U64G+，SSD |
| `ip_db_redis` | Redis 缓存 | 会话/缓存 | 8U32G |
| `ip_db_tdengine` | TDengine | 时序数据库 | 8U32G |
| `ip_db_tdengine_3` | TDengine3 | 新版时序数据库 | 8U32G |
| `ip_mq_kafka` | Kafka 消息队列 | 消息中间件 | 8U32G |
| `ip_mw_nacos` | Nacos | 服务注册/配置中心 | 4U16G |
| `ip_mw_zookeeper` | Zookeeper | 协调服务 | 4U16G |
| `ip_storage_minio` | MinIO | 对象存储 | 8U32G，大磁盘 |
| `ip_es` | Elasticsearch | 搜索引擎 | 16U64G |
| `ip_nginx_main` | 出口 Nginx | 反向代理/负载均衡 | 4U16G |

### 3.2 最小化 3 台部署方案

```
服务器A (16U64G SSD): 数据库角色
  - 业务数据库 (ip_db_biz)
  - 统计数据库 (ip_db_stat)
  - Redis (ip_db_redis)

服务器B (16U64G): 应用 + 中间件
  - 主 Web (ip_web_main)
  - MIS (ip_web_mis)
  - Nacos (ip_mw_nacos)
  - Zookeeper (ip_mw_zookeeper)
  - 出口 Nginx (ip_nginx_main)

服务器C (8U32G): 存储 + 搜索
  - MinIO (ip_storage_minio)
  - Elasticsearch (ip_es)
  - Kafka (ip_mq_kafka)
  - TDengine (ip_db_tdengine)
```

### 3.3 标准 5 台部署方案

```
服务器A (16U64G SSD): 数据库
  - 业务数据库 (ip_db_biz)
  - Redis (ip_db_redis)

服务器B (16U64G SSD): 统计 + 搜索
  - 统计数据库 (ip_db_stat)
  - Elasticsearch (ip_es)

服务器C (8U32G): 中间件
  - Nacos (ip_mw_nacos)
  - Zookeeper (ip_mw_zookeeper)
  - Kafka (ip_mq_kafka)
  - TDengine (ip_db_tdengine)

服务器D (16U64G): 应用服务
  - 主 Web (ip_web_main)
  - MIS (ip_web_mis)
  - UMA (ip_web_uma)

服务器E (8U32G): 存储 + 代理
  - MinIO (ip_storage_minio)
  - 出口 Nginx (ip_nginx_main)
```

## 四、数据库主从规划

### 4.1 什么时候需要主从？

- **单机部署（一站式/轻量化）**: 不需要
- **高可用要求**: 需要配置从节点
- 读写分离场景: 需要从节点 + Cetus 代理

### 4.2 主从约束规则

1. **业务库和统计库主节点不能在同一台服务器**
2. **一个从库不能同时属于多个主库**（不能既是业务从库又是统计从库）
3. **从库不能和对方的主库在同一台机器**（如业务从库不能和统计主库同机）
4. **TDengine 和 TDengine3 不能在同一台服务器**

### 4.3 Cetus 数据库代理

当配置了数据库从节点时，系统自动判断是否需要安装 Cetus 代理：

| 场景 | 业务代理 | 统计代理 |
|---|---|---|
| 业务库有从节点 | 安装 | - |
| 统计库有从节点 | - | 安装 |
| 两个都有从节点 | 安装 | 安装 |
| 都没有从节点 | 不安装 | 不安装 |

安装后，微服务会自动连接 Cetus 代理而非直连 MySQL。

## 五、特殊场景

### 5.1 MIS 有从节点时
- 人脸服务 (`ip_web_face_server`) **必须** 装在 MIS 的从节点上
- 系统会自动校验，不满足时会报错

### 5.2 GIS 服务
- GIS Server (`ip_web_gisserver`) 需要从已配置的 GIS 节点中选择
- 必须先配置 GIS 主节点 (`ip_web_gis`)

### 5.3 RDS 云数据库场景
- 使用菜单选项 `2` 中的 `a`（增加 IP 地址）仅添加数据库 IP
- 不执行 SSH 免密（因为无法 SSH 到云数据库）
- 数据库连接信息在微服务部署时通过依赖配置录入
