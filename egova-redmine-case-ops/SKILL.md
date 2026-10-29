---
name: egova-redmine-case-ops
description: 公司 Redmine（faq.egova.com.cn:7787）案件日常运维：① 批量调整「督办」信息（督办完成日期、督办状态变更、备注）；② 把某人名下的案件批量转派给另一个人（常用于离职交接，不关心案件当前状态）。所有操作遵循最小改动原则，只改你明确提到的字段；支持先预览再执行，遇到 422 有明确处理指引。命令前缀：duban_adjust.py / batch_reassign.py。
---

# Redmine 案件批量操作（督办调整 / 转派）

## 一、这个 skill 干什么

只有两件正事，都走 Redmine REST API：

| 能力 | 一句话描述 | 入口 |
|---|---|---|
| **督办调整** | 改案件的「督办完成日期」「督办状态变更」，并写一条合规备注 | `scripts/duban_adjust.py` |
| **批量转派** | 把 A 名下的一批案件转给 B（离职交接标准动作） | `scripts/batch_reassign.py` |

「最小改动」是本 skill 的铁律：**你只提了督办，它就只动督办字段；你只提了转派人，它就只动指派人**。
其它字段（状态、计划完成日期、优先级、各种自定义字段）原样保留，也不会触发研发/测试流转模板。

想改这两个入口之外的字段（优先级、目标版本、计划完成日期……），可以直接写 CSV 喂给底层引擎
`scripts/issue_case_batch_update.py`，见第七节。

**使用前必须做一次的事**：配置 API Key（第二节）。所有操作都会记在你的名下，
拿谁的 Key 跑，Redmine 里就显示是谁操作的。

---

## 二、首次使用：配置 API Key（只需一次）

先跑一句：

```bash
cd <本 skill 目录>
source scripts/check_env.sh
```

**✅ 成功的输出长这样**（看到这行就说明能干活了）：

```
✅ 环境就绪：登录身份 张三 技术支持部 | 地址 https://faq.egova.com.cn:7787 | 密钥来源 .../.env.local
```

**❌ 如果提示「未找到 REDMINE_API_KEY」**：脚本已经打印了配置步骤，把它原样告诉用户即可，不要继续往下做操作。简版如下：

1. 打开 Redmine 网页，登录自己的账号
2. 右上角「个人账户」→ 右侧「API 访问密钥」→「显示」（没有就点「生成」）
3. 复制密钥，执行：

   ```bash
   cp scripts/.env.example scripts/.env.local
   vi scripts/.env.local        # 把 REDMINE_API_KEY 换成自己的密钥
   ```

4. 重新 `source scripts/check_env.sh`

`.env.local` 是本机私密文件，**不要提交 git、不要发给别人**。

其它排错：

| 提示 | 含义 | 怎么办 |
|---|---|---|
| `HTTP 401` | 密钥不对/失效 | 回 Redmine 重新复制，更新 `.env.local` |
| `HTTP 403` | 被 WAF 拦截 | 确认 `REDMINE_BASE_URL=https://faq.egova.com.cn:7787`，别加路径 |
| `HTTP 000` | 连不上 | 检查网络 / VPN |
| 想换个人的身份操作 | 换 Key 即可 | 改 `.env.local` 里的 `REDMINE_API_KEY` |

环境依赖：`python3`、`curl`、`jq`。只有 xlsx 输入（第六节）额外需要 `openpyxl`。

---

## 三、能力一：调整案件督办

### 用户会怎么说（随意说，不用记格式）

> "把 526984 的督办完成日期改到 10 月 15 号，备注：改造范围较多，预留研发时间不够"
> "526273 取消督办，超期自动督办的"
> "这几条（贴一堆案件号）督办都延到 2026-10-20"

**你（agent）要提取的关键信息就 4 个**：案件号、新的督办完成日期、新的督办状态、备注（可选）。

### 怎么跑

一个命令搞定，日期支持 `2026-10-15` / `2026/10/15` / `2026.10.15` / `2026年10月15日`
（带时间如 `2026-10-15 00:00:00` 会自动截成日期）：

```bash
source scripts/check_env.sh

# 1) 先预览（不提交，会联网对比 from→to）
python3 scripts/duban_adjust.py \
  --case "526984, 2026-10-15, 督办延期, 改造范围较多，预留研发时间不够" \
  --case "526273, , 取消督办, 超期自动督办任务" \
  --dry-run

# 2) 确认无误后执行（脚本还会再问一次，输入 y 回车）
python3 scripts/duban_adjust.py \
  --case "526984, 2026-10-15, 督办延期, 改造范围较多，预留研发时间不够" \
  --case "526273, , 取消督办, 超期自动督办任务" \
  --yes
```

案件多时，写成文本文件更省事（一行一条，`#` 开头是注释）：

```
# cases.txt   ——  案件号, 新督办完成日期, 新督办状态, 备注(可选)
526984, 2026-10-15, 督办延期, 改造范围较多，预留研发时间不够
526273, ,          取消督办, 超期自动督办任务
526225, 2026-10-20, 督办延期
```

```bash
python3 scripts/duban_adjust.py --input cases.txt --dry-run
python3 scripts/duban_adjust.py --input cases.txt --yes
```

只想生成 CSV（不提交）加 `--print-only`；CSV 默认落在 `/tmp/duban-<时间戳>.csv`。

### 字段联动规则（脚本自动做，不用手填）

| 督办状态 | 督办完成日期 | 督办状态变更 | 说明 |
|---|---|---|---|
| **督办延期** | 填入新日期（必填） | `督办延期` | 两者成对出现 |
| **取消督办** | **清空** | `取消督办` | 取消后不该留完成日期 |
| **无** | 有日期则更新 | `无` | 只想改日期、不表态状态时用 |

非目标字段一律不动（`cf219`、`cf220`、`cf120`、计划完成日期等全程不碰）。

### 备注（opinion）规则：**原备注 + 操作说明**

脚本自动拼，不要手写：

| 你给的备注 | 督办状态 | 写进 Redmine 的备注 |
|---|---|---|
| 改造范围较多 | 延期到 2026-10-15 | `改造范围较多，督办延期至2026-10-15` |
| （空） | 延期到 2026-10-15 | `督办延期至2026-10-15` |
| 超期自动督办任务 | 取消督办 | `超期自动督办任务，取消督办` |
| 需求变更 | 无 | `需求变更` |

### 单个案件的小改动

只有一两条、且改动不复杂时，也可以直接调底层单案接口：

```bash
env REDMINE_API_KEY="<key>" python3 scripts/issue_case_forward.py \
  --case-id 526984 --update-only \
  --custom-field 335=2026-10-15 --custom-field 346=督办延期 \
  --opinion "改造范围较多，督办延期至2026-10-15"
```

---

## 四、能力二：批量转派

### 用户会怎么说

> "张三离职了，把他手上的案件都转给李四"
> "把 王五 的案件转给 赵六"

**只需要知道两个人是谁，不用关心案件现在是什么状态。**

### 怎么跑

```bash
source scripts/check_env.sh

# 1) 查两个人的 user_id（查不到离职人员时脚本会自动翻锁定账号）
bash scripts/query_user.sh --q 张三        # → 拿到 id / login（离职账号会自动翻出来）
bash scripts/query_user.sh --q 李四

# 2) 先预览会动哪些案件（--dry-run 只看不提交）
python3 scripts/batch_reassign.py \
  --user-id <张三 id> --user-name "张三" \
  --to-user-id <李四 id> --to-user-name "李四" \
  --opinion "离职人员案件批量批转" --dry-run

# 3) 确认后执行（不加 --yes 会在提交前再问一次）
python3 scripts/batch_reassign.py \
  --user-id <张三 id> --user-name "张三" \
  --to-user-id <李四 id> --to-user-name "李四" \
  --opinion "离职人员案件批量批转" --yes
```

只想看不动手（纯查询，先把清单打印出来人工确认）：

```bash
curl -s -G --data-urlencode "assigned_to_id=8842" \
  --data-urlencode "status_id=open" --data-urlencode "limit=100" \
  "https://faq.egova.com.cn:7787/issues.json" \
  -H "X-Redmine-API-Key: ${REDMINE_API_KEY}" \
  -H "User-Agent: Mozilla/5.0" | jq -r '.issues[] | "#\(.id) [\(.status.name)] \(.subject)"'
```

### 行为说明（避免误解）

- **不关注状态**：默认只排除「已关闭」(status_id=5)。**「已解决」也一并转派**——
  离职人员名下绝大多数就是已解决收尾态，不转的话接手人看不到这些历史。
- **只改指派人**：案件状态保持原样，不触发任何流转模板，不自动补"实际研发处理人"等字段。
- 想保留某些状态不转：`--exclude-status 3`（保留已解决）、`--exclude-status "1,17"`（保留工程新建/研发分派）。
- 每条案件会写一条统一备注（上面的 `--opinion`）。

### 转派后回查

```bash
bash scripts/query_user.sh --q 张三        # 确认人没问题
# 然后重跑上面的 curl 查询，total_count 为 0 就是清空了
```

---

## 五、遇到 422 怎么办（这是正常情况，不要怕）

Redmine 保存案件时会**校验案件里已经存着的所有日期字段**。有些历史案件里，
「需求审核日期」「产品验证日期」这类 `date` 类型字段被写成了带时间的值（例如 `2026-09-07 09:56:52`）。
这种情况下即使你只改督办、只改指派人，Redmine 也会返回：

```
422 {"errors":["需求审核日期 不是合法日期"]}
```

**这不是你操作错了，也不是数据被改坏了**——是历史脏数据挡住了保存。处理方式：
把时间部分去掉、只留日期，然后再跑一次。

推荐做法：**加 `--fix-dirty-dates` 重跑**（脚本会自动把 `2026-09-07 09:56:52` 规范化成 `2026-09-07`，
随本次更新一并提交，不改日期本身的值）：

```bash
# 督办
python3 scripts/duban_adjust.py --input cases.txt --dry-run --fix-dirty-dates
python3 scripts/duban_adjust.py --input cases.txt --yes --fix-dirty-dates

# 其它表格批量
python3 scripts/issue_case_batch_update.py --input cases.csv --update-only --yes --fix-dirty-dates
```

不带这个参数时，预览阶段脚本就会**提前告警**（哪条案件、哪个字段、脏值是什么、应该改成什么），
照着提示加参数重跑即可。`datetime` 类型字段带时间是合法的，脚本不会误伤。

**其它 422 的处置原则**：脚本不会为了让命令跑通而偷偷改别的字段。
遇到字段联动类 422（例如「实际研发处理人不能为空」），把报错字段 + 建议值报给用户确认，
再用 CSV 补上那一列（`custom_field_120=<研发 ID>`），不要自行猜测填值。

---

## 六、输入来自 Excel（可选的便捷通道）

督办需求常常是 PM/领导给的一份 xlsx。直接转成 CSV，备注会自动按「原备注 + 操作说明」拼好：

```bash
# --minimal：只改督办完成日期 + 督办状态变更（推荐，改动面最小）
uv run --with openpyxl python3 scripts/issue_case_xlsx_to_csv.py \
  --input "督办遗留任务.xlsx" --output duban.csv --minimal

python3 scripts/duban_adjust.py --input duban.csv --dry-run   # 或直接用底层引擎
```

不加 `--minimal` 时，表格里的「督办排期日期」「计划完成日期」两列也会一并写回（保持原表行为）。
列名不一致可以用 `--column-case-id` / `--column-opinion` / `--column-new-duban` 等参数映射；
表格里「调整完成日期」列若写的是"取消督办"字样，脚本会自动识别成取消场景。
详见 `scripts/issue_case_xlsx_to_csv.py --help`。

---

## 七、进阶：改其它字段（写 CSV）

只有需要改督办/指派人以外的字段时，才用底层引擎。CSV 列头 = 字段名，空单元格 = 不改，
`#clear` = 显式清空：

```csv
case_id,opinion,priority_id,due_date,custom_field_335
526984,优先级提到高，2026-10-20,2,2026-10-20,2026-10-20
```

```bash
python3 scripts/issue_case_batch_update.py --input cases.csv --update-only --dry-run
python3 scripts/issue_case_batch_update.py --input cases.csv --update-only --yes
# 失败的行会写到 cases.failed.csv，修好后直接重跑
```

字段 ID 对照见 `references/fields.md`；参数与陷阱见 `issue_case_batch_update.py --help`。

---

## 八、命令速查

| 目的 | 命令 |
|---|---|
| 环境自检 / 看当前身份 | `source scripts/check_env.sh` |
| 查人（含离职） | `bash scripts/query_user.sh --q 姓名` |
| 查某人名下案件 | `curl -G .../issues.json --data-urlencode assigned_to_id=<id>` |
| 督办调整 | `python3 scripts/duban_adjust.py --input cases.txt --dry-run` → `--yes` |
| 批量转派 | `python3 scripts/batch_reassign.py --user-id A --to-user-id B --opinion "..." --dry-run` → `--yes` |
| xlsx 转 CSV | `uv run --with openpyxl python3 scripts/issue_case_xlsx_to_csv.py --input x.xlsx --output cases.csv --minimal` |
| 任意字段批量改 | `python3 scripts/issue_case_batch_update.py --input cases.csv --update-only --dry-run` → `--yes` |
| 脏日期修复 | 上面任意命令末尾加 `--fix-dirty-dates` |

统一原则：**先 `--dry-run` 看清 from→to，再执行**；执行前脚本还会再要一次确认（`--yes` 可跳过）。

---

## 九、目录结构

```
egova-redmine-case-ops/
├── SKILL.md                     # 本文档
├── README.md                    # 分发/安装说明
├── references/
│   ├── fields.md                # 字段字典（状态码、督办字段、422 联动字段）
│   └── troubleshooting.md       # 排错表（WAF/401/422/日期脏值/超时）
└── scripts/
    ├── check_env.sh                 # 环境自检 + 首次配置指引
    ├── .env.example                 # 密钥模板 → 复制成 .env.local
    ├── duban_adjust.py              # 【入口】督办调整
    ├── batch_reassign.py            # 【入口】批量转派
    ├── issue_case_batch_update.py   # 底层：表格驱动批量改字段
    ├── issue_case_xlsx_to_csv.py    # 底层：xlsx → CSV
    ├── issue_case_forward.py        # 底层：单案字段修改 / HTTP 提交
    ├── issue_case_forward.example.yml
    └── query_user.sh                # 查 user_id（支持离职账号）
```

## 十、边界（本 skill 不做的事）

- 不做研发/测试**流转**（需求分析、研发分派、产品验证、关闭流转等模板操作）——那属于别的工具链
- 不做案件**批量关单**（把「已解决」改为「已关闭」）——如需要，用 CSV 写 `status_id=5`
- 不改数据库、不删案件、不动历史记录
- 不替你决定"该转给谁"、"该延期到几号"——只执行你确认过的事实
