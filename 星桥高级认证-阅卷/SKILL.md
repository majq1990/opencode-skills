---
name: 星桥高级认证-阅卷
version: 1.0.0
description: 【已废弃 2026-09-04】统一改用「内部阅卷」skill（D:\opencode\config\skills\内部阅卷），本 skill 仅保留脚本供引用。不要在本 skill 新建阅卷任务。原能力：星桥高级一期认证自动阅卷。支持从政通大课堂 Moodle quiz 拉取答卷附件，解析 docx，按 5 个 20 分场景完成关键词/代码/截图证据初评，生成扣分明细和终版评语。默认不自动回写成绩。
author: majianquan
category: support-dept
visibility: support-dept
---

# 星桥高级认证 — 自动化阅卷

用于星桥高级一期认证（当前题目参考附件为 quiz 263、v3 试题版）。整卷 100 分，包含 5 个场景，每个 20 分：

1. ddcat 数据模型：数据库查询、数据转换、API 生成、授权和验证。
2. MIS 统计接口代理：认证脚本、响应转换、代理发布、授权和验证。
3. 第三方案卷上报：查库、字段与多媒体封装、定时任务和调度推送。
4. 多媒体增量同步：字段转换、URL/类型/端口/状态转换、2 分钟调度。
5. MySQL binlog 多表实时同步：人口、房屋、楼栋 CDC 与分析表汇总。

## 触发条件

- 提供 `星桥高级认证`、`星桥高级阅卷`、`星桥评分` 等关键词。
- 提供政通大课堂 Moodle 地址，尤其是 `quiz?id=263`。
- 提供星桥高级认证答卷目录或 docx 参考作答。

## 推荐流程

### 1. 拉取答卷

沿用公司阅卷底座的 Moodle 下载器：

```powershell
$env:MOODLE_COOKIE = 'MoodleSession=...'
python D:\git\opencode-skills\company-grading-perf-sec-2\scripts\download_attachments.py 263 <workdir>
```

需要登录态；访客只能进入课程首页，不能读取 quiz 263 的 responses/review 页面。下载器会保存 `_attempts.json`，并将每个 attempt 的附件放到 `<attempt>_<姓名>` 目录。

### 2. 解析 docx

```powershell
python scripts/extract_docx.py <workdir>
```

输出 `_extracted/<attempt>_<姓名>__<文件名>/text_only.txt`、`items.json` 和 `media/`。题目文本若被一并提交，评分器会优先从“答/答案”标记之后取证，避免把题干关键词误计为作答。

### 3. 初版评分

```powershell
python scripts/grading_starbridge.py <workdir>
```

评分器按参考作答建立的 39 个采分点进行初评：文字/脚本关键词用于定位，截图占位用于证据强度估计，代码和验证结果作为关键覆盖项。输出：

- `_grading_starbridge_v1.json`：可审计的逐采分点评分、命中证据和截图数。
- `_grading_starbridge_v1.md`：总分排行、场景汇总和扣分明细。
- `_grading_starbridge_v1.csv`：每人×采分点矩阵。

### 4. 生成评语

```powershell
python scripts/gen_comments_starbridge.py <workdir>
```

输出 `_grading_starbridge_final.md`，包含每人总分、场景得分、缺失采分点、建议补充证据和自动评分局限。

## 评分口径

- 每个场景满分 20 分，总分 100 分；详细采分点见 `references/grading_rules_starbridge.md`。
- 截图优先、文字辅助定位；只有文字没有截图时，自动初评最多按该采分点 30% 计，并标记人工复核。
- 有截图但没有可定位的文字/脚本时，自动初评不直接给满分，标记“需视觉复核”，防止把题干截图误当作答案。
- 截图内的 URL、水印、接口返回值、运行日志无法仅靠 docx 文本可靠识别；最终定分前应抽查 `media/` 图片。
- 第 5 场景保留“三张表实时同步”的证据字段；最终分数仍封顶 20 分，但可在评语中标记额外完成情况。
- 不自动提交 Moodle、不自动修改业务系统；如将来接入成绩回写，必须先生成 dry-run 预览并获得明确确认。

## 参考答案校准

当前基线来自：

`2025星桥高级一期认证-考核试题 - v3试题版—母中林.docx`

该参考作答包含 51 个图片证据，占位范围为 image1.png 至 image51.png。基线只用于“应覆盖哪些操作”和“最低证据数量”校准，不把参考答案中的具体账号、IP、token 或密码作为学员必须命中的内容。
