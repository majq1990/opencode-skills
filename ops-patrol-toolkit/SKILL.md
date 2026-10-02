---
name: ops-patrol-toolkit
version: 1.0.0
author: 工程技术中心
license: MIT
category: ops
visibility: tech-center
description: 运维巡检与故障排查通用工具集（R48）。凡涉及：运维巡检、故障排查、巡查数据汇总、人巡/机巡/部件三源合并、巡查日报标准输入、巡查明细表生成、MySQL 只读副本高 I/O 分诊、iostat 解析、慢查询 digest 分析、全表扫描/回表放大/排序落盘/大字段溢出/复制回放根因判定、项目维护手册规范化生成、手册章节完整性与要素缺失检测、月度运维报告生成、服务器/网址批量巡检、月报 Word 模板回填、运维材料脱敏——都应使用本 Skill。
---

# ops-patrol-toolkit · 运维巡检与故障排查工具集

## 目标

把巡查/巡检/诊断/月报四类高频运维工作固化为一套零依赖、离线可跑、可独立调用的脚本工具集：

1. **巡查数据三源汇总**：人巡/机巡/部件 Excel 源表 → 统一 9 列明细表（巡查日报标准输入）
2. **MySQL 只读副本高 I/O 分诊**：iostat + 慢查询 digest + 表 DDL → 根因候选 + 置信度 + 证据链 → 中文诊断报告
3. **维护手册规范化**：零散立项资料 → 标准章节手册初稿（待补项占位）+ 章节完整性/要素缺失检测
4. **月度运维报告**：批量网址/服务器巡检 + 业务统计数据（JSON 输入）→ 回填 Word 月报模板

## 依赖

- Python 3.8+，**只用标准库**，无第三方包，01-04 离线可跑
- 05 需访问公司 redmine-assist MCP（网络出站），token 经环境变量 `DEMO_EGOVA_MCP_TOKEN` 注入（钉钉扫码获取，见 `config/patrol/kb_search.json`），缺失即 gap 停止
- 不需要数据库连接；输出统一写到 `work/` 或显式 `--out` 路径；模板与配置原件永不改写

## 子工具路由

| 步骤 | 脚本 | 说明 |
|---|---|---|
| 01 | `scripts/01_patrol_merge.py` | 三源巡查 Excel → 9 列明细表（xlsx/csv） |
| 02 | `scripts/02_mysql_io_triage.py` | MySQL 只读副本高 I/O 根因分诊（只读，零连接） |
| 03 | `scripts/03_manual_standardize.py` | 维护手册生成 + 规范检测（双模式，生成后自动回检） |
| 04 | `scripts/04_monthly_report.py` | 服务器巡检 + 月报模板回填 |
| 05 | `scripts/05_kb_similar_search.py` | 历史相似案例检索（redmine-assist MCP：17 万工单 + 4500 篇知识库文档） |
| 公共 | `scripts/redact.py` | 材料脱敏（先脱敏再分析，保留数值口径） |

## 快速开始

```powershell
# 01 三源汇总（--yes 确认字段映射后写产物；不带 --yes 只预览映射与样例行）
python scripts/01_patrol_merge.py --config config/patrol/sources.json --yes --out work/patrol/summary.xlsx

# 02 I/O 分诊（iostat 必填，digest/ddl 缺失自动降级并在报告中标注）
python scripts/02_mysql_io_triage.py run --iostat examples/iostat.txt --digest examples/digest.csv --ddl examples/schema.sql --out work/io_triage

# 03 手册生成（生成后自动回跑检测，P0 应为 0）
python scripts/03_manual_standardize.py generate --info project_info.json --sources 资料1.docx 资料2.docx --out work/manual/draft.docx
python scripts/03_manual_standardize.py check --manual work/manual/draft.docx

# 04 服务器巡检 + 月报回填（业务统计数据由人工/其他工具产出为 JSON，本工具不直连业务系统）
python scripts/04_monthly_report.py check-servers --config config/patrol/servers.json
python scripts/04_monthly_report.py fill --template assets/monthly-report-template.docx --stats stats.json --out work/monthly/2026-09月报.docx

# 05 历史相似案例检索（需联网；token 环境变量 DEMO_EGOVA_MCP_TOKEN，钉钉扫码获取）
python scripts/05_kb_similar_search.py query --text "MySQL只读副本磁盘IO高，慢查询全表扫描" --out work/kb/result.md
# 02→05 闭环：用分诊结果自动拼检索词
python scripts/05_kb_similar_search.py from-triage --triage work/io_triage/triage.json
```

## 输出契约

- 每个脚本 stdout **最后一行**是 JSON 信封：成功 `{"ok": true, ...}`；失败 `{"ok": false, "gap": "一句可行动的缺失说明"}` 并以退出码 2 结束
- 中间过程信息打印在信封之前的行；**控制台不使用 emoji**
- 报告类产物默认带 **【待复核】** 标记，未经人工复核不得外发

## 停止条件（触发即停，输出 gap，不猜测不伪装成功）

1. 输入文件缺失/损坏/无法识别工作表或分隔符
2. 01：字段映射无法确认（`--yes` 未给且样例行待确认）
3. 02：iostat 内容为空或识别不到设备段
4. 03：项目信息 JSON 缺必备键或资料全部无法解析
5. 04：模板文件缺失，或 stats.json 结构不符合约定
6. 05：环境变量 `DEMO_EGOVA_MCP_TOKEN` 未设置，或 MCP 端点不可达/超时/返回错误
7. 任何凭证类环境变量（`*_env_ref`）未设置——缺前置即停，不猜测

## 安全约束

- 材料先脱敏（`scripts/redact.py`）再分析；数据库密码、API 密钥、token、客户/人员/合同信息、未脱敏生产数据**禁止输入**
- 02 全程只读：不连接数据库、不执行任何 DDL/DML/KILL/参数修改，只读入参文件
- 所有建议均为建议，需人工复核 + 测试环境验证，禁止直接上生产
- 配置只放阈值/路径/清单；真实客户 IP、签名密钥、账号一律不进本仓库
- 涉密/敏感数据（个人标识、政府内部、公司内部、精确坐标、密级文件）严禁作为输入

## 已知边界

- 04 的业务统计数据走 JSON 文件输入，不直连客户业务系统（数字城管 API/CDP 等属客户环境定制，不在通用版内）
- xlsx 读取支持常规表格（共享字符串/日期/合并单元格），复杂图表/透视表忽略；不支持老版二进制 .xls
- docx 替换只处理正文（页眉页脚/批注/文本框内文字不替换）；复杂模板建议先另存为标准 docx
- xlsx/docx 解析内置 DTD/实体声明拒绝闸：含 `<!DOCTYPE>`/`<!ENTITY>` 的恶意构造文件（实体扩展攻击）直接拒解析
- 输入/输出路径参数（--file/--out 等）按本地单用户 CLI 威胁模型信任操作者（同 cat/grep 类命令行工具），不做路径白名单
- 04/05 的出站目标来自操作者维护的 config 文件（巡检清单/MCP 端点），属工具本职，不接受不可信输入作为请求目标
