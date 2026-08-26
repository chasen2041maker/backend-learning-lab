# Go 后端主线：对话驱动 + 完整参考实现 + 跟写重建

这是本仓库当前唯一的**日常学习主线**。

学习者已经在 Agent 工程岗位工作约 4 个月，日常会使用 Codex / AI Coding 参与真实项目；Python 基础和 Agent/RAG 应用经验明显强于 Go 与传统后端基础。因此，这条主线不采用“面对空白目录，从零手搓所有样板代码”的纯新手训练，也不采用“让 AI 一次生成大项目，然后只看结果”的方式。

采用的模式是：

```text
对话先讲通问题和调用链
↓
查看一份完整、正确、可运行的 Go 参考实现
↓
只跟写当前真正需要的 30～120 行代码
↓
运行测试 / curl / 故障实验
↓
逐段解释：谁调用、输入、状态变化、输出、失败
↓
学习者独立完成一个小变化
↓
AI Review，并把高价值理解沉淀回仓库
```

核心目标不是训练“脱离任何工具默写所有样板代码”，而是获得对 AI 生成代码的**控制力**：

```text
看得懂
讲得清
改得对
测得出
出错能定位
知道什么时候不要增加复杂度
```

---

# 1. 这个仓库和 Agent 学习仓库怎么分工

本仓库专门负责：

```text
Go 后端基础
HTTP / API
分层
PostgreSQL
Authentication / Authorization
Transaction / Idempotency
Concurrency / Timeout / Cancel
Redis 的角色边界
Async / Outbox / Worker
Testing / Debugging / Observability
Docker / CI / Deployment
系统设计与复杂度控制
```

Agent / RAG / Prompt / Eval / Multi-Agent 等内容由单独的 Agent 学习仓库承担。

本仓库只保留一条必要连接：

> Agent 任务、RAG 检索和 Tool 执行最终仍然是普通后端工作负载，必须遵守身份、权限、事务、幂等、超时、任务状态、审计和观测规则。

因此，不会在这里重复系统学习 Agent 框架；需要时只用 Agent 场景帮助理解普通后端能力。

---

# 2. 默认学习方法

## 2.1 对话是主线

每天主要通过对话学习。新的 GPT / AI 会话先读：

1. [`LEARNER_PROFILE.md`](LEARNER_PROFILE.md)
2. [`progress/current-focus.md`](progress/current-focus.md)
3. 本文件
4. 当前章节对应的代码和 walkthrough

不需要每次都先读完整 `GROWTH_PATH.md` 或 `LEARNING_ROADMAP.md`；只有做长期规划、阶段复盘或选下一方向时再读。

## 2.2 先给完整参考，不强迫从空白开始

每一章先给出最终正确形态，让学习者知道：

```text
完整调用链长什么样
哪些文件属于哪一层
为什么这样分
这段代码解决什么问题
```

然后只跟写当前章节相关的小段代码，不要求整套项目从零重建。

## 2.3 详细注释放在 walkthrough，工作代码保持清楚

真正运行的 Go 代码保持接近正常工程代码，不在每一行写“定义变量”一类低价值注释。

详细教学说明放在：

```text
exercises/go-ticket-api/walkthrough/
```

walkthrough 会解释：

```text
为什么需要这段代码
谁调用它
输入从哪里来
它拥有哪项职责
它不应该知道什么
下一步交给谁
会出现什么故障
```

## 2.4 每章至少有一个独立小变化

不要求独立完成整章，但必须独立完成一个小变化，例如：

```text
补一个 405 测试
给 Middleware 增加一个日志字段
新增 priority
补 tenant 隔离测试
给 Slow Repository 加 timeout
```

这是区分“看懂”与“能够控制代码”的最低证据。

## 2.5 每章至少制造一个失败

例如：

```text
删掉 next.ServeHTTP
↓
后面的 Handler 不执行

使用 context.Background()
↓
上游取消不能继续传播

COMMIT 后 Response 前失败
↓
客户端重试可能重复创建
```

失败实验比继续听十个新名词更能建立后端判断。

---

# 3. 掌握标准

继续使用仓库统一等级：

```text
L0 未接触
L1 见过：知道名词和大概用途
L2 能解释：能画调用链并说明失败点
L3 能控制：能修改、测试、排错
L4 能权衡：知道什么时候不用、替代方案和成本
```

这条主线不要求每个章节都从空白默写。

对于常用后端能力，L3 的证据可以是：

```text
能阅读完整参考实现
+ 能解释真实调用链
+ 能独立完成一个变化
+ 能写/修改测试
+ 能定位一个故障
```

---

# 4. 主参考项目

主项目：

- [`exercises/go-ticket-api/`](exercises/go-ticket-api/)

它是一套完整、可运行的 Go `net/http` 模块化单体基线，当前包含：

```text
http.Server
ServeMux / Router
Middleware
Authentication / Principal
Handler
Service
Repository interface
Memory Repository
context.Context
mutex
状态机
版本冲突
稳定错误映射
handler / service tests
```

使用入口：

- [`STUDY_ORDER.md`](exercises/go-ticket-api/STUDY_ORDER.md)：章节顺序、当前状态和每章验收；
- [`CODE_MAP.md`](exercises/go-ticket-api/CODE_MAP.md)：完整文件地图和请求调用链；
- `walkthrough/`：当前章节的详细注释与拆解；
- `practice/`：只要求独立完成的小变化和故障实验。

运行基线：

```powershell
cd exercises\go-ticket-api
go test ./...
go run ./cmd/server
```

---

# 5. 十二章成长目录

这不是必须按日期完成的课表，而是同一个 Go 后端项目逐层展开的目录。

## 第 1 章：HTTP Server、Handler 与 Response

核心问题：

> Client 发来的 HTTP 字节，怎样最终进入 Go 函数，再怎样返回 Response？

学习：

```text
http.Server
http.Handler
HandlerFunc
ServeHTTP
*http.Request
http.ResponseWriter
healthz
```

跟写范围：一个最小 `/healthz` Handler 和 Server。

独立变化：补非 GET 返回 405。

失败实验：服务停止后观察 connection failure，确认没有 HTTP status。

---

## 第 2 章：Router / ServeMux

核心问题：

> 同一个 Server 收到不同 Method + Path，怎样找到对应 Handler？

学习：

```text
ServeMux
route pattern
Method + Path
PathValue
404
405
```

独立变化：新增一个只允许 GET 的路由并补测试。

失败实验：路径不存在与方法不允许分别触发 404 / 405。

---

## 第 3 章：Middleware

当前章节。

核心问题：

> 为什么 `func(next http.Handler) http.Handler` 可以把 Request ID、日志和认证套在所有业务 Handler 外面？

学习：

```text
wrapper / decorator
onion model
next.ServeHTTP(w, r)
Request ID
Access Log
Authentication Middleware
Middleware order
```

当前 walkthrough：

- [`walkthrough/03-middleware.md`](exercises/go-ticket-api/walkthrough/03-middleware.md)

当前 practice：

- [`practice/03-middleware.md`](exercises/go-ticket-api/practice/03-middleware.md)

失败实验：注释掉 `next.ServeHTTP`，观察后续 Router / Handler 为什么完全不执行。

---

## 第 4 章：Handler → Service → Repository

核心问题：

> HTTP 输入、业务规则和数据存储为什么不能全部写进一个 Handler？

学习：

```text
Handler = HTTP adapter
Service = business use case
Repository = persistence boundary
Database / memory = facts
```

跟写范围：完整 create/get Ticket 调用链。

独立变化：新增一个业务字段，并判断应改哪些层。

失败实验：让 Handler 直接修改全局 map，观察测试隔离和职责混乱。

---

## 第 5 章：错误、配置、日志和测试

学习：

```text
error wrapping
errors.Is
sentinel/domain errors
HTTP error mapping
LoadConfig
slog
httptest
table-driven tests
```

独立变化：新增一个稳定业务错误码和对应 handler test。

失败实验：错误只写“发生错误”，尝试根据日志定位一次请求。

---

## 第 6 章：`context.Context`、Deadline 与 Cancel

不孤立背 API，而放入真实调用链：

```text
HTTP Request
→ Handler
→ Service
→ Slow Repository
```

学习：

```text
request context
deadline
cancel
client disconnect
database/query cancellation
context value 的边界
```

独立变化：给 Slow Repository 写一个 deadline test。

失败实验：Service 使用 `context.Background()`，观察上游取消为什么被切断。

---

## 第 7 章：PostgreSQL

把 Memory Repository 替换为 PostgreSQL Repository。

学习：

```text
migration
schema
PK / FK / UNIQUE / CHECK
parameterized SQL
connection pool
query timeout
index
EXPLAIN
tenant-scoped query
```

独立变化：从真实查询推导一个索引并用 `EXPLAIN` 说明。

失败实验：数据库不可用、constraint violation、statement timeout。

---

## 第 8 章：Authentication 与 Authorization

学习：

```text
Credential
→ Authentication
→ Principal
→ Authorization
→ role / permission / owner / tenant
```

教学 Token 继续用于证明信任边界；Session/JWT 作为实现方案理解，不自行发明密码学协议。

独立变化：补一个跨租户隐藏 404 测试。

失败实验：让 Body 自报 `tenant_id`，推演越权场景。

---

## 第 9 章：Transaction、并发更新与 Idempotency

学习：

```text
BEGIN / COMMIT / ROLLBACK
optimistic version
unique constraint
lost update
Idempotency-Key
request hash
response replay
```

独立变化：实现/验证同一 Idempotency Key 的结果重放。

失败实验：数据库 COMMIT 成功、HTTP Response 返回前进程失败，然后客户端重试。

---

## 第 10 章：Go 并发与 Redis

先学运行时资源边界，再决定是否需要 Redis。

学习：

```text
goroutine
channel / mutex
worker pool
bounded concurrency
backpressure
retry / backoff / jitter
Redis cache / session / rate limit / coordination
```

独立变化：限制一个批处理的最大并发数。

失败实验：无限启动 goroutine、Redis outage、cache stampede。

---

## 第 11 章：异步任务、Webhook、Outbox 与 Worker

学习：

```text
job / command / event
Webhook HMAC
Outbox
at-least-once
consumer idempotency
ACK
Pending / reclaim
retry / DLQ
lease / fencing
```

独立变化：为 Consumer 增加持久化幂等记录。

失败实验：业务 COMMIT 后 ACK 前 Worker 崩溃。

---

## 第 12 章：可观测性、Docker、CI 与部署

学习：

```text
request ID / trace ID
logs / metrics / traces
RED
liveness / readiness
graceful shutdown
Docker image
CI
registry digest
deployment / rollback
```

独立变化：为一个 API 增加可行动的指标和失败测试。

失败实验：readiness 错误、shutdown 超时、migration 与旧版本不兼容。

---

# 6. 每次对话的固定节奏

默认一次只推进一个小节：

```text
1. 用 5～15 分钟讲清调用链和问题
2. 打开 30～120 行完整参考代码
3. 学习者跟写或逐块阅读
4. 运行测试 / curl
5. 解释一个失败
6. 学习者独立改一个小点
7. AI Review
8. 必要时更新 current-focus / journal
```

如果当天只想听懂，可以停在第 1～3 步；但一个章节最终要完成至少一次“小改 + 测试 + 故障”。

---

# 7. 当前状态

当前已建立第一轮心智模型：

```text
HTTP Request line / Header
Router 与 404 / 405
Authentication / Authorization
DNS / IP / Port
TCP / TLS
OS / Socket
Nginx
Go net/http
http.Handler / HandlerFunc
```

当前进入：

```text
第 3 章 Middleware
```

下一次学习从：

```go
func Middleware(next http.Handler) http.Handler
```

开始，重点解释 `next.ServeHTTP(w, r)` 和 onion model；不会重新从 DNS/TCP 长篇复习。

精确接棒点见：

- [`progress/current-focus.md`](progress/current-focus.md)

---

# 8. 不在当前主线里的内容

以下内容按需阅读，不为了“完整技术栈”提前进入：

```text
Gin / Echo / GORM
微服务拆分
Kafka
Kubernetes 深度运维
Service Mesh
数据库分片
Agent 框架与 Prompt 工程
Multi-Agent
```

基础链路稳固后，框架只是同一后端模型的另一套 API；出现真实规模或故障证据后，再引入分布式组件。

---

这条路线的最终目标不是让学习者抄完一个目录，而是让完整参考代码逐渐变成可控制的工程系统：

> **AI 可以提高编码速度，但身份、事实、事务、并发、失败与恢复边界必须由工程师自己理解和负责。**
