# Tomcat 应用层切换达梦作业规程（2026-10-10 真实切换实证）

> 本规程来自一次真实的应用层切换：eGova 体系 GIS/MMS 两个 webapp 原本跑在 MySQL + Tomcat 上，
> 数据库已由 `mysql-to-dm-runbook.md` 迁到达梦 DM8，本次只改应用侧配置、**不改一行代码**，
> 把 Tomcat 上的应用切到达梦并起到可用状态。文中所有结论均为实跑结论，非推断。
>
> 数据迁移见 `mysql-to-dm-runbook.md`（达梦）与 `mysql-to-pg-runbook.md`（金仓/瀚高）。
> 本文只写"数据已经迁完之后，应用怎么切过去、怎么验、出问题怎么定位"。
> 所有 IP/端口/口令均为占位符，执行时替换为现场值（SKILL.md 停止条件 3）。

## 一、适用范围与"三层做实"的验收口径

适用：Tomcat 承载的 eGova webapp（Spring MVC / Struts / JSP 混编），源 MySQL、目标 DM8，
**代码零改动**。

**验收必须分层说，不能一句"都正常"糊过去**。本次最终口径：

| 层 | 判据 | 本次实测 |
|---|---|---|
| 基础设施层 | 进程活着、端口在听、静态资源 200 | Tomcat 以 systemd 托管，`{{HTTP_PORT}}` 在听，两个 webapp 上下文均启动完成，静态资源全 200 |
| 数据源层 | 连接池指向 DM、有活会话、校验查询在跑 | DM 侧 `v$sessions` 看到该应用用户的活会话，`SQL_TEXT` 正是连接池配置的 `validation.query`（`select 1`） |
| 数据层 | 迁移后的业务表能查到、行数符合迁移对账 | 抽查多张业务表有数据，行数与迁移对账结果一致 |
| 业务流程层 | 端到端跑通一个真实业务动作 | **本次只做到"读库链路打通"，没做到"成功登录"**——原因见第七节，不能宣称已跑通 |

**结论纪律**：可以说"基础设施/数据源/数据三层做实"，不能说"系统全部功能正常"。
差的那一层要单独点出来，写清楚缺什么、为什么补不上。

## 二、切换清单（零代码改动前提下的六项）

按顺序逐项做，每项做完留一份可回滚的备份：

1. **停应用**：`systemctl stop {{TOMCAT_SERVICE}}`，确认进程真的退出（`ps -eo pid,args | grep '[t]omcat'`）
2. **备份应用配置目录**：把 `{{WEB_DIR}}/<webapp>/WEB-INF/classes/` 整个打包留底，回滚就是解压回去
3. **改 JDBC URL**：`jdbc.properties` 里 `jdbc:mysql://...` → `jdbc:dm://{{DM_HOST}}:{{DM_PORT}}`
   （需要指定模式时带 `?schema={{DM_SCHEMA}}`）
4. **换驱动 jar**：`WEB-INF/lib/` 放入达梦 JDBC 驱动（`DmJdbcDriver18.jar` 对应 JDK8），
   **MySQL 驱动 jar 建议改名 `.disabled` 而不是删除**——回滚时改个名字就回去
5. **核对 Hibernate 方言**：这是最容易漏的一项。**方言 jar 必须与 Hibernate 主版本匹配**：
   Hibernate 4.x 用 `DmDialect-for-hibernate-4.0.jar`；Hibernate 5.3 的变体要改名 `.disabled`，
   否则两个方言 jar 同时在 classpath 上会按加载顺序命中错的那个，症状是"连上了但 SQL 语法报错"
6. **起应用并盯日志**：`systemctl start {{TOMCAT_SERVICE}}`，立刻跟日志（日志位置见第五节）

**切换前的两个预检**（本次两个真问题都该在这一步拦住，见第八节）：

```bash
# 预检 1：changelog 里有没有"到达梦就空执行"的 changeset
python scripts/check_liquibase_dm_coverage.py --jar {{WEB_DIR}}/<webapp>/WEB-INF/lib/<app>.jar --strict

# 预检 2：DM 侧那份配置文件的键，是不是比源库侧那份全
python scripts/check_props_coverage.py --base conf/MYSQLV14.properties --target conf/DM.properties --strict
```

## 三、启动期硬 blocker：`LiquibaseDatabaseInitException`

**现象**：改完配置一起应用，上下文启动直接抛
`cn.com.egova.base.datasource.EgovaLiquibaseListener` → `LiquibaseDatabaseInitException`，
整个 webapp 起不来，端口上静态资源都 404。

**根因不是"MD5 该不该置空"，而是 dbms 属性过滤**：

- eGova 产品的 liquibase changelog（打包在 `WEB-INF/lib/<app>.jar` 里的
  `gis-db-changelog.xml`，本次 8171 行 / 498 个 changeset）中，大量 `<sql>` 节点只写了
  `dbms="mysql"` 或 `dbms="oracle"` 分支
- MySQL 路径下这些语句照常执行，`databasechangelog` 里存的是**那条路径算出来的校验值**
- 切到达梦后这些语句被 dbms 过滤成**空**，Liquibase 仍然把它们登记进 `databasechangelog`，
  并用**空内容重算校验值**——与库里的原值全部 mismatch
- 于是"已登记但校验值不符"的 changeset 一次性全部爆出来（本次 47 个）

> 通用速查表里"迁移后 `update databasechangelog set MD5SUM = NULL`"这条，对**单纯校验值不一致**
> 有效；对**这种批量 dbms 过滤导致的 mismatch** 不够——它会把校验值抹掉，但抹不掉"未登记的
> changeset 会被真执行"的风险（见下）。

**另一个更危险的点**：未登记的 changeset 一旦真跑，可能执行你绝不希望它执行的语句。
本次 4 个未登记 changeset 里就带 `drop identity` 之类的 DDL——在已经迁完数据的库上跑一次，
后果不是报错，是数据没了。**所以不能"先让它跑起来再说"。**

## 四、修法：走官方 API，零手写 SQL 改 `databasechangelog`

正确解法是不碰表、不写 UPDATE/DELETE，全部调 Liquibase 官方 API：

| 场景 | API | 语义 |
|---|---|---|
| 已登记、只是校验值在达梦路径下变了 | `AbstractChangeLogHistoryService.replaceChecksum(ChangeSet)` | 把库里存的校验值刷新成当前路径算出的现值 |
| 库里有数据但 changelog 从没登记过 | `Liquibase.markNextChangeSetRan(Contexts, LabelExpression)` | 标记为已执行，**不会真去执行**（本 fork 写 `exectype=EXECUTED`） |

本次实跑：47 个 `replaceChecksum` + 4 个 `markNextChangeSetRan`，
`databasechangelog` 从 28883 行到 28887 行，复验 0 不一致、0 未登记。

**为什么不用 SQL 手改**：`update databasechangelog set MD5SUM=...` 看起来等价，但
① 你得先知道达梦路径下重算出来的校验值是多少（手算不出来，只能让 Liquibase 自己算）；
② 未登记的行用 INSERT 造一条，`EXECTYPE`/`ORDEREXECUTED`/`DATEEXECUTED` 这些字段的语义
很容易造错，下次启动照样报；
③ 属主、权限、事务边界都可能踩坑。**官方 API 是把"算什么、怎么写、写什么字段"都封装对的唯一路径。**

## 五、两个必须知道的坑

### 坑 1：`getRanChangeSets()` 在 service 内有缓存，同进程复验读到陈旧数据

本 fork 的 `getRanChangeSets()` 结果缓存在 service 内部：`replaceChecksum()` 会调 `reset()`，
但 `markNextChangeSetRan()` **不会**。所以写完立刻在同进程里复验，会读到修复前的旧快照，
看起来像"没生效"。

**纪律：修复后的复验必须另起一个进程**（或重启 JVM 后再验）。本次就是靠另起进程复验，
才确认 28887 行、0 不一致。

### 坑 2：Tomcat 日志是按日期分文件的，没有 `catalina.out`

`logs/` 下是 `catalina.<YYYY-MM-DD>.log`、`catalina.<YYYY-MM-DD>.out`、
`localhost.<YYYY-MM-DD>.log`、`localhost_access_log.<YYYY-MM-DD>.txt`。
跨天排错时"昨天的日志"在另一个文件名里，`tail -f catalina.out` 会直接报文件不存在。
`ls -lt logs/ | head` 先看当天文件名，再 `tail -f` 对应的那个。

## 六、诊断路径：起不来 / 页面 404

```
应用切库后异常
├── 上下文起不来（启动抛异常、webapp 全部 404）
│   ├── LiquibaseDatabaseInitException → 第三节：dbms 过滤导致校验值 mismatch
│   │   ├── 已登记 + 校验值不符 → replaceChecksum
│   │   └── 未登记 + changelog 要执行危险 DDL → markNextChangeSetRan（绝不放它真跑）
│   ├── Invalid username/password; logon denied → 口令/用户未授权，核对 jdbc.properties
│   ├── Schema does not exist → 模式未建，或 URL 少带 ?schema=
│   ├── Cannot load JDBC driver → 驱动 jar 没放进 WEB-INF/lib
│   ├── Connection refused / Network adapter → DM 服务没起、端口没放行
│   └── SQL 语法报错但连接正常 → 方言 jar 与 Hibernate 主版本不匹配（第二节第 5 项）
└── 上下文起来了，但某个页面 404 / JSP 报错
    ├── JSTL 相关（c:url / c:forEach 报 "Unable to find taglib" 或类似）
    │   └── 发布打包缺件：整个机器上没有任何 JSTL 实现 jar
    │       → 从 maven 中央仓取 javax.servlet:jstl:<version>，校验 c.tld 的 uri 正是应用要的那个
    │       → 按同级 jar 对齐属主/权限装入 WEB-INF/lib，重启后确认报错归零
    └── 静态资源 404 → 先确认 docBase/path 在 server.xml 里的映射，再查文件是否真的在
```

**JSTL 这一类的判定要点（本次实证）**：`index.jsp` 只有一句 `<c:url>`，但全系统
（两个 webapp 的 lib + tomcat/lib 共 379 个 jar）**没有一个 JSTL 实现**；
且该 jsp 的 mtime 是 2023-04-18、日志目录只有当天的文件——说明这是**当年发布打包就缺件**，
与切库无关。**装之前先做这个判定**，否则很容易把"发布缺件"错记成"迁移引入的缺陷"，
进而去做一堆无效的回滚。

### 探针自伤归因（排错时必做）

定位过程中自己发的请求也会在日志里留下同类报错。本次 4 条
`NullPointerException at URLDecoder.decode → LoginController`，
其中 **2 条的时间戳早于我首次介入**——证明是应用缺判空的预存缺陷，不是迁移引入；
另外 2 条是我自己 21:49 发的一条缺参数请求造出来的同源 NPE。

**纪律：看到可疑报错先看时间戳，再决定它是不是你造成的。** 自触发的报错不计入迁移缺陷，
但必须说出来，不能悄悄算了。

## 七、验证方法论：怎么证明"应用真的在读迁移后的库"

"页面能打开"只证明 Tomcat 把 JSP 渲染出来了，**不证明它读了库**。
本次踩过这个坑：`LoginController` 读的是 `oauth.properties` 文件而不是数据库，
所以"登录页能打开"完全不能说明连库成功。

按代价从低到高四步，每步都要能给出可核验的证据：

| 步 | 方法 | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| 1 | HTTP 探活：对多个端点 `curl -w '%{http_code}'` | 上下文起来了、静态资源在 | 完全不涉及库 |
| 2 | 连接池活会话：DM 侧 `v$sessions` 按应用用户分组，看 `SQL_TEXT` | 应用真的连上了 DM、校验查询在跑 | 有没有执行业务 SQL |
| 3 | **业务 SQL 前后对比**：抓 `v$sql_history` 的 `max(seq_no)` 作基线 → 触发一个业务动作 → 只看 `seq_no > 基线` 的新行 | **应用确实执行了哪条业务 SQL**（本次抓到 `select * from tc_human where user_name = ? and valid_flag = 1 and delete_flag = 0`，`command_type=7` 即 SELECT、参数化） | SQL 命中了哪几行 |
| 4 | 端到端业务动作 | 全链路通 | —— |

**第 3 步是本规程最可复用的一招**：不要试图用 `AFFECTED_ROWS` 证明 SELECT 命中了几行——
DM8 里 SELECT 的 `affected_rows` 恒为 0，这个字段对查询没有意义。前后对比 `seq_no` 才是干净的做法。

**本次第 4 步的诚实缺口**：没有跑通"成功登录"。SM2 登录契约（前端取公钥 → 加 8 字节盐 →
`sm2.doEncrypt(msg, key, 1)` C1C2C3 模式 → POST `username`/`pwd` 两个密文字段）已逆清，
并用**迁移后 `tc_human` 里的真实用户名 + 故意错误的口令**打过去，
应用稳定返回 `{"data":{},"message":"用户名或密码错误","success":false}` HTTP 200——
这一步证明了 SM2 解密、控制器、DAO、达梦读库全通。
但应用对"用户存在"和"用户不存在"返回**完全相同**的报文，没有有效口令就无法再往前一步。
**不爆破、不绕过鉴权**，这一层就停在这里，明确记为未验证。

## 八、产品侧缺口（迁移前就该修的两件事）

本次切换暴露出两个**产品自身**的缺口，都不是迁移工具的问题，但都会在切换时变成阻塞。
**建议在迁移启动前就处理掉**，不要等到应用起不来再救火。

1. **changelog 缺 `dbms="dm"` 分支**：本次 498 个 changeset 里有 47 个的 SQL 只在
   mysql/oracle 路径下生效，到达梦被过滤成空——这就是第三节那个硬 blocker 的根。
   预防工具：`scripts/check_liquibase_dm_coverage.py`（只读解析，不连库不执行 SQL），
   跑出来有 NOOP/SKIP 就说明启动时会撞校验值问题。
   **根治是给这些 changeset 补 `dbms="dm"` 分支**，让达梦路径下真的执行该执行的东西，
   而不是每次现场都去刷校验值。

2. **DM 侧配置文件键不全**：`conf/DM.properties` 比 `conf/MYSQLV14.properties`
   **少 15 个键**，另有 28 个键两侧值不同。缺键不报错，只让应用在对应分支拿到空值，
   症状是"能启动、某个页面或某个查询不正常"，极难定位。
   预防工具：`scripts/check_props_coverage.py`（只读，默认只打印键名不打印值，
   避免凭据落进共享日志）。

## 九、关键数字与回滚

- 切换本身：停应用 → 改配置 → 起应用，应用侧零代码改动；启动耗时约 48s
- 修复：47 个 `replaceChecksum` + 4 个 `markNextChangeSetRan`，`databasechangelog`
  28883 → 28887 行，另起进程复验 0 不一致、0 未登记
- 终态证据：重启后仅剩 Hibernate `HHH000362` 良性告警（方言/二级缓存提示，非错误）；
  DM 侧两个应用用户各 20 条活会话共 40 条；业务表抽查有数据；HTTP 端点全 200
- JSTL 补件：`javax.servlet:jstl:<version>`（约 414KB，290 个 standard 实现类），
  装入前先建**基线清单**（原 lib 下全部 jar 名 + md5），**回滚 = 删掉这一个 jar**

**回滚模式**：应用侧改动全部是"配置文件 + jar 增删"，天然可逆——
`jdbc.properties` 换回备份、驱动 jar 改回名、方言 jar 换回、删掉新装的 jar，重启即回 MySQL。
**不要在没做第二节第 2 步备份的情况下去改配置。**
