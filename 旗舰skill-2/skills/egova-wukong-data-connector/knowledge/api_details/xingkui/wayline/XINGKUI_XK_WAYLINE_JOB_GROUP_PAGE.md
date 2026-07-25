# 分页查询
## 1. 标准化基本信息
| 项目 | 内容 |
| --- | --- |
| apiCode | XINGKUI_XK_WAYLINE_JOB_GROUP_PAGE |
| domain | 星揆 |
| bizObject | 航线任务分组 |
| apiName | 分页查询 |
| apiType | page |
| 请求方式 | POST |
| 接口地址 | `/api/xingkui/xk-wayline-job-group/page` |
| 星桥接口路径地址 | 暂无，需自行在星桥上注册 |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 分页表格,列表 |

---

## 2. 接口说明

该接口用于分页查询航线任务分组数据，支持按id、分组名称、上级分组id、排序因子、分组所属工作区id等条件筛选；返回分页结果，适合分页表格或列表组件。

---

## 3. 数据来源

| 数据库 | 数据表 | 备注 |
| --- | --- | --- |
| xingkui | gis_xk_wayline_job_group | 从返回实体 `@Table` 推断 |

---

## 4. 请求参数

| 名称 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- | --- |
| id | String | 否 |  |  | id |
| name | String | 否 |  |  | 分组名称 |
| parentId | Integer | 否 |  |  | 上级分组id |
| orderBy | Integer | 否 |  |  | 排序因子 |
| workspaceId | String | 否 |  |  | 分组所属工作区id |

---

## 5. 请求示例

```json
{
  "id": "",
  "name": "",
  "parentId": 0,
  "orderBy": 0,
  "workspaceId": ""
}
```

---

## 6. 返回字段

- `result` 类型：`PageResult<XkWaylineJobGroup>`
- 标准化响应形态：`array`

| 名称 | 类型 | 是否必须 | 备注 | 参数说明 |
| --- | --- | --- | --- | --- |
| hasError | Boolean | 是 |  | 用于判断接口是否出错true：接口报错，按照报错说明排查传参是否出现问题false：接口正常 |
| result | Object | 是 |  | 返回对象或列表 |
| +id | String | 否 | 数据库字段：`id` | id |
| +name | String | 否 | 数据库字段：`name` | 分组名称 |
| +parentId | Integer | 否 | 数据库字段：`parent_id` | 上级分组id |
| +orderBy | Integer | 否 | 数据库字段：`order_by` | 排序因子 |
| +workspaceId | String | 否 | 数据库字段：`workspace_id` | 分组所属工作区id |
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
      "id": "",
      "name": "",
      "parentId": 0,
      "orderBy": 0,
      "workspaceId": ""
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
| 其他报错 | 需联系后台排查数据 |

---

## 9. 字段转换建议

- `filter(data)` 默认接收外层响应的 `result` 本体；只有现场明确传入完整外层响应包时，才读取 `data.result` 或 `data.totalCount`。
- 分页接口如组件需要总数，需确认悟空是否传入完整外层响应包；仅传 `result` 本体时可能拿不到 `totalCount`。
- 本文件字段主要从 Java 实体/DTO 字段注释推断；落地前需用实际接口返回样例核对字段是否全部返回、是否有动态扩展字段。
- 星桥接口路径当前按规则标记为“暂无，需自行在星桥上注册”。
