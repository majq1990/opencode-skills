"""
麒舰实操考核初版评分（v1）。
- 读取 _extracted/<name>/text_only.txt
- 按 10 大模块关键词匹配 + 段落附近图片数评估
- 输出 _grading_v1.json / .md / .csv

用法: python grading_qijian.py <workdir>
"""
import os, sys, json, re, csv

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\麒舰"
EXT = os.path.join(ROOT, "_extracted")

# 采分点定义：(代码, 模块, 描述, 分值, 关键词正则列表, 特殊说明)
# 每个采分点命中后，统计其段落附近图片数来估算完成度
MODULES = [
    # ==================== 一、部署与授权（10 分）====================
    ("A1", "部署与授权", "部署配置截图（服务界面/指定IP）", 2,
     [r"请配置服务器IP", r"10\.0\.0\.\d+", r"oneinstall", r"业务数据库", r"nacos服务器"],
     "需看到 IP 配置界面或各服务部署结果"),
    ("A2", "部署与授权", "免密登录两台服务器", 2,
     [r"免密", r"id_rsa", r"ssh", r"密钥登录"],
     "需两台服务器免密成功截图"),
    ("A3", "部署与授权", "License 授权各产品", 2,
     [r"license", r"授权", r"init", r"licence"],
     "各产品授权成功截图"),
    ("A4", "部署与授权", "各系统登录截图（智信云/麒舰/玄藏/灵珑）", 4,
     [r"智信云.*登录|egova", r"麒舰.*登录|eurbanpro", r"玄藏.*登录|xuanzang", r"灵珑.*登录|linglong", r"用户中心登录|usercenter"],
     "至少 4 个系统登录页面+URL"),

    # ==================== 二、地理数据替换（20 分）====================
    # 智信云地图（10 分）
    ("B1", "地理数据替换", "tc_region 表数据生成（地市级→单元网格）", 2,
     [r"tc_region", r"region表|region 表", r"地市级网格", r"单元网格", r"网格图层要素生成"],
     "需各级网格要素生成日志"),
    ("B2", "地理数据替换", "地理编码数据入库", 2,
     [r"地理编码", r"入库"],
     "地理编码入库截图"),
    ("B3", "地理数据替换", "网格索引生成（CellIndex + MIS）", 2,
     [r"CellIndex", r"网格索引", r"data/"],
     "索引处理及复制结果截图"),
    ("B4", "地理数据替换", "通图矢量服务发布（含prj修复）", 2,
     [r"通图", r"矢量", r"prj", r"CGCS2000", r"发布图层|服务发布"],
     "需含 prj 修复步骤"),
    ("B5", "地理数据替换", "GIS 构建向导地图配置（含底图+矢量图层）", 2,
     [r"GIS构建向导|构建向导", r"底图", r"矢量图层", r"智信云.*地图"],
     "最终地图截图需展示图层控制+勾选图层"),

    # 玄藏地图（8 分）— 按试卷分布：项目配置1.5+场景配置1.5+网格索引1.5+地址配置1.5+地图预览2
    ("B6", "地理数据替换", "玄藏项目配置+登录权限（用户中心应用中心添加玄藏应用）", 2,
     [r"玄藏.*项目配置", r"用户中心.*应用中心", r"登录权限", r"项目配置向导"],
     "用户中心添加玄藏应用+admin登录权限"),
    ("B6b", "地理数据替换", "玄藏场景配置（我的场景-场景标识）", 2,
     [r"我的场景|场景配置", r"场景标识"],
     "场景配置截图，含场景ID/标识"),
    ("B7", "地理数据替换", "玄藏网格索引配置 + 地址/场景标识", 2,
     [r"xuanzang/data|索引目录", r"CellIndex", r"服务配置.*场景"],
     "索引放置正确目录+地址配置"),
    ("B8", "地理数据替换", "玄藏地图预览（图层控制含井盖+街道）", 2,
     [r"水井盖", r"街道图层", r"图层控制", r"玄藏.*预览|地图预览"],
     "需展示图层控制+勾选特定图层，截图含URL"),
    ("B9", "地理数据替换", "星桥数据同步试跑结果（region+地理编码+兴趣点）", 2,
     [r"region表同步|区划同步", r"地理编码.*同步", r"兴趣点.*同步|同步试跑"],
     "星桥试跑日志截图，数据源须为 usercenter"),

    # ==================== 三、组织机构维护（15 分）====================
    ("C1", "组织机构维护", "部门/人员导入后智信云构建", 2,
     [r"部门导入", r"人员导入", r"构建"],
     "需部门+人员导入后截图"),
    ("C2", "组织机构维护", "星桥迁移数据到用户中心（区划/部门/岗位/人员/岗位人员）", 5,
     [r"同步.*区划", r"部门.*迁移|部门.*同步", r"岗位.*迁移|岗位.*同步",
      r"人员.*迁移|人员.*同步", r"岗位人员|试跑"],
     "需 5 步同步试跑截图"),
    ("C3", "组织机构维护", "用户中心查看同步数据 + 岗位权限配置（受理员/值班长/派遣员/专业部门）", 4,
     [r"市受理员", r"市值班长", r"市派遣员", r"专业部门.*岗位", r"权限配置"],
     "新用户中心查看+岗位权限绑定截图"),
    ("C4", "组织机构维护", "新导入账号麒舰 PC 端登录", 2,
     [r"新导入.*登录|新账号.*登录", r"麒舰登录"],
     "新账号登录麒舰截图+URL"),
    ("C5", "组织机构维护", "政府租户管理员配置（区划根节点编码清空）", 2,
     [r"政府租户", r"区划根节点|区划项目编码", r"管理员岗位"],
     "需清空区划根节点编码截图"),

    # ==================== 四、监督员和网格配置（5 分）====================
    ("D1", "监督员和网格", "责任网格配置（嘎洒镇/允景洪街办）", 2,
     [r"责任网格", r"嘎洒镇", r"允景洪街办", r"市容四支队", r"市容一"],
     "两个责任网格配置截图"),
    ("D2", "监督员和网格", "网格员责任网格关联配置", 3,
     [r"网格员", r"责任网格.*关联|关联网格", r"网格员管理"],
     "网格员与责任网格关联截图"),

    # ==================== 五、事项配置更新（5 分）====================
    ("E1", "事项配置更新", "新增小类（code:99 其他事件）+ 小类助手页面截图", 5,
     [r"code.{0,5}99|99.*小类", r"其他事件.*小类", r"立案条件.*问题发生|问题发生.*立案",
      r"处置时限", r"小类助手", r"核心区", r"一般区", r"外围区"],
     "需完整截图含立案/结案条件+时限配置"),

    # ==================== 六、栏目简单配置（10 分）====================
    ("F1", "栏目简单配置", "灵珑视图脚本（act_property_id=104）", 2,
     [r"act_property_id.*104|act_property_id.{0,3}104", r"SELECT.*mis_rec.*wf_act", r"视图脚本"],
     "视图 SQL 截图（含 104 条件）"),
    ("F2", "栏目简单配置", "新增栏目配置（协同平台-待审核栏）", 2,
     [r"协同平台", r"待审核栏", r"新增栏目|栏目配置"],
     "栏目新增+菜单配置截图"),
    ("F3", "栏目简单配置", "岗位权限配置（市派遣员）", 2,
     [r"市派遣员.*权限|权限.*派遣员", r"栏目权限", r"更新权限"],
     "岗位权限绑定+更新截图"),
    ("F4", "栏目简单配置", "市派遣员登录展示待审核栏", 2,
     [r"市派遣员.*登录|派遣员.*待审核"],
     "派逑员 PC 端截图含 URL + 待审核栏展示"),
    ("F5", "栏目简单配置", "栏目菜单配置", 2,
     [r"栏目菜单|菜单配置", r"菜单.*栏目"],
     "栏目菜单树配置截图"),

    # ==================== 七、导航配置（5 分）====================
    ("G1", "导航配置", "灵珑应用导入（园林） + 数据库创建 + 多媒体配置", 1,
     [r"灵珑应用导入", r"yuanlin", r"create database", r"多媒体配置|media"],
     "应用导入+数据库+多媒体 nginx 配置截图"),
    ("G2", "导航配置", "导航栏配置（园林管理）", 1,
     [r"导航栏|导航配置", r"园林管理|园林.*导航"],
     "导航栏结构截图"),
    ("G3", "导航配置", "岗位导航权限 + 应用权限配置", 1,
     [r"岗位.*导航权限|导航.*权限", r"应用权限|应用管理"],
     "岗位导航权限绑定截图"),
    ("G4", "导航配置", "市派遣员登录验证（园林管理打开）", 2,
     [r"园林管理.*打开|园林.*展示", r"派遣员.*导航"],
     "派遣员登录后导航页面截图+打开应用截图"),

    # ==================== 八、移动端配置（10 分）====================
    ("H1", "移动端配置", "模板配置（复制模板+修改）", 2,
     [r"模板配置|复制.*模板|模板.*复制", r"修改.*模板"],
     "模板列表+修改截图"),
    ("H2", "移动端配置", "移动端新增插件配置", 2,
     [r"自定义插件|新增插件", r"移动端配置|构建中心.*移动端"],
     "插件新增截图"),
    ("H3", "移动端配置", "工作台新增插件", 1,
     [r"工作台.*插件|插件.*工作台"],
     "工作台配置截图"),
    ("H4", "移动端配置", "插件权限配置（含核心平台+构建平台）", 4,
     [r"导航权限.*插件|插件.*权限", r"应用管理.*核心平台|应用管理.*构建平台",
      r"核心平台.*权限|构建平台.*权限"],
     "至少核心平台+构建平台权限配置截图"),
    ("H5", "移动端配置", "移动端登录后工作台展示（待审核栏）", 1,
     [r"移动端.*登录|登录.*移动端", r"工作台.*待审核|待审核.*移动端"],
     "移动端截图含待审核栏"),

    # ==================== 九、工作流简单配置（10 分）====================
    ("I1", "工作流简单配置", "参与者同步 + 一级/二级专业部门岗位加入流程", 2,
     [r"参与者.*同步|系统配置.*同步", r"一级专业部门", r"岗位.*流程|流程.*岗位"],
     "参与者+岗位参与截图"),
    ("I2", "工作流简单配置", "流程图配置后截图（含一级+二级专业部门节点）", 2,
     [r"工作流程图|流程图", r"发布"],
     "发布后流程图完整截图"),
    ("I3", "工作流简单配置", "一二级专业部门节点属性 + 过滤配置", 2,
     [r"一级.*属性|属性.*一级专业", r"二级.*属性|属性.*二级专业", r"过滤|上下级过滤"],
     "节点属性配置截图"),
    ("I4", "工作流简单配置", "二级专业部门延期授权配置", 2,
     [r"授权配置|申请延期|延期.*授权", r"答复授权|多级授权"],
     "授权配置截图"),
    ("I5", "工作流简单配置", "派遣员批转专业部门（一级+二级可见）", 2,
     [r"派遣员.*批转|批转.*专业部门", r"批转.*二级|二级.*可见"],
     "派遣员批转界面截图"),

    # ==================== 十、全业务流转（10 分）====================
    ("J1", "全业务流转", "手机端上报案件 + 全流程流转至结案", 4,
     [r"手机端.*上报|上报.*案件", r"全流程|流转.*结案", r"结案"],
     "完整流转截图（上报→核实→派遣→处置→结案），至少4张"),
    ("J2", "全业务流转", "受理平台登记 + 二级部门延期申请 + 全流程", 6,
     [r"登记.*案件|受理.*登记", r"申请延期|二级.*延期", r"核查|核查反馈",
      r"事件.*其他|其他.*事件", r"全流程|办理经过"],
     "登记→核实→延期→核查→结案全流程，至少6张截图"),
]


def grade_one(text_only_path):
    """对一份答卷评分"""
    if not os.path.exists(text_only_path):
        return None
    with open(text_only_path, "r", encoding="utf-8") as f:
        raw = f.read()
    lines = raw.split("\n")
    is_img = [bool(re.match(r"^\[图:", ln)) for ln in lines]

    rows = []
    for code, module, desc, mx, kws, note in MODULES:
        hits = []
        for kw in kws:
            pat = re.compile(kw, re.I | re.S)
            for i, ln in enumerate(lines):
                if not is_img[i] and pat.search(ln):
                    hits.append(i)

        if not hits:
            rows.append({
                "code": code, "module": module, "desc": desc, "max": mx,
                "awarded": 0, "imgs": 0, "note": note,
                "verdict": "❌ 未作答（关键词未命中）"
            })
            continue

        # 统计 hit 行附近图片数（前后 15 行窗口）
        max_imgs = 0
        hit_ctx = ""
        for h in hits:
            cnt = 0
            for j in range(max(0, h-3), min(len(lines), h+15)):
                if is_img[j]:
                    cnt += 1
            if cnt > max_imgs:
                max_imgs = cnt
                hit_ctx = lines[h][:80]

        # 按图片数给分：0图=0% / 1图=60% / 2图=80% / 3图=90% / 4+图=100%
        if max_imgs == 0:
            awarded = 0
            verdict = f"❌ 无截图（关键词命中，0张图）"
        elif max_imgs == 1:
            awarded = round(mx * 0.6, 1)
            verdict = f"⚠ 1张截图（可能不全）"
        elif max_imgs == 2:
            awarded = round(mx * 0.8, 1)
            verdict = f"✓ 2张截图"
        elif max_imgs == 3:
            awarded = round(mx * 0.9, 1)
            verdict = f"✓ 3张截图"
        else:
            awarded = mx
            verdict = f"✓ {max_imgs}张截图"

        if note and max_imgs > 0:
            verdict += f" ⚠要求:{note}"

        rows.append({
            "code": code, "module": module, "desc": desc, "max": mx,
            "awarded": awarded, "imgs": max_imgs, "note": note,
            "verdict": verdict, "ctx": hit_ctx
        })
    return rows


def main():
    names = sorted([
        d for d in os.listdir(EXT)
        if os.path.isdir(os.path.join(EXT, d))
    ])
    if not names:
        print(f"[✗] 在 {EXT} 下未找到解析结果。请先运行 extract_docx.py")
        sys.exit(1)

    print(f"[✓] 发现 {len(names)} 份已解析答卷")

    report = []
    for name in names:
        text_path = os.path.join(EXT, name, "text_only.txt")
        rows = grade_one(text_path)
        if not rows:
            print(f"  ✗ {name}: 无解析结果")
            continue

        # 按模块分组计算得分
        module_scores = {}
        module_max = {}
        for r in rows:
            mod = r["module"]
            module_scores.setdefault(mod, 0)
            module_max.setdefault(mod, 0)
            module_scores[mod] += r["awarded"]
            module_max[mod] += r["max"]

        total = sum(r["awarded"] for r in rows)
        total_max = sum(r["max"] for r in rows)

        rec = {
            "name": name, "total": total, "total_max": total_max,
            "rows": rows, "module_scores": module_scores, "module_max": module_max
        }
        report.append(rec)
        print(f"  ✓ {name}: {total:.1f}/{total_max:.1f}")

    # === 写 JSON ===
    with open(os.path.join(ROOT, "_grading_v1.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # === 写 Markdown ===
    md = ["# 麒舰实操考核 — 阅卷报告（v1 初版）",
          "",
          "**评分方法**：基于文字段落关键词匹配 + 段落附近图片数评估。",
          "**注意**：此版本未做人工视觉细判，建议对临界分进行人工复核。",
          "",
          "---",
          "",
          "## 总分排行",
          "",
          "| 排名 | 姓名 | 总分 | 满分 | 正确率 |",
          "|---|---|---|---|---|"]
    for i, r in enumerate(sorted(report, key=lambda x: -x["total"]), 1):
        pct = r["total"] / r["total_max"] * 100 if r["total_max"] > 0 else 0
        md.append(f"| {i} | {r['name']} | **{r['total']:.1f}** | {r['total_max']:.1f} | {pct:.0f}% |")

    # 模块得分汇总表
    md += ["", "## 模块得分汇总", "", "| 姓名 |"]
    all_modules = [m[1] for m in MODULES]
    unique_modules = list(dict.fromkeys(all_modules))  # 去重保序
    header = "| 姓名 | " + " | ".join(unique_modules) + " | 总分 |"
    sep = "|---|" + "---|" * (len(unique_modules) + 1)
    md += [header, sep]
    for r in sorted(report, key=lambda x: -x["total"]):
        row = f"| {r['name']} | "
        for mod in unique_modules:
            sc = r["module_scores"].get(mod, 0)
            mx = r["module_max"].get(mod, 0)
            row += f"{sc:.1f}/{mx:.1f} | "
        row += f"**{r['total']:.1f}** |"
        md.append(row)

    # 每人明细
    md += ["", "---", "", "## 每人扣分明细", ""]
    for r in sorted(report, key=lambda x: -x["total"]):
        md.append(f"### {r['name']} — {r['total']:.1f}/{r['total_max']:.1f}")
        md.append("")
        # 按模块分组
        current_mod = ""
        for p in r["rows"]:
            if p["module"] != current_mod:
                current_mod = p["module"]
                md.append(f"**{current_mod}**")
                md.append("")
                md.append("| 采分点 | 分值 | 得分 | 截图 | 评判 |")
                md.append("|---|---|---|---|---|")
            short = p["desc"][:40]
            img_tag = f"{p['imgs']}张" if p["imgs"] > 0 else "-"
            md.append(f"| {p['code']} {short} | {p['max']} | {p['awarded']} | {img_tag} | {p['verdict']} |")
        md.append("")
        md.append("---")
        md.append("")

    with open(os.path.join(ROOT, "_grading_v1.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    # === 写 CSV ===
    headers = ["name"]
    for code, mod, desc, mx, *_ in MODULES:
        headers.append(f"{code}({mx})")
    headers += unique_modules + ["Total"]
    with open(os.path.join(ROOT, "_grading_v1.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in sorted(report, key=lambda x: -x["total"]):
            row = [r["name"]]
            code_map = {p["code"]: p for p in r["rows"]}
            for code, *_ in MODULES:
                p = code_map.get(code, {})
                row.append(f"{p.get('awarded', 0)}/{p.get('max', 0)}")
            for mod in unique_modules:
                sc = r["module_scores"].get(mod, 0)
                mx = r["module_max"].get(mod, 0)
                row.append(f"{sc:.1f}/{mx:.1f}")
            row.append(f"{r['total']:.1f}")
            w.writerow(row)

    print(f"\n[✓] 已生成: _grading_v1.md / _grading_v1.csv / _grading_v1.json")


if __name__ == "__main__":
    main()
