---
name: vuln-response
description: 漏洞响应一条龙。用户给一个 CVE 编号 + 漏洞类型（os 或 software），自动产出钉钉「安全漏洞台账」AI 表格批量记录 + 钉钉处置文档（按统一模板）。当前 v0.1 完整支持「操作系统漏洞」分支；「软件漏洞」分支字段映射 + 依赖软件清单已就绪，fetch/render 流程 v0.2 阶段实施。触发词：CVE 处置 / 漏洞响应 / 安全漏洞台账 / OS 漏洞 / 内核漏洞 / 软件漏洞 / 三方依赖 / vuln-response。
---

# 漏洞响应工作流

> **vuln_type 路由**：用户每次必须明确传 `os` 还是 `software`：
>
> - `os`：操作系统/内核漏洞（v0.1 已实装），写「操作系统漏洞」表 + 钉钉云文档
> - `software`：三方依赖软件漏洞（v0.2 规划中），写「软件漏洞」表，软件白名单见 `references/software_inventory.md`

## 输入

| 字段 | 必填 | 说明 |
|---|---|---|
| `CVE_ID` | ✓ | 例如 `CVE-2026-31431`；软件漏洞场景下也接受同时给多个 CVE（一条记录可合并多 CVE，详见 `references/software_aitable_schema.md`） |
| `VULN_TYPE` | ✓ | `os` 或 `software`，二选一 |
| `SOFTWARE` | software 必填 | 软件标识（如 `redis` / `mysql` / `dameng`），值必须在 `references/software_inventory.md` 白名单内；不在的话先回填白名单 |
| `DOC_NODE_ID` | os 可选 | 已有钉钉云文档 nodeId；软件漏洞当前不生成云文档 |
| `BASE_ID`/`TABLE_ID` | 自动 | os→`f3dzlj97k3121hq4adg10`、software→`oz3kcid3c79qy2lqspsn3`，base 共用 `qnYMoO1rWxDl1N54sz3zaKemW47Z3je9` |

## 三步工作流（必须分步执行，不要一把梭）

### Step 1: scan — 抓厂商公告

调用 `scripts/fetch_vendor_advisory.py <CVE_ID>`，输出 `D:\opencode\_archive\<CVE>_scan_<ts>.json`，结构见 `references/vendor_endpoints.md`。

**铁律：**
- 不依赖搜索引擎缓存或模型记忆，必须命中厂商真实接口（见 `references/vendor_endpoints.md`）
- 国产 SPA 优先内部 JSON API，失败再降级 scrapling skill 的 PlayWrightFetcher
- 抓取结果同时保留原始响应（`_raw`）和归一化字段，便于后续审计

### Step 2: propose — 生成草稿

并行调两个脚本：

- `scripts/build_doc_md.py <scan.json>` → 产出 markdown 草稿到 `_archive\<CVE>_doc_<ts>.md`
- `scripts/build_aitable_rows.py <scan.json>` → 产出批量 records JSON 到 `_archive\<CVE>_rows_<ts>.json`

**生成完后必须把两个文件的路径报给用户审稿**，不要直接进入 Step 3。

### Step 3: publish — 写入钉钉

只有用户明确确认（"确认发布" / "干"等）后才执行：

```bash
python scripts/publish.py \
  --doc-md   <archive>/<CVE>_doc_<ts>.md \
  --rows-json <archive>/<CVE>_rows_<ts>.json \
  [--doc-node-id <existing>] \
  [--doc-name "标题"] \
  [--dry-run]
```

`publish.py` 跨 Windows / Linux，自动探测 `dws` 或 `dws.cmd`，自动执行：
1. CRLF → LF normalize（`feedback_dws_markdown_writes.md` 规则 1）
2. 占位符残留扫描 —— 还有 `{{...}}` 直接拒绝写入
3. 若 `--doc-node-id` 已存在：`dws doc read` 备份原稿到 `<archive>/<nodeId>_before_<ts>.md/.json`
4. `dws doc update --mode overwrite`（无 nodeId 走 `dws doc create`，需要 `--doc-name`）
5. `dws aitable record create` 批量插入 rows
6. `--dry-run` 模式只打印将执行的命令和样例 row，不调用任何写接口

## 操作系统漏洞处理铁律

> 这些规则刻进脚本和模板，违反就是 bug。

1. **三级数字编号**：`1.` / `1.1` / `2.1.1`，不准用 `一、二、三`
2. **2.1.4 社区检测工具节**：只给 GitHub + jsDelivr + ghproxy 下载链接和附件提示，**绝不嵌入多行 shell**（钉钉 markdown 通道会污染 fence、`${var}`、`AF_ALG` 这类元字符）
3. **不写"反思及下一步工作"**：OS 漏洞模板省略这章
4. **处置建议三段式**：AI 表格"处置建议"列固定 `[修复] cmd | [验证] cmd | [公告] URL`
5. **写入前必备份**：`_archive\<doc>_before_<ts>.md/.json`
6. **生产 nodeId 禁试探**：要试 here-string / API 用 `--dry-run` 或临时 nodeId

## 资产路径

**OS 分支（v0.1 实装）：**
- 文档模板：`references/os_cve_template.md`
- 厂商接口表：`references/vendor_endpoints.md`
- AI 表格字段映射：`references/aitable_schema.md`
- 抓取脚本：`scripts/fetch_vendor_advisory.py`
- 渲染脚本：`scripts/build_doc_md.py` + `scripts/build_aitable_rows.py`

**软件分支（v0.2 实装）：**
- 文档模板：`references/software_template.md`
- AI 表格字段映射：`references/software_aitable_schema.md`
- 依赖软件清单：`references/software_inventory.md`（18 软件：8 数据库 / 4 中间件 / 3 服务发现 / 1 MQ / 1 JDK / 1 底层加密库）
- 抓取接口：`references/software_endpoints.md`（NVD CVE 2.0 + GHSA + CNVD）
- 抓取脚本：`scripts/fetch_software_advisory.py`
- 渲染脚本：`scripts/build_software_doc_md.py` + `scripts/build_software_aitable_rows.py`
- 发布脚本：复用 `scripts/publish.py`（按 `_meta.mode` 自动路由 OS/software 流程）

## 软件漏洞分支工作流（v0.2 已实装）

**输入**：软件标识（如 `redis`）+ 一个或多个 CVE 编号

### Step 1: scan — 抓 NVD/GHSA 元数据

```bash
python scripts/fetch_software_advisory.py CVE-2025-15467 [CVE-... ...] \
  --software openssl --sources nvd,ghsa[,cnvd]
```

输出 `<archive>/sw-<software>-<ts>_scan.json`，每个 CVE 一个 `vendor_lookups[]` 数组，覆盖 NVD/GHSA/CNVD（CNVD 当前是 needs_render 占位，国产软件需 scrapling 兜底）。

### Step 2: propose — 写 plan.json + 渲染

`plan.json` 是研判结论，由 LLM 或人写，结构见 `references/software_template.md` 的占位符（doc_title / software_display_name / affected_versions / fixed_versions / vuln_summary / version_check_cmd / online_upgrade_cmd / verify_cmd / mitigation_body / offline_patch_rows / cve_overrides 等）。

```bash
python scripts/build_software_doc_md.py       <scan.json> <plan.json>
python scripts/build_software_aitable_rows.py <scan.json> <plan.json>
```

产物：`<archive>/sw-<software>-<ts>_doc.md` + `<archive>/sw-<software>-<ts>_rows.json`。

`rows.json` 用 sentinel 占位：

- `__AUTO_INCREMENT__`：发布时 query 表当前 max(序号)+1
- `__DOC_URL__`：发布时用刚 publish 的 nodeId 拼 `https://alidocs.dingtalk.com/i/nodes/{nodeId}`

### Step 3: publish — 写钉钉

```bash
python scripts/publish.py \
  --doc-md   <archive>/sw-<software>-<ts>_doc.md \
  --rows-json <archive>/sw-<software>-<ts>_rows.json \
  --doc-name "EGOVA-关于 ... CVE-XXX-YYYY 修复说明" \
  [--dry-run]
```

publish.py 自动识别 `_meta.mode=="software"`，按 software 流程：

1. doc create / update 拿到 nodeId
2. query 表当前 max(序号) 计算下一个序号
3. 替换 records 里的 sentinel
4. record create

### 软件分支铁律

1. **录入粒度**：软件 × 多 CVE 合并 = 一行（多 CVE 在「漏洞项」字段用 `\n` 分隔）
2. **必出处置文档**：无论 CVE 复杂度，都生成钉钉云文档作为「说明&解决方案」字段的 URL
3. **5 个空字段保持留空**：涉及产品 / 反馈时间 / 字段8 / 字段9 / 字段8图片 — 暂不启用
4. **任务号字段留空**：暂不关联 Redmine
5. **软件标识必须在白名单内**：见 `references/software_inventory.md`，遇到清单外的软件先回填白名单再处置

## 运行环境

跨平台。脚本只依赖：

- Python ≥ 3.6（demo.egova.com.cn 是 3.6.8；标准库 `urllib`、`json`、`pathlib`、`subprocess`、`typing`）
- `dws` CLI 在 PATH 里（Windows 是 `dws.cmd`，Linux 是 `dws`，`publish.py` 自动 `shutil.which` 探测）

## 归档目录

中间产物（`*_scan_*.json` / `*_doc_*.md` / `*_rows_*.json` / `*_before_*.md`）默认归档位置：

| 平台 | 默认路径 |
|---|---|
| Windows | `D:\opencode\_archive\` |
| Linux / macOS | `~/.local/share/vuln-response/archive/` |

**任意平台都可用环境变量 `VULN_RESPONSE_ARCHIVE_DIR` 覆盖**：

```bash
export VULN_RESPONSE_ARCHIVE_DIR=/var/lib/vuln-response/archive
```

## 部署到 demo.egova.com.cn

整个 skill 自包含，不依赖 Windows-only 工具。把目录整个 scp 过去就能跑：

```bash
# 在本机
scp -r D:/opencode/config/skills/vuln-response root@demo.egova.com.cn:/opt/

# 在服务器
ssh root@demo.egova.com.cn
cd /opt/vuln-response
export VULN_RESPONSE_ARCHIVE_DIR=/var/lib/vuln-response/archive
mkdir -p $VULN_RESPONSE_ARCHIVE_DIR

# Step 1
python3 scripts/fetch_vendor_advisory.py CVE-2026-31431
# Step 2（plan.json 由 LLM 或人写好）
python3 scripts/build_doc_md.py       $VULN_RESPONSE_ARCHIVE_DIR/CVE-2026-31431_scan_*.json plan.json
python3 scripts/build_aitable_rows.py plan.json
# Step 3（先 dry-run 校验）
python3 scripts/publish.py --doc-md ... --rows-json ... --dry-run
```

**前提**：服务器上得先装好 `dws` CLI 并登录到对应钉钉账号（用户体系跟本地一致）。

## 钉钉云文档发布机制（重要）

dws CLI **没有团队空间的写权限**——`dws doc create` 写到团队空间会报 `dentryUuid 不存在或无法访问`。但 `dws doc copy` + `dws doc rename` + `dws doc update --mode overwrite` 这条链路可以绕过该限制：

| 项 | 值 |
|---|---|
| 团队空间 workspaceId | `9JOGOMQYOo0ARX4Q` |
| 目标 folderId（CVE-2026-31431 同目录） | `Gl6Pm2Db8D3moL97iZBDm5vyJxLq0Ee4` |
| 默认模板 nodeId（CVE-2026-31431 本身） | `r1R7q3QmWe7MZNaLiZmKErdLJxkXOEP2` |

**这三个值都已写死在 publish.py 里作为默认值**，新 CVE 不用每次重传。

### 发布流程（推荐 --copy-from-template 路径）

```bash
python3 scripts/publish.py \
  --doc-md   <archive>/sw-<software>-<ts>_doc.md \
  --rows-json <archive>/sw-<software>-<ts>_rows.json \
  --doc-name "EGOVA-关于 ... CVE-XXX-YYYY 修复说明" \
  --copy-from-template
```

`publish.py` 会自动按这个顺序跑：

1. `dws doc copy` 用模板节点（默认 CVE-2026-31431）复制到默认团队空间 + 文件夹 → 拿新 nodeId
2. `dws doc rename` 把副本改成你给的 `--doc-name`
3. `dws doc update --mode overwrite` 把生成的 markdown 覆盖进去
4. 软件分支 sentinel 替换：序号取 max+1、说明&解决方案=新 nodeId 拼成的 alidocs URL
5. `dws aitable record create` 插入 AI 表格记录

### 备选路径

- `--doc-node-id <existing>`：你已经手建了空文档，把 nodeId 给 publish.py，跑 update overwrite（前提是 nodeId 已经在目标位置）
- 不传 `--doc-node-id` 也不传 `--copy-from-template`：fallback 到 `dws doc create`，但**不推荐**——dws 鉴权进不了团队空间，会落到个人空间或失败

### 铁律

- 所有 CVE 处置文档必须放到 `Gl6Pm2Db8D3moL97iZBDm5vyJxLq0Ee4` 下，不要落到根目录、个人空间
- 新 CVE 直接 `--copy-from-template`（不带值）即可，publish.py 自动用默认模板/folder/workspace

## 历史样本（CVE-2026-31431）

- 成品文档 nodeId：`r1R7q3QmWe7MZNaLiZmKErdLJxkXOEP2`
- 批量记录：「安全漏洞台账 → 操作系统漏洞」共 23 条
- 备份：`D:\opencode\_archive\cve_doc_after_*.md/json`
- 检测脚本样本：`D:\opencode\file\2026-05-06\cve-2026-31431-check.sh`
