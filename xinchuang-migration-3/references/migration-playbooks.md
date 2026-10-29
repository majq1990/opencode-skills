# 信创迁移常见问题处理手册（精编版）

> 素材来源：demo redmine-assist 知识库（钉钉知识库文档全文 + Redmine 工单），2026-09-08 抽取整理。
> 完整原文见同目录 `key-docs-fulltext.md`（23 篇关键文档全文）。
> ⚠️ 处理前务必先按 `SKILL.md` 工作流用 /query 检索对应产品的最新工单与文档，本手册是高频共性问题速查。

---

## A. 通用原则（所有迁移场景）

1. **迁移前确认目标实例参数**（达梦官方要求，现场通常由达梦方建实例，需核对）：
   - 大小写敏感：**否**
   - 字符集编码：**UTF-8**
   - 长度以字符为单位：**是**（达梦 2024 年 Q2 后取消了该配置项，需在迁移时手动配置字符长度缩放，见 B.5）
   - 实例运行时区：**+8:00**
2. **迁移工具**：
   - →达梦：达梦官方「DM 数据迁移工具」（本机装达梦客户端自带）
   - →人大金仓：KDTS 迁移小工具（web 端 http://localhost:8080 或免安装版 :54523，kingbase/kingbase）
   - →海量：迁移工具+规则模板
3. **三张 changelog 表不迁移 / 迁移后清 MD5SUM**（几乎所有产品通用）：
   - `databasechangelog`、`databasechangeloglock`（星桥/毕升）、`admin_changelog`（用户中心）、`usercenter_remote_changelog`/`v22_changelog`/`workflow_center_changelog`（麒舰/智信云）
   - 迁移完成后执行 `UPDATE xxx SET MD5SUM = NULL; COMMIT;`（达梦每句要 commit）
4. **数据库迁移过程中保持大小写一致**（全行业等多系统联动的硬要求）。
5. **迁移后必须修改启动脚本/数据源连接**（驱动、URL、用户名密码、schema），详见各产品章节。

---

## B. MySQL → 达梦（DM8）

### 迁移步骤
1. 创建达梦实例并**切换 MySQL 兼容模式**后重启实例：
   ```sql
   SP_SET_PARA_VALUE(2,'COMPATIBLE_MODE',4); commit;
   SELECT VALUE FROM V$PARAMETER WHERE NAME = 'COMPATIBLE_MODE';  -- 4=MySQL模式
   ```
2. 创建用户（一般 `eurbanpro` / 星桥 `DEX` / 大数据中心 `DATACENTER` / 大数据中心1.0 `LAKE`）。
3. 达梦官方迁移工具，**勾选「保持对象名大小写」**；建议**分两步：先迁表结构、后迁数据**；增加 `double→double` 类型映射；勾选 `IDENTITY` 自增列（新版本达梦避免自增丢失）。
4. 迁移完成后：清 changelog MD5SUM（见 A.3）。
5. 修改启动脚本：
   ```
   --DATASOURCE_DRIVER=dm.jdbc.driver.DmDriver
   --DATASOURCE_URL=jdbc:dm://IP:端口?clobAsString=true
   --DATASOURCE_USERNAME=<用户>   --DATASOURCE_PASSWORD=<密码>
   ```
   灵珑另需启动参数：`--flagwind.mybatis.name-quote=-1`、`--egova.executor.stage.type=dm`
   星桥（达梦新版/空库启动）另需：`--egova.liquibase.dm.varchar.scaleFactor=4`
6. 授权（license 需重新申请）后重启服务。

### 高频报错与处理
| 报错/现象 | 处理 |
|---|---|
| Liquibase「Change failed validation / check sum 值不一致」 | 清 MD5SUM：`UPDATE <库>.databasechangelog SET MD5SUM=null`（全部）或 `where id='xxx'`（单条）；达梦注意每条后 `COMMIT` |
| char 字段内容自动补空格 | 将 char 转 varchar 并去掉空格（明镜专项脚本，见 key-docs-fulltext）：用 syscolumns/sysobjects 生成 `ALTER TABLE ... MODIFY ... VARCHAR(...)` 与 `UPDATE ... SET ... = RTRIM(...)` 两条 SQL 依次执行 |
| 建表报错时间默认值 `0000-00-00 00:00:00` | 用 `sysdate`（或具体时间）替换后执行建表语句 |
| 「记录超长」报错 | 右键报错表 → 设置【启用超长记录】→ 重新迁移数据 |
| 表已存在索引/约束报错 | 无需处理 |
| `-3243 表中不能同时包含聚集KEY和大字段` | 关闭默认聚簇索引（改数据库参数） |
| GROUP_CONCAT 不支持 | 改为 `WM_CONCAT`，或使用自定义函数 `@GROUP_CONCAT`（部分产品需联系研发） |
| 视图/列表/详情部件查询报错 | 检查「数据源」是否同一达梦库配了多个相同连接；数据源连接不能相同（可加后缀 `?test=1`），或 schema 大小写改小写 |
| 迁移后乱码 | 文件编码设置为 utf-8 |
| 星桥迁移后登录 401 | 大概率 `com_permission`、`com_schema` 表未正确迁移（部分 DM 迁移工具版本有 BUG 字段错位），重迁这两张表 |
| 迁移后首次刷新慢/查不到表 | 收集统计信息：`DBMS_STATS.GATHER_SCHEMA_STATS(...)`（达梦技术社区标准做法，见 key-docs-fulltext 星桥迁移达梦库步骤） |
| 用户中心 MIS_CALL_RECORD_HIS 表 id 自增 | 迁移后需将 id 改为非自增 |

---

## C. MySQL → 人大金仓（KingbaseES / KES）

### 迁移步骤
1. **前提：目标模式必须先装 postgis 扩展**（否则迁移找不到 geometry 类型）：
   - 现场联系金仓技术支持要配套包；公司环境版本 `postgis-3.1.2_X86_V008R006C008B0014.tar.gz`
   - 解压后把 bin/lib/share/extension 拷贝到金仓 Server 对应目录，再 `CREATE EXTENSION postgis;`
2. 用 **KDTS** 工具：先迁表结构、表数据、索引、视图；迁移失败的视图/函数用 sql 直接执行（金仓函数视图存储过程 sql）。
3. 数据源/迁移任务配置要点：
   - KES 目标库**兼容模式必须选 `ORACLE`**（PG 模式不支持大小写敏感，易迁移异常）；版本 V8R6
   - **MySQL BIT 类型必须映射为金仓 INT**（否则报错）；全部勾选数据类型
   - 大库可拆多个迁移任务；同一任务会覆盖前次结果
4. 迁移后（麒舰/智信云体系）：
   ```sql
   ALTER SYSTEM SET ora_input_emptystr_isnull = off;   -- 金仓把空字符串当 null，需关闭
   SELECT sys_reload_conf();
   -- 清 changelog md5sum
   update usercenter_remote_changelog set md5sum=null;
   update v22_changelog set md5sum=null;
   update workflow_center_changelog set md5sum=null;
   ```
5. 驱动/连接（星桥示例）：
   ```
   --DATASOURCE_DRIVER=org.postgresql.Driver
   --DATASOURCE_URL="jdbc:postgresql://IP:端口/data_exchange?currentSchema=data_exchange&stringtype=unspecified"
   ```
   （金仓驱动也可用 `com.kingbase8.Driver` + `jdbc:kingbase8://IP:54321/库名`）
6. 授权 license 后重启服务。

### 高频报错与处理
| 报错/现象 | 处理 |
|---|---|
| 找不到 geometry 类型 | 模式未装 postgis，安装后手动重迁失败的表 |
| date_format 函数不存在 | 兼容模式/语法差异，改等价函数或 sql 处理 |
| TIMESTAMP(0) 语法不兼容 | 建表语句 `TIMESTAMP(0)` 改 `TIMESTAMP` |
| 创建外键的表不存在 / 表数据迁移失败 | 先修复创建 `act_ge_bytearray`、`act_re_proedef` 等表，再建外键/重迁数据；只迁数据时模式选【表数据】 |
| bit 类型字段 | 迁移时映射为 int；迁移后检查：`SELECT ... FROM pg_attribute WHERE atttypid='bit'::regtype` |
| 空字符串变 null | 关闭 `ora_input_emptystr_isnull`（见上） |
| databasechangeloglock locked 列类型问题 | `ALTER TABLE dex.databasechangeloglock ALTER COLUMN locked TYPE boolean USING locked::integer::boolean;` |
| 人大金仓 sys_dump 无法直接执行 | 需进金仓目录 `/opt/Kingbase/ES/V8/Server/bin` 下执行；导出用 `-n 模式名 --no-owner --no-privileges` |

---

## D. MySQL → 瀚高（HighGo）

1. **迁移时关闭大小写敏感**，迁移后表字段全小写。
2. 迁移后启动报错常见原因：`disabled` 等字段是 **bit 类型**，而传参是 integer（HighGo 不支持 bit 与 integer 直接比较）。
   - 查 bit 字段：`SELECT ... FROM pg_attribute WHERE a.atttypid='bit'::regtype AND a.attnum>0`
   - 改类型：`ALTER TABLE <schema>.<table> ALTER COLUMN <col> TYPE smallint USING (<col>::int);`
3. 建自定义转换函数（sysdba 执行）：
   ```sql
   CREATE OR REPLACE FUNCTION public.bool2smallint(boolean) RETURNS smallint AS $$
   BEGIN RETURN CASE WHEN $1 THEN 1 ELSE 0 END; END; $$ LANGUAGE plpgsql IMMUTABLE STRICT;
   CREATE CAST (boolean AS smallint) WITH FUNCTION public.bool2smallint(boolean) AS ASSIGNMENT;
   ```
4. 参考文档：瀚高数据库迁移（Wiki：Mysql数据库迁移到瀚高数据库）。

---

## E. MySQL → 海量（Vastbase）

1. 迁移规则模板：
   - `datetime → timestamp`
   - `varchar(20) → varchar(50)`
   - `bit → boolean`
2. 连接（postgresql 协议）：
   ```
   --DATASOURCE_URL=jdbc:postgresql://IP:5444/库名?currentSchema=库名&stringtype=unspecified
   --DATASOURCE_DRIVER=org.postgresql.Driver
   ```
3. 迁移后修改灵珑数据源；清 changelog MD5SUM（排水等产品：`drainage_changelog`、`databasechangelog`、`usercenter_remote_databasechangelog` 三表）。
4. 注意：海量/瀚高同为 PG 系，bit、大小写、空串等 PG 共性问题同样适用。

---

## F. 各产品专项迁移

### 星桥（DEX）
- **版本门槛**：达梦需 ≥1.7.3.45；人大金仓需 ≥1.7.3.4-20250220（不满足先提交更新案件找测试蓝希鹏发包）
- 流程：①先建空库/空用户 → ②空库启动星桥生成 changelog → ③用迁移工具迁旧数据（**com_license、databasechangelog、databasechangeloglock 三表不迁移**，主键冲突选覆盖）→ ④license 授权 → ⑤重启
- 迁移后 401 / 表字段映射不全 → 检查 com_permission/com_schema 是否迁移正确

### 灵珑（LingLong）
- 灵珑 1.6.x 已合入达梦适配 MR；**灵珑库与应用库数据源类型必须保持一致**
- 灵珑平台是达梦、业务库是 MySQL 的场景：增加 `databaseType` 配置项
- 启动脚本需加 `--flagwind.mybatis.name-quote=-1`、`--egova.executor.stage.type=dm`
- 视图查询报错 → 数据源重复/schema 大小写问题（见 B 表）
- 升级路径：先升 1.6.0 基线，再按《V1.5升级V1.6适配工作清单》做信创迁移（先升 MySQL 再迁达梦更稳）

### 毕升（Becensus）
- 前提：已部署达梦/金仓/瀚高版本毕升微服务；按现场独立库（becensus）或智信云库创建用户
- 迁移前先确认《MySQL迁移达梦注意事项》字符长度问题；没问题则正常迁表+数据
- 达梦迁移工具要点：保持对象名大小写、double→double 映射、勾选 IDENTITY 自增
- FAQ：liquibase 报错 → 清 MD5SUM（全清 `UPDATE DATABASECHANGELOG SET MD5SUM=null` 或按 id）

### 明镜（elaw）
- 达梦：参考《明镜_数据库mysql迁移达梦》：驱动包用最新、保持对象名大小写、分两步（先表结构后数据）、char→varchar+去空格（见 B 表）
- 瀚高：参考《明镜_数据库mysql迁移瀚高》，关闭大小写敏感
- 信创环境部署：麒麟 V10-SP3 ARM（推荐）/X86 均已适配

### 用户中心 2.0
- 新部署：直接导入基准库（http://oneops.egova.com.cn:8093/one/benchbasedb/）后启动
- 存量迁移：从 mysql 迁表（**admin_changelog、databasechangeloglock 不迁移**）；迁移后收集统计信息（DBMS_STATS）
- 启动问题可能与版本有关 → 联系测试蓝希鹏

### 全行业一体化
- 数据库切换后**系统默认数据源还是 mysql** → 找不到表
- 处理：改 `ibility.colltable_data_source` 中 `id='self_datasource'` 的记录：
  - `type`: 0-mysql / 14-达梦
  - `url`: mysql `jdbc:mysql://...` / 达梦 `jdbc:dm://ip:port?clobAsString=true`
  - `status=1`、`disable=0`，改完重启全行业服务
- ⚠️ 迁移保持大小写一致

---

## G. 信创环境部署（麒麟/欧拉/UOS + CPU）

- **主推 OS**：银河麒麟 V10-SP3（ARM/X86 均适配，ARM 优先）、openEuler 22.03 LTS、统信 UOS
- **部署方式**：优先走一键部署脚本（Ansible 编排，麒舰/毕升/悟空/明镜/智信云均有）；手动部署仅备选
- **常见安装问题**：
  1. 包管理器差异（apt vs yum/dnf）装包失败
  2. 启动用户与文件夹权限不一致 → 后端服务异常
  3. MySQL/MariaDB 多版本共存不兼容
  4. nginx SSL 配置、安全组策略需手工调整
  5. 基础中间件需提前准备：JDK、MySQL、Redis、Nginx、Zookeeper、Kafka、Nacos
- **国产中间件**：东方通 TongWeb、金蝶 Apusic V10、宝兰德 v9.5、中创、通图（参考各产品适配文档）
- **国产 CPU**：鲲鹏/飞腾/海光（ARM）+ X86 已覆盖；国产化大模型 GLM4 部署依赖华为支持；PolarDB 可复用 MySQL 驱动

---

## H. 数据/附件/多媒体迁移（非数据库类）

- **MinIO 迁移方案**：服务器替换场景下 MinIO 文件数据迁移
- **MinIO→RustFS**：解决 MinIO 漏洞
- **批量迁移附件数据**：附件批量导入文件系统 + 附件与采集表关联两步走
- **PG 库 geom 位置字段**：迁移后如何从 geom 修复位置字段
- **Oracle→MySQL**：转换工具/方案见知识库

## I. 金蝶（Apusic）中间件

### 部署/打包
- 打包需额外增加 `aas` profile（测试打包 + 流水线打包均需）
- 特殊项目分支：`fjptcssmxaqgcjgpt-5105`（莆田生命线）
- 麒舰相关服务打包增加 aas

### License
- license.xml 路径通过 `-Dlicpath=` 指定，**必须放在 `-jar` 参数前**
- 示例：`-Dlicpath=/egova/apps/basic/eurbanpro/license.xml`
- test 环境可用公开 license：http://npm.egova.com.cn:18081/repository/custom-file/aas-license/license.xml
- **找不到 license.xml 服务会直接进程挂掉**；放在 jar 同级目录可不传参

### 验证
```shell
info.log | grep 'apusic'
```

### 常见报错
| 报错 | 处理 |
|---|---|
| 部署到 Apusic 后地理编码查询无结果 | web.xml 加 `useResponseEncoding=false` |
| 部署到 Apusic 后不能 i 查询 | 修改 `startapusic.cmd` 第 34 行加 `-Djavax.xml.transform.TransformerFactory=com.sun.org.apache.xalan.internal.xsltc.trax.TransformerFactoryImpl` |
| Apusic 部署工具打不开 | 要求 jre1.5+，修改 `dep.cmd` 第 28 行 javaw 路径 |
| 部署报只读 web.xml 错误 | 去掉 web.xml 只读属性 |
| 文档要求有且只有一个根元素 | web.xml 另存为 Unicode 编码 |
| 金蝶发布报错 / GIS 报错 / 登录空白 | 多为 license 路径或 aas profile 未加 |
| native 方法内存马攻击漏洞 | 域下 config/web.xml 去掉两处 SSIServlet 配置 |
| 金蝶进程卡死 / 发布失败 | 检查 license + aas 配置 |

## J. 东方通（TongWeb）中间件

### 部署配置
- 灵珑配置平台："Servlet容器类型"设置为 **"tongWeb"**
- license.dat 放在指定目录（"中间件license目录"为空时放灵珑平台部署目录）

### 常见问题
- GIS 中文乱码：参考 wiki 检查东方通中间件配置
- oneops 监控：jmx-exporter 需手动注入（东方通中间件添加方式不同，优先联系厂家支持）
- 性能测试案卷：中间件类型选"东方通"

### 与金蝶对比
|项 | 金蝶（Apusic） | 东方通（TongWeb） |
|---|---|---|
| license 文件 | license.xml | license.dat |
| Servlet容器类型 | aas | tongWeb |
| 验证日志 | `info.log \| grep 'apusic'` | info.log grep tongweb |
| 部署工具 | Apusic部署工具 | TongWeb 控制台 |

---

## 附：知识库检索兜底

- 本手册无法覆盖的个性化报错 → 按 SKILL.md 工作流调 `/query` 接口（多角度关键词），或直连 demo SQLite 精确检索
- **互联网搜索兜底**：以上均无结果时，用 `anysearch` / `websearch` 搜索（关键词：产品名 + "信创迁移"/"国产化"/"中间件" + 具体问题），补充厂商文档、最新方案或社区方案

### 各国产厂商官网与社区

| 厂商 | 官网 | 社区/文档 |
|---|---|---|
| 达梦 DM | https://www.dameng.com/ | https://eco.dameng.com/community/ |
| 人大金仓 KingbaseES | https://www.kingbase.com.cn/ | https://bbs.kingbase.com.cn/ / https://www.kingbase.com.cn/explore/ |
| 瀚高 HighGo | https://www.highgo.com/ | https://www.highgo.com/document/zh-cn/application/ |
| 海量 Vastbase | https://docs.vastdata.com.cn/ | https://opengauss.org/zh/user-practice/dbv/vastdata/ |
| 金蝶 Apusic | https://www.kingdee.com | https://www.kingdee.com/service |
| 东方通 TongWeb | https://www.tongweb.com.cn | https://www.tongweb.com.cn/service |

### 搜索示例
```
anysearch(query="金蝶Apusic中间件 国产化迁移 报错 解决方案")
anysearch(query="东方通TongWeb 中间件 信创部署 license配置")
anysearch(query="达梦DM8 迁移 报错 MD5SUM 清空 解决方案")
anysearch(query="人大金仓KingbaseES 迁移 空串 大小写 兼容")
anysearch(query="瀚高HighGo 迁移 兼容问题 解决方案")
anysearch(query="海量Vastbase 迁移 openGauss 适配")
```
