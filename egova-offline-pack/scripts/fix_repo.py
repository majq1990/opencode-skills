#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ibility-platform 依赖扫描下载工具（统一脚本）
================================================
功能：
  1. 递归扫描源码中 ALL pom.xml（排除 target/.git），收集全部依赖与 parent
  2. 解析各 pom 的 <properties> 变量，还原真实版本号
  3. 与 repo/ 本地仓库比对，识别缺失的 pom/jar
  4. 网络可达时自动从内网 Nexus 下载缺失依赖到 repo/
  5. 内网不可达时提示连接公司 VPN 并退出

兼容：Python 3.6 ~ 3.13，Windows / macOS / Linux，零第三方依赖
用法：python fix_repo.py [源码根目录]
"""

import os
import sys
import re
import socket
import time
import subprocess

try:
    import urllib.request as urlreq
    import urllib.parse as urlparse
    HAS_URLLIB = True
except Exception:   # pragma: no cover
    HAS_URLLIB = False

NEXUS = "http://npm.egova.com.cn:18081/repository/maven-public"
REPO_DIR = "repo"            # repo/ 相对源码根
BACKEND_POM = "backend/pom.xml"

# ANSI 颜色（非 TTY 自动关闭）
def _col(s, code):
    if sys.stdout.isatty():
        return "\033[%sm%s\033[0m" % (code, s)
    return s

def red(s):
    return _col(s, "31")

def green(s):
    return _col(s, "32")

def yellow(s):
    return _col(s, "33")

def cyan(s):
    return _col(s, "36")


def log(title):
    print("\n" + cyan("=" * 66))
    print(cyan("  " + title))
    print(cyan("=" * 66))


def find_root(start):
    """向上查找含 backend/pom.xml 的源码根目录"""
    p = os.path.abspath(start)
    if not os.path.isdir(p):
        p = os.path.dirname(p)
    while True:
        if os.path.isfile(os.path.join(p, BACKEND_POM)):
            return p
        nxt = os.path.dirname(p)
        if nxt == p:
            return None
        p = nxt


def iter_poms(root):
    """递归收集所有 pom.xml，排除 build/.git/target/node_modules"""
    excludes = (".git", "target", "node_modules", ".idea", "dist", "build")
    for dirpath, dirnames, filenames in os.walk(root):
        # 原地修剪排除目录
        for d in list(dirnames):
            if d in excludes:
                dirnames.remove(d)
        for fn in filenames:
            if fn == "pom.xml":
                yield os.path.join(dirpath, fn)


# 项目自身模块（reactor 内构建，不从 Nexus 下载）
LOCAL_MODULES = [
    "com.egova:egova-boot-ibility-base",
    "com.egova:egova-boot-ibility-liquibase",
    "com.egova:egova-boot-ibility-service",
    "com.egova:egova-boot-ibility-biz",
    "com.egova:egova-boot-ibility-plugin",
    "com.egova:egova-boot-colltable-api",
    "com.egova:egova-boot-check-api",
    "com.egova:egova-boot-evaluation-api",
    "com.egova:egova-boot-evaluation-rest",
    "com.egova:egova-boot-ibility-api",
    "com.egova:egova-boot-ibility-openapi",
    "com.egova:egova-boot-ibility-project",
    "com.egova:egova-boot-ibility-project-proj-yazhou",
    "com.egova:egova-ibility-core",
    "com.egova:egova-ibility-core-all-bom",
    "com.egova:egova-ibility-core-starter-all",
]

# 已知的 pom 打包类型 artifact（BOM/聚合，不需要 jar，但需 pom 或依赖管理）
POM_PACKAGING_HINTS = [
    "-bom", "-parent", "-dependencies", "-core-pom", "-starter-parent",
]


def is_bom_like(gid, aid):
    """BOM/父POM 类 artifact（无 jar）"""
    if aid.startswith("egova-boot") and gid == "com.egova":
        if aid not in (x.split(":")[1] for x in LOCAL_MODULES if "egova-boot" in x):
            pass
    for hint in POM_PACKAGING_HINTS:
        if hint in aid:
            return True
    # 常见 BOM
    if aid.endswith("-bom"):
        return True
    return False


def strip_ws(s):
    import xml.sax.saxutils as su
    xml_entities = {
        "apos": "'", "quot": "\"", "lt": "<", "gt": ">", "amp": "&"
    }
    text = s.strip()
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    # 简单 XML 实体解码（不用 xmltodict 保持零依赖）
    text = re.sub(r"&(apos|quot|lt|gt|amp);", lambda m: xml_entities[m.group(1)], text)
    return text


def parse_props(text):
    """解析 <properties> 里的变量"""
    props = {}
    m = re.search(r"<properties>(.*?)</properties>", text, re.S)
    if m:
        body = m.group(1)
        for pm in re.finditer(r"<([\w.\-]+)>(.*?)</\1>", body, re.S):
            key = pm.group(1)
            val = strip_ws(pm.group(2))
            if not val.startswith("$"):
                props[key] = val
    return props


def resolve(val, props):
    """解析 ${prop} 变量（支持嵌套，最多 5 层）"""
    if not isinstance(val, str):
        return val
    cur = val
    for _ in range(5):
        m = re.match(r"^\$\{(.+)\}$", cur.strip())
        if m and m.group(1) in props:
            cur = props[m.group(1)]
        else:
            break
    return cur.strip()


def collect_coords(pom_path, props):
    """从单个 pom 提取 parent + 全部直接依赖坐标"""
    coords = set()
    text = ""
    with open(pom_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    # parent
    pm = re.search(r"<parent>(.*?)</parent>", text, re.S)
    if pm:
        block = pm.group(1)
        g = re.search(r"<groupId>(.*?)</groupId>", block, re.S)
        a = re.search(r"<artifactId>(.*?)</artifactId>", block, re.S)
        v = re.search(r"<version>(.*?)</version>", block, re.S)
        if g and a:
            gid = resolve(strip_ws(g.group(1)), props)
            aid = resolve(strip_ws(a.group(1)), props)
            ver = resolve(strip_ws(v.group(1)) if v else "", props)
            if gid and aid and ver and not gid.startswith("$"):
                coords.add((gid, aid, ver))

    # dependencies
    dm = re.search(r"<dependencies>(.*?)</dependencies>", text, re.S)
    if dm:
        body = dm.group(1)
        for dep in re.finditer(r"<dependency>(.*?)</dependency>", body, re.S):
            block = dep.group(1)
            if "<scope>test</scope>" in block or "<scope>provided</scope>" in block:
                pass  # 仍收集（编译期可能需要）
            g = re.search(r"<groupId>(.*?)</groupId>", block, re.S)
            a = re.search(r"<artifactId>(.*?)</artifactId>", block, re.S)
            v = re.search(r"<version>(.*?)</version>", block, re.S)
            if not g or not a:
                continue
            gid = resolve(strip_ws(g.group(1)), props)
            aid = resolve(strip_ws(a.group(1)), props)
            ver = resolve(strip_ws(v.group(1)) if v else "", props)
            if gid.startswith("$") or aid.startswith("$") or not gid or not aid:
                continue
            coords.add((gid, aid, ver))
    return coords


def scan(root):
    """扫描全部 pom，收集解析后的坐标"""
    all_coords = set()
    pom_files = list(iter_poms(root))
    print("  扫描到 %d 个 pom.xml" % len(pom_files))
    for pom_path in pom_files:
        text = open(pom_path, encoding="utf-8", errors="ignore").read()
        props = parse_props(text)
        coords = collect_coords(pom_path, props)
        all_coords.update(coords)
    return all_coords


def repo_path(root, gid, aid, ver):
    return os.path.join(root, REPO_DIR, gid.replace(".", "/"), aid, ver)


def _read_packaging(pom_path):
    """读取本地已存在 pom 的 packaging，默认 jar"""
    try:
        with open(pom_path, "r", encoding="utf-8", errors="ignore") as f:
            t = f.read()
        m = re.search(r"<packaging>(.*?)</packaging>", t, re.S)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return "jar"


def check_local(root, gid, aid, ver):
    """返回 (缺pom, 缺jar)；BOM/本地模块返回 (None, None) 表示跳过"""
    # 本地 reactor 模块：不下载
    if "%s:%s" % (gid, aid) in LOCAL_MODULES:
        return None, None
    # ${project.version} 未解析或任何 ${...} 未解析：版本由父 POM 继承，跳过
    if ver == "" or ("${" in ver):
        return None, None
    d = repo_path(root, gid, aid, ver)
    pom_file = os.path.join(d, "%s-%s.pom" % (aid, ver))
    has_pom = os.path.isfile(pom_file)
    if not has_pom:
        # 缺 pom：先下载 pom 再看 packaging 决定是否需 jar
        return True, True
    # pom 已存在：按实际 packaging 判断
    packaging = _read_packaging(pom_file)
    if packaging == "pom":
        return False, False
    has_jar = os.path.isfile(os.path.join(d, "%s-%s.jar" % (aid, ver)))
    return False, (not has_jar)


def check_nexus():
    try:
        s = socket.create_connection(("npm.egova.com.cn", 18081), timeout=5)
        s.close()
        return True
    except Exception:
        return False


def dl(url, dest):
    """下载单个文件，返回 True/False"""
    try:
        req = urlreq.Request(url, headers={"User-Agent": "ibility-fix/1.0"})
        with urlreq.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
            while True:
                chunk = r.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)
        return True
    except Exception:
        if os.path.exists(dest):
            os.remove(dest)
        return False


def direct_download(root, missing):
    """缺失依赖逐个从 Nexus 下载。先拉 pom，再按 packaging 决定是否拉 jar。"""
    os.makedirs(os.path.join(root, REPO_DIR), exist_ok=True)
    ok_cnt, fail_cnt = 0, 0
    for gid, aid, ver, need_pom, need_jar in sorted(missing):
        d = repo_path(root, gid, aid, ver)
        os.makedirs(d, exist_ok=True)
        base = os.path.join(d, "%s-%s" % (aid, ver))
        pom_url = "%s/%s" % (NEXUS, urlpath(gid, aid, ver, "pom"))
        jar_url = "%s/%s" % (NEXUS, urlpath(gid, aid, ver, "jar"))

        # 1) 确保 pom
        if need_pom or not os.path.isfile(base + ".pom"):
            if not dl(pom_url, base + ".pom"):
                fail_cnt += 1
                continue

        # 2) 判断 packaging：pom 类型跳过 jar
        packaging = _read_packaging(base + ".pom")
        if packaging == "pom":
            ok_cnt += 1
            continue

        # 3) 需要 jar 时下载
        if not os.path.isfile(base + ".jar"):
            if dl(jar_url, base + ".jar"):
                ok_cnt += 1
            else:
                fail_cnt += 1
        else:
            ok_cnt += 1
    return ok_cnt, fail_cnt


def urlpath(gid, aid, ver, ext):
    return "%s/%s/%s/%s-%s.%s" % (gid.replace(".", "/"), aid, ver, aid, ver, ext)


def go_offline(root):
    """用 mvn dependency:go-offline 一次性解析传递依赖"""
    repo_abs = os.path.abspath(os.path.join(root, REPO_DIR))
    cmd = ["mvn",
           "-f", os.path.join(root, BACKEND_POM),
           "dependency:go-offline",
           "-Dmaven.repo.local=%s" % repo_abs,
           "-Dmaven.source.skip=true",
           "-DskipTests"]
    print(cyan("  执行: %s" % " ".join(cmd)))
    try:
        r = subprocess.call(cmd, cwd=root)
        return r == 0
    except Exception as e:
        print("  执行 mvn 失败: %s" % e)
        return False


def count_jars(root):
    n = 0
    rdir = os.path.join(root, REPO_DIR)
    if os.path.isdir(rdir):
        for dp, _, fns in os.walk(rdir):
            for fn in fns:
                if fn.endswith(".jar"):
                    n += 1
    return n


def fix_gitignore(root):
    """删除 .gitignore 中的 **/*.jar，避免 repo/ 的 jar 被 git 忽略"""
    gi = os.path.join(root, ".gitignore")
    if not os.path.isfile(gi):
        print(yellow("  未发现 .gitignore，跳过"))
        return
    with open(gi, "r", encoding="utf-8", errors="ignore") as f:
        orig = f.read()
    # 匹配整行：**/*.jar 或 *.jar
    new = re.sub(r"(?m)^\s*\*\*?/\*\.jar\s*$\n?", "", orig)
    if new != orig:
        with open(gi, "w", encoding="utf-8") as f:
            f.write(new)
        print(green("  [OK] 已从 .gitignore 移除 **/*.jar（否则 repo/ 依赖无法提交）"))
    else:
        print("  [SKIP] .gitignore 已无 *.jar 过滤")


def remove_remote_markers(root):
    """
    清理 repo/ 下所有 _remote.repositories 元数据。
    作用：repo 作为 -Dmaven.repo.local 离线使用时，若不清理，
    Maven 会因"来源仓库 id 不匹配"把已存在的 jar/pom 判为
    "present, but unavailable"，离线构建报错。
    清理后 repo/ 完全按本地仓库使用，离线编译稳定。
    """
    repo_dir = os.path.join(root, REPO_DIR)
    if not os.path.isdir(repo_dir):
        print(yellow("  未发现 repo/，跳过 _remote.repositories 清理"))
        return
    cnt = 0
    for dp, _, fns in os.walk(repo_dir):
        for fn in fns:
            if fn == "_remote.repositories" or fn.endswith(".lastUpdated"):
                try:
                    os.remove(os.path.join(dp, fn))
                    cnt += 1
                except Exception:
                    pass
    if cnt:
        print(green("  [OK] 清理 %d 个 _remote.repositories/.lastUpdated（离线构建必备）" % cnt))
    else:
        print("  [SKIP] 无 _remote.repositories 需清理")


def main():
    print(green("=============================================="))
    print(green("   ibility-platform 依赖扫描下载工具 (统一版)"))
    print(green("   兼容 Python 3.6 ~ 3.13"))
    print(green("=============================================="))

    start = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    root = find_root(start)
    if not root:
        print(red("[FAIL] 未找到源码根目录（缺少 backend/pom.xml）"))
        print(yellow("  用法: python fix_repo.py <源码根目录>"))
        return 1
    print(cyan("[1/5] 源码根目录: %s" % root))

    # 环境
    if shutil_which("java") is None:
        print(red("[FAIL] 未找到 java/javac，请先安装 JDK 1.8"))
        return 1

    # 修 .gitignore
    log("[2/5] 检查 .gitignore (*.jar 过滤)")
    fix_gitignore(root)

    # 清理 _remote.repositories（离线构建前置）
    log("[3/5] 清理 repo/ 离线构建元数据")
    remove_remote_markers(root)

    # 扫描全部依赖
    log("[4/5] 递归扫描全部 pom.xml 依赖")
    coords = scan(root)
    print("  共提取 %d 个依赖坐标（含 parent）" % len(coords))

    # 比对 repo/
    log("[5/5] 与 repo/ 本地仓库比对")
    missing = []
    for gid, aid, ver in sorted(coords):
        np, nj = check_local(root, gid, aid, ver)
        if np is None:
            continue
        if np or nj:
            missing.append((gid, aid, ver, np, nj))

    if not missing:
        print(green("  repo/ 依赖齐全，无需下载！"))
    else:
        print(yellow("  发现 %d 个缺失依赖：" % len(missing)))
        nshown = 0
        for gid, aid, ver, np, nj in missing:
            flag = []
            if np:
                flag.append("缺pom")
            if nj:
                flag.append("缺jar")
            print("    - %s:%s:%s  [%s]" % (gid, aid, ver, ",".join(flag)))
            nshown += 1
            if nshown >= 30:
                print("      ... 等 %d 项" % (len(missing) - 30))
                break

    # 网络检测 + VPN
    log("[5/5] 检查内网 Nexus 连通性")
    if not check_nexus():
        print(red("  [!!] 无法连接内网 Nexus: %s" % NEXUS))
        print(yellow(""))
        print(yellow("  *** 请先连接公司 VPN，再重新运行本工具! ***"))
        print(yellow("  常见 VPN: EasyConnect / ZTNA / 堡垒机客户端 ..."))
        print(yellow("  连接成功后重新执行即可。"))
        return 1
    print(green("  内网可达: %s" % NEXUS))

    before = count_jars(root)

    # 下载策略：逐个下载缺失 + go-offline 兜底传递依赖
    print("")
    if missing:
        print("  开始逐一下载 %d 个缺失依赖 ..." % len(missing))
        okc, failc = direct_download(root, missing)
        print("  直连下载完成: 成功 %d / 失败 %d" % (okc, failc))
    else:
        print("  无缺失依赖，跳过逐一下载。")

    # go-offline 补充传递依赖
    print("")
    print("  执行 mvn dependency:go-offline 补充传递依赖（需要 mvn，可跳过失败）...")
    if shutil_which("mvn"):
        go_offline(root)
    else:
        print(yellow("  未找到 mvn，跳过传递依赖补齐（缺失 item 已逐个下载）。"))

    after = count_jars(root)
    print("")
    print(green("[SUCCESS] 完成！repo/ 中 jar 数量: %d -> %d" % (before, after)))

    print("")
    print(cyan("  下一步构建命令（Windows）:"))
    print(yellow("    mvn -f backend\\pom.xml clean install -U -Dmaven.test.skip=true -Dmaven.repo.local=repo -Dmaven.source.skip=true -pl modules\\egova-boot-ibility-service -am"))
    print(cyan("  产物:"))
    print(yellow("    backend\\modules\\egova-boot-ibility-service\\target\\egova-boot-ibility-service-1.0.0.jar"))
    return 0


def shutil_which(cmd):
    """兼容 3.6：检查命令是否在 PATH"""
    if sys.version_info >= (3, 3):
        import shutil
        return shutil.which(cmd)
    path = os.environ.get("PATH", "")
    for p in path.split(os.pathsep):
        full = os.path.join(p, cmd)
        if os.name == "nt":
            for ext in (".exe", ".cmd", ".bat", ""):
                if os.path.isfile(full + ext):
                    return full + ext
        elif os.path.isfile(full):
            return full
    return None


if __name__ == "__main__":
    sys.exit(main())