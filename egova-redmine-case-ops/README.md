# Redmine 案件批量操作 skill（督办调整 / 转派）

一个自包含的 skill 包：让 AI agent（或你自己敲命令）批量处理公司 Redmine 上的案件——
**调整督办信息**、**把某人名下案件转派给他人**。

详细用法看 `SKILL.md`（agent 会自动读它）。

## 安装

把整个 `egova-redmine-case-ops/` 目录放到你的 agent skills 目录下即可，任选：

```bash
# 通用（Codex / Gemini / 其它）
cp -r egova-redmine-case-ops ~/.agents/skills/

# Claude Code
cp -r egova-redmine-case-ops ~/.claude/skills/

# pi
cp -r egova-redmine-case-ops ~/.pi/agent/skills/
```

不需要安装任何 Python 包即可使用基础功能。

## 配置（只需一次）

```bash
cd <skill 目录>
cp scripts/.env.example scripts/.env.local
vi scripts/.env.local        # 把 REDMINE_API_KEY 换成你自己的密钥

source scripts/check_env.sh  # 看到 ✅ 环境就绪 即配置成功
```

API Key 获取：登录 Redmine → 右上角「个人账户」→「API 访问密钥」→ 显示/生成。

> ⚠️ `.env.local` 是你个人的私密文件，不要提交 git、不要发给别人。
> 用谁的 Key 跑，Redmine 里的操作记录就记在谁名下。

## 依赖

| 依赖 | 用途 | 是否必需 |
|---|---|---|
| `python3`（3.10+） | 所有脚本 | 必需 |
| `curl`、`jq` | 环境自检、查用户 | 必需 |
| `openpyxl` | 只有 xlsx 输入需要（`uv run --with openpyxl python3 ...`） | 可选 |

## 两个常用例子

```bash
source scripts/check_env.sh

# 1) 督办延期 / 取消督办（备注自动拼成「原备注 + 操作说明」）
python3 scripts/duban_adjust.py \
  --case "526984, 2026-10-15, 督办延期, 改造范围较多" \
  --case "526273, , 取消督办, 超期自动督办任务" \
  --dry-run          # 确认后把 --dry-run 换成 --yes

# 2) 离职人员案件批量转派（不关心案件当前状态）
bash scripts/query_user.sh --q 张三      # 查原指派人 id
bash scripts/query_user.sh --q 李四      # 查接手人 id
python3 scripts/batch_reassign.py \
  --user-id <张三 id> --to-user-id <李四 id> \
  --opinion "离职人员案件批量批转" --dry-run
```

## 遇到 422 不要慌

Redmine 保存案件时会校验案件里**已有的**日期字段。历史案件里若有 `date` 类型字段被写成了
带时间的值（如 `2026-09-07 09:56:52`），即使你只改督办、只改指派人也会 422：
`需求审核日期 不是合法日期`。

**这是正常情况**，不是你把数据改坏了。加 `--fix-dirty-dates` 重跑即可（自动去掉时间、只留日期）：

```bash
python3 scripts/duban_adjust.py --input cases.txt --yes --fix-dirty-dates
```

更多排错见 `references/troubleshooting.md`。

## 目录

```
SKILL.md                     # 给 agent 看的主文档
README.md                    # 本文件（给人看）
references/fields.md         # 字段字典
references/troubleshooting.md# 排错手册
scripts/                     # 全部可执行脚本
```

## 边界

本包**不做**研发/测试流转模板、不做批量关单、不改数据库。
所有操作遵循最小改动：只改你明确指定的字段。
