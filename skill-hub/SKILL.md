---
name: skill-hub
description: 公司 skill 服务器（skills-manager 企业源）总入口：按需求检索团队 skill 池、下载装载执行、引导安装。Use when 用户想找 skill、"有没有能做 X 的 skill"、不确定有没有现成 skill、想装/启用服务器上的某个 skill、想看公司 skill 库有什么。用户已明确点名本机已安装的 skill 时不经过本 skill；公网 skills.sh 生态找 skill 走 find-skills；向服务器发布/上传 skill 走 skill-publisher。触发词：找skill、找个skill、有没有skill、skill库、技能库、装个skill、企业源、公司skill。
metadata:
  version: 1.0.2
  author: majianquan
  category: global
  visibility: global
---

# skill-hub：公司 skill 库总入口

## 概述

本 skill 是团队 skill 服务器（skills-manager 企业源，即 `/egova/skill/`）的**只读总入口**。当用户描述一个需求而不知道该用哪个 skill 时，由本 skill 完成四件事：

1. **检索**：把用户意图转成关键词，查询服务器 skill 池
2. **推荐**：展示候选（名称/版本/可见范围/一句话说明），让用户确认或自主选择
3. **装载**：下载选中的 skill——临时装载当次即用，或装入本机 skills 目录持久生效
4. **兜底**：库里没有时，指引发布（skill-publisher）或直接人工实现

执行全部通过 `scripts/skill_server.py`（`list` / `search` / `tags` / `show` / `download` 五个子命令），不需要直接拼 API。

## 前置条件（必须先检查）

使用者本机装有 skills-manager 且**已用自己的账号登录企业服务器**。首次执行任何子命令前先跑一次轻量命令（如 `tags`）探测登录态；失败时按脚本提示引导用户打开 skills-manager 登录，**绝不代输账号密码、绝不自行调登录接口**。

## 触发示例

- "有没有能批量建 Redmine 案卷的 skill？"
- "帮我找个处理钉钉日报的工具"
- "公司 skill 库里有什么？"
- "把 build-pipeline 装到我这个环境"
- "这个需求好像得写个脚本，库里有没有现成的？"
- "我想给团队共享一个 skill，怎么发到 skill 库？"（分流到 skill-publisher）

## 边界（防止抢触发）

- 用户**已明确点名本机已装 skill**（如"用 dingtalk-doc 建个文档"）→ 直接执行，不经过本 skill
- 公网 skills.sh 生态的 skill（`npx skills`）→ 走 **find-skills**
- 发布/上传/删除服务器 skill → 走 **skill-publisher**（或 skills-manager GUI）
- 本 skill 只读：不碰服务器的上传/删除/可见性接口

## 使用原则

1. 检索先行：先 `search`，命中少再 `list`/`tags` 兜底浏览
2. 关键词构造：从需求里提"动词+对象+产品名"，中英文混排可以直接传，脚本自动逐词搜合并；不要用一长串自然语言当单个词
3. 展示候选时必须带：名称、版本、可见范围、一句话说明；多个候选并列时让用户选，不要擅自替用户定
4. 装载前确认：写操作落盘（--tool/--dest）前向用户复述目标路径；--tmp 临时装载无需确认
5. 装载后必读入口 SKILL.md 并按其执行，把关键约束（认证、确认规则）转述给用户
6. 库里没有 → 如实说没有，给出两条路：用 skill-publisher 发布新 skill，或直接人工实现
7. 不隐藏失败：登录态缺失/过期、网络不通、包损坏都要原样报告，不静默降级

## 分流逻辑

### 场景 1：按需求找 skill

1. 构造 1-3 个关键词（动词+对象+产品名），直接整句传给脚本——脚本会**逐词搜合并去重**（服务端搜索不识别空格多词，脚本已处理）：
   ```bash
   python3 "<本skill目录>/scripts/skill_server.py" search "redmine 批量创建"
   ```
2. 命中多个 → 列表格让用户选；命中 1 个 → 摘要给用户确认
3. 需要细节时 `show <name>` 看完整描述、版本史、tag
4. 0 命中 → 换同义词/英文名再搜一轮；仍无 → 场景 4

### 场景 2：浏览 skill 库

```bash
python3 "<本skill目录>/scripts/skill_server.py" tags          # 先看 tag 分布
python3 "<本skill目录>/scripts/skill_server.py" list --tag dingtalk   # 按 tag 过滤
python3 "<本skill目录>/scripts/skill_server.py" list          # 全量（当前 30+ 个）
```

### 场景 3：装载并使用

**临时装载（默认推荐，当次即用，不动用户目录）：**

```bash
python3 "<本skill目录>/scripts/skill_server.py" download <name> --tmp
```

成功后脚本输出入口路径 → **Read 该 SKILL.md → 按其内容执行**，本次会话立即可用。

**正规分发路径（推荐，优先于脚本直装）：** 本机装有 skills-manager 时，引导用户在
skills-manager「发现」页把目标 skill 导入中央库，再由应用部署到各客户端——workbuddy、
dsh、zcode、codex、opencode、autoclaw、codebuddy 等（以各人启用的工具为准），后续更新
也由应用负责。脚本直连下载只用于：本机没有 skills-manager、或只需当次临时装载。

**脚本直连装载（兜底）：**

```bash
python3 "<本skill目录>/scripts/skill_server.py" download <name> --tool zcode      # zcode / opencode / workbuddy / dsh
python3 "<本skill目录>/scripts/skill_server.py" download <name> --dest "<用户指定目录>"
```

- `--tool` 找得到该工具的 skills 目录 → 装入 `<目录>/<skill名>/`，提示"新会话起可被原生触发"
- 找不到目录 → **自动退化为临时装载并说明**，不报错不中断
- 装入 opencode 时目标即 git 仓库工作区，提示用户新文件为未跟踪状态，是否提交由用户决定

**指定版本：** 加 `--version <v>`（默认取最新 published）。

### 场景 4：库里没有

1. 明确告知"skill 库目前没有覆盖 X 的 skill"
2. 给出选项：a) 需求值得沉淀 → 用 skill-publisher 发布；b) 直接由你人工实现本次任务
3. 不硬凑相近 skill 充数

### 场景 5：发布/管理请求

- "发布/上传/更新 skill" → 转述 skill-publisher 的流程（打 zip、上传、过安全扫描）
- "删除/改可见范围" → 指引用户在 skills-manager GUI 操作，本 skill 不代办

## 脚本速查

| 命令 | 用途 |
|------|------|
| `list [--tag X] [--json]` | 全量/按 tag 列表 |
| `search <词> [--json]` | 关键词搜索 |
| `tags [--json]` | tag 清单 |
| `show <name> [--json]` | 详情+版本史 |
| `download <name> [--version v] [--tool T \| --dest P \| --tmp] [--json]` | 下载装载 |

身份说明：脚本以"本机 skills-manager 当前登录者"身份调 API，不内置账号；token 即取即用不落盘。会话细节见 [references/session-protocol.md](references/session-protocol.md)；接口细节见 [references/api-contract.md](references/api-contract.md)。

## 错误处置速查

| 现象 | 处置 |
|------|------|
| "未找到本机 skills-manager 登录数据" | 用户未装/未登录 → 引导安装并登录 skills-manager，重试 |
| "登录态已过期 / 401" | 引导打开 skills-manager 重新登录，重试 |
| "无法连接 skill 服务器" | 检查网络/VPN，稍后重试 |
| "下载内容不是合法 zip 包" | 如实报告版本与 skill 名，建议用户到 skills-manager 里核对该 skill |
| --tool 找不到目录 | 已自动临时装载；转述脚本给出的持久化建议 |

---

<!-- feedback-channel v1 -->
## 反馈渠道

本技能已纳入企业反馈监控。使用中如遇「连续多轮仍未解决同一类问题」、「工具执行报错」，或你想主动反馈：

- 在装有 feedback-monitor 插件的 agent（opencode / Claude Code / 腾讯 WorkBuddy）中，会自动采集并（脱敏后）上报到企业反馈平台；
- 也可随时在 **skills-manager 应用 →「反馈 / 建议」** 手动提交，会自动记录关联技能与提交人。
