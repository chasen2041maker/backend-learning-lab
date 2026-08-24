# 当前学习接棒点

最后更新：2026-08-24

这份文件回答：

> **如果一个新的 ChatGPT / Codex 会话现在接手教学，应该从哪里继续，而不是从头重讲整个仓库？**

它是动态文件。每次出现明显学习进展、方向变化或用户明确说“更新仓库”时，可以更新这里。

---

# 当前成长阶段

当前大致处于：

```text
GROWTH_PATH S0 后端新手
        ↓
正在向 S1 API 初学者过渡
```

注意：这是当前学习切入点，不是能力标签或职位评价。

很多技术已经“见过”，但不能默认达到独立实现水平。

---

# 当前主线主题

## HTTP Request -> Response 完整生命周期

当前正在建立这一张真正可用的后端心智图：

```text
Client
→ DNS
→ IP + Port
→ TCP / TLS
→ OS / listening socket
→ Go process
→ net/http
→ *http.Request
→ Router
→ Middleware
→ Authentication
→ Principal
→ Handler
→ Service
→ Repository
→ SQL / PostgreSQL
→ HTTP Response
→ Client
```

学习者已经看到过简化版本：

```text
Client
→ Network
→ HTTP Server
→ Router
→ Middleware
→ Authentication
→ Authorization
→ Handler
→ Service
→ Repository
→ Database
```

并明确反馈：

> 很多后端概念目前只有模糊印象，希望每个第一次出现的概念都讲得更细，通过不断连接小细节加深印象。

因此新的教学会话**不要直接跳到 `context.Context`、数据库事务或框架**，先把这条请求生命周期讲扎实。

---

# 当前讲解应从哪里继续

优先继续/复核下面这些概念，按数据流顺序讲。

## A. 一条 HTTP Request 本身

确保能真正读懂：

```http
GET /api/v1/orders/123 HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJ...
Accept: application/json
```

需要能解释：

- `GET` = Method；
- `/api/v1/orders/123` = Path；
- `123` 可能是 Path Parameter；
- `HTTP/1.1` 是协议版本；
- `Host` 是什么；
- Header 是什么；
- `Authorization: Bearer ...` 如何连接到 Token/JWT；
- `Accept` vs `Content-Type`；
- GET 常见为什么没有 Body。

不要假设这些都已经完全掌握；可以通过用户复述判断。

## B. Client 与 Network

继续建立：

```text
Browser / curl / App / another service
= HTTP Client
```

然后解释：

```text
Domain
→ DNS
→ IP
→ Port
→ connection
```

需要特别建立：

- Client 不等于前端页面；
- 攻击者不需要使用前端，可以直接调用 API；
- IP 与 Port 分别解决什么；
- `127.0.0.1` 是 loopback；
- `connection refused` 意味着请求通常还没到 HTTP Handler。

## C. TCP / TLS / HTTP 的层级

只需要展开到后端排错所需深度：

```text
HTTP 表达 Request / Response 语义
TCP 常见情况下提供可靠有序字节流
TLS 为 HTTPS 提供加密/完整性/服务器身份认证
```

暂时不需要深入 TCP 拥塞控制、TLS 密码套件或内核网络实现。

## D. HTTP Server 与 Go `net/http`

需要真正理解：

```go
http.ListenAndServe(":8080", handler)
```

不是“直接运行 Handler”，而是概念上包含：

```text
listen
→ accept connections
→ read HTTP bytes
→ parse request
→ build *http.Request
→ dispatch to handler chain
```

重点理解：

```go
func handler(w http.ResponseWriter, r *http.Request)
```

其中：

```text
r = 这次 HTTP Request 在 Go 中的表示
w = 构造 HTTP Response 的接口
```

## E. Router

需要能回答：

```text
Router 收到什么？
主要根据什么匹配？
它最终交给谁？
404 / 405 分别代表什么？
```

核心：

```text
Method + Path
→ Handler
```

## F. Middleware

不要只记“中间件”。

需要理解：

```text
Request
→ Request ID Middleware
→ Logging Middleware
→ Authentication Middleware
→ Handler
```

并理解 wrapper / onion 模型，以及为什么横切逻辑不应该复制到每个 Handler。

## G. Authentication -> Principal

把之前已经讨论过的认证知识放回请求链：

```text
Authorization: Bearer token
↓
Authentication Middleware
↓
validate credential
↓
Principal(subject, tenant, permissions)
```

重点再次区分：

```text
客户端 body 说 user_id=42
≠
服务端验证凭证后得到 Principal.user_id=42
```

## H. Authorization

需要纠正一个过度简化：

```text
Authentication
→ Authorization Middleware
→ Handler
```

只是教学图。

真实系统中，资源级授权可能必须等拿到资源后才能判断，所以授权可能分布在：

- middleware；
- service；
- repository query scope；
- owner/tenant boundary。

## I. Handler -> Service -> Repository -> Database

最终要建立：

```text
Handler
HTTP adapter

Service
business use case

Repository
persistence boundary

Database
business facts
```

特别强调：

```text
Repository != 只是“放 SQL 的文件夹”
```

以及多租户查询为什么应尽量做到：

```sql
WHERE id = $1
  AND tenant_id = $2
```

---

# 已经讨论过，但暂时不要当成完全掌握的知识

## Authentication / JWT 系列

已经系统讨论过：

```text
Cookie
Session
Session ID
Token
Bearer
Opaque Token
JWT
JWT_SECRET
Claims
Access Token
Refresh Token
Refresh Rotation
Authentication
Authorization
Principal
RBAC / owner / tenant
401 / 403 / hidden 404
XSS / CSRF / CORS
```

对应：

- [`lessons/10-auth-security.md`](../lessons/10-auth-security.md)
- [`notes/authentication-cheatsheet.md`](../notes/authentication-cheatsheet.md)
- [`notes/learning-journal/2026-08-24-auth-jwt-session.md`](../notes/learning-journal/2026-08-24-auth-jwt-session.md)

状态建议：**概念已经建立初步网络，但需要在真实 HTTP 请求链和后续代码中反复连接，才能稳固。**

## Go

已经接触过基础语法、interface、goroutine、channel、JSON、`net/http` 等，但不要因此直接按熟练 Go 后端工程师讲课。

遇到 Go 代码时：

```text
先讲调用链 / 数据流
再讲关键语法
```

不要只逐行翻译。

---

# 当前最近的下一里程碑

在进入 `context.Context` 深入学习前，应该先能不看答案完成以下复述。

## 1. 读懂请求

看到：

```http
GET /api/v1/orders/123 HTTP/1.1
Host: api.example.com
Authorization: Bearer xxx
Accept: application/json
```

能逐项解释。

## 2. 画请求链

至少能自己画：

```text
Client
→ Network
→ HTTP Server
→ Router
→ Middleware
→ Handler
→ Service
→ Repository
→ Database
```

并能把它展开一层。

## 3. 错误定位

能区分：

```text
DNS failure
connection refused
TLS error
404
405
400/422
401
403
409
500/503
```

不要求背所有状态码，而要知道这些错误大概说明请求走到了哪里。

## 4. 分层职责

能用自己的话回答：

```text
Router 为什么存在？
Middleware 为什么存在？
Handler 为什么不应该塞满 SQL？
Service 负责什么？
Repository 为什么不是简单的 SQL 文件夹？
```

达到这里以后，下一自然主题是：

# `context.Context`

因为此时可以把它放到已有请求链中：

```text
HTTP Request
↓
Context(deadline / cancel / request-scoped metadata)
↓
Handler
↓
Service
↓
Repository
↓
DB / downstream
```

然后再连接 goroutine、timeout、cancel、client disconnect、DB query cancellation。

---

# 新会话教学规则

新的 GPT 接手时：

1. 先读 [`../LEARNER_PROFILE.md`](../LEARNER_PROFILE.md)；
2. 不要从整个后端史重新讲起；
3. 从本文件当前 checkpoint 继续；
4. 如果用户已经能准确复述某一段，就快速通过，不机械重复；
5. 如果用户说“这个我还是模糊”，立即降速展开，不要继续堆新术语；
6. 每个新概念第一次出现时，说明：定义、为什么、输入、职责、输出、失败、与前后概念关系；
7. 最新用户消息永远优先于本文件；如果明显进步，下一次“更新仓库”时更新 checkpoint。

---

当前一句话接棒说明：

> **继续把一次真实 HTTP 请求从浏览器一路讲到 Go `net/http`、Router、Middleware、Handler、Service、Repository、Database；讲细，不要假设名词已经掌握；等这条链能独立复述后，再深入 `context.Context`。**