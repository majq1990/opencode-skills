# 麒舰视觉细查 sub-agent prompt 模板（quiz 259）

麒舰判分几乎全靠看截图。主线程按考生数量分组（每组 2-3 人，因每人 100+ 张图，量大），用 `general-purpose` subagent 并行细查。

## 调用方式

```
Agent(
  subagent_type="general-purpose",
  description="麒舰视觉细查 <attempt范围>",
  run_in_background=True,
  prompt=<填充以下模板>
)
```

每个 sub-agent 输出 JSON，主线程保存到 `<workdir>/_visual/visual_<range>.json`（sub-agent 不写文件，把 JSON 打印回来）。

## Prompt 模板

```
你的任务是对 N 位考生的"麒舰部署实操考核"答卷做视觉细查，按 41 个采分点逐项判定。

## 评分基线
先 Read 这个文件，理解每个采分点要看什么：
D:\<workdir>\..\reference_baseline_qijian.json    （或 skill references/reference_baseline_qijian.json）
重点字段：key_check（命中条件）、need_url（是否要求截入URL）、std_desc（标准答卷此处内容）。

## 业务系统 URL 关键字
智信云 eUrbanUMA/eUrbanGIS · 麒舰 eurbanpro · 用户中心 usercenter · 玄藏 xuanzang · 灵珑 linglong

## 考生列表
1. **<attempt> <姓名>**
   - 截图目录: `D:\<workdir>\_extracted\<attempt>_<姓名>__Q<slot>_*\`
     （含 text_only.txt + media/imageN.png，截图按文档顺序编号）

如未交标 missing；同一份重复提交只看一份。

⚠ **多附件考生必须合并判分**：若某考生有多个 `__Q<slot>_*` 目录（如 slot-1 主文档 + slot-10
全业务流转补充），要把该考生**所有** Q 目录的 text_only + 截图合在一起判，某段采分点只要在任一
附件里出现就算 found。**只看其中一个目录会把另一部分误判为"没做"**（实测 quiz259 汪志超因此被
低估 ~20 分）。

## 逐项判定方法
- 按 text_only.txt 的小标题（# **一键部署** / # **地理数据替换** ...）定位每个大项对应的截图区间，再逐个采分点判。
- 每个采分点只需看 1-3 张关键图（用 Read 读 PNG），对照 baseline 的 key_check。
- found 三档：
  - yes = key_check 命中、关键操作截图齐全
  - partial = 做了但不完整（缺关键步骤 / 统计区空 / 图层未勾选 / 流程截图过少）
  - no = 未做或截图无关；该考生整段缺失也用 no
- has_url：仅对 need_url=true 的项判断；截图里能看到**浏览器地址栏完整 URL**=true，否则 false。
  - ⚠ **必须真的看图确认地址栏**，不要因为"考试要求截 URL"就默认 true。考核明文规定未截 URL
    扣一半分，评分脚本对 need_url 且 has_url=false 的项 ×0.5。判松会系统性虚高（实测主线程凭
    文本默认 has_url=true 时，S8 移动端/S10 全流程比看图判分整体偏高 ~0.6-0.8 分/段）。
  - 移动端手机截图（jpeg）通常没有浏览器地址栏，has_url 一般为 false，按实判。
- img_count：该采分点你实际看到的相关截图张数。

## 输出 JSON（严格格式，最后单独打印）
{
  "<attempt>_<姓名>": {
    "S1-1": {"found":"yes|partial|no|missing", "has_url":true|false, "img_count":N, "evidence":"imageK.png: ..."},
    "S1-2": {...},
    ...
    "S10-7": {...}
  },
  "<下一位>": { ... }
}

## 工作要点
- 必须覆盖全部 41 个采分点（S1-1..S1-8, S2-1..S2-11, S3-1..S3-5, S4-1..S4-2, S5-1, S6-1..S6-5, S7-1..S7-6, S8-1..S8-5, S9-1..S9-5, S10-1..S10-7）。
- evidence 写明 imageN.png + 关键内容，便于人工复核。
- S2-6/S2-10（图层控制）、S3-4（四类岗位）、S10-5（延期2小时）这些项判读要谨慎，拿不准给 partial 并在 evidence 注明"需人工复核"。
- 报告输出严格 JSON。
```

## 整合阶段
全部 sub-agent 完成后，主线程把各 JSON 存入 `<workdir>/_visual/`，跑：
```
python scripts/grading_qijian.py <workdir>
```
即生成 `_grading_qijian.json/.md` 和 `_submit_plan_qijian.json`。
