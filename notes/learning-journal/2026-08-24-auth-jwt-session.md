# 2026-08-24：登录、Session、Token、JWT 与后端信任边界

这次讨论的目标不是记住 JWT API，而是把登录鉴权相关概念放进同一张后端模型里。

## 本次真正讲通的核心关系

```text
Cookie       = 浏览器保存/自动携带数据的机制
Session      = 服务端保存会话状态
Session ID   = 找到服务端 Session 的不透明标识
Token        = 凭证的统称
Bearer       = 持有者凭证的认证方案
JWT          = Token 的一种结构化格式
Access Token = 短期调用 API 的凭证
Refresh Token= 换取新 Access Token 的长期高价值凭证
```

最重要的修正是：这些词不在同一个层级，不能把它们简单理解成互相替代的技术。

## 为什么登录后还需要临时凭证

用户名和密码属于长期秘密，不应该在每个 API 请求中重复发送。登录成功后，后端需要建立一个可过期、可控制的临时身份凭证。

两条典型路径：

```text
Session：
密码登录 -> 创建 Session -> 返回 Session ID -> 后续查 Session Store

Token：
密码登录 -> 签发 Access Token -> Authorization: Bearer <token> -> 验证 Token
```

## JWT 的关键理解

JWT 常见结构：

```text
Header.Payload.Signature
```

JWT Payload 默认不是加密内容。Base64URL 是编码，不等于保密。

```text
签名解决：内容有没有被未经授权地修改、是否来自可信签发方
加密解决：别人能不能看到内容
```

因此 JWT 中不应放密码、JWT Secret、API Secret 等敏感秘密。

## `JWT_SECRET` 的真正意义

在 HS256 这类 HMAC 签名模型里，`JWT_SECRET` 是服务器签发和验证 Token 的共享秘密。

如果它泄露，攻击者可能自己伪造 Claims 并生成合法签名。因此：

- 不写死源码；
- 不提交 GitHub；
- 环境缺失时启动失败；
- 错误信息不打印 Secret；
- 生产环境考虑轮换。

同时要记住：不是所有 JWT 都依赖 `JWT_SECRET`。非对称签名使用私钥签发、公钥验证。

## Bearer Token 为什么必须防泄露

Bearer 的核心是“持有有效凭证即可使用”。攻击者拿到完整 Token 后，通常不需要破解或修改，只需要重放。

所以：

```text
JWT 有签名 != 不需要 HTTPS
```

HTTPS 仍然负责保护传输过程。

## Authentication 和 Authorization

```text
Authentication：你是谁？
Authorization：你能做什么？
```

认证成功以后，服务端应产生可信 Principal：

```text
Principal
├─ subject/user_id
├─ tenant_id
└─ scopes / auth context
```

后续授权再基于 role、permission、owner、tenant 等决定是否允许操作。

## 最重要的后端信任边界

客户端永远可以自己构造 HTTP 请求，因此下面这些字段不能因为“前端传来了”就被当成可信身份：

```text
Body.user_id
Body.tenant_id
Body.role
公网可伪造的 X-User-ID / X-Tenant-ID
```

可信身份应该来自：

```text
Session / Token
      |
      v
服务端 Authentication
      |
      v
Principal
```

然后业务层组合“可信 Principal + 已验证业务输入”。

这也是为什么前端隐藏管理员按钮不是安全措施：攻击者可以绕过 UI 直接调用 API。

## Middleware 与 Go Context

认证逻辑不应复制到每个 Handler。

```text
Request
 -> Request ID Middleware
 -> Logging Middleware
 -> Authentication Middleware
 -> Authorization
 -> Handler
 -> Service
 -> Repository
```

在 Go 中，`context.Context` 可以沿请求链传播 deadline、cancel、request ID、可信 Principal 等少量 request-scoped metadata，但不应该变成随便塞业务参数的万能 map。

## Access Token 与 Refresh Token

Access Token 应较短命，用于日常 API 请求；Refresh Token 生命周期更长，用来换取新的 Access Token。

```text
Access Token 被偷 -> 风险窗口受短 TTL 限制
Refresh Token 被偷 -> 可以持续换新访问能力，因此价值更高
```

常见 Refresh Token Rotation：

```text
R1 -> 刷新 -> A2 + R2
R1 立即失效
```

旧 R1 再次出现时，可以作为泄露/重放信号。

## 为什么 JWT 注销比 Session 麻烦

Session 可以直接删除服务端状态，实现立即失效。

如果自包含 JWT 只靠签名和 `exp`，客户端删除 Token 并不会让攻击者手中的副本自动失效。

因此实际系统会引入：

- 短 Access Token TTL；
- 可撤销 Refresh Session；
- token/session version；
- denylist；
- 高风险操作重新确认当前权限。

这说明“JWT 完全无状态所以一定更简单”是错误的绝对化理解。

## 401、403 与跨租户 404

```text
401：没有有效认证身份
403：身份有效，但没有操作权限
404：部分 owner/tenant 场景为了隐藏资源是否存在而故意返回
```

不能机械地认为所有授权失败都必须返回 403；要服从具体 API 的安全契约。

## 密码存储

密码不应该明文保存，也不应该直接使用裸 SHA-256。

推荐使用专门的 password hashing algorithm：

```text
Argon2id / bcrypt / scrypt
```

它们会故意提高离线猜密码的成本，并配合 Salt 让相同密码产生不同的存储结果。

## 浏览器安全边界

```text
HttpOnly -> JavaScript 不能直接读取 Cookie
Secure   -> Cookie 只经 HTTPS 发送
SameSite -> 控制跨站 Cookie 发送
XSS      -> 恶意脚本进入受信页面
CSRF     -> 利用浏览器自动携带凭据发出被诱导请求
CORS     -> 浏览器跨源访问策略，不是 API 身份认证
```

特别要避免误区：把 CORS 配得很严格，并不能让一个没有 Authentication/Authorization 的 API 变安全。

## 后端工程应该继续问什么

看到一个认证实现，不要停在“JWT 能不能生成”，继续追问：

1. Token 被偷怎么办？
2. 用户被封禁后旧凭证多久失效？
3. role/tenant 修改后旧 Claims 怎么处理？
4. Refresh Token 重放怎么发现？
5. 全设备退出如何实现？
6. 密钥如何轮换？
7. Session Store 或身份提供方挂了怎么办？
8. 日志和 Trace 会不会把 Token 打出去？

真正的后端能力，是在失败和攻击条件下仍然守住身份、权限与数据边界。

## 后续归档

本次内容已进一步整理到：

- `lessons/10-auth-security.md`
- `notes/authentication-cheatsheet.md`
- `notes/glossary.md`
- `notes/knowledge-map.md`
