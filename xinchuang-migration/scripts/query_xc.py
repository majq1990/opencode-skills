# -*- coding: utf-8 -*-
"""信创迁移 skill 查询脚本 —— 调用 demo 上 redmine-assist 的 /query 接口检索公司知识库。

用途：
  1) 单问模式：python query_xc.py "灵珑平台迁移到达梦报错怎么处理"
  2) 多角度模式：python query_xc.py --sweep "达梦 迁移"   # 按内置 8 个信创迁移角度依次查询
  3) 指定服务：  python query_xc.py --host http://demo.egova.com.cn/redmine-assist --token <token> "..."

输出：每个查询打印 markdown（含工单链接 + 钉钉知识库文档链接），并可选保存到 --out 目录。

依赖：Python3 标准库（urllib），无第三方包。
编码：Windows 控制台自动 UTF-8。
"""
import argparse
import io
import json
import os
import sys
import time
import urllib.request

# 让 Windows 控制台正确显示中文
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
except Exception:
    pass

DEFAULT_HOST = "https://demo.egova.com.cn/redmine-assist"
DEFAULT_TOKEN = "4bcf27f056979d06bcfb14725680cc64"

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


def call_query(query: str, host: str, token: str, timeout: int = 180) -> dict:
    """调用 /query 接口，返回响应 dict。"""
    body = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        host.rstrip("/") + "/query",
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
    ap.add_argument("--token", default=DEFAULT_TOKEN, help="鉴权 token")
    ap.add_argument("--out", default=None, help="结果保存目录（可选），单问模式存 query_result.md")
    ap.add_argument("--timeout", type=int, default=180, help="单次请求超时秒数，默认 180")
    args = ap.parse_args()

    if not args.query and not args.sweep:
        ap.error("必须提供 query 或 --sweep")

    if args.out:
        os.makedirs(args.out, exist_ok=True)

    def run_one(name: str, q: str):
        print("=" * 70)
        print(f"[{name}] 问题：{q}")
        print("=" * 70)
        try:
            r = call_query(q, args.host, args.token, args.timeout)
            md = r.get("markdown", "")
            stats = r.get("stats", {})
            print(md)
            print(f"\n>>> 本次检索: {stats.get('n_issues','?')} 工单 / {stats.get('n_docs','?')} 文档片段")
            if args.out:
                fn = os.path.join(args.out, name + ".md")
                with open(fn, "w", encoding="utf-8") as f:
                    f.write(md + f"\n\n>>> 本次检索: {stats.get('n_issues','?')} 工单 / {stats.get('n_docs','?')} 文档片段\n")
                print(f">>> 已保存: {fn}")
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
    main()
