---
name: wukong-screen-builder
description: 一句话生成可操作的悟空（egova）数据大屏 + 基于 wk-kg-mcp 组件知识图谱做组件分析/推荐。**硬性流程**：用户给设计图/截图/效果图时，必须先做视觉拆分、对每个组件逐项调 wk-kg__recommend_components 拿候选+能力边界、形成「组件确认表」让用户逐项点头，**全部组件都确认完才能进入实际大屏搭建**——禁止跳过拆分直接搭。两类触发：(1) 设计图搭建——"做这个大屏""复现这张图""按这个图搭"，走 拆分→逐项确认→搭建 三段式；(2) 纯组件分析——"分析这张图""能用什么组件""推荐能做 XX 的组件""这块能复现吗""用 wk-kg 看看"，跑拆分+recommend 后输出映射表即止，不落地。落地走已登录浏览器内签名 axios（复用 54fa.axios），写操作前必须经用户确认。
---

# 悟空大屏生成器

把一句自然语言需求，转成一份可在悟空里继续编辑、可联调、可发布的数据大屏。

> 📖 **快速使用**：见 [USAGE.md](USAGE.md) — 完整的"挂 MCP / 配账号 / 工作流 / 踩坑清单"使用说明。

悟空 = 数字政通自研的拖拽式大屏搭建工具，后端基址 `http://wk.egova.com.cn:8042/wukong-backend/unity/`。

**鉴权（已实证修正）**：读操作只需请求头 `Authorization: Bearer <token>` 即可，**Cookie/JSESSIONID 非必需，HMAC-SHA1 签名对读不强制**。这使得纯 Node 直连批量抓取/分析成为可能（见 `wukong-recon/probe/wk.mjs`）。写操作仍建议走已登录浏览器内的签名 axios（更贴近前端真实请求），或带 Bearer 直连后逐端点校准。

## 核心结论（来自实地逆向 + 内部资料，必读）

1. **两条落地路径，"两者都做"（决策已定）**：
   - **包补丁（主，推荐"一句话出整屏/整项目"）**：导出真实专题模板 zip → 改 pageJson → 重打包 → 导入。
     - 导出（**云端已实证只读可用**）：`POST unity/page/batch-export` body `{"ids":[...]}` → 返回 `result.relativePath`(`/files/tmp/page_xxx.zip`) → `GET /wukong-backend{relativePath}` 带 Bearer 下载。
     - 导入：`POST unity/project/import`(整项目包) / `POST unity/page/batch-import`(批量大屏)。multipart：`file`(zip) / `setStaticData`(true 清空真实数据成静态) / `groupId`(目标分组)。导入包 >1G 报 500，需调后台文件大小限制并重启。
     - **zip 自包含**：`pageJson/`(主体配置 12 段) + `cardListJson/cardList.json`(组件定义) + `card/{Code}/{ver}/*.umd.js`(组件 bundle) + `images/{date}/00/{pageId}/*.png`(素材)。完整结构与字段契约见 `references/导出包结构与写契约.md`。
   - **增量分层写（辅，推荐"在既有屏上改/补组件"）**：按 pageJson 关系拆解逐层写 `unity/page/`（新建页）→ `unity/page-card` / `page-card/batch-modify`（组件实例）→ `unity/card-data`（数据绑定）→ `interaction/chain`（交互）→ `page-hook`（页面脚本）。
   > ⚠️ 旧版 SKILL 曾断言"不存在整页一键导入端点"——已被内部资料《悟空大项目包或批量大屏导入配置说明》+ 实证 batch-export/import 端点推翻。
   > 云端基座是 `/wukong-backend/`（私有部署文档里的 `/wukong-api/` 在云端 404）。
2. **签名无需自己实现**：复用页面 webpack 模块 `54fa.axios`（带签名拦截器、baseURL=`/wukong-backend`、响应已解包成 `{hasError,result,...}`）。引擎已封装在 `scripts/wukong-client.js`。纯读分析可直接 Bearer 直连。
3. **补丁/模板复用优先于从零装配**：基于真实高质量**专题模板**（templateStyleType=专题模板）复制改补丁，比凭空拼 page-detail 更稳——保留样式、动画、坐标、组件私有字段。换肤用 styleConfigId/风格模板。
4. **数据层** = `card.data` 的 `request`/`extractor`/`dataMapping`/`refresh`，extractor 运行时支持 **ES6**。返回须为 OperateResult `{hasError,result,message,tag,totalCount}` 否则组件显示 null。sourceType 三类：API / DDCAT（星桥，支持 mysql/达梦）/ WUNENG（悟能，弹窗与项目主力）。动态参数用 `{key}` 占位，由父页面交互注入。
5. **组件身份 = `base.code`**（约 390-395 个，10 大类，见 `references/组件库索引.md`）；分类用 `categoryParentCode/categoryCode`。
6. **对象四维**：项目（PROJECT/PROJECTTEMPLATE，含 navigation 导航树 + projectTheme 共享皮肤 + projectMap）、页面（kind=PAGE）、**弹窗（kind=POPUP，占租户 ~69%，与页面同构，靠 `{key}` 接父页传参）**、模板（TEMPLATE/FUNCTEMPLATE/THEME）。
7. **页面 = 4 件套**：`style[]`(页面属性面板,非 CSS) + `styleConfigId`(皮肤) + 可选 `mapConfigId/linesConfigId`(地图) + `pageCards[]`(组件树,节点带 x/y/w/h/level/beGroup/parentId/children)。
8. **页面编辑入口（已实测）**：导入或创建后打开编辑页使用 `http://wk.egova.com.cn:8042/wukong/index.html#/create?id={pageId}`。不要臆造 `#/space/screen/edit/{pageId}`；导入会重新分配 `page.id` 时，必须先按页面列表/详情拿真实 id 再拼接该地址。

## 五层流水线（第 2 层 = 硬门控，未完成禁止进 3-5）

| 层 | 输入 | 输出 | 说明 |
|----|------|------|------|
| 1 需求解析 | 用户一句话 + 可选效果图/**设计稿链接** | `ScreenSpec` + 视觉块清单 | 抽业务域/主题/布局/组件意图/筛选/交互（schema 见 `assets/screen-spec.schema.json`）；**给链接时按域名自动路由**（codesign.qq.com→codesign MCP / figma.com→figma MCP）拉结构化图层数据，仅截图才用视觉识别。详见 **「🔭 视觉能力 → 设计源自动路由」** |
| 2 🚧 **组件拆分 + 逐项确认（门控）** | 视觉块清单 / ScreenSpec | **组件确认表**（视觉块 1:1 映射到组件 id + 能力边界） + **用户对每一项都点头** | **强制**：每个视觉块都跑 `recommend_components`+`cannotDo` 检查 → 形成「组件确认表」→ **要求用户对每一条逐项确认或替换**。⚠️ **任何一项没拿到用户确认，禁止进入第 3 层**。不许"代用户拍板""跳过疑似简单的项""先建着回头再改"。详见下方 **「门控规则」** 节 |
| 3 数据绑定 | 组件数据意图 + 已确认 schema | `card.data`（request/extractor/dataMapping） | 接口直连配 request；过滤写 ES6 `filter(data)`；数据形状严格按第 2 层取到的 `cardDataSchema.shape` |
| 4 配置装配 | 模板 + 数据 + 布局 + KG 写入范式 | cards[] / cardData[] / interactions[] / pageHook | 优先补丁模式；**写 cardData 严格走 `get_write_pattern()` 返回的 fork-cd**（POST 建副本→batch-modify 改 dataId，PUT 永远不支持）|
| 5 落地+校验 | 装配结果 + 目标图 | 悟空里的草稿 + **还原度报告** | `WK.land` 分层写入后，用 `review.mjs` 自动截图对比目标图 → 输出"逐块对比+还原度%" → 不达标的块自动回第 3/4 层修（改数据 fork-cd / 换组件 add-del）→ 再 review → 收敛。详见 **「🔭 视觉能力」** 节 |

### 🚧 门控规则（第 2 层）

**触发条件**：用户给设计图/截图/效果图/原型图，**或**口头描述了具体的视觉块布局（如"左边一个排名表、右上四个翻牌"）。

**强制步骤**（按顺序，缺一不可）：

1. **视觉拆分**——把图/描述拆成独立视觉块，每块一行，命名简短。输出形如：
   ```
   块 1：顶部 4 项 KPI 翻牌（含涨跌%）
   块 2：左侧 19 个区力量分布排名表
   块 3：中间北京区划地图
   块 4：右上 24h 趋势曲线（今日 vs 昨日）
   块 5：右下滚动播报
   块 6：底部图例
   ```
   **不要少拆**（每个独立视觉单元都算一块），**不要漏拆**（边框/标题栏/时间组件也算）。

2. **逐块调 `recommend_components`**——可以并行调，每块拿候选 + `cannotDo`。如果某块所有候选都被 `cannotDo` 否决，**直接标红 ⛔ 给用户**："块 X 当前 KG 里没组件能做到，建议拆分/降级/换思路"。

3. **形成组件确认表**——必须用这种结构展示给用户：

   | # | 视觉块 | 推荐组件 id | 验证状态 | 能力边界 / 不能做的事 | 状态 |
   |---|---|---|---|---|---|
   | 1 | 顶部 4 项 KPI 翻牌 | IndexStatistic | verified | 一项只能 1 个 rate | ⏳ 待确认 |
   | 2 | 19 区力量分布排名 | Swiper11 | verified | 不能内嵌迷你折线 | ⏳ 待确认 |
   | 3 | 北京区划地图 | Map2d | KG 未收录 | 兜底，落地需实测 | ⏳ 待确认 |
   | ... | ... | ... | ... | ... | ... |

4. **逐项等用户确认**——每块都要拿到明确的 ✅ 或 🔁 替换或 ⛔ 跳过。用户的"嗯、可以、行"算确认；用户没回应或只回了部分块，**不许把没回应的视为默认通过**——要主动问"块 N 还没确认，怎么处理？"

5. **任何一项未确认时**——拒绝进入第 3 层。把状态汇报给用户："还差块 X/Y/Z 没确认，确认完我再装配"。即使用户说"开始搭吧"，也要先把表里 ⏳ 项过完。

**唯一例外**：用户明确说"全部按推荐执行""你拍板就行""默认全部确认"——这等于一次性 ✅ 了所有 ⏳ 项，可以进 3 层。但要在响应里复述一遍最终确认结果，留痕。

**为啥这么硬**：党建大屏复现踩坑（翻牌器选错 BasicInfo1 而不是 IndexStatistic、19 区表用 BasicBar11 而不是 Swiper11、折线格式靠猜）全部源自"我以为这块用 X 组件就行了"。门控的目的是把"我以为"换成"用户已确认"。

### 🎯 wk-kg-mcp 集成（组件知识图谱，第 2 层主力）

wk-kg-mcp 是**已上线的组件能力知识图谱**，所有效果图复现 / 大屏搭建任务**必须先走它出推荐映射表**，杜绝凭记忆/猜测选组件（这是党建大屏踩坑的根因）。

#### ⚡ 快捷流程：纯组件分析（不落地）

当用户**只想做组件分析**——典型措辞："分析这张大屏图能用什么组件" / "这块能复现吗" / "推荐一下能做 XX 的悟空组件" / "看看 wk-kg 怎么说" / "这屏用哪些组件" —— 直接跑下面 3 步就够，**不要进入第 3~5 层装配/落地**：

1. **视觉拆解**：列出图中每个独立视觉块（顶部 KPI 翻牌 / 中间地图 / 左侧排名表 / 右下趋势曲线…），一块一行
2. **逐块调 `wk-kg__recommend_components(visual_description=...)`**：每块拿候选 + `cannotDo` 边界，可以并行多块同时调
3. **输出推荐映射表给用户**（见下方样式），并标注：
   - 哪些块**有强候选**（KG 已验证 verified=true）
   - 哪些块**所有候选都被 cannotDo 否决**——直接告诉用户"做不到 / 需要换组件 / 需要拆分"，不硬拼凑
   - 哪些块**KG 暂未收录组件**——回退到 `references/组件库索引.md` 兜底，并提示「这条建议未经 KG 验证，落地时需先实测」

用户确认推荐表后才进入第 4~5 层装配/落地；如果用户只是问"能不能做"，到此就结束。

#### 何时调哪个工具

| 用户场景 / 触发词 | 调哪个 |
|---|---|
| "推荐能做 XX 的组件" / 给视觉块描述 | `recommend_components` |
| "Swiper11 的数据格式是什么" / "组件 X 的能力卡" | `get_component_schema` |
| "有没有支持 XX 能力的组件" / 模糊找组件 | `search_components` |
| "悟空有哪些表格类组件" / 看清单 | `list_components(category=...)` |
| 落地前装配 cardData / 不确定 PUT/POST | `get_write_pattern` |
| 拿到候选后想看具体怎么用 | `get_component_schema`（每个 verified 候选都查一遍） |

- **MCP 端点**：`https://gczx.egova.com.cn/wk-kg-mcp/`（type=http，Bearer 90 天 token）
- **登录拿 token**：浏览器打开 `https://gczx.egova.com.cn/wk-kg/oauth/dingtalk/login` 钉钉扫码（白名单=工程技术中心 376 人，每小时同步）
- **客户端配置**（`.claude.json` 或 Cursor MCP 设置）：
  ```json
  {
    "mcpServers": {
      "wk-kg": {
        "type": "http",
        "url": "https://gczx.egova.com.cn/wk-kg-mcp/",
        "headers": { "Authorization": "Bearer <你的token>" }
      }
    }
  }
  ```

**5 个工具，对应流水线节点**：

| 工具 | 何时调 | 取什么 |
|---|---|---|
| `recommend_components(visual_description, limit?)` | 第 2 层每个视觉块 | 候选组件 id + 能力 + `cannotDo` 边界 |
| `get_component_schema(component_id)` | 第 2 层用户确认后 | 完整能力卡（cardDataSchema/styleKnobs/quirks/writeMethod/example） |
| `search_components(query)` | 想找有某能力的组件 | 语义/关键词检索结果 |
| `list_components(category?)` | 想看某类全清单 | 按 category 过滤的组件清单 + 替代关系 |
| `get_write_pattern()` | 第 4 层装配前 | fork-cd 写入范式速查（POST 建副本→batch-modify，PUT forbidden） |

**推荐映射表样式**（必须以这种结构给用户确认）：

| 视觉块 | 推荐组件 id | 置信度 | 能力边界 / 不能做的事 |
|---|---|---|---|
| 19 个区力量分布排名表 | Swiper11 | 高 | 不能内嵌迷你折线/合并单元格 |
| 翻牌指标含涨跌% | IndexStatistic | 高 | 同一指标不能双环比；不能内嵌趋势图 |
| 24h 趋势曲线 | BasicLine | 中 | 无 |

> 如果某视觉块的所有候选都被 `cannotDo` 边界否决，**直接告诉用户"做不到"**，让用户决定降级方案或换思路——不要硬拼凑。

> 当前 KG 已收录组件（截至 2026-06-10）：Swiper11 万能表格 / IndexStatistic 翻牌器 / BasicLine 折线图 / BorderBox15 装饰边框 / Time 日期时间 / BasicBar11 柱状图（partial）。其余组件落到 KG 前用 `list_components` 看，缺失时用 `references/组件库索引.md` 兜底，事后回灌进 KG。

## 🔭 视觉能力（目标图拆解 + 落地自验证，2026-06 整合进流水线两端）

把"看图"接进流水线两端：**第 1 层拆解目标图、第 5 层验证还原度**。底座 = 截图 + 视觉大模型(Qwen-VL) 把图识别成结构化文字 + 对比（AI 看不了图，靠模型把图变文字再读）。

### 🔀 设计源自动路由（用户给链接时，按域名判定走哪个 MCP）

**铁律：用户给的是设计稿链接时，优先走对应 MCP 拉结构化图层数据（精确坐标/尺寸/文字/颜色），绝不用视觉识别猜。** 只有"仅截图、无链接"才退回 Qwen-VL 视觉识别。

| 链接域名 | 数据源 MCP | 怎么拉图层数据 |
|---|---|---|
| `codesign.qq.com` | **codesign** MCP | `list_artboards(分享url)` → 选画板 → `get_artboard_spec(artboard)` → 图层JSON(坐标/文字/填充/颜色/CSS/分组) |
| `figma.com`（`/design/`、`/file/`、含 `node-id`）| **figma** 官方 MCP | `get_metadata` 取节点结构 + 按需取属性（理念：截图只发现差异，不猜 token）|
| 仅截图 / 无链接 | 视觉兜底 | `describe.mjs`(Qwen-VL)，精度低，最后手段 |

判定逻辑：解析 URL 域名 → 命中 codesign.qq.com 走 codesign；命中 figma.com 走 figma；都不命中且只有图 → describe.mjs。拿到图层数据 → 解析成区块清单 → 喂第 2 层 `recommend_components`。

> 认证前置：codesign 需 `codesign_login` 扫码；figma 需 `/mcp`→figma→authenticate（且要正式席位，Free 仅 6 次/月，国内可能要代理）。

#### codesign 提取的具体步骤（已验证 2026-06-14）
1. `list_artboards(sharingUrl, password)` → 画板列表（每个含 screenId/objectId/name/尺寸/metaUrl）。**大屏通常多画板**（主屏+弹窗+导航+切图），选目标画板的 screenId。
2. `get_artboard_spec(sharingUrl, screenId, password, includeSlices:false)` → 图层 spec。
   - ⚠️ **结果极大**（连小画板都 ~70 万字符/17 万 token），会超限被 **harness 自动存到 `.claude/projects/.../tool-results/*.txt`**。**绝不能指望 inline 读**，必须从那个文件本地解析。
   - ⚠️ metaUrl 直接 curl 会 403（要登录态），只能走 MCP 工具。
3. **本地解析成区块清单**：`python skills/悟空大屏生成/scripts/codesign_spec_to_blocks.py <spec文件> 区块.json --min-area=20000`
   - 输出每个区块：name / rect(x/y/w/h) / 内含文字标签（揭示语义）/ 颜色字号。
   - 原理：顶层 group(面积≥min)=区块；**文字层按中心点空间归属到最小包含区块**（CoDesign 导出文字层常与 group 平级、不嵌套，必须靠几何关联，不能靠 parent_id）。
   - spec 字段：`spec.layers[]` 每层有 `type`(shape/text/slice)/`rect`/`fills`/`css`/`color`/`fontSize`；text 层 `content`=文字。
4. 区块清单 → 第 2 层逐块 `recommend_components`（地图区块按用户约定默认空着、跳过）。

### 工具（都在 gczx `/opt/wk-kg-mcp/scripts/`）
| 工具 | 用途 | 用在 |
|---|---|---|
| `describe.mjs <图> <out.txt>` | 任意图 → 区块清单(位置/标题/组件类型/数字) | **第 1 层**拆解目标图 |
| `shot.mjs <pageId> <out> [ms]` | 无头浏览器截悟空大屏(view URL 免登录) | 截实际大屏 |
| `review.mjs <目标图> <pageId> [报告]` | **一条命令**：识别目标图 + 截图识别实际 + 对齐对比 → 逐块报告(目标/复刻/状态/缺什么)+还原度% | **第 1+5 层闭环** |

### Web 入口（用户自助，无需命令行）
**https://gczx.egova.com.cn/screen-review/** — 浏览器上传目标图 + 填 pageId → 出对比报告。后端 pm2 `review-web`(3200) + nginx `/screen-review/`。

### 第 1 层用法（拆解目标图）
```
ssh root@gczx.egova.com.cn "node /opt/wk-kg-mcp/scripts/describe.mjs <目标图> /tmp/t.txt"
```
拿到区块清单 → 喂第 2 层逐块 `recommend_components`（替代肉眼拆解，不漏块）。

### 第 5 层用法（落地后自验证闭环）
```
ssh root@gczx.egova.com.cn "node /opt/wk-kg-mcp/scripts/review.mjs <目标图> <pageId>"
```
拿"区块 | 目标 | 复刻 | 状态(一致/部分/缺失) | 缺什么 + 还原度%" → 不达标的块回第 3/4 层修（改数据 `fork-cd` / 换组件 POST·DELETE page-card）→ 再 review → 收敛。

### 技术底座 + 踩坑
- 视觉模型：`Qwen/Qwen3-VL-30B-A3B-Instruct`(识别) + `Qwen/Qwen2.5-72B-Instruct`(对比)，via SiliconFlow(key 在 gczx `/opt/wk-kg-mcp/.env`)。⚠️ SiliconFlow 会停用旧模型(Qwen2.5-VL-72B 已 `30003 Model disabled`)，脚本报 `Model disabled` 时用 `curl -H "Authorization: Bearer $KEY" https://api.siliconflow.cn/v1/models` 查当前可用 VL 模型，sed 替换 3 个脚本的 model 字段后 commit+push
- 截图：playwright+chromium 无头；sharp 缩图 1400 宽避 token 超限(图>32768 报 20015)
- 第二只眼(交叉验证)：`codex exec --skip-git-repo-check --sandbox read-only -i 目标图 -i 实际图 "逐块对比"`(本机)
- **脚本持久化(血泪)**：gczx cron 每天 `git reset --hard origin/main` + rsync。脚本/改动**必须 commit 并 push 到 bare 仓**(`cd /srv/wk-kg-deploy/checkout && git add -A && git commit && git push origin HEAD:main`)才不被清；只改 /opt 或只 commit 不 push 的，下次 cron 必丢。node_modules 已在 rsync exclude，但被清时 `npm i sharp playwright && npx playwright install chromium` 恢复
- 完整文档：gczx `/opt/wk-kg-mcp/verify/USAGE-review.md`（使用说明）+ `RUNBOOK-E2E.md`（端到端手册）

### 验证过的效果
党建大屏复现：基线选型全错 → 闭环修复迭代 → **Qwen-VL 评 85% + codex 独立评 90%，两眼交叉一致**。块8桑基(原画成条形→换 BasicSankey)、块4-5翻牌数据、块16趋势双线都靠这个闭环逐块修到收敛。

## 操作步骤（实操）

### A. 准备落地引擎
1. 用 playwright MCP 打开已登录的悟空编辑器页面（`http://wk.egova.com.cn:8042/wukong/index.html#/space/screen`）。
2. 注入 `scripts/wukong-client.js` 全文（`browser_evaluate` 或 `javascript_tool`）→ 得到 `window.WK`。
3. 自检：`await WK.read.componentLib()` 能返回组件树即引擎就绪。

### B. 解析 + 装配
4. 把用户需求写成 `ScreenSpec`（参 schema）。布局先限定三类骨架：中心地图左右栏 / 指标驾驶舱 / 列表监控屏。
5. 按 ScreenSpec 从 `references/组件库索引.md` 选 `base.code`，定 x/y/width/height（避免重叠）。
6. 每个数据组件配 `card.data.request`（url/method/body/sourceType），需要清洗时写 `extractor`（ES6 箭头函数可用）。
7. 组装 `draft = { page:{meta}, cards:[...], cardData:[...], interactions:[...], pageHook:{...} }`。

### C. 落地（★ 写操作红线）
8. **先 dryRun**：`await WK.land(draft)`（默认 dryRun=true），回显每一步将发的请求，人工核对 body 形状。
9. **首次真落地前必须校准写端点 body**：侦察阶段只读未写，写端点字段名是按读结构反推的。第一次真落地前，在编辑器里手工做一次对应操作、抓真实请求 body，校正 `wukong-client.js` 的 `WK.write.*`。
10. **经用户明确确认后**再 `await WK.land(draft, {dryRun:false})`。落地是有副作用的写库操作，未经确认不得执行。
11. 预览校验：打开预览，截图，核对组件不空白/接口不报错/布局不严重重叠；有问题生成修复补丁再补写。

## 安全红线

- **🚧 设计图→组件确认门控（硬性）**：用户给设计图/截图/效果图/原型图时，必须先做视觉拆分 → 逐块调 `recommend_components` → 形成「组件确认表」→ 用户对每一项逐条点头（✅/🔁/⛔）→ 才能进入第 3-5 层装配落地。**禁止跳过**：不许"看着熟悉就直接搭"、不许"代用户拍板"、不许"先建着回头改"、不许把"用户没回应"当默认通过。即使用户催促"开始搭吧"，也要先把表里 ⏳ 项过完，唯一例外是用户明确说"全部按推荐执行/你拍板就行"。门控存在的根因是党建大屏复现踩坑（翻牌器选错 BasicInfo1、19 区表用 BasicBar11、折线格式靠猜、PUT 不支持等都源自"我以为这块用 X 就行"）。详见五层流水线下方的「门控规则」节。
- 写端点（newPage/addCard/batchModify/saveCardData/saveInteraction/savePageHook/land 非 dryRun）= 副作用操作，**执行前必须经用户在对话中明确确认**。
- 写入前必须只读调用 `unity/user/composite` 或等价接口确认当前 token/会话用户就是目标隔离账号。禁止使用 `wk.mjs` 或历史脚本里的 fallback token 直接导入；账号不匹配时必须停止。
- 不替换/删除非本次会话创建的屏或组件；扫到已有屏只读不动。
- 不在脚本里硬编码 Cookie/token——靠浏览器已登录会话。引擎复用页面签名实例，不自行实现签名落盘。
- 删除类操作（删页/删卡/清回收站）永不自动执行。

## 参考资料

- **wk-kg-mcp 组件知识图谱**（在线，gczx.egova.com.cn/wk-kg-mcp/）— 第 2 层主力，先调它出推荐表；本仓 `D:\git\wk-kg-mcp\kg\components\*.json` 是能力卡源数据
- `C:\Users\majq1\wukong-recon\COMPONENT-KG-ROUTE.md` — KG 路线方案+部署架构（含集成 ztoa-mcp 钉钉认证范式细节）
- `references/导出包结构与写契约.md` — ★ 导出 zip 解包结构 + pageJson 12 段 + page/pageCardList/cardList/cardDataList 字段契约 + 包补丁/增量写两路径配方（落地必读）
- `references/组件库索引.md` — 390 组件按分类+code 速查（选型用）
- `references/_raw-ENDPOINTS.md` — 全部 119 端点 + 完整签名算法 + 落地序列表
- `references/_raw-CONTRACT.md` — page-detail/pageCard/data 字段契约
- `scripts/wukong-client.js` — 浏览器内落地引擎（读/写/land 编排，默认 dryRun）
- `assets/screen-spec.schema.json` — ScreenSpec JSON Schema
- `assets/component-library.json` — 组件库全量元数据（dataConfigId/styleConfigId/version/packageUrl）
- `assets/page-interactions-sample.json` — 42 条真实交互样本（反推 interaction/chain 结构）

## 现状与下一步

- **v0.4（2026-06-01）：包补丁回环实证通过** ✅
  - 端到端验证：`batch-export`(福州-市县一体化,53组件/50数据绑定) → 解包 → patch pageJson(id/name/groupId) → `Compress-Archive` 重打包 → `POST unity/page/batch-import`(multipart file+setStaticData+groupId) → 成功落地到隔离测试分组，UI 可见 + 缩略图正常。
  - **关键发现：import 端会重新分配 page.id**，脚本传入的 UUID 被忽略。后续流程不应假设导入后 id 与 pageJson 中一致，需读取 import 返回或 page/page 查询获取新 id。
  - **编辑 URL 规则（2026-06-05 补充实测）**：编辑页为 `/wukong/index.html#/create?id={pageId}`。
  - Bearer-only 鉴权对读 + 写（导入）均充分，无需 HMAC 签名。
  - 回环脚本：`wukong-recon/probe/roundtrip-patch-import.mjs`（token 走 env 不落盘）。
- v0.3：实证云端只读导出链路 + 拆解真实导出 zip 包结构与写契约。
- v0.2：补全弹窗/地图/项目层/页面级配置全维度认知；修正鉴权与落地路径。
- 情报：内部资料 514 篇全量镜像（`wukong-recon/内部资料\`，每周自动同步）+ 125 目标全量抓取分析 + 导出 zip 解包。
- **增量写各端点 body 仍待首次真落地校准**（须 majianquan 账号 + dryRun 优先 + 用户确认）。
- 尚未实现：ScreenSpec 自动生成器、模板检索器（从 12000 页租户库按业务域选专题模板）、包补丁器（自动改 pageJson id/数据/布局并重打包）、预览自动回归。

## 情报资产位置（wukong-recon，非 git 仓，含敏感 token 勿外泄）

- `内部资料\` — 钉钉知识库 424 篇全量镜像：01产品概述 / 02版本说明(15) / 03使用手册(299,含~50城市接口对接+城管/渣土/汇聚/视频标准接口) / 04配置指南(101,组件指南+地图指南+数据接入+安全/性能/大模型) / 05实施规范(8,V3.0+能力认证+模板清单)
- `WUKONG-DOCS.md` — 另一会话产出的 12 节机制摘要（原理索引，§9/10/11 为占位）
- `capture/findings\` — 抓取分析 10 份：01图表 02数据绑定 03地图GIS 04项目层 05弹窗 06模板 07交互 08hook 09pagecard 10页面级
- `probe/wk.mjs` — Bearer 直连客户端（读分析用）
