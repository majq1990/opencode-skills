# 车辆详情查询

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | VEHICLE_INFO |
| domain | 城管车辆 |
| bizObject | 车辆 |
| apiName | 车辆详情查询 |
| apiType | detail |
| 请求方式 | GET |
| 接口地址 | `/api/cgdb/vehicle/info` |
| 星桥接口路径地址 | `API平台/悟能接口/车辆相关/车辆详情查询` |
| 数据提交方式 | query/form，以实际网关配置为准 |
| 响应主路径 | `result` |
| 响应形态 | object |
| 适配组件 | 详情面板、详情弹窗、车辆信息卡片 |

---

## 2. 接口说明

该接口用于根据车辆 id 查询单个车辆详情。

适合：

- 车辆详情弹窗；
- 车辆信息卡片；
- 地图点位点击后的详情展示；
- 表格点击详情。

不适合：

- 列表展示；
- 分页表格；
- 车辆数量统计；
- 图表分组统计。

> 注意：该接口必须确认车辆 id 来源。通常来自车辆列表、车辆分页、车辆简要列表或地图点位。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdb | tc_vehicle | 业务库车辆表 |
| cgdb | tc_region | 业务库区划表 |
| cgdb | to_vehicle_pos | 业务库车辆最新点位表 |
| cgdb | tc_dic_vehicle_type | 业务库城管车辆类型表 |
| cgdb | tc_vehicle_unit | 业务库车辆单位表 |
| cgdb | tc_vehicle_human_rel | 业务库车辆-人员中间表 |
| cgdb | tc_vehicle_human | 业务库车辆人员表 |

---

## 4. 请求参数

| 参数路径 | 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|---|
| id | id | String | 是 | 无 | 车辆id |

---

## 5. 请求示例

```http
GET /api/cgdb/vehicle/info?id=2
```

或按平台配置传参：

```json
{
  "id": "2"
}
```

---

## 6. 返回字段

车辆详情返回字段与车辆列表单条数据结构基本一致。

### 6.1 顶层字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object | 是 | 车辆详情对象 | 详情数据源 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 通常忽略 |

### 6.2 车辆详情 result

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| result.id | id | String | 是 | 车辆id | id |
| result.unitId | unitId | String | 是 | 部门id | 部门联动 |
| result.vehicleNum | vehicleNum | String | 是 | 车牌号 | 标题 |
| result.simCardNum | simCardNum | String | 是 | sim号 | 设备标识 |
| result.vehicleUsage | vehicleUsage | String | 是 | 车辆用途 | 详情项 |
| result.vehicleBrand | vehicleBrand | String | 是 | 车辆品牌 | 详情项 |
| result.vehicleColor | vehicleColor | String | 是 | 车辆颜色 | 详情项 |
| result.regionId | regionId | String | 是 | 区域id | 区域联动 |
| result.startWorkTime | startWorkTime | String | 是 | 开始工作时间 | 详情项 |
| result.endWorkTime | endWorkTime | String | 是 | 结束工作时间 | 详情项 |
| result.vehicleOwner | vehicleOwner | String | 是 | 车辆所有者/司机 | 详情项 |
| result.telPhoneOwner | telPhoneOwner | String | 是 | 电话 | 详情项 |
| result.vehicleTypeId | vehicleTypeId | String | 是 | 车辆类型id | 类型联动 |
| result.onlineFlag | onlineFlag | Boolean | 是 | 车辆状态 | 在线/离线 |
| result.deleteFlag | deleteFlag | Boolean | 是 | 是否删除 | 通常不展示 |
| result.validFlag | validFlag | Boolean | 是 | 是否有效 | 通常不展示 |
| result.vehicleRemarks | vehicleRemarks | String | 是 | 车辆备注 | 详情项 |
| result.vehicleTypeName | vehicleTypeName | String | 是 | 车辆类型名称 | 详情项 |
| result.address | address | String | 是 | 地址 | 详情项 |
| result.speed | speed | Double | 是 | 车速 | 详情项 |
| result.todayCourse | todayCourse | String | 是 | 里程数 | 详情项 |
| result.consumption | consumption | String | 是 | 油耗 | 详情项 |
| result.recordTime | recordTime | String | 是 | 记录时间 | 详情项 |
| result.longitude | longitude | Double | 是 | 经度 | 地图点位 |
| result.latitude | latitude | Double | 是 | 纬度 | 地图点位 |
| result.vehiclePosList | vehiclePosList | Object[] | 是 | 车辆点位列表 | 详情/轨迹 |
| result.vehicleType | vehicleType | Object | 是 | 车辆类型对象 | 详情 |
| result.region | region | Object | 是 | 区域对象 | 详情 |
| result.vehicleUnit | vehicleUnit | Object | 是 | 车辆单位对象 | 详情 |
| result.parentRegionList | parentRegionList | Object[] | 否 | 父区域列表 | 扩展详情 |
| result.parentUnitList | parentUnitList | Object[] | 否 | 父单位列表 | 扩展详情 |
| result.vehicleHumanList | vehicleHumanList | Object[] | 否 | 车辆人员 | 关联人员 |
| result.attachments | attachments | Object[] | 是 | 附件 | 图片/附件 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": {
    "id": "2",
    "unitId": "100540",
    "vehicleNum": "鄂A77H47",
    "simCardNum": "202104301115",
    "vehicleUsage": null,
    "vehicleBrand": "山西汽车",
    "vehicleColor": "绿色",
    "regionId": "1",
    "vehicleOwner": "欧超航",
    "telPhoneOwner": "15137100888",
    "vehicleTypeId": "5",
    "onlineFlag": false,
    "validFlag": true,
    "vehicleTypeName": "垃圾车",
    "speed": 20.08,
    "recordTime": "2021-06-07 13:37:30",
    "longitude": 12738779,
    "latitude": 3542300.5
  },
  "message": null,
  "tag": null,
  "totalCount": 1
}
```

---

## 8. 报错说明

| message | 说明 | 处理建议 |
|---|---|---|
| 其他报错 | 需联系后台排查数据 | 检查 id 是否存在、数据权限、后台日志 |

---

## 9. 适配建议

### 适合组件

- 详情弹窗；
- 详情卡片；
- 地图点位详情；
- 表格行点击详情。

### 字段映射建议：详情卡片

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| title | data.vehicleNum | 字符串兜底 |
| items[].label | 固定文本 | 详情项名称 |
| items[].value | data.xxx | 字段兜底 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!data) {
        return {
            title: '',
            items: []
        };
    }

    return {
        title: data.vehicleNum || '',
        items: [
            { label: '车辆类型', value: data.vehicleTypeName || '' },
            { label: '车辆品牌', value: data.vehicleBrand || '' },
            { label: '车辆颜色', value: data.vehicleColor || '' },
            { label: '车辆用途', value: data.vehicleUsage || '' },
            { label: '车辆所有者', value: data.vehicleOwner || '' },
            { label: '联系电话', value: data.telPhoneOwner || '' },
            { label: '所属部门', value: data.vehicleUnit && data.vehicleUnit.unitName || '' },
            { label: '所属区域', value: data.region && data.region.regionName || '' },
            { label: '车辆状态', value: data.onlineFlag === true ? '在线' : '离线' },
            { label: '记录时间', value: data.recordTime || '' }
        ]
    };
}
```

### 兼容完整响应包的过滤脚本

```javascript
function filter(data) {
    if (!data || data.hasError === true || !data.result) {
        return {
            title: '',
            items: []
        };
    }

    var item = data.result;

    return {
        title: item.vehicleNum || '',
        items: [
            { label: '车辆类型', value: item.vehicleTypeName || '' },
            { label: '车辆品牌', value: item.vehicleBrand || '' },
            { label: '车辆颜色', value: item.vehicleColor || '' },
            { label: '车辆用途', value: item.vehicleUsage || '' },
            { label: '车辆所有者', value: item.vehicleOwner || '' },
            { label: '联系电话', value: item.telPhoneOwner || '' },
            { label: '所属部门', value: item.vehicleUnit && item.vehicleUnit.unitName || '' },
            { label: '所属区域', value: item.region && item.region.regionName || '' },
            { label: '车辆状态', value: item.onlineFlag === true ? '在线' : '离线' },
            { label: '记录时间', value: item.recordTime || '' }
        ]
    };
}
```

---

## 10. 性能和联调注意点

1. 必须确认车辆 id 来源。
2. 地图点位点击详情时，id 可来自车辆简要列表接口。
3. 表格行详情时，id 可来自车辆列表或分页接口。
4. 如果详情组件需要展示关联人员，需要确认 `vehicleHumanList` 是否返回。
5. 如果详情组件需要图片附件，需要确认 `attachments` 是否返回。