# 人员类型分组

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | PATROL_GROUP_TYPE |
| domain | MIS人员 |
| bizObject | 监督员 |
| apiName | 人员类型分组 |
| apiType | group |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/patrol/group` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/人员类型分组` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 饼图、柱状图、人员类型统计、在线统计、TopN 列表 |

---

## 2. 接口说明

该接口用于统计监督员中每一种人员类型的人员总数。

可通过参数配置统计每一种人员类型的在线人数：

- `groupOnlineFlag=true` 时，返回 `online` 字段；
- 不传或为 false 时，不统计在线人数。

支持通过以下条件筛选：

- 人员主键；
- 卡号；
- 人员编码；
- 人员名称；
- 人员类型；
- 区划；
- 部门；
- 在线/离线状态。

支持区划深钻和部门深钻。

适合：

- 人员类型分布饼图；
- 人员类型柱状图；
- 各类型人员数量排行；
- 各类型在线人员数量统计。

不适合：

- 人员明细列表；
- 分页表格；
- 人员详情。

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
| groupOnlineFlag | Boolean | 否 | false | 是否统计人员在线数 |

---

## 5. 请求示例

```json
{
  "state": true,
  "groupOnlineFlag": true
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 分组统计结果 | 图表数据源 |
| result[].name | name | String | 是 | 人员类型 id | 可映射为 `id` |
| result[].text | text | String | 是 | 人员类型名称 | 可映射为 `name` / `label` |
| result[].value | value | Integer | 是 | 人员总数 | 可映射为 `value` |
| result[].online | online | Integer | 否 | 人员在线数，`groupOnlineFlag=true` 时返回 | 可映射为在线数 |
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
      "name": "1",
      "text": "普通监督员",
      "value": 214,
      "online": 214
    },
    {
      "name": "11",
      "text": "处置通人员",
      "value": 36,
      "online": 36
    },
    {
      "name": "8",
      "text": "管理干部",
      "value": 8,
      "online": 8
    }
  ],
  "message": null,
  "tag": null,
  "totalCount": 3
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

- 饼图；
- 柱状图；
- 人员类型统计；
- 在线统计图；
- TopN 列表。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.name | 字符串兜底 |
| name | item.text | 字符串兜底 |
| value | item.value | Number 转换 |
| online | item.online | Number 转换 |

### 推荐过滤脚本：人员类型数量，data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            id: item.name || '',
            name: item.text || '',
            value: Number(item.value || 0),
            online: Number(item.online || 0)
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

### 推荐过滤脚本：在线率

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        var total = Number(item.value || 0);
        var online = Number(item.online || 0);

        return {
            id: item.name || '',
            name: item.text || '',
            value: total,
            online: online,
            onlineRate: total > 0 ? Number((online * 100 / total).toFixed(2)) : 0
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

---

## 10. 性能和联调注意点

1. `groupOnlineFlag=true` 时才会返回 `online` 字段。
2. 如果仅需要人员类型总数，不建议开启在线统计。
3. 需要按区域或部门过滤时，可传 `regionId`、`unitId`。
4. 需要包含下级区划或下级部门时，可开启 `regionExtendFlag`、`unitExtendFlag`。