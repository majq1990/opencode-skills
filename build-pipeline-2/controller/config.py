"""Centralized config — based on 8.145.49.174 template."""

# === ECS template (from i-0jl3fzm9oisq36ih9jq6) ===
REGION_ID = "cn-wulanchabu"
ZONE_ID = "cn-wulanchabu-c"
INSTANCE_TYPE = "ecs.e-c1m4.xlarge"  # 4 vCPU / 16 GB
IMAGE_ID = "m-0jl856ue5sjer9s2rpaw"  # build-host-v1 x86_64 (cn-wulanchabu)
IMAGE_ID_ARM64 = "m-0jl4qlwteu7cv53a014v"  # build-host-arm64-v3 (cn-wulanchabu) - 含信创 21 -pkg + wget→curl + dnf sqlite fix
INSTANCE_TYPE_ARM64 = "ecs.c8y.xlarge"  # 4C8G arm

# === Artifact upload (scp from build host) + download URL ===
UPLOAD_HOST = "182.92.5.151"
UPLOAD_PATH_BASE = "/egova/MediaRoot/rpm"  # final: /egova/MediaRoot/rpm/<os>/<ver>/<arch>/
DOWNLOAD_URL_BASE = "http://182.92.5.151:38081/MediaRoot/rpm"  # final: /MediaRoot/rpm/<os>/<ver>/<arch>/<file>
SYSTEM_DISK_CATEGORY = "cloud_essd"
SYSTEM_DISK_SIZE_GB = 50
INTERNET_MAX_BANDWIDTH_OUT = 100  # Mbps

VPC_ID = "vpc-0jl32yi9rx5ovum932wnz"
VSWITCH_ID = "vsw-0jlfj7todyuefm058cws1"
SECURITY_GROUP_ID = "sg-0jlargff0v62orby4dch"
KEY_PAIR_NAME = "mjqegova-ed25519"
SSH_KEY_PATH = "~/.ssh/mjqegova-ed25519"

# === Build pipeline paths on ECS ===
PIPELINE_ROOT = "/opt/build-pipeline"
PIPELINE_RECIPES = f"{PIPELINE_ROOT}/recipes"
PIPELINE_REPO = f"{PIPELINE_ROOT}/repo"
PIPELINE_BUILD_SH = f"{PIPELINE_ROOT}/scripts/build.sh"

# === OS family → -pkg image patterns ===
# 实际清单建议从 build-host-v1 镜像启动后 docker images 查询，这里仅初始模板
OS_FAMILY_TARGETS = {
    "centos":    ["centos:6-pkg", "centos:7-pkg", "centos:stream9-pkg", "centos:stream10-pkg"],
    "openeuler": ["openeuler/openeuler:22.03-lts-sp3-pkg", "openeuler/openeuler:22.03-lts-sp4-pkg",
                  "openeuler/openeuler:24.03-lts-pkg", "openeuler/openeuler:24.03-lts-sp1-pkg",
                  "openeuler/openeuler:24.03-lts-sp2-pkg", "openeuler/openeuler:24.03-lts-sp3-pkg",
                  "openeuler/openeuler:25.09-pkg"],
    "anolis":    ["openanolis/anolisos:7.9-pkg", "openanolis/anolisos:8.6-pkg",
                  "openanolis/anolisos:8.8-pkg", "openanolis/anolisos:23.1-pkg",
                  "openanolis/anolisos:23.2-pkg", "openanolis/anolisos:23.3-pkg",
                  "openanolis/anolisos:23.4-pkg"],
    "ubuntu":    ["ubuntu:18.04-pkg", "ubuntu:20.04-pkg", "ubuntu:22.04-pkg",
                  "ubuntu:24.04-pkg", "ubuntu:25.10-pkg", "ubuntu:26.04-pkg"],
    "kylin":     ["macrosan/kylin:v10-sp1-pkg", "macrosan/kylin:v10-sp2-pkg",
                  "macrosan/kylin:v10-sp3-pkg", "macrosan/kylin:v10-sp3-2403-pkg"],
    "uos":       ["macrosan/uos:v20-1050-pkg", "macrosan/uos:v20-1060-pkg",
                  "macrosan/uos:v20-1070-pkg"],
}

# === Behavior ===
SSH_READY_TIMEOUT_SEC = 180
BUILD_PARALLEL = 2  # CPU/2 on ecs.e-c1m4.xlarge
DEFAULT_KEEP_INSTANCE = False
DEFAULT_SPOT = True
