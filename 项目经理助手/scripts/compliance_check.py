#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
标书 / 正式文档 合规检查规则引擎
====================================
用途：写入正式文档（报告/标准/方案/合同/对外交付件）前，自动扫描合规风险。
最高优先级目标：把"引用未定稿标准"一处不漏地揪出来（查全率优先，宁可误报）。

检测项：
  A. 未定稿/在编标准状态词（高危）—— 报批稿/征求意见稿/送审稿/草案/意见反馈稿/在编…
  B. 占位或缺年份的标准号（高危/中危）—— GB/T XXXXX、GB/T ××××—××××、无年份的 GB/T 数字串
  C. 国密算法标准号配对（提示人工核对）—— SM2/3/4/9 ↔ GM/T 0003/0004/0002/0044
  D. 法规名称现行有效性（中危）—— 不在现行有效白名单的《…法/办法/条例/规定》标"待核实"

用法：
  python compliance_check.py 文档.docx
  python compliance_check.py 文档.md --json
  type 文档.txt | python compliance_check.py -          (从 stdin 读)

退出码：发现高危(A/B-高危)问题时返回 2，仅中危/提示返回 1，干净返回 0
（方便接 CI / eval：高危=合规事故，必须人工处理）

依赖：仅标准库。.docx 走 zipfile+正则提取（沿用既有 docx 处理经验，免 python-docx）。
"""

import argparse
import json
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================
# 知识库：现行有效法规白名单（仅列网络安全/数据领域常用，按需扩充）
# 不在白名单 ≠ 一定失效，而是"需人工确认现行有效"
# ============================================================
VALID_REGULATIONS = {
    "中华人民共和国网络安全法", "网络安全法",
    "中华人民共和国数据安全法", "数据安全法",
    "中华人民共和国个人信息保护法", "个人信息保护法",
    "中华人民共和国密码法", "密码法",
    "网络安全审查办法",
    "关键信息基础设施安全保护条例",
    "网络数据安全管理条例",
    "数据安全管理办法",
    "网络安全等级保护条例",
}

# 国密算法 ↔ 正确 GM/T 标准号（已发布）
GM_PAIRS = {
    "SM2": "GM/T 0003",   # 椭圆曲线公钥密码
    "SM3": "GM/T 0004",   # 密码杂凑
    "SM4": "GM/T 0002",   # 分组密码
    "SM9": "GM/T 0044",   # 标识密码
}

# A. 未定稿 / 在编状态词（高危）。"草案"易误报但宁可报。
DRAFT_WORDS = [
    "报批稿", "征求意见稿", "送审稿", "意见反馈稿", "讨论稿", "送审版",
    "在编标准", "在编", "报批", "送审", "草案", "征求意见",
]
# 例外：这些词里含"草案/送审"等但属正常用语，命中后降级提示而非高危
SOFT_CONTEXT = ["方案草案", "设计草案", "初步草案"]


def extract_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    if path.lower().endswith(".docx"):
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        # 段落 </w:p> 转换行，再剥标签
        xml = xml.replace("</w:p>", "\n")
        return re.sub(r"<[^>]+>", "", xml)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def snippet(text: str, pos: int, width: int = 30) -> str:
    s = max(0, pos - width)
    e = min(len(text), pos + width)
    return text[s:e].replace("\n", " ").strip()


def check(text: str) -> list:
    findings = []

    # --- A. 未定稿 / 在编状态词（先收集，再抑制被长词包含的短词命中，避免"报批稿"+"报批"重复报）---
    a_hits = [(m.start(), m.end(), w)
              for w in DRAFT_WORDS for m in re.finditer(re.escape(w), text)]
    for s, e, w in a_hits:
        covered = any(s2 <= s and e <= e2 and (e2 - s2) > (e - s) for s2, e2, _ in a_hits)
        if covered:
            continue
        soft = any(sc in text[max(0, s-6):e+6] for sc in SOFT_CONTEXT)
        findings.append({
            "type": "A-未定稿标准状态词",
            "severity": "提示" if soft else "高危",
            "line": line_of(text, s),
            "hit": w,
            "context": snippet(text, s),
            "advice": "若指标准/规范文件，立即删除或改写为业务描述；"
                      + ("此处疑似普通方案用语，人工确认。" if soft else "禁止引用未定稿/在编标准。"),
        })

    # --- B1. 占位标准号 GB/T XXXXX / GB/T ××××—×××× ---
    for m in re.finditer(r"GB/?T?\s*[X×x]{3,}", text):
        findings.append({
            "type": "B-占位标准号", "severity": "高危",
            "line": line_of(text, m.start()), "hit": m.group(),
            "context": snippet(text, m.start()),
            "advice": "占位编号=未定稿标准的强信号，必须删除或换成已发布标准/业务描述。",
        })
    for m in re.finditer(r"GB/?T?\s*[×xX]{2,}\s*[—\-]\s*[×xX]{2,}", text):
        findings.append({
            "type": "B-占位标准号(年份占位)", "severity": "高危",
            "line": line_of(text, m.start()), "hit": m.group(),
            "context": snippet(text, m.start()),
            "advice": "形如 GB/T ××××—×××× 为未定稿占位，禁止出现在正式文档。",
        })
    # --- B2. 无年份的 GB/T 数字号（中危：可能省略年份，需补全核实） ---
    for m in re.finditer(r"GB/T\s*\d{3,6}(?!\d)(?!\s*[—\-]\s*\d{4})", text):
        findings.append({
            "type": "B-标准号缺发布年份", "severity": "中危",
            "line": line_of(text, m.start()), "hit": m.group().strip(),
            "context": snippet(text, m.start()),
            "advice": "补全发布年份（如 GB/T 22240-2020）并确认现行有效未废止。",
        })

    # --- C. 国密算法 ↔ GM/T 配对核对 ---
    sm_hits = {sm for sm in GM_PAIRS if re.search(sm, text)}
    gm_hits = set(re.findall(r"GM/T\s*\d{4}", text))
    gm_hits = {g.replace(" ", "").replace("GM/T", "GM/T ") for g in gm_hits}
    if sm_hits:
        for sm in sorted(sm_hits):
            correct = GM_PAIRS[sm]
            # 文中是否出现了"错配"——出现了别的 SM 的标准号但没出现本 SM 的
            if gm_hits and correct.replace(" ", "") not in {g.replace(" ", "") for g in gm_hits}:
                findings.append({
                    "type": "C-国密标准号配对", "severity": "中危",
                    "line": 0, "hit": sm,
                    "context": f"文中用到 {sm}，但未见其正确标准号 {correct}",
                    "advice": f"{sm} 对应已发布标准 {correct}，请核对引用是否正确。",
                })

    # --- D. 法规名称现行有效性 ---
    for m in re.finditer(r"《([^》]{2,40}?(法|办法|条例|规定|准则))》", text):
        name = m.group(1)
        if name not in VALID_REGULATIONS:
            findings.append({
                "type": "D-法规需核实现行有效", "severity": "中危",
                "line": line_of(text, m.start()), "hit": f"《{name}》",
                "context": snippet(text, m.start()),
                "advice": "确认该法规/办法为现行有效、名称准确、未被修订替代。",
            })

    sev_rank = {"高危": 0, "中危": 1, "提示": 2}
    findings.sort(key=lambda f: (sev_rank.get(f["severity"], 9), f["line"]))
    return findings


def print_report(findings: list, src: str):
    counts = {"高危": 0, "中危": 0, "提示": 0}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    print("\n" + "=" * 60)
    print(f"  标书/文档合规检查 —— {src}")
    print("=" * 60)
    print(f"  高危 {counts['高危']}  |  中危 {counts['中危']}  |  提示 {counts['提示']}")
    if not findings:
        print("  ✓ 未发现合规风险点（仍建议人工抽检引用）")
    print("-" * 60)
    for i, f in enumerate(findings, 1):
        loc = f"第{f['line']}行" if f["line"] else "全文"
        print(f"  [{i}] 【{f['severity']}】{f['type']}  ({loc})")
        print(f"      命中: {f['hit']}")
        print(f"      上下文: ...{f['context']}...")
        print(f"      建议: {f['advice']}")
    print("=" * 60 + "\n")


def main():
    ap = argparse.ArgumentParser(description="标书/正式文档合规检查规则引擎")
    ap.add_argument("file", help="文档路径(.docx/.md/.txt)，或 - 表示从 stdin 读")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    text = extract_text(args.file)
    findings = check(text)

    if args.json:
        print(json.dumps({"source": args.file, "findings": findings},
                         ensure_ascii=False, indent=2))
    else:
        print_report(findings, args.file)

    high = sum(1 for f in findings if f["severity"] == "高危")
    mid = sum(1 for f in findings if f["severity"] == "中危")
    sys.exit(2 if high else (1 if mid else 0))


if __name__ == "__main__":
    main()
