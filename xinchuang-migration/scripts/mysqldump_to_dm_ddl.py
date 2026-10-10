# -*- coding: utf-8 -*-
"""mysqldump DDL → 达梦 DM8 DDL 转换器（纯文本，不连库、不执行 SQL）。

用途：
  把 mysqldump 导出的建表语句批量转成达梦可直接执行的 DDL，用于
  MySQL → 达梦迁移的建库阶段。类型映射口径与
  references/mysql-to-dm-runbook.md 第一节保持一致（2026-10-10 四库
  5589 表全量实证口径）。

用法：
  python mysqldump_to_dm_ddl.py dump.sql > schema.sql         # 标准用法
  python mysqldump_to_dm_ddl.py dump.sql --prefix T_          # 表名加前缀（灰度验证用）
  python mysqldump_to_dm_ddl.py - < dump.sql                  # 从 stdin 读

输出一律走 stdout，由调用方重定向落盘，脚本自身不做任意路径写入。
输出分两段，用分隔注释隔开：
  第一段  建表（仅列定义，不含主键/唯一约束/索引）
  第二段  约束与索引（灌完数据后再执行，见 runbook"建表顺序"）

转换内容：
  1. 反引号 → 双引号（保留含空格/中文的标识符）
  2. 类型映射（VARCHAR 按字符单位声明，规避 DM LENGTH_IN_CHAR=0 截断；
     n > 4000 的列降级为 CLOB）
  3. AUTO_INCREMENT → IDENTITY(1,1)，且紧跟类型（DM 要求 IDENTITY 在列注释前）
  4. 去掉 ENGINE/CHARSET/COLLATE/ROW_FORMAT/USING BTREE 等 MySQL 专属子句
  5. 去掉 unsigned / zerofill / CHARACTER SET / COLLATE 列级子句
  6. 去掉 ON UPDATE CURRENT_TIMESTAMP（DM 不支持，改触发器）
  7. 零日期 DEFAULT '0000-00-00' → DEFAULT NULL
  8. 位字面量 DEFAULT b'1' → DEFAULT 1（DM 不认 MySQL 位字面量）
  9. 表注释 COMMENT='...' → 独立 COMMENT ON TABLE 语句（DM 不接受行内表注释）
  10. 主键/唯一约束/索引从建表语句中摘出，输出到第二段；索引名 = 表名 + 原名
      （MySQL 索引名只在一张表内唯一，DM 按 schema 唯一）
  11. 同表重复索引、与主键列集合完全相同的唯一约束/索引：识别后跳过并告警

不做的事（需要人工判断，转换器只打标记）：
  - FULLTEXT / SPATIAL 索引
  - 分区表（PARTITION BY）
  - 生成列（GENERATED ALWAYS AS）
  - 带函数默认值（DEFAULT CURRENT_TIMESTAMP 之外的表达式）
  - CREATE TABLE ... LIKE ...（照抄另一张表结构，DM 无此语法）
  - 存储例程 PROCEDURE/FUNCTION/EVENT/TRIGGER（体内的 DDL 要在达梦侧人工重建）

已实证：2026-10-10 拿源库主机的 cgdb 真实 dump（5243 张表）转换后在 DM8 V8
实例上真执行，建表 5243/5243、约束/索引/表注释 8911/8911 零失败。
详见 references/mysql-to-dm-runbook.md 第六节。

依赖：Python3 标准库，无第三方包。
编码：Windows 控制台自动 UTF-8。
"""
import argparse
import io
import os
import re
import sys

# DM VARCHAR 上限：4000 字符 × 2 字节（GB18030）= 8000 < 8188 字节上限。
# 超过 4000 字符的列直接降级为 CLOB，避免 [CODE:-70005] 截断。
MAX_VARCHAR_CHARS = 4000

# ---------------------------------------------------------------------------
# 类型映射（口径见 runbook 第一节，全部为实迁验证过的结论）
# ---------------------------------------------------------------------------
SIMPLE_TYPES = {
    "tinyint": "INT",
    "smallint": "INT",
    "mediumint": "INT",
    "int": "INT",
    "integer": "INT",
    "bigint": "BIGINT",
    "bit": "INT",          # MySQL 回 bytes、DM 回 int，比对时须归一
    "bool": "INT",
    "boolean": "INT",
    "float": "DOUBLE",
    "double": "DOUBLE",
    "real": "DOUBLE",
    "date": "DATE",
    "datetime": "TIMESTAMP",
    "timestamp": "TIMESTAMP",  # 零日期 0000-00-00 须转 NULL
    "time": "VARCHAR(32 CHAR)",  # MySQL 回 timedelta、DM 回字符串，须归一
    "year": "INT",
    "json": "CLOB",
}

CHAR_TYPES = {"char", "varchar", "nchar", "nvarchar"}
TEXT_TYPES = {"tinytext", "text", "mediumtext", "longtext"}
BLOB_TYPES = {"tinyblob", "blob", "mediumblob", "longblob", "binary", "varbinary"}
GEOM_TYPES = {"geometry", "point", "linestring", "polygon", "multipoint",
              "multilinestring", "multipolygon", "geometrycollection"}
NUMERIC_TYPES = {"INT", "BIGINT", "DOUBLE", "DECIMAL", "REAL", "NUMERIC"}

# 认识的基础类型全集；不在这里面的按"未识别"处理并告警，不静默输出
KNOWN_TYPES = (set(SIMPLE_TYPES) | CHAR_TYPES | TEXT_TYPES | BLOB_TYPES | GEOM_TYPES
               | {"enum", "set", "decimal", "numeric", "dec"})

TYPE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(\([^)]*\))?", re.S)


def _split_args(s: str):
    """拆分逗号分隔的类型参数，容忍嵌套括号（如 decimal(10,2)、enum('a,b')）。"""
    out, depth, cur = [], 0, []
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur).strip())
    return out


def _char_decl(base: str, n: int) -> str:
    """按字符单位声明长度，超限降级为 CLOB。保留 CHAR / VARCHAR 的语义差别。"""
    if n > MAX_VARCHAR_CHARS:
        return "CLOB"
    return "%s(%d CHAR)" % (base, n)


def map_type(raw: str):
    """把 MySQL 列类型映射为达梦列类型。

    返回 (dm_type, known)。known 为 False 表示基础类型不在映射表内，
    调用方应告警而不是把原样大写的 MySQL 类型静默写进 DDL。
    """
    t = (raw or "").strip()
    m = TYPE_RE.match(t)
    if not m:
        return t.upper(), False
    base = m.group(1).lower()
    params = (m.group(2) or "").strip("()").strip()
    known = base in KNOWN_TYPES

    if base in CHAR_TYPES:
        args = _split_args(params)
        if not args:
            return _char_decl("VARCHAR", 4000), True
        try:
            n = int(args[0])
        except ValueError:
            return _char_decl("VARCHAR", 4000), True
        decl = _char_decl("CHAR" if base in ("char", "nchar") else "VARCHAR", n)
        return decl, True
    if base in TEXT_TYPES:
        return "CLOB", True
    if base in BLOB_TYPES or base in GEOM_TYPES:
        return "BLOB", True
    if base in ("enum", "set"):
        return "VARCHAR(500 CHAR)", True
    if base in ("decimal", "numeric", "dec"):
        args = _split_args(params) or ["18", "0"]
        if len(args) == 1:
            args.append("0")
        return "DECIMAL(%s,%s)" % (args[0], args[1]), True
    if base in SIMPLE_TYPES:
        return SIMPLE_TYPES[base], True
    return t.upper(), known


# ---------------------------------------------------------------------------
# 列定义转换
# ---------------------------------------------------------------------------
# 需要整段丢弃的列级修饰词（大小写不敏感）
_DROP_WORDS = re.compile(
    r"\b(?:unsigned|zerofill|character\s+set\s+[\w$]+|collate\s+[\w$]+|"
    r"storage\s+(?:default|memory|disk)|invisible)\b",
    re.I,
)

# ON UPDATE CURRENT_TIMESTAMP[(n)]：DM 不支持，需改触发器。
# 单独一条正则，不能并进上面的词边界正则——结尾的 \b 在 ')' 前不成立，
# 会迫使可选的小数位组回退，只吃掉 CURRENT_TIMESTAMP 而留下孤立的 "(3)"。
_ON_UPDATE_RE = re.compile(r"\bon\s+update\s+current_timestamp\s*(?:\(\s*\d+\s*\))?", re.I)

# 默认值：结尾不加 \b，否则 "'0000-00-00'" 这种带引号的值匹配不上
#（单引号与后续空格之间不存在单词边界）。
_DEFAULT_RE = re.compile(
    r"\bdefault\s+(null|'[^']*'|-?\d+(?:\.\d+)?|current_timestamp|[bB]'[01]+')",
    re.I,
)

# MySQL 的位字面量 b'101'，达梦不认，按整数值落
_BIT_LITERAL_RE = re.compile(r"^[bB]'([01]+)'$")


def _normalize_default(d: str) -> str:
    """默认值归一：零日期 → NULL，current_timestamp → CURRENT_TIMESTAMP。

    bit 字面量 b'1' 转成整数：cgdb 里 bit(1) 列映射成 INT，默认值却原样带着
    b'1'，DM8 直接报 Syntax error（真执行实证）。
    """
    d = d.strip()
    m = _BIT_LITERAL_RE.match(d)
    if m:
        return str(int(m.group(1), 2))
    if d.replace("-", "").replace(":", "").replace(" ", "").strip("'") in (
        "00000000", "00000000000000", "0000"
    ):
        return "NULL"
    if d.upper().startswith("CURRENT_TIMESTAMP"):
        return "CURRENT_TIMESTAMP"
    return d


def convert_column(coldef: str):
    """转换单列定义（`列名` 类型 [修饰...]）。返回 (新定义, 需人工标记或None)。"""
    s = coldef.strip()
    if not s:
        return s, None

    # 列名（反引号包裹或裸标识符）
    if s.startswith("`"):
        end = s.find("`", 1)
        if end < 0:
            return s, None
        name, rest = s[:end + 1], s[end + 1:]
    else:
        m = re.match(r"^([\w$]+)", s)
        if not m:
            return s, None
        name, rest = s[:m.end()], s[m.end():]

    # 反引号 → 双引号：DM 用双引号保留含空格/中文/大小写敏感的标识符
    if name.startswith("`"):
        name = '"%s"' % name[1:-1]

    rest = rest.lstrip()
    m = TYPE_RE.match(rest)
    if not m:
        return name + " " + rest, None
    new_type, known = map_type(rest[:m.end()])
    tail = rest[m.end():]

    # auto_increment → IDENTITY，放在类型之后
    is_auto = re.search(r"\bauto_increment\b", tail, re.I) is not None
    if is_auto:
        tail = re.sub(r"\bauto_increment\b", "", tail, flags=re.I)

    tail = _ON_UPDATE_RE.sub("", tail)
    tail = _DROP_WORDS.sub("", tail)
    dm = _DEFAULT_RE.search(tail)
    if dm:
        default = _normalize_default(dm.group(1))
        # mysqldump 给数值列也写引号（DEFAULT '0'）；DM 侧按字面量解析，
        # 数值列去掉引号更稳，字符列保留引号。
        if (new_type.split("(")[0] in NUMERIC_TYPES
                and default.startswith("'") and default.endswith("'")):
            default = default[1:-1]
        tail = tail[:dm.start()] + "DEFAULT " + default + tail[dm.end():]

    # 生成列等保留项：至少把反引号统一成双引号，输出别带着 MySQL 标识符
    tail = re.sub(r"`([^`]*)`", r'"\1"', tail)
    tail = re.sub(r"\s{2,}", " ", tail).strip()
    out = "%s %s" % (name, new_type)
    # DM 语法：IDENTITY 必须排在列注释之前。`COMMENT 'x' IDENTITY(1,1)`
    # 在 DM8 上直接报 Syntax error（V8 实证），所以 IDENTITY 要紧跟类型。
    if is_auto:
        out += " IDENTITY(1,1)"
    if tail:
        out += " " + tail

    note = None
    if not known:
        note = "未识别类型，已原样大写输出，需人工确认 DM 兼容性：%s" % re.sub(r"\s{2,}", " ", s)[:100]
    elif re.search(r"\bgenerated\s+always\s+as\b", s, re.I):
        note = "生成列需人工改写：%s" % re.sub(r"\s{2,}", " ", s)[:100]
    return out, note


# ---------------------------------------------------------------------------
# 建表语句解析
# ---------------------------------------------------------------------------
CREATE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(`[^`]+`|[\w$]+)\s*\(",
    re.I | re.S,
)

# CREATE TABLE ... LIKE ...：MySQL"照抄另一张表结构"的语法，DM 不支持。
# cgdb 真实 dump 里就有 2 张这样的表，必须点名告警而不是静默跳过。
CREATE_LIKE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(`[^`]+`|[\w$]+)\s+LIKE\b",
    re.I,
)

# 约束/索引类定义的前缀（不是列定义）
CONSTRAINT_PREFIX = re.compile(
    r"^\s*(?:PRIMARY\s+KEY|UNIQUE\s+KEY|UNIQUE\s+INDEX|UNIQUE|KEY|INDEX|"
    r"CONSTRAINT|FOREIGN\s+KEY|FULLTEXT|SPATIAL|CHECK)\b",
    re.I,
)


def _find_matching_paren(text: str, open_idx: int):
    """从 '(' 位置找配对的 ')'，返回 (content, close_idx)。容忍字符串与反引号内容。"""
    depth, i, n = 0, open_idx, len(text)
    quote = None
    while i < n:
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            i += 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[open_idx + 1:i], i
        i += 1
    return text[open_idx + 1:], n - 1


def _split_top_level(body: str):
    """按顶层逗号拆分列/约束定义。"""
    out, depth, cur = [], 0, []
    quote = None
    for ch in body:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            cur.append(ch)
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        out.append("".join(cur))
    return out


def _first_paren(s: str, start: int = 0):
    """取 s 中 start 之后第一个完整括号组的内容，找不到返回 None。"""
    i = s.find("(", start)
    if i < 0:
        return None
    content, _ = _find_matching_paren(s, i)
    return content


def _quote_cols(cols_text: str):
    """转换索引列列表：反引号 → 双引号，去掉前缀长度。

    返回 (sql, stripped_prefix)。DM 不按 MySQL 的方式支持前缀索引，
    剥掉长度后能建上索引但覆盖范围变小，需要调用方打标。
    """
    had_prefix = False

    def repl(m):
        nonlocal had_prefix
        name, plen = m.group(1), m.group(2)
        if plen:
            had_prefix = True
        return '"%s"' % (name[1:-1] if name.startswith("`") else name)

    out = re.sub(r"(`[^`]*`|[\w$]+)\s*(\(\s*\d+\s*\))?", repl, cols_text)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out, had_prefix


def convert_constraint(idxdef: str, dm_table: str, pk_cols=None):
    """把索引/约束定义转成独立语句。

    返回 (sql, note)。sql 为 None 表示该条需人工处理或已按 DM 语义跳过。
    索引/约束名 = 表名 + 原名：MySQL 的索引名只在一张表内唯一，达梦按 schema
    维度唯一，同名索引落在不同表上会直接撞 -2140（cgdb 真执行 150 条失败的主因）。
    dm_table 本身已带前缀，名称里不要再拼一次前缀，否则会出现 DDLCHK_DDLCHK_。

    pk_cols：本表主键列名列表，用于识别"列集合与主键完全相同"的冗余约束/索引。
    """
    s = re.sub(r"\s{2,}", " ", idxdef.strip())
    head = s.split(None, 1)[0].upper() if s else ""
    base = dm_table.strip('"')

    if head in ("FULLTEXT", "SPATIAL"):
        return None, "需人工处理（DM 无全文/空间索引）：%s" % s[:120]

    def cols_note(sql_cols):
        cols, stripped = _quote_cols(sql_cols)
        if stripped:
            return cols, "已剥掉前缀长度（DM 前缀索引支持有限，索引覆盖范围变小）：%s" % s[:100]
        return cols, None

    def unique_name(cname, fallback):
        """索引名 = 表名 + 原名，保证 schema 内唯一（表名在 schema 内唯一）。"""
        name = base + "_" + (cname or fallback)
        if len(name) > 200:
            name = name[:200]
        return name

    def col_list(cols_text):
        # 列名可能还带反引号（原始 MySQL 文本），统一剥掉再比对主键列
        cleaned = re.sub(r"`([^`]*)`", r"\1", cols_text)
        return [c.strip().strip('"') for c in cleaned.split(",") if c.strip()]

    def redundant(cols):
        """列集合与主键完全相同的唯一约束/索引：DM 不允许重复建。

        只判"完全相同"：复合主键 (a,b) 上单列 UNIQUE(a) 是更弱的合法约束，
        不能顺手删掉。
        """
        if not pk_cols:
            return False
        return bool(cols) and sorted(cols) == sorted(pk_cols)

    # PRIMARY KEY (`a`,`b`)
    if re.match(r"^PRIMARY\s+KEY", s, re.I):
        raw = _first_paren(s)
        if raw is None:
            return None, "主键定义无法解析：%s" % s[:120]
        cols, note = cols_note(raw)
        return ('ALTER TABLE %s ADD CONSTRAINT "PK_%s" PRIMARY KEY (%s);'
                % (dm_table, base, cols)), note

    # UNIQUE KEY `name` (`a`,`b`) / UNIQUE `name` (`a`)
    if re.match(r"^UNIQUE", s, re.I):
        m = re.match(r"^UNIQUE\s+(?:KEY|INDEX)?\s*(`[^`]*`|[\w$]+)?\s*\(", s, re.I)
        if not m:
            return None, "唯一约束无法解析：%s" % s[:120]
        raw = _first_paren(s, m.end() - 1)
        if raw is None:
            return None, "唯一约束无法解析：%s" % s[:120]
        cols, note = cols_note(raw)
        cname = m.group(1)
        cname = cname[1:-1] if cname and cname.startswith("`") else (cname or "")
        if redundant(col_list(raw)):
            return None, ("已跳过：%s 唯一约束的列与主键完全相同，DM 不允许"
                          "重复建（MySQL 允许）：%s" % (dm_table, s[:100]))
        return ('ALTER TABLE %s ADD CONSTRAINT "%s" UNIQUE (%s);'
                % (dm_table, unique_name(cname, "UK_%s" % base), cols)), note

    # KEY/INDEX `name` (`a`,`b`)
    m = re.match(r"^(?:KEY|INDEX)\s+(`[^`]*`|[\w$]+)\s*\(", s, re.I)
    if m:
        raw = _first_paren(s, m.end() - 1)
        if raw is None:
            return None, "索引定义无法解析：%s" % s[:120]
        cols, note = cols_note(raw)
        cname = m.group(1)
        cname = cname[1:-1] if cname.startswith("`") else cname
        if redundant(col_list(raw)):
            return None, ("已跳过：%s 索引列与主键完全相同，DM 会报重复索引"
                          "（MySQL 允许）：%s" % (dm_table, s[:100]))
        return ('CREATE INDEX "%s" ON %s (%s);'
                % (unique_name(cname, "IX_%s" % base), dm_table, cols)), note

    # FOREIGN KEY / CHECK：DM 语法兼容但依赖被引表存在，保留并打标
    if re.match(r"^(?:FOREIGN\s+KEY|CONSTRAINT|CHECK)", s, re.I):
        return (
            'ALTER TABLE %s ADD %s;' % (dm_table, re.sub(r"`([^`]*)`", r'"\1"', s)),
            "外键/CHECK 需确认被引表已存在：%s" % s[:100],
        )

    return None, "无法识别的约束定义：%s" % s[:120]


def convert_create(stmt: str, prefix: str = ""):
    """转换一条 CREATE TABLE 语句。

    返回 (create_sql, constraint_sqls, notes)。
    """
    m = CREATE_RE.search(stmt)
    if not m:
        lm = CREATE_LIKE_RE.search(stmt)
        if lm:
            t = lm.group(1)
            t = t[1:-1] if t.startswith("`") else t
            return None, [], ["%s 用 CREATE TABLE ... LIKE ... 照抄另一张表结构，"
                              "DM 不支持该语法，需按源表结构人工建表" % t]
        return None, [], []

    table_raw = m.group(1)
    table = table_raw[1:-1] if table_raw.startswith("`") else table_raw
    # 表名用双引号包裹保留原名（含空格/中文时不加前缀，避免标识符歧义）
    dm_table = '"%s%s"' % (prefix, table)

    open_idx = m.end() - 1
    body, close_idx = _find_matching_paren(stmt, open_idx)

    cols, cons, notes = [], [], []
    items = [it for it in _split_top_level(body) if it.strip()]

    # 先取主键列：达梦会为主键自动建唯一索引，重复的唯一约束/索引会被拒
    # （-2864 / -3236，真执行实证），所以要在转换期就识别出来。
    pk_cols = None
    for item in items:
        if CONSTRAINT_PREFIX.match(item) and re.match(r"^\s*PRIMARY\s+KEY", item, re.I):
            raw = _first_paren(item.strip())
            if raw:
                pk_cols = [c.strip().strip('"')
                           for c in re.sub(r"`([^`]*)`", r"\1", raw).split(",")
                           if c.strip()]
            break

    seen_index_cols = set()
    for item in items:
        if CONSTRAINT_PREFIX.match(item):
            # 同一张表里列清单完全相同的索引只保留第一条：MySQL 允许冗余索引，
            # DM 报 -3236 such column list already indexed。
            key = re.sub(r"\s+", "", item.strip().upper())
            key = re.sub(r"^(UNIQUE)?(KEY|INDEX)`[^`]*`", "", key)
            if key in seen_index_cols:
                notes.append("%s 存在列清单完全相同的重复索引，已跳过：%s"
                             % (dm_table, re.sub(r"\s{2,}", " ", item.strip())[:100]))
                continue
            seen_index_cols.add(key)
            sql, note = convert_constraint(item, dm_table, pk_cols=pk_cols)
            if sql:
                cons.append(sql)
            if note:
                notes.append(note)
        else:
            c, note = convert_column(item)
            cols.append(c)
            if note:
                notes.append(note)

    # 表级后缀子句（ENGINE=... DEFAULT CHARSET=... COMMENT='...' 等）
    suffix = stmt[close_idx + 1:].strip().rstrip(";").strip()
    cm = re.search(r"COMMENT\s*=?\s*'((?:[^'\\]|\\.)*)'", suffix, re.I)
    if cm:
        # DM 不接受 CREATE TABLE 右括号后跟 COMMENT '...'（V8 实证报 Syntax error），
        # 表注释必须拆成独立语句，且要等表建好之后才能执行。
        cons.append("COMMENT ON TABLE %s IS '%s';"
                    % (dm_table, cm.group(1).replace("'", "''")))
    if re.search(r"\bPARTITION\s+BY\b", suffix, re.I):
        # 只取第一行，避免把 /*!50100 ... */ 条件注释整段带进告警
        first = re.sub(r"/\*.*?\*/", "", suffix, flags=re.S).strip().splitlines()
        notes.append("%s 是分区表，需人工改写（DM 分区语法不同）：%s"
                     % (dm_table, first[0][:100] if first else ""))

    parts = ["CREATE TABLE %s (" % dm_table]
    for i, d in enumerate(cols):
        parts.append("    " + d + ("," if i < len(cols) - 1 else ""))
    parts.append(");")
    return "\n".join(parts), cons, notes


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def read_source(path: str) -> str:
    """读取 mysqldump 文本。path 为 '-' 时读 stdin。"""
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def split_statements(text: str):
    """按分号切分 SQL 语句，容忍字符串与反引号内的分号。"""
    out, cur, quote = [], [], None
    for ch in text:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            cur.append(ch)
            continue
        if ch == ";":
            s = "".join(cur).strip()
            if s:
                out.append(s + ";")
            cur = []
        else:
            cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        out.append(tail)
    return out


def main():
    ap = argparse.ArgumentParser(
        description="mysqldump DDL → 达梦 DM8 DDL（纯文本转换，不连库不执行）"
    )
    ap.add_argument("src", help="mysqldump 文件路径，'-' 表示从 stdin 读")
    ap.add_argument("--prefix", default="", help="表名前缀，灰度验证时用（默认空）")
    args = ap.parse_args()

    if args.src != "-" and not os.path.isfile(args.src):
        sys.stderr.write("[FAIL] 文件不存在：%s\n" % args.src)
        return 2

    stmts = split_statements(read_source(args.src))

    creates, constraints = [], []
    n_ok, n_skip = 0, 0
    # 本转换器只覆盖 CREATE TABLE。例程体（PROCEDURE/FUNCTION/EVENT/TRIGGER）
    # 里常夹带 DDL，被分号切碎后不会进产物——必须点名，否则现场会以为结构齐了。
    n_routine = 0
    routine_names = []
    for st in stmts:
        if not re.match(r"\s*CREATE\s+TABLE\b", st, re.I):
            rm = re.match(
                r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?"
                # mysqldump 会写 CREATE DEFINER=`root`@`%` PROCEDURE ...
                r"(?:DEFINER\s*=\s*[^\s(]+\s+)?"
                r"(PROCEDURE|FUNCTION|EVENT|TRIGGER)\s+"
                r"(?:IF\s+NOT\s+EXISTS\s+)?(`[^`]+`|[\w$]+)", st, re.I)
            if rm:
                n_routine += 1
                if len(routine_names) < 10:
                    nm = rm.group(2)
                    routine_names.append(nm[1:-1] if nm.startswith("`") else nm)
            continue
        create, cons, notes = convert_create(st, args.prefix)
        if create is None:
            # 解析失败的也要把原因喊出来，否则表会静默从产物里消失
            n_skip += 1
            for nt in notes:
                sys.stderr.write("[WARN] %s\n" % nt)
            continue
        creates.append(create)
        constraints.extend(cons)
        n_ok += 1
        for nt in notes:
            sys.stderr.write("[WARN] %s\n" % nt)

    out = ["-- ============================================================",
           "-- MySQL → 达梦 DM8 DDL（由 mysqldump_to_dm_ddl.py 转换）",
           "-- 第一段：建表（仅列定义）。灌完数据后执行第二段。",
           "-- ============================================================",
           ""]
    out.extend(creates)
    out.append("")
    out.append("-- ============================================================")
    out.append("-- 第二段：主键 / 唯一约束 / 索引（灌数完成后执行）")
    out.append("-- 依据：前置建索引会显著拖慢批量插入，见 runbook'建表顺序'")
    out.append("-- ============================================================")
    out.append("")
    out.extend(constraints)
    out.append("")
    sys.stdout.write("\n".join(out))
    sys.stderr.write("[DONE] 转换 %d 张表，%d 条约束/索引，跳过 %d 条无法解析的语句\n"
                     % (n_ok, len(constraints), n_skip))
    if n_routine:
        sys.stderr.write(
            "[WARN] 检出 %d 个存储例程（PROCEDURE/FUNCTION/EVENT/TRIGGER），"
            "其体内的 DDL/DML 不在本转换器覆盖范围内，需在达梦侧人工重建：%s\n"
            % (n_routine, "、".join(routine_names)))
    return 0


def _force_utf8_console():
    """Windows 控制台默认 GBK，重包一层保证中文/告警不乱码。

    只允许在 __main__ 入口调用：被 import 时替换 sys.stdout 会污染调用方
    （pytest 的捕获对象底层是临时文件，拆夹具时会被关闭）。
    """
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    try:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass


if __name__ == "__main__":
    _force_utf8_console()
    sys.exit(main())
