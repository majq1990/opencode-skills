#!/usr/bin/env python3
"""rrun.py — 远程执行/传文件（Windows 无 sshpass 时的标准通道；qijian-deploy 依赖）
用法：
  python rrun.py exec <host> --cmd "命令"
  python rrun.py put  <host> <本地文件> <远端路径>
  python rrun.py get  <host> <远端文件> <本地路径>
  python rrun.py stdin <host> --cmd "命令" --input 本地文件   # 文件内容喂给远端 stdin
环境变量：QJ_PASS（默认 Egova@123）、QJ_USER（默认 root）
注意：paramiko AutoAddPolicy 跳过 SSH 主机指纹校验（内网一次性环境，可接受）；
host 必须匹配 IPv4 正则；命令由本地可信脚本传入。
"""
import os
import re
import sys
import argparse

import paramiko

IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


def conn(host):
    if not IP_RE.match(host):
        raise SystemExit(f"非法主机地址: {host}")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        host,
        port=22,
        username=os.environ.get("QJ_USER", "root"),
        password=os.environ.get("QJ_PASS", "Egova@123"),
        timeout=25,
        banner_timeout=30,
        auth_timeout=30,
        allow_agent=False,
        look_for_keys=False,
    )
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["exec", "put", "get", "stdin"])
    ap.add_argument("host")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--cmd", default="")
    ap.add_argument("--input", default="")
    a = ap.parse_args()

    c = conn(a.host)
    try:
        if a.action == "exec":
            _in, out, err = c.exec_command(a.cmd, timeout=3600)
            o = out.read().decode("utf-8", "replace")
            e = err.read().decode("utf-8", "replace")
            rc = out.channel.recv_exit_status()
            sys.stdout.write(o)
            if e.strip():
                sys.stdout.write("\n[stderr]\n" + e)
            sys.stdout.write(f"\n[rc={rc}]\n")
            sys.exit(0 if rc == 0 else 1)
        elif a.action == "stdin":
            data = open(a.input, "rb").read()
            _in, out, err = c.exec_command(a.cmd, timeout=3600)
            _in.write(data)
            _in.channel.shutdown_write()
            sys.stdout.write(out.read().decode("utf-8", "replace"))
            e = err.read().decode("utf-8", "replace")
            if e.strip():
                sys.stdout.write("\n[stderr]\n" + e)
            sys.stdout.write(f"\n[rc={out.channel.recv_exit_status()}]\n")
        elif a.action == "put":
            sftp = c.open_sftp()
            sftp.put(a.paths[0], a.paths[1])
            sftp.close()
            print(f"put OK: {a.paths[0]} -> {a.paths[1]}")
        elif a.action == "get":
            sftp = c.open_sftp()
            sftp.get(a.paths[0], a.paths[1])
            sftp.close()
            print(f"get OK: {a.paths[0]} -> {a.paths[1]}")
    finally:
        c.close()


if __name__ == "__main__":
    main()
