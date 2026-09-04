# 评分规则参考

## Q1 性能监控（22 个采分点合计 59 分，缩放到 50）

### 一、性能应急故障处理（30 分）
| 代码 | 采分点 | 分值 | 关键词 | 特殊要求 | 类型 |
|---|---|---|---|---|---|
| P1-1 | 内网访问登录 | 3 | 内网访问 / 用户中心.*登录 / admin | 浏览器URL=满分；curl=半分 | 截图题 |
| P1-2 | mysql 状态导出 | 3 | mysql.*状态 / mysql.*导出 | — | 截图题 |
| P1-3 | 达梦状态导出 | 3 | 达梦.*状态 / dameng / DM_ | — | 截图题 |
| P1-4 | nginx 状态导出 | 5 | nginx.*状态 | 统计分布+10s耗时分布缺一段折半 | 截图题 |
| P1-5 | 应用日志错误提取 | 3 | 日志.*错误 / 应用.*日志 | — | 截图题 |
| P1-6 | jvm 信息导出 | 3 | jvm / jstack / jmap / heap | — | 截图题 |
| P1-7 | redis 状态导出 | 3 | redis.*状态 / redis.*信息 | — | 截图题 |
| P1-8 | 磁盘 I/O 状态 | 3 | 磁盘.*I.*O / iostat / disk.*io | — | 截图题 |
| P1-9 | 系统恢复思路 | 4 | 恢复.*思路 / 系统.*恢复 | ≥60字论述 | **论述题** |

### 二、auto_check 巡检（16 分）
| 代码 | 采分点 | 分值 | 关键词 | 特殊要求 |
|---|---|---|---|---|
| P2-1 | 生成最新 zip 巡检报告 | 2 | zip / 巡检.*报告 / 一键巡检 | 报告必须真生成 |
| P2-2 | report_dameng.html | 2 | dameng.html / 达梦.*报告 | **统计区有真实数据**，空白=0 |
| P2-3 | report_microservice.html | 3 | microservice.html | **需解决 dump 路径预警**，仅基本信息=20% |
| P2-4 | report_mysql.html | 2 | mysql.html / mysql.*报告 | 同 P2-2 |
| P2-5 | report_nginx.html | 3 | nginx.html / 日志.*切割 | **需解决日志切割预警**，仅查看报告=0 |
| P2-6 | report_os.html | 2 | os.html / 系统.*报告 | 同 P2-2 |
| P2-7 | report_redis.html | 2 | redis.html / redis.*报告 | 同 P2-2 |

### 三、基准测试（13 分）
| 代码 | 采分点 | 分值 | 关键词 |
|---|---|---|---|
| P3-1 | 测试前置操作 | 2 | 前置 / 准备 / 测试前 |
| P3-2 | 数据库基准测试 | 3 | 数据库.*基准 / sysbench |
| P3-3 | redis 基准测试 | 2 | redis.*基准 / redis-benchmark |
| P3-4 | 磁盘 IO 性能测试 | 2 | 磁盘.*性能 / fio |
| P3-5 | IOPS 测试 | 2 | IOPS |
| P3-6 | 宽带测试 | 2 | 宽带 / 带宽 / iperf |

## Q2 安全运维（7 个采分点合计 50 分）

### 一、雷池部署（17 分）
| 代码 | 采分点 | 分值 | 关键词 | 特殊要求 |
|---|---|---|---|---|
| S1-1 | 离线部署+登录 | 6 | 雷池 / safeline / 离线.*部署 | 登录页/仪表盘带URL；partial=80% |
| S1-2 | 模拟攻击+找日志 | 6 | 模拟攻击 / 攻击.*日志 / 真实.*ip | 拦截效果图需带URL |
| S1-3 | 拦截租户管理接口 | 5 | 租户.*管理 / tenant / 拦截.*接口 | — |

### 二、egova_lua_waf（18 分，三要素法）
| 代码 | 采分点 | 分值 | 三要素 |
|---|---|---|---|
| S2-1 | 应用中心放开 | 6 | ①DevTools 32018 拦截码 ②/etc/nginx/conf.d/wafconf/url 注释 getapps 规则 ③nginx reload + 应用中心列表恢复 |
| S2-2 | 拦截操作日志 | 6 | ①取 operatelog/page URL ②echo URL >> wafconf/url ③reload + 重访接口 403/32018 |
| S2-3 | CC 防护 | 6 | ①取 oauth/.../login URL ②echo URL >> wafconf/cc-url + reload ③【加分项】ab 攻击 + 31001 拦截日志（+10%） |

**评分**：`factors_met / 3 × 满分`；S2-3 has_ab_attack=true 额外 +10%

### 三、弱密码（15 分）
| 代码 | 采分点 | 分值 | 评分 |
|---|---|---|---|
| S3-1 | 弱密码扫描+清单 | 15 | ≥5个=100% / 3-4个=50% / <3=0 |

## 视觉细查 VISUAL_ADJUST 配置

```python
VISUAL_ADJUST = {
    "P1-1": {"true": 1.0, "partial": 0.75, "false": 0.5},   # 浏览器满 / curl 半 / 未做 0
    "P1-4": {"true": 1.0, "partial": 0.5, "false": 0.1},    # 统计分布+10s缺一段折半
    "P2-1": {"true": 1.0, "partial": 0.7, "false": 0.0},
    "P2-2": {"true": 1.0, "partial": 0.7, "false": 0.0},
    "P2-3": {"true": 1.0, "partial": 0.2, "false": 0.0},    # ⚠严：统计区必须有真实数据
    "P2-4": {"true": 1.0, "partial": 0.7, "false": 0.0},
    "P2-5": {"true": 1.0, "partial": 0.5, "false": 0.0},    # 严：必须有 logrotate 修复
    "P2-6": {"true": 1.0, "partial": 0.7, "false": 0.0},
    "P2-7": {"true": 1.0, "partial": 0.7, "false": 0.0},
    "S1-1": {"true": 1.0, "partial": 0.8, "false": 0.3},
    "S3-1": {"true": 1.0, "partial": 0.7, "false": 0.2},    # S3-1 实际按 count 字段判
}
# S2-1/S2-2/S2-3 按 factors_met/3 比例打分
```

## 总分计算

```
Q1 raw = sum(每采分点 awarded)
Q1 score = min(raw / 59 × 50, 50)   # 按比例缩放到 50

Q2 raw = sum(每采分点 awarded)
Q2 score = min(raw, 50)             # Q2 满分本就 50

total = Q1 score + Q2 score
```

## 老师评分模式 vs 严格模式

陈智源 6748 老师评 80 = Q1 50 + Q2 30。算法严格模式给 71.3 = Q1 41.1 + Q2 30.2。

差异来源：
- 老师 Q1 给满分（即使 P1-1 curl / P2-3 partial / P2-4 missing）
- 算法 Q1 按比例缩放扣分
- 老师 Q2 lua_waf 全空给 0（与算法一致）

→ **用户当前选择严格模式**：按比例缩放 Q1，扣分体现真实差距。
