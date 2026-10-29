# 三组信创库切换 web 应用统一测试规程（达梦✅ 金仓✅ 瀚高✅ 三组收官；2026-10-14 补厂商 changelog 与自增列三类缺陷）

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
6. **切换前先把全部应用和它们的每一处数据库引用列成清单**（这一步漏了就是本次最大的返工）：`server.xml` 里每个 `<Context>` 的 docBase、每个 webapp 的 `WEB-INF/classes/*.properties`、`settings`/`env` 外置配置、以及**同一个 tomcat 里挂的第二个应用**。本次 4 个 tomcat 实际挂了 6 个应用（tomcat-GIS=eUrbanGIS，tomcat-MIS=eUrbanMIS，tomcat-UMA=eUrbanUMA，tomcat-other=eGovaPublic + IMserver），其中 **tomcat-other 里还藏着一个 /IMserver**，只按 tomcat 数量数会漏。另一个坑：`eGovaPublic/WEB-INF/classes/liquibase-datasource.xml` 里 `liquibaseDataSource` 与 `liquibaseStatDataSource` **指向同一个库**（都用 `${biz.jdbc.*}`），日志里出现两次 `Reading from CGDB.DATABASECHANGELOG` 不是两个数据源，别被误导。
7. **`hibernate.dialect=MySQLDialect` 在三个已切库的 webapp 里都原样保留**——这是厂商系统性选择（ dialect 只影响 Hibernate 的 SQL 生成与限制，达梦/金仓/瀚高驱动各自兼容），不是漏改。已定性为记录项，不要去"修"。

## 二、达梦组切换（已实证）

1. `systemctl stop tomcat-GIS`，备份两份 jdbc.properties（.bak.时间戳）。
2. eUrbanGIS：`jdbc:dm://<DM_HOST>:5236?schema=CGDB` + `dm.jdbc.driver.DmDriver` + 属主用户 + `jdbc.version=DM` + `validationQuery=select 1`；eGovaMMS 同理 `?schema=MMS`（mms.jdbc.* 键）。
3. 首启必见 `LiquibaseDatabaseInitException`，两种形态都要会认：
   - **MigrationFailedException**（重放撞主键）→ 根因是 CASE_SENSITIVE=Y（第五节）或历史表读不到；
   - **ValidationFailedException**（校验值清单）→ 正常现象：存量 changelog 的 MySQL 路径校验值 ≠ 达梦路径现值。
4. **校验值修复器 A1Fix**（官方 API，零手写 SQL）：`EXECUTED/RERAN 且校验值≠V9现值 → replaceChecksum`；`未登记且 dbms 适用 dm → setExecType(EXECUTED)`；MARK_RAN 与 mysql 专用 set 不动。本次实测 **47 replaceChecksum + 4 setExecType，与 2026-10-10 演练机分毫不差**（同一产品同一 changelog）。跑前先备份 `CREATE TABLE ...databasechangelog_bak... AS SELECT *`；跑后**另起进程复验**（history service 有进程内缓存）。
5. `systemctl start tomcat-GIS`，轮询 `curl /eUrbanGIS/ /eGovaMMS/`（404=上下文没起、000=端口没监听、200=就绪）。
6. **应用真在读库的证据**：达梦 `V$SESSIONS` 按 `CURR_SCH`（**不是** `curr_schema`/`schemaname`，这两个列名在 DM8 上不存在，查了会报「无效的列名」）分组应看到各 schema 的连接池会话，`CLNT_IP` = web 服务器内网 IP。连接池空闲时 `SQL_TEXT` 只剩 `select 1` 心跳，**证明不了读库**；要看真实 SQL 得走 `V$SQL_HISTORY`——它没有 schema 列，与 `V$SESSIONS` 按 `SESS_ID`+`SESS_SEQ` 关联取 `CURR_SCH`。这是 eGovaPublic 实证的做法（EGOVAPUBLIC 1723 条真实执行，Hibernate 生成的 `pubcitysys0_.city_code ...` 与厂商 changeset 的 `COMMENT ON COLUMN` 都在）。

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

## 六、厂商 changelog 与自增列：三类缺陷（2026-10-14 eGovaPublic 实证）

前三类缺陷都在切 `eGovaPublic`（tomcat-other/18081，挂 EGOVAPUBLIC 库）时踩全，每类都有对应脚本，**不要用手改 XML / 手敲 DDL 的方式绕过去**——那样换个环境还得再踩一次。

### 缺陷类 1：`${schema.X}.序列` 空前缀 + 字面点多点

厂商 changelog 里 `select ${schema.dlsys_}.so_pub_city_module_config.nextval ...`。同库部署时 `schema.dlsys_` 解析成空串，属性后面那个**字面量点**变成前导点，达梦报「第 2 行, 第 20 列[.]附近出现错误」，context 起不来。实测 31 处，全在 `pubbase-ext-changelog-2021.xml`。

修法：`scripts/dm/lbpatch.py.txt` 的 `empty-prefix-dot` 规则。**规则是属性感知的**——先读 changelog 里该 `<property>` 的声明值，只有声明值为空串或以点结尾时那个字面点才是冗余的才删；属性值是别的内容（如 `EGOVAPUBLIC.`）时不动，否则会把 `EGOVAPUBLIC.so_x.nextval` 改成 `EGOVAPUBLICso_x.nextval`。

### 缺陷类 2：SQL Server 专有的 `SET IDENTITY_INSERT`

厂商把 `SET IDENTITY_INSERT tc_pub_city_module_config ON/OFF;` 写进了 `dbms="oracle"` 的 changeset（原意只在 SQL Server 路径生效）。MySQL 上 dbms 不匹配，这两句**从未执行过**；切到达梦后 egova fork 按 `OracleDatabase` 适配使 dbms 匹配，执行即报「表不存在IDENTITY列」。实测 12 处 = 6 个 changeset × ON/OFF，分布在 `pubbase-ext-changelog-2022.xml`（2）与 `-2023.xml`（10）。

修法：`scripts/dm/lbpatch.py.txt` 的 `sqlserver-identity-insert` 规则，整条删除、保留 INSERT 本体（这些 INSERT 走序列 nextval，本来就不需要显式插入开关）。**只删所属 changeSet 在目标库确实会执行的那些**，dbms 限定在别处的原样不动。

两个坑：
- **达梦被适配成 OracleDatabase，`db.getShortName()` 返回 `oracle` 不是 `dm`**。所以 `dbms="oracle"` 的 changeset 在达梦路径下同样生效，判 dbms 适用性必须用 `getShortName()`，绝不能写死字面量 `"dm"`。
- **入口 changelog 每次启动都会重新生成**：`EgovaLiquibaseListener.contextInitialized` → `searchAllDbChangeLog()` → `createLiquibaseEntryFile()` 两次，从 `template-changelog.xml` / `stat-template-changelog.xml` 生成 `main-1-db-changelog.xml` 与 `main-2-db-changelog.xml`。改 jar 里的 changelog 前先确认它不是启动时重建出来的。

### 缺陷类 3：MySQL `AUTO_INCREMENT` → 达梦 0 IDENTITY / 0 default

MySQL 侧 3312 个自增列（cgdb 3045 / public 151 / cgdbstat 75 / giscenter 38 / mms 3），迁到达梦后全是普通列。应用和厂商 changelog 都按"不给主键值就自动生成"写 SQL，到达梦就是 `ORA-01400: 违反列[id]非空约束`，context 起不来。

三种方案实测结论（都在达梦上真跑过）：

| 方案 | 不给值插入 | 显式给值插入 | 结论 |
|---|---|---|---|
| A 改列成 `IDENTITY` | 自增 | **失败** | 否决——厂商 changelog 有大量显式给主键的 INSERT，会连带炸一片 |
| B 列 `DEFAULT 序列.NEXTVAL` | 走序列 | 按给的走 | **采用** |
| C `BEFORE INSERT` 触发器+序列 | 同 B | 同 B | 否决——多一个 PL 对象、多一层编译失败风险，收益为零 |

修法：`scripts/dm/fix_autoincrement.py.txt`。三条硬结论：

1. **对已经是 IDENTITY 的列执行 ALTER 加 default 是静默无效的**——`data_default` 仍是 NULL，插入仍走 identity，**不报错**。所以修之前必须用 `dbms_metadata.get_ddl('TABLE', :t)` 识别 IDENTITY 列并跳过（DDL 里形如 `"id" INT IDENTITY(1, 1) NOT NULL`）。`user_tab_identity_cols` 这个 DM8 上没有，别去查。
2. **MySQL `information_schema.tables.auto_increment` 不是可靠的"下一个值"**。实测 `public.pub_encrypt_interface` 的 count=46、max(id)=46、auto_increment 也=46——拿它当种子会从 46 开始分配，直接撞已占用的主键。种子必须在目标库里实测：`GREATEST(max(列)+1, 源库 auto_increment, 1)`。
3. **Python 里不执行任何 DDL**。DDL 不能参数绑定，交给 `execute()` 就是把注入面交给静态分析看不出来的地方；脚本只读库 + 生成可人工过目的 `.sql`，由操作人用 disql 跑。这也符合本 skill「变更 SQL 先展示后执行」的硬规则。种子测算写成 PL 块内的 `GREATEST(...)`，让库自己算，Python 侧只做标识符白名单 + 生成结果整句语法校验三道闸。

多库跑必须给 `--dm-pw-map "用户=口令文件,..."`：各 schema 属主口令通常不同，只给一个 `--dm-pw-file` 等于用同一个口令连所有用户。

2026-10-14 实测：五个库 3312 列全补，`ALTER` 全部成功、零数据变动，复扫"需要补 default 的列 = 0"、"种子不足（max ≥ 序列 last_number）的列 = 0"。

### 切换后必须做的两项收尾复验

1. **厂商 changelog 自己也会 INSERT 显式主键**：eGovaPublic 启动后 `pub_encrypt_interface` 从 46 行涨到 53 行、`tc_pub_city_module_config` 灌到 516 行——这正是缺陷类 2 修好后 changeset 真正跑起来的证据。行数比源库多不是丢数据，是厂商 changeset 补灌。
2. **清理自己的诊断残留**：排查过程中造的实验表/序列/行（本人本次留过 `zt_ai_*` 三表两序列、`tc_pub_city_module_config` 里 module_id=538 的诊断行）必须在收口前删掉，否则会变成"目标库多出对象"的假性不一致。
