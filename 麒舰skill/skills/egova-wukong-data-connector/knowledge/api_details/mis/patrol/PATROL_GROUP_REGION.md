# 人员区划分组

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | PATROL_GROUP_REGION |
| domain | MIS人员 |
| bizObject | 监督员 |
| apiName | 人员区划分组 |
| apiType | group |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/patrol/group?@state=region` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/人员区划分组` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 柱状图、排行列表、区划人员统计、区域指标卡 |

---

## 2. 接口说明

该接口用于统计指定查询条件下，每个区划的人员总数。

支持区划深钻：

- 统计某个区划人员总数时，如果人员属于该区划下属区划，也可以认为该人员属于当前区划；
- 由 `regionExtendFlag` 控制。

支持通过以下条件筛选：

- 人员名称；
- 人员类型；
- 在线/离线；
- 部门；
- 区划。

适合：

- 按区划统计人员数；
- 各区人员数量排行；
- 各街道人员分布；
- 区划人员柱状图。

不适合：

- 人员明细列表；
- 区划树形统计；
- 人员类型统计；
- 部门统计。

> 注意：该接口是按区划分组，要展示的区划由 `regionCondition` 指定，因此使用该接口必须指定区划查询条件。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_patrol | 业务库监督员表 |
| cgdb | tc_human | 业务库人员表 |
| cgdb | tc_patrol_type | 业务库监督员类型字典表 |
| cgdb | tc_region | 业务库区划表 |
| cgdb | tc_patrol_state | 业务库监督员状态表 |

---

## 4. 请求参数

### 4.1 人员筛选参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| id | String | 否 | 无 | 人员主键 |
| ids | String[] | 否 | 无 | 人员主键列表 |
| cardId | String | 否 | 无 | 卡号 |
| patrolCode | String | 否 | 无 | 人员编码 |
| patrolName | String | 否 | 无 | 模糊查询人员名称 |
| patrolTypeId | String | 否 | 无 | 人员类型 |
| regionId | String | 否 | 无 | 指定所属区划 |
| regionExtendFlag | Boolean | 否 | false | 是否支持区划下钻 |
| regionIdList | String[] | 否 | 无 | 指定所属区划列表 |
| unitId | String | 否 | 无 | 指定所属部门 |
| unitExtendFlag | Boolean | 否 | 无 | 是否支持部门下钻 |
| state | Boolean | 否 | 无 | 是否在线 |

### 4.2 regionCondition 区划查询条件

| 参数路径 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| regionCondition | Object | 是 | 区划条件对象 |
| regionCondition.id | String | 否 | 指定区划主键 |
| regionCondition.ids | String[] | 否 | 指定区划主键列表 |
| regionCondition.regionType | Integer | 否 | 查询指定级别的区划 |
| regionCondition.parentId | String | 否 | 指定查询父区划下属子区划 |
| regionCondition.parentIds | String[] | 否 | 指定查询父区划列表下属子区划 |

### 4.3 regionType 说明

| 值 | 含义 |
|---|---|
| 1 | 市 |
| 2 | 区县 |
| 3 | 街道 |
| 4 | 社区 |
| 5 | 网格 |

---

## 5. 请求示例

```json
{
  "regionCondition": {
    "regionType": 2
  },
  "regionExtendFlag": true
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 区划分组结果 | 图表数据源 |
| result[].name | name | String | 是 | 区划 id | 可映射为 `id` |
| result[].text | text | String | 是 | 区划名称 | 可映射为 `name` / `label` |
| result[].value | value | Integer | 是 | 人员总数 | 可映射为 `value` |
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
      "name": "8",
      "text": "瑞安市",
      "value": 181
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
| 其他报错 | 需联系后台排查数据 | 检查 `regionCondition`、筛选条件、数据权限、后台日志 |

---

## 9. 适配建议

### 适合组件

- 柱状图；
- 横向柱状图；
- 区划排行；
- 区域人员统计；
- TopN 列表。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.name | 字符串兜底 |
| name | item.text | 字符串兜底 |
| value | item.value | Number 转换 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            id: item.name || '',
            name: item.text || '',
            value: Number(item.value || 0)
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

---

## 10. 性能和联调注意点

1. 必须传 `regionCondition` 指定要展示的区划范围。
2. 统计下级区划归属时，开启 `regionExtendFlag`。
3. 如果只统计指定区划本身，关闭 `regionExtendFlag`。
4. 展示区划应尽量保持同一级别，例如都为区县或都为街道。
5. 如果需要树形结构，应使用人员区划分组树形接口。