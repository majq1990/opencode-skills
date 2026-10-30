# 悟空3.0认证阅卷完整流程（通道⑥）

> 评分口径见 `grading_rules_wukong.md`；本文件是操作流程。
> 适用：悟空3.0考核（Moodle笔试 quiz256 + 悟空平台实操 + 钉钉阅卷分配表）

## 0. 前置

- 阅卷表节点：`ZX6GRezwJl7Dba5Kijdk17GPVdqbropQ`（钉钉 sheet）
  - 主表 `st-f0fdfb04-5317`；马健权 `st-245b4f16-8174`；郭跃增 `st-8cf690ec-68143`；陈马钦 `st-8cf690ec-68118`；考官4 `st-1c19b83a-95359`；考官5 `st-1c19b83a-95588`
- 悟空平台：http://8.130.127.28:8080/wukong/index.html（考生账号=拼音全名+工号，密码 eGova@123）
- dws CLI：`node C:\Users\majq1\AppData\Roaming\npm\node_modules\dingtalk-workspace-cli\bin\dws.js`
- **网络**：本机代理 127.0.0.1:18083 会掐断到考核服务器的连接。所有浏览器/脚本直连，`NO_PROXY=127.0.0.1,localhost` 并清空 HTTP(S)_PROXY

## 1. 浏览器环境（headless CDP，避免与用户浏览器争抢）

```bash
# 启动独立 headless Chrome（一次，后续复用）
"C:/Program Files/Google/Chrome/Application/chrome.exe" --headless=new \
  --remote-debugging-port=9333 \
  --user-data-dir="D:/opencode/file/<date>/chrome-profile-grading" \
  --no-first-run --no-default-browser-check --window-size=1920,1080 about:blank
```

脚本（`scripts/wukong/`）：
- `wukong-actions.mjs login <username>` — 登录考生账号
- `wukong-actions.mjs open <url>` / `shot <file>` / `evaljs <jsfile>`
- `byurl.mjs <url关键词> <shot|click|evaljs> <arg>` — **按 URL 定位标签页**（CDP 页面顺序跨连接不稳定，禁止用索引定位）
- `reload_layers.mjs <url关键词> <out.json>` — 刷新页面并抓 page-layer/list + layer-menu/tree/list 响应
- `pull_page_config.js` — 在页面内回放 page/detail 拿接口分类/过滤器/交互链

## 2. 单个考生阅卷步骤

### 2.1 登录 + 找项目/页面
1. `wukong-actions.mjs login <账号>`
2. 打开 `#/space/project`，读项目列表（可能有多个项目，都要看）
3. 点项目卡片眼睛图标前，拦截 `window.open` 拿 view URL（含 projectId/pageId），不真开新页

### 2.2 项目搭建 1.1-1.4（行4-7）
项目配置页 `#/create-project/basic|theme|map|nav?id=<projectId>` 逐 tab 读：
- 基础：项目名称/分辨率 1920*1080/页签Logo（有图片）
- 主题：当前主题是否为 v3.0单屏-副本
- 地图：GIS服务地址 + 地图配置名称
- 导航：树结构层级（智能视频必须两级）

### 2.3 城管秩序大屏（行8-26）
**查看模式**（`#/view?id=<pageId>&project=<projectId>`）：
1. 整体截图（2.1.1 风格、2.1.2 卡片标题、地图是否渲染）
2. 点高发类型 tab → 截图（2.1.3 高发类型、2.3.1）
3. 与模板大屏（pageId `4813ea09-82da-4c95-923b-ea19f21e3fc8`，在每个考生的"我的大屏"里）对比
4. 交互测试：
   - 2.3.2：点左下高发来源行（限定 y>650 区域）→ 看案件列表弹窗+下拉框
   - 2.3.3：点案件卡 → 详情弹窗
   - 2.3.4：全局时间改"今日"→ 看哪些卡片数据变化（高发来源变0=联动生效）
   - 2.3.5：**先关案件图层菜单 → 点处置数 → 图层出现；再关 → 点按期处置率 → 不出现**
   - 2.5.1：切 近7天 tab → 图表变化；再到编辑模式查传参配置

**配置核查**（`reload_layers.mjs` + `pull_page_config.js`）：
- page-layer/list：图层清单、各层 extractor（视频图层看 status 三目；案件图层看 id/x/y）、菜单树（监控图层 menuType、子层）
- page/detail 回放：接口分类（悟能/接口合并/自定义）、extractors（热词过滤、实时告警 id）
- interaction/chain：交互链清单（38条=模板预置；链存在≠生效，仍需行为验证）

**编辑模式**（`#/create?id=...`）：
- 选中模块 → 右侧「数据」页 → 接入方式（静态/动态）+ 接口分类 + 过滤器
- 2.5.1 传参：tab 组件参数名 vs 卡片接收参数名 + 字段传递开关
- 2.6.2：级联图层配置里是否有 区县/街道/社区/单元图层 ID；网格菜单子层绑定

### 2.4 智能视频专题（行27-39）
打开 `#/view?id=<智能视频pageId>`：
- 识别成效（指标数）/识别类型（类数）/时段分析（多指标折线+时间tab）/最新识别案件（字段+swiper）/设备总览（指标）/违规高发类型（排名+时间tab）/违规高发区域（排名）/监控抓拍（播放器?）/设备状态 tab 等隐藏 tab 要点开
- 地图：视频设备图层打点、在线离线分类、案件热力效果
- 图层配置：`reload_layers.mjs` 看 摄像头点位/热力图层

### 2.5 写表
`python scripts/wukong/write_scores.py <考生列起列> <rows.json>`
- 每人 3 列（扣分/说明/得分），行 4-39
- 写后回读第 3 行验证合计
- 格式：`[["扣分","说明"], ...]` 共 36 行

## 3. 汇报与红线

- 每个考生写完后回读验证合计并汇报：各项扣分 + 总分
- 与人工核对结果不一致时，按人工意见修订（人工为准）
- 阅卷表是多人共享文档，写前确认 sheet id 和列位置（考生顺序：张凯军/宋振君/谭金万/杨旭光/李臻哲/吴贺添）
