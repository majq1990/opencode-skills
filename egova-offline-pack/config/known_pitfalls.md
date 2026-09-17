# egova 离线打包 · 坑位档案

> 每次踩坑后追加；事实优先，不猜测。

## P1. .gitignore 误挡 jar
- **现象**：`git status` 看不到 repo/ 下的 jar，提交后依赖缺失
- **原因**：`.gitignore` 含 `**/*.jar` 或 `*.jar`
- **解决**：删除对应行（工具 fix_gitignore 自动处理）
- **实测**：ibility-platform 根 .gitignore 第 24 行 `**/*.jar`

## P2. _remote.repositories 来源标记
- **现象**：离线编译报 `artifact X is present, but unavailable` 或 `has not been downloaded from it before`
- **原因**：repo 从 Nexus 下载时有 `_remote.repositories` 记录来源仓库 id；离线时当前上下文无该 id → Maven 判不可用
- **解决**：`find repo -name "_remote.repositories" -delete` + `find repo -name "*.lastUpdated" -delete`
- **实测**：ibility 清 1880 个；drainage 清 259 个后离线通过

## P3. Maven 3.8+ 屏蔽 HTTP 仓库
- **现象**：`Blocked mirror for repositories: [egova (http://...)]`
- **原因**：Maven 3.9 默认 maven-default-http-blocker 拦 HTTP
- **解决**：提供 settings.xml 加 mirror `<mirrorOf>external:http:*</mirrorOf>` → 内网 Nexus；或降低 Maven 版本
- **实测**：本机 Maven 3.9.9 需 settings；服务器 Maven 3.6.3 无此问题

## P4. go-offline 覆盖不全编译期传递依赖
- **现象**：go-offline 显示 SUCCESS，但 clean package 时缺某 jar（如 egova-urbanpro-mis-common-base）
- **原因**：go-offline 只解析部分 phase 依赖树
- **解决**：在线完整 `mvn clean install` 兜底，缺哪个自动补哪个，再离线验证
- **实测**：drainage 两次因 go-offline 漏依赖，在线 install 后补齐

## P5. JDK 必须 8
- **现象**：`java.lang.NoSuchFieldError: Class com.sun.tools.javac.tree.JCTree$JCImport does not have member field 'qualid'`
- **原因**：项目 `maven.compiler.source=8`，且依赖含 JDK8 内部 API 的注解处理器
- **解决**：JAVA_HOME 指向 JDK8 编译
- **实测**：本机 jdk1.8.0_361 通过；JDK21 失败

## P6. git-commit-id-maven-plugin 需 .git
- **现象**：`Error: Could not get HEAD Ref, are you sure you have some commits in the dotGitDirectory?`
- **原因**：git-commit-id-maven-plugin 需要 .git 目录有提交
- **解决**：打包保留 .git；或 `git init && git add -A && git commit`；或 `-Dmaven.gitcommitid.skip=true`
- **实测**：drainage-service 模块启用该插件；服务器无 .git 时失败

## P7. 快传链接 vs 分享链接
- **现象**：`aliyunpan share set -mode 1/2` 报"只有资源库才支持分享链接"
- **原因**：当前网盘为"备份盘"，不支持普通分享
- **解决**：用 `-mode 3`（快传），`-time 0` 永久
- **实测**：`https://www.alipan.com/t/OW023CcmRqVsSs4dnGt9`

## P8. dws 发文件到群
- **命令**：`dws chat message send --group <openConversationId> --msg-type file --file-path <本地>` 
- @人：`--at-open-dingtalk-ids <openDingTalkId>`，消息内占位符 `<@openDingTalkId>`
- 群 id 查询：`dws chat search --keyword <群名>`