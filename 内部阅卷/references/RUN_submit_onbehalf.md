# 批量代交卷（未交卷处理）RUN 手册

## 适用场景

阅卷/汇总时发现 Moodle 测验里有人"作答了但没点交卷"：试答停在**进行中**，不能评分、不能批改、不能回写。
Moodle 3.x 教师端没有"代交卷"按钮（4.2+ 才有教师代提交），需要**管理员**介入：
临时给这些用户加"用户覆盖"延长截止（否则测验已关闭进不去）→"以此用户身份登录"逐个交卷 → 删覆盖。

**红线**：`submit` / `cleanup` 是写操作。先 `list` 出清单 → **人工确认**（哪些代交、空卷是否也交）→
dry-run 预览 → `--commit` 执行 → `verify` 复核（进行中=0）→ `cleanup`（覆盖=0）。
代交卷提交的是"当前已保存的答案"；空卷会因此变为"已结束"并得 0 分。

## 一分钟流程（cmid 即测验 URL 里的 id，如 report.php?id=266 → 266）

```bash
cd <工作目录>   # 产出 json 落在当前目录，建议当日 file 目录

# 1) 列清单（只读）
python scripts/common/submit_onbehalf.py list --cmid 266
#   → 输出状态统计 + 进行中明细，清单存 _submit_onbehalf_266_inprogress.json

# 2) 人工确认清单（交给用户拍板；空卷要不要交、名单是否要剔除）

# 3) 代交卷（写操作；先 dry-run 看计划，确认后加 --commit）
python scripts/common/submit_onbehalf.py submit --cmid 266 -f _submit_onbehalf_266_inprogress.json
python scripts/common/submit_onbehalf.py submit --cmid 266 -f _submit_onbehalf_266_inprogress.json --commit
#   → 自动建覆盖（默认截止=当前+2小时，可用 --close "2026-09-15 12:00" 指定）
#   → 逐个考生交卷；过程与结果存 _submit_onbehalf_266_state.json（断点续跑依据）

# 4) 复核（只读）
python scripts/common/submit_onbehalf.py verify --cmid 266
#   → 进行中应为 0；用户覆盖若不为 0 进入下一步清理

# 5) 删覆盖（写操作；不删的话窗口内考生还能继续进测验）
python scripts/common/submit_onbehalf.py cleanup --cmid 266 -f _submit_onbehalf_266_state.json --commit
#   → 覆盖列表应为 0
```

## 认证与环境变量

| 变量 | 用途 |
|---|---|
| `MOODLE_COOKIE` | 会话 Cookie（浏览器 F12 复制整条；GET 可、POST 可能被弹回登录，仅作兜底） |
| `MOODLE_USER` + `MOODLE_PASSWORD` | 账密登录（推荐；每个考生独立全新会话，最稳） |
| `MOODLE_BASE` | 站点地址，默认 `http://onekey.egova.com.cn:8888`（也可用 `--base`） |
| `MOODLE_ENV_FILE` | 变量文件路径，默认 `D:\opencode\config\.env`（键=值 每行一条） |

## 已实测机制与坑（onekey Moodle 3.8.5，2026-09-15 quiz 266 实战）

- **关闭后学生进不去**；"用户覆盖"可临时延长截止（覆盖优先于全局关闭）。办完必须删覆盖。
- **交卷入口**：`summary.php?attempt=N&cmid=266`（"结束试答"页）→ POST `processattempt.php`
  表单（`attempt` / `finishattempt=1` / `timeup=0` / `slots` / `cmid` / `sesskey`）→ 302 到 view.php，试答变"已结束"。
  答题页（attempt.php）只有"下一页"，没有交卷按钮，**必须走 summary.php**。
- **已保存答案/附件不受影响**：实测 4 份有附件卷提交后附件完好（1/1/7/3 个）。
- **覆盖删除是两步**：`overridedelete.php?id=..&sesskey=..`（GET）只是**确认页**，必须再 POST
  （`confirm=1` + `sesskey`）才真删；只 GET 不 POST 会"看似执行了其实没删"。
- **覆盖创建**：GET `overrideedit.php?cmid=266` 取表单 → POST（`userid` + `timeclose[...]` 各段 + `timeclose[enabled]=1`）；
  列表页 `overrides.php?cmid=266&mode=user` 可核对（行内含 `overridedelete.php?id=..` 链接）。
- **loginas**：`/course/loginas.php?id=<课程id>&user=<uid>&sesskey=<管理员sesskey>`；
  课程 id 脚本自动从测验页探测（本测验=12）。
- **时间时区**：覆盖时间按管理员用户时区（北京时间）解释；`--close` 用本机时间。
- **会话坑**：requests 复用浏览器旧 Cookie 做 POST 会被弹回登录页；脚本对**每个考生新建会话+账密登录**，避免串号。
- **窗口副作用**：覆盖窗口期内，考生本人若正好还在页面里，可能自己点交卷（甚至新开一份空卷）；
  `submit` 会先复核"是否仍是进行中"，已结束的自动跳过。跑完 `list` 再看一眼有没有新冒出来的进行中。

## 常见问题

| 现象 | 处理 |
|---|---|
| `list` 显示进行中 0 | 没有要处理的；若刚关窗后又有人进，重跑 `list` |
| `submit` 某份 skip | 该试答已结束或不可进入（输出带 snippet 提示），无需重试 |
| 提交后仍显示进行中 | 看 state json 的 `finished` 字段；个别失败重跑 `submit`（会跳过已结束的） |
| `cleanup` 后覆盖列表非 0 | 可能有非本流程的覆盖，人工核对 `verify` 输出再处理（可按 `--uids` 定向删） |
| 登录失败 | 确认 MOODLE_USER/PASSWORD 有效（别连试错锁号）；或改用 MOODLE_COOKIE |

## 实战记录

- 2026-09-15 quiz 266（AI认证实操）：截止 09:59 后仍有 24 份"进行中"（其中 4 份有作答内容）。
  流程：加覆盖（24 人，截止 12:00）→ 代交 20 份（另 4 份在批量前已自行完成）→ 最终 277 份全部"已结束"、进行中 0 → 删覆盖 24 条成功（列表 0）。
  附件完好（1/1/7/3 个）；期间 1 名考生窗口内新开一份空卷（7375，0 分，不影响其有效卷评分）。
  现场脚本与日志：`D:\opencode\file\2026-09-15\`（m*.py / m*_output.txt / m*_log.jsonl）。
