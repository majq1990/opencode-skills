#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建「项目工期初始化审核」35 列 xlsx（老表 schema 复刻）。
用法:
  python build_audit_xlsx.py --workdir <probe json 目录> [--since 2026-07-01] \
      [--docx-dirs <逗号分隔 docx 目录>] [--old-xlsx <6.26 老表路径>] [--out <输出 xlsx>]
数据源（先跑 probe_tables.mjs）:
  probe_duration.json / probe_suspend.json / probe_projects.json
规则:
  - 工期行: ztoa 工期表 JSON 直取（验收方式从 docx 扫描补）
  - 挂起行: 挂起表 JSON 直取 + rel.name 定级 + 主数据表(rel.sid)补进场/136时间
  - 挂起期间 = 开始 + 期限月数; 0 月占位(无类型且期限0)行删除
  - --old-xlsx 老表仅兜底填空（大区/区域/验收方式/日期/136 时间）
"""
import sys, os, json, io, re, glob, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from datetime import date
from dateutil.relativedelta import relativedelta
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from docx import Document

ap = argparse.ArgumentParser()
ap.add_argument("--workdir", default=os.path.join("D:/opencode/file", date.today().isoformat()))
ap.add_argument("--since", default="2026-07-01")
ap.add_argument("--docx-dirs", default=",".join([r"D:\opencode\file\2026-09-02", os.path.join("D:/opencode/file", date.today().isoformat())]))
ap.add_argument("--old-xlsx", default="")
ap.add_argument("--out", default="")
a = ap.parse_args()
OUT = a.out or os.path.join(a.workdir, "项目工期初始化审核.xlsx")

# ===== cid 映射（2026-09 值矩阵交叉验证，见 SKILL.md）=====
D = {"project":"69fc40831e6716810741b843","apply_no":"69fc3daa1e6716810741b7ce","level":"69fc41b81e6716810741b864",
     "base_init":"69fc410a1e6716810741b858","base_trial":"69fc41b81e6716810741b863","base_final":"69fc4126111e45dac897c958","base_one":"6a2a1c29964e268c286b7279",
     "enter":"69fc3bc11e6716810741b718","init_init":"6a043ae9111e45dac8984864","init_final":"6a043b99ac3fb911f275dcd1",
     "adj_init":"6a067fe71e67168107425bd0","adj_final":"6a067fe71e67168107425bd1",
     "final_init":"69fc3bc11e6716810741b71a","final_final":"69fc3bc11e6716810741b71b",
     "final_init2":"69fc3bc11e6716810741b71d","final_final2":"69fc3bc91e6716810741b72b",
     "sign_date":"6a390615416b923955e67bf8","region":"69fc40d0111e45dac897c94b",
     "applicant":"69fc30b91e6716810741b4b2","note":"69fc30b91e6716810741b4b9"}
S = {"project":"6a1808ba964e268c28697ebe","region":"6a0aa397416b923955e18975",
     "start":"69fc3c581e6716810741b750","end":"69fc3c581e6716810741b751","rel":"6a0aa776964e268c286826fa",
     "type":"6a0aa1e9964e268c28682672","reason":"69fc30c1111e45dac897c665",
     "period":"69fc30c1111e45dac897c667","upper":"6a0aa203964e268c2868267f","lower":"6a0aa203964e268c2868267e",
     "hist":"6a0add0a416b923955e19466","acc_days":"6a06efc6964e268c286801cb","applicant":"69fc30c1111e45dac897c663"}
# 交付项目主数据表
PC = {"enter":"629dc18f6f0dcb3b9b7cd74f","p136":"68d8d2015c2e9b88a20e4e23","r136":"68d8d2015c2e9b88a20e4e24",
      "enter_candidates":["629dc18f6f0dcb3b9b7cd74f","64bf43bfb84fb18ee3e762fc","65783bfab16612491956b843",
                          "65e9875f0a3edc60a8d28de8","67e64f0b6c077ddf2d8bad8a"],
      "big":"629dc18f6f0dcb3b9b7cd740","region":"629dc18f6f0dcb3b9b7cd741","name":"629dc18f6f0dcb3b9b7cd742"}

def load(n):
    p = os.path.join(a.workdir, n)
    if not os.path.exists(p):
        print(f"!! 缺 {p}（先跑 probe_tables.mjs）"); sys.exit(1)
    return json.load(open(p, encoding="utf-8"))

def parse_list(v):
    if isinstance(v, str) and v.strip().startswith("["):
        try:
            j = json.loads(v)
            return j if isinstance(j, list) else None
        except Exception: return None
    return v if isinstance(v, list) else None

def getv(row, cid):
    v = row.get(cid)
    if isinstance(v, str): return v.strip()
    if isinstance(v, (int, float)): return str(v)
    return ""

def first_name(row, cid):
    l = parse_list(row.get(cid))
    if l and isinstance(l[0], dict):
        return (l[0].get("fullname") or l[0].get("name") or "").strip()
    return ""

def strip_html(s): return re.sub(r"<[^>]+>", "\n", s or "")
def clean(s): return re.sub(r"\n{2,}", "\n", s or "").strip()
def strip_level(s): return re.sub(r"^[SABCDE]\d+级[-—]\s*|^独立合同运维级[-—]\s*", "", s or "")
def level_of(name):
    m = re.match(r"^([SABCDE]\d+级|独立合同运维级)-", name or "")
    return m.group(1) if m else ""

# ===== 大区映射 =====
region2big = {}
FALLBACK = {"安徽区域":"东南大区","江西区域":"东南大区","浙江区域":"东南大区","福建区域":"东南大区",
    "江苏区域":"华中大区","河南区域":"华中大区","湖北区域":"华中大区","湖南区域":"华中大区",
    "山东区域":"华北一区","山西区域":"华北一区","内蒙古区域":"华北二区","北京区域":"华北二区","吉林区域":"华北二区","天津区域":"华北二区","辽宁区域":"华北二区",
    "广东区域":"华南大区","海南区域":"华南大区","宁夏区域":"西北大区","新疆区域":"西北大区","甘肃区域":"西北大区","青海区域":"西北大区",
    "贵州区域":"西南大区","重庆区域":"西南大区"}
rm_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "region_mapping.json")
if os.path.exists(rm_p):
    for k in json.load(open(rm_p, encoding="utf-8")):
        parts = k.split("/")
        if len(parts) == 2:
            region2big[parts[1].replace("（测试）", "")] = parts[0].replace("（测试）", "")
region2big.update(FALLBACK)

# ===== 验收方式（docx 扫描）=====
def cells_unique(row):
    seen = []
    for c in row.cells:
        t = c.text.strip()
        if not seen or seen[-1] != t: seen.append(t)
    return seen

def docx_accept_map(dirs):
    m = {}
    for d in dirs:
        for fp in glob.glob(os.path.join(d, "工期更新-*.docx")):
            try: doc = Document(fp)
            except Exception: continue
            if len(doc.tables) < 2: continue
            no = ""
            for r in doc.tables[1].rows:
                u = cells_unique(r); i = 0
                while i < len(u) - 1:
                    if u[i] == "申请编号": no = u[i+1]
                    if u[i] == "合同约定验收方式": m[no] = u[i+1]
                    i += 2
    return m

accept_map = docx_accept_map([d for d in a.docx_dirs.split(",") if d])
print(f"验收方式映射 {len(accept_map)} 条（docx 扫描）")

# ===== 数据 =====
dur_all = load("probe_duration.json")
sus_all = load("probe_suspend.json")
proj_all = load("probe_projects.json")
proj_by_sid = {p.get("rowid"): p for p in proj_all}

dur_rows = sorted([r for r in dur_all if str(r.get("ctime","")) >= a.since], key=lambda r: r.get("ctime",""))
sus_rows = sorted([r for r in sus_all if str(r.get("ctime","")) >= a.since], key=lambda r: r.get("ctime",""))
print(f"{a.since} 之后: 工期 {len(dur_rows)}, 挂起 {len(sus_rows)}")

# ===== 老表兜底（可选）=====
old_idx = {}
if a.old_xlsx and os.path.exists(a.old_xlsx):
    owb = load_workbook(a.old_xlsx, data_only=True)
    ows = owb.active
    for r in range(3, ows.max_row + 1):
        av = str(ows.cell(r, 1).value or "").strip()
        if not av: continue
        key = strip_level(av)
        rec = {"B": ows.cell(r,2).value, "C": ows.cell(r,3).value, "E": ows.cell(r,5).value,
               "L": ows.cell(r,12).value, "M": ows.cell(r,13).value, "N": ows.cell(r,14).value,
               "O": ows.cell(r,15).value, "P": ows.cell(r,16).value, "Q": ows.cell(r,17).value,
               "R": ows.cell(r,18).value, "S": ows.cell(r,19).value, "T": ows.cell(r,20).value, "U": ows.cell(r,21).value}
        old_idx.setdefault(key, rec)
    print(f"老表索引 {len(old_idx)} 项目")

def old_fill(key, col, cur):
    """老表兜底：cur 为空才填"""
    if cur not in ("", None): return cur
    rec = old_idx.get(key) or {}
    v = rec.get(col)
    if v in (None, "", "/"): return cur if cur not in (None,) else ""
    if isinstance(v, str) and v == "/": return cur
    import datetime as _dt
    if isinstance(v, _dt.datetime): return v.strftime("%Y-%m-%d")
    return v

# ===== 工作簿 =====
HEADERS_TOP = ["交付项目","所属大区","所属区域","申请人","合同约定验收方式","项目定级","工期基线",None,None,None,
    "是否调整工期","初验日期","终验日期","合同签订日期","进场日期","初验工期",None,"终验工期",None,"一次性验收终验工期",None,
    "试运行工期调整",None,"增加工期申请",None,None,"工期挂起",None,None,None,None,"审核意见",None,None,None]
HEADERS_SUB = [None]*6 + ["初验工期","试运行工期","终验工期","一次性验收周期",None]*5 + \
    ["136初始化应初验时间","工期调整后计划应初验时间","136初始化应终验时间","工期调整后计划应终验时间",
     "136初始化一次性应终验时间","工期调整后一次性计划应终验时间","试运行调整后月数(月)","试运行调整附件材料",
     "增加工期","增加天数","申请说明","挂起类型","挂起期限（月）","挂起上限（月）","挂起下限（月）","挂起原因详述",
     "大区意见","南北区意见","技术部意见","其他部门意见\n（研发、移动测量、采购）"]
MERGED = ["A1:A2","B1:B2","C1:C2","D1:D2","E1:E2","F1:F2","G1:J1","K1:K2","L1:L2","M1:M2","N1:N2","O1:O2",
    "P1:Q1","R1:S1","T1:U1","V1:W1","X1:Z1","AA1:AE1","AF1:AI1"]

wb = Workbook(); ws = wb.active; ws.title = "项目申请清单"
for c, h in enumerate(HEADERS_TOP, 1): ws.cell(1, c, h)
for c, h in enumerate(HEADERS_SUB, 1): ws.cell(2, c, h)
for rng in MERGED: ws.merge_cells(rng)
hf = Font(bold=True, size=11); hfill = PatternFill("solid", fgColor="DDEBF7")
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
thin = Side(border_style="thin", color="999999"); border = Border(left=thin, right=thin, top=thin, bottom=thin)
for rr in (1, 2):
    for c in range(1, 36):
        cell = ws.cell(rr, c); cell.font, cell.fill, cell.alignment, cell.border = hf, hfill, center, border
ws.row_dimensions[1].height = 24; ws.row_dimensions[2].height = 32

def write_row(ridx, vals):
    for c, v in enumerate(vals, 1):
        cell = ws.cell(ridx, c, v)
        cell.alignment = Alignment(vertical="top", wrap_text=True); cell.border = border

SLASH = "/"
r = 3
# ===== 工期行 =====
for row in dur_rows:
    no = getv(row, D["apply_no"]); proj = getv(row, D["project"]); level = getv(row, D["level"])
    accept = accept_map.get(no, "")
    key = strip_level(proj)
    accept = accept or (old_idx.get(key, {}).get("E") or "")
    is_one = "一次性" in accept
    region = getv(row, D["region"]); big = region2big.get(region, "") or (old_idx.get(key, {}).get("B") or "")
    p_init = getv(row, D["init_init"]); r_init = getv(row, D["init_final"])
    q_adj = getv(row, D["adj_init"]) or getv(row, D["final_init"]) or getv(row, D["final_init2"])
    s_adj = getv(row, D["adj_final"]) or getv(row, D["final_final"]) or getv(row, D["final_final2"])
    if is_one:
        P = Qv = R = Sv = SLASH
        T = r_init or SLASH
        U = ((s_adj or T) if r_init else SLASH)
    else:
        P = p_init or SLASH
        Qv = (q_adj or p_init) if (p_init or q_adj) else SLASH
        R = r_init or SLASH
        Sv = (s_adj or r_init) if (r_init or s_adj) else SLASH
        T = U = SLASH
    is_adjust = "是" if ((q_adj and q_adj != p_init) or (s_adj and s_adj != r_init)) else "否"
    note = clean(strip_html(getv(row, D["note"])).replace("\n", ""))
    vals = [f"{level}级-{proj}" if level else proj, big, region, first_name(row, D["applicant"]), accept, level,
            getv(row, D["base_init"]), getv(row, D["base_trial"]), getv(row, D["base_final"]), getv(row, D["base_one"]),
            is_adjust, old_fill(key,"L",""), old_fill(key,"M",""), getv(row, D["sign_date"]) or (old_idx.get(key,{}).get("N") or ""),
            getv(row, D["enter"]) or (old_idx.get(key,{}).get("O") or ""),
            P, Qv, R, Sv, T, U, "", "", "", "", note, "", "", "", "", "", "", "", "", ""]
    write_row(r, vals); r += 1

# ===== 挂起行 =====
dropped = 0
for row in sus_rows:
    typ = first_name(row, S["type"])
    period = getv(row, S["period"])
    if not typ and (not period or period == "0"):
        dropped += 1; continue  # 0月占位行丢弃
    proj = getv(row, S["project"]); region = getv(row, S["region"])
    rel = parse_list(row.get(S["rel"])) or []
    rel_name = (rel[0].get("name") or "").strip() if rel else ""
    rel_sid = rel[0].get("sid") if rel else ""
    proj_full = rel_name or proj
    level = level_of(proj_full)
    key = strip_level(proj_full)
    big = region2big.get(region, "") or (old_idx.get(key, {}).get("B") or "")
    prow = proj_by_sid.get(rel_sid, {})
    # 进场：多候选 cid（74f 为 None 时冗余字段可能存值），老表兜底
    enter = ""
    for cid in PC["enter_candidates"]:
        v = getv(prow, cid)
        if v: enter = v; break
    if not enter:
        ov = old_idx.get(key, {}).get("O")
        enter = ov.strftime("%Y-%m-%d") if hasattr(ov, "strftime") else (ov or "")
    # 136：老表(人工审核)优先 → 主数据兜底
    def pick136(col, mainval):
        ov = old_idx.get(key, {}).get(col)
        if hasattr(ov, "strftime"): return ov.strftime("%Y-%m-%d")
        if isinstance(ov, str) and ov.strip() not in ("", "/"): return ov.strip()
        return mainval or ""
    accept = old_idx.get(key, {}).get("E") or ""
    is_one = "一次性" in accept
    if is_one:
        Pcol = Qcol = Rcol = Scol = SLASH
        Tcol = pick136("T", getv(prow, PC["r136"])) or SLASH
        Ucol = Tcol
    else:
        Pcol = pick136("P", getv(prow, PC["p136"])) or SLASH
        Qcol = Pcol
        Rcol = pick136("R", getv(prow, PC["r136"])) or SLASH
        Scol = Rcol
        Tcol = Ucol = SLASH
    reason = clean(strip_html(getv(row, S["reason"])))
    start = getv(row, S["start"]); end = getv(row, S["end"])
    hist = getv(row, S["hist"]); acc = getv(row, S["acc_days"])
    extra = []
    if start and period.isdigit() and int(period) > 0:
        try:
            sd = date.fromisoformat(start)
            ed = sd + relativedelta(months=int(period))
            extra.append(f"挂起期间：{start} ~ {ed.isoformat()}（默认挂起{period}个月）")
        except Exception:
            extra.append(f"挂起期间：{start} ~ {end or '?'}")
    elif start or end:
        extra.append(f"挂起期间：{start or '?'} ~ {end or '?'}")
    if hist:
        extra.append(f"本项目历次挂起 {hist} 次，累计挂起 {acc or '?'} 天")
    ae = (reason + "\n" if reason else "") + "\n".join(extra)
    vals = [proj_full, big, region, first_name(row, S["applicant"]), accept, level,
            "", "", "", "", "否", old_fill(key,"L",""), old_fill(key,"M",""),
            old_fill(key,"N",""), enter,
            Pcol, Qcol, Rcol, Scol, Tcol, Ucol,
            "", "", "", "", "",
            typ, period, getv(row, S["upper"]), getv(row, S["lower"]), ae,
            "", "", "", ""]
    write_row(r, vals); r += 1
print(f"0月占位行已丢弃: {dropped}")

for col, w in {"A":32,"B":10,"C":10,"D":10,"E":18,"F":12,"G":8,"H":8,"I":8,"J":8,"K":10,"L":12,"M":12,"N":12,"O":12,
    "P":14,"Q":14,"R":14,"S":14,"T":14,"U":14,"V":10,"W":14,"X":10,"Y":10,"Z":28,"AA":22,"AB":10,"AC":10,"AD":10,
    "AE":60,"AF":20,"AG":20,"AH":20,"AI":20}.items():
    ws.column_dimensions[col].width = w

try:
    wb.save(OUT)
except PermissionError:
    OUT = OUT.replace(".xlsx", "_new.xlsx"); wb.save(OUT)
print(f"\n✅ 已写入: {OUT}  共 {r-3} 行 (工期 {len(dur_rows)} + 挂起 {r-3-len(dur_rows)})")
