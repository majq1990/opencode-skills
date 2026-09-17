"""ssh.py — minimal SSH/SCP wrappers (uses system `ssh` and `scp`).

Why not paramiko: avoids extra deps; OpenSSH on Windows already shipped.
"""

from __future__ import annotations
import os
import shlex
import socket
import subprocess
import time
from . import config


def _ssh_base(host: str) -> list[str]:
    key = os.path.expanduser(config.SSH_KEY_PATH)
    return [
        "ssh", "-i", key,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=10",
        f"root@{host}",
    ]


def wait_ssh(host: str, port: int = 22, timeout: int | None = None) -> None:
    """Block until TCP/22 accepts + sshd ready."""
    timeout = timeout or config.SSH_READY_TIMEOUT_SEC
    deadline = time.time() + timeout
    last_err = ""
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=5):
                pass
            # Probe with a trivial command
            r = subprocess.run(
                _ssh_base(host) + ["echo ready"],
                capture_output=True, text=True, timeout=15,
            )
            if r.returncode == 0:
                print(f"[ssh] {host} ready")
                return
            last_err = r.stderr.strip()
        except Exception as e:
            last_err = str(e)
        time.sleep(3)
    raise TimeoutError(f"ssh to {host} not ready within {timeout}s: {last_err}")


def run(host: str, cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a remote shell command, stream output."""
    full = _ssh_base(host) + [cmd]
    print(f"[ssh] $ {cmd[:120]}")
    return subprocess.run(full, check=check)


def capture(host: str, cmd: str) -> str:
    """Run remote command and return stdout."""
    full = _ssh_base(host) + [cmd]
    r = subprocess.run(full, capture_output=True, text=True, check=True)
    return r.stdout


def scp_pull(host: str, remote: str, local: str) -> None:
    key = os.path.expanduser(config.SSH_KEY_PATH)
    os.makedirs(os.path.dirname(local) if os.path.splitext(local)[1] else local, exist_ok=True)
    cmd = [
        "scp", "-r", "-i", key,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        f"root@{host}:{remote}", local,
    ]
    print(f"[scp] pulling {remote} → {local}")
    subprocess.run(cmd, check=True)
