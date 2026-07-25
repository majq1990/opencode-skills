#!/usr/bin/env bash
# /opt/build-pipeline/scripts/build.sh
# Usage: build.sh <recipe-name> <version> [-j parallel] [--no-upload]
set -e

RECIPE="${1:?usage: build.sh <recipe> <version> [-j N] [--no-upload]}"
VERSION="${2:?usage: build.sh <recipe> <version> [-j N] [--no-upload]}"
PARALLEL=2
UPLOAD=1
shift 2
while [ "$#" -gt 0 ]; do
  case "$1" in
    -j) PARALLEL="${2:-2}"; shift 2 ;;
    --no-upload) UPLOAD=0; shift ;;
    *) shift ;;
  esac
done

# === Upload target ===
UPLOAD_HOST="182.92.5.151"
UPLOAD_BASE="/egova/MediaRoot/rpm"
DOWNLOAD_BASE="http://182.92.5.151:38081/MediaRoot/rpm"

# === DingTalk webhook (关键字 egova) ===
DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=abba9910309cc78b4dcfe5dea9c4ab90a601a0dfefb7c9087662a306c57be4ae"

push_dingtalk() {
  local content="$1"
  local body
  body=$(python3 -c "import json,sys;print(json.dumps({'msgtype':'text','text':{'content':sys.argv[1]}},ensure_ascii=False))" "$content" 2>/dev/null)
  [ -z "$body" ] && return 0
  curl -s -X POST "$DINGTALK_WEBHOOK" -H "Content-Type: application/json" -d "$body" >/dev/null 2>&1
}

PIPE=/opt/build-pipeline
RECIPE_DIR="$PIPE/recipes/$RECIPE/$VERSION"
[ -d "$RECIPE_DIR" ] || { echo "FATAL: $RECIPE_DIR not found"; exit 1; }
[ -f "$RECIPE_DIR/recipe.sh" ] || { echo "FATAL: missing recipe.sh"; exit 1; }
[ -f "$RECIPE_DIR/targets.list" ] || { echo "FATAL: missing targets.list"; exit 1; }

mapfile -t TARGETS < <(grep -vE "^#|^[[:space:]]*$" "$RECIPE_DIR/targets.list")
echo "==[ build pipeline ]== $RECIPE-$VERSION × ${#TARGETS[@]} targets, parallel=$PARALLEL upload=$UPLOAD"

URL_LIST_FILE=$(mktemp)

parse_target() {
  local t="$1"
  case "$t" in
    centos:6-pkg)        echo "centos 6" ;;
    centos:7-pkg)        echo "centos 7" ;;
    centos:stream9-pkg)  echo "centos stream9" ;;
    centos:stream10-pkg) echo "centos stream10" ;;
    openeuler/openeuler:*-pkg)
      v="${t#openeuler/openeuler:}"; v="${v%-pkg}"
      echo "openeuler $v" ;;
    openanolis/anolisos:*-pkg)
      v="${t#openanolis/anolisos:}"; v="${v%-pkg}"
      echo "anolis $v" ;;
    ubuntu:*-pkg)
      v="${t#ubuntu:}"; v="${v%-pkg}"
      echo "ubuntu $v" ;;
    macrosan/kylin:*-pkg)
      v="${t#macrosan/kylin:}"; v="${v%-pkg}"
      echo "kylin $v" ;;
    macrosan/uos:*-pkg)
      v="${t#macrosan/uos:}"; v="${v%-pkg}"
      echo "uos $v" ;;
    *) echo "unknown unknown" ;;
  esac
}

upload_to_repo() {
  local target="$1"; local distro_tag="$2"
  local out_dir="$PIPE/repo/$distro_tag"
  read os ver < <(parse_target "$target")
  local arch=$(uname -m)
  local remote_path="$UPLOAD_BASE/$os/$ver/$arch"

  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "root@$UPLOAD_HOST" \
      "mkdir -p $remote_path" 2>/dev/null
  scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
      "$out_dir"/* "root@$UPLOAD_HOST:$remote_path/" 2>&1 | tail -3
  echo "  uploaded → $UPLOAD_HOST:$remote_path/"

  for f in "$out_dir"/*; do
    fn=$(basename "$f")
    echo "$DOWNLOAD_BASE/$os/$ver/$arch/$fn" >> "$URL_LIST_FILE"
  done
}

build_one() {
  local target="$1"
  local distro_tag=$(echo "$target" | sed -E "s|[/:]|-|g; s|-pkg$||")
  local work="$PIPE/workspace/$RECIPE-$VERSION-$distro_tag"
  local log="$PIPE/logs/$RECIPE-$VERSION-$distro_tag.log"
  rm -rf "$work"; mkdir -p "$work/staging" "$work/output"
  : > "$log"

  echo "===== $target START $(date +%T) =====" >> "$log"
  local start=$(date +%s)

  if timeout 1800 docker run --rm \
       -v "$RECIPE_DIR:/recipe:ro" \
       -v "$work:/work" \
       -e VERSION="$VERSION" \
       -e DISTRO="$distro_tag" \
       -e TARGET_IMAGE="$target" \
       "$target" bash /recipe/recipe.sh build >> "$log" 2>&1 \
     && timeout 600 docker run --rm \
       -v "$RECIPE_DIR:/recipe:ro" \
       -v "$work:/work" \
       -v "$PIPE/repo:/repo" \
       -e VERSION="$VERSION" \
       -e DISTRO="$distro_tag" \
       -e TARGET_IMAGE="$target" \
       pkg-center:latest bash /recipe/recipe.sh package >> "$log" 2>&1; then
    local elapsed=$(( $(date +%s) - start ))
    echo "===== $target OK ($elapsed s) =====" | tee -a "$log"
    [ "$UPLOAD" = 1 ] && upload_to_repo "$target" "$distro_tag" 2>&1 | tee -a "$log"
    return 0
  else
    local elapsed=$(( $(date +%s) - start ))
    echo "===== $target FAIL ($elapsed s) =====" | tee -a "$log"
    return 1
  fi
}

OK=0; FAIL=0; RUNNING=0
for target in "${TARGETS[@]}"; do
  if [ "$PARALLEL" -le 1 ]; then
    build_one "$target" && OK=$((OK+1)) || FAIL=$((FAIL+1))
  else
    build_one "$target" &
    RUNNING=$((RUNNING+1))
    if [ $RUNNING -ge "$PARALLEL" ]; then
      if wait -n; then OK=$((OK+1)); else FAIL=$((FAIL+1)); fi
      RUNNING=$((RUNNING-1))
    fi
  fi
done
[ "$PARALLEL" -gt 1 ] && while [ $RUNNING -gt 0 ]; do
  if wait -n; then OK=$((OK+1)); else FAIL=$((FAIL+1)); fi
  RUNNING=$((RUNNING-1))
done

echo ""
echo "==================================================="
echo "==[ DONE ]== $(date +%T)  OK=$OK  FAIL=$FAIL"
echo "==================================================="
echo "--- repo 产物 ---"
find "$PIPE/repo" -type f \( -name "*.rpm" -o -name "*.deb" \) -printf "  %p  %s bytes\n" 2>/dev/null

if [ "$UPLOAD" = 1 ] && [ -s "$URL_LIST_FILE" ]; then
  URL_COUNT=$(wc -l < "$URL_LIST_FILE")
  echo ""
  echo "--- 下载 URL 清单（共 $URL_COUNT 个）---"
  URL_BLOCK=$(sort -u "$URL_LIST_FILE")
  echo "$URL_BLOCK" | sed "s/^/  /"

  # 钉钉推送（关键字 egova）
  ARCH=$(uname -m)
  DD_MSG="[egova] build-pipeline DONE
sw=$RECIPE-$VERSION arch=$ARCH
OK=$OK FAIL=$FAIL targets=${#TARGETS[@]}
下载 URL ($URL_COUNT 个):
$URL_BLOCK"
  push_dingtalk "$DD_MSG" && echo "  (钉钉已推送)"
fi
rm -f "$URL_LIST_FILE"
