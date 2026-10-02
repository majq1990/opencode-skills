# 信创迁移操作流程

> 本文件包含完整的迁移命令、SQL 语句和配置参数，按阶段组织。

## 1. 前期准备

### 1.1 服务器 DNS 解析检查

```bash
ping oneops.egova.com.cn
```

- 能解析：直接使用一键部署脚本 `dl_v2.sh`
- 不能解析：修改 `/etc/hosts`，添加（前提是能访问 {{ONEOPS_IP}}）：
```
{{ONEOPS_IP}} oneops.egova.com.cn
```
- **备选方案**：如果服务器完全无法访问公司地址，找一台能联网的服务器执行一键部署脚本下载所有产品包，然后上传到新服务器。

### 1.2 服务器版本兼容性检查

```bash
cat /etc/os-release
cat /etc/os-version
```

确认系统版本后，执行一键部署脚本选择对应版本。统信 1060e 满足要求。

### 1.3 老服务器产品版本评估

联系各产品测试人员评估升级需求。建议：先迁移老服务器产品到新服务器，再在新服务器上升级，避免影响老系统运行。

---

## 2. 达梦数据库部署

### 2.1 创建 dmdba 用户

```bash
# 创建用户组
groupadd dinstall -g 2002

# 如果创建不了组，执行以下命令解锁系统文件
chattr -i /etc/group
chattr -i /etc/gshadow
chattr -i /etc/passwd
chattr -i /etc/shadow
chmod 644 /etc/group
chmod 640 /etc/gshadow
chmod 644 /etc/passwd
chmod 600 /etc/shadow
chown root:root /etc/group
chown root:root /etc/gshadow
chown root:root /etc/passwd
chown root:root /etc/shadow

# 创建用户
useradd -G dinstall -m -d /home/dmdba -s /bin/bash -u 2002 dmdba

# 修改密码
passwd dmdba
```

### 2.2 修改文件打开最大数

编辑 `/etc/security/limits.conf`，末尾添加：

```
dmdba  soft    nice       0
dmdba  hard    nice       0
dmdba  soft    as         unlimited
dmdba  hard    as         unlimited
dmdba  soft    fsize      unlimited
dmdba  hard    fsize      unlimited
dmdba  soft    nproc      65536
dmdba  hard    nproc      65536
dmdba  soft    nofile     65536
dmdba  hard    nofile     65536
dmdba  soft    core       unlimited
dmdba  hard    core       unlimited
dmdba  soft    data       unlimited
dmdba  hard    data       unlimited
```

修改后重启服务器生效。验证：
```bash
su - dmdba
ulimit -a
```

### 2.3 目录规划与权限

```bash
# 创建目录
mkdir -p /egova/dmdata/data
mkdir -p /egova/dmdata/arch
mkdir -p /egova/dmdata/dmbak
mkdir -p /egova/log/dm

# 修改属主
chown -R dmdba:dinstall /egova/dmdata/data
chown -R dmdba:dinstall /egova/dmdata/arch
chown -R dmdba:dinstall /egova/dmdata/dmbak
chown -R dmdba:dinstall /egova/log/dm

# 设置权限
chmod -R 755 /egova/dmdata/data
chmod -R 755 /egova/dmdata/arch
chmod -R 755 /egova/dmdata/dmbak
```

### 2.4 安装达梦

```bash
# 挂载镜像
cd /opt
mkdir -p /mnt && mount -o loop dm8_20251202_x86_centos6_64.iso /mnt

# 命令行安装
su - dmdba
cd /mnt
./DMInstall.bin -i
```

### 2.5 初始化实例

```bash
su - dmdba
cd /egova/dmdata/data/bin
./dminit
```

### 2.6 注册服务

```bash
su - root
cd /egova/dmdata/data/script/root
./dm_service_installer.sh -t dmserver -dm_ini /egova/dmdata/data/dm.ini -p DLMIS
```

### 2.7 启动/停止服务

```bash
systemctl status DmServiceDLMIS.service
systemctl start DmServiceDLMIS.service
systemctl stop DmServiceDLMIS.service
```

---

## 3. 金蝶10（AAS）部署

### 3.1 安装

```bash
# 解压安装包
unzip AAS-V10.0.8-SP11-EE-20251205.zip -d /egova/Apusic

# 替换 license 文件
# 进入 ass 目录，将厂家发的 license 内容复制到 license.xml
cd /egova/Apusic/ApusicAS/aas/
```

### 3.2 启动/停止

```bash
cd /egova/Apusic/ApusicAS/aas/bin
./asadmin start-domain      # 启动
./asadmin stop-domain        # 停止
./asadmin list-domains       # 查看域状态
```

管理控制台地址：`https://ip:6848/`

### 3.3 配置步骤

1. 配置 JDBC 连接池（资源类型 java.sql.Driver，上传 JDBC 驱动包）
2. 创建独立实例
3. 创建 JDBC 资源
4. 部署应用（上传 war 包或选择应用目录，填写上下文路径，选择目标实例）
5. 启动实例中的应用

### 3.4 端口配置

创建实例后端口默认分配。如需修改：管理控制台 → 配置管理 → 找到对应实例 → 系统属性 → 修改端口值，修改后需重启实例。

### 3.5 查看日志

金蝶管理控制台查看应用日志：
1. 点击「独立实例」
2. 点进对应「服务器」
3. 点击「查看原始日志」

---

## 4. MySQL 替换为达梦

### 4.0 迁移前评估（必做）

迁移前必须记录源库基线数据，用于迁移后校验。

#### 统计源库对象数量

```sql
-- MySQL 中执行：统计表数量
SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema = 'cgdb';

-- 统计视图数量
SELECT COUNT(*) AS view_count FROM information_schema.views WHERE table_schema = 'cgdb';
```

#### 记录关键表数据量

```sql
-- MySQL 中执行：记录各表行数
SELECT table_name, table_rows FROM information_schema.tables 
WHERE table_schema = 'cgdb' AND table_type = 'BASE TABLE' ORDER BY table_rows DESC;
```

#### 确认字符集

```sql
-- 查看源库字符集
SELECT default_character_set_name FROM information_schema.schemata WHERE schema_name = 'cgdb';

-- 如果是 GBK 字符集迁移到 UTF8 达梦库，需在迁移工具中设置字段长度扩展倍数
```

### 4.1 数据迁移报错处理

报错"非法的基类名 SYSGEO2"时：

```sql
-- 检查达梦是否存在 sysgeo/sysgeo2 模式
-- 执行以下语句开启空间包
SP_INIT_GEO_SYS(1);    -- 基础空间包
SP_INIT_GEO2_SYS(1);   -- 扩展空间包（解决当前报错）
```

如果执行报错，联系达梦厂商建立这两个模式。

### 4.2 迁移前置操作

#### 本地安装达梦迁移工具

参考达梦官方文档，下载达梦数据库自带迁移工具。

#### 设置自定义类型映射

在迁移工具的"数据类型映射"中，MySQL -> DM：
- `DOUBLE` -> `DOUBLE`
- `GEOMETRY` -> `SYSGEO.ST_GEOMETRY`
- `POINT` -> `SYSGEO.ST_POINT`

迁移时不勾选"使用默认数据类型映射关系"，优先使用自定义映射。

### 4.3 迁移操作流程

1. 新增迁移，最大保留次数改为 -1
2. 填写数据库信息（驱动可从服务器 `/egova/web/eUrbanxxx/WEB-INF/lib` 下载）
3. 勾选"创建模式和表"，其他不勾
4. 选择所有表
5. 随便选一条数据，点击转换，按提示操作
6. 开始执行迁移

### 4.4 迁移后验证（必做）

迁移完成后，必须对比源库和目标库的数据一致性。

#### 对比对象数量

```sql
-- 达梦中执行：统计表数量
SELECT COUNT(*) FROM all_tables WHERE owner = 'DLMIS';

-- 对比视图、存储过程等
SELECT object_type, COUNT(*) FROM all_objects WHERE owner = 'DLMIS' GROUP BY object_type ORDER BY 1;
```

与迁移前 4.0 节记录的源库数量对比，不一致时排查遗漏对象。

#### 校验关键表数据量

```sql
-- 达梦中执行：抽查关键表行数
SELECT COUNT(*) FROM DLMIS.table_name;
-- 与源库记录的 table_rows 对比
```

#### 置空 MD5

```sql
-- 每个产品库都要执行
update databasechangelog set MD5SUM = NULL;
commit;
```

#### 应用启动验证

启动应用后检查日志，确认无数据库连接报错、无 SQL 语法错误。

### 4.5 迁移后 SQL 调优

达梦 CBO 统计信息策略与 MySQL/Oracle 不同，迁移后建议执行：

```sql
-- 手动收集统计信息（替换模式名）
CALL DBMS_STATS.GATHER_SCHEMA_STATS('DLMIS', 100, TRUE, 'FOR ALL COLUMNS SIZE AUTO');
```

- 关注慢查询，必要时通过 HINT 调整执行计划
- 建立性能基线对比，确保核心查询响应时间不低于迁移前 95%
- 批量导入场景建议关闭外键检查，采用直接路径加载，完成后重建索引

---

## 5. 各产品迁移详细参数

### 5.0 产品依赖关系与迁移顺序

迁移时必须按依赖顺序执行，被依赖的库必须先完成创建和迁移：

```
                          ┌─────────────────┐
                          │   达梦实例启动    │
                          └────────┬────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
     ┌────────────┐       ┌────────────┐       ┌────────────┐
     │ DLMIS+UMSTAT│       │ GISCENTER  │       │DATACENTER2 │
     │  (核心库)   │       │  (通图库)   │       │  (星桥库)   │
     └──────┬─────┘       └──────┬─────┘       └──────┬─────┘
            │                    │                    │
     ┌──────┼────────┬──────────┤                    │
     ▼      ▼        ▼          ▼                    ▼
  ┌─────┐┌──────┐┌──────┐  ┌──────────┐       ┌──────────┐
  │MIS  ││UMA   ││MF    │  │GIS / MMS │       │  星桥    │
  │     ││      ││      │  │  通图    │       │  (dex)   │
  └─────┘└──────┘└──────┘  └──────────┘       └──────────┘
            │
     ┌──────┼──────┐
     ▼      ▼      ▼
  ┌──────┐┌─────┐┌──────┐
  │ 毕升 ││采集 ││(可选)│
  │      ││服务 ││      │
  └──────┘└─────┘└──────┘

  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │  灵珑    │  │ 用户中心  │  │  悟空    │  │  明镜    │
  │ LINGLONG │  │USERCENTER│  │ WUKONG   │  │  MJING   │
  └──────────┘  └──────────┘  └──────────┘  └──────────┘

  ┌──────────┐  ┌──────────┐
  │  全行业   │  │  物联网   │
  │ IBILITY  │  │ EGOVAIOT │
  └──────────┘  └──────────┘
```

**依赖说明：**

| 依赖关系 | 说明 |
|----------|------|
| 毕升 → DLMIS+UMSTAT | 毕升复用智信云核心库，DLMIS/UMSTAT 必须先就绪 |
| 采集服务 → DLMIS+UMSTAT | 采集直接连 DLMIS/UMSTAT 读数据，不需要独立建库 |
| GIS → GISCENTER+PG | GIS 同时依赖达梦 GISCENTER 和 PostgreSQL giscenter |
| 星桥 → DATACENTER2 | 星桥独立建库，但须先用空库启应用再迁数据 |
| 灵珑/悟空/用户中心/明镜/全行业/物联网 | 各自独立库，无互相依赖，可并行迁移 |

**推荐迁移顺序：**
1. 达梦实例启动
2. DLMIS + UMSTAT（核心库，DTS 迁移）
3. 独立产品库（LINGLONG/USERCENTER/WUKONG/MJING/IBILITY/EGOVAIOT — 可并行）
4. GISCENTER + MMS（GIS 体系）
5. DATACENTER2（星桥，特殊步骤）
6. 采集服务（最后，依赖 DLMIS+UMSTAT 就绪）

### 5.1 智信云（MIS/UMA/MF）

#### 创建表空间和用户

```sql
-- 创建表空间
create tablespace "TBS_DLMIS" datafile '/egova/dmdata/data/TBS_DLMIS.DBF' size 12288 autoextend on;

-- 创建用户
create user "DLMIS" identified by "{{DM_PWD_EXAMPLE}}" default tablespace "TBS_DLMIS";
create user "UMSTAT" identified by "{{DM_PWD_EXAMPLE}}" default tablespace "TBS_DLMIS";

-- 授权
grant DBA to DLMIS;
grant DBA to UMSTAT;
commit;
```

- MySQL cgdb -> 达梦模式 dlmis
- MySQL cgdbstat -> 达梦模式 umstat
- 表空间共用 TBS_DLMIS

#### 修改 jdbc.properties

文件路径：`/egova/web/eUrbanXXX/WEB-INF/classes/jdbc.properties`（XXX = MIS/UMA/MF）

```properties
# 达梦数据库
biz.jdbc.url=jdbc:dm://ip:5236?clobAsString=true
biz.jdbc.driverClassName=dm.jdbc.driver.DmDriver
biz.jdbc.username=DLMIS
biz.jdbc.cryptogram={{DM_PWD_EXAMPLE}}
biz.jdbc.validation.query=select sysdate from dual

# stat 统计库
stat.jdbc.url=jdbc:dm://ip:5236?clobAsString=true
stat.jdbc.driverClassName=dm.jdbc.driver.DmDriver
stat.jdbc.username=UMSTAT
stat.jdbc.cryptogram=密码
stat.jdbc.validation.query=select sysdate from dual
```

#### 修改 hibernate.properties

文件路径：`/egova/web/eUrbanXXX/WEB-INF/classes/hibernate.properties`

```properties
hibernate.show_sql=false
hibernate.format_sql=true
# 注释掉其他 dialect，启用达梦
hibernate.dialect=org.hibernate.dialect.DmDialect
# 达梦数据库使用 oracle sql 语句
hibernate.special_sql_type=1
```

#### 修改 redis.properties

修改 IP 和密码。

#### 修改 reg.properties

修改 IP。文件路径：`/egova/web/eUrbanXXX/WEB-INF/classes/jobmanager/reg.properties`

#### 置空 MD5

```sql
-- 在 DLMIS 和 UMSTAT 库都执行
update databasechangelog set MD5SUM = NULL;
commit;
```

### 5.2 GISCENTER / MMS（GIS / MMS / 通图）

#### 创建模式

```sql
-- 属于 DLMIS 用户，不需要额外创建用户和表空间
CREATE SCHEMA "GISCENTER" AUTHORIZATION "DLMIS";
CREATE SCHEMA "MMS" AUTHORIZATION "DLMIS";
commit;
```

#### eUrbanGIS 修改 jdbc.properties

路径：`/egova/web/eUrbanGIS/WEB-INF/classes/jdbc.properties`

```properties
jdbc.driverClassName=dm.jdbc.driver.DmDriver
jdbc.url=jdbc:dm://ip:5236/DLMIS?characterEncoding=utf-8&connectTimeout=10000&socketTimeout=600000&autoReconnect=true
jdbc.username=DLMIS
jdbc.cryptogram=密码
jdbc.version=DM
jdbc.validationQuery=select now()

# PG 库（如果有）
geo.jdbc.driverClassName=org.postgresql.Driver
geo.jdbc.url=jdbc:postgresql://ip:5432/giscenter?characterEncoding=utf8&autoReconnect=true
geo.jdbc.username=postgres
geo.jdbc.cryptogram=密码
geo.jdbc.validationQuery=select now()
```

#### eGovaMMS 修改 jdbc.properties 和 hibernate.properties

路径：`/egova/web/eGovaMMS/WEB-INF/classes/`

```properties
# jdbc.properties
mms.jdbc.driverClassName=dm.jdbc.driver.DmDriver
mms.jdbc.url=jdbc:dm://ip:5236/MMS?encoding=UTF-8&connectTimeout=10000&socketTimeout=600000
mms.jdbc.username=DLMIS
mms.jdbc.cryptogram=密码
mms.jdbc.validation.query=select 1
```

#### egovagisserver 修改 giscenter.env

路径：`/egova/web/egovagisserver/giscenter.env`

```bash
--DATASOURCE_URL=jdbc:dm://ip:5236?schema=GISCENTER \
--DATASOURCE_DRIVER=dm.jdbc.driver.DmDriver \
--DATASOURCE_USERNAME=DLMIS \
--DATASOURCE_PASSWORD=密码 \
--HIBERNATE_DIALECT=org.hibernate.dialect.DmDialect \
```

#### 置空 MD5

```sql
update databasechangelog set MD5SUM = NULL;
commit;
```

### 5.3 基础产品（玲珑/悟空/毕升/用户中心/全行业/明镜/物联网）

#### 创建表空间和用户

```sql
-- 表空间
create tablespace "LINGLONG" datafile '/egova/dmdata/data/LINGLONG.DBF' size 12288 autoextend on;
create tablespace "USERCENTER" datafile '/egova/dmdata/data/USERCENTER.DBF' size 12288 autoextend on;
create tablespace "WUKONG" datafile '/egova/dmdata/data/WUKONG.DBF' size 12288 autoextend on;
create tablespace "XUANZANG_GIS" datafile '/egova/dmdata/data/XUANZANG_GIS.DBF' size 12288 autoextend on;
create tablespace "IBILITY" datafile '/egova/dmdata/data/IBILITY.DBF' size 12288 autoextend on;
create tablespace "MJING" datafile '/egova/dmdata/data/MJING.DBF' size 12288 autoextend on;
create tablespace "EGOVAIOT" datafile '/egova/dmdata/data/EGOVAIOT.DBF' size 12288 autoextend on;

-- 用户
create user "LINGLONG" identified by "密码" default tablespace "LINGLONG";
create user "USERCENTER" identified by "密码" default tablespace "USERCENTER";
create user "WUKONG" identified by "密码" default tablespace "WUKONG";
create user "XUANZANG_GIS" identified by "密码" default tablespace "XUANZANG_GIS";
create user "IBILITY" identified by "密码" default tablespace "IBILITY";
create user "MJING" identified by "密码" default tablespace "MJING";
create user "EGOVAIOT" identified by "密码" default tablespace "EGOVAIOT";

-- 授权
grant DBA to LINGLONG;
grant DBA to USERCENTER;
grant DBA to WUKONG;
grant DBA to XUANZANG_GIS;
grant DBA to IBILITY;
grant DBA to MJING;
grant DBA to EGOVAIOT;
commit;
```

#### 各产品配置文件修改

**玲珑** - `/egova/apps/basic/linglong/linglong.env`：
```bash
--DATASOURCE_DRIVER=dm.jdbc.driver.DmDriver \
--spring.datasource.url=jdbc:dm://ip:5236/LINGLONG \
--flagwind.mybatis.name-quote=-1 \
--DATASOURCE_USERNAME=LINGLONG \
--DATASOURCE_PASSWORD=密码 \
```

**用户中心** - `/egova/apps/basic/usercenter/usercenter.env`：
```bash
--DATASOURCE_DRIVER=dm.jdbc.driver.DmDriver \
--DATASOURCE_URL=jdbc:dm://ip:5236?schema=USERCENTER \
--DATASOURCE_USERNAME=USERCENTER \
--DATASOURCE_PASSWORD=密码 \
```

**毕升** - `/egova/apps/basic/evaluation/evaluation.env`：
> 注意：毕升使用 DLMIS/UMSTAT 是部分现场的情况，根据实际情况选择独立的毕升库或复用 DLMIS/UMSTAT。

```bash
--DATASOURCE_DRIVER=dm.jdbc.driver.DmDriver \
--DATASOURCE_URL=jdbc:dm://ip:5236?clobAsString=true \
--DATASOURCE_USERNAME=DLMIS \
--DATASOURCE_PASSWORD=密码 \
--STAT_DATASOURCE_DRIVER=dm.jdbc.driver.DmDriver \
--STAT_DATASOURCE_URL=jdbc:dm://ip:5236?clobAsString=true \
--STAT_DATASOURCE_USERNAME=UMSTAT \
--STAT_DATASOURCE_PASSWORD=密码 \
--HIBERNATE_DIALECT=org.hibernate.dialect.DmDialect \
```

**全行业** - `/egova/apps/sg/ibility/ibility.env`：
```bash
--DATASOURCE_DRIVER=dm.jdbc.driver.DmDriver \
--DATASOURCE_URL=jdbc:dm://ip:5236/IBILITY?zeroDateTimeBehavior=convertToNull&useUnicode=true&characterEncoding=utf-8 \
--DATASOURCE_USERNAME=IBILITY \
--DATASOURCE_PASSWORD=密码 \
```

**悟空** - `/egova/apps/basic/wukong/wukong.env`：
```bash
--DATASOURCE_DRIVER=dm.jdbc.driver.DmDriver \
--DATASOURCE_URL=jdbc:dm://ip:5236?schema=WUKONG \
--DATASOURCE_USERNAME=WUKONG \
--DATASOURCE_PASSWORD=密码 \
--PUMP_STAGE_TYPE=dm
```

**玄奘** - `/egova/apps/gis/xuanzang/run.sh`：根据脚本提示修改。

**明镜** - `/egova/apps/elaw/mjing/mjing.env`：
```bash
--DATASOURCE_DRIVER=dm.jdbc.driver.DmDriver \
--DATASOURCE_URL="jdbc:dm://ip:5236/MJING?zeroDateTimeBehavior=convertToNull&useUnicode=true&characterEncoding=utf-8&connectTimeout=60000&socketTimeout=3600000" \
--DATASOURCE_USERNAME=MJING \
--DATASOURCE_PASSWORD=密码 \
```

**物联网** - `/egova/apps/iot/iot/application.properties`：
> 目录定位：如路径不一致，执行 `cat /etc/systemd/system/iot.service` 查找实际部署目录。

```properties
spring.datasource.url=jdbc:dm://ip:5236?clobAsString=true
spring.datasource.username=EGOVAIOT
spring.datasource.password=密码
spring.datasource.driver-class-name=dm.jdbc.driver.DmDriver
```

#### 置空 MD5（每个库都要执行）

```sql
update databasechangelog set MD5SUM = NULL;
commit;
```

### 5.4 星桥（dex/datacenter2）

#### 创建表空间和用户

```sql
create tablespace "DATACENTER2" datafile '/egova/dmdata/data/DATACENTER2.DBF' size 12288 autoextend on;

create user "DATACENTER2" identified by "密码" default tablespace "DATACENTER2";
grant DBA to DATACENTER2;
commit;
```

#### 修改参数

在 dex 配置文件底部新增：
```bash
--egova.liquibase.dm.varchar.scaleFactor=4
```

达梦参数：
```bash
--DATASOURCE_DRIVER=dm.jdbc.driver.DmDriver \
--DATASOURCE_URL=jdbc:dm://ip:5236?schema=DATACENTER2 \
--DATASOURCE_USERNAME=DATACENTER2 \
--DATASOURCE_PASSWORD=密码 \
```

#### 星桥迁移特殊步骤

1. 先用空的达梦库启动应用（让 liquibase 建表）
2. 再迁移数据
3. 迁移时跳过三张表：`com_license`、`databasechangelog`、`databasechangeloglock`（保留达梦自动建的 changelog 表数据）
4. 迁移完成后重新启动星桥

### 5.5 采集服务（statgather）

采集服务运行在独立的采集服务器上，通过 Python 脚本 + dmPython 驱动连接达梦数据库。切换达梦分为四步：传输达梦依赖库 → 配置环境变量 → 安装 dmPython → 修改配置文件。

#### 5.5.1 dmPython 安装准备

从达梦数据库安装根目录获取以下文件并上传到采集服务器：

```bash
# 1. 获取 dmPython 驱动源码（在达梦服务器的安装根目录下）
# 路径：达梦安装目录/drivers/python/dmPython/
# 将整个 dmPython 文件夹传到采集服务器的 /egova/ 目录

# 2. 获取 bin 和 include 目录
# 将达梦安装目录下的 bin/ 和 include/ 上传到采集服务器
```

#### 5.5.2 环境配置

```bash
# 在采集服务器上创建目录
mkdir -p /egova/dmdbms/

# 将 bin 和 include 放到 /egova/dmdbms/ 目录下

# 设置环境变量（根据实际路径调整）
export DM_HOME=/egova/dmdbms
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/egova/dmdbms/bin
export PATH=$PATH:/egova/dmdbms/bin
```

#### 5.5.3 安装 dmPython

安装前必须确认采集脚本的 Python 版本：

```bash
cd /egova/web/statgather
cat testOne.sh
```

| Python 版本 | 安装命令 |
|------------|---------|
| Python 3 | `cd dmPython && python3 setup.py install` |
| Python 2 | `cd dmPython && python setup.py install` |

#### 5.5.4 修改配置并启动

修改 `/egova/web/statgather/settings.py`：

```python
dbTypeName = "dm"
stat_conn = {
    "host": "达梦IP",
    "port": 5236,
    "user": "UMSTAT",
    "password": "密码"
}
stat_db_name = "UMSTAT"
biz_conn = {
    "host": "达梦IP",
    "port": 5236,
    "user": "DLMIS",
    "password": "密码"
}
biz_db_name = "DLMIS"
```

修改后启动采集服务。采集服务依赖 DLMIS 和 UMSTAT 两个达梦库，这两个库在智信云迁移阶段已经创建并迁移完成。

> 采集服务无需额外创建表空间和用户，直接复用智信云的 DLMIS/UMSTAT。
> 参考 wiki：[达梦环境采集部署](https://faq.egova.com.cn:7787/projects/redmine/wiki/%E8%BE%BE%E6%A2%A6%E7%8E%AF%E5%A2%83%E9%87%87%E9%9B%86%E9%83%A8%E7%BD%B2)

#### 5.5.5 常见报错：libdmdpi.so 找不到（高频坑）

**报错特征**（启动采集服务时，`import dmPython` 处直接抛）：

```
ImportError: libdmdpi.so: cannot open shared object file: No such file or directory
```

典型堆栈位置：`statGatherApp.py` → `TaskManager.auto_start()` → `tools/utils.py` 的 `get_bizdb_conn()` → `import dmPython`

**根因**：dmPython 是 C 扩展模块，`import` 时会 dlopen 加载达梦客户端动态库 `libdmdpi.so`。这个 so 通常不在系统默认库路径里，必须靠 `LD_LIBRARY_PATH` 指向 `/egova/dmdbms/bin`。**最常见的坑**：`LD_LIBRARY_PATH` 写在了 `/etc/profile` 里，而采集服务用 nohup 或启动脚本后台拉起时**不加载 /etc/profile**，环境变量丢失，运行时就找不到 so。

**排查三步（按顺序）**：

```bash
# 第1步：确认 so 文件真的存在（最常见是 bin 没传全或路径不对）
ls -l /egova/dmdbms/bin/libdmdpi*
# 如果没有输出，从达梦服务器重传 bin；注意 x86_64 与 aarch64 的 so 不通用，架构必须与达梦服务器一致

# 第2步：前台带变量验证，区分"库缺失"还是"环境变量丢失"
LD_LIBRARY_PATH=/egova/dmdbms/bin python3 -c "import dmPython; print(dmPython.__file__)"
# 能打印出路径 → so 存在且位数匹配，问题就是环境变量没生效 → 走修复方案A/B
# 仍报错 → so 本身缺失/架构不匹配/权限问题

# 第3步：检查启动脚本内部有没有 export（很多脚本只依赖 /etc/profile，必踩坑）
cat /egova/web/statgather/start.sh   # 或 testOne.sh，看开头有无 export LD_LIBRARY_PATH
```

**修复方案（按推荐顺序）**：

| 方案 | 操作 | 适用场景 |
|------|------|---------|
| **A. ldconfig 全局注册（推荐，一劳永逸）** | `echo "/egova/dmdbms/bin" > /etc/ld.so.conf.d/dmdbms.conf && ldconfig`，验证 `ldconfig -p \| grep dmdpi` | 所有进程（含 nohup/systemd/定时任务）都能找到 so，最省心 |
| **B. 启动脚本显式 export** | 在 `start.sh`/`testOne.sh` 开头加 `export DM_HOME=/egova/dmdbms` + `export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/egova/dmdbms/bin` | 不想动系统配置，只影响采集服务 |
| **C. 复制 so 到系统库目录（应急）** | `cp /egova/dmdbms/bin/libdmdpi.so /usr/lib64/ && ldconfig` | 快速止血，注意系统升级可能被清掉 |

**验证**：修复后重新启动采集服务，日志不再出现 `ImportError` 即成功；再抽查数据入库情况。

---

## 6. 服务启动顺序

### 6.1 中间件应用（AAS 体系）

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

### 6.2 基础产品（systemd 管理）

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

### 6.3 脚本管理的服务

**wuneng（悟能）**

```bash
cd /egova/apps/basic/wuneng
sh ./start.sh     # 启动
sh ./stop.sh      # 停止
sh ./restart.sh   # 重启
```

- 进程查看：无特定进程名（按应用特征查找）
- 日志：`/egova/apps/basic/wuneng/logs/wuneng/web_logs/`，查看 `wuneng.log`

**newplatform（新平台）**

```bash
cd /egova/apps/basic/wuneng
sh ./start.sh     # 启动
sh ./stop.sh      # 停止
sh ./restart.sh   # 重启
```

- 进程查看：`ps -ef | grep newplatform`
- 日志：`/egova/web/newplatform/api/logs/egova-service-starter/web_logs/`，查看 `error.log`、`info.log`

**采集服务 statgather（统计）**

```bash
cd /egova/web/statgather
bash startStatGather.sh
```

- 日志：`/egova/web/statgather/log/`，查看 `stat-gather.log`

### 6.4 基础设施服务

**Kafka**

```bash
service kafka status/start/stop
```

- 进程查看：`ps -ef | grep kafka`
- 日志：`/egova/kafka/logs/`，查看 `server.log`

**Zookeeper**

```bash
service zookeeper status/start/stop
```

- 进程查看：`ps -ef | grep zookeeper`
- 日志：`/egova/log/zookeeper/`，查看 `zookeeper-egova-server-xxx.out`

**Redis**

```bash
service redis status/stop/start
```

**Elasticsearch**

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

**Nacos**

```bash
service nacos status/stop/start
```

- 进程查看：`ps -ef | grep nacos`
- 日志：`/egova/nacos/logs/`，查看 `nacos.log`（主运行日志）、`startup.log`（启动脚本日志）

**Eureka**

```bash
systemctl daemon-reload
systemctl enable eureka  # 开机自启
service eureka restart
```

- 进程查看：`ps -ef | grep eureka`
- 日志：`/egova/apps/springcloud/eureka/logs/egova-eureka/web_logs/`，查看 `error.log`、`info.log`

**MinIO**

```bash
service minio status/stop/start
```

- 进程查看：`ps -ef | grep minio`
- 日志：`/egova/minio/`，查看 `error.log`

### 6.5 其他业务服务

| 服务 | 启停命令 | 进程查看 | 日志路径 |
|------|---------|---------|---------|
| export | `service export start/stop/status` | `ps -ef \| grep export` | `/egova/apps/basic/export/logs/egova-service-export/web_logs/` |
| 车载服务 | `bash dm-start.sh start/stop/status` | `ps -ef \| grep egova-vehicle-service.jar` | `/egova/apps/sani-vehicle-v14/logs/web_logs/` |
| eUrbanFac（市政微服务 V20） | `service eUrbanFac status/stop/start` | `ps -ef \| grep eUrbanFac` | `/egova/apps/fac/eUrbanFac/logs/facilities-facv20-service/web_logs/` |
| fac（市政微服务 V22） | `service fac status/stop/start` | `ps -ef \| grep fac` | `/egova/apps/fac/fac/logs/facilities-facv22-service/web_logs/` |
| httpfileservice（多媒体） | `service httpfileservice status/stop/start` | `ps -ef \| grep httpfileservice` | `/egova/apps/basic/httpfileservice/logs/egova-httpfileserver-netty/web_logs/` |

> 各服务日志通用查看方式：`error.log` 为报错日志，`info.log` 为应用信息日志。
