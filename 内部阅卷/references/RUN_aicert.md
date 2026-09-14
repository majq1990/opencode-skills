# 通道⑤ AI认证阅卷（quiz265笔试 + quiz266实操，增量）

100分制：T1/30 + T2/30 + T3/40 = 实操100，60合格；笔试准入≥90。
A版只卡总分；B版加卡 (T1+T2)≥36 且 T3≥24。安全红线一票否决。

## 输入（每次只需给这两个）

- 笔试 quiz：`http://onekey.egova.com.cn:8888/mod/quiz/view.php?id=265`（overview 全部分页取成绩，同人取最高）
- 实操 quiz：`http://onekey.egova.com.cn:8888/mod/quiz/view.php?id=266`（responses 全部分页下载附件）
- 花名册：钉钉表格“全员状态”（权威大区/区域/姓名/邮箱/已交卷状态），只看此表

## 状态文件（workdir内，增量依据）

| 文件 | 内容 |
|---|---|
| `_attempts.json` | 全量 attempt 元数据（common下载脚本翻页后重写） |
| `_manifest.json` | 解包清单（unpack_266.py逻辑，复用/重写为 unpack_aicert.py时保留） |
| `_posted_<quiz>.json` | `{attempt: {slot: mark}}` 已回写记录；增量时跳过已POST slot |
| `_grading/G{0..3}_{Q1,Q2,Q3}.json` | attempt级三题分数（agent独立阅卷产物） |
| `_总成绩表100_v2.csv` | 合并底表；表格/文档由此生成 |

## 增量一轮流程

1. **拉取**：`download_attachments.py <实操id> <workdir>`（已翻页+断点续传；cookie过期从CDP重取）
   `fetch_265_grades.py` 同理拉笔试（见当时workdir内脚本，overview分页）。
2. **找新增**：对比 `_attempts.json` files 列表与 `_posted_<quiz>.json`，
   新增/补交 attempt（或新增文件）才进入阅卷；其余跳过。
3. **解包新增**：`unpack`（7z解zip/rar/7z，成功清单入_manifest）。
4. **阅卷新增**：每~50份一组，每题一个独立agent（Q1/Q2/Q3 rubric见
   `references/grading_rules_aicert.md`），只看证据截图（svg图标不算），
   0证据截图该题 cap30%，缺交0分，红线0分；返回JSON数组落 `_grading/`。
5. **花名册对碰**：只看“全员状态”：已交卷vs已评分双向差异；参考中未交卷=下轮待拉；
   实际未参考=不计分；重名/多attempt取最高并备注；排除考核名单（如陈涵/李冰/刘龙战）
   标“不参考”（Moodle已写分需同步改评语，不动marks）。
6. **合并**：`rebuild_100.py` 逻辑 → `_总成绩表100_v2.csv`（12列，含马健权类钉钉文档提交行）。
7. **回写（红线）**：`submit_aicert.py <workdir>` 先dry-run展示代表评语，
   用户明确说“提交”后加 `--commit`；只POST未POST过的slot；
   评语按题写扣分明细（REQ表），slot1/2/3=maxmark 30/30/40预检，不符即停。
8. **更新表格**：`set_range_from_csv` 全量覆盖“版本A全量/版本B全量”两表；
   文档（双版本说明+名单+全量表）同步覆盖/追加。

## 校准基线

- 马健权三份答卷 strict 99.1（T1-4组合承载图标扣1），规则有扣分能力；
  人群 mean ~55，区分度正常。详见验证目录与 `_ grading` 产物。
- Moodle 404 slot（如7259-Q1/Q3、7301-Q1）无法回写，备注留痕。
