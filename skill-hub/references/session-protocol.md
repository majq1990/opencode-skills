# 会话协议：以 skills-manager 登录态调 API

## 原则

skill-hub **不做登录、不内置任何账号**。每个使用者以"本机 skills-manager 当前登录者"的身份访问服务器——谁登录就用谁的。凭据不存在于本 skill 的任何文件中。

## 会话文件（跨平台候选）

| 文件 | 候选路径（按 `~` 展开） | 说明 |
|------|------------------------|------|
| 数据库 | `~/.skills-manager/skills-manager.db` | SQLite（WAL），`settings` 表键值对 |
| 密钥 | `~/.skills-manager/.secret.key` | 32 字节原始二进制，AES-256 密钥 |

只读打开：`sqlite3.connect("file:<db>?mode=ro", uri=True)`；WAL 只读失败退化为 `immutable=1`。macOS/Linux 上 skills-manager 数据目录同样在 `~/.skills-manager/`；若未来版本变更位置，按候选列表探测、探测不到走"未登录"提示，不猜测其他位置。

## token 获取流程

1. 读 `settings` 表取 `enterprise_token`（缺失 = 从未登录过 → 提示登录）
2. 解密 `enc:v1:` 值：
   - 编码格式：`enc:v1:` + hex
   - 字节布局：hex 解码后 = `nonce(12B) ‖ AES-256-GCM 密文 ‖ tag(16B)`
   - 密钥：`.secret.key` 的 32 字节原始二进制（无 KDF、无 AAD）
   - 解密引擎：python `cryptography` 的 `AESGCM`；库缺失时回退 `node -e` + `crypto.createDecipheriv('aes-256-gcm', …)`（key/密文经 stdin 传 JSON，不进命令行）
3. 解出 JWT（HS256 三段式）。解析 payload 的 `exp`（秒级时间戳）：
   - 已过期 → 提示"skills-manager 登录态已过期（时间），请重新登录后重试"
4. token 只在内存中使用：不落盘、不打印、不写日志

## 旧字段说明

`enterprise_auth_token` 是早期版本的会话记录（JSON 包装 `{token, expires_at, user, …}`），可能早已过期，**不要使用**；一律以 `enterprise_token` 为准。

## 401 / 过期处置

- API 返回 401：登录态被服务器拒绝 → 提示"打开 skills-manager 重新登录企业服务器后重试"
- 本地 exp 已过：同上
- 绝不尝试自行调用 `/auth/login` 兜底（那需要收集用户密码，违背"各自账号、不由 skill 经手凭据"的设计）

## 定位（对应 scripts/skill_server.py）

- `_locate_session_files()`：候选探测 db + key
- `_read_settings()`：只读读 settings
- `_decrypt_enc_v1()` → `_decrypt_gcm_python()` / `_decrypt_gcm_node()`
- `get_token()`：串流程 + exp 校验
