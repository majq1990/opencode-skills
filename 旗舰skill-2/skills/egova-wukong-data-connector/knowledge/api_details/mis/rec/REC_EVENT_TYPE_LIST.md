# 案件类型列表接口

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_EVENT_TYPE_LIST |
| domain | MIS案件 |
| bizObject | 问题类型 |
| apiName | 案件类型列表接口 |
| apiType | dict |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/eventType/list` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件类型相关/案件类型列表接口` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 下拉筛选、级联筛选、问题类型字典、案件类型筛选项 |

---

## 2. 接口说明

该接口用于按照查询条件查询所需的问题类型，用于问题类型展示或筛选条件。

适合：

- 问题类型下拉框；
- 问题大类筛选；
- 问题小类筛选；
- 级联筛选；
- 案件类型/问题类型字典展示。

不适合：

- 案件统计；
- 案件列表；
- 案件详情；
- 图表聚合统计。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_dic_event_any_type | 业务库问题类型表 |

---

## 4. 请求参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| id | String | 否 | 无 | 指定问题类型主键 |
| ids | String[] | 否 | 无 | 指定问题类型主键列表 |
| typeCode | String | 否 | 无 | 指定问题类型编码 |
| typeName | String | 否 | 无 | 模糊查询问题类型名称 |
| grade | String | 否 | 无 | 指定问题类型等级 |
| parentId | String | 否 | 无 | 指定问题类型父类型，查询其子问题类型 |
| parentIds | String[] | 否 | 无 | 指定问题类型父类型列表，查询其子问题类型 |

### grade 说明

| 值 | 含义 |
|---|---|
| 1 | 问题类型 |
| 2 | 问题大类 |
| 3 | 问题小类 |

---

## 5. 请求示例

```json
{
  "grade": "2"
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果 | 下拉/字典数据源 |
| result[].id | id | String | 是 | 问题类型主键 | 可映射为 `value` |
| result[].typeCode | typeCode | String | 是 | 问题类型编码 | 可用于展示或联动 |
| result[].typeName | typeName | String | 是 | 问题类型名称 | 可映射为 `label` |
| result[].grade | grade | String | 是 | 等级：1 问题类型，2 问题大类，3 问题小类 | 可用于层级判断 |
| result[].parentId | parentId | String | 是 | 父问题类型主键 | 可用于级联 |
| result[].children | children | Object[] | 否 | 子节点列表 | 树/级联组件 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 辅助统计 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "id": "222",
      "typeCode": "01",
      "typeName": "公用设施",
      "grade": "2",
      "displayOrder": null,
      "showFlag": "1",
      "parentId": "2",
      "regionId": "0",
      "extendType": null,
      "children": []
    }
  ],
  "message": null,
  "tag": null,
  "totalCount": 23
}
```

---

## 8. 报错说明

| message | 说明 | 处理建议 |
|---|---|---|
| 其他报错 | 需联系后台排查数据 | 检查请求参数、数据权限、后台日志 |

---

## 9. 适配建议

### 适合组件

- 下拉筛选；
- 级联筛选；
- 树形筛选；
- 问题类型字典。

### 字段映射建议：下拉筛选

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| label | item.typeName | 字符串兜底 |
| value | item.id | 字符串兜底 |
| parentId | item.parentId | 字符串兜底 |
| grade | item.grade | 字符串兜底 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            label: item.typeName || '',
            value: item.id || '',
            code: item.typeCode || '',
            grade: item.grade || '',
            parentId: item.parentId || '',
            children: Array.isArray(item.children) ? item.children : []
        };
    });
}
```

---

## 10. 性能和联调注意点

1. 该接口是字典接口，不返回案件数量。
2. `grade=2` 通常用于查询问题大类。
3. 查询级联时，通常使用 `parentId` 或 `parentIds`。
4. 如组件需要树形结构，应确认返回中的 `children` 是否完整。