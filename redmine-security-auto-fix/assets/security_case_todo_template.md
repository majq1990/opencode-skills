# {{project}} 安全案件待办清单（{{date}}）

> 状态：**{{status}}** ｜ 共 {{case_count}} 项，按责任人分组
> 回复口径：案件号 + 处置动作 + 预计完成时间；完成后在 `work/security_case/progress/progress_{{date}}.json` 回填 `status=fixed`
> 推送规则：必须经人工复核后先推送测试目标（config/security_case/notify.json），缺确认只预览

## 一、按责任人分组

{{todo_blocks}}

## 二、未定责事项（需人工确认归属）

{{unmapped_blocks}}

## 三、时限口径

{{sla_block}}

## 四、次日自动跟踪

- `scripts/track_case_state.py --date {{next_date}}` 自动生成超期 / 进行中 / 待验证三类提醒
- 超期案件：升级标记并同步给资产责任人及直属主管（由人工决定是否上报）

---

生成脚本：`scripts/gen_security_report.py` ｜ 待复核后经 `scripts/notify_dingtalk.py` / 钉钉机器人推送（测试目标先行）
