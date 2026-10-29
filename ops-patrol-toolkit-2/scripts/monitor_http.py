#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""监控类子工具（06-09）共享 HTTP 客户端与 URL 安全闸。

约定：
  1. 所有出站请求必须经 guard_url 校验 + request_json 发起，禁止散落裸 urllib
  2. 安全闸默认拒绝：非 http/https、带 userinfo 的 URL、localhost/回环、云元数据地址
     （169.254.169.254 等 link-local，无任何放行开关）；私有网段（RFC1918 等）默认拒绝，
     由配置项 allow_private_targets=true 显式放行——监控端点在内网属部署常态，
     以"运维在配置文件中显式声明端点"为信任边界（与 04/05 的已接受威胁模型一致）
  3. 请求统一带浏览器 User-Agent（公司 WAF 拦截 Python-urllib 特征）
  4. 控制台不使用 emoji；本模块不打印
"""

import json
import socket
import urllib.error
import urllib.parse
import urllib.request

try:
    import sys as _sys
    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# 无论任何开关都禁止访问的地址（云凭证元数据等 link-local）
_ALWAYS_BLOCKED_NETS_LABEL = "link-local/云元数据"


class MonitorHttpError(Exception):
    """HTTP/安全闸错误。kind: scheme|userinfo|blocked_local|blocked_private|url|http|network|not_json|timeout"""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind
        self.message = message


def _ip_flags(ip):
    """返回 (is_local, is_private) —— ip 为 ipaddress.IPv4Address/IPv6Address。"""
    import ipaddress
    is_local = ip.is_loopback or ip.is_link_local  # 含 127.0.0.0/8、::1、169.254/16（云元数据）、fe80::/10
    is_private = (not is_local) and (ip.is_private or not ip.is_global)
    return is_local, is_private


def guard_url(url, allow_local=False, allow_private=False):
    """校验并归一 URL，返回 (scheme, host, port)。

    规则：
      - 仅允许 http/https
      - 禁止 userinfo（https://user:pass@host 形式）
      - localhost/回环/link-local 默认拒绝；allow_local=True 时回环可放行，
        但 link-local（云元数据 169.254.169.254 等）永远拒绝
      - 私有/保留网段默认拒绝；allow_private=True 时放行（内网监控部署常态）
    """
    try:
        p = urllib.parse.urlsplit(url)
    except ValueError as e:
        raise MonitorHttpError("url", "URL 无法解析: %s (%s)" % (url, e))
    if p.scheme not in ("http", "https"):
        raise MonitorHttpError("scheme", "仅允许 http/https，收到 %r" % p.scheme)
    if not p.hostname:
        raise MonitorHttpError("url", "URL 缺少主机名: %s" % url)
    if p.username or p.password or "@" in (p.netloc or ""):
        raise MonitorHttpError("userinfo", "URL 不允许携带 userinfo（用户名/密码）: %s" % url)
    host = p.hostname
    if host.lower() == "localhost" and not allow_local:
        raise MonitorHttpError("blocked_local", "拒绝 localhost 目标（如需放行请配置 allow_local_targets）")

    # 解析所有地址逐一检查
    try:
        infos = socket.getaddrinfo(host, p.port or (443 if p.scheme == "https" else 80),
                                   proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise MonitorHttpError("url", "主机解析失败 %s: %s" % (host, e))
    import ipaddress
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr.split("%")[0])
        except ValueError:
            continue
        is_local, is_private = _ip_flags(ip)
        if is_local and ip.is_link_local:
            # 云元数据/链路本地：无开关，永远拒绝
            raise MonitorHttpError("blocked_local",
                                   "拒绝 link-local 地址 %s（%s）" % (addr, _ALWAYS_BLOCKED_NETS_LABEL))
        if is_local and not allow_local:
            raise MonitorHttpError("blocked_local",
                                   "拒绝回环地址 %s（如需放行请配置 allow_local_targets）" % addr)
        if is_private and not allow_private:
            raise MonitorHttpError("blocked_private",
                                   "拒绝私有/保留地址 %s（内网监控端点请在配置中 allow_private_targets=true）" % addr)
    return p.scheme, host, p.port


def request_json(url, method="GET", payload=None, headers=None, token=None,
                 timeout_s=30, allow_local=False, allow_private=False):
    """发起 JSON 请求，返回 (status:int, body_obj|body_str)。

    失败抛 MonitorHttpError（kind: guard_* 转发 / timeout / http / network / not_json）。
    token 非空时加 Authorization: Bearer 头。
    """
    guard_url(url, allow_local=allow_local, allow_private=allow_private)
    hdrs = {
        "User-Agent": BROWSER_UA,
        "Accept": "application/json, text/plain, */*",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    if token:
        hdrs["Authorization"] = "Bearer %s" % token
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout_s)
    except socket.timeout:
        raise MonitorHttpError("timeout", "请求超时（%ss）: %s" % (timeout_s, url))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read(300).decode("utf-8", "replace").strip()
        except Exception:
            detail = ""
        raise MonitorHttpError("http", "HTTP %s: %s %s" % (e.code, url, detail))
    except urllib.error.URLError as e:
        raise MonitorHttpError("network", "网络错误: %s (%s)" % (url, e.reason))
    body = resp.read()
    status = getattr(resp, "status", resp.getcode())
    text = body.decode("utf-8", "replace")
    try:
        return status, json.loads(text)
    except json.JSONDecodeError:
        raise MonitorHttpError("not_json", "响应不是 JSON（前 200 字符）: %s" % text[:200])


def http_get_json(url, **kw):
    return request_json(url, method="GET", **kw)


def http_post_json(url, payload, **kw):
    return request_json(url, method="POST", payload=payload, **kw)


def load_monitor_config(config_path, group):
    """从监控配置读取一组端点声明，返回 dict；缺关键字段即 KeyError（调用方转 gap）。

    期望结构（config/patrol/monitors.json）：
      {group: {"url":..., "token_env_ref":..., "timeout_s":60,
               "allow_private_targets":true, "allow_local_targets":false, ...}}
    """
    import os
    with open(config_path, "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)
    g = cfg.get(group)
    if not isinstance(g, dict):
        raise KeyError("配置缺少端点组 %r" % group)
    if not g.get("url"):
        raise KeyError("端点组 %r 缺少 url" % group)
    token = None
    ref = g.get("token_env_ref")
    if ref:
        token = os.environ.get(ref)
    g = dict(g)
    g["_token"] = token
    return g
