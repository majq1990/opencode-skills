#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill-hub 客户端：以本机 skills-manager 登录态访问公司 skill 服务器（只读）。

身份模型：不做登录、不内置任何账号。每次运行时从本机 skills-manager 的
登录会话中读取 enterprise_token 并解密，以"当前登录 skills-manager 的用户
本人"身份调用 API。未登录或登录过期时，提示用户打开 skills-manager 重新
登录企业服务器。

安全约束：
- token 即取即用，不落盘、不打印、不进日志；
- 仅允许 https、host 固定为 SERVER_HOST，发请求前校验协议与 host，并把
  域名解析出的全部 IP 与私网/环回/链路本地/保留地址做比对，全部通过才
  发起请求；禁用重定向；
- 只调用只读接口（list/search/tags/show/download），上传/删除等写操作不
  在本脚本能力范围内；
- 所有外部字符串在进入文件系统前一律做字面 ".." 检查 + 规范化 +
  commonpath 边界校验；zip 解压显式拒绝 ".." 与绝对路径成员，不基于成员
  名做任何目录拼接推导；skill 名与版本号走白名单正则；
- 会话解密仅限本机本人会话使用。

跨平台：Windows / macOS / Linux 均可运行，路径全部基于用户主目录展开，
不预设盘符或任何个人机器的专属布局。目标装载路径解析失败时自动退化为
临时目录装载，不影响当次使用。
"""

import argparse
import base64
import io
import ipaddress
import json
import os
import re
import socket
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

SERVER_HOST = "demo.egova.com.cn"
SERVER_BASE = "https://" + SERVER_HOST + "/skill-api"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
TIMEOUT_SECONDS = 30

ENC_PREFIX = "enc:v1:"
# \w 为 Unicode 语义（含中文）：服务器 skill 池存在中文名（如"灵珑支持"）；
# 首字符不允许 . / 空格，从源头排除 ".."、隐藏文件与路径分隔符
NAME_RE = re.compile(r"^\w[\w.\-]{0,63}$", re.UNICODE)
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,31}$")

# skills-manager 会话文件（跨平台候选，按顺序探测，全部基于 ~ 展开）
SM_DATA_DIRS = ["~/.skills-manager"]
SM_DB_NAMES = ["skills-manager.db"]
SM_KEY_NAMES = [".secret.key"]

# 各工具 skills 目录的跨平台默认候选（相对 ~）。skills-manager 的
# custom_tool_paths 配置（若可读）会插到候选列表最前面。
TOOL_DIR_CANDIDATES = {
    "zcode": ["~/.zcode/skills"],
    "workbuddy": ["~/.workbuddy/skills"],
    "dsh": ["~/.dsh/skills"],
    "opencode": [
        "~/.config/opencode/skill",
        "~/.opencode/skills",
        "~/opencode/skills",
    ],
}


class HubError(Exception):
    """带用户可读提示的错误。"""


class SessionUnavailable(HubError):
    """本机无可用 skills-manager 登录态。"""


# ---------------------------------------------------------------------------
# 会话：从 skills-manager 登录态取 token
# ---------------------------------------------------------------------------

def _expand_candidates(rel_paths):
    seen = []
    for rel in rel_paths:
        p = Path(rel).expanduser()
        if p not in seen:
            seen.append(p)
    return seen


def _locate_session_files():
    """返回 (db_path, key_path)；找不到抛 SessionUnavailable。"""
    for data_dir in _expand_candidates(SM_DATA_DIRS):
        for db_name in SM_DB_NAMES:
            db = data_dir / db_name
            key = data_dir / SM_KEY_NAMES[0]
            if db.is_file() and key.is_file():
                return db, key
    raise SessionUnavailable(
        "未找到本机 skills-manager 登录数据（~/.skills-manager/ 下缺 "
        "skills-manager.db 或 .secret.key）。\n"
        "请先安装并打开 skills-manager，登录企业服务器后重试。"
    )


def _read_settings(db_path):
    """只读读取 settings 表；WAL 库只读失败时退化为 immutable 模式。"""
    db_uri = urlparse.quote(str(db_path).replace("\\", "/"))
    for param in ("mode=ro", "immutable=1"):
        uri = "file:%s?%s" % (db_uri, param)
        try:
            con = sqlite3.connect(uri, uri=True)
            try:
                rows = con.execute("SELECT key, value FROM settings").fetchall()
                return dict(rows)
            finally:
                con.close()
        except sqlite3.Error:
            continue
    raise SessionUnavailable("无法读取 skills-manager 数据库（%s）。" % db_path)


def _decrypt_gcm_python(hex_payload, key_bytes):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # 局部导入：可选依赖

    raw = bytes.fromhex(hex_payload)
    return AESGCM(key_bytes).decrypt(raw[:12], raw[12:], None).decode("utf-8")


_NODE_DECRYPT_SCRIPT = r"""
const crypto = require('crypto');
let input = '';
process.stdin.on('data', (c) => { input += c; });
process.stdin.on('end', () => {
  try {
    const { key, hex } = JSON.parse(input);
    const keyBuf = Buffer.from(key, 'base64');
    const raw = Buffer.from(hex, 'hex');
    const d = crypto.createDecipheriv('aes-256-gcm', keyBuf, raw.subarray(0, 12));
    d.setAuthTag(raw.subarray(raw.length - 16));
    const out = Buffer.concat([d.update(raw.subarray(12, raw.length - 16)), d.final()]);
    process.stdout.write(out.toString('utf8'));
  } catch (e) { process.exit(1); }
});
"""


def _decrypt_gcm_node(hex_payload, key_bytes):
    try:
        proc = subprocess.run(
            ["node", "-e", _NODE_DECRYPT_SCRIPT],
            input=json.dumps({
                "key": base64.b64encode(key_bytes).decode("ascii"),
                "hex": hex_payload,
            }),
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise HubError(
            "本机缺少可用的 AES-GCM 解密环境（需 python cryptography 库或 node）。"
        )
    if proc.returncode != 0 or not proc.stdout:
        raise HubError("会话解密失败（node 兜底也未成功），请确认 skills-manager 登录态有效。")
    return proc.stdout


def _decrypt_enc_v1(encrypted, key_bytes):
    """解密 skills-manager 的 enc:v1: 值。

    格式：`enc:v1:` + hex(nonce 12B ‖ AES-256-GCM 密文 ‖ tag 16B)。
    优先 python cryptography，缺失时回退 node crypto。
    """
    if not encrypted.startswith(ENC_PREFIX):
        raise HubError("skills-manager 会话值不是预期的 enc:v1: 格式。")
    hex_payload = encrypted[len(ENC_PREFIX):].strip()
    try:
        return _decrypt_gcm_python(hex_payload, key_bytes)
    except ImportError:
        return _decrypt_gcm_node(hex_payload, key_bytes)
    except Exception:
        return _decrypt_gcm_node(hex_payload, key_bytes)


def _jwt_exp(token):
    """解析 JWT 的 exp（秒级时间戳）；解析失败返回 None。"""
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return int(payload.get("exp")) if payload.get("exp") else None
    except Exception:
        return None


def get_token():
    """获取当前 skills-manager 登录者的 enterprise token。"""
    db_path, key_path = _locate_session_files()
    settings = _read_settings(db_path)
    encrypted = settings.get("enterprise_token")
    if not encrypted:
        raise SessionUnavailable(
            "skills-manager 中没有企业服务器登录态（enterprise_token 缺失）。\n"
            "请先打开 skills-manager 登录企业服务器（用你自己的账号），然后重试。"
        )
    key_bytes = key_path.read_bytes()
    token = _decrypt_enc_v1(encrypted, key_bytes)
    exp = _jwt_exp(token)
    if exp is not None and exp < time.time():
        raise SessionUnavailable(
            "skills-manager 的企业服务器登录态已过期（%s）。\n"
            "请打开 skills-manager 重新登录后重试。"
            % time.strftime("%Y-%m-%d %H:%M", time.localtime(exp))
        )
    return token


def get_custom_tool_paths(settings):
    """读取 skills-manager 的 custom_tool_paths（明文 JSON）；读不到返回空表。"""
    raw = settings.get("custom_tool_paths")
    if not raw or raw.startswith(ENC_PREFIX):
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        return {}


# ---------------------------------------------------------------------------
# 安全出口校验：协议 + host 白名单 + 解析 IP 边界 + 禁重定向
# ---------------------------------------------------------------------------

_TARGET_VALIDATED = False


def _validate_outbound_target():
    """发请求前校验固定目标：仅 https、host 在白名单、解析出的 IP 全部为公网。"""
    global _TARGET_VALIDATED
    if _TARGET_VALIDATED:
        return
    parsed = urlparse.urlsplit(SERVER_BASE)
    if parsed.scheme != "https":
        raise HubError("目标协议非 https，已拒绝请求。")
    if parsed.hostname != SERVER_HOST or parsed.port not in (None, 443):
        raise HubError("目标 host 不在白名单内，已拒绝请求。")
    try:
        addr_infos = socket.getaddrinfo(SERVER_HOST, 443, proto=socket.IPPROTO_TCP)
    except OSError as e:
        raise HubError("域名解析失败（%s）：%s" % (SERVER_HOST, e))
    for info in addr_infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise HubError("目标域名解析到非公网地址（%s），已拒绝请求。" % ip)
    _TARGET_VALIDATED = True


class _NoRedirect(urlrequest.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # 不跟随任何重定向


_OPENER = urlrequest.build_opener(_NoRedirect)


def api_get(path, token, expect_json=True):
    _validate_outbound_target()
    url = SERVER_BASE + path
    req = urlrequest.Request(url, method="GET")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/json")
    req.add_header("Authorization", "Bearer " + token)
    try:
        with _OPENER.open(req, timeout=TIMEOUT_SECONDS) as resp:
            body = resp.read()
    except urlerror.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            raise HubError("服务器返回重定向（%s），出于安全已拒绝跟随。" % e.code)
        if e.code == 401:
            raise SessionUnavailable(
                "登录态被服务器拒绝（401）。请打开 skills-manager 重新登录"
                "企业服务器后重试。"
            )
        if e.code == 404:
            raise HubError("服务器上不存在该资源：%s" % path)
        raise HubError("服务器返回 HTTP %s（%s）" % (e.code, url))
    except urlerror.URLError as e:
        raise HubError("无法连接 skill 服务器（%s）：%s" % (url, e.reason))
    if not expect_json:
        return body
    try:
        return json.loads(body.decode("utf-8"))
    except ValueError:
        raise HubError("服务器响应不是合法 JSON（%s）" % url)


def _check_payload(data):
    if isinstance(data, dict) and data.get("success") is False:
        raise HubError("服务器返回失败：%s" % data.get("error", data))
    return data


# ---------------------------------------------------------------------------
# 路径与装载：外部输入先过字面 ".." 检查 + 白名单，写入前过 commonpath 边界
# ---------------------------------------------------------------------------

def _validate_name(name):
    if not isinstance(name, str) or ".." in name or not NAME_RE.fullmatch(name):
        raise HubError("非法的 skill 名：%r" % name)
    return name


def _validate_version(version):
    if not isinstance(version, str) or ".." in version or not VERSION_RE.fullmatch(version):
        raise HubError("非法的版本号：%r" % version)
    return version


def _safe_dest(dest):
    """规范化 --dest：展开 ~、转绝对路径、字面与成分级双重 '..' 检查。"""
    if not isinstance(dest, str) or ".." in dest:
        raise HubError("--dest 非法（不允许包含 '..'）：%r" % dest)
    p = Path(dest).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    p = Path(os.path.normpath(str(p)))
    if ".." in p.parts:
        raise HubError("--dest 规范化后仍含 '..'，已拒绝。")
    return p


def resolve_tool_dir(tool, custom_paths):
    """解析某工具的 skills 目录：skills-manager 配置 → 默认候选 → 存在性探测。

    找不到已存在的目录时返回 None（调用方退化为临时装载，不报错）。
    """
    tool = (tool or "").strip().lower()
    if tool not in TOOL_DIR_CANDIDATES:
        raise HubError(
            "未知工具 %r（支持：%s），或改用 --dest / --tmp。"
            % (tool, "/".join(sorted(TOOL_DIR_CANDIDATES)))
        )
    candidates = []
    configured = custom_paths.get(tool) or ""
    if isinstance(configured, str) and configured and ".." not in configured \
            and not configured.startswith(ENC_PREFIX):
        candidates.append(Path(configured).expanduser())
    candidates.extend(_expand_candidates(TOOL_DIR_CANDIDATES[tool]))
    for cand in candidates:
        try:
            if cand.is_dir():
                return cand
        except OSError:
            continue
    return None


def _safe_member_relpath(raw_name):
    """校验 zip 成员名，返回限定在解压根内的相对路径；非法成员直接拒绝。"""
    name = raw_name.replace("\\", "/")
    if ".." in name or name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        raise HubError("skill 包内含非法路径成员（%r），已中止解压。" % raw_name)
    parts = [p for p in name.split("/") if p not in ("", ".")]
    if not parts or parts[0] == "__MACOSX":
        return None
    rel = os.path.normpath(os.path.join(*parts))
    if os.path.isabs(rel) or rel.startswith("..") or ".." in rel.split(os.sep):
        raise HubError("skill 包成员规范化后越界（%r），已中止解压。" % raw_name)
    return rel


def _safe_extract(zip_bytes, dest_dir, skill_name):
    """把 skill zip 解压到 <dest_dir>/<skill_name>/，全程限制在目标目录内。

    不基于 zip 成员名推导目录：成员相对路径逐段校验后仅用于落在解压根内，
    包裹目录（若有）原样保留，由调用方在其下定位 SKILL.md。
    """
    root_s = str((_safe_dest(str(dest_dir)) / _validate_name(skill_name)).resolve())
    os.makedirs(root_s, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            rel = _safe_member_relpath(info.filename)
            if rel is None:
                continue
            full = os.path.normpath(os.path.join(root_s, rel))
            if os.path.commonpath([root_s, full]) != root_s:
                raise HubError("skill 包解压路径越界（%r），已中止。" % info.filename)
            if ".." in full or ".." in rel:
                raise HubError("skill 包解压路径含 '..'（%r），已中止。" % info.filename)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with zf.open(info) as src:
                Path(full).write_bytes(src.read())
            perm = (info.external_attr >> 16) & 0o777
            if perm & stat.S_IXUSR:
                os.chmod(full, os.stat(full).st_mode | stat.S_IXUSR)
    return Path(root_s)


def _locate_skill_md(install_path):
    """定位解压结果里的 SKILL.md：根目录优先，其次唯一一层子目录。"""
    direct = install_path / "SKILL.md"
    if direct.is_file():
        return direct, ""
    try:
        children = sorted(p for p in install_path.iterdir() if p.is_dir())
    except OSError:
        children = []
    for child in children:
        candidate = child / "SKILL.md"
        if candidate.is_file():
            return candidate, "skill 包带了一层目录（%s），入口已定位到包内。" % child.name
    return direct, "注意：包内未找到 SKILL.md，请人工检查解压结果。"


def load_skill(token, name, version, custom_paths, tool=None, dest=None):
    """下载并解压 skill。返回 (install_path, entry, resolved_version, is_temp, note)。"""
    _validate_name(name)
    if version:
        _validate_version(version)
        chosen = version
    else:
        chosen = None
        try:
            detail = _check_payload(api_get("/skills/%s/versions" % name, token))
            versions = detail.get("versions") if isinstance(detail, dict) else None
            if isinstance(versions, list) and versions:
                first = versions[0]
                candidate = first.get("version") if isinstance(first, dict) else first
                if candidate:
                    chosen = _validate_version(str(candidate))
        except HubError:
            pass  # versions 端点缺失时退回详情接口
        if not chosen:
            info = _check_payload(api_get("/skills/%s" % name, token))
            candidate = info.get("version") if isinstance(info, dict) else None
            if candidate:
                chosen = _validate_version(str(candidate))
    if not chosen:
        raise HubError("无法确定 %s 的版本号，请用 --version 显式指定。" % name)

    zip_bytes = api_get(
        "/skills/%s/%s/download" % (urlrequest.quote(name, safe=""),
                                    urlrequest.quote(chosen, safe="")),
        token, expect_json=False,
    )
    try:
        zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        raise HubError("下载内容不是合法 zip 包（%s@%s）。" % (name, chosen))

    note = ""
    if dest:
        target_root = _safe_dest(dest)
        target_root.mkdir(parents=True, exist_ok=True)
        is_temp = False
    elif tool:
        resolved = resolve_tool_dir(tool, custom_paths)
        if resolved is None:
            target_root = Path(tempfile.mkdtemp(prefix="skill-hub-"))
            is_temp = True
            note = (
                "未找到 %s 的 skills 目录，已装载到临时目录（不影响当次使用）。"
                "如需持久安装：重跑并加 --dest <路径>，或在 skills-manager "
                "发现页导入该 skill。" % tool
            )
        else:
            target_root = resolved
            is_temp = False
    else:
        target_root = Path(tempfile.mkdtemp(prefix="skill-hub-"))
        is_temp = True

    install_path = _safe_extract(zip_bytes, target_root, name)
    entry, locate_note = _locate_skill_md(install_path)
    if locate_note:
        note = (note + " " if note else "") + locate_note
    return install_path, entry, chosen, is_temp, note


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_skills(data):
    skills = data.get("skills", []) if isinstance(data, dict) else []
    if not skills:
        print("（无匹配结果）")
        return
    width = min(max(max(len(s.get("name", "")) for s in skills), 8), 40)
    for s in skills:
        print(
            "%-*s  v%-8s [%s]  %s"
            % (
                width,
                s.get("name", ""),
                str(s.get("version", ""))[:8],
                s.get("visibility", ""),
                str(s.get("description", "")).replace("\n", " ")[:110],
            )
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="skill_server.py",
        description="skill-hub 客户端：以 skills-manager 登录态访问公司 skill 服务器（只读）。",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="列出企业 skill 池")
    p_list.add_argument("--tag", default=None, help="按 tag 过滤")

    p_search = sub.add_parser("search", help="关键词搜索（多词默认逐词搜合并）")
    p_search.add_argument("query")
    p_search.add_argument("--exact", action="store_true", help="整串作为单一关键词（默认逐词搜）")

    sub.add_parser("tags", help="列出全部 tag")

    p_show = sub.add_parser("show", help="查看某 skill 详情")
    p_show.add_argument("name")

    p_dl = sub.add_parser("download", help="下载并装载 skill")
    p_dl.add_argument("name")
    p_dl.add_argument("--version", default=None)
    p_dl.add_argument("--tool", default=None,
                      help="装载到该工具的 skills 目录（zcode/opencode/workbuddy/dsh）")
    p_dl.add_argument("--dest", default=None, help="显式指定装载目标目录")
    p_dl.add_argument("--tmp", action="store_true", help="装载到临时目录（当次即用）")

    for p in (p_list, p_search, sub.choices["tags"], p_show, p_dl):
        p.add_argument("--json", action="store_true", help="结构化输出")

    args = parser.parse_args(argv)

    try:
        token = get_token()
        db_path, _ = _locate_session_files()
        custom_paths = get_custom_tool_paths(_read_settings(db_path))

        if args.command == "list":
            data = _check_payload(api_get("/skills", token))
            skills = data.get("skills", []) if isinstance(data, dict) else []
            # 服务端 ?tag= 过滤无效（实测忽略该参数返回全量），tag 过滤在本地做
            if args.tag:
                wanted = args.tag.strip().lower()
                skills = [s for s in skills
                          if wanted in [str(t).lower() for t in (s.get("tags") or [])]]
            if args.json:
                print(json.dumps({"success": True, "count": len(skills), "skills": skills},
                                 ensure_ascii=False, indent=2))
            else:
                print("共 %s 个 skill%s：" % (
                    len(skills), "（tag=%s）" % args.tag if args.tag else ""))
                _print_skills({"skills": skills})

        elif args.command == "search":
            # 服务端搜索把整串当一个词匹配：空格分隔的多词会 0 命中，
            # 因此默认逐词搜合并去重；--exact 保持原样整串搜。
            queries = [args.query] if args.exact else args.query.split()
            merged = {}
            for q in queries:
                if not q:
                    continue
                data = _check_payload(
                    api_get("/skills/search?q=%s" % urlrequest.quote(q, safe=""), token)
                )
                for s in (data.get("skills") or []) if isinstance(data, dict) else []:
                    merged[s.get("name", "")] = s
            skills = list(merged.values())
            if args.json:
                print(json.dumps({"success": True, "count": len(skills), "skills": skills},
                                 ensure_ascii=False, indent=2))
            else:
                if len(queries) > 1:
                    print("逐词搜索“%s”合并命中 %s 个：" % (" ".join(queries), len(skills)))
                else:
                    print("搜索“%s”命中 %s 个：" % (args.query, len(skills)))
                _print_skills({"skills": skills})

        elif args.command == "tags":
            data = _check_payload(api_get("/skills/tags", token))
            if args.json:
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print("共 %s 个 tag：%s" % (data.get("count", 0), "、".join(data.get("tags", []))))

        elif args.command == "show":
            data = _check_payload(api_get("/skills/%s" % urlrequest.quote(args.name, safe=""), token))
            if args.json:
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                skill = data.get("skill") if isinstance(data, dict) else None
                skill = skill if isinstance(skill, dict) else (data or {})
                for k in ("name", "latestVersion", "author", "visibility", "updatedAt"):
                    if skill.get(k):
                        print("%-14s %s" % (k + ":", skill[k]))
                print("%-14s %s" % ("description:", skill.get("description", "")))
                print("%-14s %s" % ("tags:", "、".join(skill.get("tags", []) or [])))
                versions = skill.get("versions") or []
                if versions:
                    print("%-14s %s" % ("versions:", "、".join(
                        str(v.get("version") if isinstance(v, dict) else v) for v in versions
                    )))

        elif args.command == "download":
            if sum(1 for v in (args.tool, args.dest, args.tmp) if v) > 1:
                raise HubError("--tool、--dest、--tmp 最多指定一个。")
            install_path, entry, resolved_version, is_temp, note = load_skill(
                token, args.name, args.version, custom_paths,
                tool=args.tool, dest=args.dest,
            )
            result = {
                "skill": args.name,
                "version": resolved_version,
                "install_path": str(install_path),
                "entry": str(entry),
                "temporary": is_temp,
                "note": note,
            }
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("✔ %s@%s 已装载" % (args.name, resolved_version))
                print("  位置: %s%s" % (install_path, "（临时目录）" if is_temp else ""))
                print("  入口: %s" % entry)
                if note:
                    print("  说明: %s" % note)
                print("  下一步: 阅读 SKILL.md 并按其执行。")

    except HubError as e:
        print("✘ %s" % e, file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
