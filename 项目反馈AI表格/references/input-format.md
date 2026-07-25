# 输入与中间 JSON

`projects_enriched.json` 是 `scripts/create_aitable.py` 的输入之一。结构：

```json
[
  {
    "project_no": "可空",
    "project_name": "项目名称",
    "project_region_group": "华北二区",
    "project_area": "北京区域",
    "project_manager_userids": ["16827827927173713"],
    "sales_manager_userids": [],
    "province_lead_userids": [],
    "region_lead_userids": [],
    "district_lead_userids": [],
    "visibility_userids": ["16827827927173713"],
    "match_note": "项目名称精确匹配"
  }
]
```

字段说明：
- `project_manager_userids`：项目经理
- `sales_manager_userids`：项目销售经理
- `province_lead_userids`：省份总
- `region_lead_userids`：大区总
- `district_lead_userids`：片区总
- `visibility_userids`：用于“可见人员”字段；为空时脚本会从项目经理、省份总、大区总、片区总自动合并

成员字段写入钉钉 AI 表格格式：

```json
[{"userId": "钉钉userId"}]
```
