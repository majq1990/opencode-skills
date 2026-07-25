#!/usr/bin/env bash
# Universal -pkg bootstrap: 装 base build toolchain + 切国内 mirror + 建 builder 用户
set -e

ID=""; VER=""
if [ -f /etc/os-release ]; then
  . /etc/os-release
  ID="${ID,,}"; VER="${VERSION_ID:-unknown}"
elif [ -f /etc/redhat-release ]; then
  if grep -q "release 6" /etc/redhat-release 2>/dev/null; then ID=centos; VER=6
  elif grep -q "release 7" /etc/redhat-release 2>/dev/null; then ID=centos; VER=7; fi
fi
[ -z "$ID" ] && { echo "FATAL: cannot detect OS"; exit 1; }
echo "==[ bootstrap start ]== os=${ID} ver=${VER} arch=$(uname -m)"

PKG_MGR=""; FAMILY=""
case "$ID" in
  ubuntu|debian)        PKG_MGR=apt; FAMILY=deb ;;
  centos)
    if [ -x /usr/bin/dnf ]; then PKG_MGR=dnf; else PKG_MGR=yum; fi
    FAMILY=rpm ;;
  rhel|rocky|almalinux|openeuler) PKG_MGR=dnf; FAMILY=rpm ;;
  anolis|alinux)
    if [ "${VER%%.*}" = "7" ] || [ ! -x /usr/bin/dnf ]; then PKG_MGR=yum; else PKG_MGR=dnf; fi
    FAMILY=rpm ;;
  kylin|neokylin|uos)
    if [ -x /usr/bin/dnf ]; then PKG_MGR=dnf; else PKG_MGR=yum; fi
    FAMILY=rpm ;;
  *) echo "FATAL: unsupported OS id=$ID"; exit 1 ;;
esac
echo "  family=$FAMILY pkg_mgr=$PKG_MGR"

# 切国内 mirror（按 OS 简单处理）
case "$ID" in
  ubuntu)
    if [ "$VER" = "18.04" ]; then
      sed -i -e "s@archive.ubuntu.com@old-releases.ubuntu.com@g" -e "s@security.ubuntu.com@old-releases.ubuntu.com@g" /etc/apt/sources.list 2>/dev/null || true
    else
      for f in /etc/apt/sources.list /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources; do
        [ -f "$f" ] || continue
        sed -i -e "s@archive.ubuntu.com@mirrors.aliyun.com@g" -e "s@security.ubuntu.com@mirrors.aliyun.com@g" -e "s@ports.ubuntu.com@mirrors.aliyun.com/ubuntu-ports@g" -e "s@old-releases.ubuntu.com@mirrors.aliyun.com@g" "$f"
      done
    fi
    ;;
  centos)
    case "$VER" in
      6|7)
        rm -f /etc/yum.repos.d/CentOS-*.repo
        VV="6.10"; [ "$VER" = "7" ] && VV="7.9.2009"
        cat > /etc/yum.repos.d/CentOS-Base.repo << REPOEOF
[base]
name=CentOS-$VER
baseurl=https://mirrors.aliyun.com/centos-vault/$VV/os/\$basearch/
gpgcheck=0
enabled=1
[updates]
name=CentOS-$VER Updates
baseurl=https://mirrors.aliyun.com/centos-vault/$VV/updates/\$basearch/
gpgcheck=0
enabled=1
[extras]
name=CentOS-$VER Extras
baseurl=https://mirrors.aliyun.com/centos-vault/$VV/extras/\$basearch/
gpgcheck=0
enabled=1
REPOEOF
        ;;
      *)
        sed -i "s@mirror.stream.centos.org@mirrors.aliyun.com/centos-stream@g" /etc/yum.repos.d/*.repo 2>/dev/null || true
        ;;
    esac
    ;;
  openeuler)
    sed -i "s@repo.openeuler.org@mirrors.huaweicloud.com/openeuler@g" /etc/yum.repos.d/*.repo 2>/dev/null || true
    ;;
esac

# 装 base toolchain
case "$FAMILY" in
  deb)
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq -o Acquire::AllowInsecureRepositories=true 2>&1 | tail -3 || true
    apt-get install -y --no-install-recommends \
      build-essential devscripts debhelper dh-make fakeroot lintian dpkg-dev \
      quilt git wget curl ca-certificates pkg-config xz-utils \
      libssl-dev zlib1g-dev libsqlite3-dev libreadline-dev python3-dev 2>&1 | tail -8
    apt-get clean
    rm -rf /var/lib/apt/lists/*
    ;;
  rpm)
    $PKG_MGR makecache 2>&1 | tail -3 || true
    $PKG_MGR install -y --setopt=install_weak_deps=False \
      rpm-build rpmdevtools gcc gcc-c++ make autoconf automake libtool \
      git patch wget curl tar bzip2 xz which \
      openssl-devel zlib-devel readline-devel 2>&1 | tail -8 || echo "  (主清单部分失败,继续)"
    $PKG_MGR install -y sqlite-devel createrepo 2>&1 | tail -3 || true
    if [ "$PKG_MGR" = "dnf" ]; then
      $PKG_MGR install -y dnf-plugins-core python3-devel cmake 2>&1 | tail -3 || true
    else
      $PKG_MGR install -y yum-utils 2>&1 | tail -3 || true
    fi
    $PKG_MGR clean all 2>/dev/null
    rm -rf /var/cache/dnf /var/cache/yum
    ;;
esac

# builder 用户
for u in ubuntu anolis cloud-user ec2-user; do
  if id "$u" >/dev/null 2>&1; then userdel -r "$u" 2>/dev/null || true; fi
done
if ! id builder >/dev/null 2>&1; then
  useradd -m -u 1000 -s /bin/bash builder 2>/dev/null || useradd -m -s /bin/bash builder
fi
mkdir -p /home/builder/build && chown -R builder:builder /home/builder
if command -v rpmdev-setuptree >/dev/null 2>&1; then
  su - builder -c "rpmdev-setuptree" 2>/dev/null || true
fi

# anolis 8.x rpm db 修复
if [ "$ID" = "anolis" ]; then
  chmod -R u+w /var/lib/rpm 2>/dev/null || true
  rm -f /var/lib/rpm/.dbenv.lock /var/lib/rpm/__db* 2>/dev/null || true
  rpm --rebuilddb 2>/dev/null || true
fi

echo "==[ bootstrap done ]== ${ID} ${VER}"
