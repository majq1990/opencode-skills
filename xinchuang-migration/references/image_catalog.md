# 信创迁移文档图片索引

> 来源：信创迁移文档_辽宁区域.docx
> 共 77 张截图，按迁移阶段分类索引
> 路径：`assets/` 目录下

## 一、前期准备（01-06）

| 图片文件 | 说明 | 文档上下文 |
|----------|------|------------|
| 01_prep_os_version_check.png | 服务器版本兼容性检查 | 服务器版本是否兼容公司脚本 |
| 02_prep_os_version_detail.png | 查看系统小版本（统信1060e） | cat /etc/os-version 查看版本 |
| 03_prep_product_version_check.png | 确认老服务器产品版本 | 确认老服务器各产品版本是否满足迁移要求 |
| 04_prep_product_version_detail.png | 产品版本详情 | 确认老服务器各产品版本是否满足迁移要求 |
| 05_prep_dameng_error_pattern.png | 达梦迁移工具常见报错 | 执行语句报错时联系厂商建立模式 |
| 06_prep_dameng_error_solution.png | 报错解决方案 | 达梦迁移工具报错处理 |

## 二、老服务器迁移（07）

| 图片文件 | 说明 | 文档上下文 |
|----------|------|------------|
| 07_oldserver_compress_package.png | 老服务器产品包压缩 | tar -zcvf eUrbanMIS.tar.gz eUrbanMIS/ |

## 三、服务启动（08-12）

| 图片文件 | 说明 | 文档上下文 |
|----------|------|------------|
| 08_service_stop_tomcat.png | 停止 Tomcat 进程 | ps -ef \| grep tomcat, kill -9 进程号 |
| 09_service_stop_tomcat_detail.png | kill 进程号详情 | 进入 /egova/tomcat-xxx/bin 目录 |
| 10_service_tomcat_log.png | Tomcat 日志目录 | /egova/tomcat-xxx/log/catalina.xxx.out |
| 11_basic_products_status.png | 基础产品状态查看 | linglong/wukong/dex/evaluation/usercenter/xuanzang |
| 12_basic_products_log.png | 基础产品日志位置 | 日志在对应产品目录的 log 目录下 |

## 四、达梦数据库部署（13-25）

| 图片文件 | 说明 | 文档上下文 |
|----------|------|------------|
| 13_dameng_create_user.png | 创建 dmdba 用户 | 创建用户命令 |
| 14_dameng_set_password.png | 修改用户密码 | 修改密码命令 |
| 15_dameng_limits_conf.png | 修改文件打开最大数 | /etc/security/limits.conf 配置 |
| 16_dameng_directory_plan.png | 目录规划 | 实例保存/归档/备份目录 |
| 17_dameng_create_dirs.png | 创建目录 | mkdir -p 创建实例/归档/备份目录 |
| 18_dameng_chown_dirs.png | 修改目录权限 | chown dmdba:dinstall |
| 19_dameng_install_step1.png | 达梦安装步骤1 | 命令行安装 |
| 20_dameng_install_step2.png | 达梦安装步骤2 | 命令行安装 |
| 21_dameng_install_step3.png | 达梦安装步骤3 | 命令行安装 |
| 22_dameng_install_step4.png | 达梦安装步骤4 | 命令行安装 |
| 23_dameng_config_instance.png | 配置实例 | dmdba 用户配置实例，bin 目录中执行 |
| 24_dameng_register_service.png | 注册服务 | ./dm_service_installer.sh -t dmserver |
| 25_dameng_start_stop.png | 启动/停止服务 | 达梦服务启停 |

## 五、金蝶中间件部署（26-52）

### 5.1 安装与启动

| 图片文件 | 说明 | 文档上下文 |
|----------|------|------------|
| 26_aas_deploy_extract.png | 金蝶安装包解压 | 上传到 /egova 并解压 |

### 5.2 配置 JDBC 连接池

| 图片文件 | 说明 | 文档上下文 |
|----------|------|------------|
| 27_aas_jdbc_pool_mysql.png | 新建 MySQL 连接池 | 资源类型 java.sql.Driver |
| 28_aas_jdbc_pool_config.png | 连接池参数配置 | 驱动类名/URL/用户名/口令 |
| 29_aas_jdbc_pool_save.png | 保存连接池 | 保存配置 |

### 5.3 创建实例与 JDBC 资源

| 图片文件 | 说明 | 文档上下文 |
|----------|------|------------|
| 30_aas_create_instance.png | 创建独立实例 | 以独立实例为例 |
| 31_aas_instance_config1.png | 实例配置1 | 创建 JDBC 资源 |
| 32_aas_instance_config2.png | 实例配置2 | 创建 JDBC 资源 |
| 33_aas_instance_config3.png | 实例配置3 | 创建 JDBC 资源 |
| 34_aas_instance_config4.png | 实例配置4 | 创建 JDBC 资源 |
| 35_aas_instance_config5.png | 实例配置5 | 创建 JDBC 资源 |

### 5.4 部署应用

| 图片文件 | 说明 | 文档上下文 |
|----------|------|------------|
| 36_aas_deploy_war_upload.png | 上传 WAR 包 | 部署应用 |
| 37_aas_deploy_select_war.png | 选择 WAR 包 | 选择应用目录或上传 |
| 38_aas_deploy_context_path.png | 上下文路径 | 填写上下文路径 |
| 39_aas_deploy_upload_step.png | 上传步骤1 | 点击上传，下一步 |
| 40_aas_deploy_upload_step2.png | 上传步骤2 | 上传过程 |
| 41_aas_deploy_upload_step3.png | 上传步骤3 | 上传完成 |
| 42_aas_deploy_context_config.png | 上下文配置 | 填写上下文路径，其他默认 |
| 43_aas_deploy_select_instance.png | 选择部署实例 | 选择刚创建的实例 |
| 44_aas_deploy_confirm.png | 确认部署 | 点击确定，等待部署 |
| 45_aas_deploy_running_status.png | 应用运行状态 | 应用管理中查看状态 |
| 46_aas_deploy_verify_url.png | URL 验证 | http://ip:端口/eUrbanxxx 验证 |

### 5.5 端口配置与日志

| 图片文件 | 说明 | 文档上下文 |
|----------|------|------------|
| 47_aas_port_config.png | 端口配置1 | 端口配置 |
| 48_aas_port_config2.png | 端口配置2 | 端口配置 |
| 49_aas_view_log.png | 查看日志1 | 查看日志 |
| 50_aas_view_log_server.png | 查看日志-点进服务器 | 点进服务器 |
| 51_aas_view_raw_log.png | 查看原始日志 | 点击查看原始日志 |
| 52_aas_view_log_detail.png | 日志详情 | 日志详情 |

## 六、数据迁移工具 DTS（53-66）

| 图片文件 | 说明 | 文档上下文 |
|----------|------|------------|
| 53_dts_download_dameng.png | 下载达梦迁移工具 | 本地电脑下载达梦 |
| 54_dts_custom_type_mapping.png | 设置自定义类型映射 | 迁移前设置自定义类型 |
| 55_dts_custom_type_detail.png | 自定义类型详情 | 不勾选"使用默认数据类型映射" |
| 56_dts_new_migration.png | 新增迁移 | 名称自定，最大保留次数改-1 |
| 57_dts_migration_config.png | 迁移配置 | 填写信息 |
| 58_dts_select_tables.png | 勾选创建模式和表 | cgdb 目标模式 DLMIS |
| 59_dts_select_tables2.png | 选择表2 | 勾选创建模式和表 |
| 60_dts_select_tables3.png | 选择表3 | 勾选创建模式和表 |
| 61_dts_select_all_tables.png | 选择所有表 | 选择所有的表 |
| 62_dts_data_transform.png | 数据转换 | 随便选择一条数据，点击转换 |
| 63_dts_transform_config.png | 转换配置 | 按照下图选择 |
| 64_dts_start_migration.png | 开始迁移 | 后续便开始执行迁移 |
| 65_dts_migration_progress.png | 迁移进度 | 迁移执行中 |
| 66_dts_migration_complete.png | 迁移完成 | 迁移完成 |

## 七、各产品配置修改（67-77）

| 图片文件 | 说明 | 文档上下文 |
|----------|------|------------|
| 67_config_modify_ip_password.png | 修改 IP 和密码 | 修改红色标记的 IP 和密码 |
| 68_config_reg_properties.png | 修改 reg.properties | reg.properties 配置 |
| 69_config_reg_properties_detail.png | reg.properties 详情 | 置空 MD5 的值 |
| 70_config_gis_giscenter_env.png | GIS 修改 giscenter.env | egovagisserver 的 giscenter.env |
| 71_config_linglong_env.png | 灵珑修改 linglong.env | linglong.env 文件 |
| 72_config_usercenter_evaluation_env.png | 用户中心/毕升 env | usercenter.env / evaluation.env |
| 73_config_mjing_env.png | 明镜修改 mjing.env | mjing.env 文件 |
| 74_config_iot_application_properties.png | 物联网修改 application.properties | jdbc:dm://...?clobAsString=true |
| 75_config_dameng_params.png | 达梦参数配置 | 达梦参数 |
| 76_config_migrate_data1.png | 迁移数据1 | 迁移数据 |
| 77_config_migrate_data2.png | 迁移数据2 | 迁移数据 |
