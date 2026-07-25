# dws aitable CLI 速查 + 已知坑

## 命令链

```
dws aitable base    create / update / delete / get / list / search / copy
dws aitable table   create / update / delete / get
dws aitable field   create / update / delete / get
dws aitable record  create / update / delete / query
dws aitable view    create / update / delete / get
```

加 `-y` 跳过确认；加 `-v` 看 verbose；用 `--dry-run` 预览（**注意**：dry-run 输出有时是空 `{}`，不一定能验证 payload 格式）。

## 字段类型对照

| 用途 | dws CLI type | 备注 |
|---|---|---|
| 单行文本 | `text` | 大多数情况 |
| 主键文档 | `primaryDoc` | 默认表自带的"标题"是 primaryDoc，不能改 type，但可以 rename |
| 单选 | `singleSelect` | options 创建时不生效，必须 update 补 |
| 多选 | `multiSelect` | 同上 |
| 数字 | `number` | |
| 日期 | `date` | `config: {dateFormat, includeTime}` |
| 钉钉成员 | `user` | **不是 `member`**！member/memberMulti/人员 全部失败 |
| 附件 | `attachment` | |

## 创建字段时的关键坑

### 坑 1：`field create --fields` **不会** 写入单选 options

```bash
# 这样写 options 会被忽略：
dws aitable field create --fields '[{"fieldName":"大区","type":"singleSelect","property":{"options":[{"name":"华北一区"}]}}]'
# 字段建出来了，但 options 是空的
```

**正确做法：先 create 空字段，再 update 补 options**：

```bash
dws aitable field create --base-id $B --table-id $T -y --fields '[{"fieldName":"大区","type":"singleSelect"}]'
# 拿 fieldId
dws aitable field get --base-id $B --table-id $T
# update 补
dws aitable field update --base-id $B --table-id $T --field-id $F -y \
  --config '{"options":[{"name":"华北一区"},{"name":"华北二区"}]}'
```

### 坑 2：record 字段名是 `cells` 不是 `fields`

```jsonc
// ❌ 错（会报 INVALID_CELLS）
{"records": [{"fields": {"01ZM8y7": "项目A"}}]}

// ✅ 对
{"records": [{"cells": {"01ZM8y7": "项目A"}}]}
```

### 坑 3：user 字段值的格式

```jsonc
// ❌ 错（user field items must be objects）
"4dCZcZ5": ["045827440538654698"]

// ✅ 对
"4dCZcZ5": [{"userId": "045827440538654698"}]
```

### 坑 4：单选/日期等字段返回的 cell 是 dict

```jsonc
// query 回来的 record.cells 长这样：
{
  "01ZM8y7": "项目名"                                  // primaryDoc → 直接 str
  "iRWA4SK": {"id": "t9OfSPpvDh", "name": "华北一区"}   // singleSelect → dict
  "diu5pTA": {"id": "7QqIyHTloU", "name": "未反馈"}     // 同上
  "4dCZcZ5": [{"corpId": "ding...", "userId": "xxx"}]  // user → list of dict
  "YQWBWFh": "2026-05-06"                              // date → str
  "81LkWjk": "山东区域"                                 // text → str
}
```

读取时单选要 `cell.get("name")`，user 要遍历 `[u["userId"] for u in cell]`。

### 坑 5：默认 base create 自带一个表

```bash
dws aitable base create --name "xxx"
# 返回 baseId，但 base 里默认有一张表 "数据表"，主字段名"标题"(primaryDoc)
# 推荐做法：rename 这张表 + rename 主字段为业务名（如"项目"），不要新建
```

### 坑 6：`view update --config custom.hiddenFields` 不生效

`dws aitable view update --config '{"custom":{"hiddenFields":{...}}}'` 接口返回 status=success 但 hiddenFields 没真改。**字段隐藏目前必须在钉钉前端手动操作**。

## 命令行长度限制（Windows）

Windows cmd 单参数 ~32K 限制，记录创建分批：

| 字段数/记录 | 推荐批次大小 |
|---|---|
| 简单（5-7 字段，含 1 个 user） | 20 条/批 |
| 复杂（10+ 字段，多 user） | 10 条/批 |

## subprocess 调用约定（Windows）

```python
# ❌ 错：[WinError 2] 系统找不到指定的文件
subprocess.run(["dws", "contact", "user", "search", "--query", "马健权"], ...)

# ✅ 对：dws.cmd 显式指定
subprocess.run(["dws.cmd", "contact", "user", "search", "--query", "马健权"],
               capture_output=True, timeout=20, shell=False)

# ✅ 对：bytes 读出再容错解码（避免 GBK 异常）
out = (r.stdout or b"").decode("utf-8", errors="replace")
err = (r.stderr or b"").decode("utf-8", errors="replace")
```

stdout 装饰：

```python
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
```

否则 print 中文会触发 `UnicodeEncodeError: 'gbk' codec can't encode...`。

## record query 翻页

`record query --limit` 范围 1~100。翻页用 `--cursor`：

```python
all_recs, cursor = [], ""
while True:
    args = ["aitable","record","query","--base-id",B,"--table-id",T,"--limit","100","-y"]
    if cursor: args += ["--cursor", cursor]
    d = call_dws(args)
    recs = (d.get("data") or {}).get("records") or []
    all_recs.extend(recs)
    cursor = (d.get("data") or {}).get("nextCursor") or ""
    if not cursor: break
```

## 一些命令的实际 flag 命名差异

| 通用术语 | dws contact user 的 flag |
|---|---|
| user-id | `--ids`（**不是 `--user-id`**） |
| query / keyword | `--query` |
| mobile | `--mobile` |

## 钉钉成员搜索/查询路径

```bash
# 按姓名搜
dws contact user search --query "马健权" -y
# 返回 result[].name/userId/title/openDingTalkId

# 按 userId 拿详情（含部门）
dws contact user get --ids 045827440538654698,16984255030023919 -y
# 返回 result[].orgEmployeeModel.depts[].deptName

# 按手机号
dws contact user search-mobile --mobile 15928716057 -y
```

## 钉钉 AI 表格访问 URL

- AI 表格首页：`https://docs.dingtalk.com/i/nodes/{baseId}`
- 数据表：`https://docs.dingtalk.com/i/nodes/{baseId}?iframeQuery=sheetId%3D{tableId}`
- 仪表盘：`https://docs.dingtalk.com/i/nodes/{baseId}?iframeQuery=applicationId%3D{dashboardId}`

(URL 规则来自 dws aitable base get 返回的 `summary` 段)
