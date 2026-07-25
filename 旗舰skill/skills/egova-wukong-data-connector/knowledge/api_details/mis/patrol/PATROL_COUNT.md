# 条件查询人员总数

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | PATROL_COUNT |
| domain | MIS人员 |
| bizObject | 监督员 |
| apiName | 条件查询人员总数 |
| apiType | count |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/patrol/count` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/条件查询人员总数` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | number |
| 适配组件 | 指标卡、总数卡片、分页总数辅助 |

---

## 2. 接口说明

该接口用于查询人员数量。

查询逻辑与人员分页接口和人员列表查询相同，主要用于：

- 悟空分页组件获取条件查询后的数据总数；
- 指标卡展示人员总数；
- 根据筛选条件统计人员数量。

该接口与人员分页接口配套使用时，请求参数需要与分页接口请求体中的 `condition` 字段保持一致。

适合：

- 指标卡；
- 总数卡片；
- 分页组件总数辅助；
- 条件筛选人员数量统计。

不适合：

- 人员明细列表；
- 地图点位；
- 人员详情；
- 类型/区划/部门分组统计。

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
| unitId | String | 否 | 无 | 指定所属部门 |
| unitExtendFlag | Boolean | 否 | 无 | 是否支持部门下钻 |
| regionIdList | String[] | 否 | 无 | 指定所属区划列表 |
| state | Boolean | 否 | 无 | 是否在线 |

---

## 5. 请求示例

```json
{
  "regionId": "0"
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Integer | 是 | 人员数量 | 指标卡 value |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 通常为 1 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": 95,
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

- 指标卡；
- 总数卡片；
- 分页组件总数辅助。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| title | 固定值 | 例如“人员总数” |
| value | data | Number 转换 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    return {
        title: '人员总数',
        value: Number(data || 0)
    };
}
```

### 兼容完整响应包的过滤脚本

```javascript
function filter(data) {
    if (!data || data.hasError === true) {
        return {
            title: '人员总数',
            value: 0
        };
    }

    return {
        title: '人员总数',
        value: Number(data.result || 0)
    };
}
```

---

## 10. 性能和联调注意点

1. 该接口只返回数量，不返回人员明细。
2. 与分页接口配套时，请求参数必须和分页接口 `condition` 保持一致。
3. 如果需要按类型、区划、部门分组统计，应使用对应分组接口。