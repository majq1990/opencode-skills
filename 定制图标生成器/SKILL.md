---
name: 定制图标生成器
description: 定制图标生成器。This skill should be used when the user wants to generate SVG icons. Triggers on requests like "生成图标", "图标", "定制图标", "create icon", "粘贴SVG", "导入SVG", "paste SVG", or any icon generation tasks. Supports iconfont integration, custom SVG paste/import, color customization (solid + gradient + custom), background layer, corner radius, and SVG/PNG download.
---

# SVG图标生成器

## Overview

单流程生成可商用纯矢量 SVG 图标。**只需输入图标名称**，即可生成预览页面，支持纯色（11色）+ 渐变色（10色 + 自定义配色）、背景层（10色渐变 + 圆角）、4种尺寸、粘贴SVG/复制SVG/下载SVG/下载PNG。

支持两种图标来源：
- 📦 **iconfont 图标库**：阿里 iconfont，3个 JS 库共 1086 个图标
- 📋 **粘贴SVG代码**：导入任意 SVG 代码，自动解析渲染
- ✏️ **自定义绘制**：根据关键词生成矢量 SVG path

---

## Unified Flow — 统一生成流程 {#unified-flow}

触发技能后，只需一步即可生成预览：

---

### Step 1：输入图标名称

**引导语：**
> 请输入图标名称（如：路灯、巡检、购物车、设置）
> 输入「列表」查看全部 1086 个图标

**处理逻辑：**

1. **匹配成功** → 直接生成预览页面

2. **未找到匹配** → 提示用户选择：
   > 😕 未找到「{关键词}」图标
   >
   > 请选择：
   > - 输入「列表」查看全部 1086 个图标
   > - 输入其他图标名称重新搜索
   > - 或描述图标样式，我来尝试绘制

3. **用户输入「列表」** → 展示图标库分类列表

4. **用户描述样式** → 尝试用 AI 生成自定义 SVG

> ⚠️ 若用户未提供名称，禁止执行生成

---

### ✅ 生成 → 预览

**生成完成后：**
> ✅ 生成完成！预览页面已打开。
>
> 在预览页面可自由切换：
> - 🖌️ **颜色**：纯色（11色）+ 渐变色（10色）+ 自定义配色
> - 📐 **尺寸**：无背景 24/32/48/64，有背景 48/64/96/128
> - 🔲 **背景层**：10色渐变 + 圆角（1px~100px）
> - ⬇️ **下载**：粘贴SVG代码、复制SVG、下载SVG、下载PNG

---

## 配色方案

### 图标层 — 纯色（11色，上排）

| 序号 | 颜色 | 色值 |
|:----:|:----:|------|
| 1 | 白色 | #ffffff |
| 2 | 绿色 | #3FBF00 |
| 3 | 青色 | #11C79B |
| 4 | 浅蓝 | #33BBFF |
| 5 | 蓝色 | #3388FF |
| 6 | 蓝紫 | #4433FF |
| 7 | 紫色 | #AA33FF |
| 8 | 粉色 | #FF33DD |
| 9 | 红色 | #FF4433 |
| 10 | 橙色 | #FF6600 |
| 11 | 黄色 | #FFAA00 |

### 图标层 — 渐变色（10色，下排，方向从上到下）

| 序号 | 颜色 | 色值 |
|:----:|:----:|------|
| 1 | 绿色 | #28EB78 → #28CD78 |
| 2 | 青色 | #00CD91 → #00AF91 |
| 3 | 浅蓝 | #00E6F0 → #00C8F0 |
| 4 | 蓝色 | #00C8F0 → #0091FA |
| 5 | 蓝紫 | #0091FA → #505FDC |
| 6 | 紫色 | #917DFF → #505FDC |
| 7 | 粉色 | #FF69AF → #FF4BAF |
| 8 | 红色 | #FF5023 → #E62314 |
| 9 | 橙色 | #FF9623 → #FF5023 |
| 10 | 黄色 | #FFEB23 → #FF9623 |

### 背景层 — 渐变色（10色，与图标层渐变色一致）

色值与图标层渐变色完全相同。

### 自定义渐变配色

渐变色色板右侧有"自定义配色"按钮，点击展开配置面板：
- **方向下拉框**：从上到下、从左到右、从左上到右下、从右上到左下
- **起始色值** 和 **结束色值** 输入框（6位16进制）
- 每个输入框旁有**色板按钮**，点击弹出 HSV 色板选择器（SV面板 + 色相条 + HEX输入）

---

## 界面结构

### 布局分区
- **图标颜色区域**（`.color-section`）：独立区块，边框 + 底色包裹
  - "图标颜色"标题：13px, #ffffff, 加粗
  - 纯色排：标签"纯色"（12px, 48px宽）+ 11个色板
  - 渐变色排（距上方10px）：标签"渐变色"（12px, 48px宽）+ 10个色板 + "自定义配色"按钮
- **背景层区域**（`.bg-layer-section`）：独立区块，边框 + 底色包裹，max-width 600px
  - "背景层"标题 + 开关按钮
  - "背景颜色"标签（12px, #8888aa, 不加粗）+ 10个渐变色板（同一行）
  - "圆角"标签 + 滑块（1px~100px，默认16px）
- **尺寸切换**：4个按钮
- **预览区域**：棋盘格透明背景
- **操作按钮**：粘贴SVG代码、复制SVG、下载SVG、下载PNG

### 按钮样式
| 按钮 | 背景色 | 边框 | 文字颜色 |
|------|--------|------|----------|
| 粘贴SVG代码 | rgba(255,152,35,0.4) | 1px solid #FF9823 | #ffffff |
| 复制SVG | rgba(35,199,155,0.4) | 1px solid #23C79B | #ffffff |
| 下载SVG | rgba(55,187,255,0.4) | 1px solid #37BBFF | #ffffff |
| 下载PNG | rgba(52,136,255,0.4) | 1px solid #3488FF | #ffffff |

---

## 尺寸体系

| 模式 | 可选尺寸 |
|------|----------|
| 无背景 | 24×24, 32×32, 48×48, 64×64 |
| 有背景 | 48×48, 64×64, 96×96, 128×128 |

开启背景层时自动切换到有背景尺寸，关闭时切换回无背景尺寸。

---

## 背景层

- **渐变色**：10种预设渐变色，与图标层渐变色一致
- **圆角**：像素控制，范围 1px~100px（默认16px）
- **预览**：背景层和图标层是两个独立 SVG，用 position:absolute 叠加
- **下载**：背景层 rect 的 rx 直接使用 px 值（`bgRadius`）

---

## Preview Page — 预览页面 {#preview-page}

预览页面固定为 `svg-icon-generator/icon-preview.html`，不再为每个图标新建页面。

### 切换图标时需要修改的内容

1. `targetSymbolId` 变量 — 图标 ID
2. 页面标题 `<title>` — 图标名称
3. `<h1>` — 图标名称
4. `header p` — 分类描述
5. `footer` 文字 — 图标名称
6. 下载文件名前缀（两处 `var prefix`）— 图标名称

### 关键技术实现

- **iconfont 数据获取**：通过 `fetchSymbolPaths()` 从 3 个 iconfont JS 库中按 `targetSymbolId` 查找
- **viewBox 计算**：用浏览器 `getBBox()` 精确计算图标 bounds，自动生成正方形 viewBox
- **SVG 渲染**：预览时用 DOM API 创建 `<path>` 元素，下载时用字符串拼接构建完整 SVG
- **自定义绘制回退**：iconfont 未找到时可用自定义 SVG path 数组作为备选
- **粘贴SVG代码**：通过 `pasteSvgCode()` → `parseAndLoadSvg()` 导入外部 SVG
  - 优先使用 `navigator.clipboard.readText()` 自动读取剪贴板
  - 若权限受限，弹出模态框让用户手动粘贴（textarea + 确定/关闭）
  - 使用 `DOMParser` 解析 SVG，提取 `<path>` 元素的 `d` 属性
  - 若无 `<path>`，自动将 `<rect>`、`<circle>`、`<ellipse>`、`<line>`、`<polygon>` 转为 path 数据
  - 加载后切换为 `customPaths` 模式，完全支持后续的调色、背景层、尺寸、下载等所有功能

---

## Generation Rules — 生成规则 {#generation-rules}

1. **纯矢量路径**：所有 SVG 必须为纯矢量，禁止嵌入位图，无限放大无损
2. **版权合规**：所有图标默认可商用，禁止生成侵权、违规内容
3. **代码精简**：清理无效属性，压缩体积，可直接用于生产环境
4. **背景透明**：无背景模式下图标背景统一透明
5. **色值互斥**：纯色和渐变色选中互斥，选纯色清除渐变 active，反之亦然

---

## Error Handling — 异常处理 {#error-handling}

| 异常场景 | 处理方式 |
|----------|----------|
| 用户未输入名称 | 提示输入，列出示例 |
| iconfont 未找到匹配 | 展示相关图标列表，或切换自定义绘制 |
| 颜色格式错误 | 自动识别 HEX 格式，提示正确格式 |
| 生成失败 | 自动重试 1 次，仍失败则说明原因 |
| 用户中途调整 | 保留已填参数，重新生成预览页面 |

---

## Iconfont — iconfont 图标库 {#iconfont}

### 已配置图标库

- **JS 地址**：
  - `//at.alicdn.com/t/c/font_5064679_wfkhie1dn2.js`
  - `//at.alicdn.com/t/c/font_3632408_jfq3j1asgn.js`
  - `//at.alicdn.com/t/c/font_3563889_jj7d0vj2cg.js`
- **图标数量**：1086 个（icon- 912 个 + zt-icon- 129 个 + icon- 45 个公共）
- **主题**：智慧城市、市政管理、通用 UI
- **SVG 处理**：从 JS 文件提取 SVG paths，内联到预览页面，不依赖外链

### 图标列表（icon- 912 个，zt-icon- 129 个，共 1086 个）

---

<!-- TOTAL: 912 icon- icons -->

#### 🏙️ 城市设施（67 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-a-12319rexianchaxun` | 12319热线查询 |
| `icon-a-12345` | 12345热线 |
| `icon-a-123451` | 12345热线（变体） |
| `icon-a-96301` | 96301 |
| `icon-biaoshibiaopai` | 标识标牌 |
| `icon-chengshigongce` | 城市公厕 |
| `icon-chengshigongyuan` | 城市公园 |
| `icon-chengshigongyuan-1` | 城市公园（变体） |
| `icon-chengshigongyuan1` | 城市公园（变体2） |
| `icon-chengshiyunhangpingjia` | 城市运行评价 |
| `icon-chengshiyunhangtaishizhuping` | 城市运行态势主屏 |
| `icon-danche` | 单车 |
| `icon-danchehuoyueliang` | 单车活跃量 |
| `icon-daping` | 大屏 |
| `icon-ditu` | 地图 |
| `icon-ditu1` | 地图（变体） |
| `icon-dituliulan` | 地图浏览 |
| `icon-gongcesheshiwenti` | gongcesheshiwenti |
| `icon-gongceweishengwenti` | gongceweishengwenti |
| `icon-gonggongjianzhu` | 公共建筑 |
| `icon-gongxiangdanche` | 共享单车 |
| `icon-gongxiangdanchetingfangwuxu` | 共享单车停放无序 |
| `icon-gongyuanjingdian` | 公园景点 |
| `icon-guanggaopaibian` | 广告牌匾 |
| `icon-guojiachengshiyunhangguanlifuwupingtai` | 国家城市运行管理服务平台 |
| `icon-haodianpu` | 好店铺 |
| `icon-huanweidaping` | 环卫大屏 |
| `icon-huwaiguanggao` | 户外广告 |
| `icon-huwaiguanggao1` | 户外广告（变体） |
| `icon-huwaiguanggaosheshiguanlixitong` | 户外广告设施管理系统 |
| `icon-huwaiguanggaoshiminfuwu` | 户外广告市民服务 |
| `icon-lucetingchechaxun` | 路侧停车查询 |
| `icon-ludengguanli` | 路灯管理 |
| `icon-menqiansanbao` | 门前三包 |
| `icon-menqianwubao` | 门前五包 |
| `icon-mentoudianzhaoshenpi` | 门头电子招牌审批 |
| `icon-shangpuguanli` | 商铺管理 |
| `icon-shanxichengshiyunhangguanlifuwupingtai` | 陕西城市运行管理服务平台 |
| `icon-shichangzhutiguanlichengxinxitong` | 市场主体管理诚信系统 |
| `icon-shizhengdaping` | 市政大屏 |
| `icon-shizhenggongcheng` | 市政工程 |
| `icon-shouye` | 首页 |
| `icon-shuziyuanlin` | 数字园林 |
| `icon-tingchechangchaxun` | 停车场查询 |
| `icon-tingchedianwei` | 停车点位 |
| `icon-tingcheguanli` | 停车管理 |
| `icon-wentiguanggaojilu` | 问题广告记录 |
| `icon-yituzhaoche` | 一键找车 |
| `icon-yuanlindaping` | 园林大屏 |
| `icon-yuanlinfenxi` | 园林分析 |
| `icon-yuanlingaikuang` | 园林概况 |
| `icon-yuanlingailan` | 园林护栏 |
| `icon-yuanlinlvhua` | 园林绿化 |
| `icon-yuanlinlvhua-1` | 园林绿化（变体） |
| `icon-yuanlinlvhua1` | 园林绿化（变体2） |
| `icon-yuanlinsheshi` | 园林设施 |
| `icon-yuanlinsheshi1` | 园林设施（变体） |
| `icon-zhaogongce-copy` | 找公厕 |
| `icon-zhaopaiguanli` | 拍照管理 |
| `icon-zhendigongxiang` | 阵地共享 |
| `icon-zhifadaping` | 执法大屏 |
| `icon-zhihuigongce` | 智慧公厕 |
| `icon-zhihuigongce1` | 智慧公厕（变体） |
| `icon-zhihuitingche` | 智慧停车 |
| `icon-zhihuiyuanlin` | 智慧园林 |
| `icon-zhihuiyuanlin1` | 智慧园林（变体） |
| `icon-zhihuizhaoming` | 智慧照明 |

#### 🏗️ 基础设施（147 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-TDOAtanceshebei` | TDOA探测设备 |
| `icon-bangongrenwu` | 办公任务 |
| `icon-chaoxijiance` | 潮汐监测 |
| `icon-chengshidaolubujie` | 城市道路不洁 |
| `icon-chengshiqiaoliang` | 城市桥梁 |
| `icon-chengshizhaomingguanlixitong` | 城市照明管理系统 |
| `icon-chengxiangranqi` | 城乡燃气 |
| `icon-danweimianjidianhao` | 单位面积电号 |
| `icon-danweimianjirehao` | 单位面积热号 |
| `icon-danweimianjishuihao` | 单位面积水号 |
| `icon-daolu` | 道路 |
| `icon-daoluchangdu` | 道路长度 |
| `icon-daolujishui` | 道路积水 |
| `icon-daoluposun` | 道路破损 |
| `icon-daoluwajue` | 道路挖掘 |
| `icon-daoluwajueshenpi` | 道路挖掘审批 |
| `icon-daoluweihu` | 道路维护 |
| `icon-daoluxuncha` | 道路巡查 |
| `icon-daoluxuncha1` | 道路巡查（变体） |
| `icon-daoqiaoguanlixitong` | 道桥管理系统 |
| `icon-daoqiaoyizhangtu` | 道桥一账图 |
| `icon-diaota` | 吊塔 |
| `icon-dikongsheshi` | 低空设施 |
| `icon-dikongshifeiquyu` | 低空施飞区域 |
| `icon-dixiaguanlang` | 地下管廊 |
| `icon-dixiaguanxian` | 地下管线 |
| `icon-ganzhishebei` | 感知设备 |
| `icon-gaojing` | 告警 |
| `icon-gaojing1` | 告警（变体） |
| `icon-gaopindaolu` | 高频道路 |
| `icon-gaopinkakou` | 高频卡口 |
| `icon-gongchengxiaofangshenyanguanli` | 工程消防审验管理 |
| `icon-gongdianguanwang` | 供电管网 |
| `icon-gongqiguanwang` | 供气管网 |
| `icon-gongre` | 供热 |
| `icon-gongreguan` | 供热管 |
| `icon-gongrejiandu` | 供热监督 |
| `icon-gongrejianguan` | 供热监管 |
| `icon-gongremianji` | 供热面积 |
| `icon-gongreyizhangtu` | 供热一账图 |
| `icon-gongrezhuanjia` | 供热专家 |
| `icon-gongshui` | 供水 |
| `icon-gongshuijianguan` | 供水监管 |
| `icon-gongshuixitong` | 供水系统 |
| `icon-gongshuiyizhangtu` | 供水一账图 |
| `icon-guanlangfenqushu` | 管廊分区数 |
| `icon-guanlangjianguan` | 管廊监管 |
| `icon-guanlangshu` | 管廊数 |
| `icon-guanlangyizhangtu` | 管廊一账图 |
| `icon-guanlangzongchangdu` | 管廊总长度 |
| `icon-guanwangyewei` | 管网液位 |
| `icon-guanxian` | 管线 |
| `icon-guanxianfenxi` | 管线分析 |
| `icon-huanrezhan` | 换热站 |
| `icon-huojingshibie` | 火警识别 |
| `icon-jianceshebei` | 监测设备 |
| `icon-jiasuduji` | 加速度计 |
| `icon-jiezhen` | 介振 |
| `icon-jinggai` | 井盖 |
| `icon-jinggaiposun` | 井盖破损 |
| `icon-jinggaiqueshi` | 井盖缺失 |
| `icon-liefengji` | 裂缝计 |
| `icon-liuliang` | 流量 |
| `icon-liuliangji` | 流量计 |
| `icon-nongdujiance` | 浓度监测 |
| `icon-nongdujiance1` | 浓度监测（变体） |
| `icon-paishuihu` | 排水户 |
| `icon-paishuihu-1` | 排水户（变体） |
| `icon-paishuijianguan` | 排水监管 |
| `icon-paishuixitong` | 排水系统 |
| `icon-paishuiyinhuan` | 排水隐患 |
| `icon-paishuiyizhangtu` | 排水一账图 |
| `icon-paishuizhuanxiangzixitong` | 排水转项自系统 |
| `icon-qiaoliang` | 桥梁 |
| `icon-qiaoliangsheshiwenti` | qiaoliangsheshiwenti |
| `icon-qiaoliangzhuanxiangzixitong` | 桥梁转项自系统 |
| `icon-qitijiance` | 气体检测 |
| `icon-qixiangyujing` | 气象预警 |
| `icon-qixiangzhan` | 气象站 |
| `icon-ranqi` | 燃气 |
| `icon-ranqi1` | 燃气（变体） |
| `icon-ranqiguanli` | 燃气管理 |
| `icon-ranqiguanlibeifen` | ranqiguanlibeifen |
| `icon-ranqiguanwang` | 燃气管网 |
| `icon-ranqijianguan` | 燃气监管 |
| `icon-ranqijianguan1` | 燃气监管（变体） |
| `icon-ranqiping` | 燃气瓶 |
| `icon-ranqiqiye` | 燃气企业 |
| `icon-ranqirelishiwushujuguanlixitong` | 燃气热力事务数据管理系统 |
| `icon-ranqisheshi` | 燃气设施 |
| `icon-ranqiyizhangtu` | 燃气一账图 |
| `icon-ranqizhuanxiangzixitong` | 燃气转项自系统 |
| `icon-religuanwang` | 热力管网 |
| `icon-relitu` | 热力图 |
| `icon-relizhuanxiangzixitong` | 热力转项自系统 |
| `icon-rongqimanyi` | 容器满意 |
| `icon-rongqiposun` | 容器破损 |
| `icon-shebei` | 设备 |
| `icon-shebeigengxin` | 设备更新 |
| `icon-shebeilixian` | 设备离线 |
| `icon-shebeizongshu` | 设备总数 |
| `icon-shigongrenyuan` | 施工人员 |
| `icon-shiwenjiance` | 示温监测 |
| `icon-shizheng` | 市政 |
| `icon-shizhengfenxi` | 市政分析 |
| `icon-shizhenggongyong` | 市政公用 |
| `icon-shizhengsheshi` | 市政设施 |
| `icon-shizhengsheshi1` | 市政设施（变体） |
| `icon-shizhengzonghe` | 市政综合 |
| `icon-shuibengshuliang` | 水泵数量 |
| `icon-shuiku` | 水库 |
| `icon-shuiqingjiance` | 水情监测 |
| `icon-shuiqingjiance-1` | 水情监测（变体） |
| `icon-shuiyuandi` | 水源地 |
| `icon-shuizhicaiyang` | 水质采样 |
| `icon-shuizhijiance` | 水质监测 |
| `icon-suidao` | 隧道 |
| `icon-tonggansheshi` | 同感设施 |
| `icon-tongxinjizhan` | 通信基站 |
| `icon-weiguigongqi` | 违规公器 |
| `icon-wenshidu` | 温湿度 |
| `icon-wenshiduchuanganqi` | 温湿度传感器 |
| `icon-wunichulichang` | 污泥处理厂 |
| `icon-wushuibengzhan` | 污水泵站 |
| `icon-wushuibengzhan-1` | 污水泵站（变体） |
| `icon-wushuibengzhan-2` | 污水泵站（变体2） |
| `icon-wushuiguanwang` | 污水管网 |
| `icon-wushuiguanwang-1` | 污水管网（变体） |
| `icon-xiaofangzhandao` | 消防占道 |
| `icon-xiaohuoshuan` | 消火栓 |
| `icon-xieloubaojing` | 泄漏报警 |
| `icon-yali` | 压力 |
| `icon-yali1` | 压力（变体） |
| `icon-yaliji` | 压力计 |
| `icon-yanwushibie` | 烟雾识别 |
| `icon-yewei` | 液位 |
| `icon-yeweijiance` | 液位监测 |
| `icon-yuliangjiance` | 雨量监测 |
| `icon-yushuibengzhan` | 雨水泵站 |
| `icon-yushuiguanwang` | 雨水管网 |
| `icon-zhihuidaoqiao` | 智慧道桥 |
| `icon-zhihuiqiaoliang` | 智慧桥梁 |
| `icon-zhihuishizheng` | 智慧市政 |
| `icon-zilaishui` | 自来水 |
| `icon-zilaishuitiaojiechi` | 自来水调节池 |
| `icon-zongheguanlang` | 综合管廊 |
| `icon-zongheguanlangfushe` | 综合管廊辐射 |

#### 🌿 环境管理（96 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-a-jianzhulajijianguanxitong` | 建筑垃圾监管系统 |
| `icon-baoloujianzhulaji` | 暴露建筑垃圾 |
| `icon-baolouluotu` | 暴露裸土 |
| `icon-baoloushenghuolaji` | 暴露生活垃圾 |
| `icon-bujifenwenti` | 不尽分问题 |
| `icon-canchulaji` | 餐厨垃圾 |
| `icon-canchushenghuolaji` | 餐厨生活垃圾 |
| `icon-chutushenbao` | 出土申报 |
| `icon-chutushenpi` | 出土审批 |
| `icon-chuyulaji` | 厨余垃圾 |
| `icon-fenbianchulichang` | 粪便处理场 |
| `icon-fenleitianbao` | 分类日报 |
| `icon-fenleitoufang` | 分类投放 |
| `icon-fenleiyizhangtu` | 分类一账图 |
| `icon-fenleizhuanyun` | 分类转运 |
| `icon-fenleizhuanyun1` | 分类转运（变体） |
| `icon-huanweianjian` | 环卫安检 |
| `icon-huanweianjian1` | 环卫安检（变体） |
| `icon-huanweicheliang` | 环卫车辆 |
| `icon-huanweicheliang1` | 环卫车辆（变体） |
| `icon-huanweidashuju` | 环卫大数据 |
| `icon-huanweifenxi` | 环卫分析 |
| `icon-huanweigailan` | 环卫概览 |
| `icon-huanweijiandu` | 环卫监督 |
| `icon-huanweijianguan` | 环卫监管 |
| `icon-huanweilaji` | 环卫垃圾 |
| `icon-huanweirenyuan1` | 环卫人员 |
| `icon-huanweisheshi` | 环卫设施 |
| `icon-huanweisheshi1` | 环卫设施（变体） |
| `icon-huanweisheshi2` | 环卫设施（变体2） |
| `icon-huanweisheshi3` | 环卫设施（变体3） |
| `icon-huanweiyoujiangjubaoshenpi` | 环卫优秀举报审批 |
| `icon-huanweizuoyecheliangshujuguanlimokuai` | 环卫作业车辆数据管理模块 |
| `icon-jianzhulaji` | 建筑垃圾 |
| `icon-jianzhulaji1` | 建筑垃圾（变体） |
| `icon-jianzhulajigongchengmingxibiao` | 建筑垃圾工程项目名录 |
| `icon-jianzhulajiyisa` | 建筑垃圾遗撒 |
| `icon-lajichuli` | 垃圾处理 |
| `icon-lajichuzhi` | 垃圾处置 |
| `icon-lajifenlei` | 垃圾分类 |
| `icon-lajifenlei1` | 垃圾分类（变体） |
| `icon-lajifenleibaogao` | 垃圾分类报告 |
| `icon-lajifenshao` | 垃圾焚烧 |
| `icon-lajifenshaochang` | 垃圾焚烧场 |
| `icon-lajifenshaochang1` | 垃圾焚烧场（变体） |
| `icon-lajiqingyun` | 垃圾轻运 |
| `icon-lajishoujidian` | 垃圾收集点 |
| `icon-lajishouyun` | 垃圾收运 |
| `icon-lajishouyun1` | 垃圾收运（变体） |
| `icon-lajitianmaichang` | 垃圾填埋场 |
| `icon-lajizhongzhuanzhan` | 垃圾中转站 |
| `icon-liangbaotianbao` | 两保天保 |
| `icon-liangbaotianbao1` | 两保天保（变体） |
| `icon-lumianwuran` | 路面污染 |
| `icon-peisongcheliang` | 配送车辆 |
| `icon-pingzhuangqichongzhuangjianguanxitong` | 瓶装气充装监管系统 |
| `icon-qingjiehuanweibaoruoquyu` | 清洁环卫薄弱区域 |
| `icon-sanbaoguanli` | 扫包管理 |
| `icon-sanbaowenti` | 扫包问题 |
| `icon-sanduizhuanti` | 三队专题 |
| `icon-saojinglu` | 扫径路 |
| `icon-saoxuechubingguanlixitong` | 扫雪除冰管理系统 |
| `icon-shenghuolaji` | 生活垃圾 |
| `icon-shenghuolaji1` | 生活垃圾（变体） |
| `icon-shenghuolaji2` | 生活垃圾（变体2） |
| `icon-shenghuolajiguanlixitong` | 生活垃圾管理系统 |
| `icon-shengmingxian` | 生命线 |
| `icon-shengtaihuanbao` | 生态环保 |
| `icon-shirong` | 市容 |
| `icon-shirongfenxi` | 市容分析 |
| `icon-shironghuanweilingyu` | 市容环卫领域 |
| `icon-shirongjianguanshangbao` | 市容监管上报 |
| `icon-shirongshimao` | shirongshimao |
| `icon-shouyunche` | 收运车 |
| `icon-shouzhan` | 收站 |
| `icon-shuzihuanwei` | 数字环卫 |
| `icon-wushui` | 污水 |
| `icon-wushuichuli` | 污水处理 |
| `icon-wushuichulichang` | 污水处理厂 |
| `icon-wushuichulixitong` | 污水处理系统 |
| `icon-wushuijianguan` | 污水监管 |
| `icon-wushuiyizhangtu` | 污水一账图 |
| `icon-youyan` | 油烟 |
| `icon-youyanjiance` | 油烟检测 |
| `icon-youyanshishijiance` | 油烟实时检测 |
| `icon-yunshuche` | 运输车 |
| `icon-zhatuche` | 渣土车 |
| `icon-zhatucheliangchaxun` | 渣土车辆查询 |
| `icon-zhatucheshenweimibi` | 渣土车审未密蔽 |
| `icon-zhatuchetongji` | 渣土车统计 |
| `icon-zhihuihuanwei` | 智慧环卫 |
| `icon-zhihuihuanwei1` | 智慧环卫（变体） |
| `icon-zhihuishirong` | 智慧市容 |
| `icon-zhongzhuanzhan` | 中转站 |
| `icon-zhuangxiulaji` | 装修垃圾 |
| `icon-zhuanyunche` | 转运车 |

#### 🌳 园林绿化（11 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-lvhuagongcheng` | 绿化工程 |
| `icon-lvhuaguanli` | 绿化管理 |
| `icon-miaomuguanli` | 苗木管理 |
| `icon-shumukanfashenpi` | 树木砍伐审批 |
| `icon-xunchayanghurenwuguanlixitong` | 巡查养护任务管理系统 |
| `icon-yanghugongdanliuzhuanpaifaxitong` | 养护工单流转派发系统 |
| `icon-yanghugongsi` | 养护公司 |
| `icon-yanghurenwu` | 养护任务 |
| `icon-yanghurenwu1` | 养护任务（变体） |
| `icon-zhihuilianghua` | 智慧亮化 |
| `icon-zhihuilianghua1` | 智慧亮化（变体） |

#### 🚗 车辆与运输（34 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-changfengshuzichengguan` | 常数资产管 |
| `icon-cheliangchaxun` | 车辆查询 |
| `icon-cheliangchaxun1` | 车辆查询（变体） |
| `icon-cheliangjiankong` | 车辆监控 |
| `icon-cheliangjiankong1` | 车辆监控（变体） |
| `icon-cheliangliebiao` | 车辆列表 |
| `icon-cheliangpaosahangwei` | 车辆抛洒行为 |
| `icon-cheliangweigui` | 车辆违规 |
| `icon-cheliangweiguichachu` | 车辆违规查处 |
| `icon-cheliangweiguishangbao` | 车辆违规上报 |
| `icon-cheliangzuoye` | 车辆作业 |
| `icon-chewuguanli` | 车务管理 |
| `icon-dingdianxuncha` | 定点巡查 |
| `icon-dongtaijiankong` | 动态监控 |
| `icon-dongtaijiankong1` | 动态监控（变体） |
| `icon-dongtaijiankong2` | 动态监控（变体2） |
| `icon-hefeishuzichengguan` | 合肥数资产管 |
| `icon-jiayouzhanchaxun` | 加油站查询 |
| `icon-jixiehuazuoye` | 机械合作业 |
| `icon-kaishiyunshu` | 开始运输 |
| `icon-kakouchaxun` | 卡口查询 |
| `icon-luchanghuiyan` | 路场会验 |
| `icon-luchangzhi` | 路场治 |
| `icon-paizhujiandu` | 派单监督 |
| `icon-xichedian` | 洗车点 |
| `icon-xiuxiedian` | 修鞋点 |
| `icon-xiyidian` | 洗衣点 |
| `icon-yunshudanwei` | 运输单位 |
| `icon-yunshugongsi` | 运输公司 |
| `icon-yunshuqiye` | 运输企业 |
| `icon-yunshuqiyechaxun` | 运输企业查询 |
| `icon-zaxiudian` | 杂修点 |
| `icon-zhatuyunshu` | 渣土运输 |
| `icon-zhunyunzhengchaxun` | 准运证查询 |

#### 🚑 应急与安全（48 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-anfangkaoping` | 安防考评 |
| `icon-anquan` | 安全 |
| `icon-anquan1` | 安全（变体） |
| `icon-baojing` | 报警 |
| `icon-baojingchuzhi` | 报警处置 |
| `icon-disanfangceping` | 第三方测评 |
| `icon-fangxun` | 防汛 |
| `icon-fangxunduiwu` | 防汛队伍 |
| `icon-fangxunpailaojianguanxitong` | 防汛排涝监管系统 |
| `icon-fangxunpingtai` | 防汛平台 |
| `icon-fangxunwuzi` | 防汛物资 |
| `icon-fangxunzhuanjia` | 防汛专家 |
| `icon-fengxianfangkong` | 风险防控 |
| `icon-fengxianguanli` | 风险管理 |
| `icon-jianceyujingxitong` | 检测预警系统 |
| `icon-jiemianzhixu` | 界面秩序 |
| `icon-jinritishi` | 今日提示 |
| `icon-kongyufangan` | 控余方案 |
| `icon-kongyuguihua` | 控余规划 |
| `icon-kongyushifangshuai` | 控余释放率 |
| `icon-kongyuziyuan` | 控余资源 |
| `icon-luanduiluanfang` | 乱堆乱放 |
| `icon-shanzhichangfeng` | 山中火风 |
| `icon-shujuanquan` | 数据权证 |
| `icon-tufachuzhi` | 突发处置 |
| `icon-tufashijian` | 突发事件 |
| `icon-weixianfangwu` | 危险房屋 |
| `icon-xianchangjiancha` | 现场检查 |
| `icon-xunjianbaojingchuzhishuai` | 巡检报警处置率 |
| `icon-yijianchuishao` | 一键吹哨 |
| `icon-yingji` | 应急 |
| `icon-yingjicheliang` | 应急车辆 |
| `icon-yingjiduiwu` | 应急队伍 |
| `icon-yingjijiuyuan` | 应急救援 |
| `icon-yingjirenyuan` | 应急人员 |
| `icon-yingjitoutiao` | 应急头条 |
| `icon-yingjiwuzichubeidian` | 应急物资储备点 |
| `icon-yingjiyanlian` | 应急演练 |
| `icon-yingjiyuan` | 应急源 |
| `icon-yingjizhihui` | 应急智慧 |
| `icon-yingjizhihuitiaoduxitong` | 应急智慧调度系统 |
| `icon-yingjizhuanjia` | 应急专家 |
| `icon-yinhuan` | 隐患 |
| `icon-yinhuanguanli` | 隐患管理 |
| `icon-yinhuanpaicha` | 隐患排查 |
| `icon-yiyaokangyang` | 医疗康养 |
| `icon-yubaojingguanli` | 预警警管理 |
| `icon-yujingchuzhi` | 预警处置 |

#### ⚖️ 行政执法（69 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-banjiaozhuang` | 搬角桩 |
| `icon-bianminchaxun` | 便民查询 |
| `icon-bianminfuwu` | 便民服务 |
| `icon-bianminyizhangtu` | 便民一账图 |
| `icon-chengguandongtai` | 城管动态 |
| `icon-chengguanwanggebianjixitong` | 城管网格编辑系统 |
| `icon-chengguanzhifa` | 城管执法 |
| `icon-chengguanzhifa1` | 城管执法（变体） |
| `icon-chengguanzhifalingyu` | 城管执法领域 |
| `icon-cherongchemaowenti` | 车容车貌问题 |
| `icon-danganguanli` | 档案管理 |
| `icon-danganguanli1` | 档案管理（变体） |
| `icon-dangjietuzai` | 挡街土栽 |
| `icon-dangtuqiang` | 挡土墙 |
| `icon-dianziweilan` | 电子围栏 |
| `icon-dianziweilan2` | 电子围栏（变体） |
| `icon-dinglouguanggao` | 顶楼广告 |
| `icon-falvfagui` | 法律法规 |
| `icon-falvfaguichaxun` | 法规法规查询 |
| `icon-gaizao` | 改造 |
| `icon-gongshigonggao` | 公示公告 |
| `icon-guanggao` | 广告 |
| `icon-guifanguizhang` | 规范规章 |
| `icon-hangzhengshenpi` | 行政审批 |
| `icon-jidongcheluantingfang` | 机动车乱停放 |
| `icon-jinglishuizhunyi` | 经理水准仪 |
| `icon-jinglishuizhunyi1` | 经理水准仪（变体） |
| `icon-jinyan` | 禁烟 |
| `icon-qingchufeifaxiaoguanggao` | 清除非法小广告 |
| `icon-shigong` | 施工 |
| `icon-shigongguanli` | 施工管理 |
| `icon-shimincanyu` | 市民参与 |
| `icon-shujuziyuanguanli` | 数据资源管理 |
| `icon-sidaluanjian` | 私搭乱建 |
| `icon-sidaluanjian1` | 私搭乱建（变体） |
| `icon-tousu` | 投诉 |
| `icon-tousujubao` | 投诉举报 |
| `icon-tousulishi` | 投诉历史 |
| `icon-wangge` | 网格 |
| `icon-weiguihaomaguanli` | 违规号码管理 |
| `icon-weiguitianbao` | 违规填报 |
| `icon-weiguizhanlv` | 违规占绿 |
| `icon-xiaoxizixun` | 消息资讯 |
| `icon-xiaozhaotiejubao` | 小招贴举报 |
| `icon-xinyongjianguan` | 信用监管 |
| `icon-xuanchuanguanggao` | 宣传广告 |
| `icon-xuanchuantiaofu` | 宣传条幅 |
| `icon-yitihuashuzichengguanpingtai` | 一体化数字资产管理平台 |
| `icon-zhengcefagui` | 政策法规 |
| `icon-zhengjianguanli` | 证照管理 |
| `icon-zhifabanan` | 执法办安 |
| `icon-zhifaduiwu` | 执法队伍 |
| `icon-zhifafenxi` | 执法分析 |
| `icon-zhifajiandu` | 执法监督 |
| `icon-zhifakaoshipeixunxitong` | 执法考核培训系统 |
| `icon-zhifarenyuan` | 执法人员 |
| `icon-zhihuizhifa` | 智慧执法 |
| `icon-zhihuizhifa1` | 智慧执法（变体） |
| `icon-zhihuizhifa2` | 智慧执法（变体2） |
| `icon-zhinengjiance` | 智能监测 |
| `icon-zhongdianrenzoufangtongji` | 重点人走访统计 |
| `icon-zhongping` | 重平 |
| `icon-ziyuanguanli` | 资源管理 |
| `icon-ziyuanmulu` | 资源目录 |
| `icon-zizhishenpi` | 自制审批 |
| `icon-zonghechaxun` | 综合查询 |
| `icon-zonghejiancha` | 综合检查 |
| `icon-zongherenwu` | 综合任务 |
| `icon-zonghezhifa` | 综合执法 |

#### 📋 案件管理（48 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-anjian` | 案件 |
| `icon-anjianchoucha` | 案件抽查 |
| `icon-anjianchoucha1` | 案件抽查（变体） |
| `icon-anjianchuli` | 案件处理 |
| `icon-anjianchuzhi` | 案件处置 |
| `icon-anjianduban` | 案件督办 |
| `icon-anjianfenxi` | 案件分析 |
| `icon-anjianshangbao` | 案件上报 |
| `icon-anjianshenhe` | 案件审核 |
| `icon-anshichuzhi` | 按时处置 |
| `icon-anyuanfenpai` | 案源分派 |
| `icon-beianguanli` | 备案管理 |
| `icon-chuzhizheng` | 处置证 |
| `icon-chuzhizhengchaxun` | 处置证查询 |
| `icon-daixiangying` | 待响应 |
| `icon-hechabanjie` | 核查办结 |
| `icon-heimingdanchaxun` | 黑名单查询 |
| `icon-heshihecha` | 合食核查 |
| `icon-jinduchaxun` | 进度查询 |
| `icon-jujueanjian` | 拒绝案件 |
| `icon-lingdaojiaoban` | 领导交班 |
| `icon-lingdaoshenpi` | 领导审批 |
| `icon-renwuchaosong` | 任务抄送 |
| `icon-renwuchaxun` | 任务查询 |
| `icon-renwufenpei` | 任务分配 |
| `icon-rexian` | 热线 |
| `icon-rexianhuchu` | 热线呼出 |
| `icon-rexianhuru` | 热线呼入 |
| `icon-reyuan` | 热源 |
| `icon-ruhuanjianzongshu` | 入环件总数 |
| `icon-shangbaoanjian` | 上报案件 |
| `icon-shijianchuzhi` | 事件处置 |
| `icon-shijianhecha` | 事件核查 |
| `icon-suqiu` | 诉求 |
| `icon-suqiurenshu` | 诉求人数 |
| `icon-weichuzhi` | 未处置 |
| `icon-weijiananjianguanli` | 违建安检管理 |
| `icon-wenti` | 问题 |
| `icon-wenti1` | 问题（变体） |
| `icon-wentijiaoban` | 问题交班 |
| `icon-wentishangbao` | 问题上报 |
| `icon-wentizhenggai` | 问题整改 |
| `icon-woderenwu` | 我的任务 |
| `icon-woderenwu1` | 我的任务（变体） |
| `icon-woshenhederenwu` | 我审核的任务 |
| `icon-woyaoliuyan` | 我要留言 |
| `icon-yichuzhi` | 已处置 |
| `icon-yijianjiaoban` | 一键交班 |

#### 📊 监测与统计（118 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-banjieshuai` | 办结率 |
| `icon-daofang` | 到访 |
| `icon-daoqiaojianguan` | 道桥监管 |
| `icon-daoqiaojianguan-1` | 道桥监管（变体） |
| `icon-dashujufenxixitong` | 大数据分析系统 |
| `icon-dianli` | 电力 |
| `icon-dianziliandan` | 电子联单 |
| `icon-dubanguanli` | 督办管理 |
| `icon-gongzhongfuwupingjia` | 公众服务评价 |
| `icon-gongzuojixiaopingjia` | 工作绩效评价 |
| `icon-jiance` | 监测 |
| `icon-jiancexinxiguanli` | 检测信息管理 |
| `icon-jiandukaohe` | 检测考核 |
| `icon-jiandukaohe1` | 检测考核（变体） |
| `icon-jiandushouli` | 检测受理 |
| `icon-jiandushouli-1` | 检测受理（变体） |
| `icon-jiandushouli1` | 检测受理（变体2） |
| `icon-jiandutianbao` | 监督填报 |
| `icon-jiandutongbao` | 监督通报 |
| `icon-jianduzhihui` | 检测指挥 |
| `icon-jianduzhihui-1` | 检测指挥（变体） |
| `icon-jianduzhihui-11` | 检测指挥（变体2） |
| `icon-jianduzhihui1` | 检测指挥（变体3） |
| `icon-jianduzhihui2` | 检测指挥（变体4） |
| `icon-jianguan` | 监管 |
| `icon-jichushuju` | 基础数据 |
| `icon-jichushujucaiji` | 基础数据采集 |
| `icon-jiejueshuai` | 解决率 |
| `icon-jingxihuakaoping` | 精细化考核 |
| `icon-jinritixing` | 今日提醒 |
| `icon-juecejianyi` | 决策建议 |
| `icon-kaohedengji` | 考核等级 |
| `icon-kaohefankui` | 考核反馈 |
| `icon-kaohepingjia` | 考核评价 |
| `icon-kaohepingjia1` | 考核评价（变体） |
| `icon-kaohetongbao` | 考核通报 |
| `icon-kaopingguanli` | 考评管理 |
| `icon-kaopingtong` | 考评通报 |
| `icon-kaopingxitong` | 考评系统 |
| `icon-kongjianfenxi` | 空间分析 |
| `icon-kongjianxinxi` | 空间信息 |
| `icon-lajimoduanchuzhitongchoujianguanxitong` | 垃圾末端处置统筹监管系统 |
| `icon-litixuncha` | 立体巡查 |
| `icon-manyidu` | 满意度 |
| `icon-manyishuai` | 满意率 |
| `icon-pingjiazhibiao` | 评价指标 |
| `icon-pingjiazhibiao-1` | 评价指标（变体） |
| `icon-pingjiazhibiao1` | 评价指标（变体2） |
| `icon-qushi` | 趋势 |
| `icon-quxian` | 曲线 |
| `icon-richangxuncha` | 日常巡查 |
| `icon-ruhujiancha` | 入户检查 |
| `icon-ruwangshuai` | 入网率 |
| `icon-shengchanxunjianrenwuguanlimokuai` | 生产巡检任务管理模块 |
| `icon-shequxianfeng` | 社区先锋 |
| `icon-shexiangtou` | 摄像头 |
| `icon-shipin` | 视频 |
| `icon-shipinfenxi` | 视频分析 |
| `icon-shipinguangchang` | 视频广场 |
| `icon-shipinjiankong` | 视频监控 |
| `icon-shipinjiankong1` | 视频监控（变体） |
| `icon-shipinjiankong2` | 视频监控（变体2） |
| `icon-shipinjiankongchakan` | 视频监控查看 |
| `icon-shipinshangbao` | 视频上报 |
| `icon-shipintonghua` | 视频通话 |
| `icon-shipinzhinengfenxixitong` | 视频智能分析系统 |
| `icon-shipinzhongxinxitong` | 视频中心系统 |
| `icon-shiquxianyitihua` | 市辖区一体化 |
| `icon-shishizhuizong` | 实时追踪 |
| `icon-shishizhuizong1` | 实时追踪（变体） |
| `icon-shujubiaozhun` | 数据标准 |
| `icon-shujufuwuzhicheng` | 数据服务支撑 |
| `icon-shujuhuiju` | 数据汇聚 |
| `icon-shujujianmo` | 数据建模 |
| `icon-shujujiaohuan` | 数据交换 |
| `icon-shujujiaohuan1` | 数据交换（变体） |
| `icon-shujujicheng` | 数据集成 |
| `icon-shujumulu` | 数据目录 |
| `icon-shujutianbao` | 数据年报 |
| `icon-shujutianbao1` | 数据年报（变体） |
| `icon-shujutianbao2` | 数据年报（变体2） |
| `icon-shujutianbao3` | 数据年报（变体3） |
| `icon-shujuyunweijiankong` | 数据运维监控 |
| `icon-shujuzhiliang` | 数据质量 |
| `icon-shujuzhongxin` | 数据中枢 |
| `icon-tianhuzhanhu` | 天户站户 |
| `icon-tongjifenxi` | 统计分析 |
| `icon-tongjifenxi-1` | 统计分析（变体1） |
| `icon-tongjifenxi-2` | 统计分析（变体2） |
| `icon-tongjifenxi1` | 统计分析（变体3） |
| `icon-tongjifenxi2` | 统计分析（变体4） |
| `icon-tongjifenxi3` | 统计分析（变体5） |
| `icon-tongzhi` | 通知 |
| `icon-wenjianjilu` | 文件记录 |
| `icon-xianqing` | 险情 |
| `icon-xunchaguiji` | 巡查轨迹 |
| `icon-xunchajihua` | 巡查计划 |
| `icon-xunchajihua1` | 巡查计划（变体） |
| `icon-xunchashangbao` | 巡查上报 |
| `icon-xunjianguanli` | 巡检管理 |
| `icon-xunshi` | 巡视 |
| `icon-yuanshuju` | 元数据 |
| `icon-yunhangjiance` | 运行监测 |
| `icon-yuqingjiance` | 舆情监测 |
| `icon-yuqingjiance1` | 舆情监测（变体） |
| `icon-zerenqu` | 责任区 |
| `icon-zhiliangxunchaxitong` | 质量巡查系统 |
| `icon-zhuanxiangpingjia` | 专项评价 |
| `icon-zhuanxiangpucha` | 专项普查 |
| `icon-zhuanyunzhandiantongjifenxixitong` | 转运站点统计分析系统 |
| `icon-zonghefenxi` | 综合分析 |
| `icon-zonghefenxi1` | 综合分析（变体） |
| `icon-zonghepingjia` | 综合评价 |
| `icon-zonghepingjia-1` | 综合评价（变体） |
| `icon-zonghezhanshi` | 综合展示 |
| `icon-zonghezhili` | 综合治理 |
| `icon-zongzhikaohe` | 综治考核 |
| `icon-zongzhizuzhi` | 综治组织 |

#### 💾 数据与信息（23 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-biaodan` | 表单 |
| `icon-chaxuntongji` | 查询统计 |
| `icon-dengji` | 登记 |
| `icon-gongzuoliu` | 工作流 |
| `icon-guifanwajueshiminfuwu` | 规范挖掘民服务 |
| `icon-jichuxinxi` | 基础信息 |
| `icon-juecefenxi` | 决策分析 |
| `icon-kongzhatu` | 控闸图 |
| `icon-sanweicaiji` | 三维采集 |
| `icon-sanweimoxing` | 三维模型 |
| `icon-shoulipingtai` | 受理平台 |
| `icon-shuzinengli` | 数字能力 |
| `icon-shuziyunzhuan` | 数字运转 |
| `icon-tongyiGIS` | 统一 GIS |
| `icon-tongyiyonghu` | 统一用户 |
| `icon-wulianwangpingtai` | 物联网平台 |
| `icon-xietongpingtai` | 协同平台 |
| `icon-xinxigengxin` | 信息更新 |
| `icon-xitongpeizhi` | 系统配置 |
| `icon-xitongshezhi` | 系统设置 |
| `icon-yuqingshangbao` | 舆情上报 |
| `icon-zaixiancaiji` | 在线采集 |
| `icon-ziliaoku` | 资料库 |

#### 🏢 企业与人员（35 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-anyuanguanli` | 案员管理 |
| `icon-anyuanshenpi` | 案员审批 |
| `icon-caijiyuanguanli` | 采购元管理 |
| `icon-chengxinguanli` | 城行管理 |
| `icon-congyerenyuan` | 从业元人员 |
| `icon-dilibianma` | 地理编码 |
| `icon-dilibianma1` | 地理编码（变体） |
| `icon-gerenzhongxin` | 个人中心 |
| `icon-gushumingmu` | 股述名目 |
| `icon-gushumingmu1` | 股述名目（变体） |
| `icon-haoyouyuan` | 好友元 |
| `icon-haoyouyuan1` | 好友元（变体） |
| `icon-kaoqinyichangshenpi` | 考勤异常审批 |
| `icon-qiandaodati` | 签到打卡 |
| `icon-qinwuguanli` | 勤务管理 |
| `icon-qiyechaxun` | 企业查询 |
| `icon-qiyechaxun1` | 企业查询（变体） |
| `icon-qiyeguanli` | 企业管理 |
| `icon-qiyeguanli1` | 企业管理（变体） |
| `icon-qiyenianshen` | 企业年报 |
| `icon-qiyenianshen1` | 企业年报（变体） |
| `icon-qiyexinyongguanli` | 企业信用管理 |
| `icon-quanzeguanli` | 权责管理 |
| `icon-renmizhuanxiangzixitong` | 人密转项自系统 |
| `icon-renxiangshibie` | 人像识别 |
| `icon-renyuancaita` | 人员踩踏 |
| `icon-renyuanguanli` | 人员管理 |
| `icon-shimingrenzheng` | 实名认证 |
| `icon-xuncharenyuanguanli` | 巡查人员管理 |
| `icon-xungengdaka` | 巡更打卡 |
| `icon-xungengrenwudaka` | 巡更任务打卡 |
| `icon-yidongkaoqin` | 移动考勤 |
| `icon-yishuyima` | 艺术条码 |
| `icon-yonghuzhongxinxitong` | 用户中心系统 |
| `icon-yunweirenyuan` | 运维人员 |

#### 📢 公众服务（39 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-aixinyizhan` | 爱心驿站 |
| `icon-aixinyizhan-1` | 爱心驿站（变体） |
| `icon-bujian` | 部件 |
| `icon-bujiangengxin` | 步检更新 |
| `icon-bujiangengxin1` | 步检更新（变体） |
| `icon-duanxinfuwu` | 短信服务 |
| `icon-erweimatupian` | 二维码图片 |
| `icon-gongwentonggao` | 公文通告 |
| `icon-gongzhongfuwu` | 公众服务 |
| `icon-gongzhongfuwuerweima` | 公众服务二维码 |
| `icon-gongzhongtiaocha` | 公众调查 |
| `icon-gongzhongtiaocha1` | 公众调查（变体） |
| `icon-hezhunbeian` | 核准备案 |
| `icon-hezhunguanli` | 核准管理 |
| `icon-jifenguanli` | 积分管理 |
| `icon-ligebaobei` | 理赔宝贝 |
| `icon-linlihuzhu` | 邻里互助 |
| `icon-ruandianhua` | 软电话 |
| `icon-saoyisao` | 扫一扫 |
| `icon-shanghuxinxicaiji` | 商户信息采集 |
| `icon-shanghuzhuxiaoshenpi` | 商户注销审批 |
| `icon-shequfuwu` | 社区服务 |
| `icon-shequgonggao` | 社区公告 |
| `icon-shequweishengfuwuzhan` | 社区卫生服务站 |
| `icon-shixiangqingdanguanli` | 事项清单管理 |
| `icon-shixiangqingdanquequan` | 事项清单权缺 |
| `icon-xiaoleizhushou` | 小类助手 |
| `icon-xingfuzhishu` | 幸福指数 |
| `icon-xinwenzixun` | 新闻资讯 |
| `icon-yingyongguanli` | 应用管理 |
| `icon-yingyongweihu` | 应用维护 |
| `icon-yingyongweihu1` | 应用维护（变体） |
| `icon-yitukongwei` | 一体控位 |
| `icon-yuqingjiankongerweima` | 舆情监控二维码 |
| `icon-yuyueguanli` | 预约管理 |
| `icon-zhengjianxinxi` | 证件信息 |
| `icon-zhiyuanzhefuwu` | 志愿者服务 |
| `icon-zixun` | 资讯 |
| `icon-zixunhudong` | 资讯互动 |

#### 🔧 运维与配置（10 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-changdiguanli` | 场地管理 |
| `icon-gongju` | 工具 |
| `icon-paibianbiaoshiguanlixitong` | 牌匾标识管理系统 |
| `icon-paibianbiaoshiguanlixitongbeifen` | 牌匾标识管理系统（备份） |
| `icon-peizhiguanli` | 配置管理 |
| `icon-peizhiweihu` | 配置维护 |
| `icon-peizhiweihu1` | 配置维护（变体） |
| `icon-shiyongbangzhu` | 使用帮助 |
| `icon-xiangmukuguanlixitong` | 项目库管理系统 |
| `icon-zhinengfuzhu` | 智能辅助 |

#### 🏘️ 智慧社区（26 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-chanyejiegou` | 产业结构 |
| `icon-chengshibiaoshi` | 城市标识 |
| `icon-chengshicehui` | 城市测绘 |
| `icon-chengshigengxin` | 城市更新 |
| `icon-chengshineilao` | 城市内涝 |
| `icon-chengshineilaoguanlixitong` | 城市内涝管理系统 |
| `icon-chengshireliguanlixitong` | 城市立面管理系统 |
| `icon-chengshitijian` | 城市事件 |
| `icon-chengzhenfangwuzongheguanli` | 城镇房屋综合管理 |
| `icon-huangtuluolou` | 黄土裸露 |
| `icon-jianzhuwuwailimian` | 建筑物外立面 |
| `icon-lishijianzhu` | 历史建筑 |
| `icon-loufang` | 楼房 |
| `icon-loufang1` | 楼房（变体） |
| `icon-nongcunfangwuzongheguanli` | 农村房屋综合管理 |
| `icon-quyu` | 区域 |
| `icon-quyusousuo` | 区域搜索 |
| `icon-quyuxinxizhanshi` | 区域信息展示 |
| `icon-shehuigongyue` | 社会公约 |
| `icon-shengtingyewuzhidaoxitong` | 省厅业务指导系统 |
| `icon-weixiu` | 维修 |
| `icon-weixiu1` | 维修（变体） |
| `icon-wenjuantiaocha` | 问卷调查 |
| `icon-wenjuantiaocha1` | 问卷调查（变体） |
| `icon-xionganxinquyewuzhidaoxitong` | 雄安新区业务指导系统 |
| `icon-zongbujingji` | 总部经济 |

#### 🏗️ 工地管理（27 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-chuangjianyundan` | 创建运单 |
| `icon-gaoduanqingzhizaoye` | 高端轻制造业 |
| `icon-gongchengtouzi` | 工程投资 |
| `icon-gongchengyizhangtu` | 工程一账图 |
| `icon-gongchushenqingguanli` | 工程申请管理 |
| `icon-gongdanguanlixitong` | 工单管理系统 |
| `icon-gongdi` | 工地 |
| `icon-gongdichaxun` | 工地查询 |
| `icon-gongdichutuqingkuang` | 工地出图情况 |
| `icon-gongdiguanli` | 工地管理 |
| `icon-gongdixinxi` | 工地信息 |
| `icon-gongdiyangchenshangbao` | 工地扬尘上报 |
| `icon-gongdizhili` | 工地治理 |
| `icon-gongjiangongxiang` | 工地共享 |
| `icon-jianzhushichangguanli` | 建筑市场管理 |
| `icon-jianzhushichangguanlibeifen` | 建筑市场管理（备份） |
| `icon-nianduwangongxiangmu` | 年度完工项目 |
| `icon-nianduxinjianxiangmu` | 年度新建项目 |
| `icon-nianduxujianxiangmu` | 年度续建项目 |
| `icon-rengongzhineng` | 人工智能 |
| `icon-wurenji` | 无人机 |
| `icon-wurenji1` | 无人机（变体） |
| `icon-wurenji2` | 无人机（变体2） |
| `icon-xiangmuyiwanchengtouzi` | 项目已完成投资 |
| `icon-xiangmuzongtouzi` | 项目总投资 |
| `icon-zhatugongdichaxun` | 渣土工地查询 |
| `icon-zhujianbuyewuzhidaoxitong` | 主建不业务指导系统 |

#### 📡 通信与物联（12 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-ADS-B` | ADS-B |
| `icon-Aoa` | Aoa |
| `icon-PHzhi` | PH值 |
| `icon-a-5G` | 5G |
| `icon-a-5GA` | 5GA |
| `icon-a-RemoteId` | a-RemoteId |
| `icon-a-hubeizhujianzonghefuwupingtai` | 湖北住建综合服务平台 |
| `icon-jishitongxun` | 技术通讯 |
| `icon-jishitongxun1` | 技术通讯（变体） |
| `icon-lianwangjiandu` | 联网监督 |
| `icon-lianwangjiandu1` | 联网监督（变体） |
| `icon-zhimaifushe` | 植埋辐射 |

#### 🔲 违建与渣土（9 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-weifajianshe` | 违法建设 |
| `icon-weifangtanta` | 违法摊摊 |
| `icon-weijianjihua` | 违建计划 |
| `icon-weijiantongji` | 违建统计 |
| `icon-zhatugaikuang` | 渣土概况 |
| `icon-zhatuzhifa` | 渣土执法 |
| `icon-zhihuiweijian` | 智慧违建 |
| `icon-zhihuizhatu` | 智慧渣土 |
| `icon-zhongduanchuzhichaxun` | 终端处置查询 |

#### 📋 办公与任务（28 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-a-zhongdiansheshixuncha` | 重点设施巡查 |
| `icon-changdiyuyue` | 场地预约 |
| `icon-gongzuofankui` | 工作反馈 |
| `icon-gongzuoliangtongji` | 工作量统计 |
| `icon-gongzuorizhi` | 工作日志 |
| `icon-goutongjiaoliu` | 沟通交流 |
| `icon-jierujichang` | 接入机场 |
| `icon-jisaoshuixi` | 洒水水洗 |
| `icon-jisaoshuixi1` | 洒水水洗（变体） |
| `icon-linshixinghuwaihuodongshenpi` | 临时性户外活动审批 |
| `icon-mianji` | 面积 |
| `icon-qingxu` | 情绪 |
| `icon-qingxuerongbing` | 清雪融冰 |
| `icon-renwu` | 任务 |
| `icon-shangbaojihua` | 上报计划 |
| `icon-shiqianshizhongshihou` | 事前事中事后 |
| `icon-shishifeihanghuodong` | 实时飞行活动 |
| `icon-shuji` | 书记 |
| `icon-taishi` | 态势 |
| `icon-xiaonachang` | 小牧场 |
| `icon-xiaonachang1` | 小牧场（变体） |
| `icon-xiaonachangxinxi` | 小牧场信息 |
| `icon-xietonggongzuo` | 协同工作 |
| `icon-yangqi` | 扬弃 |
| `icon-yanjieshanghuguankong` | 沿街商铺管控 |
| `icon-yikelunjing` | 一刻钟景 |
| `icon-zhihuipaiqian` | 智慧派遣 |
| `icon-zonghetaishi` | 综合态势 |

#### 🏷️ 状态与其他（65 个）

| 图标ID | 中文名 |
|--------|--------|
| `icon-a-Frame1` | 框架1 |
| `icon-a-Frame11` | 框架1（变体） |
| `icon-a-Frame2` | 框架2 |
| `icon-biaomianshiyingbianji` | biaomianshiyingbianji |
| `icon-buhege` | 不合格 |
| `icon-caidan` | 菜单 |
| `icon-caigangwa` | 彩钢瓦 |
| `icon-cheliangzhandaojingying` | 车辆占道经营 |
| `icon-chuzhi` | chuzhi |
| `icon-daidaochang` | daidaochang |
| `icon-didingjizuoshangbao` | didingjizuoshangbao |
| `icon-diqiu` | 地球 |
| `icon-gangping` | 钢瓶 |
| `icon-gonganjingyong` | gonganjingyong |
| `icon-gongchang` | 工厂 |
| `icon-guoqixuanguabuguifan` | 国旗悬挂不规范 |
| `icon-handongshuiwei` | 涵洞水位 |
| `icon-hangluguihua` | hangluguihua |
| `icon-hangyeguanli` | 行业管理 |
| `icon-hangyeyingyong` | 行业应用 |
| `icon-hedaoshuiwei` | 河道水位 |
| `icon-hege` | 合格 |
| `icon-hehuxuncha` | hehuxuncha |
| `icon-heliu` | 河流 |
| `icon-huochezhan` | 火车站 |
| `icon-jiandujianchaguanlixitong` | 监督检查管理系统 |
| `icon-jianyi` | 建议 |
| `icon-jiaoguanyingyong` | jiaoguanyingyong |
| `icon-jiawan` | jiawan |
| `icon-jihuawancheng` | jihuawancheng |
| `icon-jishuidian` | jishuidian |
| `icon-laxianweiyiji` | 拉线位移计 |
| `icon-lishi` | 历史 |
| `icon-lixian` | 离线 |
| `icon-lixian1` | 离线（变体） |
| `icon-luduan` | 路段 |
| `icon-lukou` | 路口 |
| `icon-nongmaoshichang` | 农贸商场 |
| `icon-paomaodilou` | paomaodilou |
| `icon-qingjiaoji` | 清角机 |
| `icon-qinzhanwuzhangaitongdao` | qinzhanwuzhangaitongdao |
| `icon-sanzhoucezhenyi` | 三轴测振仪 |
| `icon-shijian` | 时间 |
| `icon-shijingdianwei` | 市景点位 |
| `icon-sijiduan` | 四季段 |
| `icon-sunhaichengshihuanjing` | 损毁城市环境 |
| `icon-toufangdian` | 投放点 |
| `icon-waizhisheshi` | 外置设施 |
| `icon-xuncha` | xuncha |
| `icon-yewuzhidaoxitong` | 业务指导系统 |
| `icon-yichangcheliangtianbao` | 异常车辆填报 |
| `icon-yingyongzhicheng` | 应用支撑 |
| `icon-yuantoudianchaxun` | yuantoudianchaxun |
| `icon-yulv` | 雨率 |
| `icon-yushui` | 雨水 |
| `icon-zaixiancheliang` | 在线车辆 |
| `icon-zhandaobuguifandawei` | 占道不规范大位 |
| `icon-zhandaojingying` | 占道经营 |
| `icon-zhandaojingying1` | 占道经营（变体） |
| `icon-zhaopian` | zhaopian |
| `icon-zhatuzhuanxiangzixitong` | 渣土转项自系统 |
| `icon-zhihuixietiaoxitong` | 智慧协调系统 |
| `icon-zhongyangzijinzhichi` | 中央资金支持 |
| `icon-zhuodu` | 浊度 |
| `icon-zonghekaohe` | 综合考核 |


---

#### 📦 通用 UI 图标库（129 个）

#### 📦 通用 UI 图标库（129 个）

##### 基础操作（20 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-search` | 搜索 |
| `zt-icon-icon_line_search` | 搜索（线条）|
| `zt-icon-back` | 返回 |
| `zt-icon-home` | 首页 |
| `zt-icon-homepage-person-s` | 首页人员 |
| `zt-icon-menu` | 菜单 |
| `zt-icon-menu-collapse` | 菜单折叠 |
| `zt-icon-menu-s` | 菜单（小）|
| `zt-icon-more` | 更多 |
| `zt-icon-more-miniprogram` | 小程序更多 |
| `zt-icon-more-plugin` | 插件更多 |
| `zt-icon-expand` | 展开 |
| `zt-icon-shrink` | 收缩 |
| `zt-icon-close-miniprogram` | 关闭小程序 |
| `zt-icon-refresh` | 刷新 |
| `zt-icon-clear` | 清除 |
| `zt-icon-clear-r` | 清除（右下角）|
| `zt-icon-delete` | 删除 |
| `zt-icon-down` | 向下 |
| `zt-icon-exit` | 退出 |

##### 选择与状态（17 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-check` | 勾选 |
| `zt-icon-check-blank-r` | 圆形勾选 |
| `zt-icon-check-r` | 勾选（右下角）|
| `zt-icon-all-check` | 全选 |
| `zt-icon-checkbox-select` | 复选框选择 |
| `zt-icon-radio-round` | 单选圆圈 |
| `zt-icon-select-multiple` | 多选 |
| `zt-icon-success` | 成功 |
| `zt-icon-success-r` | 成功（右下角）|
| `zt-icon-warning` | 警告 |
| `zt-icon-warning-r` | 警告（右下角）|
| `zt-icon-deadline-r` | 截止时间 |
| `zt-icon-funnel` | 漏斗 |
| `zt-icon-filter` | 过滤 |
| `zt-icon-icon_line_filter` | 过滤（线条）|
| `zt-icon-sort` | 排序 |
| `zt-icon-verify` | 验证 |

##### 显示与隐藏（4 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-eye` | 显示 |
| `zt-icon-eye-closed` | 隐藏 |
| `zt-icon-eye-o` | 显示（轮廓）|
| `zt-icon-eye-closed-o` | 隐藏（轮廓）|

##### 导航与位置（10 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-arrow-right` | 右箭头 |
| `zt-icon-backspace` | 退格 |
| `zt-icon-location` | 位置 |
| `zt-icon-locate` | 定位 |
| `zt-icon-navigation` | 导航 |
| `zt-icon-top` | 顶部 |
| `zt-icon-top-mark` | 顶部标记 |
| `zt-icon-move` | 移动 |
| `zt-icon-link` | 链接 |
| `zt-icon-site` | 站点 |

##### 媒体与通讯（18 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-call` | 电话 |
| `zt-icon-microphone` | 麦克风 |
| `zt-icon-microphone-in-talk` | 通话中 |
| `zt-icon-audio` | 音频 |
| `zt-icon-sound-wave` | 声波 |
| `zt-icon-volume-on` | 音量开 |
| `zt-icon-volume-off` | 音量关 |
| `zt-icon-broadcast` | 广播 |
| `zt-icon-message` | 消息 |
| `zt-icon-letter` | 信件 |
| `zt-icon-scan` | 扫描 |
| `zt-icon-photo-default` | 默认图片 |
| `zt-icon-photo-fail` | 图片失败 |
| `zt-icon-ring` | 铃声 |
| `zt-icon-whistle` | 口哨 |
| `zt-icon-smile` | 笑脸 |
| `zt-icon-smile-plus` | 笑脸加 |
| `zt-icon-no-disturbing` | 免打扰 |

##### 交互与操作（18 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-play` | 播放 |
| `zt-icon-play-r` | 播放（右下角）|
| `zt-icon-play-small` | 播放（小）|
| `zt-icon-pause` | 暂停 |
| `zt-icon-stop-r` | 停止（右下角）|
| `zt-icon-edit` | 编辑 |
| `zt-icon-copy` | 复制 |
| `zt-icon-revoke` | 撤销 |
| `zt-icon-recall` | 回撤 |
| `zt-icon-reply` | 回复 |
| `zt-icon-recycle` | 重用 |
| `zt-icon-recollect` | 重新收集 |
| `zt-icon-sweep` | 扫除 |
| `zt-icon-keyboard-arrow-down` | 键盘向下箭头 |
| `zt-icon-keyboard-arrow-up` | 键盘向上箭头 |
| `zt-icon-keyboard-s` | 键盘（小）|
| `zt-icon-keyboard-shrink` | 键盘收缩 |
| `zt-icon-scroll-button` | 滚动按钮 |

##### 分享与标记（9 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-share` | 分享 |
| `zt-icon-share-o` | 分享（轮廓）|
| `zt-icon-like` | 点赞 |
| `zt-icon-upvote` | 赞 |
| `zt-icon-star` | 星标 |
| `zt-icon-star-half` | 半星标 |
| `zt-icon-tag` | 标签 |
| `zt-icon-quote` | 引用 |
| `zt-icon-petal` | 花瓣 |

##### 信息与时间（8 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-help-r` | 帮助 |
| `zt-icon-question-r` | 问题 |
| `zt-icon-clock` | 时钟 |
| `zt-icon-time-slip` | 时间滑块 |
| `zt-icon-time-interval` | 时间间隔 |
| `zt-icon-calendar` | 日历 |
| `zt-icon-mission` | 任务 |
| `zt-icon-case` | 案例 |

##### 数据与列表（4 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-statistics` | 统计 |
| `zt-icon-list` | 列表 |
| `zt-icon-waterfall-flow` | 瀑布流 |
| `zt-icon-linkage` | 联动 |

##### 设置与安全（6 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-setting` | 设置 |
| `zt-icon-setting-o` | 设置（轮廓）|
| `zt-icon-setting-s` | 设置（小）|
| `zt-icon-fingerprint` | 指纹 |
| `zt-icon-face-recognition` | 人脸识别 |
| `zt-icon-passphrase` | 密码短语 |

##### 个人与组织（3 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-me` | 我 |
| `zt-icon-contact` | 联系人 |
| `zt-icon-department` | 部门 |

##### 加载与下载（3 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-spinner-expand` | 加载展开 |
| `zt-icon-spinner-shrink` | 加载收缩 |
| `zt-icon-download` | 下载 |

##### 系统与工具（2 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-gps-signal` | GPS 信号 |
| `zt-icon-cloud` | 云 |

##### 其他图标（7 个）

| 图标ID | 中文名 |
|--------|--------|
| `zt-icon-at` | @ 符号 |
| `zt-icon-plus` | 加号 |
| `zt-icon-plus-r` | 加号（右下角）|
| `zt-icon-minus` | 减号 |
| `zt-icon-minus-r` | 减号（右下角）|
| `zt-icon-minus-s` | 减号（小）|
| `zt-icon-tab-default` | 标签页默认 |

### iconfont 使用说明

生成 iconfont 图标时，预览页面中通过 `fetchSymbolPaths()` 函数从 3 个 JS 库中按 `targetSymbolId` 查找匹配的 `<symbol>` 元素，提取其中的 `<path d="...">` 属性，内联渲染为纯 SVG，不依赖外部 CSS 或字体。
