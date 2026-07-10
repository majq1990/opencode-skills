# Spring 容器 Bean 获取 API

> 星桥脚本支持通过 `Application` 对象从 Spring 容器中直接获取已定义的 Bean 实例。

## 核心 API

### Application.resolve

通过类名或 Bean 名称获取 Spring 容器中的对象。

```groovy
import com.flagwind.application.Application;

// 获取指定的 Bean
var bean = Application.resolve(ClassName.class);
```

---

## 常用场景

### 获取 Redis 模板

```groovy
import org.springframework.data.redis.core.StringRedisTemplate;
import com.flagwind.application.Application;

var redisTemplate = Application.resolve(StringRedisTemplate.class);
```

### 获取 JdbcTemplate

虽然平台提供了 `sql` 变量，但在需要执行原生 JDBC 操作或复杂事务时，可以获取 `JdbcTemplate`。

```groovy
var queryTemplate = sql.of('数据源名称');
var jdbcTemplate = queryTemplate.session.jdbcTemplate;
```

---

## 注意事项

1. **导包规范**：使用 Spring 对象通常需要导入相应的类路径。
2. **性能考量**：频繁调用 `Application.resolve` 可能有微小开销，建议在脚本顶部获取一次后复用。
3. **安全限制**：沙箱环境可能限制获取部分核心系统 Bean，建议优先使用平台提供的 `sql`、`tokenStore` 等内置变量。
