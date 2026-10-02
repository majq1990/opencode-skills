#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_mysql_io_triage · MySQL 只读副本高 I/O 分诊（ops-patrol-toolkit 子工具 02）

只读工具链：解析 iostat / 慢查询 digest / 表 DDL，判定 MySQL 只读副本磁盘高 I/O
的根因候选并生成中文诊断报告。判定逻辑移植自内部评审入选样例工程 io_triage v1.0.0
（已脱敏），并按本仓库契约改造：
  - 全部判定阈值外置到 config/patrol/triage_thresholds.json（带治理元数据），代码不写死
  - stdout 最后一行固定为 JSON 信封：成功 {"ok": true, ...}；失败 {"ok": false, "gap": "..."}
    并以退出码 2 结束
  - 报告标题带【待复核】标记：结论未经 DBA 人工复核不得外发

安全约束（代码层面强制）：
  - 本脚本不导入任何数据库驱动，不建立任何网络连接
  - 只读取 --iostat/--digest/--ddl/--meta 指定的文件
  - 只写入 --out 指定的输出目录（缺省写入 work/io_triage）
  - 不产出、不执行任何 DDL / DML / KILL / SET GLOBAL

用法:
  python scripts/02_mysql_io_triage.py run --iostat X [--digest Y] [--ddl Z] [--meta M] [--top 10] [--out DIR]
  python scripts/02_mysql_io_triage.py parse-iostat --iostat X
  python scripts/02_mysql_io_triage.py analyze-digest --digest Y [--top 10]
  python scripts/02_mysql_io_triage.py analyze-ddl --ddl Z
"""

import argparse
import json
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

# 允许以 `python scripts/02_mysql_io_triage.py ...` 从任意工作目录直接运行：
# 先把本脚本所在的 scripts/ 目录加进 sys.path，再 import 公共库
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import patrol_lib  # noqa: E402  公共库：信封(emit/stop)/路径(skill_path/work_path)/退出码

__version__ = "1.0.0"

_TH_CACHE = None


def load_thresholds(refresh=False):
    """加载外置阈值 config/patrol/triage_thresholds.json（进程内缓存一份）。

    约定：triage() 里的判定阈值/打分权重/分级口径一律不写死在代码里，改数值只改配置。
    配置缺失或 JSON 损坏时由 patrol_lib 直接 gap 停机（退出码 2），不做静默兜底。
    """
    global _TH_CACHE
    if _TH_CACHE is None or refresh:
        _TH_CACHE = patrol_lib.load_config("triage_thresholds")
    return _TH_CACHE


# ---------------------------------------------------------------- 基础工具


def read_text(path):
    """只读方式读入参文件。

    utf-8-sig：现场导出的 CSV 常带 BOM，会让首列名变成 ﻿xxx 而匹配不上（源样例踩过的坑）。
    """
    if not path:
        return None
    if not os.path.isfile(path):
        patrol_lib.stop("输入文件不存在: %s（请确认材料路径；生产材料须先用 scripts/redact.py 脱敏）" % path)
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def human_mb(mb):
    if mb >= 1024:
        return "%.2f GB/s" % (mb / 1024.0)
    return "%.2f MB/s" % mb


# ---------------------------------------------------------------- iostat 解析

# 表头里可能出现的列名 -> 内部字段名。注意：key 必须全小写，查找时会统一 lower。
# 这是列名映射（schema），不属于数值阈值，故保留在代码里。
IOSTAT_COLS = {
    "device": "dev", "dev": "dev",
    "r/s": "r_s", "w/s": "w_s",
    "rkb/s": "r_kb", "rmb/s": "r_mb",
    "rkB/s".lower(): "r_kb", "rMB/s".lower(): "r_mb",
    "wkb/s": "w_kb", "wmb/s": "w_mb",
    "wkB/s".lower(): "w_kb", "wMB/s".lower(): "w_mb",
    "rrqm/s": "rrqm", "wrqm/s": "wrqm",
    "avgrq-sz": "avgrq_sz", "avgqu-sz": "avgqu_sz",
    "await": "await", "r_await": "r_await", "w_await": "w_await",
    "svctm": "svctm", "%util": "util",
    "rareq-sz": "rareq_sz", "wareq-sz": "wareq_sz",
}

UNIT_KB = "kB/s"
UNIT_MB = "MB/s"


def _is_num(tok):
    try:
        float(tok)
        return True
    except (TypeError, ValueError):
        return False


def parse_iostat(text):
    """解析 iostat -x (/-m/-k) 输出。

    设计要点（源样例踩过坑的地方，近保真保留）：
      - 不按空行分块：iostat 的 avg-cpu 段与 Device 段被空行隔开，
        分块会导致 CPU 行与设备行落在不同块里而互相丢失。改为全文线性扫描。
      - 多轮采样（iostat -xmt 1 N）取「最后一轮」：即最后一个 Device 表头
        及其后连续的数据行，最能代表当下状态。
      - 自动识别吞吐单位（rkB/s vs rMB/s，对应 -k / -m）。
      - 设备名不以数字开头，不能靠首字符判断是否为数据行。
    """
    if not text:
        patrol_lib.stop("iostat 内容为空：请提供含 Device 段的 iostat -x 采样文本（建议多轮采样 3 轮以上）")

    lines = [ln.rstrip("\n") for ln in text.splitlines()]

    # --- CPU：全文找所有 avg-cpu 后的首个纯数值行，取最后一个
    cpu = {}
    samples = 0
    for i, ln in enumerate(lines):
        if ln.strip().lower().startswith("avg-cpu"):
            samples += 1
            for j in range(i + 1, min(i + 4, len(lines))):
                s = lines[j].strip()
                if s == "" or "%" in s:
                    if s == "":
                        break
                    continue
                toks = s.split()
                if len(toks) >= 6 and all(_is_num(t) for t in toks):
                    keys = ["user", "nice", "system", "iowait", "steal", "idle"]
                    cpu = {k: float(v) for k, v in zip(keys, toks[:6])}
                    break
            # 继续向后找，最终保留最后一次

    # --- Device：找所有表头，取最后一个
    hdr_idx = None
    for i, ln in enumerate(lines):
        s = ln.strip().lower()
        if s.startswith("device") or s.startswith("dev"):
            hdr_idx = i
    if hdr_idx is None:
        patrol_lib.stop("未能从 iostat 输入中识别设备段：确认文件包含 'Device:' 表头与数据行（iostat -x 输出）")

    head_parts = lines[hdr_idx].strip().split()
    head_parts[0] = head_parts[0].strip(":")
    unit = None
    for h in head_parts[1:]:
        hl = h.lower()
        if hl.startswith("r") and hl.endswith(("/s", "b/s")) and ("kb" in hl or "mb" in hl):
            unit = UNIT_MB if "mb" in hl else UNIT_KB

    rows = []
    for ln in lines[hdr_idx + 1:]:
        s = ln.strip()
        if s == "":
            # 数据行结束后遇到空行即停止（空行后出现的是下一轮 avg-cpu）
            if rows:
                break
            continue
        parts = s.split()
        if len(parts) < 3:
            continue
        if parts[0].lower().startswith(("device", "dev", "avg-cpu")):
            break
        # 数据行：第一列是设备名，其余应基本为数值
        if not all(_is_num(p) for p in parts[1:]):
            continue
        rows.append(parts)

    if not rows:
        patrol_lib.stop("iostat 设备表头之后没有解析到数据行：确认采样文件完整、未被截断")

    devices = []
    for parts in rows:
        rec = {"dev": parts[0]}
        for i, h in enumerate(head_parts[1:], start=1):
            if i < len(parts):
                rec[h] = parts[i]
        devices.append(_normalize_dev(rec, unit))

    return {
        "cpu": cpu,
        "devices": devices,
        "samples": samples or 1,
        "unit": unit or UNIT_KB,
        "header": " ".join(head_parts),
    }


def _normalize_dev(rec, unit):
    """把原始列映射成统一字段，吞吐统一换算成 MB/s。"""
    out = {"dev": rec.get("dev", "?")}
    for k, v in rec.items():
        key = IOSTAT_COLS.get(k.lower())
        if key and key != "dev":
            out[key] = _to_f(v)

    # 吞吐单位归一
    if "r_mb" in out:
        out["r_mbs"] = out["r_mb"]
    elif "r_kb" in out:
        out["r_mbs"] = out["r_kb"] / 1024.0
    if "w_mb" in out:
        out["w_mbs"] = out["w_mb"]
    elif "w_kb" in out:
        out["w_mbs"] = out["w_kb"] / 1024.0

    out.setdefault("r_s", 0.0)
    out.setdefault("w_s", 0.0)
    out.setdefault("r_mbs", 0.0)
    out.setdefault("w_mbs", 0.0)
    out.setdefault("await", 0.0)
    out.setdefault("r_await", 0.0)
    out.setdefault("w_await", 0.0)
    out.setdefault("util", 0.0)
    out.setdefault("avgqu_sz", 0.0)
    out.setdefault("avgrq_sz", 0.0)
    return out


def _to_f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def aggregate_devices(devices, exclude=None):
    """汇总设备，并挑出「主压力设备」。

    聚合策略（源样例踩坑保留）：排除虚拟/光驱设备；若存在 dm-* 与底层 sd*/vd* 重复，
    以 IOPS 最高的设备为准做展示，其余保留在明细里——把 dm-* 与底层盘相加会得出
    翻倍的 IOPS。排除前缀外置在配置 aggregate.exclude_device_prefixes。
    """
    if exclude is None:
        exclude = tuple(load_thresholds()["aggregate"]["exclude_device_prefixes"])
    real = [d for d in devices if not any(d["dev"].startswith(p) for p in exclude)]
    pool = real if real else devices
    if not pool:
        patrol_lib.stop("iostat 设备列表为空：确认采样文件里至少有一个物理设备的数据行")

    tot = {
        "r_s": sum(d["r_s"] for d in pool),
        "w_s": sum(d["w_s"] for d in pool),
        "r_mbs": sum(d["r_mbs"] for d in pool),
        "w_mbs": sum(d["w_mbs"] for d in pool),
    }
    tot["iops"] = tot["r_s"] + tot["w_s"]
    tot["mbs"] = tot["r_mbs"] + tot["w_mbs"]

    # 主压力设备：按 IOPS 贡献
    hot = max(pool, key=lambda d: (d["r_s"] + d["w_s"], d["util"]))
    tot["hot_dev"] = hot["dev"]
    tot["hot_util"] = hot["util"]
    tot["hot_await"] = hot["await"]
    tot["hot_r_await"] = hot["r_await"]
    tot["hot_w_await"] = hot["w_await"]
    tot["hot_avgqu_sz"] = hot["avgqu_sz"]

    # 平均 IO 大小（KB）：吞吐 / IOPS
    if tot["r_s"] > 0:
        tot["avg_read_kb"] = tot["r_mbs"] * 1024.0 / tot["r_s"]
    else:
        tot["avg_read_kb"] = 0.0
    if tot["w_s"] > 0:
        tot["avg_write_kb"] = tot["w_mbs"] * 1024.0 / tot["w_s"]
    else:
        tot["avg_write_kb"] = 0.0

    tot["read_iops_share"] = (tot["r_s"] / tot["iops"] * 100.0) if tot["iops"] else 0.0
    tot["read_mb_share"] = (tot["r_mbs"] / tot["mbs"] * 100.0) if tot["mbs"] else 0.0
    return tot


# ---------------------------------------------------------------- digest 解析

# 常见列名（performance_schema / pt-query-digest / 自定义导出）-> 内部字段。
# 同样属于列名映射（schema），保留在代码里。
DIGEST_ALIASES = {
    "digest": "digest", "digest_text": "sql", "query": "sql", "sql": "sql",
    "sql_text": "sql", "语句": "sql", "sql指纹": "sql",
    "schema_name": "schema", "db": "schema", "库": "schema",
    "count_star": "exec_count", "exec_count": "exec_count", "count": "exec_count",
    "执行次数": "exec_count",
    "sum_timer_wait": "sum_latency_ps", "sum_latency": "sum_latency_ps",
    "avg_timer_wait": "avg_latency_ps", "avg_latency": "avg_latency_ps",
    "平均耗时": "avg_latency_ps",
    "sum_rows_examined": "rows_examined", "rows_examined": "rows_examined",
    "扫描行数": "rows_examined",
    "sum_rows_sent": "rows_sent", "rows_sent": "rows_sent", "返回行数": "rows_sent",
    "sum_rows_affected": "rows_affected",
    "sum_created_tmp_disk_tables": "tmp_disk_tables", "tmp_disk_tables": "tmp_disk_tables",
    "磁盘临时表": "tmp_disk_tables",
    "sum_created_tmp_tables": "tmp_tables", "临时表": "tmp_tables",
    "sum_sort_rows": "sort_rows", "排序行数": "sort_rows",
    "sum_no_index_used": "no_index_used", "no_index_used": "no_index_used",
    "无索引": "no_index_used",
    "sum_no_good_index_used": "no_good_index",
    "sum_select_scan": "select_scan", "全表扫描次数": "select_scan",
}


def _detect_delim(line):
    if "\t" in line:
        return "\t"
    if "," in line:
        return ","
    if "|" in line:
        return "|"
    return None


def parse_digest(text):
    """解析慢查询 digest，支持 CSV / TSV / 管道分隔 / JSON 数组。

    返回 list[dict]，字段已归一化； latency 单位统一换算成「秒」。
    """
    if not text:
        return []
    s = text.strip()
    if s.startswith("["):
        try:
            arr = json.loads(s)
        except json.JSONDecodeError as e:
            patrol_lib.stop("digest JSON 解析失败: %s（应为 JSON 数组，或改用 CSV/TSV/管道分隔文本）" % e)
        return [_norm_digest_row(r) for r in arr if isinstance(r, dict)]

    lines = [ln for ln in s.splitlines() if ln.strip()]
    if not lines:
        return []
    delim = _detect_delim(lines[0])
    if not delim:
        patrol_lib.stop("digest 无法识别分隔符：支持 CSV/TSV/管道分隔/JSON 数组，请检查首行列格式")

    # 用 csv 模块而不是 split：SQL 指纹里含逗号/引号是常态，
    # 直接 split 会导致列错位（源样例踩坑保留）。quotechar 支持双引号包裹。
    import csv as _csv
    import io as _io
    reader = _csv.reader(_io.StringIO(s), delimiter=delim, quotechar='"')
    table = [r for r in reader if any(c.strip() for c in r)]
    if not table:
        return []
    header = [h.strip().strip('"').strip("'") for h in table[0]]

    fields = []
    for h in header:
        key = h.lower().replace(" ", "_")
        fields.append(DIGEST_ALIASES.get(key, DIGEST_ALIASES.get(h.lower(), h)))

    rows = []
    for vals in table[1:]:
        if len(vals) < len(fields):
            vals = vals + [""] * (len(fields) - len(vals))
        rec = {fields[i]: vals[i] for i in range(len(fields))}
        rows.append(_norm_digest_row(rec))
    rows = [r for r in rows if r.get("sql") or r.get("rows_examined")]
    return rows


def _norm_digest_row(rec):
    out = dict(rec)
    for k in ("exec_count", "rows_examined", "rows_sent", "tmp_disk_tables",
              "tmp_tables", "sort_rows", "no_index_used", "no_good_index",
              "select_scan", "rows_affected"):
        out[k] = _to_f(rec.get(k, 0))
    # 延迟：picosecond -> 秒；单位判断阈值外置在配置 digest_norm
    # （除数 1e12/1e3 是固定单位换算，保留在代码）
    ln_th = load_thresholds()["digest_norm"]
    for src, dst in (("sum_latency_ps", "sum_latency_s"),
                     ("avg_latency_ps", "avg_latency_s")):
        v = _to_f(rec.get(src, 0))
        if v > ln_th["picosecond_gt"]:       # picosecond
            out[dst] = v / 1e12
        elif v > ln_th["millisecond_gt"]:    # 毫秒
            out[dst] = v / 1e3
        else:                                # 已近似为秒
            out[dst] = v
    # 扫描放大比
    ex = out.get("rows_examined", 0.0)
    se = out.get("rows_sent", 0.0)
    out["scan_ratio"] = (ex / se) if se > 0 else (ex if ex > 0 else 0.0)
    out["examined_per_exec"] = (ex / out["exec_count"]) if out.get("exec_count") else 0.0
    return out


def rank_digest(rows, top=10):
    """按「对磁盘的逻辑读压力」排序。

    主序：sum(rows_examined)；次序：磁盘临时表 + 无索引 + 排序行数。
    权重外置在配置 digest_rank_weights。
    """
    w = load_thresholds()["digest_rank_weights"]

    def score(r):
        return (r.get("rows_examined", 0.0)
                + r.get("tmp_disk_tables", 0.0) * w["tmp_disk_tables"]
                + r.get("no_index_used", 0.0) * w["no_index_used"]
                + r.get("sort_rows", 0.0) * w["sort_rows"])
    ranked = sorted(rows, key=score, reverse=True)
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    return ranked[:top]


# ---------------------------------------------------------------- DDL 解析


def parse_ddl(text):
    """极简 DDL 解析：抽出表名、引擎、行格式、字段、索引、大字段。

    只做正则级的尽力解析，不做完整 SQL 语法分析；解析失败会降级并标注。
    """
    if not text:
        return {}
    tables = OrderedDict()
    # 逐个 CREATE TABLE 块
    chunks = re.split(r"(?im)^\s*CREATE\s+TABLE\s+", text)
    for ch in chunks[1:]:
        m = re.match(r"(?:IF\s+NOT\s+EXISTS\s+)?`?([\w$.]+)`?", ch)
        if not m:
            continue
        tname = m.group(1).strip("`").split(".")[-1]
        body = ch[m.end():]
        end = body.find(";")
        if end > 0:
            body = body[:end]
        # 去掉行注释
        body = re.sub(r"--[^\n]*", "", body)

        cols, idx = [], []
        depth = 0
        buf = ""
        for c in body:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            if c == "," and depth == 1:
                seg = buf.strip()
                buf = ""
                if seg:
                    (idx if re.match(r"(?i)^(primary|unique|key|index|fulltext|constraint)", seg) else cols).append(seg)
            else:
                buf += c
        if buf.strip():
            seg = buf.strip()
            (idx if re.match(r"(?i)^(primary|unique|key|index|fulltext|constraint)", seg) else cols).append(seg)

        fields = []
        for c in cols:
            cm = re.match(r"(?i)^`?([\w$]+)`?\s+([a-z]+)", c.strip())
            if not cm:
                continue
            fname, ftype = cm.group(1), cm.group(2).lower()
            fields.append({
                "name": fname,
                "type": ftype,
                "is_lob": ftype in ("text", "mediumtext", "longtext", "blob",
                                    "mediumblob", "longblob", "json"),
                "is_big_varchar": bool(re.search(r"(?i)varchar\s*\(\s*(\d{3,})\s*\)", c)),
            })

        eng = re.search(r"(?i)ENGINE\s*=\s*(\w+)", body)
        rowf = re.search(r"(?i)ROW_FORMAT\s*=\s*(\w+)", body)
        cs = re.search(r"(?i)(?:DEFAULT\s+)?CHARSET\s*=\s*(\w+)", body)
        pk = [i for i in idx if re.match(r"(?i)^primary", i.strip())]
        tables[tname] = {
            "engine": eng.group(1) if eng else None,
            "row_format": rowf.group(1) if rowf else None,
            "charset": cs.group(1) if cs else None,
            "field_count": len(fields),
            "lob_fields": [f["name"] for f in fields if f["is_lob"]],
            "big_varchar": [f["name"] for f in fields if f["is_big_varchar"]],
            "indexes": [i.strip() for i in idx],
            "has_pk": bool(pk),
        }
    return tables


def match_tables(sql, tables):
    """从 SQL 文本里粗略匹配涉及到的表（用于 DDL 佐证）。"""
    if not sql or not tables:
        return []
    found = []
    low = sql.lower()
    for t in tables:
        if re.search(r"(?i)\b%s\b" % re.escape(t.lower()), low):
            found.append(t)
    return found


# ---------------------------------------------------------------- 根因判定


def triage(io, cpu, top_sql, tables, meta):
    """按决策树给出根因候选 + 置信度 + 证据链。

    所有判定阈值/打分权重/佐证加权来自外置配置（triggers/scoring/digest_bump/
    ddl_bump/confidence）。返回 list[dict]，按 score 降序；
    每项含 key/name/score/confidence/evidence/suggestion。
    """
    th = load_thresholds()
    tg = th["triggers"]
    sc = th["scoring"]
    db = th["digest_bump"]
    dlb = th["ddl_bump"]
    cf = th["confidence"]

    cands = []
    iops = io["iops"]
    mbs = io["mbs"]
    r_mbs, w_mbs = io["r_mbs"], io["w_mbs"]
    avg_read_kb = io["avg_read_kb"]
    util = io["hot_util"]
    r_await = io["hot_r_await"] or io["hot_await"]
    iowait = cpu.get("iowait", 0.0)

    # --- 证据构造辅助
    def ev(*items):
        return [i for i in items if i]

    # 1) 随机小块读主导 → 二级索引回表 / 点查放大
    if (io["r_s"] > 0 and avg_read_kb
            and avg_read_kb < tg["random_read"]["avg_read_kb_lt"]
            and io["r_s"] >= tg["random_read"]["read_iops_gte"]):
        cands.append({
            "key": "random_read_amplification",
            "name": "随机小块读主导 · 二级索引回表/点查放大",
            "score": 0,
            "evidence": ev(
                "读 IOPS %.0f，平均单次读仅 %.1f KB（小块随机特征）" % (io["r_s"], avg_read_kb),
                "读 IOPS 占比 %.1f%%" % io["read_iops_share"],
                ("读等待 r_await=%.2f ms" % r_await) if r_await else None,
            ),
            "suggestion": [
                "核查 TOP SQL 是否 SELECT * 或取了未覆盖的列，改为覆盖索引或按需取列",
                "确认过滤条件是否命中索引最左前缀，避免索引失效后回表放大",
                "评估热点数据是否已超出 buffer pool，考虑扩容内存或拆分大查询",
            ],
        })

    # 2) 大块顺序读 → 全表扫描 / 大范围扫描 / 备份
    if (avg_read_kb and avg_read_kb >= tg["large_seq_scan"]["avg_read_kb_gte"]
            and r_mbs >= tg["large_seq_scan"]["read_mbs_gte"]):
        cands.append({
            "key": "large_seq_scan",
            "name": "大块顺序读主导 · 全表扫描/大范围扫描",
            "score": 0,
            "evidence": ev(
                "平均单次读 %.1f KB（大块顺序特征），读吞吐 %s" % (avg_read_kb, human_mb(r_mbs)),
                "读吞吐占比 %.1f%%" % io["read_mb_share"],
            ),
            "suggestion": [
                "定位扫描量最大的 SQL，补充合适的复合索引或限制扫描范围（时间分区/分页游标）",
                "确认是否存在无索引的 ORDER BY / GROUP BY 组合",
                "排查同机是否有备份、mysqldump、日志归档在抢占带宽",
            ],
        })

    # 3) 写压力大 → 磁盘临时表 / 排序落盘 / relay log 回放
    if (w_mbs > 0 and (io["w_s"] >= tg["write_pressure"]["write_iops_gte"]
                       or w_mbs >= tg["write_pressure"]["write_mbs_gte"]
                       or io["read_mb_share"] < tg["write_pressure"]["read_mb_share_lt"])):
        cands.append({
            "key": "write_pressure",
            "name": "写入压力显著 · 磁盘临时表/排序落盘/复制回放",
            "score": 0,
            "evidence": ev(
                "写 IOPS %.0f，写吞吐 %s（占比 %.1f%%）" % (io["w_s"], human_mb(w_mbs), 100 - io["read_mb_share"]),
                ("写等待 w_await=%.2f ms" % io["hot_w_await"]) if io["hot_w_await"] else None,
            ),
            "suggestion": [
                "检查 Created_tmp_disk_tables / Sort_merge_passes 是否持续增长",
                "评估 sort_buffer_size、join_buffer_size、tmp_table_size 是否偏小（调参需先在测试环境验证）",
                "RO 上还需区分 relay log 回放与临时文件写入",
            ],
        })

    # 4) 设备饱和
    if (util >= tg["device_saturation"]["util_gte"]
            or (r_await and r_await >= tg["device_saturation"]["r_await_gte"])):
        cands.append({
            "key": "device_saturation",
            "name": "块设备已接近饱和 · 队列积压",
            "score": 0,
            "evidence": ev(
                "%s 的 %%util=%.1f%%" % (io["hot_dev"], util),
                ("平均队列长度 avgqu-sz=%.2f" % io["hot_avgqu_sz"]) if io["hot_avgqu_sz"] else None,
                ("await=%.2f ms" % io["hot_await"]) if io["hot_await"] else None,
            ),
            "suggestion": [
                "先降低 I/O 需求（优化 SQL/索引），再考虑扩容存储规格",
                "确认是否为云盘突发配额（burst balance）耗尽导致的降速",
                "与其他同机实例/进程错峰",
            ],
        })

    # 5) iowait 与 IOPS 量级不匹配 → 非 DB 因素或单设备异常
    if (iowait >= tg["mismatch_low_io"]["iowait_gte"]
            and iops < tg["mismatch_low_io"]["iops_lt"]
            and mbs < tg["mismatch_low_io"]["mbs_lt"]):
        cands.append({
            "key": "mismatch_low_io",
            "name": "iowait 高但 I/O 量不大 · 需排查设备异常/其他进程",
            "score": 0,
            "evidence": ev(
                "iowait=%.2f%%，但总 IOPS 仅 %.0f、吞吐 %s" % (iowait, iops, human_mb(mbs)),
            ),
            "suggestion": [
                "用 pidstat -d / iotop 定位具体进程，确认是否为 MySQL",
                "检查磁盘健康（smartctl、云盘监控）、RAID 卡电池/缓存策略",
                "确认 iostat 采样窗口是否与告警窗口对齐",
            ],
        })

    # --- 用 SQL digest 给候选加权
    sql_ev = []
    if top_sql:
        worst = top_sql[0]
        sql_ev.append("扫描量最大的 SQL：%s" % _clip(worst.get("sql", ""), 120))
        if worst.get("rows_examined"):
            sql_ev.append("累计扫描行数 %.0f，返回 %.0f，扫描放大比 %.1f"
                          % (worst["rows_examined"], worst.get("rows_sent", 0), worst["scan_ratio"]))
        if any(r.get("tmp_disk_tables", 0) > 0 for r in top_sql):
            n = sum(r.get("tmp_disk_tables", 0) for r in top_sql)
            sql_ev.append("存在磁盘临时表，累计 %.0f 次" % n)
            _bump(cands, "write_pressure", db["tmp_disk_write"], "磁盘临时表 %.0f 次与写压力相互印证" % n)
        if any(r.get("no_index_used", 0) > 0 for r in top_sql):
            n = sum(r.get("no_index_used", 0) for r in top_sql)
            sql_ev.append("存在无索引访问，累计 %.0f 次" % n)
            _bump(cands, "large_seq_scan", db["no_index_seq"], "无索引访问 %.0f 次与顺序扫相互印证" % n)
            _bump(cands, "random_read_amplification", db["no_index_random"], "无索引访问会放大随机读")
        if worst.get("scan_ratio", 0) > db["scan_ratio_gt"]:
            _bump(cands, "random_read_amplification", db["scan_ratio_random"],
                  "扫描放大比 %.0f 说明大量扫描未转化为返回行" % worst["scan_ratio"])
            _bump(cands, "large_seq_scan", db["scan_ratio_seq"],
                  "扫描放大比 %.0f 同样支持大范围扫描" % worst["scan_ratio"])

    # --- 用 DDL 结构加权
    ddl_ev = []
    _seen_ddl = set()
    if tables:
        for r in top_sql[:3]:
            ts = match_tables(r.get("sql", ""), tables)
            for t in ts:
                info = tables[t]
                if info["lob_fields"] and ("lob:" + t) not in _seen_ddl:
                    _seen_ddl.add("lob:" + t)
                    ddl_ev.append("表 %s 含大字段(%s)，可能触发溢出页随机读"
                                  % (t, ",".join(info["lob_fields"][:3])))
                    _bump(cands, "random_read_amplification", dlb["lob_random"],
                          "%s 的大字段会放大随机读" % t)
                if not info["has_pk"] and ("pk:" + t) not in _seen_ddl:
                    _seen_ddl.add("pk:" + t)
                    ddl_ev.append("表 %s 未识别到主键，InnoDB 回表成本更高" % t)
                    _bump(cands, "random_read_amplification", dlb["no_pk_random"], "%s 无显式主键" % t)
                if len(info["indexes"]) <= dlb["index_few_max"] and ("idx:" + t) not in _seen_ddl:
                    _seen_ddl.add("idx:" + t)
                    ddl_ev.append("表 %s 索引数量偏少（%d 个），大范围过滤易全扫"
                                  % (t, len(info["indexes"])))
                    _bump(cands, "large_seq_scan", dlb["index_few_seq"], "%s 索引偏少" % t)

    # --- 打分：基础分由量级决定（除数/上限/加成全部来自配置 scoring）
    sr, sl, sw, sd, sm = (sc["random_read"], sc["large_seq_scan"], sc["write_pressure"],
                          sc["device_saturation"], sc["mismatch_low_io"])
    for c in cands:
        s = 0.0
        if c["key"] == "random_read_amplification":
            s = min(io["r_s"] / sr["iops_divisor"], sr["cap"]) + \
                (sr["small_read_bonus"] if avg_read_kb and avg_read_kb < sr["small_read_kb_lt"] else 0)
        elif c["key"] == "large_seq_scan":
            s = min(r_mbs / sl["mbs_divisor"], sl["cap"]) + \
                (sl["huge_read_bonus"] if avg_read_kb and avg_read_kb >= sl["huge_read_kb_gte"] else 0)
        elif c["key"] == "write_pressure":
            s = min(w_mbs / sw["mbs_divisor"], sw["mbs_cap"]) + \
                min(io["w_s"] / sw["iops_divisor"], sw["iops_cap"])
        elif c["key"] == "device_saturation":
            s = min(util / sd["util_divisor"], sd["cap"])
        elif c["key"] == "mismatch_low_io":
            s = min(iowait / sm["iowait_divisor"], sm["cap"])
        c["score"] = round(s + c.get("bump", 0.0), 2)

    cands.sort(key=lambda c: c["score"], reverse=True)

    # 置信度：证据条数 + 分值差距（口径来自配置 confidence）
    if cands:
        top = cands[0]
        n = len(top["evidence"])
        gap = top["score"] - (cands[1]["score"] if len(cands) > 1 else top["score"])
        if n >= cf["high_evidence"] and gap >= cf["high_gap"]:
            conf = "高"
        elif n >= cf["mid_evidence"] or gap >= cf["mid_gap"]:
            conf = "中"
        else:
            conf = "低"
        top["confidence"] = conf
        for c in cands[1:]:
            c["confidence"] = "中" if len(c["evidence"]) >= cf["mid_evidence"] else "低"

    for c in cands:
        c.pop("bump", None)

    return cands, sql_ev, ddl_ev


def _bump(cands, key, val, reason):
    for c in cands:
        if c["key"] == key:
            c["bump"] = c.get("bump", 0.0) + val
            c["evidence"].append(reason)
            return


def _clip(s, n):
    s = (s or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[:n] + "…"


# ---------------------------------------------------------------- 报告生成


def build_report(io, cpu, parsed_io, top_sql, tables, meta, cands, sql_ev, ddl_ev, inputs):
    """生成中文诊断报告（Markdown）。

    与源样例的差异：标题带【待复核】并明确「结论未经 DBA 人工复核不得外发」；
    DDL 缺失时输出占位章节（源样例直接省略该章），因此章节号固定为一~八。
    """
    th = load_thresholds()
    L = []
    A = L.append
    inst = meta.get("instance", "(未命名实例)")
    A("# MySQL 只读副本 I/O 分诊报告 【待复核】")
    A("")
    A("> 本报告由 `ops-patrol-toolkit/02_mysql_io_triage` v%s 自动生成，全程只读，**不含任何变更动作**。" % __version__)
    A("> **结论未经 DBA 人工复核不得外发**，亦不得直接作为处置依据。")
    A("")
    A("## 一、场景与目标")
    A("")
    A("- **实例**：%s（%s）" % (inst, meta.get("role", "只读副本/RO")))
    A("- **告警**：%s" % meta.get("alert", "磁盘 I/O / iowait 告警"))
    A("- **时间窗**：%s" % meta.get("window", "见输入材料时间戳（需人工核对与告警对齐）"))
    A("- **目标**：定位磁盘压力的物理特征与 SQL 归因，给出可验证的处置方向。")
    A("")
    A("## 二、数据来源与口径")
    A("")
    A("| 材料 | 来源 | 说明 |")
    A("|---|---|---|")
    for k, v in inputs.items():
        A("| %s | `%s` | %s |" % (k, v.get("path", "-"), v.get("note", "")))
    A("")
    A("> 吞吐单位自动识别为 **%s**，已统一换算为 MB/s。" % parsed_io["unit"])
    A("> 分诊阈值版本：triage_thresholds v%s（`config/patrol/triage_thresholds.json`）。" % th["version"])
    A("")
    A("## 三、物理 I/O 画像")
    A("")
    A("| 指标 | 数值 | 判读 |")
    A("|---|---|---|")
    A("| 总 IOPS | %.0f | %s |" % (io["iops"], _judge_iops(io["iops"], th)))
    A("| 读 IOPS / 写 IOPS | %.0f / %.0f | 读占比 %.1f%% |" % (io["r_s"], io["w_s"], io["read_iops_share"]))
    A("| 读吞吐 / 写吞吐 | %s / %s | 读占比 %.1f%% |" % (human_mb(io["r_mbs"]), human_mb(io["w_mbs"]), io["read_mb_share"]))
    A("| 平均单次读大小 | %.1f KB | %s |" % (io["avg_read_kb"], _judge_iosize(io["avg_read_kb"], th)))
    if io["avg_write_kb"]:
        A("| 平均单次写大小 | %.1f KB | — |" % io["avg_write_kb"])
    A("| 主压力设备 | %s | util=%.1f%% |" % (io["hot_dev"], io["hot_util"]))
    A("| await / r_await / w_await | %.2f / %.2f / %.2f ms | %s |" % (
        io["hot_await"], io["hot_r_await"], io["hot_w_await"], _judge_await(io["hot_await"], th)))
    if io["hot_avgqu_sz"]:
        A("| avgqu-sz | %.2f | %s |" % (io["hot_avgqu_sz"], _judge_queue(io["hot_avgqu_sz"], th)))
    if cpu:
        A("| CPU iowait | %.2f%% | %s |" % (cpu.get("iowait", 0), _judge_iowait(cpu.get("iowait", 0), th)))
        A("| CPU user / system / idle | %.2f / %.2f / %.2f %% | — |" % (
            cpu.get("user", 0), cpu.get("system", 0), cpu.get("idle", 0)))
    A("")

    A("## 四、SQL 归因（TOP %d）" % len(top_sql))
    A("")
    if top_sql:
        A("| # | 扫描行数 | 返回行数 | 放大比 | 执行次数 | 磁盘临时表 | 无索引 | SQL 摘要 |")
        A("|---|---|---|---|---|---|---|---|")
        for r in top_sql:
            A("| %d | %.0f | %.0f | %.1f | %.0f | %.0f | %.0f | `%s` |" % (
                r["rank"], r.get("rows_examined", 0), r.get("rows_sent", 0), r.get("scan_ratio", 0),
                r.get("exec_count", 0), r.get("tmp_disk_tables", 0), r.get("no_index_used", 0),
                _clip(r.get("sql", ""), 70).replace("|", "\\|")))
        A("")
        for e in sql_ev:
            A("- %s" % e)
        A("")
    else:
        A("_未提供 digest 材料，本节跳过。建议补齐 `performance_schema`.`events_statements_summary_by_digest` 或 pt-query-digest 输出。_")
        A("")

    A("## 五、表结构佐证")
    A("")
    if tables:
        A("| 表 | 引擎 | 行格式 | 字段数 | 大字段 | 索引数 | 主键 |")
        A("|---|---|---|---|---|---|---|")
        for t, i in tables.items():
            A("| %s | %s | %s | %d | %s | %d | %s |" % (
                t, i.get("engine") or "-", i.get("row_format") or "-", i.get("field_count", 0),
                ",".join(i.get("lob_fields") or []) or "-", len(i.get("indexes") or []),
                "有" if i.get("has_pk") else "无"))
        A("")
        for e in ddl_ev:
            A("- %s" % e)
        A("")
    else:
        A("_未提供 DDL 材料，本节跳过。建议补齐相关表的 `SHOW CREATE TABLE` 输出。_")
        A("")

    A("## 六、根因判定")
    A("")
    if cands:
        top = cands[0]
        A("### 主因：%s" % top["name"])
        A("")
        A("- **置信度**：%s" % top["confidence"])
        A("- **证据链**：")
        for e in top["evidence"]:
            A("  - %s" % e)
        A("- **处置建议**（均为建议，需变更评审 + 测试环境验证）：")
        for s in top["suggestion"]:
            A("  - %s" % s)
        A("")
        if len(cands) > 1:
            A("### 备选根因（按可能性排序）")
            A("")
            for c in cands[1:]:
                A("**%s**（置信度：%s）" % (c["name"], c["confidence"]))
                A("")
                for e in c["evidence"]:
                    A("- %s" % e)
                A("")
    else:
        A("_当前输入未触发任何根因判定规则，可能是采样窗口与告警窗口不一致，或指标量级正常。请复核输入材料。_")
        A("")

    A("## 七、风险边界")
    A("")
    A("1. **只读**：本次分析未连接数据库，未执行任何 DDL/DML/KILL/参数修改。")
    A("2. **脱敏**：实例 IP、主机名、账号、业务字面值须在入参前完成脱敏；本报告不落库任何凭据。")
    A("3. **禁止输入**：数据库密码、API 密钥、token、客户/人员/合同信息、未脱敏生产数据。")
    A("4. **建议非指令**：所有优化建议需经 DBA 在测试环境验证并走变更流程，禁止直接上生产。")
    A("5. **作用域**：仅限单一实例，不做跨实例/跨项目推断。")
    A("")
    A("## 八、待确认项")
    A("")
    A("- [ ] 采样窗口是否与告警窗口严格对齐")
    A("- [ ] 主压力设备上是否还有其他进程（iotop/pidstat 佐证）")
    A("- [ ] buffer pool 命中率与脏页比例（需补 InnoDB 状态）")
    A("- [ ] RO 是否存在复制回放延迟叠加影响")
    A("- [ ] TOP SQL 的执行计划是否已现场 EXPLAIN 验证")
    A("")
    A("---")
    A("")
    A("_报告生成：ops-patrol-toolkit 02_mysql_io_triage v%s（只读）· 结论未经人工复核不得外发_" % __version__)
    A("")
    return "\n".join(L)


def _judge_iops(v, th):
    j = th["judges"]
    if v >= j["iops_very_high_gte"]:
        return "极高"
    if v >= j["iops_high_gte"]:
        return "偏高"
    if v >= j["iops_mid_gte"]:
        return "中等"
    return "正常"


def _judge_iosize(v, th):
    j = th["judges"]
    if v <= 0:
        return "无读"
    if v < j["iosize_small_kb_lt"]:
        return "小块随机读为主"
    if v < j["iosize_large_kb_gte"]:
        return "混合"
    return "大块顺序读为主"


def _judge_await(v, th):
    j = th["judges"]
    if v >= j["await_severe_gte"]:
        return "严重排队"
    if v >= j["await_obvious_gte"]:
        return "明显排队"
    if v >= j["await_slight_gte"]:
        return "轻微排队"
    return "正常"


def _judge_queue(v, th):
    j = th["judges"]
    if v >= j["queue_severe_gte"]:
        return "队列严重积压"
    if v >= j["queue_obvious_gte"]:
        return "队列明显积压"
    if v >= j["queue_some_gte"]:
        return "有排队"
    return "无明显排队"


def _judge_iowait(v, th):
    j = th["judges"]
    if v >= j["iowait_severe_gte"]:
        return "严重"
    if v >= j["iowait_high_gte"]:
        return "偏高"
    if v >= j["iowait_watch_gte"]:
        return "关注"
    return "正常"


# ---------------------------------------------------------------- 子命令


def cmd_parse_iostat(a):
    p = parse_iostat(read_text(a.iostat))
    agg = aggregate_devices(p["devices"])
    print("已解析设备 %d 个（%d 轮取最后一轮，吞吐单位 %s），主压力设备 %s"
          % (len(p["devices"]), p["samples"], p["unit"], agg["hot_dev"]))
    patrol_lib.emit({
        "cmd": "parse-iostat",
        "cpu": p["cpu"], "unit": p["unit"], "samples": p["samples"],
        "aggregate": agg, "devices": p["devices"],
    })
    return 0


def cmd_analyze_digest(a):
    rows = rank_digest(parse_digest(read_text(a.digest)), a.top)
    print("digest 解析出 %d 行，按扫描压力取 TOP %d" % (len(rows), a.top))
    patrol_lib.emit({"cmd": "analyze-digest", "count": len(rows), "top": rows})
    return 0


def cmd_analyze_ddl(a):
    t = parse_ddl(read_text(a.ddl))
    print("DDL 解析出 %d 张表（正则级尽力解析）" % len(t))
    patrol_lib.emit({"cmd": "analyze-ddl", "count": len(t), "tables": t})
    return 0


def cmd_run(a):
    th = load_thresholds()
    out_dir = a.out or str(patrol_lib.work_path("io_triage"))
    os.makedirs(out_dir, exist_ok=True)

    io_text = read_text(a.iostat)
    if not io_text:
        patrol_lib.stop("--iostat 是必填项：空文件无法分诊，请提供含 Device 段的 iostat -x 采样文本")

    pio = parse_iostat(io_text)
    agg = aggregate_devices(pio["devices"])
    cpu = pio["cpu"]

    meta = {}
    if a.meta:
        try:
            meta = json.loads(read_text(a.meta))
        except json.JSONDecodeError as e:
            patrol_lib.stop("meta JSON 解析失败: %s（请提供合法的实例元信息 JSON）" % e)

    drows = rank_digest(parse_digest(read_text(a.digest)), a.top) if a.digest else []
    tables = parse_ddl(read_text(a.ddl)) if a.ddl else {}

    cands, sql_ev, ddl_ev = triage(agg, cpu, drows, tables, meta)

    inputs = OrderedDict()
    inputs["iostat"] = {"path": a.iostat, "note": "物理 I/O 采样，%d 轮取最后一轮" % pio["samples"]}
    if a.digest:
        inputs["digest"] = {"path": a.digest, "note": "慢查询汇总，取 TOP %d" % a.top}
    if a.ddl:
        inputs["ddl"] = {"path": a.ddl, "note": "表结构，正则级解析（尽力而为）"}
    if a.meta:
        inputs["meta"] = {"path": a.meta, "note": "实例元信息"}

    report = build_report(agg, cpu, pio, drows, tables, meta, cands, sql_ev, ddl_ev, inputs)

    rp = Path(out_dir) / "report.md"
    jp = Path(out_dir) / "triage.json"
    patrol_lib.write_text(rp, report)
    patrol_lib.write_json(jp, {
        "version": __version__,
        "thresholds_version": th["version"],
        "instance": meta.get("instance"),
        "cpu": cpu, "io": agg, "devices": pio["devices"],
        "top_sql": drows, "tables": tables,
        "candidates": cands, "sql_evidence": sql_ev, "ddl_evidence": ddl_ev,
    })

    print("报告已生成: %s" % rp)
    print("结构化结果: %s" % jp)
    if cands:
        print("主因: %s （置信度 %s）" % (cands[0]["name"], cands[0]["confidence"]))
    else:
        print("未触发任何根因判定规则，请复核输入材料与采样窗口")
    patrol_lib.emit({
        "cmd": "run",
        "report": str(rp),
        "triage": str(jp),
        "top_cause": ({"key": cands[0]["key"], "name": cands[0]["name"],
                       "confidence": cands[0]["confidence"]} if cands else None),
        "candidates": len(cands),
        "unit": pio["unit"],
        "samples": pio["samples"],
    })
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="02_mysql_io_triage", description="MySQL 只读副本 I/O 分诊（只读工具，不执行任何变更）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("parse-iostat", help="解析 iostat 输出")
    p1.add_argument("--iostat", required=True)
    p1.set_defaults(func=cmd_parse_iostat)

    p2 = sub.add_parser("analyze-digest", help="解析慢查询 digest")
    p2.add_argument("--digest", required=True)
    p2.add_argument("--top", type=int, default=10)
    p2.set_defaults(func=cmd_analyze_digest)

    p3 = sub.add_parser("analyze-ddl", help="解析表 DDL")
    p3.add_argument("--ddl", required=True)
    p3.set_defaults(func=cmd_analyze_ddl)

    p4 = sub.add_parser("run", help="完整分诊并生成报告")
    p4.add_argument("--iostat", required=True, help="iostat -x 输出文件")
    p4.add_argument("--digest", help="慢查询 digest CSV/TSV/JSON")
    p4.add_argument("--ddl", help="表结构 DDL")
    p4.add_argument("--meta", help="实例元信息 JSON")
    p4.add_argument("--top", type=int, default=10)
    p4.add_argument("--out", default=None, help="输出目录（缺省写入 work/io_triage）")
    p4.set_defaults(func=cmd_run)

    a = ap.parse_args(argv)
    return a.func(a) or 0


if __name__ == "__main__":
    sys.exit(main())
