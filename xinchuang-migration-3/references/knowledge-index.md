# 信创迁移知识索引（2026-09-08 抽取自 demo redmine-assist）

> 来源：`/opt/redmine-assist/data/vectors.db`（issues_meta + docs_meta + doc_chunks_meta）
> 全量数据见 `knowledge-index-docs.md`（130 篇文档全文清单）和 `key-docs-fulltext.md`（23 篇关键文档全文）。
> 处理手册见 `migration-playbooks.md`（精编版）。

---

## 文档分类清单（按主题）

| 主题 | 文档数 | 典型文档 |
|---|---|---|
| 达梦 DM | 37 | MySQL迁移达梦步骤、星桥迁移达梦库步骤、数据中心10迁移到达梦、灵珑MySql库迁移至达梦库、毕升系统数据从MySQL迁移到达梦、明镜_数据库mysql迁移达梦、达梦数据库迁移、GIS达梦数据库启动报错、达梦数据库压测注意事项 |
| 人大金仓 Kingbase | 23 | MySQL迁移至KingbaseES操作说明、星桥数据迁移至人大金仓、人大金仓数据库迁移、金仓兼容mysql模式、人大金仓数据库过期授权、星桥-人大金仓环境部署、毕升微服务人大金仓版本部署 |
| 瀚高 HighGo | 17 | 明镜_数据库mysql迁移瀚高、瀚高数据库迁移、封版瀚高兼容问题汇总、瀚高兼容问题处理-星桥、灵珑平台瀚高版本部署、毕升微服务瀚高版本部署 |
| 海量 Vastbase | 9 | 海量数据库迁移、毕升迁移海量数据库、星桥连接海量数据库无表结构、华为海量数据库人大金仓数据源适配 |
| 国产中间件 | 7+ | Apusic安装和部署说明、毕升宝兰德部署、毕升金蝶中间件、生命线应用金蝶中间件适配、用户中心金蝶中间件国产化改造支持、金蝶中间件、金蝶相关native方法内存马攻击漏洞修复支持；**东方通**见分片（灵珑中间件配置/oneops监控部署等） |
| 信创总括 | 12 | 03_信创数据库适配问题、Cim服务中心国产化数据库配置、切换国产化数据后启动报错、国产化启动失败、国产化配置、排水国产化部署注意事项、明镜_信创环境部署 |
| 数据迁移 | 46 | MinIO迁移方案、MinIO迁移至RustFS、PG数据库迁移后如何从geom修复位置字段、城运大屏白模数据迁移至悟空地图、全行业相关数据表迁移、批量迁移附件数据、物联网平台-数据迁移-1.0迁移到2.0、标签tc_rec_mark_item迁移新版标签表记录 |
| 麒麟 Kylin | 1 | 麒麟 V10 服务器安装 Python2 环境及问题处理记录 |
| 欧拉 openEuler | 0 | 见工单（38 条） |
| 统信 UOS | 0 | 见工单（32 条） |
| 国产 CPU | 1 | 即时通讯arm架构部署 |

---

## 精选工单（按主题，各取 10 条以内高价值/高相关性）

### 达梦 DM（724 条）
- #526688 案件抽查模块升级需求达梦环境上增加抽查模块功能
- #526022 灵珑数据视图修复达梦数据库SQL诊断连接获取错误
- #525590 深圳民生诉求达梦测试环境下综合查询排错
- #525541 Framework索引管理服务适配达梦数据库
- #525534 毕升测试环境配置界面组织机构用达梦数据库查询表报错修复
- #525384 自贡运管服达梦主键自增问题处理
- #525266 锦州燃气达梦与灵珑版本系统功能适配问题
- #524901 自贡运管服采集升级python3适配达梦对接逻辑
- #524224 灵珑升级1.6.0.83 MySQL迁移到达梦
- #524111 物联网2.0物联设备管理设备地图/监测详情适配达梦数据库

### 人大金仓 Kingbase（324 条）
- #523792 海南CIM人大金仓矢量与编目服务发布适配
- #523790 海南CIM人大金仓资源删除与模式清理适配
- #523707 海南CIM cimserver2.0适配人大金仓pg及达梦数据库
- #520115 清远微地图星桥功能适配人大金仓数据库
- #516856 吉安城管国产化迁移改造采集适配人大金仓
- #516813 吉安人大金仓采集环境支持
- #513603 海南CIM通途GIS人大金仓适配问题支持
- #512576 清远微地图 eUrbanGIS人大金仓基准文件开发
- #512547 清远微地图市民通功能适配人大金仓
- #509624 芜湖城管升级采集适配人大金仓

### 瀚高 HighGo（760 条）
- #526070 威海市运管服瀚高数据库物联网设备对接数据更新机制优化
- #524761 青岛运管服悟能智云版本适配瀚高
- #524354 青岛运管服住建部采集脚本适配瀚高数据库
- #517448 青岛运管服瀚高数据库慢sql优化
- #515241 灵珑 cursor分页查询接口适配达梦瀚高等数据库
- #514806 嘉祥运管服悟空适配瀚高异常
- #513049 统一用户中心2.1.1瀚高环境升级问题
- #511283 灵珑更新嘉祥运管服瀚高
- #510791 临沂智慧城管信创改造 pub-ex包兼容瀚高数据库
- #508737 青岛运管服违法建设监管子系统瀚高适配问题汇总

### 海量 Vastbase（110 条）
- #526852 长沙排水海量数据库适配问题汇总
- #525475 天津垃圾分类海量数据库查询已审批报错
- #525302 海量适拦截器修复
- #523854/853/852/851 长沙排水麒舰排水相关服务信创环境适配支持——海量适配
- #522401 长沙排水海量数据库G100管理系统V2.2
- #512182 天津垃圾分类星桥连接海量数据库无表结构

### 麒麟/欧拉/统信（OS适配）
- #522402 长沙排水银河麒麟高级服务器操作系统V10
- #498284 南昌运管服国产银河麒麟V10服务器漏洞修复
- #377864 信创一键部署 openEuler-22.03-LTS-amd64 测试问题汇总
- #362855 绵阳运管服信创迁移过程应用及中间件一键部署失败问题支持排查
- #454117 临沂智慧城管信创改造智信云测试问题排查支持
- #340934 烟台一网统管信创改造通图初次部署报错支持

### 国产中间件
- #496155 灵珑平台tomcat替换-160补提
- #441996 江苏省运管服独立中间件及微服务封装中间件适配宝兰德v9.5
- #496120 20260422金蝶中间件国产化改造（微服务产品的改造）-星桥
- #373774 红安环卫系统国产中间件-中创适配支持
- #340190 堆龙行政执法执法eLaw达梦金蝶环境部署

#### 金蝶（Apusic）精选工单（33 条）
- #522403 长沙排水麒舰排水相关服务信创环境适配支持——金蝶Apusic应用服务器V10
- #499836 莆田生命线金蝶中间件国产化改造支持-workflow、patrol_gather
- #499474 毕升金蝶包适配排除tomcat导致类缺少
- #496517 莆田生命线金蝶中间件国产化改造支持-用户中心验证
- #496322 供水金蝶中间件国产化改造（微服务产品的改造）
- #496318 燃气金蝶中间件国产化改造（微服务产品的改造）
- #496316 城市安全/麒舰版市政/管线GIS/管网防护金蝶中间件国产化改造
- #495856 麒舰金蝶中间件国产化改造（微服务产品的改造）
- #495854 主任务金蝶中间件国产化改造（微服务产品的改造）
- #495372 莆田生命线金蝶中间件国产化改造支持
- #476099 GIS服务国产中间件金蝶替换Tomcat
- #415103 灵珑平台tomcat替换金蝶中间件国产化改造（微服务产品的改造）-灵珑
- #404176 临县城管tomcat替换金蝶异常
- #369913 新疆阿克陶县运管服金蝶系统部署支持-采集
- #369912 新疆阿克陶县运管服金蝶系统部署支持-GIS、通图
- #369910 新疆阿克陶县运管服金蝶系统部署支持-MIS（挂起）

#### 东方通（TongWeb）
- 无独立文档，内容散布于灵珑中间件配置、oneops监控部署等文档分片中
- 灵珑配置："Servlet容器类型"= tongWeb，license.dat

### CPU适配（鲲鹏/飞腾/海光/ARM）
- #499634 华为鲲鹏认证-玄藏环境问题排查
- #498461 华为鲲鹏认证-城市安全产品部署
- #498144 华为鲲鹏认证
- #460412 国产化部署一键部署arm架构
- #388038 渣土车牌ocr识别算法适配现场鲲鹏CPU

### 信创总括（1517 条）
- #526680 杭州信创麒舰更新任务
- #526386 东营城管信创改造案件延期
- #526138 杭州一网统管信创处置通链接配置项changelog补提
- #526066 焦作运管服城市安全服务更新兼容国产化数据库
- #525672 青岛运管服信创改造适配任务-垃圾分类子系统问题汇总

### 数据迁移（2193 条）
- #526838 宜昌考核升级智云版本统计/查询迁移到毕升
- #526731 湖北省厅运管服建筑垃圾dm库主机迁移
- #526281 毕升智能报表指标直连/派生字段分流与筛选条件默认化全链迁移
- #526227 海南CIM测试环境迁移至生产环境麒舰栏目打开报错

---

## 钉钉知识库链接汇总（最值得精读的文档）

| 文档 | URL |
|---|---|
| MySQL迁移达梦步骤 | https://alidocs.dingtalk.com/i/nodes/jb9Y4gmKWr7l1v5MijG0BYRaVGXn6lpz |
| MySQL迁移至KingbaseES操作说明 | https://alidocs.dingtalk.com/i/nodes/R1zknDm0WR3eownji2XM36oDVBQEx5rG |
| 达梦数据库迁移 | https://alidocs.dingtalk.com/i/nodes/Qnp9zOoBVBZzoL47cL1PlLonV1DK0g6l |
| 星桥迁移达梦库步骤 | https://alidocs.dingtalk.com/i/nodes/Gl6Pm2Db8D3moL97iGK0pq5QJxLq0Ee4 |
| 星桥数据迁移至人大金仓 | https://alidocs.dingtalk.com/i/nodes/MNDoBb60VLrOowp4SPDXnrzr8lemrZQ3 |
| 星桥数据由mysql迁移到达梦 | https://alidocs.dingtalk.com/i/nodes/gwva2dxOW4KpzGNXUByxLnx28bkz3BRL |
| 灵珑MySql库迁移至达梦库 | https://alidocs.dingtalk.com/i/nodes/2Amq4vjg89gq7LzDsQZMrXORV3kdP0wQ |
| 明镜_数据库mysql迁移达梦 | https://alidocs.dingtalk.com/i/nodes/MNDoBb60VLrOowp4SB0LEz0X8lemrZQ3 |
| 明镜_迁移达梦后字段内容后补全空格问题处理 | https://alidocs.dingtalk.com/i/nodes/Gl6Pm2Db8D3moL97i9bQdK4YJxLq0Ee4 |
| 明镜_信创环境部署 | https://alidocs.dingtalk.com/i/nodes/14lgGw3P8vvl1M5XTpyO3ekM85daZ90D |
| 明镜_数据库mysql迁移瀚高 | https://alidocs.dingtalk.com/i/nodes/gwva2dxOW4KpzGNXU0epRGDN8bkz3BRL |
| 毕升系统数据从MySQL迁移到达梦 | https://alidocs.dingtalk.com/i/nodes/G1DKw2zgV2RXpGMNTBQqMlyMVB5r9YAn |
| 海量数据库迁移 | https://alidocs.dingtalk.com/i/nodes/14lgGw3P8vvl1M5XTpzvY0Yw85daZ90D |
| 瀚高数据库迁移 | https://alidocs.dingtalk.com/i/nodes/R1zknDm0WR3eownjixpDbbLvVBQEx5rG |
| 人大金仓数据库迁移 | https://alidocs.dingtalk.com/i/nodes/lyQod3RxJK3moqXKi4roYvzOJkb4Mw9r |
| 数据中心10迁移到达梦 | https://alidocs.dingtalk.com/i/nodes/YQBnd5ExVEwmoLDOs039vvvk8yeZqMmz |
| 全行业数据库切换处理 | https://alidocs.dingtalk.com/i/nodes/Gl6Pm2Db8D3moL97i91YyGO3JxLq0Ee4 |
| 国产化启动失败 | https://alidocs.dingtalk.com/i/nodes/gvNG4YZ7JneM3nBvc9xgydeMV2LD0oRE |
| 切换国产化数据后启动报错 | https://alidocs.dingtalk.com/i/nodes/14lgGw3P8vvl1M5XTQRk0RvP85daZ90D |
| 排水国产化部署注意事项 | https://alidocs.dingtalk.com/i/nodes/MNDoBb60VLrOowp4SBe1KxLL8lemrZQ3 |
| 智信云迁移麒舰数据迁移操作步骤 | https://alidocs.dingtalk.com/i/nodes/m9bN7RYPWdlgzjZLfKPywl3DWZd1wyK0 |
| MinIO迁移方案 | https://alidocs.dingtalk.com/i/nodes/MNDoBb60VLrOowp4SB7nBbzM8lemrZQ3 |
| 03_信创数据库适配问题 | https://alidocs.dingtalk.com/i/nodes/2Amq4vjg89gq7LzDsQAdwdXGV3kdP0wQ |
