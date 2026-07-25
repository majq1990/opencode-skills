"""
从 reference_answers/ 下的标准答卷 docx 抽取每个采分点的截图基线，
生成 references/reference_baseline.json。

用法: python build_baseline.py

新一轮考试题目变化时：
1. 把新版标准答卷 docx 放入 reference_answers/
2. 跑本脚本重新生成 baseline
3. 人工微调过度计数项（标准答卷因分节问题可能高估的项）
"""
import os, json, re, sys
import docx

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
REF_DIR = os.path.join(SKILL_ROOT, "reference_answers")
OUT_PATH = os.path.join(SKILL_ROOT, "references", "reference_baseline.json")

# 采分点关键词 → 标准描述（手工维护：Q1 性能监控 19 项 + Q2 安全 7 项）
SCORING_DEF = {
    "P1-1": {"kw": ["内网访问", "内网访问登录"],
             "std_desc": "浏览器内网访问用户中心登录页 (8.x.x.x:8080/usercenter/.../login)"},
    "P1-2": {"kw": ["mysql 状态导出"], "std_desc": "修改脚本中数据库密码 + 执行导出脚本"},
    "P1-3": {"kw": ["达梦状态导出"], "std_desc": "达梦配置脚本 + 执行 + 状态信息输出"},
    "P1-4": {"kw": ["nginx 状态导出"], "std_desc": "状态码统计分布 + 10s 耗时请求节点分布（两段）"},
    "P1-5": {"kw": ["应用日志错误提取"], "std_desc": "日志错误定位（如 nacos 连接失败），启动服务后正常"},
    "P1-6": {"kw": ["jvm 信息导出"], "std_desc": "jstack/jmap 或 jvm 信息输出"},
    "P1-7": {"kw": ["redis 状态导出"], "std_desc": "redis-cli info / 状态信息输出"},
    "P1-8": {"kw": ["磁盘 I/O", "磁盘 IO 状态"], "std_desc": "iostat / 磁盘 IO 状态截图"},
    "P1-9": {"kw": ["系统恢复思路"], "std_desc": "≥60 字论述根因+恢复步骤"},
    "P2-1": {"kw": ["生成最新的 zip 巡检报告"], "std_desc": "auto-check archive 目录下 zip 报告已生成"},
    "P2-2": {"kw": ["report_dameng.html"], "std_desc": "dameng 报告统计区有真实数据行"},
    "P2-3": {"kw": ["report_microservice.html"],
             "std_desc": "microservice 报告 + HeapDumpPath 修复（修改前/后/重启验证）"},
    "P2-4": {"kw": ["report_mysql.html"], "std_desc": "mysql 报告基本+空闲100s/大表等区块数据"},
    "P2-5": {"kw": ["report_nginx.html"], "std_desc": "nginx 报告 + logrotate 配置/crontab 部署修复"},
    "P2-6": {"kw": ["report_os.html"], "std_desc": "os 报告 cpu/内存/磁盘多区块数据"},
    "P2-7": {"kw": ["report_redis.html"], "std_desc": "redis 报告 连接/内存/持久化等数据"},
    "P3-1": {"kw": ["测试前置操作"], "std_desc": "sysbench/iperf/fio 等工具准备"},
    "P3-2": {"kw": ["数据库基准测试"],
             "std_desc": "sysbench: 创建测试库+用户 → 准备数据 → prepare → run → cleanup"},
    "P3-3": {"kw": ["redis 基准测试"], "std_desc": "redis-benchmark 输出"},
    "P3-4": {"kw": ["磁盘 IO 性能测试"], "std_desc": "fio 顺序/随机读写测试（双服务器）"},
    "P3-5": {"kw": ["IOPS 测试"], "std_desc": "fio IOPS 测试（双服务器）"},
    "P3-6": {"kw": ["宽带测试"], "std_desc": "iperf 带宽测试（双向）"},
}

# Q2 不在标准答卷 docx 里逐节出现，写死
Q2_FIXED = {
    "S1-1": {"std_min_imgs": 3,
             "std_desc": "雷池离线部署 + 登录页/仪表盘带URL（须 https://x.x.x.x:9443/...）"},
    "S1-2": {"std_min_imgs": 4,
             "std_desc": "模拟攻击 + 雷池攻击日志找到真实IP + 拦截效果图（带URL）"},
    "S1-3": {"std_min_imgs": 4,
             "std_desc": "雷池规则拦截租户管理接口 + reload 后验证 403/拦截页"},
    "S2-1": {"std_min_imgs": 3,
             "std_desc": "①DevTools 32018 拦截截图 ②wafconf/url 注释 getapps ③nginx reload + 应用中心列表恢复"},
    "S2-2": {"std_min_imgs": 3,
             "std_desc": "①取 operatelog URL ②echo URL >> wafconf/url ③reload + 重访接口 403/X-Waf-Code 32018"},
    "S2-3": {"std_min_imgs": 3,
             "std_desc": "①取 oauth/.../login URL ②echo >> wafconf/cc-url + reload ③ab 攻击 + 31001 拦截日志"},
    "S3-1": {"std_min_imgs": 2,
             "std_desc": "弱密码字典扫描 + check_result.log 命中 ≥5 个账号清单"},
}

# 手工微调：标准答卷因分节问题被高估的项（实测调整）
MANUAL_OVERRIDE = {
    "P1-3": 2,  # 王拥民答卷 5 张但实际 2 张合理
    "P3-2": 3,  # sysbench 5 步骤但学员通常截 prepare+run 即可
    "P3-6": 2,  # 答卷"宽带测试"节误吞了雷池部署 20 张图
}


def parse_doc(path):
    """返回每个标题节的图片数 [{title, images}]"""
    d = docx.Document(path)
    sections = []
    cur = {"title": "<前言>", "images": 0}
    for el in d.element.body.iter():
        tag = el.tag.split("}")[-1]
        if tag == "p":
            txt = "".join(t.text or "" for t in el.iter() if t.tag.endswith("}t")).strip()
            has_img = any(c.tag.endswith("}drawing") or c.tag.endswith("}pict") for c in el.iter())
            if has_img:
                cur["images"] += 1
            elif txt and re.search(r"[:：]$", txt) and len(txt) < 100:
                sections.append(cur)
                cur = {"title": txt, "images": 0}
    sections.append(cur)
    return sections


def baseline_imgs(sections_list, kws):
    """从所有标准答卷的节里找匹配关键词的节，返回图数最大值"""
    mx = 0
    for sects in sections_list:
        for s in sects:
            if any(k in s["title"] for k in kws):
                mx = max(mx, s["images"])
                break
    return max(mx, 1)


def main():
    docxs = [os.path.join(REF_DIR, f) for f in os.listdir(REF_DIR) if f.endswith(".docx")]
    print(f"扫描标准答卷 {len(docxs)} 份")
    sections_list = [parse_doc(p) for p in docxs]

    baseline = {}
    for code, info in SCORING_DEF.items():
        n = baseline_imgs(sections_list, info["kw"])
        if code in MANUAL_OVERRIDE:
            n = MANUAL_OVERRIDE[code]
        baseline[code] = {
            "kw": info["kw"],
            "std_desc": info["std_desc"],
            "std_min_imgs": n,
        }
    baseline.update(Q2_FIXED)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(baseline, f, ensure_ascii=False, indent=2)
    print(f"OK: 写入 {OUT_PATH}（{len(baseline)} 个采分点）")


if __name__ == "__main__":
    main()
