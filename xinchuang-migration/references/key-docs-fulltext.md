# 关键迁移文档全文

## 447516 全行业数据库切换处理
URL: https://alidocs.dingtalk.com/i/nodes/Gl6Pm2Db8D3moL97i91YyGO3JxLq0Ee4?utm_scene=team_space

### chunk0 **1、背景**
[**1、背景**]
[http://faq.egova.com.cn:7777/issues/447516#](http://faq.egova.com.cn:7777/issues/447516#)

现场数据库之前是mysql， 后面换成了达梦，但是系统默认的数据源还是mysql, 导致无法查询到表。

### chunk1 **2、排查过程**
[**2、排查过程**]
查看数据源管理，发现全行业默认数据源无法连接：

[img]

数据库里面默认数据源状态也是未连接状态：

| [img] |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

### chunk2 **3、解决办法**
[**3、解决办法**]
1、手动将id=self\_datasource的全行业默认数据源替换为新的数据库：

select \* from ibility.colltable\_data\_source

[img]

id: self\_datasource

name:ibility\_self\_ibility

type:0-mysql 14-达梦

url: 数据库链接(可参考启动脚本里面数据库链接参数)
```sql
mysql:
jdbc:mysql://ip:port/db?useUnicode=true&characterEncoding=utf-8&useSSL=false&serverTimezone=GMT%2B8&autoReconnect=true&connectTimeout=60000&socketTimeout=3600000&allowMultiQueries=true&reWriteBatchedInserts=true

达梦：
jdbc:dm://ip:port?clobAsString=true
```

user\_name:用户名

password: 密码（可以填明文或者加密后的）

status :填1

disable: 填0

2、重启全行业系统

3、自测验证

[img]

[img]

4、注意：

数据库迁移建议保持大小写一致！

## 全行业数据库切换处理
URL: https://alidocs.dingtalk.com/i/nodes/Obva6QBXJw9l1j5KS2GpoPn3Wn4qY5Pr?utm_scene=team_space

### chunk0 
全行业数据库切换处理

### chunk1 全行业数据库切换处理
[全行业数据库切换处理]
【相关任务】#447516

注意：数据库迁移过程中需要保持大小写一致！

【问题描述】全行业从默认的mysql数据库切换为其他数据库，但是系统中的全行业数据源没有同步修改，导致操作系统时提示找不到表

ibility\_self\_iblility 处置连接失败状态

[img]

数据库中全行业数据源也是未连接状态[img]

【解决方案】

mysql: jdbc:mysql://10.255.18.23:3306/ibility?useUnicode=true&characterEncoding=utf-8&useSSL=false&serverTimezone=GMT%2B8&autoReconnect=true&connectTimeout=60000&socketTimeout=3600000&allowMultiQueries=true&reWriteBatchedInserts=true 达梦： jdbc:dm://10.255.18.49:5339?clobAsString=true

1、 手动将id=self\_datasource的全行业默认数据源替换为新的数据库：

select \* from ibility.colltable\_data\_source

[img]

id: self\_datasource

name:ibility\_self\_ibility

type:0-mysql 14-达梦

url: 数据库链接(可参考启动脚本里面数据库链接参数)

user\_name:用户名

password: 密码（可以填明文或者加密后的）

status :填1

disable: 填0

2、配置项完成修改后，重启全行业服务

[img]

## 明镜_迁移达梦后字段内容后补全空格问题处理
URL: https://alidocs.dingtalk.com/i/nodes/Gl6Pm2Db8D3moL97i9bQdK4YJxLq0Ee4?utm_scene=team_space

### chunk0 
明镜\_迁移达梦后字段内容后补全空格问题处理

原始链接： https://faq.egova.com.cn:7787/projects/redmine/wiki/%E6%98%8E%E9%95%9C\_%E8%BF%81%E7%A7%BB%E8%BE%BE%E6%A2%A6%E5%90%8E%E5%AD%97%E6%AE%B5%E5%86%85%E5%AE%B9%E5%90%8E%E8%A1%A5%E5%85%A8%E7%A9%BA%E6%A0%BC%E9%97%AE%E9%A2%98%E5%A4%84%E7%90%86

### chunk1 明镜 迁移达梦后字段内容后补全空格问题处理
[明镜 迁移达梦后字段内容后补全空格问题处理]
【问题描述】

明镜数据库从mysql库迁移到达梦数据库，因数据库兼容问题，char类型字段内容会自动用空格补全

[img]

【解决办法】

达梦明镜库下执行sql

select 'alter table mjing.'\|\|b.name \|\|' modify '\|\|a.name\|\|' varchar('\|\|length\$\|\|');', 'update mjing.'\|\|b.name\|\|' set '\|\|a.name\|\|'=RTRIM('\|\|a.name\|\|');'

from syscolumns a,sysobjects b where a.id=b.id and a.type\$='CHAR' and (b.name not  like 'SYS%' and b.name not  like 'VSYS%' and b.name not  like 'ALL\_%')

生成两条sql语句，分别执行生成的sql

先执行左边sql，把cha字段类型改为varhcar，再执行右边sql，类型转换后去掉字段的空格内容[img]

## 明镜_信创环境部署
URL: https://alidocs.dingtalk.com/i/nodes/14lgGw3P8vvl1M5XTpyO3ekM85daZ90D?utm_scene=team_space

### chunk0 
明镜\_信创环境部署

原始链接： https://faq.egova.com.cn:7787/projects/redmine/wiki/%E6%98%8E%E9%95%9C\_%E4%BF%A1%E5%88%9B%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2

### chunk1 明镜 信创环境部署
[明镜 信创环境部署]
--达梦

\[\[明镜\_数据库mysql迁移达梦\]\]

--人大金仓

--瀚高

\[\[明镜\_数据库mysql迁移瀚高\]\]

## 明镜_数据库mysql迁移达梦
URL: https://alidocs.dingtalk.com/i/nodes/MNDoBb60VLrOowp4SB0LEz0X8lemrZQ3?utm_scene=team_space

### chunk0 
明镜\_数据库mysql迁移达梦

原始链接： https://faq.egova.com.cn:7787/projects/redmine/wiki/%E6%98%8E%E9%95%9C\_%E6%95%B0%E6%8D%AE%E5%BA%93mysql%E8%BF%81%E7%A7%BB%E8%BE%BE%E6%A2%A6

### chunk1 明镜 数据库mysql迁移达梦
[明镜 数据库mysql迁移达梦]
迁移操作，参考wiki

MySQL迁移达梦实施规范（主wiki）

迁移注意事项：

1.驱动包，mysql和达梦，指定驱动，都需要使用最新的驱动包，可在附件中下载

[img]

[img]

2.保持对象名大小写，不勾选使用默认数据类型映射关系，并增加double类型到double类型的映射

[img]

[img]

3.分两步迁移，先迁移表结构

[img]

[img]

4.后迁移数据

[img]

5.两类报错可以不处理

[img][img]

6.数据迁移失败需要手动处理

从mysql中将数据复制成insert语句，在达梦库中执行进去，执行过程中若有报错，再针对性解决，最终需要确保数据成功执行进去

[img]

7.遇到报错如下，可以对相关表执行sql后，再次迁移对应表的数据

[img]

SET IDENTITY\_INSERT mjing.sys\_nav on;

8.char类型字段转为varchar类型，并删除字段内补全的空格内容

\[\[明镜\_迁移达梦后字段内容后补全空格问题处理\]\]

## 排水国产化部署注意事项
URL: https://alidocs.dingtalk.com/i/nodes/MNDoBb60VLrOowp4SBe1KxLL8lemrZQ3?utm_scene=team_space

### chunk0 
海量基准库：[http://oneops.egova.com.cn:8093/one/benchbasedb/shengmingxian/drainage/海量/drainage.sql](http://oneops.egova.com.cn:8093/one/benchbasedb/shengmingxian/drainage/海量/drainage.sql)

1、drainage.env文件连接方式按实际数据库调整

海量数据库：

--DATASOURCE\_DRIVER=org.postgresql.Driver --DATASOURCE\_URL=jdbc:postgresql://10.59.21.147:15432/drainage?currentSchema=drainage&serverTimezone=Asia/Shanghai&allowMultiQueries=true&autoReconnect=true&failOverReadOnly=false&useUnicode=true&characterEncoding=utf8&stringtype=unspecified --DATASOURCE\_USERNAME=vbadmin --DATASOURCE\_PASSWORD=Vbase@admin \\

2、清空排水数据库中drainage\_changelog、databasechangelog、usercenter\_remote\_databasechangelog三个表的MD5SUM值

3、连接排水数据库的相关灵珑应用调整数据源

[img]

## 毕升系统数据从MySQL迁移到达梦
URL: https://alidocs.dingtalk.com/i/nodes/G1DKw2zgV2RXpGMNTBQqMlyMVB5r9YAn?utm_scene=team_space

### chunk0 
**原文来自案卷平台wiki：https://faq.egova.com.cn:7787/projects/redmine/wiki/毕升系统数据从MySQL迁移到达梦**

### chunk1 毕升系统数据从MySQL迁移到达梦
[毕升系统数据从MySQL迁移到达梦]
**【前提条件】已部署达梦版本毕升微服务，请参考\[\[毕升手动部署v2智信云版本\]\]、\[\[毕升手动部署v2麒舰版本\]\]**

**【创建用户】1.如果现场的毕升是独立库becensus，则在达梦创建becensus用户2.如果现场的毕升不是独立库，是cgdbstat或者zfdbstat等，则按照智信云的要求创建用户**

**【操作说明】迁移前，先确认：\[\[MySQL迁移达梦注意事项\]\]，确认是否有字符长度问题如果字符没有问题，则正常迁移表及数据即可，如果有问题，则先迁移表，再迁移数据，以下操作参考，不是基于最新达梦版本截图。**

1\. 打开达梦数据迁移工具

[img]

2\. 新建工程，填写工程名和工程描述，点击“确定”

[img]

3\. 选中“迁移”，右键选择“新建迁移”

[img]

新建迁移框中填写迁移名称、迁移描述，点击“确定”

[img]

4\. 点击“下一步”

[img]

5\. 迁移方式选择“MySQL-&gt;DM”，点击“下一步”

[img]

6.填写MySQL数据库信息和达梦数据库信息

[img]

[img]

**7\. 【指定对象】页面，选择“从数据源复制对象”，勾选源模式并确认目的模式正确，勾选“保持对象名大小写”，点击“下一步”**

[img]

**8\. 【 选择迁移对象】页面，勾选需迁移数据的表**

[img]

**9\. 选中源对象表名，点击下方的“转换”菜单，弹出【设置表映射关系页面】**

[img]

**10\. 设置数据选项，点击“应用当前选项到其他同类对象”弹出【选择对象】页面，可将当前的设置应用到其他表设置中**

[img]

最新版本的达梦，还需要勾选使用IDENTITY自增列，避免表的自增在迁移时丢失

[img]

### chunk2 毕升系统数据从MySQL迁移到达梦
11.设置完后选中所有的表名点击“转换”进行检查，确保设置正确

**12\. 【审阅】页面可再次检查源数据库、目的数据和迁移表，确认后点击右下角的“完成”**

[img]

13\. 迁移任务结束，可查看迁移数据情况，导出数据和导入数据是否一致有报错可点击“查看详细信息”进行错误问题查看和错误数据查看

[img]

14\. 迁移完成后，查看达梦数据库数据是否正确，达梦环境毕升系统数据是否正确，可视化平台是否正常使用

[img]

15\. 数据源、数据类型修改（1）打开配置平台，修改业务库和统计库配置，确保连接成功

[img]

（2）数据视图中点击“刷新字段”，将视图、报表和查询中的字段类型刷新为oracle字段类型

[img]

FAQ1、liquibase执行报错，如“Change failed validation”，或者check sum值不一致。

[img]

解决办法：去毕升库执行语句，如果大量记录发生变化，就全把MD5SUM 设置为null: UPDATE DATABASECHANGELOG SET MD5SUM = null如果就只有几条报错，就指定id设置MD5SUM为null： UPDATE DATABASECHANGELOG SET MD5SUM = null where id =&#39;xxxxx&#39;

### chunk3 毕升系统数据从MySQL迁移到达梦
UPDATE becensus.databasechangelog SET MD5SUM=&#39;9:82369cb4248d95d5c5889f38cdef09a9&#39; where id =&#39;dsscp-20201230-1631&#39;;UPDATE becensus.databasechangelog SET MD5SUM=&#39;9:d41d8cd98f00b204e9800998ecf8427e&#39; where id =&#39;dsscp-20210514-1500&#39;;UPDATE becensus.databasechangelog SET MD5SUM=&#39;9:d41d8cd98f00b204e9800998ecf8427e&#39; where id =&#39;dsscp-20210514-1501&#39;;

## 切换国产化数据后启动报错
URL: https://alidocs.dingtalk.com/i/nodes/14lgGw3P8vvl1M5XTQRk0RvP85daZ90D?utm_scene=team_space

### chunk0 
切换国产化数据库后启动报错

2026-03-20 16:20:34,434 ERROR \[main\] org.springframework.beans.factory.BeanCreationException: Error creating bean with name 'statSpringLiquibase' defined in class path resource \[cn/com/egova/liquibase/StatLiquibaseConfig.class\]: Invocation of init method failed; nested exception is liquibase.exception.CommandExecutionException: liquibase.exception.ValidationFailedException: Validation Failed:
3 changesets check sum

[img]

解决方法：复制上述报错后面的内容，更新到数据库里，以下sql为示例，然后重启服务

[img]

UPDATE becensus.databasechangelog SET MD5SUM='9:82369cb4248d95d5c5889f38cdef09a9' where id ='dsscp-20201230-1631';

## MySQL迁移至KingbaseES操作说明
URL: https://alidocs.dingtalk.com/i/nodes/R1zknDm0WR3eownji2XM36oDVBQEx5rG?utm_scene=team_space

### chunk0 
MySQL迁移至KingbaseES操作说明

原始链接: https://faq.egova.com.cn:7787/projects/redmine/wiki/MySQL%E8%BF%81%E7%A7%BB%E8%87%B3KingbaseES%E6%93%8D%E4%BD%9C%E8%AF%B4%E6%98%8E

### chunk1 MySQL迁移至KingbaseES操作说明
[MySQL迁移至KingbaseES操作说明]
**【背景说明】**

本文主要针对mysql数据库数据迁移kingbase数据库相关操作进行指引说明。**详细的软件安装说明可以见附件中的官方文档。**

**【前提说明】**

**1.已安装好人大金仓数据库，已新建数据库以及模式，具体参考：** **基于Linux系统的人大金仓数据库软件安装说明** **数据库实例创建操作说明**

2.MySQL迁移至KingbaseES需要借助工具：

客户端迁移小工具KDTS（数据迁移工具），具体安装可以参考wiki: 基于windows系统的人大金仓数据库软件安装说明 （其中完全安装，客户端安装都包含该小工具，也可以定制化单独安装该小工具）。

**注意：先使用KDTS工具迁移表结构，表数据，索引，视图等，然后迁移不成功的视图和函数通过直接执行sql处理，详细参考：** **人大金仓数据库函数视图存储过程sql**

**特别说明：迁移前** **需要安装postgis扩展**

现场需要联系人大金仓技术支持人员发送配套的包，因人大金仓数据库版本和服务器系统版本，postgis版本都有关系，不同版本对于的postgis插件不同。

如果自行安装 ：公司环境所使用postgis插件版本：postgis-3.1.2\_X86\_V008R006C008B0014.tar.gz

1、解压插件包，将插件包的 bin、lib、share/extension 目录下的文件全部依次拷贝到数据库安装目录的 Server/ bin、Server/lib、Server/share/extension 下

2、在所在的 数据库模式 下执行：CREATE EXTENSION postgis; （提前建好数据库和数据库模式，模式名称建议和数据库名称同名）

### chunk2 MySQL迁移至KingbaseES操作说明
3、检查所在模式的扩展和数据类型目录下是否有gis类型，如下图，表示安装成功

[img][img]

**【数据迁移工具KDTS操作说明】**

数据迁移工具支持迁移的数据库版本：MySQL 5.X、8.X，KingbaseES V7、V8R3、V8R6。

**小工具启动入口有两种：**

**方式一：从导航进入**

[img]

点击后系统自动启动小工具进程

[img]

上述Console页面会给出小工具浏览器访问的入口，以及默认用户名和密码。上图所示访问地址为： http://localhost:8080 用户名/密码：kingbase/kingbase

**方式二：使用免安装包**

kdts免安装包下载地址： 点击下载

直接点击bin目录下的.bat文件运行即可，然后访问： http://localhost:54523 用户名/密码：kingbase/kingbase

注意：启动后不要关闭后台进程。

[img]

以上两种方法都可以启动后台进程，建议使用免安装，免安装版本相对高一点 。

**【迁移步骤】**

在浏览器窗口输入上述访问地址，进入小工具web端操作台，输入用户名和密码登录

[img]

（1）配置源数据库

进入“数据源管理--源数据库”-【新建】源数据库的基本信息（允许编辑修改）。测试此数据源是否连接成功，连接成功将会弹出“测试连接成功”提示框。

[img]

[img]

（2）配置目标数据库

进入“数据源管理--目标数据库”-【新建】目标数据库的基本信息（允许编辑修改）。测试此数据源是否连接成功，连接成功将会弹出“测试连接成功”提示框。[img]

（3）配置迁移任务

1.进入“迁移任务管理--迁移任务”，【新建】迁移任务。

[img]

[img]

### chunk3 MySQL迁移至KingbaseES操作说明
2.选择模式：默认勾选要迁移的数据库全部内容。 选择的模式必须先安装好postgis，参考本文的前提说明，否则会有部分表迁移失败。

[img]

下图为：未给模式安装postgis导致找不到geometry类型，当出现以下失败，可安装postgis插件后，手动再次执行。

[img]

[img]

3.选择迁移对象：一般是选择【全部】；

[img]

**特别说明：当库太大，可以选择【包含指定对象】，需要创建多个迁移任务，选择每次要迁移的表**

[img]

[img]

同时如果用同一个迁移任务会给出下图所示的提示，本次迁移覆盖前一次迁移结果。

[img]

4.配置参数

（1）迁移配置-源数据库配置：

[img]

（2）源库配置中可以同步配置kdms转换视图，函数，存储过程等信息：

[img]

（3）目标数据库配置：

[img]

（4）数据类型映射

bit类型需转换成int，否则会有报错 ，并全部勾选所有数据类型

[img]

（5）线程配置：

[img]

4.正式迁移数据

配置迁移任务后点击【保存并迁移】开始迁移。可以通过列表“状态”知道迁移成功或失败。

[img]

5.查看迁移结果

可以点击列表【详情】按钮进入“结果查看”页面查看详细信息。

[img]

如果迁移有错误，可以点击操作-错误日志查看详情

[img]

5.目前20230301版本人大金仓数据库迁移结果如下，失败的视图和函数执行sql处理： 人大金仓数据库函数视图存储过程sql

业务库：[img]

统计库：

[img]

6.迁移完成后部署智信云相关服务，参考： 智信云应用连接人大金仓数据库配置说明

7.迁移完成后，麒舰需要处理的内容如下，原因：人大金仓会将空字符串识别为null，需要关闭

### chunk4 MySQL迁移至KingbaseES操作说明
| -- 修改配置ALTER SYSTEM SET ora\_input\_emptystr\_isnull = off;SELECT sys\_reload\_conf(); |
|----------------------------------------------------------------------------------------------|

[img]

──────────────────────────────────────────────────

通过实践下述方式导出的sql语句在金仓数据库中执行失败，暂不推荐使用下面的方式处理，可能有一定的用处，暂保留（20231009记录）。

【在线浏览器迁移工具KDMS操作说明】

该工具支持迁移的数据库版本：MySQL5.5及以上。支持的浏览器：建议Chrome75版本及以上浏览器，IE浏览器不支持。

**【安装前提】：**

**1.软件包及用户手册下载地址详见百度云盘：**

**链接: https://pan.baidu.com/s/1qBswBdorxZuPMLrNfeUMtQ?pwd=uktk 提取码: uktk**

官方下载数据采集工具和手册地址： https://bbs.kingbase.com.cn/thread-116-1-1.html 。

[img]

[img]

MySQL数据的采集请参考《数据库迁移评估使用手册》的3.2.

[img]

2. **该工具主要用于迁移视图，函数，存储过程等，如果前面在KDTS工具中已做了KDMS的迁移，就可以忽略不用再次操作。**

【安装步骤】

1.双击“KingbaseDMS-mysql.exe”，系统启动正常后给出Console页面默认访问地址： http://localhost:9003

[img]

### chunk5 MySQL迁移至KingbaseES操作说明
[img]

2.新建采集项目

[img]

3.开始采集任务（ 注意 ：使用root用户进行采集，也就是配置mysql用户名为：root）

创建项目后系统自行发起采集

[img]

4.校验并下载采集数据

[img]

[img]

导出的采集数据，解压后如下图所示。 **不同采集项目的** **dat** **文件不可混用** 。

[img]

5.MySQL数据采集完成后，进行评估:

**(1)访问浏览器：https://bbs.kingbase.com.cn/，需要自行注册，注册成功后登录点击【数据库迁移评估】。**

[img]

(2)进入评估管理系统的“数据库迁移--评估管理”，【新建评估】，上传第4步采集的ZIP包，填写其他必填项，点击【确定】。

[img]

(3）等待评估进度为100%。

[img]

转换有失败的情况，点击【详情】查看。[img]

一般失败原因为以下2种：

[img]

查看【对象详情】时，可以根据失败原因筛选过滤失败对象。[img]

为进一步了解报错情况，可以点击【查看详情】。

[img]

（4）评估完成后可以下载对象语句在金仓数据库中执行：

[img]

[img]

[img]

（5）金仓数据库中执行sql

## 数据中心10迁移到达梦
URL: https://alidocs.dingtalk.com/i/nodes/YQBnd5ExVEwmoLDOs039vvvk8yeZqMmz?utm_scene=team_space

### chunk0 
数据中心10迁移到达梦

原始链接: https://faq.egova.com.cn:7787/projects/redmine/wiki/%E6%95%B0%E6%8D%AE%E4%B8%AD%E5%BF%8310%E8%BF%81%E7%A7%BB%E5%88%B0%E8%BE%BE%E6%A2%A6

### chunk1 数据中心10迁移到达梦
[数据中心10迁移到达梦]
**【应用场景】**

大数据中心1.0已经部署的项目因为已经存在数据，所以，需要采用迁移数据库的方式，从MySQL迁移到达梦库。

以下列出的迁移方法也适用于星桥和大数据中心2.0。

大数据中心1.0用户：LAKE

大数据中心2.0用户：DATACENTER

星桥用户：DEX

**【迁移说明】**

本机能内网连接达梦的服务器数据库，本地安装达梦数据库，目的是利用自带的工具，直接在本机利用达梦官方迁移工具进行迁移；

数据库选择和服务器相同的版本，根据自己操作系统下载对应系统版本。

1、官网首页下载的均为试用开发版本，参考官方文档安装: 达梦数据库安装官方文档

《达梦数据库管理系统安装手册.pdf》

[img] \[图片加载失败: https://faq.egova.com.cn:7787/ueditor/themes/default/images/spacer.gif\]

安装完成。

[img]

**【迁移准备】**

1.准备好达梦库实例，一般项目上由达梦方提供；可参考：\[\[达梦数据库实例创建\]\]

确认一下实例是否按照我方要求建立，具体要求和操作如下：

1） 大小写敏感：否；

2） 字符集编码：UTF-8；

3） 长度以字符为单位：是；

4） 实例运行时区：\+8:00；

2.创建用户LAKE，可参考：\[\[达梦创建用户\]\]

**【开始迁移】**

1.数据库实例使用LAKE连接

2.打开DM数据迁移工具；

[img]

右键新建工程

[img]

[img]

按照上面设置数据类型映射后新建迁移

[img]

[img]

3.在列表里选中迁移任务，点击【下一步】

[img]

4.选择Mysql向DM迁移

[img]

填写源端MySQL库的连接参数

[img]

### chunk2 数据中心10迁移到达梦
填写目标端达梦库的连接参数， 注意用户使用LAKE

[img]

5.按下图勾选，大数据中心1.0没有“视图”需要迁移。 目的模式改成LAKE

[img]

6.下图中点击【选择】，确认所有的表都被选中，点击【下一步】

[img]

下图中查看无误，勾选“以文本方式显示执行任务”，点击【完成】

[img]

迁移完成。

7.错误处理

会出现一些报错，需要完整保存这些报错内容，然后单独进行处理。

保存完报错后，可以关闭迁移工具，处理迁移报错的问题。

也可以根据下面的几个按钮分别查看错误数据和日志。

[img]

查看出错的详内容。

[img]

**【更换databasechangelog表】**

星桥和大数据中心2.0数据库迁移需要更换databasechangelog表，表格见附件DATABASECHANGELOG.sql。更换时需要确认模式名一致。 更换后重启服务。

[img]

**【迁移报错处理】**

1.迁移错误文档中会有每个建表失败的sql，需要修改所有sql，常见的错误主要是**时间默认为** **“0000-00-00 00:00:00”****的错误****，解决办法是修改时间默认为****sysdate****，或者修改为一个具体的时间。**

**其他建表错误请反馈测试或研发。**

**在处理建表错误语法的同时，新建一个****txt****文档，保存每个处理的表名，方便后续继续迁移这些表的数据。**

2.**时间默认为** **“0000-00-00 00:00:00”****的错误**

1）用notepad工具打开报错的文档，用sysdate替换'0000-00-00 00:00:00'

[img]

将替换后建表语句复制到达梦管理工具下执行建表语句

[img]

### chunk3 数据中心10迁移到达梦
2.此类报错，为表已存在索引或约束，因此出现报错。

**此类报错无需处理。**

[img]

3.字段超长报错

迁移过程中，存在数据长度超过达梦元表字段的定义长度，从而出现**“记录超长”的报错**。

解决办法：右键报错的表，设置【启用超长记录】，重新迁移数据即可。

[img]

## 星桥迁移达梦库步骤
URL: https://alidocs.dingtalk.com/i/nodes/Gl6Pm2Db8D3moL97iGK0pq5QJxLq0Ee4?utm_scene=team_space

### chunk0 
星桥迁移达梦库步骤

原始链接: https://faq.egova.com.cn:7787/projects/redmine/wiki/%E6%98%9F%E6%A1%A5%E8%BF%81%E7%A7%BB%E8%BE%BE%E6%A2%A6%E5%BA%93%E6%AD%A5%E9%AA%A4

### chunk1 星桥迁移达梦库步骤
[星桥迁移达梦库步骤]
**--egova.liquibase.dm.varchar.scaleFactor=4** 参考： 系统上线第一步 \| 如何正确的第一次更新统计信息 \| 达梦技术社区 select 'DBMS\_STATS.GATHER\_SCHEMA\_STATS('''\|\|username\|\|''',100,TRUE,''FOR ALL COLUMNS SIZE AUTO'');' from all\_users; --这里我们一般选择需要收集的用户对应的行，进行执行即可。 -- 在同一个窗口中复制结果集，执行完成即可。验证：-- 查找统计信息更新一天内的表 SELECT OWNER, TABLE\_NAME, LAST\_ANALYZED, DATEDIFF(DAY, LAST\_ANALYZED, SYSDATE) AS DAYS\_SINCE\_LAST\_ANALYZED FROM DBA\_TABLES WHERE DATEDIFF(DAY, LAST\_ANALYZED, SYSDATE) \  30; -- 查找统计信息缺失的表 SELECT OWNER, TABLE\_NAME, LAST\_ANALYZED, DATEDIFF(DAY, LAST\_ANALYZED, SYSDATE) AS DAYS\_SINCE\_LAST\_ANALYZED FROM DBA\_TABLES WHERE LAST\_ANALYZED is null ; -- 我们更新后，第一步应该能找到表，第二步、第三步不应该还有找到的业务相关表！--egova.liquibase.dm.varchar.scaleFactor=4

适用范围：MySQL环境迁移至达梦。

人大金仓、瀚高也适用该方案。

星桥从mysql迁移到达梦，步骤如下：

### chunk2 星桥迁移达梦库步骤
**1、****更新MySQL环境，星桥版本在1.7.3.45及以上**

（低于此版本，联系测试人员蓝希鹏支持更新，如果更新了版本则需用新版本先把Mysql环境跑起来）

**2、达梦环境星桥版本同上，保持一致**

**（1）** **建空库**

**（2）星桥** **配置文件中增加启动参数**

[img]

**（3）从空库启动星桥**

正常情况下应当能正常启动完成。

**3、迁旧数据：从mysql迁移表至达梦库，** **com\_license、databasechangelog、databasechangeloglock三张表不迁移（目的是为了保留达梦的changelog表数据）**

[img]

[img]

注意：主键冲突选择覆盖。

[img]

以下报错不需理会。

[img]

**4、license授权**

\[\[星桥大数据中心20系统授权\]\]

**5、迁移数据库后首次刷新**

问题：[img]
- [img]

此类大概率为表字段映射不全导致，针对迁移失败的表检查字段映射后重新迁移

[img]

[img]

迁移后账号登录401问题，也大概率未com\_permission表和com\_schema表没有正确迁移导致（部分版本的DM迁移工具存在BUG，即使显示迁移成功，也有可能数据不匹配，如将A字段值迁移到了B字段）。

[img]

**常见问题及解决方案**

1.迁移错误文档中会有每个建表失败的sql，需要修改所有sql，常见的错误主要是时间默认为 “0000-00-00 00:00:00”的错误，解决办法是修改时间默认为sysdate，或者修改为一个具体的时间。

其他建表错误请反馈测试或研发。

在处理建表错误语法的同时，新建一个txt文档，保存每个处理的表名，方便后续继续迁移这些表的数据。

### chunk3 星桥迁移达梦库步骤
2.时间默认为 “0000-00-00 00:00:00”的错误

1）用notepad工具打开报错的文档，用sysdate替换'0000-00-00 00:00:00'

[img]

将替换后建表语句复制到达梦管理工具下执行建表语句

[img]

2.此类报错，为表已存在索引或约束，因此出现报错。

此类报错无需处理。

[img]

3.空库启动报错，字段超长请先确认数据库设置正确，新版本达梦空库启动时，星桥启动脚本中需要添加启动参数--egova.liquibase.dm.varchar.scaleFactor=4

a. 关闭默认聚簇索引 \[-3243\]:表\[TEST\]中不能同时包含聚集KEY和大字段；能通过改数据库参数处理这个问题吗 \| 达梦技术社区

b. 确认字符编码，以及字符长度单位配置正确： 达梦环境数据库创建 - FAQ - 政通项目管理平台 [img][img]达梦在2024年第二季度后，**取消了长度以字符为单位配置**，若达梦为最新版本，则在迁移时手动配置字符长度缩放大小，如下图所示：[img]注意此版本达梦空库启动星桥时，须在启动参数中添加

若以上配置正确空库启动仍存在问题，可以先通过DM迁移工具，将表结构先迁移到空库（不包括表数据、约束、索引），再尝试启动星桥即可。

**FAQ**

其他参考文档：\[\[星桥数据由mysql迁移到达梦\]\]

## 星桥数据迁移至人大金仓
URL: https://alidocs.dingtalk.com/i/nodes/MNDoBb60VLrOowp4SPDXnrzr8lemrZQ3?utm_scene=team_space

### chunk0 
星桥数据迁移至人大金仓

原始链接: https://faq.egova.com.cn:7787/projects/redmine/wiki/%E6%98%9F%E6%A1%A5%E6%95%B0%E6%8D%AE%E8%BF%81%E7%A7%BB%E8%87%B3%E4%BA%BA%E5%A4%A7%E9%87%91%E4%BB%93

### chunk1 星桥数据迁移至人大金仓
[星桥数据迁移至人大金仓]
适用版本：星桥需升级为1.7.3.4-20250220及以上的版本。若不满足版本要求，提交更新案件联系测试人员蓝希鹏申请发包。

**mysql-\>人大金仓**

1\. 新建数据库和模式(以星桥为例，大数据中心2.0迁移自行修改数据库和模式名为bigdata)

新建数据库data\_exchange，然后在模式旁边单击右键，选择新建模式

[img]

填写模式名data\_exchange，点击确定

[img]

**确认星桥版本已升级至****1.7.3.4-20250220及以上的版本！**配置连接此空库，从空库启动。

启动完成后，继续下一步操作。

2\. 迁移旧库数据

**先确认已将旧的MySQL版本星桥，升级至****1.7.3.4-20250220及以上的版本。（即使用MySQL配置，更新一遍星桥）**

星桥已升级版本后，使用官方工具进行迁移。

迁移方法参考\[\[MySQL迁移至KingbaseES操作说明\]\]。

迁移时注意：

**com\_license、databasechangelog、databasechangeloglock    这三张表不需要迁移！**

迁移之后，进行检查。在人大金仓数据库执行下列语句：

查找bit类型字段sql：

### chunk2 星桥数据迁移至人大金仓
| SELECT attrelid::regclass AS table\_name, attname AS column\_name FROM pg\_attribute WHERE atttypid = 'bit'::regtype AND attnum \> 0; |
|-------------------------------------------------------------------------------------------------------------------------------------------|

正常情况，从空库启动的星桥应当查询结果为空，即没有bit类型字段。

[img]

迁移之后，授权license，可参照：\[\[星桥大数据中心20系统授权\]\]。授权完成后重启即可访问服务。

3\. 修改驱动配置

在星桥的启动配置文件，即run脚本或者.env文件中。（具体是哪个文件与现场是手动还是一键部署有关）

注释掉之前的MySQL驱动配置，添加人大金仓的驱动配置如下：

run脚本中的格式示例如下：

### chunk3 星桥数据迁移至人大金仓
| \# 人大金仓驱动配置DATASOURCE\_DRIVER=org.postgresql.DriverDATASOURCE\_URL="jdbc:postgresql://**\{IP\}:\{端口\}**/**data\_exchange**?currentSchema=**data\_exchange**&stringtype=unspecified"DATASOURCE\_USERNAME=**system**DATASOURCE\_PASSWORD=**eG0va@yWck**PUMP\_STAGE\_TYPE=postgresql |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

.env文件可参照格式修改。

4.关于星桥中的数据源

**涉及数据源的产品，例如：星桥、灵珑等。从MySQL迁移至人大金仓后，原数据源配置不变！**

**现场工程需根据实际需要，自行修改数据源连接，例如：修改为人大金仓数据源配置。**

[img]

5\. 迁移常见问题：

（1）类型转换问题：在星桥1.7.3.4-20250220及以上的版本，从空库启动已避免了此类问题。现场先检查是否是按该版本，从空库启动，再进行迁移的。

[img]

## 星桥数据由mysql迁移到达梦
URL: https://alidocs.dingtalk.com/i/nodes/gwva2dxOW4KpzGNXUByxLnx28bkz3BRL?utm_scene=team_space

### chunk0 
星桥数据由mysql迁移到达梦

原始链接: https://faq.egova.com.cn:7787/projects/redmine/wiki/%E6%98%9F%E6%A1%A5%E6%95%B0%E6%8D%AE%E7%94%B1mysql%E8%BF%81%E7%A7%BB%E5%88%B0%E8%BE%BE%E6%A2%A6

### chunk1 星桥数据由mysql迁移到达梦(废弃)
[星桥数据由mysql迁移到达梦(废弃)]
**【应用场景】**

星桥已经部署在mysql数据库的项目需要迁移到达梦数据库上，所以需要采用迁移数据库的方式，从MySQL迁移到达梦库。

以下列出的迁移方法也适用于大数据中心2.0。

星桥用户：DEX

大数据中心2.0用户：DATACENTER

**【迁移说明】**

本机能内网连接达梦的服务器数据库，本地安装达梦数据库，目的是利用自带的工具，直接在本机利用达梦官方迁移工具进行迁移；

数据库选择和服务器相同的版本，根据自己操作系统下载对应系统版本。

1、官网首页下载的均为试用开发版本，参考官方文档安装: 达梦数据库安装官方文档

《达梦数据库管理系统安装手册.pdf》

[img] \[图片加载失败: https://faq.egova.com.cn:7787/ueditor/themes/default/images/spacer.gif\]

安装完成。

[img]

**【迁移准备】**

1.准备好达梦库实例，一般项目上由达梦方提供；可参考：\[\[达梦数据库实例创建\]\]

确认一下实例是否按照我方要求建立，具体要求和操作如下：

1） 大小写敏感：否；

2） 字符集编码：UTF-8；

3） 长度以字符为单位：是；

4） 实例运行时区：\+8:00；

2.创建用户DEX，可参考：\[\[达梦创建用户\]\]

**【迁移整体顺序】**

1.先创建一个空用户，用于空库启动星桥（改用户仅用于空库启动星桥，生成表databasechangelog和databasechangeloglock，迁移完成后可将该用户删除）。

2.使用DM迁移工具，将MYSQL数据迁移到DM数据库DEX用户，具体细节如下。

**【开始迁移】**

1.数据库实例使用DEX连接;

2.打开DM数据迁移工具；

### chunk2 星桥数据由mysql迁移到达梦(废弃)
[img]

空白处点击右键新建工程

[img]

[img]

选择新建迁移

[img]

[img]

3.在列表里选中迁移任务，点击【下一步】

[img]

4.选择Mysql向DM迁移

[img]

填写源端MySQL库的连接参数

[img]

填写目标端达梦库的连接参数， 注意用户使用DEX

[img]

5.按下图勾选， 目的模式为DEX

[img]

6.下图中点击【选择】，确认所有的表都被选中，点击【下一步】

[img]

注意：下面两张表取消勾选

[img][img]

下图中查看无误，勾选“以文本方式显示执行任务”，点击【完成】

[img]

迁移完成。

7.错误处理

会出现一些报错，需要完整保存这些报错内容，然后单独进行处理。

保存完报错后，可以关闭迁移工具，处理迁移报错的问题。

也可以点击【查看错误数据】或者点击【迁移日志】-迁移详细查看错误数据和日志。

[img]

查看出错的详细内容。

[img]

**【迁移databasechangelog表】**

星桥和大数据中心2.0数据库迁移需要更换databasechangelog表。新建一个达梦数据库，从空库启动，然后迁移该库的databasechangelog表 databasechangeloglock表，迁移步骤和上述一致。 更换后重启服务。

迁移方式选择DM-\>DM

[img]

指定对象的时候源模式和目标模式选择正确

[img]

选择迁移对象

[img]

迁移成功

[img]

**【迁移报错处理】**

1.迁移错误文档中会有每个建表失败的sql，需要修改所有sql，常见的错误主要是时间默认为 “0000-00-00 00:00:00”的错误，解决办法是修改时间默认为sysdate，或者修改为一个具体的时间。

### chunk3 星桥数据由mysql迁移到达梦(废弃)
其他建表错误请反馈测试或研发。

在处理建表错误语法的同时，新建一个txt文档，保存每个处理的表名，方便后续继续迁移这些表的数据。

2.时间默认为 “0000-00-00 00:00:00”的错误

1）用notepad工具打开报错的文档，用sysdate替换'0000-00-00 00:00:00'

[img]

将替换后建表语句复制到达梦管理工具下执行建表语句

[img]

2.此类报错，为表已存在索引或约束，因此出现报错。

此类报错无需处理。

[img]

3.字段超长报错

迁移过程中，存在数据长度超过达梦元表字段的定义长度，从而出现“记录超长”的报错。

解决办法：右键报错的表，设置【启用超长记录】，重新迁移数据即可。

[img]

3.空库启动报错请先确认数据库设置正确a. 关闭默认聚簇索引 \[-3243\]:表\[TEST\]中不能同时包含聚集KEY和大字段；能通过改数据库参数处理这个问题吗 \| 达梦技术社区

b. 确认字符编码，以及字符长度单位配置正确： 达梦环境数据库创建 - FAQ - 政通项目管理平台 [img][img]达梦在2024年第二季度后，**取消了长度以字符为单位配置**，若达梦为最新版本，则在迁移时手动配置字符长度缩放大小，如下图所示：[img]注意此版本达梦空库启动星桥时，须在启动参数中添加

--egova.liquibase.dm.varchar.scaleFactor=4

若以上配置正确空库启动仍存在问题，可以先通过DM迁移工具，将表结构先迁移到空库（不包括表数据、约束、索引），再尝试启动星桥即可。

## MySQL迁移至KingbaseES操作说明
URL: https://alidocs.dingtalk.com/i/nodes/14lgGw3P8vvl1M5XTQlyO6jj85daZ90D?utm_scene=team_space

### chunk0 
MySQL迁移至KingbaseES操作说明

原始链接: https://faq.egova.com.cn:7787/projects/redmine/wiki/MySQL%E8%BF%81%E7%A7%BB%E8%87%B3KingbaseES%E6%93%8D%E4%BD%9C%E8%AF%B4%E6%98%8E

### chunk1 MySQL迁移至KingbaseES操作说明
[MySQL迁移至KingbaseES操作说明]
**【背景说明】**

本文主要针对mysql数据库数据迁移kingbase数据库相关操作进行指引说明。**详细的软件安装说明可以见附件中的官方文档 。**

**【前提说明】**

**1.已安装好人大金仓数据库，已新建数据库以及模式，具体参考：** **基于Linux系统的人大金仓数据库软件安装说明** **数据库实例创建操作说明**

2.MySQL迁移至KingbaseES需要借助工具：

客户端迁移小工具KDTS（数据迁移工具），具体安装可以参考wiki: 基于windows系统的人大金仓数据库软件安装说明 （其中完全安装，客户端安装都包含该小工具，也可以定制化单独安装该小工具）。

**注意：先使用KDTS工具迁移表结构，表数据，索引，视图等，然后迁移不成功的视图和函数通过直接执行sql处理，详细参考：** **人大金仓数据库函数视图存储过程sql**

**特别说明：迁移前** **需要安装postgis扩展**

现场需要联系人大金仓技术支持人员发送配套的包，因人大金仓数据库版本和服务器系统版本，postgis版本都有关系，不同版本对于的postgis插件不同。

如果自行安装 ：公司环境所使用postgis插件版本：postgis-3.1.2\_X86\_V008R006C008B0014.tar.gz

1、解压插件包，将插件包的 bin、lib、share/extension 目录下的文件全部依次拷贝到数据库安装目录的 Server/ bin、Server/lib、Server/share/extension 下

2、在所在的 数据库模式 下执行：CREATE EXTENSION postgis; （提前建好数据库和数据库模式，模式名称建议和数据库名称同名）

### chunk2 MySQL迁移至KingbaseES操作说明
3、检查所在模式的扩展和数据类型目录下是否有gis类型，如下图，表示安装成功

[img][img]

**【数据迁移工具KDTS操作说明】**

数据迁移工具支持迁移的数据库版本：MySQL 5.X、8.X，KingbaseES V7、V8R3、V8R6。

**小工具启动入口有两种：**

**方式一：从导航进入**

[img]

点击后系统自动启动小工具进程

[img]

上述Console页面会给出小工具浏览器访问的入口，以及默认用户名和密码。上图所示访问地址为： http://localhost:8080 用户名/密码：kingbase/kingbase

**方式二：使用免安装包**

kdts免安装包下载地址： 点击下载

直接点击bin目录下的.bat文件运行即可，然后访问： http://localhost:54523 用户名/密码：kingbase/kingbase

注意：启动后不要关闭后台进程。

[img]

以上两种方法都可以启动后台进程，建议使用免安装，免安装版本相对高一点 。

**【迁移步骤】**

在浏览器窗口输入上述访问地址，进入小工具web端操作台，输入用户名和密码登录

[img]

（1）配置源数据库

进入“数据源管理--源数据库”-【新建】源数据库的基本信息（允许编辑修改）。测试此数据源是否连接成功，连接成功将会弹出“测试连接成功”提示框。

[img]

[img]

（2）配置目标数据库

进入“数据源管理--目标数据库”-【新建】目标数据库的基本信息（允许编辑修改）。测试此数据源是否连接成功，连接成功将会弹出“测试连接成功”提示框。[img]

（3）配置迁移任务

1.进入“迁移任务管理--迁移任务”，【新建】迁移任务。

[img]

[img]

### chunk3 MySQL迁移至KingbaseES操作说明
2.选择模式：默认勾选要迁移的数据库全部内容。 选择的模式必须先安装好postgis，参考本文的前提说明，否则会有部分表迁移失败。

[img]

下图为：未给模式安装postgis导致找不到geometry类型，当出现以下失败，可安装postgis插件后，手动再次执行。

[img]

[img]

3.选择迁移对象： 一般是选择【全部】；

[img]

**特别说明：当库太大，可以选择【包含指定对象】，需要创建多个迁移任务，选择每次要迁移的表**

[img]

[img]

同时如果用同一个迁移任务会给出下图所示的提示，本次迁移覆盖前一次迁移结果。

[img]

4.配置参数

（1）迁移配置-源数据库配置：

[img]

（2）源库配置中可以同步配置kdms转换视图，函数，存储过程等信息：

[img]

（3）目标数据库配置：

[img]

（4）数据类型映射

bit类型需转换成int，否则会有报错 ，并全部勾选所有数据类型

[img]

（5）线程配置：

[img]

4.正式迁移数据

配置迁移任务后点击【保存并迁移】开始迁移。可以通过列表“状态”知道迁移成功或失败。

[img]

5.查看迁移结果

可以点击列表【详情】按钮进入“结果查看”页面查看详细信息。

[img]

如果迁移有错误，可以点击操作-错误日志查看详情

[img]

5.目前20230301版本人大金仓数据库迁移结果如下，失败的视图和函数执行sql处理： 人大金仓数据库函数视图存储过程sql

业务库：[img]

统计库：

[img]

6.迁移完成后部署智信云相关服务，参考： 智信云应用连接人大金仓数据库配置说明

7.迁移完成后，麒舰需要处理的内容如下，原因：人大金仓会将空字符串识别为null，需要关闭

### chunk4 MySQL迁移至KingbaseES操作说明
| -- 修改配置ALTER SYSTEM SET ora\_input\_emptystr\_isnull = off;SELECT sys\_reload\_conf(); |
|----------------------------------------------------------------------------------------------|

[img]

──────────────────────────────────────────────────

通过实践下述方式导出的sql语句在金仓数据库中执行失败，暂不推荐使用下面的方式处理，可能有一定的用处，暂保留（20231009记录）。

【在线浏览器迁移工具KDMS操作说明】

该工具支持迁移的数据库版本：MySQL5.5及以上。支持的浏览器：建议Chrome75版本及以上浏览器，IE浏览器不支持。

**【安装前提】：**

**1.软件包及用户手册下载地址详见百度云盘：**

**链接: https://pan.baidu.com/s/1qBswBdorxZuPMLrNfeUMtQ?pwd=uktk 提取码: uktk**

官方下载数据采集工具和手册地址： https://bbs.kingbase.com.cn/thread-116-1-1.html 。

[img]

[img]

MySQL数据的采集请参考《数据库迁移评估使用手册》的3.2.

[img]

2. **该工具主要用于迁移视图，函数，存储过程等，如果前面在KDTS工具中已做了KDMS的迁移，就可以忽略不用再次操作。**

【安装步骤】

1.双击“KingbaseDMS-mysql.exe”，系统启动正常后给出Console页面默认访问地址： http://localhost:9003

[img]

### chunk5 MySQL迁移至KingbaseES操作说明
[img]

2.新建采集项目

[img]

3.开始采集任务（ 注意 ：使用root用户进行采集，也就是配置mysql用户名为：root）

创建项目后系统自行发起采集

[img]

4.校验并下载采集数据

[img]

[img]

导出的采集数据，解压后如下图所示。 **不同采集项目的dat文件不可混用** 。

[img]

5.MySQL数据采集完成后，进行评估:

**(1)访问浏览器：https://bbs.kingbase.com.cn/，需要自行注册，注册成功后登录点击【数据库迁移评估】。**

[img]

(2)进入评估管理系统的“数据库迁移--评估管理”，【新建评估】，上传第4步采集的ZIP包，填写其他必填项，点击【确定】。

[img]

(3）等待评估进度为100%。

[img]

转换有失败的情况，点击【详情】查看。[img]

一般失败原因为以下2种：

[img]

查看【对象详情】时，可以根据失败原因筛选过滤失败对象。[img]

为进一步了解报错情况，可以点击【查看详情】。

[img]

（4）评估完成后可以下载对象语句在金仓数据库中执行：

[img]

[img]

[img]

（5）金仓数据库中执行sql

## MySQL迁移达梦步骤
URL: https://alidocs.dingtalk.com/i/nodes/jb9Y4gmKWr7l1v5MijG0BYRaVGXn6lpz?utm_scene=team_space

### chunk0 
统一用户中心20-MySQL迁移达梦步骤

原始链接： https://faq.egova.com.cn:7787/projects/redmine/wiki/%E7%BB%9F%E4%B8%80%E7%94%A8%E6%88%B7%E4%B8%AD%E5%BF%8320-MySQL%E8%BF%81%E7%A7%BB%E8%BE%BE%E6%A2%A6%E6%AD%A5%E9%AA%A4

### chunk1 统一用户中心20-MySQL迁移达梦步骤
[统一用户中心20-MySQL迁移达梦步骤]
**若是新部署现场，则只需导入基准库，不涉及步骤2的迁移旧数据。**

用户中心2.0从mysql迁移到达梦，步骤如下：

1、关于达梦库，使用基准库文件，导入达梦，然后启动

用户中心210版本基准库地址：

[ http://oneops.egova.com.cn:8093/one/benchbasedb/ ](http://oneops.egova.com.cn:8093/one/benchbasedb/)

可使用迁移工具，文件sql-DM方式导入；或命令行导入。

以迁移工具为例：

[img]

[img]

[img]

[img]

**导入成功之后，启动用户中心服务，正常情况下liquibase能顺利执行下去，等待服务runing。**

**有迁移旧数据的需求，再停止服务，执行下面的步骤。**

2、迁移数据：从mysql迁移表至达梦库， admin\_changelog和databasechangeloglock两张表不迁移

[img]

[img]

[img]

[img]

[img]

3、如果还遇到启动问题，可能与用户中心版本，尝试更新版本，具体联系测试人员蓝希鹏

4、迁移数据库后首次刷新

### chunk2 统一用户中心20-MySQL迁移达梦步骤
select 'DBMS\_STATS.GATHER\_SCHEMA\_STATS('''\|\|username\|\|''',100,TRUE,''FOR ALL COLUMNS SIZE AUTO'');' from all\_users; --这里我们一般选择需要收集的用户对应的行，进行执行即可。 -- 在同一个窗口中复制结果集，执行完成即可。-- 查找统计信息更新一天内的表 SELECT OWNER, TABLE\_NAME, LAST\_ANALYZED, DATEDIFF(DAY, LAST\_ANALYZED, SYSDATE) AS DAYS\_SINCE\_LAST\_ANALYZED FROM DBA\_TABLES WHERE DATEDIFF(DAY, LAST\_ANALYZED, SYSDATE) \  30; -- 查找统计信息缺失的表 SELECT OWNER, TABLE\_NAME, LAST\_ANALYZED, DATEDIFF(DAY, LAST\_ANALYZED, SYSDATE) AS DAYS\_SINCE\_LAST\_ANALYZED FROM DBA\_TABLES WHERE LAST\_ANALYZED is null ;

-- 我们更新后，第一步应该能找到表，第二步、第三步不应该还有找到的业务相关表！

参考： 系统上线第一步 \| 如何正确的第一次更新统计信息 \| 达梦技术社区

验证：

备注：注意迁移的第二步，changelog相关表不要勾选，否则可能引起某些启动冲突。

## 灵珑MySql库迁移至达梦库
URL: https://alidocs.dingtalk.com/i/nodes/2Amq4vjg89gq7LzDsQZMrXORV3kdP0wQ?utm_scene=team_space

### chunk0 
灵珑MySql库迁移至达梦库

原始链接： https://faq.egova.com.cn:7787/projects/redmine/wiki/%E7%81%B5%E7%8F%91MySql%E5%BA%93%E8%BF%81%E7%A7%BB%E8%87%B3%E8%BE%BE%E6%A2%A6%E5%BA%93

### chunk1 灵珑MySql库迁移至达梦库 / 1、使用达梦迁移工具
[灵珑MySql库迁移至达梦库 / 1、使用达梦迁移工具]
将mysql库迁移到达梦库 ，mysql迁移达梦参考： MySQL迁移达梦实施规范 （ 注意旧库迁移和新项目部署 ）

【示例】将78环境上的灵珑库迁移到18达梦环境LINGLONG库

[img]

[img]

勾选保持对象大小写

[img]

注意 勾选所有表

[img]

### chunk2 灵珑MySql库迁移至达梦库 / 2、清理databasechangelog MD5SUM值
[灵珑MySql库迁移至达梦库 / 2、清理databasechangelog MD5SUM值]
在达梦库中执行

1）MD5SUM置空：update "LINGLONG"."databasechangelog"set MD5SUM = NULL

2）提交事务： COMMIT

3、 启动脚本调整

需将mysql 启动脚本数据库的连接调整达梦的方式

#达梦数据库连接start

--DATASOURCE\_DRIVER=dm.jdbc.driver.DmDriver \\--spring.datasource.url=jdbc:dm:// 192.168.101.18:6000?schema=LINGLONGHOTFIX \\--flagwind.mybatis.name-quote= -1 \\--DATASOURCE\_USERNAME= LINGLONG \\--DATASOURCE\_PASSWORD= \*\*\*\*\*\* \\

--egova.executor.stage.type=dm \\

#达梦数据库连接end

**4、申请授权重启服务**

若是新服务器数据库，需重新申请授权，参考： 灵珑平台license申请

重启服务

FAQ：

1、迁移后启动脚本未调整，启动服务报sql语法错误，是由于达梦启动脚本未添加启动参数

--flagwind.mybatis.name-quote=-1--egova.executor.stage.type=dm

[img]

2、视图查询报错：

问题现象：数据库从MySQL迁移到达梦库，执行数据视图的查询或者使用数据视图的详情部件、列表部件查询报下面的错误

[img]

解决办法：检查“数据源”里是否相同的达梦库配置了多个数据源？如果是，“数据源连接”不能相同（后缀灵珑优化后将不存在此问题）。

### chunk3 灵珑MySql库迁移至达梦库 / 2、清理databasechangelog MD5SUM值
或者 应用所属的数据源连接，schema的名字从大写改为小写；

或者 增加后缀让数据源不一致，例如：schema=eurbanpro ?test=1 ；

[img]

3、达梦不支持GROUP\_CONCAT函数

解决办法：

（1）在达梦环境下把GROUP\_CONCAT改为WM\_CONCAT可以解决；

（2）应该使用自定义函数 @GROUP\_CONCAT ，有些产品不支持，请联系研发；

[img]

4、迁移后出现乱码问题

【解决办法】mysql文件迁移到达梦库时，文件编码需设置为utf-8

[img]

[img]

参考： MySQL迁移达梦实施规范 数据中心10迁移到达梦

## 海量数据库迁移
URL: https://alidocs.dingtalk.com/i/nodes/14lgGw3P8vvl1M5XTpzvY0Yw85daZ90D?utm_scene=team_space

### chunk0 **迁移步骤**
[**迁移步骤**]
1、新增规则

datetime转timestamp

varchar(20)转varchar(50)

bit转boolean

[img]

[img]

2、新增规则模板

[img]

3、迁移数据库

[img]

选择规则模板

[img]

### chunk1 **jdbc连接**
[**jdbc连接**]
```shell
--DATASOURCE_URL=jdbc:postgresql://10.255.18.2:5444/eurbanpro?currentSchema=eurbanpro&stringtype=unspecified \
--DATASOURCE_DRIVER=org.postgresql.Driver \
--DATASOURCE_USERNAME=eurbanpro \
--DATASOURCE_PASSWORD=eGova@26 \
```

### chunk2 **修改灵珑数据源**
[**修改灵珑数据源**]
[img]

## 人大金仓数据库迁移
URL: https://alidocs.dingtalk.com/i/nodes/lyQod3RxJK3moqXKi4roYvzOJkb4Mw9r?utm_scene=team_space

### chunk0 
人大金仓数据库迁移

原始链接： https://faq.egova.com.cn:7787/projects/redmine/wiki/%E4%BA%BA%E5%A4%A7%E9%87%91%E4%BB%93%E6%95%B0%E6%8D%AE%E5%BA%93%E8%BF%81%E7%A7%BB

### chunk1 **参考文档**
[**参考文档**]
参考Wiki创建人大金仓数据库：[数据库实例创建操作说明.docx](https://alidocs.dingtalk.com/i/nodes/a9E05BDRVQ6LowmMiywYQ3XqJ63zgkYA?utm_scene=team_space)

参考Wiki安装迁移工具：[MySQL迁移至KingbaseES操作说明](https://alidocs.dingtalk.com/i/nodes/14lgGw3P8vvl1M5XTQlyO6jj85daZ90D?utm_scene=team_space)

### chunk2 **迁移步骤**
[**迁移步骤**]
1、新增源数据库；

[img]

### chunk3 **迁移步骤**
| 配置项 | 说明 | 示例值 |
|---------|------|---------|
| 连接名称 | 自定义标识，用于区分不同数据源，建议按业务命名，如`业务名&#95;库名&#95;mysql` | `麒舰111` |
| 数据库类型 | 下拉选择，此处固定选择`MYSQL` | `MYSQL` |
| 数据库版本 | 根据实际 MySQL 版本选择，需与源库版本一致 | `8.0` |
| 服务器地址 | MySQL 数据库所在服务器 IP / 域名 | `10.255.18.220` |
| 服务器端口 | MySQL 服务端口，默认`3306` | `3306` |
| 用户名 | 源 MySQL 数据库登录账号，需具备读取权限 | `root` |
| 密码 | 对应账号的登录密码 | `&#42;&#42;&#42;&#42;&#42;&#42;&#42;&#42;` |
| 数据库 | 需迁移的具体 MySQL 库名 | `eurbanprokingbasets` |
| 驱动 | 自动填充，MySQL 8.0 \+ 默认驱动 | `com.mysql.cj.jdbc.Driver` |
| URL | 工具自动拼接生成，格式为`jdbc:mysql://IP:端口/库名` | `jdbc:mysql://10.255.18.220:3306/eurbanprokingbasets` |

### chunk4 **迁移步骤**
| 连接参数 | 可选配置，建议添加以下参数： 1\. `zeroDateTimeBehavior=convertToNull`（处理 MySQL `0000-00-00` 日期兼容问题） 2\. `useUnicode=true&amp;characterEncoding=utf-8`（字符集兼容） 3\. `useCursorFetch=true`（大数据量迁移优化） 4\. `useSSL=false`（关闭 SSL 连接，避免测试报错） | 参考图 1 配置 |
| 确定按钮 | 测试连接成功后，点击保存配置 | - |
| 测试按钮 | 配置完成后，点击测试连接是否正常连通，确认无误后再保存 | - |

2、新增目标数据库；

[img]

### chunk5 **迁移步骤**
| 配置项 | 说明 | 示例值 |
|---------|------|---------|
| 连接名称 | 自定义标识，用于区分不同目标数据源，建议按「业务名\_库名\_KES」格式命名，方便后续管理 | `麒舰111ks` |
| 数据库类型 | 下拉选择，此处固定为`KINGBASE` | `KINGBASE` |
| 数据库版本 | 需与实际人大金仓版本一致，此处为`V8R6` | `V8R6` |
| KES 兼容模式 | **必须选择**`**ORACLE**`**模式**，该模式支持大小写敏感、函数兼容等特性，适配 MySQL 迁移场景；`PG`模式不支持大小写敏感，易导致迁移异常 | `ORACLE` |
| 服务器地址 | 人大金仓数据库所在服务器 IP / 域名 | `10.255.18.225` |
| 服务器端口 | 人大金仓服务默认端口为`54321`，需根据实际配置填写 | `54321` |
| 用户名 | 目标库登录账号，默认管理员账号为`system`，需具备数据写入、表创建等权限 | `system` |
| 密码 | 对应账号的登录密码，需与数据库实际配置一致 | `&#42;&#42;&#42;&#42;&#42;&#42;&#42;&#42;` |
| 数据库 | 迁移目标库名，需为提前创建好的人大金仓数据库 | `eurbanpro111`/`cgdbstat20230101` |
| 驱动 | 工具自动填充，KingbaseES V8R6 默认驱动 | `com.kingbase8.Driver` |
| URL | 工具自动拼接生成，格式为`jdbc:kingbase8://IP:端口/库名`，无需手动修改 | `jdbc:kingbase8://10.255.18.225:54321/eurbanpro111` |

### chunk6 **迁移步骤**
| 连接参数 | 建议添加以下参数优化兼容性： 1\. `clientEncoding=utf8`（字符集兼容，避免乱码） 2\. `ApplicationName=kingbase&#95;transfer`（标识迁移任务，方便日志排查） | 参考图 1 配置 |
| 确定按钮 | 测试连接成功后，点击保存配置 | - |
| 测试按钮 | 配置完成后，点击验证连接是否正常，确认无误后再保存 | - |

3、新增迁移任务；

1）新增迁移任务，选择数据源；

[img]

| 配置项 | 说明 | 填写要求 / 示例 |
|---------|------|---------------------|
| 任务名称 | 自定义标识，用于区分不同迁移任务，建议按「业务名\_源库\_目标库」格式命名 | 示例：`业务名&#95;mysql&#95;to&#95;kes`、`eurbanpro&#95;migration` |
| 源数据库连接名 | 下拉选择已配置好的**MySQL 源数据库**连接，若未配置，可点击右侧「新建数据源」快速添加 | 需选择已测试连通性正常的 MySQL 数据源 |
| 目标数据库连接名 | 下拉选择已配置好的**人大金仓目标数据库**连接，若未配置，可点击右侧「新建数据源」快速添加 | 需选择已测试连通性正常的 KingbaseES 数据源 |

2）选择模式

[img]

### chunk7 **迁移步骤**
| 配置项 | 说明 | 填写要求 / 示例 |
|---------|------|---------------------|
| 源模式 | 下拉列表中显示**MySQL 源数据库的 Schema / 库名**，需勾选需要迁移的源库模式 | 示例：`eurbanpro111` |
| 目标模式 | 选择源模式对应的**人大金仓目标模式（Schema）**，需提前在目标库中创建 | 示例：`eurbanpro111` |
| 目标属主 | 迁移对象在目标库中的所属用户，**必填项**，决定表 / 对象的权限归属 | 推荐选择目标库管理员用户 `system`，也可选择业务专用用户 |
| 迁移对象 | 勾选需要迁移的数据库对象类型，建议全选，确保结构与数据完整迁移 | 包括：`表结构`、`表数据`、`主键`、`索引`、`唯一性约束`、`外键`、`检查约束`等 |

3）选择迁移对象，第一次迁移选择“全部”

[img]

4）勾选数据类型映射；

MySQL 的 BIT 类型必须映射为人大金仓的 INT 类型

点击右下角的 「保存并迁移」 按钮，启动迁移任务。

[img]

[img]

4、执行sql，清除changelog表的md5sum：

update usercenter\_remote\_changelog set md5sum=null;

update v22\_changelog set md5sum=null;

update workflow\_center\_changelog set md5sum=null;

update "eurbanpro111kingbase".usercenter\_remote\_changelog set md5sum=null;

### chunk8 **迁移步骤**
update "eurbanpro111kingbase".v22\_changelog set md5sum=null;

update "eurbanpro111kingbase".workflow\_center\_changelog set md5sum=null;

### chunk9 **导入导出**
[**导入导出**]
人大金仓数据库sys\_dump命令不能直接执行，需要进到人大金仓数据库目录下的/opt/Kingbase/ES/V8/Server/bin下执行，

二进制格式:

备份全库：

./sys\_dump -h ip -p 端口 -U 用户 -F c -f 备份路径/xxx.dmp 库名

还原全库：

./sys\_restore -h ip -p 端口 -U 用户 -d 库名 备份路径/xxx.dmp

sql格式：

~~备份全库：~~

~~sys\_dump -h ip -p 端口 -U 用户 -f 备份路径/xxx.sql 库名~~

还原全库：

ksql -h ip -U用户名 -d 库名 -f 备份路径/xxx.sql

导出sql：~~./sys\_dump -h localhost -p 54321 -U system -f /egova/data/eurbanpro.sql 库名~~

./sys\_dump -U system -d 源库名 -n 模式名 --no-owner --no-privileges -F p -f /egova/XXX.sql

[img]

导出dmp:

./sys\_dump -U system -d 源库名 -n 模式名 --no-owner --no-privileges -F c -f /egova/XXX.dmp

### chunk10 **启动服务**
[**启动服务**]
1、修改env文件，启动麒舰服务；

### chunk11 **启动服务**
\[root@cg134:/egova/apps/basic/eurbanpro\]# cat eurbanpro.env #!/bin/bash --loginshopt -s expand\_aliasesJAVA\_SERVER\_OPTS=" -Xms128m -Xmx4096m \\-Dfile.encoding=UTF-8 \\ \\-Dlog4j2.formatMsgNoLookups=true \\-XX:\+HeapDumpOnOutOfMemoryError  -XX:HeapDumpPath=/egova/apps/basic/eurbanpro/jvm \\-javaagent:/egova/apps/basic/eurbanpro/arex/arex-agent-qijian.jar -Darex.service.name=v22-test -Darex.storage.service.host=172.26.1.146:8093 \\-Darex.coverage.packages=com.egova -XX:MetaspaceSize=512m -XX:MaxMetaspaceSize=512m \\-jar /egova/apps/basic/eurbanpro/egova-urbanpro-mis-service.jar \\--SERVER\_PORT=16000 \\--ROOT\_DIR=/egova/apps/basic/eurbanpro/ \\--LOG\_LEVEL=INFO \\--DATASOURCE\_DRIVER=org.postgresql.Driver \\--DATASOURCE\_URL='jdbc: postgresql://172.26.1.135:54321/eurbanpro?

### chunk12 **启动服务**
currentSchema=eurbanpro&serverTimezone=Asia/Shanghai&useSSL=false&allowMultiQueries=true&autoReconnect=true&failOverReadOnly=false&useUnicode=true&characterEncoding=utf8&nullCatalogMeansCurrent=true ' \\--DATASOURCE\_USERNAME=system \\--DATASOURCE\_PASSWORD=eGovaZT@2023 \\--REDIS\_URL=172.26.1.134 \\--REDIS\_PORT=6380 \\--REDIS\_DATABASE=2 \\--REDIS\_PASSWORD=eGova@redis \\--TOKEN\_REDIS\_URL=172.26.1.135 \\--TOKEN\_REDIS\_PORT=6380 \\--TOKEN\_REDIS\_DATABASE=3 \\--TOKEN\_REDIS\_PASSWORD=eGova@redis \\--MINIO\_ENDPOINTS= http://172.26.1.134:30001 \\--MINIO\_ACCESS=admin \\--MINIO\_SECRET=eGova@2022 \\--MINIO\_BUCKET=eurbanpro \\--BUCKET\_NAME=eurbanpro \\--MINIO\_PROXY= http://172.26.1.134:30001 \\--NACOS\_ENABLE=true \\--NACOS\_URL=172.26.1.134:8848 \\--NACOS\_NAMESPACE=egova \\--NACOS\_U

### chunk13 **启动服务**
2、修改灵珑中麒舰数据源

[img]

3、测试数据清除

[基准库测试数据清除](https://alidocs.dingtalk.com/i/nodes/Y1OQX0akWm3gYmA4iE1D9NO4JGlDd3mE?corpId=ding950f23e6cefc750c35c2f4657eb6378f&utm_medium=im_card&iframeQuery=utm_medium%3Dim_card%26utm_source%3Dim&utm_scene=team_space&utm_source=im)

### chunk14 **FAQ**
[**FAQ**]
1\. TIMESTAMP时间类型的语法差异

MySQL 中 TIMESTAMP(0) 这种写法，在人大金仓里语法不兼容，手动修改这张表的建表语句，把 TIMESTAMP(0) 改成 TIMESTAMP。

[img]

2.创建外键的表不存在

先修复并创建 act\_ge\_bytearray 表，再创建外键约束。

[img]

3.表数据迁移失败

先修复并创建 act\_ge\_bytearray、act\_re\_proedef 表，再重新迁移表数据。

[img]

表数据迁移失败后，只导入表数据，选择模式【表数据】即可

[img]

## 达梦数据库迁移
URL: https://alidocs.dingtalk.com/i/nodes/Qnp9zOoBVBZzoL47cL1PlLonV1DK0g6l?utm_scene=team_space

### chunk0 
达梦数据库迁移

原始链接： https://faq.egova.com.cn:7787/projects/redmine/wiki/%E8%BE%BE%E6%A2%A6%E6%95%B0%E6%8D%AE%E5%BA%93%E8%BF%81%E7%A7%BB

### chunk1 达梦数据库迁移
[达梦数据库迁移]
1、参考Wiki创建达梦数据库实例：\[\[达梦数据库实例创建\]\] ;

注意：

导入数据库前一定要修改兼容模式为mysql兼容，执行后重启数据库实例

SP\_SET\_PARA\_VALUE(2,'COMPATIBLE\_MODE',4);commit;

查询：

SELECT VALUE FROM V\$PARAMETER WHERE NAME = 'COMPATIBLE\_MODE';  --4为MySQL模式

2、参考Wiki创建用户：\[\[达梦创建用户\]\]

一般用户名为：eurbanpro

3、导入附件中的迁移配置文件，进行迁移

1）打开配置文件，修改MySQL连接信息：

[img]

2）修改达梦的连接信息，选择指定驱动，这里的驱动可以将麒舰相关的jar包解压后在BOOT-INF\\lib\\DmJdbcDriver18-8.1.3.140.jar路径下找到；

[img]

3）勾选指定模式；

[img]

4）选择所有表；

[img]

5）点击完成开始迁移；

[img]

6）迁移遇到唯一约束的问题可忽略。

[img]

4、执行sql，清除changelog表的md5sum：

每条语句后要执行commit，否则不生效

update usercenter\_remote\_changelog set md5sum=null; commit;

update v22\_changelog set md5sum=null; commit;

update workflow\_center\_changelog set md5sum=null; commit;

5、修改启动脚本：

--DATASOURCE\_DRIVER=dm.jdbc.driver.DmDriver

### chunk2 达梦数据库迁移
--DATASOURCE\_URL=jdbc:dm://10.255.18.12:5335?clobAsString=true

--DATASOURCE\_USERNAME=eurbanpro

--DATASOURCE\_PASSWORD=eGova@2024

6、查看MIS\_CALL\_RECORD\_HIS表id字段是否为自增，是的话需要改为否

[img]

7、启动麒舰服务

8、修改灵珑中麒舰数据源

[img]

其他服务：

灵珑MySQL迁移达梦参考Wiki：\[\[灵珑MySql库迁移至达梦库\]\]

用户中心2.0MySQL迁移达梦参考Wiki：\[\[统一用户中心20-MySQL迁移达梦步骤\]\]

## 国产化启动失败
URL: https://alidocs.dingtalk.com/i/nodes/gvNG4YZ7JneM3nBvc9xgydeMV2LD0oRE?utm_scene=team_space

### chunk0 
国产化启动失败

### chunk1 国产化启动失败
[国产化启动失败]
1、达梦启动失败，报错如下

[img]

找测试更新center jar执行sql：insert into "GISCENTER"."DATABASECHANGELOG" ("ID","AUTHOR","FILENAME","DATEEXECUTED","ORDEREXECUTED","EXECTYPE","MD5SUM","DESCRIPTION","COMMENTS","TAG","LIQUIBASE","CONTEXTS","LABELS","DEPLOYMENT\_ID") values ('gis20210511-1134', 'yanya', 'db/changelog/app-service-db-changelog.xml', '2024-09-13 13:50:04', 137, 'MARK\_RAN', '', 'modifyDataType columnName=service\_id, tableName=tc\_app\_registry\_base; sql', '修改字段类型', null, '4.25.0', null, null, '6206603949');

重启微服务：service giscenter restart

2、达梦版本是v8高版本，需要按wiki更新通图，#385689

查看版本：SELECT \* FROM v\$instance;

3、达梦数据库报错 java.lang.NullPointerException

[img]

启动文件缺少如下这一行

[img]

## 瀚高数据库迁移
URL: https://alidocs.dingtalk.com/i/nodes/R1zknDm0WR3eownjixpDbbLvVBQEx5rG?utm_scene=team_space

### chunk0 
按照瀚高迁移文档

[https://faq.egova.com.cn:7787/projects/redmine/wiki/Mysql%E6%95%B0%E6%8D%AE%E5%BA%93%E8%BF%81%E7%A7%BB%E5%88%B0%E7%80%9A%E9%AB%98%E6%95%B0%E6%8D%AE%E5%BA%93](https://faq.egova.com.cn:7787/projects/redmine/wiki/Mysql%E6%95%B0%E6%8D%AE%E5%BA%93%E8%BF%81%E7%A7%BB%E5%88%B0%E7%80%9A%E9%AB%98%E6%95%B0%E6%8D%AE%E5%BA%93)

迁移时关闭大小写敏感，迁移后数据库表字段全是小写

[img]

执行changlog报错找不到字段

[img]

迁移时需要勾选如下

[img]

迁移后启动服务问题

[img]

错误原因：

这个错误是因为数据库中的 `disabled` 字段类型是 `bit` ，但你在 SQL 中传入的参数是 `integer` 类型（很可能是 0 或 1）。HighGo（基于 PostgreSQL）不支持直接比较 `bit` 和 `integer` 。

基于AI分析查找数据库中bit类型的字段

SELECT

n.nspname as schema,

c.relname as table,

a.attname as column,

a.atttypid::regtype as type

FROM pg\_attribute a

JOIN pg\_class c ON a.attrelid = c.oid

JOIN pg\_namespace n ON c.relnamespace = n.oid

### chunk1 
WHERE a.atttypid = 'bit'::regtype

AND a.attnum \> 0

ORDER BY n.nspname, c.relname, a.attname;

结果如下：

[img]

修改字段类型

ALTER TABLE dex.com\_attachment ALTER COLUMN disabled TYPE smallint USING (disabled::int);

ALTER TABLE dex.com\_category ALTER COLUMN disabled TYPE smallint USING (disabled::int);

ALTER TABLE dex.com\_client\_details ALTER COLUMN disabled TYPE smallint USING (disabled::int);

ALTER TABLE dex.com\_department ALTER COLUMN disabled TYPE smallint USING (disabled::int);

ALTER TABLE dex.com\_login\_log ALTER COLUMN actived TYPE smallint USING (actived::int);

ALTER TABLE dex.com\_option ALTER COLUMN disabled TYPE smallint USING (disabled::int);

ALTER TABLE dex.com\_option ALTER COLUMN important TYPE smallint USING (important::int);

### chunk2 
ALTER TABLE dex.com\_option\_group ALTER COLUMN disabled TYPE smallint USING (disabled::int);

ALTER TABLE dex.com\_person ALTER COLUMN disabled TYPE smallint USING (disabled::int);

ALTER TABLE dex.com\_role ALTER COLUMN disabled TYPE smallint USING (disabled::int);

ALTER TABLE dex.com\_schema ALTER COLUMN disabled TYPE smallint USING (disabled::int);

ALTER TABLE dex.com\_schema ALTER COLUMN spread TYPE smallint USING (spread::int);

ALTER TABLE dex.com\_user ALTER COLUMN disabled TYPE smallint USING (disabled::int);

修改后服务可正常启动

[img]

[img]

切换到sysdba用户执行自定义转换函数

-- 1. 创建 boolean 到 smallint 的转换函数
CREATE OR REPLACE FUNCTION public.bool2smallint(boolean) RETURNS smallint AS \$\$
BEGIN
RETURN (\$1)::smallint;
END;
\$\$ LANGUAGE plpgsql IMMUTABLE STRICT;

### chunk3 
-- 2. 注册转换
CREATE CAST (boolean AS smallint) WITH FUNCTION public.bool2smallint(boolean) AS ASSIGNMENT;

DROP CAST IF EXISTS (boolean AS smallint);
DROP FUNCTION IF EXISTS public.bool2smallint(boolean);

CREATE OR REPLACE FUNCTION public.bool2smallint(boolean) RETURNS smallint AS \$\$
BEGIN
RETURN CASE WHEN \$1 THEN 1 ELSE 0 END;
END;
\$\$ LANGUAGE plpgsql IMMUTABLE STRICT;

CREATE CAST (boolean AS smallint) WITH FUNCTION public.bool2smallint(boolean) AS ASSIGNMENT;

[img]

[img]

解决办法： 无法解决
```
-- 1. 创建 integer 到 varchar 的转换函数

```

CREATE OR REPLACE FUNCTION public.int2varchar(integer) RETURNS character varying AS \$\$
BEGIN
RETURN \$1::character varying;
END;
\$\$ LANGUAGE plpgsql IMMUTABLE STRICT;

### chunk4 
-- 2. 注册为隐式转换
CREATE CAST (integer AS character varying) WITH FUNCTION public.int2varchar(integer) AS ASSIGNMENT;

继续报错

[img]

DROP CAST IF EXISTS (integer AS character varying);
DROP FUNCTION IF EXISTS public.int2varchar(integer);

CREATE OR REPLACE FUNCTION public.int2varchar(integer) RETURNS character varying AS \$\$
BEGIN
RETURN CASE WHEN \$1 IS NOT NULL THEN \$1::text ELSE NULL END;
END;
\$\$ LANGUAGE plpgsql IMMUTABLE STRICT;

CREATE CAST (integer AS character varying) WITH FUNCTION public.int2varchar(integer) AS ASSIGNMENT;

## 人大金仓数据库迁移
URL: https://alidocs.dingtalk.com/i/nodes/N7dx2rn0JbZ9pg2LcZ35LqX1JMGjLRb3?utm_scene=team_space

### chunk0 
迁移文档见

[https://faq.egova.com.cn:7787/projects/redmine/wiki/MySQL%E8%BF%81%E7%A7%BB%E8%87%B3KingbaseES%E6%93%8D%E4%BD%9C%E8%AF%B4%E6%98%8E](https://faq.egova.com.cn:7787/projects/redmine/wiki/MySQL%E8%BF%81%E7%A7%BB%E8%87%B3KingbaseES%E6%93%8D%E4%BD%9C%E8%AF%B4%E6%98%8E)

遇到的问题

[img]

ALTER TABLE dex.databasechangeloglock ALTER COLUMN locked TYPE boolean USING locked::integer::boolean;

## 智信云迁移麒舰数据迁移操作步骤
URL: https://alidocs.dingtalk.com/i/nodes/m9bN7RYPWdlgzjZLfKPywl3DWZd1wyK0?utm_scene=team_space

### chunk0 **说明**
[**说明**]
1. 迁移的数据主要涉及 地理数据、大小类、组织机构及业务数据的迁移， 要 了解每种数据迁移的源数据库和目标数据库 ，每个章节的标题也有源数据源和目标数据源的标识。
2. 迁移的数据主要是 通过星桥脚本进行迁移 ，迁移涉及的所有脚本，有部门已经内置为模板，有些还没有处理。可跟据需要迁移的数据，单独导入脚本，各章节有单独的数据，也可以统一导入

[export-all.json](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXLbYE4Rx5qX1/att/fef6c628-9631-4966-a0bd-49831549d61b.json?Expires=1782159357&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=NYjxoyUkYM5yCMAshcKCmU24SbQ%3D)

3. 星桥中数据源各章节有单独说明，也可以统一设置，主要涉及数据源如下，可以提前在星桥数据源中创建好，也可以单独章节迁移创建
1. 智信云业务库：cgdb
2. 智信云统计库：cgdbstat
3. 麒舰体系玄藏数据库：xuanzang
4. 麒舰体系用户中心数据库：usercenter
5. 麒舰提测毕升库：becensus

### chunk1 **地理数据迁移**
[**地理数据迁移**]
区划信息理论上应该迁也只有一套，迁移region表，需要将cgdb中的region表，迁移到麒舰体系下的这些库中：xuanzang、usercenter、becensus
1. 检查迁移脚本，星桥内置了模板：同步玄藏-1智信云迁移玄藏。

[img]
2. 检查添加数据源

主要创建cgdb、usercenter、xuanzang、becenus的数据源，
3. 编辑任务后，进入配置页面
1. 配置源端信息：
1. 数据源类型：数据源类型
2. 数据源：选择配置的老系统统计库数据源名称，如：cgdb
2. 配置目标端信息：
3. 数据源类型：数据源类型
4. 数据源：选择配置的迁入数据的数据源名称，如：xuanzang

[img]
4. 点击预览，如果预览有问题，可能是字段的问题，在老系统业务库cgdb库中执行，直至调试成功，再拷贝到自定义查询中，进行预览，预览成功后，点击【下一步】，直至试跑界面
5. 进行试跑，可刷新日志，出现下面的信息，表示已完成迁移；可到对应的数据库中进行查看

[img]
6. 同理，完成region表到usercenter、becensus库的迁移，迁移步骤相同，只是目标数据源换成usercenter、becensus的库

### chunk2 **大小类迁移(cgdb-\>eurbanpro)**
[**大小类迁移(cgdb-\>eurbanpro)**]
1. 检查/导入迁移脚本

[export-大小类.json](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXLbYE4Rx5qX1/att/da190b2c-c184-467e-a7db-fe66b68fb7a8.json?Expires=1782159357&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=hkiTwd0iCuv1gqvusgV1sT4rrMw%3D)

[img]
2. 检查添加数据源

主要创建cgdb、eurbanpro的数据源，
3. 按照迁移顺序进行迁移，先编辑【1问题来源】

[img]
4. 编辑任务后，进入配置页面
1. 配置源端信息：
1. 数据源类型：数据源类型
2. 数据源：选择配置的老系统统计库数据源名称，如：cgdb
2. 配置目标端信息：
3. 数据源类型：数据源类型
4. 数据源：选择配置的迁入数据的数据源名称，如：eurbanpro

[img]
5. 点击预览，如果预览有问题，可能是字段的问题，在老系统业务库cgdb库中执行，直至调试成功，再拷贝到自定义查询中，进行预览，预览成功后，点击【下一步】，直至试跑界面
6. 进行试跑，可刷新日志，出现下面的信息，表示已完成迁移；可到对应的数据库中进行查看

[img]
7. 同理，根据编号，完成其他【2案件类型】、【3问题类型大小类】、【4立结案条件】、【5责任网格类型】、【6责任网格数据】、【7单元网格数据】、【8问题来源-案件类型】、【9大小类-案件类型】、【10问题来源-大小类】的迁移

### chunk3 **组织机构迁移（cgdb-\>usercenter）**
[**组织机构迁移（cgdb-\>usercenter）**]
1. 检查迁移脚本，如果没有，导入对应的脚本

[组织架构.json](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXLbYE4Rx5qX1/att/d994da2f-7b71-4fb5-98fc-bbbf973b12e0.json?Expires=1782159357&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=L6U9PhteWa80HCdVfCzpFVHPips%3D)

[img]
2. 检查/添加数据源

主要创建cgdb、eurbanpro的数据源，

### chunk4 **组织机构迁移（cgdb-\>usercenter）** / **迁移部门数据（tc\_unit-\>sys\_unit）**
[**组织机构迁移（cgdb-\>usercenter）** / **迁移部门数据（tc\_unit-\>sys\_unit）**]
1. 查看麒舰默认租户的租户标识，如：egova

[img]
2. 点击【部门同步】的编辑按钮

[img]
3. 进入编辑界面，修改和确认以下信息
1. 配置源端信息：
1. 数据源类型：数据源类型
2. 数据源：选择配置的老系统业务库数据源名称，如：cgdb
2. 配置目标端信息：
3. 数据源类型：数据源类型
4. 数据源：选择配置的迁入数据的数据源名称，如：usercenter
3. 自定义查询sql修改，需要修改为步骤1查询到的租户标识
4. 前置sql修改， tenant\_id就是步骤1查到的iddelete from sys\_unit where tenant\_id = egova

[img]
3. 点击下一步至转换/过滤函数，点击编辑，
1. 修改现场星桥真实ip和端口dex-api
2. 修改星桥新增数据源时，用户中心数据库对应的数据源名称，即创建的用户中心数据库的数据源名称

[img]
3. 用户中心的ip和端口，改成现场的ip和端口

[img]
4. 点击【试跑】，完成部门的迁移

### chunk5 **组织机构迁移（cgdb-\>usercenter）** / **岗位数据迁移(tc\_role -\> sys\_role)**
[**组织机构迁移（cgdb-\>usercenter）** / **岗位数据迁移(tc\_role -\> sys\_role)**]
1. 点击【岗位同步】的编辑按钮

[img]

2. 编辑任务后，进入以下界面，修改和确认以下信息：
1. 配置源端信息：
1. 数据源类型：数据源类型
2. 数据源：选择配置的老系统业务库数据源名称，如：cgdb
2. 配置目标端信息：
3. 数据源类型：数据源类型
4. 数据源：选择配置的迁入数据的数据源名称，如：usercenter
3. 自定义查询sql修改，需要修改为步骤1查询到的租户标识
4. 前置sql修改，tenant\_id就是步骤1查到的id

[img]
3. 点击下一步至转换/过滤函数，点击编辑，
5. 修改现场星桥真实ip和端口dex-api
6. 修改星桥新增数据源时，用户中心数据库对应的数据源名称，即创建usercenter数据库对应的数据源名称

[img]
7. 用户中心的ip和端口，改成现场的ip和端口

[img]

### chunk6 **组织机构迁移（cgdb-\>usercenter）** / **人员数据迁移(tc\_human -\> sys\_human)**
[**组织机构迁移（cgdb-\>usercenter）** / **人员数据迁移(tc\_human -\> sys\_human)**]
1. 点击【人员同步】任务的编辑按钮

[img]
2. 编辑任务后，进入以下界面，修改和确认以下信息：
1. 配置源端信息：
1. 数据源类型：数据源类型
2. 数据源：选择配置的老系统业务库数据源名称，如：cgdb
2. 配置目标端信息：
3. 数据源类型：数据源类型
4. 数据源：选择配置的迁入数据的数据源名称，如：usercenter

[img]
3. 点击下一步至转换/过滤函数，点击编辑，
3. 修改现场星桥真实ip和端口dex-api
4. 修改星桥新增数据源时，用户中心数据库对应的数据源名称，即3.1章节创建的数据源名称

[img]
5. 用户中心的ip和端口，改成现场的ip和端口

[img]

### chunk7 **组织机构迁移（cgdb-\>usercenter）** / **人员岗位关联(tc\_human\_role -\> sys\_human\_role)**
[**组织机构迁移（cgdb-\>usercenter）** / **人员岗位关联(tc\_human\_role -\> sys\_human\_role)**]
1. 点击【人员岗位关联】的编辑按钮

[img]
2. 编辑任务后，进入以下界面，修改和确认以下信息：
1. 配置源端信息：
1. 数据源类型：数据源类型
2. 数据源：选择配置的老系统业务库数据源名称，如：cgdb
2. 配置目标端信息：
3. 数据源类型：数据源类型
4. 数据源：选择配置的迁入数据的数据源名称，如：usercenter

[img]
3. 点击下一步，直至试跑界面，点击【试跑】，通过刷新日志，可看是否完成迁移

### chunk8 **组织机构迁移（cgdb-\>usercenter）** / **岗位部门关联同步迁移（** tc\_role-\>sys\_role\_unit**）**
[**组织机构迁移（cgdb-\>usercenter）** / **岗位部门关联同步迁移（** tc\_role-\>sys\_role\_unit**）**]
1. 点击【岗位部门关联同步】的编辑按钮

[img]
2. 编辑任务后，进入以下界面，修改和确认以下信息：
1. 配置源端信息：
1. 数据源类型：数据源类型
2. 数据源：选择配置的老系统业务库数据源名称，如：cgdb
2. 配置目标端信息：
3. 数据源类型：数据源类型
4. 数据源：选择配置的迁入数据的数据源名称，如：usercenter

[img]
3. 点击下一步，直至试跑界面，点击【试跑】，通过刷新日志，可看是否完成迁移

### chunk9 **业务数据迁移（cgdbstat/cgdb-\>becensus)** / **迁移前处理**
[**业务数据迁移（cgdbstat/cgdb-\>becensus)** / **迁移前处理**]
1. **在统计库(becensus)创建(to\_stat\_info、to\_his\_rec、to\_rec\_process、to\_his\_media)表**，用于迁移数据至这些表中。
1. mysql类型数据库下建表语句：

[MigrationTable.sql](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXLbYE4Rx5qX1/att/5e43a53b-de31-425f-9c78-e26dc8fda717.sql?Expires=1782159357&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=%2BAFdQUbl6oArNf8y68h9FelfMX0%3D)

2. **达梦数据库类型下的建表语句**

[MigrationTable-dm.sql](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXLbYE4Rx5qX1/att/733d7e8b-bd8b-4cd3-8890-c7c2ccaa0068.sql?Expires=1782159357&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=0dZKmY7qhgKFwtJcdO9K%2B6WoMeg%3D)

2. **检查数据同步-任务管理中，是否有业务数据的迁移脚本，若没有，导入以下脚本**

### chunk10 **业务数据迁移（cgdbstat/cgdb-\>becensus)** / **迁移前处理**
[export-业务数据.json](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXLbYE4Rx5qX1/att/12be4bf0-ee6b-4a63-9624-8db208caa35b.json?Expires=1782159357&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=3JgkdPvXhCUxQ4I9pbFhj3dSHm4%3D)

[img]
3. 检查API管理-API注册中，是否有【智信云迁移麒舰】，若没有，进行导入

[data-model-api.json](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXLbYE4Rx5qX1/att/479062b1-ac0a-484e-afb5-fbc04fcfc7f5.json?Expires=1782159357&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=2Ug0bwFBB%2F%2FZ9C1QNSL4LU%2BO58U%3D)

[img]
4. 在星桥中添加数据源：
3. 老系统的统计数据库，如：老城管cgdbstat，用于迁移统计数据，对应第2章节的数据源选择
4. 老系统的业务数据库，如：老城管cgdb，用于迁移件案件数据，对应第3章节数据源的选择
5. 迁入数据的数据源，如：新数据库becensus，对应第1**章节中创建的数据表对应的becensus库**

### chunk11 **业务数据迁移（cgdbstat/cgdb-\>becensus)** / **统计数据迁移(****)**
[**业务数据迁移（cgdbstat/cgdb-\>becensus)** / **统计数据迁移(****)**]
1. 在任务管理中，找到对应的迁移任务：【1统计数据】，点击【编辑】，进入数据源信息的配置界面，填写数据源信息
1. 配置源端信息：
1. 数据源类型：数据源类型
2. 数据源：选择配置的老系统统计库数据源名称，如：老城管cgdbstat
2. 配置目标端信息：
3. 数据源类型：数据源类型
4. 数据源：选择配置的迁入数据的数据源名称，如：新数据库becensus

[img]

2. 点击预览，看是否预览成功，若预览成功，点击【下一步】，跳转到步骤4；
3. 若不成功，将自定义查询语句在老系统的统计数据库中进行查询，一般是一些字段现场没有，删除查不到的字段，直至调试成功，并将调试好的语句拷贝至自定义查询框中，再次点击预览，预览成功后，点击【下一步】
4. 进入字段映射界面，字段会自动映射，点击【下一步】

[img]
5. 进入脚本转换页面，点击【试跑】，一般数据量比较大，迁移时间较少，可通过点击【刷新日志】查看迁移过程，一般出现以下内容，说明迁移完成，可进入迁移的数据库中查看是否有迁移的数据

[img]

### chunk12 **业务数据迁移（cgdbstat/cgdb-\>becensus)** / **案件数据(cgdb.to\_his\_rec -\> becensus.to\_rec)**
[**业务数据迁移（cgdbstat/cgdb-\>becensus)** / **案件数据(cgdb.to\_his\_rec -\> becensus.to\_rec)**]
1. 在任务管理中，找到对应的迁移任务：【2统计数据】，点击【编辑】，进入数据源信息的配置界面，填写数据源信息
1. 配置源端信息：
1. 数据源类型：数据源类型
2. 数据源：选择配置的老系统统计库数据源名称，如：老城管cgdb
2. 配置目标端信息：
3. 数据源类型：数据源类型
4. 数据源：选择配置的迁入数据的数据源名称，如：新数据库becensus

[img]

[img]

2. 点击预览，看是否预览成功，若预览成功，点击【下一步】，跳转到步骤4；
3. 若预览不成功，将自定义查询语句在老系统的业务库中进行查询，一般是一些字段现场没有，删除查不到的字段，直至调试成功，并将调试好的语句拷贝至自定义查询框中，再次点击预览，预览成功后，点击【下一步】

[img]

[img]
4. 字段映射页面，点击【下一步】
5. 进入脚本转换页面，点击【试跑】，一般数据量比较大，迁移时间较少，可通过点击【刷新日志】查看迁移过程，一般出现以下内容，说明迁移完成，可进入迁移的数据库中查看是否有迁移的数据

[img]

### chunk13 **业务数据迁移（cgdbstat/cgdb-\>becensus)** / **办理经过(cgdb.to\_rec\_process-\>becensus)**
[**业务数据迁移（cgdbstat/cgdb-\>becensus)** / **办理经过(cgdb.to\_rec\_process-\>becensus)**]
1. 在API管理-API注册中，点击【智信云迁移麒舰】

[img]
2. 将环境变量修改为MIS的内网访问地址

[img]
3. 在【前置脚本】中，url地址的ip和端口，修改为MIS内网的访问地址；humanId的100433换成老系统tc\_human表中存在的humanId，

[img]
4. 在后置脚本中，将sql.of中的内容，改成迁入数据的数据源，如：新数据库becensus

[img]
5. 在任务管理中，编辑【3办理经过】

[img]
6. 配置源端信息：
1. 数据源类型：数据源类型
2. 数据源：选择配置的迁入数据的数据源名称，如：新数据库becensus
1. 配置目标端信息：
3. 数据源类型：http（即上面配置的api接口）
4. 数据源：智信云迁移麒舰（HTTP)（即api接口的名称）

[img]
1. 点击【试跑】，会进行数据的迁移，改时间会比较长，可通过点击【刷新日志】查看迁移情况，或迁移数据库查看becensus.to\_rec\_process表

### chunk14 **多媒体关系迁移(cgdb-\>becensus)**
[**多媒体关系迁移(cgdb-\>becensus)**]
1. 检查数据同步-任务管理中，是否有业务数据的迁移脚本，若没有，导入以下脚本

[export-多媒体数据.json](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXLbYE4Rx5qX1/att/5f7f2871-7ae4-4394-9612-73512a302786.json?Expires=1782159357&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=iUAzNRbTzqNFXAiG%2FhrVb4g5vhs%3D)

[img]
2. 在任务管理中，找到对应的迁移任务：【1案件多媒体】，点击【编辑】，进入数据源信息的配置界面，填写数据源信息
1. 配置源端信息：
1. 数据源类型：数据源类型
2. 数据源：选择配置的老系统业务库数据源名称，如：老城管cgdb
2. 配置目标端信息：
3. 数据源类型：数据源类型
4. 数据源：选择配置的迁入数据的数据源名称，如：新数据库becensus

[img]
3. 点击预览，如果预览有问题，可能是字段的问题，在老系统业务库cgdb库中执行，直至调试成功，再拷贝到自定义查询中，进行预览，预览成功后，点击【下一步】，直至试跑界面

[img]
4. 点击试跑，直至迁移成功，也可以到becensus库中，查看迁移的表内容

[img]

### chunk15 **监督员数据迁移（cgdb-\>eurbanpro）**
[**监督员数据迁移（cgdb-\>eurbanpro）**]
监督员数据迁移是将智信云监督员tc\_patrol相关表数据迁移到麒舰patrol相关表。
1. 检查数据同步-任务管理中，是否有监督员数据的迁移脚本，若没有，导入以下脚本：

[export-监督员数据迁移.json](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXLbYE4Rx5qX1/att/ed42c8e1-59b2-407e-b4e3-8a2ed6f86e8c.json?Expires=1782159357&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=hrnt2yqHKG43MlrqpNgDqfFImAI%3D)

本次监督员模块数据迁移，共配置 **4 个定时任务**，迁移涉及的源表与目标表如下：

`tc_patrol_type` → `patrol_dic_type`

`tc_patrol` → `patrol`

`tc_patrol` → `patrol_type_rel`

`tc_duty_grid_patrol` → `patrol_duty_grid_rel`

[img]

从上至下依次完成：同步监督员类型字典数据，同步监督员数据，同步监督员类型关联关系数据，同步监督员责任网格关联关系数据。
1. 检查添加数据源

主要创建智信云业务库cgdb和麒舰数据库eurbanpro的数据源
2. 编辑任务后，进入配置页面
1. 配置源端信息：
1. 数据源类型：数据源类型
2. 数据源：选择配置的老系统统计库数据源名称，如：cgdb
2. 配置目标端信息：
3. 数据源类型：数据源类型
4. 数据源：选择配置的迁入数据的数据源名称，如：eurbanpro

### chunk16 **监督员数据迁移（cgdb-\>eurbanpro）**
[img]
3. 点击预览，如果预览有问题，可能是字段的问题，在老系统业务库cgdb库中执行，直至调试成功，再拷贝到自定义查询中，进行预览，预览成功后，点击【下一步】，直至试跑界面
4. 进行试跑，可刷新日志，出现下面的信息，表示已完成迁移；可到对应的数据库中进行查看

[img]

