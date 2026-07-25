# 部件树查询
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | MIXTURE_GIS_PART_TREE |
| domain | 资源混合 |
| bizObject | 部件树 |
| apiName | 部件树查询 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/mixture/partTree` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| v22状态 | 当前源码中该接口入口未启用，暂不作为悟能可用接口推荐 |
| 适配组件 | 树组件,统计列表,地图图层筛选 |

---

## 2. 接口说明

v22 当前源码中该接口入口未启用，以下内容仅作为历史/现场自有接口核对参考；如现场仍需使用，需先确认后端已恢复对应接口入口。

该接口用于查询 GIS 部件树数据，通过 mixture 模块转发 GIS 部件树查询能力；支持按小类名称、空间类型、排序字段、树结构返回标识和专题图id等条件筛选，适合部件分类树或地图图层筛选组件。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| GIS服务 | 外部部件树接口 | 由 mixture 模块转发 GIS 部件树查询能力，返回结构需结合 GIS 配置核对 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| subname | String | 否 |  |  | 小类名称模糊查询 |
| geomtype | Integer | 否 |  |  | 空间类型，默认0；1点、2线、3面 |
| orderfield | String | 否 |  |  | 排序字段 |
| returntree | Boolean | 否 |  |  | 返回结果是否以大小类层级树形式返回 |
| callback | String | 否 |  |  | 回调函数 |
| mapid | Integer | 否 |  |  | 专题图id号，默认-1 |

---

## 5. 请求示例

```json
{
  "subname": "",
  "geomtype": 0,
  "orderfield": "",
  "returntree": false,
  "callback": "",
  "mapid": 0
}
```

---

## 6. 返回字段

- `result` 类型：`List<PartTreeModel>`
- 标准化响应形态：`array`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object[] | 是 |  | 返回列表 |
| +geomType | Integer | 否 |  | 空间类型 |
| +mainTypeName | String | 否 |  | 大类名称 |
| +mainUniqueCode | String | 否 |  | 大类唯一编码 |
| +nums | Integer | 否 |  | 数量 |
| +phyLayerID | Integer | 否 |  | 物理图层id |
| +phyLayerName | String | 否 |  | 物理图层名称 |
| +subTypeName | String | 否 |  | 小类名称 |
| +subUniqueCode | String | 否 |  | 小类唯一编码 |
| message | String | 是 |  | 当hasError为true时这里展示报错信息 |
| tag | / | 是 |  | 未使用到 |
| totalCount | Integer | 是 |  | 返回数据的总条数 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "geomType": 0,
      "mainTypeName": "",
      "mainUniqueCode": "",
      "nums": 0,
      "phyLayerID": 0,
      "phyLayerName": "",
      "subTypeName": "",
      "subUniqueCode": ""
    }
  ],
  "message": null,
  "tag": null,
  "totalCount": 0
}
```

---

## 8. 报错说明

| message信息 | 说明 |
| --- | --- |
| 其他报错 | 需联系后台或 GIS 服务排查数据 |

---

## 9. 字段转换建议

- v22 当前源码中该接口入口未启用，默认不要在数据源推荐中使用；只有现场确认已恢复接口时再按本文字段核对。
- `filter(data)` 默认接收外层响应的 `result` 本体；只有现场明确传入完整外层响应包时，才读取 `data.result` 或 `data.totalCount`。
- 本文件字段主要从 Java Condition/Model 字段和方法注释推断；落地前需用实际接口返回样例核对字段是否全部返回、是否有动态扩展字段。
- 星桥接口路径当前按规则标记为“暂无，需自行在星桥上注册”。
