#!/usr/bin/env python3
"""pack — build packages for a software across multiple OS targets.

Spawns a spot ECS, runs the build pipeline, pulls artifacts, releases ECS.

Usage:
    pack <software> [version] [--os <fam[,fam...]>] [--osver <ver[,ver...]>]
                    [--keep] [--no-spot] [--region cn-wulanchabu]
                    [--image-id m-xxx] [--output ./output]
"""
from __future__ import annotations
import argparse
import os
import sys
import time

from controller import config, ecs, ssh
from controller.targets import resolve_targets
from controller.dingtalk import collect_build_records, format_records_for_dingtalk, DINGTALK_SPREADSHEET_NODE_ID, DINGTALK_SPREADSHEET_SHEET_ID


def _split_csv(s: str | None) -> list[str] | None:
    if not s:
        return None
    return [x.strip() for x in s.split(",") if x.strip()]


def main() -> int:
    p = argparse.ArgumentParser(description="On-demand multi-OS build pipeline")
    p.add_argument("software", help="e.g. openresty / nginx")
    p.add_argument("version", nargs="?", default=None, help="omit → latest stable")
    p.add_argument("--os", dest="os_filter", help="comma-list of families: centos,openeuler,...")
    p.add_argument("--osver", dest="osver_filter", help="comma-list of versions: 7,24.03-lts,...")
    p.add_argument("--keep", action="store_true", help="don't terminate ECS after build")
    p.add_argument("--no-spot", action="store_true", help="use PostPaid (not spot)")
    p.add_argument("--image-id", dest="image_id", default=None,
                   help="override custom image ID (default: config.IMAGE_ID)")
    p.add_argument("--output", default="./output", help="local artifact dir")
    args = p.parse_args()

    # 1. Resolve targets
    targets = resolve_targets(_split_csv(args.os_filter), _split_csv(args.osver_filter))
    print(f"[plan] software={args.software} version={args.version or 'latest'} → {len(targets)} targets")
    for t in targets:
        print(f"        - {t}")

    # 2. Resolve version (placeholder — each recipe should provide latest)
    version = args.version or _resolve_latest(args.software)
    print(f"[plan] version resolved to: {version}")

    # 3. Spawn ECS
    name = f"build-{args.software}-{int(time.time())}"
    instance_id, public_ip = ecs.run_spot_instance(
        name, image_id=args.image_id, spot=not args.no_spot,
    )
    print(f"[ecs] {instance_id} @ {public_ip}")

    try:
        # 4. Wait SSH
        ssh.wait_ssh(public_ip)

        # 5. Inject targets.list
        recipe_dir = f"{config.PIPELINE_RECIPES}/{args.software}/{version}"
        targets_blob = "\n".join(targets)
        ssh.run(public_ip, f"mkdir -p {recipe_dir}")
        ssh.run(public_ip, f'cat > {recipe_dir}/targets.list << "TGTEOF"\n{targets_blob}\nTGTEOF')

        # 6. Run build
        ssh.run(public_ip, f"{config.PIPELINE_BUILD_SH} {args.software} {version} -j {config.BUILD_PARALLEL}")

        # 7. Pull artifacts
        os.makedirs(args.output, exist_ok=True)
        ssh.scp_pull(public_ip, f"{config.PIPELINE_REPO}/.", args.output)
        print(f"[done] artifacts → {args.output}")

        # 8. Print download URL summary
        urls = _enumerate_download_urls(args.output)
        if urls:
            print("\n" + "=" * 60)
            print(f"  下载 URL 清单（共 {len(urls)} 个）")
            print("=" * 60)
            for u in urls:
                print(f"  {u}")

        recipe_dir_local = f"recipes/{args.software}/{version}"
        records = collect_build_records(args.software, version, args.output, recipe_dir_local)
        if records:
            _write_to_dingtalk_spreadsheet(records)

    finally:
        if not args.keep:
            ecs.terminate(instance_id)
        else:
            print(f"[keep] instance {instance_id} kept (ssh root@{public_ip})")

    return 0


_DISTRO_TAG_TO_OSVER = {
    "centos-6": ("centos", "6"),
    "centos-7": ("centos", "7"),
    "centos-stream9": ("centos", "stream9"),
    "centos-stream10": ("centos", "stream10"),
    "macrosan-uos-v20-1050": ("uos", "v20-1050"),
    "macrosan-uos-v20-1060": ("uos", "v20-1060"),
    "macrosan-uos-v20-1070": ("uos", "v20-1070"),
    "macrosan-kylin-v10-sp1": ("kylin", "v10-sp1"),
    "macrosan-kylin-v10-sp2": ("kylin", "v10-sp2"),
    "macrosan-kylin-v10-sp3": ("kylin", "v10-sp3"),
    "macrosan-kylin-v10-sp3-2403": ("kylin", "v10-sp3-2403"),
}


def _distro_tag_to_osver(tag: str) -> tuple[str, str] | None:
    """e.g. 'openeuler-openeuler-24.03-lts' → ('openeuler', '24.03-lts')."""
    if tag in _DISTRO_TAG_TO_OSVER:
        return _DISTRO_TAG_TO_OSVER[tag]
    if tag.startswith("openeuler-openeuler-"):
        return ("openeuler", tag[len("openeuler-openeuler-"):])
    if tag.startswith("openanolis-anolisos-"):
        return ("anolis", tag[len("openanolis-anolisos-"):])
    if tag.startswith("ubuntu-"):
        return ("ubuntu", tag[len("ubuntu-"):])
    return None


def _enumerate_download_urls(output_dir: str) -> list[str]:
    """Walk pulled artifact dir, build download URLs based on config."""
    import platform
    arch = platform.machine() or "x86_64"
    if arch == "AMD64":
        arch = "x86_64"
    urls = []
    for distro_tag in sorted(os.listdir(output_dir)):
        sub = os.path.join(output_dir, distro_tag)
        if not os.path.isdir(sub):
            continue
        m = _distro_tag_to_osver(distro_tag)
        if not m:
            continue
        os_id, ver = m
        for fn in sorted(os.listdir(sub)):
            urls.append(f"{config.DOWNLOAD_URL_BASE}/{os_id}/{ver}/{arch}/{fn}")
    return urls


def _write_to_dingtalk_spreadsheet(records: list[dict[str, str]]) -> None:
    """写入打包记录到钉钉表格."""
    try:
        import subprocess
        import json

        rows = format_records_for_dingtalk(records)
        if not rows:
            return

        get_range_cmd = [
            "dws", "spreadsheet", "get-range",
            "--node-id", DINGTALK_SPREADSHEET_NODE_ID,
            "--sheet-id", DINGTALK_SPREADSHEET_SHEET_ID,
            "--range", "A:A",
        ]
        result = subprocess.run(get_range_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[warn] 获取钉钉表格信息失败: {result.stderr}")
            return

        try:
            data = json.loads(result.stdout)
            values = data.get("values", [])
            last_row = 0
            for i, row in enumerate(values):
                if row and row[0]:
                    last_row = i + 1
            next_row = last_row + 1
        except (json.JSONDecodeError, KeyError):
            next_row = 2

        for i, row in enumerate(rows):
            row_num = next_row + i
            range_addr = f"A{row_num}:F{row_num}"
            update_cmd = [
                "dws", "spreadsheet", "update-range",
                "--node-id", DINGTALK_SPREADSHEET_NODE_ID,
                "--sheet-id", DINGTALK_SPREADSHEET_SHEET_ID,
                "--range", range_addr,
                "--values", json.dumps([row], ensure_ascii=False),
            ]
            result = subprocess.run(update_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[warn] 写入钉钉表格第 {row_num} 行失败: {result.stderr}")
            else:
                print(f"[dingtalk] 已写入第 {row_num} 行: {row[0]} {row[1]} {row[2]} {row[3]}")

        print(f"[dingtalk] 共写入 {len(rows)} 条记录到钉钉表格")

    except Exception as e:
        print(f"[warn] 写入钉钉表格失败: {e}")


def _resolve_latest(software: str) -> str:
    """Resolve latest version. Hooks point: each recipe could ship a `latest.sh`.

    For now, raise if version not given — implement per-recipe logic later.
    """
    # Simple approach: ssh into image-builder once or read from a shipped recipes/ index.
    # For openresty: HTTP scrape openresty.org/en/download.html
    if software == "openresty":
        import urllib.request, re
        try:
            html = urllib.request.urlopen(
                "https://openresty.org/en/download.html", timeout=15
            ).read().decode()
            m = re.search(r"openresty-([\d.]+)\.tar\.gz", html)
            if m:
                return m.group(1)
        except Exception as e:
            print(f"[warn] cannot fetch latest openresty: {e}", file=sys.stderr)
    raise SystemExit(
        f"version not given and no latest-resolver for '{software}'. "
        f"Pass version explicitly or implement controller/_resolve_latest()."
    )


if __name__ == "__main__":
    raise SystemExit(main())
