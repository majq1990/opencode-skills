---
name: 通途工期挂起
description: 通途(ztoa)平台工期表/挂起表一站式工具。拉取工期与挂起记录、按日期过滤、补导出 Word 件、构建「项目工期初始化审核」35 列 xlsx。当用户提到 通途工期 / 工期挂起 / 拉取工期 / 工期导出 / 挂起导出 / 工期初始化审核表 / 工期审核 xlsx / 7.1后工期 / ztoa工期 / 补导出工期 或要求把工期、挂起记录导出/汇总成表时使用。
---

# 通途工期挂起一站式工具

覆盖四件事：①拉取三张表全量行 JSON ②按日期过滤 + 对账补导出 docx ③构建 35 列审核表 ④挂起行补全（定级/大区/进场/136 时间/挂起期间延后）。

## 前置条件

- 登录态浏览器 profile：`D:\git\工程实施改造\.edge-profile`（已免登；新机器需先跑 `export_duration_word.mjs login` 扫码一次）
- 依赖：`node` + `playwright`（`C:/Users/majq1/node_modules`）、`python` + `openpyxl` + `python-docx` + `python-dateutil`
- 三张关键表（worksheetId）：
  - 工期表 `69fc30b91e6716810741b4a7`
  - 挂起表 `69fc30c1111e45dac897c658`
  - 交付项目主数据表 `629da7f86f0dcb3b9b7cd603`

## 标准工作流（scripts/ 目录下执行）

```powershell
cd D:\git\opencode-skills\通途工期挂起\scripts

# 1. 拉三张表全量（产出 probe_duration/suspend/projects.json 到工作目录）
node probe_tables.mjs --out D:\opencode\file\<日期>

# 2. 按日期过滤（默认 2026-07-01），产出 dur_since.json / sus_since.json
python filter_since.py --workdir D:\opencode\file\<日期> --since 2026-07-01

# 3. 对账补导出缺失 docx（逐条独立进程+重试；输出落到 --dir 第一个目录）
node run_missing.mjs --type dur --list <workdir>\dur_since.json --dir "D:\opencode\file\2026-09-02,D:\opencode\file\<日期>"
node run_missing.mjs --type sus --list <workdir>\sus_since.json --dir "同上"

# 4. 构建审核表（36 列 schema，含挂起期间延后/占位行剔除/主数据补全）
python build_audit_xlsx.py --workdir <workdir> --since 2026-07-01 `
  --docx-dirs "D:\opencode\file\2026-09-02,D:\opencode\file\<日期>" `
  --old-xlsx "D:\backup\user1\majq\Desktop\20260626项目工期初始化审核.xlsx" `
  --out <workdir>\项目工期初始化审核_7.1后.xlsx
```

## 核心 cid 映射（2026-09 值矩阵交叉验证）

### 工期表
| cid | 字段 | cid | 字段 |
|---|---|---|---|
| 69fc4083...b843 | 项目名称 | 69fc3daa...b7ce | 申请编号 |
| 69fc41b8...b864 | 项目定级 | 6a390615...7bf8 | 合同签订日期 |
| 69fc410a...b858 | 基线初验工期_月 | 69fc41b8...b863 | 基线试运行工期_月 |
| 69fc4126...c958 | 基线终验周期_月 | 6a2a1c29...7279 | 基线一次性验收周期_月 |
| 69fc3bc1...b718 | 进场日期 | 69fc3bc1...b719 | 正式合同签订后进场 |
| 6a043ae9...4864 | 136初始化应初验 | 6a043b99...dcd1 | 136初始化应终验(一次性项目同标签) |
| 6a067fe7...5bd0 | 调整后应初验 | 6a067fe7...5bd1 | 调整后应终验 |
| 69fc3bc1...b71a/b71d | 136最终应初验 | 69fc3bc1...b71b/b72b | 136最终应终验 |
| 69fc40d0...c94b | 所属区域(明文) | 69fc30b9...b4b2 | 申请人(list) |
| 69fc30b9...b4b9 | 申请说明(富文本) | | |

### 挂起表
| cid | 字段 | cid | 字段 |
|---|---|---|---|
| 6a1808ba...7ebe | 项目名称(公式) | 6a0aa397...8975 | 所属区域(明文) |
| 69fc3c58...b750/b751 | 挂起开始/结束日期 | 6a0aa776...26fa | 关联交付项目(含 name+sid+link) |
| 6a0aa1e9...2672 | 挂起类型(对象自带 name①②③) | 69fc30c1...c665 | 挂起原因详述(富文本) |
| 69fc30c1...c667 | 挂起期限_月 | 6a0aa203...267f/267e | 上限/下限 |
| 6a0add0a...9466 | 历次挂起次数 | 6a06efc6...01cb | 累计挂起天数 |
| 69fc30c1...c663 | 申请人(list) | 69fc5fe5...c029 | 自动编号(会重复，勿作匹配键) |

### 交付项目主数据表
| cid | 字段 |
|---|---|
| 629dc18f...cd74f | 项目进场日期（UI 显示为空但 API 有值！） |
| 68d8d201...4e23 / 69fd9981...ec50 | 136 应初验时间（冗余双字段） |
| 68d8d201...4e24 / 69fd9981...ec51 | 136 应终验时间（一次性项目 T/U 同用） |
| 629dc18f...cd740/741/742 | 大区/区域/项目名（明文） |

## 硬规则与坑（必读）

1. **GetFilterRows 必须 `searchType:0` 才是全量**；`searchType:1` 只回部分行（曾漏 10 条）
2. **导出 docx 禁用批量并发模式**：打印预览页触发导出后 4-9 秒自动关闭（站内定时器），未完成的 blob 下载被取消，`saveAs: Target page closed` 是竞态，单次成功率 ~35%。唯一可靠方案 = `run_missing.mjs` 逐条独立浏览器进程 + 重试（MAX_TRY=5, ZTOA_HEADLESS=1, CONCURRENCY=1）
3. 挂起导出 rowsfile 的每条 item **必须带 `attaches` 字段**（可为 []），否则 TypeError
4. 挂起表「关联交付项目」等 list 字段是 **JSON 字符串**，需 `json.loads` 后取 `[0].name/sid`
5. **自动编号（SUS-/STS-）会重复/变化**，docx 与 json 对齐只能用 rowId 或「项目名+挂起开始日期」
6. 同项目多条挂起：文件名第 2 条起带 `-记录N` 后缀；对账按「同名 docx 数 vs 同名记录数（ctime 排序）」比对
7. **0 月占位行**（无类型且期限 0）是真实存在的空记录，构建审核表时丢弃；删除/匹配判断必须看行自身字段，不能用项目级信息（同项目多条会误判）
8. 挂起行项目信息：A 列用 rel.name（含定级前缀）、F 列解析前缀；进场/136 用 rel.sid 查主数据表（`74f/e23/e24`），老表（--old-xlsx）只兜底填空
9. 老表口径：一次性验收项目 P/R 列填 `/`、T/U 填日期；分初验终验项目 T/U 填 `/`；未调整时 Q=P、S=R；独立运维级无需验收，基线全 0 无验收日期
10. 大区映射 `region_mapping.json` 是 6-22 快照，新区域（黑龙江/河北/陕西等）会缺 → build 脚本内置七大区 fallback，仍缺的留空人工确认
11. 行详情页 **UI innerText 会漏显字段值**，必须以 API 行 JSON 为准；GetWorksheetInfo 不返回控件定义（template 只有 version），新 cid 只能值匹配法锚定

## 更新维护

- 本 skill 位于 `D:\git\opencode-skills\通途工期挂起\`（junction 到 `D:\opencode\config\skills\`），改动后 `git -C D:\git\opencode-skills add -A && git commit && git push`
- 新增字段/新坑：先在会话里值匹配验证，再更新本文件 cid 表与坑列表，同步 mem0（user_id majq1）
