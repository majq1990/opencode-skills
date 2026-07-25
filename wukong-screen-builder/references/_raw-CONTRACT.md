# 悟空大屏配置契约（逆向结论）

侦察样本：页面 `4.1 综合考评-部门评价`，id=`6ad6d3e2-da22-471a-ad3d-c6c35dc2ac32`，1920×1080，32 个组件。
后端基址：`http://wk.egova.com.cn:8042/wukong-backend/unity/`
鉴权：会话 Cookie（JSESSIONID + token）+ 每请求 HMAC 签名（query 的 signature/timestamp/nonce，前端计算）。

## 一、整页定义就是 page-detail（自包含，疑似导入/导出载荷）

`page/detail/{pageId}` 返回的 `result` 是**完整自包含**的整页定义：

```
result = {
  id, name, type=PAGE, kind=PAGE,
  width:1920, height:1080,
  groupId,                       # 所属分组
  styleConfigId / mapConfigId / linesConfigId,   # 三个外链配置 id
  style: [ ...12 项页面级样式表单 ... ],          # 画布/页面级样式（表单 schema 形态）
  lines: {...}, map: null,
  pageCards: [ 32 个组件，每个内联 data/style/interaction ]   # ← 关键：内联，不再外链
}
```

> 对比 `page-card/level-tree/{pageId}`：那里 card 的 data/interaction 是用 `dataId` **外链**的；
> 而 `page/detail` 里 pageCards 把 data/style/interaction **内联**了 → page-detail 是落地用的完整载荷。

## 二、单个 pageCard（组件）结构

```
card = {
  id, name, type,
  base: {...},          # 组件模板定义（身份）：核心是 base.code
  style: { base:{...}, configuration:[...] },   # 外观（表单 schema 列表）
  data: {...},          # 数据绑定层（见下，= 现有 skill 的产出域）
  interaction: ...,     # 单组件交互
  interactionList: [...],
  scripts: ...,         # 组件级脚本
  x, y, width, height,  # 几何（绝对坐标，本页全部 parentId=None，扁平布局）
  parentId, children, level, grade, totalGrade,
  beHidden, beLocked, beGroup
}
```

### 组件身份 = base.code
本页用到的组件库 code（categoryName / code）：
- 下拉菜单 `Cascader1` `Select1`，时间选择器 `Datepick`，时间组件 `Time`
- 轮播列表 `Swiper11` `Swiper1`，平铺展示 `BasicInfo3`，选项卡 `Tabs1`，分页 `Pagination`
- 文本 `BasicText2`，卡片标题 `Title5`，形状 `Icon`，图片 `BasicImg`

### style.configuration = 属性编辑器的持久化表单
列表，每项 `{name, displayName, warp, config, value:[{name,displayName,value,type,config}...]}`。
`type` 如 `w-input`，`config.readonly` 等 —— 即右侧属性面板的可编辑项快照。

### data = 数据绑定层（★ 现有 egova-screen-data-connector 的产出正好填这里）
```
data = {
  type,                  # StaticData / 接口类型
  proxy,                 # 是否走代理
  request,               # 接口调用定义（URL/方法/参数）
  extractor, extractorEnable,        # ES5 filter(data) 过滤脚本
  paramFilter, paramFilterEnable,    # 入参过滤
  dataMapping, dataMappingEnable,    # 字段映射
  refreshInterval, refreshEnable, timeoutTime,  # 刷新
  cardData,              # 静态数据数组
  testRunConfig, beControlled
}
```
→ 现有 skill 输出的「数据源 + 字段映射 + function filter(data)」恰好对应 `request`/`dataMapping`/`extractor`。

## 三、页面级脚本/Webhook = page-hook
`page-hook/...` 的 `result`：
```
{ id, pageId, type, preScript, afterScript, globalScript, globalScriptJson, ... }
```
- `preScript` = `function hook(wk){...}`：页面加载前钩子（样本里从 sessionStorage 取 regionId/regionCode 注入 globalPara）
- `afterScript` / `globalScript` / `globalScriptJson`：全局脚本层（「写脚本」能力）

## 四、落地通道判定
- **通道 A（API 导入/保存）= 首选且高度可行**：page-detail 已是自包含 JSON；编辑器有「导入」按钮。
  - 待确认：保存 POST 端点 + 导入端点的确切路径与签名要求（Phase 1 第一步验证）。
- 通道 B（直写 DB/文件）：备选，风险高。
- 通道 C（playwright 拖拽）：兜底，脆弱。

## 五、对「一句话出大屏」的分层映射
| 层 | 内容 | 现状 |
|----|------|------|
| 布局/选型 | 从组件库选 base.code + x/y/w/h + 填 style.configuration | **待建** |
| 数据绑定 | 每个 card.data（request/extractor/dataMapping/refresh） | **已有 skill** |
| 交互/脚本 | card.interaction(List) + page preScript/globalScript | **待建** |
| 落地 | 组装 page-detail JSON → POST 保存/导入端点 | **待验证端点** |
