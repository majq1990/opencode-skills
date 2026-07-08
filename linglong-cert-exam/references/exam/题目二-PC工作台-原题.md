<!-- 来源：钉钉文档 nodeId=Y1OQX0akWm3gYmA4ivD7MZrkJGlDd3mE （题目二（必考）：PC工作台，https://alidocs.dingtalk.com/i/nodes/Y1OQX0akWm3gYmA4ivD7MZrkJGlDd3mE） -->

# **一、试题背景**

现需在灵珑平台中配置一个监管工作台页面，用于展示项目、车辆、垃圾类型和运输时间范围下的联单数据概览、趋势图表及联单明细列表。

请基于已提供的数据表、视图或数据模型，在灵珑中完成页面搭建、数据绑定、图表配置、筛选联动和列表操作配置，最终页面效果参考提供的工作台截图。包括：
1. 支持按项目名称、车牌号、垃圾类型、运输时间进行组合查询；
2. 展示联单总数、异常运单数、垃圾清运量、垃圾处置量等概览指标；
3. 展示联单趋势图表；
4. 展示联单列表，并支持导出数据和跳转查看更多；
5. 查询、重置和筛选条件变化后，各模块数据应正确刷新。

![image.png](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/1GXn45Ko38YBMqDQ/img/2b763b0a-fda9-474c-97ad-e8d229e2fb88.png?Expires=1783485198&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=rJsfSPCDN4Q7sontHEF%2BFi4iOGU%3D "")



[工作台.mp4](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/1GXn45Ko38YBMqDQ/att/03832bfa-6f89-40e8-b40b-1f84ab87139c.mp4?Expires=1783485198&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=DGDyBds457LV4CoJjFptmRZCPb0%3D)



# **二、背景条件与数据准备**

## **1\. 数据来源说明**

本题涉及的数据来源如下，已内置在考试应用里。

| **数据用途分组** | **数据源类型** | **数据源名称** | **说明** |
|----------------------|-------------------|-------------------|----------|
| 查询筛选项 |  视图  | 项目下拉；<br>车辆选择下拉；<br>垃圾类型下拉 | 用于顶部筛选区下拉选项 |
| 数据概览 | 视图 | 联单概览统计 | 返回联单总数、异常运单数、垃圾清运量、垃圾处置量 |
| 联单趋势 | DDCAT | 联单趋势 | 返回日期、电子联单数量、异常联单数量 |
| 联单列表 | 视图 | 电子联单列表 | 返回联单编号、工地名称、运输企业等列表字段 |

## **2\. 建议入参要求**

各统计数据源和联单列表需支持以下动态入参：

| **入参名称** | **字段含义** | **对应字段** | **说明** |
|----------------|----------------|----------------|----------|
| siteIds | 项目标识 | site\_id | 为空时查询全部项目；项目名称为下拉多选 |
| vehicleNum | 车牌号 | <span style="background-color: rgb(245, 247, 250);">vehicle\_num</span> | 为空时查询全部车辆 |
| cicleType | “天/周/月”图例控制组件参数 | \\ | 联单趋势图数据展示控制参数 |
| muckType | 垃圾类型 | muck\_type | 为空时查询全部垃圾类型 |
| startDate | 运输开始时间 | trans\_date | 为空时不限制开始时间 |
| endDate | 运输结束时间 | trans\_date | 为空时不限制结束时间 |

默认运输时间范围建议为近 30 天。

## **3\. 输出字段要求**

### **3.1 数据概览输出字段**

| **输出字段** | **含义** | **展示要求** |
|----------------|----------|----------------|
| totalWaybillCount | 联单总数 | 数值 \+ 单位“单” |
| abnormalWaybillCount | 异常运单数 | 数值 \+ 单位“单” |
| cleanAmount | 垃圾清运量 | 保留 2 位小数 \+ 单位“吨” |
| disposalAmount | 垃圾处置量 | 保留 2 位小数 \+ 单位“吨” |



### **3.2 联单趋势输出字段**

| **输出字段** | **含义** | **展示要求** |
|----------------|----------|----------------|
| statDate | 统计日期 | x 轴日期 |
| electronicWaybillCount | 电子联单数量 | 柱状图数据 |
| abnormalWaybillCount | 异常联单数量 | 折线图数据 |



### **3.3 联单列表输出字段**

| **输出字段** | **含义** | **展示要求** |
|----------------|----------|----------------|
| record\_num | 联单编号 | 列表展示 |
| record\_num | 工地名称 | 列表展示 |
| unit\_name | 运输企业 | 列表展示 |
| vehicle\_num | 车牌号 | 列表展示 |
| consumptive\_name | 处置场所名称 | 列表展示 |
| create\_time | 创建时间 | 格式：yyyy-MM-dd HH:mm:ss |

# 三、工作台页面配置要求

## **1\. 页面目标**

请在灵珑中配置一个建筑垃圾监管工作台页面。页面需支持顶部筛选，并根据筛选条件刷新数据概览、联单趋势和联单列表。

页面整体结构参考截图，采用上方查询区、下方统计图表和列表组合布局。

## **2\. 页面布局要求**

页面至少包含以下区域：
1. 查询区位于页面顶部，包含项目名称、车牌号、垃圾类型、运输时间、重置按钮、查询按钮。
2. 统计区左侧展示数据概览，包含 4 张指标卡片；右侧展示联单趋势图。
3. 列表操作区联单列表顶部应有“导出数据”按钮和“更多 \>”入口。

## **3\. 查询区要求**

### **3.1 内容要求**

![image.png](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/1GXn45Ko38YBMqDQ/img/1911f7eb-1efb-4508-b840-255ef6b1817b.png?Expires=1783485198&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=jI2%2FglAi1jmB28sP65IGs8TnRn0%3D "")



查询区需包含以下筛选字段：

| **字段** | **控件类型** | **要求** |
|----------|----------------|----------|
| 项目名称 | 下拉多选 | 占位提示“请选择项目名称”；支持清空 |
| 车牌号 | 下拉单选 / 下拉搜索 | 占位提示“请选择车牌号”；支持清空 |
| 垃圾类型 | 下拉单选 | 占位提示“垃圾类型”；支持清空 |
| 运输时间 | 日期范围选择 | 默认近 30 天或按考试环境要求设置 |
| 重置 | 按钮 | 清空查询字段或恢复默认值 |
| 查询 | 按钮 | 触发所有模块刷新 |

### **3.2 交互要求**
1. 点击“查询”后，页面所有数据模块按当前筛选条件刷新；
2. 点击“重置”后，项目名称、车牌号、垃圾类型恢复为空，运输时间恢复默认值，并展示所有数据；
3. 任一筛选字段为空时，对应条件不生效；
4. 查询字段需正确传递到所有统计和列表数据源。



## **4\. 数据概览要求**

### **4.1 内容要求**

![image.png](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/1GXn45Ko38YBMqDQ/img/0b68f8b2-069e-4909-8ed2-ef9eb2cadefb.png?Expires=1783485198&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=GXTVqBM%2F2PT1kUE%2FmfmP4CZl4pU%3D "")

图片素材：

![QQ20260529-163610.png](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/1GXn45Ko38YBMqDQ/img/9145bd6a-6367-4fdf-8821-94ac536da936.png?Expires=1783485198&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=98APjnIOF1jVRzJLY6dT9UX9iRk%3D "")![QQ20260529-163810.png](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/1GXn45Ko38YBMqDQ/img/eb0b1a80-d91e-4c42-9b67-340172eb17c1.png?Expires=1783485198&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=1pGXLzOWJxNcvJZIdUsyABPkVbA%3D "")![QQ20260529-163829.png](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/1GXn45Ko38YBMqDQ/img/86a9b0ca-2e60-42cb-9608-c95d88c12213.png?Expires=1783485198&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=FZUjRqWNKmDsTfN9bQYPd4v31n4%3D "")![QQ20260529-163911.png](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/1GXn45Ko38YBMqDQ/img/f36885e7-b34d-4e06-acd5-1da752590c13.png?Expires=1783485198&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=U%2Fqm8ITpVWxq7GDAtiigKDaVl1U%3D "")



数据概览区域展示 4 个指标：

| **指标名称** | **展示单位** | **示例值** |
|----------------|----------------|-------------|
| 联单总数 | 单 | 3089 单 |
| 异常运单数 | 单 | 14 单 |
| 垃圾清运量 | 吨 | 59311.35 吨 |
| 垃圾处置量 | 吨 | 58313.96 吨 |

### **4.2 交互要求**

顶部筛选条件变化并查询后，4 个指标需同步更新。数据为空时，指标显示为 0 或 0.00，不应出现 undefined、null、NaN。



## **5\. 联单趋势要求**

### **5.1 内容要求**

![image.png](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/1GXn45Ko38YBMqDQ/img/437bf673-3f4c-421a-9a10-e0c7d918a588.png?Expires=1783485198&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=eJjaO2oZ2YBvnehG%2Fyev8TveBPc%3D "")



使用 echart 柱状图或柱线混合图展示联单趋势。图表需包含：
1. 顶部图例：电子联单、异常联单；
2. x 轴展示日期；
3. y 轴展示联单数量，单位为“单”；
4. 电子联单建议用柱状图展示；
5. 异常联单建议用折线图展示；
6. 鼠标悬停时展示对应日期和数据值。

### **5.2 交互要求**

顶部筛选条件变化并查询后，联单趋势图需刷新；右上角粒度切换后，图表需按新粒度刷新。





## **6\. 联单列表要求**

![image.png](https://alidocs2.oss-cn-zhangjiakou.aliyuncs.com/res/1GXn45Ko38YBMqDQ/img/0821993b-238a-4ed2-80ce-5a6f4372a650.png?Expires=1783485198&OSSAccessKeyId=LTAI5tKTjg4Kq1HCdBJ8qpSp&Signature=HQ7FmYdzmCTC7gc23ekhpzqGPyc%3D "")

### **6.1 内容要求**

联单列表需展示以下字段：

| **字段** | **说明** |
|----------|----------|
| 序号 | 当前页序号 |
| 联单编号 | 联单唯一编号 |
| 工地名称 | 工地 / 项目点位名称 |
| 运输企业 | 运输企业名称 |
| 车牌号 | 车辆牌照 |
| 处置场所名称 | 处置场所或消纳场名称 |
| 创建时间 | 联单创建时间 |

列表需支持分页，分页信息应展示总条数、当前页、页码和跳页能力。

### **6.2 顶部操作要求**
1. “导出数据”：导出当前筛选条件下的联单列表数据；
2. “更多 \>”：配置一个联单列表页面，点击“更多 \>”跳转到联单列表列表页面；

### **6.3 交互要求**

顶部查询条件需控制联单列表数据。点击查询或重置后，列表应重新加载并回到第一页。



# 四、评分标准（40分）

本题总分 40 分。

| 评分子项 | 评分分数 | 评分点 |
|------------|------------|---------|
| 查询 | 8 | 内容：查询字段包含项目名称下拉多选、车牌号、垃圾类型单选、运输时间日期范围选择、重置按钮和查询按钮（4）。交互：重置按钮重置查询字段为空并展示所有数据（4）；查询按钮控制页面所有模块的数据展示。 |
| 数据概览 | 8 | 内容：数据概览详情组件展示联单总数、异常运单数、垃圾清运量、垃圾处置量（4）。交互：顶部查询条件控制数据概览数据（4）。 |
| 联单趋势（echarts 柱状图） | 16 | 内容：顶部图例数据完整；鼠标悬停展示数据；x 轴和 y 轴展示正确；图里展示电子联单柱状条和异常联单折线数据（6）。交互：顶部查询条件控制图表数据（8）；“天/周/月”时间维度控制图标数据交互（2分） |
| 联单列表 | 8 | 内容：展示列表字段，包括联单编号、工地名称、运输企业、车牌号、处置场所名称、创建时间；顶部操作按钮包含导出数据，更多跳转到具体列表页（4）。交互：顶部查询条件控制列表数据（4）。 |
