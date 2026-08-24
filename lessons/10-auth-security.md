# 第 10 课：认证、授权与安全边界——从 Cookie/Session 到 JWT/Refresh Token

这节课解决一个后端最常见、也最容易被教程讲乱的问题：**用户登录以后，后端到底凭什么知道“你是谁”，又凭什么决定“你能做什么”？**

本课不要求你手写密码学，也不要求现在就做一套生产登录系统。目标是先建立正确的后端模型：以后看到 Cookie、Session、Bearer、JWT、Access Token、Refresh Token、RBAC、OAuth 时，知道它们各自处在哪一层，为什么存在，失败时会发生什么。

如果只想快速复习，先看 [认证与鉴权速查图](../notes/authentication-cheatsheet.md)。

## 1. 先把最容易混淆的词分层

先记住这一句：

> Cookie 是浏览器机制；Session 是服务端维护会话状态的方法；Token 是凭证的统称；Bearer 是一种“持有者凭证”的认证方案；JWT 是 Token 的一种标准格式。

它们不是同一维度的概念。

| 概念 | 它是什么 | 典型例子 |
| --- | --- | --- |
| Cookie | 浏览器保存并按规则自动携带少量数据的 HTTP 机制 | `session_id=abc123` |
| Session | 服务端保存的一份会话状态 | `abc123 -> user_id=42` |
| Session ID | 客户端用来找到 Session 的不透明标识 | `abc123` |
| Token | 认证/授权凭证的统称 | 随机字符串、JWT、OAuth Access Token |
| Bearer | HTTP `Authorization` 中常见的认证方案 | `Authorization: Bearer <token>` |
| JWT | 一种可携带 Claims 的 Token 格式 | `header.payload.signature` |
| Access Token | 调 API 的短期凭证 | 15 分钟有效的 JWT 或 opaque token |
| Refresh Token | 换取新 Access Token 的长期高价值凭证 | 随机高熵字符串 |

所以这些表达都可能成立：

```text
Cookie + Session ID + 服务端 Session

Authorization: Bearer + opaque Access Token

Authorization: Bearer + JWT Access Token

HttpOnly Cookie + Refresh Token
```

不要把“Cookie 登录”和“JWT 登录”理解成两个严格对立的技术名词。Cookie 解决的是浏览器如何保存/发送数据；JWT 解决的是一种 Token 如何表达和验证。

## 2. 为什么登录之后还需要 Session 或 Token

HTTP 请求天然是一次一次到达服务器的。第一次登录时，用户可以用用户名和密码证明身份：

```text
POST /login
username + password
        |
        v
服务器验证密码
        |
        v
确认：这是 user_42
```

但后面的每个请求都重新发送密码是不合理的。密码是长期秘密，暴露面应该尽量小。

因此登录成功后，服务器通常签发或建立一个**临时凭证**：

```text
第一次：用户名 + 密码 -> 登录成功 -> 获得临时凭证
以后：临时凭证 -> API
```

这个临时凭证可能是 Session ID，也可能是 Access Token。

## 3. Authentication 和 Authorization 必须分开

### Authentication：认证

回答：**你是谁？**

```text
Bearer Token
    |
    v
验证成功
    |
    v
Principal(subject=user_42, tenant=tenant_a)
```

### Authorization：授权

回答：**你能做什么？**

user_42 即使已经通过认证，也不代表能执行：

```http
DELETE /api/v1/admin/users/99
```

所以：

```text
Authentication 成功
Authorization 仍然可能失败
```

## 4. Cookie 到底是什么

服务器可以返回：

```http
Set-Cookie: session_id=abc123
```

浏览器保存后，在符合 Domain、Path、Secure、SameSite 等规则时，可以自动携带：

```http
Cookie: session_id=abc123
```

Cookie 本身不知道 `abc123` 是什么。它可能是 Session ID、偏好设置，甚至某种 Token。

因此：

```text
Cookie != Session
Cookie != JWT
```

Cookie 只是浏览器/HTTP 层面的保存和发送机制。

## 5. Session：状态主要在服务器

经典 Session 登录流程：

```text
客户端                         服务器
  |                              |
  | POST /login                  |
  | username/password ---------->|
  |                              | 验证密码
  |                              | 创建 Session
  |                              | abc123 -> user_42
  |<-- Set-Cookie:               |
  |    session_id=abc123          |
```

服务器可能把 Session 放在进程内存、Redis 或数据库。

下一次请求：

```text
Cookie: session_id=abc123
        |
        v
服务器查 Session Store
        |
        v
abc123 -> user_42
```

### Session 的优势

服务端控制力强。用户退出或被封禁时，可以撤销 Session，让后续请求立即失败。

### Session 的代价

需要考虑多实例共享、Session Store 可用性、TTL、容量与连接预算。

所以 Session 不是“老技术”，JWT 也不是天然“更高级”。

## 6. Token 和 Bearer Token

Token 是宽泛概念：

```text
Token
├─ opaque random token
├─ JWT
├─ OAuth access token
└─ 某些 API credential
```

Bearer 常出现在：

```http
Authorization: Bearer eyJ...
```

拆开看：

```text
Authorization  -> HTTP Header
Bearer         -> 认证方案
后面的字符串   -> Token
```

Bearer 的核心语义可以粗略理解为：谁持有这个凭证，谁就能使用它。

因此 Token 泄露后，攻击者往往不需要破解，只需原样重放。

注意：

```text
Bearer Token != JWT
```

Bearer 后面也可以是不透明随机字符串。

## 7. JWT 到底是什么

JWT 全称 JSON Web Token。常见紧凑形式：

```text
xxxxx.yyyyy.zzzzz
```

通常分为：

```text
Header.Payload.Signature
```

Header 示例：

```json
{"alg":"HS256","typ":"JWT"}
```

Payload 示例：

```json
{
  "sub": "user_42",
  "tenant_id": "tenant_a",
  "exp": 1780000000
}
```

Signature 用于验证 Token 没被未经授权地修改，并且来自持有正确签名密钥的一方。

## 8. JWT 默认不是加密

常见 JWT 的 Header/Payload 使用 Base64URL 编码。**编码不是加密。**

拿到 Token 的人通常可以看到 Payload。

```text
签名 -> 保护完整性和真实性
加密 -> 保护内容机密性
```

所以不要把密码、JWT Secret、API Secret 或不必要的敏感个人数据塞进普通可读 Claims。

## 9. `JWT_SECRET` 到底负责什么

如果使用 HS256 这类 HMAC 算法，服务器可能配置：

```text
JWT_SECRET=<high-entropy-secret>
```

签发和验证都依赖这个共享秘密。

如果攻击者拿到了 Secret，就可能构造自己想要的 Claims，并生成服务器会接受的签名。

所以 Secret：

- 不写死在源码；
- 不提交 GitHub；
- 通过 Secret 管理或环境变量提供；
- 缺失时启动失败；
- 错误信息不能打印 Secret 值；
- 生产环境要考虑轮换。

但并不是所有 JWT 都有 `JWT_SECRET`。非对称签名使用私钥/公钥模型：签发方保护私钥，验证方可以持有公钥。

## 10. 验 JWT 不能只看 Signature

生产验证通常还要检查：

- `exp`：是否过期；
- `nbf`：是否还没到允许使用时间；
- `iss`：是否来自期望签发方；
- `aud`：是否签给当前系统；
- 允许的签名算法；
- 必需 Claims 是否存在且格式正确。

常见 Claims：

| Claim | 含义 |
| --- | --- |
| `iss` | issuer，谁签发 |
| `sub` | subject，Token 主体是谁 |
| `aud` | audience，给谁使用 |
| `exp` | expiration，何时过期 |
| `nbf` | not before，何时之前不能用 |
| `iat` | issued at，何时签发 |
| `jti` | JWT ID，可选唯一标识 |

还要注意 Claims 会变旧。例如 Token 里写 `role=admin`，但五分钟后该权限被撤销。长寿命 Token 仍可能携带旧角色。

## 11. Access Token 和 Refresh Token

Access Token 用于真正访问 API：

```http
Authorization: Bearer <access-token>
```

它通常应该较短命。

Refresh Token 用来换新的 Access Token：

```text
登录
 |
 +--> Access Token  -> 短期访问 API
 |
 +--> Refresh Token -> 较长期换新 Access Token
```

重要：

```text
Access Token 不一定是 JWT
Refresh Token 也不一定是 JWT
```

实际系统经常把 Refresh Token 设计成随机高熵 opaque token，并在服务端保存它的哈希或会话记录。

## 12. Refresh Token Rotation

常见设计：每刷新一次都更换 Refresh Token。

```text
R1
 |
 | 刷新
 v
A2 + R2
同时 R1 失效
```

如果 R1 后面再次出现，可能说明泄露或重放。服务器可以撤销整个 token family 或要求重新登录。

## 13. Logout 为什么在 JWT 世界里更麻烦

Session：

```text
logout -> 删除服务端 Session -> 马上失效
```

纯自包含 JWT：客户端删除 Token，只代表这个客户端不再保存它。如果攻击者早就复制一份，而且 Token 还没过期，服务器仍可能接受。

常见策略：

- Access Token 短 TTL；
- Refresh Token 服务端可撤销；
- token/session version；
- denylist；
- 高风险操作重新校验当前权限。

所以“JWT 完全无状态，因此永远更简单”是不可靠的结论。

## 14. Cookie、localStorage 与浏览器存储

### Cookie

常见安全属性：

```text
HttpOnly -> JavaScript 不能直接读取
Secure   -> 只通过 HTTPS 发送
SameSite -> 控制跨站场景下发送规则
```

### localStorage

JavaScript 可直接读取，但浏览器不会自动把它变成 Authorization Header。

发生 XSS 时，localStorage 中的 Token 更容易被恶意脚本直接读取并外传。

HttpOnly 也不是“XSS 免疫”。攻击者若能执行页面脚本，仍可能借用户当前会话发起操作。

## 15. XSS 和 CSRF 不要混为一谈

### XSS

攻击者让恶意 JavaScript 在受信任页面中执行。

### CSRF

利用浏览器自动携带某些凭据的行为，诱导用户发出攻击者想要的请求。

常见防护包括合理的 SameSite、CSRF Token、Origin/Referer 校验等。

```text
XSS 重点：恶意脚本进入页面
CSRF 重点：浏览器自动带凭据完成被诱导请求
```

## 16. HTTPS 为什么仍然必须要有

JWT 有签名，不代表网络传输安全。

攻击者如果直接截获：

```text
Authorization: Bearer abc123
```

根本不需要修改，直接重放即可。

所以：

```text
JWT signature != HTTPS
```

## 17. 密码为什么要 Hash，而不是可逆加密

密码验证通常不需要恢复原始密码，所以应该使用专门的 password hashing algorithm，例如：

- Argon2id；
- bcrypt；
- scrypt。

不要用裸 SHA-256 直接保存用户密码，因为快速 Hash 反而方便攻击者高速猜测。

Salt 是每个密码 Hash 使用的随机值，使相同密码不会得到相同存储结果，并抵抗预计算攻击。成熟库会正确处理 Salt 和参数。

数据库保存：

```text
password_hash
```

而不是明文 password。

## 18. Middleware：把认证从每个 Handler 中抽出来

常见请求链：

```text
HTTP Request
    |
    v
Request ID Middleware
    |
    v
Logging Middleware
    |
    v
Authentication Middleware
    |
    v
Authorization / Resource Check
    |
    v
Handler
    |
    v
Service
    |
    v
Repository
```

认证中间件成功后产生服务端可信 Principal，例如：

```text
Principal
├─ subject: user_42
├─ tenant_id: tenant_a
└─ auth context / scopes
```

后面的代码使用 Principal，而不是再次相信客户端提交的 `user_id` / `tenant_id`。

## 19. Go 的 `context.Context` 在这里干什么

请求 Context 可以沿调用链传播：deadline、cancel signal、request ID、当前经过验证的 Principal 等少量 request-scoped metadata。

```text
HTTP Request
  context
    |
    +-- request_id
    +-- principal
    +-- deadline
         |
         v
      Handler -> Service -> Repository
```

但 Context 不是万能 map。不要把普通业务参数和整个 Service 随便塞进去。

## 20. 不要相信客户端

错误：客户端 Body 自报：

```json
{
  "user_id": 42,
  "tenant_id": "tenant_a",
  "role": "admin",
  "product_id": 99
}
```

客户端可以用 curl、Postman、开发者工具或脚本随意修改请求。

正确思路：

```text
Token / Session
      |
      v
服务端认证
      |
      v
Principal(user_42, tenant_a)
```

Body 只提供业务输入，例如：

```json
{"product_id":99}
```

后端组合“可信 Principal + 已验证业务输入”。

## 21. 前端权限控制不是后端权限控制

前端隐藏删除按钮只能改善体验。攻击者仍可手工请求：

```http
DELETE /api/v1/users/99
```

真正 Authorization 必须在服务端。

## 22. RBAC、ABAC、owner 和 tenant

RBAC：基于角色授权。

```text
Reader -> read
Editor -> read + write
Admin  -> read + write + admin actions
```

ABAC：基于属性组合判断，例如部门、等级、资源属性等。

Ownership：资源是否属于当前主体。

Tenant boundary：多租户系统中 `Principal.tenant_id` 必须来自可信认证上下文，并进入 Repository 查询条件。

本仓库统一把跨租户资源查询隐藏成 404，是为了避免泄露资源存在性；这不代表所有授权失败都应该返回 404。

## 23. 401、403 和有意的 404

### 401 Unauthorized

通常表示没有有效认证身份：缺 Token、Token 无效、Token 过期等。

### 403 Forbidden

服务器知道你是谁，但你没有当前操作所需权限。

### 404 Not Found

在 owner/tenant 隔离中，有些系统故意统一返回 404，避免泄露资源存在性。

## 24. 服务之间传播身份时不要信任任意 Header

危险做法：公网客户端发送：

```http
X-User-ID: admin
X-Tenant-ID: tenant_b
```

而下游直接相信。

如果 Gateway 验证外部 Token 后通过内部 Header/RPC metadata 传播身份，必须保证：

- 边缘层删除客户端伪造的同名 Header；
- 下游只信任受保护调用来源；
- 服务到服务本身也有认证；
- 权限边界不能只靠“这个 Header 看起来像内部字段”。

## 25. CORS 不是认证，也不是 API 防火墙

CORS 是浏览器跨源访问策略。

curl、Postman、服务器脚本不会因为浏览器 CORS 配置就失去访问 API 的能力。

所以：

```text
CORS != Authentication
CORS != Authorization
```

## 26. Session vs JWT：没有永远正确的赢家

| 问题 | Session + opaque ID | 自包含 JWT Access Token |
| --- | --- | --- |
| 服务端保存会话状态 | 通常是 | 验证 Access Token 本身可不查 Session |
| 每次请求查 Session Store | 通常需要 | 不一定 |
| 立即撤销 | 相对直接 | 需要短 TTL/denylist/version/refresh state 等 |
| Claims 变旧 | 服务端状态较易更新 | 长寿命 Token 更容易携带旧 Claims |
| 多服务本地验证 | 需要共享/查询状态 | 公钥验证等方式较方便 |

真正的问题不是“哪个高级”，而是撤销要求、服务边界、浏览器架构、身份提供方、权限变化速度和故障模型是什么。

## 27. API Key、OAuth 2.0、OIDC

API Key 常用于识别调用 API 的应用、项目或开发者。它不等于 JWT。

OAuth 2.0 主要是授权框架。

OpenID Connect（OIDC）在 OAuth 2.0 之上增加身份层，用于登录/身份认证场景。

现阶段记住：

```text
OAuth 2.0 -> 授权框架
OIDC      -> 身份层
JWT       -> Token 格式
```

ID Token 经常是 JWT，但 Access Token 不保证一定是 JWT。

## 28. 一个完整的认证请求链

```text
Browser / App
      |
      | HTTPS
      | Cookie 或 Authorization: Bearer ...
      v
Gateway / HTTP Server
      |
      v
Authentication
      |
      | 产生可信 Principal
      v
Authorization
      |
      | role / scope / owner / tenant
      v
Handler
      |
      v
Service
      |
      | 业务不变量
      v
Repository
      |
      | tenant/owner 条件不能丢
      v
Database
```

## 29. 生产认证系统要问的失败问题

读任何认证实现时，至少问：

1. Token 被偷了怎么办？
2. Access Token 过期怎么办？
3. Refresh Token 被重放怎么办？
4. 用户修改密码后旧会话是否继续有效？
5. 管理员封禁用户后多久生效？
6. 全设备退出如何实现？
7. 签名密钥怎么轮换？
8. 服务时间漂移会不会影响 `exp` / `nbf`？
9. Session Store / Identity Provider 不可用时怎么失败？
10. 日志、Trace、错误信息会不会泄露 Token？
11. role/tenant 变化后旧 Claims 怎么处理？
12. 重试是否会让刷新/撤销发生异常重复？

后端工程的重点不是“能生成 JWT”，而是异常情况下仍然守住身份和权限边界。

## 30. 最小安全检查清单

- 密码使用成熟 password hashing algorithm；
- 不记录明文密码、Access Token、Refresh Token、JWT Secret；
- 生产流量使用 HTTPS；
- Token 有明确 TTL；
- JWT 验证期望算法、签名和必要 Claims；
- 关键 Secret 缺失时启动失败；
- Cookie 根据场景配置 `HttpOnly`、`Secure`、`SameSite`；
- Cookie 写操作考虑 CSRF；
- 前端隐藏按钮不代替服务端授权；
- `user_id` / `tenant_id` 不从不可信 Body 获得；
- owner/tenant 条件一路进入数据访问边界；
- Refresh Token 有服务端撤销/轮换策略；
- 401/403/404 行为与 API 契约一致；
- 认证失败不泄露内部 Secret 或不必要的账户信息。

## 31. 本仓库练习：先证明边界，不急着造登录系统

运行已有授权微实验：

```powershell
python -m unittest discover -s exercises/reliability-labs/tests -v
```

打开：

- `exercises/reliability-labs/authorization.py`
- 对应 tests

回答：

1. Authentication 在哪里产生可信身份？
2. Authorization 在哪里检查 tenant / permission / resource？
3. 如果把 `tenant_id` 改成客户端 Body 提供，会出现什么攻击？
4. 为什么 Agent Tool 被模型选择仍然不代表它有执行权限？
5. 哪些写操作需要确认和幂等键？

第 4 课的教学 Token 不是生产 JWT，但它仍然可以证明“可信 Principal 必须由服务器建立”这个不变量。

## 32. 不看文档复述

完成本课后，关闭文档，用自己的话回答：

1. Cookie、Session、Token、Bearer、JWT 分别是什么？
2. 为什么 JWT Payload 可读却仍能防篡改？
3. `JWT_SECRET` 泄露为什么危险？它为什么只适用于某些签名模型？
4. Access Token 和 Refresh Token 为什么分开？
5. Refresh Token Rotation 解决什么风险？
6. 为什么删除客户端 JWT 不一定等于服务端立即注销？
7. 为什么前端隐藏按钮不能代替后端 Authorization？
8. 401、403、跨租户 404 分别何时出现？
9. 为什么 CORS 不能保护一个没有认证的 API？
10. 为什么密码应该使用 Argon2id/bcrypt/scrypt，而不是裸 SHA-256？
11. Middleware 和 Go `context.Context` 在认证链里分别负责什么？
12. Session 和 JWT 哪个更好？为什么正确答案通常是“看系统约束”？

## 33. 这部分对后端是不是必学

### 必须掌握

- HTTP Header / Cookie 基础；
- Authentication / Authorization；
- Session / Token / Bearer / JWT 的关系；
- 401 / 403；
- 密码 Hash；
- Middleware 与可信 Principal；
- owner / tenant 服务端校验；
- HTTPS 和 Secret 基础；
- Access/Refresh Token 基本职责。

### 工作中逐步熟练

- Refresh Token Rotation；
- Token 撤销与密钥轮换；
- RBAC/ABAC；
- XSS/CSRF/CORS 的真实边界；
- 多服务身份传播；
- Identity Provider 故障与审计。

### 以后按项目深入

- OAuth 2.0 Authorization Code + PKCE 等流程；
- OIDC Discovery / JWKS；
- 企业 SSO；
- mTLS / workload identity；
- 更复杂策略引擎。

学习顺序仍遵守本仓库原则：**先理解为什么和失败模式，再学框架怎么写。**
