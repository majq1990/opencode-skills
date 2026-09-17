#!/bin/bash
# ==============================================================
# egova 离线编译封装
# 用法: bash offline_build.sh <pom路径> <repo路径> [额外的-D参数]
#   例: bash offline_build.sh ./pom.xml ./repo
#   例: bash offline_build.sh ./backend/pom.xml ./repo "-pl modules/x -am"
# ==============================================================
set -e
POM="${1:?用法: offline_build.sh <pom路径> <repo路径> [额外参数]}"
REPO="${2:?缺少 repo 路径}"
EXTRA="${3:-}"

# 1. 找 JDK8（跨平台）
find_jdk8() {
  local candidates=(
    "/usr/lib/jvm/java-1.8.0-amazon-corretto"
    "/usr/lib/jvm/jdk1.8*"
    "/usr/lib/jvm/java-8*"
    "/opt/java/openjdk"
    "C:/Program Files/Java/jdk1.8*"
    "C:/Program Files/Java/jre1.8*"
    "$HOME/.sdkman/candidates/java/8*"
  )
  for c in "${candidates[@]}"; do
    for d in $c; do
      if [ -d "$d" ]; then echo "$d"; return 0; fi
    done
  done
  # 兜底：当前 java 若是 8
  if java -version 2>&1 | grep -qi 'version "1.8'; then
    command -v java >/dev/null && { echo "$(dirname "$(dirname "$(command -v java)")")"; return 0; }
  fi
  return 1
}

JDK_HOME=$(find_jdk8) && {
  export JAVA_HOME="$JDK_HOME"
  export PATH="$JAVA_HOME/bin:$PATH"
  echo "[OFFLINE-BUILD] JAVA_HOME=$JDK_HOME"
}

# 2. 清 _remote.repositories（离线必备）
if [ -d "$REPO" ]; then
  echo "[OFFLINE-BUILD] 清理 _remote.repositories ..."
  find "$REPO" -name "_remote.repositories" -delete 2>/dev/null || true
  find "$REPO" -name "*.lastUpdated" -delete 2>/dev/null || true
fi

# 3. 离线编译
ABS_POM="$(cd "$(dirname "$POM")" && pwd)/$(basename "$POM")"
ABS_REPO="$(cd "$REPO" && pwd)"
echo "[OFFLINE-BUILD] mvn -o -f $ABS_POM clean package -Dmaven.repo.local=$ABS_REPO ..."
mvn -o -f "$ABS_POM" clean package \
    "-Dmaven.repo.local=$ABS_REPO" \
    "-Dmaven.source.skip=true" \
    "-DskipTests" $EXTRA

echo "[OFFLINE-BUILD] DONE"