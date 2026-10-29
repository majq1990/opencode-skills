# skill-hub

公司 skill 服务器（skills-manager 企业源，即 `/egova/skill/`）的总入口 skill：按需求检索团队 skill 池、下载装载执行、引导安装。

## 解决什么问题

团队 skill 池已沉淀 30+ 个 skill，但使用者记不住名字、不知道该用哪个。本 skill 让使用者**只描述需求**，就能完成"找到 → 确认 → 装载 → 使用"全链路，无需预先知道任何 skill 名。

## 设计约束

- **各自账号**：不内置任何账号，脚本以"本机 skills-manager 当前登录者"身份调 API，谁登录就用谁的
- **路径自适应**：不预设任何人的机器布局。装载目标按 `--dest` > `--tool` 探测 > 临时目录 三段式解析，目标不存在时自动降级为临时装载，不影响使用
- **跨平台**：Windows / macOS / Linux 均可运行；会话探测、目录候选全部基于 `~` 展开
- **只读**：只用 list/search/tags/show/download 五个只读接口；上传删除走 skill-publisher 或 skills-manager GUI
- **零硬依赖**：python 标准库实现；AES-GCM 解密在 `cryptography` 缺失时自动回退 `node crypto`

## 目录结构

```
skill-hub/
├── SKILL.md                          # 总入口：触发场景 + 分流逻辑
├── README.md
├── scripts/
│   └── skill_server.py               # 客户端（list/search/tags/show/download）
├── references/
│   ├── api-contract.md               # 服务器 API 契约（实测）
│   └── session-protocol.md           # 会话读取与 401 处置
└── tests/
    └── test_skill_hub.py             # 离线单元测试（python3 tests/test_skill_hub.py）
```

## 快速使用

```bash
# 探测登录态 / 看 tag 分布
python3 scripts/skill_server.py tags

# 按需求找 skill
python3 scripts/skill_server.py search "redmine 批量"

# 看详情
python3 scripts/skill_server.py show build-pipeline

# 装载到临时目录（当次即用，最稳）
python3 scripts/skill_server.py download build-pipeline --tmp

# 装载到某工具的 skills 目录（持久生效）
python3 scripts/skill_server.py download build-pipeline --tool zcode   # zcode/opencode/workbuddy/dsh
python3 scripts/skill_server.py download build-pipeline --dest /path/to/skills

# 所有命令支持 --json
```

## 安装

**方式一（推荐）：skills-manager 企业源导入**——在发现页找到 `skill-hub` 导入，由 skills-manager 按各人环境部署到各 AI 工具的 skills 目录。

**方式二：直接下载**——本 skill 自身就是公司 skill 池的成员，任何已登录 skills-manager 的用户都能搜到它。

## 与相邻 skill 的关系

| skill | 分工 |
|-------|------|
| skill-hub（本 skill） | 发现 + 装载（只读入口） |
| skill-publisher | 发布/上传到服务器（写侧） |
| find-skills | 公网 skills.sh 生态发现 |

## 测试

```bash
python3 tests/test_skill_hub.py   # 11 项离线单测：白名单/解压边界/降级/JWT 解析
```
