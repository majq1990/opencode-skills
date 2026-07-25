# 第一题：差错件管理配置详解

## 基本信息

- **工作空间**：`2060246493936320512-c872-c95b-d674`
- **应用名称**：`实操练习应用-mjq-第一题`
- **访问入口**：`http://8.130.36.66:8080/linglong/workspace.html#/2060246493936320512-c872-c95b-d674/`

---

## 1. 业务实体

### 1.1 实体分组

- **全部分组**（根）
  - **题目一**（分组）
    - 差错件页面（页面）
  - **题目二**（分组）

### 1.2 实体列表（12个）

| 中文名称 | 表名 | 实体标识 | 类型 | 数据源 |
|---------|------|---------|------|-------|
| 领导看板 | root_5lwuoz | ds_tbl_t_eb721c4faf064ab0b0d1dfcf9ec5698a | 内部表 | 技术支持部实操练习 |
| 领导看板 | root_a49sgn | ds_tbl_f9a88f7119a81ade70b89f560f776fca-d674 | 内部表 | 技术支持部实操练习 |
| **差错件表** | **mis_error_rec** | ds_tbl_e33c0bffe8750ba2e25b7df87aebe821-d674 | **外部表** | 技术支持部实操练习 |
| 处置场表 | to_site_consumptive | ds_tbl_bf4eba2c6869a2a324fb81d72a52dbc4-d674 | 外部表 | 技术支持部实操练习 |
| 工地表 | to_construction_site | ds_tbl_f22bd890d14102d83ba3c14ca3cc4410-d674 | 外部表 | 技术支持部实操练习 |
| 车辆表 | tc_vehicle | ds_tbl_1a799f335442922e2d026f879ad3679c-d674 | 外部表 | 技术支持部实操练习 |
| 车辆单位表 | tc_vehicle_unit | ds_tbl_6ba18b01bac302e253c5237ee7a37b2a-d674 | 外部表 | 技术支持部实操练习 |
| 区域表 | tc_region | ds_tbl_c330be3c7532ca9d7fc502bd6805c03b-d674 | 外部表 | 技术支持部实操练习 |
| 主表 | constr_waybill_record | ds_tbl_a9208d9f21e906405da4312b56ee2361-d674 | 外部表 | 技术支持部实操练习 |
| 天周月下拉选择-联单趋势 | root_c95gvk | ds_tbl_5dbb3acff5d210402b3b8e09eaccbca9-d674 | 内部表 | 技术支持部实操练习 |

---

## 2. 数据视图（SQL视图）

### 2.1 视图信息

- **viewid**: `ds_tbl_t_df8c35468df94d91a7f9dc19387a3a60`
- **categoryId**: `52459070-3142-4cd4-ab81-8abc5d5115a9`
- **查询表**: `mis_error_rec`（差错件表）
- **访问路径**：数据管理 → 数据视图 → 编辑 → 设计

### 2.2 完整 SQL

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

### 2.3 SQL 关键点

1. **SELECT 字段**：30个字段，涵盖差错件的完整信息（任务号、错误类型、创建时间、区域、建议、审核状态等）
2. **FROM 表**：`mis_error_rec`（外部表，需先导入表结构）
3. **动态筛选**：
   - `#tag where()`：自动生成 WHERE 关键字（避免没有条件时 WHERE 后面跟 AND 报错）
   - `#if/#end`：Freemarker 风格的条件判断
   - 筛选参数：`createTimeStart` / `createTimeEnd`（由页面组件绑定传入）

### 2.4 操作记录

- 直接访问 SQL 视图 URL 返回 404，需通过数据视图列表 → 编辑 → 设计路径进入
- 编辑按钮触发"10项未保存的修改"警告，需关闭警告后再进入设计页
- Monaco 编辑器 `window.monaco` 全局对象不可访问
- 通过缩放编辑器容器（`.code-editor` → `style.height = '600px'`）后，可访问 `.view-line` 元素提取 SQL 内容

---

## 3. 页面管理

### 3.1 页面信息

- **页面名称**：差错件页面
- **页面ID**：`2077947046590119936`
- **分组**：第一题
- **URL**：`http://8.130.36.66:8080/linglong/workspace.html#/2060246493936320512-c872-c95b-d674/page-build/page/2077947046590119936`

### 3.2 页面构建器

- **画布状态**：空画布（"从左侧拖拽来添加组件"）
- **组件库**：左侧导航（表单 / 列表 / 详情 / 树形）
- **页面属性**（右侧配置面板）：
  - **页头配置**：关
  - **弹性布局**：
    - 方向：column
    - 主轴：flex-start
    - 副轴：flex-start
  - **生命周期**：
    - 页面加载完成时：绑定动作（待配置）
    - 页面关闭时：绑定动作（待配置）

### 3.3 配置建议

1. **拖拽列表组件**到画布，绑定数据源为上述 SQL 视图
2. **配置列表列**：根据 SQL 视图字段配置显示列（任务号、错误类型、创建时间等）
3. **配置筛选区**：添加日期选择器，绑定 `createTimeStart` / `createTimeEnd` 参数
4. **绑定生命周期**：
   - 页面加载完成时：调用 `api.DATA_SOURCE_EXECUTE` 查询数据
   - 页面关闭时：清理数据/重置状态

---

## 4. 配置步骤总结

```
第一步：业务实体 → 确认 mis_error_rec 外部表已导入
第二步：数据视图 → 创建 SQL 视图（复制上述 SQL）
第三步：页面管理 → 新建页面，拖拽列表组件，绑定数据源
第四步：配置筛选 → 添加日期筛选组件，绑定参数
第五步：生命周期 → 绑定页面加载动作
第六步：导航配置 → 配置菜单入口
第七步：发布预览 → 验证功能
```

---

## 5. 注意事项

- Monaco 编辑器无法直接通过 `window.monaco` 访问，需通过 DOM 操作提取内容
- SQL 视图编辑需先关闭"未保存的修改"警告
- 页面构建器组件库需从左侧拖拽添加
- 数据视图 SQL 中的 `#tag where()` 和 `#if/#end` 是灵珑平台的模板语法，不是标准 SQL
