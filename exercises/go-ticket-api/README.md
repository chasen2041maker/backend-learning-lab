# Go `net/http` 工单练习：用标准库看清一个请求真正经过什么

这个目录不是“Go 版本的成品业务项目”，而是一套**可运行的 Go 后端基线**。它和 Python Ticket API 表达同一领域，用于把已经理解的 HTTP、分层、可信身份、状态机和契约用 Go `net/http` 重新走一遍。

目标不是先学 Gin/Echo，也不是追求目录像某个公司模板；目标是你能顺着真实代码回答：

```text
请求从哪里进来？
Method/Path 谁判断？
JSON 谁解析？
Principal 谁产生？
业务规则在哪里？
Repository 怎么隔离 tenant？
错误怎么映射成 HTTP？
context 什么时候取消？
```

## 运行基线

在本目录：

```powershell
go test ./...
go run ./cmd/server
```

服务监听：

```text
http://127.0.0.1:8080
```

端点：

```text
POST /api/v1/tickets
GET  /api/v1/tickets/{id}
GET  /api/v1/tickets?limit=20
POST /api/v1/tickets/{id}/close
GET  /health
```

除 `/health` 外，请求使用教学凭据：

```http
Authorization: Bearer lab-token-tenant-a
```

固定 Token 只是本地桩。真正要学的是：

```text
Credential
→ 服务端验证
→ Principal
→ tenant/owner boundary
```

而不是把 `tenant_id` 从 Body 里抄出来。

## 读代码的推荐顺序

不要从 `main.go` 开始逐行背。

按调用链：

1. `cmd/server/main.go`：进程、Server、依赖组装；
2. `internal/ticket/handler.go`：HTTP 输入/输出；
3. `identity.go`：可信 Principal；
4. `service.go`：状态机与业务错误；
5. `repository.go`：数据边界；
6. tests：每个边界由什么证据保护。

每打开一个文件先回答“谁调用它、它应该不知道什么”，再看语法。

## 你应该特别观察的 Go 基础

- `http.Handler` / `ServeHTTP` 如何组成请求链；
- `struct` 作为依赖容器而不是“面向对象类”的机械翻译；
- interface 为什么定义在消费者需要的最小行为附近；
- `(value, error)` 如何跨层传播；
- `errors.Is` / sentinel/domain error 与 HTTP status 的分离；
- `context.Context` 为什么属于请求生命周期；
- pointer receiver 什么时候意味着修改共享状态；
- mutex/并发安全为什么是 Repository 实现问题之一。

## 不要误解测试通过的含义

当前基线大量使用内存状态和教学 Token。所以：

```text
go test ./... 通过
```

证明的是当前代码契约，不代表：

- 数据能在进程重启后保留；
- JWT/Session 已生产化；
- PostgreSQL transaction 已验证；
- 多实例共享状态正确；
- 高并发容量足够。

## 推荐独立练习顺序

### A. `priority`

先写失败测试，再加入：

```text
low | normal | high
```

要求输入、领域状态、JSON 输出一致。

### B. 跨租户查询

用 tenant A 创建，再用 tenant B 查询，证明返回契约要求的隐藏 404。

### C. version conflict

两个请求都基于旧 version，最终只能一个成功。先在内存实现证明语义，再到 PostgreSQL 事务中重做。

### D. cursor pagination

从 `(created_at, id)` 稳定排序推导 cursor，不要只写 `offset` 因为教程说 cursor 更高级。

### E. context timeout

让 Repository 人为变慢，给请求 deadline，观察取消如何传播。不要在 Service 内重新创建一个与请求无关的 `context.Background()` 抹掉上游取消。

## 每次改动的验收格式

```text
目标：
我改哪一层：
为什么是这一层：
失败测试：
最终测试：
一个故障窗口：
仍未证明：
```

如果你能独立解释这些问题，再换 Gin/GORM 时只是在学习工具 API；如果这些边界没懂，换框架只会把问题藏起来。
