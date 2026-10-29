#!/usr/bin/env python3

import argparse
import json
import os
import re
import ssl
import subprocess
import urllib.error
import urllib.request
from copy import deepcopy
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

SCRIPT_DIR = Path(__file__).resolve().parent
QUERY_USER_SCRIPT = SCRIPT_DIR / "query_user.sh"

EXAMPLE_CONFIG_PATH = SCRIPT_DIR / "issue_case_forward.example.yml"
LOCAL_CONFIG_PATH = SCRIPT_DIR / "issue_case_forward.local.yml"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/149.0.0.0 Safari/537.36"
)

OPERATION_RULES = {
    "需求分析流转": {"status_name": "研发分派", "assignee_field": "assigned_to_zg", "include_target_version": False},
    "研发分派流转": {"status_name": "开发中", "assignee_field": "assigned_to_kf", "include_target_version": True},
    "研发完成流转": {
        "status_name": "研发完成",
        "assignee_field": "assigned_to_zg",
        "include_target_version": True,
    },
    "研发验证流转": {"status_name": "产品验证", "assignee_field": "assigned_to_cp", "include_target_version": False},
    "产品验证流转": {"status_name": "测试中", "assignee_field": "assigned_to_cs", "include_target_version": False},
    "测试验证流转": {"status_name": "已解决", "assignee_field": "assigned_to_gc", "include_target_version": False},
    "研发关闭流转": {
        "status_name": "已关闭",
        "assignee_field": "",
        "include_target_version": False,
        "assign_to_author": True,
    },
    "工程验证流转": {"status_name": "已关闭", "assignee_field": "assigned_to_gc", "include_target_version": False},
}

ISSUE_FIELD_WHITELIST = {
    "status_id",
    "assigned_to_id",
    "fixed_version_id",
    "priority_id",
    "start_date",
    "due_date",
    "tester_id",
    "product",
    "module_id",
    "project_id",
    "tracker_id",
    "parent_issue_id",
    "estimated_hours",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按产品+流转操作模板批转案卷")
    parser.add_argument("--case-id", required=True, help="案卷ID或案卷URL")
    parser.add_argument("--product", help="产品类型（--update-only 模式下可省略）")
    parser.add_argument("--task-type", help="流转操作类型（--update-only 模式下可省略）")
    parser.add_argument("--opinion", required=True, help="流转备注")

    parser.add_argument("--assigned-to-user",
                        help="覆盖指派给的用户（姓名或全拼），内部会调用 query_user.sh 查询 ID")
    parser.add_argument("--assigned-to-id",
                        help="覆盖指派给 assigned_to_id（直接使用 ID）")
    parser.add_argument("--status-id", help="覆盖状态 status_id")
    parser.add_argument("--fixed-version-id", help="覆盖目标版本 fixed_version_id")

    parser.add_argument("--priority-id", help="优先级 priority_id")
    parser.add_argument("--start-date", help="开始日期 start_date (YYYY-MM-DD)")
    parser.add_argument("--due-date", help="计划完成日期 due_date (YYYY-MM-DD)")
    parser.add_argument("--tester-id", help="测试人员 tester_id")
    parser.add_argument("--issue-product", help="产品 product")
    parser.add_argument("--module-id", help="模块 module_id")
    parser.add_argument("--project-id", help="项目 project_id")

    parser.add_argument("--dev-estimate-point",
                        help="研发预估积分 dev_estimate_point")
    parser.add_argument("--point", help="积分 point")
    parser.add_argument("--include-product-reason",
                        help="纳入/不纳入产品的原因 include_product_reason")

    parser.add_argument("--custom-field", action="append", metavar="ID=VALUE",
                        default=[],
                        help="覆盖自定义字段，格式 custom_field_<id>=<值>，"
                        "可重复，例如 --custom-field 335=2026-08-15 "
                        "--custom-field 346=督办延期")
    parser.add_argument("--update-only", action="store_true",
                        help="只改字段+评论，不触发流转；放宽 status_id/assigned_to_id 必填")

    parser.add_argument("--dry-run", action="store_true", help="仅打印请求，不实际提交")
    return parser.parse_args()


def load_yaml(path: Path) -> dict:
    if yaml is None:
        return load_simple_yaml(path)
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict):
            raise SystemExit(f"配置文件格式错误: {path}")
        return data


def parse_simple_yaml_scalar(value: str):
    raw = value.strip()
    if raw in {"", '""', "''"}:
        return ""
    if raw == "[]":
        return []
    if raw == "{}":
        return {}
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw


def load_simple_yaml(path: Path) -> dict:
    """Small YAML subset parser for the bundled flat config file."""
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            raise SystemExit(f"配置文件格式错误: {path} 行 `{raw}`")
        key, value = stripped.split(":", 1)
        key = key.strip().strip('"').strip("'")
        value = value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value == "":
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_simple_yaml_scalar(value)
    return root


def ensure_local_config() -> None:
    if LOCAL_CONFIG_PATH.exists():
        return
    if not EXAMPLE_CONFIG_PATH.exists():
        raise SystemExit(f"缺少模板配置文件: {EXAMPLE_CONFIG_PATH}")
    LOCAL_CONFIG_PATH.write_text(EXAMPLE_CONFIG_PATH.read_text(
        encoding="utf-8"), encoding="utf-8")


def migrate_legacy_config(config: dict) -> dict:
    if "products" in config and "task_type_aliases" in config and "operation_status_ids" in config:
        return config

    migrated = deepcopy(config)

    if not isinstance(migrated.get("product_aliases"), dict) or not migrated.get("product_aliases"):
        migrated["product_aliases"] = {
            "悟空": "悟空",
            "灵珑": "灵珑",
            "统一用户中心2.0": "统一用户中心2.0",
            "麒舰平台": "麒舰平台",
            "智能体平台": "智能体平台",
            "星桥": "星桥",
        }

    if not isinstance(migrated.get("task_type_aliases"), dict) or not migrated.get("task_type_aliases"):
        migrated["task_type_aliases"] = {
            name: name for name in OPERATION_RULES.keys()}

    if not isinstance(migrated.get("operation_status_ids"), dict) or not migrated.get("operation_status_ids"):
        migrated["operation_status_ids"] = {
            name: "" for name in OPERATION_RULES.keys()}

    if not isinstance(migrated.get("products"), dict) or not migrated.get("products"):
        migrated["products"] = {
            "默认": {
                "assigned_to_kf": "",
                "assigned_to_zg": "",
                "assigned_to_cp": "",
                "assigned_to_cs": "",
                "assigned_to_gc": "",
                "target_version": "",
            }
        }

    if "base_payload" not in migrated or not isinstance(migrated.get("base_payload"), dict):
        migrated["base_payload"] = {
            "priority_id": "",
            "start_date": "",
            "due_date": "",
            "tester_id": "",
            "product": "",
            "module_id": "",
            "project_id": "",
            "tracker_id": "",
            "parent_issue_id": "",
            "estimated_hours": "",
            "extra_fields": {},
        }

    if not isinstance(migrated.get("report_user_id_fields"), list):
        migrated["report_user_id_fields"] = []
    if not isinstance(migrated.get("report_user_name_fields"), list):
        migrated["report_user_name_fields"] = []

    return migrated


def load_runtime_config() -> dict:
    ensure_local_config()
    config = load_yaml(LOCAL_CONFIG_PATH)
    config = migrate_legacy_config(config)

    required = [
        "product_aliases",
        "task_type_aliases",
        "operation_status_ids",
        "products",
        "base_payload",
    ]
    for key in required:
        if key not in config:
            raise SystemExit(f"配置缺少必要字段: {key}")
    return config


def normalize_case_id(value: str) -> str:
    raw = str(value).strip()
    matched = re.search(r"/issues/(\d+)", raw)
    if matched:
        return matched.group(1)
    if raw.isdigit():
        return raw
    raise SystemExit(f"无效的 case-id: {value}")


def normalize_alias(value: str, aliases: dict, label: str) -> str:
    key = value.strip()
    if key not in aliases:
        options = "、".join(sorted(aliases.keys()))
        raise SystemExit(f"不支持的{label}: {value}，可选值：{options}")
    canonical = aliases[key]
    canonical_key = str(canonical).strip()
    if not canonical_key:
        raise SystemExit(f"{label}别名映射不能为空: {value}")
    return canonical_key


def resolve_user_by_query(user_query: str) -> tuple:
    """通过 query_user.sh 查询用户，返回 (user_id, user_name)"""
    if not QUERY_USER_SCRIPT.exists():
        raise SystemExit(f"缺少用户查询脚本: {QUERY_USER_SCRIPT}")

    proc = subprocess.run(
        ["bash", str(QUERY_USER_SCRIPT), "--q", user_query, "--limit", "20"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy(),
    )
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or "未知错误"
        raise SystemExit(f"查询用户失败: {message}")

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"查询用户失败：返回不是 JSON ({exc})")

    users = payload.get("users") if isinstance(payload, dict) else None
    if not isinstance(users, list) or not users:
        raise SystemExit(f"未找到匹配用户: {user_query}")

    # 优先精确匹配 login
    exact = None
    q = user_query.strip().lower()
    for item in users:
        if not isinstance(item, dict):
            continue
        login = str(item.get("login", "")).strip().lower()
        if login == q:
            exact = item
            break

    user = exact or users[0]
    user_id = user.get("id")
    firstname = str(user.get("firstname", "")).strip()
    lastname = str(user.get("lastname", "")).strip()
    user_name = f"{lastname}{firstname}".strip()

    if user_id in (None, ""):
        raise SystemExit(f"查询用户结果缺少 id: {user_query}")

    return str(user_id), user_name


def split_assignee(value: str):
    raw = str(value or "").strip()
    if not raw:
        return "", ""
    if ":" in raw:
        name, uid = raw.rsplit(":", 1)
        return name.strip(), uid.strip()
    if raw.isdigit():
        return "", raw
    return raw, ""


def fetch_issue_author(case_id: str) -> tuple[str, str]:
    api_key = os.environ.get("REDMINE_API_KEY", "")
    if not api_key:
        raise SystemExit("REDMINE_API_KEY is required to resolve issue author")

    base_url = os.environ.get(
        "REDMINE_BASE_URL", "https://faq.egova.com.cn:7787").rstrip("/")
    insecure = os.environ.get("REDMINE_INSECURE_SKIP_VERIFY", "").lower() in {
        "1", "true", "yes"}
    context = ssl._create_unverified_context() if insecure else None
    url = f"{base_url}/issues/{case_id}.json"
    request = urllib.request.Request(
        url=url,
        method="GET",
        headers={
            "Accept": "application/json",
            "X-Redmine-API-Key": api_key,
            "User-Agent": os.environ.get("EGOVA_USER_AGENT", DEFAULT_USER_AGENT),
        },
    )

    try:
        with urllib.request.urlopen(request, context=context) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"查询案卷创建人失败: {exc.code} {error_body}")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"查询案卷创建人失败：返回不是 JSON ({exc})")

    issue = payload.get("issue") if isinstance(payload, dict) else None
    author = issue.get("author") if isinstance(issue, dict) else None
    if not isinstance(author, dict) or not author.get("id"):
        raise SystemExit(f"查询案卷创建人失败：案卷 {case_id} 缺少 author.id")

    return str(author["id"]), str(author.get("name", "")).strip()


def apply_operation_defaults(payload: dict, product_fields: dict, operation_status_ids: dict, task_type_key: str) -> None:
    if task_type_key not in OPERATION_RULES:
        options = "、".join(OPERATION_RULES.keys())
        raise SystemExit(f"不支持的流转操作: {task_type_key}，可选值：{options}")

    rule = OPERATION_RULES[task_type_key]
    payload["status_name"] = rule["status_name"]

    status_id = str(operation_status_ids.get(task_type_key, "")).strip()
    if status_id:
        payload["status_id"] = status_id

    assignee_key = rule["assignee_field"]
    assignee_name, assignee_id = split_assignee(
        product_fields.get(assignee_key, ""))
    if assignee_name:
        payload["target_user"] = assignee_name
    if assignee_id:
        payload["assigned_to_id"] = assignee_id

    if rule["include_target_version"]:
        version_value = str(product_fields.get("target_version", "")).strip()
        if version_value:
            payload["fixed_version_id"] = version_value


def normalize_payload_aliases(payload: dict) -> None:
    payload.pop("done_ratio", None)
    payload.pop("affected_version_id", None)
    payload.pop("sprint_id", None)
    payload.pop("test_progress", None)
    payload.pop("test_key_point", None)
    payload.pop("target_department", None)
    payload.pop("target_user", None)
    payload.pop("deadline", None)


def build_payload(
    args: argparse.Namespace,
    config: dict,
    case_id: str,
    product_key: str,
    task_type_key: str,
) -> dict:
    update_only = bool(getattr(args, "update_only", False))
    payload = deepcopy(config.get("base_payload", {}))

    # update-only 模式：跳过产品模板校验（只改字段+评论，不走流转模板）
    if not update_only:
        product_fields = config.get("products", {}).get(product_key)
        if not isinstance(product_fields, dict):
            raise SystemExit(f"产品模板不存在: {product_key}")

        apply_operation_defaults(payload, product_fields, config.get(
            "operation_status_ids", {}), task_type_key)

    payload["case_id"] = case_id
    payload["case_type"] = task_type_key
    payload["opinion"] = args.opinion
    rule = OPERATION_RULES.get(task_type_key, {})

    # 处理 assigned_to_user（优先级高于 assigned_to_id）
    if args.assigned_to_user is not None:
        user_id, user_name = resolve_user_by_query(args.assigned_to_user)
        payload["assigned_to_id"] = user_id
    elif args.assigned_to_id is not None:
        payload["assigned_to_id"] = args.assigned_to_id
    elif rule.get("assign_to_author"):
        author_id, author_name = fetch_issue_author(case_id)
        payload["assigned_to_id"] = author_id
        if author_name:
            payload["target_user"] = author_name
    if args.status_id is not None:
        payload["status_id"] = args.status_id
    if args.fixed_version_id is not None:
        payload["fixed_version_id"] = args.fixed_version_id

    if args.priority_id is not None:
        payload["priority_id"] = args.priority_id
    if args.start_date is not None:
        payload["start_date"] = args.start_date
    if args.due_date is not None:
        payload["due_date"] = args.due_date
    if args.tester_id is not None:
        payload["tester_id"] = args.tester_id
    if args.issue_product is not None:
        payload["product"] = args.issue_product
    if args.module_id is not None:
        payload["module_id"] = args.module_id
    if args.project_id is not None:
        payload["project_id"] = args.project_id

    if args.dev_estimate_point is not None:
        payload["dev_estimate_point"] = args.dev_estimate_point
    if args.point is not None:
        payload["point"] = args.point
    if args.include_product_reason is not None:
        payload["include_product_reason"] = args.include_product_reason

    # 解析 --custom-field id=value，写入 custom_field_<id> 键（build_issue_update 再转嵌套数组）
    for item in getattr(args, "custom_field", None) or []:
        if "=" not in item:
            raise SystemExit(
                f"--custom-field 格式错误（应为 id=value）：{item}")
        raw_id, value = item.split("=", 1)
        field_id = raw_id.strip()
        if not re.match(r"\d+", field_id):
            raise SystemExit(
                f"--custom-field 的 id 必须为数字：{item}")
        payload[f"custom_field_{field_id}"] = value

    normalize_payload_aliases(payload)
    return payload


def validate_payload(payload: dict, update_only: bool = False) -> None:
    required = ["case_id", "opinion"]
    # update-only 模式只改字段+评论，放宽 case_type 必填
    if not update_only:
        required.append("case_type")
    missing = [key for key in required if not payload.get(key)]
    if missing:
        raise SystemExit(f"缺少必要字段: {', '.join(missing)}")

    # update-only 模式：跳过 assigned_to_id / status_id 必填校验（只改自定义字段也合法）
    if update_only:
        return

    if not payload.get("assigned_to_id"):
        raise SystemExit("缺少 assigned_to_id，请检查产品默认指派人或通过 --assigned-to-id 覆盖")

    if not payload.get("status_id"):
        raise SystemExit(
            "缺少 status_id，请在配置 operation_status_ids 中填写或通过 --status-id 覆盖")


def build_issue_update(payload: dict) -> dict:
    issue = {"notes": payload["opinion"]}
    for key in ISSUE_FIELD_WHITELIST:
        value = payload.get(key)
        if value not in (None, ""):
            issue[key] = value
    # 扫描 custom_field_<id> 键，转成 Redmine 嵌套数组 custom_fields
    # 格式与 issue_case_create.py 一致：{"id": <int>, "value": <str>}
    # 即使 value 为空串也发出：用户显式 --custom-field 335=#clear 时需要把 cf335 清空
    # （Redmine 以空串清空字段；batch_update.py 会把 "#clear" 转空字符串再传过来）
    # base_payload 里没有 custom_field_* 键，所以不会误发空值
    custom_fields = []
    for key, value in payload.items():
        match = re.match(r'custom_field_(\d+)$', key)
        if match:
            custom_fields.append({"id": int(match.group(1)), "value": str(value)})
    if custom_fields:
        issue["custom_fields"] = custom_fields
    return issue


def resolve_request(payload: dict):
    base_url = os.environ.get(
        "REDMINE_BASE_URL", "https://faq.egova.com.cn:7787").rstrip("/")
    custom_endpoint = os.environ.get("REDMINE_FORWARD_ENDPOINT", "").strip()

    if custom_endpoint:
        endpoint = custom_endpoint
        body = payload
    else:
        if not base_url:
            raise SystemExit(
                "REDMINE_BASE_URL 未设置，且 REDMINE_FORWARD_ENDPOINT 为空")
        endpoint = f"{base_url}/issues/{payload['case_id']}.json"
        body = {"issue": build_issue_update(
            payload), "forward_context": payload}

    method = "PUT" if endpoint.endswith(".json") else "POST"
    body_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8")
    return endpoint, method, body, body_bytes


def send_request(url: str, method: str, body_bytes: bytes) -> dict:
    api_key = os.environ.get("REDMINE_API_KEY", "")
    if not api_key:
        raise SystemExit("REDMINE_API_KEY is required")

    insecure = os.environ.get("REDMINE_INSECURE_SKIP_VERIFY", "").lower() in {
        "1", "true", "yes"}
    context = ssl._create_unverified_context() if insecure else None

    request = urllib.request.Request(
        url=url,
        data=body_bytes,
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-Redmine-API-Key": api_key,
            "User-Agent": os.environ.get("EGOVA_USER_AGENT", DEFAULT_USER_AGENT),
        },
    )

    try:
        with urllib.request.urlopen(request, context=context) as response:
            raw = response.read().decode("utf-8")
            return {
                "ok": True,
                "status": response.status,
                "body": json.loads(raw) if raw else {},
            }
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": exc.code,
            "body": error_body,
        }


def main() -> None:
    args = parse_args()
    config = load_runtime_config()

    case_id = normalize_case_id(args.case_id)

    # update-only 模式下 product / task-type 可省略；否则两者必填并走别名归一
    if args.update_only:
        product_key = args.product or ""
        task_type_key = args.task_type or ""
    else:
        if not args.product:
            raise SystemExit("缺少 --product（或使用 --update-only 仅改字段）")
        if not args.task_type:
            raise SystemExit("缺少 --task-type（或使用 --update-only 仅改字段）")
        product_key = normalize_alias(
            args.product, config["product_aliases"], "产品类型")
        task_type_key = normalize_alias(
            args.task_type, config["task_type_aliases"], "流转操作")
    merged_payload = build_payload(
        args,
        config,
        case_id,
        product_key,
        task_type_key,
    )
    validate_payload(merged_payload, update_only=getattr(args, "update_only", False))

    url, method, request_body, request_body_bytes = resolve_request(
        merged_payload)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "url": url,
                    "method": method,
                    "merged_payload": merged_payload,
                    "request_body": request_body,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    result = send_request(url, method, request_body_bytes)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("ok"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
