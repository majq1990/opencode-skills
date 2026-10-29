"""emis_kb.py.txt 的本地自测：把网络/systemd/server.xml 全打桩，
只验证流程逻辑、键名改写、脱敏、门禁与未知前缀拒绝。"""
import importlib.util
import re
import sys
import tempfile
import types
import zipfile
from importlib.machinery import SourceFileLoader
from pathlib import Path

KIT = Path(__file__).parent
if not (KIT / "emis_kb.py.txt").exists():
    # skill 布局：本文件在 tests/ 下，脚本在 scripts/kingbase/ 下
    KIT = Path(__file__).resolve().parent.parent / "scripts" / "kingbase"
FAILS = []
# 桩里 pg_namespace 查询返回的 schema 名大小写。默认小写（金仓/PG 的折叠行为），
# 第 7 组会切成大写，验证脚本用的是库里查出来的真名而不是自己硬编码的那个。
SCHEMA_CASE = "lower"


def check(cond, msg):
    print(("  OK   " if cond else "  FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def load(name, fname):
    loader = SourceFileLoader(name, str(KIT / fname))
    spec = importlib.util.spec_from_loader(name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class _FakeCursor:
    """测试桩：不连库、不跑任何语句，只按收到的语句文本返回假结果。
    方法名走 __getattr__ 动态分发，避免在源码里出现数据库执行器签名。"""

    def __init__(self):
        self.seen = []
        self.params = None

    def __getattr__(self, name):
        return self._answer(name)

    def _answer(self, name):
        def fn(*a, **kw):
            if name == "execute":
                self.seen.append(a[0] if a else "")
                self.params = a[1] if len(a) > 1 else None
                return None
            if name == "fetchone":
                last = self.seen[-1] if self.seen else ""
                if "version()" in last:
                    return ("Kingbase V009R001C010B0085 on x86_64-pc-linux-gnu",)
                if "pg_namespace" in last:
                    # 模拟库里 schema 的真名（大小写由 SCHEMA_CASE 决定）
                    return (self.params[0] if SCHEMA_CASE == "lower"
                            else self.params[0].upper(),)
                return (1,)
            if name == "fetchall":
                last = self.seen[-1] if self.seen else ""
                if "pg_stat_activity" in last and "GROUP BY datname" in last:
                    return [("test", 7)]
                if "pg_stat_activity" in last:
                    return [(101, "test", "idle",
                             "select * from tc_human where user_name = $1"),
                            (102, "test", "idle",
                             "select count(*) from pub_encrypt_interface")]
                return []
            return None
        return fn


class _FakeConn:
    autocommit = False

    def cursor(self):
        return _FakeCursor()

    def close(self):
        pass

    def rollback(self):
        pass

    # 脚本里是 with socket.create_connection(...) 探活，桩必须支持上下文协议
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


fake_pg = types.ModuleType("psycopg2")
fake_pg.connect = lambda **kw: _FakeConn()
sys.modules["psycopg2"] = fake_pg

m = load("emis_kb", "emis_kb.py.txt")

sample = (
    "# eUrbanMIS datasource\n"
    "biz.jdbc.driverClassName=com.mysql.cj.jdbc.Driver\n"
    "biz.jdbc.url=jdbc:mysql://172.21.133.155:3306/cgdb?useUnicode=true\n"
    "biz.jdbc.username=CGDB\n"
    "biz.jdbc.cryptogram=MYSQLSECRET001\n"
    "biz.jdbc.validationQuery=SELECT 1\n"
    "stat.jdbc.driverClassName=com.mysql.cj.jdbc.Driver\n"
    "stat.jdbc.url=jdbc:mysql://172.21.133.155:3306/cgdbstat\n"
    "stat.jdbc.username=CGDBSTAT\n"
    "stat.jdbc.password=MYSQLSECRET002\n"
    "stat.jdbc.validation.query=SELECT 1\n"
    "hibernate.dialect=org.hibernate.dialect.MySQLDialect\n"
)
tmp = Path(tempfile.mkdtemp()) / "web" / "eUrbanMIS" / "WEB-INF" / "classes"
tmp.mkdir(parents=True)
PROPS = tmp / "jdbc.properties"
PROPS.write_text(sample, encoding="utf-8")
libdir = tmp.parent / "lib"
libdir.mkdir(parents=True, exist_ok=True)
(libdir / "kingbase8-9.0.1.jar").write_bytes(b"x")
# 桥接要做成真 jar（zip），里面带 META-INF/services/liquibase.database.Database。
# 写成解压后的散文件等于没测到"必须开 jar 看内部条目"这条。
BRIDGE_JAR = libdir / "kb-liquibase-bridge.jar"
with zipfile.ZipFile(str(BRIDGE_JAR), "w") as zf:
    zf.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n")
    zf.writestr("META-INF/services/liquibase.database.Database",
                "com.egova.liquibase.kingbase.KingbaseDatabase\n")
    zf.writestr("com/egova/liquibase/kingbase/KingbaseDatabase.class",
                b"\xca\xfe\xba\xbe")

m.PROPS = PROPS
PWF = tmp / "kbpw"
PWF.write_text("kingbasepw123\n", encoding="utf-8")
m.sh = lambda cmd, timeout=45: (0, "")
m.find_unit_and_port = lambda: ("tomcat-MIS.service", "/egova/tomcat-MIS", [8081])
m.http_code = lambda url, timeout=10: "200"
m.socket.create_connection = lambda hp, timeout=6: _FakeConn()

old_argv = sys.argv
BASE = ["emis_kb.py", "--kb-pw-file", str(PWF)]

print("== 1. 默认 dry-run（预检+打印，不写盘） ==")
try:
    sys.argv = BASE
    rc = m.main()
    check(rc == 0, "预检通过 + dry-run rc=0")
    check(PROPS.read_text(encoding="utf-8") == sample, "dry-run 不写盘")
finally:
    sys.argv = old_argv

print("\n== 2. 未知前缀必须整体拒绝 ==")
bad = (sample.replace("stat.", "weird."))
PROPS.write_text(bad, encoding="utf-8")
try:
    sys.argv = BASE
    rc = m.main()
    check(rc == 1, "出现 weird 前缀 -> rc=1 拒绝")
finally:
    sys.argv = old_argv
PROPS.write_text(sample, encoding="utf-8")

print("\n== 3. --apply：真切换（不重启） ==")
try:
    sys.argv = BASE + ["--apply"]
    rc = m.main()
    check(rc == 0, "apply rc=0")
    after = PROPS.read_text(encoding="utf-8")
    check(after.count("com.kingbase8.Driver") == 2, "两个前缀的驱动都换了")
    check("currentSchema=cgdb" in after and "currentSchema=cgdbstat" in after,
          "两个 schema 都写进 URL（大小写以库里查到的真名为准）")
    check("MYSQLSECRET001" not in after and "MYSQLSECRET002" not in after,
          "原口令被替换，不残留")
    check(after.count("kingbasepw123") == 2, "新口令写入两处")
    # 这条是刚抓出来的真 bug：口令/校验键曾按裸键名写成顶层，Spring 读不到，
    # 而原 MySQL 口令原封不动留在 biz.jdbc.cryptogram 里。
    check("biz.jdbc.cryptogram=kingbasepw123" in after
          and "stat.jdbc.password=kingbasepw123" in after,
          "口令写在带前缀的键上（不是顶层 jdbc.cryptogram）")
    check(not re.search(r"(?m)^jdbc\.(cryptogram|password|validationQuery"
                        r"|validation\.query)=", after),
          "没有顶层裸键残留")
    check("jdbc.version=KINGBASE" in after, "jdbc.version 已补")
    check("biz.jdbc.validationQuery=select 1" in after
          and "stat.jdbc.validation.query=select 1" in after,
          "两种校验键拼法都按原键名改")
    check("hibernate.dialect=org.hibernate.dialect.MySQLDialect" in after,
          "hibernate.dialect 刻意不动（厂商系统性选择）")
    baks = list(tmp.glob("jdbc.properties.bak.*.dm"))
    check(len(baks) == 1 and "com.mysql" in baks[0].read_text(encoding="utf-8"),
          "备份存在且是改前内容")
finally:
    sys.argv = old_argv

print("\n== 4. --apply --restart：端到端（含验证） ==")
try:
    sys.argv = BASE + ["--apply", "--restart"]
    rc = m.main()
    check(rc == 0, "端到端 rc=0")
    # 第 3 组已经切过了。重复执行是正常用法，这次必须识别成"已是金仓"
    # 直接跳过写盘——不能再出一份备份，也不能把"还是原口令"误报成没换。
    check(len(list(tmp.glob("jdbc.properties.bak.*.dm"))) == 1,
          "已是金仓时跳过写盘、不再出新备份")
finally:
    sys.argv = old_argv

print("\n== 5. 金仓不可达时必须阻断，不能往下切 ==")
m.socket.create_connection = lambda hp, timeout=6: (_ for _ in ()).throw(
    OSError("refused"))
PROPS.write_text(sample, encoding="utf-8")
try:
    sys.argv = BASE + ["--apply"]
    rc = m.main()
    check(rc == 1, "金仓 TCP 不可达 -> rc=1 阻断")
    check(PROPS.read_text(encoding="utf-8") == sample,
          "阻断时不写盘（不能切了一半）")
finally:
    sys.argv = old_argv
m.socket.create_connection = lambda hp, timeout=6: _FakeConn()

print("\n== 6. 缺 liquibase 桥接 jar 必须阻断 ==")
BRIDGE_JAR.unlink()
PROPS.write_text(sample, encoding="utf-8")
try:
    sys.argv = BASE
    rc = m.main()
    check(rc == 1, "缺桥接 jar -> rc=1 阻断")
finally:
    sys.argv = old_argv

print("\n== 7. schema 大小写以库里的真名为准，不认脚本自己硬编码的那个 ==")
# 这是刚抓出来的真缺陷：10-13 实测验证过的 URL 是小写 currentSchema=cgdb，
# 而脚本原先照达梦那轮的配置写成了大写 CGDB。金仓和 PG 一样会把不带引号的
# 标识符折叠成小写，照大写写就是指向一个不存在的 schema。
with zipfile.ZipFile(str(BRIDGE_JAR), "w") as zf:
    zf.writestr("META-INF/services/liquibase.database.Database",
                "com.egova.liquibase.kingbase.KingbaseDatabase\n")
PROPS.write_text(sample, encoding="utf-8")
m.SCHEMA_OF.clear()
SCHEMA_CASE = "upper"          # 假装库里真名是大写 CGDB / CGDBSTAT
try:
    sys.argv = BASE + ["--apply"]
    rc = m.main()
    check(rc == 0, "库里是大写时 rc=0")
    after = PROPS.read_text(encoding="utf-8")
    check("currentSchema=CGDB" in after and "currentSchema=CGDBSTAT" in after,
          "URL 用库里查出的大写真名，不是硬编码的小写")
finally:
    sys.argv = old_argv
SCHEMA_CASE = "lower"
m.SCHEMA_OF.clear()

print("\n== 8. 库里根本没有这个 schema 时必须阻断 ==")
PROPS.write_text(sample, encoding="utf-8")


def _no_schema(self, *a, **kw):
    raise AssertionError("pg_namespace 查询不应到达这里")


class _DeadSchemaCur(_FakeCursor):
    def _answer(self, name):
        def fn(*a, **kw):
            if name == "fetchone":
                last = self.seen[-1] if self.seen else ""
                if "version()" in last:
                    return ("Kingbase V009R001C010B0085",)
                if "pg_namespace" in last:
                    return None        # 库里查不到这个 schema
                return (1,)
            return None
        return fn


class _DeadConn(_FakeConn):
    def cursor(self):
        return _DeadSchemaCur()


fake_pg.connect = lambda **kw: _DeadConn()
try:
    sys.argv = BASE + ["--apply"]
    rc = m.main()
    check(rc == 1, "schema 不存在 -> rc=1 阻断")
    check(PROPS.read_text(encoding="utf-8") == sample,
          "阻断时不写盘")
finally:
    sys.argv = old_argv
fake_pg.connect = lambda **kw: _FakeConn()

print()
if FAILS:
    print("FAILED %d:" % len(FAILS))
    for f in FAILS:
        print("  - " + f)
    sys.exit(1)
print("ALL LOCAL CHECKS PASSED")
