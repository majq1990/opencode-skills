# -*- coding: utf-8 -*-
"""把 skill 的 scripts 目录加入 sys.path，供测试导入。"""
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
