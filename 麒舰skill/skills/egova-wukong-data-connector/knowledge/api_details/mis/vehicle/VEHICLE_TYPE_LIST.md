# 车辆类型列表查询

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | VEHICLE_TYPE_LIST |
| domain | 城管车辆 |
| bizObject | 车辆类型 |
| apiName | 车辆类型列表查询 |
| apiType | dict |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/vehicle-type/list` |
| 星桥接口路径地址 | `待确认` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 下拉筛选、筛选项、字典列表 |

---

## 2. 接口说明

该接口用于按查询条件查询车辆类型，用于车辆类型展示或筛选条件。

适合：

- 车辆类型下拉框；
- 筛选项；
- 字典选项；
- 车辆类型枚举展示。

不适合：

- 车辆数量统计；
- 车辆明细列表；
- 地图打点；
- 车辆详情。

> 注意：当前原始文档未明确提供星桥接口路径地址，因此 `xingqiaoPath` 暂标为 `待确认`。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_dic_vehicle_type | 业务库车辆类型表 |

---

## 4. 请求参数

| 参数路径 | 参数名 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
|---|---|---|---|---|---|---|
| id | id | String | 否 | 无 |  | 指定车辆类型主键 |
| ids | ids | String[] | 否 | 无 |  | 指定车辆类型主键列表 |

---

## 5. 请求示例

```json
{
  "id": "1"
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错；true 表示报错，false 表示正常 | 用于异常判断 |
| result | result | Object[] | 是 | 返回结果数组 | 下拉选项数据源 |
| result[].id | id | String | 是 | 车辆类型id | 可映射为 `value` |
| result[].vehicleTypeName | vehicleTypeName | String | 是 | 车辆类型名称 | 可映射为 `label` |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 可辅助统计 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "id": "1",
      "vehicleTypeName": "车辆类型一"
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

- 下拉筛选；
- 多选筛选；
- 字典列表；
- 查询条件配置。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| label | item.vehicleTypeName | 字符串兜底 |
| value | item.id | 字符串兜底 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        return {
            label: item.vehicleTypeName || '',
            value: item.id || ''
        };
    });
}
```

### 兼容完整响应包的过滤脚本

```javascript
function filter(data) {
    if (!data || data.hasError === true) {
        return [];
    }

    var list = data.result;
    if (!Array.isArray(list)) {
        return [];
    }

    return list.map(function (item) {
        return {
            label: item.vehicleTypeName || '',
            value: item.id || ''
        };
    });
}
```

---

## 10. 性能和联调注意点

1. 该接口是字典接口，不返回车辆数量或车辆明细。
2. 如果用于筛选项，应确认组件目标字段是 `label/value` 还是 `text/value`。
3. 当前星桥接口路径地址待确认，现场需要补充。