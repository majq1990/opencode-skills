# tianditu-map · README（认证证据包配套）

> 对应《AI应用能力培训与认证方案》构造题。完整证据包 = 本文件 + SKILL.md + scripts/ + config/ + assets/ + evidence/。

## 1. 环境准备

| 依赖 | 说明 |
|---|---|
| Python 3.8+ | 仅标准库（urllib/threading/csv/json）；`apply-db` 需 `psycopg2`（连 Kingbase/PG） |
| playwright | 仅用于 `collect_run_evidence.py` 出地图截图证据（证据包可选） |
| 网络 | 可访问 `api.tianditu.gov.cn`（勿走代理）；本机无需安装任何第三方地理库 |

```bash
# 1) 部署 skill（二选一目录，不重复）
D:\opencode\config\skills\tianditu-map\            # opencode/Claude 系全局 skill 目录
C:\Users\<you>\.agents\skills\tianditu-map\         # 本机 agent 目录

# 2) 配置 API key（本机私有，不入库）
#   - 把真实 key 写入 config/keys.local.json（.gitignore 已排除）
#   - 或设置环境变量（可临时追加，逗号分隔）
setx TIANDITU_MAP_KEYS "key3,key4"

# 3) （可选）数据库回写需要连接串，只放环境变量，勿写入任何文件
setx TIANDITU_DB_DSN "host=172.28.43.118 port=30209 dbname=iotbase user=system password=***"
```

> **密钥红线**：`keys.json` / `SKILL.md` / `README.md` 等**公开文件不含任何明文 key 或密码**。真实值只在本机 `config/keys.local.json`（已 .gitignore）或环境变量里。

## 2. 运行

```bash
S=.../tianditu-map/scripts/tdt.py
python "$S" keys                                  # 查看 key 池状态
python "$S" geocode "宁夏银川市西夏小区15-1-203"    # 地址 → 坐标
python "$S" reverse 106.10047 38.48822            # 坐标 → 地址
python "$S" batch 源.csv --col address --out 结果.csv --prefix "宁夏银川市" --encoding gbk
python "$S" crawl-communities "106.0,38.3,106.6,38.6" --out-prefix comm --keywords "小区,花园,家园"
python "$S" map comm.csv --out map.html --title "小区分布"
python "$S" apply-db 结果.csv --table iotbase.iot_equip_info          # 预览 SQL
python "$S" apply-db 结果.csv --table iotbase.iot_equip_info --confirm "确认写入"  # 人工门禁后写库
```

**完整交付链**（对应认证"计划-调用-检查-交付-复盘"闭合）：
1. **计划**：任务卡（SKILL.md §四）→ 明确来源/人工确认点/交付物
2. **调用**：`batch` 批量编码 → 输出 CSV + GeoJSON + 【待复核】清单
3. **检查**：打开 `*.review.md` 按清单抽检（坐标范围/未命中/样例复测）
4. **交付**：`map` 出图交付；`apply-db --confirm "确认写入"` 回写数据库（先建备份表）
5. **复盘**：迭代记录见 SKILL.md §四；证据包见 `evidence/`

## 3. 权限清单

| 操作 | 读写 | 说明 |
|---|---|---|
| 天地图 API | 只读 | geocode/reverse/search 无副作用 |
| batch / crawl / map | 只写本地 | 输出 CSV/GeoJSON/HTML/复核清单到指定目录 |
| apply-db | 写数据库（受控） | 标识符白名单校验；默认预览；`--confirm "确认写入"` 才执行；事务失败回滚；先建备份表 `iot_equip_info_bak_xy_20260909` |

## 4. 安全红线（一票否决对照）

- ✅ 不向 AI 输入密钥/密码原文：key 与 DB 密码只在本机配置/环境变量，公开文件零明文
- ✅ AI 输出未核验即发送/写库：产物默认【待复核】+ `--confirm` 技术门禁
- ✅ 不伪造来源/验证：所有实测输出在 evidence/ 可复现
- ✅ 不用 AI 替代审批：写库/对外交付均人工确认
- ✅ 只读/只写授权目标：不跨项目读写

## 5. 反向测试清单（新环境部署后照单验证）

```bash
python "$S" apply-db x.csv --table "iot_equip_info;drop table"   # → {"ok":false,"gap":"非法标识符"} 不执行
python "$S" apply-db x.csv --table a.b --key-cols equip_name,address --coord-cols lon,lat  # 无DSN → gap 停止
python "$S" apply-db x.csv --table a.b  # 有DSN → 仅预览 SQL，ok:false preview:true，不写库
python "$S" geocode "北京市"             # 坏 key 自动摘除警告，正常返回坐标
python "$S" batch 无坐标.csv --col address --out out.csv  # 未命中地址进 .miss.txt，出复核清单
```

## 6. 可复用交付物

| 交付物 | 复用方式 |
|---|---|
| SKILL.md | 触发/边界/权限/停止条件完整，装上即用 |
| tdt.py | 零依赖 CLI，换 key/换 CSV 即跑 |
| 地图 HTML 模板 | make_map 自动生成（Leaflet+聚合+天地图底图），任意点位数据复用 |
| 复核清单模板 | batch 自动生成 `*.review.md` |
| apply-db 门禁 | 通用回写（任何表/主键/坐标列），白名单防注入 |
| 本证据包 | 作为构造题证据包样例结构 |
