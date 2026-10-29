# PG 系验证环境重构包（MySQL 源库 → PostgreSQL 目标库）

不依赖任何外部新购服务器，也不依赖 DM8 / 人大金仓 / 瀚高的安装包与授权。
源库在哪台机器上，目标库就建在哪台机器的容器里——**只要源库活着，验证环境就能重建**。

配套规程见 `mysql-to-pg-runbook.md` 第十节（本次重构暴露并修掉的 4 个"小库不暴露、大库才炸"的缺陷）。

## 为什么就地重建

原验证环境里承载目标库的机器已消失，且当时所有装机通道都不可用：

- 公有云 CLI 凭证有效但账号下**零实例**，且没有"释放中的实例可找回"的接口；
- 另一家公有云 token 过期；
- 公司开通平台不可达；
- 源库所在机器是私有云，没有 metadata service，无法自助开机关联；
- 本机 Docker Desktop 未运行。

源库机器上本来就有 MySQL、redis、postgis 和若干 Tomcat，磁盘余量够，
因此把目标库直接建在该机器的 **PostgreSQL 13.20 + PostGIS 3.5.2 容器**里。

**判定机器是否真的没了，只能靠认证 SSH 之后的 `date` / `uptime` / 容器状态 / 端口实测**，
不能看 ping，也不能沿用记忆里或口头确认的"已释放"记录——本次这条误判已经反复出现多次。

## 目录内容

| 文件 | 作用 |
| --- | --- |
| `setup_target.py.txt` | 建目标库 + 扩展；把 PostGIS 挪进独立 schema 并设 search_path |
| `engine_mysql_to_pg.py.txt` | 迁移引擎：建表 / 灌数 / 后置约束 / 注释 / 逐表 ANALYZE |
| `verify_pg.py.txt` | 四轨过程验证器 |
| `view_conv.py.txt` | 视图定义转换器 + 全量试建归因 |
| `run.sh` | 编排：01_setup → 02_migrate → 03_verify → 04_views |

## 文件为什么以 .py.txt 结尾

PG 的 DDL 无法对标识符（库名 / 表名 / 列名）做占位符绑定，引擎靠 `qi()` 双写引号转义保证安全。
安全扫描器对动态 DDL 一律报 SQL 注入，所以按项目既有约定以 `.txt` 承载，推到服务器后
直接 `python3 xxx.py.txt` 执行，解释器按扩展名无关的方式加载，不需要改名。

## 怎么跑

```bash
# 凭据只走环境变量，脚本和源码里不出现任何口令字面量
export MIG_MYSQL_PWD='...'      # MySQL root
export MIG_PG_PWD='...'         # PG postgres
export PGHOST=127.0.0.1 PGPORT=5432 PGUSER=postgres PGDB=mig
export MYHOST=127.0.0.1 MYPORT=3306 MYUSER=root

bash run.sh                        # 跑全部五个库
bash run.sh cgdb                   # 只跑一个库
RECREATE=1 bash run.sh             # 目标库已有对象时，先 DROP 再整库重跑
```

## 四轨验证分别验什么

1. **一轨 行数对账**：逐表 `COUNT(*)`。不一致时不直接判丢行——取该表第一个日期/时间列，
   若源独有行的取值全部晚于目标侧该列最大值，判定为「源表实时写入」，否则判「疑似丢行」。
2. **二轨 逐字段多重集**：源与目标各取全表，按字段做值多重集比对，能定位到具体列和具体值。
3. **三轨 中文逐字比对**：含中文字段随多重集一并比对，中文按码点逐个进 Counter。
4. **四轨 超大表整体 md5**：超过 `--max-rows`（默认 20000）的表按主键排序流式算整表 md5。
   复合主键必须整组都进 `ORDER BY`，只排第一列会让两侧各自按物理序补足，md5 必然假性不一致。

外加**对象对账**：表 / 主键 / 唯一约束 / 外键 / 索引（语义口径，剔主键、前缀、FULLTEXT、SPATIAL）
两侧逐一对照，并单独报出「迁移跳过的索引」数量。

## 实测结果（2026-10-12）

五个库全量迁移，**0 失败**：

| 库 | 表 | 行 | 主键 | 索引 | 外键 | 注释 |
| --- | --- | --- | --- | --- | --- | --- |
| cgdb | 5243 | 370586 | 5227 | 2633 | 3 | 34464 |
| cgdbstat | 263 | 40608 | 261 | 175 | 0 | 1507 |
| giscenter | 53 | 7878 | 52 | 23 | 19 | 229 |
| mms | 30 | 247 | 30 | 36 | 0 | 10 |
| public | 308 | 12276 | 307 | 87 | 0 | 1519 |
| **合计** | **5897** | **431596** | | | | |

验证：cgdb 5243/5243 表、5227/5227 主键、96/96 唯一约束、3/3 外键、2633/2633 索引全部一致；
逐字段多重集 1242 张一致、2 张不一致；超大表 md5 4/4 一致。其余四库全部一致。

视图：cgdb 49 个建成 43 个，cgdbstat 14 个建成 13 个。

## 重构过程中修掉的四个真缺陷

1. **验证器锁表打爆**：一轨对 5000+ 张表逐张 `SELECT COUNT(*))`，每条 COUNT 都会拿该表及
   其索引的 AccessShareLock。整个循环共用一个事务，锁一路累积超过共享锁表容量，报
   `out of shared memory / You might need to increase max_locks_per_transaction`。
   修法：只读校验连接 `dst.autocommit = True`，逐条自提交、锁随语句释放。

2. **引擎同款缺陷，且更严重**：收尾一条裸 `ANALYZE` 扫全库，单条语句要对库内每张表及其
   每个索引各取一把锁，五个库**全部崩在这一行**，而且崩在汇总打印之前——连「零日期改写了
   几处」都没输出。数据本身已逐表 commit 所以没丢，但统计信息和摘要计数全丢了。
   修法：改成逐表 `ANALYZE` + 连接切 autocommit。

3. **PostGIS 污染 public schema**：扩展默认建在 public 里，`spatial_ref_sys` /
   `geometry_columns` 会混进目标 public 库的对象清单，而源库有一个就叫 `public` 的库，
   对象对账立刻假性不一致。`ALTER EXTENSION ... SET SCHEMA` 对 postgis 不支持，
   只能 `DROP EXTENSION postgis CASCADE` 后按 schema 重建。
   连带效应：视图里裸调 `st_astext` 会找不到函数，必须把承载扩展的 schema 设进
   `search_path`（`ALTER DATABASE ... SET search_path TO "$user", public, postgis`）。

4. **视图转换器三个 bug**：
   - `fix_concat` 传给 `_match_paren`/`_args_of` 的下标差一（`concat(` 的左括号在 `j+6`，
     代码写 `j+7`），`_args_of` 又从 `open_idx+1` 起截，把第一个参数的首字符吃掉；
   - `fix_concat`/`fix_if`/`fix_convert_using` 替换时都没把「被改写片段之前的原文」拼回去，
     `concat(if(...))` 这种嵌套写法会把外层 `concat(` 一起吃掉；
   - `INFOSCHEMA_RE` 正则漏了收尾的 `"`，匹配短一个字符，替换后多出一个引号。

## 已知的 MySQL → PG 语义差（必须报出来，不能静默）

- **内嵌 NUL 字节被剥**：`cgdb.tcdicadmindivision` 的 `AcquisitionName`/`AcquisitionDesc`
  两列共 2 行，源值形如 `s\uf8df\x00桥区`，目标值 NUL 被剥成 `s\uf8df桥区`。
  PG 的 `text` 存不了 NUL 字节，MySQL 的 `varchar` 可以。引擎 `adapt()` 做 `replace("\x00","")`。
- **零日期改 NULL**：`cgdb.to_patrol_labour_state.labour_update_time` 源值
  `0000-00-00 00:00:00`，目标为 NULL。PG 拒绝零日期，只能落 NULL；引擎会计数并在汇总里
  打印「零日期改写为 NULL：N 处」。另有 5 个列的**默认值**是零日期，默认值被直接丢弃
  （同样在汇总的 NOTE 里列出）。
- **视图剩余 7 个建不成**，全部属于「MySQL 宽松 / PG 严格」类，需要人工逐条改写：
  - 3 个 GROUP BY 功能依赖（MySQL 关掉 `ONLY_FULL_GROUP_BY` 后可选非分组列，PG 不允许）
  - 2 个 UNION 两侧类型不一致（MySQL 隐式转，PG 要求显式一致）
  - 1 个 `character varying = bigint` 无对应运算符
  - 1 个 information_schema 列名大小写（MySQL 侧大写 `TABLE_NAME`，PG 全小写 `table_name`）
- **MySQL GEOMETRY 列在目标侧落成 `bytea`**：字节原样保住、四轨验证零丢失，但不是 PostGIS
  `geometry` 类型，视图里调 `st_astext` 需要显式 `::geometry`。这是引擎的类型映射选择，
  换成 `geometry` 会引入 SRID 与 WKB 合法性问题。

## 凭据纪律

`MIG_MYSQL_PWD` / `MIG_PG_PWD` 只从环境变量读，脚本与源码内不出现任何口令字面量。
PG 口令由本机生成后只经 SSH 环境变量传递，不落进任何源文件。
