#!/usr/bin/env bash
# recipe.sh build|package — redis
set -e
PKG_VERSION="${VERSION:?}"
DISTRO="${DISTRO:?}"
TARGET_IMAGE="${TARGET_IMAGE:-unknown}"
unset VERSION

case "${1:?usage: recipe.sh build|package}" in
  build)
    . /etc/os-release 2>/dev/null
    OS_ID="${ID,,}"
    OS_VER="${VERSION_ID:-unknown}"
    echo "[recipe redis] os=$OS_ID ver=$OS_VER pkg=$PKG_VERSION"

    case "$OS_ID" in
      ubuntu|debian)
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -qq -o Acquire::AllowInsecureRepositories=true || true
        apt-get install -y --no-install-recommends libssl-dev libsystemd-dev pkg-config
        ;;
      *)
        if [ -x /usr/bin/dnf ]; then
          dnf install -y --setopt=install_weak_deps=False openssl-devel systemd-devel pkgconf-pkg-config \
            || dnf install -y openssl-devel systemd-devel pkgconfig
        else
          yum install -y openssl-devel systemd-devel pkgconfig
        fi
        ;;
    esac

    cd /work
    SRC="redis-${PKG_VERSION}.tar.gz"
    [ -f "$SRC" ] || curl -fsSL --connect-timeout 30 -o "$SRC" "https://download.redis.io/releases/${SRC}"
    tar xzf "$SRC"
    cd "redis-${PKG_VERSION}"

    JOBS=$(nproc 2>/dev/null || echo 2)
    [ "$JOBS" -gt 4 ] && JOBS=$((JOBS / 2))
    echo "[recipe redis] make -j$JOBS BUILD_TLS=yes USE_SYSTEMD=yes"
    make -j$JOBS BUILD_TLS=yes USE_SYSTEMD=yes
    echo "[recipe redis] install to staging"
    make PREFIX=/work/staging/usr install
    # 打包 systemd unit / config
    mkdir -p /work/staging/etc/redis /work/staging/usr/lib/systemd/system /work/staging/var/lib/redis /work/staging/var/log/redis
    cp redis.conf /work/staging/etc/redis/redis.conf
    cat > /work/staging/usr/lib/systemd/system/redis.service << "SVC"
[Unit]
Description=Redis In-Memory Data Store
After=network.target

[Service]
Type=notify
ExecStart=/usr/bin/redis-server /etc/redis/redis.conf --supervised systemd
ExecStop=/usr/bin/redis-cli shutdown
Restart=on-failure
User=redis
Group=redis

[Install]
WantedBy=multi-user.target
SVC
    ls /work/staging/usr/bin/
    ;;

  package)
    [ -d /work/staging/usr/bin ] || { echo "FATAL: staging missing"; exit 1; }

    OUT_TYPE=rpm
    DEPENDS_KEY=rpm
    case "$TARGET_IMAGE" in
      ubuntu:*|debian:*) OUT_TYPE=deb; DEPENDS_KEY=deb ;;
    esac

    case "$DISTRO" in
      *centos-7*)    ITER="1.el7" ;;
      *centos-stream9*) ITER="1.el9.stream" ;;
      *centos-stream10*) ITER="1.el10.stream" ;;
      *openeuler-22.03-lts-sp3*) ITER="1.oe2203sp3" ;;
      *openeuler-22.03-lts-sp4*) ITER="1.oe2203sp4" ;;
      *openeuler-24.03-lts-sp1*) ITER="1.oe2403sp1" ;;
      *openeuler-24.03-lts-sp2*) ITER="1.oe2403sp2" ;;
      *openeuler-24.03-lts-sp3*) ITER="1.oe2403sp3" ;;
      *openeuler-24.03-lts*)     ITER="1.oe2403" ;;
      *openeuler-25.09*)         ITER="1.oe2509" ;;
      *anolisos-7*)  ITER="1.an7" ;;
      *anolisos-23*) ITER="1.an23" ;;
      *anolisos-8*)  ITER="1.an8" ;;
      *kylin-v10-sp1*) ITER="1.ky10sp1" ;;
      *kylin-v10-sp2*) ITER="1.ky10sp2" ;;
      *kylin-v10-sp3*) ITER="1.ky10sp3" ;;
      *uos-v20-1050*) ITER="1.uos1050" ;;
      *uos-v20-1060*) ITER="1.uos1060" ;;
      *uos-v20-1070*) ITER="1.uos1070" ;;
      *ubuntu-*) ITER="1.${DISTRO#*ubuntu-}"; ITER="${ITER//./}" ;;
      *) ITER="1.${DISTRO//-/}" ;;
    esac

    if [ "$DEPENDS_KEY" = "rpm" ]; then
      DEPENDS=(--depends openssl-libs --depends systemd-libs)
    else
      DEPENDS=(--depends libssl3 --depends libsystemd0)
    fi

    OUT_DIR=/repo/$DISTRO
    mkdir -p "$OUT_DIR"

    cd /work/staging
    fpm -s dir -t "$OUT_TYPE" -f \
      --name redis \
      --version "$PKG_VERSION" \
      --iteration "$ITER" \
      --description "Redis 8.x for $DISTRO" \
      --license "RSALv2-SSPLv1" \
      --maintainer "build-pipeline@majq1990" \
      --url "https://redis.io/" \
      --architecture "$(uname -m)" \
      "${DEPENDS[@]}" \
      --before-install <(echo "getent group redis >/dev/null || groupadd -r redis; getent passwd redis >/dev/null || useradd -r -g redis -s /sbin/nologin redis") \
      --after-install <(echo "systemctl daemon-reload >/dev/null 2>&1 || true") \
      -C . \
      -p "$OUT_DIR/" \
      .

    echo "[recipe redis] produced:"
    ls -lh "$OUT_DIR/"
    ;;

  *) echo "usage: recipe.sh build|package"; exit 1 ;;
esac
