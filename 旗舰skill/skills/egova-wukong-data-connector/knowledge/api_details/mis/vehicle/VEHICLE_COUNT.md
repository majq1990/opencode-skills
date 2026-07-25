# 条件查询车辆总数

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | VEHICLE_COUNT |
| domain | 城管车辆 |
| bizObject | 车辆 |
| apiName | 条件查询车辆总数 |
| apiType | count |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/vehicle/count` |
| 星桥接口路径地址 | `API平台/悟能接口/车辆相关/条件查询车辆总数` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | number |
| 适配组件 | 指标卡、总数卡片 |

---

## 2. 接口说明

该接口用于按条件查询车辆数量。

常见用途：

- 为悟空指标卡提供车辆总数；
- 与车辆分页查询接口配套使用，用于获取分页总数；
- 根据条件筛选后返回车辆总量。

如果与分页接口配套使用，该接口的传参需要与分页接口中 `condition` 字段保持一致。

适合：

- 指标卡；
- 总数卡片；
- 分页表格总数辅助。

不适合：

- 分类统计；
- 地图打点；
- 车辆明细列表；
- 详情页。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_vehicle | 业务库车辆表 |
| cgdb | tc_region | 业务库区划表 |
| cgdb | to_vehicle_pos | 业务库车辆最新点位表 |
| cgdb | tc_dic_vehicle_type | 业务库城管车辆类型表 |
| cgdb | tc_vehicle_unit | 业务库车辆单位表 |

---

## 4. 请求参数

| 参数路径 | 参数名 | 类型 | 是否必须 | 默认值 | 备注 | 参数说明 |
|---|---|---|---|---|---|---|
| id | id | String | 否 | 无 |  | 车辆id |
| ids | ids | String[] | 否 | 无 | `["xx","xx"]` | 多个车辆id |
| vehicleNum | vehicleNum | String | 否 | 无 | 模糊查询 | 车牌号 |
| vehicleUsage | vehicleUsage | String | 否 | 无 | 模糊查询 | 车辆用途 |
| vehicleBrand | vehicleBrand | String | 否 | 无 | 模糊查询 | 车辆品牌 |
| regionId | regionId | String | 否 | 无 |  | 区域id |
| unitId | unitId | String | 否 | 无 |  | 部门id |
| regionIdList | regionIdList | String[] | 否 | 无 | `["xx","xx"]` | 多个区域id |
| unitIdList | unitIdList | String[] | 否 | 无 | `["xx","xx"]` | 多个部门id |
| startWorkTime | startWorkTime | String | 否 | 无 |  | 开始工作时间 |
| endWorkTime | endWorkTime | String | 否 | 无 |  | 结束工作时间 |
| vehicleOwner | vehicleOwner | String | 否 | 无 |  | 车辆所属者/司机 |
| onlineFlag | onlineFlag | String | 否 | 无 |  | 车辆状态 |
| telPhoneOwner | telPhoneOwner | String | 否 | 无 |  | 电话 |
| vehicleTypeId | vehicleTypeId | String | 否 | 无 |  | 车辆类型 |
| vehicleTypeIds | vehicleTypeIds | String[] | 否 | 无 | `["xx","xx"]` | 多个车辆类型 |
| deleteFlag | deleteFlag | String | 否 | 无 |  | 是否删除 |
| validFlag | validFlag | String | 否 | 无 |  | 是否有效 |
| regionExtendFlag | regionExtendFlag | String | 否 | 无 |  | 是否统计下级区划 |
| unitExtendFlag | unitExtendFlag | String | 否 | 无 |  | 是否统计下级部门 |

---

## 5. 请求示例

```json
{
  "id": "2",
  "ids": ["2", "3"],
  "vehicleNum": "",
  "vehicleUsage": "",
  "vehicleBrand": "",
  "regionId": "",
  "unitId": "",
  "regionIdList": [],
  "unitIdList": [],
  "startWorkTime": "",
  "endWorkTime": "",
  "vehicleOwner": "",
  "onlineFlag": "",
  "telPhoneOwner": "",
  "vehicleTypeId": "",
  "vehicleTypeIds": [],
  "deleteFlag": "",
  "validFlag": "",
  "regionExtendFlag": "",
  "unitExtendFlag": ""
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错；true 表示报错，false 表示正常 | 用于异常判断 |
| result | result | Integer | 是 | 车辆数量 | 可映射为指标卡 `value` |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 通常为 1 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": 1,
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
| title | 固定值 | 例如“车辆总数” |
| value | data | Number 转换 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    return {
        title: '车辆总数',
        value: Number(data || 0)
    };
}
```

### 兼容完整响应包的过滤脚本

```javascript
function filter(data) {
    if (!data || data.hasError === true) {
        return {
            title: '车辆总数',
            value: 0
        };
    }

    return {
        title: '车辆总数',
        value: Number(data.result || 0)
    };
}
```

---

## 10. 性能和联调注意点

1. 该接口只返回数量，不返回明细。
2. 如果和分页接口配套，参数必须和分页接口的 `condition` 保持一致。
3. 如果统计口径包含区域或部门下级，应确认 `regionExtendFlag` / `unitExtendFlag`。
4. 如果用于指标卡，标题通常由组件静态结构或 filter 固定输出。