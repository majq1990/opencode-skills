# -*- coding: utf-8 -*-
"""从钉钉文档导出的 Excel/CSV 读取姓名和工号，生成悟空 com_user 批量导入 SQL"""
import csv
import os
import sys
from pypinyin import lazy_pinyin

PASSWORD_HASH = "a2defcd18070f91bc59c113ab499920309dbcbd7156faf3ef8b4086b986daced"
ENCRYPT_SALT = "GQQiaYnk"
START_ID = 12000

str_ini = '''create table if not exists wukong.com_user_bak like wukong.com_user;
replace into wukong.com_user_bak SELECT * FROM wukong.com_user;

delete from wukong.com_user where username != 'admin';
select * from wukong.com_user;

INSERT INTO wukong.com_user
(id, password, username, departmentId, name, sex, email, phone, photo, creator, modifier, createTime, modifyTime, remark, phonetic, userType, regionId, terminalType, disabled, tenantId, personId, sign, documentNo, accountExpireTime, sourceId, passwordExpireTime, encryptionType, passwordChanged, identityNumber, status, telephone, gridName, identity, description, linkDepartmentName, code, encryptSalt)
VALUES'''


def read_table(file_path):
    """读取 Excel/CSV 全部行，返回二维字符串数组"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ('.xlsx', '.xls'):
        from openpyxl import load_workbook
        ws = load_workbook(file_path, read_only=True, data_only=True).active
        return [[('' if c is None else str(c).strip()) for c in row] for row in ws.iter_rows(values_only=True)]
    if ext == '.csv':
        with open(file_path, newline='', encoding='utf-8-sig') as f:
            return [[c.strip() for c in row] for row in csv.reader(f)]
    sys.exit("仅支持 .xlsx/.xls/.csv 文件")


def pick_column(header, prompt, default=None):
    """指定列：可输入列名、列序号(从1开始)或列字母(A/B/...)，default 命中时直接回车"""
    while True:
        tip = f"{prompt}（默认：{default}）：" if default else f"{prompt}："
        s = input(tip).strip() or (default or '')
        if not s:
            print("不能为空，请重新输入")
            continue
        if s in header:
            return header.index(s)
        if s.isdigit() and 1 <= int(s) <= len(header):
            return int(s) - 1
        if s.isalpha():
            idx = 0
            for ch in s.upper():
                idx = idx * 26 + ord(ch) - 64
            if 1 <= idx <= len(header):
                return idx - 1
        print(f"无效输入，可用列：{header}")


def load_rows(file_path):
    """返回 [(姓名, 工号), ...]，跳过姓名或工号为空、工号重复的行"""
    rows = read_table(file_path)
    if not rows:
        sys.exit("文件为空")

    header = rows[0]
    print(f"检测到 {len(header)} 列：" + " | ".join(f"{i+1}.{h}" for i, h in enumerate(header)))
    i_name = pick_column(header, "姓名列", "姓名" if "姓名" in header else None)
    i_id = pick_column(header, "工号列", "工号" if "工号" in header else None)

    pairs, seen = [], set()
    for row in rows[1:]:
        name = row[i_name] if i_name < len(row) else ''
        uid = row[i_id] if i_id < len(row) else ''
        if not name or not uid or uid in seen:
            continue
        seen.add(uid)
        pairs.append((name, uid))
    return pairs


def main():
    file_path = input("请输入钉钉导出的文件路径（xlsx/xls/csv）：").strip().strip('"')
    if not os.path.isfile(file_path):
        sys.exit("文件不存在：" + file_path)

    pairs = load_rows(file_path)
    if not pairs:
        sys.exit("没有有效数据行")

    print(f"\n共 {len(pairs)} 个账号：")
    for name, uid in pairs:
        print(''.join(lazy_pinyin(name)) + uid)

    if input("\n回车生成 SQL（其他键退出）：") != "":
        return

    lines = [str_ini]
    int_last_id = START_ID + len(pairs)
    cur = START_ID
    for name, uid in pairs:
        cur += 1
        username = ''.join(lazy_pinyin(name)) + uid
        sql = (f"('{cur}', '{PASSWORD_HASH}', '{username}', NULL, '{name}', -1, NULL, NULL, NULL, "
               f"'admin', 'admin', NOW(), NOW(), NULL, '{name} {uid}', '0', 420000, "
               f"'Web', 0, 'ca38aab2-23cd-4eca-93ed-1be55da90fb3', NULL, NULL, NULL, "
               f"DATE_ADD(NOW(), INTERVAL 1 YEAR), NULL, "
               f"'Sm3WithSalt', 1, NULL, 1, NULL, NULL, NULL, NULL, NULL, NULL, '{uid}', '{ENCRYPT_SALT}')")
        lines.append(sql + (";" if cur == int_last_id else ","))
    lines.append("")
    lines.append("-- 2026-09-02 实测必补：缺这三项会导致 unity/page-group/list 403，新建大屏失败")
    lines.append("-- 与后台手工新建账号 ('6a935dd4...') 对比确认；时间字段用表达式，自动跟随采购部署日")
    lines.append("UPDATE wukong.com_user SET regionId='420000', userType='0', "
                 "createTime=NOW(), accountExpireTime=DATE_ADD(NOW(), INTERVAL 1 YEAR) "
                 f"WHERE id > {START_ID};")
    lines.append("")
    lines.append("-- 密码永不过期（防登录被 passwordExpireTime 拦截）")
    lines.append("update wukong.com_user set passwordExpireTime = NULL where username != 'admin';")
    lines.append("")
    lines.append("-- 关联角色 00003 工程（含大屏页面权限），如已有则跳过")
    lines.append("INSERT INTO wukong.com_role_member (Id, roleId, memberId, memberType, creator, createTime, remark)")
    lines.append("SELECT REPLACE(UUID(),'-',''), '00003', id, 0, 'admin', NOW(), '考生'")
    lines.append(f"FROM wukong.com_user WHERE id > {START_ID} AND id NOT IN (SELECT memberId FROM wukong.com_role_member WHERE roleId='00003');")
    output = "\n".join(lines)
    print("\n" + output)

    out_file = os.path.join(os.path.dirname(os.path.abspath(file_path)), "wukong_user_import.sql")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"\nSQL 已保存：{out_file}")


if __name__ == '__main__':
    main()
