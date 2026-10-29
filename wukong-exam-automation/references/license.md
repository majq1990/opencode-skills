# License 申请与校验（2026-10-28 实测补全）

## 核心机制：申请标识不是 info API 显示的 licenseKey

**最大的坑**：`/wukong-api/free/license/info` 返回的 `licenseKey` 是**当前加载的那份 license 里绑定的 key**（新实例上是镜像自带的旧 license，绑定的是封镜像那台机器的 DB），**不是本机的申请标识**。拿它去申请，拿到的 license 绑定旧 key，本机校验必失败。

**正确的申请标识**（本机 MySQL 的数据库 key）：

```sql
select substring(uuid(),25);
```

- 在该 MySQL 上**确定性**（基于 server_uuid，多次调用结果一致），本机实测返回 `00163e139dec`
- `wukong` 和 `data_exchange` 两个库返回**同一个值**（服务级 UUID），所以悟空和星桥共用一套 license 时，申请一次即可
- 换机器/重装 MySQL 会变，每次新采购都要重新取

## 校验逻辑（扒 egova-license jar 字节码确认）

`LicenseManagerImpl.verifyKeyAndDate()`：

1. license / validFromDate / validToDate / licenseKey / functionSet 任一为空 → `无效授权，不包含对应的key`
2. `validFromDate.after(now)` → 未生效；`validToDate.before(now)` → `授权已过期`
3. **key 校验**：`("," + license.licenseKey + ",").indexOf("," + dbKey + ",") > -1`，即 license 的 licenseKey 字段必须**精确包含** `select substring(uuid(),25)` 的值（licenseKey 可以是逗号分隔的多 key 列表）
4. `verifyPlugin()` 再过插件关：`license.getPlugins().contains(pluginName)`（插件名如 `wukong`、`exam`、`data-exchange`）

旧 license 的失败顺序：先日期后 key，所以过期 license 报"授权已过期"；新 license 日期对但 key 错，报"无效授权，不包含对应的key"。LicenseAop 拦截时 OAuth 登录端点（含 `/oauth/extras/public-key`）全部返回 `invalid_grant`。

## 标准流程

1. 服务起来后（或启动前）先取 key：`mysql -uroot -p<环境约定密码> wukong -N -e "select substring(uuid(),25);"`
2. 用户拿这个 key 去 license 门户申请（有效期建议覆盖考核+阅卷至少一个月；功能清单 235+ 项，含 wukong/exam/data-exchange/mis/workflow/form/screen/gisbuilder）
3. 拿到 license 内容（约 9.3KB 加密串）后写入两个库：
   ```sql
   UPDATE wukong.com_license SET content='<license>' WHERE id=1;
   UPDATE data_exchange.com_license SET content='<license>' WHERE id=1;
   ```
   （两库内容相同——一套 license 共用；写入前先备份老内容）
4. 重启 dex → wukong → videocenter
5. 验证：license/info 的 licenseKey 应等于第 1 步取到的 key；LicenseStartup 日志无"证书校验失败"；候选账号能登录

## 排障速查

| 现象 | 原因 | 处理 |
|---|---|---|
| 登录返回 invalid_grant / invalid authentication，日志有 LicenseException | license 过期或 key 不匹配 | 按上面流程重申请写入 |
| 日志"授权已过期" | validToDate 早于当前 | 重申请 |
| 日志"无效授权，不包含对应的key" | license 绑定的 key ≠ 本机 substring(uuid(),25) | 用正确的 key 重申请 |
| 日志"暂无插件[x]授权" | license 插件集缺 x | 申请时补全功能清单 |
| info API 能返回 license 信息但 AOP 不认 | info API 读的是加载的 license 对象，AOP 用同一对象——若日期/ key 对仍被拦，查 dex 侧日志（dex 也有独立 LicenseAop） | 两库都要写对 |

## 登录验证的正确姿势（SM2）

登录不是明文密码：`POST /wukong-api/oauth/extras/token`，参数
`client_id=unity-client&client_secret=unity&grant_type=password&username=<账号>&password=<SM2密文>`
- 加密类型取 `/wukong-api/oauth/extras/alg`（本环境为 `sm2`）
- 公钥取 `/wukong-api/oauth/extras/public-key`（65 字节十六进制，04 开头）
- 用 gmssl：`sm2.CryptSM2(public_key=pub, private_key='', mode=1).encrypt(pwd.encode()).hex()`
- 密码哈希验证（本地可算）：`sm3(salt + password)`，默认密码 eGova@123 的 salt 为 `GQQiaYnk`
