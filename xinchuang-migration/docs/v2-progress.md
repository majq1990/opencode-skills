# v2.0 合并落地进度日志

| 日期 | 步骤 | 结果 |
|---|---|---|
| 2026-10-02 | R51 推进计划排定（五阶段，节点 10-31）；知识库双通道实测（公网 MCP 加钉钉 OAuth 鉴权，用户 token 配置 `D:\opencode\config\redmine-assist-mcp.json`；SSH bridge 通道 8 主题 121.7s 捞 40 案件） | ✅ 计划文档 `D:\opencode\file\2026-10-02\R51-信创迁移推进计划.md` |
| 2026-10-02 | 摸底：既有仓库 v1.0（检索型，9-08 建库：MCP/REST/兜底架构+playbooks+23 篇全文+机器人集成）× Q3 提交物（现场作业型：李涵 7378 与武扬 7093 为**孪生包**，字节级一致，仅 8 处现场参数差异） | ✅ 定合并策略：升 v2.0.0，取李涵版为现场基线 |
| 2026-10-02 | P0 资产入库：77 截图 + migration_steps/service_management/image_catalog/图册模板 + 3 备份脚本；脱敏（`{{ONEOPS_IP}}`×2、`{{DM_PWD_EXAMPLE}}`×3，4 个敏感字面量全仓归零） | ✅ 脱敏复扫零残留 |
| 2026-10-02 | P1 SKILL.md 合并升 v2.0.0：现场六阶段×知识检索×自动化三线合体，新增场景路由/停止条件 6 条/周边 skill 边界（oneinstall-planner→qijian-deploy→本 skill→egova-oneinstall-guide→xinchuang-pkg-probe） | ✅ |
| 2026-10-02 | P1 新增 config：`site_profile.md`（多现场差异表，A/B 档位）+ `product-config-map.json`（16 产品机器可读映射） | ✅ |
| 2026-10-02 | P1 新增 4 自动化脚本：`precheck_env.sh`（只读预检，bash -n 过）、`verify_migration.py`（collect/compare，全静态 SQL+参数绑定）、`check_product_config.py`（16 产品核对）、`kb_query.py`（公网 MCP 直调，SSRF 白名单+私网阻断） | ✅ Mimosa 安全闸两处拦截均已按建议修复（kb_query SSRF、verify_migration SQL 注入→改全静态 SQL） |
| 2026-10-02 | P2 `references/xinchuang-cases.md`：precheck 5 类高频模式 + 40 案件按 6 主题归档 + 4 篇权威 wiki 链接 | ✅ |
| 2026-10-02 | 测试：pytest **15 passed**（compare 语义：缺表判不一致、多表仅提示=liquibase 建表预期；kb_query SSE 解析/token 加载；product_config PASS/FAIL/SKIP）；Windows %TEMP% pytest-of-* 毒 ACL 用 basetemp=work/pytest-tmp 绕过（pytest.ini 固化） | ✅ |
| 2026-10-02 | 冒烟：precheck_env.sh 在 Git Bash 真跑（输出 PASS/WARN/FAIL 结构正确）；check_product_config CLI 真跑（15 产品 SKIP 符合预期）；kb_query 真跑「达梦 SYSGEO2 报错」返回高质量综述（含 gt-dmgeo2 jar 部署要点、#457759 等案件） | ✅ |
| 2026-10-10 | **P3 演练闭环**：真实源库 MySQL 8.0.46 @ 172.21.133.155（cg155 跳板 + SSH 隧道）四库 5589 表全量迁移 **0 FAIL**，四轨独立过程验证（行数对账 / 1394 表逐字段多重集 / 中文回读 / 26 大表指纹）**0 数据丢失** | ✅ 见 `references/mysql-to-dm-runbook.md` |
| 2026-10-10 | **v2.1 实迁作业线**：新增 `references/mysql-to-dm-runbook.md`（七节）+ `scripts/mysqldump_to_dm_ddl.py`（mysqldump DDL → 达梦 DDL 纯文本转换，不连库不执行 SQL）；SKILL.md 三线升四线并接线场景路由/工作流/参考文件；pytest **64 passed** | ✅ Mimosa 闸机结论：写入型 `open()` 判得比读取型严，去掉 `-o` CLI 写路径、只读 stdin/文件 + 一律写 stdout 后通过 |
| 2026-10-10 | 转换器实证校验：拿 cg155 真实 DDL（5243 表 / 61983 列）与迁移引擎 `map_type()` 逐列对比 **1:1 全对上**；产物无反引号 / ENGINE / CHARSET / COLLATE / unsigned / ON UPDATE / 0000-00-00 / USING BTREE / AUTO_INCREMENT / PARTITION 残留 | ✅ 真实数据暴露 3 个坑（time 漏映射 / --prefix 未作用于索引名 / CREATE TABLE LIKE 被静默跳过），均已修 |

| 2026-10-10 | **转换产物拿到 DM8 V8 真执行**（凭据死结已解：演练机 CGDB/Cgdb@2026 可直连 dmPython，此前"业务用户密码未留档"的记忆是错的）：第一轮建表 4107/5243、约束 8782/8911，逐条定位出 **5 个转换器 bug**（行内表注释 / IDENTITY 顺序 / bit 默认值 b'1' / 索引名 schema 内唯一 / 冗余唯一约束）；修后第二轮 **建表 5243/5243、约束 索引 表注释 8911/8911，零失败**（49s + 49s） | ✅ 关键结论：类型逐列 1:1 只证明类型选对，证明不了 DM 认这些语法；5 个 bug 全不在类型映射里 |
| 2026-10-10 | DM 侧反查元数据 + 功能验证：`CHAR_USED='C'` 列 24722 个；255 个汉字写入 `VARCHAR(255 CHAR)` 成功（CHAR_LENGTH=255 / LENGTHB=510）；`IDENTITY(1,1)` 连续插入得 1,2,3；表注释 1069 + 列注释 33395 条全部落库；对象对账 5227 主键 + 93 唯一 + 3 外键 + 2519 索引 + 1069 表注释 = 8911 与产物一致 | ✅ 语义真落地，不是"碰巧建上了" |
| 2026-10-10 | 转换器补 16 个测试（全套 **70 passed**），新增例程检出告警：cgdb 的 `po_sys_config_bak` 过程体内夹带 `create table ... like`，被分号切碎后不进产物，现在点名到 stderr | ✅ 例程本身仍需在达梦侧人工重建（DMSQL 程序语法差异大，非文本替换可解） |


## 已知边界与遗留

- **P3 演练未做**：DM8/AAS 安装包与 license 未在演练机实装（计划允许：先交 v2.0.0，演练顺延 v2.1）。
- **雷同事项未裁决**（用户侧）：李涵/武扬孪生包评分复查由用户决定，与本 skill 技术线无关。
- `verify_migration.py` 行数抽查为人工交互 SQL（模板在 migration_steps.md 4.0/4.4），自动 COUNT 因"标识符无法参数绑定"被安全闸拦截，v2.1 可评估 DM 系统视图统计口径替代。
- skills-manager 发现页导入需用户在应用内操作（双层结构，见记忆 skills-manager-discovery-import）。
