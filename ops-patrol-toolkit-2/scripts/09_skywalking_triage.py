#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09 SkyWalking 告警拉取与离线分诊（两阶段 CLI，triage 可离线复跑）。

alarms 阶段（联网，出站必经 monitor_http 安全闸）：
  1. GraphQL：POST {url}，payload = {"query": <monitors.json skywalking.alarm_query 或默认值>,
     "variables": {"duration": <配置 duration 或 --duration 覆盖>}}
  2. 响应含非空 errors -> gap（带 message）；data.alarms 缺失或非列表 -> gap
  3. 归一化为统一 findings 结构落盘 alarms.json（字段尽量兼容 OAP 版本差异，缺失补空；
     任何 token 都不落盘）

triage 阶段（纯离线）：
  读 alarms.json，按（告警标题 + 服务名）小写后对剧本库 match_keywords 做 contains 匹配
  （按 references/playbooks/common_playbooks.json 库内顺序首个命中生效）；
  未命中给通用兜底 3 步；按拉取顺序生成处置引导报告 guide.md（头部带【待复核】标记）。

用法:
  python scripts/09_skywalking_triage.py alarms --config config/patrol/monitors.json [--group skywalking] [--duration "minutes:60"] [--out work/skywalking/alarms.json]
  python scripts/09_skywalking_triage.py triage --alarms work/skywalking/alarms.json [--common references/playbooks/common_playbooks.json] [--out work/skywalking/guide.md]

凭证：token 只经环境变量注入（名字由 monitors.json skywalking.token_env_ref 声明，可为空），
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
from monitor_http import MonitorHttpError, http_post_json, load_monitor_config  # noqa: E402

__version__ = "1.0.0"

DEFAULT_GROUP = "skywalking"
DEFAULT_DURATION = "minutes:60"
DEFAULT_QUERY = ("query ($duration: Duration!) { alarms: queryAlarms(duration: $duration) "
                 "{ key id message startTime } }")
DEFAULT_OUT_ALARMS = "work/skywalking/alarms.json"
DEFAULT_OUT_GUIDE = "work/skywalking/guide.md"
DEFAULT_COMMON = "references/playbooks/common_playbooks.json"

TITLE_MAX_LEN = 120


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------

def _one_line(text):
    """压平空白成单行（标题/服务名/消息进报告与示例命令用）。"""
    return " ".join(str(text or "").split())


def truncate_title(text, limit=TITLE_MAX_LEN):
    """标题截断到 limit 字符，超长以 ... 结尾。"""
    t = _one_line(text)
    if len(t) <= limit:
        return t
    return t[:limit] + "..."


def epoch_to_str(epoch):
    """Unix 秒 -> "YYYY-MM-DD HH:MM:SS"（本地时区）；0/负值/非法给空串。"""
    try:
        epoch = int(epoch)
    except (TypeError, ValueError):
        return ""
    if epoch <= 0:
        return ""
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")


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


def resolve_duration(cli_duration, cfg):
    """告警时间窗：--duration 覆盖 > 配置 duration > 默认 minutes:60。"""
    d = str(cli_duration or "").strip()
    if d:
        return d
    d = str(cfg.get("duration") or "").strip()
    return d or DEFAULT_DURATION


# ---------------------------------------------------------------------------
# alarms 阶段：SkyWalking GraphQL 拉取 + 归一化落盘
# ---------------------------------------------------------------------------

def normalize_alarm(entry, index):
    """queryAlarms 原始条目 -> 统一 findings 结构（字段尽量兼容版本差异，缺失补空）。"""
    a = entry if isinstance(entry, dict) else {}
    ident = a.get("key") or a.get("id") or str(index)
    scope = a.get("name") or a.get("scope") or a.get("service") or "unknown"
    message = _one_line(a.get("message"))
    title = (truncate_title(message) or _one_line(a.get("name"))
             or _one_line(a.get("id")) or str(index))
    return {
        "source": "skywalking",
        "id": str(ident),
        "title": title,
        "scope": _one_line(scope),
        "started_at": epoch_to_str(a.get("startTime")),
        "message": message,
        "raw": a,
    }


def graphql_alarms(cfg, duration, query, group):
    """发一条 GraphQL 查询（必经 monitor_http 安全闸），返回 data.alarms 列表。

    响应含非空 errors 即 gap（带 message）；data.alarms 缺失或非列表即 gap；
    网络/超时/非 JSON 统一转 gap。
    """
    payload = {"query": query, "variables": {"duration": duration}}
    try:
        status, resp = http_post_json(
            cfg["url"], payload,
            token=cfg.get("_token") or None,
            timeout_s=int(cfg.get("timeout_s") or 60),
            allow_local=as_bool(cfg.get("allow_local_targets")),
            allow_private=as_bool(cfg.get("allow_private_targets")),
        )
    except MonitorHttpError as e:
        stop("SkyWalking GraphQL 请求失败（%s）：%s" % (e.kind, e.message))
    except (TypeError, ValueError) as e:
        stop("SkyWalking 配置不合法（timeout_s 等）：%s" % e)
    if not isinstance(resp, dict):
        stop("SkyWalking GraphQL 响应不是 JSON 对象（HTTP %s）" % status)
    errors = resp.get("errors")
    if errors:
        if isinstance(errors, list) and errors and isinstance(errors[0], dict):
            msg = "; ".join(str(e.get("message") or "") for e in errors
                            if isinstance(e, dict) and e.get("message"))
        else:
            msg = json.dumps(errors, ensure_ascii=False)
        stop("SkyWalking GraphQL 返回 errors：%s" % (msg or "（无 message）"))
    data = resp.get("data")
    alarms = data.get("alarms") if isinstance(data, dict) else None
    if not isinstance(alarms, list):
        stop("SkyWalking GraphQL 响应缺少 data.alarms 列表字段（OAP 版本间返回结构有差异，"
             "可按 monitors.json %s.alarm_query 调整查询后重试）" % group)
    return alarms


def run_alarms(config_path, group, cli_duration, out):
    """拉取 SkyWalking 告警并落盘 alarms.json，打印成功信封。"""
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
        stop("环境变量 %s 未设置（monitors.json %s.token_env_ref），无法认证 SkyWalking OAP；"
             "请设置该环境变量后重试（token 只进环境变量，绝不落盘）" % (token_ref, group))

    duration = resolve_duration(cli_duration, cfg)
    query = str(cfg.get("alarm_query") or "").strip() or DEFAULT_QUERY
    raw_alarms = graphql_alarms(cfg, duration, query, group)
    findings = [normalize_alarm(a, i) for i, a in enumerate(raw_alarms, 1)]
    doc = {
        "version": "1.0",
        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "skywalking",
        "endpoint": endpoint_of(cfg["url"]),
        "duration": duration,
        "findings": findings,
    }
    out_path = resolve_out(out)
    write_json(out_path, doc)
    print("[09] alarms: 端点 %s（组 %s，duration=%s）拉取到 %d 条告警，已落盘"
          % (doc["endpoint"], group, duration, len(findings)))
    payload = {
        "total": len(findings),
        "endpoint": doc["endpoint"],
        "duration": duration,
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
    """（标题 + 服务名）对每个剧本 match_keywords 做边界感知命中
    （patrol_lib.keyword_hit：保留原文判定驼峰词首/词左边界，内部忽略大小写；
    调用侧不得先 lower），按库内顺序首个命中返回，否则 None。"""
    f = finding if isinstance(finding, dict) else {}
    text = "%s %s" % (f.get("title") or "", f.get("scope") or "")
    for pb in playbooks or []:
        if not isinstance(pb, dict):
            continue
        for kw in pb.get("match_keywords") or []:
            if patrol_lib.keyword_hit(kw, text):
                return pb
    return None


def fallback_steps(finding):
    """未命中剧本的通用兜底 3 步（确认 APM 链路与指标 / 查告警规则与 webhooks /
    用 05 号子工具检索历史案例）。"""
    f = finding if isinstance(finding, dict) else {}
    title = _one_line(f.get("title") or "未知告警")
    scope = _one_line(f.get("scope") or "unknown")
    return [
        "确认 APM 链路与指标：登录 SkyWalking UI 查看服务 %s 在告警时段的链路追踪（Trace）"
        "与关键指标（SLA/响应时间/吞吐量），确认现象真实存在并评估业务影响面" % scope,
        "查告警规则与 webhooks：核对 OAP alarm-settings.yml 中触发该告警的规则阈值，"
        "以及 webhooks 通知配置是否正确送达",
        "检索历史案例：用本工具集 05 号子工具查历史相似工单与知识库，示例命令："
        'python scripts/05_kb_similar_search.py query --text "%s %s 告警排查"' % (title, scope),
    ]


def render_report(doc, findings, playbooks):
    """生成处置引导报告 markdown，返回 (文本, matched, unmatched)。"""
    matched = 0
    blocks = []
    for idx, f in enumerate(findings, 1):
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
        blocks.extend([
            "## %d. %s" % (idx, _one_line(f.get("title") or "（无标题）")),
            "",
            "- 告警 ID：%s" % f.get("id", ""),
            "- 服务/范围：%s" % (_one_line(f.get("scope")) or "（未知服务）"),
            "- 开始时间：%s" % (f.get("started_at") or "（未知）"),
            "- 告警消息：%s" % (_one_line(f.get("message")) or _one_line(f.get("title")) or "（无消息）"),
            "- %s" % pb_line,
            "- 处置步骤：",
            "",
        ])
        for j, s in enumerate(steps, 1):
            blocks.append("   %d. %s" % (j, s))
        blocks.append("")
    unmatched = len(findings) - matched
    header = [
        "# SkyWalking 告警分诊处置引导",
        "",
        "**【待复核】** 本报告由 ops-patrol-toolkit 09 号子工具自动生成，未经人工复核不得外发。",
        "",
        "- 生成时间：%s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "- 数据来源：SkyWalking OAP GraphQL（%s）" % (doc.get("endpoint") or "未知端点"),
        "- 告警时间窗：%s" % (doc.get("duration") or "未知"),
        "- 告警总数：%d（剧本命中 %d / 通用兜底 %d）" % (len(findings), matched, unmatched),
        "",
    ]
    tail = [
        "---",
        "说明：以上处置步骤为引导建议，执行前需人工确认并在测试环境验证；"
        "对未命中剧本的告警可用 05 号子工具检索历史相似案例辅助定位。",
    ]
    return "\n".join(header + blocks + tail) + "\n", matched, unmatched


def run_triage(alarms_path, common_path, out):
    """读 alarms.json 离线分诊并生成处置引导报告，打印成功信封。"""
    doc = read_json(alarms_path)  # 缺文件/坏 JSON 由 patrol_lib 统一 gap
    if not isinstance(doc, dict) or "findings" not in doc:
        stop("alarms 文件缺少 findings 键，结构不符合约定：%s（请先运行 alarms 子命令拉取）" % alarms_path)
    raw_findings = doc.get("findings")
    if not isinstance(raw_findings, list):
        stop("alarms 文件的 findings 键不是数组，结构不符合约定：%s" % alarms_path)
    findings = [f if isinstance(f, dict) else {"title": str(f)} for f in raw_findings]

    playbooks = []
    if common_path:
        common = read_json(common_path)
        playbooks = common.get("playbooks") or [] if isinstance(common, dict) else []

    report_text, matched, unmatched = render_report(doc, findings, playbooks)
    out_path = resolve_out(out)
    write_text(out_path, report_text)
    print("[09] triage: 剧本命中 %d 条，通用兜底 %d 条，报告已生成" % (matched, unmatched))
    emit({
        "total": len(findings),
        "matched": matched,
        "unmatched": unmatched,
        "report": str(out_path),
    })
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="09_skywalking_triage.py",
        description="SkyWalking 告警拉取与离线分诊：alarms 联网 GraphQL 拉取落盘，"
                    "triage 离线生成处置引导报告",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_alarms = sub.add_parser("alarms", help="从 SkyWalking OAP 拉取告警（GraphQL queryAlarms）并归一化落盘")
    p_alarms.add_argument("--config", default="config/patrol/monitors.json",
                          help="监控端点配置，默认 config/patrol/monitors.json")
    p_alarms.add_argument("--group", default=DEFAULT_GROUP, help="端点组名，默认 %s" % DEFAULT_GROUP)
    p_alarms.add_argument("--duration", default=None,
                          help='告警时间窗（OAP Duration），如 "minutes:60"；缺省用配置 duration')
    p_alarms.add_argument("--out", default=DEFAULT_OUT_ALARMS,
                          help="输出 alarms.json 路径，默认 %s" % DEFAULT_OUT_ALARMS)

    p_triage = sub.add_parser("triage", help="离线分诊 alarms.json，按剧本库生成处置引导报告")
    p_triage.add_argument("--alarms", required=True, help="alarms 子命令产出的 alarms.json 路径")
    p_triage.add_argument("--common", default=DEFAULT_COMMON,
                          help="通用处置剧本库，默认 %s" % DEFAULT_COMMON)
    p_triage.add_argument("--out", default=DEFAULT_OUT_GUIDE,
                          help="输出报告 markdown 路径，默认 %s" % DEFAULT_OUT_GUIDE)

    args = ap.parse_args(argv)
    if args.cmd == "alarms":
        run_alarms(args.config, args.group, args.duration, args.out)
    else:
        run_triage(args.alarms, args.common, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
