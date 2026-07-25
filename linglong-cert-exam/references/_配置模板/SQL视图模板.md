# SQL 视图配置模板

## 基础模板

```sql
SELECT 
    field1,
    field2,
    field3,
    -- ... 其他字段
FROM table_name
#tag where()
    #if (param1 != null && param1 != '')
        AND field1 = '${param1}'
    #end
    #if (param2 != null && param2 != '')
        AND field2 = '${param2}'
    #end
```

## 时间范围筛选模板

```sql
SELECT 
    -- ... 字段列表
FROM table_name
#tag where()
    #if (startTime != null && startTime != '')
        AND create_time >= '${startTime}'
    #end
    #if (endTime != null && endTime != '')
        AND create_time <= '${endTime}'
    #end
```

## 多条件筛选模板

```sql
SELECT 
    -- ... 字段列表
FROM table_name
#tag where()
    #if (status != null && status != '')
        AND status = '${status}'
    #end
    #if (regionId != null && regionId != '')
        AND region_id = '${regionId}'
    #end
    #if (startTime != null && startTime != '')
        AND create_time >= '${startTime}'
    #end
    #if (endTime != null && endTime != '')
        AND create_time <= '${endTime}'
    #end
```

## 分页 + 排序模板

```sql
SELECT 
    -- ... 字段列表
FROM table_name
#tag where()
    #if (filterParam != null && filterParam != '')
        AND field = '${filterParam}'
    #end
ORDER BY sortField #sortOrder
LIMIT #pageSize OFFSET #offset
```

## 注意事项

1. **`#tag where()`**：自动生成 WHERE 关键字，避免没有条件时 WHERE 后面跟 AND 报错
2. **`#if/#end`**：Freemarker 风格的条件判断，参数由页面组件绑定传入
3. **`${param}`**：参数占位符，灵珑平台会自动替换为实际值
4. **参数绑定**：页面组件（如日期选择器、下拉框）的绑定字段需与 SQL 中的参数名一致

## 常见问题

- **Q**: SQL 执行报错 "You have an error in your SQL syntax"
  - **A**: 检查 `#tag where()` 是否缺失，或 `#if/#end` 配对是否正确

- **Q**: 筛选参数不生效
  - **A**: 检查页面组件绑定的参数名是否与 SQL 中 `${param}` 一致

- **Q**: Monaco 编辑器无法提取 SQL
  - **A**: 缩放编辑器容器（`.code-editor` → `style.height = '600px'`），然后遍历 `.view-line` 元素的 `textContent`
