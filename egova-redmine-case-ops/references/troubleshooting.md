# 排错手册

## 一、连接 / 权限类

| 现象 | 原因 | 处理 |
|---|---|---|
| `HTTP 403` + Body 有"请求存在威胁"之类 | Redmine 前置 WAF 拦了 Python 默认 UA | 本 skill 脚本已内置浏览器 UA；自己写请求时加 `User-Agent: Mozilla/5.0 ...` |
| `HTTP 401`，而且接口像没收到 key | 密钥没加载 | 先 `source scripts/check_env.sh`；子进程/后台跑要显式传 `env REDMINE_API_KEY="..."` |
| `HTTP 000` / 连接超时 | 网络不通 | 确认在公司内网或已连 VPN |
| `❌ REDMINE_API_KEY 未设置` | 没配置或没加载 | 见 SKILL.md 第二节，`cp scripts/.env.example scripts/.env.local` 填 key |
| 查人名查不到 | 离职账号被锁定（status=3），常规搜索不返回 | `query_user.sh` 会自动回落查锁定账号；实在查不到就用拼音/login 试 |
| `query_user.sh` 返回空且无提示 | 需要管理员权限才能列锁定账号 | 找管理员要 user_id，或从案件页面 URL / 日志里找 |

## 二、422 类（最常见的"拦路虎"）

### 1. `XXX 不是合法日期` —— 历史脏数据，不是你的错

- **表现**：只改了督办/指派人，报错字段却不在你提交的清单里（如"需求审核日期 不是合法日期"）
- **根因**：Redmine 保存时校验**案件里已存在的所有 date 类型字段**。某些自动化流程把 `2026-09-07 09:56:52`
  这种带时间的值写进了 `date` 字段，于是任何保存都会被卡住
- **处理（标准动作）**：去掉时间、只留日期，再跑一次 →
  给命令加 `--fix-dirty-dates`，脚本会随本次更新一并把这些字段规范化成 `YYYY-MM-DD`
- **注意**：一个案件上可能有多个脏 date 字段，脚本一次全修；`datetime` 字段带时间是合法的，不会误伤
- 平台会自动在预览阶段提前告警（列出案件 + 字段 + 脏值 + 修复值）

```bash
python3 scripts/duban_adjust.py --input cases.txt --dry-run   # 先看告警
python3 scripts/duban_adjust.py --input cases.txt --yes --fix-dirty-dates
```

### 2. `实际研发处理人 不能为空字符`

- **触发**：任何修改 cf / `due_date` 的 PUT，只要 `custom_field_120` 是空字符串就会触发（不限状态）
- **处理**：CSV 补 `custom_field_120=<当前研发处理人 user_id>`；用 `query_user.sh` 查 ID
- **不要猜**：指派人 ≠ 实际研发处理人，拿不准就问用户

### 3. `基础平台联动（开发）不能为空字符` / `功能形态不能为空字符`

- **触发**：已解决→已关闭时这两个字段为空
- **处理**：补 `custom_field_219=不相关`、`custom_field_220=不相关-其他`
  （功能形态写笼统的"不相关"会报"不包含于列表中"）

### 4. 改了指派人但指派人没变

- **原因**：状态机联动校验
- **处理**：通常接口返回 200 其实已成功，看返回 body；实在没变就单独重跑一次

### 5. 通用原则

遇到 422 **不要**为了让命令跑通而注释校验、加绕过标记、或擅自填别的字段。
把「报错字段 + 候选值」报给用户确认，再补列重跑。失败的行会写到 `<csv>.failed.csv`，修好直接重跑那个文件。

## 三、CSV 类

| 现象 | 原因 | 处理 |
|---|---|---|
| 某列的值跑到别的字段去了，脚本还不报错 | 列数对不上 / `opinion` 里带了英文逗号或 `#clear` | 用 `python3 -c "import csv;[print(r) for r in csv.reader(open('cases.csv'))]"` 打印核对；`#clear` 只放字段列 |
| 字段列不生效 | 列头大小写写错 | 必须是 `custom_field_<id>` 全小写 |
| Excel 打开乱码 | 编码 | CSV 用 UTF-8 with BOM（脚本生成的默认带 BOM） |

## 四、预览 / 执行类

| 现象 | 原因 | 处理 |
|---|---|---|
| dry-run 很慢或超时 | 会逐条联网查当前值 | 加 `--skip-fetch` 离线预览（但不做脏日期体检） |
| 预览没提交却以为提交了 | 忘了去掉 `--dry-run` | 看输出末尾「🔍 dry-run 模式，未提交」 |
| 执行时被问 y/N | 正常的安全确认 | 确认后输入 `y`；批量确认过可用 `--yes` |
| 子进程报 `REDMINE_API_KEY 未设置` | env 没继承 | `env REDMINE_API_KEY="..." python3 ...` |
| 想换身份执行 | — | 改 `scripts/.env.local` 里的 key，重跑 `check_env.sh` |
