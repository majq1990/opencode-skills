#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
08 Prometheus 告警拉取与离线分诊（两阶段 CLI，triage 可离线复跑）。

alerts 阶段（联网，出站必经 monitor_http 安全闸）：
  1. GET {url}/api/v1/alerts 拉取当前告警列表（url 尾部多余斜杠自动归一，避免双斜杠）
  2. 归一化为统一 findings 结构落盘 alerts.json（任何 token 都不落盘）

triage 阶段（纯离线）：
  读 alerts.json，按（标题 + labels.alertname + 描述）小写关键词匹配
  references/playbooks/common_playbooks.json 的处置剧本（contains，按库内顺序
  首个命中生效）；未命中给通用兜底 3 步（确认现象影响 / 查 PromQL 与规则
  annotations.runbook_url（如有则列出）/ 用 05 号子工具检索历史案例）；
  按 critical -> warning -> info 排序生成处置引导报告 guide.md（头部带【待复核】标记）。

用法:
  python scripts/08_prometheus_triage.py alerts --config config/patrol/monitors.json [--group prometheus] [--out work/prometheus/alerts.json]
  python scripts/08_prometheus_triage.py triage --alerts work/prometheus/alerts.json [--common references/playbooks/common_playbooks.json] [--out work/prometheus/guide.md]

凭证：token 只经环境变量注入（名字由 monitors.json <group>.token_env_ref 声明），
绝不落盘；测试全部走本地假服务（127.0.0.1），绝不真实联网。
"""

import argparse
import json
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import patrol_lib  # noqa: E402
from patrol_lib import as_bool, emit, read_json, stop, write_json, write_text  # noqa: E402
from monitor_http import MonitorHttpError, http_get_json, load_monitor_config  # noqa: E402

__version__ = "1.0.0"

DEFAULT_GROUP = "prometheus"
DEFAULT_OUT_ALERTS = "work/prometheus/alerts.json"
DEFAULT_OUT_GUIDE = "work/prometheus/guide.md"
DEFAULT_COMMON = "references/playbooks/common_playbooks.json"

# severity 归一映射与报告分块顺序（critical 最高）
SEVERITY_NORM = {"critical": "critical", "firing": "critical",
                 "warning": "warning", "warn": "warning"}
SEVERITY_ORDER = ["critical", "warning", "info"]


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------

def _one_line(text):
    """压平空白成单行（标题/描述/主机进报告与示例命令用）。"""
    return " ".join(str(text or "").split())


def norm_severity_label(raw):
    """labels.severity -> critical/warning/info（critical|firing/warning|warn/其余）。"""
    s = str(raw or "").strip().lower()
    if s in SEVERITY_NORM:
        return SEVERITY_NORM[s]
    return "info"


def build_alerts_url(base_url):
    """Prometheus 根地址 -> {根}/api/v1/alerts；尾部多余斜杠归一避免双斜杠。"""
    return str(base_url or "").rstrip("/") + "/api/v1/alerts"


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


def count_by_severity(findings):
    """按 critical -> warning -> info 统计各级条数，未知标签追加在最后。"""
    counts = {}
    for f in findings:
        label = str(f.get("severity_label") or "info") if isinstance(f, dict) else "info"
        counts[label] = counts.get(label, 0) + 1
    ordered = {}
    for label in SEVERITY_ORDER:
        if label in counts:
            ordered[label] = counts[label]
    for label, n in counts.items():
        if label not in ordered:
            ordered[label] = n
    return ordered


# ---------------------------------------------------------------------------
# alerts 阶段：Prometheus HTTP API 拉取 + 归一化落盘
# ---------------------------------------------------------------------------

def normalize_alert(alert):
    """/api/v1/alerts 的原始条目 -> 统一 findings 结构（labels/annotations 原样保留）。"""
    a = alert if isinstance(alert, dict) else {}
    labels = a.get("labels") if isinstance(a.get("labels"), dict) else {}
    annotations = a.get("annotations") if isinstance(a.get("annotations"), dict) else {}
    alertname = _one_line(labels.get("alertname")) or "unknown"
    instance = _one_line(labels.get("instance"))
    node = _one_line(labels.get("node"))
    active_at = a.get("activeAt") or a.get("active_at")
    raw_value = a.get("value")
    return {
        "source": "prometheus",
        "id": "%s@%s" % (alertname, instance or "unknown"),
        "title": _one_line(annotations.get("summary")) or alertname,
        "host": instance or node or "unknown",
        "severity_label": norm_severity_label(labels.get("severity")),
        "state": str(a.get("state") or ""),
        "active_at": str(active_at or ""),
        "value": "" if raw_value is None else str(raw_value),
        "description": _one_line(annotations.get("description")),
        "labels": labels,
        "annotations": annotations,
    }


def fetch_findings(cfg):
    """GET /api/v1/alerts 拉取并归一化，任何失败一律 gap（不猜测不伪装成功）。"""
    url = build_alerts_url(cfg["url"])
    token = str(cfg.get("_token") or "").strip()
    try:
        status, resp = http_get_json(
            url,
            token=token or None,
            timeout_s=int(cfg.get("timeout_s") or 60),
            allow_local=as_bool(cfg.get("allow_local_targets")),
            allow_private=as_bool(cfg.get("allow_private_targets")),
        )
    except MonitorHttpError as e:
        stop("Prometheus API 请求失败（%s，GET %s）：%s" % (e.kind, url, e.message))
    except (TypeError, ValueError) as e:
        stop("Prometheus 配置不合法（timeout_s 等）：%s" % e)
    if not isinstance(resp, dict):
        stop("Prometheus API 响应不是 JSON 对象（HTTP %s）" % status)
    if resp.get("status") != "success":
        detail = json.dumps(resp, ensure_ascii=False, default=str)[:200]
        stop("Prometheus API 返回 status=%r（非 success）：%s" % (resp.get("status"), detail))
    data = resp.get("data")
    alerts = data.get("alerts") if isinstance(data, dict) else None
    if not isinstance(alerts, list):
        stop("Prometheus API 响应缺少 data.alerts 数组，结构不符合预期")
    return [normalize_alert(a) for a in alerts]


def run_alerts(config_path, group, out):
    """拉取当前告警并落盘 alerts.json，打印成功信封。"""
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
        stop("环境变量 %s 未设置（monitors.json %s.token_env_ref），无法认证 Prometheus；"
             "请设置该环境变量后重试（token 只进环境变量，绝不落盘）" % (token_ref, group))

    findings = fetch_findings(cfg)
    doc = {
        "version": "1.0",
        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "prometheus",
        "endpoint": endpoint_of(build_alerts_url(cfg["url"])),
        "findings": findings,
    }
    out_path = resolve_out(out)
    write_json(out_path, doc)
    print("[08] alerts: 端点 %s（组 %s）拉取到 %d 条活动告警，已落盘"
          % (doc["endpoint"], group, len(findings)))
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

def match_playbook(finding, playbooks):
    """（标题 + labels.alertname + 描述）对每个剧本 match_keywords 做边界感知命中
    （patrol_lib.keyword_hit：保留原文判定驼峰词首/词左边界，内部忽略大小写；
    调用侧不得先 lower，否则 HighCpuLoad 这类驼峰告警名的词首信息会被销毁），
    按库内顺序首个命中返回，否则 None。"""
    labels = finding.get("labels") if isinstance(finding.get("labels"), dict) else {}
    hay = " ".join([
        str(finding.get("title") or ""),
        str(labels.get("alertname") or ""),
        str(finding.get("description") or ""),
    ])
    for pb in playbooks or []:
        if not isinstance(pb, dict):
            continue
        for kw in pb.get("match_keywords") or []:
            if patrol_lib.keyword_hit(kw, hay):
                return pb
    return None


def fallback_steps(finding):
    """未命中剧本的通用兜底 3 步（确认现象影响 / 查 PromQL 与规则 runbook_url /
    用 05 号子工具检索历史案例，附示例命令）。"""
    title = _one_line(finding.get("title") or "未知告警")
    host = _one_line(finding.get("host") or "目标实例")
    annotations = finding.get("annotations") if isinstance(finding.get("annotations"), dict) else {}
    labels = finding.get("labels") if isinstance(finding.get("labels"), dict) else {}
    runbook = _one_line(annotations.get("runbook_url") or labels.get("runbook_url"))
    if runbook:
        step2 = ("查告警规则：在 Prometheus Rules 中查看该告警的 PromQL 表达式与采集口径，"
                 "按声明的 runbook 处置：%s" % runbook)
    else:
        step2 = ("查告警规则：在 Prometheus Rules 中查看该告警的 PromQL 表达式与采集口径，"
                 "若规则 annotations.runbook_url 有值则按其处置手册操作")
    return [
        "确认现象影响：登录 Prometheus 控制台（Alerts 页）核对该告警的 state 与持续时间，"
        "结合标签定位受影响实例，评估业务影响面",
        step2,
        "检索历史案例：用本工具集 05 号子工具查历史相似工单与知识库，示例命令："
        'python scripts/05_kb_similar_search.py query --text "%s %s 告警排查"' % (title, host),
    ]


def _sev_rank(finding):
    """报告分块排序键：critical(0) -> warning(1) -> info(2)，未知排最后。"""
    return SEVERITY_ORDER.index(finding.get("severity_label")) \
        if finding.get("severity_label") in SEVERITY_ORDER else len(SEVERITY_ORDER)


def render_report(doc, findings, playbooks):
    """生成处置引导报告 markdown，返回 (文本, matched, unmatched)。"""
    ordered = sorted(findings, key=_sev_rank)  # critical -> warning -> info，同级保持拉取顺序
    matched = 0
    blocks = []
    for idx, f in enumerate(ordered, 1):
        if not isinstance(f, dict):
            f = {"title": str(f)}
        pb = match_playbook(f, playbooks)
        if pb:
            matched += 1
            steps = [str(s) for s in (pb.get("steps") or [])]
            pb_line = "处置剧本：%s（%s）" % (pb.get("title") or pb.get("id") or "", pb.get("id") or "")
        else:
            steps = fallback_steps(f)
            pb_line = "处置剧本：无（未命中剧本库，使用通用兜底步骤）"
        label = str(f.get("severity_label") or "info")
        blocks.extend([
            "## %d. [%s] %s" % (idx, label, _one_line(f.get("title") or "（无标题）")),
            "",
            "- 告警 ID：%s" % f.get("id", ""),
            "- 实例：%s" % (f.get("host") or "（未知实例）"),
            "- 严重度：%s" % label,
            "- 触发时间：%s" % (f.get("active_at") or "（未知）"),
            "- 当前值：%s" % (f.get("value") or "（未知）"),
            "- 描述：%s" % (_one_line(f.get("description")) or "（无）"),
            "- %s" % pb_line,
            "- 处置步骤：",
            "",
        ])
        for j, s in enumerate(steps, 1):
            blocks.append("   %d. %s" % (j, s))
        blocks.append("")
    unmatched = len(ordered) - matched
    header = [
        "# Prometheus 告警分诊处置引导",
        "",
        "**【待复核】** 本报告由 ops-patrol-toolkit 08 号子工具自动生成，未经人工复核不得外发。",
        "",
        "- 生成时间：%s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "- 数据来源：Prometheus API（%s）" % (doc.get("endpoint") or "未知端点"),
        "- 告警总数：%d（剧本命中 %d / 通用兜底 %d）" % (len(ordered), matched, unmatched),
        "",
    ]
    tail = [
        "---",
        "说明：以上处置步骤为引导建议，执行前需人工确认并在测试环境验证；"
        "对未命中剧本的告警可用 05 号子工具检索历史相似案例辅助定位。",
    ]
    return "\n".join(header + blocks + tail) + "\n", matched, unmatched


def run_triage(alerts_path, common_path, out):
    """读 alerts.json 离线分诊并生成处置引导报告，打印成功信封。"""
    doc = read_json(alerts_path)  # 缺文件/坏 JSON 由 patrol_lib 统一 gap
    if not isinstance(doc, dict) or "findings" not in doc:
        stop("alerts 文件缺少 findings 键，结构不符合约定：%s（请先运行 alerts 子命令拉取）" % alerts_path)
    raw_findings = doc.get("findings")
    if not isinstance(raw_findings, list):
        stop("alerts 文件的 findings 键不是数组，结构不符合约定：%s" % alerts_path)
    findings = [f if isinstance(f, dict) else {"title": str(f)} for f in raw_findings]

    playbooks = []
    if common_path:
        common = read_json(common_path)
        playbooks = common.get("playbooks") or [] if isinstance(common, dict) else []

    report_text, matched, unmatched = render_report(doc, findings, playbooks)
    out_path = resolve_out(out)
    write_text(out_path, report_text)
    print("[08] triage: 剧本命中 %d 条，通用兜底 %d 条，报告已生成" % (matched, unmatched))
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
        prog="08_prometheus_triage.py",
        description="Prometheus 告警拉取与离线分诊：alerts 联网拉取落盘，triage 离线生成处置引导报告",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_alerts = sub.add_parser("alerts", help="从 Prometheus 拉取当前告警（GET /api/v1/alerts）并归一化落盘")
    p_alerts.add_argument("--config", required=True, help="监控端点配置，如 config/patrol/monitors.json")
    p_alerts.add_argument("--group", default=DEFAULT_GROUP, help="端点组名，默认 %s" % DEFAULT_GROUP)
    p_alerts.add_argument("--out", default=DEFAULT_OUT_ALERTS,
                          help="输出 alerts.json 路径，默认 %s" % DEFAULT_OUT_ALERTS)

    p_triage = sub.add_parser("triage", help="离线分诊 alerts.json，按剧本库生成处置引导报告")
    p_triage.add_argument("--alerts", required=True, help="alerts 子命令产出的 alerts.json 路径")
    p_triage.add_argument("--common", default=DEFAULT_COMMON,
                          help="通用处置剧本库，默认 %s" % DEFAULT_COMMON)
    p_triage.add_argument("--out", default=DEFAULT_OUT_GUIDE,
                          help="输出报告 markdown 路径，默认 %s" % DEFAULT_OUT_GUIDE)

    args = ap.parse_args(argv)
    if args.cmd == "alerts":
        run_alerts(args.config, args.group, args.out)
    else:
        run_triage(args.alerts, args.common, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
