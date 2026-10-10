#!/usr/bin/env python3
"""把本 skill 打包为可上传分发服务器的 zip（SKILL.md 在 zip 根部）。

用法：
  python package.py                 # 输出 dist/redmine-security-auto-fix-<version>.zip
  python package.py --out <dir>     # 指定输出目录

排除：运行时产物（work/、__pycache__/、.pytest_cache/、.env）与打包脚本自身。
上传前服务端会自动跑 skill-security-auditor 安全扫描，包内不得含密钥/凭据。
"""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

EXCLUDE_DIRS = {"work", "__pycache__", ".pytest_cache", ".git", "dist", ".venv"}
EXCLUDE_FILES = {".env", "package.py"}
EXCLUDE_SUFFIX = {".pyc", ".pyo", ".log"}


def read_version() -> str:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"^version:\s*(\S+)", text, re.M)
    if not match:
        raise SystemExit("SKILL.md frontmatter 缺少 version")
    return match.group(1)


def build(out_dir: Path) -> Path:
    version = read_version()
    name = ROOT.name
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{name}-{version}.zip"

    files = []
    for path in sorted(ROOT.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(ROOT)
        parts = rel.parts
        if any(part in EXCLUDE_DIRS for part in parts):
            continue
        if rel.name in EXCLUDE_FILES or path.suffix.lower() in EXCLUDE_SUFFIX:
            continue
        files.append((path, rel))

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, rel in files:
            zf.write(path, str(rel))

    # 打包自检：SKILL.md 必须在根部且带 frontmatter
    with zipfile.ZipFile(target) as zf:
        names = zf.namelist()
        assert "SKILL.md" in names, "SKILL.md 不在包根"
        head = zf.read("SKILL.md")[:200].decode("utf-8", "replace")
        assert "name:" in head and "version:" in head, "frontmatter 缺失"
        bad = [n for n in names if n.startswith(("work/",)) or "__pycache__" in n or n == ".env"]
        assert not bad, f"包内混入排除项: {bad}"
    print(f"打包完成: {target}")
    print(f"  文件数: {len(files)}  大小: {target.stat().st_size / 1024:.0f} KB  版本: {version}")
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "dist"))
    args = parser.parse_args()
    build(Path(args.out))


if __name__ == "__main__":
    main()
