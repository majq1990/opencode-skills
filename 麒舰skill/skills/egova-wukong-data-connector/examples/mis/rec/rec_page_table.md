# 示例：案件分页表格

## 用户需求示例

```text
我要做一个案件分页表格，展示任务号、案件描述、地址、问题类型、案件阶段和上报时间。
```

## 应命中接口

| 项目 | 内容 |
|---|---|
| apiCode | REC_PAGE |
| 接口名称 | 案件分页查询 |
| 请求方式 | POST |
| 接口地址 | `/api/cgdbstat/records/page` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/案件相关/案件分页查询` |
| 详细接口文档 | `knowledge/api_details/mis/rec/REC_PAGE.md` |
| 响应主路径 | `result` |
| 响应形态 | array |

## 判断要点

1. 用户明确要分页表格，应使用 page 接口。
2. 分页组件通常需要 `totalCount`。
3. 因此建议让悟空传入完整响应包，而不是只传 `result` 本体。
4. 请求体必须包含 `condition` 和 `paging`。

## 推荐请求参数

```json
{
  "condition": {},
  "paging": {
    "pageIndex": 1,
    "pageSize": 10
  }
}
```

## 映射

| 组件目标字段 | 来源字段 | 转换规则 | 说明 |
|---|---|---|---|
| list | data.result | 数组兜底 | 当前页案件列表 |
| total | data.totalCount | Number 转换 | 分页总数 |
| id | item.id | 字符串兜底 | 案件 id |
| taskNum | item.taskNum | 字符串兜底 | 任务号 |
| eventDesc | item.eventDesc | 字符串兜底 | 案件描述 |
| address | item.address | 字符串兜底 | 案发地址 |
| eventTypeName | item.eventTypeName | 字符串兜底 | 问题类型 |
| eventStateName | item.eventStateName | 字符串兜底 | 案件阶段 |
| createTime | item.createTime | 字符串兜底 | 上报时间 |

## 过滤脚本

```javascript
function filter(data) {
    if (!data || data.hasError === true) {
        return {
            list: [],
            total: 0
        };
    }

    var list = Array.isArray(data.result) ? data.result : [];

    return {
        list: list.map(function (item) {
            return {
                id: item.id || '',
                taskNum: item.taskNum || '',
                eventDesc: item.eventDesc || '',
                address: item.address || '',
                eventTypeName: item.eventTypeName || '',
                eventStateName: item.eventStateName || '',
                createTime: item.createTime || ''
            };
        }),
        total: Number(data.totalCount || 0)
    };
}
```

## 需要核对的内容

| 序号 | 待确认项 | 影响范围 | 建议处理 |
|---|---|---|---|
| 1 | 悟空是否能把完整响应包传入 filter | 分页总数 | 分页表格建议传完整响应包，否则无法获取 `totalCount` |