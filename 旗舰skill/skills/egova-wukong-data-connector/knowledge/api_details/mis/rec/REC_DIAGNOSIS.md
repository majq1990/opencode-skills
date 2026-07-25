# 案件诊断信息

## 1. 标准化基本信息

| 项目 | 内容 |
|---|---|
| apiCode | REC_DIAGNOSIS |
| domain | MIS案件 |
| bizObject | 案件 |
| apiName | 案件诊断信息 |
| apiType | diagnosis |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/diagnosis` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/案件诊断信息` |
| 数据提交方式 | application/json |
| 响应主路径 | `result` |
| 响应形态 | array |
| 适配组件 | 诊断卡片、文本列表、轮播列表、态势分析文本 |

---

## 2. 接口说明

该接口用于统计某段时间内的案件诊断信息。

支持的诊断类型包括：

- 趋势诊断；
- 区域诊断；
- 类型诊断。

也可以根据条件过滤，例如：

- 指定区划；
- 指定案件来源；
- 指定案件类型；
- 指定问题类型；
- 指定统计时间范围。

注意：

1. 该接口传参不同，对应查询逻辑和返回字段会有区别；
2. 如果需要的诊断类型当前接口不支持，需要联系后端重新开发；
3. `groupList` 必填，否则接口会报错；
4. 该接口返回的是文本诊断内容，不是数值统计图表。

---

## 3. 数据来源

| 数据库 | 数据表 | 说明 |
|---|---|---|
| cgdbstat | to_stat_info | 统计库案件表 |

---

## 4. 请求参数

### 4.1 诊断类型参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| groupList | String[] | 是 | 无 | 需要统计的诊断指标列表 |

### 4.2 groupList 支持值

| 指标 | 含义 |
|---|---|
| trendDiagnosis | 趋势诊断 |
| eventDiagnosis | 类型诊断 |
| regionDiagnosis | 区域诊断 |

### 4.3 时间参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| startTimestamp | String | 否 | 当前时间减去 30 天的当天 0 时 0 分 0 秒 | 统计指标开始时间，格式 `yyyy-MM-dd HH:mm:ss` |
| endTimestamp | String | 否 | 当天 23 时 59 分 59 秒 | 统计指标结束时间，格式 `yyyy-MM-dd HH:mm:ss` |
| interval | Integer | 否 | 7 | 返回时显示的天数，例如近 7 天 |

### 4.4 区划筛选参数

| 参数名 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| dutyGridId | String | 否 | 责任网格 id |
| cellId | String | 否 | 单元网格 id |
| communityId | String | 否 | 社区 id |
| streetId | String | 否 | 街道 id |
| districtId | String | 否 | 区县 id |
| cityId | Integer | 否 | 市 id |

### 4.5 案件类型 / 问题类型 / 来源参数

| 参数名 | 类型 | 是否必须 | 参数说明 |
|---|---|---|---|
| recTypeId | Integer | 否 | 案件类型 id |
| eventTypeId | String | 否 | 问题类型 id |
| mainTypeId | String | 否 | 问题大类 id |
| subTypeId | String | 否 | 问题小类 id |
| eventTypeIds | String[] | 否 | 问题类型 id 列表 |
| notEventTypeId | String | 否 | 排除指定问题类型 |
| eventSrcId | String | 否 | 问题来源 id |
| eventSrcIds | String[] | 否 | 问题来源 id 列表 |

### 4.6 eventTypeId 特殊说明

| 参数值 | 趋势诊断返回名称 |
|---|---|
| 1 | 事件指数 |
| 2 | 部件指数 |
| 不传 | 城管指数 |

> 注意：该逻辑当前暂时只适配于 `1=事件`、`2=部件` 的现场 `tc_dic_event_any_type` 表情况。

### 4.7 区域诊断参数

| 参数名 | 类型 | 是否必须 | 默认值 | 参数说明 |
|---|---|---|---|---|
| regionDiagnosisField | String | 否 | district | 区域诊断时返回的区域类型 |

### 4.8 regionDiagnosisField 支持值

| 值 | 含义 |
|---|---|
| district | 区县 |
| street | 街道 |
| community | 社区 |
| cell | 单元网格 |

---

## 5. 请求示例

```json
{
  "groupList": [
    "eventDiagnosis",
    "regionDiagnosis",
    "trendDiagnosis"
  ],
  "interval": 7,
  "regionDiagnosisField": "street"
}
```

---

## 6. 返回字段

| 字段路径 | 字段名 | 类型 | 是否必须 | 字段说明 | 组件映射建议 |
|---|---|---|---|---|---|
| hasError | hasError | Boolean | 是 | 是否接口报错 | 用于异常判断 |
| result | result | Object[] | 是 | 诊断结果数组 | 文本列表数据源 |
| result[].name | name | String | 是 | 指标 code 或诊断名称 | 可映射为 `title` / `name` |
| result[].text | text | String | 是 | 诊断模板文本 | 可映射为 `template` / `desc` |
| result[].value | value | String | 是 | 诊断内容 | 可映射为 `value` / `content` |
| message | message | String | 是 | hasError 为 true 时展示报错信息 | 错误提示 |
| tag | tag | / | 是 | 未使用 | 忽略 |
| totalCount | totalCount | Integer | 是 | 返回数据总条数 | 辅助统计 |

---

## 7. 返回示例

```json
{
  "hasError": false,
  "result": [
    {
      "name": "类型诊断",
      "text": "近7天%s问题较突出，需要加强管控。",
      "value": "违规设置广告、生活垃圾"
    },
    {
      "name": "区域诊断",
      "text": "近7天%s问题较突出，且有加速增长趋势，需有关部门加强管控。",
      "value": "湖坊镇违规设置广告、湖坊镇出店经营"
    },
    {
      "name": "趋势诊断",
      "text": "近7天%s，在整体上方运行，由于周末上报量下降，案卷指数趋缓。",
      "value": "平均城管指数为2255.3"
    }
  ],
  "message": null,
  "tag": null,
  "totalCount": 3
}
```

---

## 8. 报错说明

| message | 说明 | 处理建议 |
|---|---|---|
| 其他报错 | 需联系后台排查数据 | 查看后台日志 |
| 需要统计的指标为空！ | `groupList` 未传参 | 补充 `groupList` |
| 不存在的诊断 | `groupList` 中存在接口暂不支持的诊断指标 | 检查 `groupList` |
| 获取数据失败! | 数据获取异常 | 联系后端排查 |
| 动态查询出错 | 动态 SQL 或指标查询异常 | 联系后端排查 |

---

## 9. 适配建议

### 适合组件

- 诊断卡片；
- 文本列表；
- 轮播列表；
- 态势分析文本；
- 大屏结论区。

### 字段映射建议

| 组件目标字段 | 接口字段 | 转换规则 |
|---|---|---|
| title | item.name | 字符串兜底 |
| template | item.text | 字符串兜底 |
| value | item.value | 字符串兜底 |
| content | item.text + item.value | 可拼接完整文案 |

### 推荐过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        var template = item.text || '';
        var value = item.value || '';
        var content = template;

        if (template.indexOf('%s') >= 0) {
            content = template.replace('%s', value);
        } else if (value) {
            content = template + value;
        }

        return {
            title: item.name || '',
            template: template,
            value: value,
            content: content
        };
    });
}
```

### 轮播列表过滤脚本：data 为 result 本体

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        var template = item.text || '';
        var value = item.value || '';
        var content = template;

        if (template.indexOf('%s') >= 0) {
            content = template.replace('%s', value);
        } else if (value) {
            content = template + value;
        }

        return {
            title: item.name || '',
            subTitle: content,
            value: value
        };
    });
}
```

---

## 10. 性能和联调注意点

1. `groupList` 必填。
2. 该接口返回文本诊断，不适合作为普通图表数值。
3. `regionDiagnosisField` 会影响区域诊断粒度。
4. `interval` 会影响返回文案中的时间范围。
5. 如果诊断文案需要完全由前端控制，应确认是否使用 `text` 模板和 `value` 拼接。
6. 如果 `groupList` 包含不支持的诊断指标，会报“不存在的诊断”。