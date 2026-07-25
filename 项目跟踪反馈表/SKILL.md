---
name: project-tracking-table
version: 1.0.0
author: majianquan
category: support-dept
visibility: support-dept
description: 按交付项目维度建立「问题/漏洞/任务」跟踪反馈钉钉 AI 表格。从 ztoa 拉「打开+在职项目经理」的 587 个项目，匹配钉钉成员（按部门解决同名），从「大区省份表-琅琊榜特殊使用」回填大区工程总/省份工程总，建一个标准化的反馈表（项目/大区/区域/项目经理/N 选 1 状态/可填字段）。触发词：项目跟踪表 / 问题跟踪 / 反馈表 / CVE 跟踪 / 漏洞反馈 / 按项目分发 / project-tracking-table。
---

# 项目级跟踪反馈表（标准化建表流程）

## 用途

某个问题（漏洞/合规检查/中间件升级/数据上报…）需要按 **交付项目** 维度让项目经理逐一反馈结果时，用本 skill 一条龙完成：

1. 从 ztoa 拉项目清单（项目状态=打开 + 至少一名在职 PM）
2. 解析 PM 姓名 → 钉钉 userId（部门匹配解决同名）
3. 从「大区省份表-琅琊榜特殊使用」回填大区工程总 + 省份工程总（按 大区+区域 联合键）
4. 在钉钉创建标准化 AI 表格（base + table + 字段 + 单选选项）
5. 批量写入项目行（每个项目一行）
6. （可选）通过视图隐藏「大区/省份工程总」，避免填表人误改

## 输入参数（plan.json）

放在 `D:\opencode\_archive\<topic>_plan.json`，例如 `D:\opencode\_archive\CVE-2026-31431_plan.json`：

```json
{
  "topic": "CVE-2026-31431",
  "base_name": "CVE-2026-31431漏洞修复跟踪反馈表",
  "base_desc": "工作说明：项目经理 SSH 服务器跑社区脚本 https://... ，把 OS/版本/内核 + 4 选 1 扫描结果填回来。详细修复方案见钉钉云文档『...』。",
  "result_options": [
    {"name": "PATCHED 已修复", "color": "#00C853"},
    {"name": "MITIGATED 已缓解", "color": "#FFC107"},
    {"name": "VULNERABLE 受影响", "color": "#D32F2F"},
    {"name": "UNKNOWN 未知", "color": "#757575"}
  ],
  "extra_text_fields": [
    "操作系统名称",
    "OS版本",
    "内核版本(uname -r)"
  ],
  "include_engineering_leads": true,
  "feedback_status_options": ["未反馈", "已反馈", "反馈中", "无法反馈"]
}
```

可选项：
- `result_options`：N 选 1 的状态（不一定是 4 个）
- `extra_text_fields`：填表人需要补充的文本字段（不固定，比如换成"中间件名称/版本/JDK 版本"）
- `include_engineering_leads`：是否拉琅琊榜回填大区/省份工程总（默认 true）

## 一条命令跑完（v1）

```bash
cd D:\opencode\config\skills\project-tracking-table
python -m scripts.main D:\opencode\_archive\<topic>_plan.json
```

中间产物全部落到 `D:\opencode\_archive\<topic>_workdir\`。可以中途断、再续：

```bash
# 只跑前 3 步（dry-run，不写 dws）
python -m scripts.main path/to/plan.json --to-step 3

# 从 step 4 开始（前面已经跑过、缓存还在 work_dir）
python -m scripts.main path/to/plan.json --from-step 4
```

## 6 步流程（每一步独立可跑）

| # | 脚本 | 作用 | 关键产物 |
|---|---|---|---|
| 1 | step01_fetch_projects | ztoa 拉打开+在职 PM 项目（约 587 条） | projects.json |
| 2 | step02_resolve_pms | PM 姓名→钉钉 userId（按部门去歧同名） | pm_resolved.json / userid_to_depts.json / projects_with_userids.json |
| 3 | step03_fetch_langya | 琅琊榜映射（仅 include_engineering_leads=true） | langya_mapping.json |
| 4 | step04_create_table | 建 base + 表 + 字段 + 单选 options | table_meta.json |
| 5 | step05_push_records | 批量插记录（20 条/批） | dws AI 表格落地 |
| 6 | step06_fill_engineering_leads | 按 (大区,区域) 回填大区/省份工程总 | dws record 批量 update |
| 7 | （手动） | 钉钉前端隐藏「大区工程总/省份工程总」列+设只读 | — |

## 关键决策（写进脚本 + references/）

- 项目过滤：`项目状态=='打开'` AND `项目经理 status==1`（**中文 value 比，不是 key**）
- 琅琊榜过滤：`是否可用=='是'`（去掉测试行）
- 「大区/省份工程总」= ztoa 「大区责任人/省份责任人」（不是销售总），controlId `63e59b056028cc4370625a92` / `63e59b056028cc4370625a93`
- ztoa OpenAPI **关闭了** user/department 接口（404/405），拿不到工号/手机号 → 必须走 `dws contact user search` + `dws contact user get` 用部门去歧
- dws record 字段名是 **`cells`** 不是 `fields`；user 字段值是 `[{"userId":"x"}]`；单选 options 必须 update 补
- Windows cmd 单参数 ~32K，一批最多 ~20 条；subprocess 必须 `dws.cmd`（不是 `dws`），bytes 读再 `decode('utf-8','replace')`
- dws view update --config 写 hiddenFields **不生效**，字段隐藏只能在钉钉前端右键

## 输出物路径

- 输入 plan：`D:\opencode\_archive\<topic>_plan.json`（可拷 `plan_template.json` 改）
- 中间产物：`D:\opencode\_archive\<topic>_workdir\`
- 表快照（建议手动落）：`D:\opencode\_archive\<topic>_table_snapshot.txt`

## 历史样本

CVE-2026-31431（首次实战，2026-05-06，手工分步跑）：
- baseId: `vy20BglGWOeOolZDc02KElDqJA7depqY`
- 项目数：587 → 删除测试行后 586
- 字段：项目/大区/区域/项目经理/脚本扫描结果(4 选 1)/操作系统名称/OS 版本/内核版本/反馈状态/反馈备注/反馈时间/大区工程总/省份工程总
- 完整快照：`references/case_cve_2026_31431.md`
- v0 阶段散落脚本路径：`D:\git\ztoa-mcp\scripts\probe_*.py / extract_*.py / resolve_*.py / push_*.py`（本 skill v1 已重写到 `scripts/step0[1-6]_*.py`）
