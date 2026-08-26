# Go `net/http` 参考项目：边对话、边跟写、边验证

这个目录是本仓库的**主参考项目**。

它不是要求学习者从空白目录一次写完的挑战，也不是“AI 生成后只运行一下”的成品。正确用法是：

```text
先通过对话理解当前问题
↓
查看完整、正确、可运行的参考实现
↓
按章节只跟写必要代码
↓
运行测试 / curl
↓
独立完成一个小变化
↓
制造一个失败
↓
AI Review
```

当前项目使用 Go 标准库 `net/http`，让 Router、Middleware、Handler、Context 和错误传播保持可见；基础阶段不先用 Gin/Echo/GORM 隐藏这些边界。

---

# 先看这三个文件

1. [`STUDY_ORDER.md`](STUDY_ORDER.md)：十二章顺序、当前状态、每章要改什么；
2. [`CODE_MAP.md`](CODE_MAP.md)：文件地图和一次请求的真实调用链；
3. 当前章节的 `walkthrough/` 与 `practice/`。

当前章节：

```text
第 3 章 Middleware
```

- [`walkthrough/03-middleware.md`](walkthrough/03-middleware.md)
- [`practice/03-middleware.md`](practice/03-middleware.md)

---

# 运行基线

```powershell
cd exercises\go-ticket-api
go test ./...
go run ./cmd/server
```

默认监听：

```text
http://127.0.0.1:8080
```

端点：

```text
GET  /health
POST /api/v1/tickets
GET  /api/v1/tickets
GET  /api/v1/tickets/{id}
POST /api/v1/tickets/{id}/close
```

除 `/health` 外，请求使用本地教学凭据：

```http
Authorization: Bearer lab-token-tenant-a
```

固定 Token 不是生产认证。它只用于证明：

```text
Credential
→ 服务端验证
→ Principal
→ tenant / owner boundary
```

---

# 项目当前包含什么

```text
cmd/server/main.go
→ 进程、依赖组装、http.Server、graceful shutdown

internal/ticket/handler.go
→ ServeMux、路由、Request ID Middleware、HTTP 输入输出、错误映射

internal/ticket/identity.go
→ Authentication Middleware、Principal、context

internal/ticket/service.go
→ 创建/查询/列表/关闭的业务规则

internal/ticket/repository.go
→ Repository interface、Memory Repository、mutex、tenant/version 边界

internal/ticket/model.go
→ 输入与领域状态

handler_test.go / service_test.go
→ HTTP 与业务边界证据
```

完整调用图见 [`CODE_MAP.md`](CODE_MAP.md)。

---

# 详细注释为什么不全部写进 `.go` 文件

真实运行代码应保持清楚、可维护，不应充满：

```go
// 定义一个变量
id := ...
```

详细教学解释放在 `walkthrough/`，重点说明：

```text
为什么需要
谁调用
输入从哪里来
状态在哪里变化
错误怎么走
下一层是谁
故障会怎样
```

需要跟写时，walkthrough 会给出完整参考代码和注释。

---

# 每章怎么使用

一次只推进一个小节。

## 1. 对话讲解

先讲：

```text
这个抽象解决什么问题
在调用链哪里
上一层给它什么
它交给下一层什么
```

## 2. 打开完整参考

不是先猜最终结构。先看到正确形态，再逐块理解。

## 3. 跟写必要代码

通常只处理当前章节的 30～120 行，不重抄整个项目。

## 4. 运行

```powershell
go test ./...
go run ./cmd/server
curl.exe -v ...
```

## 5. 独立小变化

每章至少一个，但不会要求从零实现全部功能。

## 6. 故障实验

临时破坏一个不变量，观察测试或请求如何失败，然后恢复。

## 7. Review

固定回答：

```text
谁调用？
输入？
状态变化？
输出？
失败点？
测试证明什么？
还没有证明什么？
```

---

# 当前代码阅读顺序

不要从 `main.go` 第一行一路往下背。

按请求链：

```text
NewHTTPHandler
↓
RequestContext
↓
root ServeMux
↓
Authenticate（API only）
↓
api ServeMux
↓
endpoint Handler
↓
Service
↓
Repository
```

然后再回 `cmd/server/main.go` 看这些依赖怎样组装进 `http.Server`。

---

# 测试通过证明什么

```text
go test ./...
```

当前能证明：

- Router / Handler 契约；
- 教学 Authentication 边界；
- strict input 与稳定错误；
- tenant 隔离；
- 内存 Repository 并发安全；
- 状态与版本冲突语义。

它不能证明：

- 数据重启后保留；
- JWT / Session 已生产化；
- PostgreSQL transaction 正确；
- 多实例共享状态；
- 真实容量和性能；
- 完整生产安全。

---

# 当前章节完成标准

Middleware 章节完成至少需要：

```text
能解释 func(next http.Handler) http.Handler
能画 onion before/after 顺序
能解释 next.ServeHTTP(w, r)
读懂 RequestContext 与 Authenticate
运行现有测试
独立完成一个小变化
观察不调用 next 导致 chain 截断
```

精确接棒点见：

- [`../../progress/current-focus.md`](../../progress/current-focus.md)

完整主线见：

- [`../../GO_BACKEND_TRACK.md`](../../GO_BACKEND_TRACK.md)

---

这个项目的价值不在于代码量，而在于学习者最终可以对下面每条边负责：

```text
Request 为什么进入这里？
身份从哪里来？
业务事实在哪里变化？
并发和重复会怎样？
失败如何恢复？
测试和日志有什么证据？
```
