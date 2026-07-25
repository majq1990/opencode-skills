#!/usr/bin/env python3
"""把 build_doc_md.py + build_aitable_rows.py 的产物写入钉钉。

跨平台（Windows / Linux）。dws 通过 subprocess 调用，自动探测 dws/dws.cmd。

步骤：
  1. normalize CRLF -> LF
  2. 扫描占位符残留
  3. DocNodeId 已存在 -> dws doc read 备份 -> dws doc update --mode overwrite
     DocNodeId 未给   -> dws doc create（需要 --doc-name；可选 --workspace / --folder）
  4. dws aitable record create 批量插入
  5. --dry-run: 只打印将执行的命令

Python 3.6+ compatible.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import archive_dir  # noqa: E402

# Windows 终端默认 GBK，会把 utf-8 中文打成 mojibake；强制 utf-8 输出
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

CST = timezone(timedelta(hours=8))
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")
SENTINEL_AUTO_INC = "__AUTO_INCREMENT__"
SENTINEL_DOC_URL = "__DOC_URL__"
ALIDOCS_URL_TPL = "https://alidocs.dingtalk.com/i/nodes/{node_id}"

# CVE-2026-31431 文档所在的团队空间 + 文件夹，所有处置文档默认放这里
DEFAULT_TEMPLATE_NODE_ID = "r1R7q3QmWe7MZNaLiZmKErdLJxkXOEP2"
DEFAULT_WORKSPACE_ID = "9JOGOMQYOo0ARX4Q"
DEFAULT_FOLDER_ID = "Gl6Pm2Db8D3moL97iZBDm5vyJxLq0Ee4"


def step(msg: str) -> None:
    print(f"[publish] {msg}", file=sys.stderr)


def dry(msg: str) -> None:
    print(f"[dry-run] {msg}", file=sys.stderr)


def fail(msg: str) -> None:
    print(f"[publish][FATAL] {msg}", file=sys.stderr)
    sys.exit(1)


def find_dws() -> str:
    for cand in ("dws", "dws.cmd"):
        p = shutil.which(cand)
        if p:
            return p
    fail("dws CLI not found in PATH")
    return ""  # unreachable


def run_dws(args: List[str], *, dry_run: bool, label: str) -> str:
    cmd = [find_dws()] + list(args)
    if dry_run:
        # 隐藏 markdown body（太长且含特殊字符），改用长度提示
        printable = []
        skip_next = False
        for tok in cmd:
            if skip_next:
                printable.append(f"<{len(tok)} chars>")
                skip_next = False
                continue
            printable.append(tok)
            if tok in ("--markdown", "--records"):
                skip_next = True
        dry(f"{label}: {' '.join(printable)}")
        return ""
    step(f"running: {label}")
    # Py3.6: capture_output / text are 3.7+, use stdout/stderr=PIPE + universal_newlines
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        fail(f"{label} failed (rc={proc.returncode}): {proc.stderr or proc.stdout}")
    return proc.stdout


def normalize_md(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    md = raw.replace("\r\n", "\n").replace("\r", "\n")
    leftover = sorted(set(PLACEHOLDER_RE.findall(md)))
    if leftover:
        fail(f"markdown 仍含占位符 {leftover} —— 请回 build_doc_md.py 修补再重发")
    if not md.endswith("\n"):
        md += "\n"
    if md != raw:
        # 写回 LF 版（utf-8 无 BOM）
        with open(path, "w", encoding="utf-8", newline="\n") as fp:
            fp.write(md)
    return md


def copy_from_template(template_node_id: str, workspace_id: str, folder_id: str,
                       new_name: str, dry_run: bool) -> str:
    """dws doc copy + dws doc rename。返回新节点 nodeId。

    用于把处置文档落到团队空间——dws doc create 没有团队空间写权限，
    但 dws doc copy 能把已有 adoc 节点复制到指定 workspace+folder。
    """
    step(f"copy template node={template_node_id} -> workspace={workspace_id} folder={folder_id}")
    out = run_dws(
        ["doc", "copy", "--node", template_node_id,
         "--workspace", workspace_id, "--folder", folder_id],
        dry_run=dry_run, label="dws doc copy",
    )
    if dry_run:
        dry(f"假设新 nodeId = <copied>")
        return "<copied>"
    try:
        obj = json.loads(out)
        new_id = obj.get("nodeId") or obj.get("data", {}).get("nodeId")
    except Exception:
        new_id = ""
    if not new_id:
        fail(f"无法从 doc copy 输出解析 nodeId: {out}")
    step(f"new nodeId = {new_id}")
    step(f"rename {new_id} -> {new_name}")
    run_dws(["doc", "rename", "--node", new_id, "--name", new_name],
            dry_run=dry_run, label="dws doc rename")
    return new_id


def parse_node_id_from_doc_create(stdout: str) -> str:
    """dws doc create 返回 JSON 包含 nodeId（具体路径 data.nodeId 或 data.node.nodeId）。
    解析失败返回空串，由 caller 决定是否致命。"""
    try:
        obj = json.loads(stdout)
    except Exception:
        return ""
    data = obj.get("data") or {}
    for path in ("nodeId", "id"):
        if data.get(path):
            return str(data[path])
    node = data.get("node") or {}
    if node.get("nodeId"):
        return str(node["nodeId"])
    return ""


def query_max_sequence(base_id: str, table_id: str, field_id: str, dry_run: bool) -> int:
    """查表里指定字段的当前最大值。失败返回 0（即新表从 1 开始）。

    dws --sort 的 order=DESC 实测无效（仍返回升序），改为客户端取 max。
    dws 对超过表实际行数的大 limit 会返回 0 条记录，所以 limit 不能太大；
    100 足以覆盖软件漏洞表的现实规模（2026-05-06 实测 59 条），超过 100 会被警告。
    """
    if dry_run:
        dry(f"query max({field_id}) on table {table_id}: 假设当前最大值=99，新值=100")
        return 99
    out = run_dws(
        ["aitable", "record", "query", "--base-id", base_id, "--table-id", table_id,
         "--limit", "100"],
        dry_run=False, label="dws aitable record query (max sequence)"
    )
    try:
        obj = json.loads(out)
        records = ((obj.get("data") or {}).get("records")) or []
        max_v = 0
        for r in records:
            cells = r.get("cells") or {}
            v = cells.get(field_id)
            try:
                iv = int(float(v)) if v not in (None, "") else 0
                if iv > max_v:
                    max_v = iv
            except (TypeError, ValueError):
                continue
        if (obj.get("data") or {}).get("nextCursor") and len(records) >= 100:
            print(f"[publish][warn] 表行数可能超过 100，max 序号可能不准；建议补分页", file=sys.stderr)
        return max_v
    except Exception as e:
        print(f"[publish][warn] parse max sequence failed: {e}", file=sys.stderr)
        return 0


def resolve_software_sentinels(records: list, meta: dict, doc_node_id: str, dry_run: bool) -> list:
    """software 模式下把 SENTINEL 替换成真实值；返回新 records。"""
    base_id = meta.get("baseId")
    table_id = meta.get("tableId")
    auto_field = meta.get("auto_increment_field")
    url_field = meta.get("doc_url_field")

    next_seq = None
    if auto_field:
        max_seq = query_max_sequence(base_id, table_id, auto_field, dry_run)
        next_seq = max_seq + 1

    doc_url = ALIDOCS_URL_TPL.format(node_id=doc_node_id) if doc_node_id else "(待定 nodeId)"

    out_records = []
    for rec in records:
        # 兼容历史 fields 字段名，但服务端要的是 cells
        cells = dict(rec.get("cells") or rec.get("fields") or {})
        for fid, val in list(cells.items()):
            if val == SENTINEL_AUTO_INC and fid == auto_field and next_seq is not None:
                cells[fid] = next_seq
                next_seq += 1
            elif val == SENTINEL_DOC_URL and fid == url_field:
                cells[fid] = doc_url
        out_records.append({"cells": cells})
    return out_records


def backup_doc(node_id: str, dry_run: bool) -> None:
    ts = datetime.now(CST).strftime("%Y%m%d%H%M%S")
    base = archive_dir() / f"{node_id}_before_{ts}"
    step(f"backup nodeId={node_id} -> {base}.json/.md")
    out = run_dws(["doc", "read", "--node", node_id], dry_run=dry_run, label="dws doc read")
    if dry_run:
        return
    with open(f"{base}.json", "w", encoding="utf-8", newline="\n") as fp:
        fp.write(out)
    try:
        parsed = json.loads(out)
        md = (parsed.get("data") or {}).get("markdown")
        if md:
            with open(f"{base}.md", "w", encoding="utf-8", newline="\n") as fp:
                fp.write(md)
    except json.JSONDecodeError as e:
        print(f"[publish][warn] could not parse backup json: {e}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc-md", required=True, help="path to <CVE>_doc_<ts>.md")
    ap.add_argument("--rows-json", required=True, help="path to <CVE>_rows_<ts>.json")
    ap.add_argument("--doc-node-id", default=None, help="existing nodeId (overwrite mode)")
    ap.add_argument("--doc-name", default=None, help="required when --doc-node-id absent")
    ap.add_argument("--workspace", default=None,
                    help=f"workspaceId (默认 {DEFAULT_WORKSPACE_ID}，CVE-2026-31431 同空间)")
    ap.add_argument("--folder", default=None,
                    help=f"folderId (默认 {DEFAULT_FOLDER_ID}，跟 CVE-2026-31431 同目录)")
    ap.add_argument("--copy-from-template", nargs="?", const=DEFAULT_TEMPLATE_NODE_ID, default=None,
                    metavar="TEMPLATE_NODE_ID",
                    help=f"用 dws doc copy 从模板节点复制（不传值则用默认 {DEFAULT_TEMPLATE_NODE_ID}），"
                         f"避开 doc create 的鉴权限制；之后 rename + update overwrite")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-doc", action="store_true")
    ap.add_argument("--skip-rows", action="store_true")
    args = ap.parse_args()

    doc_md = Path(args.doc_md)
    rows_json = Path(args.rows_json)
    if not doc_md.is_file():
        fail(f"--doc-md not found: {doc_md}")
    if not rows_json.is_file():
        fail(f"--rows-json not found: {rows_json}")

    step(f"normalize {doc_md} (CRLF -> LF, scan placeholders)")
    md = normalize_md(doc_md)

    # 加载 rows 元数据，需要在 doc step 之前知道 mode
    rows_obj = json.loads(rows_json.read_text(encoding="utf-8"))
    meta = rows_obj.get("_meta") or {}
    mode = meta.get("mode", "os")  # software | os
    base_id = meta.get("baseId")
    table_id = meta.get("tableId")
    records = rows_obj.get("records") or []
    if not args.skip_rows:
        if not base_id or not table_id:
            fail("rowsJson 缺少 _meta.baseId / _meta.tableId")
        if not records:
            fail("rowsJson.records 为空")

    new_node_id = ""
    workspace_id = args.workspace or DEFAULT_WORKSPACE_ID
    folder_id = args.folder or DEFAULT_FOLDER_ID

    # Step 2: doc
    if not args.skip_doc:
        if args.doc_node_id:
            # 路径 A: 已有 nodeId，直接 update overwrite
            backup_doc(args.doc_node_id, args.dry_run)
            run_dws(
                ["doc", "update", "--node", args.doc_node_id, "--mode", "overwrite", "--markdown", md],
                dry_run=args.dry_run,
                label="dws doc update --mode overwrite",
            )
            new_node_id = args.doc_node_id
        elif args.copy_from_template:
            # 路径 B（推荐）: 从模板复制 + rename + update overwrite
            if not args.doc_name:
                fail("--copy-from-template 模式下必须给 --doc-name 作为新节点的标题")
            new_node_id = copy_from_template(
                args.copy_from_template, workspace_id, folder_id,
                args.doc_name, args.dry_run,
            )
            if args.dry_run:
                # 复制阶段没有真 nodeId；后续 update 也跳过，让用户看完 dry-run 再真发
                dry(f"dws doc update --mode overwrite (会写入新复制的节点)")
            else:
                run_dws(
                    ["doc", "update", "--node", new_node_id, "--mode", "overwrite", "--markdown", md],
                    dry_run=False,
                    label="dws doc update --mode overwrite",
                )
        else:
            # 路径 C: 走 dws doc create（注意：当前 dws 鉴权写不到团队空间，仅 fallback）
            if not args.doc_name:
                fail("未给 --doc-node-id 也未给 --copy-from-template 时，必须给 --doc-name")
            print("[publish][warn] doc create 受 dws 鉴权限制可能写不到团队空间；"
                  "推荐改用 --copy-from-template", file=sys.stderr)
            create_args = ["doc", "create", "--name", args.doc_name, "--markdown", md]
            if args.workspace:
                create_args += ["--workspace", args.workspace]
            if args.folder:
                create_args += ["--folder", args.folder]
            create_out = run_dws(create_args, dry_run=args.dry_run, label="dws doc create")
            if not args.dry_run:
                new_node_id = parse_node_id_from_doc_create(create_out)
                if not new_node_id:
                    print(f"[publish][warn] 无法从 doc create 输出解析 nodeId；原始输出:\n{create_out}", file=sys.stderr)
                else:
                    step(f"new doc nodeId = {new_node_id}")
    else:
        step("skip-doc=true, 跳过文档写入")

    # Step 3: aitable rows
    if not args.skip_rows:
        # software 模式：替换 sentinel
        if mode == "software":
            step("software 模式：解析 SENTINEL（auto-increment 序号 + doc URL）")
            records = resolve_software_sentinels(records, meta, new_node_id, args.dry_run)

        # 兜底：服务端要 cells 不是 fields；旧 build 输出兼容
        records = [{"cells": (r.get("cells") or r.get("fields") or {})} for r in records]

        records_compact = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
        step(f"dws aitable record create  (mode={mode} base={base_id} table={table_id} rows={len(records)})")
        if args.dry_run:
            sample = json.dumps(records[0], ensure_ascii=False, indent=2)
            dry(f"dws aitable record create --base-id {base_id} --table-id {table_id} --records <{len(records)}条>")
            print("[dry-run] 第 1 行样例:", file=sys.stderr)
            print(sample, file=sys.stderr)
        else:
            run_dws(
                ["aitable", "record", "create", "--base-id", base_id, "--table-id", table_id, "--records", records_compact],
                dry_run=False,
                label="dws aitable record create",
            )
    else:
        step("skip-rows=true, 跳过 AI 表格写入")

    step("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
