# 调用流程详解（Claude 主控视角）

## 输入

用户给出 quiz URL，如：
- `http://onekey.egova.com.cn:8888/mod/quiz/view.php?id=258`
- 或仅 quiz id：`258`

## Phase 0：准备

```bash
# 1. 检查 CDP
bash ~/.claude/skills/web-access/scripts/check-deps.sh

# 2. 提取登录 Cookie（用 CDP 拿 Chrome 当前 onekey.egova 站点的 cookie）
# 通过 /eval 在 onekey 站点的任意 tab 执行 document.cookie
# 设置环境变量 MOODLE_COOKIE=<取到的 cookie>

# 3. 创建工作目录
QUIZ_ID=<从URL提取>
WORKDIR="D:\backup\user1\majq\Desktop\阅卷_${QUIZ_ID}"
mkdir -p "$WORKDIR"

# 4. 把 reference_answers/ 链接或复制到 workdir/_reference/
cp -r "<skill>/reference_answers" "$WORKDIR/_reference"
```

## Phase 1：抓附件

```bash
export MOODLE_COOKIE="MoodleSession=...; MOODLEID1_=..."
python <skill>/scripts/download_attachments.py $QUIZ_ID "$WORKDIR"
```

输出：`<WORKDIR>/<attempt>_<姓名>/Q<n>_<原文件名>.docx` + `_attempts.json`

## Phase 2：解析

```bash
# .doc → .docx（用户机器装有 Word）
pwsh <skill>/scripts/doc2docx.ps1 "$WORKDIR"

# 解析所有 docx
python <skill>/scripts/extract_docx.py "$WORKDIR"
```

输出：`<WORKDIR>/_extracted/<key>__Q<n>_*/text_only.txt + media/*.png`

## Phase 3：初评

```bash
python <skill>/scripts/grading.py "$WORKDIR"
```

输出：`_grading_v1.{json,md,csv}`

## Phase 4：派 4 个并行视觉细查 sub-agent

主线程读 `<WORKDIR>/_extracted/` 的目录列表，按 attempt 平均分 4 组。每组用 Agent 工具派一个 general-purpose sub-agent（run_in_background=True），prompt 用 `references/visual_check_prompt.md` 模板填充。

派完 4 个后等任务通知。每个 sub-agent 回来：
- 解析其 JSON 输出
- 写入 `<WORKDIR>/_visual/visual_<n>.json`

如有重复提交（同名 attempt，如 6752/6753 康航源），手动在 grading_v2.py 加 alias 行：
```python
visual_data["6753_康航源v2"] = dict(visual_data["6752_康航源"])
```

## Phase 5：综合校准 → v2

```bash
python <skill>/scripts/grading_v2.py "$WORKDIR"
```

输出：`_grading_v2.{json,md,csv}` 含视觉细查 + 严格规则。

## Phase 6：评语生成（v3 含标准答卷对比）

```bash
python <skill>/scripts/gen_comments_v3.py "$WORKDIR"
```

输出：`_grading_v3.json` + `_submit_plan.json`（待提交清单）+ `_submit_preview.md`（每人 HTML 评语预览，含"标准答卷此处应有 X 张/缺 Y"对比文案）

v3 在 v2 基础上：
- 截图数 ≥ `references/reference_baseline.json` 标准 → 自动回满分
- 截图数不足 → 保留 90% 折扣但文案说清缺什么
- 旧 `gen_comments.py` 仅作向后兼容，新一轮阅卷直接走 v3

> ⚠ v3 调整后分数会变化（实测 quiz 260 每人 +0.0~0.8）。若 Phase 8 已提交过 v2 评语，v3 需再跑一次 `batch_submit.py` 覆盖。

## Phase 7：dry-run 预览（**必停**等用户确认）

向用户展示：
1. **完整排行榜**（带总分 + 备注）
2. **1 位代表的 HTML 评语**（推荐最高分 attempt 的 Q1+Q2）

询问：「评语样式与分数满意吗？OK 我就批量录入。」

如果用户要调整，回到 Phase 5 修参数。

## Phase 8：批量录入

```bash
python <skill>/scripts/batch_submit.py "$WORKDIR"
# 或跳过某些已评/不动的 attempt:
# python <skill>/scripts/batch_submit.py "$WORKDIR" --skip 6748:1,6748:2
```

失败的会列在末尾，单独重试：
```bash
python <skill>/scripts/moodle_submit.py "$WORKDIR"   # 不带 plan 入参不会自动跑；自己 import 后调
```

## Phase 9：抽查校验

抽 2-3 个 attempt 访问 `mod/quiz/review.php?attempt=X` 看分数+评语都正确显示。

## 重要细节

### Cookie 提取
用 web-access CDP 在已打开的 onekey 站点 tab 执行：
```js
document.cookie
```
返回 `MoodleSession=xxx; MOODLEID1_=xxx` 直接用作环境变量。

### attempts 列表
`_attempts.json` 含每个 attempt 的 {attempt, name, email, files[]}，files 里每项有 quba_id。
batch_submit 不用预存 QUBA 表 — `moodle_submit.fetch_form` 每次 POST 前先 GET 拿 quba_id 和 sesskey。

### 重复提交识别
download_attachments 默认目录名会冲突，处理逻辑：
- 同 attempt id 永远不同目录
- 同姓名不同 attempt 直接用 `<attempt>_<姓名>` 区分（attempt 是唯一的）

### 阻塞点
- 用户必须先在 Chrome 登录 onekey.egova.com.cn
- 用户机器必须装 Word（处理 .doc 老格式）
- CDP 必须 chrome://inspect/#remote-debugging 启用

## 错误处理

| 错误 | 处理 |
|---|---|
| MOODLE_COOKIE 缺 | 从 CDP /eval `document.cookie` 重新提取 |
| .doc 转换失败 | 检查 Word/WPS COM 注册 |
| POST 超时 | 单独重试该项 |
| 关键词未命中 | 视觉细查可能 missing，重新看 text_only.txt 调正则 |
| Q1 raw > 59 | 检查采分点定义是否新增导致 max_sum 错 |
