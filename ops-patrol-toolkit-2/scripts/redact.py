#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用脱敏器：在把现场材料交给 AI/工具分析之前，先抹掉身份信息。

覆盖：URL 中的口令、邮箱、身份证、手机号、IPv4、实例名、主机名、常见凭据串。
原则：只替换「身份类」文本，绝不改动任何数值口径（IOPS/耗时/行数等原样保留）。

用法:
  python scripts/redact.py 输入文件 [更多文件...] --out 输出目录
  python scripts/redact.py 输入文件 --inplace
  cat iostat.txt | python scripts/redact.py --stdin
"""

import argparse
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

__version__ = "1.0.0"

RULES = [
    # 顺序敏感：先处理带凭据的 URL，再处理一般规则
    ("url_cred", re.compile(r"(?i)\b([a-z]+://)([^/\s:@]+):([^/\s@]+)@"),
     lambda m: "%s%s:***@" % (m.group(1), m.group(2))),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "***@***"),
    ("idcard", re.compile(r"\b\d{17}[\dXx]\b"), "IDCARD-REDACTED"),
    ("mobile", re.compile(r"\b1[3-9]\d{9}\b"), "PHONE-REDACTED"),
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "IP-REDACTED"),
    # 实例名：形如 xxx-MYS-RO-10.x.x.x / rm-xxx-mysql-01
    ("inst", re.compile(r"\b[\w-]*-MYS-(?:RO|RW|HA)-[\w.-]+\b"), "INSTANCE-REDACTED"),
    ("hostname", re.compile(r"(?im)^\s*(?:Host(?:name)?|主机)\s*[:：]\s*(\S+)"),
     lambda m: m.group(0).replace(m.group(1), "HOST-REDACTED")),
    # 常见凭据写法
    ("kv_cred", re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key)\s*[:=]\s*\S+"),
     lambda m: "%s=***" % m.group(1)),
]


def redact_line(line):
    out = line
    for _name, pat, rep in RULES:
        out = pat.sub(rep, out)
    return out


def redact_text(text):
    return "\n".join(redact_line(ln) for ln in text.splitlines())


def main():
    ap = argparse.ArgumentParser(description="运维材料脱敏（只抹身份类文本，保留数值口径）")
    ap.add_argument("files", nargs="*", help="待脱敏文件")
    ap.add_argument("--out", help="输出目录；不指定则打印到标准输出")
    ap.add_argument("--inplace", action="store_true", help="就地覆盖（会先生成 .bak）")
    ap.add_argument("--stdin", action="store_true", help="从标准输入读取")
    a = ap.parse_args()

    if a.stdin:
        sys.stdout.write(redact_text(sys.stdin.read()))
        return 0

    if not a.files:
        ap.error("请提供文件或使用 --stdin")

    for fp in a.files:
        if not os.path.isfile(fp):
            sys.stderr.write("[WARN] 跳过不存在的文件: %s\n" % fp)
            continue
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            src = f.read()
        dst = redact_text(src)

        if a.inplace:
            bak = fp + ".bak"
            with open(bak, "w", encoding="utf-8") as f:
                f.write(src)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(dst)
            print("[ok] %s （原文件备份为 %s）" % (fp, bak))
        elif a.out:
            os.makedirs(a.out, exist_ok=True)
            tp = os.path.join(a.out, os.path.basename(fp))
            with open(tp, "w", encoding="utf-8") as f:
                f.write(dst)
            print("[ok] %s -> %s" % (fp, tp))
        else:
            print("===== %s =====" % fp)
            print(dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
