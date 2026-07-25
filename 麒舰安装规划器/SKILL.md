---
name: oneinstall-planner
description: |
  一键部署项目的智能服务器资源规划助手。凡涉及以下场景必须使用此 skill：
  用户提供服务器列表（IP/CPU/内存/磁盘）请求分配部署方案；用户上传或粘贴
  server_info.json；用户说"帮我规划部署"、"生成 metadata.yml"、"资源怎么分配"、
  "服务器够不够"；用户要求按用户规模（100/500/1000/2000/3000）出方案；
  用户对已有方案提出调整（"把数据库移到另一台"、"加个从节点"、"禁用某服务"）。
  只要涉及 eUrbanPro 节点分配或 metadata.yml 生成，都使用此 skill。
---

# 一键部署资源规划 Skill

大模型 负责理解意图、对话交互、解读结果、处理约束；
Python 脚本负责确定性计算、格式生成、完整性校验。

**完整工作流：**
```
① 收集信息  →  ② 拉取规格  →  ③ 确认参数  →  ④ 执行规划
→  ⑤ 展示结果  →  ⑥ 接受微调  →  ⑦ 生成并校验配置
```

---

## 步骤一：收集服务器信息

**接受三种输入方式，无需要求用户统一格式：**

**方式 A：上传 / 粘贴 server_info.json**
直接写入 `/tmp/dp_servers.json`，进入步骤二。

**方式 B：自然语言描述**
例如「我有三台机器：10.0.0.1 是 32 核 64G 1T 盘，另外两台是 16 核 32G 500G」。
提取字段，构造 JSON，**回显给用户确认**后写入 `/tmp/dp_servers.json`。

**方式 C：信息不足**
按优先级追问缺失字段，最少需要：IP、CPU（核）、内存（GB）、磁盘（GB）。
未提供的字段使用默认值：`diskType=SSD`、`arch=x86_64`。

**服务器 JSON 结构：**
```json
[
  {
    "name": "数据库服务器",
    "ip": "10.0.0.1",
    "cpu": 32,
    "mem": 64,
    "disk": 1000,
    "diskType": "SSD",
    "arch": "x86_64"
  }
]
```

> ARM 服务器（`arch: aarch64`）的 CPU 需求在规划时自动上浮 20%，
> 无需用户手动换算。

**特殊约束收集（此步骤询问，交给脚本执行）：**
主动询问用户是否有以下约束，有则记录到 `/tmp/dp_constraints.json`：
- 某服务必须固定在某台服务器（pin）
- 某台服务器只允许部署某类服务（reserve）
- 某些服务不需要部署（disable）

```json
{
  "pins": [
    { "group_key": "ip_db_biz", "ip": "10.0.0.1" }
  ],
  "reserves": [
    { "ip": "10.0.0.1", "only_categories": ["db"] }
  ],
  "disables": ["ip_web_es", "ip_web_onlyoffice"]
}
```

若无约束，写入空结构 `{"pins": [], "reserves": [], "disables": []}` 即可。

---

## 步骤二：拉取服务组规格

调用规格接口（接口地址从用户处或环境变量 `SPEC_API_BASE` 获取）：

```
GET {SPEC_API_BASE}/api/service-specs?scale={用户规模}
```

用户规模若未明确，**先询问**，不假设默认值。可选值：`100 | 500 | 1000 | 2000 | 3000`。
用户规模 > 5000 时终止流程，提示联系技术支持部和质管部。

**响应结构（写入 `/tmp/dp_specs.json`）：**
```json
{
  "scale": 500,
  "groups": [
    {
      "key": "ip_db_biz",
      "name": "业务数据库",
      "category": "db",
      "req_mem": 16,
      "req_cpu": 8,
      "req_disk": 500,
      "req_disk_iops": "读50k写10k",
      "need": true,
      "optional": false,
      "sub_type": "biz",
      "module_type": "mysql"
    }
  ]
}
```

**接口不可用时：**
告知用户并询问：① 用户手动提供规格 JSON，② 使用内置 fallback 规格。
fallback 数据见 `references/fallback_specs.json`，直接复制到 `/tmp/dp_specs.json`。

---

## 步骤三：确认规划参数

在调用规划脚本前，确认以下三个参数均已明确（已在对话中说明则跳过询问）：

| 参数 | 可选值 | 说明 |
|------|--------|------|
| `scale` | 100 / 500 / 1000 / 2000 / 3000 | 日活用户数 |
| `mode` | qijian / uma / lifeline / mingjing | 决定业务服务的启禁范围 |
| `arch` | x86_64 / aarch64 | 主体架构，影响 CPU 系数 |

参数确认后**直接执行**步骤四，不需要再次征得用户许可。

---

## 步骤四：执行规划脚本

```bash
python3 scripts/planner.py \
  --servers      /tmp/dp_servers.json \
  --specs        /tmp/dp_specs.json \
  --constraints  /tmp/dp_constraints.json \
  --scale        {scale} \
  --mode         {mode} \
  --arch         {arch} \
  --output       /tmp/dp_result.json
```

脚本输出 `/tmp/dp_result.json`，结构见 `references/script_contracts.md`。

**脚本异常处理：**
- 退出码非 0：读取 stderr，向用户说明具体错误，提供修正建议。
- 出现 `WARN` 前缀行：提取警告内容，在步骤五的「问题汇总」中呈现。

---

## 步骤五：展示规划结果

读取 `/tmp/dp_result.json`，**按以下固定格式**展示，不要自由发挥布局：

### 5.1 服务器资源总览

```
服务器名称       IP            内存          CPU           磁盘          状态
数据库服务器     10.0.0.1      50/64G (78%)  20/32核 (63%) 800/1000G     ✅ 正常
应用服务器A      10.0.0.2      30/32G (94%)  15/16核 (94%) 400/500G      ⚠️ 紧张
```

使用率 ≥ 90% 标记 ⚠️，≥ 100% 标记 ❌。

### 5.2 服务分配明细

按分类分组，每组折叠展示，问题项排在前面：

```
【数据库类】4 项
  ✅ 业务数据库       (ip_db_biz)        → 10.0.0.1   16G / 8核 / 500G
  ✅ 统计数据库       (ip_db_stat)       → 10.0.0.1    8G / 4核 / 500G
  ✅ PostGIS 数据库   (ip_tool_postgis)  → 10.0.0.1    8G / 4核 / 300G
  ✅ TDengine 时序库  (ip_db_tdengine)   → 10.0.0.1    8G / 4核 / 200G

【基础服务类】6 项
  ✅ Nacos 注册中心   (ip_web_nacos)     → 10.0.0.2    2G / 2核 / 50G
  ...

【已禁用】2 项（灰色）
  — Elasticsearch   (ip_web_es)         已禁用
  — OnlyOffice      (ip_web_onlyoffice) 已禁用
```

### 5.3 问题与建议

```
⚠️ 发现 1 个警告：
• 应用服务器A (10.0.0.2) 内存使用率 94%，建议将「玄藏服务」迁移至其他节点

💡 建议确认：
• 是否需要为数据库配置从节点（高可用）？
• 「悟空服务」「悟能服务」为可选服务，是否需要部署？
```

---

## 步骤六：接受微调指令

展示完结果后，询问是否需要调整。支持以下自然语言指令：

| 用户说 | Claude 的处理 |
|--------|--------------|
| 「把玄藏移到 10.0.0.3」 | 更新 `/tmp/dp_constraints.json`，追加 pin，**重新执行步骤四** |
| 「数据库加从节点 10.0.0.5」 | 更新 `/tmp/dp_result.json` 中对应服务的 `slave_ip`，无需重新规划 |
| 「禁用 ES 和 OnlyOffice」 | 追加到 constraints.disables，**重新执行步骤四** |
| 「确认，生成配置」 | 进入步骤七 |
| 「重新规划」 | 清空中间文件，回到步骤一 |

**重新执行规划后，重新展示步骤五的完整结果。**

每次微调最多循环 5 次，超过后提示用户直接生成当前方案，剩余调整手动修改 yml。

---

## 步骤七：生成并校验配置

### 7.1 生成 metadata.yml

```bash
python3 scripts/generator.py \
  --result  /tmp/dp_result.json \
  --specs   /tmp/dp_specs.json \
  --output  /tmp/metadata.yml
```

### 7.2 校验配置完整性

```bash
python3 scripts/validator.py \
  --metadata /tmp/metadata.yml \
  --specs    /tmp/dp_specs.json \
  --result   /tmp/dp_result.json
```

校验脚本检查项见 `references/script_contracts.md`。

**校验通过：**
将 `/tmp/metadata.yml` 内容展示在代码块中，告知用户保存到部署项目的 `config/metadata.yml`。

**校验失败：**
说明具体失败项，询问用户是否自动修正（调用 `generator.py --fix`）或手动处理。

---

## 全局注意事项

- **不跳步骤**：每步骤有明确完成条件，未完成不进入下一步。
- **脚本结果优先**：展示内容以脚本输出的 JSON 为准，不自行推算资源用量。
- **调整必须重新计算**：凡涉及节点变更的微调，必须重跑 `planner.py`，不凭记忆修改数字。
- **保持简洁**：服务数量多时按分类折叠，不要一次平铺 30+ 行。
- **中间文件清理**：完成后提示用户可删除 `/tmp/dp_*.json` 和 `/tmp/metadata.yml`。
