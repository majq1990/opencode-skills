"""ecs.py — ECS lifecycle (RunInstances / DescribeInstances / DeleteInstance).

Uses subprocess + aliyun-cli (already installed locally) instead of SDK to
avoid bringing in heavy deps. If you prefer aliyun-python-sdk just swap out
the _aliyun() helper.
"""

from __future__ import annotations
import json
import shlex
import subprocess
import time
from . import config


def _aliyun(*args: str, capture: bool = True) -> dict | None:
    """Run aliyun-cli, return parsed JSON (or None on capture=False)."""
    cmd = ["aliyun"] + list(args)
    proc = subprocess.run(cmd, capture_output=capture, text=True, check=True)
    if not capture:
        return None
    out = proc.stdout.strip()
    if not out:
        return {}
    return json.loads(out)


def run_spot_instance(
    instance_name: str,
    image_id: str | None = None,
    instance_type: str | None = None,
    spot: bool = True,
) -> tuple[str, str]:
    """Create one ECS instance, return (instance_id, public_ip).

    Blocks until the instance is Running and has a public IP.

    instance_type defaults to config.INSTANCE_TYPE (x86). For arm images pass
    config.INSTANCE_TYPE_ARM64 explicitly — InstanceType arch must match the
    image arch or RunInstances rejects it.
    """
    image = image_id or config.IMAGE_ID
    itype = instance_type or config.INSTANCE_TYPE
    args = [
        "ecs", "RunInstances",
        "--RegionId", config.REGION_ID,
        "--ZoneId", config.ZONE_ID,
        "--InstanceType", itype,
        "--ImageId", image,
        "--SystemDisk.Category", config.SYSTEM_DISK_CATEGORY,
        "--SystemDisk.Size", str(config.SYSTEM_DISK_SIZE_GB),
        "--InternetChargeType", "PayByTraffic",
        "--InternetMaxBandwidthOut", str(config.INTERNET_MAX_BANDWIDTH_OUT),
        "--VSwitchId", config.VSWITCH_ID,
        "--SecurityGroupId", config.SECURITY_GROUP_ID,
        "--KeyPairName", config.KEY_PAIR_NAME,
        "--InstanceName", instance_name,
        "--InstanceChargeType", "PostPaid",
        "--Amount", "1",
    ]
    if spot:
        args += ["--SpotStrategy", "SpotAsPriceGo"]

    res = _aliyun(*args)
    iid = res["InstanceIdSets"]["InstanceIdSet"][0]
    print(f"[ecs] created {iid}, waiting for Running + public IP...")
    return iid, _wait_running(iid)


def _wait_running(instance_id: str, timeout: int = 180) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        res = _aliyun(
            "ecs", "DescribeInstances",
            "--RegionId", config.REGION_ID,
            "--InstanceIds", json.dumps([instance_id]),
        )
        ins_list = res.get("Instances", {}).get("Instance", [])
        if ins_list:
            ins = ins_list[0]
            if ins.get("Status") == "Running":
                pub = ins.get("PublicIpAddress", {}).get("IpAddress", [])
                if pub:
                    return pub[0]
        time.sleep(5)
    raise TimeoutError(f"instance {instance_id} not Running within {timeout}s")


def terminate(instance_id: str) -> None:
    print(f"[ecs] terminating {instance_id}")
    _aliyun(
        "ecs", "DeleteInstance",
        "--InstanceId", instance_id,
        "--Force", "true",
    )


def create_image(instance_id: str, image_name: str, description: str = "") -> str:
    """Snapshot a stopped/running instance into a new custom image.

    Returns new ImageId. Blocks until image Status=Available.
    """
    print(f"[ecs] CreateImage from {instance_id} → {image_name}")
    res = _aliyun(
        "ecs", "CreateImage",
        "--RegionId", config.REGION_ID,
        "--InstanceId", instance_id,
        "--ImageName", image_name,
        "--Description", description or image_name,
    )
    new_id = res["ImageId"]
    print(f"[ecs] new image {new_id}, waiting Available...")
    wait_image_available(new_id)
    return new_id


def wait_image_available(image_id: str, timeout: int = 1800) -> None:
    """Poll DescribeImages until Status=Available (typical: 3-10 min)."""
    deadline = time.time() + timeout
    last_status = ""
    while time.time() < deadline:
        res = _aliyun(
            "ecs", "DescribeImages",
            "--RegionId", config.REGION_ID,
            "--ImageId", image_id,
        )
        imgs = res.get("Images", {}).get("Image", [])
        if imgs:
            st = imgs[0].get("Status", "")
            prog = imgs[0].get("Progress", "")
            if st != last_status:
                print(f"[ecs] image {image_id} status={st} progress={prog}")
                last_status = st
            if st == "Available":
                return
            if st in ("CreateFailed", "UnAvailable"):
                raise RuntimeError(f"image {image_id} status={st}, abort")
        time.sleep(15)
    raise TimeoutError(f"image {image_id} not Available within {timeout}s")


def delete_image(image_id: str) -> None:
    """Permanently delete a custom image. Caller must verify the replacement
    image works in production before calling this — see feedback memory
    'build-pipeline 镜像替换流程'.
    """
    print(f"[ecs] DeleteImage {image_id} (irreversible)")
    _aliyun(
        "ecs", "DeleteImage",
        "--RegionId", config.REGION_ID,
        "--ImageId", image_id,
        "--Force", "true",
    )
