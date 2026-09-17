---
name: tianditu-map
description: 天地图地图数据操作执行 skill。配置双主力 key 池（key3+key4），直接调用天地图 API 出结果：地理编码（地址转坐标）、逆地理编码（坐标转地址）、POI/地名搜索、CSV 批量地理编码（多key并发、楼栋级去重、断点续跑、429退避）、城市小区 POI 爬取、Leaflet 地图可视化、CSV 坐标回写数据库（人工门禁）。当用户需要地址转经纬度、坐标转地址、批量编码、拉小区点位、出地图时使用。与 tianditu-webapi（API 开发指南）互补：那个讲怎么写代码，这个直接出结果。
license: MIT
metadata:
  version: 1.1.0
  homepage: http://lbs.tianditu.gov.cn
  evidence: evidence/（实测截图证据包，见 README）
---

# tianditu-map · 天地图地图数据操作 Skill

> 认证构造题证据包（对应《AI应用能力培训与认证方案》构造题 40 分六项标准）
> 版本 v1.1 · 最后更新 2026-09-09

---

## 一、场景说明

- **一句话定位**：为"设备/小区名单地理数据加工"场景构造一个 Skill，把散落的地址批量转成经纬度，并支持城市小区 POI 拉取、地图可视化与坐标回写数据库，全程留痕可复核。
- **业务背景**：物联网项目实施中，供热/供水 IoT 设备表只有简写地址（如"西夏小区15-1-203"，无省市前缀）且无坐标；客户要求台账在地图上可定位。人工 7 万行逐个查坐标不可行。同时验收需要"城市小区分布图"。
- **目标**：
  1. 批量地理编码：70432 行设备地址 → 经纬度，100% 命中，楼栋级去重省 5 倍调用量；
  2. 城市小区 POI 拉取：网格切分遍历突破单关键词 300 条上限，产出小区点位 CSV/GeoJSON；
  3. 地图可视化：Leaflet 聚合打点 HTML，天地图底图；
  4. 坐标回写数据库（Kingbase）：**默认预览，人工确认后才写库**；
  5. 每次产出自动生成【待复核】复核清单，人工核验留痕。

---

## 二、来源（资料来源可追溯）

| 数据源 | 固定来源位置 | 版本/日期 | 适用范围 |
|---|---|---|---|
| 天地图 Web API | http://lbs.tianditu.gov.cn/server/api2.html（地理编码/逆地理编码/v2搜索） | 2026-09-09 实测 | gcj02ll 坐标系，全国 |
| 天地图 API Key | 本机 `config/keys.local.json`（.gitignore，不入库）；公开文件只写环境变量引用名 | v1.1 | 仅服务端接口；浏览器端 key 服务端调用 301012 |
| 银川 IoT 设备源表 | `D:\backup\user1\majq\Desktop\iot_equip_info_202609091148.csv`（GBK，4列） | 2026-09-09 导出 | 14 家供热企业设备，70432 行 |
| 编码成果 | `D:\backup\user1\majq\Desktop\iot_equip_info_202609091148_geo.csv` | 2026-09-09 | 同源表，x/Y 已填满 |
| 目标数据库 | `172.28.43.118:30209/test`（Kingbase，库 iotbase，模式 iotbase，表 iot_equip_info）；连接串仅放环境变量 `TIANDITU_DB_DSN` | 2026-09-09 实测 | 仅该表，仅 x/y/longitude/latitude 四列 |
| 银川城区范围 | 实测 bbox `106.0,38.3,106.6,38.6`（高德区划边界交叉验证） | 2026-09-09 | 银川城区 |

> 来源原则：写"固定位置"而不是"网上搜的"；别人按路径能找到同一份数据。

---

## 三、Skill 范围

| 项 | 内容 |
|---|---|
| Skill 名称 | `tianditu-map` |
| 选择理由 | 批量地理编码+小区POI+地图+回写是重复固定流程（调用→编码→核验→回写），适合封装；触发条件明确，他人装上即可复用 |
| 版本 | v1.1（增量版本见 §四；如有全局发布记录以 Skill Manager 为准） |
| 读权限 | 天地图 API（只读）、指定设备 CSV、指定数据库表（apply-db 预览时只读统计） |
| 写权限 | 仅本地输出目录（CSV/GeoJSON/HTML/复核清单）；写数据库必须 `--confirm "确认写入"` 人工门禁 |
| 禁止 | 跨项目读取、未授权批量写库、key 明文入库/入文档、未经确认写库 |
| 输入 | 地址/CSV、bbox、关键词、key 池（本机配置）、可选数据库连接串 |
| 预期输出 | 单条坐标 JSON、批量 CSV+复核清单、小区 POI CSV/GeoJSON、地图 HTML、写库预览 SQL / 执行结果 |

**停止条件**：无可用 key、CSV 无有效坐标、数据库连接失败、标识符合法性校验不过 → 返回 `{"ok":false,"gap":...}` 并停止，不伪装成功。

---

## 四、问题/提示词（任务卡 + 关键迭代）

**① 任务卡**
```
问题：如何把 70432 条只有简写地址的 IoT 设备坐标填全并回写数据库？
目标：批量地理编码 100% 命中 → 坐标回写 iot_equip_info 表 → 人工抽检留痕
资料来源：iot_equip_info_202609091148.csv、天地图 geocoder API、Kingbase iotbase 库
待确认项：CSV 无主键（仅 equip_name+address）；44 行鑫尔特地址是设备号非地址
选择的工具/Skill：tianditu-map（geocode→batch→apply-db）
人工确认点：写库前人工抽检 + 输入 --confirm "确认写入"
最终交付物：geo.csv（坐标填满）+ iot_equip_info_bak_xy_20260909 备份表 + 复核清单
```

**② 首轮提示词（实际用过的）**
```
请用 tianditu-map 的 batch 命令，为 iot_equip_info_202609091148.csv 批量地理编码：
1) 地址统一加前缀 "宁夏银川市"；CSV 是 GBK，--encoding gbk
2) 楼栋级去重后编码（省 5 倍调用量），断点续跑
3) 产出 geo.csv 后先给我复核清单，不写库
4) 我抽检确认后，再用 apply-db --confirm "确认写入" 回写 Kingbase
```

**③ 关键迭代记录（v1.0 → v1.1）**
- 第 1 轮：单 key 编码，429 频发 → 引入双 key 池轮询 + 指数退避；
- 第 2 轮：环境变量里的浏览器端 key（721342…）混入池导致请求全部 301012 → 增加"权限错误自动摘除"（KeyPool.disable）；
- 第 3 轮：crawl-communities 返回 0 小区（search() 已把 lonlat 拆成 lon/lat，爬取仍按 lonlat 读）→ 统一用 lon/lat 字段，银川全城 8896 小区验证；
- 第 4 轮：地址编码成果回写数据库——曾因 CSV 无主键用 name+addr 匹配（含 219 行重复设备），重复行同地址同坐标属预期；44 行鑫尔特设备地址被 Excel 转科学计数法损坏 → 跳过并人工补地址；
- 第 5 轮（v1.1）：按认证红线增加写库人工门禁 `apply-db`（无 `--confirm` 仅预览 SQL）+ 批量产物【待复核】清单。

---

## 五、人工复核

| 复核项 | AI 初稿 | 人工核验后发现 | 修改动作 | 复核人/时间 |
|---|---|---|---|---|
| 西夏小区坐标 | 旧默认点 106.278179,38.46637 | 表内 99.6% 旧坐标是同一默认点，无意义 | 用编码结果 106.10047,38.48822 覆盖 | 马健权 / 2026-09-09 17:40 |
| 鑫尔特 44 台设备 | 尝试编码 | 表内 address 是设备号长数字（非地址），CSV 被 Excel 转科学计数法损坏 | 跳过不写，列入人工补地址清单 | 马健权 / 2026-09-09 17:42 |
| x/y 与 longitude/latitude | 只打算写 x/y | 表中四列成对维护 | 四列同步写入保持一致 | 马健权 / 2026-09-09 17:45 |
| 楼栋级去重 | 连楼号一起截断 | 不同楼栋应保留楼号 | 只去末尾一段纯数字房号 | 马健权 / 2026-09-09 18:20 |
| 写库 | 直接 UPDATE | 认证红线要求人工确认 | 增加 apply-db `--confirm "确认写入"` 门禁 | 马健权 / 2026-09-09 |

> 关键设计：batch 产物默认标【待复核】并生成 `*.review.md`；apply-db 缺 `--confirm` 只预览 SQL。"AI 输出未核验即发送/写库"在技术上不可能发生。

---

## 六、风险边界

| 类别 | 说明 |
|---|---|
| 授权范围 | 只处理授权来源：指定设备 CSV 与指定数据库表、银川小区 POI；不跨项目读取 |
| 密钥管理 | **公开文件不含明文 API key / 数据库密码**：key 在 `config/keys.local.json`（.gitignore）或环境变量；DB 连接串仅环境变量 `TIANDITU_DB_DSN`；配置只写环境变量引用名 |
| 脱敏规则 | 产物只输出小区名/地址/经纬度；设备号变体（如历史 CSV 科学计数法行）不写库；证据包不含敏感字段 |
| 禁止输入 | 不向 AI 输入密码/密钥原文；skill 文档和代码不出现 key 明文 |
| 工具权限 | 天地图 API 只读；batch/map 只写本地输出目录；apply-db 标识符合法性白名单校验（防注入），默认预览，`--confirm "确认写入"` 才在事务中执行（失败回滚） |
| 必须人工确认点 | ① 写库前抽检 + 输入 `--confirm "确认写入"`；② 未命中地址人工补地址；③ 前端 key 类型核验 |
| 停止条件 | 无 key / CSV 无坐标 / 连接失败 / 非法标识符 / 权限错误 → 返回 `{"ok":false,"gap":...}` 停止，不伪装成功 |

**反向测试（实测通过，见证据包）**：无 `--confirm` 仅预览；非法表名被白名单拦截；坏 key 自动摘除；无 DSN 时 gap 停止。

---

## 快速用法（原技术手册保留）

```bash
S=.../tianditu-map/scripts/tdt.py
python "$S" geocode "宁夏银川市西夏小区15-1-203"      # 地址→坐标
python "$S" reverse 106.10047 38.48822                # 坐标→地址
python "$S" search "超市" --map-bound "106.0,38.3,106.6,38.6" --count 20
python "$S" batch 设备表.csv --col address --out 结果.csv --prefix "宁夏银川市" --encoding gbk
python "$S" crawl-communities "106.0,38.3,106.6,38.6" --out-prefix yinchuan_comm --keywords "小区,花园,家园" --grid-size 0.1
python "$S" map yinchuan_comm.csv --out map.html --title "银川小区分布"
python "$S" apply-db 结果.csv --table iotbase.iot_equip_info --confirm "确认写入"
python "$S" keys
```

## key 池与已知坑

- `keys.json`（公开范本）只含环境变量引用名；真实 key 在 `config/keys.local.json` 或 `TIANDITU_MAP_KEYS` 环境变量（逗号分隔，可临时追加）
- **浏览器端 key 服务端调用必 301012/403**（带 Referer 也没用，类型级拦截）；坏 key 自动摘除
- 简写地址必须加省市前缀（如 `--prefix "宁夏银川市"`）；CSV 是 GBK 时 `--encoding gbk`
- 天地图只给小区**中心点**，不提供边界多边形（v2/search、行政区、geocoder 实测均无边界字段）
- v2.0 搜索不支持 queryType=1/4/7，用 2（视野内）替代
- 批量跑完先确认输出已落盘再考虑删 ckpt
