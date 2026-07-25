# 脚本接口契约（Script Contracts）

Claude 与 Python 脚本之间通过临时 JSON 文件通信。
本文件定义所有中间文件的完整结构，是 Claude 解读脚本输出的唯一参考。

---

## 临时文件一览

| 文件路径 | 写入方 | 读取方 | 说明 |
|----------|--------|--------|------|
| `/tmp/dp_servers.json` | Claude | planner.py | 服务器列表 |
| `/tmp/dp_specs.json` | Claude（来自接口或 fallback） | planner.py, generator.py | 服务组规格 |
| `/tmp/dp_constraints.json` | Claude | planner.py | 约束条件 |
| `/tmp/dp_result.json` | planner.py | generator.py, validator.py, Claude | 规划结果 |
| `/tmp/metadata.yml` | generator.py | validator.py, Claude | 最终配置文件 |

---

## dp_servers.json

```json
[
  {
    "name": "数据库服务器",      // 备注名，用于显示
    "ip": "10.0.0.1",           // 内网 IP，唯一标识符
    "cpu": 32,                   // 逻辑核数
    "mem": 64,                   // 内存 GB
    "disk": 1000,                // 磁盘 GB（主分区可用空间）
    "diskType": "SSD",           // SSD | HDD | NVMe | SAS
    "arch": "x86_64"             // x86_64 | aarch64
  }
]
```

---

## dp_specs.json

来自规格接口响应，或从 `references/fallback_specs.json` 复制。

```json
{
  "scale": 500,
  "groups": [
    {
      "key": "ip_db_biz",         // 对应 eurbanpro_multi_server.yml 的顶层 key
      "name": "业务数据库",
      "category": "db",           // db|cache|infra|gis|storage|app|biz
      "req_mem": 16,              // 所需内存 GB（已按规模换算）
      "req_cpu": 8,               // 所需 CPU 核数（已按规模换算）
      "req_disk": 500,            // 所需磁盘 GB
      "req_disk_iops": "读50k写10k", // 仅展示用，不影响分配逻辑
      "need": true,               // 默认是否启用
      "optional": false,          // 是否为可选服务
      "sub_type": "biz",          // metadata.yml 中的 sub_type 值
      "module_type": "mysql"      // metadata.yml 中的顶层中间件 key
    }
  ]
}
```

---

## dp_constraints.json

```json
{
  "pins": [
    {
      "group_key": "ip_db_biz",   // 服务组 key
      "ip": "10.0.0.1"            // 强制分配到此 IP
    }
  ],
  "reserves": [
    {
      "ip": "10.0.0.1",
      "only_categories": ["db"]   // 此服务器只允许 db 类服务
    }
  ],
  "disables": [
    "ip_web_es",                  // 强制禁用的服务组 key 列表
    "ip_web_onlyoffice"
  ]
}
```

无约束时写入：`{"pins": [], "reserves": [], "disables": []}`

---

## dp_result.json（planner.py 输出）

```json
{
  "params": {
    "scale": 500,
    "mode": "qijian",
    "arch": "x86_64"
  },
  "server_summary": [
    {
      "ip": "10.0.0.1",
      "name": "数据库服务器",
      "mem_total": 64,
      "mem_used": 50,
      "mem_pct": 78,              // 使用率百分比（整数）
      "cpu_total": 32,
      "cpu_used": 20,
      "cpu_pct": 63,
      "disk_total": 1000,
      "disk_used": 800,
      "disk_pct": 80,
      "status": "ok"              // ok | tight | overloaded
    }
  ],
  "assignments": [
    {
      "key": "ip_db_biz",
      "name": "业务数据库",
      "category": "db",
      "status": "ok",             // ok | warn | unassigned | disabled
      "disable_reason": "",       // user_disabled | mode_disabled | optional_default_off
      "assigned_ip": "10.0.0.1",
      "assigned_name": "数据库服务器",
      "slave_ip": null,           // 从节点 IP，用户在微调步骤填写
      "slave_name": null,
      "req_mem": 16,
      "req_cpu": 8,
      "req_disk": 500,
      "sub_type": "biz",
      "module_type": "mysql",
      "arm_adjusted": false       // true 表示 CPU 已上浮 20%
    }
  ]
}
```

### status 枚举说明

| status | 含义 | 需要处理 |
|--------|------|----------|
| `ok` | 正常分配，节点资源充足 | 无 |
| `warn` | 分配成功但节点资源超配 | 建议迁移 |
| `unassigned` | 无可用节点，未分配 | 必须处理 |
| `disabled` | 已禁用，不会写入 metadata.yml | 无 |

### server_summary.status 枚举

| status | 含义 |
|--------|------|
| `ok` | 内存和 CPU 使用率均 < 90% |
| `tight` | 内存或 CPU 使用率 ≥ 90% |
| `overloaded` | 内存或 CPU 使用率 ≥ 100% |

---

## planner.py 退出码

| 退出码 | 含义 | Claude 处理方式 |
|--------|------|----------------|
| `0` | 成功，无问题 | 正常展示结果 |
| `1` | 致命错误（输入有误、规模超限等） | 读 stderr，向用户说明错误 |
| `2` | 成功但有未分配服务 | 展示结果，在问题汇总中突出显示未分配项 |

---

## validator.py 退出码

| 退出码 | 含义 |
|--------|------|
| `0` | 校验通过（无错误，可有警告） |
| `1` | 有错误，禁止使用此 metadata.yml |
| `2` | strict 模式下有警告（视为错误） |

---

## 微调时 Claude 对 dp_result.json 的直接修改规则

以下微调**不需要重新运行 planner.py**，Claude 直接修改 `dp_result.json`：

- 添加/修改从节点：更新 `assignments[n].slave_ip` 和 `slave_name`
- 仅这一种情况允许直接修改

以下微调**必须重新运行 planner.py**：

- 更换主节点分配（任何 `assigned_ip` 的变更）
- 新增/修改 pin 约束
- 新增/修改 reserve 约束
- 启用/禁用服务
- 更换服务器（新增或删除节点）
