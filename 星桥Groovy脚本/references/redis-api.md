# Redis 操作 API

> 星桥脚本中执行 Redis 操作的内部 API 说明。主要通过 Spring 的 `StringRedisTemplate` 进行访问。

## 推荐写法

```groovy
import com.flagwind.application.Application;
import org.springframework.data.redis.core.StringRedisTemplate;
import java.util.concurrent.TimeUnit;

// 从 Spring 容器中获取 StringRedisTemplate Bean 对象
var redisTemplate = Application.resolve(StringRedisTemplate.class);

// 写，建议加过期时间
redisTemplate.opsForValue().set("custom:1", 'test', 1, TimeUnit.HOURS);

// 读
var v = redisTemplate.opsForValue().get("custom:1");
```

## 常用操作示例

### 存储数据

```groovy
// 设置值，并指定过期时间
redisTemplate.opsForValue().set("key_name", "value_content", 25, TimeUnit.HOURS);
```

### 读取数据

```groovy
// 获取数据
var value = redisTemplate.opsForValue().get("key_name");
out.println("读取到 Redis 数据: " + value);
```

### 结合变量动态存取

```groovy
var todayIn = "count_in_" + variables['env'].id;
redisTemplate.opsForValue().set(todayIn, variables['count'] + '', 24, TimeUnit.HOURS);
```

---

## 常见场景
- **Token 缓存**：存储第三方系统 Token，避免频繁调用授权接口。
- **接口限流**：记录某段时间内的请求次数。
- **数据共享**：在不同接口脚本间共享临时计算状态。
