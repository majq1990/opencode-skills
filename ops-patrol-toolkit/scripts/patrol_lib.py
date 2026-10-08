#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ops-patrol-toolkit 公共库。

全部脚本必须遵守的约定：
  1. 只依赖 Python 标准库，离线可跑，不引入第三方包
  2. stdout 最后一行输出结构化 JSON 信封：成功 {"ok": true, ...}；失败 {"ok": false, "gap": "..."}
  3. 控制台不使用 emoji（Windows GBK 兼容），中文正常输出
  4. 凭证只经环境变量引用名（*_env_ref）获取，绝不写进配置或代码
  5. 运行期产物只写 work/ 或显式 --out 指定的路径
"""

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config" / "patrol"
REFERENCES_DIR = ROOT / "references"
ASSETS_DIR = ROOT / "assets"
WORK_DIR = ROOT / "work"

EXIT_GAP = 2


def keyword_hit(keyword, text):
    """处置剧本关键词命中判定（供 06-09 号子工具的 match_playbook 统一使用）。

    ASCII 关键词在原文（保留大小写）上找命中位置，逐个判定词左边界：
      - 位置 0，或前一字符非字母数字（空格/标点/下划线/中文）→ 命中
      - 驼峰词首（前字符小写 + 当前字符大写，如 HighCpuLoad 里的 Cpu/Load）→ 命中
      - 其余词中片段（replication 里的 io、export 里的 port、EXPORT 里的 PORT）→ 不命中
    允许右向扩展（"connection" 命中 "connections"）；含非 ASCII（中文等）保持 contains。
    """
    kw = str(keyword or "").strip()
    src = str(text or "")
    if not kw:
        return False
    if kw.isascii():
        for m in re.finditer(re.escape(kw), src, re.IGNORECASE):
            pos = m.start()
            if pos == 0:
                return True
            prev = src[pos - 1]
            cur = src[pos]
            if not prev.isalnum():
                return True
            if cur.isupper() and prev.islower():
                return True
        return False
    return kw.lower() in src.lower()


def skill_path(*parts):
    """skill 内资源（config/references/assets/tests）的绝对路径。"""
    return ROOT.joinpath(*parts)


def work_path(*parts):
    """work/ 下运行期产物路径，父目录自动创建。"""
    p = WORK_DIR.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def emit(payload):
    """打印成功信封（应作为 stdout 最后一行）。"""
    payload = dict(payload)
    payload.setdefault("ok", True)
    print(json.dumps(payload, ensure_ascii=False))


def stop(gap, **kw):
    """打印 gap 信封并以退出码 2 结束。gap 必须是一句可行动的缺失说明，禁止静默兜底。"""
    payload = {"ok": False, "gap": gap}
    payload.update(kw)
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(EXIT_GAP)


def read_json(path):
    p = Path(path)
    if not p.is_file():
        stop("文件不存在: %s" % p)
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        stop("JSON 解析失败 %s: %s" % (p, e))


def load_config(name):
    """读取 config/patrol/<name>.json（缺 .json 后缀自动补）。"""
    if not str(name).endswith(".json"):
        name += ".json"
    return read_json(CONFIG_DIR / name)


def write_json(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return p


def write_text(path, text):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def parse_args(argv, defaults=None):
    """轻量参数解析：--key value / --key=value / 布尔 flag。

    键统一转下划线风格；非 -- 开头的位置参数收进 args["_pos"]。
    子命令型脚本（argparse）不必用它；单命令脚本用它保持风格统一。
    """
    args = dict(defaults or {})
    args.setdefault("_pos", [])
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--") and len(a) > 2:
            body = a[2:]
            if "=" in body:
                k, v = body.split("=", 1)
                args[k.replace("-", "_")] = v
            elif i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                args[body.replace("-", "_")] = argv[i + 1]
                i += 1
            else:
                args[body.replace("-", "_")] = True
        else:
            args["_pos"].append(a)
        i += 1
    return args


def require(args, *keys):
    """校验必填参数，缺失即 stop（不猜测、不默认）。"""
    missing = ["--" + k for k in keys if not args.get(k)]
    if missing:
        stop("缺少必填参数: %s" % " ".join(missing))


def to_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def as_bool(v):
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")
