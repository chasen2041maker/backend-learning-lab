# 当前学习接棒点

最后更新：2026-08-26

这份文件回答：

> **如果一个新的 ChatGPT / Codex 会话现在接手教学，应该从哪里继续，而不是从头重讲整个仓库？**

它是动态文件。出现明显学习进展、方向变化，或用户明确说“更新仓库/沉淀仓库”时，应更新这里。

---

# 当前成长阶段

当前大致处于：

```text
GROWTH_PATH S0 后端新手
        ↓
正在向 S1 API 初学者过渡
```

注意：这是当前学习切入点，不是能力标签或职位评价。

很多技术已经“见过”，但不能因此默认达到独立实现水平。

---

# 当前主线主题

## HTTP Request -> Response 完整生命周期

当前正在建立这张可用于写代码、读代码和排错的后端心智图：

```text
Client
→ Domain / DNS
→ IP + Port
→ listening socket
→ TCP connection
→ TLS（HTTPS）
→ OS network stack / socket
→ Go process
→ net/http
→ *http.Request
→ ServeMux / Router
→ Middleware
→ Authentication
→ Principal
→ Authorization
→ Handler
→ Service
→ Repository
→ SQL / PostgreSQL
→ HTTP Response
→ Client
```

2026-08-26 对话中的高密度整理见：

- [`../notes/learning-journal/2026-08-26-http-network-go-handler.md`](../notes/learning-journal/2026-08-26-http-network-go-handler.md)

---

# 已通过本轮对话复述的部分

以下内容已经能在提示很少的情况下给出正确方向，但仍然只代表“心智模型初步建立”，不代表已经独立编码熟练。

## 1. Request line / Header

已经能区分：

```text
Method
Path
Route Pattern
Path Parameter
HTTP version
Host
Authorization Header
Accept
Content-Type
```

关键关系：

```text
Content-Type
= 当前 Body 是什么格式

Accept
= Client 希望收到什么格式
```

以及：

```text
Authorization Header
= 携带 Credential
≠ Authorization 已经通过
```

## 2. Router 与 404 / 405

已经纠正并能复述：

```text
Method + Route Pattern
→ 选择 Handler

Path Parameter
→ 决定这个 Handler 处理哪个具体资源
```

```text
Path 匹配不到
→ 404

Path 能匹配，但 Method 不支持
→ 405
```

## 3. Authentication / Authorization

已经能区分：

```text
Authentication
= 你是谁？

Authorization
= 你能做什么？
```

并理解：

```text
Credential
→ Authentication
→ Principal
→ Authorization
```

`401` 与 `403` 的分层关系已经建立，但后续仍需要在真实代码中反复连接。

## 4. Client / DNS / IP / Port / listen

已经理解：

```text
Client
= 主动发请求的一方
≠ 前端页面的同义词
```

以及：

```text
Domain
→ DNS
→ IP
→ Port
→ connection
```

能够用自己的话解释 `listen`：进程通过操作系统在某个 `IP:Port` 等待外部连接。

## 5. TCP 与 HTTP

已经明确：

```text
TCP Connection
≠ HTTP Request
```

当前心智模型：

```text
TCP
= 为应用提供可靠、有序的字节流

HTTP
= 定义 Request / Response 的格式和语义
```

不需要现在深入拥塞控制、sequence number 等底层算法。

## 6. TLS / HTTPS / Nginx

已经讲过并建立初步连接：

```text
HTTP
↓
TLS
↓
TCP
```

TLS 主要解决：机密性、完整性、服务器身份验证。

已经知道：

```text
JWT Signature
≠ 网络传输加密
```

因此 JWT 仍需要 HTTPS。

Nginx 当前只需掌握：

```text
Reverse Proxy
TLS termination
Load Balancing
```

以及：

```text
Nginx ≠ API Gateway 这个架构概念本身
```

## 7. OS / Socket / Process / Go `net/http`

已经建立：

```text
Network
→ OS network stack
→ Socket
→ Go Process
→ net/http
```

能区分：

```text
Port
= 编号

Socket
= OS 管理、程序用于网络通信的对象/端点
```

并理解：

```go
http.ListenAndServe(":8080", handler)
```

概念上不是“直接执行 Handler”，而是封装了监听、接受连接、读取/解析 HTTP、构造 `*http.Request`、调度 Handler、写回 Response 等过程。

## 8. `http.Handler` / `HandlerFunc`

这是当前最新通过复述的点。

核心接口：

```go
type Handler interface {
    ServeHTTP(ResponseWriter, *Request)
}
```

已经能用自己的话说出：

> `HandlerFunc` 有 `ServeHTTP`，因此满足 `http.Handler`；它把普通 `func(w, r)` 对接/适配到 Go HTTP Handler 体系。

需要继续通过真实 Go 代码巩固 `ServeMux -> Handler -> ServeHTTP` 调用链。

---

# 当前精确接棒点

**不要重新从 DNS、TCP、JWT 开始长篇复习。**

除非复述明显退化，否则下一步直接进入：

# Middleware

重点真正讲清：

```text
Request
↓
Request ID Middleware
↓
Logging Middleware
↓
Authentication Middleware
↓
Handler
```

不能只说“中间件就是在中间执行”。需要解释：

1. Middleware 输入通常也是一个 `http.Handler`；
2. Middleware 返回一个新的 `http.Handler`；
3. wrapper / onion 模型为什么成立；
4. `next.ServeHTTP(w, r)` 到底表示什么；
5. 为什么可以在 `next` 前做认证，在 `next` 后统计耗时；
6. 为什么 Request ID、Logging、Authentication 等横切逻辑不应该复制到每个业务 Handler；
7. Middleware 与 Router、Handler 的真实组合顺序如何变化。

建议用最小 Go 例子，但仍然先讲调用链和数据流，再讲语法。

---

# Middleware 之后的顺序

Middleware 讲通后继续：

```text
Handler
→ Service
→ Repository
→ Database
```

必须能用自己的话解释：

```text
Handler
= HTTP adapter

Service
= business use case / business rules

Repository
= persistence boundary

Database
= business facts / source of truth
```

特别强调：

```text
Repository != 只是“放 SQL 的文件夹”
```

以及资源/tenant 范围为什么应该进入持久化边界，例如：

```sql
WHERE id = $1
  AND tenant_id = $2
```

---

# 进入 `context.Context` 前的验收

不要因为已经“讲过”就直接进入 `context.Context`。

先做一次关闭文档复述，至少能完整说明：

```text
Client
→ DNS
→ IP + Port
→ TCP / TLS
→ OS / Socket
→ Go net/http
→ Request
→ Router
→ Middleware
→ Authentication / Principal / Authorization
→ Handler
→ Service
→ Repository
→ DB
→ Response
```

并能回答：

```text
为什么 connection refused 不是 404？
为什么 TLS error 还没到 Handler？
为什么 Path 对、Method 错是 405？
为什么 Authorization Header 不等于授权成功？
为什么 TCP Connection 不等于 HTTP Request？
为什么 HandlerFunc 能当 Handler？
Middleware 为什么适合横切逻辑？
Handler 为什么不应该直接塞满 SQL？
```

达到这里以后，下一自然主题才是：

# `context.Context`

此时再连接：

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

然后再连接 goroutine、timeout、client disconnect、DB query cancellation。

---

# 新会话教学规则

新的 GPT 接手时：

1. 先读 [`../LEARNER_PROFILE.md`](../LEARNER_PROFILE.md)；
2. 再读本文件和本轮 learning journal；
3. 不要从整个后端史重新讲起；
4. 从 Middleware 这个 checkpoint 继续；
5. 用户能准确复述的部分快速通过，不机械重复；
6. 用户说模糊时立即降速，解释定义、为什么、输入、职责、输出、失败、前后关系；
7. Go 代码仍然坚持“先调用链 / 数据流，再关键语法”；
8. 最新用户消息永远优先于本文件。

当前一句话接棒说明：

> **HTTP 请求从 Client、DNS、TCP/TLS、OS/Socket 到 Go `net/http`、`*http.Request`、Router、`http.Handler` / `HandlerFunc` 已经建立第一轮心智模型；下一步直接把 Go Middleware 的 wrapper/onion 调用链讲透，再进入 Handler -> Service -> Repository -> DB，完成整链复述后才进入 `context.Context`。**
