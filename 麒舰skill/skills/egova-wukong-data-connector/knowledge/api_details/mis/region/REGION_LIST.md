# 区划列表接口

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REGION_LIST |
| domain | MIS基础资料 |
| bizObject | 区划 |
| apiName | 区划列表接口 |
| apiType | dict |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/region/list` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/区划相关/区划列表接口` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 区划下拉、区划筛选、区域列表、地图区域筛选 |

---

## 2. 接口说明

该接口用于按照查询条件查询所需的区划列表，用于区划展示或筛选条件。

适合：

- 区划下拉框；
- 区县/街道/社区筛选；
- 地图区域筛选；
- 区划字典展示。

不适合：

- 完整区划树；
- 区划案件统计；
- 区划车辆统计。

如需要完整区划树，应使用 `REGION_TREE.md` 对应接口。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_region | 业务库区划表 |

---

## 4. 请求参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| id | String | 否 | 无 | 查询指定主键的区划 |
| ids | String[] | 否 | 无 | 查询指定主键列表的区划 |
| regionCode | String | 否 | 无 | 查询指定区域编码的区划 |
| regionName | String | 否 | 无 | 模糊查询区划名称 |
| regionType | Integer | 否 | 无 | 查询指定级别的区划 |
| parentId | String | 否 | 无 | 查询指定父区划主键的子区划 |
| parentIds | String[] | 否 | 无 | 查询指定父区划主键列表的子区划 |

### regionType 说明

| 值 | 含义 |
|---|---|
| 1 | 市 |
| 2 | 区县 |
| 3 | 街道 |
| 4 | 社区 |
| 5 | 网格 |

返回字段中可能出现 `regionType=0`，表示省级。

---

## 5. 请求示例

```json
{
  "regionType": 2
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果 | 区划字典数据源 |
| result[].id | id | String | 是 | 区划主键 | 可映射为 `value` |
| result[].regionCode | regionCode | String | 是 | 区划编码 | 可展示或联动 |
| result[].longitude | longitude | Double | 是 | 经度 | 地图中心点 lng |
| result[].latitude | latitude | Double | 是 | 纬度 | 地图中心点 lat |
| result[].regionName | regionName | String | 是 | 区划名称 | 可映射为 `label` |
| result[].regionType | regionType | Integer | 是 | 区划类型 | 层级判断 |
| result[].parentId | parentId | String | 是 | 父区划 id | 可用于父子关系 |
| result[].validFlag | validFlag | String | 否 | 有效标识 | 可辅助过滤 |
| result[].children | children | Object[] | 否 | 子区划 | 如返回则可用于树 |
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
      "id": "0",
      "regionCode": "",
      "longitude": 0.0,
      "latitude": 0.0,
      "regionName": "温州市",
      "regionType": 1,
      "parentId": "-1",
      "validFlag": "1",
      "children": []
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

- 区划下拉框；
- 区划筛选；
- 区划字典；
- 区域列表。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| label | item.regionName | 字符串兜底 |
| value | item.id | 字符串兜底 |
| parentId | item.parentId | 字符串兜底 |
| regionType | item.regionType | Number 转换 |
| lng | item.longitude | Number 转换 |
| lat | item.latitude | Number 转换 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            label: item.regionName || '',
            value: item.id || '',
            parentId: item.parentId || '',
            regionCode: item.regionCode || '',
            regionType: Number(item.regionType || 0),
            lng: Number(item.longitude || 0),
            lat: Number(item.latitude || 0),
            children: Array.isArray(item.children) ? item.children : []
        };
    });
}
```

---

## 10. 性能和联调注意点

1. 查询区县通常传 `regionType=2`。
2. 查询某个父区划下级通常传 `parentId`。
3. 如果需要完整树，优先使用 `REGION_TREE.md`。
4. 返回中的 `children` 不一定包含完整树结构，应以实际返回为准。