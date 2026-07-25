---
name: 灵珑考核实战
description: |
  灵珑资深专家认证考核专用 skill，聚焦实操配置场景的快速落地。
  已探明第一题完整配置结构（mis_error_rec 差错件表 + SQL视图 + 页面构建）。
  触发词：灵珑考核 / 认证考试 / 实操题 / 第一题 / 第二题 / 差错件 / 
  mis_error_rec / SQL视图配置 / 考核workspace / 认证题 / 配置手册生成 /
  领导看板考核 / PC工作台考核 / 移动流程考核 / 复杂视图公式打印考核 / 数据模型高级检索考核。
---

# 灵珑认证考核实战（LingLong Cert Exam）

专注灵珑资深专家认证的实操题快速配置。本 skill 存的是**已探明的配置结构和可复用模板**，
不是通用灵珑支持（通用配置/脚本/知识库检索用 `linglong-support`）。

---

## 考核背景

- **认证名称**：大区灵珑资深专家认证
- **时间**：每年 4 月 / 9 月
- **题型**：必考 2 题（各 40 分：领导看板 / PC 工作台）+ 抽考 1 题（20 分：移动流程 / 复杂视图公式打印 / 数据模型高级检索 三选一）
- **总分**：100 分
- **考核环境**：独立 workspace，需从零搭建应用

---

## 已探明：第一题 workspace 结构

**工作空间**：`2060246493936320512-c872-c95b-d674`
**应用名称**：`实操练习应用-mjq-第一题`
**访问入口**：`http://8.130.36.66:8080/linglong/workspace.html#/2060246493936320512-c872-c95b-d674/`

### 导航栏模块
数据管理 / 部件管理 / 页面管理 / 导航配置 / 登录页 / 工作台 / 应用设置

### 业务实体（12个）

| 中文名称 | 表名 | 类型 | 备注 |
|---------|------|------|------|
| **差错件表** | `mis_error_rec` | **外部表** | ⭐第一题核心表 |
| 处置场表 | `to_site_consumptive` | 外部表 | |
| 工地表 | `to_construction_site` | 外部表 | |
| 车辆表 | `tc_vehicle` | 外部表 | |
| 车辆单位表 | `tc_vehicle_unit` | 外部表 | |
| 区域表 | `tc_region` | 外部表 | |
| 主表 | `constr_waybill_record` | 外部表 | |
| 领导看板 | `root_5lwuoz` / `root_a49sgn` | 内部表 | 看板用 |
| 天周月下拉选择-联单趋势 | `root_c95gvk` | 内部表 | 趋势筛选 |

### 数据视图（SQL视图）

- **viewid**: `ds_tbl_t_df8c35468df94d91a7f9dc19387a3a60`
- **查询表**: `mis_error_rec`
- **完整 SQL**：

```sql
SELECT 
    task_num,
    error_main_type_names,
    create_time,
    district_name,
    suggest,
    error_id,
    district_id,
    explain_content,
    explain_state,
    explain_time,
    rec_id,
    rec_task_num,
    task_id,
    verify_suggest,
    verify_time,
    act_def_id,
    urgent_flag,
    un_archive_flag,
    read_flag,
    rec_mark_error_flag,
    explain_end_time,
    error_main_type_ids,
    mark_human_id,
    mark_human_name,
    remarks,
    error_sub_type_ids,
    error_sub_type_names,
    accepter_id,
    accepter_name
FROM mis_error_rec
#tag where()
    #if (createTimeStart != null && createTimeStart != '')
        AND create_time >= '${createTimeStart}'
    #end
    #if (createTimeEnd != null && createTimeEnd != '')
        AND create_time <= '${createTimeEnd}'
    #end
```

- **动态筛选机制**：`#tag where()` 自动生成 WHERE 关键字；`#if/#end` 实现条件动态拼接
- **筛选参数**：`createTimeStart` / `createTimeEnd`（页面组件绑定）

### 页面管理

- **页面名称**：差错件页面
- **页面ID**：`2077947046590119936`
- **分组**：第一题
- **URL**：`.../page-build/page/2077947046590119936`
- **画布状态**：空画布（待拖拽组件）
- **页面属性**：
  - 弹性布局：column 方向
  - 生命周期：页面加载完成时 / 页面关闭时 可绑定动作

---

## 第一题配置要点（已探明）

1. **数据源**：基于 `mis_error_rec` 外部表创建 SQL 视图
2. **筛选能力**：通过 `#tag where()` + `#if/#end` 实现时间范围动态筛选
3. **页面构建**：在"差错件页面"中拖拽列表/表单组件，绑定 SQL 视图数据源
4. **交互设计**：页面生命周期绑定动作（加载时查询数据、关闭时清理）

---

## 第二题（待探明）

第二题分组已存在但配置内容未探明。需：
1. 点击"题目二"分组查看实体
2. 探查数据视图配置
3. 探查页面管理配置

---

## 考核配置通用流程

```
1. 业务实体 → 导入/创建外部表（获取表结构）
2. 数据视图 → 创建 SQL 视图（配置查询逻辑 + 动态筛选）
3. 页面管理 → 新建页面 + 拖拽组件 + 绑定数据源
4. 导航配置 → 配置菜单入口
5. 工作台（如需）→ 配置看板组件
6. 发布预览 → 验证功能
```

---

## 关键操作记录

| 操作 | 路径/方法 |
|------|----------|
| 访问 SQL 视图设计页 | 数据视图 → 编辑 → 设计（不能直接访问 URL，需列表进入） |
| 提取 Monaco 编辑器 SQL | 缩放容器 → `querySelector('.view-line')` → 遍历 `textContent` |
| 编辑按钮警告 | 弹出"10项未保存的修改"，需关闭警告后再进入设计页 |

---

## 数据来源

- 2026-07-17：首次探明第一题 workspace 完整配置结构
- 成熟配置手册范例：`D:\opencode\file\2026-07-10\灵珑配置手册\`
- 通用灵珑支持：`D:\git\opencode-skills\linglong-support\`

---

## 目录结构

```
linglong-cert-exam/
├── SKILL.md                  # 本文件（考核专用）
├── references/               # 已探明配置记录
│   ├── 第一题-config.md       # 第一题完整配置详情
│   ├── 第二题-config.md       # 第二题配置（待探明）
│   └── _配置模板/             # 可复用配置模板
└── samples/                  # 考核真题范例（如有）
```

> **注意**：通用灵珑配置/脚本/知识库检索请优先使用 `linglong-support` skill。
> 本 skill 只专注认证考核的实操题快速落地。
