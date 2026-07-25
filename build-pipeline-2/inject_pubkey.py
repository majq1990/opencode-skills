#!/usr/bin/env python3
"""inject_pubkey — append SSH public keys to build-host custom image(s).

Use case
--------
部门同事都要能 ssh 进 build host 调试（pack --keep 场景）。把同事的公钥
追加到 ECS 自定义镜像的 /root/.ssh/authorized_keys，然后用新镜像替换
controller/config.py 里的 IMAGE_ID / IMAGE_ID_ARM64。

Flow（每个架构独立走一遍）
-------------------------
1. 用现有 IMAGE_ID 起一台 spot ECS
2. ssh 进去 → append pubkeys（grep -F 去重）
3. ecs CreateImage → 新 ImageId（等到 Available）
4. 用新 ImageId 起第二台 spot ECS（验证用）
5. 验证：sshd OK + /opt/build-pipeline 在 + docker images 非空
   + 跑 build.sh hello-noop 0.1.0 -j 1 --no-upload（< 30s）
6. 验证通过 → in-place 改 controller/config.py（先备份 .bak.<ts>）
7. 终止两台实例
8. **不自动删旧镜像** → 提示用户验证一两次后单独跑 --delete-old

Safety（落实 feedback memory「build-pipeline 镜像替换流程」）
- 任一步失败立即 abort，旧 IMAGE_ID 保留不动
- DeleteImage 必须显式单独命令（--delete-old），物理隔离
- config.py 改之前先备份

Usage
-----
    # 默认 x86 + arm 两套都注入
    python inject_pubkey.py ~/.ssh/liaokun.pub ~/.ssh/yaofeng.pub

    # 只处理 x86
    python inject_pubkey.py ~/.ssh/foo.pub --arch x86_64

    # 只造新镜像不替换 config.py（dry-run）
    python inject_pubkey.py ~/.ssh/foo.pub --dry-run

    # 验证日常打包都正常后，单独删旧镜像
    python inject_pubkey.py --delete-old m-0jl856ue5sjer9s2rpaw

Notification
------------
镜像替换成功后通过 dws 调钉钉机器人推送：
  - 操作者身份从 `dws contact user get-self` 拿
  - 推送渠道用 `dws chat message send-by-webhook`，token 与 build.sh 一致
"""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from controller import config, ecs, ssh

SKILL_ROOT = Path(__file__).resolve().parent
CONFIG_PY = SKILL_ROOT / "controller" / "config.py"

# 跟 scripts/build.sh 保持一致的 access_token（部门 egova 群机器人，关键字 egova）
DINGTALK_TOKEN = "abba9910309cc78b4dcfe5dea9c4ab90a601a0dfefb7c9087662a306c57be4ae"

VALIDATION_INSTANCE_TYPE = {
    "x86_64":  "ecs.e-c1m4.xlarge",   # 沿用 config.INSTANCE_TYPE
    "aarch64": "ecs.c8y.xlarge",
}


# ────────────────────────── pubkey helpers ──────────────────────────

def load_pubkeys(paths: list[str]) -> list[tuple[str, str]]:
    """Read pubkey files, return [(filename, key_line), ...]. Strict: each
    file must contain exactly one valid ssh-* / ecdsa-* / ssh-ed25519 line.
    """
    out = []
    for p in paths:
        path = Path(os.path.expanduser(p))
        if not path.is_file():
            raise SystemExit(f"pubkey not found: {path}")
        lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.strip().startswith("#")]
        if len(lines) != 1:
            raise SystemExit(f"{path} should contain exactly one pubkey line, got {len(lines)}")
        ln = lines[0]
        if not re.match(r"^(ssh-rsa|ssh-ed25519|ssh-dss|ecdsa-sha2-\S+)\s+\S+", ln):
            raise SystemExit(f"{path} doesn't look like an SSH pubkey: {ln[:60]}")
        out.append((path.name, ln))
    return out


def inject_into_instance(host: str, pubkeys: list[tuple[str, str]]) -> int:
    """ssh into instance, append each pubkey to authorized_keys if not already
    present. Returns number of newly added keys (0 = all dedup'd)."""
    ssh.run(host, "mkdir -p /root/.ssh && chmod 700 /root/.ssh && touch /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys")
    added = 0
    for name, key in pubkeys:
        # grep -F -x: fixed-string, full-line match. Returns 0 if hit.
        check = subprocess.run(
            _ssh_cmd(host) + [f"grep -F -x {_shquote(key)} /root/.ssh/authorized_keys"],
            capture_output=True, text=True,
        )
        if check.returncode == 0:
            print(f"  [skip] {name} already present")
            continue
        ssh.run(host, f"echo {_shquote(key)} >> /root/.ssh/authorized_keys")
        print(f"  [add]  {name}")
        added += 1
    return added


def _ssh_cmd(host: str) -> list[str]:
    key = os.path.expanduser(config.SSH_KEY_PATH)
    return ["ssh", "-i", key, "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=10",
            f"root@{host}"]


def _shquote(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


# ────────────────────────── validation ──────────────────────────

def validate_image(host: str) -> None:
    """Run a fast smoke test on the new image instance. Raises on failure."""
    print(f"[validate] checks on {host}")
    # 1. build pipeline structure exists
    ssh.run(host, "test -x /opt/build-pipeline/scripts/build.sh")
    ssh.run(host, "test -d /opt/build-pipeline/recipes")

    # 2. docker images present (-pkg images installed)
    pkg_count = ssh.capture(host, "docker images --format '{{.Repository}}' | grep -c -- '-pkg' || true").strip()
    try:
        n = int(pkg_count)
    except ValueError:
        n = 0
    if n < 1:
        raise RuntimeError(f"no -pkg docker images on {host} (got {n})")
    print(f"  -pkg images: {n}")

    # 3. hello-noop recipe should be in the image (we shipped it via the
    #    bootstrap flow; if missing, push it before running)
    has_recipe = subprocess.run(
        _ssh_cmd(host) + ["test -d /opt/build-pipeline/recipes/hello-noop/0.1.0"],
        capture_output=True,
    ).returncode == 0
    if not has_recipe:
        print("  [push] hello-noop recipe not on image — uploading now")
        local_recipe = SKILL_ROOT / "recipes" / "hello-noop" / "0.1.0"
        # mkdir + scp 3 个小文件
        ssh.run(host, "mkdir -p /opt/build-pipeline/recipes/hello-noop/0.1.0")
        for fn in ("recipe.sh", "targets.list", "meta.yaml"):
            scp = ["scp", "-i", os.path.expanduser(config.SSH_KEY_PATH),
                   "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
                   str(local_recipe / fn),
                   f"root@{host}:/opt/build-pipeline/recipes/hello-noop/0.1.0/{fn}"]
            subprocess.run(scp, check=True)
        ssh.run(host, "chmod +x /opt/build-pipeline/recipes/hello-noop/0.1.0/recipe.sh")

    # 4. real smoke build (no upload, no dingtalk — build.sh skips both when --no-upload)
    print("  [smoke] running hello-noop build (target ubuntu:24.04-pkg, no upload)...")
    t0 = time.time()
    ssh.run(host, "/opt/build-pipeline/scripts/build.sh hello-noop 0.1.0 -j 1 --no-upload")
    elapsed = int(time.time() - t0)
    print(f"  [smoke] OK in {elapsed}s")


# ────────────────────────── config.py rewrite ──────────────────────────

def patch_config(arch: str, new_image_id: str) -> str:
    """Rewrite IMAGE_ID or IMAGE_ID_ARM64 in controller/config.py.
    Returns the OLD image id. Backs up to config.py.bak.<timestamp>.
    """
    var = "IMAGE_ID" if arch == "x86_64" else "IMAGE_ID_ARM64"
    src = CONFIG_PY.read_text(encoding="utf-8")

    pat = re.compile(rf'^({var}\s*=\s*")(m-[a-z0-9]+)(".*)$', re.MULTILINE)
    m = pat.search(src)
    if not m:
        raise RuntimeError(f"cannot locate {var} in {CONFIG_PY}")
    old = m.group(2)
    if old == new_image_id:
        print(f"[config] {var} already = {new_image_id}, no change")
        return old

    bak = CONFIG_PY.with_suffix(f".py.bak.{int(time.time())}")
    shutil.copy2(CONFIG_PY, bak)
    new_src = pat.sub(rf'\g<1>{new_image_id}\g<3>', src, count=1)
    CONFIG_PY.write_text(new_src, encoding="utf-8")
    print(f"[config] {var}: {old} → {new_image_id}  (backup: {bak.name})")
    return old


# ────────────────────────── dws integration ──────────────────────────

def dws_get_self() -> dict:
    """Call `dws contact user get-self --format json`. Return the parsed user
    object, or {} on failure (we don't want notification path to break the
    main flow)."""
    try:
        r = subprocess.run(
            ["dws", "contact", "user", "get-self", "--format", "json"],
            capture_output=True, text=True, timeout=20,
        )
        if r.returncode != 0:
            print(f"[dws] get-self failed rc={r.returncode}: {r.stderr.strip()[:200]}", file=sys.stderr)
            return {}
        data = json.loads(r.stdout)
        # dws 通常包一层 {"data": {...}} 或直接返回对象 — 兼容
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
            data = data["data"]
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        print("[dws] command not found — install dws CLI to enable identity-aware notification", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"[dws] get-self error: {e}", file=sys.stderr)
        return {}


def operator_label(self_info: dict) -> str:
    """Pick the most human-readable name from get-self response."""
    for k in ("name", "nickname", "displayName", "userName", "mobile", "userId"):
        v = self_info.get(k)
        if v:
            return str(v)
    return f"unknown({os.environ.get('USERNAME') or os.environ.get('USER') or 'na'})"


def push_dingtalk(title: str, text: str) -> None:
    """`dws chat message send-by-webhook` — soft-fail (don't break main flow)."""
    try:
        r = subprocess.run(
            ["dws", "chat", "message", "send-by-webhook",
             "--token", DINGTALK_TOKEN,
             "--title", title,
             "--text", text,
             "--format", "json"],
            capture_output=True, text=True, timeout=20,
        )
        if r.returncode == 0:
            print("[dingtalk] pushed")
        else:
            print(f"[dingtalk] push failed rc={r.returncode}: {r.stderr.strip()[:200]}", file=sys.stderr)
    except FileNotFoundError:
        print("[dingtalk] dws CLI missing — skip notification", file=sys.stderr)
    except Exception as e:
        print(f"[dingtalk] push error: {e}", file=sys.stderr)


# ────────────────────────── main flow per arch ──────────────────────────

def _arch_image_attrs(arch: str) -> tuple[str, str]:
    """Return (current_image_id, instance_type) for the given arch."""
    if arch == "x86_64":
        return config.IMAGE_ID, config.INSTANCE_TYPE
    if arch == "aarch64":
        return config.IMAGE_ID_ARM64, config.INSTANCE_TYPE_ARM64
    raise ValueError(f"unknown arch: {arch}")


def inject_for_arch(arch: str, pubkeys: list[tuple[str, str]], dry_run: bool) -> dict | None:
    """Returns a result dict on success, None on no-op (all keys already present)."""
    old_id, itype = _arch_image_attrs(arch)
    print(f"\n========== arch={arch} (current ImageId: {old_id}, InstanceType: {itype}) ==========")

    # Step 1: boot src instance
    name = f"injectpub-src-{arch}-{int(time.time())}"
    src_id, src_ip = ecs.run_spot_instance(name, image_id=old_id, instance_type=itype)
    src_terminated = False
    new_id = None
    val_id = None
    try:
        ssh.wait_ssh(src_ip)

        # Step 2: append pubkeys
        added = inject_into_instance(src_ip, pubkeys)
        if added == 0:
            print(f"[arch={arch}] all {len(pubkeys)} keys already present, no rebuild needed")
            return None

        # Step 3: snapshot → new image
        ts = datetime.now().strftime("%Y%m%d-%H%M")
        img_name = f"build-host-{arch}-pubkey-{ts}"
        new_id = ecs.create_image(src_id, img_name, description=f"+{added} pubkey(s) on {ts}")

        # src can go now — we have the snapshot
        ecs.terminate(src_id)
        src_terminated = True

        # Step 4: boot validation instance from new image
        val_name = f"injectpub-val-{arch}-{int(time.time())}"
        val_id, val_ip = ecs.run_spot_instance(val_name, image_id=new_id, instance_type=itype)
        ssh.wait_ssh(val_ip)

        # Step 5: smoke build
        validate_image(val_ip)

        # Step 6: rewrite config.py (unless dry-run)
        if dry_run:
            print(f"[arch={arch}] --dry-run: skipped patching config.py; new ImageId={new_id}")
        else:
            patch_config(arch, new_id)

        return {"arch": arch, "old": old_id, "new": new_id, "added": added}

    finally:
        if val_id:
            try: ecs.terminate(val_id)
            except Exception as e: print(f"[warn] terminate val {val_id}: {e}", file=sys.stderr)
        if not src_terminated:
            try: ecs.terminate(src_id)
            except Exception as e: print(f"[warn] terminate src {src_id}: {e}", file=sys.stderr)


# ────────────────────────── CLI ──────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(
        description="Append SSH pubkeys to build-host custom image",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("pubkeys", nargs="*", help="path(s) to .pub files")
    p.add_argument("--arch", choices=["x86_64", "aarch64", "all"], default="all",
                   help="target architecture (default: all)")
    p.add_argument("--dry-run", action="store_true",
                   help="build new image + validate, but don't patch config.py")
    p.add_argument("--delete-old", metavar="IMAGE_ID", default=None,
                   help="standalone command: permanently delete an old ImageId. "
                        "Use only after verifying replacement image works in production.")
    args = p.parse_args()

    # ── --delete-old branch ────────────────────────────────────────
    if args.delete_old:
        if args.pubkeys:
            print("--delete-old must be used alone (no pubkey args)", file=sys.stderr)
            return 2
        cur = {config.IMAGE_ID, config.IMAGE_ID_ARM64}
        if args.delete_old in cur:
            print(f"refuse: {args.delete_old} is currently the ACTIVE ImageId in config.py", file=sys.stderr)
            print("        edit config.py to point elsewhere first, or you'll brick the pipeline.", file=sys.stderr)
            return 2
        print(f"[delete-old] about to DeleteImage {args.delete_old} (irreversible)")
        confirm = input("type the ImageId again to confirm: ").strip()
        if confirm != args.delete_old:
            print("aborted")
            return 1
        ecs.delete_image(args.delete_old)
        print(f"[done] deleted {args.delete_old}")
        return 0

    # ── inject branch ──────────────────────────────────────────────
    if not args.pubkeys:
        p.error("provide at least one pubkey file (or use --delete-old)")

    pubkeys = load_pubkeys(args.pubkeys)
    print(f"[plan] {len(pubkeys)} pubkey(s):")
    for name, key in pubkeys:
        print(f"  - {name}: {key.split()[0]} ...{key.split()[1][-12:]}")

    arches = ["x86_64", "aarch64"] if args.arch == "all" else [args.arch]
    print(f"[plan] arch(es): {arches}, dry-run={args.dry_run}")

    results: list[dict] = []
    for arch in arches:
        r = inject_for_arch(arch, pubkeys, dry_run=args.dry_run)
        if r:
            results.append(r)

    if not results:
        print("\n[done] nothing to do (all pubkeys already present in all arches)")
        return 0

    # ── notify dingtalk ────────────────────────────────────────────
    self_info = dws_get_self()
    op = operator_label(self_info)
    pubkey_names = ", ".join(name for name, _ in pubkeys)
    lines = [
        f"[egova] build-pipeline 镜像公钥更新",
        f"操作者: {op}",
        f"新增公钥: {pubkey_names}",
        "",
    ]
    for r in results:
        action = "(dry-run, config.py 未改)" if args.dry_run else ""
        lines.append(f"  {r['arch']}: {r['old']} → {r['new']}  +{r['added']} 把 {action}".rstrip())
    if not args.dry_run:
        lines.append("")
        lines.append("旧 ImageId 已保留。验证日常打包正常后，单独跑：")
        for r in results:
            lines.append(f"  python inject_pubkey.py --delete-old {r['old']}")

    text = "\n".join(lines)
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)
    push_dingtalk("build-pipeline 镜像公钥更新", text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
