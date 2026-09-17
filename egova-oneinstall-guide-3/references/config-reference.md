# 配置文件参考

## 一、ansible/inventory/hosts.yml — 服务器节点清单

### 1.1 作用
定义所有参与部署的服务器节点。主控机通过 SSH 连接到这些节点执行 Ansible 任务。

### 1.2 结构说明
```yaml
all:
  hosts:
    node1:                          # 节点名称（自动递增: node1, node2...）
      ansible_ssh_host: "192.168.1.10"   # 服务器 IP
      ansible_ssh_port: "22"             # SSH 端口
  children:
    mysql:                        # 主机组（按服务类型分组）
      hosts:
        node1: ""                 # 该节点属于 mysql 组
    redis:
      hosts:
        node2: ""
    microservice:
      hosts:
        node1: ""
    # ... 其他组
```

### 1.3 常用操作
```bash
# 查看所有节点
yq '.all.hosts' ansible/inventory/hosts.yml

# 查看节点分组
yq '.all.children' ansible/inventory/hosts.yml

# 获取某个节点的 IP
yq '.all.hosts.node1.ansible_ssh_host' ansible/inventory/hosts.yml
```

---

## 二、ansible/inventory/metadata.yml — 部署元数据

### 2.1 作用
记录所有组件的部署状态、配置信息、依赖关系。这是**最核心**的状态文件，安装引擎根据此文件决定跳过已安装组件或处理依赖。

### 2.2 结构说明
```yaml
software:                          # 基础软件
  mysql:
    mysql_1:                       # 软件名_序号（自动递增）
      name: "MySQL业务库"           # 显示名称
      host: "node1"               # 部署在哪个节点
      ip: "192.168.1.10"          # 服务器 IP
      port: "3306"                # 服务端口
      db_type: "biz"              # 数据库类型（biz/stat）
      status: "success"           # 状态: undeployed / success / delete
      wiki: "..."                 # Wiki 文档链接
      login_url: "..."            # 登录地址
      user: "root"                # 用户名
      password: "..."             # 密码
  redis:
    redis_1:
      name: "Redis"
      host: "node1"
      ip: "192.168.1.10"
      port: "6379"
      status: "success"
  # ... nacos, kafka, minio 等

microservice:                      # 微服务
  linglong:
    linglong_1:
      name: "灵珑"
      host: "node1"
      ip: "192.168.1.10"
      server_port: "8080"         # 微服务端口
      base_path: "/egova/apps/basic/linglong"  # 部署路径
      jar_name: "linglong.jar"    # jar 包名
      status: "success"
      depends:                     # 依赖列表
        - type: "mysql"
          name: "MySQL"
          sub_type: "biz"
          depend_key: "mysql_1"   # 依赖的 mysql_1 实例
        - type: "redis"
          name: "Redis"
          depend_key: "redis_1"
      login_url: "http://192.168.1.10:8080/linglong"
      user: "admin"
      password: "..."

service:                           # Tomcat 类应用（智信云等）
  eUrbanSG:
    eUrbanSG_1:
      name: "智信云"
      host: "node1"
      ip: "192.168.1.10"
      server_port: "8080"
      status: "success"
      # ...
```

### 2.3 状态说明
| 状态 | 含义 | 安装引擎行为 |
|---|---|---|
| `undeployed` | 已生成待安装记录，但未安装 | 尝试安装 |
| `success` | 安装成功 | 跳过，不重复安装 |
| `delete` | 已标记删除 | 跳过 |

### 2.4 常用操作
```bash
# 查看所有已部署成功的微服务
yq '.microservice | .. | select(.status == "success") | .name' ansible/inventory/metadata.yml

# 查看某个微服务的依赖配置
yq '.microservice.linglong.linglong_1.depends' ansible/inventory/metadata.yml

# 修改某个服务的状态
yq -i '.microservice.linglong.linglong_1.status = "delete"' ansible/inventory/metadata.yml

# 查看所有已部署服务的完整信息（IP、端口、登录地址等）
yq '.microservice, .service' ansible/inventory/metadata.yml
```

---

## 三、ansible/group_vars/all.yml — 全局变量

### 3.1 关键配置项

| 变量 | 默认值 | 说明 |
|---|---|---|
| `devops_ssh_user` | `root` | SSH 连接用户名 |
| `devops_ssh_port` | `22` | SSH 默认端口 |
| `devops_ssh_key` | `/root/.ssh/id_ed25519` | SSH 密钥路径 |
| `ansible_master_ip` | 自动检测 | 主控机 IP |
| `app_root_dir` | `/egova/apps/basic` | 应用部署根目录 |
| `data_root_dir` | `/egova/data` | 数据根目录 |
| `web_root_dir` | `/egova/web` | Web 根目录 |
| `log_root_dir` | `/egova/log` | 日志根目录 |
| `tools_root_dir` | `/egova/tools` | 工具根目录 |
| `conf_root_dir` | `/egova/conf` | 配置根目录 |
| `ops_user` | `egova` | 运维用户 |
| `common_password` | `Wk2uBTeyp6` | 通用密码 |
| `PG_password` | `Wk2uBTeyp6` | PostgreSQL 密码 |
| `mysql_port` | `3306` | MySQL 端口 |
| `proxy_biz_flag` | `0` | 业务库代理开关（0关/1开） |
| `proxy_stat_flag` | `0` | 统计库代理开关 |
| `debug_flag` | `0` | 调试模式（0关/1开） |
| `default_jdk_version` | `8` | 默认 JDK 版本 |
| `egova_local_port` | `7777` | 本地源 Nginx 端口 |

### 3.2 修改方法
```bash
# 修改 SSH 端口
yq -i '.devops_ssh_port = "2222"' ansible/group_vars/all.yml

# 修改通用密码
yq -i '.common_password = "NewPassword123"' ansible/group_vars/all.yml

# 修改应用部署路径
yq -i '.app_root_dir = "/data/apps"' ansible/group_vars/all.yml
```

---

## 四、option_config.yml — 菜单选项配置

### 4.1 作用
定义主菜单中显示的选项及其对应的功能。

### 4.2 关键字段

| 字段 | 说明 |
|---|---|
| `name` | 菜单显示名称 |
| `display` | 是否显示（1 显示 / 0 隐藏） |
| `choice_index` | 菜单选择编号 |
| `sub_options` | 子菜单配置 |

### 4.3 修改示例
```yaml
# 隐藏某个菜单选项
benchmark_check:
  name: 基准检查
  display: 0          # 改为 0 即可隐藏
  choice_index: b
```

---

## 五、shell/template/microservice_template.yml — 微服务模板

### 5.1 作用
定义所有可部署微服务的元信息，包括名称、端口、依赖关系、环境变量等。

### 5.2 关键字段
```yaml
linglong:
  name: "灵珑"                    # 显示名称
  display: "1"                    # 是否在菜单中显示
  category: "basic"               # 所属类别
  server_port: 8080               # 默认端口
  base_path: "/egova/apps/basic/linglong"  # 部署路径
  jar_name: "linglong.jar"        # jar 包名称
  environment:
    jvm_opts: "-Xms512m -Xmx1024m"  # JVM 参数
  depends:                         # 依赖列表
    - type: "mysql"
      name: "MySQL业务库"
      sub_type: "biz"
    - type: "redis"
      name: "Redis"
```

---

## 六、ansible/inventory/software_tools.yml — 软件工具配置

### 6.1 作用
定义"软件部署工具箱"（菜单选项 4）中可单独安装的软件及其参数。

### 6.2 结构
```yaml
software_tools:
  - name: "mysql"                 # 软件名称
    desc: "MySQL数据库"           # 描述
    params:                       # 安装参数
      - name: "port"
        desc: "端口号"
        display: "1"              # 是否在安装时显示
        default: "3306"
      - name: "password"
        desc: "root密码"
        display: "1"
        default: "Egova@2024"
```

---

## 七、multi_server.yml / eurbanpro_multi_server.yml — 分布式部署配置

### 7.1 作用
定义分布式部署中各服务器角色的分配关系。

### 7.2 关键字段
```yaml
ip_db_biz:
  name: "业务数据库"
  choice_index: "1"
  need_flag: "1"                  # 是否必填
  sub_flag: "0"                   # 是否支持从节点（0否/1是）
  deploy_status_flag: "0"         # 部署状态（0未部署/1已部署）
  hosts:
    master: "node1"               # 主节点
    slave: ["node3"]              # 从节点列表
  modules:                        # 该服务器上安装的组件
    - type: "software"
      sub_type: "mysql"
      name: "MySQL业务库"
    - type: "cetus"
      sub_type: "biz"
      name: "Cetus业务代理"
  biz_flag: "0"                   # 是否为业务线服务器
  tiny_flag: "0"                  # 是否参与轻量化部署（1是/0否）
```

---

## 八、shell/template/db_template.yml — 数据库切换模板

### 8.1 作用
定义各数据库类型的连接格式和切换规则。

### 8.2 支持的数据库类型
| 数据库 | choice_index | driver |
|---|---|---|
| 达梦 | 1 | `dm.jdbc.driver.DmDriver` |
| PostgreSQL | 2 | `org.postgresql.Driver` |
| 瀚高 | 3 | `com.highgo.jdbc.Driver` |

---

## 九、系统级配置文件

| 文件路径 | 说明 |
|---|---|
| `/etc/yum.repos.d/egova-oneinstall-local.repo` | 本地 yum 源配置 |
| `/etc/apt/sources.list` | Ubuntu 本地 apt 源配置 |
| `/etc/ansible/ansible.cfg` | Ansible 全局配置 |
| `/var/log/ansible.log` | Ansible 执行日志 |
| `/etc/nginx/conf.d/egova-oneinstall-local-repo-nginx.conf` | 本地源 Nginx 配置 |
| `/egova/conf/nginx/` | 业务 Nginx 配置目录 |
| `/root/.ssh/id_ed25519` | SSH 密钥 |
| `/egova/conf/ssh_{ip}.status` | SSH 免密状态标记文件 |
