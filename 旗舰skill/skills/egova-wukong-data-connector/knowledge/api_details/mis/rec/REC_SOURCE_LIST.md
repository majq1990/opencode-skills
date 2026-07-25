# 案件来源列表接口

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_SOURCE_LIST |
| domain | MIS案件 |
| bizObject | 案件来源 |
| apiName | 案件来源列表接口 |
| apiType | dict |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/recordsSource/list` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件来源相关/案件来源列表接口` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 下拉筛选、字典列表、案件来源筛选项 |

---

## 2. 接口说明

该接口用于按照查询条件查询所需的案件来源，用于案件来源展示或筛选条件。

适合：

- 案件来源下拉框；
- 案件来源筛选项；
- 案件来源字典展示；
- 案件来源树/级联筛选的基础数据。

不适合：

- 案件统计；
- 案件列表；
- 案件详情；
- 图表聚合统计。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_dic_event_src | 业务库案件来源表 |

---

## 4. 请求参数

| 参数名 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
|---|---|---|---|---|---|
| id | String | 否 | 无 | 用于查询展示的案件来源 | 指定案件来源 id |
| ids | String[] | 否 | 无 | 用于查询展示的案件来源 | 指定案件来源 id 列表 |
| excludeIds | String[] | 否 | 无 | 用于查询展示的案件来源 | 指定排除的案件来源 id 列表 |
| eventSrcName | String | 否 | 无 | 用于查询展示的案件来源 | 模糊查询案件来源 |
| seniorId | String | 否 | 无 | 用于查询展示的案件来源 | 指定案件来源的父来源 id |
| seniorIds | String[] | 否 | 无 | 用于查询展示的案件来源 | 指定案件来源的父来源 id 列表 |

---

## 5. 请求示例

```json
{}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果 | 下拉/字典数据源 |
| result[].id | id | String | 是 | 案件来源主键 | 可映射为 `value` |
| result[].eventSrcName | eventSrcName | String | 是 | 案件来源名称 | 可映射为 `label` |
| result[].seniorId | seniorId | String | 是 | 上级案件来源主键 | 可用于父子关系 |
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
      "eventSrcName": "信息采集员上报",
      "seniorId": "-1"
    }
  ],
  "message": null,
  "tag": null,
  "totalCount": 39
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
- 案件来源字典；
- 级联来源筛选。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| label | item.eventSrcName | 字符串兜底 |
| value | item.id | 字符串兜底 |
| parentId | item.seniorId | 字符串兜底 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            label: item.eventSrcName || '',
            value: item.id || '',
            parentId: item.seniorId || ''
        };
    });
}
```

---

## 10. 性能和联调注意点

1. 该接口是字典接口，不返回案件数量。
2. 如果用于下拉筛选，通常映射为 `label/value`。
3. 如果要做级联来源筛选，可使用 `seniorId` 构建父子关系。