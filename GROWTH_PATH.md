# 后端成长路径：从新手到“10 年开发成熟度”

这份文件回答一个长期问题：

> **如果从后端初学者一路成长到成熟高级工程师，能力应该按什么顺序长出来？**

它不是按真实年份打卡，也不是职位晋升表。

“10 年开发”在这里表示一种成熟度参照：面对陌生业务和故障时，能独立建立模型、做可靠取舍、控制复杂度，并用证据说明为什么。

具体知识依赖见 [`LEARNING_ROADMAP.md`](LEARNING_ROADMAP.md)；当前真正学到哪里见 [`progress/current-focus.md`](progress/current-focus.md)。

---

# 总体成长方向

```text
S0  后端新手：先看懂一次 Request -> Response
↓
S1  API 初学者：能独立写和解释小型 HTTP API
↓
S2  初级后端：数据、分层、认证、测试开始成体系
↓
S3  独立后端工程师：事务、并发、幂等、故障恢复
↓
S4  生产型工程师：部署、观测、性能、事故排查
↓
S5  高级后端：服务边界、异步、扩展性、系统设计
↓
S6  Senior+/Lead 成熟度：跨系统演进、迁移、成本和风险
↓
S7  “10 年开发”成熟度目标：复杂问题简化、技术战略、长期可靠性
```

不要为了快进阶段而跳过基础。

真正成熟通常表现为：

> 越来越知道什么时候**不用**一个技术，而不是知道越来越多技术名字。

---

# S0：后端新手——先把“一次请求”真正看懂

## 核心问题

```text
浏览器发出 GET /orders/123
到底怎样走到数据库，再怎样返回？
```

## 必须建立的心智模型

```text
Client
→ DNS / IP / Port
→ TCP / TLS
→ HTTP Server
→ Request parsing
→ Router
→ Middleware
→ Authentication / Principal
→ Handler
→ Service
→ Repository
→ Database
→ Response
```

## 要能解释

- Client / Server 是什么；
- IP、Port、`127.0.0.1`；
- HTTP Method、Path、Header、Body；
- `Content-Type` vs `Accept`；
- Router / Middleware / Handler 分别做什么；
- `connection refused`、404、405、401、403 大概分别在哪一层；
- 为什么请求不是“直接进入 Handler”。

## 要能动手

- 启一个 Go `net/http` 服务；
- 写 `/healthz`；
- 用 curl 调用；
- 制造 wrong method / wrong path；
- 看懂 `*http.Request` 和 `http.ResponseWriter`。

## 退出证据

关闭文档以后能画完整 Request -> Response，并沿图解释至少五个失败位置。

## 常见误区

```text
404 = 服务没启动             ❌
JWT = 登录本身               ❌
前端不会传非法值所以不用验证   ❌
Handler = 整个后端            ❌
```

---

# S1：API 初学者——能独立完成一个小后端请求链

## 核心问题

> 一个小功能应该怎样从 HTTP 输入变成可靠业务行为？

## 重点能力

### HTTP

- Method / Path 设计；
- JSON strict input；
- Header；
- status code；
- stable error code；
- request ID。

### Go

- struct / method / interface；
- error handling；
- `errors.Is`；
- `net/http`；
- `httptest`；
- 基础 `context.Context`。

### 分层

```text
Handler
负责 HTTP

Service
负责业务用例

Repository
负责访问事实
```

## 要能动手

自己写一个内存 Ticket / Order API：

```text
create
get
list
close/cancel
healthz
```

并有基础测试。

## 退出证据

给一个“新增 priority 字段”的需求，能自己判断：

```text
哪些是输入验证？
哪些是业务规则？
哪些是存储变化？
哪些测试要加？
```

---

# S2：初级后端工程师——让数据库、身份和测试成为系统边界

这个阶段开始从“Web Demo”进入真正后端。

## PostgreSQL

要理解：

```text
table / row / column
PK / FK
NOT NULL / UNIQUE / CHECK
SELECT / INSERT / UPDATE / DELETE
JOIN
ORDER BY
index
EXPLAIN
migration
connection pool
```

重点不是 SQL 语法数量，而是：

> **数据库如何保护业务事实？**

## Authentication / Authorization

要建立：

```text
Credential
→ Authentication
→ Principal
→ Authorization
→ owner / tenant / permission
```

并真正理解：

```text
Cookie
Session
Token
Bearer
JWT
Access Token
Refresh Token
```

不在同一层级。

## Testing

能区分：

```text
unit
handler/API
integration
contract
E2E
```

## 安全最低线

- 参数化 SQL；
- password hashing；
- Secret 不进 Git；
- client `tenant_id/user_id/role` 不可信；
- tenant/owner scope 进入后端数据访问。

## 退出证据

能把内存 Repository 换 PostgreSQL，并解释：

```text
为什么数据重启后还在？
哪个 constraint 保护哪个不变量？
为什么这个 query 要这个 index？
身份从哪里来？
为什么 tenant 不能相信 body？
```

---

# S3：独立后端工程师——开始真正处理“失败后会怎样”

这是很关键的一次跃迁。

新手主要想：

```text
正常情况下能不能跑？
```

独立工程师开始想：

```text
在任何两步之间宕机会怎样？
两个请求同时来会怎样？
客户端重试会怎样？
```

## Transaction

不只背 ACID，要能推演：

```text
BEGIN
↓
业务写入
↓
COMMIT
↓
HTTP Response
```

每个边界失败的结果。

## Concurrency

要理解：

- data race；
- business race；
- lost update；
- optimistic locking/version；
- `FOR UPDATE`；
- unique constraint；
- deadlock；
- bounded concurrency。

## Idempotency

核心失败：

```text
DB COMMIT 成功
↓
Response 丢失
↓
客户端 timeout
↓
retry
```

必须知道如何避免重复业务副作用。

## Timeout / Cancel / Retry

建立：

```text
request deadline
↓
Service
↓
Repository
↓
DB / HTTP dependency
```

并知道 retry 可能放大压力。

## Redis

不再问：

```text
Redis 会不会？
```

而问：

```text
这里 Redis 的角色是什么？
cache/session/rate-limit/coordination/stream？
它全丢后会怎样？
source of truth 是谁？
```

## 退出证据

能亲手制造并解释：

- lost update；
- COMMIT 后 response 前失败；
- duplicate request；
- context timeout；
- Redis unavailable；
- bounded worker pool。

---

# S4：生产型后端工程师——系统不仅要正确，还要能运行和排错

## Observability

真正理解：

```text
Log
Metric
Trace
```

分别回答什么问题。

会使用：

- request ID / trace ID；
- HTTP RED；
- async backlog / oldest age；
- high-cardinality 风险；
- liveness / readiness；
- SLI / SLO / error budget。

## Debugging

排障不再靠猜：

```text
稳定复现
→ 最后一个正确状态
→ 第一个错误状态
→ 可证伪假设
→ 最小实验
→ 根因
→ regression test
```

## Deployment

理解：

```text
source
→ CI
→ tested artifact
→ Docker Image
→ Registry / Digest
→ Deployment
→ readiness
→ rollout
```

而不是只会 `docker build`。

## Performance

开始掌握：

- latency percentiles；
- throughput；
- saturation；
- connection pool；
- profiling；
- load test；
- capacity budget。

## 退出证据

面对：“接口偶尔 2 秒变 20 秒”，不会第一反应加机器，而是能先提出可观测证据和验证计划。

---

# S5：高级后端工程师——从单功能正确走向系统边界正确

## Modular Monolith / Microservice

成熟顺序：

```text
先有模块边界
↓
再判断是否需要网络边界
```

要能解释拆服务新增：

```text
network timeout
service auth
version compatibility
partial failure
retry amplification
observability
independent deployment
```

## 同步 / 异步

能根据业务语义选择：

```text
HTTP/REST
gRPC
job/event/message
SSE/WebSocket
```

不是哪个“高级”用哪个。

## Outbox / Messaging

能推演：

```text
DB + Broker dual write
Outbox
at-least-once
consumer idempotency
ACK timing
Pending / reclaim
retry / DLQ
lease / fencing
```

## Cache / Search / Projection

知道派生数据和事实源的区别。

## System Design

开始从：

```text
需求
→ 规模估算
→ source of truth
→ 最小设计
→ failure model
→ bottleneck evidence
→ evolution
```

推导架构。

## 退出证据

给一个“做一个客服工单系统”的需求，可以先设计可靠单服务方案，而不是立即画 12 个微服务。

---

# S6：Senior+ / Lead 成熟度——能管理演进，而不只是设计新系统

很多真正困难的问题不是 greenfield，而是：

> **旧系统正在运行，怎样安全地变成新系统？**

## Schema / API Evolution

要能做：

```text
additive change
backward compatibility
expand / migrate / contract
backfill
version rollout
```

## Migration

能设计：

- 单体拆服务；
- 存储迁移；
- cache rollout；
- event version migration；
- dual read / dual write 风险；
- rollback 条件。

## Reliability Engineering

能讨论：

- failure domains；
- RPO / RTO；
- dependency budget；
- graceful degradation；
- overload protection；
- incident learning；
- game day / fault injection。

## Security

不只是 JWT：

- trust boundary；
- least privilege；
- service identity；
- Secret lifecycle；
- audit；
- SSRF / injection；
- abuse/rate policy；
- data retention / deletion。

## Cost / Operability

知道工程选择同时消耗：

```text
开发成本
运行成本
认知成本
排障成本
值班成本
迁移成本
```

## 退出证据

能审一个复杂方案，并清楚指出：

```text
哪些复杂度是现在真正需要的？
哪些只是预想？
最安全的渐进迁移路径是什么？
失败后如何恢复？
```

---

# S7：“10 年开发成熟度”目标——复杂系统中保持简单、可靠和可解释

这不是“知道所有框架”。

成熟工程师面对新问题往往先问：

```text
我们真正要保护的业务事实是什么？
哪个约束是硬约束？
规模到底多大？
失败能不能接受？
哪里必须强一致？
哪里可以最终一致？
最小设计是什么？
有什么证据说明它不够？
```

## 1. 能在模糊需求中找到关键变量

例如主动澄清：

- QPS；
- 数据规模；
- latency SLO；
- consistency；
- availability；
- tenant isolation；
- compliance；
- failure tolerance；
- budget。

## 2. 能控制复杂度

面对：

```text
Redis
Kafka
K8s
Microservice
Service Mesh
CQRS
Event Sourcing
```

首先问“为什么”，而不是“怎么接”。

## 3. 能设计失败，而不只设计成功路径

对关键链路可以逐箭头推演：

```text
这里 timeout？
这里重复？
这里宕机？
这里发生网络分区？
这里旧 Worker 继续写？
这里 schema 新旧版本同时存在？
```

## 4. 能通过证据改变设计

不是凭资历说：

```text
我觉得 Kafka 更好。
```

而是：

```text
当前 backlog / throughput / retention / replay 需求已经超过现方案边界，因此引入 log-based broker；它新增这些运维和兼容成本。
```

## 5. 能快速读陌生系统

进入陌生代码库先找：

```text
entrypoint
request flow
identity
source of truth
transaction boundaries
async boundaries
timeouts/retries
observability
deployment
ownership
```

而不是逐文件阅读。

## 6. 能做事故推理

从 symptom 到证据：

```text
impact
→ scope
→ first bad signal
→ changed dependency/state
→ hypothesis
→ mitigation
→ root cause
→ prevention
```

## 7. 能指导别人

真正成熟不仅自己会做，还能把复杂概念解释给初学者，并知道：

- 哪些细节现在必须讲；
- 哪些可以以后讲；
- 哪个实验最能暴露错误心智模型；
- 如何 review 而不替别人完成全部思考。

## 8. 能承担长期系统责任

考虑：

```text
今天能上线
≠
两年后还能维护
```

包括：

- migration；
- deprecation；
- ownership；
- operational load；
- cost；
- documentation；
- on-call；
- security lifecycle；
- data lifecycle。

---

# AI 如何使用这张成长路径

不要根据阶段编号机械授课。

每次先读取 [`progress/current-focus.md`](progress/current-focus.md)，然后使用本文件回答：

```text
当前问题属于哪个成熟度阶段？
它依赖哪些更基础的心智模型？
现在应该展开到多深？
什么证据说明可以进入下一层？
```

如果用户在 S0 学 HTTP，却主动问 Kafka，可以解释 Kafka 是什么，但应该把它放回成长路径：

```text
你现在可以先知道它解决什么；真正深入它之前，需要先理解 transaction、idempotency、async delivery 和 failure model。
```

这不是阻止探索，而是让新知识有位置。

---

# 每一阶段都使用同一套能力判定

```text
L0 未接触
L1 见过
L2 能解释
L3 能独立实现 / 测试 / 排错
L4 能做取舍
```

因此可能出现：

```text
HTTP = L2
Go syntax = L1/L2
JWT concept = L2
PostgreSQL = L1
Kubernetes = L1
```

这很正常。

工程师不是“整体处于一个等级”，而是不同能力维度逐渐形成网络。

---

# 最终标准

真正从新手走向成熟工程师，不是仓库文件越来越多，而是思考开始从：

```text
这个 API 怎么写？
```

升级为：

```text
它为什么存在？
事实在哪里？
谁有权修改？
并发怎么办？
失败怎么办？
恢复怎么办？
如何证明？
当前最简单正确方案是什么？
```

当这些问题成为默认反应时，才是真正接近“10 年开发成熟度”。