# 第 3 章 Walkthrough：Go Middleware、`next.ServeHTTP` 与 Onion Model

当前目标不是背一个 Middleware 模板，而是彻底理解：

```go
func Middleware(next http.Handler) http.Handler
```

为什么可以把 Request ID、日志、认证等公共逻辑包在业务 Handler 外面。

真实参考：

- [`../internal/ticket/handler.go`](../internal/ticket/handler.go)：`RequestContext`
- [`../internal/ticket/identity.go`](../internal/ticket/identity.go)：`Authenticate`
- [`../CODE_MAP.md`](../CODE_MAP.md)：完整调用链

本章对应练习：

- [`../practice/03-middleware.md`](../practice/03-middleware.md)

---

# 1. 先回到 `http.Handler`

Go 标准库的核心约定：

```go
type Handler interface {
    ServeHTTP(http.ResponseWriter, *http.Request)
}
```

所以只要一个值拥有：

```go
ServeHTTP(w, r)
```

它就可以被 Go HTTP Server、ServeMux 或另一个 Middleware 统一调用。

`http.HandlerFunc` 是一个命名函数类型，标准库为它实现了 `ServeHTTP`。因此：

```go
http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    // 普通函数体
})
```

可以当作 `http.Handler`。

Middleware 正是利用这个统一接口：

```text
它接收 Handler
它返回的仍然是 Handler
所以可以继续套下一层
```

---

# 2. Middleware 的标准形状

最小形状：

```go
func Middleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // 在 next 之前执行

        next.ServeHTTP(w, r)

        // 在 next 返回之后执行
    })
}
```

逐块理解。

## 输入：`next http.Handler`

`next` 表示：

> 当前 Middleware 处理完以后，请求链中的下一层。

下一层可能是：

```text
另一个 Middleware
ServeMux / Router
最终业务 Handler
```

Middleware 不需要知道 `next` 的具体类型，只需要知道它满足 `http.Handler`。

## 输出：`http.Handler`

Middleware 返回一个**新的 Handler**。

这个新 Handler 的行为是：

```text
先执行当前 Middleware 的逻辑
↓
再决定要不要调用 next
↓
next 返回后还能继续执行
```

## 核心：`next.ServeHTTP(w, r)`

这句可以翻译成：

> 把当前这一次请求使用的同一个 `ResponseWriter` 和 `Request`，继续交给链条中的下一层处理。

它不是创建新网络请求，也不是重新连接服务器。

它只是函数调用：

```text
当前 Handler
→ 下一 Handler 的 ServeHTTP
```

---

# 3. 为什么可以一层套一层

假设有：

```go
final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintln(w, "handler")
})

wrapped := Outer(Inner(final))
```

调用：

```go
wrapped.ServeHTTP(w, r)
```

实际顺序：

```text
Outer before
→ Inner before
→ final Handler
→ Inner after
→ Outer after
```

这就是常说的：

```text
wrapper model
onion model
洋葱模型
```

图：

```text
┌──────────────────────────────────────┐
│ Outer Middleware                    │
│   before                            │
│   ┌──────────────────────────────┐  │
│   │ Inner Middleware             │  │
│   │   before                     │  │
│   │   ┌──────────────────────┐   │  │
│   │   │ Final Handler        │   │  │
│   │   └──────────────────────┘   │  │
│   │   after                      │  │
│   └──────────────────────────────┘  │
│   after                             │
└──────────────────────────────────────┘
```

注意：所谓“洋葱”只是函数嵌套和返回顺序的类比，不是 Go 运行时里真的存在一个特殊 Middleware 引擎。

---

# 4. 用一个最小追踪例子证明顺序

```go
func Trace(name string, events *[]string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            *events = append(*events, name+" before")

            next.ServeHTTP(w, r)

            *events = append(*events, name+" after")
        })
    }
}
```

组合：

```go
events := []string{}

final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    events = append(events, "handler")
})

handler := Trace("outer", &events)(
    Trace("inner", &events)(final),
)
```

执行后：

```text
outer before
inner before
handler
inner after
outer after
```

这个例子先用于证明调用顺序，不是生产日志实现。

---

# 5. 当前项目的 `RequestContext`

当前代码：

```go
func RequestContext(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // 先尝试使用客户端传来的 Request ID。
        // TrimSpace 防止只有空格的值被当成有效 ID。
        id := strings.TrimSpace(r.Header.Get("X-Request-ID"))

        // 客户端没有提供时，由服务端生成。
        if id == "" {
            generated, err := newID()
            if err != nil {
                http.Error(
                    w,
                    "cannot create request id",
                    http.StatusInternalServerError,
                )
                return
            }
            id = "req_" + generated
        }

        // 写回 Request，后面的 Authentication、Handler、Service 日志
        // 都可以沿同一次请求读取这个 ID。
        r.Header.Set("X-Request-ID", id)

        // 写入 Response Header，客户端也能看到同一个 ID。
        // Header 必须在后续 Handler 开始写响应前设置。
        w.Header().Set("X-Request-ID", id)

        // 继续执行 root ServeMux。
        // 没有这句，后面的 Router / Handler 完全不会运行。
        next.ServeHTTP(w, r)
    })
}
```

它解决的问题：

```text
一次请求经过多个函数和日志
↓
需要一个共同 ID 关联
```

它的输入：

```text
next = root ServeMux
w / r = 当前这次 HTTP 请求
```

它的输出不是一个业务对象；它通过返回一个新的 `http.Handler` 改变请求处理链。

它不负责：

```text
验证 Bearer Token
判断 tenant
解析 Ticket JSON
访问 Repository
```

---

# 6. 当前项目的 `Authenticate`

简化并加教学注释后的完整逻辑：

```go
func Authenticate(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // 1. 从 HTTP Header 读取客户端提供的凭证。
        authorization := strings.TrimSpace(
            r.Header.Get("Authorization"),
        )

        // 2. 没有 Bearer 格式：认证失败。
        // 写出 401 后直接 return，不允许继续调用 next。
        if !strings.HasPrefix(authorization, "Bearer ") {
            writeError(
                w,
                r,
                http.StatusUnauthorized,
                "authentication_required",
                "a bearer token is required",
            )
            return
        }

        // 3. 取出 Bearer 后面的教学 Token，映射成 Principal。
        token := strings.TrimSpace(
            strings.TrimPrefix(authorization, "Bearer "),
        )
        principal, ok := labTokens[token]
        if !ok {
            writeError(
                w,
                r,
                http.StatusUnauthorized,
                "authentication_required",
                "the bearer token is invalid",
            )
            return
        }

        // 4. 认证成功后，把可信 Principal 放进派生 Context。
        ctx := context.WithValue(
            r.Context(),
            principalContextKey{},
            principal,
        )

        // 5. 继续调用下一层，但要把带有新 Context 的 Request 传下去。
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

最重要的两个分支：

```text
认证失败
→ 写 401
→ return
→ 不调用 next

认证成功
→ Principal 放入 Context
→ next.ServeHTTP
```

这里的“不调用 next”不是 Bug，而是有意识的短路：

> 未认证请求不应该进入真正业务 Handler。

所以不能机械认为“每个 Middleware 都必须无条件调用 next”。正确原则是：

```text
想让请求继续
→ 调 next

当前层已经决定终止并写出响应
→ return，不调 next
```

---

# 7. 当前项目的真实组合顺序

`NewHTTPHandler` 概念结构：

```go
func NewHTTPHandler(service *Service, logger *slog.Logger) http.Handler {
    root := http.NewServeMux()
    root.HandleFunc("GET /health", health)

    api := http.NewServeMux()
    NewHandler(service, logger).Register(api)

    root.Handle("/api/v1/", Authenticate(api))

    return RequestContext(root)
}
```

## API 请求

例如：

```http
GET /api/v1/tickets/{id}
```

顺序：

```text
RequestContext before
↓
root ServeMux
↓
匹配 /api/v1/
↓
Authenticate
↓
api ServeMux
↓
GET /api/v1/tickets/{id}
↓
Handler.get
```

## Health 请求

```http
GET /health
```

顺序：

```text
RequestContext
↓
root ServeMux
↓
health Handler
```

它不会进入 `Authenticate`。

所以 Middleware 并不一定套在整个 Server 的所有路由外面；可以只包装某一棵子路由。

---

# 8. Middleware 顺序为什么重要

假设以后增加 Access Log：

```go
handler := RequestContext(
    AccessLog(logger)(
        root,
    ),
)
```

顺序：

```text
RequestContext 先生成 request ID
↓
AccessLog 才能记录这个 ID
↓
root Router
```

如果反过来：

```go
handler := AccessLog(logger)(
    RequestContext(root),
)
```

AccessLog 的 `before` 阶段可能还拿不到服务端生成的 request ID。

因此 Middleware 的排列不是装饰风格问题，而会改变行为。

---

# 9. `next` 前后分别适合做什么

## `next` 之前

适合：

```text
生成 Request ID
读取开始时间
认证
限流
输入大小限制
把 metadata 放进 Context
```

因为这些事情通常必须在业务 Handler 执行前完成。

## `next` 之后

适合：

```text
计算耗时
结束 Trace span
记录完成日志
清理资源
```

因为需要等后面的 Handler 返回。

注意：后面 Handler 很可能已经写出 HTTP Header 和 Body，所以 `next` 返回后再修改普通 Response Header 往往太晚。

---

# 10. 五个重要失败场景

## 失败 1：忘记调用 `next`

```go
func Broken(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // next.ServeHTTP(w, r) 被漏掉
    })
}
```

结果：

```text
Middleware 被调用
↓
链条在这里停止
↓
Router / Handler 不执行
```

如果 Middleware 自己也没写响应，`net/http` 最后可能形成一个空的默认响应，具体测试会暴露契约错误。

## 失败 2：调用 `next` 两次

```go
next.ServeHTTP(w, r)
next.ServeHTTP(w, r)
```

可能导致：

```text
业务副作用执行两次
重复写 Response
superfluous WriteHeader
```

Middleware 不是 Retry 机制，不能随便重复调用下游。

## 失败 3：写错误响应后仍继续 `next`

```go
http.Error(w, "unauthorized", 401)
next.ServeHTTP(w, r) // 错误
```

后面的业务 Handler 仍然可能执行，造成：

```text
未认证访问
重复响应
状态码/Body 混乱
```

所以认证失败必须 `return`。

## 失败 4：丢掉上游 Context

错误：

```go
ctx := context.Background()
next.ServeHTTP(w, r.WithContext(ctx))
```

这会丢失：

```text
上游 deadline
client cancellation
已有 request metadata
```

正确做法是从：

```go
r.Context()
```

派生。

## 失败 5：顺序不合理

如果日志 Middleware 在 Request ID 外层，却期望在 `before` 阶段读取服务端生成的 ID，就会拿不到。

所以要根据依赖安排顺序。

---

# 11. Middleware 和 Handler 的边界

Middleware 适合：

```text
多个路由共同需要
与具体 Ticket 业务无关
可以围绕 next 执行
```

例如：

```text
Request ID
Access Log
Authentication
Rate Limit
Recovery
CORS
```

业务 Handler 适合：

```text
解析某个端点的 Path / Query / Body
调用具体业务 Service
映射当前端点结果
```

不要把 Ticket 状态机写进通用 Middleware，也不要让每个 Ticket Handler 各自复制一遍 Authentication。

---

# 12. 当前章节的代码跟写范围

不需要重写整个项目。

建议只跟写/阅读：

```text
RequestContext
Authenticate
一个最小 AccessLog Middleware
NewHTTPHandler 中的组合
```

总量控制在约 100 行以内。

然后完成 practice 中的一个独立小变化。

---

# 13. 关闭文档后应该能回答

1. 为什么 Middleware 的输入和输出都是 `http.Handler`？
2. `next` 可能是什么？
3. `next.ServeHTTP(w, r)` 到底做了什么？
4. 为什么可以在 `next` 前认证、在 `next` 后计算耗时？
5. `RequestContext(root)` 中谁在外层？
6. 为什么 `/health` 不经过 `Authenticate`？
7. 认证失败为什么必须 `return`？
8. 为什么从 `r.Context()` 派生，而不是换成 `context.Background()`？
9. 不调用 `next` 会发生什么？
10. Middleware 顺序为什么会改变行为？

能回答这些，再通过 practice 的小改和故障实验，才算从 L1 进入 L2/L3。
