# 部门列表接口

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | UNIT_LIST |
| domain | MIS基础资料 |
| bizObject | 部门 |
| apiName | 部门列表接口 |
| apiType | dict |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/unit/list` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/部门相关/部门列表接口` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 部门下拉、部门筛选、组织列表、部门字典 |

---

## 2. 接口说明

该接口用于按照查询条件查询所需的部门，用于部门展示或筛选条件。

注意：

部门信息存在是否删除以及是否有效的逻辑，所以在做列表查询时，查询条件建议加上未删除且有效：

```json
{
  "deleteFlag": false,
  "validFlag": true
}
```

适合：

- 部门下拉框；
- 部门筛选项；
- 部门字典展示；
- 组织机构列表。

不适合：

- 部门案件统计；
- 部门车辆统计；
- 部门树形统计；
- 人员明细查询。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_unit | 业务库部门表 |

---

## 4. 请求参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| id | String | 否 | 无 | 指定部门主键 |
| ids | String[] | 否 | 无 | 指定部门主键列表 |
| typeCode | String | 否 | 无 | 指定部门编码 |
| address | String | 否 | 无 | 模糊查询部门地址 |
| validFlag | Boolean | 否 | 无 | 是否有效 |
| deleteFlag | Boolean | 否 | 无 | 是否删除 |
| unitName | String | 否 | 无 | 模糊查询部门名称 |
| regionId | String | 否 | 无 | 指定部门所属区划 |
| parentId | String | 否 | 无 | 指定部门所属父级部门 |

---

## 5. 请求示例

```json
{
  "deleteFlag": false,
  "validFlag": true
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果 | 下拉/字典数据源 |
| result[].id | id | String | 是 | 部门 id | 可映射为 `value` |
| result[].unitName | unitName | String | 是 | 部门名称 | 可映射为 `label` |
| result[].unitShortened | unitShortened | String | 是 | 部门简称 | 可展示 |
| result[].unitDesc | unitDesc | String | 是 | 部门描述 | 可展示 |
| result[].unitCode | unitCode | String | 是 | 部门编码 | 可用于联动 |
| result[].parentId | parentId | String | 是 | 上级部门 id，默认为 0 | 可用于父子关系 |
| result[].displayOrder | displayOrder | Integer | 是 | 显示次序 | 可用于排序 |
| result[].address | address | String | 是 | 部门地址 | 可展示 |
| result[].telOffice | telOffice | String | 是 | 部门电话 | 可展示 |
| result[].validFlag | validFlag | Boolean | 是 | 是否有效 | 过滤条件 |
| result[].deleteFlag | deleteFlag | Boolean | 是 | 是否删除 | 过滤条件 |
| result[].regionId | regionId | String | 是 | 所属区划 | 可用于联动 |
| result[].regionType | regionType | String | 是 | 所属区划类型 | 可用于联动 |
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
      "unitName": "网格化城市管理",
      "unitShortened": "",
      "unitDesc": "",
      "unitCode": "1",
      "parentId": "0",
      "displayOrder": null,
      "address": "",
      "telOffice": "",
      "validFlag": true,
      "deleteFlag": false,
      "regionId": "0",
      "regionType": "1",
      "count": null
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

- 部门下拉框；
- 部门筛选项；
- 组织列表；
- 部门字典。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| label | item.unitName | 字符串兜底 |
| value | item.id | 字符串兜底 |
| parentId | item.parentId | 字符串兜底 |
| code | item.unitCode | 字符串兜底 |
| regionId | item.regionId | 字符串兜底 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            label: item.unitName || '',
            value: item.id || '',
            parentId: item.parentId || '',
            code: item.unitCode || '',
            regionId: item.regionId || '',
            regionType: item.regionType || ''
        };
    });
}
```

---

## 10. 性能和联调注意点

1. 建议默认传 `deleteFlag=false`、`validFlag=true`。
2. 该接口是部门字典接口，不返回统计数据。
3. 如果需要树形组织结构，需根据 `parentId` 自行构建，或确认是否存在部门树接口。