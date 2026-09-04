"""星桥高级认证初版评分器。

输入：<workdir>/_extracted/**/text_only.txt
输出：_grading_starbridge_v1.json/.md/.csv

这是证据定位型初评：题干关键词会被过滤，文字/脚本用于定位，截图占位用于估计证据完整度。
最终分数仍需抽查 media/ 下的截图。
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from collections import OrderedDict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\星桥高级认证阅卷"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULES_PATH = os.path.join(BASE_DIR, "references", "reference_baseline_starbridge.json")

ITEMS = [
    ("S1-01", "ddcat 数据模型", "连接 exam 数据源/查看表数据", 2, 1, [r"exam(?:_accident)?", r"数据源|连接|表数据"]),
    ("S1-02", "ddcat 数据模型", "检查事故表字段", 1, 1, [r"roadName|roadId", r"reportTime|报案时间"]),
    ("S1-03", "ddcat 数据模型", "创建按道路统计的查询模型", 4, 1, [r"select|查询", r"count", r"roadName", r"group\s+by|分组", r"order\s+by|倒序|desc", r"limit\s*5|前\s*5", r"start_time|end_time|时间范围"]),
    ("S1-04", "ddcat 数据模型", "调试并查看查询结果", 2, 1, [r"运行结果|查询结果|调试", r"道路|roadName", r"数量|count"]),
    ("S1-05", "ddcat 数据模型", "配置 name/text/value 数据转换", 3, 1, [r"转换脚本|脚本", r"name", r"text", r"value"]),
    ("S1-06", "ddcat 数据模型", "生成目标接口", 2, 1, [r"/api/data-model|接口地址|生成接口", r"top5|exam"]),
    ("S1-07", "ddcat 数据模型", "应用审核/接口授权", 2, 1, [r"应用审核|审核", r"授权申请|接口授权|client"]),
    ("S1-08", "ddcat 数据模型", "OAuth 前置脚本", 2, 1, [r"tokenStore|token", r"clientId|clientSecret", r"Bearer|Authorization"]),
    ("S1-09", "ddcat 数据模型", "时间范围验证接口", 2, 1, [r"postman|星桥 API|验证", r"2022-10-01|2022-12-18|start_time|end_time", r"hasError|totalCount|result"]),

    ("S2-01", "MIS 接口代理", "注册 MIS 统计接口及 query 参数", 2, 1, [r"getgeneraldata", r"dateType|dateValue", r"token"]),
    ("S2-02", "MIS 接口代理", "认证前置脚本获取 token", 3, 1, [r"gettokenbyhumanid|humanID|humanId", r"tokenStore|token", r"setQueryParam|query"]),
    ("S2-03", "MIS 接口代理", "解析 resultInfo.data.generaldata", 4, 1, [r"resultInfo", r"generaldata", r"INSTNUM|REPORTNUM|ARCHIVENUM|ARCHIVERATE"]),
    ("S2-04", "MIS 接口代理", "转换立案/上报/结案/结案率", 4, 1, [r"立案数|INSTNUM", r"上报数|REPORTNUM", r"结案数|ARCHIVENUM", r"结案率|ARCHIVERATE", r"name", r"text", r"value"]),
    ("S2-05", "MIS 接口代理", "配置接口代理", 2, 1, [r"接口代理|代理配置|proxy|upstream", r"代理地址|接口地址"]),
    ("S2-06", "MIS 接口代理", "申请应用授权", 2, 1, [r"应用授权|授权申请|授权成功", r"clientId|应用"]),
    ("S2-07", "MIS 接口代理", "验证代理接口返回", 3, 2, [r"postman|验证|调用", r"Bearer|token", r"立案数|上报数|结案数|结案率|hasError|totalCount"]),

    ("S3-01", "案卷上报调度", "注册上报接口/平台编码", 2, 2, [r"uprecreport|案卷上报|上报接口", r"senderCode|平台编码", r"UP_REC_REPORT|actionType"]),
    ("S3-02", "案卷上报调度", "映射 exam_rec 案卷字段", 4, 1, [r"exam_rec|task_num|event_desc", r"coordinate_x|coordinate_y|坐标", r"district|street|community|区域", r"rec_type|event_type|main_type|sub_type", r"event_level|create_time|上报时间"]),
    ("S3-03", "案卷上报调度", "查询并封装多媒体", 4, 2, [r"exam_media|relationId", r"mediaServer|mediaPath|mediaName", r"mediaURL|媒体路径", r"mediaType|mediaUsage|mediaNum"]),
    ("S3-04", "案卷上报调度", "前置脚本组装 form-urlencoded 请求", 4, 1, [r"request\.getBody|读取.*data|oldData", r"newData|组装|字段映射", r"medias|多媒体", r"form-urlencoded|setHeader|setBody"]),
    ("S3-05", "案卷上报调度", "调试并验证案件生成", 2, 2, [r"运行接口|调试|上报成功", r"recID|taskNum|success", r"综合查询|案件可查|城管系统"]),
    ("S3-06", "案卷上报调度", "配置增量查询任务", 2, 5, [r"查询任务|任务配置|定时任务", r"exam_rec|增量|新数据"]),
    ("S3-07", "案卷上报调度", "配置 5 分钟调度", 2, 1, [r"5\s*分钟|5min|300", r"调度|日志|多次"]),

    ("S4-01", "多媒体增量同步", "源/目标任务与增量 SQL", 3, 2, [r"exam_mis_media|exam_out_media", r"SYSTEM_LAST_VALUE|SYSTEM_CURRENT_VALUE|增量", r"createTime|mediapath"]),
    ("S4-02", "多媒体增量同步", "基础字段映射", 2, 1, [r"mediaId|relationId|mediaName|mediaUsage", r"createTime|updateTime|字段映射"]),
    ("S4-03", "多媒体增量同步", "拼接 URL", 3, 2, [r"mediaServer.*mediaPath.*mediaName|路径拼接", r"URL|record\.setColumn"]),
    ("S4-04", "多媒体增量同步", "媒体类型 IMAGE/VIDEO 转换", 3, 1, [r"IMAGE|图片", r"VIDEO|视频", r"1|2|类型转换|字典"]),
    ("S4-05", "多媒体增量同步", "拆分 server 和端口", 3, 1, [r"serverPort|端口", r"split|拆分", r"egova\.top|http://"]),
    ("S4-06", "多媒体增量同步", "mediaUsage 转 status", 2, 1, [r"mediaUsage", r"status", r"非空|为空|1|0"]),
    ("S4-07", "多媒体增量同步", "配置 2 分钟调度", 2, 1, [r"2\s*分钟|2min|120", r"调度|周期"]),
    ("S4-08", "多媒体增量同步", "验证目标端结果", 2, 2, [r"结果|目标表|目标端", r"调度日志|多次|新增|更新"]),

    ("S5-01", "binlog 多表实时同步", "人口表 CDC 监听", 3, 1, [r"exam_sg_resident_cdc|人口表.*CDC", r"mysql-cdc", r"PRIMARY KEY|主键"]),
    ("S5-02", "binlog 多表实时同步", "分析目标表/JDBC 维表", 2, 1, [r"exam_sg_analysis|分析表", r"connector.*jdbc|JDBC", r"目标表|维表"]),
    ("S5-03", "binlog 多表实时同步", "人口变更写入分析表", 3, 1, [r"resident.*cdc|exam_sg_resident_cdc", r"INSERT INTO.*analysis|写入.*分析", r"house.*building|LEFT JOIN"]),
    ("S5-04", "binlog 多表实时同步", "房屋表实时关联", 3, 1, [r"exam_sg_house_cdc|房屋表.*CDC", r"resident.*house|house.*resident", r"实时|INSERT INTO"]),
    ("S5-05", "binlog 多表实时同步", "楼栋表实时关联", 3, 1, [r"exam_sg_building_cdc|楼栋表.*CDC", r"resident.*building|building.*resident", r"实时|INSERT INTO"]),
    ("S5-06", "binlog 多表实时同步", "字段类型和目标映射", 2, 1, [r"CAST|类型转换|String.*INT", r"floorNum|houseNum|字段映射"]),
    ("S5-07", "binlog 多表实时同步", "修改源数据验证实时更新", 2, 1, [r"修改源|更新源|源端", r"实时更新|目标表.*更新|验证"]),
    ("S5-08", "binlog 多表实时同步", "作业部署和运行状态", 2, 1, [r"提交作业|部署|运行状态|作业", r"日志|运行成功|验证"]),
]

def is_image(line: str) -> bool:
    return bool(re.search(r"\[图\s*:", line, re.I))

def answer_indexes(lines: list[str]) -> set[int]:
    markers = re.compile(r"^\s*(答|答案|作答)\s*[:：]?\s*$", re.I)
    if not any(markers.search(x) for x in lines):
        return set(range(len(lines)))
    indexes: set[int] = set()
    active = False
    for i, line in enumerate(lines):
        if markers.search(line):
            active = True
            continue
        if active:
            indexes.add(i)
    return indexes

def load_lines(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().splitlines()

def score_item(lines: list[str], allowed: set[int], code: str, max_score: float, min_imgs: int, patterns: list[str], baseline: dict) -> dict:
    hits = []
    matched = []
    for p in patterns:
        rx = re.compile(p, re.I | re.S)
        found = [i for i in sorted(allowed) if not is_image(lines[i]) and rx.search(lines[i])]
        if found:
            matched.append(p)
            hits.extend(found)
    hits = sorted(set(hits))
    img_count = 0
    anchor = None
    for h in hits:
        nearby = sum(1 for j in range(max(0, h - 6), min(len(lines), h + 19)) if is_image(lines[j]))
        if nearby > img_count:
            img_count, anchor = nearby, h
    total_images = sum(1 for i in allowed if is_image(lines[i]))
    if not hits:
        return {"code": code, "max": max_score, "awarded": 0, "imgs": 0, "matched": 0, "patterns": [], "verdict": "❌ 未定位到作答证据", "evidence": "", "needs_visual": total_images > 0}

    content_factor = min(1.0, len(matched) / max(1, min(3, len(patterns) // 2 + 1)))
    if len(matched) >= max(2, len(patterns) // 2):
        content_factor = 1.0
    if img_count == 0:
        evidence_factor, verdict = 0.30, "⚠ 只有文字/脚本，需补截图或人工核验"
    elif img_count < min_imgs:
        evidence_factor, verdict = 0.60 + 0.30 * (img_count / max(1, min_imgs)), f"⚠ {img_count} 张截图，低于参考基线 {min_imgs} 张"
    else:
        evidence_factor, verdict = 1.0, f"✓ {img_count} 张截图，达到参考基线"
    awarded = round(max_score * min(content_factor, evidence_factor), 1)
    if awarded >= max_score * 0.95:
        awarded = max_score
    evidence = lines[anchor][:160] if anchor is not None else ""
    return {"code": code, "max": max_score, "awarded": awarded, "imgs": img_count, "matched": len(matched), "patterns": matched, "verdict": verdict, "evidence": evidence, "needs_visual": True}

def grade_file(path: str, baseline: dict) -> dict:
    lines = load_lines(path)
    allowed = answer_indexes(lines)
    rows = []
    for code, section, desc, max_score, default_min_imgs, patterns in ITEMS:
        min_imgs = baseline.get(code, {}).get("std_min_imgs", default_min_imgs)
        row = score_item(lines, allowed, code, max_score, min_imgs, patterns, baseline)
        row.update({"section": section, "desc": desc, "std_min_imgs": min_imgs, "need_url": baseline.get(code, {}).get("need_url", False)})
        rows.append(row)
    section_scores = OrderedDict()
    section_max = OrderedDict()
    for r in rows:
        section_scores[r["section"]] = section_scores.get(r["section"], 0) + r["awarded"]
        section_max[r["section"]] = section_max.get(r["section"], 0) + r["max"]
    return {"name": os.path.basename(os.path.dirname(path)), "source": path, "total": round(sum(x["awarded"] for x in rows), 1), "total_max": sum(x["max"] for x in rows), "rows": rows, "section_scores": section_scores, "section_max": section_max, "answer_lines": len(allowed), "images": sum(1 for i in allowed if is_image(lines[i]))}

def combine_records(name: str, records: list[dict]) -> dict:
    """同一 attempt 多个题位附件合并为一份答卷。

    每个采分点选择证据最完整的附件，防止一个题位的题干影响另一题位的判分。
    """
    rows = []
    for code, section, desc, max_score, *_ in ITEMS:
        choices = []
        for record in records:
            found = next((row for row in record["rows"] if row["code"] == code), None)
            if found:
                choices.append((found, record["source"]))
        best, source = max(choices, key=lambda x: (x[0]["awarded"], x[0]["matched"], x[0]["imgs"]))
        merged = dict(best)
        merged["source"] = source
        rows.append(merged)
    section_scores = OrderedDict()
    section_max = OrderedDict()
    for row in rows:
        section_scores[row["section"]] = section_scores.get(row["section"], 0) + row["awarded"]
        section_max[row["section"]] = section_max.get(row["section"], 0) + row["max"]
    return {
        "name": name,
        "sources": [record["source"] for record in records],
        "total": round(sum(row["awarded"] for row in rows), 1),
        "total_max": sum(row["max"] for row in rows),
        "rows": rows,
        "section_scores": section_scores,
        "section_max": section_max,
        "answer_lines": sum(record["answer_lines"] for record in records),
        "images": sum(record["images"] for record in records),
    }

def main() -> None:
    ext = os.path.join(ROOT, "_extracted")
    if not os.path.isdir(ext):
        raise SystemExit(f"[✗] 未找到 {ext}，请先运行 extract_docx.py")
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        baseline = json.load(f).get("items", {})
    files = []
    for root, _, names in os.walk(ext):
        if "text_only.txt" in names:
            files.append(os.path.join(root, "text_only.txt"))
    if not files:
        raise SystemExit(f"[✗] {ext} 下没有 text_only.txt")
    manifest_path = os.path.join(ext, "_manifest.json")
    groups = OrderedDict()
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        for item in manifest:
            text_path = os.path.join(item.get("out", ""), "text_only.txt")
            if not os.path.exists(text_path):
                continue
            attempt_name = os.path.basename(os.path.dirname(item.get("src", text_path)))
            groups.setdefault(attempt_name, []).append(text_path)
    if not groups:
        for path in sorted(files):
            groups[os.path.basename(os.path.dirname(path))] = [path]
    report = [combine_records(name, [grade_file(path, baseline) for path in paths]) for name, paths in groups.items()]
    with open(os.path.join(ROOT, "_grading_starbridge_v1.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    sections = list(OrderedDict((x[1], None) for x in ITEMS))
    md = ["# 星桥高级认证 — 初版阅卷报告", "", "评分方法：答题区文字/脚本关键词定位 + 附近截图占位数 + 参考答案最低截图基线。自动初评需人工视觉复核。", "", "## 总分排行", "", "| 排名 | 答卷 | 总分 | 满分 | 完成度 |", "|---:|---|---:|---:|---:|"]
    for i, rec in enumerate(sorted(report, key=lambda x: -x["total"]), 1):
        md.append(f"| {i} | {rec['name']} | **{rec['total']:.1f}** | {rec['total_max']} | {rec['total']/rec['total_max']:.0%} |")
    md += ["", "## 场景汇总", "", "| 答卷 | " + " | ".join(sections) + " | 总分 |", "|---|" + "---|" * (len(sections) + 1)]
    for rec in sorted(report, key=lambda x: -x["total"]):
        cells = [rec["name"]]
        for section in sections:
            cells.append(f"{rec['section_scores'].get(section, 0):.1f}/{rec['section_max'].get(section, 0):.0f}")
        cells.append(f"**{rec['total']:.1f}**")
        md.append("| " + " | ".join(cells) + " |")
    md += ["", "## 逐采分点明细", ""]
    for rec in sorted(report, key=lambda x: -x["total"]):
        md += [f"### {rec['name']} — {rec['total']:.1f}/{rec['total_max']}", "", "| 代码 | 采分点 | 分值 | 得分 | 截图 | 评判 |", "|---|---|---:|---:|---:|---|"]
        for r in rec["rows"]:
            md.append(f"| {r['code']} | {r['desc']} | {r['max']} | {r['awarded']} | {r['imgs']} | {r['verdict']} |")
        md.append("")
    with open(os.path.join(ROOT, "_grading_starbridge_v1.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    headers = ["name"] + [f"{x[0]}({x[3]})" for x in ITEMS] + sections + ["Total"]
    with open(os.path.join(ROOT, "_grading_starbridge_v1.csv"), "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for rec in sorted(report, key=lambda x: -x["total"]):
            by_code = {x["code"]: x for x in rec["rows"]}
            row = [rec["name"]] + [f"{by_code[x[0]]['awarded']}/{x[3]}" for x in ITEMS]
            row += [f"{rec['section_scores'].get(s, 0):.1f}/{rec['section_max'].get(s, 0):.0f}" for s in sections]
            row.append(f"{rec['total']:.1f}")
            writer.writerow(row)
    print(f"[✓] 已评分 {len(report)} 份，生成 _grading_starbridge_v1.json/.md/.csv")

if __name__ == "__main__":
    main()
