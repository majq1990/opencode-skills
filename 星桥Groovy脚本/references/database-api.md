# 数据库操作 API

> 星桥脚本中执行数据库操作的内部 API 说明

## 获取 SQL 查询操作模板

星桥平台通过 `sql` 内置变量提供 SQL 查询能力。

### sql.of - 普通参数化 SQL

```groovy
// 获取 SQL 查询操作模板
var queryTemplate = sql.of('数据源名称')
```

### sql.ofNamed - 命名参数化 SQL

```groovy
// 获取命名 SQL 查询操作模板
var namedQueryTemplate = sql.ofNamed('数据源名称')
```

---

## 查询一条数据

### 使用 forMap

```groovy
// 普通 SQL 查询一条数据
var map = queryTemplate.forMap('select * from table where name = ? and sex = ?', ['zhangsan', '男'] as Object[])

if (map) {
    def userName = map.userName
    def userPhone = map.phoneNumber
    out.println("用户: ${userName}, 电话: ${userPhone}")
} else {
    out.println("未找到用户记录")
}
```

### 命名参数示例

```groovy
// 命名 SQL 查询一条数据
var map = namedQueryTemplate.forMap('select * from table where id in (:ids) and sex = :sex', ['ids': [1, 2], 'sex': '男'])
```

---

## 查询多条数据

### 默认查询（10 条限制）

```groovy
// 普通 SQL 查询多条数据（默认10条）
var list = queryTemplate.forList('select * from table where name LIKE ? and sex = ?', ['zhang%', '男'] as Object[])

list.each { user ->
    out.println("${user.id} - ${user.userName}")
}
```

### 指定最大条数

```groovy
// 普通 SQL 查询多条数据（限制条数）
var list = queryTemplate.forList('select * from table where name LIKE ? and sex = ?', limit, ['zhang%', '男'] as Object[])
```

### 命名参数多条查询

```groovy
// 命名 SQL 查询多条数据（默认10条）
var list = namedQueryTemplate.forList('select * from table where id in (:ids) and sex = :sex', ['ids': [1, 2], 'sex': '男'])

// 命名 SQL 查询多条数据（限制条数）
var list = namedQueryTemplate.forList('select * from table where id in (:ids) and sex = :sex', limit, ['ids': [1, 2], 'sex': '男'])
```

---

## 分页查询

### 使用 forPage

```groovy
// 普通 SQL 分页查询数据
var page = queryTemplate.forPage('select * from table where name LIKE ? and sex = ?', pageIndex, pageSize, ['zhang%', '男'] as Object[])

// 命名 SQL 分页查询数据
var page = namedQueryTemplate.forPage('select * from table where id in (:ids) and sex = :sex', pageIndex, pageSize, ['ids': [1, 2], 'sex': '男'])

out.println("查询到 ${page.total} 条记录")
```

---

## 完整业务示例

### 查库获取配置并设置请求

```groovy
// ========== 前置脚本：查库获取上报配置 ==========
import com.egova.json.utils.JsonUtils

var queryTemplate = sql.of('晋江v11')
var senderCode = '362200'
var actionType = 'UP_REC_REPORT'
var fileServerAddr = 'http://127.0.0.1:8088/MediaRoot/'
var reportURL = 'http://127.0.0.1:8082/eUrbanMIS/openapi/v2/upstream'

// 从表里面查询数据
var recList = queryTemplate.forList('select * from dlmis.torec where recid in (1258623,1256926)')

// 遍历查询到的数据，逐条组装上报参数，调用上报接口
for(rec in recList) {
    // 多媒体图片数据格式转换
    var medias = []
    var medialist = queryTemplate.forList('select * from dlmis.torecmedia where recid = ' + rec['RECID'])
    for(pic in medialist) {
        var mediaURL = fileServerAddr + pic['MEDIAPATH'] + pic['MSGID'] + '_' + pic['MEDIAID'] + '_' + pic['MEDIANAME']
        var media = [
            'mediaName': pic['MEDIANAME'],
            'mediaURL': mediaURL,
            'mediaType': 'IMAGE',
            'mediaUsage': '上报'
        ]
        medias.add(media)
    }

    transferData = [
        'otherTaskNum': rec['TASKNUM'],
        'eventLevelID': '1',
        'medias': medias,
        'mediaNum': medias.size()
    ]

    var requestMap = [
        'senderCode': senderCode,
        'actionType': actionType,
        'data': JsonUtils.serialize(transferData)
    ]

    out.println(requestMap)

    // 调用上报接口
    import com.egova.api.util.http.HttpUtils
    var response = HttpUtils.postForm(reportURL, requestMap, String.class)
}
```

## 使用原生 JdbcTemplate

在需要执行复杂事务或原生更新（如 `INSERT/UPDATE`）时，可以通过 `sql` 对象获取 `JdbcTemplate`。

```groovy
var queryTemplate = sql.of('数据源名称');
var jdbcTemplate = queryTemplate.session.jdbcTemplate;

// 执行更新操作
var sql = "INSERT INTO table(id, name, create_time) VALUES (?, ?, ?)";
jdbcTemplate.update(sql, 1, '测试', '2024-01-01 10:00:00');
```

---

## 插入或更新记录 (Merge/Update)

针对不同数据库，实现“不存在则插入，存在则更新”的常用逻辑。

### MySQL (ON DUPLICATE KEY UPDATE)

```groovy
var namedQueryTemplate = sql.ofNamed('数据源');
var jdbcTemplate = namedQueryTemplate.session.jdbcTemplate;

var mergeSQL = '''
    INSERT INTO to_media (ID, AJXSBH, GLLX, DMTURL) 
    VALUES (?, ?, ?, ?)
    ON DUPLICATE KEY UPDATE
        AJXSBH = VALUES(AJXSBH),
        GLLX = VALUES(GLLX),
        DMTURL = VALUES(DMTURL);
'''
jdbcTemplate.update(mergeSQL, [map?.ID, map?.AJXSBH, map?.GLLX, map?.DMTURL] as Object[])
```

### Oracle/DB2 (MERGE INTO)

```groovy
var mergeSQL = '''
    MERGE INTO to_media A USING (
        SELECT ? AS ID, ? AS AJXSBH FROM DUAL
    ) TMP ON (A.ID = TMP.ID) 
    WHEN MATCHED THEN UPDATE SET AJXSBH = TMP.AJXSBH
    WHEN NOT MATCHED THEN INSERT (ID, AJXSBH) VALUES (TMP.ID, TMP.AJXSBH)
'''
jdbcTemplate.update(mergeSQL, [map?.ID, map?.AJXSBH] as Object[])
```

---

## 注意事项

1. **数据源名称**：`sql.of()` 需要指定数据源名称，不是 SQL 语句
2. **SQL 注入防护**：始终使用参数化查询，不要拼接 SQL 字符串
3. **默认条数限制**：`forList()` 默认最多返回 10 条，避免大量数据查询
4. **分页查询**：大数据量查询务必使用 `forPage()` 进行分页
5. **结果判空**：`forMap()` 可能返回 `null`，使用前务必判空
6. **字段命名**：返回的 Map 中，数据库字段名会自动转为大写或保持原样
7. **错误处理**：数据库查询异常时使用 `return 'api_stop'` 终止执行
8. **日志输出**：使用 `out.println()` 输出查询过程信息
