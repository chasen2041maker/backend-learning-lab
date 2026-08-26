# 第 3 章 Practice：跟写 AccessLog，独立完成一个小变化

先读：

- [`../walkthrough/03-middleware.md`](../walkthrough/03-middleware.md)
- [`../CODE_MAP.md`](../CODE_MAP.md)

本练习不要求从空白写整个 HTTP 服务，只处理 Middleware 这一小段。

目标：

```text
完整参考代码跟写
→ 运行
→ 独立小改
→ 故意截断 chain
→ 恢复并 Review
```

---

# A. 跟写完整参考：AccessLog Middleware

建议把下面函数暂时加入：

```text
internal/ticket/handler.go
```

以后代码规模扩大时可以移到独立 platform/middleware package；当前不要为了目录漂亮先拆包。

完整参考：

```go
func AccessLog(logger *slog.Logger) func(http.Handler) http.Handler {
    // 第一层接收依赖 logger，返回真正的 Middleware。
    return func(next http.Handler) http.Handler {
        // 第二层接收 chain 中的下一 Handler，返回包装后的 Handler。
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            // next 之前记录开始时间。
            startedAt := time.Now()

            // 继续执行 Router / 其他 Middleware / endpoint Handler。
            next.ServeHTTP(w, r)

            // next 返回以后，计算整段下游处理耗时。
            logger.Info(
                "http request completed",
                "request_id", requestID(r),
                "method", r.Method,
                "path", r.URL.Path,
                "duration", time.Since(startedAt),
            )
        })
    }
}
```

需要新增 import：

```go
"time"
```

如果 `handler.go` 已经导入 `log/slog`，无需重复。

---

# B. 把它接入真实请求链

当前：

```go
return RequestContext(root)
```

改成：

```go
return RequestContext(
    AccessLog(logger)(root),
)
```

调用顺序：

```text
RequestContext before
↓
AccessLog before：startedAt
↓
root ServeMux
↓
Authenticate / endpoint Handler
↓
AccessLog after：记录 duration
↓
RequestContext 返回
```

为什么 `RequestContext` 放外层？

因为 AccessLog 的 `before` 阶段就可能需要读取服务端生成的 request ID。

---

# C. 运行

```powershell
cd exercises\go-ticket-api
gofmt -w internal\ticket\handler.go
go test ./...
go run ./cmd/server
```

另一个终端：

```powershell
curl.exe -v http://127.0.0.1:8080/health
```

再请求一个受保护端点：

```powershell
curl.exe -v `
  -H "Authorization: Bearer lab-token-tenant-a" `
  http://127.0.0.1:8080/api/v1/tickets
```

观察日志至少包含：

```text
request_id
method
path
duration
```

注意：当前参考没有捕获真实 HTTP status。要捕获 status 需要包装 `ResponseWriter`，属于后续小节；不要假装已有实现能记录 status。

---

# D. 独立小变化：二选一

不要照答案，自己完成其中一个。

## 选项 1：增加 `host`

让日志再记录：

```text
host
```

思考应该读取：

```go
r.Host
```

还是某个普通 Header。

## 选项 2：写 before/after 顺序测试

写一个测试构造：

```text
Outer Middleware
Inner Middleware
Final Handler
```

最终断言事件顺序：

```text
outer before
inner before
handler
inner after
outer after
```

这个测试不依赖真实网络，可以使用 `httptest.NewRequest` 和 `httptest.NewRecorder`。

---

# E. 故障实验：截断 Middleware Chain

在 `AccessLog` 中临时注释：

```go
next.ServeHTTP(w, r)
```

然后运行：

```powershell
go test ./...
```

再请求：

```powershell
curl.exe -v http://127.0.0.1:8080/health
```

观察并记录：

```text
AccessLog 是否执行？
health Handler 是否执行？
Response status/body 变成什么？
哪些测试失败？
```

原因：

```text
当前 Middleware 没有把控制权交给 next
↓
chain 在这里结束
↓
ServeMux / endpoint Handler 不运行
```

实验后必须恢复 `next.ServeHTTP(w, r)`，再次运行全部测试。

---

# F. 不要做的错误改法

## 1. 认证失败后仍调用 next

```go
writeError(...401...)
next.ServeHTTP(w, r) // 不允许
```

这可能让未认证请求继续进入业务 Handler。

## 2. 调用 next 两次

可能造成业务副作用和 Response 重复执行。

## 3. next 返回后再设置普通 Response Header

后续 Handler 可能已经写出 Header，修改可能无效。

## 4. 用 `context.Background()` 替换请求 Context

会切断 deadline、cancel 和已有 request metadata。

---

# G. 完成后提交给 AI Review 的内容

只需要发：

```text
1. 修改后的 Middleware 代码
2. 新增/修改的测试
3. go test ./... 输出
4. 故障实验观察
5. 自己用一句话解释 next.ServeHTTP
```

Review 固定检查：

```text
调用顺序
Middleware 排列
错误分支是否 return
是否重复调用 next
日志字段是否可靠
测试到底证明什么
```

---

# H. 本章完成标准

```text
[ ] 跟写 AccessLog
[ ] gofmt
[ ] go test ./... 通过
[ ] curl 能触发日志
[ ] 独立完成一个小变化
[ ] 做过 chain 截断故障
[ ] 恢复代码并再次测试通过
[ ] 能解释 before / next / after
```

完成后再进入：

```text
Handler → Service → Repository
```
