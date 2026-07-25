# 钉钉「安全漏洞台账 → 软件漏洞」字段映射

> 通过 `dws aitable field get` + 3 条现有记录反推（2026-05-06 校验）。
>
> 字段命名有占位（"字段8/9"未改名），现有记录里也未启用。本文是结合现有数据的「事实派」字段约定，正式接入时建议先跟用户确认每个字段实际期望填什么。

## 定位

| Key | Value |
|---|---|
| baseId | `qnYMoO1rWxDl1N54sz3zaKemW47Z3je9` |
| baseName | 安全漏洞台账 |
| tableId | `oz3kcid3c79qy2lqspsn3` |
| tableName | 软件漏洞 |

## 字段清单（用户 2026-05-06 决策版）

| 字段名 | fieldId | 类型 | skill 写入策略 |
|---|---|---|---|
| 涉及产品 | `n3djf91ig7kmb0kdr22x8` | text | **留空** |
| 漏洞项 | `6hcpem5c9dgsvsmyxv7tq` | text | **必填**，多 CVE 用 `\n` 换行合并，每行格式 `<漏洞标题>(<CVE-ID>)` |
| 字段9 | `1z0wikuz84x1gsm5lx2od` | text | **留空** |
| 反馈时间 | `mg7pem3ji0yfumkbxrw2y` | date(YYYY-MM-DD) | **留空** |
| 序号 | `7k08ogebp2icgn93thnv4` | number(INT) | **必填**，写入前 query 当前表 max(序号)+1 |
| 说明&解决方案 | `o9qusfb8e9qow49igstwg` | text | **必填**，钉钉云文档 URL（处置文档无论复杂度都生成） |
| 字段8 | `y0wszd9ndgz5i56nx4xxp` | text | **留空** |
| 软件 | `7ajxu4kgmvjirkvoamcv3` | text | **必填**，来自 `software_inventory.md` 白名单 |
| 字段8图片 | `ktfe3cqp3oc01nm95j8dg` | attachment | **留空**（dws CLI 不支持附件直传） |
| 任务号 | `r9jnby1krjxr9qgyihb1b` | number(INT) | **留空**（暂不关联 Redmine） |

## 录入范式（已敲定）

**软件 × 多 CVE 合并 = 一行**：一个软件遇到多个 CVE 时，合并到同一条记录的「漏洞项」字段，每行一个 CVE。例如 redis 同时报 3 个 CVE：

```
漏洞项 字段值（用 \n 分隔）：
软件版本泄露漏洞(CVE-2024-31449)
认证绕过漏洞(CVE-2024-46981)
缓冲区溢出漏洞(CVE-2024-51741)
```

如果一次涉及多个软件（比如 redis 和 mysql 各有 CVE），写两条记录，一软件一行。

## 与 OS 漏洞表的关键差异

| 维度 | OS 漏洞表 | 软件漏洞表 |
|---|---|---|
| 录入粒度 | 每个 CVE × 每个 OS = 一行 | **每个软件 × 多 CVE = 一行** |
| 处置方案在哪 | 写在记录里（三段式） | **写钉钉云文档，记录里只填文档 URL** |
| 处置文档 | 必出三级编号大模板 | **必出**（参考 OS 模板，结构适配多 CVE 合并） |
| 抓取来源 | 6 家发行版安全公告 | NVD JSON API 主路径 + 国产软件 SPA 兜底 |
| 序号字段 | 无 | 流水号，写入前自动 max+1 |

## records.create 调用 payload 范例

```json
{
  "records": [
    {
      "fields": {
        "7ajxu4kgmvjirkvoamcv3": "redis",
        "7k08ogebp2icgn93thnv4": 50,
        "6hcpem5c9dgsvsmyxv7tq": "Lua 脚本沙箱逃逸(CVE-2024-31449)\n认证绕过(CVE-2024-46981)\n缓冲区溢出(CVE-2024-51741)",
        "o9qusfb8e9qow49igstwg": "https://alidocs.dingtalk.com/i/nodes/<nodeId>"
      }
    }
  ]
}
```

> 写入顺序：**先 publish 钉钉云文档拿到 nodeId → 拼出 alidocs URL → 再 record create**（跟 OS 分支可同时插记录不同；这是为了让「说明&解决方案」字段能填上文档 URL）
