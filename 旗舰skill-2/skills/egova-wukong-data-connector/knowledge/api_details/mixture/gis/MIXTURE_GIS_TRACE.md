# 轨迹查询
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | MIXTURE_GIS_TRACE |
| domain | 资源混合 |
| bizObject | 轨迹 |
| apiName | 轨迹查询 |
| apiType | list |
| 请求方式 | POST |
| 接口地址 | `/api/mixture/trace` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| v22状态 | 当前源码中该接口入口未启用，暂不作为悟能可用接口推荐 |
| 适配组件 | 地图轨迹,轨迹列表 |

---

## 2. 接口说明

v22 当前源码中该接口入口未启用，以下内容仅作为历史/现场自有接口核对参考；如现场仍需使用，需先确认后端已恢复对应接口入口。

该接口用于查询监督员或车辆轨迹点数据，通过 mixture 模块转发 GIS 轨迹查询能力；支持按对象id、请求类型、时间范围、轨迹字段和轨迹数据来源等条件筛选，适合地图轨迹或轨迹列表组件。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| GIS服务 | 外部轨迹接口 | 由 mixture 模块转发 GIS 轨迹查询能力，接口问题需结合 GIS 服务配置排查 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| objectID | String | 否 |  |  | 对象id |
| requestType | Integer | 否 |  |  | 请求类型，默认1；1为监督员，2为车辆 |
| beginDate | String | 否 |  |  | 开始时间，格式为 yyyy-MM-dd HH:mm:ss |
| endDate | String | 否 |  |  | 截至时间 |
| fixTrace | Boolean | 否 |  |  | 是否优化轨迹 |
| xField | String | 否 |  |  | 轨迹点数据的x坐标字段 |
| yField | String | 否 |  |  | 轨迹点数据的y坐标字段 |
| idField | String | 否 |  |  | 轨迹点数据的所属id字段 |
| speedField | String | 否 |  |  | 轨迹点数据的速度字段 |
| timeField | String | 否 |  |  | 轨迹点上报时间字段 |
| tableName | String | 否 |  |  | 轨迹数据存储表 |
| stayAggre | Boolean | 否 |  |  | 是否开启逗留点聚合 |
| montionlessSpan | String | 否 |  |  | 逗留阈值，由逗留半径、逗留累计时间阈值、逗留时间内可忽略点个数组成 |
| filterTrace | Boolean | 否 |  |  | 是否开启卡尔曼滤波 |
| resourcetype | Integer | 否 |  |  | GPS数据存储类型，1数据库存储、2 Redis存储、3大数据存储、4 TDengine |
| rawData | Boolean | 否 |  |  | 返回结果是否包含轨迹精度超过阈值的数据 |
| fields | String | 否 |  |  | 要查询的字段集合 |
| callback | String | 否 |  |  | 回调函数 |
| rectificationType | Integer | 否 |  |  | 是否进行百度纠偏，0不纠偏，1纠偏 |
| onlyShowgrid | Integer | 否 |  |  | 是否只加载责任网格轨迹，0不加载，1加载 |

---

## 5. 请求示例

```json
{
  "objectID": "",
  "requestType": 0,
  "beginDate": "",
  "endDate": "",
  "fixTrace": false,
  "xField": "",
  "yField": "",
  "idField": "",
  "speedField": "",
  "timeField": "",
  "tableName": "",
  "stayAggre": false
}
```

---

## 6. 返回字段

- `result` 类型：`List<TraceModel>`
- 标准化响应形态：`array`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object[] | 是 |  | 返回列表 |
| +accuracy | Double | 否 |  | 轨迹精度 |
| +attributes | Object | 否 |  | 扩展属性 |
| +pointX | Double | 否 |  | X坐标 |
| +pointY | Double | 否 |  | Y坐标 |
| +speed | Double | 否 |  | 速度 |
| +stateTime | LocalDateTime | 否 |  | 状态时间 |
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
      "accuracy": 0,
      "attributes": {},
      "pointX": 0,
      "pointY": 0,
      "speed": 0,
      "stateTime": ""
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
