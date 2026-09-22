# -*- coding: utf-8 -*-
"""安全案件三源研判子系统的共用库（v2.0 自 security-case-handling 移植）。

约定（沿用原实现）：
1) 所有脚本只依赖 Python 标准库，离线可跑；
2) stdout 一律输出结构化 JSON（ok/gap），便于上层解析与留痕；
3) 控制台不使用 emoji，避免 Windows GBK 控制台 UnicodeEncodeError；
4) 凭证只通过环境变量引用名获取，禁止写入配置文件与日志。

与原 _lib.py 的差异：配置目录固定为本 skill 的 config/security_case/，
运行期产物统一落在 work/security_case/ 下（不入 git）。
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(ROOT, "config", "security_case")
WORK_DIR = os.path.join(ROOT, "work", "security_case")


def skill_path(*parts):
    """以 Skill 根目录解析路径，避免相对路径随调用目录漂移。"""
    return os.path.join(ROOT, *parts)


def work_path(*parts):
    """运行期产物路径（cache/output/progress 均在 work/security_case 下）。"""
    return os.path.join(WORK_DIR, *parts)


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def stop(gap, **kw):
    payload = {"ok": False, "gap": gap}
    payload.update(kw)
    emit(payload)
    sys.exit(2)


def read_json(path):
    if not os.path.exists(path):
        return None, "文件不存在: %s" % path
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, "JSON 解析失败: %s -> %s" % (path, e)


def load_config(name):
    path = os.path.join(CONFIG_DIR, name)
    data, err = read_json(path)
    if err:
        return None, err
    return data, None


def write_text(path, text):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def write_json(path, data):
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2))


def parse_args(argv, defaults=None):
    opts = dict(defaults or {})
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            key = a[2:]
            if "=" in key:
                key, val = key.split("=", 1)
                opts[key] = val
                i += 1
                continue
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                opts[key] = argv[i + 1]
                i += 2
                continue
            opts[key] = "true"
            i += 1
            continue
        i += 1
    return opts


def parse_repeated(argv, flag):
    """收集可重复出现的 --flag 值（如 --cve 可传多个）。"""
    values = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == flag:
            if i + 1 < len(argv):
                values.append(argv[i + 1])
                i += 2
                continue
            i += 1
            continue
        if a.startswith(flag + "="):
            values.append(a[len(flag) + 1:])
        i += 1
    return values


def norm_date(s):
    """把 2026/09/02、2026.9.2、2026-9-2 归一成 2026-09-02；不可解析返回 None。"""
    if s is None:
        return None
    s = str(s).strip().replace("/", "-").replace(".", "-")
    parts = s.split("-")
    if len(parts) != 3:
        return None
    try:
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        if not (1970 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31):
            return None
        return "%04d-%02d-%02d" % (y, m, d)
    except Exception:
        return None


def to_float(v):
    """cvss_score 可能是字符串 "7.5"，统一转 float；不可转返回 None。"""
    if v is None or isinstance(v, bool):
        return None
    try:
        return float(str(v).strip())
    except Exception:
        return None


def norm_enum(v, allowed, aliases=None):
    """大小写/空格/中文脏值归一，例如 " medium" / "INTERNAL" / "高危"。"""
    if v is None:
        return None
    key = str(v).strip().lower()
    aliases = aliases or {}
    key = aliases.get(key, key)
    return key if key in allowed else None
