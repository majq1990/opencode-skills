# 人员类型列表查询

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | PATROL_TYPE_LIST |
| domain | MIS人员 |
| bizObject | 人员类型 |
| apiName | 人员类型列表查询 |
| apiType | dict |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/patrol-type/list` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/人员类型列表查询` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 下拉筛选、人员类型筛选项、字典列表 |

---

## 2. 接口说明

该接口用于按照查询条件查询所需的人员类型，用于人员类型展示或筛选条件。

适合：

- 人员类型下拉框；
- 人员类型筛选项；
- 人员类型字典展示；
- 人员类型枚举配置。

不适合：

- 人员数量统计；
- 人员明细列表；
- 地图点位；
- 人员详情。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_patrol_type | 业务库人员类型表 |

---

## 4. 请求参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| id | String | 否 | 无 | 指定人员类型主键 |
| ids | String[] | 否 | 无 | 指定人员类型主键列表 |

---

## 5. 请求示例

```json
{
  "id": "1"
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果 | 下拉/字典数据源 |
| result[].id | id | String | 是 | 人员类型 id | 可映射为 `value` |
| result[].displayName | displayName | String | 是 | 人员类型名称 | 可映射为 `label` |
| result[].displayOrder | displayOrder | Integer | 是 | 显示次序 | 可用于排序 |
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
      "id": "1",
      "displayName": "人员类型一",
      "displayOrder": 1
    }
  ],
  "message": null,
  "tag": null,
  "totalCount": 1
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
- 多选筛选；
- 人员类型字典；
- 查询条件配置。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| label | item.displayName | 字符串兜底 |
| value | item.id | 字符串兜底 |
| order | item.displayOrder | Number 转换 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            label: item.displayName || '',
            value: item.id || '',
            order: Number(item.displayOrder || 0)
        };
    }).sort(function (a, b) {
        return a.order - b.order;
    });
}
```

---

## 10. 性能和联调注意点

1. 该接口是字典接口，不返回人员数量或人员明细。
2. 如果用于筛选项，通常映射为 `label/value`。
3. 如果组件字段要求是 `name/value`，需要在 filter 中把 `displayName` 映射为 `name`。