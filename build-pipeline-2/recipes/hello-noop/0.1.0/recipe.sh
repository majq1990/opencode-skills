#!/usr/bin/env bash
# recipe.sh build|package — hello-noop
#
# 专供 inject_pubkey.py 验证新自定义镜像可用性使用：
#   - build 阶段：不下源码、不联网、不编译，只 mkdir + echo 一个 1 行 shell 脚本
#   - package 阶段：fpm 打成 build-pipeline-hello 包（rpm/deb 自动按 TARGET_IMAGE 选）
# 端到端目标 < 15s，零外部依赖。
set -e
PKG_VERSION="${VERSION:?}"
DISTRO="${DISTRO:?}"
TARGET_IMAGE="${TARGET_IMAGE:-unknown}"
unset VERSION

case "${1:?usage: recipe.sh build|package}" in
  build)
    echo "[hello-noop] staging dummy binary for $DISTRO ($TARGET_IMAGE)"
    mkdir -p /work/staging/usr/local/bin
    cat > /work/staging/usr/local/bin/build-pipeline-hello << EOF
#!/bin/sh
echo "hello from build-pipeline ${PKG_VERSION} on \$(uname -a)"
EOF
    chmod +x /work/staging/usr/local/bin/build-pipeline-hello
    ls -l /work/staging/usr/local/bin/
    ;;

  package)
    [ -d /work/staging/usr/local/bin ] || { echo "FATAL: staging missing"; exit 1; }

    OUT_TYPE=rpm
    case "$TARGET_IMAGE" in
      ubuntu:*|debian:*) OUT_TYPE=deb ;;
    esac

    case "$DISTRO" in
      *centos-stream10*) ITER="1.el10.stream" ;;
      *centos-stream9*)  ITER="1.el9.stream" ;;
      *centos-7*)        ITER="1.el7" ;;
      *ubuntu-*)         ITER="1.${DISTRO#*ubuntu-}"; ITER="${ITER//./}" ;;
      *)                 ITER="1.${DISTRO//-/}" ;;
    esac

    OUT_DIR=/repo/$DISTRO
    mkdir -p "$OUT_DIR"
    cd /work/staging

    fpm -s dir -t "$OUT_TYPE" -f \
      --name build-pipeline-hello \
      --version "$PKG_VERSION" \
      --iteration "$ITER" \
      --description "build-pipeline image validation noop ($DISTRO)" \
      --license "MIT" \
      --maintainer "build-pipeline@majq1990" \
      --architecture "$(uname -m)" \
      -C . \
      -p "$OUT_DIR/" \
      .

    echo "[hello-noop] produced:"
    ls -lh "$OUT_DIR/"
    ;;

  *) echo "usage: recipe.sh build|package"; exit 1 ;;
esac
