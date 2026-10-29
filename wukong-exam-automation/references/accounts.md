# 人员名单与账号录入

## 输入字段

人员名单至少需要：

- 姓名
- 工号
- 岗位/岗位体系
- 大区/区域
- 是否参考

可选字段：悟空账号、考官/实操阅卷人、备注。

## 处理规则

1. 只处理 `是否参考=是` 的人员。
2. 若名单已有账号，优先使用名单账号。
3. 若无账号，按历史规则从姓名和工号派生，生成后必须输出映射清单供核对。
4. 导入前查询现有 `wukong.com_user`，避免重复插入。
5. 导入后抽查账号能登录悟空入口。

## SQL 注意事项

- 不改 `admin`。
- 写入前备份或至少导出将影响的账号列表（`create table if not exists com_user_bak like com_user; replace into com_user_bak select * from com_user;`）。
- 密码、盐值和加密方式沿用当前环境约定；最终答复不要明文展开密码散列。
- 对失败账号单独列出姓名、账号、原因。
- **com_user 列序漂移教训（2026-10-28）**： positional INSERT 的 VALUES 比列名少一个元素（passwordExpireTime 位缺 NULL），导致其后全部左移一位，报 `Incorrect datetime value: 'Sm3WithSalt' for column 'passwordExpireTime'`。导入脚本已改为列表构造 + `assert len(values)==37`；手写 SQL 时先 `desc com_user` 核对列数。
- **2026-09-02 实测必补**（缺这三项会导致 unity/page-group/list 403、新建大屏失败）：`regionId='420000'`、`userType='0'`、`accountExpireTime=DATE_ADD(NOW(), INTERVAL 1 YEAR)`、`createTime=NOW()`；另 `passwordExpireTime=NULL`（防登录被拦截）。
- 角色关联：`com_role_member` 插 roleId=`00003`（工程，含大屏页面权限），memberType=0，幂等（`id NOT IN (SELECT memberId FROM com_role_member WHERE roleId='00003')`）。
- **延期考生的账号处理**：批准延期的，把其 `accountExpireTime` 改成当晚结束时间（如 `2026-10-28 23:00:00`），`remark` 标注 `<姓名> <工号> 延至23:00结束`——考后改密和无操作查询按备注排除这批人，走单独时间线。
- 登录抽查走 SM2 流程（`references/license.md` 末节），不要用明文密码直接打 token 端点。
