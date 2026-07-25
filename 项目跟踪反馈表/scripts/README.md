# scripts/

> 当前阶段（v0），核心脚本仍在 `D:\git\ztoa-mcp\scripts\` 下，本目录暂只列触发顺序与文件路径。下一次类似建表时把它们搬过来 + 参数化即可。

## 触发顺序与脚本对应

| 步骤 | 脚本 (D:\git\ztoa-mcp\scripts\) | 输入 | 输出 (D:\git\ztoa-mcp\_probe_out\) |
|---|---|---|---|
| 1. fetch projects | `probe_delivery_projects.py` | (无) | `delivery_rows.json`（全量 1851 行）+ `delivery_schema.json` |
| 2. extract & filter | `extract_filtered_projects.py` | delivery_rows.json | `delivery_filtered.json`（587 行：打开+在职 PM） |
| 3. resolve PM userIds | `resolve_pm_userids.py` | delivery_filtered.json | `pm_name_to_userid.json` + `delivery_with_userids.json` |
| 4. refine same-name | `refine_pm_userids.py` | 上一步 + dws contact user get | `userid_to_depts.json` + `delivery_with_userids_v2.json`（同名按部门去歧） |
| 5. fetch langya | `probe_langya_table.py` | (无) | `langya_schema.json` + `langya_rows.json` |
| 6. build langya mapping | `build_langya_mapping.py` | langya_rows.json | `langya_mapping.json` |
| 7. resolve langya userIds | `resolve_langya_userids.py` | langya_mapping.json | `langya_mapping_with_userids.json` |
| 8. build records | `build_feedback_records.py` | delivery_with_userids_v2.json | `records_batch_*.json` |
| 9. push records | `build_and_push_records.py` | 上面所有 | dws AI 表格 |
| 10. fill engineering leads | `push_langya_and_fix.py` | langya_mapping_with_userids.json | dws record update |

## 参数化（v1 规划）

下一版抽出公共配置到 `_config.py`：

```python
ZTOA_BASE = "https://ztoa.egova.com.cn"
ZTOA_APP_KEY = "8f88361d723b7e6c"
ZTOA_SIGN = "ZTk2NTli...=="

WS_DELIVERY = "629da7f86f0dcb3b9b7cd603"           # 交付项目
WS_LANGYA = "63e59ab31c09549442d4717f"             # 大区省份表-琅琊榜特殊使用

# 交付项目字段
F_PROJECT_DAQU_TXT = "629dc18f6f0dcb3b9b7cd740"
F_PROJECT_DAQU_SEL = "62aff5b9182553a4819a42b0"
F_PROJECT_QUYU = "629dc18f6f0dcb3b9b7cd741"
F_PROJECT_NAME = "629dc18f6f0dcb3b9b7cd742"
F_PROJECT_STATUS = "62cb8536182553a4819d6506"
F_PROJECT_PM = "629dc18f6f0dcb3b9b7cd745"

# 琅琊榜字段
F_LY_DAQU = "63e59ab31c09549442d47180"
F_LY_PROVINCE = "63e59b056028cc4370625a8f"
F_LY_DAQU_ENG = "63e59b056028cc4370625a92"  # 大区责任人 = 大区工程总
F_LY_PROV_ENG = "63e59b056028cc4370625a93"  # 省份责任人 = 省份工程总
F_LY_USABLE = "6486d00e1d46a4779da959cd"
```

让 plan.json 决定：
- baseName / desc
- 4 个状态选项
- extra text fields
- 是否拉琅琊榜

## 命令模板（实战速记）

```bash
# 1) 拉项目
cd D:\git\ztoa-mcp
.venv/Scripts/python.exe scripts/probe_delivery_projects.py
.venv/Scripts/python.exe scripts/extract_filtered_projects.py

# 2) 解析 PM userId
.venv/Scripts/python.exe scripts/resolve_pm_userids.py
.venv/Scripts/python.exe scripts/refine_pm_userids.py

# 3) 拉琅琊榜
.venv/Scripts/python.exe scripts/probe_langya_table.py
.venv/Scripts/python.exe scripts/build_langya_mapping.py
.venv/Scripts/python.exe scripts/resolve_langya_userids.py

# 4) 建表（手动用 dws CLI，参考 SKILL.md Step 3）

# 5) 写入数据
.venv/Scripts/python.exe scripts/build_and_push_records.py
.venv/Scripts/python.exe scripts/push_langya_and_fix.py

# 6) 钉钉前端隐藏 大区工程总/省份工程总 列
```
