# Skill: egova-offline-pack

# egova 源码离线打包 Skill

> **版本**：v1.0.0
> **实测**：ibility-platform（backend/ 布局）与 egova-drainage-core（根 pom 布局）均离线 BUILD SUCCESS

## 用途

把 egova 系（ibility / drainage 等）Maven 源码打包成**含离线依赖库、现场可直接复用**的完整离线包：
- 扫描源码全部 pom 依赖 → 从内网 Nexus 补全 repo/ 离线库
- 修复 .gitignore / _remote.repositories / JDK 版本等坑
- 本地 + 服务器离线编译验证
- 打包成 zip 上传阿里云盘，发群分发

## ⚠️ 前置条件：必须能访问内网 Nexus（VPN）

**首次补依赖阶段必须连接公司 VPN**，要求可直连 `npm.egova.com.cn:18081`。

> 若代理/VPN 未挂，本阶段会失败或长期超时。工具会自动探测：
> - 不可达 → 红色提示「请先连接公司 VPN，再重新运行」，随后退出
> - 可达 → 继续下载

**验证可达性：**
```bash
# Windows
Test-NetConnection npm.egova.com.cn -Port 18081

# Linux/macOS
nc -zv npm.egova.com.cn 18081
```

一旦 repo/ 离线库补齐，**后续编译阶段无需网络**（离线 `-o` 模式），可在无网环境进行。

## 工具依赖检查

| 工具 | 用途 | 检查命令 |
|---|---|---|
| java 1.8 | 编译（必须 JDK8） | `java -version` |
| mvn 3.6+ | 构建/下载依赖 | `mvn --version` |
| python3 | fix_repo.py（可选） | `python3 --version` |
| aliyunpan | 上传网盘分发 | `aliyunpan who` |
| zip/tar | 打包 | `zip --version` |

## 触发方式

- 自然语言："这套源码能离线打包吗"、"验证离线编译"、"生成离线复用包"、"打一个含依赖的完整包"、"上传到阿里云盘分发" 等
- 提供源码 zip / 服务器路径 / 本地目录均可

## 输入约定

| 参数 | 默认 | 覆盖示例 |
|---|---|---|
| 源码来源 | 用户提供路径/zip/服务器路径 | "D:\...\egova-drainage-core.zip" |
| 服务器 | gczx.egova.com.cn (root) | "用另一台服务器验证" |
| JDK8 路径（Windows） | C:\Program Files\Java\jdk1.8.0_361 | 自动探测 |
| 内网 Nexus | http://npm.egova.com.cn:18081 | — |
| 阿里云盘目标目录 | / （根） | "上传到 /数字政通相关/" |

## 核心文件

| 文件 | 说明 |
|---|---|
| `scripts/fix_repo.py` | 依赖扫描/下载/修复工具（兼容 Py 3.6~3.13，零依赖） |
| `scripts/fix_repo.bat` | Windows 原生版（双击即用） |
| `scripts/offline_build.sh` | 离线编译封装（自动探测 JDK8 + 打包） |
| `config/known_pitfalls.md` | 坑位档案（见下） |

## 全流程

### 阶段 0：定位源码

1. 拿到源码（zip / 目录 / 服务器路径）
2. 确认布局：
   - **根 pom 布局**：根部直接有 `pom.xml`（drainage）
   - **backend/ 布局**：根部有 `backend/pom.xml`（ibility）
3. 若 zip 带 target，排除 target 只取源码；**保留 .git**（git-commit-id 插件需要）

### 阶段 1：检查环境（本地）

```bash
java -version          # 必须显示 1.8.x
mvn --version
```

若 Java 版本不对，探测已知 JDK8 路径后再编译。Windows 候选：
- `C:\Program Files\Java\jdk1.8.0_361`
- `C:\Program Files\Java\jre1.8.0_471` 等（遍历 `C:\Program Files\Java`）

### 阶段 2：生成/补全 repo 离线库

**场景 A：已有 repo/（如 ibility）** → 只需修元数据。
**场景 B：无 repo/（如 drainage）** → 本机联网从内网 Nexus 下载全部依赖：

```bash
# 用 fix_repo / mvn go-offline 拉全依赖到项目 repo/
mvn -s <settings允许http> -f <pom或backend/pom> dependency:go-offline \
    -Dmaven.repo.local=<项目>/repo -Dmaven.source.skip=true -DskipTests
```

> ⚠️ Maven 3.8+ 默认屏蔽 HTTP 仓库（maven-default-http-blocker）。需提供允许 HTTP 的 settings（mirror `external:http:*` → `http://npm.egova.com.cn:18081/repository/maven-public/`）。

> ⚠️ **go-offline 不覆盖所有编译期传递依赖**。可靠补充：在线完整跑一次 `mvn clean install`（缺哪个自动补哪个），再离线验证。

### 阶段 3：修复三坑（关键 gate）

1. **.gitignore 误挡 jar**：删除 `**/*.jar` / `*.jar` 行（否则 repo 提交不到 git）
2. **清理 `_remote.repositories` + `*.lastUpdated`**：
   ```bash
   find repo -name "_remote.repositories" -delete
   find repo -name "*.lastUpdated" -delete
   ```
   > 不清理则离线报 `present, but unavailable` / "not downloaded before"（实测一次清 259 个）。
3. **JDK 版本**：必须 JDK8。JDK21 报 `NoSuchFieldError: JCImport.qualid`。
4. **git-commit-id 插件**：打包保留 `.git`；无 .git 时 `git init && git add -A && git commit`，或加 `-Dmaven.gitcommitid.skip=true`。

### 阶段 4：离线编译验证（核心 gate）

**本地离线编译**（`-o` 强制不联网，验证依赖真实性）：

```bash
set JAVA_HOME=C:\Program Files\Java\jdk1.8.0_361   # Windows
mvn -o -f pom.xml clean package -Dmaven.repo.local=repo -Dmaven.source.skip=true -DskipTests
```

成功判据：`BUILD SUCCESS` + 产物 jar 存在（ibility 217MB / drainage 276MB）。

失败排查顺序：
1. `present, but unavailable` → 清 `_remote.repositories`
2. 缺某个 jar → 回到阶段 2 在线 install 补全后重试
3. 源码编译错误（如 `setWaterPointStrategyList` 不存在）→ **源码问题**，需开发修代码，非流程可解

### 阶段 5：服务器验证

把源码+repo 传服务器（JDK8 + Maven3.6.3 已装），服务器也离线编译一次，确认跨环境可复现：

```bash
# 服务器 gczx.egova.com.cn
cd /opt/build/<workdir>
mvn -o -f pom.xml clean package -Dmaven.repo.local=repo -Dmaven.source.skip=true -DskipTests
```

### 阶段 6：打包分发

1. 制作完整离线包 zip（含源码+repo+.git+工具+README）：
   ```bash
   zip -rq <name>-offline.zip pom.xml README.md .gitignore bom modules services repo fix_repo .git -x '*/target/*'
   ```
2. 校验：`unzip -t <name>.zip`
3. 上传阿里云盘（服务器已装 aliyunpan）：
   ```bash
   aliyunpan upload <name>-offline.zip /           # 备份盘根目录
   aliyunpan share set -mode 3 -time 0 /<name>-offline.zip   # 快传链接（永久）
   ```
   > ⚠️ 备份盘不支持普通分享链接（"只有资源库才支持分享链接"），用**快传链接**（mode 3）。
4. dws 发群：`dws chat message send --group <cid> --text <链接+说明>`

## 已知 pitfall 档案

见 `config/known_pitfalls.md`，核心 6 条：
1. `.gitignore` 的 `**/*.jar` 挡掉 repo 依赖 → 必删
2. `_remote.repositories` 来源标记 → 离线报 unavailable，必清
3. Maven 3.8+ 屏蔽 HTTP 仓库 → 需允许 http 的 settings
4. go-offline 覆盖不全编译期传递依赖 → 用在线 install 兜底
5. JDK 必须 8 → 21 报 JCImport.qualid
6. git-commit-id 插件要 .git → 保留或 skip

## 完成后对话回显模板

```
离线打包完成 ✓
源码布局：<backend|根pom>，<N> 个模块
依赖库：<repo 大小>/<jar 数>（来源 npm.egova.com.cn）
本地离线编译：BUILD SUCCESS，产物 <jar 大小>
服务器离线编译：BUILD SUCCESS
离线包：<name>-offline.zip（<大小>MB，unzip -t 通过）
阿里云盘快传：<永久链接>
已发群：511773源码上传
```

## 善后提醒

1. **保留 .git**：交付包必须含 .git，否则新环境 git-commit-id 报错
2. **截图留痕**：离线 BUILD SUCCESS + jar 列表 截图
3. **验证闭环**：换全新机器解压 → 跑工具 → 离线编译 → java -jar 能启动