# 一键部署脚本说明

## 目录说明

目录 | 说明 | 发布时是否打包
--- | --- | ---
install.sh | 现场运行入口脚本 | 是
ansible | ansible脚本 | 是
shell | shell脚本 | 是
deploy | 发布tar.gz辅助脚本|否

# 信创一键部署开发和维护说明

# 分支说明

| 分支类型 | 分支名称格式 | 核心职责 | 生命周期 |
| --- | --- | --- | --- |
| 主分支（正式版） | main | 存放可部署正式版代码，仅接收测试通过功能的合并； | 永久 |
| 开发分支（测试版） | dev | 集成待测试功能，作为内部测试环境代码来源；仅接收feat/fix分支合并，禁止直接开发。 | 永久 |
| 功能分支（临时） | feat/功能名\[-案件号\] | 单个独立功能的开发迭代载体，从dev拉出；测试通过前合并至dev，通过后合并至main。 | 临时（功能稳定发布后可删除） |
| 修复分支（临时） | fix/问题描述-\[案件号\]（普通修复）、hotfix/问题描述-\[案件号\]（线上紧急修复） | fix分支：修复dev分支问题，从dev拉出并合并回dev；hotfix分支：修复main线上bug，从main拉出并合并回main和dev。 | 临时（修复完成合并后删除） |

## 目录结构

```text/x-java
 tree -L 2
.
├── ansible
│   ├── benchmark_check.yml ##基准检查入口
│   ├── check_main_nginx.yml ## 检查是否安装nginx入口
│   ├── config_minio_bucket.yml
│   ├── config_nacos_namespace.yml
│   ├── config_outlet_nginx.yml
│   ├── filter_plugins
│   ├── group_vars ### 存放全局变量地方
│   ├── init_db.yml ### 初始数据库
│   ├── install_cetus.yml ### 安装cetus入口，install_xxx 均为playbooks(安装软件或服务入口)
│   ├── install_common.yml
│   ├── install_docker.yml
│   ├── install_elasticsearch.yml
│   ├── install_eurbanpro_cetus.yml
│   ├── install_eurbanpro_tomcat_app.yml
│   ├── install_faceserver.yml
│   ├── install_frontend.yml
│   ├── install_IM.yml
│   ├── install_jdk.yml
│   ├── install_kafka.yml
│   ├── install_microservice.yml
│   ├── install_minio.yml
│   ├── install_mysqlclient.yml
│   ├── install_mysql.yml
│   ├── install_nacos.yml
│   ├── install_nginx.yml
│   ├── install_ntp_client.yml
│   ├── install_OnlyOffice.yml
│   ├── install_outginx.yml
│   ├── install_postgresql.yml
│   ├── install_python2.yml
│   ├── install_redis.yml
│   ├── install_statgather.yml
│   ├── install_sysbench.yml
│   ├── install_TDengine.yml
│   ├── install_tiny.yml
│   ├── install_tomcat_app.yml
│   ├── install_tomcat.yml
│   ├── install_videocenter.yml
│   ├── install_video.yml
│   ├── install_xtrabackup.yml
│   ├── install_zookeeper.yml
│   ├── inventory
│   ├── LICENSE.md
│   ├── modify_db.yml ###一键替换信创数据库配置文件入口
│   ├── one_install.yml
│   ├── onekey_update_web.yml
│   ├── README.md
│   └── roles ##安装基础软件role或微服务
├── deploy
│   ├── download ###包含下载脚本dl_v.sh
│   ├── oneinstall_v2.sh ### 全局入口脚本：压测、磁盘挂载、调用install.sh脚本
│   └── package
├── install.sh ### 安装入口脚本
├── option_config.yml ### 配置模版文件，安装面板显示定义在此配置如安装本地源、安装ansible等
├── README.md
├── shell ### 存放shell脚本
│   ├── include
│   ├── template ##微服务和智信云服务配置模版文件
│   ├── toolbox ##安全加固的脚本如弱密码检查、端口加固等
│   ├── tools ##工具类脚本，如本地源创建脚本 i_create_repo_apt.sh
│   └── upgrade
├── update.sh
└── VERSION.md
```

## 关键代码入口解读

### 2.1 dl\_v2.sh

选择操作系统

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/fcddb88c-41a9-48c3-a77e-00db6e6173c4.png)

选择待部署的应用，选择智信云还是麒舰（只会下载待安装的相关服务）

*   选择0：会跳过应用包的下载，比如只想安装基础软件如jdk、onlyoffice等

*   选择2：只下载麒舰相关的应用包


![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/9291ffa1-ee63-405a-a610-7d6fe9a990ab.png)

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/738f00c6-596c-42d3-8bf9-4ba96490a199.png)

以基础平台微服务举例，所有的微服务都以下面格式命名

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/589db6df-74d4-4944-a405-3ce4ecd15509.png)

根据ini文件下载对应web服务包逻辑如下：

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/6b4d6041-dcb2-4c50-aedd-a3d8dfb9055a.png)

### 2.2 install.sh

bash install.sh

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/a930193c-da1e-40c8-abf9-b0d0fe134ae5.png)

上述截图出现的内容都在option\_config.yml配置，不是写死在代码

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/7e3ee625-b5ed-4d75-818e-8bcc7a296506.png)

#### 2.2.1 应用服务部署（继续输入4）

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/75704902-ec14-4e69-b3c9-7065c57719ce.png)

也在option\_config.yml配置文件

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/ebcc7084-8040-4c2b-b359-149e0837b170.png)

具体代码：

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/2b704cc4-83d0-49c5-961d-123d39bb8a03.png)

#### 2.2.2 应用服务部署-基础平台微服务（输入3->32 ）

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/dda44c4e-306c-4517-9ff0-264fbeee2cdc.png)

具体代码：

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/9fa7ad91-0667-4e30-9c41-ec8143179e3e.png)

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/70d81b65-ffb4-4704-ac8f-31c4ec2ce52d.png)

微服务配置文件

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/4dd7ea2b-862b-42b8-bce7-bb5e1fed50c8.png)

#### 2.3 部署软件工具箱（输入4）

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/8df66de3-4ade-4134-b560-33e789c0f66b.png)

基础软件显示也写配置文件中

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/c3f5f694-db62-40df-9d65-50a9c9cd7b8e.png)

具体代码

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/14df4b4c-4c02-402d-b1b6-331f4c37366a.png)

## 增加类似jdk基础软件

*   在roles下面增加文件夹（有意义英文命名，统一小写）


![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/47eb4546-004f-4820-9d7e-d79a791a3f7f.png)

*   install\_xxxx.yml 其中xx 命名要上对应roles下面的基础软件命名一致


![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/fa1cdd4c-01b3-4ee2-94e3-973cc5bbe736.png)

如需增加配置文件，需要在该roles下面增加templates文件夹，后缀以.j2命名

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/47f166e4-f93b-4480-b80d-45fecae5e6bf.png)

**备注：无配置文件不需要增加templates文件夹**

## 信创适配

### 4.1 本地源需要改造

管理源的方式有两种，apt或yum/dnf

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/c39c11df-4ba8-4423-bf9e-ee49a62b153e.png)

### 4.2 ansible安装改造

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/f87cd6e5-64b7-49ba-a3db-1fcfabff3d3d.png)

### 4.3 部分软件安装需改造

根据ansible\_pkg\_mgr变量适配不同操作系统

以安装时序数据库举例，本地原有有对应包，比如ubuntu系统

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/de831d27-8fd2-4564-ac1c-326a968c1590.png)

本地源无对应包，采用二进制安装

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/4890d4b4-c362-42b2-9fcd-7c2e7c52b196.png)

安装mysql不同操作系统对应包不一样，安装方式有差别，如何兼容，参考以下写法

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/4aa38f97-e50d-4576-ab66-169c8abf3964.png)

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/39855b17-2f16-431c-a09c-9040e04aa94d.png)

### 4.4 注意

不管是apt或yum管理，采用本地源安装方式，都统一用package:根据操作系统自动切换apt install xxx 或yum intsall xxx

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/1dac1b4e-0f03-43d9-859b-461e575f7cb7.png)

## 更新说明

将本地代码更新到武汉服务器

```text/x-java
cd  oneinstall_v2
git pull --rebase
if [ $? -eq 0 ]; then
   echo "git pull success"
   cd ../
  tar -czpf oneinstall_v2-code_latest.tar.gz oneinstall_v2/
  scp oneinstall_v2-code_latest.tar.gz root@10.255.1.25:/egova/one/v2/code
fi

```

武汉服务器一键部署目录

```text/x-java
oot@oneops:/egova/one/v2# tree -L 1
.
├── anolis7_x86 ##龙蜥7 x86架构
├── anolis8_arm ##龙蜥8 arm架构
├── anolis8_x86 ##龙蜥8 x86架构
├── automount.sh ##磁盘挂载脚本
├── centos7_x86 ##centos7 x86架构
├── clean_nginx_headers.sh
├── code ##一键部署正式环境代码目录
├── code_test ##一键部署测试环境代码目录
├── db_init
├── dl8.sh
├── dl_v2.sh ##正式下载入口脚本
├── dl_v2_dev.sh ##测试环境下载入口脚本
├── egova-security-toolbox.tar.gz
├── el7
├── el8
├── iniconfig
├── jdk-8u421-linux-aarch64.rpm
├── jdk-8u421-linux-x64.rpm
├── kylinV10_arm ##银河麒麟V10-arm
├── kylinV10_x86 ##银河麒麟V10-x86
├── microservice-web
├── microservice-web-test
├── oneinstall_v2-env-common-bin-arm.tar.gz ##一键部署arm二进制文件
├── oneinstall_v2-env-common-bin-x86.tar.gz ##一键部署x86二进制文件
├── oneinstall_v2-env-common-bin.tar.gz ##一键部署通用二进制文件和初始化数据库文件
├── oneinstall_v2-env-security-toolbox.tar.gz ##一键部署安全加固脚本
├── oneinstall_v2-env-tools-script.tar.gz ##一键部署基础脚本
├── oneinstall_v2-web-20230301 ##智信云应用软件包0301
├── oneinstall_v2-web-20240301 ##智信云应用软件包0401
├── onlyoffice-arm
├── onlyoffice-x86
├── openEuler22_arm ##欧拉22 arm架构的rpm包和特殊的二进制文件
├── openEuler22_x86 ##欧拉22 x86架构的rpm包和特殊的二进制文件
├── sync-to-aliyun.sh ##同步到阿里云脚本
├── ubuntu20_x86 ##ubuntu20 x86架构的rpm包和特殊的二进制文件
├── ubuntu_car ##无人车
├── uos20a_arm ##uos-20-1060a arm架构的rpm包和特殊的二进制文件
├── uos20a_x86 ##uos-20-1060a x86架构的rpm包和特殊的二进制文件
├── uos20e_arm ##uos-20-1060e arm架构的rpm包和特殊的二进制文件
├── uos20e_x86 ##uos-20-1060e x86架构的rpm包和特殊的二进制文件
```

注：更新武汉服务器，需同步更新到阿里云 bash sync-to-aliyun.sh ./

# 常见问题和解决方案

[http://faq.egova.com.cn:7777/projects/redmine/wiki/%E4%BF%A1%E5%88%9B%E4%B8%80%E9%94%AE%E9%83%A8%E7%BD%B2%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98FAQ](http://faq.egova.com.cn:7777/projects/redmine/wiki/%E4%BF%A1%E5%88%9B%E4%B8%80%E9%94%AE%E9%83%A8%E7%BD%B2%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98FAQ)

## 其它问题

1.  微服务多节点分布式部署时如果安装到子控节点时不成功，可以参考去掉文件中connection: local。


问题现象：有类似如下的报错，同时子控节点相关的文件目录或者配置文件均没有拷贝成功

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/2ea6a7f9-598d-4c91-a590-ea7d9c00e659.png)

目标服务器中没有新增对应的目录：

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/79abbe06-59e0-4f99-af24-729747bf8daf.png)

那可能需要修改脚本/oneinstall\_v2/ansible/roles/microservice/tasks/main.yml ，**去掉文件中connection: local**，保证可以多节点部署。（**注意：根据实际情况修改去掉，需要修改的地方不止一次，同时不需要去掉的也别随意去掉了，要仔细测试确认**）

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/5VLqXZ4WbaLZlX19/img/4c775bdd-c6bf-4387-9596-f7c86f3855a9.png)
