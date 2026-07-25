from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


DEFAULT_STATUS_OPTIONS = ["无需处理", "已经处理"]
BATCH_SIZE = 20


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_dws(args: list[str]) -> dict:
    cmd = ["dws", *args, "--format", "json", "--yes"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = p.stdout.decode("utf-8", "replace")
    err = p.stderr.decode("utf-8", "replace")
    if p.returncode != 0:
        raise RuntimeError(f"dws failed: {' '.join(cmd)}\nstdout={out}\nstderr={err}")
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"dws returned non-json: {' '.join(cmd)}\n{out}\n{err}") from exc
    status = str(data.get("status") or data.get("code") or "").lower()
    if status and status not in ("success", "ok", "0"):
        raise RuntimeError(f"dws returned failure: {' '.join(cmd)}\n{out}\n{err}")
    return data


def data_of(resp: dict) -> dict:
    return resp.get("data") or resp


def create_base(name: str, desc: str | None = None) -> str:
    base_id = data_of(run_dws(["aitable", "base", "create", "--name", name]))["baseId"]
    if desc:
        run_dws(["aitable", "base", "update", "--base-id", base_id, "--name", name, "--desc", desc])
    return base_id


def get_first_table(base_id: str) -> str:
    data = data_of(run_dws(["aitable", "base", "get", "--base-id", base_id]))
    return (data.get("tables") or [])[0]["tableId"]


def rename_table(base_id: str, table_id: str, name: str) -> None:
    run_dws(["aitable", "table", "update", "--base-id", base_id, "--table-id", table_id, "--name", name])


def list_fields(base_id: str, table_id: str) -> list[dict]:
    data = data_of(run_dws(["aitable", "field", "get", "--base-id", base_id, "--table-id", table_id]))
    return data.get("fields") or []


def rename_field(base_id: str, table_id: str, field_id: str, name: str) -> None:
    run_dws(["aitable", "field", "update", "--base-id", base_id, "--table-id", table_id, "--field-id", field_id, "--name", name])


def create_fields(base_id: str, table_id: str, fields: list[dict]) -> None:
    run_dws([
        "aitable", "field", "create",
        "--base-id", base_id,
        "--table-id", table_id,
        "--fields", json.dumps(fields, ensure_ascii=False),
    ])


def patch_options(base_id: str, table_id: str, field_id: str, options: list[str]) -> None:
    run_dws([
        "aitable", "field", "update",
        "--base-id", base_id,
        "--table-id", table_id,
        "--field-id", field_id,
        "--config", json.dumps({"options": [{"name": x} for x in options]}, ensure_ascii=False),
    ])


def user_cells(userids: list[str] | None) -> list[dict]:
    seen, out = set(), []
    for uid in userids or []:
        uid = str(uid).strip()
        if uid and uid not in seen:
            seen.add(uid)
            out.append({"userId": uid})
    return out


def visibility_userids(row: dict, include_sales: bool) -> list[str]:
    keys = ["project_manager_userids", "province_lead_userids", "region_lead_userids", "district_lead_userids"]
    if include_sales:
        keys.append("sales_manager_userids")
    ids = []
    for key in keys:
        ids.extend(row.get(key) or [])
    if row.get("visibility_userids"):
        ids.extend(row["visibility_userids"])
    return [x["userId"] for x in user_cells(ids)]


def build_records(projects: list[dict], fields: dict[str, str], plan: dict) -> list[dict]:
    include_sales = bool(plan.get("include_sales_manager_in_visibility"))
    default_status = (plan.get("status_options") or DEFAULT_STATUS_OPTIONS)[0]
    records = []
    for row in projects:
        cells = {
            fields["项目名称"]: row.get("project_name") or "",
            fields["反馈内容"]: plan["feedback_content"],
            fields["反馈处理情况"]: default_status,
        }
        optional_text = {
            "项目编号": row.get("project_no"),
            "项目大区": row.get("project_region_group"),
            "项目区域": row.get("project_area"),
            "匹配备注": row.get("match_note"),
        }
        for name, value in optional_text.items():
            if value not in (None, "") and name in fields:
                cells[fields[name]] = value
        user_map = {
            "项目经理": row.get("project_manager_userids"),
            "项目销售经理": row.get("sales_manager_userids"),
            "省份总": row.get("province_lead_userids"),
            "大区总": row.get("region_lead_userids"),
            "片区总": row.get("district_lead_userids"),
            "可见人员": visibility_userids(row, include_sales),
        }
        for name, ids in user_map.items():
            users = user_cells(ids)
            if users and name in fields:
                cells[fields[name]] = users
        records.append({"cells": cells})
    return records


def create_records(base_id: str, table_id: str, records: list[dict]) -> None:
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        run_dws([
            "aitable", "record", "create",
            "--base-id", base_id,
            "--table-id", table_id,
            "--records", json.dumps(batch, ensure_ascii=False),
        ])
        print(f"[records] pushed {min(i + BATCH_SIZE, len(records))}/{len(records)}")


def main(plan_path: Path, projects_path: Path) -> Path:
    plan = load_json(plan_path)
    projects = load_json(projects_path)
    if not plan.get("feedback_content"):
        raise SystemExit("plan.feedback_content is required")
    status_options = list(dict.fromkeys(plan.get("status_options") or DEFAULT_STATUS_OPTIONS))

    base_id = create_base(plan["base_name"], plan.get("base_desc"))
    table_id = get_first_table(base_id)
    rename_table(base_id, table_id, "项目反馈")

    primary_id = list_fields(base_id, table_id)[0]["fieldId"]
    rename_field(base_id, table_id, primary_id, "项目名称")

    create_fields(base_id, table_id, [
        {"fieldName": "项目编号", "type": "text"},
        {"fieldName": "项目大区", "type": "text"},
        {"fieldName": "项目区域", "type": "text"},
        {"fieldName": "项目经理", "type": "user"},
        {"fieldName": "项目销售经理", "type": "user"},
        {"fieldName": "省份总", "type": "user"},
        {"fieldName": "大区总", "type": "user"},
        {"fieldName": "片区总", "type": "user"},
        {"fieldName": "反馈内容", "type": "text"},
        {"fieldName": "反馈处理情况", "type": "singleSelect"},
        {"fieldName": "反馈处理截图证明", "type": "attachment"},
        {"fieldName": "反馈处理人", "type": "user"},
        {"fieldName": "反馈处理时间", "type": "date", "property": {"dateFormat": "YYYY-MM-DD HH:mm", "includeTime": True}},
        {"fieldName": "可见人员", "type": "user", "property": {"multiple": True}},
        {"fieldName": "匹配备注", "type": "text"},
    ])
    time.sleep(0.5)

    name_to_id = {f["fieldName"]: f["fieldId"] for f in list_fields(base_id, table_id)}
    patch_options(base_id, table_id, name_to_id["反馈处理情况"], status_options)

    records = build_records(projects, name_to_id, plan)
    create_records(base_id, table_id, records)

    meta = {
        "baseId": base_id,
        "tableId": table_id,
        "url": f"https://alidocs.dingtalk.com/i/nodes/{base_id}",
        "targetKnowledgeNodeId": plan.get("knowledge_node_id"),
        "fields": name_to_id,
        "recordCount": len(records),
        "visibilityNote": "已写入可见人员字段；行级权限需通过钉钉前端或权限 API 绑定该字段后才算生效。",
    }
    out = plan_path.parent / "table_meta.json"
    dump_json(out, meta)
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/create_aitable.py <plan.json> <projects_enriched.json>")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
