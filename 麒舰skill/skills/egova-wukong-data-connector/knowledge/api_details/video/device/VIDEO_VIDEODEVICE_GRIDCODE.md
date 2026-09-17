# 批量修改grid_code
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | VIDEO_VIDEODEVICE_GRIDCODE |
| domain | 视频 |
| bizObject | 视频设备 |
| apiName | 批量修改grid_code |
| apiType | detail |
| 请求方式 | PUT |
| 接口地址 | `/api/video/videoDevice/gridCode` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | boolean |
| 适配组件 | 运维操作,状态提示 |

---

## 2. 接口说明

该接口用于批量同步视频设备表中的 grid_code，根据视频设备经纬度计算所属责任网格并更新；返回布尔值表示操作是否成功，适合后台维护或数据修复场景，不建议直接作为大屏展示数据源。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| video | video_device | 从返回实体和 Service 查询主表推断 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| 无 | / | 否 |  |  | 该接口不需要业务入参 |

---

## 5. 请求示例

```json
{}
```

---

## 6. 返回字段

- `result` 类型：`Boolean`
- 标准化响应形态：`boolean`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Boolean | 是 |  | 操作是否成功 |
| message | String | 是 |  | 当hasError为true时这里展示报错信息 |
| tag | / | 是 |  | 未使用到 |
| totalCount | Integer | 是 |  | 返回数据的总条数 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": false,
  "message": null,
  "tag": null,
  "totalCount": 0
}
```

---

## 8. 报错说明

| message信息 | 说明 |
| --- | --- |
| 其他报错 | 需联系后台排查数据 |

---

## 9. 字段转换建议

- `filter(data)` 默认接收外层响应的 `result` 本体；只有现场明确传入完整外层响应包时，才读取 `data.result` 或 `data.totalCount`。

- 本文件字段主要从 Java 实体/DTO 字段注释推断；落地前需用实际接口返回样例核对字段是否全部返回、是否有动态扩展字段。
- 星桥接口路径当前按规则标记为“暂无，需自行在星桥上注册”。
