# Moodle 笔试成绩回填

## 输入

优先接收 Moodle overview 地址：

```text
http://onekey.egova.com.cn:8888/mod/quiz/report.php?id=<quizid>&mode=overview
```

如果用户给的是 `view.php?id=<quizid>`，转换为 overview 报表地址。

## 抓取流程

1. 访问登录页并检查是否已登录；未登录时用当前已知 Moodle 管理账号或提示用户登录。
2. 打开 overview 报表，确认标题和 quiz id。
3. 从下载表单提取 `sesskey`。
4. 下载 `download=csv`，必要时同时下载 `download=json`。
5. 解析列：`名`、`电子邮件地址`、`状态`、`完成`、`评分/100.00`。

## 匹配规则

- 默认按人员名单中的姓名精确匹配 Moodle `名` 字段。
- 同名、重复记录、多个 attempt 时列出候选；不要静默取最高分，除非用户确认口径。
- 总表中人员无 Moodle 成绩时，笔试分数留空，并输出未匹配名单。
- 实操未作答但 Moodle 有笔试成绩时，照常写入笔试分数。

## 写表规则

- 只写总表 `笔试分数` 列，不覆盖实操公式和综合公式。
- 写入后跑公式校验。
- 输出 Moodle 记录数、匹配数、未匹配人员、重复姓名。
