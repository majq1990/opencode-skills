# 金仓（KingbaseES V9）切换执行包 — 2026-10-14

本包把 cg156 上 web 应用的数据源从达梦切到金仓，并给出可复现的验证判据。
所有脚本都是**先 dry-run / 先预检，确认后才动真**；没有任何口令字面量，
口令一律从 600 权限的口令文件读。

**当前范围已按用户要求收窄为 eUrbanMIS 一个应用**（eUrbanUMA / IMserver 的
schema 映射没有默认值，不猜，这次不碰）。只想跑 eUrbanMIS 就看第 2.5 节，
一把跑完；要推全量应用才需要前面第 1、2 节那两个通用脚本。

| 文件 | 作用 | 会改东西吗 |
|---|---|---|
| `kb_health.py.txt` | **"金仓库是不是没了"只读体检**（七组证据，见第 8 节） | 不改 |
| `kb_rebuild.py.txt` | 库没了的重建 + 四 schema 重迁（默认 dry-run） | 加 `--apply` 才动 |
| `emis_kb.py.txt` | **eUrbanMIS 端到端一把跑完**（预检→切换→重启→验证） | 分段开关，见 2.5 |
| `test_emis_kb.py` | 上面这个的本机自测（21 项，全过） | 只在临时目录写 |
| `preflight_kb.py.txt` | 只读预检：枚举全部应用/数据源/端口/金仓端点/驱动 jar | 不改 |
| `switch_kb.py.txt` | 改写全部应用的 jdbc.properties（默认 dry-run） | 加 `--apply` 才写 |
| `verify_kb.py.txt` | 重启+探活+证明在读金仓数据 | 加 `--restart` 才重启 |
| `test_kb_scripts.py` | 通用三脚本的本机自测（24 项，全过） | 只在临时目录写 |

---

## 0. 当前唯一阻塞点：这台机器到 eGova 内网不通

切换本身随时能跑，卡在**我从本机连不上 cg156**。已实测排除的几种可能：

- sing-box（PID 61300，`singbox_tun` 172.18.0.1，默认路由 metric 0）把
  `172.21.0.0/16` 和 `8.130.175.100` 全截走：这些目标的**每一个端口**（含 1、19999）
  都是"TCP 连上 → 一发数据即 reset"。用 192.168.56.1:22/8080/19999 校准过，
  本机探针本身是准的，不是探针误报。
- 深信服 SSL VPN（以太网 4，2.0.1.3）路由表里**没有 `172.21.0.0/16`**，
  只有 10.x 与一批 192.168.x；即便 sing-box 不拦，包也出不去。
- VPN 放行的各网段（10.250/10.11/10.254/192.168.102/177/210/212/220/222/223）
  逐段普查全部超时，没有可用跳板；`10.255.1.25:8080` 出现过一次 200，
  复测 6 次全部 reset，判定为瞬时噪声，不算通路。

**解除办法（二选一，都要管理员权限，我做不了）：**

```
# A. 把 eGova 网段拉回 SSL VPN 通道（管理员 cmd）
route add 172.21.0.0 mask 255.255.0.0 2.0.1.4 metric 1

# B. 在 sing-box 配置里把 172.21.0.0/16 与 8.130.175.100/32 加进直连/绕过规则
```

你在自己机器上测过系统可访问，说明现场是通的；我这边一通，立刻按下面顺序跑完。

---

## 1. 传到 cg156 并预检

```bash
scp preflight_kb.py.txt root@172.21.133.156:/root/_kbkit/
ssh root@172.21.133.156 'python3 /root/_kbkit/preflight_kb.py.txt \
    --kb-host 127.0.0.1 --kb-port 54321 --kb-db test'
```

预检要盯的四件事（都是上一轮真实踩过的）：

1. **应用枚举按文件不按 tomcat**。4 个 tomcat 单元里塞了 6 个应用，
   按 tomcat 数必漏。预检直接扫 `/egova/web/*/WEB-INF/classes/jdbc.properties`。
2. **键名风格每个应用不一样**。`cryptogram`/`password`、
   `validationQuery`/`validation.query`、带不带 `mms.` 前缀都见过。
   照一个模板改会漏键，漏了 Spring 不读，等于没切还不报错。
3. **giscenter 不走 jdbc.properties**，它读 `giscenter.env` 里的
   `--DATASOURCE_URL=`。只改 properties 切不掉它。
4. **kingbase8 驱动产品不随包分发**，`WEB-INF/lib` 里没有；
   缺了启动即 `ClassNotFoundException`。

预检退出码 0 才往下走；有阻断项先处理。

---

## 2. 切换（默认 dry-run）

```bash
ssh root@172.21.133.156 'python3 /root/_kbkit/switch_kb.py.txt \
    --kb-host 127.0.0.1 --kb-port 54321 --kb-db test \
    --kb-pw-file /root/.kb_mig_pw \
    --map "eUrbanMIS:=CGDB,eUrbanMIS:stat=CGDBSTAT,eGovaPublic:biz=EGOVAPUBLIC"'
```

先看 dry-run 输出，确认每个前缀的 schema 都对，再加 `--apply`。

**脚本拒绝执行的两种情况**（不是故障，是防猜）：

- 有数据源没给 schema 映射 → 整体拒绝。猜错会把 A 库数据指到 B 库 schema，
  而且不报错，所以一律要显式 `--map`。
- 某前缀找不到口令键 → 拒绝。说明这个应用的文件格式和预期不同，
  先看预检报告再决定。

已内置的默认映射：`eUrbanGIS:""→CGDB`、`eGovaMMS:mms→MMS`、
`eUrbanMIS:biz→CGDB`、`eUrbanMIS:stat→CGDBSTAT`、`eGovaPublic:biz→EGOVAPUBLIC`。
**eUrbanUMA 和 IMserver 的映射没有默认值**，预检会列出它们的前缀，用 `--map` 补上。

每个文件改前自动备份为 `<原名>.bak.<时间戳>.dm`，属主/权限跟随原文件。

---

## 2.5 eUrbanMIS 一把跑完（当前收窄范围，推荐）

一条命令四个阶段，每阶段有门禁，前一阶段不过就不往下走：

```bash
scp emis_kb.py.txt root@172.21.133.156:/root/_kbkit/
# 第一步：只预检 + dry-run，什么都不改
ssh root@172.21.133.156 'python3 /root/_kbkit/emis_kb.py.txt'
# 第二步：确认 dry-run 输出无误后真切换（仍不重启）
ssh root@172.21.133.156 'python3 /root/_kbkit/emis_kb.py.txt --apply'
# 第三步：切换 + 重启 + 验证（重启不可逆，单独一个开关）
ssh root@172.21.133.156 'python3 /root/_kbkit/emis_kb.py.txt --apply --restart'
```

金仓端点默认 `127.0.0.1:54321/test`，是上一轮（2026-10-13 容器与 tomcat 同机）
的取值。**现场如果不是这个端点，用 `--kb-host/--kb-port/--kb-db` 显式指定**——
预检第一件事就是探这个端点，探不通直接阻断，不会带着错端点往下切。

数据源映射写死在脚本里且只有两个：`biz→CGDB`、`stat→CGDBSTAT`。
发现别的前缀**整体拒绝**，不猜——猜错会把 CGDB 的数据指到别的 schema 上，
而且不报错。

三个阶段各自的门禁：

| 阶段 | 拦什么 |
|---|---|
| 预检 | 端点不可达 / schema 不存在 / 缺驱动 jar / 缺 liquibase 桥接 jar / 找不到 tomcat 单元 |
| 切换 | 口令文件缺失或过短 / **写回后自检不过** |
| 验证 | HTTP 非 200 / 金仓侧无 mig 会话 / 3306 残留 / 日志异常 |

**"写回后自检"是这轮新加的**，专门拦一类最阴的错：键名错位。
回显看着"已写回"，实际 Spring 读的那个键还是旧值——详见下面第 7 节。

---

## 3. 金仓特有的四个坑（照顺序处理）

1. **驱动 jar**：`kingbase8-9.0.1.jar`（Maven Central `cn.com.kingbase:kingbase8:9.0.1`，
   字节码 major=52，JDK8 可用）放进每个 webapp 的 `WEB-INF/lib`，属主改 `egova:egova`。
2. **liquibase 桥接 jar（最关键）**：fork liquibase 内置 DMDatabase、PgSupportedHgDatabase、
   OscarDatabase，**唯独不认 KingbaseES**。`DatabaseFactory` 警告
   `Unknown database: KingbaseES` 后兜底 `UnsupportedDatabase`，它发 Oracle 风格
   `call current_schema`，金仓报 `syntax error at end of input`，**应用必死**。
   修法：打一个 1.8KB 桥接 jar，继承 fork 的 `com.egova.liquibase.database.PostgresDatabase`，
   `isCorrectDatabaseImplementation` 认领产品名含 kingbase，**shortName 不覆写**
   （保持 `postgresql`，changelog 里 `dbms="postgresql"` 的 property 分支才能生效），
   经 `META-INF/services/liquibase.database.Database` 走 ServiceLoader，
   放进两个 webapp 的 `WEB-INF/lib`。预检第五项就是查这个服务文件在不在。
3. **校验值修复 B1Fix**：金仓变体，URL 带 `currentSchema=cgdb`，上一轮实测
   replaceChecksum=48 处。不修则 liquibase 校验和不匹配，changeset 重跑或报错。
4. **空串即 NULL 兼容开关**：金仓默认把空串当 NULL，MySQL 里空串 ≠ NULL。
   迁移后要量化影响面（源库四库文本列逐列数空串单元格），
   再决定是否开 `ora_empty_string`。这一项是数据语义问题，**不在本次切换里动**，
   单独记录。

---

## 4. 验证

```bash
ssh root@172.21.133.156 'python3 /root/_kbkit/verify_kb.py.txt \
    --kb-host 127.0.0.1 --kb-port 54321 --kb-db test --restart --json /root/_kbkit/verify.json'
```

四条判据**全部满足**才算通过，缺一条不算：

1. 每个应用 HTTP 非 000/404/5xx；
2. 金仓 `pg_stat_activity` 出现该应用的连接池会话；
3. 打一遍业务页面后能抓到**真实业务 SQL**——只证明"连上了"不够，
   必须证明"在读迁移过来的数据"；连接池空闲抓不到 active 时，
   脚本自动退看 idle 会话的最近 query；
4. MySQL 3306 残留连接归零。

另外扫一遍 tomcat 日志的新增 Exception。

> `--restart` 是单独开关：重启是不可逆动作，默认不重启，
> 想先看拓扑和现状就裸跑一遍（只读）。

---

## 5. 回滚

```bash
# 每个应用把备份拷回原名
cp -p /egova/web/<app>/WEB-INF/classes/jdbc.properties.bak.<时间戳>.dm \
      /egova/web/<app>/WEB-INF/classes/jdbc.properties
systemctl restart <tomcat 单元>
```

驱动 jar 和桥接 jar 留着不碍事（达梦那轮也是混放的），不用删。

---

## 6. 一个刻意不改的东西

`hibernate.dialect` 一律保持 `MySQLDialect` 不动。三个已切应用都是这个口径，
单独改一个会造成不一致；方言问题是厂商系统性选择，作为独立缺陷记录，
不在切换里动。这一点和达梦那轮保持一致。

---

## 7. 本机自测抓出来的三个真 bug（都是"看着成功实际没切"的类型）

这三条不是测试写法问题，是脚本本身的缺陷，在现场跑会静默失败或永久卡死。
写进这里是因为它们都符合同一个模式：**回显说成功，盘面不是那么回事**。

### 7.1 口令/校验键按裸键名写成了顶层键（最严重）

`PWD_KEYS = ("jdbc.cryptogram", "jdbc.password")` 里存的是**裸键名**。
写盘时直接把裸名传给 `set_key`，于是文件末尾多出：

```
jdbc.cryptogram=kingbasepw123      ← Spring 不读这个
jdbc.validationQuery=select 1      ← 也不读这个
```

而真正被读的 `biz.jdbc.cryptogram` **原封不动还是 MySQL 口令**。
结果：应用拿旧 MySQL 口令去连金仓 URL，启动即认证失败，
而脚本还在打印"已写回，备份 → ..."。故障现象和根因完全不沾边，极难定位。

修法：键名一律走 `jk(pre, name)` 拼成完整名再写。同时加了写后回读自检，
逐项核对每个前缀的 url/driver/用户名/口令键，并显式检查"还有没有键指向 MySQL"、
"原口令是否还留在原键上"。

### 7.2 桥接 jar 预检永远不可能通过

原来的检查是 glob `WEB-INF/lib/META-INF/services/liquibase.database.Database`。
但桥接 jar **本身是个 jar**，没解压过，那个路径下什么都没有——
这个预检永远报"缺桥接 jar"，会把切换**永久卡死**在第一步，
而且看起来像一个真实的缺失，会让人去找一个根本不存在的文件。

修法：用 `zipfile` 逐个开 `WEB-INF/lib/*.jar`，看内部条目
`META-INF/services/liquibase.database.Database` 在不在、内容是否含 kingbase。

### 7.3 阻断项在进程里累积 + 阶段名永远显示"预检"

`FAILS` 是模块级列表、`STAGE` 在 `main()` 里是局部赋值——
同进程里第二次调用会把上一轮的阻断项带过来，且失败阶段永远显示"预检"
（因为 `report()` 读的是模块级的初始值）。单次执行看不出来，
但 skill 会被反复调用（预检、切换、验证各跑一次），必然踩到。

修法：`main()` 入口 `del FAILS[:]`，`global STAGE`。

### 7.4 附带：重复执行不再误报

修 7.1 的自检引入了新问题：`--apply --restart` 是第二次跑，此时文件已是金仓，
"还是原口令"检查会把金仓口令判成没换。而"先 dry-run 预检 → 再 `--apply`
→ 再 `--apply --restart`"正是标准用法。修法：检测到 url 已指向金仓就跳过写盘，
直接进后续阶段，也不再出新备份。

**共同教训**：切换类脚本的自检不能只查"新值写进去了没有"，
必须同时查"旧值还在不在原来的键上"。只查前者，键名一错就能全过。

---

## 8. "金仓库是不是没了"——怎么判、怎么重建

用户 2026-10-14 问的原话是"你测试一下，是不是金仓库没了？如果没了，重建重新迁移"。
这两个动作都做成了 skill 能力（`kb_health.py.txt` 判、`kb_rebuild.py.txt` 修），
不是一次性命令。

### 8.1 判：`kb_health.py`（只读，七组证据）

在 cg156 上跑，七组问题逐个给证据：

| 组 | 查什么 | 为什么这一项不够就会误判 |
|---|---|---|
| A | 容器 `kingbase` 在不在、跑没跑、54321 映射没映射 | `docker ps` 看不到 ≠ 一定没了，可能是改名了，所以按名字和端口双匹配 |
| B | 54321 端口 | **协议级**探活，不是裸 connect（见 8.4） |
| C | `mig` 连不上连、什么版本 | 连不上分三种：容器没起 / 角色没建 / 口令不对，报错文本不一样 |
| D | 四 schema 表数 + **抽样行数** | 只有表没有行 = 数据也没了，一样要重迁。只数表会把"空库"判成"健在" |
| E | 源库 MySQL cg155:3306 | 不通知就无法重迁；先确认再动手，别等到重迁一半才发现源库也够不着 |
| F | eUrbanMIS 当前指向哪个库 | 可能已经切了、可能回滚了，先看现状再决定要不要动 |
| G | kingbase8 驱动 jar + 桥接 jar | 这两个缺一个，应用起不来，且报错极具误导性（见第 3 节） |

退出码 0 = 健在，1 = 有问题并列出清单。`--json` 可落证据文件。

```bash
scp kb_health.py.txt root@172.21.133.156:/root/_keskit/kb_health.py
ssh root@172.21.133.156 'python3 /root/_keskit/kb_health.py'
```

### 8.2 修：`kb_rebuild.py`（默认 dry-run，`--apply` 才动真）

先只读体检判定"到底没了什么"，再按结论走对应动作，不一律推倒重来：

- 容器不在/没跑 → 起容器 + 建 `mig` 角色 + 四 schema 重迁
- 容器在但数据不全 → **不动容器**，只补角色和重迁
- 四 schema 表行都全 → 什么都不做，提示直接去跑 `emis_kb.py`

镜像名**一律从 `docker images` 发现，不硬编码**：没有实证记录它叫什么，
硬编码猜错会拉个不相干的镜像起来，跑一堆莫名其妙的问题。发现多个候选时不猜，
列出让人选；一个都没有就明确报"需 `--image` 指定"。

`mig` 角色重建用 `docker exec -e MIG_PW`（不带 `=值`）从父进程环境透传口令。
写成 `-e MIG_PW=值` 会把口令暴露在 docker 命令行里，`ps` 一眼看见。

```bash
# 先看体检结论，什么都不改
python3 kb_rebuild.py
# 确认后真重建真重迁
python3 kb_rebuild.py --apply
# 体检发现不了镜像时手工指定
python3 kb_rebuild.py --apply --image <镜像名>
```

`--recreate` 只在"容器在但表结构对不上"时加；**加之前先
`python3 engine_mysql_to_pg.py.txt --help` 核对引擎是否真收这个参数**，
没核对过别加——引擎参数列表没有实证记录。

### 8.3 重建完的固定收尾（脚本只提示，不自动做）

1. B1Fix 金仓变体修 liquibase 校验值（URL 带 `currentSchema=cgdb`，
   2026-10-13 实测 replaceChecksum=48）
2. 确认驱动 jar 与桥接 jar 在各 webapp 的 `WEB-INF/lib`（chown egova:egova）
3. `python3 emis_kb.py --apply --restart` 切 eUrbanMIS 并验证

### 8.4 又一个真 bug：裸 connect 把"库没了"报成"源库可达"

`kb_rebuild.py` 第一版用 `socket.create_connection` 探源库，本机干跑时
报 `源库 MySQL 可达（可重迁）`——**这是假阳性**。sing-box TUN 会替所有目标
完成 TCP 握手，包括 RFC 5737 保留测试网段（192.0.2.1、198.51.100.7）这种
不可能有主机的地址，实测全部"连上"；送数据才 reset。

修法：改成协议级探活——connect 之后 `recv`。MySQL 和 PostgreSQL/金仓都是
**服务端先说话**（连上立刻发握手/问候包），收到字节才是真服务，超时或
reset 就是没有。改完同一目标报"连上但 4s 无响应（代理伪造握手，非真服务）"。

`kb_health.py` 有同样的裸 connect，一并修了。

**这条对所有探测脚本都成立**：在带透明代理的机器上，`connect()` 成功
零信息量。要判"服务在不在"，必须至少完成一次应用层收发。
