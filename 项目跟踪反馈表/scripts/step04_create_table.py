"""Step 4：建 dws AI 表格（base + 默认表 rename + 主字段 rename + 各类字段 + 单选 options 补刀）。

输出  : work_dir/table_meta.json   {baseId, tableId, viewId, fieldIds:{...}}

字段顺序（视图列序）：
  项目(primaryDoc) / 大区(singleSelect) / 区域(text) / 项目经理(user) /
  result_field(singleSelect, plan.result_options) /
  extra_text_fields[*](text) /
  反馈状态(singleSelect) / 反馈备注(text) / 反馈时间(date) /
  [可选] 大区工程总(user) / 省份工程总(user)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts import _config as cfg
from scripts._common import call_dws, dws_ok, work_path


def _create_base(name: str) -> str:
    d, out, err = call_dws(["aitable", "base", "create", "--name", name, "-y"])
    assert dws_ok(d), f"create base failed: {out}"
    return d["data"]["baseId"]


def _get_default_table(base_id: str) -> tuple[str, str]:
    d, out, err = call_dws(["aitable", "base", "get", "--base-id", base_id, "-y"])
    assert dws_ok(d), f"base get failed: {out}"
    tables = (d.get("data") or {}).get("tables") or []
    return tables[0]["tableId"], tables[0]["tableName"]


def _rename_table(base_id: str, table_id: str, new_name: str) -> None:
    d, out, err = call_dws(["aitable", "table", "update", "--base-id", base_id, "--table-id", table_id, "--name", new_name, "-y"])
    assert dws_ok(d), f"rename table failed: {out}"


def _list_fields(base_id: str, table_id: str) -> list[dict]:
    d, out, err = call_dws(["aitable", "field", "get", "--base-id", base_id, "--table-id", table_id, "-y"])
    assert dws_ok(d), f"list fields failed: {out}"
    return (d.get("data") or {}).get("fields") or []


def _rename_field(base_id: str, table_id: str, field_id: str, new_name: str) -> None:
    d, out, err = call_dws(["aitable", "field", "update", "--base-id", base_id, "--table-id", table_id, "--field-id", field_id, "--name", new_name, "-y"])
    assert dws_ok(d), f"rename field {field_id} failed: {out}"


def _create_fields(base_id: str, table_id: str, fields_spec: list[dict]) -> None:
    d, out, err = call_dws(["aitable", "field", "create", "--base-id", base_id, "--table-id", table_id, "-y", "--fields", json.dumps(fields_spec, ensure_ascii=False)])
    assert dws_ok(d) and (d.get("data") or {}).get("failedCount", 1) == 0, f"create fields failed: {out}"


def _patch_field_options(base_id: str, table_id: str, field_id: str, options: list[dict]) -> None:
    d, out, err = call_dws(["aitable", "field", "update", "--base-id", base_id, "--table-id", table_id, "--field-id", field_id, "-y", "--config", json.dumps({"options": options}, ensure_ascii=False)])
    assert dws_ok(d), f"patch options {field_id} failed: {out}"


def main(plan: dict) -> Path:
    print("[step4] creating base + table + fields...")

    base_id = _create_base(plan["base_name"])
    print(f"  baseId={base_id}")

    table_id, _ = _get_default_table(base_id)
    _rename_table(base_id, table_id, "项目反馈跟踪")
    print(f"  tableId={table_id}")

    # 主字段（primaryDoc）rename "项目"
    primary_id = _list_fields(base_id, table_id)[0]["fieldId"]
    _rename_field(base_id, table_id, primary_id, "项目")

    # === 批量加字段（不带 options） ===
    daqu_options = [{"name": x} for x in cfg.DEFAULT_DAQU_OPTIONS]
    result_field_name = plan.get("result_field_name", "脚本扫描结果")
    extra = list(plan.get("extra_text_fields") or [])
    fb_status_options = list(plan.get("feedback_status_options") or [])

    fields_spec: list[dict] = [
        {"fieldName": "大区", "type": "singleSelect"},
        {"fieldName": "区域", "type": "text"},
        {"fieldName": "项目经理", "type": "user"},
        {"fieldName": result_field_name, "type": "singleSelect"},
        *[{"fieldName": n, "type": "text"} for n in extra],
        {"fieldName": "反馈状态", "type": "singleSelect"},
        {"fieldName": "反馈备注", "type": "text"},
        {"fieldName": "反馈时间", "type": "date", "property": {"dateFormat": "YYYY-MM-DD HH:mm", "includeTime": True}},
    ]
    if plan.get("include_engineering_leads", True):
        fields_spec += [
            {"fieldName": "大区工程总", "type": "user"},
            {"fieldName": "省份工程总", "type": "user"},
        ]
    _create_fields(base_id, table_id, fields_spec)
    time.sleep(0.5)

    # 拿全部 fieldId
    fields = _list_fields(base_id, table_id)
    name_to_id = {f["fieldName"]: f["fieldId"] for f in fields}

    # 补单选 options
    _patch_field_options(base_id, table_id, name_to_id["大区"], daqu_options)
    _patch_field_options(base_id, table_id, name_to_id[result_field_name], list(plan.get("result_options") or []))
    _patch_field_options(base_id, table_id, name_to_id["反馈状态"], [{"name": x} for x in fb_status_options])

    # base desc
    if plan.get("base_desc"):
        call_dws(["aitable", "base", "update", "--base-id", base_id, "--name", plan["base_name"], "-y", "--desc", plan["base_desc"]])

    # 拿 viewId
    d, out, err = call_dws(["aitable", "view", "get", "--base-id", base_id, "--table-id", table_id, "-y"])
    view_id = ((d.get("data") or {}).get("views") or [{}])[0].get("viewId") if dws_ok(d) else None

    meta = {
        "baseId": base_id,
        "tableId": table_id,
        "viewId": view_id,
        "fields": name_to_id,
        "result_field_name": result_field_name,
        "include_engineering_leads": plan.get("include_engineering_leads", True),
    }
    p = work_path(plan, "table_meta.json")
    p.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  fields: {list(name_to_id.keys())}")
    print(f"  -> {p}")
    print(f"  URL: https://docs.dingtalk.com/i/nodes/{base_id}")
    return p


if __name__ == "__main__":
    from scripts._common import load_plan
    main(load_plan(sys.argv[1]))
