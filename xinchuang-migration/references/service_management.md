# 服务管理手册（阶段六详解）

> 本文件是 SKILL.md 阶段六的详细展开。启停命令、domain 目录对照、日志路径均在此维护。

## 一、中间件应用（AAS 体系）

应用：eUrbanMIS（智信云）、eUrbanMF（市政服务）、eUrbanUMA（运管服）、eUrbanGIS（GIS）、eGovaMMS、eGovaPublic（市民通）、IMserver（即时通讯）

> **架构说明**：
> - **传统 Tomcat 拆分架构（V14 拆分后）**：市政服务对应 `eUrbanMF`
> - **微服务架构（一键部署 v2 / 信创部署）**：市政服务对应 `eUrbanFac`（V20）或 `fac`（V22）

```bash
# 启动（以 eUrbanMIS 为例，其他应用替换 domain 目录名）
cd /opt/AAS/domains/mydomain/bin
nohup ./startapusic > /dev/null &

# 停止
ps -ef | grep AAS
kill -9 进程号

# 查看进程
ps -ef | grep AAS

# 日志
cd /opt/AAS/domains/mydomain/logs
tail -fn 100 apusic.log.0
```

> **路径说明**：AAS 安装路径以现场实际为准，常见为 `/opt/AAS/` 或 `/egova/Apusic/`。
> 各应用对应的 domain 目录名：
> | 应用 | 中文名 | domain 目录示例 | 适用架构 |
> |------|------|----------------|---------|
> | eUrbanMIS | 智信云 | `mydomain` | 通用 |
> | eUrbanMF | 市政服务 | `mydomainMF` | Tomcat 拆分架构（V14 拆分后） |
> | eUrbanUMA | 运管服 | `mydomainUMA` | 通用 |
> | eUrbanGIS | GIS | `mydomain` | 通用 |
> | eGovaMMS | MMS | `mydomain` | 通用 |
> | eGovaPublic | 市民通 | `mydomain` | 通用 |
> | IMserver | 即时通讯 | `mydomainOR` | 通用 |
> | eUrbanFac | 市政微服务 | — | 微服务架构（V20） |
> | fac | 市政微服务 | — | 微服务架构（V22） |

## 二、基础产品（systemd 管理）

产品：linglong（灵珑）、wukong（悟空）、bigdata（星桥）、evaluation（毕升）、usercenter（用户中心）、xuanzang（玄奘）

```bash
service xxx status    # 查看状态
service xxx start     # 启动
service xxx stop      # 停止
service xxx restart   # 重启
```

> 服务名与实际产品名对照：`wukong`、`bigdata`、`linglong`、`usercenter`、`evaluation`、`xuanzang`

| 产品 | 服务名 | 进程查看 | 日志路径 |
|------|--------|---------|---------|
| wukong（悟空） | `wukong` | `ps -ef \| grep wukong` | `/egova/apps/basic/wukong/logs/wukong/web_logs/` |
| 星桥 | `bigdata` | `ps -ef \| grep bigdata` | `/egova/apps/basic/bigdata/logs/egova-bigdata-all/web_logs/` |
| 灵珑 | `linglong` | `ps -ef \| grep linglong` | `/egova/apps/basic/linglong/logs/linglong/web_logs/` |
| 用户中心 | `usercenter` | `ps -ef \| grep usercenter` | `/egova/apps/basic/usercenter/logs/egova-admin-service/web_logs/` |
| 毕升 | `evaluation` | `ps -ef \| grep evaluation` | `/egova/apps/basic/evaluation/logs/egova-service-stat/web_logs/` |
| 玄奘 | `xuanzang` | `ps -ef \| grep xuanzang` | `/egova/apps/gis/xuanzang/logs/web_logs/` |

## 三、脚本管理的服务

### wuneng（悟能）

```bash
cd /egova/apps/basic/wuneng
sh ./start.sh     # 启动
sh ./stop.sh      # 停止
sh ./restart.sh   # 重启
```

- 进程查看：无特定进程名（按应用特征查找）
- 日志：`/egova/apps/basic/wuneng/logs/wuneng/web_logs/`，查看 `wuneng.log`

### newplatform（新平台）

```bash
cd /egova/apps/basic/wuneng
sh ./start.sh     # 启动
sh ./stop.sh      # 停止
sh ./restart.sh   # 重启
```

- 进程查看：`ps -ef | grep newplatform`
- 日志：`/egova/web/newplatform/api/logs/egova-service-starter/web_logs/`，查看 `error.log`、`info.log`

### 采集服务 statgather（统计）

```bash
cd /egova/web/statgather
bash startStatGather.sh
```

- 日志：`/egova/web/statgather/log/`，查看 `stat-gather.log`

## 四、基础设施服务

### Kafka

```bash
service kafka status/start/stop
```

- 进程查看：`ps -ef | grep kafka`
- 日志：`/egova/kafka/logs/`，查看 `server.log`

### Zookeeper

```bash
service zookeeper status/start/stop
```

- 进程查看：`ps -ef | grep zookeeper`
- 日志：`/egova/log/zookeeper/`，查看 `zookeeper-egova-server-xxx.out`

### Redis

```bash
service redis status/stop/start
```

### Elasticsearch

```bash
# 启动
cd /egova/elasticsearch-7.17.8
./elasticsearch -d

# 停止
ps -ef | grep elasticsearch
kill -9 进程号
```

- 进程查看：`ps -ef | grep elasticsearch`
- 日志：`/egova/elasticsearch-7.17.8/logs/`，查看 `elasticsearch.log`

### Nacos

```bash
service nacos status/stop/start
```

- 进程查看：`ps -ef | grep nacos`
- 日志：`/egova/nacos/logs/`，查看 `nacos.log`（主运行日志）、`startup.log`（启动脚本日志）

### Eureka

```bash
systemctl daemon-reload
systemctl enable eureka  # 开机自启
service eureka restart
```

- 进程查看：`ps -ef | grep eureka`
- 日志：`/egova/apps/springcloud/eureka/logs/egova-eureka/web_logs/`，查看 `error.log`、`info.log`

### MinIO

```bash
service minio status/stop/start
```

- 进程查看：`ps -ef | grep minio`
- 日志：`/egova/minio/`，查看 `error.log`

## 五、其他业务服务

| 服务 | 启停命令 | 进程查看 | 日志路径 |
|------|---------|---------|---------|
| export | `service export start/stop/status` | `ps -ef \| grep export` | `/egova/apps/basic/export/logs/egova-service-export/web_logs/` |
| 车载服务 | `bash dm-start.sh start/stop/status` | `ps -ef \| grep egova-vehicle-service.jar` | `/egova/apps/sani-vehicle-v14/logs/web_logs/` |
| eUrbanFac（市政微服务 V20） | `service eUrbanFac status/stop/start` | `ps -ef \| grep eUrbanFac` | `/egova/apps/fac/eUrbanFac/logs/facilities-facv20-service/web_logs/` |
| fac（市政微服务 V22） | `service fac status/stop/start` | `ps -ef \| grep fac` | `/egova/apps/fac/fac/logs/facilities-facv22-service/web_logs/` |
| httpfileservice（多媒体） | `service httpfileservice status/stop/start` | `ps -ef \| grep httpfileservice` | `/egova/apps/basic/httpfileservice/logs/egova-httpfileserver-netty/web_logs/` |

> 各服务日志通用查看方式：`error.log` 为报错日志，`info.log` 为应用信息日志。
