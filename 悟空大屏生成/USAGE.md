# 悟空大屏生成 skill — 使用说明

把 codesign / Figma 设计稿链接 → 还原成悟空（egova）数据大屏的完整流程说明。

适用：majianquan 账号 + Codex隔离测试 分组 + 工程/研发中心人员（wk-kg 白名单内）。

---

## 一、首次环境准备（每台机器只做一次）

### 1.1 装 codesign-mcp（读 CoDesign 设计稿）

```bash
npm install -g codesign-mcp
```

加进 Claude Code 配置（**user scope，全局**）：

```bash
claude mcp add-json codesign -s user '{"type":"stdio","command":"cmd","args":["/c","node","C:/Users/majq1/AppData/Roaming/npm/node_modules/codesign-mcp/dist/index.js"],"env":{}}'
```

> ⚠️ 路径用**正斜杠**（`C:/Users/...`）。用 `claude mcp add ... -- cmd /c node` 会把 `/c` 转成 `C:/` 连不上，必须用 `add-json`。

**Chrome 补丁**（codesign-mcp 默认用 playwright 自带 chromium v1223，GFW 卡死下载）：
编辑 `C:/Users/majq1/AppData/Roaming/npm/node_modules/codesign-mcp/dist/browser/manager.js`，在 `launchPersistentContext` 选项里加 `channel: 'chrome'`，用系统 Chrome。

```js
const ctx = await chromium.launchPersistentContext(config.profileDir, {
  headless: mode === 'headless',
  channel: 'chrome',                  // ← 加这一行
  viewport: { width: 1440, height: 900 },
  args: ['--disable-blink-features=AutomationControlled'],
});
```

⚠️ 这是 node_modules 补丁，重装 codesign-mcp 会丢，要重打。

### 1.2 挂 wk-kg（组件知识图谱 MCP）

浏览器走 OAuth：

1. 打开 https://gczx.egova.com.cn/wk-kg/oauth/dingtalk/login
2. 钉钉扫码（白名单 = 工程技术中心 + 研发中心，自动通过）
3. 拿到 90 天 Bearer token
4. 加进 Claude Code（**user scope**）：

```bash
claude mcp add --transport http wk-kg https://gczx.egova.com.cn/wk-kg-mcp/ -s user \
  -H "Authorization: Bearer <你的token>"
```

验证：
```bash
claude mcp get wk-kg   # 应显示 ✔ Connected
```

> ⚠️ token 90 天过期。看到 `Failed to connect` → 浏览器重新走一遍 OAuth 拿新 token → `claude mcp remove wk-kg -s user` 再 `add` 一次。

### 1.3 配悟空账号（落地大屏用 majianquan）

```bash
mkdir -p ~/.wukong-cli
cat > ~/.wukong-cli/credentials.json <<EOF
{
  "username": "majianquan",
  "password": "<你的悟空密码>"
}
EOF
chmod 600 ~/.wukong-cli/credentials.json
```

装 sm-crypto（悟空 SM2 加密登录依赖）：

```bash
cd "D:/git/opencode-skills/悟空大屏生成/scripts"   # junction 真实路径
npm install sm-crypto
```

> ⚠️ 本机 `~/.claude/skills/悟空大屏生成/` 是 junction → `D:/git/opencode-skills/悟空大屏生成`。必须在**真实路径**下装 npm 包，否则 wk-login.mjs 找不到。

测试：
```bash
node "D:/git/opencode-skills/悟空大屏生成/scripts/wk-login.mjs" --print
# 应返回一个长 token 字符串
```

### 1.4 启动会话时
- 在 Claude Code 里直接说**「拉这个设计图 https://codesign.qq.com/s/xxx 还原成悟空大屏」**
- 我会按下面的流程自动跑

---

## 二、完整工作流（每张大屏一次）

### 阶段 1：读设计稿 → 区块清单

| 步 | 动作 | 输入/输出 |
|---|---|---|
| 1.1 | 用户给链接（codesign / figma） | `https://codesign.qq.com/s/xxx` |
| 1.2 | 按域名路由 MCP（codesign / figma） | 自动 |
| 1.3 | `list_artboards(url, password)` | 12 画板列表 |
| 1.4 | **用户选画板**（不擅自决定）| 选 screenId |
| 1.5 | `get_artboard_spec(screenId, password)` | **会超 token 限制，自动存盘** `.claude/projects/.../tool-results/*.txt` |
| 1.6 | 本地解析 `codesign_spec_to_blocks.py <spec文件> 输出.json --min-area=12000` | 区块清单 JSON |

```bash
python "D:/git/opencode-skills/悟空大屏生成/scripts/codesign_spec_to_blocks.py" \
  "<.txt路径>" "<输出.json>" --min-area=12000
```

输出每块：`name / rect(x/y/w/h) / 内含文字 / 颜色字号`。

### 阶段 2：wk-kg 推荐组件 → 用户逐块确认（🚧 硬门控）

| 步 | 动作 |
|---|---|
| 2.1 | 抽每块自然语言描述（"5项KPI翻牌"/"排名表"/"5项气泡"）|
| 2.2 | 逐块调 `recommend_components(visual_description, limit:4)` |
| 2.3 | 整理成确认表 → **用户对每块点头/换/跳过** |
| 2.4 | 取 schema：每个已确认组件 → `get_component_schema(component_id)` 拿 cardDataSchema |
| 2.5 | 取 libCardId：`POST unity/card/list` 一次拉全组件库（5819 个）→ 按 base.code 匹配真实 UUID |

> ⚠️ 描述自然语言，不要"块N 区域 文字Y"机械化，KG 召不准。
> ⚠️ wk-kg 直调 HTTP（curl/requests）必须 **UTF-8 编码**，Git Bash 直发会乱码。Python 用 requests 必须 `data=json.dumps(...,ensure_ascii=False).encode('utf-8')`。SSE 响应按字节解析，不要 r.text。

### 阶段 3：生成 ScreenSpec → POST 创建 → PUT 写真实内容

**核心铁律：POST 只是创建空壳，PUT 才是写真实内容。**

| 步 | 端点 | 作用 | body 关键 |
|---|---|---|---|
| 3.1 | `POST unity/page` | 新建空壳 | `{id, name, kind:"PAGE", groupId, width, height, type:"PAGE", status:"UNRELEASED"}` ⚠️ 不要传 `shareType` |
| 3.2 | `POST unity/page-card` ×N | 创建空壳 card | `{cardId:<libCardId>, pageId, type:"DATA"}` 其余字段会被忽略 |
| 3.3 | `POST unity/card-data` ×M | 创建空壳数据 | `{type:"StaticData"}` ⚠️ 不要传 `"API"` |
| 3.4 | `POST unity/page-card/batch-modify` | 绑 dataId | **body 是裸数组** `[{id, dataId}, ...]` 不是 `{records:[...]}` |
| 3.5 | `PUT unity/page-card/{realId}` ×N | **改坐标尺寸名字** | `{id, name, x, y, width, height, level}` |
| 3.6 | `PUT unity/card-data` | **改真实数据**（⚠️ 无 id 后缀）| 必须 GET 完整 card-data → 改 cardData 字段 → 整体 PUT 回去 |
| 3.7 | `PUT unity/page-card/{realId}` ×N | **改样式** | `{id, style}` style 从 GET 来改局部字段 |

⚠️ **POST 返回的 result 才是真实 id**，不是我们 body 里传的 id。所以要从 `send_results` 里拿 `resultId.id` 做后续 PUT。

⚠️ **POST 看似 hasError=false 不代表数据写进去了**。必须 GET 回来验证字段值。

### 阶段 4：样式还原（结构 + 字体 + 颜色）

**结构是底层**（错了再美也是默认 demo 数据），先修：

| 组件 | 关键字段 |
|---|---|
| BaseData2 KPI | `prop.bgShow=false` 关默认背景 |
| BasicInfo14 气泡 | `itemStyle.sliderNum=N` 显示数量 |
| SeniorBall 排行 | `slides.isLoop=false` 关轮播 + `slides.row=1 column=5` |
| IndexStatistic 进度 | `row.number=N column.number=1` |
| Swiper11 表格 | `style.styleTab.value=[{field,title,width,align,color,fontSize},...]` **必须配列定义，否则表格塌掉** |
| Tabs1 | 字体在 `selectStyle / unSelectStyle` 段 |

**字体颜色字号**（从 codesign 抽 → 映射悟空字段）：

| 悟空字段位置 | codesign 字段 |
|---|---|
| `text.fontFamily/fontWeight/fontSize/color` | text 层 `fontFace / fontWeight / fontSize / color.color-hex` |
| `value.fontFamily/...` | text 层（数值） |
| `unit.fontFamily/...` | text 层（单位） |

⚠️ 悟空字号是 **w-select 下拉枚举** `[12,14,16,18,20,22,24,26,28,30,32,36,40,48,56,72]`。codesign 12.6 等小数要 snap 到最近允许值。

### 阶段 5：自验证（视觉对比）

打开预览：`http://wk.egova.com.cn:8042/wukong/index.html#/view?id={pageId}`

或上传目标图到 https://gczx.egova.com.cn/screen-review/ 自动跑 Qwen3-VL 视觉对比，出"目标 vs 复刻"逐块报告 + 还原度%。

---

## 三、关键产物文件位置（每张大屏都生成）

| 文件 | 内容 |
|---|---|
| `wukong-recon/<screen>_blocks.json` | codesign 区块清单 |
| `wukong-recon/<screen>_recommend.json` | wk-kg 推荐结果 + 用户确认 |
| `wukong-recon/<screen>_schemas.json` | 11 组件 schema |
| `wukong-recon/<screen>_screenspec.json` | 最终 ScreenSpec |
| `wukong-recon/<screen>_dryrun_v2.json` | dryRun 33 条请求序列 |
| `wukong-recon/<screen>_send_results.json` | POST 真实返回（含真实 id 映射） |

---

## 四、踩过的坑清单（按优先级）

### 🔴 必须知道（不知道就废）

| 坑 | 表现 | 修法 |
|---|---|---|
| POST 只创建空壳 | 截图所有组件挤左上 / 全是 demo 数据 | PUT 改坐标 / GET+PUT 改 cardData |
| PUT card-data 无 id 后缀 | PUT 报 404 / DB 异常 | endpoint = `PUT unity/card-data` 不是 `/card-data/{id}` |
| 字段是 dict 不是 string | `color.color-hex` 不是 `color` | 取 `color['color-hex'].split()[0]` |
| 中文 UTF-8 编码 | curl/Git Bash 直发钉钉/MCP 乱码 | 强制 `ensure_ascii=False .encode('utf-8')` |
| Swiper11 styleTab 必须配列 | 表格完全塌掉只剩一行字 | `styleTab.value=[{field:'field1',title:'部门',...},...]` |

### 🟡 容易栽

| 坑 | 表现 |
|---|---|
| 服务端枚举不接受 | `shareType:"PRIVATE"` / `type:"NORMAL"` / `card-data.type:"API"` 都报错 → 用 `null / "PAGE" / "StaticData"` |
| batch-modify body 是裸数组 | `{records:[...]}` 报 JSON parse error → 直接传数组 |
| chromium v1223 下不动 | GFW 卡死 → channel:'chrome' 用系统 Chrome |
| skills 目录 npm 装错路径 | wk-login 找不到 sm-crypto → 必须在 `D:/git/opencode-skills/...` 真实路径装 |
| token 过期 | wk-kg `Failed to connect` → 重走 OAuth + 重新 `claude mcp add` |
| 组件默认 row/column 是 1 | 5 条数据只显示 1 个 | 手动设 `slides.row/column` 或 `row.number / column.number` |
| 组件默认 isLoop=true | 5 项轮播只显示一个 | `slides.isLoop=false` |

### 🟢 设计/约定

- **地图区按用户约定默认空着**，跳过不配
- **门控**：用户给设计图必须先视觉拆分 → 逐块确认 → 才能进搭建
- **写操作**：dryRun 默认开，真发前用户必须确认
- **隔离分组**：默认落 `Codex隔离测试`（296776df-545f-4ff9-94a6-e068d6c7af31），不污染生产

---

## 五、常用资源

| 资源 | 位置 |
|---|---|
| wk-kg-mcp 端点 | https://gczx.egova.com.cn/wk-kg-mcp/ |
| wk-kg OAuth 入口 | https://gczx.egova.com.cn/wk-kg/oauth/dingtalk/login |
| 悟空后端 | http://wk.egova.com.cn:8042/wukong-backend/ |
| 悟空编辑页 | `http://wk.egova.com.cn:8042/wukong/index.html#/create?id={pageId}` |
| 悟空预览 | `http://wk.egova.com.cn:8042/wukong/index.html#/view?id={pageId}` |
| 视觉对比工具 | https://gczx.egova.com.cn/screen-review/ |
| Codex隔离测试 groupId | `296776df-545f-4ff9-94a6-e068d6c7af31` |
| 悟空签名 ak | `ad13dec6216acac85e91562821bf8dda` |

---

## 六、快速排查

| 症状 | 看哪 |
|---|---|
| MCP 不显示工具 | `claude mcp get <name>` 看 status；重启 Claude Code |
| codesign 弹不出浏览器 | manager.js channel:'chrome' 补丁有没有打 |
| codesign 拉不到稿 | `codesign_status` 看 profile.exists，没登录就 `codesign_login` |
| wk-kg recommend 召不准 | 改自然语言描述（"5项排名带百分比" 比 "块N 区域 文字Y" 好） |
| 大屏组件挤一团 | 没做 PUT 修坐标，重跑 PUT page-card |
| 大屏全是 demo 数据 | 没做 PUT 修 cardData，重跑 GET+PUT card-data |
| 表格塌掉 | Swiper11 styleTab 没配列 |
| 5 项数据只显示 1 | row/column 是默认 1×1，要改 |
| 截图字号颜色不对 | 各组件字体段名不同（BasicText1 在 text 段、BaseData2 在 text/value/unit 段、SeniorBall 在 style.textfontFamily），看 `tab1_schemas.json` |
