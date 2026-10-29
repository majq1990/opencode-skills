#!/usr/bin/env python3
"""批量修改案卷字段。

读取 CSV 表格，每行翻译成一次 issue_case_forward.py 调用，提交前打印全量
from→to 计划供人工确认。底层 HTTP / 认证 / 字段格式全部复用 forward 脚本。

详见 SKILL.md 第七节与 references/fields.md。
"""

import argparse
import csv
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FORWARD_SCRIPT = SCRIPT_DIR / "issue_case_forward.py"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/149.0.0.0 Safari/537.36"
)

# /custom_fields.json 缓存（避免每个 case 都拉一次）
_DATE_FIELD_IDS_CACHE: set[int] | None = None

# 列头中代表"要修改的字段"的前缀/名称。
# custom_field_<id>   → 自定义字段
# 标准字段            → 直接用 forward 的白名单字段名
STANDARD_FIELD_KEYS = {
    "status_id", "assigned_to_id", "fixed_version_id", "priority_id",
    "start_date", "due_date", "tester_id", "product", "module_id",
    "project_id", "tracker_id", "parent_issue_id", "estimated_hours",
}
# CSV 里允许的"控制列"（不参与提交，只用于参数）
CONTROL_KEYS = {"case_id", "opinion", "product", "task_type"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="根据 CSV 表格批量修改案卷字段")
    parser.add_argument("--input", required=True, help="CSV 文件路径")
    parser.add_argument("--product", help="产品类型（非 update-only 时必填）")
    parser.add_argument("--task-type", help="流转操作类型（非 update-only 时必填）")
    parser.add_argument("--update-only", action="store_true",
                        help="只改字段+评论，不触发流转")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅打印全量计划，不提交")
    parser.add_argument("--skip-fetch", action="store_true",
                        help="预览时不联网查当前值（离线预览）")
    parser.add_argument("--yes", action="store_true",
                        help="跳过提交前的人工确认（谨慎）")
    parser.add_argument("--force-idempotent", action="store_true",
                        help="强制执行幂等行（默认跳过所有字段已是目标值的行）")
    parser.add_argument("--fix-dirty-dates", action="store_true",
                        help="自动把 date 字段脏值（带时间）规范化为 YYYY-MM-DD，"
                        "随本次更新一并提交；避免 422 '不是合法日期'")
    return parser.parse_args()


def normalize_case_id(raw: str) -> str:
    """从案卷 ID 或 URL 中提取纯数字 ID。"""
    raw = str(raw).strip()
    match = re.search(r"/issues/(\d+)", raw)
    if match:
        return match.group(1)
    if raw.isdigit():
        return raw
    raise SystemExit(f"无法识别的案卷 ID：{raw}")


def load_rows(csv_path: Path) -> tuple[list[str], list[dict]]:
    """读取 CSV，返回 (列头, 行字典列表)。空单元格统一为空串。

    校验：
    - 每行列数必须等于列头数（防止中文逗号让 #clear 错位等无声错误）
    - opinion 列里包含 `=` 时打印警告（防止误把 #clear 写在意见里）
    """
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fp:
        # 用 csv.reader 读原始列数，再喂给 DictReader（避免 DictReader 把缺列静默填 None）
        raw_reader = csv.reader(fp)
        raw_fieldnames = next(raw_reader, [])
        fieldnames = [f for f in raw_fieldnames if f]
        rows = []
        for lineno, raw_row in enumerate(raw_reader, start=2):
            # 跳过完全空行
            if not any((c or "").strip() for c in raw_row):
                continue

            # 校验 1: 原始列数对齐（防中文逗号 / Excel 合并单元格 / 列错位等无声错误）
            if len(raw_row) != len(fieldnames):
                # 多余的列放在 row[len(fieldnames)] 之后；少的列用 None 填
                if len(raw_row) > len(fieldnames):
                    extra = raw_row[len(fieldnames):]
                    raise SystemExit(
                        f"CSV 第 {lineno} 行列数过多：{len(raw_row)} 列（期望 {len(fieldnames)}）\n"
                        f"  多余的列：{extra}\n"
                        f"  常见原因：opinion 列里写了中文逗号 `，` 让 #clear 错位进 opinion（应放在 custom_field_* 列）\n"
                        f"  详见 references/fields.md 'CSV 里的特殊写法' 小节"
                    )
                missing = fieldnames[len(raw_row):]
                raise SystemExit(
                    f"CSV 第 {lineno} 行列数过少：{len(raw_row)} 列（期望 {len(fieldnames)}）\n"
                    f"  缺失的列：{missing}\n"
                    f"  常见原因：opinion 列里写了中文逗号 `，` 让 #clear 错位进 opinion（应放在 custom_field_* 列）\n"
                    f"  详见 references/fields.md 'CSV 里的特殊写法' 小节"
                )

            # 校验通过，转成 dict
            row = dict(zip(fieldnames, raw_row))

            # 校验 2: opinion 列里包含 `=` 时警告
            opinion = (row.get("opinion") or "").strip()
            if opinion and "=" in opinion:
                print(
                    f"⚠️  CSV 第 {lineno} 行 opinion 列包含 `=`：{opinion!r}",
                    file=sys.stderr,
                )
                print(
                    "   如果意见里包含 #clear / --custom-field 等指令，请放到对应的字段列",
                    file=sys.stderr,
                )

            normalized = {k: (v or "").strip() for k, v in row.items() if k}
            normalized["_lineno"] = lineno
            rows.append(normalized)
    return fieldnames, rows


def validate_header(fieldnames: list[str], update_only: bool) -> None:
    """校验必填列存在。"""
    if "case_id" not in fieldnames:
        raise SystemExit("CSV 缺少必填列：case_id")
    if "opinion" not in fieldnames:
        raise SystemExit("CSV 缺少必填列：opinion（Redmine notes 不能为空）")
    if not update_only and "task_type" not in fieldnames:
        # 非 update-only 时，task_type 可由 --task-type 全局提供
        pass


def split_field_columns(fieldnames: list[str]) -> tuple[list[str], list[str], list[str]]:
    """把列头分成 (标准字段, custom_field, 控制列)。"""
    standard, custom, control = [], [], []
    for col in fieldnames:
        if col in CONTROL_KEYS:
            control.append(col)
        elif re.match(r"custom_field_\d+$", col):
            custom.append(col)
        elif col in STANDARD_FIELD_KEYS:
            standard.append(col)
        else:
            # 未知列：忽略（便于在表里留备注列），不打断
            pass
    return standard, custom, control


def fetch_issue_current(case_id: str) -> dict:
    """查询单条案件的当前值（含 custom_fields），用于 from→to 预览。"""
    base_url = os.environ.get(
        "REDMINE_BASE_URL", "https://faq.egova.com.cn:7787").rstrip("/")
    api_key = os.environ.get("REDMINE_API_KEY", "")
    if not api_key:
        raise SystemExit("REDMINE_API_KEY 未设置，无法查询当前值（可用 --skip-fetch 跳过）")

    insecure = os.environ.get("REDMINE_INSECURE_SKIP_VERIFY", "").lower() in {"1", "true", "yes"}
    context = ssl._create_unverified_context() if insecure else None
    url = f"{base_url}/issues/{case_id}.json?include=custom_fields"
    request = urllib.request.Request(
        url=url, method="GET",
        headers={
            "X-Redmine-API-Key": api_key,
            "User-Agent": os.environ.get("EGOVA_USER_AGENT", DEFAULT_USER_AGENT),
        },
    )
    try:
        with urllib.request.urlopen(request, context=context) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("issue", {})
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"_fetch_error": f"HTTP {exc.code}: {body[:200]}"}
    except Exception as exc:  # noqa: BLE001
        return {"_fetch_error": str(exc)}


def fetch_date_field_ids() -> set[int]:
    """拉 /custom_fields.json 缓存所有 field_format='date' 的字段 id。

    缓存到模块全局变量避免重复请求。
    网络失败时抛 SystemExit——date 类型判断是核心逻辑，不能静默 fallback
    （fallback 到硬编码列表会让脚本对实例配置变化不敏感）。
    """
    global _DATE_FIELD_IDS_CACHE
    if _DATE_FIELD_IDS_CACHE is not None:
        return _DATE_FIELD_IDS_CACHE

    api_key = os.environ.get("REDMINE_API_KEY", "")
    if not api_key:
        raise SystemExit(
            "REDMINE_API_KEY 未设置，无法拉 /custom_fields.json 判定 date 类型字段"
        )
    base_url = os.environ.get(
        "REDMINE_BASE_URL", "https://faq.egova.com.cn:7787"
    ).rstrip("/")
    insecure = os.environ.get("REDMINE_INSECURE_SKIP_VERIFY", "").lower() in {
        "1", "true", "yes"
    }
    context = ssl._create_unverified_context() if insecure else None
    try:
        req = urllib.request.Request(
            url=f"{base_url}/custom_fields.json",
            headers={
                "X-Redmine-API-Key": api_key,
                "User-Agent": os.environ.get("EGOVA_USER_AGENT", DEFAULT_USER_AGENT),
            },
        )
        with urllib.request.urlopen(req, context=context, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        date_ids = {
            cf["id"]
            for cf in data.get("custom_fields", [])
            if cf.get("field_format") == "date"
        }
        _DATE_FIELD_IDS_CACHE = date_ids
        return date_ids
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            f"拉 /custom_fields.json 失败（{type(exc).__name__}: {exc}），"
            f"无法判定 date 类型字段。请检查 REDMINE_BASE_URL 和 API key，或用 --skip-fetch 跳过脏值检测。"
        )


def detect_dirty_date_fields(
    issue: dict, date_field_ids: set[int]
) -> list[dict]:
    """扫 issue 里的 date 字段脏值（值包含 ' ' 即带时间）。

    返回 [{"cf_id": 352, "current": "2026-09-18 15:45:25", "fixed": "2026-09-18"}]
    datetime 字段（field_format=datetime）带时间是合法的，不会被误判。
    """
    dirty = []
    for cf in issue.get("custom_fields", []):
        cid = cf["id"]
        val = cf.get("value", "")
        if cid in date_field_ids and val and " " in str(val):
            dirty.append({
                "cf_id": cid,
                "current": str(val),
                "fixed": str(val)[:10],  # 取 YYYY-MM-DD 部分
            })
    return dirty


def current_value_of(issue: dict, field: str) -> str:
    """从当前案件数据里取某字段的值（标准字段或 custom_field）。"""
    if field.startswith("custom_field_"):
        target_id = int(field.replace("custom_field_", ""))
        for cf in issue.get("custom_fields", []):
            if cf.get("id") == target_id:
                return str(cf.get("value", ""))
        return ""
    # 标准字段：可能是标量或 {id,name}
    value = issue.get(field, "")
    if isinstance(value, dict):
        return str(value.get("name") or value.get("id") or "")
    return str(value)


def build_preview_table(rows: list[dict], field_cols: list[str], skip_fetch: bool) -> list[dict]:
    """为每行构造 from→to 预览记录。

    每个 change 项额外带：
    - `_target_value`: 实际传给 Redmine 的值（#clear 转为空串）
    - `_idempotent`: 目标值是否等于当前值（整行所有字段都幂等才在 plan 项上标 _idempotent=True）

    plan 项额外带：
    - `_dirty_fixes`: date 字段脏值（[{cf_id, current, fixed}]），来自联网扫描
    - `_fetch_error`: 拉当前 issue 失败时的错误信息（用于 dry-run 提示）
    """
    plan = []
    # 拉一次 date 类型字段列表（缓存到全局，避免每个 case 都拉 /custom_fields.json）
    date_field_ids: set[int] = set()
    if not skip_fetch:
        try:
            date_field_ids = fetch_date_field_ids()
        except SystemExit:
            # 没 API key 时 fetch_date_field_ids 会抛 SystemExit；跳过脏值检测
            pass

    for row in rows:
        case_id = normalize_case_id(row["case_id"])
        changes = []
        issue: dict = {}
        if skip_fetch:
            fetch_error = None
        else:
            issue = fetch_issue_current(case_id)
            fetch_error = issue.get("_fetch_error")

        # 1. 用户 CSV 里列出的字段改动
        for col in field_cols:
            new_value = row.get(col, "")
            if new_value == "":
                continue  # 空单元格 = 不修改
            if fetch_error:
                old_value = f"<查询失败:{fetch_error[:40]}>"
            elif skip_fetch:
                old_value = "<未查询>"
            else:
                old_value = current_value_of(issue, col) or "<空>"

            # #clear 是清空标记：实际传给 Redmine 的是空串，预览显示"<清空>"
            target_value = "" if new_value == "#clear" else new_value
            display_to = "<清空>" if new_value == "#clear" else new_value

            # 幂等性判断：目标值（空串/<空>）等于当前值
            is_idempotent = (
                old_value == target_value
                or (old_value == "<空>" and target_value == "")
            )

            changes.append({
                "field": col,
                "from": old_value,
                "to": display_to,
                "_target_value": target_value,
                "_idempotent": is_idempotent,
            })

        # 2. 扫 date 字段脏值（不依赖用户 CSV 里的字段——任何 date 脏值都列出）
        dirty_fixes: list[dict] = []
        if not skip_fetch and not fetch_error and date_field_ids:
            dirty_fixes = detect_dirty_date_fields(issue, date_field_ids)
            # 跳过 CSV 里已显式修改的 cf（避免重复——用户已经写了合法值）
            explicit_cf_cols = {c["field"] for c in changes}
            dirty_fixes = [
                d for d in dirty_fixes
                if f"custom_field_{d['cf_id']}" not in explicit_cf_cols
            ]

        # 3. 案卷基础信息（让 dry-run 显示当前 status / 指派人 / cf120 是否空）
        status_name = ""
        assigned_to_id = ""
        cf120_empty = False
        cf120_explicit = any(c["field"] == "custom_field_120" for c in changes)
        has_cf_change = any(c["field"].startswith("custom_field_") for c in changes)
        if not skip_fetch and not fetch_error:
            status_name = issue.get("status", {}).get("name", "")
            assigned_to = issue.get("assigned_to") or {}
            assigned_to_id = str(assigned_to.get("id", "")) if assigned_to else ""
            for cf in issue.get("custom_fields", []):
                if cf["id"] == 120 and not (cf.get("value") or "").strip():
                    cf120_empty = True
                    break
        # cf120 联动预警：用户要改 custom_field_* 但 cf120 空 + 没显式提供 cf120 → 可能 422
        needs_cf120_warning = has_cf_change and cf120_empty and not cf120_explicit

        # 整行幂等性：所有用户改动都幂等（且至少有一个改动），且无脏值修复
        all_idempotent = bool(changes) and all(c["_idempotent"] for c in changes) and not dirty_fixes
        plan.append({
            "case_id": case_id,
            "opinion": row.get("opinion", ""),
            "changes": changes,
            "_lineno": row.get("_lineno"),
            "_raw": row,
            "_idempotent": all_idempotent,
            "_dirty_fixes": dirty_fixes,
            "_status": status_name,
            "_assigned_to_id": assigned_to_id,
            "_cf120_empty": cf120_empty,
            "_needs_cf120_warning": needs_cf120_warning,
        })
    return plan


def print_preview(plan: list[dict]) -> None:
    """打印全量 from→to 计划。幂等行加标记、脏字段提示、状态/联动预警，整体统计。"""
    print(f"\n📋 批量修改计划（共 {len(plan)} 条）")
    print("=" * 80)
    idempotent_count = sum(1 for item in plan if item["_idempotent"])
    total_dirty = sum(len(p["_dirty_fixes"]) for p in plan)
    total_cf120_warn = sum(1 for p in plan if p["_needs_cf120_warning"])
    if idempotent_count:
        print(f"💡 其中 {idempotent_count} 条全部字段已是目标值（幂等）")
        print(f"   执行时默认跳过（加 --force-idempotent 强制执行）")
    if total_dirty:
        print(f"⚠️  发现 {total_dirty} 个 date 字段脏值（带时间），不带 --fix-dirty-dates 执行会 422")
        print(f"   加 --fix-dirty-dates 自动修复（随本次更新一并覆盖成 YYYY-MM-DD）")
    if total_cf120_warn:
        print(f"⚠️  {total_cf120_warn} 条案卷 cf120（实际研发处理人）为空且未提供，可能 422")
        print(f"   详见 references/troubleshooting.md '实际研发处理人 不能为空字符' 节")
    print("=" * 80)
    for item in plan:
        marker = "  [幂等]" if item["_idempotent"] else ""
        status_info = ""
        if item.get("_status"):
            extras = [f"status={item['_status']}"]
            if item.get("_assigned_to_id"):
                extras.append(f"指派人={item['_assigned_to_id']}")
            status_info = "  [" + ", ".join(extras) + "]"
        print(f"\n案卷 #{item['case_id']}（第 {item['_lineno']} 行）{marker}{status_info}")
        if not item["changes"]:
            print("  （无字段改动）")
        else:
            width = max(len(c["field"]) for c in item["changes"])
            for c in item["changes"]:
                print(f"  {c['field']:<{width}}  {c['from']}  →  {c['to']}")
        if item["_dirty_fixes"]:
            for d in item["_dirty_fixes"]:
                print(f"  [脏日期] custom_field_{d['cf_id']}  {d['current']}  →  {d['fixed']}")
        if item["_needs_cf120_warning"]:
            print(f"  ⚠️  cf120（实际研发处理人）当前为空，改 custom_field 可能 422（见 references/troubleshooting.md）")
        print(f"  备注：{item['opinion']}")
    print("\n" + "=" * 80)


def build_forward_args(item: dict, global_product: str, global_task_type: str,
                       update_only: bool, field_cols: list[str],
                       fix_dirty_dates: bool = False) -> list[str]:
    """把一行预览记录翻译成 issue_case_forward.py 的命令行参数。

    fix_dirty_dates=True 时，把 item["_dirty_fixes"] 里的脏字段修复值也加进 --custom-field，
    让 forward 把这些合法值随本次更新一并提交（覆盖脏值，避免 422）。
    """
    args = [
        sys.executable, str(FORWARD_SCRIPT),
        "--case-id", item["case_id"],
        "--opinion", item["opinion"],
    ]

    # 产品 / 流转类型：优先行内列，其次全局参数
    product = item["_raw"].get("product") or global_product
    task_type = item["_raw"].get("task_type") or global_task_type
    if update_only:
        args.append("--update-only")
    else:
        if product:
            args += ["--product", product]
        if task_type:
            args += ["--task-type", task_type]

    # 字段覆盖
    for col in field_cols:
        value = item["_raw"].get(col, "")
        if value == "":
            continue
        if col.startswith("custom_field_"):
            field_id = col.replace("custom_field_", "")
            # #clear 是 batch_update 的清空标记：转空串传给 forward（Redmine 以空串清空字段）
            # 否则脚本会把字面字符串 "#clear" 塞到 PUT body，触发"不是合法日期"等 422
            if value == "#clear":
                value = ""
            args += ["--custom-field", f"{field_id}={value}"]
        elif col == "assigned_to_id":
            args += ["--assigned-to-id", value]
        elif col == "status_id":
            args += ["--status-id", value]
        elif col == "fixed_version_id":
            args += ["--fixed-version-id", value]
        elif col == "priority_id":
            args += ["--priority-id", value]
        elif col == "due_date":
            args += ["--due-date", value]
        elif col == "start_date":
            args += ["--start-date", value]
        elif col == "tester_id":
            args += ["--tester-id", value]
        elif col == "product":
            # product 走 --issue-product（标准字段 product），区别于 --product（产品模板）
            args += ["--issue-product", value]
        elif col == "module_id":
            args += ["--module-id", value]
        elif col == "project_id":
            args += ["--project-id", value]
        # 其它标准字段：暂未在 forward 暴露 CLI，跳过

    # 脏日期修复：把 item._dirty_fixes 里每个 cf 也加进 --custom-field
    if fix_dirty_dates:
        for d in item.get("_dirty_fixes", []):
            args += ["--custom-field", f"{d['cf_id']}={d['fixed']}"]

    return args


def execute(plan: list[dict], global_product: str, global_task_type: str,
            update_only: bool, field_cols: list[str],
            force_idempotent: bool = False,
            fix_dirty_dates: bool = False) -> tuple[int, list[dict], int]:
    """逐条执行 forward，返回 (成功数, 失败记录列表, 跳过数)。"""
    success = 0
    skipped = 0
    failed = []
    total = len(plan)
    for idx, item in enumerate(plan, start=1):
        # 幂等行默认跳过（除非 --force-idempotent）
        if item["_idempotent"] and not force_idempotent:
            skipped += 1
            print(f"\n[{idx}/{total}] 案卷 #{item['case_id']} ... ⏭️  幂等，跳过", flush=True)
            continue
        cmd = build_forward_args(
            item, global_product, global_task_type, update_only, field_cols,
            fix_dirty_dates=fix_dirty_dates)
        marker = " +脏值修复" if fix_dirty_dates and item.get("_dirty_fixes") else ""
        print(f"\n[{idx}/{total}] 案卷 #{item['case_id']} ...{marker}", flush=True)
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode == 0:
            success += 1
            print(f"  ✅ 成功")
        else:
            failed.append(item["_raw"])
            print(f"  ❌ 失败（退出码 {result.returncode}）")
    return success, failed, skipped


def write_failed_csv(csv_path: Path, fieldnames: list[str], failed_rows: list[dict]) -> Path:
    """把失败的行写成 <input>.failed.csv，结构与输入一致，便于续跑。"""
    failed_path = csv_path.with_suffix(csv_path.suffix + ".failed.csv")
    # 失败行可能带 _lineno 等内部字段，按原列头写出
    clean_fieldnames = [f for f in fieldnames if f]
    with failed_path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=clean_fieldnames)
        writer.writeheader()
        for row in failed_rows:
            writer.writerow({k: row.get(k, "") for k in clean_fieldnames})
    return failed_path


def confirm(prompt: str) -> bool:
    """读 stdin 确认。"""
    try:
        answer = input(f"\n{prompt} [y/N] ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def main() -> None:
    args = parse_args()
    csv_path = Path(args.input)
    if not csv_path.exists():
        raise SystemExit(f"CSV 文件不存在：{csv_path}")

    # 非 update-only 时必须有 product + task_type
    if not args.update_only:
        if not args.product and "product" not in csv_path.read_text(encoding="utf-8-sig"):
            # 简单兜底：允许行内 product 列提供
            pass
        if not args.product:
            raise SystemExit("非 update-only 模式必须提供 --product（或在 CSV 加 product 列）")

    fieldnames, rows = load_rows(csv_path)
    if not rows:
        raise SystemExit("CSV 没有数据行")

    validate_header(fieldnames, args.update_only)
    standard_cols, custom_cols, _ = split_field_columns(fieldnames)
    field_cols = standard_cols + custom_cols
    if not field_cols:
        raise SystemExit("CSV 没有可修改的字段列（custom_field_<id> 或标准字段）")

    print(f"读取 {len(rows)} 行，可改字段列：{field_cols}")

    # 1. 预览
    plan = build_preview_table(rows, field_cols, skip_fetch=args.skip_fetch)
    print_preview(plan)

    if args.dry_run:
        print("\n🔍 dry-run 模式，未提交。去掉 --dry-run 执行。")
        return

    # 2. 强警告：发现 date 脏值但没加 --fix-dirty-dates，会 422
    total_dirty = sum(len(p["_dirty_fixes"]) for p in plan)
    if total_dirty and not args.fix_dirty_dates:
        print(f"\n❌ 检测到 {total_dirty} 个 date 字段脏值，不加 --fix-dirty-dates 几乎肯定 422")
        print(f"   选项：")
        print(f"     A) 加 --fix-dirty-dates 自动修复（推荐）")
        print(f"     B) 中断，在 CSV 里手动加 custom_field_<id>=<YYYY-MM-DD> 列")
        if not args.yes:
            if not confirm("仍然继续（继续会让这些行 422）？"):
                print("已取消。加 --fix-dirty-dates 重跑。")
                return
        else:
            print("⚠️  --yes 模式下仍然继续（用户已确认风险）")

    # 2b. cf120 联动预警：有 custom_field 改动但 cf120 空
    total_cf120_warn = sum(1 for p in plan if p["_needs_cf120_warning"])
    if total_cf120_warn:
        print(f"\n⚠️  {total_cf120_warn} 条案卷 cf120（实际研发处理人）为空")
        print(f"   改 custom_field 字段时 Redmine 可能 422 '实际研发处理人 不能为空字符'")
        print(f"   选项：")
        print(f"     A) 中断，在 CSV 里加 custom_field_120=<研发 ID> 列")
        print(f"     B) 仍然继续（如果确定这些行不会触发校验）")
        if not args.yes:
            if not confirm("仍然继续？"):
                print("已取消。")
                return
        else:
            print("⚠️  --yes 模式下仍然继续（用户已确认风险）")

    # 3. 提交前确认
    if not args.yes:
        if not confirm(f"即将提交 {len(plan)} 条修改，是否继续？"):
            print("已取消。")
            return

    # 4. 逐条执行
    success, failed, skipped = execute(
        plan, args.product or "", args.task_type or "",
        args.update_only, field_cols,
        force_idempotent=args.force_idempotent,
        fix_dirty_dates=args.fix_dirty_dates)

    # 4. 汇总
    print(f"\n{'=' * 80}")
    summary = f"✅ 成功 {success} / ❌ 失败 {len(failed)}"
    if skipped:
        summary += f" / ⏭️  幂等跳过 {skipped}"
    print(summary)
    if failed:
        failed_path = write_failed_csv(csv_path, fieldnames, failed)
        print(f"失败清单已写入：{failed_path}（修好后可重跑）")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
