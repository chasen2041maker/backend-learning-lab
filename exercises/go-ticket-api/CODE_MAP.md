# Go Ticket API 代码地图

这份文件不逐行解释语法，而是回答：

```text
请求从哪里进来？
谁调用谁？
每个文件负责什么？
每层不应该知道什么？
错误和 context 怎样传播？
```

当前代码位于：

```text
exercises/go-ticket-api/
```

---

# 1. 一次 API 请求的总调用链

以：

```http
GET /api/v1/tickets/{id}
Authorization: Bearer lab-token-tenant-a
```

为例：

```text
Client
↓
http.Server
↓
Handler: ticket.NewHTTPHandler(...)
↓
RequestContext Middleware
↓
root ServeMux
↓
Authenticate Middleware（仅 /api/v1/）
↓
api ServeMux
↓
Handler.get
↓
principalFromContext
↓
r.PathValue("id")
↓
Service.Get
↓
Repository.Get
↓
Memory map（当前实现）
↓
Ticket / error
↓
Service
↓
Handler
↓
writeJSON / writeError
↓
http.ResponseWriter
↓
Client
```

`GET /health` 的链更短：

```text
RequestContext
→ root ServeMux
→ health Handler
```

它不会经过 `Authenticate`。

---

# 2. 目录地图

```text
cmd/server/main.go
internal/ticket/
├─ errors.go
├─ handler.go
├─ handler_test.go
├─ identity.go
├─ model.go
├─ repository.go
├─ service.go
└─ service_test.go
```

---

# 3. `cmd/server/main.go`：进程与依赖组装

职责：

```text
创建 logger
创建 Repository
创建 Service
创建 HTTP Handler
配置 http.Server
启动监听
接收退出信号
graceful shutdown
```

核心组装：

```text
MemoryRepository
→ Service
→ NewHTTPHandler
→ http.Server.Handler
```

它应该知道：

- 应用由哪些主要组件组成；
- Server 监听地址与 timeout；
- 启动和停止生命周期。

它不应该知道：

- Ticket title 的业务验证；
- JSON 输入字段；
- tenant 查询细节；
- 某个 HTTP status 对应哪个业务错误。

阅读时先看：

```go
repository := ticket.NewMemoryRepository()
service := ticket.NewService(repository)
server.Handler = ticket.NewHTTPHandler(service, logger)
```

不要一开始被 signal、goroutine 和 shutdown 细节淹没。

---

# 4. `handler.go`：HTTP Adapter

主要职责：

```text
创建 ServeMux
注册 Method + Path
读取 Path / Query / Header / Body
严格解析 JSON
从 context 取得 Principal
调用 Service
把业务错误映射成 HTTP status + stable code
写 JSON Response
```

它应该知道：

- HTTP Method、Path、Header、Body；
- `http.ResponseWriter` 与 `*http.Request`；
- status code、JSON、request ID；
- Service 的输入输出与业务错误。

它不应该知道：

- map 怎样加锁；
- PostgreSQL SQL；
- Ticket 关闭的完整业务状态机应该怎样实现；
- JWT 密码学细节。

关键入口：

```text
NewHTTPHandler
NewHandler
Handler.Register
Handler.create / get / list / close
```

---

# 5. `NewHTTPHandler`：真实 Router + Middleware 组合

当前结构：

```text
root ServeMux
├─ GET /health -> health
└─ /api/v1/ -> Authenticate(api ServeMux)

整个 root 外面再包：
RequestContext(root)
```

所以 API 请求的真实顺序是：

```text
RequestContext
→ root ServeMux
→ Authenticate
→ api ServeMux
→ endpoint Handler
```

这正是当前 Middleware 章节的主要参考。

---

# 6. `RequestContext`：Request ID Middleware

位置：

```text
handler.go
```

职责：

```text
读取或生成 X-Request-ID
↓
写入 Request Header
↓
写入 Response Header
↓
next.ServeHTTP(w, r)
```

它不关心：

- Ticket 是什么；
- 当前请求是否有权限；
- Service / Repository；
- JSON Body。

如果不调用：

```go
next.ServeHTTP(w, r)
```

后面的 Router 和 Handler 都不会执行。

---

# 7. `identity.go`：Authentication 与 Principal

`Authenticate` 的输入输出形状：

```text
输入：next http.Handler
输出：新的 http.Handler
```

请求流程：

```text
读取 Authorization Header
↓
检查 Bearer 格式
↓
查教学 Token
↓
失败 -> 401 + return
↓
成功 -> Principal
↓
context.WithValue
↓
next.ServeHTTP(w, r.WithContext(ctx))
```

这里建立的信任边界是：

```text
客户端自报 user_id / tenant_id
≠ 可信身份

Credential 经过服务端验证
→ Principal
```

`principalFromContext` 让后面的 Handler 读取已经认证的身份，而不是重新解析 Token。

---

# 8. Endpoint Handler：把 HTTP 转成用例调用

以 `Handler.create` 为例：

```text
principalFromContext
↓
decodeStrictJSON -> CreateInput
↓
Service.Create(ctx, tenantID, input)
↓
writeJSON(201, response)
```

以 `Handler.get` 为例：

```text
principalFromContext
↓
r.PathValue("id")
↓
UUID 格式验证
↓
Service.Get(ctx, id, tenantID)
↓
writeJSON(200, response)
```

Handler 的价值不是“代码入口”这么简单，而是隔离：

```text
HTTP 世界
↔
业务世界
```

---

# 9. `service.go`：Business Use Case

职责：

```text
输入规范化
业务不变量
状态转换
版本判断
调用 Repository
包装基础设施错误
```

例如 `Create`：

```text
tenant/title 验证
↓
生成 ID / time
↓
构造 Ticket
↓
Repository.Create
```

例如 `Close`：

```text
Get
↓
是否已关闭
↓
expectedVersion 是否有效
↓
当前 version 是否匹配
↓
状态变为 closed
↓
version + 1
↓
Repository.Update
```

Service 应该知道业务规则，但不应该知道：

- HTTP status；
- JSON；
- Authorization Header；
- SQL 语句；
- `ResponseWriter`。

---

# 10. `repository.go`：Persistence Boundary

`Repository` interface 定义 Service 真正需要的数据行为：

```text
Create
Get
List
Update
```

当前实现：

```text
MemoryRepository
```

它使用：

```text
map
sync.RWMutex
tenant check
expectedVersion check
context error check
```

Repository 不是“专门放 SQL 的文件夹”。它表达的是：

> Service 怎样访问和修改业务事实，而不依赖当前事实存放在 map 还是 PostgreSQL。

以后 PostgreSQL Repository 应实现同一个或经过演进的行为边界。

---

# 11. `model.go`：输入与领域状态

通常包含：

```text
CreateInput
CloseInput
Principal
Ticket
Status
```

阅读时区分：

```text
外部输入 DTO
≠
内部业务状态
```

例如 `CreateInput` 只代表 Client 可提交的字段；`TenantID` 来自认证后的 Principal，不应该让 Client 在 Body 自报。

---

# 12. `errors.go`：稳定的业务错误分类

Service / Repository 返回业务语义错误，例如：

```text
ErrInvalidInput
ErrNotFound
ErrStateConflict
ErrVersionConflict
ErrAuthentication
```

Handler 再映射：

```text
业务错误
→ HTTP status
→ stable machine-readable code
```

这样 Service 不需要知道 401 / 404 / 409。

---

# 13. Tests：每层到底证明什么

## `service_test.go`

主要证明：

```text
业务规则
状态转换
版本冲突
Repository 替身下的用例行为
```

不证明完整 HTTP Header / JSON 契约。

## `handler_test.go`

主要证明：

```text
Method / Path
Authentication
strict JSON
status / stable code
request ID
tenant isolation
HTTP response
```

当前内存测试不证明 PostgreSQL transaction 或多实例行为。

---

# 14. 一次错误怎样回来

例如 Ticket 不存在：

```text
Repository.Get
→ ErrNotFound
↓
Service.Get
→ 继续返回错误
↓
Handler.get
→ handleError
↓
404 + ticket_not_found
```

例如 Repository 发生未知错误：

```text
Repository
→ unexpected error
↓
Service
→ fmt.Errorf("...: %w", err)
↓
Handler.handleError default
↓
log internal error
↓
500 internal_error
```

客户端不会看到内部错误细节。

---

# 15. `context.Context` 怎样穿过调用链

当前已经存在：

```text
r.Context()
→ Service
→ Repository
```

Authentication 还会创建派生 Context：

```text
原 Request Context
↓
context.WithValue(..., Principal)
↓
r.WithContext(ctx)
↓
next
```

后续第 6 章会再加入 deadline / cancel 实验。

---

# 16. 当前阅读顺序

当前不要把所有文件一次读完。

按下面顺序：

```text
1. NewHTTPHandler
2. RequestContext
3. Authenticate
4. Handler.Register
5. 任选一个 endpoint Handler
6. 对应 Service method
7. 对应 Repository method
8. 对应 tests
9. 最后回 main.go 看依赖组装
```

当前第 3 章只看前 3 项。

---

# 17. 每打开一个函数先问

```text
谁调用它？
它收到什么？
它拥有哪项职责？
它不应该知道什么？
它修改了什么状态？
它把什么交给下一层？
失败怎样传播？
哪个测试证明？
```

按照这张地图读代码，框架和语法不会再把真实后端链路藏起来。
