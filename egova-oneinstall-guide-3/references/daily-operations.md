# 日常运维操作手册

## 一、查看部署状态

### 1.1 查看所有已部署服务
```bash
cat ansible/inventory/metadata.yml
```

### 1.2 查看已添加的服务器节点
```bash
cat ansible/inventory/hosts.yml
```

### 1.3 通过 Ansible 查看所有主机状态
```bash
cd /path/to/oneinstall_v2
ansible all -i ansible/inventory/hosts.yml -m ping
```

### 1.4 查看特定服务的部署信息
```bash
# 查看某个微服务的配置
yq '.microservice.linglong' ansible/inventory/metadata.yml

# 查看某个软件的状态
yq '.mysql' ansible/inventory/metadata.yml
```

---

## 二、服务启停管理

### 2.1 在主控机上管理所有节点

```bash
# 查看所有节点的服务状态
ansible all -i ansible/inventory/hosts.yml -m shell -a "systemctl status {service_name}"

# 重启某台机器的服务
ansible {node_name} -i ansible/inventory/hosts.yml -m shell -a "systemctl restart {service_name}"

# 停止服务
ansible {node_name} -i ansible/inventory/hosts.yml -m shell -a "systemctl stop {service_name}"

# 启动服务
ansible {node_name} -i ansible/inventory/hosts.yml -m shell -a "systemctl start {service_name}"
```

### 2.2 常见服务名称

| 服务 | service 名称 | 说明 |
|---|---|---|
| 灵珑 | `linglong` | 基础平台核心 |
| 悟空 | `wukong` | 数据中台 |
| 星桥 | `xingqiao` | 集成平台 |
| 用户中心 | `usercenter` | 统一用户管理 |
| Nacos | `nacos` | 服务注册/配置 |
| MySQL | `mysqld` 或 `mysql` | 数据库 |
| Redis | `redis` 或 `redis-server` | 缓存 |
| Nginx | `nginx` | Web 服务器 |
| MinIO | `minio` | 对象存储 |
| Kafka | `kafka` | 消息队列 |
| Elasticsearch | `elasticsearch` | 搜索引擎 |
| Zookeeper | `zookeeper` | 协调服务 |
| TDengine | `taosd` 或 `tdengine` | 时序数据库 |

### 2.3 查看服务日志

```bash
# systemd 日志
journalctl -u {service_name} -f --no-pager

# 应用日志
tail -f /egova/log/{service_name}/{service_name}.log

# 在远程机器上查看
ansible {node_name} -i ansible/inventory/hosts.yml -m shell -a "tail -100 /egova/log/{service_name}/{service_name}.log"
```

---

## 三、更新微服务（打补丁包）

### 3.1 使用一键更新脚本

```bash
# 进入部署目录
cd /path/to/oneinstall_v2

# 将更新包放到 /egova/update/ 目录下
# 支持 .zip 格式，脚本会自动解压

# 执行更新（需要传入 hostgroup）
./shell/tools/onekey_update_service.sh {hostgroup}
```

**更新流程**:
1. 自动解压 `/egova/update/` 下的 zip 包
2. 选择更新的产品类型（智信云 / 微服务）
3. 自动更新后端 jar 包和前端文件
4. **需要手动重启服务**

### 3.2 手动更新单个微服务

```bash
# 1. 找到微服务的部署路径
yq '.microservice.{ms_type}.{ms_type}_1.base_path' ansible/inventory/metadata.yml

# 2. 停止服务
ssh root@{ip} "systemctl stop {service_name}"

# 3. 替换 jar 包
scp {new_jar} root@{ip}:/egova/apps/basic/{ms_type}/{ms_type}.jar

# 4. 启动服务
ssh root@{ip} "systemctl start {service_name}"

# 5. 验证
ssh root@{ip} "systemctl status {service_name}"
```

### 3.3 批量重启服务

```bash
# 重启所有节点的某类服务
ansible all -i ansible/inventory/hosts.yml -m shell -a "systemctl restart {service_name}"

# 重启特定分组
ansible {group_name} -i ansible/inventory/hosts.yml -m shell -a "systemctl restart tomcat-{hostgroup}"
```

---

## 四、数据库切换

### 4.1 使用一键切换功能（菜单选项 `m`）

1. 运行 `./install.sh`，选择 `m`
2. 选择数据库类型:
   - `1`: 达梦 (dm)
   - `2`: PostgreSQL
   - `3`: 瀚高 (highgo)
3. 选择产品类型（微服务 / 智信云）
4. 输入数据库连接信息
5. 自动推送到所有节点

### 4.2 手动修改数据库连接

**微服务 (.env 文件)**:
```bash
# 找到 env 文件路径
yq '.microservice.{ms_type}.{ms_type}_1.base_path' ansible/inventory/metadata.yml

# 编辑 env 文件
vi {base_path}/{ms_type}.env

# 修改以下配置:
--DATASOURCE_URL=jdbc:{db_type}://{host}:{port}/{db_name}
--DATASOURCE_DRIVER={driver_class}
--DATASOURCE_USERNAME={user}
--DATASOURCE_PASSWORD={password}
```

**智信云 (jdbc.properties)**:
```bash
vi /egova/web/{app_name}/WEB-INF/classes/jdbc.properties

# 修改以下配置:
biz.jdbc.url=jdbc:{db_type}://{host}:{port}
biz.jdbc.driverClassName={driver_class}
biz.jdbc.username={user}
biz.jdbc.cryptogram={password}
```

### 4.3 各数据库驱动类名

| 数据库 | 驱动类名 | URL 格式 |
|---|---|---|
| MySQL | `com.mysql.jdbc.Driver` | `jdbc:mysql://{host}:{port}` |
| 达梦 | `dm.jdbc.driver.DmDriver` | `jdbc:dm://{host}:{port}?clobAsString=true` |
| PostgreSQL | `org.postgresql.Driver` | `jdbc:postgresql://{host}:{port}/{db_name}?currentSchema={schema},public` |
| 瀚高 | `com.highgo.jdbc.Driver` | `jdbc:highgo://{host}:{port}/{db_name}?currentSchema={schema}` |

---

## 五、配置出口 Nginx

### 5.1 手动配置（菜单选项 `101`）

当微服务独立安装时（非完整场景部署），需要手动配置 Nginx 路由：

```bash
./install.sh
# 选择 101
# 选择微服务类型
# 选择出口 Nginx 节点
```

### 5.2 查看 Nginx 配置

```bash
# 主 Nginx 配置
cat /egova/conf/nginx/nginx.conf

# 站点配置
ls /egova/conf/nginx/conf.d/

# OpenResty 配置
cat /egova/conf/nginx/openresty_nginx.conf
```

### 5.3 重载 Nginx

```bash
ssh root@{nginx_ip} "nginx -t && nginx -s reload"
```

---

## 六、MinIO 对象存储管理

### 6.1 创建桶和用户

微服务部署时会自动创建所需桶和用户。手动操作：

```bash
# 配置 MinIO 客户端连接
mc config host add myminio http://{minio_ip}:{minio_port} {access_key} {secret_key}

# 创建桶
mc mb myminio/{bucket_name} -p

# 创建用户
mc admin user add myminio {username} {password}

# 赋予权限
mc admin policy attach myminio readonly --user {username}
mc admin policy attach myminio writeonly --user {username}
```

---

## 七、Nacos 配置管理

### 7.1 访问 Nacos 控制台

```
http://{nacos_ip}:8848/nacos
默认用户名: nacos
默认密码: nacos
```

### 7.2 微服务命名空间

微服务部署时会自动创建对应的 Nacos 命名空间。

---

## 八、备份与恢复

### 8.1 数据库备份

```bash
# MySQL 备份
mysqldump -u{user} -p{password} {db_name} > {db_name}_backup.sql

# 通过 xtrabackup（安装时已部署）
# 物理备份在 /egova/data/mysql/backup/ 下
```

### 8.2 配置文件备份

```bash
# 备份关键配置
cp -r ansible/inventory/ ansible/inventory_backup_$(date +%Y%m%d)
cp -r /egova/conf/ /egova/conf_backup_$(date +%Y%m%d)
```

### 8.3 metadata.yml 备份

`metadata.yml` 是部署状态的唯一记录，非常重要：
```bash
cp ansible/inventory/metadata.yml ansible/inventory/metadata.yml.bak
```

---

## 九、扩容操作

### 9.1 增加新的应用服务器

1. 运行 `./install.sh` → 选择 `2` 添加新服务器
2. 选择 `3` → 对应的服务类型 → 选择安装方式
3. 在 IP 配置中为新服务器分配角色
4. 确认安装

### 9.2 增加数据库从节点

1. 进入分布式部署 IP 配置界面
2. 选择 `a`（增加从节点）
3. 选择要增加从节点的主机类型
4. 输入从节点对应的服务器编号
5. 系统自动安装从库并配置主从同步

### 9.3 添加新的微服务

1. 运行 `./install.sh` → 选择 `3` → 选择微服务类别（如 `3` 基础平台微服务）
2. 选择要部署的微服务
3. 配置依赖组件（选择已部署的 MySQL、Redis 等）
4. 选择目标服务器
5. 确认安装

---

## 十、卸载与清理

### 10.1 卸载单个服务

```bash
# 停止服务
ssh root@{ip} "systemctl stop {service_name} && systemctl disable {service_name}"

# 删除应用文件
ssh root@{ip} "rm -rf /egova/apps/basic/{service_name}"

# 更新 metadata.yml 状态为 delete
yq -i '.{type}.{key}.status = "delete"' ansible/inventory/metadata.yml
```

### 10.2 清理整个部署

> **警告**: 以下操作会删除所有已部署的服务和数据，请确保已备份！

```bash
# 在所有节点执行
ansible all -i ansible/inventory/hosts.yml -m shell -a "rm -rf /egova/apps /egova/data /egova/web /egova/work /egova/deploy"

# 清理 metadata.yml
echo '{}' > ansible/inventory/metadata.yml
```
