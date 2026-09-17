# 案件详情

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_INFO |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 案件详情 |
| apiType | detail |
| 请求方式 | GET |
| 接口地址 | `/api/cgdbstat/records/info` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/案件详情` |
| 数据提交方式 | query/form，以实际网关配置为准 |
| 响应主路径 | `result` |
| 响应形态 | object |
| 适配组件 | 详情弹窗、详情面板、地图点位详情、表格行详情 |

---

## 2. 接口说明

该接口用于根据案件主键查询单个案件详情。

适合：

- 案件详情弹窗；
- 地图点位点击后的案件详情；
- 案件表格行点击详情；
- 案件信息卡片。

不适合：

- 列表展示；
- 分页表格；
- 图表统计；
- 热力图展示。

注意：

1. 必须确认案件 id 来源；
2. id 通常来自案件简要列表、案件列表、案件分页查询或地图点位；
3. 若需要附件或图片，需要结合实际返回字段确认附件结构。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdbstat | to_stat_info | 统计库案件表 |
| cgdbstat | to_media | 统计库附件表 |
| cgdb | to_media | 业务库附件表 |
| cgdb | to_his_media | 业务库历史附件表 |

---

## 4. 请求参数

| 参数路径 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| id | String | 是 | 无 | 案件主键 |

---

## 5. 请求示例

```http
GET /api/cgdbstat/records/info?id=1803060
```

或按平台配置传参：

```json
{
  "id": "1803060"
}
```

---

## 6. 返回字段

### 6.1 顶层字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object | 是 | 案件详情对象 | 详情数据源 |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 通常忽略 |

### 6.2 result 常用字段

| 字段路径 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|
| result.id | String | 是 | 主键 | id |
| result.taskNum | String | 是 | 任务号 | 标题 |
| result.address | String | 是 | 案发地址 | 详情项 |
| result.eventDesc | String | 是 | 案件描述 | 详情项 |
| result.longitude | Double | 是 | 经度 | 地图点位 |
| result.latitude | Double | 是 | 纬度 | 地图点位 |
| result.createTime | String | 是 | 上报/创建时间 | 详情项 |
| result.archiveTime | String | 否 | 结案时间 | 详情项 |
| result.eventSrcName | String | 否 | 案件来源名称 | 详情项 |
| result.eventTypeName | String | 否 | 问题类型名称 | 详情项 |
| result.mainTypeName | String | 否 | 问题大类名称 | 详情项 |
| result.subTypeName | String | 否 | 问题小类名称 | 详情项 |
| result.recTypeName | String | 否 | 案件类型名称 | 详情项 |
| result.eventStateName | String | 否 | 案件阶段名称 | 详情项 |
| result.dutyGridName | String | 否 | 责任网格名称 | 详情项 |
| result.cellName | String | 否 | 单元网格名称 | 详情项 |
| result.communityName | String | 否 | 社区名称 | 详情项 |
| result.streetName | String | 否 | 街道名称 | 详情项 |
| result.districtName | String | 否 | 区县名称 | 详情项 |
| result.disposeUnitName | String | 否 | 处置部门名称 | 详情项 |
| result.reportPatrolName | String | 否 | 上报人员名称 | 详情项 |
| result.attachments | Object[] | 否 | 附件列表 | 图片/附件展示 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": {
    "id": "1803060",
    "taskNum": "22041800001",
    "address": "瑞祥路11号的东北方向13.76米",
    "eventDesc": "存在垃圾未入桶的现象。",
    "longitude": 120.955465,
    "latitude": 28.116796,
    "createTime": "2022-04-18 13:01:55",
    "archiveTime": "2022-04-18 15:10:00",
    "eventSrcName": "监督员上报",
    "eventTypeName": "事件",
    "mainTypeName": "市容环境",
    "subTypeName": "暴露垃圾",
    "recTypeName": "事件",
    "eventStateName": "结案",
    "districtName": "区县一",
    "streetName": "街道一",
    "disposeUnitName": "处置部门一",
    "reportPatrolName": "张三"
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
- 详情面板；
- 地图点位详情；
- 表格行详情。

### 字段映射建议：详情卡片

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| title | data.taskNum | 字符串兜底 |
| items[].label | 固定文本 | 详情项名称 |
| items[].value | data.xxx | 字符串兜底 |
| lng | data.longitude | Number 转换 |
| lat | data.latitude | Number 转换 |

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
        title: data.taskNum || '',
        lng: Number(data.longitude || 0),
        lat: Number(data.latitude || 0),
        items: [
            { label: '任务号', value: data.taskNum || '' },
            { label: '案件来源', value: data.eventSrcName || '' },
            { label: '案件类型', value: data.recTypeName || '' },
            { label: '问题类型', value: data.eventTypeName || '' },
            { label: '问题大类', value: data.mainTypeName || '' },
            { label: '问题小类', value: data.subTypeName || '' },
            { label: '案件阶段', value: data.eventStateName || '' },
            { label: '案发地址', value: data.address || '' },
            { label: '案件描述', value: data.eventDesc || '' },
            { label: '上报时间', value: data.createTime || '' },
            { label: '结案时间', value: data.archiveTime || '' },
            { label: '处置部门', value: data.disposeUnitName || '' },
            { label: '上报人员', value: data.reportPatrolName || '' }
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
        title: item.taskNum || '',
        lng: Number(item.longitude || 0),
        lat: Number(item.latitude || 0),
        items: [
            { label: '任务号', value: item.taskNum || '' },
            { label: '案件来源', value: item.eventSrcName || '' },
            { label: '案件类型', value: item.recTypeName || '' },
            { label: '问题类型', value: item.eventTypeName || '' },
            { label: '问题大类', value: item.mainTypeName || '' },
            { label: '问题小类', value: item.subTypeName || '' },
            { label: '案件阶段', value: item.eventStateName || '' },
            { label: '案发地址', value: item.address || '' },
            { label: '案件描述', value: item.eventDesc || '' },
            { label: '上报时间', value: item.createTime || '' },
            { label: '结案时间', value: item.archiveTime || '' },
            { label: '处置部门', value: item.disposeUnitName || '' },
            { label: '上报人员', value: item.reportPatrolName || '' }
        ]
    };
}
```

---

## 10. 性能和联调注意点

1. 必须确认案件 id 来源。
2. id 可来自案件简要列表、案件列表、案件分页查询。
3. 若详情组件要展示附件，需要确认 `attachments` 的真实结构。
4. 如果详情字段不满足现场展示，需要补充字段或改用现场接口。