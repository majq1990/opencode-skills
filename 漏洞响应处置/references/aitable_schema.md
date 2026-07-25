# 钉钉「安全漏洞台账 → 操作系统漏洞」字段映射

> 通过 `dws aitable field get` 探查得到（2026-05-06 校验）。fieldId 不会变，options.id 也不会变；如果钉钉表结构发生变更，重新跑一次 `dws aitable field get --base-id ... --table-id ...` 校准。

## 定位

| Key | Value |
|---|---|
| baseId | `qnYMoO1rWxDl1N54sz3zaKemW47Z3je9` |
| baseName | 安全漏洞台账 |
| tableId | `f3dzlj97k3121hq4adg10` |
| tableName | 操作系统漏洞 |

## 字段清单

| 字段名 | fieldId | 类型 | 说明 |
|---|---|---|---|
| 操作系统 | `eyyot4lp34qhb0no8pfft` | singleSelect | 见下方选项表 |
| 版本 | `k7k539eh44ge7cx4a00kg` | text | 形如 `V10 SP3` / `22.04 LTS` / `8.x` |
| CVSS | `4c0tcmju3g99f13eaviy5` | number(FLOAT_2) | 数值或字符串数字均可，如 `7.8` |
| 信息来源 | `92sy0dfe1sui2jb8chr94` | text | 厂商名 + SA 编号 + 备注，例如 `openEuler 官方公告 openEuler-SA-2026-1544` |
| 是否受影响 | `kgdi0bpx8hz6zc0lz5792` | singleSelect | `是` / `否` |
| 默认内核 | `mszmmh1eeh3e0j13znjx1` | text | 形如 `5.10.x` / `5.4 / 5.15 HWE` |
| CVE编号 | `rqhppwz3wc6ei91funonu` | text | 形如 `CVE-2026-31431` |
| 漏洞名称 | `w4yy82i3eupd9bq2j0bwk` | text | 漏洞代号或一句话描述 |
| 处置建议 | `oxlb9cvxvwku691qho1e1` | text | **固定三段式**，见下文 |

## 操作系统选项映射

| 显示名 | optionId |
|---|---|
| 银河麒麟 | `4hkgn34cc60kr3frph6zq` |
| openEuler | `n8zdtszzudsi4e15d8nf6` |
| OpenAnolis | `c01b825u5u7iwdh78f7qp` |
| 统信UOS | `45k4yidgplj982ip0t4v1` |
| Ubuntu | `51tjzft5sb1pwf4l4wl65` |
| CentOS | `sqaq8qstux4hhn8c4t4te` |

> **注意**：当前没有独立的 `RedHat` 选项。RHEL 和 CentOS Stream 都归到 `CentOS`，在「版本」字段里写明（例如 `RHEL 9` / `Stream 9`）。

## 是否受影响选项

| 显示名 | optionId |
|---|---|
| 是 | `alvkl56p8qaogewi6bj7u` |
| 否 | `diratl3d195p969ohptox` |

## 处置建议三段式

格式固定：

```
[修复] <一行修复命令> | [验证] <一行验证命令> | [公告] <官方公告 URL>
```

- 三段以 ` | ` 分隔（前后各一空格）
- 修复命令不要换行；多步骤用 `&&` 连接
- 公告 URL 必须是该 OS 厂商的真实公告，不接受 NVD / 通用站

样本：

```
[修复] apt update && apt upgrade && reboot | [验证] uname -r | [公告] https://ubuntu.com/security/CVE-2026-31431
```

## records.create 调用 payload

`dws aitable record create --records <jsonStr>` 接受的格式：

```json
{
  "records": [
    {
      "fields": {
        "eyyot4lp34qhb0no8pfft": "openEuler",
        "k7k539eh44ge7cx4a00kg": "22.03 LTS",
        "4c0tcmju3g99f13eaviy5": 7.8,
        "92sy0dfe1sui2jb8chr94": "openEuler 官方公告 openEuler-SA-2026-1544",
        "kgdi0bpx8hz6zc0lz5792": "是",
        "mszmmh1eeh3e0j13znjx1": "5.10",
        "rqhppwz3wc6ei91funonu": "CVE-2026-31431",
        "w4yy82i3eupd9bq2j0bwk": "Copy Fail (algif_aead 本地提权)",
        "oxlb9cvxvwku691qho1e1": "[修复] dnf update kernel && reboot | [验证] uname -r | [公告] https://www.openeuler.org/zh/security/security-bulletins/detail/?id=openEuler-SA-2026-1544"
      }
    }
  ]
}
```

> singleSelect 字段直接传选项的「显示名」字符串即可，dws 服务端会做映射。如果显示名拼错会被拒绝；为了保险，build_aitable_rows.py 在写入前会校验值在白名单内。
