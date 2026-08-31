# Go Ticket API 学习顺序

这份文件把 [`GO_BACKEND_TRACK.md`](../../GO_BACKEND_TRACK.md) 的十二章落实到当前 Go 项目。

它不是“每天必须完成一章”的课表。每次对话只推进当前最小小节。

状态说明：

```text
概念已讲：已经建立第一轮心智模型，但未必能改代码
当前：正在通过参考代码 + 小改 + 故障进入 L2/L3
未开始：只存在完整参考，不默认掌握
按需：不属于当前后端主线
```

---

# 当前总进度

| 章 | 主题 | 当前状态 | 主要参考文件 | 最小独立证据 |
| --- | --- | --- | --- | --- |
| 01 | HTTP Server / Handler | 概念已讲 | `cmd/server/main.go`、`handler.go` | 能解释 HandlerFunc 为什么满足 Handler |
| 02 | Router / ServeMux | 概念已讲 | `handler.go:Register` | 能区分 404 / 405、Method + Pattern |
| 03 | Middleware | 概念已讲（待实践证据） | `RequestContext`、`Authenticate` | 一个独立小改 + chain 截断故障 |
| 04 | Handler → Service → Repository | **当前：L2 对话理解推进** | `handler.go`、`service.go`、`repository.go` | 独立新增一个小业务字段/规则 + test |
| 05 | Error / Config / Logging / Testing | 未开始（已在第 4 章接触错误回传） | `errors.go`、tests、`main.go` | 新错误码 + handler test |
| 06 | `context.Context` | 下一自然概念（尚未验收） | 全调用链 | Slow Repository deadline test |
| 07 | PostgreSQL | 未开始 | `sql-postgres/` | Repository 替换 + integration evidence |
| 08 | Auth / Authorization | 概念初步，tenant boundary 已连接 Repository | `identity.go`、tenant boundary | 跨租户/无权限测试 |
| 09 | Transaction / Idempotency | 未开始（已初步接触 optimistic version conflict） | SQL / reliability labs | COMMIT 后响应前失败实验 |
| 10 | Concurrency / Redis | 未开始（已在 MemoryRepository 接触 RWMutex） | MemoryRepository / redis-lab | bounded concurrency 或明确 Redis role |
| 11 | Async / Outbox / Worker | 未开始 | reliability labs / SQL | ACK/COMMIT 故障恢复 |
| 12 | Observability / Delivery | 未开始 | metrics / Docker / CI | 可行动指标 + deployment failure |

精确接棒位置见：

- [`../../progress/current-focus.md`](../../progress/current-focus.md)

---

# 每章固定流程

```text
A. 对话：先讲问题和调用链
B. Reference：看完整正确实现
C. Follow：只跟写当前必要代码
D. Run：go test / go run / curl
E. Explain：谁调用、输入、状态、输出、失败
F. Change：独立完成一个小变化
G. Break：故意破坏一个不变量
H. Review：审查并记录证据
```

不是所有步骤必须在同一天完成，但一个章节最终不能只停留在“看过”。

---

# 第 1 章：HTTP Server / Handler

## 参考

```text
cmd/server/main.go
internal/ticket/handler.go: health
```

## 已讲内容

```text
Client -> DNS -> IP/Port -> TCP/TLS -> OS/Socket -> net/http
http.Handler
HandlerFunc
ServeHTTP
ResponseWriter
*http.Request
```

## 暂时不补写

当前不要求重新从空白实现 Server；后续读 `main.go` 时再把 timeout 与 graceful shutdown 分块理解。

## 最小验收

- 能说出 `HandlerFunc` 为什么满足 `http.Handler`；
- 能读懂 `w` 和 `r` 的方向；
- 能区分 connection failure 与 HTTP status。

---

# 第 2 章：Router / ServeMux

## 参考

```go
mux.HandleFunc("GET /api/v1/tickets/{id}", h.get)
```

## 已讲内容

```text
Method + Route Pattern -> Handler
Path Parameter -> 当前资源
404 -> Path 不存在
405 -> Path 存在但 Method 不允许
```

## 后续巩固

读 `Register`，手工给四条 route 画映射表。

---

# 第 3 章：Middleware（概念已讲，待实践证据）

## 先读

1. [`CODE_MAP.md`](CODE_MAP.md)
2. [`walkthrough/03-middleware.md`](walkthrough/03-middleware.md)
3. [`practice/03-middleware.md`](practice/03-middleware.md)

## 当前参考

```text
internal/ticket/handler.go: RequestContext
internal/ticket/identity.go: Authenticate
```

## 已建立

```text
func(next http.Handler) http.Handler 的输入输出
http.HandlerFunc 如何适配匿名函数
next.ServeHTTP(w, r) 如何继续 chain
before / after 与 onion model
RequestContext / Authenticate 的基本职责
启动时组装 vs 请求时执行
闭包为什么还能记住 next
```

## 尚缺完成证据

```text
[ ] go test ./... 通过（作为本章主动验证）
[ ] 完成一个独立小改
[ ] 观察一次 chain 被截断
```

---

# 第 4 章：Handler → Service → Repository（当前）

## 参考请求

```text
POST /api/v1/tickets
GET /api/v1/tickets/{id}
POST /api/v1/tickets/{id}/close
```

## 已顺过的真实链

```text
Handler.create
→ Service.Create
→ Repository.Create
→ MemoryRepository map
```

```text
Handler.get
→ Service.Get
→ Repository.Get
→ Ticket / ErrNotFound
→ Service
→ Handler
```

```text
Handler.close
→ Service.Close
→ Service.Get
→ Repository.Get
→ 业务状态 / Version 检查
→ StatusOpen -> StatusClosed
→ Repository.Update
→ map
```

## 已建立的重点

```text
Handler
= HTTP 输入 / 输出适配

Service
= 业务用例负责人，组织步骤、执行业务规则、修改状态

Repository
= Service 访问和修改业务事实的数据边界

MemoryRepository
= 当前 Repository 的具体内存实现
```

当前已通过对话建立：

```text
map[string]Ticket 与 Python dict 的阅读类比
Create / Get / Update
TenantID scope
Repository -> Service -> Handler 的错误反向传播
Service.Close 的状态转换
Version / expectedVersion
optimistic conflict / lost update 的第一轮模型
RWMutex：RLock vs Lock
defer Unlock
RWMutex 与 Version 解决不同问题
```

## 当前明确未完成

这部分主要是参考代码 + 对话理解，不等于 L3。

仍需：

```text
[ ] 独立完成一个第 4 章小变化（候选：priority）
[ ] 修改/补至少一个 test
[ ] 主动制造一个 conflict / 分层错误并解释
```

## 下一自然话题

Repository 方法一直携带：

```go
ctx context.Context
```

下一次可以沿：

```text
r.Context()
→ Service
→ Repository
```

讲 `deadline / cancel / ctx.Err()`，但这只是自然跨章节连接，不代表第 4 章已经完成验收。

---

# 第 5 章：Error / Config / Logging / Testing

## 参考

```text
errors.go
handleError
writeJSON / writeError
handler_test.go
service_test.go
cmd/server/main.go
```

## 独立变化候选

新增一个业务冲突错误：

```text
HTTP status
stable code
service error
handler mapping
test
```

第 4 章已提前接触：

```text
Repository error
→ Service
→ Handler
→ HTTP status / stable code
```

但还没有系统进入本章。

---

# 第 6 章：`context.Context`

## 参考链

```text
r.Context()
→ Service
→ Repository
```

## 实验

加入 Slow Repository：

```text
request deadline
→ context.Done
→ Repository 停止
```

然后故意使用 `context.Background()`，观察取消链被切断。

---

# 第 7 章：PostgreSQL

## 目标

保留 Service/Handler 语义，替换 Repository 实现。

## 证据

```text
migration from empty DB
constraint failure
parameterized SQL
tenant-scoped query
query timeout
EXPLAIN
integration test
```

---

# 第 8 章：Authentication / Authorization

## 目标

把之前概念真正落到代码：

```text
Authorization Header
→ Authenticate
→ Principal in context
→ Service / Repository tenant boundary
```

教学 Token 保留，JWT/Session 只作为认证方案比较。

当前已经通过 `Repository.Get/Update` 看到 tenant scope 的第一轮真实落点，但仍缺主动跨租户测试。

---

# 第 9 章：Transaction / Idempotency

## 目标

制造并解决：

```text
lost update
COMMIT 后响应前失败
并发相同 Idempotency-Key
```

不是先背 ACID 缩写。

当前在 MemoryRepository 的 `expectedVersion` 中已经预览了 lost update / optimistic conflict，但尚未进入数据库事务实现。

---

# 第 10 章：Concurrency / Redis

先用 Go 控制：

```text
bounded worker pool
deadline
backpressure
retry budget
```

再按明确角色使用 Redis：

```text
cache / session / rate limit / coordination / stream
```

当前只在 MemoryRepository 中建立了 `RWMutex` 的最小模型：多读可并行、写入独占；不把这视为第 10 章完成。

---

# 第 11 章：Async / Outbox / Worker

目标是解释每个故障窗口：

```text
DB change
→ Outbox
→ Publisher
→ Transport
→ Consumer
→ DB COMMIT
→ ACK
```

---

# 第 12 章：Observability / Delivery

目标：

```text
log / metric / trace
liveness / readiness
graceful shutdown
Docker image
CI
rollout / rollback
```

不是只会复制 Dockerfile 或 K8s YAML。

---

# 学习中断后如何恢复

下一次打开仓库：

```text
1. progress/current-focus.md
2. 本文件当前章节
3. 当前 walkthrough / 真实代码
4. CODE_MAP 中对应调用链
5. 需要进入实践证据时再运行 go test ./...
```

不要重新从第 1 章开始机械复习。
