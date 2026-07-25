# 生成区划树接口

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REGION_TREE |
| domain | MIS基础资料 |
| bizObject | 区划 |
| apiName | 生成区划树接口 |
| apiType | tree |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/region/tree` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/区划相关/生成区划树接口` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 区划树、级联选择、区域筛选树、地图区域树 |

---

## 2. 接口说明

该接口用于生成一棵完整的区划树。

适合：

- 区划树组件；
- 级联选择器；
- 地图区域树；
- 区域筛选树；
- 左侧区划树 + 右侧业务数据联动。

不适合：

- 区划统计；
- 案件统计；
- 车辆统计；
- 分页列表。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_region | 业务库区划表 |

---

## 4. 请求参数

暂无传参。

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
| result | result | Object[] | 是 | 返回结果 | 区划树数据源 |
| result[].id | id | String | 是 | 区划主键 | 可映射为 `id` / `value` |
| result[].regionCode | regionCode | String | 是 | 区划编码 | 可展示或联动 |
| result[].longitude | longitude | Double | 是 | 经度 | 地图中心点 lng |
| result[].latitude | latitude | Double | 是 | 纬度 | 地图中心点 lat |
| result[].regionName | regionName | String | 是 | 区划名称 | 可映射为 `label` |
| result[].regionType | regionType | Integer | 是 | 区划类型 | 层级判断 |
| result[].parentId | parentId | String | 是 | 父区划 id | 父子关系 |
| result[].validFlag | validFlag | String | 否 | 有效标识 | 可辅助过滤 |
| result[].children | children | Object[] | 是 | 子区划列表；子区划字段与父区划一致 | 树节点 children |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 辅助统计 |

### regionType 说明

| 值 | 含义 |
|---|---|
| 0 | 省 |
| 1 | 市 |
| 2 | 区县 |
| 3 | 街道 |
| 4 | 社区 |
| 5 | 网格 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "id": "0",
      "regionCode": "",
      "longitude": 0,
      "latitude": 0,
      "regionName": "温州市",
      "regionType": 1,
      "parentId": "-1",
      "validFlag": "1",
      "children": [
        {
          "id": "1",
          "regionCode": "330302",
          "longitude": 120.592180578154,
          "latitude": 28.0645365021072,
          "regionName": "鹿城区",
          "regionType": 2,
          "parentId": "0",
          "validFlag": "1",
          "children": []
        }
      ]
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
| 其他报错 | 需联系后台排查数据 | 查看后台日志 |

---

## 9. 适配建议

### 适合组件

- 区划树；
- 级联选择器；
- 地图区域树；
- 区域筛选树。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| id | item.id | 字符串兜底 |
| value | item.id | 字符串兜底 |
| label | item.regionName | 字符串兜底 |
| parentId | item.parentId | 字符串兜底 |
| regionType | item.regionType | Number 转换 |
| children | item.children | 递归处理 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    function convert(list) {
        if (!Array.isArray(list)) {
            return [];
        }

        return list.map(function (item) {
            return {
                id: item.id || '',
                value: item.id || '',
                label: item.regionName || '',
                regionCode: item.regionCode || '',
                regionType: Number(item.regionType || 0),
                parentId: item.parentId || '',
                lng: Number(item.longitude || 0),
                lat: Number(item.latitude || 0),
                children: convert(item.children)
            };
        });
    }

    return convert(data);
}
```

---

## 10. 性能和联调注意点

1. 该接口返回完整区划树，层级较多时数据量较大。
2. 如果只需要某一级区划列表，优先使用 `REGION_LIST.md`。
3. 如果悟空树组件字段要求是 `name` 而不是 `label`，需要在 filter 中调整。
4. 该接口暂无传参，无法直接按区域过滤。