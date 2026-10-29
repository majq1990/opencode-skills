# -*- coding: utf-8 -*-
"""信创迁移 skill 查询脚本 —— 调用 demo 上 redmine-assist 的 /query 接口检索公司知识库。

用途：
  1) 单问模式：python query_xc.py "灵珑平台迁移到达梦报错怎么处理"
  2) 多角度模式：python query_xc.py --sweep "达梦 迁移"   # 按内置 8 个信创迁移角度依次查询
  3) 指定服务：  python query_xc.py --host https://demo.egova.com.cn/redmine-assist "..."
     token 只从环境变量 REDMINE_ASSIST_TOKEN 读，脚本内不落任何凭据字面量。

输出：每个查询打印 markdown（含工单链接 + 钉钉知识库文档链接）。脚本只写 stdout，
      要落盘由调用方重定向（如 `python query_xc.py --sweep ... > sweep.md`）。

依赖：Python3 标准库（urllib），无第三方包。
编码：Windows 控制台自动 UTF-8。

安全边界（与 kb_query.py 同口径，2026-10-10 Mimosa 扫描后补齐）：
  * endpoint 只接受 https + *.egova.com.cn，且解析结果不得落入私网/环回/链路本地段；
  * 不提供任何 CLI 可控的写文件路径——一律写 stdout，由调用方决定落盘位置。
"""
import argparse
import io
import ipaddress
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_HOST = "https://demo.egova.com.cn/redmine-assist"
ALLOWED_HOST_SUFFIX = ".egova.com.cn"
TOKEN_ENV = "REDMINE_ASSIST_TOKEN"


def _force_utf8_console() -> None:
    """让 Windows 控制台正确显示中文。只在 __main__ 里调用——
    放在 import 期会把 pytest 的捕获流包坏，拆夹具时底层临时文件已关闭会崩 teardown。"""
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass

# 信创迁移 8 个检索角度（与知识库文档分类对齐）
SWEEP_ANGLES = [
    ("01_信创数据库迁移总览", "信创数据库迁移 从MySQL迁移到达梦 人大金仓 瀚高 openGauss 迁移步骤 注意事项"),
    ("02_达梦迁移", "达梦数据库 迁移 MySQL迁移达梦 数据迁移步骤 报错处理 启动失败"),
    ("03_人大金仓迁移", "人大金仓 KingbaseES 数据迁移 从MySQL迁移 部署 报错 兼容问题"),
    ("04_麒麟欧拉UOS部署", "银河麒麟 openEuler UOS 信创环境部署 系统适配 安装问题"),
    ("05_国产化中间件", "东方通 TongWeb 金蝶 宝兰德 国产中间件 部署 适配 信创"),
    ("06_国产CPU适配", "鲲鹏 飞腾 海光 CPU架构 信创 适配 编译 部署"),
    ("07_灵珑信创适配", "灵珑平台 信创 达梦 人大金仓 适配 部署 报错"),
    ("08_星桥信创适配", "星桥 信创 达梦 人大金仓 数据源适配 部署"),
]


def validate_endpoint(url: str) -> str:
    """endpoint 边界校验：仅 https、仅公司域名、解析结果不得落入私网/环回/链路本地段。"""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise SystemExit(f"[xc] endpoint 必须是 https，拒绝：{url}")
    host = (parsed.hostname or "").lower()
    if not host.endswith(ALLOWED_HOST_SUFFIX):
        raise SystemExit(f"[xc] endpoint 主机不在允许范围（*{ALLOWED_HOST_SUFFIX}），拒绝：{host}")
    try:
        infos = socket.getaddrinfo(host, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise SystemExit(f"[xc] 域名解析失败 {host}: {exc}")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            raise SystemExit(f"[xc] {host} 解析到受限地址 {ip}，拒绝请求")
    return url


def load_token() -> str:
    """token 只从环境变量读；缺失即退出并提示获取途径，不在源码留凭据。"""
    token = os.environ.get(TOKEN_ENV, "").strip()
    if not token:
        raise SystemExit(
            f"[xc] 未设置 {TOKEN_ENV}：请 export {TOKEN_ENV}=<扫码拿到的 token>"
            "（https://demo.egova.com.cn/oauth/dingtalk/login 钉钉扫码，401=过期需重扫）"
        )
    return token


def call_query(query: str, host: str, token: str, timeout: int = 180) -> dict:
    """调用 /query 接口，返回响应 dict。"""
    endpoint = validate_endpoint(host.rstrip("/") + "/query")
    body = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Precheck-Token": token,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser(description="信创迁移知识库检索（demo redmine-assist /query）")
    ap.add_argument("query", nargs="?", help="要检索的问题（单问模式）")
    ap.add_argument("--sweep", action="store_true", help="多角度模式：按 8 个信创迁移角度依次检索")
    ap.add_argument("--host", default=DEFAULT_HOST, help=f"接口地址，默认 {DEFAULT_HOST}")
    ap.add_argument("--timeout", type=int, default=180, help="单次请求超时秒数，默认 180")
    args = ap.parse_args()

    if not args.query and not args.sweep:
        ap.error("必须提供 query 或 --sweep")

    token = load_token()

    def run_one(name: str, q: str):
        print("=" * 70)
        print(f"[{name}] 问题：{q}")
        print("=" * 70)
        try:
            r = call_query(q, args.host, token, args.timeout)
            md = r.get("markdown", "")
            stats = r.get("stats", {})
            print(md)
            print(f"\n>>> 本次检索: {stats.get('n_issues','?')} 工单 / {stats.get('n_docs','?')} 文档片段")
        except urllib.error.HTTPError as e:
            print(f"[FAIL] HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:300]}")
        except Exception as e:
            print(f"[FAIL] {e}")
        print()
        time.sleep(2)

    if args.sweep:
        for name, q in SWEEP_ANGLES:
            run_one(name, q)
    else:
        run_one("query_result", args.query)


if __name__ == "__main__":
    _force_utf8_console()
    main()
