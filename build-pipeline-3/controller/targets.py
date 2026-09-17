"""targets.py — resolve OS family/version filters to docker -pkg image names."""

from __future__ import annotations
import re
from typing import Iterable
from .config import OS_FAMILY_TARGETS


def _normalize(s: str) -> str:
    return s.lower().strip()


def _osver_in_image(image: str, ver: str) -> bool:
    """Check if version string `ver` matches the version part of an image tag.

    Examples:
        ubuntu:22.04-pkg + "22.04" → True
        openeuler/openeuler:24.03-lts-pkg + "24.03-lts" → True
        openeuler/openeuler:24.03-lts-sp1-pkg + "24.03-lts" → False (strict)
        macrosan/kylin:v10-sp2-pkg + "v10-sp2" → True
    """
    # extract tag part: everything after last ':' minus trailing '-pkg'
    tag = image.rsplit(":", 1)[-1]
    tag = re.sub(r"-pkg$", "", tag)
    return tag == _normalize(ver)


def resolve_targets(
    os_filter: Iterable[str] | None = None,
    osver_filter: Iterable[str] | None = None,
) -> list[str]:
    """Decide which -pkg images to build against.

    - os_filter=None → all families
    - osver_filter=None → all versions in selected families
    """
    families = (
        [_normalize(f) for f in os_filter] if os_filter else list(OS_FAMILY_TARGETS.keys())
    )
    unknown = [f for f in families if f not in OS_FAMILY_TARGETS]
    if unknown:
        raise ValueError(f"Unknown OS family: {unknown}. Known: {list(OS_FAMILY_TARGETS.keys())}")

    candidates: list[str] = []
    for fam in families:
        candidates.extend(OS_FAMILY_TARGETS[fam])

    if osver_filter:
        wanted = [_normalize(v) for v in osver_filter]
        candidates = [img for img in candidates if any(_osver_in_image(img, v) for v in wanted)]
        if not candidates:
            raise ValueError(f"No images matched osver filter {wanted} within families {families}")

    return candidates


if __name__ == "__main__":
    # smoke
    print("all:", len(resolve_targets()))
    print("ubuntu:", resolve_targets(["ubuntu"]))
    print("centos:7:", resolve_targets(["centos"], ["7"]))
    print("kylin v10-sp2:", resolve_targets(["kylin"], ["v10-sp2"]))
