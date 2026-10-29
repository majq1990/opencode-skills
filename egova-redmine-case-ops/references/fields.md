# 字段字典

## 标准字段（CSV 里直接写字段名）

| 字段 | 含义 | 取值 |
|---|---|---|
| `status_id` | 状态 | 1=工程新建 / 2=开发中 / 3=已解决 / 5=已关闭 / 17=研发分派 / 18=产品验证（测试中） / 25=研发验证 |
| `assigned_to_id` | 指派人 | user_id（转派用） |
| `due_date` | 计划完成日期 | `YYYY-MM-DD` |
| `start_date` | 开始日期 | `YYYY-MM-DD` |
| `priority_id` | 优先级 | 优先级 ID |
| `fixed_version_id` | 目标版本 | 版本 ID |
| `tester_id` | 测试人员 | user_id |
| `estimated_hours` | 预估工时 / 研发预估积分 | 已验证可用值 `0` |
| `project_id` / `tracker_id` / `module_id` / `parent_issue_id` | 项目 / 跟踪 / 模块 / 父任务 | ID |

## 督办字段（本 skill 的主角）

| cf id | 含义 | 类型 | 取值 |
|---|---|---|---|
| `custom_field_334` | 督办排期日期 | date | `YYYY-MM-DD` |
| `custom_field_335` | 督办完成日期 | date | `YYYY-MM-DD`；取消督办时用 `#clear` 清空 |
| `custom_field_346` | 督办状态变更 | 枚举 | `督办延期` / `无` / `取消督办` |

联动规则：**督办延期** → cf346 必为 `督办延期`，且 cf335 必给新日期；
**取消督办** → cf335 清空（`#clear`）+ cf346 为 `取消督办`。`scripts/duban_adjust.py` 已内置，无需手填。

## 容易踩 422 的联动字段

| cf id | 名称 | 什么时候报 | 建议值 |
|---|---|---|---|
| `custom_field_120` | 实际研发处理人 | 案件保存时若该字段是空字符串 → `实际研发处理人 不能为空字符`（改任何 cf 或 `due_date` 都可能触发） | 当前研发处理人的 user_id |
| `custom_field_219` | 基础平台联动（开发） | 已解决→已关闭、且该字段为空 → `不能为空字符` | `不相关` |
| `custom_field_220` | 功能形态 | 同上 | `不相关-其他`（写笼统的 `不相关` 会报"不包含于列表中"） |

## 其它常用自定义字段

| cf id | 含义 | 备注 |
|---|---|---|
| `custom_field_10` | 产品 | 文本 |
| `custom_field_2` | 测试人员 | user_id |
| `custom_field_19` | 模块 | |
| `custom_field_149` | 研发截止日期 | **datetime**，带时间合法 |
| `custom_field_150` | 测试截止日期 | **datetime**，带时间合法 |
| `custom_field_352` / `353` / `354` | 需求审核 / 产品设计 / 产品验证日期 | **date**，带时间即脏值（见 troubleshooting） |
| `custom_field_255` | 产品审核截止日期 | **string**，带时间只是文本，不会 422 |

## date / datetime / string 判别（决定要不要修脏值）

用 `GET /custom_fields.json` 看 `field_format`：

```bash
curl -s -H "X-Redmine-API-Key: $REDMINE_API_KEY" \
  "${REDMINE_BASE_URL}/custom_fields.json" \
| jq -r '.custom_fields[] | "\(.id)\t\(.name)\t\(.field_format)"'
```

- `date` 带时间 → **会 422，要修**（`--fix-dirty-dates` 只动这类）
- `datetime` 带时间 → 合法，**不要修**
- `string` 带时间 → 只是文本，不会 422

## CSV 里的特殊写法

| 写法 | 含义 |
|---|---|
| 空单元格 | 该字段**不修改** |
| `#clear` | 显式**清空**该字段（如取消督办清空 cf335） |

⚠️ `#clear` 只能放在要清空的字段列里，不要写进 `opinion` 列——里含英文逗号会导致**整行列错位**，且不报错。
`opinion` 是必填列（Redmine 评论不能为空）。

## 完整字段清单

`scripts/issue_case_forward.example.yml` 的 `base_fields` 段列出了实例上可提交的字段与 ID 对应关系。
