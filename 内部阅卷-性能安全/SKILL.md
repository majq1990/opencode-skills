---
name: company-grading-perf-sec
version: 1.2.0
description: 公司内部阅卷工具，支持两条通道。①性能安全通道：onekey.egova.com.cn Moodle quiz（性能安全认证实操，双题Q1/Q2各50分），登录→下载docx→解析→关键词初评→4并行视觉sub-agent→基准对照→标准答卷基线校准→HTML扣分评语→dry-run→批量POST录入。②麒舰部署通道（quiz 259，单题满分100，10大项41采分点部署实操）：下载→解析→视觉细查（按baseline的key_check/URL红线逐项判）→grading_qijian.py算分→评语→submit_qijian.py单slot录入。触发词：性能安全认证阅卷 / Moodle 阅卷 / onekey.egova quiz / 性能安全评分 / 麒舰部署阅卷 / 麒舰实操考核 / quiz 259。
author: majianquan
category: support-dept
visibility: support-dept
---

# 公司内部阅卷-性能安全

自动化阅卷工具。一次性把 Moodle 性能安全认证实操考试的所有学员答卷下载、解析、视觉判分、生成评语、录入完成。

## 触发条件

本 skill 有**两条通道**，按信号自动路由：

### 性能安全通道（默认，双题 Q1/Q2 各 50 分）
- Moodle quiz URL（`http://onekey.egova.com.cn:8888/mod/quiz/view.php?id=XXX`）
- 提及"性能安全认证阅卷"、"性能安全认证评分"、"性能安全实操打分"
- 提供 quiz id 数字 + 上下文有"性能安全"

### 麒舰部署通道（单题满分 100，10 大项部署实操）
- **quiz 259**（`.../mod/quiz/view.php?id=259`）
- 提及"麒舰部署阅卷"、"麒舰实操考核"、"麒舰评分"
- 评分规则见 `references/grading_rules_qijian.md`，完整流程见文末 **「麒舰部署阅卷通道」** 章节

## 运行环境前置

- **登录态**：Chrome 已登录 onekey.egova.com.cn（账号 majianquan / Egova@123）
- **CDP**：Chrome remote-debugging 已开（`chrome://inspect/#remote-debugging`）
- **Python 3.10+**, **Word 16+**（用于 .doc → .docx 转换）
- 工作目录：默认 `D:\backup\user1\majq\Desktop\阅卷_<quizid>\`，可指定

## 端到端工作流

### Phase 1：登录 + 下载附件
1. 用 web-access skill 启动 CDP，访问 `http://onekey.egova.com.cn:8888/mod/quiz/report.php?id={quizid}&mode=responses&pagesize=100`
2. 拿到所有 attempt 列表 + 每位考生的 Q1/Q2 附件 URL（pluginfile.php 链接 + quba_id）
3. 提取 Chrome 的 MoodleSession cookie
4. 用 `scripts/download_attachments.py <quizid> <workdir>` 批量下载所有 .docx/.doc 到 `<workdir>/<attempt>_<name>/Q<n>_*.docx`

### Phase 2：解析
1. `.doc` → `.docx`：`pwsh scripts/doc2docx.ps1 <workdir>` （Word COM 转换）
2. `python scripts/extract_docx.py <workdir>`：解压 docx 提取按段落顺序的"文字段+图片占位+图片文件"到 `<workdir>/_extracted/`

### Phase 3：初版评分
`python scripts/grading.py <workdir>` — 基于关键词+图片数+论述字数对 29 个采分点初评，输出 `_grading_v1.json/md/csv`

### Phase 4：派 4 个并行视觉细查 sub-agent
**主线程**根据 attempt 数量分 4 组，每组 3-4 人。用 Agent 工具并行调用 `general-purpose` subagent，prompt 模板见 `references/visual_check_prompt.md`。每个 sub-agent 输出 JSON 保存到 `<workdir>/_visual/visual_*.json`：
- P1-1 内网访问 URL（浏览器=true / curl=false）
- P1-4 nginx 状态（统计分布+10s耗时缺一段→partial）
- P2-1~P2-7 巡检报告（统计区数据真假）
- S1-1 雷池登录 URL
- S2-1/S2-2/S2-3 lua_waf 三要素（factors_met 0-3）
- S3-1 弱密码清单 count

### Phase 5：综合校准 → v2 评分
`python scripts/grading_v2.py <workdir>` — 用 `references/grading_rules.md` 里定义的 VISUAL_ADJUST 比例对初版打分，Q1 按 raw/59×50 缩放（22 采分点合计 59 分但满分 50）。

### Phase 6：生成评语（v3，含标准答卷对比）
`python scripts/gen_comments_v3.py <workdir>` — 在 v2 结果上做"截图基线校准 + 评语对比文案"：
- 读取 `references/reference_baseline.json`（每个采分点的 `std_min_imgs` + `std_desc`，从两份标准答卷自动抽取）
- 对未视觉细查覆盖的项：若 `imgs ≥ std_min_imgs` → 自动回满分（标"内容覆盖完整"），否则保留 90% 折扣但文案说清"标准应有 X 张（覆盖 Y/Z），实际 N 张"
- 输出 `_grading_v3.json` + `_submit_plan.json` + `_submit_preview.md`（每人 Q1/Q2 HTML 评语含扣分明细+视觉证据+**标准答卷对比**+满分项）
- 旧版 `gen_comments.py` 不再推荐，保留向后兼容

### Phase 7：dry-run 预览（**必停**）
向用户展示 1 位代表考生（推荐最高分 attempt）的 Q1+Q2 评语 + 完整排行榜。等用户说"提交"。

### Phase 8：批量录入
`python scripts/batch_submit.py <workdir>` — 对每个 attempt × 2 slot POST 到 `mod/quiz/comment.php`，自动获取 quba_id + sesskey + itemid，间隔 0.5s 避免限流。失败的单独重试。

### Phase 9：抽查校验
用 web-access 访问 review.php?attempt=XXX 几个代表 attempt，确认分数+评语已显示。

## 评分规则（详见 references/grading_rules.md）

### Q1 性能监控（22 采分点合计 59 分，缩放到 50）
| 段 | 采分点 | 分 | 视觉要求 |
|---|---|---|---|
| 应急 | P1-1 内网访问 | 3 | 浏览器URL=满分 / curl=半分 |
| 应急 | P1-2 mysql 状态 | 3 | 截图 |
| 应急 | P1-3 达梦状态 | 3 | 截图 |
| 应急 | P1-4 nginx 状态 | 5 | 统计分布+10s耗时分布 二段必须都有 |
| 应急 | P1-5 应用日志 | 3 | 截图 |
| 应急 | P1-6 jvm 信息 | 3 | 截图 |
| 应急 | P1-7 redis 状态 | 3 | 截图 |
| 应急 | P1-8 磁盘 I/O | 3 | 截图 |
| 应急 | P1-9 系统恢复思路 | 4 | **论述题**≥60字 |
| 巡检 | P2-1~7 各项 | 2-3 | **报告统计区必须有数据**，仅基本信息=20%，空白=0 |
| 巡检 | P2-3 microservice | 3 | 含 dump 路径处理（HeapDumpPath） |
| 巡检 | P2-5 nginx | 3 | 含 logrotate 修复过程 |
| 基准 | P3-1~6 各项 | 2-3 | 截图 |

### Q2 安全运维（7 采分点合计 50 分）
| 段 | 采分点 | 分 | 视觉要求 |
|---|---|---|---|
| 雷池 | S1-1 部署+登录 | 6 | 登录页/仪表盘需带URL |
| 雷池 | S1-2 模拟攻击 | 6 | 拦截效果图带URL |
| 雷池 | S1-3 拦截租户接口 | 5 | 截图 |
| lua_waf | S2-1 应用中心放开 | 6 | 三要素：32018拦截+wafconf/url 注释+应用中心恢复 |
| lua_waf | S2-2 拦截操作日志 | 6 | 三要素：取URL+echo>>url+reload+403验证 |
| lua_waf | S2-3 CC 防护 | 6 | 三要素：取login URL+echo>>cc-url+reload；**ab+31001 加分 10%** |
| 弱密码 | S3-1 清单 | 15 | ≥5个=100% / 3-4个=50% / 其他=0 |

## 关键文件输出

| 文件 | 内容 |
|---|---|
| `_grading_v1.json` | 初版（关键词+图数+论述字数） |
| `_grading_v2.json` | 视觉校准后 |
| `_grading_v2.md` | 排行榜+每人扣分明细 |
| `_grading_v2.csv` | Excel 矩阵（行=学员 列=采分点） |
| `_grading_v3.json` | **标准答卷基线校准后（终版）**，含 `v3_adjustments` 字段记录回满项 |
| `_visual/visual_*.json` | 4 组视觉细查结果 |
| `_submit_plan.json` | 待提交计划（attempt/slot/mark/comment），v3 直接覆写 |
| `_submit_preview.md` | HTML 评语预览（每人 Q1/Q2，含标准答卷对比） |
| `_submit_results.json` | 批量提交结果日志 |

## 参考答案

默认复用 `reference_answers/` 下三份钉钉文档导出：
- `性能监控实操-马健权.docx`
- `性能监控实操-李棒棒.docx`
- `性能安全实操考核-王拥民.docx`

新一轮考试题目变化时：
1. 把新参考答案放入此目录
2. 重新生成 `references/reference_baseline.json`：跑 `scripts/build_baseline.py`（取两份标准答卷各采分点的图数最大值 + 内容描述），把过度计数的项（如标准答卷因分节问题被高估）人工微调

## 麒舰实操阅卷特别规则

麒舰实操题与性能安全报告题不同，很多学员答案是纯截图或极少文字说明。阅卷时必须采用“截图证据优先，文字辅助定位”的口径：

- 不得因为截图前后没有文字、只有“是/已完成”等弱说明，就把该题直接判 0；应查看截图或生成 contact sheet 人工复核。
- 对整套题塞在一个 Word 里的提交，要警惕两类错误：截图连续出现导致自动漏判；题目要求文字被误当成学生证据导致误加分。
- 自动初评只能作为候选结果。凡是“截图数量不少但分数低”的模块，必须二次视觉复核；凡是“有题目说明文字但无对应学生截图”的模块，应扣回误加分。
- 人工覆盖分数时，必须在脚本的 override 中写明原因，并重新生成 `_qijian_grading_v1.*`、`_qijian_submit_plan.json` 和预览。
- 提交 Moodle 前必须 dry-run 验证 quba/sesskey/itemid/sequencecheck 抓取正常；重复/旧 attempt 要明确 skip，避免把 0 附件旧记录写入。

## 重要变更记录

### v1.1.0（2026-05-18，quiz 260 实战沉淀）
- 新增 `references/reference_baseline.json`：26 个采分点的 `std_min_imgs` + `std_desc`（从两份标准答卷自动抽取）
- 新增 `scripts/gen_comments_v3.py`：在 v2 结果上做截图基线校准 + 标准答卷对比文案
- **关键改动**：v1 残留的"截图数 → 90% 折扣"机制下，截图数 ≥ 标准基线 → 自动回满分（避免如 P1-6 jvm 标准只 1 张但学员交了 2 张反被扣分的不合理情况）
- 评语模板从「✓ N张截图 ⚠特殊要求」改为「标准答卷此处应有 X 张，覆盖 Y/Z，本卷 N 张」，扣分理由更具诊断性

## 异常处理

- **未登录**：跳转登录页，提示用户用 Chrome 手动登录后再触发
- **Cookie 过期**：从 CDP 重新提取
- **.doc 转换失败**：检查 Word/WPS 是否安装
- **POST 超时**：单独重试该项（参考 batch_submit.py 中失败列表）
- **重复提交 attempt**（如 6752/6753 康航源 v1/v2）：视觉数据复用第一个，两份都提交（Moodle 取最高分）

---

# 麒舰部署阅卷通道（quiz 259）

与性能安全完全不同：**单题满分 100**，10 大项部署实操，41 个采分点几乎全靠**截图证据**判分。下载 / 解析 / 提交机制复用，评分 / 视觉 / 评语为麒舰专属。

## 采分结构（100 分）
S1 一键部署授权10 · S2 地理数据替换20 · S3 组织机构维护15 · S4 监督员网格5 · S5 事项配置5 · S6 栏目配置10 · S7 导航配置5 · S8 移动端10 · S9 工作流10 · S10 全业务流转10。
全部采分点 + `std_min_imgs` / `need_url` / `key_check` 见 `references/reference_baseline_qijian.json`，判分规则见 `references/grading_rules_qijian.md`。

## 关键差异
- **URL 红线**：考核说明明确"业务系统截图未截入 URL 默认扣一半分"。`need_url:true` 的项若做了但无 URL → 得分 ×0.5（脚本自动处理）。
- **新加考点无标准样本**（须人工复核，预览标 ⚠）：S2-6 / S2-10 图层控制截图、S3-4 四类岗位权限、S9-5 二级授权、S10-5 延期2小时。
- **标准答卷有新旧两版**：以考核说明（新版：地理20/组织15/移动10）为准，baseline 已按新版建立。

## 端到端工作流

### Phase 1：下载（复用）
1. 同性能安全：CDP 取 MoodleSession cookie → `python scripts/download_attachments.py 259 <workdir>`。
2. **确认 slot 数**：麒舰默认按单题 slot=1 满分 100。首次跑前访问任一 `review.php?attempt=XXX` 确认 quiz 259 实际 slot 数；若拆成多题，提交时按实际 slot 标注。

### Phase 2：解析（复用）
`pwsh scripts/doc2docx.ps1 <workdir>` → `python scripts/extract_docx.py <workdir>`，得到每人 `_extracted/<attempt>_<名>__Q<slot>_*/` 下 text_only.txt + media/imageN.png。

### Phase 3：视觉细查（麒舰专属，核心）
麒舰每人 100+ 张图，按 **2-3 人一组**派 `general-purpose` sub-agent 并行，prompt 用 `references/visual_check_prompt_qijian.md` 模板。每个 agent 对 41 采分点逐项输出 `{found, has_url, img_count, evidence}`，主线程存入 `<workdir>/_visual/visual_<range>.json`。

### Phase 4：评分（麒舰专属）
`python scripts/grading_qijian.py <workdir> [--slot 1]`：读 baseline + `_visual/*.json` → 算分（found 三档 ×URL红线）→ 产出 `_grading_qijian.json` / `_grading_qijian.md`（排行+大项失分明细）/ `_submit_plan_qijian.json`（含 HTML 评语）。

### Phase 5：dry-run 预览（**必停**）
展示排行榜 + 1 位代表考生的完整大项评语，重点标出 ⚠ 人工复核项。等用户说"提交"。

### Phase 6：批量录入（麒舰专属，单 slot 满分 100）
`python scripts/submit_qijian.py <workdir> [--dry-run] [--skip attempt,...]`，复用 `moodle_submit.post_grade`（满分由 comment.php 表单 maxmark 自动读取）。

### Phase 7：抽查校验（复用）
访问几个代表 attempt 的 review.php 确认分数 + 评语已显示。

## 麒舰专属文件
| 文件 | 内容 |
|---|---|
| `references/reference_baseline_qijian.json` | 41 采分点基线（std_min_imgs/need_url/key_check） |
| `references/grading_rules_qijian.md` | 麒舰判分规则（URL红线/三档比例/人工复核项） |
| `references/visual_check_prompt_qijian.md` | 视觉细查 sub-agent prompt 模板 |
| `scripts/grading_qijian.py` | 评分 + 生成评语 + 提交计划 |
| `scripts/submit_qijian.py` | 单 slot 满分 100 批量录入 |
| `<workdir>/_grading_qijian.{json,md}` | 评分明细 / 排行榜 |
| `<workdir>/_submit_plan_qijian.json` | 待提交（attempt/name/slot/mark/comment） |

## 麒舰参考答卷（建 baseline 用）
4 份标准答卷（钉钉文档）：施坚兴(新版)/凌灿/马健权(旧版)/王拥民。新一轮题目变化时，重新读取标准答卷重建 `reference_baseline_qijian.json`（用 dws doc read 取 markdown，统计各采分点图数 + key_check）。

## 重要变更记录（麒舰）
### v1.2.0（2026-06-01）
- 新增麒舰部署通道：quiz 259 单题满分 100，10 大项 41 采分点
- 从 4 份标准答卷自动抽取 `reference_baseline_qijian.json`（含 URL 红线标记）
- 新增 `grading_qijian.py` / `submit_qijian.py` + 视觉/规则文档；下载/解析/提交底座复用
