# -*- coding: utf-8 -*-
"""路径安全与文件 IO（本地 CLI，路径来自用户命令行参数）。

safe_path 规范化并校验路径：绝对化、消解 . 与 .. 拼接形态，规范化后
残留向上跳转段时显式拒绝。

写入函数采用「目录 + 文件名」二段式：写入目标被限制在调用方声明的输出
目录内，文件名经 basename 清洗，不得携带路径片段。
"""
import os
import re
import csv
import json
import hashlib


class GapError(Exception):
    """前置条件不满足——必须停止，不得用兜底默认值继续。"""


def safe_path(path):
    """规范化并校验路径；规范化后残留向上跳转段即拒绝。"""
    if not path:
        return path
    p = os.path.abspath(os.path.expanduser(str(path)))
    parts = p.replace("/", os.sep).split(os.sep)
    if os.pardir in parts:
        raise GapError("路径含向上跳转段，已拒绝：%s" % path)
    return p


# 兼容别名
_normpath = safe_path


def skill_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_json(path, required=True, default=None):
    path = safe_path(path)
    if not path:
        if required:
            raise GapError("未提供文件路径")
        return default
    if not os.path.isfile(path):
        if required:
            raise GapError("必需文件不存在：%s" % path)
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise GapError("不是合法 JSON：%s（%s）" % (path, e))


def load_rules(name, required=True):
    """从 config/ 读取规则文件；name 为 config 目录下的文件名（不拼路径片段）。"""
    safe_name = os.path.basename(str(name or ""))
    if safe_name != name:
        raise GapError("规则文件名不得含路径分隔符：%s" % name)
    return load_json(os.path.join(skill_root(), "config", safe_name), required=required)


def _write_target(outdir, filename):
    """构造写入目标：限制在声明目录内；filename 可含子目录，但每段经
    basename 清洗、不得出现向上跳转段。"""
    d = safe_path(outdir)
    parts = [p for p in re.split(r"[\\/]+", str(filename or "")) if p]
    if not parts:
        raise GapError("非法文件名：%r" % filename)
    cleaned = []
    for p in parts:
        b = os.path.basename(p)
        if not b or b in (".", os.pardir):
            raise GapError("非法文件名：%r" % filename)
        cleaned.append(b)
    root = d + os.sep
    path = os.path.join(d, *cleaned)
    if not path.startswith(root):
        raise GapError("写入目标逃逸出输出目录：%r" % filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def ensure_parent(path):
    path = safe_path(path)
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def dump_json(outdir, filename, obj):
    path = _write_target(outdir, filename)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_text(outdir, filename, text):
    path = _write_target(outdir, filename)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def read_csv(path):
    """读取 UTF-8-SIG CSV，返回 (headers, rows[dict])。不存在返回 ([], [])。"""
    path = safe_path(path)
    if not os.path.isfile(path):
        return [], []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return (reader.fieldnames or []), rows


def write_csv(outdir, filename, rows, headers):
    path = _write_target(outdir, filename)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in headers})


def rel_of(path, root):
    return os.path.relpath(safe_path(path), safe_path(root)).replace("\\", "/")


def sha256_file(path):
    h = hashlib.sha256()
    with open(safe_path(path), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_tree(root, skip_dirs=()):
    """返回 {相对路径: sha256}，用于「运行前后目录哈希一致」的零写入自证。"""
    root = safe_path(root)
    skip = set(skip_dirs or ())
    out = {}
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in skip]
        for f in sorted(fn):
            p = os.path.join(dp, f)
            try:
                out[rel_of(p, root)] = sha256_file(p)
            except Exception:
                out[rel_of(p, root)] = "UNREADABLE"
    return out


def ensure_target_readable(target):
    target = safe_path(target)
    if not os.path.isdir(target):
        raise GapError("交付目录不存在或不是目录：%s" % target)
    if not os.access(target, os.R_OK):
        raise GapError("交付目录不可读：%s" % target)
    return target


def ensure_outdir_safe(outdir, target):
    """输出目录不得位于交付目录内部（防止工具污染被审计目录）。"""
    t = safe_path(target)
    o = safe_path(outdir)
    if o == t or o.startswith(t + os.sep):
        raise GapError("输出目录不得位于交付目录内部：--outdir=%s 位于交付目录之内" % outdir)
    return o
