---
name: xinchuang-migration
version: 2.0.0
author: majianquan
license: MIT
category: project-delivery
visibility: tech-manager
description: 信创迁移全流程支持。v2.0 由两条能力线合并而成：①现场作业线——eGova 产品从 MySQL/Tomcat 迁移到达梦DM8/金蝶AAS 的六阶段实操流程（前期准备、新服务器部署、达梦部署、金蝶部署、MySQL替换达梦、启动验证），含 14 条报错速查（SYSGEO2/Liquibase MD5/JDBC连接/Schema不存在/表空间/GBK截断/无效列名/保留字等）、排错决策树、16 产品配置对照表、迁移前标准备份脚本、Oracle 兼容参数速查、全量服务启停管理、77 张现场操作截图索引；②知识检索线——经公网 MCP（precheck/zhengtong_query）查公司 17 万 Redmine 工单 + 4500 篇知识库文档，覆盖达梦/人大金仓/瀚高/海量/麒麟/欧拉/UOS/金蝶(Apusic)/东方通(TongWeb)/鲲鹏/飞腾/海光等全信创场景，自带 REST 降级、vectors.db 直连应急与互联网搜索兜底；③自动化线——迁移前环境预检、迁移前后数据一致性校验、16 产品配置对照检查三个工程化脚本。凡涉及信创迁移、国产化迁移/适配、达梦迁移/部署、人大金仓/瀚高/海量迁移、金蝶/Apusic/东方通中间件、麒麟/欧拉/UOS 部署、DTS 数据迁移、dmPython、statgather 采集服务切换达梦、迁移报错排查、迁移前预检、迁移后校验，都应使用本 Skill。
trigger_keywords:
  - 信创迁移
  - 国产化迁移
  - 达梦迁移
  - 达梦部署
  - 达梦安装
  - MySQL迁移达梦
  - Oracle迁移达梦
  - 金蝶部署
  - 金蝶替换Tomcat
  - AAS部署
  - Apusic
  - 东方通
  - TongWeb
  - 人大金仓
  - Kingbase
  - 瀚高
  - 海量
  - Vastbase
  - 麒麟部署
  - 欧拉部署
  - UOS部署
  - 国产CPU
  - 鲲鹏
  - 飞腾
  - 海光
  - DTS
  - dmPython
  - statgather
  - SYSGEO2
  - liquibase
  - MD5SUM
  - CASE_SENSITIVE
  - COMPATIBLE_MODE
  - V$RESERVED_WORDS
  - 迁移前预检
  - 迁移后校验
  - 麒舰信创
  - 星桥迁移
  - 灵珑信创
  - 毕升迁移
  - 明镜迁移
when_to_use: |
  - 用户要在信创环境（麒麟/欧拉/UOS + 达梦 + 金蝶AAS/东方通）部署或迁移 eGova 体系产品
  - 迁移前准备：环境预检、备份、版本评估
  - 迁移中：达梦安装初始化、DTS 数据迁移、金蝶部署应用、各产品配置参数修改、报错排查
  - 迁移后：对象数量/行数一致性校验、服务启动验证、SQL 统计信息调优
  - 询问信创相关历史经验：公司工单/知识库检索（达梦/金仓/瀚高/海量/各中间件/各国产CPU）
  - 采集服务 statgather 切换达梦（dmPython/libdmdpi 专项）
when_not_to_use: |
  - 非 eGova 体系产品的配置路径/参数名依赖 eGova 结构，仅检索部分适用
  - DM7 及以下版本命令差异大，本 skill 基于 DM8
  - 信创节点第三方软件版本探测与 CVE 匹配 → 用 xinchuang-pkg-probe
  - oneinstall_v2 一键部署的规划与部署本身 → 用 oneinstall-planner / qijian-deploy / egova-oneinstall-guide
  - 服务器资源规划出 metadata.yml → 用 oneinstall-planner
---

# 信创迁移

信创迁移全流程支持 skill。**三条能力线**：

1. **现场作业**（v2.0 自 quiz266 提交物沉淀）：六阶段迁移流程 + 报错速查 + 决策树 + 16 产品配置对照 + 备份/启停 + 77 张现场截图
2. **知识检索**（v1.0 既有架构）：`skill → MCP（precheck/zhengtong_query）→ demo redmine-assist → live vectors.db`，知识库每次同步后自动最新
3. **自动化**（v2.0 新增）：迁移前环境预检、迁移前后一致性校验、产品配置对照检查

## 迁移流程总览

```
前期准备 → 新服务器部署 → 达梦/金蝶部署 → MySQL 替换为达梦 → 各产品配置修改 → 启动验证
   │            │                                │                        │
 precheck_env.sh                     DTS + verify_migration.py      check_product_config.py
 （环境预检）                        （基线采集+一致性校验）          （16产品配置核对）
```

**与周边 skill 的链条**：`oneinstall-planner`（资源规划出 metadata.yml）→ `qijian-deploy`（MySQL/Tomcat 基线部署）→ **本 skill（达梦/金蝶替换，六阶段）** → `egova-oneinstall-guide`（菜单 m `i_modify_db_connection.sh` 一键切库 + 排障）→ `xinchuang-pkg-probe`（迁移后版本矩阵回填 + CVE 标记）。

## 自动化脚本总表

| 脚本 | 用途 | 运行位置 | 说明 |
|---|---|---|---|
| `scripts/precheck_env.sh` | 迁移前环境预检（OS/磁盘/内存/端口/dmdba 用户/内核限制） | 目标 Linux 节点 | 全程只读，输出 PASS/FAIL/WARN 清单 |
| `scripts/verify_migration.py` | 迁移基线采集与前后一致性校验（表/视图/存储过程/行数对比） | 本机或节点 | `collect` 采基线，`compare` 出差异报告；判不一致时**停止并报告，不自动修复** |
| `scripts/check_product_config.py` | 16 产品配置对照检查（jdbc:dm 驱动/方言/模式名） | 本机或节点 | 依赖 `config/product-config-map.json`，核对实际配置文件 |
| `scripts/kb_query.py` | 公网 MCP 直调（precheck/zhengtong_query） | 本机 | token 从 `D:\opencode\config\redmine-assist-mcp.json` 或环境变量 `REDMINE_ASSIST_TOKEN` 读取，**不落源码** |
| `scripts/query_xc.py` | REST 降级查询（`--sweep` 批量） | 本机 | MCP 不可用时走 `/query` REST |
| `scripts/backup_web.sh` | 备份 `/egova/web` → `/egova/backup/web` | 老服务器 | tar.gz 全备份、保留 15 份、文件锁防并发、磁盘预检、nohup 后台 |
| `scripts/backup_apps.sh` | 备份 `/egova/apps` → `/egova/backup/apps` | 老服务器 | 同上 |
| `scripts/backup_egova.sh` | 多目录合并备份（`BACKUP_DIRS` 数组） | 老服务器 | crontab 每月 1 号 03:00 |

## 交互模型

### 何时追问

- 用户未说明具体产品（如只说"迁移配置怎么改"）→ 列出可选产品：MIS/UMA/MF/GIS/MMS/通图/灵珑/用户中心/毕升/全行业/悟空/明镜/物联网/星桥/玄奘/采集服务/悟能/新平台
- 用户未说明迁移阶段（如只说"达梦怎么装"）→ 问是新部署还是已有实例
- 用户提到非 MySQL/Tomcat 体系（如 Oracle→达梦）→ 说明本 skill 侧重 MySQL，部署/配置/验证步骤通用；Oracle→达梦额外参考"Oracle 兼容参数速查"
- 用户问某服务怎么启停/看日志 → 直接查阶段六服务分类表，细节见 `references/service_management.md`
- 涉及具体 IP、密码、端口等环境参数 → 提示替换为现场实际值
- 用户描述报错但信息不足 → 引导提供完整错误日志，按排错决策树定位；同时用 `zhengtong_query` 检索历史工单

### 何时直接回答

- 用户明确指定了产品和阶段 → 直接给出对应配置
- 用户描述了具体报错信息 → 直接定位到"常见报错速查表"
- 用户问通用参数（JDBC 驱动类、Hibernate 方言等）→ 直接输出
- 用户问流程顺序 → 直接展示"迁移流程总览"

## 输出格式指引

| 问题类型 | 输出格式 |
|----------|----------|
| 配置修改 | 先给文件路径，再给完整配置片段（properties/bash 代码块） |
| 报错排查 | 先给原因，再给解决 SQL/命令，最后给验证方法；附知识库检索到的同类案件链接 |
| 多产品对比 | 使用对照表（产品/库名/模式名/用户名/配置路径） |
| 流程步骤 | 编号列表，每步含可执行命令 |
| 注意事项 | 加粗关键词 + 简短说明 |

## 文档截图引用

内置信创迁移文档（辽宁区域）的 77 张操作截图，存放在 `assets/`，按迁移阶段分类编号，完整索引见 `references/image_catalog.md`。

> ⚠️ 截图摄自真实现场环境，可能含内网地址等信息：**仅限公司内部使用，禁止外发**。示例密码/IP 在文档中一律为占位符（`{{ONEOPS_IP}}`/`{{DM_PWD_EXAMPLE}}`），执行时替换为现场实际值。

### 图片命名与阶段分类

```
序号_阶段_操作描述.png
```

| 编号范围 | 阶段 | 示例 |
|----------|------|------|
| 01-06 | 前期准备 | `01_prep_os_version_check.png` |
| 07 | 老服务器迁移 | `07_oldserver_compress_package.png` |
| 08-12 | 服务启动 | `08_service_stop_tomcat.png` |
| 13-25 | 达梦数据库部署 | `19_dameng_install_step1.png` |
| 26-52 | 金蝶中间件部署 | `36_aas_deploy_war_upload.png` |
| 53-66 | 数据迁移工具 DTS | `56_dts_new_migration.png` |
| 67-77 | 各产品配置修改 | `74_config_iot_application_properties.png` |

### 回答时如何引用图片

**第一步：定位图片** — 查 `references/image_catalog.md`：

| 用户提问内容 | 对应图片范围 |
|--------------|-------------|
| 达梦怎么安装/部署 | 13-25 |
| 金蝶怎么安装/部署 | 26（解压 + 替换 license） |
| 金蝶怎么部署应用 | 36-46 |
| 金蝶怎么配置连接池 | 27-29 |
| 金蝶怎么看日志 | 49-52 |
| 金蝶怎么改端口 | 47-48 |
| 达梦迁移工具怎么用 | 53-66 |
| 某产品的配置怎么改 | 67-77（按产品名匹配） |
| 老服务器怎么迁移 | 07 |
| 采集服务怎么切换达梦 | `references/migration_steps.md` 5.5 节（纯文本步骤） |
| Tomcat 怎么启停 / 怎么看日志 | 08-10 |
| 基础产品怎么启停 | 11-12 |

**第二步：展示图片** — 按优先级两种方式：

1. **方式一（首选）**：Read 工具读 `assets/<图片名>`，多模态直接展示
2. **方式二（fallback）**：方式一失败时**必须**改用 `references/image_gallery_template.html` 模板生成 HTML 图册（`file:///` 绝对路径引用 assets），一张 HTML 按阶段分区块展示多图

## 适用场景边界

| 场景 | 覆盖程度 | 说明 |
|------|---------|------|
| **MySQL → 达梦** | ✅ 完整覆盖 | 核心场景，含 DTS 迁移全流程 |
| **Oracle → 达梦** | ⚠️ 部分适用 | 部署/配置/置空 MD5 通用；含"Oracle 兼容参数速查"；DTS 类型映射需额外调整 |
| **纯应用层迁移（金蝶替换 Tomcat）** | ⚠️ 部分适用 | 步骤通用，不涉及数据库 |
| **MySQL → 金仓/瀚高/海量** | ⚠️ 检索为主 | 现场流程未沉淀，走知识库检索 + `references/migration-playbooks.md` C/D/E 章 |
| **非 eGova 体系** | ❌ 不适用 | 配置文件路径和参数名依赖 eGova 产品结构 |
| **DM7 及以下** | ❌ 不适用 | 基于 DM8，DM7 命令差异大 |

## 停止条件（硬规则）

1. **变更类 SQL 必须先展示后执行**：除 skill 自带备份脚本外，任何对生产库的 DDL/DML（含置空 MD5、改表空间）先完整展示给用户确认再执行
2. **不碰 license**：金蝶 `license.xml` 只做"替换文件"指路，不生成、不修改、不分发 license
3. **占位符纪律**：现场 IP/密码/端口写入交付物时一律占位符；禁止把现场真实参数回写进本 skill 任何文件
4. **校验不一致即停止**：`verify_migration.py compare` 判定不一致时输出差异清单并停止，不自动"修复"数据
5. **鉴权不绕过**：公网 MCP 返回 401 时按配置文件说明重新扫码换 token，不尝试绕过鉴权
6. **预检不修复**：`precheck_env.sh` 只报告不修改任何系统配置

## 阶段一：前期准备

### 1. 服务器 DNS 解析检查

执行 `ping oneops.egova.com.cn` 确认能否解析公司地址（用于一键部署脚本 `dl_v2.sh`）。政务网环境如无法解析，修改 `/etc/hosts`（IP 用现场 oneops 实际地址，参考 `config/site_profile.md`）：
```
{{ONEOPS_IP}} oneops.egova.com.cn
```

### 2. 服务器版本兼容性检查

```bash
bash scripts/precheck_env.sh          # 一键预检（推荐）
cat /etc/os-release && cat /etc/os-version
```

### 3. 老服务器产品版本评估

联系各产品测试人员评估是否需要升级。建议**先迁移再升级**，避免影响老系统。

### 4. 迁移前备份（标准备份脚本）

迁移动任何东西之前先备份。三个标准备份脚本见"自动化脚本总表"，统一特性：

- 全备份 tar.gz 不排除文件，包名 `<目录名>_YYYYMMDD_HHMMSS.tar.gz`，保留最近 15 份自动清理
- 文件锁 `/tmp/backup_<name>.lock` 防并发，磁盘空间预检
- 首次运行自动 `nohup` 转后台，前台立即提示 `tail -f` 日志路径
- 日志按天分割到 `/egova/backup/logs/`（`LOG_KEEP_DAYS=0` 默认不清理），最后一行固定"备份成功: 路径"
- crontab 每月一号调度：`0 3 1 * * /egova/backup_<name>.sh`

使用方式：
```bash
scp scripts/backup_web.sh root@服务器ip:/egova/
chmod +x /egova/backup_web.sh
/egova/backup_web.sh
tail -1 /egova/backup/logs/backup_web_$(date +%Y%m%d).log
```

> 需要备份其他目录时，改脚本头部 `SRC_DIR`；多目录场景用 `backup_egova.sh` 的 `BACKUP_DIRS` 数组（格式 `"源目录:目标目录"`）。

## 阶段二：新服务器产品部署

使用公司一键部署脚本完成产品部署（规划用 oneinstall-planner，部署用 qijian-deploy）。重点：确保 mysql、tomcat、nginx 等环境能启动即可，产品本身能否启动不是此阶段重点。

### 老服务器迁移

```bash
tar -zcvf eUrbanMIS.tar.gz eUrbanMIS/
scp eUrbanMIS.tar.gz root@新服务器ip:/egova
```

## 阶段三：达梦数据库部署

> 详细命令和 SQL 参见 `references/migration_steps.md` 第 2 节；截图 13-25

关键步骤：
1. 创建 dmdba 用户（**禁止 root 安装**）
2. 修改 `/etc/security/limits.conf` 文件打开数限制
3. 创建目录规划：`/egova/dmdata/data`、`/egova/dmdata/arch`、`/egova/dmdata/dmbak`、`/egova/log/dm`
4. 挂载 ISO 镜像并命令行安装
5. `dminit` 初始化实例（CASE_SENSITIVE/PAGE_SIZE/LENGTH_IN_CHAR 等建库后不可改，见"Oracle 兼容参数速查"）
6. 注册系统服务（`dm_service_installer.sh`）
7. `systemctl start DmServiceDLMIS.service` 启动

## 阶段四：金蝶10（AAS）部署

> 详细步骤参见 `references/migration_steps.md` 第 3 节；截图 26-52

关键步骤：
1. 解压安装包到 `/egova/Apusic`
2. 替换 `license.xml` 文件（见停止条件 2）
3. `./asadmin start-domain` 启动
4. 管理控制台 `https://ip:6848/` 配置 JDBC 连接池、创建实例、部署应用
5. **不要使用金蝶默认模板生成域**——复制 mis 的 domain 并修改 config 指向 web（知识库高频坑，见 `references/xinchuang-cases.md`）

## 阶段五：MySQL 替换为达梦（核心）

> 详细 SQL 和配置参数参见 `references/migration_steps.md` 第 4-5 节

### 迁移前评估（重要）

迁移前必须记录源库基线，用于迁移后校验：

```bash
# 采集源库（MySQL）与目标库（达梦）基线清单
python scripts/verify_migration.py collect --dialect mysql --host <ip> --port 3306 \
    --user <user> --schema cgdb --out baseline_cgdb.json
python scripts/verify_migration.py collect --dialect dm   --host <ip> --port 5236 \
    --user DLMIS --schema DLMIS --out target_cgdb.json
# 迁移完成后对比
python scripts/verify_migration.py compare --baseline baseline_cgdb.json --target target_cgdb.json
```

手工评估 SQL 参见 `references/migration_steps.md` 第 4.0 节；确认源库字符集，评估 GBK→UTF8 场景的字段长度扩展。

### 常见报错速查表

| 报错关键词 | 原因 | 解决方案 | 阶段 |
|-----------|------|---------|------|
| **非法的基类名 SYSGEO2** | 达梦缺少空间扩展包 | `SP_INIT_GEO_SYS(1); SP_INIT_GEO2_SYS(1);`，仍报错联系达梦厂商 | 迁移中 |
| **Liquibase 校验失败 / MD5SUM mismatch** | 迁移后 MD5 值不匹配 | `update databasechangelog set MD5SUM = NULL; commit;` | 迁移后 |
| **Invalid username/password; logon denied** | 达梦用户名或密码错误 | 检查 `jdbc.properties` 中 username/password，确认用户已创建且授权 DBA | 启动 |
| **Schema 'XXX' does not exist** | 达梦模式未创建 | `CREATE SCHEMA "XXX" AUTHORIZATION "用户";` 或检查 JDBC URL 中的 `?schema=XXX` | 启动 |
| **Network adapter could not establish the connection** | 达梦端口不通或服务未启动 | `systemctl status DmServiceDLMIS` 检查服务状态；防火墙放行 5236 端口 | 启动 |
| **Connection refused / timeout** | JDBC URL 中 IP 或端口错误 | 确认达梦 IP 和端口（默认 5236），`jdbc:dm://ip:5236` | 启动 |
| **Cannot load JDBC driver class 'dm.jdbc.driver.DmDriver'** | 缺少达梦 JDBC 驱动 | 从达梦安装目录 `drivers/jdbc/` 复制 jar 到应用的 `WEB-INF/lib/` | 启动 |
| **GBK→UTF8 字符串截断** | 中文字符字节数变化（2→3） | DTS 中设置字段长度扩展倍数为 1.5 | 迁移中 |
| **外键约束违反** | 迁移顺序导致依赖表数据先插入 | DTS 中关闭外键检查，迁移完成后重新启用 | 迁移中 |
| **表空间不足 / tablespace full** | 数据文件未设 autoextend | `ALTER TABLESPACE "TBS_DLMIS" ADD DATAFILE '...' SIZE 10240 AUTOEXTEND ON;` | 迁移中 |
| **ImportError: libdmdpi.so: cannot open shared object file** | dmPython 找不到达梦客户端动态库；LD_LIBRARY_PATH 写在 /etc/profile，后台启动不加载 | ldconfig 全局注册：`echo "/egova/dmdbms/bin" > /etc/ld.so.conf.d/dmdbms.conf && ldconfig`；或启动脚本显式 export；详见 migration_steps.md 5.5.5 节 | 采集服务启动 |
| **无效列名 / 无效的列名** | 大小写敏感配置不一致（CASE_SENSITIVE，建库时定死不可改） | Oracle 迁移的库 CASE_SENSITIVE 应为 Y；核对表/列名实际大小写及是否被引号包裹 | 迁移中 |
| **语法分析出错（建表/建对象）** | 对象名命中达梦系统保留字 | `SELECT * FROM V$RESERVED_WORDS WHERE RESERVED='Y' AND KEYWORD='对象名';` 确认后改名、加双引号，或 dm_svc.conf 配 `KEYWORDS=对象名` 屏蔽 | 迁移中 |
| **无效的表或视图名（视图）** | 视图依赖的表未先迁移 | 按顺序迁移：序列 → 表 → 视图 → 函数/存储过程/包 | 迁移中 |

> 详细排查步骤和验证方法见 `references/migration_steps.md` 第 4.1 节；公司历史同类案件见 `references/xinchuang-cases.md`。

### 排错决策树

```
报错发生在哪个阶段？
├── 达梦安装阶段
│   ├── "cannot create user/group" → 系统文件锁定 → chattr -i 解锁
│   ├── "permission denied" → 未用 dmdba 用户 → su - dmdba
│   └── "cannot open shared object file" → 缺少依赖库 → yum install 对应的库
├── DTS 迁移阶段
│   ├── SYSGEO2 相关 → 空间扩展包未开启 → SP_INIT_GEO2_SYS(1)
│   ├── 字符串截断 → GBK→UTF8 问题 → 设字段扩展倍数 1.5
│   ├── 外键错误 → 表导入顺序 → 关闭外键检查再迁移
│   └── 类型映射错误 → 未设自定义映射 → 检查 DOUBLE/GEOMETRY/POINT 映射
├── 应用启动阶段
│   ├── Liquibase / MD5SUM → 未置空 MD5 → update databasechangelog
│   ├── Schema not found → 模式未建或 URL 错误 → CREATE SCHEMA / 检查 URL
│   ├── Cannot load driver → 缺少 DmDriver jar → 复制 JDBC 驱动到 lib
│   └── Connection refused → 达梦未启动/端口不对 → systemctl status / 检查 5236
└── 迁移后运行阶段
    ├── 查询慢 → 统计信息过时 → DBMS_STATS.GATHER_SCHEMA_STATS
    ├── 数据不一致 → 迁移遗漏 → verify_migration.py compare 对比基线
    └── 乱码 → 字符集不匹配 → 检查源库/目标库字符集设置
```

采集服务（statgather）启动阶段补充分支：

```
采集服务启动报错
├── ImportError: libdmdpi.so ... No such file → 达梦客户端库找不到
│   ├── 后台拉起不加载 /etc/profile → ldconfig 全局注册 或 启动脚本显式 export（见 migration_steps.md 5.5.5）
│   └── so 缺失/架构不匹配 → 重传 bin，核对 x86_64/aarch64
├── No module named dmPython → 未安装或装错 Python 版本 → 按 testOne.sh 确认版本重装
└── can't connect / password 报错 → 达梦连接问题 → 检查 IP/端口 5236/账号密码
```

### 迁移工具（DTS）设置

1. 本地安装达梦，自带迁移工具（截图 53-66）
2. 设置自定义类型映射（MySQL -> DM）：`DOUBLE`→`DOUBLE`、`GEOMETRY`→`SYSGEO.ST_GEOMETRY`、`POINT`→`SYSGEO.ST_POINT`
3. 迁移时**不勾选**"使用默认数据类型映射关系"
4. 勾选"创建模式和表"，其他不勾
5. 最大保留次数改为 -1

### 通用操作

每个产品迁移后必须执行（先按停止条件 1 展示确认）：
```sql
update databasechangelog set MD5SUM = NULL;
commit;
```

### 各产品迁移对照表

| 产品 | MySQL 库名 | 达梦模式名 | 达梦用户名 | 配置文件路径 |
|------|-----------|-----------|-----------|-------------|
| MIS/UMA/MF | cgdb | DLMIS | DLMIS | `/egova/web/eUrbanXXX/WEB-INF/classes/jdbc.properties` |
| MIS/UMA/MF | cgdbstat | UMSTAT | UMSTAT | 同上（stat 配置） |
| GIS/MMS | giscenter | GISCENTER | DLMIS | `/egova/web/eUrbanGIS/WEB-INF/classes/jdbc.properties` |
| GIS/MMS | mms | MMS | DLMIS | `/egova/web/eGovaMMS/WEB-INF/classes/jdbc.properties` |
| 通图 | - | GISCENTER | DLMIS | `/egova/web/egovagisserver/giscenter.env` |
| 灵珑 | - | LINGLONG | LINGLONG | `/egova/apps/basic/linglong/linglong.env` |
| 用户中心 | - | USERCENTER | USERCENTER | `/egova/apps/basic/usercenter/usercenter.env` |
| 毕升 | - | DLMIS/UMSTAT | DLMIS | `/egova/apps/basic/evaluation/evaluation.env` |
| 全行业 | - | IBILITY | IBILITY | `/egova/apps/sg/ibility/ibility.env` |
| 悟空 | - | WUKONG | WUKONG | `/egova/apps/basic/wukong/wukong.env` |
| 明镜 | - | MJING | MJING | `/egova/apps/elaw/mjing/mjing.env` |
| 物联网 | - | EGOVAIOT | EGOVAIOT | `/egova/apps/iot/iot/application.properties` |
| 星桥 | - | DATACENTER2 | DATACENTER2 | dex 配置文件 |
| 玄奘 | - | XUANZANG_GIS | XUANZANG_GIS | `/egova/apps/gis/xuanzang/run.sh` |
| 采集服务 | - | DLMIS+UMSTAT | 复用 | `/egova/web/statgather/settings.py` |

> 机器可读版（供 `check_product_config.py` 使用）：`config/product-config-map.json`

### 星桥迁移特殊步骤

星桥与其他产品不同，流程为：
1. 先用空达梦库启动应用（让 liquibase 自动建表）
2. 再迁移数据，但**跳过三张表**：`com_license`、`databasechangelog`、`databasechangeloglock`
3. 迁移完成后重新启动

### 达梦 JDBC 通用参数

- 驱动类：`dm.jdbc.driver.DmDriver`
- Hibernate 方言：`org.hibernate.dialect.DmDialect`
- `hibernate.special_sql_type=1`（达梦使用 Oracle SQL 语句）
- URL 格式：`jdbc:dm://ip:5236` 或 `jdbc:dm://ip:5236?schema=模式名` 或 `jdbc:dm://ip:5236?clobAsString=true`

### Oracle 兼容参数速查（Oracle → 达梦必读）

> 适用 Oracle 体系迁移（如 eGovaMMS、悟能、玲珑）。参数建库时定死，迁移前规划好。

**dminit 初始化参数（建库后不可修改）**：

| 参数 | Oracle 迁移建议值 | 说明 |
|------|-----------------|------|
| CASE_SENSITIVE | **Y**（Oracle 体系）/ N（MySQL 体系） | 大小写敏感。Oracle 标识符默认大写且敏感，配错直接导致"无效列名" |
| PAGE_SIZE | 16 或 32 | 含长字符串字段的表建议 ≥16K；每条记录总长不能超过页大小一半 |
| LENGTH_IN_CHAR | Y | 字符串长度按字符计数，贴近 Oracle 习惯 |
| BLANK_PAD_MODE | 1 | 空格填充模式，1 与 Oracle 一致 |
| CHARSET | 按现场 | GB18030 省空间 / UTF-8（1）国际化 |

**dm.ini 参数（可后改，改后重启生效）**：

```sql
ALTER SYSTEM SET 'COMPATIBLE_MODE' = 2 SPFILE;   -- 兼容模式：0 不兼容 / 2 Oracle / 4 MySQL
ALTER SYSTEM SET 'CALC_AS_DECIMAL' = 1 SPFILE;    -- 整数相除保留小数（与 Oracle 一致）
ALTER SYSTEM SET 'ORDER_BY_NULLS_FLAG' = 1 SPFILE; -- 升序排序 NULL 排最后（与 Oracle 一致）
```

**JDBC 连接串兼容参数**：`jdbc:dm://ip:5236?compatibleMode=oracle`（或 `?comOra=true`）

**Oracle 语法兼容说明**：COMPATIBLE_MODE=2 后 CONNECT BY、(+) 外连接、NVL、DECODE、ROWNUM、序列 CURRVAL/NEXTVAL 等可直接使用；CONNECT_BY_ROOT、MODEL 子句等高级特性需验证或应用层改写。

### 迁移后验证

每个产品迁移完成后必须执行：
1. **对象数量对比**：`python scripts/verify_migration.py compare --baseline <源库.json> --target <达梦.json>`（表/视图/存储过程数量与关键表行数）
2. **配置核对**：`python scripts/check_product_config.py --profile config/product-config-map.json --root /egova`
3. **置空 MD5**：`update databasechangelog set MD5SUM = NULL; commit;`（先展示确认）
4. **应用启动验证**：启动应用，检查日志无数据库报错

> 手工验证 SQL 见 `references/migration_steps.md` 第 4.4 节

### 迁移后 SQL 调优

达梦 CBO 统计信息策略与 MySQL/Oracle 不同，迁移后建议：
- 手动收集统计信息：`DBMS_STATS.GATHER_SCHEMA_STATS('模式名', 100, TRUE, 'FOR ALL COLUMNS SIZE AUTO')`
- 关注慢查询，必要时通过 HINT 调整执行计划
- 建立性能基线对比，确保核心查询响应时间不低于迁移前 95%

## 阶段六：服务启动

> 各服务完整启停命令、domain 目录对照表、日志路径见 `references/service_management.md`；截图 08-12

| 服务类别 | 代表服务 | 管理方式 |
|---------|---------|---------|
| 中间件应用（AAS 体系） | eUrbanMIS/MF/UMA/GIS、eGovaMMS/Public、IMserver | domain 目录下 `startapusic` 启动，日志 `apusic.log.0` |
| 基础产品（systemd） | wukong、星桥(bigdata)、灵珑、用户中心、毕升、玄奘 | `service xxx status/start/stop/restart` |
| 脚本管理 | 悟能(wuneng)、新平台(newplatform)、采集服务(statgather) | 产品目录 `sh ./start.sh` / `bash startStatGather.sh` |
| 基础设施 | Kafka、ZooKeeper、Redis、Elasticsearch、Nacos、Eureka、MinIO | 多为 `service xxx start/stop`（ES 用 `./elasticsearch -d`，Eureka 用 systemctl） |
| 其他业务 | export、车载服务、eUrbanFac(V20)、fac(V22)、httpfileservice | `service` / `bash dm-start.sh` |

> **架构提示**：微服务架构（一键部署 v2 / 信创部署）下市政服务对应 `eUrbanFac`（V20）或 `fac`（V22），与传统 Tomcat 拆分架构的 `eUrbanMF` 不同，先确认现场架构再操作。
> 日志通用查看：`error.log` 为报错日志，`info.log` 为应用信息日志；AAS 日志在 `domains/<domain>/logs/apusic.log.0`。

## 关键注意事项

1. **dmdba 用户**：安装达梦必须用 dmdba 用户，禁止 root 安装
2. **置空 MD5**：每个产品迁移后都要执行 `update databasechangelog set MD5SUM = NULL`，否则应用起不来
3. **星桥特殊**：必须先用空库启动再迁移数据，且跳过三张表（`com_license`、`databasechangelog`、`databasechangeloglock`）
4. **政务网环境**：可能无法访问互联网，提前在能联网的服务器下载好安装包再上传
5. **密码统一**：文档中示例密码均为占位符 `{{DM_PWD_EXAMPLE}}`，实际部署替换为现场密码
6. **金蝶替换 Tomcat**：先在金蝶部署应用，再停止 Tomcat 上的应用，最后通过金蝶启动
7. **金蝶端口修改**：管理控制台 → 配置管理 → 对应实例 → 系统属性 → 修改端口，改后重启实例
8. **金蝶查看日志**：管理控制台 → 独立实例 → 服务器 → 查看原始日志
9. **毕升库选择**：部分现场毕升复用 DLMIS/UMSTAT，根据实际情况决定是否独立建库
10. **物联网目录定位**：如 `/egova/apps/iot/iot/` 路径不存在，查 `cat /etc/systemd/system/iot.service` 定位实际目录
11. **新服务器产品启动**：一键部署后产品可能启动失败，重点是确保 mysql/tomcat/nginx 环境存在即可，不要在此阶段耗费过多时间
12. **回滚预案**：迁移前备份源库全量数据（mysqldump），迁移失败回退 MySQL + Tomcat 环境；金蝶部署应用前先保留 Tomcat 配置备份；应用目录备份用 `scripts/backup_*.sh`
13. **字符集注意**：GBK→UTF8 迁移时中文字符字节变化（2→3）可能截断，需在迁移工具中设置字段长度扩展倍数
14. **多现场差异**：DM8 ISO/AAS 版本、表空间大小、备份策略等现场差异参数见 `config/site_profile.md`，执行前先确认现场档位

---

# 知识库检索（信创经验查询）

**检索架构**：`skill → MCP（zhengtong_query / precheck）→ demo redmine-assist → live vectors.db`（约 17 万工单 + 4500 篇知识库文档，每次同步后自动最新，skill 无需改动）。

## 检索工作流

1. **场景识别**：把用户问题归到"场景路由"表之一
2. **知识库检索**：优先 `scripts/kb_query.py`（公网 MCP 直调），返回工单 + 文档链接 + 避坑建议
3. **方案输出**：内置手册（六阶段/报错速查/playbooks）给出通用步骤 + 检索结果中的产品专项说明
4. **兜底**：MCP 不可用 → `scripts/query_xc.py` REST 降级 → SSH 直连 vectors.db 应急 → 互联网搜索

## 兜底策略优先级

| 优先级 | 手段 | 适用条件 |
|---|---|---|
| 1 | 内置手册速查（六阶段 + 报错速查表 + playbooks） | 通用常见问题 |
| 2 | MCP `zhengtong_query` / `precheck`（kb_query.py） | 知识库最新同步数据 |
| 3 | REST `query_xc.py` / 直连 vectors.db SQL | MCP 通道故障或个性化/罕见报错 |
| 4 | 互联网搜索（anysearch / websearch） | 以上均无结果，搜厂商文档/最新方案 |

## kb_query.py 用法（推荐）

```bash
# 政通问答：历史解决方案/实施经验/文档要点
python scripts/kb_query.py "达梦迁移后 liquibase 启动报 MD5SUM mismatch 怎么处理"

# 对接前置避坑：迁移启动前的场景级风险扫描（聚类高频问题模式 + 典型案件链接）
python scripts/kb_query.py "eGova产品信创迁移：MySQL替换达梦DM8、Tomcat替换金蝶AAS，麒麟V10" --tool precheck
```

token 配置：默认读 `D:\opencode\config\redmine-assist-mcp.json`（键 `auth.token`），或环境变量 `REDMINE_ASSIST_TOKEN`。**token 来自 /oauth/dingtalk/login 钉钉扫码，出现过期（401）时重新扫码更新配置文件**，不得绕过鉴权。调用细节（Bearer + Mcp-Session-Id、SSE 解析）见该配置文件 `call_recipe` 段。

## REST 降级（脚本模式）

无 MCP 客户端环境时：
```bash
python scripts/query_xc.py "灵珑迁移到达梦后视图查询报错怎么处理"
python scripts/query_xc.py --sweep "达梦 迁移" --out /tmp/xc_result
```
参数：`--host`（默认 https://demo.egova.com.cn/redmine-assist）、`--token`、`--out`、`--timeout`。

## 限速与错误

| HTTP | 含义 | 处理 |
|---|---|---|
| 200 | 成功 | 返回 markdown |
| 400 | query 缺失/超 4000 字 | 精简问题重试 |
| 401 | token 失效 | 重新扫码更新 token（停止条件 5） |
| 503 | cold load（服务重启后 ~8 min） | 8 分钟后重试 |
| 500 | 服务端错误 | 联系运维 |

端到端延迟 20-60 秒（含 LLM 精排）。

## 应急直连 vectors.db（仅调试，SSH 到 demo）

```bash
sqlite3 /opt/redmine-assist/data/vectors.db "SELECT issue_id,subject,status,updated_on FROM issues_meta WHERE subject LIKE '%达梦%' ORDER BY issue_id DESC LIMIT 50;"
sqlite3 /opt/redmine-assist/data/vectors.db "SELECT title,url FROM docs_meta WHERE title LIKE '%迁移%' ORDER BY title LIMIT 30;"
```

批量语义检索（KNN+LLM 精排）走 redmine-security-auto-fix 的 `similar_assist_bridge.py`（SSH→docker exec→容器内 sqlite-vec）。

## 互联网搜索兜底

以上均无结果时，用 `anysearch` / `websearch`（关键词组合：产品名 + "信创迁移"/"国产化"/"中间件" + 具体问题）：
达梦 https://eco.dameng.com/ ｜ 金仓 https://bbs.kingbase.com.cn/ ｜ 瀚高 https://www.highgo.com/ ｜ 海量 https://docs.vastdata.com.cn/ ｜ 金蝶 https://www.kingdee.com ｜ 东方通 https://www.tongweb.com.cn

## 场景路由

| 用户问题关键词 | 路由 | 落点 |
|---|---|---|
| 迁移流程/怎么迁/实施步骤 | 现场作业 | 本文"迁移流程总览"+ 六阶段 |
| 达梦 / DM8 / dameng | 现场作业 + 检索 | 阶段三/五 + playbooks B 章 |
| 人大金仓 / Kingbase / KES | 检索为主 | playbooks C 章 + zhengtong_query |
| 瀚高 / HighGo | 检索为主 | playbooks D 章 |
| 海量 / Vastbase | 检索为主 | playbooks E 章 |
| 金蝶 / Apusic 中间件 | 现场作业 + 检索 | 阶段四 + playbooks I.金蝶 |
| 东方通 / TongWeb 中间件 | 检索为主 | playbooks I.东方通 |
| 麒麟 / 欧拉 / UOS + 部署 | 检索 + 预检 | precheck_env.sh + playbooks G 章 |
| 鲲鹏 / 飞腾 / 海光 / ARM | 检索 | playbooks G 章 |
| 星桥 + 迁移 | 现场作业 | "星桥迁移特殊步骤" |
| 灵珑/毕升/明镜/用户中心/全行业 + 迁移 | 现场作业 | 各产品迁移对照表 |
| 采集服务 statgather / dmPython | 现场作业 | migration_steps.md 5.5 + 决策树补充分支 |
| 迁移报错 / 具体报错信息 | 速查 + 检索 | 常见报错速查表 → 决策树 → zhengtong_query |
| 迁移启动前评估 | 预检 + 检索 | precheck_env.sh + kb_query.py --tool precheck |
| 迁移完要验证 | 自动化 | verify_migration.py + check_product_config.py |
| 版本探测 / CVE | 旁路 skill | xinchuang-pkg-probe（本 skill 不做） |

## 参考文件索引

**现场作业（v2.0 自 quiz266 提交物沉淀，经脱敏）**
- `references/migration_steps.md` — 迁移步骤全文（达梦部署/DTS/各产品参数/采集服务 dmPython 切换）
- `references/service_management.md` — 全量服务启停手册（AAS/systemd/悟能/Nacos/Kafka/Redis/ES/MinIO）
- `references/image_catalog.md` — 77 张截图双向索引；`references/image_gallery_template.html` — HTML 图册模板；`assets/` — 截图本体
- `config/site_profile.md` — 多现场参数差异表（现场档位/占位符表）
- `config/product-config-map.json` — 16 产品配置机器可读映射（供 check_product_config.py）
- `references/xinchuang-cases.md` — 公司信创案件速查（2026-10-02 快照，活数据走 MCP）

**知识检索（v1.0 既有）**
- `references/migration-playbooks.md` — 常见迁移问题处理手册（A~J 章）
- `references/knowledge-index.md` — 知识索引（130 篇文档 + 精选工单 + 钉钉链接）
- `references/knowledge-index-docs.md` — 130 篇文档完整分类清单
- `references/key-docs-fulltext.md` — 23 篇关键文档全文（迁移步骤/报错处理/SQL）
- `references/robot-integration.md` — 信创迁移 × 工程中心应答机器人集成方案

**脚本**
- 见"自动化脚本总表"；测试在 `tests/`
