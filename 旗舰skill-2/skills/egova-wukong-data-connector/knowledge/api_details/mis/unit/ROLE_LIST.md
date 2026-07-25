# 岗位列表接口

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | ROLE_LIST |
| domain | MIS基础资料 |
| bizObject | 岗位 |
| apiName | 岗位列表接口 |
| apiType | dict |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/role/list` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/岗位相关/岗位列表接口` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 岗位下拉、岗位筛选、岗位字典、岗位列表 |

---

## 2. 接口说明

该接口用于按照查询条件查询所需的岗位，用于岗位展示或筛选条件。

注意：

岗位信息存在是否删除以及是否有效的逻辑，所以在做列表查询时，查询条件建议加上未删除且有效：

```json
{
  "deleteFlag": false,
  "validFlag": true
}
```

适合：

- 岗位下拉框；
- 岗位筛选项；
- 岗位字典展示；
- 按部门过滤岗位。

不适合：

- 岗位统计；
- 人员列表；
- 部门统计。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_role | 业务库岗位表 |

---

## 4. 请求参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| id | String | 否 | 无 | 指定岗位主键 |
| ids | String[] | 否 | 无 | 指定岗位主键列表 |
| roleCode | String | 否 | 无 | 指定岗位编码 |
| roleName | String | 否 | 无 | 模糊查询岗位名称 |
| validFlag | Boolean | 否 | 无 | 是否有效 |
| deleteFlag | Boolean | 否 | 无 | 是否删除 |
| unitId | String | 否 | 无 | 指定所属部门 |

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
| result[].id | id | String | 是 | 岗位 id | 可映射为 `value` |
| result[].roleName | roleName | String | 是 | 岗位名称 | 可映射为 `label` |
| result[].roleShortened | roleShortened | String | 是 | 岗位简称 | 可展示 |
| result[].roleCode | roleCode | String | 是 | 岗位编码 | 可用于联动 |
| result[].roleDesc | roleDesc | String | 是 | 岗位描述 | 可展示 |
| result[].displayOrder | displayOrder | Integer/String | 是 | 显示次序 | 可用于排序 |
| result[].unitId | unitId | String | 是 | 部门 id | 可用于按部门联动 |
| result[].validFlag | validFlag | Boolean | 是 | 是否有效 | 过滤条件 |
| result[].deleteFlag | deleteFlag | Boolean | 是 | 是否删除 | 过滤条件 |
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
      "id": "100267",
      "roleName": "和平里邮政分局",
      "roleShortened": null,
      "roleCode": "100267",
      "roleDesc": null,
      "unitId": "100266",
      "displayOrder": "100267",
      "validFlag": true,
      "deleteFlag": false
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

- 岗位下拉框；
- 岗位筛选项；
- 岗位字典；
- 岗位列表。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| label | item.roleName | 字符串兜底 |
| value | item.id | 字符串兜底 |
| code | item.roleCode | 字符串兜底 |
| unitId | item.unitId | 字符串兜底 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            label: item.roleName || '',
            value: item.id || '',
            code: item.roleCode || '',
            unitId: item.unitId || ''
        };
    });
}
```

---

## 10. 性能和联调注意点

1. 建议默认传 `deleteFlag=false`、`validFlag=true`。
2. 可用 `unitId` 查询某部门下岗位。
3. 该接口是字典接口，不返回人员明细。