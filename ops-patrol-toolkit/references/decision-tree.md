# 02 · MySQL 只读副本高 I/O 分诊决策树

输入：iostat 物理画像 + 慢查询 digest 逻辑画像 + 表 DDL 结构画像
输出：有序的根因候选（主因 + 备选），每条带证据链与置信度

> **阈值外置约定**：本文出现的所有判定阈值统一维护在 `config/patrol/triage_thresholds.json`
> （`triggers`=触发条件 / `scoring`=基础打分 / `digest_bump`、`ddl_bump`=佐证加权 /
> `confidence`=置信度口径 / `judges`=画像分级 / `aggregate`=设备聚合口径）。
> 括号内标注的是配置键与当前默认值，两者不一致时以配置文件为准；
> 调整数值须同步更新配置的 `version`/`updated` 并复核本文语义。
>
> 本决策树逻辑移植自内部评审入选样例工程（已脱敏），阈值口径保持近保真。

## 总流程

```
iostat 解析（多轮采样取最后一轮；吞吐单位自动识别 kB/s 或 MB/s 并统一换算 MB/s）
   ├─ 平均单次读 < 32KB 且 读 IOPS ≥ 500  ──► [A] 随机小块读
   │    (triggers.random_read.avg_read_kb_lt=32 / read_iops_gte=500)
   ├─ 平均单次读 ≥ 64KB 且 读吞吐 ≥ 20MB/s ──► [B] 大块顺序读
   │    (triggers.large_seq_scan.avg_read_kb_gte=64 / read_mbs_gte=20)
   ├─ 写 IOPS ≥ 200 或 写吞吐 ≥ 10MB/s 或 读吞吐占比 < 60% ──► [C] 写入压力
   │    (triggers.write_pressure.write_iops_gte=200 / write_mbs_gte=10 / read_mb_share_lt=60)
   ├─ %util ≥ 85 或 r_await ≥ 10ms        ──► [D] 设备饱和
   │    (triggers.device_saturation.util_gte=85 / r_await_gte=10)
   └─ iowait ≥ 15% 但 IOPS < 500 且吞吐 < 20MB/s ──► [E] 量级不匹配
        (triggers.mismatch_low_io.iowait_gte=15 / iops_lt=500 / mbs_lt=20)
                    │
                    ▼
digest 佐证（加权，见配置 digest_bump）
   ├─ SUM_NO_INDEX_USED > 0      → 加权 [B]、[A]
   ├─ 磁盘临时表 > 0             → 加权 [C]
   ├─ 扫描放大比 > 100           → 加权 [A]、[B]（digest_bump.scan_ratio_gt=100）
   └─ TOP SQL 定位具体语句与表
                    │
                    ▼
DDL 结构佐证（加权，见配置 ddl_bump）
   ├─ 含 TEXT/BLOB 大字段        → 加权 [A]（溢出页随机读）
   ├─ 无显式主键                 → 加权 [A]（回表成本）
   └─ 索引数量 ≤ 1               → 加权 [B]（易全扫；ddl_bump.index_few_max=1）
                    │
                    ▼
            按 score 排序 → 主因 + 置信度
```

## 各分支的判定逻辑与典型处置

### [A] 随机小块读主导 · 回表/点查放大

**特征**：读 IOPS 高、单次读小（<32KB）、`r_await` 抬升、吞吐中等。
**常见成因**：
1. 二级索引过滤后大量回表（尤其 `SELECT *`）
2. 索引失效后的逐行扫描（隐式类型转换、函数包裹列、字符集/排序规则不一致）
3. 热点数据超出 buffer pool，命中率下降
4. 大字段（TEXT/BLOB）溢出页读取

**佐证动作**（人工）：`EXPLAIN` 看 `key`/`rows`/`Extra`；查 `Handler_read_*` 状态；看 buffer pool 命中率。
**处置方向**：覆盖索引、按需取列、修正类型/字符集、扩容内存或拆分查询。

### [B] 大块顺序读主导 · 全表扫描/大范围扫描

**特征**：`rMB/s` 高、单次读大（≥64KB）、IOPS 中等。
**常见成因**：无合适索引的全扫、大范围时间扫、备份/导出任务、统计类聚合。
**佐证动作**：`SHOW FULL PROCESSLIST`；`EXPLAIN` 看 `type=ALL`；确认同机是否有备份任务。
**处置方向**：复合索引、限制扫描范围（分区/游标）、错峰备份。

### [C] 写入压力显著 · 临时表落盘/复制回放

**特征**：写 IOPS 或写吞吐占比高、`w_await` 抬升。
**注意**：只读副本上写入来源与主库不同——RO 不产生业务写，
主要来自 **relay log 落盘与回放**、**磁盘临时表**、**排序/连接缓冲区落盘**。
**佐证动作**：`Created_tmp_disk_tables`、`Sort_merge_passes`、`Slave_SQL_Running_State`。
**处置方向**：优化触发落盘的 SQL；缓冲区参数调整（必须测试环境验证）；区分复制回放压力。

### [D] 设备接近饱和 · 队列积压

**特征**：`%util` ≥ 85%、`avgqu-sz` 大、`await` 明显抬升。
**注意**：`%util` 100% 不等于性能耗尽（SSD/RAID 可并行），必须结合 `await` 与队列深度。
**处置方向**：先降需求（优化 SQL/索引）再谈扩容；排查云盘突发配额耗尽。

### [E] iowait 高但 I/O 量不大

**特征**：iowait 高，但 IOPS/吞吐都很低。
**这是最容易误判的一支**——不能直接下结论说"磁盘压力大"。
**佐证动作**：`iotop` / `pidstat -d` 定位进程；检查磁盘健康与 RAID 缓存策略；
核对采样窗口是否与告警窗口对齐。

## 置信度口径

配置节：`confidence`（high_evidence=3 / high_gap=1.0 / mid_evidence=2 / mid_gap=0.5）。

| 条件 | 置信度 |
|---|---|
| 证据 ≥3 条 且 与次因分差 ≥1.0 | 高 |
| 证据 ≥2 条 或 分差 ≥0.5 | 中 |
| 其他 | 低 |

**置信度是给复核人的提示，不是结论正确性保证。**
任何置信度的结论都必须经 DBA 现场复核后才能作为处置依据；
工具产出的报告一律带【待复核】标记，未经人工复核不得外发。

## 打分口径（score 怎么来的）

1. **基础分**（配置节 `scoring`）：`min(量级/除数, 上限) + 读大小加成`
   - [A] `min(读IOPS/2000, 4.0)`，平均读 <16KB 再 +2.0
   - [B] `min(读吞吐/50, 4.0)`，平均读 ≥128KB 再 +2.0
   - [C] `min(写吞吐/20, 4.0) + min(写IOPS/500, 2.0)`
   - [D] `min(%util/25, 4.0)`
   - [E] `min(iowait/8, 3.0)`
2. **佐证加权**（配置节 `digest_bump`/`ddl_bump`）：只对**已触发**的候选加分并追加证据。
3. 总分取两位小数，降序排列；与次因的分差参与置信度判定。

## digest TOP 排序口径

配置节 `digest_rank_weights`：
`score = rows_examined + tmp_disk_tables×5000 + no_index_used×1000 + sort_rows×0.5`，
降序取 TOP N（默认 10，`--top` 可调）。

## 反模式（本工具明确禁止）

- 只看 iowait 就下结论 —— 必须落到具体设备、具体 SQL
- 只看单轮 iostat —— 必须与告警窗口对齐，最好多轮
- 把 dm-* 与底层盘重复相加 —— 会得出翻倍的 IOPS（工具已按 `aggregate.exclude_device_prefixes` 排除）
- 把「建议」当「可执行指令」—— 加索引/改参数都必须走变更流程
- 直接把报告外发给客户/上游 —— 必须先经 DBA 复核，且确认材料已用 `scripts/redact.py` 脱敏
