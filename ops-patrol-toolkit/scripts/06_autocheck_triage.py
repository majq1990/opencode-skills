#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
06_autocheck_triage —— auto-check 巡检报告告警分诊与处置引导（R48 子工具 06）。

摄取公司 auto-check 巡检系统产出的 JSON 巡检报告，解码指标键与预警表达式，
判定告警项并按剧本库生成中文处置引导报告，实现"巡检发现的问题 → 引导问题处理"。

报告契约（参考 D:/git/auto-check 只读调研，源码 ansible/filter_plugins/filters.py）：
  {"{type}_{hostname}": {"version": "...", "report_time": "...",
   "data": {"basic": {...}, "topics": {"NN:topic": [ {"指标键": 值, ...}, ...]}}}}
指标键格式：`序号:名称:单位:预警表达式:WIKI锚点`，如 "01:cpu_used%:%:DATA_gt_60:#4864"。

预警表达式为子串替换语法（安全复刻，禁止 eval/exec/compile）：
  lt_→<  le_→<=  ge_→>=  gt_→>  eq_→==  ne_→!=  dot_→.  _quot_→"
  _and_→" and "  _or_→" or "  _lbc_→(  _rbc_→)  _lbk_→[  _rbk_→]  mul_→*
  WRAPDATA_/WRAPDATA、DATA_/DATA 占位替换为指标值（去千分位逗号后尝试 int/float，
  失败用带引号字符串）；CURTIME30 替换为当前时间-30 分钟（带引号）。
求值用自研递归下降安全求值器：数字/带引号字符串、比较 < <= > >= == !=、
and/or、括号、白名单函数 abs()。解析失败/类型不一致一律视为告警——与参考实现
check_by_key 的 `except: return True` 保守行为一致（例如 DATA_ne_0 解码后为
"X !=_0" 的真实语法错误场景，参考实现因 SyntaxError 恒告警，本实现同样恒告警）。

剧本匹配优先级：
  1. --playbooks（references/autocheck_playbooks.json，延后同步）按指标名精确匹配，
     文件缺失静默跳过该层。schema：
     {"version": "...", "playbooks": [{"metric_names": ["cpu_used%"], "title": "...",
       "severity_hint": "high", "steps": ["..."]}]}（也接受直接 {"指标名": {...}} 映射）
  2. --metrics（references/autocheck_metrics.json，延后同步）按指标名精确匹配，
     文件缺失静默跳过该层。schema：
     {"version": "...", "metrics": {"cpu_used%": {"title": "...",
       "severity_hint": "high", "steps": ["..."]}}}
  3. --common（references/playbooks/common_playbooks.json）名称/表达式小写 contains 关键词
  4. 兜底通用 3 步（确认现象与影响范围 / 查 WIKI / 用 05 号子工具检索历史案例）

用法：
  python scripts/06_autocheck_triage.py triage --report R.json [--report R2.json ...] \\
      [--dir DIR] [--metrics P] [--playbooks P] [--common P] [--out work/autocheck/guide.md]

stdout 最后一行 JSON 信封：
  {"ok": true, "files": N, "hosts": N, "topics": N, "alert_items": K,
   "by_severity": {...}, "report": "路径", "warnings": [...]}
缺文件/全部无法识别 → {"ok": false, "gap": "..."} 退出码 2。

与参考实现的差异决策（均为有意为之）：
  - HTML 报告专属单位 A_HREF/A_TARGET 原样输出值（本工具产 markdown，不产 html 锚点）
  - 嵌套 dict 值（如 tcpconnection 的子指标）按子指标键递归检查，覆盖参考实现
    get_warning_summary 不下钻的盲区；带表达式的键仍按自身表达式判定
  - WIKI 锚点同时接受 "#9744" 与 "9744" 两种形式
  - 阈值人读展示中 CURTIME30 显示为"当前时间-30分钟"，避免报告掺入噪声时间戳
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import patrol_lib  # noqa: E402

WIKI_BASE = "http://faq.egova.com.cn:7777/projects/redmine/wiki/"

# 与参考实现 get_comp_expr 的 comp_dict 逐项一致，顺序即替换顺序（dict 保序）
COMP_DICT = [
    ("lt_", "<"),
    ("le_", "<="),
    ("ge_", ">="),
    ("gt_", ">"),
    ("eq_", "=="),
    ("ne_", "!="),
    ("dot_", "."),
    ("_quot_", "\""),
    ("_and_", " and "),
    ("_or_", " or "),
    ("_lbc_", "("),
    ("_rbc_", ")"),
    ("_lbk_", "["),
    ("_rbk_", "]"),
    ("mul_", "*"),
]

FALLBACK_STEPS = [
    "确认现象与影响范围：登录 {host} 复核指标【{name}】当前值，区分持续越限与瞬时抖动，评估影响业务范围",
    "按 WIKI 链接查阅处理指引（无链接时向 auto-check 维护团队确认该指标含义）",
    "必要时用 05 号子工具检索历史相似案例：python scripts/05_kb_similar_search.py query --text \"{name} {host} 处理方法\"",
]


# ---------------------------------------------------------------- 指标键解析

def parse_metric_key(key):
    """解析 `序号:名称:单位:预警表达式:WIKI锚点`，返回 dict；非指标键（段数<2）返回 None。"""
    parts = str(key).split(":")
    if len(parts) < 2:
        return None
    wiki = ""
    if len(parts) >= 5:
        tail = parts[4].strip()
        if tail.startswith("#"):
            wiki = tail[1:]
        elif tail.isdigit():
            wiki = tail  # 兼容无 # 前缀的纯数字锚点
    return {
        "seq": parts[0],
        "name": parts[1],
        "unit": parts[2] if len(parts) >= 3 else "",
        "expr": parts[3] if len(parts) >= 4 else "",
        "wiki": wiki,
    }


def has_expr(key):
    parts = str(key).split(":")
    return len(parts) >= 4 and len(parts[3]) > 0


def wiki_url(key):
    info = parse_metric_key(key)
    if info and info["wiki"]:
        return WIKI_BASE + info["wiki"]
    return ""


def topic_display(topic):
    """topic 键形如 "01:cpu"，剥掉序号前缀做展示名。"""
    t = str(topic)
    if len(t) > 3 and t[2] == ":" and t[:2].isdigit():
        return t[3:]
    return t


# ---------------------------------------------------------------- 单位格式化（对齐参考实现 format_by_key/format_size/format_unixtime）

def format_size(size, unit):
    size_unit = {0: "", 1: "B", 2: "KB", 3: "MB", 4: "GB", 5: "TB", 6: "PB"}
    n = 0
    for power, ut in size_unit.items():
        if unit == ut:
            n = power
            break
    while size > 1024 and n < 6:
        size /= 1024.0
        n += 1
    return "{0:.2f}{1}".format(size, size_unit[n])


def format_big_number(data):
    """大数加千分位。带小数的值在 py3 下 `'{:,}'.format(str)` 必抛 ValueError，
    与参考实现一致走 except 返回原值（保留该怪癖以对齐线上展示口径）。"""
    try:
        result = str(data).strip()
        if "." in result:
            tmp = "{:.2f}".format(float(result))
            return "{:,}".format(tmp)  # str 不支持 , 格式化 → 必抛 → 返回原值
        return "{:,}".format(int(result))
    except (TypeError, ValueError):
        return str(data)


def format_unixtime(data):
    try:
        return datetime.fromtimestamp(float(data)).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError, OverflowError):
        return str(data)


def format_by_key(value, key=""):
    """按指标键单位格式化值（对齐参考实现 format_by_key）。"""
    parts = str(key).split(":")
    if len(parts) < 3:
        return format_big_number(value)
    unit = parts[2]
    try:
        if unit == "NO_FORMAT":
            return str(value)
        if unit.endswith("B"):
            return format_size(float(value), unit)
        if unit in ("A_HREF", "A_TARGET"):
            return str(value)  # markdown 报告不产 html 锚点，原样输出
        if unit == "UNIXTIME":
            return format_unixtime(value)
        if unit == "FLOAT":
            return "{0:.2f}".format(float(value))
    except (TypeError, ValueError):
        return str(value)
    return "{0}{1}".format(format_big_number(value), unit)


# ---------------------------------------------------------------- 表达式解码（对齐参考实现 get_comp_expr）

def _apply_comp_dict(expr):
    for k, v in COMP_DICT:
        expr = expr.replace(k, v)
    return expr


def decode_expr(value, key, now=None):
    """指标值 + 指标键 → 解码后的比较表达式；无表达式返回空串。

    数值分支会把带引号的纯数字阈值去引号（参考实现的 re.sub 行为）；
    字符串分支保留引号做字符串比较。替换顺序 WRAPDATA_ 先于 WRAPDATA、
    DATA_ 先于 DATA，与参考实现一致（顺序错了会把 `_` 残留在值后面）。

    无占位符扩展：参考实现中表达式一律显式写 DATA_/WRAPDATA 占位（全仓无反例），
    裸表达式（如 `lt_95`）在参考实现里解码为 "<95"，eval 必然 SyntaxError 恒告警，
    无判别意义。本实现约定：原表达式不含 DATA/WRAPDATA 占位时，把指标值前置到
    表达式头部（`32.5 < 95`），使任务样例键 `01:cpu_idle::lt_95:9744` 语义成立。
    对真实 auto-check 指标键（全部带占位符）行为与参考实现完全一致。
    """
    parts = str(key).split(":")
    if len(parts) < 4 or len(parts[3]) == 0:
        return ""
    raw = parts[3]
    expr = _apply_comp_dict(raw)
    clean = str(value).replace(",", "")
    has_placeholder = "DATA" in raw
    try:
        if "." in clean:
            numeric = float(clean)
        else:
            numeric = int(clean)
        expr = expr.replace("WRAPDATA_", str(numeric) + " ")
        expr = expr.replace("WRAPDATA", str(numeric))
        expr = expr.replace("DATA_", str(numeric) + " ")
        expr = expr.replace("DATA", str(numeric))
        expr = re.sub(r'"(\d+\.?\d*)"', r"\1", expr)
        if not has_placeholder:
            expr = str(numeric) + " " + expr
    except (ValueError, TypeError):
        expr = expr.replace("WRAPDATA_", "\"" + str(value) + "\" ")
        expr = expr.replace("WRAPDATA", "\"" + str(value) + "\"")
        expr = expr.replace("DATA_", str(value) + " ")
        expr = expr.replace("DATA", str(value))
        if not has_placeholder:
            expr = "\"" + str(value) + "\" " + expr
    if now is None:
        now = datetime.now()
    cur = (now - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    expr = expr.replace("CURTIME30", "\"" + cur + "\" ")
    return expr


# ---------------------------------------------------------------- 安全求值器（递归下降，禁 eval/exec/compile）

class ExprError(Exception):
    """表达式词法/语法/类型错误。调用方捕获后按告警保守处理。"""


_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_CMP_OPS = ("<", "<=", ">", ">=", "==", "!=")


def _tokenize(text):
    tokens = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if c == "\"":
            j = i + 1
            while j < n and text[j] != "\"":
                j += 1
            if j >= n:
                raise ExprError("字符串未闭合")
            tokens.append(("str", text[i + 1:j]))
            i = j + 1
            continue
        if c.isdigit() or (c == "." and i + 1 < n and text[i + 1].isdigit()):
            m = _NUM_RE.match(text, i)
            lit = m.group(0)
            tokens.append(("num", float(lit) if "." in lit else int(lit)))
            i = m.end()
            continue
        two = text[i:i + 2]
        if two in ("==", "!=", "<=", ">="):
            tokens.append(("op", two))
            i += 2
            continue
        if c in "<>":
            tokens.append(("op", c))
            i += 1
            continue
        if c in "()":
            tokens.append(("paren", c))
            i += 1
            continue
        if c == "-":
            tokens.append(("op", "u-"))
            i += 1
            continue
        m = _WORD_RE.match(text, i)
        if m:
            word = m.group(0)
            if word in ("and", "or"):
                tokens.append(("logic", word))
            elif word == "abs" and text[m.end():].lstrip().startswith("("):
                tokens.append(("func", "abs"))
            else:
                # 任何白名单外的标识符（含 DATA_ne_0 解码残留的 _0、未解析的变量名）
                # 都拒绝求值 → 由上层按告警保守处理，对齐参考实现 eval 异常→True
                raise ExprError("不支持的标识符: %s" % word)
            i = m.end()
            continue
        raise ExprError("无法识别的字符: %r" % c)
    return tokens


def _compare(v, op, r):
    if op in ("<", "<=", ">", ">="):
        # 序比较要求同为数值或同为字符串；数字比字符串在参考实现 eval 里抛
        # TypeError → 告警，这里显式拒绝（bool 是 int 子类，一并排除）
        v_num = isinstance(v, (int, float)) and not isinstance(v, bool)
        r_num = isinstance(r, (int, float)) and not isinstance(r, bool)
        v_str = isinstance(v, str)
        r_str = isinstance(r, str)
        if not ((v_num and r_num) or (v_str and r_str)):
            raise ExprError("序比较类型不一致: %r %s %r" % (v, op, r))
        if op == "<":
            return v < r
        if op == "<=":
            return v <= r
        if op == ">":
            return v > r
        return v >= r
    if op == "==":
        return v == r
    return v != r


class _Parser:
    """文法：or := and ("or" and)* ; and := cmp ("and" cmp)* ;
    cmp := unary (cmpop unary)? ; unary := "-" unary | primary ;
    primary := NUM | STR | "(" or ")" | "abs" "(" or ")" """

    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0

    def _peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def _next(self):
        t = self._peek()
        if t is None:
            raise ExprError("表达式意外结束")
        self.i += 1
        return t

    def parse(self):
        v = self._or()
        if self.i != len(self.toks):
            raise ExprError("表达式有多余内容")
        return v

    def _or(self):
        v = self._and()
        while self._peek() == ("logic", "or"):
            self._next()
            r = self._and()
            v = bool(v) or bool(r)  # 短路：bool(v) 为真时不求值 bool(r)
        return v

    def _and(self):
        v = self._cmp()
        while self._peek() == ("logic", "and"):
            self._next()
            r = self._cmp()
            v = bool(v) and bool(r)
        return v

    def _cmp(self):
        v = self._unary()
        t = self._peek()
        if t is not None and t[0] == "op" and t[1] in _CMP_OPS:
            self._next()
            r = self._unary()
            nxt = self._peek()
            if nxt is not None and nxt[0] == "op" and nxt[1] in _CMP_OPS:
                raise ExprError("不支持比较链")
            return _compare(v, t[1], r)
        return v

    def _unary(self):
        t = self._peek()
        if t == ("op", "u-"):
            self._next()
            v = self._unary()
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise ExprError("负号只能作用于数值")
            return -v
        return self._primary()

    def _primary(self):
        t = self._next()
        kind, val = t
        if kind in ("num", "str"):
            return val
        if t == ("paren", "("):
            v = self._or()
            if self._next() != ("paren", ")"):
                raise ExprError("缺少右括号")
            return v
        if t == ("func", "abs"):
            if self._next() != ("paren", "("):
                raise ExprError("abs 后缺少左括号")
            v = self._or()
            if self._next() != ("paren", ")"):
                raise ExprError("abs 后缺少右括号")
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise ExprError("abs 只接受数值")
            return abs(v)
        raise ExprError("意外标记: %r" % (t,))


def safe_eval(expr):
    """安全求值解码后的表达式；任何词法/语法/类型错误抛 ExprError。"""
    tokens = _tokenize(expr)
    if not tokens:
        raise ExprError("空表达式")
    return _Parser(tokens).parse()


def check_by_key(value, key, now=None):
    """判定指标值是否告警（安全复刻参考实现 check_by_key）。

    参考实现：表达式为空 → False；eval 异常（语法错/类型错/未定义名）→ True
    （保守视为告警）。本实现用 safe_eval 复刻同样的保守语义，全程不触碰 eval。
    """
    expr = decode_expr(value, key, now=now)
    if not expr:
        return False
    try:
        return bool(safe_eval(expr))
    except ExprError:
        return True
    except Exception:  # 防御：任何意外都按告警保守处理，与参考 except 行为一致
        return True


def human_threshold(key):
    """阈值人读（对齐参考实现 format_key：表达式数字按单位格式化），如 `值 > 3.00GB`。

    与 decode_expr 的无占位符扩展对应：裸表达式（如 `lt_95`）补 `值` 前缀，
    展示为 `值 < 95`。
    """
    parts = str(key).split(":")
    if len(parts) < 4 or len(parts[3]) == 0:
        return ""
    raw = parts[3]
    prefix = "" if "DATA" in raw else "值 "
    disp = raw.replace("CURTIME30", "_quot_当前时间-30分钟_quot_")
    expr = _apply_comp_dict(disp)
    expr = expr.replace("WRAPDATA_", "值 ").replace("WRAPDATA", "值")
    expr = expr.replace("DATA_", "值 ").replace("DATA", "值")
    expr = re.sub(r"(\d+\.?\d*)", lambda m: format_by_key(m.group(0), key), expr)
    expr = re.sub(r"(<=|>=|==|!=|<|>) ?", r"\1 ", expr)  # 运算符后补空格，人读友好
    return prefix + expr


# ---------------------------------------------------------------- 剧本库加载与匹配

def _norm_entry(entry, fallback_title=""):
    if not isinstance(entry, dict):
        return None
    steps = entry.get("steps") or []
    if not isinstance(steps, list):
        steps = []
    return {
        "title": entry.get("title") or fallback_title,
        "severity_hint": entry.get("severity_hint") or "",
        "steps": [str(s) for s in steps],
        "source": entry.get("_source", ""),
    }


def load_playbook_layer(path, kind, warnings):
    """加载可选剧本/指标层。文件缺失 → 静默返回 None（该层跳过）；
    存在但解析失败 → 记 warning 后跳过。返回统一 list[entry]。"""
    p = Path(path) if path else None
    if p is None or not p.is_file():
        return None
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        warnings.append("%s 文件解析失败，跳过该层: %s (%s)" % (kind, p, e))
        return None
    entries = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and isinstance(data.get("playbooks"), list):
        items = data["playbooks"]
    elif isinstance(data, dict) and isinstance(data.get("metrics"), dict):
        items = [{"metric_names": [k], **(v if isinstance(v, dict) else {})}
                 for k, v in data["metrics"].items()]
    elif isinstance(data, dict):
        items = [{"metric_names": [k], **(v if isinstance(v, dict) else {})}
                 for k, v in data.items()]
    else:
        warnings.append("%s 文件结构不识别，跳过该层: %s" % (kind, p))
        return None
    for it in items:
        if not isinstance(it, dict):
            continue
        names = it.get("metric_names") or it.get("names") or []
        if isinstance(names, str):
            names = [names]
        e = _norm_entry(it)
        if e is not None:
            e["metric_names"] = [str(x) for x in names]
            entries.append(e)
    return entries


def match_playbook(key, custom, metrics_layer, common):
    """返回 (entry, source_label)。优先级：--playbooks 精确 > --metrics 精确 >
    --common 关键词 contains > 兜底。common 命中取第一条（剧本库顺序即优先级）。"""
    info = parse_metric_key(key)
    name = (info or {}).get("name", str(key))
    name_l = name.lower()
    expr_l = str((info or {}).get("expr", "")).lower()
    decoded_l = decode_expr("$V", key).lower()

    for e in custom or []:
        if name in (e.get("metric_names") or []):
            return e, "playbooks(精确)"
    for e in metrics_layer or []:
        if name in (e.get("metric_names") or []):
            if e["steps"]:
                return e, "metrics(精确)"
            # 只有说明没有步骤：沿用其标题/严重度，步骤继续向下找
            tail, tail_src = _match_common(name_l, expr_l, decoded_l, common)
            if tail is None:
                tail, tail_src = _fallback_entry(key, name), "fallback"
            merged = dict(tail)
            merged["title"] = e["title"] or tail["title"]
            merged["severity_hint"] = e["severity_hint"] or tail["severity_hint"]
            return merged, tail_src + "+metrics说明"
    hit, src = _match_common(name_l, expr_l, decoded_l, common)
    if hit is not None:
        return hit, src
    return _fallback_entry(key, name), "fallback"


def _match_common(name_l, expr_l, decoded_l, common):
    hay = " ".join(x for x in (name_l, expr_l, decoded_l) if x)
    for e in common or []:
        for kw in e.get("_keywords", []):
            if kw and kw in hay:
                return e, "common(%s)" % kw
    return None, ""


def _fallback_entry(key, name):
    return {
        "title": "通用处置兜底",
        "severity_hint": "",
        "steps": list(FALLBACK_STEPS),
        "source": "fallback",
        "metric_names": [],
        "_raw_key": key,
        "_name": name,
    }


def load_common_playbooks(path, warnings):
    """加载通用剧本库（关键字小写 contains 匹配）。缺失/损坏只警告不阻断。"""
    p = Path(path) if path else None
    if p is None or not p.is_file():
        warnings.append("通用剧本库缺失，全部走兜底步骤: %s" % p)
        return None
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        warnings.append("通用剧本库解析失败，全部走兜底步骤: %s (%s)" % (p, e))
        return None
    items = data.get("playbooks", []) if isinstance(data, dict) else []
    entries = []
    for it in items:
        if not isinstance(it, dict):
            continue
        kws = [str(k).lower() for k in (it.get("match_keywords") or [])]
        e = _norm_entry(it, fallback_title=it.get("id", ""))
        if e is not None:
            e["metric_names"] = []
            e["_keywords"] = kws
            entries.append(e)
    return entries


# ---------------------------------------------------------------- 报告摄取与告警扫描

class ReportFileError(Exception):
    pass


def _read_json_file(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def parse_report_blocks(data, source_name, warnings):
    """从一个报告 JSON 提取 auto-check 主机块；结构不识别抛 ReportFileError。"""
    if not isinstance(data, dict) or not data:
        raise ReportFileError("顶层不是非空 JSON 对象")
    blocks = []
    for block_key, block in data.items():
        bdata = block.get("data") if isinstance(block, dict) else None
        if not isinstance(bdata, dict):
            warnings.append("跳过无法识别的块 %s（%s）: 缺少 data 对象" % (block_key, source_name))
            continue
        btype, _, host = str(block_key).partition("_")
        basic = bdata.get("basic")
        topics = bdata.get("topics")
        blocks.append({
            "key": str(block_key),
            "type": btype,
            "host": host or btype,
            "version": block.get("version", "") if isinstance(block, dict) else "",
            "report_time": block.get("report_time", "") if isinstance(block, dict) else "",
            "basic": basic if isinstance(basic, dict) else {},
            "topics": topics if isinstance(topics, dict) else {},
            "source": source_name,
        })
    if not blocks:
        raise ReportFileError("未找到任何 {type}_{hostname} 主机块")
    return blocks


def _iter_metric_pairs(row):
    """展开一行 (键, 值)。带表达式的键按自身判定；无表达式的 dict 值（如
    tcpconnection 子表）下钻一层按子指标键判定——覆盖参考实现不下钻的盲区。"""
    for k, v in row.items():
        if has_expr(k):
            yield k, v
        elif isinstance(v, dict):
            for k2, v2 in v.items():
                yield k2, v2


def _row_label(row, alerted_keys):
    """行标识：取行内首个无表达式的信息列（如 01:mount），便于多行 topic 定位。"""
    for k, v in row.items():
        if k in alerted_keys or not isinstance(v, (str, int, float)):
            continue
        if has_expr(k):
            continue
        return format_by_key(v, k)
    return ""


def scan_block(block, custom, metrics_layer, common, now=None):
    """扫描一个主机块，返回 (alerts, topics_scanned)。"""
    alerts = []

    def _check(k, v, section, section_disp, row=None, alerted=None):
        if not has_expr(k):
            return
        if check_by_key(v, k, now=now):
            info = parse_metric_key(k)
            name = info["name"] if info else str(k)
            entry, source = match_playbook(k, custom, metrics_layer, common)
            steps = entry.get("steps") or []
            if entry.get("source") == "fallback":
                steps = [s.replace("{host}", block["host"]).replace("{name}", name)
                         for s in steps]
            expr = decode_expr(v, k, now=now)
            parse_failed = False
            try:
                safe_eval(expr)
            except ExprError:
                parse_failed = True
            except Exception:
                parse_failed = True
            alerts.append({
                "block": block["key"],
                "type": block["type"],
                "host": block["host"],
                "section": section,
                "section_disp": section_disp,
                "row_label": _row_label(row, alerted or set()) if row else "",
                "key": k,
                "name": name,
                "raw_value": v,
                "value": format_by_key(v, k),
                "threshold": human_threshold(k),
                "wiki": wiki_url(k),
                "severity": entry.get("severity_hint") or "warn",
                "playbook_title": entry.get("title") or "",
                "playbook_steps": steps,
                "playbook_source": source,
                "expr": expr,
                "expr_raw": (info or {}).get("expr", ""),
                "parse_failed": parse_failed,
            })
            if alerted is not None:
                alerted.add(k)

    for k, v in block["basic"].items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                _check(k2, v2, "basic", "basic（基本信息）")
        else:
            _check(k, v, "basic", "basic（基本信息）")

    topics_scanned = 0
    for topic, rows in block["topics"].items():
        if not isinstance(rows, list):
            continue
        topics_scanned += 1
        disp = topic_display(topic)
        for row in rows:
            if not isinstance(row, dict):
                continue
            alerted = set()
            for k, v in _iter_metric_pairs(row):
                _check(k, v, topic, "topic %s（%s）" % (disp, topic), row=row, alerted=alerted)
    return alerts, topics_scanned


# ---------------------------------------------------------------- 报告渲染与 CLI

def render_report(blocks, all_alerts, files_total, warnings, out_text=True):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("# auto-check 巡检告警处置引导报告")
    lines.append("")
    lines.append("> **【待复核】** 本报告由 06_autocheck_triage 自动生成，处置步骤需运维人员复核并评估后再执行。")
    lines.append("> 生成时间：%s" % now)
    sources = []
    seen = set()
    for b in blocks:
        if b["source"] not in seen:
            seen.add(b["source"])
            sources.append(b["source"])
    lines.append("> 数据来源：%s（共 %d 个文件，解析出 %d 个主机块）"
                 % ("、".join(sources) if sources else "-", files_total, len(blocks)))
    lines.append("")
    if not all_alerts:
        lines.append("**本次巡检无告警项。**")
    by_block = {}
    for a in all_alerts:
        by_block.setdefault(a["block"], []).append(a)
    idx = 0
    for b in blocks:
        items = by_block.get(b["key"], [])
        if not items:
            continue
        meta = ["块 %s" % b["key"]]
        if b["version"]:
            meta.append("版本 %s" % b["version"])
        if b["report_time"]:
            meta.append("巡检时间 %s" % b["report_time"])
        lines.append("## [%s] %s（%s）" % (b["type"], b["host"], " · ".join(meta)))
        lines.append("")
        for a in items:
            idx += 1
            lines.append("### %d. [%s] %s = %s" % (idx, a["severity"], a["name"], a["value"]))
            loc = a["section_disp"]
            if a["row_label"]:
                loc += " · 行：%s" % a["row_label"]
            lines.append("- 所属：%s" % loc)
            lines.append("- 当前值：%s（原始值：%s）" % (a["value"], a["raw_value"]))
            if a["threshold"]:
                lines.append("- 阈值：%s" % a["threshold"])
            lines.append("- 严重度：%s" % a["severity"])
            lines.append("- WIKI：%s" % (a["wiki"] if a["wiki"] else "无"))
            if a["parse_failed"]:
                lines.append("- 注意：预警表达式无法安全解析（原表达式 `%s`），按告警保守处理，请人工确认是否真告警"
                             % a["expr_raw"])
            title = a["playbook_title"] or "未命名剧本"
            lines.append("- 处置步骤（剧本：%s · 来源 %s）：" % (title, a["playbook_source"]))
            for i, s in enumerate(a["playbook_steps"], 1):
                lines.append("  %d. %s" % (i, s))
            lines.append("")
    if warnings:
        lines.append("## 说明与跳过项")
        lines.append("")
        for w in warnings:
            lines.append("- %s" % w)
        lines.append("")
    return "\n".join(lines)


def _collect_files(args):
    files = []
    for r in (args.report or []):
        files.append((Path(r), True))
    if args.dir:
        d = Path(args.dir)
        if not d.is_dir():
            patrol_lib.stop("巡检报告目录不存在: %s" % d)
        files.extend((p, False) for p in sorted(d.glob("*.json")))
    if not files:
        patrol_lib.stop("未提供输入：用 --report 指定巡检 JSON 文件，或 --dir 指定报告目录")
    return files


def cmd_triage(args):
    warnings = []
    files = _collect_files(args)

    blocks = []
    for path, explicit in files:
        if not path.is_file():
            patrol_lib.stop("巡检报告文件不存在: %s（请确认 --report 路径）" % path)
        try:
            data = _read_json_file(path)
            blocks.extend(parse_report_blocks(data, path.name, warnings))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
            warnings.append("文件 JSON 解析失败跳过: %s (%s)" % (path, e))
        except ReportFileError as e:
            warnings.append("文件结构不识别跳过: %s (%s)" % (path, e))
    if not blocks:
        gap = ("所有输入均无法识别为 auto-check 巡检结构"
               "（需形如 {type_hostname: {version, report_time, data: {basic, topics}}}），"
               "请确认 --report/--dir 指向 auto-check json 产物目录")
        patrol_lib.stop(gap, warnings=warnings)

    custom = load_playbook_layer(args.playbooks, "autocheck_playbooks", warnings)
    metrics_layer = load_playbook_layer(args.metrics, "autocheck_metrics", warnings)
    common = load_common_playbooks(args.common, warnings)

    all_alerts = []
    topics_total = 0
    for b in blocks:
        alerts, n_topics = scan_block(b, custom, metrics_layer, common)
        all_alerts.extend(alerts)
        topics_total += n_topics

    by_severity = {}
    for a in all_alerts:
        by_severity[a["severity"]] = by_severity.get(a["severity"], 0) + 1
    by_severity = {k: by_severity[k] for k in sorted(by_severity)}

    report = render_report(blocks, all_alerts, len(files), warnings)
    out_path = patrol_lib.write_text(args.out, report)

    print("已解析 %d 个文件 / %d 个主机块 / %d 个 topic，发现 %d 个告警项"
          % (len(files), len(blocks), topics_total, len(all_alerts)))
    patrol_lib.emit({
        "files": len(files),
        "hosts": len(blocks),
        "topics": topics_total,
        "alert_items": len(all_alerts),
        "by_severity": by_severity,
        "report": str(out_path),
        "warnings": warnings,
    })
    return 0


def build_parser():
    root = patrol_lib.ROOT
    p = argparse.ArgumentParser(prog="06_autocheck_triage.py",
                                description="auto-check 巡检报告告警分诊与处置引导")
    sub = p.add_subparsers(dest="command")
    t = sub.add_parser("triage", help="解析巡检报告并生成处置引导")
    t.add_argument("--report", action="append", default=None,
                   help="巡检报告 JSON，可重复")
    t.add_argument("--dir", default=None, help="报告目录（收 *.json）")
    t.add_argument("--metrics",
                   default=str(root / "references" / "autocheck_metrics.json"),
                   help="auto-check 指标目录 JSON（缺文件静默跳过该层）")
    t.add_argument("--playbooks",
                   default=str(root / "references" / "autocheck_playbooks.json"),
                   help="auto-check 专属处置剧本 JSON（缺文件静默跳过该层）")
    t.add_argument("--common",
                   default=str(root / "references" / "playbooks" / "common_playbooks.json"),
                   help="通用剧本库 JSON")
    t.add_argument("--out", default=str(patrol_lib.WORK_DIR / "autocheck" / "guide.md"),
                   help="处置引导报告输出路径")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    if args.command != "triage":
        parser.print_help()
        return 1
    return cmd_triage(args)


if __name__ == "__main__":
    sys.exit(main())
