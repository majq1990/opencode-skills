---
name: memory-2026-07-27-wukong-exam-automation-skill
description: [memory] Personal memory: 2026-07-27-wukong-exam-automation-skill
---

# 2026-07-27 悟空考核自动化 skill 封装

已将悟空 3.0 认证考核自动化封装为 `wukong-exam-automation`。

## 新入口

- Git skill 仓：`D:\git\opencode-skills\wukong-exam-automation`
- OpenCode skill 目录：`D:\opencode\config\skills\wukong-exam-automation`
- 旧入口 `wukong-exam-env` 已归档，说明新任务改用 `wukong-exam-automation`。

## 能力边界

输入为：考核人员名单、考核开始/结束时间、笔试 Moodle overview 地址、原始阅卷模板/评分表、输出位置。

默认流程：考前读取人员名单、采购 cn-wlcb 悟空 ECS（包年包月 1 周）、初始化悟空服务器、录入考生账号；考后 30 分钟改密、查询无页面无项目账号、拉取 Moodle 笔试成绩、复制原始阅卷模板并输出阅卷分配表。

## 重要经验

- 阅卷表必须直接复制原始模板，不要重建阅卷细表。
- 笔试地址作为必填输入之一。
- `wukong-exam-env` 不是删除，而是归档跳转，避免破坏历史入口。
- 执行 ECS 采购、改密、释放实例、批量写表前必须展示目标、范围和影响。
