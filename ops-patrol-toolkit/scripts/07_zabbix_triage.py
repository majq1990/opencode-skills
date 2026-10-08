#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07 Zabbix 告警拉取与离线分诊（两阶段 CLI，triage 可离线复跑）。

problems 阶段（联网，出站必经 monitor_http 安全闸）：
  1. problem.get 拉取当前活动告警（recent=true，按 eventid 倒序，limit 上限；
     配置 severities 或 CLI --severities 声明时仅拉指定级别）
  2. trigger.get 批量回填触发器所属主机
  归一化为统一 findings 结构落盘 problems.json（任何 token 都不落盘）。

triage 阶段（纯离线）：
  读 problems.json，按告警标题关键词匹配 references/playbooks/common_playbooks.json
  的处置剧本（标题 contains 关键词，按剧本库顺序首个命中生效）；未命中给通用兜底 3 步；
  按严重度降序生成处置引导报告 guide.md（头部带【待复核】标记）。

用法:
  python scripts/07_zabbix_triage.py problems --config config/patrol/monitors.json [--group zabbix] [--limit 100] [--severities 3,4,5] [--out work/zabbix/problems.json]
  python scripts/07_zabbix_triage.py triage --problems work/zabbix/problems.json [--common references/playbooks/common_playbooks.json] [--out work/zabbix/guide.md]

凭证：token 只经环境变量注入（名字由 monitors.json zabbix.token_env_ref 声明），绝不落盘；
测试全部走本地假服务（127.0.0.1），绝不真实联网。
"""

import argparse
import json
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import patrol_lib  # noqa: E402
from patrol_lib import as_bool, emit, read_json, stop, write_json, write_text  # noqa: E402
from monitor_http import MonitorHttpError, http_post_json, load_monitor_config  # noqa: E402

__version__ = "1.0.0"

DEFAULT_GROUP = "zabbix"
DEFAULT_LIMIT = 100
DEFAULT_OUT_PROBLEMS = "work/zabbix/problems.json"
DEFAULT_OUT_GUIDE = "work/zabbix/guide.md"
DEFAULT_COMMON = "references/playbooks/common_playbooks.json"

SEVERITY_LABELS = {0: "未定义", 1: "信息", 2: "警告", 3: "一般严重", 4: "严重", 5: "灾难"}


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------

def _one_line(text):
    """压平空白成单行（标题/主机进报告与示例命令用）。"""
    return " ".join(str(text or "").split())


def epoch_to_str(epoch):
    """Unix 秒 -> "YYYY-MM-DD HH:MM:SS"（本地时区）；0/负值/非法给空串。"""
    try:
        epoch = int(epoch)
    except (TypeError, ValueError):
        return ""
    if epoch <= 0:
        return ""
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")


def humanize_duration(seconds):
    """秒数 -> 人读时长（X 秒 / X 分钟 / X 小时 Y 分钟 / X 天 Y 小时）。"""
    try:
        sec = int(seconds)
    except (TypeError, ValueError):
        return "未知"
    if sec < 0:
        sec = 0
    if sec < 60:
        return "%d 秒" % sec
    minute, _ = divmod(sec, 60)
    if minute < 60:
        return "%d 分钟" % minute
    hour, minute = divmod(minute, 60)
    if hour < 24:
        return "%d 小时 %d 分钟" % (hour, minute)
    day, hour = divmod(hour, 24)
    return "%d 天 %d 小时" % (day, hour)


def endpoint_of(url):
    """url -> "主机[:端口]/路径"（不含 scheme 与任何凭证），用于落盘与报告头。"""
    p = urllib.parse.urlsplit(url)
    host = p.hostname or ""
    netloc = host if p.port is None else "%s:%s" % (host, p.port)
    return "%s%s" % (netloc, p.path or "")


def resolve_out(out):
    """输出路径：相对路径一律相对 skill 根目录解析（与工具集输出契约一致）。"""
    p = Path(out)
    if not p.is_absolute():
        p = patrol_lib.ROOT / p
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def parse_severities(raw):
    """CLI --severities "3,4,5" -> [3,4,5]；未给返回 None（回落配置），非法即 gap。"""
    if raw is None:
        return None
    parts = [p.strip() for p in str(raw).split(",") if p.strip()]
    return _norm_severity_list(parts, "--severities")


def _norm_severity_list(values, origin):
    out = []
    for v in values:
        try:
            iv = int(str(v).strip())
        except (TypeError, ValueError):
            stop("%s 的告警级别需为 0-5 整数（收到 %r）" % (origin, v))
        if not 0 <= iv <= 5:
            stop("%s 的告警级别取值需在 0-5（收到 %s）" % (origin, iv))
        out.append(iv)
    return out


def _sev_int(finding):
    try:
        return int(finding.get("severity") or 0)
    except (TypeError, ValueError):
        return 0


def count_by_severity(findings):
    """按严重度降序统计各级别条数（label -> count），额外未知标签追加在最后。"""
    counts = {}
    for f in findings:
        sev = _sev_int(f)
        label = f.get("severity_label") if isinstance(f, dict) else None
        label = label or SEVERITY_LABELS.get(sev, "未知")
        counts[label] = counts.get(label, 0) + 1
    ordered = {}
    for sev in sorted(SEVERITY_LABELS, reverse=True):
        label = SEVERITY_LABELS[sev]
        if label in counts:
            ordered[label] = counts[label]
    for label, n in counts.items():
        if label not in ordered:
            ordered[label] = n
    return ordered


# ---------------------------------------------------------------------------
# problems 阶段：Zabbix JSON-RPC 拉取 + 归一化落盘
# ---------------------------------------------------------------------------

def rpc_call(cfg, payload):
    """发一条 Zabbix JSON-RPC 请求（必经 monitor_http 安全闸），返回 result。

    Content-Type 按 Zabbix API 约定覆盖为 application/json-rpc；
    响应含 error 即 gap（带 code/message）；网络/超时/非 JSON 统一转 gap。
    """
    try:
        status, resp = http_post_json(
            cfg["url"], payload,
            token=cfg.get("_token") or None,
            timeout_s=int(cfg.get("timeout_s") or 60),
            allow_local=as_bool(cfg.get("allow_local_targets")),
            allow_private=as_bool(cfg.get("allow_private_targets")),
            headers={"Content-Type": "application/json-rpc"},
        )
    except MonitorHttpError as e:
        stop("Zabbix API 请求失败（%s，method=%s）：%s" % (e.kind, payload.get("method"), e.message))
    except (TypeError, ValueError) as e:
        stop("Zabbix API 配置不合法（timeout_s 等）：%s" % e)
    if not isinstance(resp, dict):
        stop("Zabbix API 响应不是 JSON 对象（HTTP %s，method=%s）" % (status, payload.get("method")))
    if "error" in resp:
        err = resp.get("error") or {}
        stop("Zabbix API 返回 JSON-RPC error（method=%s）：code=%s message=%s"
             % (payload.get("method"), err.get("code"), err.get("message")))
    result = resp.get("result")
    if result is None:
        stop("Zabbix API 响应缺少 result（method=%s）" % payload.get("method"))
    return result


def normalize_problem(problem, host, now):
    """problem.get 的原始条目 -> 统一 findings 结构。"""
    p = problem if isinstance(problem, dict) else {}
    try:
        sev = int(p.get("severity") or 0)
    except (TypeError, ValueError):
        sev = 0
    try:
        clock = int(p.get("clock") or 0)
    except (TypeError, ValueError):
        clock = 0
    tags = []
    for t in p.get("tags") or []:
        if isinstance(t, dict):
            tags.append({"tag": str(t.get("tag") or ""), "value": str(t.get("value") or "")})
    return {
        "source": "zabbix",
        "id": str(p.get("eventid") or ""),
        "title": str(p.get("name") or ""),
        "host": str(host or ""),
        "severity": sev,
        "severity_label": SEVERITY_LABELS.get(sev, "未知(%s)" % sev),
        "fired_at": epoch_to_str(clock),
        "age_s": max(0, now - clock) if clock > 0 else 0,
        "tags": tags,
    }


def fetch_findings(cfg, limit, severities):
    """两步 JSON-RPC：problem.get 拉告警 -> trigger.get 回填主机，返回归一化 findings。

    必然先 problem.get 后 trigger.get（triggerids 非空才发第二步）。
    """
    token = cfg.get("_token") or ""
    params = {
        "output": "extend",
        "recent": True,
        "sortfield": "eventid",
        "sortorder": "DESC",
        "limit": limit,
    }
    if severities:
        params["severity"] = list(severities)
    problems = rpc_call(cfg, {
        "jsonrpc": "2.0", "id": 1, "method": "problem.get",
        "auth": token, "params": params,
    })
    if not isinstance(problems, list):
        stop("Zabbix problem.get 的 result 不是数组，响应结构不符合预期")

    host_map = {}
    triggerids = sorted({str(p.get("objectid")) for p in problems if isinstance(p, dict) and p.get("objectid")})
    if triggerids:
        triggers = rpc_call(cfg, {
            "jsonrpc": "2.0", "id": 2, "method": "trigger.get",
            "auth": token,
            "params": {
                "triggerids": triggerids,
                "output": ["triggerid", "description", "priority"],
                "selectHosts": ["host", "name"],
            },
        })
        for t in triggers or []:
            if not isinstance(t, dict):
                continue
            hosts = t.get("hosts") or []
            name = ""
            if hosts and isinstance(hosts[0], dict):
                name = hosts[0].get("name") or hosts[0].get("host") or ""
            host_map[str(t.get("triggerid") or "")] = str(name)

    now = int(time.time())
    findings = []
    for p in problems:
        objid = str(p.get("objectid") or "") if isinstance(p, dict) else ""
        findings.append(normalize_problem(p, host_map.get(objid, ""), now))
    return findings


def run_problems(config_path, group, limit, cli_severities, out):
    """拉取当前告警并落盘 problems.json，打印成功信封。"""
    try:
        cfg = load_monitor_config(config_path, group)
    except KeyError as e:
        stop("读取监控配置失败：%s（文件 %s）" % (e, config_path))
    except (OSError, json.JSONDecodeError) as e:
        stop("监控配置无法读取 %s：%s" % (config_path, e))

    if not as_bool(cfg.get("enabled")):
        stop("端点未启用（monitors.json %s.enabled=false，如需拉取请置 true）" % group)

    token = str(cfg.get("_token") or "").strip()
    token_ref = str(cfg.get("token_env_ref") or "").strip()
    if token_ref and not token:
        # 缺前置凭证即停，且此检查必须发生在任何出站请求之前
        stop("环境变量 %s 未设置（monitors.json %s.token_env_ref），无法认证 Zabbix API；"
             "请设置该环境变量后重试（token 只进环境变量，绝不落盘）" % (token_ref, group))

    if cli_severities is not None:
        severities = cli_severities
    elif cfg.get("severities") is not None:
        raw = cfg.get("severities")
        if isinstance(raw, str):
            raw = [p for p in raw.split(",") if p.strip()]
        severities = _norm_severity_list(raw, "monitors.json %s.severities" % group)
    else:
        severities = []

    findings = fetch_findings(cfg, limit, severities)
    doc = {
        "version": "1.0",
        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "zabbix",
        "endpoint": endpoint_of(cfg["url"]),
        "findings": findings,
    }
    out_path = resolve_out(out)
    write_json(out_path, doc)
    print("[07] problems: 端点 %s（组 %s）拉取到 %d 条活动告警，已落盘" % (doc["endpoint"], group, len(findings)))
    payload = {
        "total": len(findings),
        "by_severity": count_by_severity(findings),
        "endpoint": doc["endpoint"],
        "output": str(out_path),
    }
    if not findings:
        payload["note"] = "无活动告警"
    emit(payload)
    return payload


# ---------------------------------------------------------------------------
# triage 阶段：离线剧本匹配 + 处置引导报告
# ---------------------------------------------------------------------------

def match_playbook(title, playbooks):
    """标题对每个剧本 match_keywords 做边界感知命中（patrol_lib.keyword_hit：
    保留原文判定驼峰词首/词左边界，内部忽略大小写；调用侧不得先 lower），
    按库内顺序首个命中返回，否则 None。"""
    t = str(title or "")
    for pb in playbooks or []:
        if not isinstance(pb, dict):
            continue
        for kw in pb.get("match_keywords") or []:
            if patrol_lib.keyword_hit(kw, t):
                return pb
    return None


def fallback_steps(finding):
    """未命中剧本的通用兜底 3 步（确认现象影响 / 查触发器文档 / 用 05 号子工具检索历史案例）。"""
    title = _one_line(finding.get("title") or "未知告警")
    host = _one_line(finding.get("host") or "目标主机")
    return [
        "确认现象影响：登录 Zabbix 控制台查看该告警详情（触发器表达式、事件流与持续时间），"
        "确认现象真实存在并评估业务影响面",
        "查触发器文档：在 Zabbix 前端打开对应触发器与监控项，确认采集口径与阈值设置是否合理，"
        "必要时查阅模板说明或 Zabbix 官方文档",
        "检索历史案例：用本工具集 05 号子工具查历史相似工单与知识库，示例命令："
        'python scripts/05_kb_similar_search.py query --text "%s %s 告警排查"' % (title, host),
    ]


def render_report(doc, findings, playbooks):
    """生成处置引导报告 markdown，返回 (文本, matched, unmatched)。"""
    ordered = sorted(findings, key=_sev_int, reverse=True)  # 严重度降序，同级保持拉取顺序
    matched = 0
    blocks = []
    for idx, f in enumerate(ordered, 1):
        if not isinstance(f, dict):
            f = {"title": str(f)}
        pb = match_playbook(f.get("title"), playbooks)
        if pb:
            matched += 1
            steps = [str(s) for s in (pb.get("steps") or [])]
            pb_line = "处置剧本：%s（%s）" % (pb.get("title") or pb.get("id") or "", pb.get("id") or "")
        else:
            steps = fallback_steps(f)
            pb_line = "处置剧本：无（未命中剧本库，使用通用兜底步骤）"
        sev = _sev_int(f)
        label = f.get("severity_label") or SEVERITY_LABELS.get(sev, "未知")
        blocks.extend([
            "## %d. [%s] %s" % (idx, label, _one_line(f.get("title") or "（无标题）")),
            "",
            "- 告警 ID：%s" % f.get("id", ""),
            "- 主机：%s" % (f.get("host") or "（未知主机）"),
            "- 严重度：%s %s" % (sev, label),
            "- 触发时间：%s" % (f.get("fired_at") or "（未知）"),
            "- 持续时长：%s" % humanize_duration(f.get("age_s") or 0),
            "- %s" % pb_line,
            "- 处置步骤：",
            "",
        ])
        for j, s in enumerate(steps, 1):
            blocks.append("   %d. %s" % (j, s))
        blocks.append("")
    unmatched = len(ordered) - matched
    header = [
        "# Zabbix 告警分诊处置引导",
        "",
        "**【待复核】** 本报告由 ops-patrol-toolkit 07 号子工具自动生成，未经人工复核不得外发。",
        "",
        "- 生成时间：%s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "- 数据来源：Zabbix API（%s）" % (doc.get("endpoint") or "未知端点"),
        "- 告警总数：%d（剧本命中 %d / 通用兜底 %d）" % (len(ordered), matched, unmatched),
        "",
    ]
    tail = [
        "---",
        "说明：以上处置步骤为引导建议，执行前需人工确认并在测试环境验证；"
        "对未命中剧本的告警可用 05 号子工具检索历史相似案例辅助定位。",
    ]
    return "\n".join(header + blocks + tail) + "\n", matched, unmatched


def run_triage(problems_path, common_path, out):
    """读 problems.json 离线分诊并生成处置引导报告，打印成功信封。"""
    doc = read_json(problems_path)  # 缺文件/坏 JSON 由 patrol_lib 统一 gap
    if not isinstance(doc, dict) or "findings" not in doc:
        stop("problems 文件缺少 findings 键，结构不符合约定：%s（请先运行 problems 子命令拉取）" % problems_path)
    raw_findings = doc.get("findings")
    if not isinstance(raw_findings, list):
        stop("problems 文件的 findings 键不是数组，结构不符合约定：%s" % problems_path)
    findings = [f if isinstance(f, dict) else {"title": str(f)} for f in raw_findings]

    playbooks = []
    if common_path:
        common = read_json(common_path)
        playbooks = common.get("playbooks") or [] if isinstance(common, dict) else []

    report_text, matched, unmatched = render_report(doc, findings, playbooks)
    out_path = resolve_out(out)
    write_text(out_path, report_text)
    print("[07] triage: 剧本命中 %d 条，通用兜底 %d 条，报告已生成" % (matched, unmatched))
    emit({
        "total": len(findings),
        "matched": matched,
        "unmatched": unmatched,
        "by_severity": count_by_severity(findings),
        "report": str(out_path),
    })
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="07_zabbix_triage.py",
        description="Zabbix 告警拉取与离线分诊：problems 联网拉取落盘，triage 离线生成处置引导报告",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_problems = sub.add_parser("problems", help="从 Zabbix 拉取当前告警（problem.get + trigger.get）并归一化落盘")
    p_problems.add_argument("--config", required=True, help="监控端点配置，如 config/patrol/monitors.json")
    p_problems.add_argument("--group", default=DEFAULT_GROUP, help="端点组名，默认 %s" % DEFAULT_GROUP)
    p_problems.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                            help="最多拉取条数（problem.get limit），默认 %d" % DEFAULT_LIMIT)
    p_problems.add_argument("--severities", default=None,
                            help="逗号分隔告警级别 0-5，如 3,4,5；缺省用配置 severities，两者都缺则全量")
    p_problems.add_argument("--out", default=DEFAULT_OUT_PROBLEMS,
                            help="输出 problems.json 路径，默认 %s" % DEFAULT_OUT_PROBLEMS)

    p_triage = sub.add_parser("triage", help="离线分诊 problems.json，按剧本库生成处置引导报告")
    p_triage.add_argument("--problems", required=True, help="problems 子命令产出的 problems.json 路径")
    p_triage.add_argument("--common", default=DEFAULT_COMMON,
                          help="通用处置剧本库，默认 %s" % DEFAULT_COMMON)
    p_triage.add_argument("--out", default=DEFAULT_OUT_GUIDE,
                          help="输出报告 markdown 路径，默认 %s" % DEFAULT_OUT_GUIDE)

    args = ap.parse_args(argv)
    if args.cmd == "problems":
        if args.limit < 1:
            stop("--limit 需为正整数（收到 %s）" % args.limit)
        run_problems(args.config, args.group, args.limit, parse_severities(args.severities), args.out)
    else:
        run_triage(args.problems, args.common, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
