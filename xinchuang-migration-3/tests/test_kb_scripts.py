"""本地自测：用假 webroot 跑 switch_kb / preflight_kb 的纯逻辑部分。
不连任何数据库，只验证键名改写、前缀发现、脱敏、未知映射拒绝这几件事。
"""
import importlib.util
import json
import os
import re
import sys
import tempfile
from importlib.machinery import SourceFileLoader
from pathlib import Path

KIT = Path(__file__).parent
if not (KIT / "switch_kb.py.txt").exists():
    # skill 布局：本文件在 tests/ 下，脚本在 scripts/kingbase/ 下
    KIT = Path(__file__).resolve().parent.parent / "scripts" / "kingbase"
FAILS = []


def load(name, fname):
    loader = SourceFileLoader(name, str(KIT / fname))
    spec = importlib.util.spec_from_loader(name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def check(cond, msg):
    print(("  OK   " if cond else "  FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


# ---------------- switch_kb ----------------
print("== switch_kb ==")
sw = load("switch_kb", "switch_kb.py.txt")

sample = (
    "# comment\n"
    "jdbc.driverClassName=com.mysql.cj.jdbc.Driver\n"
    "jdbc.url=jdbc:mysql://172.21.133.155:3306/cgdb?useUnicode=true\n"
    "jdbc.username=CGDB\n"
    "jdbc.cryptogram=SECRETVALUE123\n"
    "jdbc.validationQuery=SELECT 1\n"
    "stat.jdbc.url=jdbc:mysql://172.21.133.155:3306/cgdbstat\n"
    "stat.jdbc.driverClassName=com.mysql.cj.jdbc.Driver\n"
    "stat.jdbc.username=CGDBSTAT\n"
    "stat.jdbc.password=ANOTHERSECRET99\n"
    "stat.jdbc.validation.query=SELECT 1\n"
)
props = sw.parse_props(sample)
check(props["jdbc.username"] == "CGDB", "parse_props 读得到用户名")
check(len(sw.parse_props("# c\nnope\n")) == 0, "注释行与无等号行被跳过")

t = sw.set_key(sample, "jdbc.url", "jdbc:kingbase8://127.0.0.1:54321/test?currentSchema=CGDB")
check("jdbc.url=jdbc:kingbase8://127.0.0.1:54321/test?currentSchema=CGDB" in t,
      "set_key 原地改值")
check(t.count("jdbc.url=") == 2, "set_key 不动 stat.jdbc.url")
t2 = sw.set_key(t, "brand.new.key", "v")
check(t2.rstrip().endswith("brand.new.key=v"), "键不存在时追加一行")

masked = sw.mask("jdbc.cryptogram=SECRETVALUE123\nstat.jdbc.password=ANOTHERSECRET99\njdbc.url=x")
check(all("SECRET" not in m and "ANOTHER" not in m for m in masked),
      "mask 不泄漏口令")
check(any("len=15" in m for m in masked), "mask 保留长度信息")

tmp = Path(tempfile.mkdtemp()) / "web"
app = tmp / "eUrbanMIS" / "WEB-INF" / "classes"
app.mkdir(parents=True)
(app / "jdbc.properties").write_text(sample, encoding="utf-8")
sw.WEB_ROOT = tmp
files = sw.find_props()
check(len(files) == 1 and sw.app_of(files[0]) == "eUrbanMIS", "find_props/app_of")

argv = ["--kb-host", "127.0.0.1", "--kb-port", "54321", "--kb-db", "test",
        "--kb-pw-file", str(tmp / "nopw")]
(tmp / "nopw").write_text("kingbasepw123\n", encoding="utf-8")
old = sys.argv

# 未知映射必须整体拒绝，不猜（样本里是空前缀 + stat 两个源，都没映射）
try:
    sys.argv = ["switch_kb.py"] + argv
    rc = sw.main()
    check(rc == 3, "无映射的数据源 -> rc=3 整体拒绝（不猜）")
finally:
    sys.argv = old

# 给全映射后 dry-run 不落盘
try:
    sys.argv = ["switch_kb.py", "--kb-pw-file", str(tmp / "nopw"),
                "--map", "eUrbanMIS:=CGDB,eUrbanMIS:stat=CGDBSTAT"]
    rc = sw.main()
    check(rc == 0, "映射给全后 dry-run rc=0")
    check((app / "jdbc.properties").read_text(encoding="utf-8") == sample,
          "dry-run 不写盘")
finally:
    sys.argv = old

# apply 后落盘 + 备份 + 口令已换
try:
    sys.argv = ["switch_kb.py", "--kb-pw-file", str(tmp / "nopw"),
                "--map", "eUrbanMIS:=CGDB,eUrbanMIS:stat=CGDBSTAT", "--apply"]
    rc = sw.main()
    check(rc == 0, "apply rc=0")
    after = (app / "jdbc.properties").read_text(encoding="utf-8")
    check("com.kingbase8.Driver" in after, "驱动已换成 kingbase8")
    check("currentSchema=CGDB" in after and "currentSchema=CGDBSTAT" in after,
          "两个 schema 都写进 URL")
    check("SECRETVALUE123" not in after and "ANOTHERSECRET99" not in after,
          "原口令已被替换")
    check("kingbasepw123" in after, "新口令写入")
    check("jdbc.version=KINGBASE" in after, "jdbc.version 已补")
    check("jdbc.validationQuery=select 1" in after
          and "stat.jdbc.validation.query=select 1" in after,
          "校验查询两种拼法都按原键名改")
    baks = list(app.glob("jdbc.properties.bak.*.dm"))
    check(len(baks) == 1 and "com.mysql" in baks[0].read_text(encoding="utf-8"),
          "备份存在且是改前内容")
finally:
    sys.argv = old

# 空 schema 名（空前缀）也能映射
try:
    sys.argv = ["switch_kb.py", "--kb-pw-file", str(tmp / "nopw"),
                "--map", "eUrbanMIS:=CGDB,eUrbanMIS:stat=CGDBSTAT", "--apply"]
    rc = sw.main()
    check(rc == 0, "二次 apply 幂等 rc=0")
finally:
    sys.argv = old

print("\n== preflight_kb ==")
pf = load("preflight_kb", "preflight_kb.py.txt")
p = pf.parse_props(sample)
check(pf.prefixes_of(p) == ["", "stat"], "prefixes_of 发现空前缀与 stat")
check(pf.mask_url("jdbc:x://h/db?password=abc&a=1")
      == "jdbc:x://h/db?password=***&a=1", "mask_url 打掉 URL 里的口令")

print("\n== verify_kb ==")
vk = load("verify_kb", "verify_kb.py.txt")
check(vk.DEAD == {"000", "404", "400", "500", "502", "503"}, "DEAD 集合")
# 服务器上 real server.xml 的发现逻辑，用合成文件验一遍
sxml = tmp / "server.xml"
sxml.write_text(
    '<Server><Service><Connector port="8081" protocol="HTTP/1.1"/>'
    '<Engine><Host><Context path="/eUrbanMIS" docBase="/egova/web/eUrbanMIS"/>'
    '</Host></Engine></Service></Server>', encoding="utf-8")
m = re.search(r'<Connector[^>]*?\bport\s*=\s*"(\d+)"', sxml.read_text(encoding="utf-8"))
check(m and m.group(1) == "8081", "server.xml Connector 端口可解析")

print()
if FAILS:
    print("FAILED %d:" % len(FAILS))
    for f in FAILS:
        print("  - " + f)
    sys.exit(1)
print("ALL LOCAL CHECKS PASSED")
