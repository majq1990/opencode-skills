# 常见问题排查手册 (FAQ)

## 一、安装本地源相关

### Q1: "安装本地源失败, 请提案件给技术支持部，补充缺失依赖包"
**原因**: `src/repo/` 目录下缺少某些 OS 版本的依赖 rpm/deb 包。

**解决**:
1. 查看具体缺少哪些包（终端输出中有包名）
2. 将缺失的包放到 `src/repo/{os_name}/` 对应目录下
   - CentOS: `src/repo/centos/`
   - Kylin: `src/repo/kylin/`
   - UOS: `src/repo/uos/`
   - Ubuntu: `src/repo/ubuntu/`
   - openEuler: `src/repo/openeuler/`
   - Anolis: `src/repo/anolis/`
3. 重新执行菜单选项 `0`

### Q2: 本地源 Nginx 启动失败
**排查**:
```bash
# 检查端口占用
netstat -tlnp | grep 7777

# 检查 Nginx 配置
cat /etc/nginx/conf.d/egova-oneinstall-local-repo-nginx.conf

# 查看 Nginx 日志
tail -50 /var/log/nginx/error.log
```

### Q3: "发现 xxx 不支持的操作系统，请检查系统版本"
**原因**: 当前操作系统不在支持列表中。

**解决**: 参考 `os-compatibility.md` 确认支持范围，或联系技术支持评估适配。

---

## 二、Ansible 安装相关

### Q4: Ansible 安装失败
**排查步骤**:
```bash
# 检查本地源是否正常
yum repolist | grep egova-local   # 或 apt list

# 手动安装测试
yum install -y ansible --disablerepo="*" --enablerepo="egova-local"
```

**Anolis 特殊处理**: Anolis 使用 `ansible-core` 而非 `ansible`，还需手动安装 community 集合：
```bash
ansible-galaxy collection install src/bin/postgresql/collections/community-general-9.4.0.tar.gz
ansible-galaxy collection install src/bin/postgresql/collections/community-postgresql-3.6.1.tar.gz
```

---

## 三、SSH 免密相关

### Q5: SSH 免密登录失败
**常见原因与解决**:

| 原因 | 解决方法 |
|---|---|
| 目标机器 SSH 端口不对 | 确认端口，添加服务器时输入正确端口 |
| 目标机器防火墙阻止 | `firewall-cmd --add-port=22/tcp --permanent && firewall-cmd --reload` |
| 目标机器禁止 root 登录 | 检查 `/etc/ssh/sshd_config` 中 `PermitRootLogin yes` |
| 密钥权限问题 | `chmod 600 /root/.ssh/id_ed25519` |
| 已配置过免密但失效 | 删除 `/egova/conf/ssh_{ip}.status` 文件后重试 |
| 使用自定义 SSH 密钥 | 修改 `ansible/group_vars/all.yml` 中的 `devops_ssh_key` |

**手动排查命令**:
```bash
# 测试 SSH 连接
ssh -p {port} -o "StrictHostKeyChecking no" root@{ip} "echo ok"

# 检查密钥
ls -la /root/.ssh/
cat /root/.ssh/id_ed25519.pub

# 检查目标机器授权
ssh -p {port} root@{ip} "cat /root/.ssh/authorized_keys"
```

### Q6: "设置免密码登录xxx失败"
**排查**:
1. 确认目标服务器可达: `ping {ip}`
2. 确认 SSH 端口开放: `telnet {ip} {port}` 或 `nc -zv {ip} {port}`
3. 确认 root 密码正确（首次免密需要输入密码）
4. 如果使用 `devops_ssh_key` 指定的密钥，确保密钥文件存在且权限为 600

---

## 四、增加服务器相关

### Q7: "ip=xxx的主机已存在,无需添加"
**原因**: 该 IP 已在 `ansible/inventory/hosts.yml` 中。

**解决**: 
- 如果需要修改: 先删除再重新添加（菜单选项 `2` → `1`）
- 或者手动编辑 `hosts.yml`

### Q8: 添加服务器后子控节点安装失败
**常见原因**:
1. **connection: local 问题**: 检查 playbook 中是否有多余的 `connection: local`
2. **本地源未同步**: 检查子控节点的 yum 源配置
   ```bash
   ssh root@{ip} "cat /etc/yum.repos.d/egova-oneinstall-local.repo"
   ```
3. **Python 未安装**: Ansible 需要目标机器有 Python
   ```bash
   ssh root@{ip} "python3 --version || python --version"
   ```
4. **SELinux 干扰**: 临时关闭测试
   ```bash
   ssh root@{ip} "setenforce 0"
   ```

---

## 五、应用服务部署相关

### Q9: 分布式部署 IP 配置校验失败
**常见校验错误**:

| 错误信息 | 原因 | 解决 |
|---|---|---|
| `[xxx]IP不能为空!` | 必填项未配置 | 给带 `*` 标记的角色分配 IP |
| `统计主库和业务主库不能同一个服务器上` | 业务库和统计库主节点用了同一 IP | 分配到不同服务器 |
| `从库[xxx]不可同时为业务主库!` | 从库 IP 和对方主库相同 | 更换从库 IP |
| `从库[xxx]存在多个主库!` | 同一个从库被分配给多个主库 | 确保从库只属于一个主库 |
| `MIS服务有从节点时，人脸服务只能装在从节点` | 人脸服务和 MIS 主节点同 IP | 将人脸服务配到 MIS 从节点 |
| `TDengine 和 TDengine3 不应该在同一个服务器上` | 两个时序库同 IP | 分配到不同服务器 |
| `ES服务器IP不能为空!` | 配置了 ES 相关服务但未配 IP | 配置 ES 服务器 |

### Q10: "xxx安装失败！"
**排查步骤**:
1. **查看 Ansible 日志**（最重要）:
   ```bash
   tail -200 /var/log/ansible.log
   ```
2. **找到失败的具体任务**: 日志中搜索 `FATAL` 或 `failed`
3. **常见 Ansible 失败原因**:

| 失败类型 | 排查方法 |
|---|---|
| `UNREACHABLE` | 目标机器网络不通或 SSH 失败 |
| `Permission denied` | 文件权限问题，检查 egova 用户权限 |
| `Module failed` | Ansible 模块执行失败，查看详细 stderr |
| `Timeout` | 操作超时，可能是网络慢或服务未启动 |
| `Port already in use` | 端口冲突，检查已有服务 |

4. **重试**: 修复问题后重新运行部署，已成功的组件会自动跳过（`metadata.yml` 中状态为 `success`）

### Q11: 端口冲突
**场景**: 同一台服务器上重复安装同一类型服务。

**系统行为**: 安装前会检查 `metadata.yml`，如果发现同一 host + port 已有 `success` 状态的记录，会提示"已安装过"。

**解决**:
- 如果是误操作: 直接忽略，不会重复安装
- 如果需要重新安装: 
  ```bash
  # 方法1: 通过工具箱安装时会提示"是否强制安装"
  # 方法2: 手动修改 metadata.yml 中对应记录的状态为 "delete"
  ```

### Q12: 某个微服务依赖配置报错"未找到xxx安装信息，请先配置！"
**原因**: 该微服务依赖的组件（如 MySQL、Redis、Nacos）尚未安装或未在 metadata.yml 中有 `success` 记录。

**解决**: 先安装依赖组件（菜单选项 `4` 软件工具箱，或选项 `3` 安装基础平台微服务），再安装该微服务。

### Q13: 灵珑组件初始化失败
**排查**:
1. 确认灵珑服务已安装成功（`metadata.yml` 中 `microservice.linglong.linglong_1.status == "success"`）
2. 确认 `ansible/inventory/linglong_init.yml` 文件存在
3. 确认灵珑组件包存在: `src/web/{ms_type}/{ms_type}-linglong.tar`
4. 查看 Ansible 日志: `tail -200 /var/log/ansible.log`

---

## 六、Ansible 通用问题

### Q14: "Error: ansible could not resolve the host"
**原因**: `hosts.yml` 中的主机名无法解析。

**解决**: 确保 `hosts.yml` 中使用的是 IP 地址而非主机名，或者 DNS/hosts 文件已配置。

### Q15: Ansible 执行很慢
**优化**:
1. 确保 `ansible.cfg` 中 `gathering = explicit`（已自动配置）
2. 检查 `display_skipped_hosts = False`（已自动配置）
3. 网络问题: 检查主控到子控的网络延迟
   ```bash
   ping {子控IP}
   ```

### Q16: Ansible 任务卡住不动
**解决**:
1. `Ctrl+C` 终止
2. 查看目标机器是否有进程卡住: `ssh root@{ip} "ps aux | grep ansible"`
3. 杀掉卡住的进程后重试

---

## 七、服务运行问题

### Q17: 服务启动失败
```bash
# 查看服务状态
systemctl status {service_name}

# 查看服务日志
journalctl -u {service_name} -n 100 --no-pager

# 查看应用日志
tail -100 /egova/log/{service_name}/{service_name}.log
```

### Q18: 微服务启动后无法访问
**排查**:
1. 确认服务已启动: `systemctl status {service_name}`
2. 确认端口监听: `netstat -tlnp | grep {port}`
3. 确认防火墙: `firewall-cmd --list-ports`
4. 确认 Nginx 路由配置: `cat /egova/conf/nginx/*.conf`
5. 确认出口 Nginx 配置正确

### Q19: Nginx 502 Bad Gateway
**原因**: Nginx 无法连接到后端服务。

**排查**:
1. 确认后端服务已启动
2. 确认 Nginx 配置中的 upstream 地址和端口正确
3. 查看 Nginx 错误日志: `tail -50 /egova/log/nginx/error.log`

---

## 八、数据库相关

### Q20: MySQL 安装失败
**排查**:
1. 检查磁盘空间: `df -h`（MySQL 数据目录需要充足空间）
2. 检查是否已有 MySQL 实例运行: `netstat -tlnp | grep 3306`
3. 查看 Ansible 日志: `tail -200 /var/log/ansible.log`
4. 检查 MySQL 数据目录权限: `ls -la /egova/data/mysql/`

### Q21: 数据库切换后服务无法连接
**排查**:
1. 确认数据库连接信息正确（IP、端口、用户名、密码、Schema）
2. 确认数据库已创建对应的库和 Schema
3. 确认网络可达: `telnet {db_ip} {db_port}`
4. 确认防火墙放行数据库端口
5. 确认 env 文件修改已生效（可能需要重启服务）

---

## 九、其他常见问题

### Q22: 磁盘空间不足
```bash
# 检查磁盘使用
df -h

# 检查大文件
du -sh /egova/* | sort -rh | head -20

# 清理临时文件
rm -rf /egova/temp/*
rm -rf /egova/tmp/*
```

### Q23: 时间不同步导致问题
```bash
# 同步时间
ntpdate ntp.aliyun.com
# 或
chronyc makestep

# 确认时间
date
```

### Q24: egova 用户相关
部署工具会自动创建 `egova` 用户。如遇权限问题：
```bash
# 确认用户存在
id egova

# 检查目录权限
ls -la /egova/

# 修复权限
chown -R egova:egova /egova/apps/
chown -R egova:egova /egova/data/
chown -R egova:egova /egova/web/
chown -R egova:egova /egova/log/
```

### Q25: 更新 oneinstall 后出现问题
**解决**: 
1. 检查更新日志: `cat update.sh`
2. 如果更新后部署脚本异常，可以回退到上一个版本（通过 git）
3. 更新不会影响已部署的服务（`/egova/` 目录下的内容不会被更新覆盖）
