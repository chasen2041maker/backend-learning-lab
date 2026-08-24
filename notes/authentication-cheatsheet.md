# 认证与鉴权速查图

这份文件用于复习，不代替 `lessons/10-auth-security.md`。

## 一句话分清

```text
Cookie       = 浏览器保存/自动携带数据的机制
Session      = 服务端保存登录会话状态
Session ID   = 找到 Session 的不透明标识
Token        = 凭证的统称
Bearer       = “持有这个 Token 就能用”的认证方案
JWT          = Token 的一种结构化格式
Access Token = 调 API 的短期凭证
Refresh Token= 换取新 Access Token 的长期高价值凭证
```

## 两种常见登录形态

### Session

```text
登录
 -> 服务端创建 Session
 -> 返回 Session ID
 -> 浏览器 Cookie 保存 Session ID
 -> 后续请求自动带 Cookie
 -> 服务端查 Session Store
```

### Token

```text
登录
 -> 服务端签发 Access Token
 -> 客户端携带
 Authorization: Bearer <token>
 -> 服务端验证 Token
 -> 产生可信 Principal
```

## JWT

```text
Header.Payload.Signature
```

- Header：算法等元数据；
- Payload：Claims；
- Signature：防篡改/验证签发方；
- 默认不是加密；
- Base64URL 编码不等于保密。

常见 Claims：

```text
iss  谁签发
sub  主体是谁
aud  给谁使用
exp  何时过期
nbf  何时之前不能用
iat  何时签发
jti  Token ID
```

## Access + Refresh

```text
Access Token
短命
每次调用 API

Refresh Token
长命
只用于刷新 Access Token
```

Refresh Token 通常比 Access Token 更敏感，应支持服务端撤销；常见做法是 rotation。

## Authentication vs Authorization

```text
Authentication
你是谁？
    |
    v
Principal

Authorization
你能做什么？
    |
    +-- role
    +-- permission
    +-- owner
    +-- tenant
```

## 401 / 403 / 404

```text
401：没有有效身份
403：身份有效，但没有权限
404：某些 owner/tenant 场景故意隐藏资源存在性
```

## 浏览器安全

```text
HttpOnly -> JS 不能直接读 Cookie
Secure   -> 只经 HTTPS
SameSite -> 控制跨站 Cookie
XSS      -> 恶意脚本进入页面
CSRF     -> 利用浏览器自动携带凭据
CORS     -> 浏览器跨源访问策略，不是认证
```

## 密码

```text
不要：明文、可逆加密、裸 SHA-256
应该：Argon2id / bcrypt / scrypt
```

## 后端最重要的信任边界

```text
不可信：
Body.user_id
Body.tenant_id
Body.role
X-User-ID（如果公网可伪造）

可信：
经过认证系统验证后构造的 Principal
```

完整链路：

```text
Request
 -> Authentication
 -> Principal
 -> Authorization
 -> Handler
 -> Service
 -> Repository
 -> Database
```

## Session vs JWT

不要问：

```text
哪个更高级？
```

应该问：

```text
撤销要求是什么？
权限多久变化一次？
有多少服务？
浏览器还是 App？
Token 被盗怎么处理？
Identity Provider 挂了怎么办？
```

## 后端必须会的程度

必须掌握：

- Cookie / Session / Token / Bearer / JWT；
- Authentication / Authorization；
- 401 / 403；
- 密码 Hash；
- Middleware / Principal；
- owner / tenant；
- HTTPS / Secret；
- Access / Refresh Token。

工作中逐步掌握：

- Refresh Token Rotation；
- Token 撤销；
- RBAC / ABAC；
- XSS / CSRF / CORS；
- 多服务身份传播；
- OAuth 2.0 / OIDC。
