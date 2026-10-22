---
name: daily-work-log
description: 当日工作面板填报与日志格式规则。把当日完成的工作写入内网「当日工作面板」（每天 18:20 自动整理成日报推钉钉）。Use when 用户说"记录工作/写今日总结/更新工作面板/写日报/记录到面板/总结今日工作"，或要求按「分组，序号、内容」格式整理工作记录。
metadata:
  version: 1.0.0
  author: majianquan
  category: global
  visibility: global
---

# daily-work-log：当日工作面板填报

## 面板

- 地址：`http://100.103.28.84:8765/input?key=AhXDXgGlwjFarWup`
- `day=YYMMDD`（当天）。**每天 18:20 面板自动把当日内容整理成日报推钉钉——18:20 前写好。**

## 读写接口

- 读：`GET /input?key=...`（返回 HTML；`freeform` = 「其它工作」textarea；另有待办勾选区 `done_*` / 进展 `prog_*` 字段）
- 写：`POST /submit-input`，form-urlencoded 三字段：`key` / `day` / `freeform`

## 硬规则（踩过坑的）

1. **编码必须 UTF-8**：Windows 下 curl 会按本地 GBK 发送中文 → 面板全文乱码。用 python `urllib.parse.urlencode(...)`（自动 utf-8）或预先编码好的 `--data-binary @file`。
2. **超时 ≠ 失败**：`/submit-input` 处理慢（常见 40 秒无响应超时），数据实际已保存。提交后必须 `GET /input` 回读验证（中文正常 + 内容为最新一版）。
3. **记录格式（用户拍板 2026-10-22）**：每条记录 = `分组名，序号、内容`
   - 逗号**前**是工作分组（已知分组：`AI提效-售前工作台`；其他分组以用户当日说明为准）；
   - 逗号后写序号「1、2、…」；多条工作 = 多条记录（各自带分组与序号）；
   - 每条 30-50 字：只写核心成果（可带提交号），不写过程、不逐条罗列细节。
4. **写前先读**：续写追加，不覆盖用户已手工修改的内容；待办勾选区（`done_*`/`prog_*`）属用户个人待办，未经用户明确指示不勾选、不改动。
5. 写后回读确认内容与编码。

## 提交模板（规避编码坑）

```python
import urllib.parse, urllib.request
text = "AI提效-售前工作台，1、……"
body = urllib.parse.urlencode({
    "key": "AhXDXgGlwjFarWup", "day": "YYMMDD", "freeform": text,
}).encode("utf-8")
urllib.request.urlopen(urllib.request.Request(
    "http://100.103.28.84:8765/submit-input", data=body,
    headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=8)
# 这里大概率超时——属正常，回读 /input 验证即可
```

## 示例

```
AI提效-售前工作台，1、修复公司介绍误引友商材料事故（检索排除+主体锁定），模型链五级重排接入WorkBuddy，主模型切deepseek-v4.1-flash
```
