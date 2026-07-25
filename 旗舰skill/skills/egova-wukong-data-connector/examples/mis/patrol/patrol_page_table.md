# 示例：人员分页表格

## 用户需求示例

```text
我要做一个人员分页表格，展示人员名称、人员类型、所属区划、所属部门、手机号和在线状态。
```

## 应命中接口

| 项目 | 内容 |
|---|---|
| apiCode | PATROL_PAGE |
| 接口名称 | 人员分页查询 |
| 请求方式 | POST |
| 接口地址 | `/api/cgdb/patrol/page` |
| 星桥接口路径地址 | `API平台/悟能接口/城管接口/人员相关/人员分页查询` |
| 详细接口文档 | `knowledge/api_details/mis/patrol/PATROL_PAGE.md` |
| 响应主路径 | `result` |
| 响应形态 | array |

## 判断要点

1. 用户明确要分页表格，应使用 page 接口。
2. 分页组件需要 `totalCount`，建议传完整响应包。
3. 不需要上级区划、上级部门、责任网格、头像时，不开启扩展 flag。
4. 在线状态来自 `patrolState.patrolStateId`，通常 `1` 表示在线。

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
| list | data.result | 数组兜底 | 当前页人员列表 |
| total | data.totalCount | Number 转换 | 分页总数 |
| id | item.id | 字符串兜底 | 人员 id |
| name | item.patrolName | 字符串兜底 | 人员名称 |
| patrolTypeName | item.patrolType.displayName | 对象判空 | 人员类型 |
| regionName | item.region.regionName | 对象判空 | 所属区划 |
| unitName | item.human.unitName | 对象判空 | 所属部门 |
| mobile | item.human.telMobile | 对象判空 | 手机号 |
| onlineStatus | item.patrolState.patrolStateId | 状态转换 | 在线/离线 |

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
            var stateId = item.patrolState ? item.patrolState.patrolStateId : 0;

            return {
                id: item.id || '',
                name: item.patrolName || '',
                cardId: item.cardId || '',
                patrolCode: item.patrolCode || '',
                patrolTypeName: item.patrolType && item.patrolType.displayName || '',
                regionName: item.region && item.region.regionName || '',
                unitName: item.human && item.human.unitName || '',
                mobile: item.human && item.human.telMobile || '',
                onlineStatus: stateId === 1 ? '在线' : '离线'
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