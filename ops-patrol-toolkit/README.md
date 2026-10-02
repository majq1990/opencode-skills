# ops-patrol-toolkit · 运维巡检与故障排查工具集（R48）

工程技术中心通用 Skill。四个子工具可独立调用，零第三方依赖，离线可跑。

## 能力一览

| 编号 | 能力 | 入口 | 输入 | 输出 |
|---|---|---|---|---|
| 01 | 巡查三源汇总 | `scripts/01_patrol_merge.py` | 人巡/机巡/部件 xlsx 或 csv | 统一 9 列明细表（xlsx/csv） |
| 02 | MySQL 高 I/O 分诊 | `scripts/02_mysql_io_triage.py` | iostat / digest / DDL 文本 | report.md + triage.json |
| 03 | 维护手册规范化 | `scripts/03_manual_standardize.py` | 立项资料 docx + 项目信息 json | 手册初稿 docx + 差异清单 md |
| 04 | 月度运维报告 | `scripts/04_monthly_report.py` | servers.json + 统计 json + Word 模板 | 巡检状态 json + 月报 docx |
| 05 | 历史相似案例检索 | `scripts/05_kb_similar_search.py` | 症状描述或 02 的 triage.json | 历史工单/知识库案例报告 md（联网，需 token 环境变量） |
| 公共 | 脱敏 | `scripts/redact.py` | 任意文本材料 | 脱敏后文本 |

## 自测

```bash
python -m pytest tests/ -p no:cacheprovider -q
```

全部用例离线合成数据，不连任何真实系统。

## 设计原则

- **零依赖**：xlsx/docx 读写为自研 OOXML 实现（`scripts/xlsx_io.py`、`scripts/docx_io.py`）
- **gap-stop**：缺前置条件输出 `{"ok": false, "gap": "..."}` 并退出码 2，不静默兜底
- **模板/配置永不改写**：产物只写 `work/` 或显式 `--out`
- **报告默认【待复核】**：未经人工复核不得外发
- **换项目只改配置**：字段签名、巡检清单、阈值、月报映射全部外置 `config/patrol/`

## 版本历史

- 1.0.0（2026-10）：四子工具首发；公共库 patrol_lib/xlsx_io/docx_io/redact；合成 fixtures 离线自测。
