# 示例：人员类型统计

## 用户需求示例

```text
我要做一个人员类型统计图，展示每种人员类型的总人数和在线人数。
```

## 应命中接口

| 项目 | 内容 |
|---|---|
| apiCode | PATROL_GROUP_TYPE |
| 接口名称 | 人员类型分组 |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/patrol/group` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/人员类型分组` |
| 详细接口文档 | `knowledge/api_details/mis/patrol/PATROL_GROUP_TYPE.md` |
| 响应主路径 | `result` |
| 响应形态 | array |

## 判断要点

1. 用户要按人员类型分组统计。
2. “在线人数”需要开启 `groupOnlineFlag=true`。
3. 接口返回 `value` 表示总人数，`online` 表示在线人数。
4. 可计算在线率。

## 推荐请求参数

```json
{
  "groupOnlineFlag": true
}
```

## 映射

| 组件目标字段 | 来源字段 | 转换规则 | 说明 |
|---|---|---|---|
| id | item.name | 字符串兜底 | 人员类型 id |
| name | item.text | 字符串兜底 | 人员类型名称 |
| value | item.value | Number 转换 | 总人数 |
| online | item.online | Number 转换 | 在线人数 |
| onlineRate | item.online / item.value | 百分比计算 | 在线率 |

## 过滤脚本

```javascript
function filter(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(function (item) {
        var total = Number(item.value || 0);
        var online = Number(item.online || 0);

        return {
            id: item.name || '',
            name: item.text || '',
            value: total,
            online: online,
            onlineRate: total > 0 ? Number((online * 100 / total).toFixed(2)) : 0
        };
    }).sort(function (a, b) {
        return b.value - a.value;
    });
}
```

## 需要核对的内容

```text
无
```