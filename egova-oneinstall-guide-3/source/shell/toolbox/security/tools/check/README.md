# 安全检查工具

## 概述
本套脚本用于根据特定工具和配置进行检查。该脚本依赖于以下链接中的文档：
[文档](https://alidocs.dingtalk.com/i/nodes/gwva2dxOW4KpzGNXU6G5Dw4d8bkz3BRL?utm_scene=team_space)（版本：2024/8/8）

## 脚本及其检查项
### 执行脚本 bash main.sh ，选择8
| 脚本名称             | 检查项             |
| :------------------ | :----------------- |
| check_cgdb.sh      | 网格化核心库       |
| check_bisheng.sh   | 毕升               |
| check_dex.sh       | 星桥               |
| check_linglong.sh  | 灵珑               |
| check_smt.sh       | 市民通             |
| check_wukong.sh    | 悟空               |
| check_law.sh       | 执法               |

## 使用说明
1. **选择需要检查产品**：
    - 请根据您的需求选择要检查的产品。
   
2. **数据库连接**：
    - 请根据您的需求修改数据库连接设置。

3. **支持版本**：
    - 本机制仅支持 MySQL 8.0 系列版本。

4. **毕升检查**：
    - 脚本 `check_bisheng.sh` 需要您手动输入 `IP_FIREWALL_BLACKLIST` 和 `IP_FIREWALL_WHITELIST`，即 IP 防火墙黑白名单。
    - 这些信息需要通过交互方式输入。
    - 输入后，将自动保存到当前路径下的 `bisheng_firewall_value.txt` 文件中，以便后续检查使用。

5. **星桥检查**：
    - 脚本 `check_dex.sh` 也需要手动输入 `IP_FIREWALL_BLACKLIST` 和 `IP_FIREWALL_WHITELIST`。
    - 输入的值将保存到当前路径下的 `dex_firewall_value.txt` 文件中，以供后续检查使用。

6. **执法检查**：
    - 脚本 `check_law.sh` 需要您手动输入 `MIS_BUILDER_HUMAN_DEFAULT_PASSWORD`，即新增账号的默认密码。
    - 此密码需要交互输入两次以进行确认。
    - 输入后，将保存到当前路径下的 `law_default_passwd.txt` 文件中，以便后续检查使用。