#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill-hub 离线单元测试（零依赖，python tests/test_skill_hub.py 直接跑）。

覆盖：名字/版本白名单、--dest 规范化、zip 成员校验与解压边界、
包裹目录下 SKILL.md 定位、工具落点解析与降级、JWT exp 解析。
网络相关（list/search/download 实调）不在此文件，属集成验证。
"""

import io
import os
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import skill_server as ss  # noqa: E402

FAILED = []


def check(label, fn):
    try:
        fn()
        print("✔ %s" % label)
    except AssertionError as e:
        FAILED.append(label)
        print("✘ %s: %s" % (label, e))
    except Exception as e:  # noqa: BLE001
        FAILED.append(label)
        print("✘ %s: 异常 %r" % (label, e))


def expect_hub_error(fn):
    try:
        fn()
    except ss.HubError:
        return
    raise AssertionError("未抛出 HubError")


# --- 名字/版本白名单 -------------------------------------------------------

def test_name_whitelist():
    assert ss._validate_name("build-pipeline") == "build-pipeline"
    assert ss._validate_name("灵珑支持") == "灵珑支持"  # 服务器存在中文 skill 名
    expect_hub_error(lambda: ss._validate_name("../evil"))
    expect_hub_error(lambda: ss._validate_name("a/b"))
    expect_hub_error(lambda: ss._validate_name(""))
    expect_hub_error(lambda: ss._validate_name(None))


def test_version_whitelist():
    assert ss._validate_version("1.0.1") == "1.0.1"
    expect_hub_error(lambda: ss._validate_version("../1"))
    expect_hub_error(lambda: ss._validate_version("1..0"))


# --- --dest 规范化 ---------------------------------------------------------

def test_safe_dest():
    expect_hub_error(lambda: ss._safe_dest("/tmp/../etc"))
    expect_hub_error(lambda: ss._safe_dest("a/../../b"))
    p = ss._safe_dest("./sub/dir")
    assert p.is_absolute() and ".." not in p.parts


# --- zip 成员校验 ----------------------------------------------------------

def test_member_relpath():
    assert ss._safe_member_relpath("SKILL.md") == os.path.normpath("SKILL.md")
    assert ss._safe_member_relpath("scripts/a.py") == os.path.normpath("scripts/a.py")
    assert ss._safe_member_relpath("__MACOSX/x") is None
    assert ss._safe_member_relpath("./a/./b") == os.path.normpath("a/b")
    expect_hub_error(lambda: ss._safe_member_relpath("../evil.txt"))
    expect_hub_error(lambda: ss._safe_member_relpath("a/../../evil.txt"))
    expect_hub_error(lambda: ss._safe_member_relpath("/abs/path.txt"))
    expect_hub_error(lambda: ss._safe_member_relpath("C:\\windows\\evil.txt"))


def _zip_bytes(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in entries:
            zf.writestr(name, content)
    return buf.getvalue()


def test_safe_extract_normal():
    with tempfile.TemporaryDirectory() as tmp:
        data = _zip_bytes([
            ("SKILL.md", "# demo"),
            ("scripts/run.py", "print('hi')"),
        ])
        root = ss._safe_extract(data, Path(tmp), "demo-skill")
        assert (root / "SKILL.md").is_file()
        assert (root / "scripts" / "run.py").is_file()


def test_safe_extract_traversal_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        evil = _zip_bytes([("../evil.txt", "x")])
        try:
            ss._safe_extract(evil, Path(tmp), "demo-skill")
        except ss.HubError:
            pass
        else:
            raise AssertionError("穿越包未被拒绝")
        assert not (Path(tmp) / "evil.txt").exists()


def test_locate_skill_md_wrapped():
    with tempfile.TemporaryDirectory() as tmp:
        data = _zip_bytes([
            ("demo-skill/SKILL.md", "# wrapped"),
            ("demo-skill/x.txt", "y"),
        ])
        root = ss._safe_extract(data, Path(tmp), "wrapped-skill")
        entry, note = ss._locate_skill_md(root)
        assert entry.is_file() and entry.name == "SKILL.md"
        assert note  # 有包裹目录说明


# --- 工具落点解析与降级 ----------------------------------------------------

def test_resolve_tool_dir_fallback():
    # 候选目录全部不存在 → None（调用方退化 --tmp，不报错）。
    # patch 掉默认候选表，避免依赖本机是否真有这些目录。
    saved = ss.TOOL_DIR_CANDIDATES
    ss.TOOL_DIR_CANDIDATES = {"zcode": ["~/definitely-not-exists-xyz/skills"]}
    try:
        assert ss.resolve_tool_dir("zcode", {}) is None
    finally:
        ss.TOOL_DIR_CANDIDATES = saved


def test_resolve_tool_dir_unknown():
    expect_hub_error(lambda: ss.resolve_tool_dir("no-such-tool", {}))


def test_resolve_tool_dir_candidates():
    # 构造一个真实存在的临时目录塞进 custom_paths 首选位
    with tempfile.TemporaryDirectory() as tmp:
        got = ss.resolve_tool_dir("zcode", {"zcode": tmp})
        assert got is not None and Path(got).resolve() == Path(tmp).resolve()


# --- JWT exp 解析 ----------------------------------------------------------

def test_jwt_exp_garbage():
    assert ss._jwt_exp("not-a-jwt") is None


def main():
    check("名字白名单", test_name_whitelist)
    check("版本白名单", test_version_whitelist)
    check("--dest 规范化", test_safe_dest)
    check("zip 成员校验", test_member_relpath)
    check("正常解压", test_safe_extract_normal)
    check("穿越包拒绝", test_safe_extract_traversal_rejected)
    check("包裹目录定位 SKILL.md", test_locate_skill_md_wrapped)
    check("工具落点降级返回 None", test_resolve_tool_dir_fallback)
    check("未知工具报错", test_resolve_tool_dir_unknown)
    check("候选目录解析", test_resolve_tool_dir_candidates)
    check("垃圾 JWT 不崩", test_jwt_exp_garbage)
    print()
    if FAILED:
        print("失败 %s 项：%s" % (len(FAILED), "、".join(FAILED)))
        return 1
    print("全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
