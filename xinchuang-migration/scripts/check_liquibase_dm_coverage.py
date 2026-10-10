#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_liquibase_dm_coverage.py — Liquibase changelog 的达梦覆盖审计（迁移前跑）。

真实故障背景：应用从 MySQL 切到达梦后启动即抛 LiquibaseDatabaseInitException。
根因不是"MD5 该不该置空"，而是 changelog 里一批 changeset 的 <sql> 只写了
dbms="mysql" / "oracle" 分支——到达梦路径这些语句被过滤成空，Liquibase 仍然把它们
登记进 databasechangelog，并用空内容重算校验值，于是与 MySQL 路径下记录的原值全部
mismatch。本脚本在迁移前把这些 changeset 点名出来，让人提前决定补 dbms="dm" 分支，
而不是等到启动失败再救火。

只读解析 XML：不连库、不执行任何 SQL、不写任何文件，结果只走 stdout。

用法：
  python check_liquibase_dm_coverage.py --changelog <gis-db-changelog.xml>
  python check_liquibase_dm_coverage.py --jar <WEB-INF/lib/egova-gis-1.0.1.jar>
  python check_liquibase_dm_coverage.py --jar <jar> --entry gis-db-changelog.xml
  python check_liquibase_dm_coverage.py --dir <WEB-INF/classes>
  python check_liquibase_dm_coverage.py --dir <WEB-INF/classes> --json --strict

判定口径：
  OK    有 dbms 适用 dm 的 <sql>/<sqlFile>，或本来就是结构类 change，达梦路径照常执行
  META  没有 SQL 子元素（createTable/addColumn 等），无 dbms 分支问题
  NOOP  有 SQL 但每一条都被 dbms 排除——达梦路径空执行，会重算校验值（最危险的一类）
  SKIP  changeSet 级 dbms 或 preConditions 的 dbms 排除了 dm，整个 changeset 不执行
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.parsers.expat as expat
import zipfile
from pathlib import Path

DM_TOKEN = "dm"
SQL_TAGS = ("sql", "sqlFile")
ROOT_TAG = "databaseChangeLog"

# changelog 是可来源于现场 jar/目录的不可信输入，解析前先卡体积
MAX_XML_BYTES = 64 * 1024 * 1024


def _local(tag: str) -> str:
    """去掉 XML 命名空间前缀，只留本地名。"""
    return tag.rsplit("}", 1)[-1]


class _Elem:
    """极简元素节点：只要 tag/attrs/children，够 changelog 审计用。"""

    __slots__ = ("tag", "attrs", "children")

    def __init__(self, tag: str, attrs: dict) -> None:
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []

    def __iter__(self):
        return iter(self.children)

    def iter(self):
        yield self
        for child in self.children:
            for node in child.iter():
                yield node


def _reject_entity(*_args) -> None:
    raise ValueError("changelog 不允许声明实体（DTD/ENTITY），已拒绝解析")


def parse_xml(data) -> _Elem:
    """解析 changelog XML，返回唯一根元素。

    用 expat 手工建树而不是 ElementTree.fromstring：本函数的输入是现场 jar/目录里
    扒出来的不可信 XML，必须从解析器层面关掉实体扩展（billion laughs）与外部实体
    解析，否则一个恶意 changelog 就能把这个只读审计脚本打成内存炸弹。
    """
    raw = data.encode("utf-8", "replace") if isinstance(data, str) else data
    if len(raw) > MAX_XML_BYTES:
        raise ValueError("输入超过 %d 字节上限，拒绝解析" % MAX_XML_BYTES)

    roots = []
    stack = []

    def start(name: str, attrs: dict) -> None:
        node = _Elem(_local(name), attrs)
        if stack:
            stack[-1].children.append(node)
        else:
            roots.append(node)
        stack.append(node)

    def end(_name: str) -> None:
        stack.pop()

    parser = expat.ParserCreate(namespace_separator="}")
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.EntityDeclHandler = _reject_entity
    parser.ExternalEntityRefHandler = _reject_entity
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    parser.Parse(raw, True)

    if len(roots) != 1:
        raise ValueError("XML 应有且仅有一个根元素，实际 %d 个" % len(roots))
    return roots[0]


def _attr(elem, name: str) -> str:
    return (elem.attrs.get(name) or "").strip()


def _kids(elem, name: str) -> list:
    return [c for c in elem if _local(c.tag) == name]


def dbms_matches(spec: str, target: str = DM_TOKEN) -> bool:
    """Liquibase dbms 属性匹配：逗号分隔白名单，! 前缀为黑名单，空=不限。"""
    tokens = [t.strip().lower() for t in (spec or "").split(",") if t.strip()]
    if not tokens:
        return True
    excluded = [t[1:] for t in tokens if t.startswith("!")]
    if excluded:
        return target not in excluded
    return target in tokens


def _audit_changeset(cs) -> dict:
    info = {
        "id": _attr(cs, "id"),
        "author": _attr(cs, "author"),
        "runAlways": _attr(cs, "runAlways").lower() == "true",
        "verdict": "OK",
        "reason": "",
    }

    cs_dbms = _attr(cs, "dbms")
    if cs_dbms and not dbms_matches(cs_dbms):
        info["verdict"] = "SKIP"
        info["reason"] = 'changeSet 级 dbms="' + cs_dbms + '" 不含 dm，整个 changeset 不执行'
        return info

    for pc in _kids(cs, "preConditions"):
        for node in pc.iter():
            if _local(node.tag) != "dbms":
                continue
            cond = _attr(node, "type")
            if cond and not dbms_matches(cond):
                info["verdict"] = "SKIP"
                info["reason"] = 'preConditions dbms type="' + cond + '" 不含 dm，changeset 不执行'
                return info

    sqls = [c for c in cs if _local(c.tag) in SQL_TAGS]
    if not sqls:
        info["verdict"] = "META"
        info["reason"] = "无 SQL 子元素（结构/元数据类 change），无 dbms 分支问题"
        return info

    usable = [s for s in sqls if dbms_matches(_attr(s, "dbms"))]
    if usable:
        info["verdict"] = "OK"
        info["reason"] = "%d 条 SQL 中 %d 条适用 dm" % (len(sqls), len(usable))
        return info

    specs = ",".join(sorted({_attr(s, "dbms") for s in sqls}))
    info["verdict"] = "NOOP"
    info["reason"] = '%d 条 SQL 全部只在 dbms="%s" 下生效，达梦路径被过滤为空' % (len(sqls), specs)
    return info


def audit_changelog(text: str, source: str = "") -> dict:
    """审计一份 changelog 文本，返回 {source, total, counts, changesets, includes, error}。"""
    rep = {
        "source": source,
        "total": 0,
        "counts": {"OK": 0, "META": 0, "NOOP": 0, "SKIP": 0},
        "changesets": [],
        "includes": [],
        "error": "",
    }
    try:
        root = parse_xml(text)
    except (expat.ExpatError, ValueError) as exc:
        rep["error"] = "XML 解析失败: %s" % exc
        return rep
    if _local(root.tag) != ROOT_TAG:
        rep["error"] = "根元素不是 " + ROOT_TAG + "（实际 " + _local(root.tag) + "），跳过"
        return rep
    for node in root.iter():
        if _local(node.tag) == "include":
            rep["includes"].append(_attr(node, "file"))
        elif _local(node.tag) == "changeSet":
            rep["changesets"].append(_audit_changeset(node))
    rep["total"] = len(rep["changesets"])
    for cs in rep["changesets"]:
        rep["counts"][cs["verdict"]] += 1
    return rep


def _read_text(path: Path) -> str:
    """按 UTF-8 宽松解码，只用于根元素粗筛；真正解析交给原始字节。"""
    return path.read_bytes().decode("utf-8", "replace")


def audit_dir(root: Path) -> list:
    """递归审计目录下所有 Liquibase changelog XML。"""
    reports = []
    for p in sorted(root.rglob("*.xml")):
        if not p.is_file():
            continue
        raw = p.read_bytes()
        if ROOT_TAG not in raw.decode("utf-8", "replace"):
            continue
        reports.append(audit_changelog(raw, source=str(p)))
    return reports


def audit_jar(jar: Path, entry: str = "") -> list:
    """审计 jar 包内的 changelog XML（不释放文件，直接读 zip 成员）。"""
    reports = []
    with zipfile.ZipFile(str(jar)) as zf:
        names = [entry] if entry else zf.namelist()
        for name in names:
            if not name.lower().endswith(".xml"):
                continue
            raw = zf.read(name)
            if ROOT_TAG not in raw.decode("utf-8", "replace") and not entry:
                continue
            reports.append(audit_changelog(raw, source=jar.name + "!" + name))
    return reports


def _collect(args) -> list:
    reports = []
    for one in args.changelog or []:
        p = Path(one)
        if not p.is_file():
            raise SystemExit("gap: changelog 不存在: " + str(p))
        reports.append(audit_changelog(_read_text(p), source=str(p)))
    if args.jar:
        p = Path(args.jar)
        if not p.is_file():
            raise SystemExit("gap: jar 不存在: " + str(p))
        reports.extend(audit_jar(p, args.entry))
    if args.dir:
        p = Path(args.dir)
        if not p.is_dir():
            raise SystemExit("gap: 目录不存在: " + str(p))
        reports.extend(audit_dir(p))
    return reports


def render(reports: list) -> str:
    lines = ["Liquibase changelog 达梦(dbms=\"dm\")覆盖审计", ""]
    bad = []
    for rep in reports:
        if rep["error"]:
            lines.append("⏭ " + rep["source"] + " — " + rep["error"])
            continue
        c = rep["counts"]
        lines.append("源: " + rep["source"])
        lines.append("  changeset 总数 %d：OK %d / META %d / NOOP %d / SKIP %d"
                     % (rep["total"], c["OK"], c["META"], c["NOOP"], c["SKIP"]))
        if rep["includes"]:
            lines.append("  include %d 个（需另行审计）: %s"
                         % (len(rep["includes"]), ", ".join(rep["includes"])))
        for cs in rep["changesets"]:
            if cs["verdict"] in ("NOOP", "SKIP"):
                bad.append((rep["source"], cs))
        lines.append("")
    if bad:
        lines.append("❌ 需要处理的 changeset %d 个（达梦路径下不产生预期 SQL）：" % len(bad))
        for src, cs in bad:
            tag = "空执行" if cs["verdict"] == "NOOP" else "不执行"
            lines.append("  - [%s %s] id=%s author=%s — %s"
                         % (cs["verdict"], tag, cs["id"] or "(空)", cs["author"] or "(空)", cs["reason"]))
    else:
        lines.append("✅ 未发现 NOOP/SKIP changeset")
    lines.append("")
    lines.append("口径：NOOP=有 SQL 但全被 dbms 排除，会以空内容重算校验值并与原值 mismatch；")
    lines.append("     SKIP=整个 changeset 不执行；META=无 SQL 子元素，无 dbms 分支问题。")
    lines.append("处置：为这些 changeset 补 dbms=\"dm\" 分支，或用官方 API 刷新已登记校验值、")
    lines.append("      对未登记的标记为已执行（零手写 SQL 改 databasechangelog）。")
    return "\n".join(lines)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Liquibase changelog 达梦(dbms=\"dm\")覆盖审计（只读，不连库不执行 SQL）")
    parser.add_argument("--changelog", action="append",
                        help="changelog XML 路径，可重复")
    parser.add_argument("--jar", help="含 changelog 的 jar 包路径")
    parser.add_argument("--entry", help="配合 --jar：指定 jar 内的条目名（不给则自动扫全部 xml）")
    parser.add_argument("--dir", help="递归扫描目录下的 changelog XML")
    parser.add_argument("--json", action="store_true", dest="as_json", help="JSON 输出")
    parser.add_argument("--strict", action="store_true",
                        help="存在 NOOP/SKIP 时退出码 2（可作迁移前门禁）")
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding \
            and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if not (args.changelog or args.jar or args.dir):
        raise SystemExit("gap: 必须给 --changelog / --jar / --dir 之一")

    reports = _collect(args)
    if args.as_json:
        print(json.dumps(reports, ensure_ascii=False, indent=1))
    else:
        print(render(reports))

    n_bad = sum(r["counts"]["NOOP"] + r["counts"]["SKIP"] for r in reports if not r["error"])
    return 2 if (args.strict and n_bad) else 0


if __name__ == "__main__":
    sys.exit(main())
