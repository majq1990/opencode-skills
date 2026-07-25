"""共享工具：dws 调用、plan 加载、stdout utf-8、ztoa 客户端实例、user 字段解析。"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# 默认 stdout/stderr 重配 utf-8（Windows 控制台 GBK 中文崩溃保护）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from . import _config as cfg  # type: ignore  # noqa: E402

# ZtoaOpenApiClient 导入（_config 已把 ztoa-mcp/src 加进 sys.path）
try:
    from ztoa_mcp.auth.ztoa_openapi import ZtoaOpenApiClient  # type: ignore
except ImportError:
    ZtoaOpenApiClient = None  # type: ignore


# ---------- plan 加载 ----------

DEFAULT_PLAN: dict[str, Any] = {
    "topic": "untitled",
    "base_name": "未命名跟踪反馈表",
    "base_desc": "",
    "result_options": [
        {"name": "未填", "color": "#9E9E9E"},
        {"name": "已修复", "color": "#00C853"},
        {"name": "受影响", "color": "#D32F2F"},
        {"name": "未知", "color": "#757575"},
    ],
    "extra_text_fields": ["操作系统名称", "OS版本", "内核版本(uname -r)"],
    "include_engineering_leads": True,
    "feedback_status_options": ["未反馈", "已反馈", "反馈中", "无法反馈"],
    "result_field_name": "脚本扫描结果",
    # 工作目录（中间产物）
    "work_dir": None,
}


def load_plan(plan_path: str | Path) -> dict[str, Any]:
    p = Path(plan_path).resolve()
    user = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    plan = {**DEFAULT_PLAN, **user}
    if not plan.get("work_dir"):
        topic = plan.get("topic") or p.stem
        plan["work_dir"] = str(Path("D:/opencode/_archive") / f"{topic}_workdir")
    Path(plan["work_dir"]).mkdir(parents=True, exist_ok=True)
    return plan


def work_path(plan: dict[str, Any], name: str) -> Path:
    return Path(plan["work_dir"]) / name


# ---------- dws CLI 包装 ----------

def call_dws(args: list[str], timeout: int = 120, retries: int = 2) -> tuple[dict | None, str, str]:
    """调用 dws.cmd <args>，自动重试 timeout/transient 错误。返回 (json|None, stdout, stderr)。"""
    cmd = ["dws.cmd"] + args
    last_out = last_err = ""
    for attempt in range(retries + 1):
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=timeout, shell=False)
        except subprocess.TimeoutExpired:
            last_err = f"timeout after {timeout}s (attempt {attempt + 1})"
            continue
        last_out = (r.stdout or b"").decode("utf-8", errors="replace")
        last_err = (r.stderr or b"").decode("utf-8", errors="replace")
        try:
            d = json.loads(last_out)
            # transient: AUTH_ERROR / SYSTEM_ERROR retryable
            err = (d.get("error") or {})
            if err and err.get("retryable") and attempt < retries:
                continue
            return d, last_out, last_err
        except Exception:
            if attempt < retries:
                continue
            return None, last_out, last_err
    return None, last_out, last_err


def dws_ok(d: dict | None) -> bool:
    return bool(d and d.get("status") == "success")


# ---------- ztoa 客户端 ----------

def make_ztoa_client():
    if ZtoaOpenApiClient is None:
        raise RuntimeError("ZtoaOpenApiClient 不可用：请安装 D:/git/ztoa-mcp 或在环境变量里提供 ztoa client")
    return ZtoaOpenApiClient(cfg.ZTOA_BASE_URL, cfg.ZTOA_APP_KEY, cfg.ZTOA_SIGN, verify=True)


def run_async(coro):
    return asyncio.run(coro)


# ---------- 字段解析 ----------

def parse_user_cell(v: Any) -> list[dict]:
    """ztoa user 字段返回 JSON 字符串数组。"""
    if not v:
        return []
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return []
    return v if isinstance(v, list) else []


def text_value(v: Any) -> str:
    """ztoa 文本/单选/数字字段统一取字符串。"""
    if v is None:
        return ""
    if isinstance(v, dict):
        return v.get("name") or v.get("text") or v.get("value") or ""
    return str(v).strip()


def cell_to_text(cells: dict, fid: str) -> str:
    return text_value(cells.get(fid))


def cell_to_user_ids(cells: dict, fid: str) -> list[str]:
    v = cells.get(fid) or []
    if isinstance(v, list):
        return [u.get("userId") for u in v if isinstance(u, dict) and u.get("userId")]
    return []
