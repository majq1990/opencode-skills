# -*- coding: utf-8 -*-
"""v2.0 可选主动模式：CVE/CNVD 情报采集（跨目录引用 vuln-response，本 skill 零复制）。

用法：
  python scripts/collect_cve_intel.py --cve CVE-2026-XXXX [--cve CVE-... ]            # os 分支（厂商公告）
  python scripts/collect_cve_intel.py --software redis --cve CVE-2025-XXXX ...       # software 分支（NVD/GHSA/CNVD）

行为：
  1) 读 config/security_case/cve_intel.json 拿 vuln-response 脚本目录；
  2) 通过 VULN_RESPONSE_ARCHIVE_DIR 环境变量把 vuln-response 的抓取产物重定向到
     work/security_case/cache/cve_intel/，不改动 vuln-response 任何文件；
  3) subprocess 调用其 fetch_vendor_advisory.py / fetch_software_advisory.py，
     透传其 stdout（结构化 JSON）。

边界（不得越界）：
  - 抓取产物是"情报原始数据"，不是"已研判结论"。喂给 triage_cases.py 之前，
    需经人工/LLM 研判转换为 cve_items JSON（schema 见下），本脚本不做自动转换，
    防止把情报包装成研判结论。

cve_items JSON schema（triage_cases.py --cve 输入，与 security-case-handling 对齐）：
  {"meta": {"record_count_raw": N, "source": "..."},
   "items": [{"cve_id": "CVE-...", "title": "...", "cvss_score": 9.8,
              "has_public_exploit": true, "in_kev": false,
              "published": "2026-09-01", "source_url": "https://..."}]}
"""
import json
import os
import subprocess
import sys

from security_case_lib import emit, load_config, parse_repeated, stop, work_path


def main(argv):
    cves = parse_repeated(argv, "--cve")
    args = {"software": "", "mode": ""}
    opts = parse_repeated  # noqa: F841  (保持导入一致性)
    i = 0
    while i < len(argv):
        if argv[i] == "--software" and i + 1 < len(argv):
            args["software"] = argv[i + 1]
            i += 2
            continue
        i += 1
    if not cves:
        stop("缺少 --cve（至少一个 CVE 编号，可重复传多个）",
             hint="用法见本文件 docstring：os 分支只传 --cve；software 分支加 --software <标识>")

    cfg, err = load_config("cve_intel.json")
    if err:
        stop("配置文件缺失: config/security_case/cve_intel.json -> %s" % err)
    scripts_dir = cfg.get("vuln_response_scripts_dir") or ""
    if args["software"]:
        script_name = cfg.get("fetch_software_script") or "fetch_software_advisory.py"
        mode = "software"
    else:
        script_name = cfg.get("fetch_os_script") or "fetch_vendor_advisory.py"
        mode = "os"
    script_path = os.path.join(scripts_dir, script_name)
    if not scripts_dir or not os.path.exists(script_path):
        stop("vuln-response 抓取脚本不存在: %s（检查 config/security_case/cve_intel.json 的 "
             "vuln_response_scripts_dir）" % script_path)

    archive = work_path("cache", "cve_intel")
    os.makedirs(archive, exist_ok=True)
    env = dict(os.environ)
    env[cfg.get("archive_env") or "VULN_RESPONSE_ARCHIVE_DIR"] = archive

    cmd = [sys.executable, script_path] + list(cves)
    if mode == "software":
        cmd += ["--software", args["software"]]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env=env, timeout=180)
    except subprocess.TimeoutExpired:
        stop("vuln-response 抓取超时（180s）", script=script_path)
    if proc.returncode != 0:
        stop("vuln-response 抓取失败（exit %s）" % proc.returncode,
             script=script_path, stderr_tail=(proc.stderr or "")[-800:])

    # 透传 vuln-response 的结构化输出；其产物已重定向到本 skill 的 archive 目录
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except Exception:
        pass
    payload = {"ok": True, "step": "collect_cve_intel", "mode": mode,
               "cves": cves, "archive": archive.replace("\\", "/"),
               "note": "情报原始数据已落盘；转 cve_items 需人工/LLM 研判后另行产出，勿直接喂 triage"}
    if parsed is not None:
        payload["upstream"] = parsed
    else:
        payload["upstream_stdout_tail"] = (proc.stdout or "")[-800:]
    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
