---
name: 内部阅卷
version: 2.0.0
description: |
  公司内部统一阅卷工具，一套 skill 支持 4 类阅卷工作（通道自动路由）：
  ①性能安全认证阅卷（onekey.egova.com.cn Moodle quiz，双题 Q1/Q2 各 50 分）：登录→下载docx→解析→关键词初评→视觉细查→基线校准→HTML评语→dry-run→批量POST录入；
  ②麒舰实操阅卷（本地 docx 目录，10 大模块 100 分）：docx 解析→关键词+截图初评→基线校准→扣分明细+分数建议，仅出报告不回写；
  ③星桥高级认证阅卷（Moodle quiz 263，5 场景×20 分共 39 采分点）：拉卷→解析→关键词/代码/截图证据初评→人工复核应用→评语→提交 Moodle Q2~Q6；
  ④社招笔试阅卷（assesscenter.italent.cn 链接，Shell/Python/SQL/日期题）：打开链接→分析题目→下载答题附件→(连库取正确答案)→自动评分→MD 报告。
  触发词：内部阅卷 / 阅卷 / 评分 / 批改试卷 / 性能安全认证阅卷 / 性能安全评分 / 麒舰阅卷 / 麒舰实操打分 / 星桥高级阅卷 / 星桥评分 / 社招笔试 / Moodle 阅卷 / quiz 259 / quiz 263 / assesscenter / italent.cn。
  旧 skill（社招阅卷 / 麒舰实操考核-阅卷 / 星桥高级认证-阅卷 / company-grading-perf-sec）均已废弃，统一走本 skill。
author: majianquan
category: support-dept
visibility: support-dept
---

# 内部阅卷（统一阅卷 Skill）

公司内部统一阅卷工具。把原先分散的 4 个阅卷 skill（性能安全 / 麒舰实操 / 星桥高级 / 社招）合并为一套，共享下载、解析、视觉细查、报告、Moodle 提交底座，按触发信号自动路由到对应通道。

## 通道路由表

用户给出以下任一信号，先路由到对应通道，再按该通道工作流执行：

| 触发信号 | 通道 | 数据源 | 是否回写 |
|---|---|---|---|
| `onekey.egova.com.cn` Moodle URL / "性能安全认证阅卷" / "性能安全评分" / quiz id + 性能安全 | **perfsec 性能安全** | Moodle quiz（Q1/Q2 各 50 分） | ✅ 批量 POST |
| 本地目录含 `麒舰实操考核-*.docx` / "麒舰阅卷" / "麒舰实操打分" | **qijian 麒舰实操** | 本地 docx 目录（10 模块 100 分） | ❌ 仅报告 |
| `quiz?id=263` / "星桥高级阅卷" / "星桥评分" | **starbridge 星桥高级** | Moodle quiz 263（5 场景×20 分） | ✅ 提交 Q2~Q6 |
| `assesscenter.italent.cn` 链接 / "社招笔试" / "社招评分" | **social 社招** | AssessCenter 网页 | ❌ 仅报告 |

> 注：原 company-grading-perf-sec 的「麒舰部署 quiz 259」通道本次未并入；需要时按「扩展新通道」章节补脚本即可。

**⚑ 全局红线（所有通道）**：任何成绩回写都必须先 dry-run 预览、**人工明确确认后才执行**；未获确认禁止调用提交脚本。自动初评只作候选，最终分数以人工复核为准。

## 共享前置（所有 Moodle 通道）

- **登录态**：Chrome 已登录 `onekey.egova.com.cn`（账号 majianquan / Egova@123）
- **CDP**：Chrome remote-debugging 已开（`chrome://inspect/#remote-debugging`）
- **Python 3.10+**、**Word 16+**（.doc → .docx 转换）
- **工作目录**：默认 `D:\backup\user1\majq\Desktop\阅卷_<场景>\`，可指定
- **脚本路径**：以下命令均相对本 skill 根目录（`<skill_dir>`）

## 目录结构

```
内部阅卷/
├── SKILL.md                     # 本文件（统一入口 + 路由）
├── scripts/
│   ├── common/                  # 共享底座（Moodle 下载/解析/提交）
│   │   ├── download_attachments.py   # Moodle quiz 答卷批量下载（env: MOODLE_COOKIE）
│   │   ├── doc2docx.ps1              # .doc → .docx（Word COM）
│   │   ├── extract_docx.py           # docx 解压 → text_only.txt + media/ + items.json
│   │   └── moodle_submit.py          # Moodle 提交内核（fetch_form / post_grade）
│   ├── perfsec/                 # 通道①性能安全
│   │   ├── grading.py / grading_v2.py / gen_comments_v3.py / batch_submit.py / build_baseline.py
│   ├── qijian/                  # 通道②麒舰实操（本地 docx）
│   │   ├── grading_qijian.py / gen_comments_qijian.py
│   ├── starbridge/              # 通道③星桥高级
│   │   ├── grading_starbridge.py / gen_comments_starbridge.py / apply_manual_review_starbridge.py / submit_starbridge.py
│   └── social/                  # 通道④社招
│       └── db_query.py              # 连库取正确答案（pymysql）
├── references/                  # 各通道评分规则 + 基线
│   ├── grading_rules_perfsec.md / reference_baseline_perfsec.json / visual_check_prompt.md / RUN_perfsec.md
│   ├── grading_rules_qijian.md
│   └── grading_rules_starbridge.md / reference_baseline_starbridge.json
├── reference_answers/           # 性能安全标准答卷（基线重建用）
└── templates/grading_report_template.md   # 社招评分报告模板
```

---

## 通道① 性能安全阅卷（Moodle Q1/Q2，各 50 分）

评分规则详见 `references/grading_rules_perfsec.md`，完整流程详见 `references/RUN_perfsec.md`。

1. **下载**：CDP 取 MoodleSession cookie → `python scripts/common/download_attachments.py <quizid> <workdir>`（每人 `<workdir>/<attempt>_<名>/Q<n>_*.docx`）
2. **解析**：`pwsh scripts/common/doc2docx.ps1 <workdir>` → `python scripts/common/extract_docx.py <workdir>`
3. **初评**：`python scripts/perfsec/grading.py <workdir>` → `_grading_v1.*`
4. **视觉细查**：按 attempt 分 4 组派视觉 sub-agent（prompt 见 `references/visual_check_prompt.md`），结果存 `_visual/visual_*.json`
5. **校准**：`python scripts/perfsec/grading_v2.py <workdir>` → `_grading_v2.*`
6. **评语（v3，含标准答卷对比）**：`python scripts/perfsec/gen_comments_v3.py <workdir>` → `_grading_v3.json` + `_submit_plan.json` + `_submit_preview.md`
7. **dry-run 预览（必停）**：展示 1 位代表考生评语 + 排行榜，等用户说"提交"
8. **批量录入**：`python scripts/perfsec/batch_submit.py <workdir>`（POST 到 `mod/quiz/comment.php`，Q1/Q2 各一 slot）
9. **抽查校验**：访问 `review.php?attempt=XXX` 确认分数+评语

**标准答卷基线**：默认复用 `reference_answers/` 下 3 份 docx；题目变化时放新版 → `python scripts/perfsec/build_baseline.py` 重建 `references/reference_baseline_perfsec.json`。

---

## 通道② 麒舰实操阅卷（本地 docx，10 模块 100 分）

评分规则详见 `references/grading_rules_qijian.md`。**截图证据优先，文字辅助定位**；纯截图无文字的答案不得直接判 0，进入人工复核。

1. **解析**：输入目录含 `麒舰实操考核-*.docx` → `python scripts/common/extract_docx.py <workdir>`（每份 → `_extracted/<名>/text_only.txt` + `media/`）
2. **初评**：`python scripts/qijian/grading_qijian.py <workdir>` → `_grading_v1.json/md/csv`（10 模块关键词匹配 + 段落附近图片数评估）
3. **评语**：`python scripts/qijian/gen_comments_qijian.py <workdir>` → `_grading_final.md`（每人扣分明细 + 建议）
4. **汇报**：展示总分排行 + 代表考生完整扣分明细；截图充足但分数低的模块需视觉复核后人工覆盖（在脚本 override 中写明原因）

---

## 通道③ 星桥高级阅卷（Moodle quiz 263，5 场景×20 分）

评分规则详见 `references/grading_rules_starbridge.md`（39 采分点基线 `reference_baseline_starbridge.json`）。

1. **拉卷**：`python scripts/common/download_attachments.py 263 <workdir>`（需 Moodle 登录态）
2. **解析**：`python scripts/common/extract_docx.py <workdir>`（题目文本若一并提交，评分器自动过滤题干关键词）
3. **初评**：`python scripts/starbridge/grading_starbridge.py <workdir>` → `_grading_starbridge_v1.json/md/csv`
4. **人工复核**：对 `needs_visual` 项抽查 `media/` 截图 → 写 override JSON → `python scripts/starbridge/apply_manual_review_starbridge.py <workdir> <override.json>` → `_grading_starbridge_v2_manual.*`
5. **评语**：`python scripts/starbridge/gen_comments_starbridge.py <workdir>` → `_grading_starbridge_final.md`
6. **提交**：`python scripts/starbridge/submit_starbridge.py <workdir> [--only <attempt>] [--commit]`（提交到 Q2~Q6 五个 slot；默认 dry-run）

---

## 通道④ 社招笔试阅卷（AssessCenter）

1. **打开链接**：用 web-access 打开 `https://assesscenter.italent.cn/Report/SummaryReport?Elink=...`，提取考试名、学生姓名、题目列表（题号/分值/要求）、答题状态
2. **下载附件**：点击每题"下载答案"保存到临时目录
3. **读取答案**：文本直读；Word 提取文字+图片；识别格式（代码/截图/文本）
4. **取正确答案**（如需要）：`python scripts/social/db_query.py <命令>`（pymysql 连 demo.egova.com.cn:18260/school；命令见脚本 help）
5. **评分**：按题型标准评分（Shell：语法20/结果60/效率20；Python：逻辑40/结果40/质量20；SQL：语法20/结果60/效率20；日期：逻辑40/边界30/健壮30）
6. **报告**：按 `templates/grading_report_template.md` 输出 MD 评分报告（含总分汇总）

---

## 扩展新通道

1. `scripts/<新通道>/` 放评分/评语/提交脚本；共享底座直接 import `scripts/common/`
2. 基线/规则放 `references/`（命名带通道前缀）
3. 在路由表 + 触发词里登记新通道信号
4. 参考 `submit_starbridge.py` 的 common 引用写法（`os.path.join(SCRIPT_DIR, "..", "common")`）

## 注意事项

- **回写红线（所有通道）**：任何成绩回写必须先 dry-run 预览、人工明确确认后才执行；重复/旧 attempt 要 skip
- **截图答案**：社招截图答案需人工评分；麒舰/星桥按"截图优先"口径，不足的标记人工复核
- **编码**：脚本输出 UTF-8；中文乱码时检查 `[Console]::OutputEncoding`
- **临时文件**：阅卷完成后清理 `_extracted/`、`_visual/` 等中间产物（工作目录内保留评分结果）
