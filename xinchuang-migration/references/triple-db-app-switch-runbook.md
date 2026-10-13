# 三组信创库切换 web 应用统一测试规程（2026-10-13 实测收官：达梦✅ 金仓✅ 瀚高⏸）

> 场景：数据已迁入信创库之后，把 eGova 产品 web 应用从 MySQL 切到信创库，逐组启动验证"系统可用"。
> 本规程来自 2026-10-13 真实双组实测：**达梦 DM8（cg155:5236）双应用 200 + 活会话实证；金仓 KES V009R001C010（容器 54321）双应用 200 + 31 活连接实证**；瀚高组物料（镜像+license）已就绪待补测。
> 前置拓扑：web 服务器与三组库的关系、jdbc 配置位置见 [site_profile.md](../config/site_profile.md) 与部署环境盘点。所有口令走远端 600 权限文件，不进命令行、不进入仓文件。

## 一、产品切换机制（先读懂再动手）

1. **webapp 的 jdbc 配置**在 `WEB-INF/classes/jdbc.properties`：
   - eUrbanGIS 用 `jdbc.*` 前缀键（主库）+ `geo.jdbc.*`（PG 空间库）+ `td.*`（TDengine）+ 独立的 `redis.properties`；
   - eGovaMMS 用 `mms.jdbc.*` 前缀键（mms 库）。
   切换只动主库块：`url / driverClassName / username / cryptogram / version / validationQuery`。
2. **驱动 jar 已随产品分发**：`DmJdbcDriver18-8.1.3.140.jar`（达梦）、`HgdbJdbc-6.2.3.jar`（瀚高）都在 WEB-INF/lib；**唯独没有 kingbase8**，需自行补（Maven Central `cn.com.kingbase:kingbase8:9.0.1`，字节码 major=52，JDK8 可用）。
3. **tomcat 必须 egova 用户跑**：产品打了 SecurityListener，root 启动会在 server.start 阶段被 `java.lang.Error` 杀掉，症状是"catalina.sh start 显示 Tomcat started 后几秒进程消失"。**启停一律走 systemd 单元**（tomcat-GIS / tomcat-MIS / tomcat-UMA / tomcat-other）。
4. **JSP 编译缺 JSTL**：eGovaMMS 发布包 174 个 jar 里没有 jstl，index.jsp 报 `ClassNotFoundException: org.apache.jsp.view.index_jsp`（Jasper 编译失败）。借同环境兄弟 webapp（eUrbanMIS/eGovaPublic/eUrbanUMA）的 `jakarta.servlet.jsp.jstl-1.2.6.jar` + `-api-1.2.7.jar` 补入 WEB-INF/lib。这是与 2026-10-10 演练机同款的**产品打包缺件**，每次部署新环境都要补。
5. **达梦实例大小写**：产品 liquibase 用**不带引号**标识符访问 `DATABASECHANGELOG` 等表。达梦实例若 `CASE_SENSITIVE=Y`（dminit 默认），表名是小写带引号的，历史表读成空 → 启动全量重放 changeset 撞主键（MigrationFailedException）。**面向产品的达梦实例必须 CASE_SENSITIVE=N**（引擎迁移用 Y/N 都行，产品只有 N 跑得通；2026-10-12 runbook 8.2 选 Y 的决策已修正）。改 N 无法在线改，需 dminit 重建 + 重迁（5589 表 335s）。

## 二、达梦组切换（已实证）

1. `systemctl stop tomcat-GIS`，备份两份 jdbc.properties（.bak.时间戳）。
2. eUrbanGIS：`jdbc:dm://<DM_HOST>:5236?schema=CGDB` + `dm.jdbc.driver.DmDriver` + 属主用户 + `jdbc.version=DM` + `validationQuery=select 1`；eGovaMMS 同理 `?schema=MMS`（mms.jdbc.* 键）。
3. 首启必见 `LiquibaseDatabaseInitException`，两种形态都要会认：
   - **MigrationFailedException**（重放撞主键）→ 根因是 CASE_SENSITIVE=Y（第五节）或历史表读不到；
   - **ValidationFailedException**（校验值清单）→ 正常现象：存量 changelog 的 MySQL 路径校验值 ≠ 达梦路径现值。
4. **校验值修复器 A1Fix**（官方 API，零手写 SQL）：`EXECUTED/RERAN 且校验值≠V9现值 → replaceChecksum`；`未登记且 dbms 适用 dm → setExecType(EXECUTED)`；MARK_RAN 与 mysql 专用 set 不动。本次实测 **47 replaceChecksum + 4 setExecType，与 2026-10-10 演练机分毫不差**（同一产品同一 changelog）。跑前先备份 `CREATE TABLE ...databasechangelog_bak... AS SELECT *`；跑后**另起进程复验**（history service 有进程内缓存）。
5. `systemctl start tomcat-GIS`，轮询 `curl /eUrbanGIS/ /eGovaMMS/`（404=上下文没起、000=端口没监听、200=就绪）。
6. **应用真在读库的证据**：达梦 `V$SESSIONS` 按 `curr_sch` 分组应看到 CGDB/MMS 两条 schema 的连接池会话，`clnt_ip` = web 服务器内网 IP。

## 三、金仓组切换（已实证）

1. **容器一键起**（本地 tar 或 registry）：金仓 V9 镜像自带试用授权，无需 license。
2. 数据迁移用 PG 系引擎（`scripts/pg/engine_mysql_to_pg.py.txt`）按 schema 迁入 `test` 库四个 schema（5589 表 0 失败）。
3. 补 kingbase8 驱动 + 改 jdbc.properties：`jdbc:kingbase8://127.0.0.1:54321/test?currentSchema=cgdb` + `com.kingbase8.Driver` + `jdbc.version=KINGBASE`。
4. **fork liquibase 无人认领 KingbaseES**：内置 DMDatabase（达梦）、PgSupportedHgDatabase（瀚高）、OscarDatabase（神通），唯独缺金仓——`DatabaseFactory` 警告 `Unknown database: KingbaseES` 后兜底 **UnsupportedDatabase**，它发出 Oracle 风格 `call current_schema`，金仓报 `syntax error at end of input`，应用必死。
5. **修法=桥接 jar**（1.8KB，`scripts/kingbase/KingbaseDatabase.java`）：继承 fork 的 `com.egova.liquibase.database.PostgresDatabase`，`isCorrectDatabaseImplementation` 认领产品名含 kingbase，**shortName 不覆写**（保持 `postgresql`，changelog 里 `dbms="postgresql"` 的 property 分支才能生效），打 `META-INF/services/liquibase.database.Database` 走 ServiceLoader 放进两个 webapp 的 WEB-INF/lib。
6. **校验值修复器 B1Fix**（同一规程金仓变体，URL `currentSchema=cgdb`）：本次实测 replaceChecksum=48。
7. 重启验证：双应用 30 秒内 200；金仓侧 `pg_stat_activity` 应见连接池会话（本次 31 条）。

## 四、瀚高组（物料就绪，流程=B组同款）

1. **容器**：`registry.highgo.com/hgdb/hgdb:9.0.5.1`（1.85G，registry 慢，下载约 40-60 分钟）；V9 镜像**硬性要求 license**：`-v <路径>/license.dat:/home/highgo/license/license.dat` 挂载（license 离线 zip 内 all_*.dat 改名而来，试用有效期至 2026-12-10）。env 是 `HGDB_PASSWORD`（不是 PASSWORD）。
2. fork 已内置 `PgSupportedHgDatabase` 认领瀚高 → **理论不需要桥接 jar**；驱动 HgdbJdbc-6.2.3 产品自带。
3. 迁移/校验值修复/切换验证与金仓组同款（URL `jdbc:hgdb://127.0.0.1:5866/highgo`，`jdbc.version=HIGHGO`）。

## 五、通用纪律

- **每组测完再修**：问题只记录不扩修（本轮 8 条问题全记录于台账）。
- **修复器三步纪律**：备份 databasechangelog → 修 → **另起进程复验 0 待修**。
- **恢复原状**：测试结束把 jdbc.properties 从 MySQL 备份恢复并重启，四 tomcat 全 active + 200 才算收口；信创配置以 .bak 存档供随时切回。
- 诚实口径：页面 200 + 数据库活会话 = "基础设施/数据源/数据三层可用"；**真实口令的登录业务流未跑**（无有效账号），不宣称端到端业务验证。
