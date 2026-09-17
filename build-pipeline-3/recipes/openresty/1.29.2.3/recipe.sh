#!/usr/bin/env bash
# recipe.sh build|package
set -e

# ---- Snapshot env BEFORE sourcing /etc/os-release (which clobbers VERSION) ----
PKG_VERSION="${VERSION:?VERSION env required}"
DISTRO="${DISTRO:?DISTRO env required}"
TARGET_IMAGE="${TARGET_IMAGE:-unknown}"
unset VERSION

case "${1:?usage: recipe.sh build|package}" in
  build)
    if [ -f /var/lib/rpm/Packages ] || [ -f /var/lib/rpm/rpmdb.sqlite ]; then rpm --rebuilddb 2>/dev/null || true; fi
    . /etc/os-release 2>/dev/null
    OS_ID="${ID,,}"
    OS_VER="${VERSION_ID:-unknown}"
    echo "[recipe] os=$OS_ID ver=$OS_VER pkg-version=$PKG_VERSION"

    # ---- Recipe-specific build deps ----
    case "$OS_ID" in
      ubuntu|debian)
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -qq -o Acquire::AllowInsecureRepositories=true || true
        apt-get install -y --no-install-recommends libpcre3-dev perl
        ;;
      *)
        if [ -x /usr/bin/dnf ]; then
          dnf install -y --setopt=install_weak_deps=False pcre-devel perl perl-devel \
            || dnf install -y pcre2-devel perl
        else
          yum install -y pcre-devel perl
        fi
        ;;
    esac

    # ---- Source ----
    cd /work
    SRC="openresty-${PKG_VERSION}.tar.gz"
    [ -f "$SRC" ] || wget -q "https://openresty.org/download/${SRC}"
    tar xzf "$SRC"
    cd "openresty-${PKG_VERSION}"

    # ---- CentOS 6/7 OpenSSL old → embed 1.1.1w ----
    EXTRA=""
    if [ "$OS_ID" = "centos" ] && [ "${OS_VER%%.*}" -le 7 ] 2>/dev/null; then
      cd /work
      [ -d openssl-1.1.1w ] || { wget -q https://www.openssl.org/source/openssl-1.1.1w.tar.gz && tar xzf openssl-1.1.1w.tar.gz; }
      cd "openresty-${PKG_VERSION}"
      EXTRA="--with-openssl=/work/openssl-1.1.1w"
    fi

    JOBS=$(nproc 2>/dev/null || echo 2)
    [ "$JOBS" -gt 4 ] && JOBS=$((JOBS / 2))
    echo "[recipe] configure (jobs=$JOBS, extra=${EXTRA:-none})"
    ./configure --prefix=/usr/local/openresty $EXTRA -j$JOBS
    echo "[recipe] make"
    make -j$JOBS
    echo "[recipe] install to staging"
    DESTDIR=/work/staging make install
    ls /work/staging/usr/local/openresty/
    ;;

  package)
    [ -d /work/staging/usr/local/openresty ] || { echo "FATAL: staging missing"; exit 1; }

    OUT_TYPE=rpm
    DEPENDS_KEY=rpm
    case "$TARGET_IMAGE" in
      ubuntu:*|debian:*) OUT_TYPE=deb; DEPENDS_KEY=deb ;;
    esac

    case "$DISTRO" in
      *centos-7*)    ITER="1.el7" ;;
      *centos-6*)    ITER="1.el6" ;;
      *centos-stream9*)  ITER="1.el9.stream" ;;
      *centos-stream10*) ITER="1.el10.stream" ;;
      *openeuler-22.03-lts-sp3*) ITER="1.oe2203sp3" ;;
      *openeuler-22.03-lts-sp4*) ITER="1.oe2203sp4" ;;
      *openeuler-24.03-lts-sp1*) ITER="1.oe2403sp1" ;;
      *openeuler-24.03-lts-sp2*) ITER="1.oe2403sp2" ;;
      *openeuler-24.03-lts-sp3*) ITER="1.oe2403sp3" ;;
      *openeuler-24.03-lts*)     ITER="1.oe2403" ;;
      *openeuler-25.09*)         ITER="1.oe2509" ;;
      *anolisos-7*)  ITER="1.an7" ;;
      *anolisos-8*)  ITER="1.an8" ;;
      *anolisos-23*) ITER="1.an23" ;;
      *kylin-v10-sp1*) ITER="1.ky10sp1" ;;
      *kylin-v10-sp2*) ITER="1.ky10sp2" ;;
      *kylin-v10-sp3*) ITER="1.ky10sp3" ;;
      *uos-v20-1050*) ITER="1.uos1050" ;;
      *uos-v20-1060*) ITER="1.uos1060" ;;
      *uos-v20-1070*) ITER="1.uos1070" ;;
      *ubuntu-18.04*) ITER="1.ubuntu1804" ;;
      *ubuntu-20.04*) ITER="1.ubuntu2004" ;;
      *ubuntu-22.04*) ITER="1.ubuntu2204" ;;
      *ubuntu-24.04*) ITER="1.ubuntu2404" ;;
      *ubuntu-25.10*) ITER="1.ubuntu2510" ;;
      *ubuntu-26.04*) ITER="1.ubuntu2604" ;;
      *) ITER="1.${DISTRO//-/}" ;;
    esac

    if [ "$DEPENDS_KEY" = "rpm" ]; then
      DEPENDS=(--depends pcre --depends openssl-libs)
    else
      DEPENDS=(--depends libpcre3 --depends libssl3)
    fi

    OUT_DIR=/repo/$DISTRO
    mkdir -p "$OUT_DIR"

    cd /work/staging
    fpm -s dir -f -t "$OUT_TYPE" \
      --name openresty \
      --version "$PKG_VERSION" \
      --iteration "$ITER" \
      --description "OpenResty (Nginx+Lua) for $DISTRO" \
      --license "BSD-2-Clause" \
      --maintainer "build-pipeline@majq1990" \
      --url "https://openresty.org/" \
      --architecture "$(uname -m)" \
      "${DEPENDS[@]}" \
      -C . \
      -p "$OUT_DIR/" \
      usr/local/openresty
    
    echo "[recipe] produced:"
    ls -lh "$OUT_DIR/"
    ;;

  *) echo "usage: recipe.sh build|package"; exit 1 ;;
esac
