# 后端能力路线：按依赖学习，不按周数打卡

这份路线不是 20 周课表，也不是要求从第 0 课机械读到第 16 课。

它回答的是：

> **一个后端知识通常依赖哪些更基础的东西？我现在遇到的问题应该回到哪一层？**

平时主要通过对话、代码、真实报错和项目学习。某个知识点讲通以后，再用这里判断它属于哪一层、下一步最自然的扩展是什么。

## 0. 学习方式先定下来

后端不是框架 API 的集合，而是一串不断加约束的数据流：

```text
客户端发请求
↓
HTTP 服务接住
↓
验证输入 / 身份 / 权限
↓
业务规则决定能不能做
↓
数据库改变事实
↓
缓存 / 消息 / 外部服务参与
↓
发生超时、重复、并发、宕机
↓
系统必须能检测、恢复、解释
```

每学一个新组件，先问四个问题：

1. 它解决前一版的什么具体问题？
2. 不加它会出现什么真实失败？
3. 它自己又引入了什么新失败？
4. 我如何用测试、日志或实验证明设计有效？

如果答不出来，先不要加组件。

---

# 主干 A：请求、进程与 API

这是所有后端知识的入口。

## A1. 进程、端口、HTTP 请求生命周期

对应：

- [第 0 课：学习方式](lessons/00-start-here.md)
- [环境准备](lessons/00b-environment-setup.md)
- [第 1 课：HTTP 请求生命周期](lessons/01-request-lifecycle.md)

要真正讲清：

```text
源代码
→ 启动进程
→ 监听 IP:Port
→ 客户端建立连接
→ HTTP Request
→ Router / Handler
→ HTTP Response
```

你至少应该能区分：

- `connection refused`：根本没连到应用；
- 404：连到了 HTTP 服务，但路由/资源不存在；
- 405：路径可能对，但 Method 不允许；
- 400/422：请求到了应用，但输入无法接受；
- 401/403：身份或权限问题；
- 500：服务端内部失败。

### 进入下一层的证据

关闭文档以后，能画出一次真实请求，并指出至少三个不同失败位置。

---

## A2. Handler / Service / Repository

对应：

- [第 2 课：Python 后端基础](lessons/02-python-backend-foundations.md)
- [第 3 课：分层 Service](lessons/03-layered-service.md)

核心不是记三个目录，而是分清责任：

```text
Handler
负责 HTTP 世界

Service
负责业务规则和用例

Repository
负责事实如何持久化/读取
```

Go、Python 都可以练。语言不是主角。

### Go 路线

优先理解：

- `net/http`；
- struct / method / interface；
- `(value, error)`；
- `errors.Is`；
- `context.Context`；
- `httptest`。

### Python 路线

优先理解：

- type hints；
- Pydantic；
- Protocol；
- exception -> HTTP error 映射；
- pytest。

### 进入下一层的证据

能自己新增一个业务字段或规则，并知道应该改哪一层、为什么。

---

## A3. 契约、严格输入与可信身份入口

对应：

- [第 4 课：API 契约](lessons/04-api-contracts.md)
- `contracts/`

要理解：

- URL、Method、Header、Body 都是契约的一部分；
- 人类文档和机器可执行测试各自解决什么；
- JSON 能解析不代表业务输入合法；
- 客户端发来的 `user_id` / `tenant_id` / `role` 默认不可信；
- 服务端认证后形成的 Principal 才是可信身份入口。

### 进入下一层的证据

能解释为什么跨租户查询不能只靠前端隐藏按钮，也不能相信 Body 中的 tenant。

---

# 主干 B：数据事实、SQL 与事务

HTTP 服务不落数据时，很多问题只是内存 Demo。一旦有数据库，真正后端问题开始出现。

## B1. PostgreSQL 与 SQL

对应：

- [第 5 课：SQL / PostgreSQL](lessons/05-sql-postgresql.md)
- `exercises/sql-postgres/`

学习顺序：

```text
表 / 行 / 列
↓
主键 / 外键 / NOT NULL / UNIQUE / CHECK
↓
SELECT / INSERT / UPDATE / DELETE
↓
JOIN / GROUP BY / ORDER BY
↓
索引
↓
EXPLAIN
↓
连接池 / timeout / migration
```

不要先背所有 SQL 语法。先能回答：

> 数据库里什么是“事实”？数据库本身如何阻止错误事实？

### 进入下一层的证据

能根据一个真实查询设计约束和索引，并用 `EXPLAIN` 验证，而不是“感觉这个字段重要所以加索引”。

---

## B2. Transaction / Lock / Idempotency

对应：

- [第 6 课：事务、并发更新和幂等](lessons/06-transactions-idempotency.md)

核心链路：

```text
一次业务操作
↓
可能修改多条事实
↓
需要 transaction
↓
多个请求可能同时修改
↓
需要冲突策略 / lock / version
↓
客户端可能因为超时重试
↓
需要 idempotency
```

重点不是背 ACID 四个字母，而是推演：

```text
数据库已经 COMMIT
但 HTTP Response 还没到客户端
此时服务宕机
客户端重试
会不会产生第二份业务事实？
```

### 进入下一层的证据

能自己画出“提交前宕机 / 提交后响应前宕机 / 并发重复请求”三种状态，并给出恢复方式。

---

# 主干 C：运行时可靠性

## C1. Redis：先明确角色

对应：

- [第 7 课：Redis](lessons/07-redis.md)
- `exercises/redis-lab/`

每次使用 Redis 前先填空：

```text
这次 Redis 是：
[ ] cache
[ ] session/短期状态
[ ] rate limiter
[ ] coordination
[ ] stream/message transport
```

如果说不清角色，不要先写 Redis 代码。

关键原则：

> 核心业务事实默认应有更可靠、可恢复的事实源；缓存丢了应该能重建。

### 进入下一层的证据

能解释 Redis 整库清空后，哪些功能只是变慢，哪些功能会真正丢业务，以及这是否符合设计。

---

## C2. 并发、goroutine、async、timeout、cancel

对应：

- [第 8 课：并发、超时和取消](lessons/08-concurrency-timeouts.md)
- `exercises/reliability-labs/concurrency_timeout.py`

先分清：

```text
Concurrency 并发
= 多个任务在同一时间段推进

Parallelism 并行
= 多个任务真的同时执行

Goroutine
= Go runtime 调度的轻量执行单元
```

然后再学：

- goroutine / channel；
- mutex / race；
- event loop / await；
- worker pool；
- semaphore；
- backpressure；
- timeout / deadline / cancel；
- retry / backoff / jitter。

### 进入下一层的证据

能解释为什么“启动 1000 个 goroutine”不等于“吞吐一定更高”，并能为下游设置并发上限和 deadline。

---

## C3. 异步消息与 Outbox

对应：

- [第 9 课：Outbox / Streams](lessons/09-streams-outbox.md)
- `exercises/redis-lab/`
- `exercises/reliability-labs/outbox_worker.py`

学习顺序：

```text
为什么不直接同步做完？
↓
为什么需要异步任务/消息？
↓
消息可能重复
↓
ACK 在什么时候？
↓
数据库和消息系统双写会怎样？
↓
Transactional Outbox
↓
Pending / reclaim / DLQ
↓
consumer idempotency
```

不要从 `XREADGROUP` API 开始学。

### 进入下一层的证据

能推演：业务事务已经提交，但 Consumer 在 ACK 前崩溃，消息再次投递为什么不能重复产生业务副作用。

---

# 主干 D：身份与安全

对应：

- [第 10 课：认证、授权与安全](lessons/10-auth-security.md)
- [认证速查](notes/authentication-cheatsheet.md)

必须建立这组关系：

```text
Cookie      浏览器机制
Session     服务端会话状态
Token       凭证统称
Bearer      Token 的使用方式之一
JWT         Token 格式之一

Authentication  你是谁
Authorization   你能做什么
```

然后再扩展：

- password hashing；
- Access/Refresh Token；
- JWT claims；
- RBAC/ABAC；
- owner/tenant；
- XSS/CSRF/CORS；
- HTTPS；
- Secret 管理；
- Webhook HMAC。

### 进入下一层的证据

能不看文档解释 JWT 与 Session 的取舍，并明确指出前端权限控制为什么不是安全边界。

---

# 主干 E：证明、调试与观测

## E1. Testing / Debugging

对应：

- [第 11 课：测试与调试](lessons/11-testing-debugging.md)
- [Debug log](progress/debug-log.md)

要分清测试在证明什么：

```text
Unit
Integration
Contract
E2E
Fault / load test
```

调试固定走：

```text
稳定复现
→ 收集证据
→ 找第一个错误状态
→ 提可证伪假设
→ 做最小实验
→ 修根因
→ 回归
```

### 进入下一层的证据

遇到 bug 时，不再只说“报错了”，而是能给出预期、实际、复现、第一处异常状态和验证假设的实验。

---

## E2. Logs / Metrics / Traces / SLO

对应：

- [第 12 课：可观测性](lessons/12-observability.md)

核心关系：

```text
Log    发生了什么具体事件
Metric 系统整体趋势怎样
Trace  一次请求跨组件经历了什么
```

然后学：

- request ID / trace ID；
- RED；
- cardinality；
- readiness / liveness；
- SLI / SLO；
- alert；
- error budget。

### 进入下一层的证据

能为一个 API 和一个异步 Worker 各设计最少一组“发生问题后真的能行动”的指标与告警。

---

# 主干 F：交付与分布式边界

## F1. Docker / CI / K8s

对应：

- [第 13 课：Docker、K8s、CI/CD](lessons/13-docker-k8s-ci.md)
- `exercises/infrastructure/`
- `exercises/reliability-labs/k8s/`

学习顺序：

```text
程序为什么依赖运行环境
↓
Image 为什么存在
↓
Container 与 VM 的区别
↓
Registry / digest
↓
Compose
↓
CI pipeline
↓
部署、滚动更新、回滚
↓
最后才是 Kubernetes desired state
```

K8s 不是后端入门前置知识。

### 进入下一层的证据

能解释 Docker image 为什么是部署单位，以及 Kubernetes 为什么是在多实例/多机器上持续维持期望状态，而不是“更高级的 Docker”。

---

## F2. 单体、微服务、Gateway、gRPC、事件

对应：

- [第 14 课：服务边界与通信](lessons/14-grpc-events-boundaries.md)

学习顺序：

```text
单进程
↓
模块化单体
↓
明确 owner / boundary
↓
真的存在独立部署/扩缩/团队边界时再拆服务
```

必须分清：

- reverse proxy；
- load balancer；
- API Gateway；
- BFF；
- REST；
- gRPC；
- SSE / WebSocket；
- async event。

### 进入下一层的证据

给定一个跨服务需求，能说清哪些操作应该同步、哪些适合异步，以及为什么不应该共享表随便写。

---

# 主干 G：Agent 工程化与系统设计

## G1. RAG / Agent 作为后端系统

对应：

- [第 15 课：RAG / Agent 生产化](lessons/15-rag-agent-production.md)

这里不再把 Agent 当“Prompt + 模型”。

要把它放回后端链路：

```text
HTTP / job request
↓
auth / tenant
↓
workflow / agent orchestration
↓
model + retrieval + tools
↓
deadline / concurrency / budget
↓
side-effect authorization / idempotency
↓
state / audit / eval / observability
```

重点：

- function/tool calling 是模型提出结构化工具调用，不等于自动有权限；
- workflow 是工程控制流；
- agent autonomy 越高，边界和审计要求越高；
- RAG 权限过滤必须发生在模型看到内容之前。

### 进入下一层的证据

能把一个 Agent Tool 当普通后端有副作用操作审查：谁有权限、能否重试、是否幂等、失败后如何补偿。

---

## G2. System Design

对应：

- [第 16 课：系统设计](lessons/16-system-design.md)

固定顺序：

```text
需求 / 非目标
↓
容量和 SLO
↓
API / contract
↓
数据事实和 owner
↓
正常数据流
↓
并发、一致性和失败窗口
↓
安全
↓
观测 / 测试 / 恢复
↓
找到真实瓶颈以后再扩展
```

系统设计不是背“Redis + Kafka + K8s + 微服务”。

### 掌握证据

能够解释一个组件为什么存在、去掉它会出现什么问题、以及在当前规模下为什么没有选择更复杂方案。

---

# 语言轨道怎么并行

## Go 轨道

当前学习 Go 后端时，可以直接把 Go 作为主轨：

```text
HTTP
→ middleware
→ config
→ context
→ errors
→ repository
→ SQL
→ transaction
→ goroutine/channel
→ graceful shutdown
→ tests
```

不要等“Python 课程完成”才写 Go。

## Python 轨道

Python 用于：

- FastAPI API 对照；
- asyncio；
- RAG / Agent；
- 快速可靠性实验。

如果某个概念已经在 Go 中理解，不必为了完成路线再机械重写 Python；反过来也一样。

## SQL / Redis 轨道

这两者不是独立语言课程，而是后端能力：

- SQL 必须跟真实数据模型、约束、查询和事务一起学；
- Redis 必须跟一个明确运行时问题一起学。

---

# 对话学习如何接入这条路线

一次对话可能跳跃：今天 JWT，明天 goroutine，后天数据库事务。这没有问题。

处理方式：

```text
对话讲通
↓
判断属于哪条主干
↓
如果是一次关键认知纠正 -> learning journal
↓
如果原 lesson 太薄或有误 -> 更新 lesson
↓
如果需要亲手验证 -> 新增/更新 exercise
↓
在 progress 中记录当前能力证据
```

不要为了“保持章节顺序”阻止真实问题驱动的学习。

---

# 什么时候做综合项目

[综合项目](projects/reliable-support-agent/README.md)用于整合已经理解的能力，不用于一次性学习所有技术。

新的阶段顺序：

```text
P0 单服务内存 API
P1 PostgreSQL 事实源
P2 事务 + 鉴权 + 幂等
P3 Redis + 并发（按实际问题引入）
P4 Outbox + Worker / Streams
P5 Agent/RAG
P6 可选：Gateway / 多服务 / K8s
```

每个阶段可以停很久。没有通过退出条件，就不要为了“进度”进入下一阶段。

---

# 最后判断是否真正进步

不要问：

> 我学到第几周了？

改问：

> 给我一个真实后端请求，我现在能独立解释到哪一层？遇到重复、并发、数据库提交、依赖超时和宕机时，我能推演到哪里？

这才是这份路线真正衡量的东西。
