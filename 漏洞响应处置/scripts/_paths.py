"""Cross-platform path resolution for vuln-response scripts.

ARCHIVE_DIR 解析顺序：
  1. 环境变量 VULN_RESPONSE_ARCHIVE_DIR
  2. Windows: D:\\opencode\\_archive
  3. 其他: ~/.local/share/vuln-response/archive
目录不存在时自动创建。

Python 3.6+ compatible.
"""
import os
import sys
from pathlib import Path


def archive_dir() -> Path:
    env = os.environ.get("VULN_RESPONSE_ARCHIVE_DIR")
    if env:
        p = Path(env)
    elif sys.platform == "win32":
        p = Path(r"D:\opencode\_archive")
    else:
        p = Path.home() / ".local" / "share" / "vuln-response" / "archive"
    p.mkdir(parents=True, exist_ok=True)
    return p


def references_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "references"
