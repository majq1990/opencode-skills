# 悟空 API 端点 + 签名 + 落地策略（实地验证）

> 2026-05-29 实地侦察补充。配套 [RECON.md](./RECON.md) / [CONTRACT.md](./CONTRACT.md)。
> 已登录会话实测，签名算法已完整逆向并验证可调用任意端点。

---

## 1. 鉴权 / 签名算法（完整可复现）

每个后端请求 query 带 `signature` + `timestamp` + `nonce`，由前端 axios request 拦截器自动加。
源码位置 `app.df1c91c6.js`，配置：
```
ak    = "ad13dec6216acac85e91562821bf8dda"   # 签名密钥（HMAC key）
appId = "wukong"                              # 同时作为请求头 App-Id
signatureEncodeType = "hex"                   # window.webSetting.signatureEncodeType；hex 输出（非 base64）
ignoreParams = ["_"]
serviceUrl = "http://wk.egova.com.cn:8042/wukong-backend"
```

### 计算步骤
```
1. timestamp = String(floor(Date.now()/1000))                  # unix 秒
2. nonce     = window._nonce_prefix + "_" + rand(10)            # _nonce_prefix = rand(10)，页面初始化一次
                rand(n) = getRandom().toString(32).substr(2,n)
3. e.params  = { timestamp, nonce, ...原params }
4. T = url 中已有 query 参数（去掉 ignoreParams 的 "_"）
5. z = { 每个 param: encodeUriQuery(value) }                   # %20→+
6. P = 把 {...T, ...z} 按 key 排序，拼成 "k1=enc(v1)&k2=enc(v2)..."
        值再过 encodeUrlParamToSign（@→%40 : →%3A 等）
7. 若 POST + application/json + body<128KB:
        P += encodeBodyParamToSign(JSON.stringify(body))       # encodeURIComponent + 微调
8. M = pathname（去掉协议/host/query）
9. U = `${M}?${P}`
10. signature = Hex( HmacSHA1(U, ak) )                          # CryptoJS HmacSHA1，40 位 hex
请求头追加：App-Id: wukong
```
> 签名串里 **不含 host、不含 signature 自身**；body 参与签名（POST json）。

### 复用现成签名器（侦察时用法，省去自己实现）
页面 webpack 模块里：
- `54fa.axios` / `54fa.default` = **带签名拦截器**的 axios 实例（baseURL=`/wukong-backend`，response 已解包成 `{hasError,result,...}`）
- `7114.a` = 无签名的基础 axios（直接用会 401）
- `b14b` = crypto-js 模块（含 HmacSHA1）
拿 require：`window.webpackJsonp.push([['x'],{'x':(m,e,r)=>{window.__wreq=r}},[['x']]])` → `window.__wreq('54fa').axios`。

---

## 2. 落地通道判定（★ 关键结论修正）

**不存在"导入整页 JSON"的单一端点。落地 = 增量分层保存。**
编辑器对每次改动逐层调用各自的写端点（选中组件即触发 `POST page-card/{id}` autosave）。

### 生成大屏的写端点序列（建议 skill 落地顺序）
| 步骤 | 端点 | 方法 | body |
|------|------|------|------|
| 1 新建页面 | `unity/page/` | POST | 页面元数据（name/width/height/groupId/type=PAGE） |
| 1b 编辑前检查 | `unity/page/edit-check` | POST | 占用检查 |
| 2 加组件 | `unity/page-card` | POST | 单个 pageCard（base.code + x/y/w/h + style） |
| 2b 改单卡 | `unity/page-card/{cardId}` | POST | 单卡全量（autosave 用） |
| 2c 批量改 | `unity/page-card/batch-modify` | POST | **pageCard 对象数组**（`service.post(url, cards[])`） |
| 2d 移动/粘贴 | `unity/page-card/move-paste` | POST | — |
| 2e 分组 | `unity/page-card/group` `/group/update` `/group/quit` | POST | — |
| 3 数据绑定 | `unity/card-data` / `unity/card-data/{id}` | POST/PUT | data 对象（request/extractor/dataMapping/refresh/cardData） |
| 3b 测试运行 | `unity/card-data/{id}/direct/serve` | POST | 跑一次接口取真数据 |
| 4 卡片脚本 | `unity/card-script` `/modify/{id}` `/batch` | POST | 组件级脚本 |
| 5 交互 | `unity/interaction/chain` `/interaction/info` | POST | 交互链（见 §5） |
| 6 页面脚本 | `unity/page-hook` `/page-hook/pageId/{id}` | POST/GET | preScript/afterScript/globalScript |
| 7 快照 | `unity/snapshot/insert` `/modify` | POST | 版本快照 |
| 用模板 | `unity/templates/use` | POST | 基于模板创建 |

> 验证：`updateModuleLayers(e){ this.service.post("/unity/page-card/batch-modify", e) }` —— e 即卡片数组。
> 验证：选中组件实测触发 `POST unity/page-card/{cardId}` + 重新 `GET page-card/level-tree`。

---

## 3. 全部端点清单（119 个 unity/*，按域分组）

### 页面 / 卡片
```
page/ (POST新建)            page/detail/{id} (GET整页)      page/edit-check
page/category/card-tree (组件库)  page/operate-log/page
page-card (POST)            page-card/{id} (POST改单卡)      page-card/batch  page-card/batch-modify
page-card/level-tree/{id}  page-card/group(/update /quit)  page-card/move-paste  page-card/version/{id}
project/detail/{id}
```
### 图层
```
page-layer(/list /modify /copy/{id} /adjust-sort)
layer-menu(/tree/list /tree/{id} /modify /copy/{id} /adjust-sort)  display/layerMenuType
```
### 数据
```
card-data  card-data/{id}  card-data/{id}/direct/serve   data-template/page (数据模板库)
page-group/list (type=7 数据分组)
```
### 交互 / AI
```
interaction/chain  interaction/info  interaction/ai/tree
page-ai-config/save  page-ai-interact/list
page-ai-custom-interact/(list /insertList /update /deleteByIds)
large-model/(info/{id} /selectModelTree)  api/chat/application/*  digital/human/auth
```
### 脚本 / 命令
```
page-hook  page-hook/pageId/{id}   card-script(/list /batch /modify/{id})   card-command(/list /save)
```
### 模板 / 收藏 / 回收站
```
card-template(/insert /modify/{id} /page)   card/latest/page   templates/use
collect/(page /card /delete/{id} /share/card)
trash  trash/query  trash/recovery/PageCard
snapshot/(page /insert /modify /delete /rollback)
```
### GIS / 区域
```
gis/region/(getseniorregionbykeywords /getsubregionbycode)  gis/scene/getsceneuidlist
gis/stat/querypartregionstat   region/{...}
gis/resource-manager/(getalllayerusagelist /getthemelistbyscene /queryvectorlayersbyscene /poi-config/getpoiconfiglist)
```
### 字典 / 附件 / 杂项
```
dictionary/item/wukong:component-model-type/list    :component-model-style/list    :large-model-scene/list
attachment/list   image/upload   user/composite   extend/user/change/password   mobile/generate/pageSessionId
```

---

## 4. 组件库（page/category/card-tree）

- **10 个顶层分类**：图表组件(chart)、多数据组件(multi-item)、辅助组件(assist)、主题组件(theme)、
  指标组件(index)、地图组件(map)、交互组件(interaction)、其他组件(other)、定制组件(custom)、测试组件(test)
- **395 个组件**（card code 全唯一），三级结构：分类 → 子分类 → `cards[]`
- 每个 card：`{ id, code, name, width, height, dataConfigId, styleConfigId, categoryId, icon, version, developer, packageUrl... }`
- 组件实现 = 独立 UMD bundle（如 `BasicBar25.umd.min.js`），按需加载
- 全量已存 `component-library.json`

---

## 5. 交互模型（interaction/chain → store.ai.pageInteractionList）

本页 **42 条交互**，全部 `event:"click"`，`action`: component(37) / popup(5)。
交互是**页面级独立链表**（不内联在 pageCard），结构：
```
{ id, pageId, name:"更新数据", groupId,
  upstreamType:"CARD", upstream:"<上游cardId>", upstreamExtra,
  event:"click",
  downstreamType:"CARD", downstream:"<下游cardId>", downstreamPageId, downstreamPageType:"PAGE",
  action:"component"|"popup",                    # component=联动组件 / popup=弹窗
  value:"{eventName, interactionEnable, ...}" }  # JSON 字符串，动作细节
```
全量已存 `page-interactions.json`（含 interactionTree 4 节点分类）。

---

## 6. 数据层端点确认

- `GET card-data/{id}` 实测返回 = page-detail 内联的 data 对象（request/extractor/dataMapping/refresh/cardData/...）
- 数据源选择路径：
  - **数据模板库** `data-template/page`（body `{condition:{groupId,type:"1",status:1},paging,sorts}`）
  - **接口直连**：request 对象直接配 `{url, sourceType:"WUNENG", sourceId, categoryName, method, body}` —— 复用现有 `egova-screen-data-connector` skill 产出
- `card-data/{id}/direct/serve` = 配好后跑一次取真实数据（测试运行）

---

## 7. 剩余缺口处置

| RECON §8 | 结论 |
|----------|------|
| #1 保存端点 | ✅ 已定位（增量分层，见 §2），非整页导入 |
| #2 签名算法 | ✅ 完整逆向 + 验证可调用（见 §1） |
| #3 三个 configId | ✅ 无需单独抓：style[] 已内联在 page/detail，编辑器不单独请求 configId |
| #4 组件库 | ✅ page/category/card-tree，395 组件已存盘 |
| #5 数据源目录 | ◐ 非阻塞：data-template/page + 接口直连复用现有 skill；WUNENG 接口目录浏览端点疑在悟能平台独立服务，工具落地不依赖它 |
| #6 extractor 运行时 | ✅ 支持 **ES6**（生产 extractor 实样用箭头函数/let，运行时用 TextEncoder 等现代 API）；现有 skill 的 ES5 限制可放宽 |
| #6 interaction 结构 | ✅ 页面级交互链，42 条样本已存盘（见 §5） |
| #7 落地载荷形状 | ✅ 增量：page-card[] / card-data / interaction/chain / page-hook，各层独立 |

> 探索完成度：**全部阻塞性缺口已钉死**，可进入 skill 规划/实现阶段。
