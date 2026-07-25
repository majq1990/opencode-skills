# metadata.yml 格式规范

generator.py 生成 metadata.yml 时以本文件为格式标准。
Claude 在展示生成结果时也以本文件为参考，确保格式一致。

---

## 文件头注释

每个生成的 metadata.yml 必须包含以下头部注释：

```yaml
# 由 eUrbanPro 部署规划工具生成
# 生成时间: {YYYY-MM-DD HH:MM}
# 用户规模: {scale} | 产品模式: {mode} | 架构: {arch}
```

---

## 完整结构模板

```yaml
# 由 eUrbanPro 部署规划工具生成
# 生成时间: 2025-06-01 14:30
# 用户规模: 500 | 产品模式: qijian | 架构: x86_64

# ── 中间件 ──────────────────────────────────────────

mysql:
  need: true
  # master: 10.0.0.1 (数据库服务器)
  # slave:  10.0.0.5 (备用节点)        ← 有从节点时才加此行

redis:
  need: true
  # master: 10.0.0.2 (缓存服务器)

minio:
  need: true

nginx:
  need: true

zookeeper:
  need: true

kafka:
  need: true

elasticsearch:
  need: false

postgresql:
  need: true

cetus:
  need: true

TDengine:
  need: true

# ── 应用服务 ─────────────────────────────────────────

service:

  eUrbanMIS:
    need: false

  eUrbanMF:
    need: false

  eUrbanUMA:
    need: false

  eUrbanGIS:
    need: true
    # master: 10.0.0.3 (GIS服务器)

  eUrbanSG:
    need: false

  eGovaPublic:
    need: false

  IMserver:
    need: false

  statgather:
    need: false

# ── 微服务 ───────────────────────────────────────────

microservice:

  linglong:
    need: true
    # master: 10.0.0.4 (应用服务器A)

  wukong:
    need: true

  dex:
    need: true

  httpfileservice:
    need: true

  evaluation:
    need: true

  export:
    need: true

  usercenter:
    need: true

  eurbanpro:
    need: true

  mjing:
    need: true

  patrol_gather:
    need: true

  trajectory:
    need: false

  sms:
    need: false

  eurbanpro_media:
    need: false

  xuanzang:
    need: false

  dataflow:
    need: false

  dataflow_zookeeper:
    need: false

  giscenter:
    need: false

  gisserver:
    need: false
```

---

## 格式规则

### 顶层中间件字段顺序（固定，不可更改）

```
mysql → redis → minio → nginx → zookeeper → kafka →
elasticsearch → postgresql → cetus → TDengine
```

顺序与现有一键部署脚本的解析逻辑对应，不得调整。

### service 子字段顺序（固定）

```
eUrbanMIS → eUrbanMF → eUrbanUMA → eUrbanGIS →
eUrbanSG → eGovaPublic → IMserver → statgather
```

### microservice 子字段顺序（固定）

```
linglong → wukong → dex → httpfileservice → evaluation →
export → usercenter → eurbanpro → mjing → patrol_gather →
trajectory → sms → eurbanpro_media → xuanzang → dataflow →
dataflow_zookeeper → giscenter → gisserver
```

### 主从节点注释格式

```yaml
mysql:
  need: true
  # master: {ip} ({服务器备注名})
  # slave:  {ip} ({服务器备注名})    ← 仅有从节点时添加，无从节点不写此行
```

- 注释缩进与 `need` 对齐（两空格）
- `master:` 和 `slave:` 后跟一个空格
- IP 后紧跟空格和括号包裹的备注名
- 若同一中间件有多个服务组（如 mysql 同时对应 ip_db_biz 和 ip_db_stat），
  每个服务组各写一行 master 注释，并加服务名区分：

```yaml
mysql:
  need: true
  # master(业务库): 10.0.0.1 (数据库服务器)
  # master(统计库): 10.0.0.1 (数据库服务器)
```

### need 字段值

- 只允许 `true` 或 `false`，小写，无引号
- 所有字段必须存在，即使 `need: false` 也不能省略

### 空行规则

- 每个顶层中间件项之后有一个空行
- `service:` 和 `microservice:` 标题行之后有一个空行
- 每个 service / microservice 子项之后有一个空行
- 文件末尾有一个换行符

---

## 与现有 metadata.yml 的兼容性说明

| 现有字段 | 规划工具处理方式 |
|----------|----------------|
| 所有现有 need 字段 | 完整保留，按规划结果赋值 |
| 主从节点 IP | 新增为注释，当前部署脚本忽略注释，不影响兼容性 |
| 未知新字段 | 不生成，保持最小化原则 |

> 当一键部署脚本升级支持主从配置时，只需修改 generator.py 将注释改为正式字段，
> 其余逻辑不变。
